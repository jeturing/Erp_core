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
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Plan,
    Invoice, InvoiceStatus, InvoiceType, InvoiceIssuer,
    BillingMode, Partner, SessionLocal,
)

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


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


def _next_invoice_number(db: Session) -> str:
    """Genera INV-YYYY-NNNN."""
    year = datetime.utcnow().year
    last = db.query(Invoice).filter(
        Invoice.invoice_number.like(f"INV-{year}-%")
    ).order_by(Invoice.id.desc()).first()
    seq = int(last.invoice_number.split("-")[-1]) + 1 if last else 1
    return f"INV-{year}-{seq:04d}"


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
    results = {
        "linked": 0,
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "details": [],
    }

    try:
        # Fetch suscripciones activas de Stripe
        stripe_subs = _fetch_all_stripe_subscriptions(
            statuses=["active", "trialing", "past_due"]
        )
        logger.info(f"Stripe sync: {len(stripe_subs)} suscripciones encontradas")

        for s_sub in stripe_subs:
            try:
                _process_stripe_subscription(db, s_sub, results)
            except Exception as e:
                results["errors"].append({
                    "stripe_sub_id": s_sub.get("id"),
                    "error": str(e),
                })
                logger.error(f"Error procesando sub {s_sub.get('id')}: {e}")

        db.commit()

    except stripe.error.StripeError as e:
        results["errors"].append({"error": f"Stripe API: {e}"})
        logger.error(f"Stripe API error: {e}")

    return results


def _fetch_all_stripe_subscriptions(statuses: List[str] = None) -> list:
    """Pagina por TODAS las suscripciones de Stripe."""
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


def _process_stripe_subscription(
    db: Session, s_sub: dict, results: dict
) -> None:
    """Procesa una suscripción individual de Stripe."""
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

    # 1. Por stripe_customer_id directo
    local_customer = _find_customer_by_stripe_id(db, stripe_cust_id)

    # 2. Por metadata.erp_customer_id
    if not local_customer and metadata.get("erp_customer_id"):
        try:
            cid = int(metadata["erp_customer_id"])
            local_customer = db.query(Customer).filter(Customer.id == cid).first()
        except (ValueError, TypeError):
            pass

    # 3. Por email (puede haber múltiples — buscar el que NO sea admin)
    if not local_customer and stripe_email:
        candidates = db.query(Customer).filter(
            Customer.email == stripe_email
        ).all()
        # Preferir no-admin
        for c in candidates:
            if not c.is_admin_account:
                local_customer = c
                break
        if not local_customer and candidates:
            local_customer = candidates[0]

    # 4. Si aún no hay match → buscar por nombre de empresa
    if not local_customer and stripe_name:
        local_customer = db.query(Customer).filter(
            Customer.company_name.ilike(f"%{stripe_name}%")
        ).first()

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

    # ── Actualizar stripe_customer_id si falta ──
    if not local_customer.stripe_customer_id and stripe_cust_id:
        local_customer.stripe_customer_id = stripe_cust_id

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

    # Monto real de Stripe (en USD)
    monthly_amount = stripe_amount / 100 if stripe_amount else 0

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
        if monthly_amount > 0 and abs((local_sub.monthly_amount or 0) - monthly_amount) > 0.01:
            local_sub.monthly_amount = monthly_amount
            changed.append(f"amount→${monthly_amount:.2f}")
        if period_start:
            local_sub.current_period_start = period_start
        if period_end:
            local_sub.current_period_end = period_end

        local_sub.updated_at = datetime.utcnow()

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
            monthly_amount=monthly_amount,
            currency="USD",
            current_period_start=period_start,
            current_period_end=period_end,
            billing_mode=BillingMode.JETURING_DIRECT_SUBSCRIPTION,
        )
        db.add(new_sub)
        results["created"] += 1
        results["details"].append({
            "action": "created",
            "customer": local_customer.company_name,
            "stripe_sub_id": stripe_sub_id,
            "plan": plan_name,
            "amount": monthly_amount,
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
            datetime.utcnow().replace(
                day=1, hour=0, minute=0, second=0
            ).timestamp()
        ) - (months_back * 30 * 86400)

        stripe_invoices = _fetch_stripe_invoices(since_ts)
        logger.info(f"Stripe invoice sync: {len(stripe_invoices)} facturas")

        for s_inv in stripe_invoices:
            try:
                _process_stripe_invoice(db, s_inv, results)
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


def _process_stripe_invoice(
    db: Session, s_inv: dict, results: dict
) -> None:
    """Procesa una factura individual de Stripe."""
    stripe_inv_id = s_inv["id"]

    # ¿Ya existe?
    existing = db.query(Invoice).filter(
        Invoice.stripe_invoice_id == stripe_inv_id
    ).first()

    if existing:
        # Actualizar estado si cambió
        new_status = _map_invoice_status(s_inv.get("status"))
        if existing.status != new_status:
            existing.status = new_status
            if new_status == InvoiceStatus.paid and not existing.paid_at:
                existing.paid_at = _ts_to_dt(s_inv.get("status_transitions", {}).get("paid_at"))
            results["updated"] += 1
        else:
            results["skipped_existing"] += 1
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

    # ── Datos factura ──
    amount_total = (s_inv.get("amount_paid") or s_inv.get("total") or 0) / 100
    amount_subtotal = (s_inv.get("subtotal") or 0) / 100
    tax_amount = (s_inv.get("tax") or 0) / 100
    inv_status = _map_invoice_status(s_inv.get("status"))
    paid_at_ts = s_inv.get("status_transitions", {}).get("paid_at")

    # Líneas de la factura
    lines = []
    for line in s_inv.get("lines", {}).get("data", []):
        desc = line.get("description") or line.get("plan", {}).get("nickname") or "Suscripción"
        lines.append({
            "description": desc,
            "qty": line.get("quantity", 1),
            "unit_price": (line.get("amount") or 0) / 100,
            "subtotal": (line.get("amount") or 0) / 100,
            "period_start": _ts_to_dt(line.get("period", {}).get("start")),
            "period_end": _ts_to_dt(line.get("period", {}).get("end")),
        })
    # Serializar datetimes en lines para JSON
    for line in lines:
        for k in ("period_start", "period_end"):
            if line.get(k) and hasattr(line[k], "isoformat"):
                line[k] = line[k].isoformat()

    invoice = Invoice(
        invoice_number=_next_invoice_number(db),
        subscription_id=local_sub.id if local_sub else None,
        customer_id=local_customer.id,
        partner_id=local_partner.id if local_partner else None,
        invoice_type=InvoiceType.SUBSCRIPTION,
        billing_mode=local_sub.billing_mode if local_sub else BillingMode.JETURING_DIRECT_SUBSCRIPTION,
        issuer=InvoiceIssuer.JETURING,
        subtotal=amount_subtotal,
        tax_amount=tax_amount,
        total=amount_total,
        currency=s_inv.get("currency", "usd").upper(),
        lines_json=lines,
        stripe_invoice_id=stripe_inv_id,
        stripe_payment_intent_id=s_inv.get("payment_intent"),
        status=inv_status,
        issued_at=_ts_to_dt(s_inv.get("created")),
        paid_at=_ts_to_dt(paid_at_ts) if paid_at_ts else None,
        due_date=_ts_to_dt(s_inv.get("due_date")),
    )
    db.add(invoice)
    db.flush()

    results["imported"] += 1
    results["details"].append({
        "action": "imported",
        "invoice_number": invoice.invoice_number,
        "stripe_invoice_id": stripe_inv_id,
        "customer": local_customer.company_name,
        "total": amount_total,
        "status": inv_status.value,
    })


def _map_invoice_status(stripe_status: str) -> InvoiceStatus:
    """Mapea estado de factura Stripe → enum local."""
    mapping = {
        "paid": InvoiceStatus.paid,
        "open": InvoiceStatus.issued,
        "draft": InvoiceStatus.draft,
        "void": InvoiceStatus.void,
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
    results = {"linked": 0, "already_linked": 0, "not_found": 0, "details": []}

    customers_without = db.query(Customer).filter(
        Customer.stripe_customer_id == None,
        Customer.is_admin_account == False,
    ).all()

    for customer in customers_without:
        try:
            stripe_custs = stripe.Customer.list(email=customer.email, limit=1)
            if stripe_custs["data"]:
                customer.stripe_customer_id = stripe_custs["data"][0]["id"]
                results["linked"] += 1
                results["details"].append({
                    "customer": customer.company_name,
                    "stripe_customer_id": customer.stripe_customer_id,
                })
            else:
                results["not_found"] += 1
        except Exception as e:
            results["details"].append({
                "customer": customer.company_name,
                "error": str(e),
            })

    db.commit()
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
