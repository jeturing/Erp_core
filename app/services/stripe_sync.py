"""
Stripe Sync Service — Stripe es la fuente de verdad.

Sincroniza:
1. Stripe Subscriptions → subscriptions (vincular por email/metadata)
2. Stripe Invoices     → invoices (facturas reales de consumo mensual)
3. Stripe Customers    → customers.stripe_customer_id

Flujo: Stripe API → match por email → actualizar BD local.
"""
import stripe
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Plan,
    Invoice, InvoiceStatus, InvoiceType, InvoiceIssuer,
    BillingMode, Partner, SessionLocal,
)
from ..config import get_runtime_setting
from ..services.pricing import (
    calculate_effective_subscription_amount,
    get_effective_plan_snapshot,
    recalculate_subscription_monthly_amount,
)

logger = logging.getLogger(__name__)

JETURING_INTERNAL_EMAILS = {"admin@sajet.us"}


def _configure_stripe() -> str:
    stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
    return stripe.api_key


# ── Helpers ──

def _ts_to_dt(ts: int) -> Optional[datetime]:
    """Unix timestamp → datetime UTC."""
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)


def _stripe_status_to_local(status: str) -> SubscriptionStatus:
    """Mapea status de Stripe → enum local."""
    mapping = {
        "active": SubscriptionStatus.active,
        "trialing": SubscriptionStatus.trialing,
        "past_due": SubscriptionStatus.past_due,
        "canceled": SubscriptionStatus.cancelled,
        "incomplete": SubscriptionStatus.pending,
        "incomplete_expired": SubscriptionStatus.cancelled,
        "unpaid": SubscriptionStatus.suspended,
        "paused": SubscriptionStatus.suspended,
    }
    return mapping.get(status, SubscriptionStatus.pending)


def _match_plan_by_price(db: Session, stripe_price_id: str) -> Optional[Plan]:
    """Busca plan local que coincida con stripe_price_id."""
    if not stripe_price_id:
        return None
    return db.query(Plan).filter(
        Plan.stripe_price_id == stripe_price_id,
        Plan.is_active == True,
    ).first()


def _match_plan_by_amount(db: Session, amount_cents: int) -> Optional[Plan]:
    """Fallback: busca plan por monto ($amount/100)."""
    amount_usd = amount_cents / 100
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.base_price).all()
    for p in plans:
        if abs(p.base_price - amount_usd) < 1.0:
            return p
    return None


def _find_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    """Busca cliente local por email."""
    if not email:
        return None
    return db.query(Customer).filter(Customer.email == email).first()


def _find_customers_by_email(db: Session, email: str) -> list[Customer]:
    """Busca todos los customers locales por email."""
    if not email:
        return []
    return db.query(Customer).filter(Customer.email == email).all()


def _find_customer_by_stripe_id(db: Session, stripe_cust_id: str) -> Optional[Customer]:
    """Busca cliente local por stripe_customer_id."""
    if not stripe_cust_id:
        return None
    return db.query(Customer).filter(
        Customer.stripe_customer_id == stripe_cust_id
    ).first()


def _find_partner_by_email(db: Session, email: str) -> Optional[Partner]:
    """Busca partner por contact_email para vincular facturas."""
    if not email:
        return None
    return db.query(Partner).filter(Partner.contact_email == email).first()


def _is_jeturing_associated_customer(customer: Optional[Customer]) -> bool:
    if not customer:
        return False
    email = (customer.email or "").strip().lower()
    return bool(customer.is_admin_account) or email in JETURING_INTERNAL_EMAILS


def _next_invoice_number(db: Session) -> str:
    """Genera INV-YYYY-NNNN."""
    year = datetime.now(timezone.utc).replace(tzinfo=None).year
    last = db.query(Invoice).filter(
        Invoice.invoice_number.like(f"INV-{year}-%")
    ).order_by(Invoice.id.desc()).first()
    seq = int(last.invoice_number.split("-")[-1]) + 1 if last else 1
    return f"INV-{year}-{seq:04d}"


def _billing_period_key(period_start: Optional[datetime], period_end: Optional[datetime]) -> Optional[str]:
    """Clave estable para idempotencia de facturas por período."""
    if not period_start or not period_end:
        return None
    return f"{period_start.date().isoformat()}__{period_end.date().isoformat()}"


def _extract_invoice_period_bounds(s_inv: dict) -> tuple[Optional[datetime], Optional[datetime]]:
    """Intenta inferir el período real de la factura Stripe desde líneas o suscripción expandida."""
    starts: list[datetime] = []
    ends: list[datetime] = []

    for line in s_inv.get("lines", {}).get("data", []):
        start = _ts_to_dt(line.get("period", {}).get("start"))
        end = _ts_to_dt(line.get("period", {}).get("end"))
        if start:
            starts.append(start)
        if end:
            ends.append(end)

    if starts and ends:
        return min(starts), max(ends)

    stripe_sub = s_inv.get("subscription")
    if isinstance(stripe_sub, dict):
        return _ts_to_dt(stripe_sub.get("current_period_start")), _ts_to_dt(stripe_sub.get("current_period_end"))

    return None, None


def _find_local_invoice_for_period(
    db: Session,
    *,
    local_sub: Optional[Subscription],
    local_customer: Customer,
    billing_period_key: Optional[str],
) -> Optional[Invoice]:
    """Busca una factura local del mismo período para vincularla a Stripe."""
    if local_sub and billing_period_key:
        candidate = db.query(Invoice).filter(
            Invoice.subscription_id == local_sub.id,
            Invoice.billing_period_key == billing_period_key,
        ).order_by(Invoice.id.asc()).first()
        if candidate:
            return candidate

    return None


def _apply_stripe_invoice_to_local(
    invoice: Invoice,
    s_inv: dict,
    *,
    local_sub: Optional[Subscription],
    local_partner: Optional[Partner],
    billing_period_key: Optional[str],
    period_start: Optional[datetime],
    period_end: Optional[datetime],
) -> None:
    """Aplica el estado/importe de Stripe sobre una factura local."""
    amount_total = (s_inv.get("amount_paid") or s_inv.get("total") or 0) / 100
    amount_subtotal = (s_inv.get("subtotal") or 0) / 100
    tax_amount = (s_inv.get("tax") or 0) / 100
    inv_status = _map_invoice_status(s_inv.get("status"))
    paid_at_ts = s_inv.get("status_transitions", {}).get("paid_at")

    lines = []
    for line in s_inv.get("lines", {}).get("data", []):
        desc = line.get("description") or line.get("plan", {}).get("nickname") or "Suscripción"
        line_period_start = _ts_to_dt(line.get("period", {}).get("start"))
        line_period_end = _ts_to_dt(line.get("period", {}).get("end"))
        lines.append({
            "description": desc,
            "qty": line.get("quantity", 1),
            "unit_price": (line.get("amount") or 0) / 100,
            "subtotal": (line.get("amount") or 0) / 100,
            "period_start": line_period_start.isoformat() if line_period_start else None,
            "period_end": line_period_end.isoformat() if line_period_end else None,
        })

    invoice.subscription_id = local_sub.id if local_sub else invoice.subscription_id
    invoice.partner_id = local_partner.id if local_partner else invoice.partner_id
    invoice.invoice_type = InvoiceType.SUBSCRIPTION
    invoice.billing_mode = local_sub.billing_mode if local_sub else (invoice.billing_mode or BillingMode.JETURING_DIRECT_SUBSCRIPTION)
    invoice.issuer = InvoiceIssuer.JETURING
    invoice.subtotal = amount_subtotal
    invoice.tax_amount = tax_amount
    invoice.total = amount_total
    invoice.currency = s_inv.get("currency", "usd").upper()
    invoice.lines_json = lines
    invoice.stripe_invoice_id = s_inv["id"]
    invoice.stripe_payment_intent_id = s_inv.get("payment_intent")
    invoice.status = inv_status
    invoice.issued_at = _ts_to_dt(s_inv.get("created"))
    invoice.paid_at = _ts_to_dt(paid_at_ts) if paid_at_ts else None
    invoice.due_date = _ts_to_dt(s_inv.get("due_date"))
    invoice.billing_period_key = billing_period_key
    invoice.period_start = period_start
    invoice.period_end = period_end

    if inv_status == InvoiceStatus.void:
        note = f"stripe_void:{s_inv['id']}"
        if note not in (invoice.notes or ""):
            invoice.notes = f"{(invoice.notes or '').strip()} {note}".strip()


# ═══════════════════════════════════════════════════════════════
#  SYNC SUBSCRIPTIONS: Stripe → BD
# ═══════════════════════════════════════════════════════════════

def sync_subscriptions(db: Session) -> Dict[str, Any]:
    """
    Lee TODAS las suscripciones activas/trialing/past_due de Stripe
    y las vincula/actualiza en la BD local.

    Matching: stripe_customer.email → customers.email
              OR metadata.erp_customer_id → customers.id
              OR stripe_customer_id directo

    Returns:
        {linked, created, updated, skipped, errors, details}
    """
    _configure_stripe()
    results = {
        "linked": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "details": [],
    }
    reserved_customer_links = {
        row.stripe_customer_id: row.id
        for row in db.query(Customer).filter(Customer.stripe_customer_id != None).all()
        if row.stripe_customer_id
    }

    try:
        # Fetch suscripciones activas de Stripe
        stripe_subs = _fetch_all_stripe_subscriptions(
            statuses=["active", "trialing", "past_due"]
        )
        logger.info(f"Stripe sync: {len(stripe_subs)} suscripciones encontradas")

        for s_sub in stripe_subs:
            try:
                upsert_stripe_subscription(db, s_sub, results, reserved_customer_links=reserved_customer_links)
            except Exception as e:
                results["errors"].append({
                    "stripe_sub_id": s_sub.get("id"),
                    "error": str(e),
                })
                logger.error(f"Error procesando sub {s_sub.get('id')}: {e}")

        try:
            db.commit()
        except IntegrityError as e:
            db.rollback()
            results["errors"].append({
                "error": f"subscription_commit_failed: {e}",
            })

    except stripe.error.StripeError as e:
        results["errors"].append({"error": f"Stripe API: {e}"})
        logger.error(f"Stripe API error: {e}")

    return results


def _fetch_all_stripe_subscriptions(statuses: List[str] = None) -> list:
    """Pagina por TODAS las suscripciones de Stripe."""
    _configure_stripe()
    all_subs = []
    for status in (statuses or ["active"]):
        has_more = True
        starting_after = None
        while has_more:
            params = {"limit": 100, "status": status, "expand": ["data.customer"]}
            if starting_after:
                params["starting_after"] = starting_after
            result = stripe.Subscription.list(**params)
            all_subs.extend(result["data"])
            has_more = result.get("has_more", False)
            if result["data"]:
                starting_after = result["data"][-1]["id"]
    return all_subs


def upsert_stripe_subscription(
    db: Session,
    s_sub: dict,
    results: dict,
    reserved_customer_links: Optional[dict[str, int]] = None,
) -> None:
    """Procesa una suscripción individual de Stripe."""
    reserved_customer_links = reserved_customer_links or {}
    stripe_sub_id = s_sub["id"]
    stripe_cust = s_sub.get("customer", {})

    # Si customer es string (no expandido), fetch
    if isinstance(stripe_cust, str):
        try:
            stripe_cust = stripe.Customer.retrieve(stripe_cust)
        except Exception:
            stripe_cust = {"id": stripe_cust, "email": None}

    stripe_cust_id = stripe_cust.get("id", "")
    stripe_email = (stripe_cust.get("email") or "").lower().strip()
    stripe_name = stripe_cust.get("name") or stripe_cust.get("description") or ""
    metadata = s_sub.get("metadata", {})

    # ── Match customer local ──
    local_customer = None

    # 1. Por stripe_customer_id ya vinculado/reservado
    reserved_customer_id = reserved_customer_links.get(stripe_cust_id) if stripe_cust_id else None
    if reserved_customer_id:
        local_customer = db.query(Customer).filter(Customer.id == reserved_customer_id).first()

    # 2. Por stripe_customer_id directo persistido
    if not local_customer:
        local_customer = _find_customer_by_stripe_id(db, stripe_cust_id)

    # 3. Por metadata.erp_customer_id
    if not local_customer and metadata.get("erp_customer_id"):
        try:
            cid = int(metadata["erp_customer_id"])
            local_customer = db.query(Customer).filter(Customer.id == cid).first()
        except (ValueError, TypeError):
            pass

    # 4. Por email solo si hay un único customer local elegible
    if not local_customer and stripe_email:
        candidates = _find_customers_by_email(db, stripe_email)
        non_admin_candidates = [candidate for candidate in candidates if not candidate.is_admin_account]
        effective_candidates = non_admin_candidates or candidates

        if len(effective_candidates) == 1:
            local_customer = effective_candidates[0]
        elif len(effective_candidates) > 1:
            results["skipped"] += 1
            results["details"].append({
                "action": "skipped",
                "stripe_sub_id": stripe_sub_id,
                "stripe_customer_id": stripe_cust_id,
                "stripe_email": stripe_email,
                "reason": "duplicate_local_customers_for_email",
                "customer_ids": [candidate.id for candidate in effective_candidates],
            })
            return

    # 5. Si aún no hay match → buscar por nombre de empresa solo si es único
    if not local_customer and stripe_name:
        candidates = db.query(Customer).filter(
            Customer.company_name.ilike(f"%{stripe_name}%")
        ).all()
        non_admin_candidates = [candidate for candidate in candidates if not candidate.is_admin_account]
        effective_candidates = non_admin_candidates or candidates
        if len(effective_candidates) == 1:
            local_customer = effective_candidates[0]

    if not local_customer:
        results["skipped"] += 1
        results["details"].append({
            "action": "skipped",
            "stripe_sub_id": stripe_sub_id,
            "stripe_email": stripe_email,
            "stripe_name": stripe_name,
            "reason": "No matching customer found in DB",
        })
        return

    if _is_jeturing_associated_customer(local_customer):
        results["skipped"] += 1
        results["details"].append({
            "action": "skipped",
            "stripe_sub_id": stripe_sub_id,
            "stripe_email": stripe_email,
            "reason": "jeturing_associated_customer_excluded_from_stripe_billing",
            "customer_id": local_customer.id,
            "subdomain": local_customer.subdomain,
        })
        return

    # ── Actualizar stripe_customer_id si falta ──
    if not local_customer.stripe_customer_id and stripe_cust_id:
        linked_customer_id = reserved_customer_links.get(stripe_cust_id)
        if linked_customer_id and linked_customer_id != local_customer.id:
            results["skipped"] += 1
            results["details"].append({
                "action": "skipped",
                "stripe_sub_id": stripe_sub_id,
                "stripe_customer_id": stripe_cust_id,
                "reason": "stripe_customer_reserved_for_other_customer",
                "customer_id": local_customer.id,
                "reserved_customer_id": linked_customer_id,
            })
            return
        local_customer.stripe_customer_id = stripe_cust_id
        reserved_customer_links[stripe_cust_id] = local_customer.id
    elif stripe_cust_id and local_customer.stripe_customer_id == stripe_cust_id:
        reserved_customer_links[stripe_cust_id] = local_customer.id

    # ── Buscar suscripción local existente ──
    local_sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()

    if not local_sub:
        # Buscar por customer_id sin stripe_subscription_id
        local_sub = db.query(Subscription).filter(
            Subscription.customer_id == local_customer.id,
            Subscription.stripe_subscription_id == None,
            Subscription.status == SubscriptionStatus.active,
        ).first()

    # ── Datos de Stripe ──
    items = s_sub.get("items", {}).get("data", [])
    stripe_item = items[0] if items else {}
    stripe_price_id = stripe_item.get("price", {}).get("id") if stripe_item else None
    stripe_qty = stripe_item.get("quantity", 1)
    stripe_amount = (stripe_item.get("price", {}).get("unit_amount") or 0) * stripe_qty
    stripe_status = _stripe_status_to_local(s_sub.get("status", "active"))

    # Detectar plan
    plan = _match_plan_by_price(db, stripe_price_id)
    if not plan:
        plan = _match_plan_by_amount(db, stripe_amount)
    plan_name = plan.name if plan else "basic"

    period_start = _ts_to_dt(s_sub.get("current_period_start"))
    period_end = _ts_to_dt(s_sub.get("current_period_end"))

    if local_sub:
        # ── UPDATE suscripción existente ──
        changed = []
        if local_sub.stripe_subscription_id != stripe_sub_id:
            local_sub.stripe_subscription_id = stripe_sub_id
            changed.append("stripe_subscription_id")
        if local_sub.status != stripe_status:
            local_sub.status = stripe_status
            changed.append(f"status→{stripe_status.value}")
        if local_sub.plan_name != plan_name:
            local_sub.plan_name = plan_name
            changed.append(f"plan→{plan_name}")
        if stripe_qty and local_sub.user_count != stripe_qty:
            local_sub.user_count = stripe_qty
            local_customer.user_count = stripe_qty
            changed.append(f"users→{stripe_qty}")
        if period_start:
            local_sub.current_period_start = period_start
        if period_end:
            local_sub.current_period_end = period_end

        effective_amount = calculate_effective_subscription_amount(
            db,
            local_sub,
            customer=local_customer,
            plan=plan,
            user_count=stripe_qty,
        )
        if abs((local_sub.monthly_amount or 0) - effective_amount) > 0.01:
            local_sub.monthly_amount = effective_amount
            changed.append(f"amount→${effective_amount:.2f}")

        local_sub.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        if changed:
            results["updated"] += 1
            results["details"].append({
                "action": "updated",
                "customer": local_customer.company_name,
                "stripe_sub_id": stripe_sub_id,
                "changes": changed,
            })
        else:
            results["linked"] += 1
            results["details"].append({
                "action": "linked_ok",
                "customer": local_customer.company_name,
                "stripe_sub_id": stripe_sub_id,
            })
    else:
        # ── CREATE nueva suscripción local ──
        new_sub = Subscription(
            customer_id=local_customer.id,
            stripe_subscription_id=stripe_sub_id,
            plan_name=plan_name,
            status=stripe_status,
            user_count=stripe_qty,
            monthly_amount=0,
            currency="USD",
            current_period_start=period_start,
            current_period_end=period_end,
            billing_mode=BillingMode.JETURING_DIRECT_SUBSCRIPTION,
        )
        db.add(new_sub)
        db.flush()
        effective_amount = calculate_effective_subscription_amount(
            db,
            new_sub,
            customer=local_customer,
            plan=plan,
            user_count=stripe_qty,
        )
        new_sub.monthly_amount = effective_amount
        results["created"] += 1
        results["details"].append({
            "action": "created",
            "customer": local_customer.company_name,
            "stripe_sub_id": stripe_sub_id,
            "plan": plan_name,
            "amount": effective_amount,
        })


# ═══════════════════════════════════════════════════════════════
#  SYNC INVOICES: Stripe → BD
# ═══════════════════════════════════════════════════════════════

def sync_invoices(
    db: Session,
    months_back: int = 3,
) -> Dict[str, Any]:
    """
    Importa facturas reales de Stripe (pagadas/abiertas) a la BD local.
    Vincula con customer y partner por email.

    Solo importa facturas tipo 'subscription' (recurrentes).
    Las vincula a suscripciones locales por stripe_subscription_id.
    """
    _configure_stripe()
    results = {
        "imported": 0,
        "updated": 0,
        "skipped_existing": 0,
        "skipped_no_match": 0,
        "errors": [],
        "details": [],
    }

    try:
        since_ts = int(
            datetime.now(timezone.utc).replace(tzinfo=None).replace(
                day=1, hour=0, minute=0, second=0
            ).timestamp()
        ) - (months_back * 30 * 86400)

        stripe_invoices = _fetch_stripe_invoices(since_ts)
        logger.info(f"Stripe invoice sync: {len(stripe_invoices)} facturas")

        for s_inv in stripe_invoices:
            try:
                upsert_stripe_invoice(db, s_inv, results)
            except Exception as e:
                results["errors"].append({
                    "stripe_invoice_id": s_inv.get("id"),
                    "error": str(e),
                })

        db.commit()

    except stripe.error.StripeError as e:
        results["errors"].append({"error": f"Stripe API: {e}"})

    return results


def _fetch_stripe_invoices(since_ts: int) -> list:
    """Pagina facturas de Stripe desde since_ts."""
    _configure_stripe()
    all_invoices = []
    has_more = True
    starting_after = None

    while has_more:
        params = {
            "limit": 100,
            "created": {"gte": since_ts},
            "expand": ["data.customer", "data.subscription"],
        }
        if starting_after:
            params["starting_after"] = starting_after
        result = stripe.Invoice.list(**params)
        all_invoices.extend(result["data"])
        has_more = result.get("has_more", False)
        if result["data"]:
            starting_after = result["data"][-1]["id"]

    return all_invoices


def upsert_stripe_invoice(
    db: Session, s_inv: dict, results: dict
) -> None:
    """Procesa una factura individual de Stripe."""
    stripe_inv_id = s_inv["id"]
    period_start, period_end = _extract_invoice_period_bounds(s_inv)
    billing_period_key = _billing_period_key(period_start, period_end)

    # ¿Ya existe?
    existing = db.query(Invoice).filter(
        Invoice.stripe_invoice_id == stripe_inv_id
    ).first()

    if existing:
        _apply_stripe_invoice_to_local(
            existing,
            s_inv,
            local_sub=existing.subscription,
            local_partner=existing.partner,
            billing_period_key=billing_period_key,
            period_start=period_start,
            period_end=period_end,
        )
        results["updated"] += 1
        return

    # ── Match customer ──
    stripe_cust = s_inv.get("customer", {})
    if isinstance(stripe_cust, str):
        stripe_cust_id = stripe_cust
        stripe_email = ""
    else:
        stripe_cust_id = stripe_cust.get("id", "")
        stripe_email = (stripe_cust.get("email") or "").lower().strip()

    local_customer = _find_customer_by_stripe_id(db, stripe_cust_id)
    if not local_customer and stripe_email:
        candidates = db.query(Customer).filter(Customer.email == stripe_email).all()
        for c in candidates:
            if not c.is_admin_account:
                local_customer = c
                break
        if not local_customer and candidates:
            local_customer = candidates[0]

    if not local_customer:
        results["skipped_no_match"] += 1
        return

    if _is_jeturing_associated_customer(local_customer):
        results["skipped_no_match"] += 1
        results["details"].append({
            "action": "skipped",
            "stripe_invoice_id": stripe_inv_id,
            "reason": "jeturing_associated_customer_excluded_from_stripe_billing",
            "customer_id": local_customer.id,
            "subdomain": local_customer.subdomain,
        })
        return

    # ── Match subscription ──
    stripe_sub_ref = s_inv.get("subscription")
    stripe_sub_id = None
    if isinstance(stripe_sub_ref, dict):
        stripe_sub_id = stripe_sub_ref.get("id")
    elif isinstance(stripe_sub_ref, str):
        stripe_sub_id = stripe_sub_ref

    local_sub = None
    if stripe_sub_id:
        local_sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_sub_id
        ).first()
    if not local_sub:
        local_sub = db.query(Subscription).filter(
            Subscription.customer_id == local_customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).first()

    # ── Match partner (para vincular factura) ──
    local_partner = None
    if local_sub and local_sub.owner_partner_id:
        local_partner = db.query(Partner).filter(
            Partner.id == local_sub.owner_partner_id
        ).first()
    if not local_partner and stripe_email:
        local_partner = _find_partner_by_email(db, stripe_email)

    existing_period_invoice = _find_local_invoice_for_period(
        db,
        local_sub=local_sub,
        local_customer=local_customer,
        billing_period_key=billing_period_key,
    )

    invoice = existing_period_invoice or Invoice(
        invoice_number=_next_invoice_number(db),
        subscription_id=local_sub.id if local_sub else None,
        customer_id=local_customer.id,
        partner_id=local_partner.id if local_partner else None,
    )

    if existing_period_invoice is None:
        db.add(invoice)
        db.flush()

    _apply_stripe_invoice_to_local(
        invoice,
        s_inv,
        local_sub=local_sub,
        local_partner=local_partner,
        billing_period_key=billing_period_key,
        period_start=period_start,
        period_end=period_end,
    )

    if existing_period_invoice is None:
        results["imported"] += 1
        action = "imported"
    else:
        results["updated"] += 1
        action = "linked_existing_period"
    results["details"].append({
        "action": action,
        "invoice_number": invoice.invoice_number,
        "stripe_invoice_id": stripe_inv_id,
        "customer": local_customer.company_name,
        "total": invoice.total,
        "status": invoice.status.value,
        "billing_period_key": billing_period_key,
    })


def _map_invoice_status(stripe_status: str) -> InvoiceStatus:
    """Mapea estado de factura Stripe → enum local."""
    mapping = {
        "paid": InvoiceStatus.paid,
        "open": InvoiceStatus.issued,
        "draft": InvoiceStatus.draft,
        "void": InvoiceStatus.void,
        "voided": InvoiceStatus.void,
        "uncollectible": InvoiceStatus.overdue,
    }
    return mapping.get(stripe_status, InvoiceStatus.issued)


# ═══════════════════════════════════════════════════════════════
#  SYNC CUSTOMERS: Stripe → BD
# ═══════════════════════════════════════════════════════════════

def sync_stripe_customers(db: Session) -> Dict[str, Any]:
    """
    Sincroniza stripe_customer_id para todos los clientes
    buscando por email en Stripe.
    """
    _configure_stripe()
    results = {
        "linked": 0,
        "already_linked": 0,
        "not_found": 0,
        "conflicts": 0,
        "details": [],
    }

    customers_without = db.query(Customer).filter(
        Customer.stripe_customer_id == None,
        Customer.is_admin_account == False,
    ).all()
    existing_links = {
        row.stripe_customer_id: row.id
        for row in db.query(Customer).filter(Customer.stripe_customer_id != None).all()
        if row.stripe_customer_id
    }
    email_groups: dict[str, list[int]] = {}
    for row in db.query(Customer).filter(Customer.is_admin_account == False).all():
        normalized_email = (row.email or "").strip().lower()
        if normalized_email:
            email_groups.setdefault(normalized_email, []).append(row.id)

    for customer in customers_without:
        try:
            if _is_jeturing_associated_customer(customer):
                results["not_found"] += 1
                results["details"].append({
                    "customer": customer.company_name,
                    "customer_id": customer.id,
                    "reason": "jeturing_associated_customer_excluded_from_stripe_billing",
                })
                continue

            normalized_email = (customer.email or "").strip().lower()
            if not normalized_email:
                results["not_found"] += 1
                results["details"].append({
                    "customer": customer.company_name,
                    "reason": "missing_email",
                })
                continue

            stripe_custs = stripe.Customer.list(email=customer.email, limit=1)
            if stripe_custs["data"]:
                stripe_customer_id = stripe_custs["data"][0]["id"]
                holder_id = existing_links.get(stripe_customer_id)
                duplicate_email_ids = email_groups.get(normalized_email, [])

                if holder_id and holder_id != customer.id:
                    results["conflicts"] += 1
                    results["details"].append({
                        "customer": customer.company_name,
                        "customer_id": customer.id,
                        "stripe_customer_id": stripe_customer_id,
                        "reason": "stripe_customer_id_already_linked",
                        "linked_customer_id": holder_id,
                    })
                    continue

                if len(duplicate_email_ids) > 1:
                    results["conflicts"] += 1
                    results["details"].append({
                        "customer": customer.company_name,
                        "customer_id": customer.id,
                        "email": customer.email,
                        "stripe_customer_id": stripe_customer_id,
                        "reason": "duplicate_local_customers_for_email",
                        "customer_ids": duplicate_email_ids,
                    })
                    continue

                customer.stripe_customer_id = stripe_customer_id
                try:
                    db.commit()
                    existing_links[stripe_customer_id] = customer.id
                    results["linked"] += 1
                    results["details"].append({
                        "customer": customer.company_name,
                        "customer_id": customer.id,
                        "stripe_customer_id": customer.stripe_customer_id,
                    })
                except IntegrityError as exc:
                    db.rollback()
                    results["conflicts"] += 1
                    results["details"].append({
                        "customer": customer.company_name,
                        "customer_id": customer.id,
                        "stripe_customer_id": stripe_customer_id,
                        "reason": "unique_violation",
                        "error": str(exc),
                    })
            else:
                results["not_found"] += 1
        except Exception as e:
            results["details"].append({
                "customer": customer.company_name,
                "error": str(e),
            })

    return results


# ═══════════════════════════════════════════════════════════════
#  FULL SYNC
# ═══════════════════════════════════════════════════════════════

def full_stripe_sync(db: Session, months_back: int = 3) -> Dict[str, Any]:
    """
    Sincronización completa:
    1. Stripe Customers → BD (vincular IDs)
    2. Stripe Subscriptions → BD (vincular + actualizar)
    3. Stripe Invoices → BD (importar facturas reales)
    """
    logger.info("═══ Starting full Stripe sync ═══")

    customer_results = sync_stripe_customers(db)
    logger.info(f"Customers: linked={customer_results['linked']}")

    sub_results = sync_subscriptions(db)
    logger.info(
        f"Subscriptions: linked={sub_results['linked']} "
        f"created={sub_results['created']} updated={sub_results['updated']}"
    )

    invoice_results = sync_invoices(db, months_back=months_back)
    logger.info(
        f"Invoices: imported={invoice_results['imported']} "
        f"updated={invoice_results['updated']}"
    )

    logger.info("═══ Full Stripe sync complete ═══")

    return {
        "customers": customer_results,
        "subscriptions": sub_results,
        "invoices": invoice_results,
    }
