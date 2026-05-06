"""
Stripe Billing Service — Bidireccional DB ↔ Stripe.

Funcionalidades:
1. push_invoice_to_stripe  → Crea factura en Stripe desde BD local y obtiene payment link
2. sync_subscription_qty   → Actualiza qty en Stripe cuando cambian usuarios
3. create_stripe_customer   → Crea cliente en Stripe si no existe
4. get_payment_link        → Obtiene hosted_invoice_url de Stripe para pago
5. create_checkout_for_invoice → Checkout Session para pagar factura pendiente

Flujo bidireccional:
  - BD cambia (nuevo usuario, plan upgrade) → push a Stripe
  - Stripe cambia (pago recibido, factura) → pull vía stripe_sync.py
"""
import stripe
import logging
from datetime import datetime, timezone, timedelta
from calendar import monthrange
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Plan,
    Invoice, InvoiceStatus, InvoiceType, InvoiceIssuer,
    BillingMode, Partner, SessionLocal, CustomerAddonSubscription, SeatHighWater, SeatEvent,
)
from ..config import get_runtime_setting
from ..services.pricing import (
    get_effective_plan_snapshot,
    recalculate_subscription_monthly_amount,
)

logger = logging.getLogger(__name__)

PAYABLE_INVOICE_STATUSES = {"draft", "issued", "open", "overdue", "past_due"}
INTERNAL_BILLING_EMAIL_DOMAINS = {"sajet.us", "jeturing.com"}


def _is_internal_billing_email(value: Optional[str]) -> bool:
    email = (value or "").strip().lower()
    if "@" not in email:
        return False
    domain = email.split("@", 1)[1]
    return domain in INTERNAL_BILLING_EMAIL_DOMAINS


def _is_partner_billed_subscription(subscription: Subscription) -> bool:
    mode = subscription.billing_mode
    return bool(
        subscription.owner_partner_id
        or mode in {
            BillingMode.PARTNER_DIRECT,
            BillingMode.PARTNER_PAYS_FOR_CLIENT,
        }
    )


def _configure_stripe() -> str:
    stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
    return stripe.api_key


def _app_url() -> str:
    return get_runtime_setting("APP_URL", "https://sajet.us")


def _normalize_period_start(value: Optional[datetime]) -> datetime:
    if value is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return datetime(now.year, now.month, 1)
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _resolve_billing_period(
    subscription: Subscription,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> tuple[datetime, datetime, str]:
    """Resuelve período de facturación priorizando current_period_* de Stripe."""
    if period_start is None:
        period_start = subscription.current_period_start
    if period_end is None:
        period_end = subscription.current_period_end

    if period_start is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        period_start = datetime(now.year, now.month, 1)
    else:
        period_start = _normalize_period_start(period_start)

    if period_end is None:
        year = period_start.year
        month = period_start.month
        _, last_day = monthrange(year, month)
        period_end = datetime(year, month, last_day) + timedelta(days=1)
    else:
        period_end = _normalize_period_start(period_end)

    if period_end <= period_start:
        period_end = period_start + timedelta(days=1)

    billing_period_key = f"{period_start.date().isoformat()}__{period_end.date().isoformat()}"
    return period_start, period_end, billing_period_key


def _normalize_invoice_status(status: Any) -> Optional[str]:
    if status is None:
        return None
    if hasattr(status, "value"):
        return str(status.value).lower()
    return str(status).lower()


def invoice_is_payable(status: Any) -> bool:
    return (_normalize_invoice_status(status) or "") in PAYABLE_INVOICE_STATUSES


def build_invoice_action_urls(
    *,
    status: Any,
    pdf_url: Optional[str] = None,
    hosted_url: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    normalized_status = _normalize_invoice_status(status)
    payment_url = hosted_url if invoice_is_payable(normalized_status) else None
    download_url = pdf_url or None
    view_url = hosted_url or pdf_url or None

    preferred_action = None
    if payment_url:
        preferred_action = "pay"
    elif download_url:
        preferred_action = "download"
    elif view_url:
        preferred_action = "view"

    return {
        "pdf_url": pdf_url or None,
        "hosted_url": hosted_url or None,
        "download_url": download_url,
        "payment_url": payment_url,
        "view_url": view_url,
        "preferred_action": preferred_action,
    }


def fetch_stripe_invoice_links(stripe_invoice_id: str) -> Dict[str, Optional[str]]:
    _configure_stripe()
    invoice = stripe.Invoice.retrieve(stripe_invoice_id)
    status = _normalize_invoice_status(invoice.get("status"))
    urls = build_invoice_action_urls(
        status=status,
        pdf_url=invoice.get("invoice_pdf"),
        hosted_url=invoice.get("hosted_invoice_url"),
    )
    return {
        "status": status,
        **urls,
    }


def _resolve_period_user_count(
    db: Session,
    subscription: Subscription,
    *,
    customer: Optional[Customer],
    period_start: datetime,
    period_end: datetime,
) -> tuple[int, str]:
    hwm = (
        db.query(SeatHighWater)
        .filter(
            SeatHighWater.subscription_id == subscription.id,
            SeatHighWater.period_date >= period_start,
            SeatHighWater.period_date < period_end,
        )
        .order_by(SeatHighWater.hwm_count.desc(), SeatHighWater.period_date.desc())
        .first()
    )
    if hwm and hwm.hwm_count is not None:
        return max(1, int(hwm.hwm_count)), "seat_high_water"

    live_count = getattr(subscription, "user_count", None) or (customer.user_count if customer else None) or 1
    return max(1, int(live_count)), "live_user_count"


def _resolve_partner_billable_user_count(
    db: Session,
    subscription: Subscription,
    *,
    period_start: datetime,
    period_end: datetime,
    fallback_count: int,
) -> tuple[int, str, dict]:
    """
    Estimación de seats billables para partner:
    - Parte del HWM/live count.
    - Descuenta cuentas internas detectadas por dominio (@sajet.us, @jeturing.com)
      en eventos del período.
    """
    internal_logins = (
        db.query(SeatEvent.odoo_login)
        .filter(
            SeatEvent.subscription_id == subscription.id,
            SeatEvent.created_at >= period_start,
            SeatEvent.created_at < period_end,
            SeatEvent.odoo_login.isnot(None),
        )
        .all()
    )
    internal_unique = {
        login.lower().strip()
        for (login,) in internal_logins
        if _is_internal_billing_email(login)
    }
    discounted = max(1, int(fallback_count) - len(internal_unique))
    return discounted, "partner_excluding_internal_domains", {
        "fallback_count": int(fallback_count),
        "internal_accounts_detected": len(internal_unique),
    }


def _invoice_has_metered_addons(invoice: Invoice) -> bool:
    lines = invoice.lines_json or []
    for line in lines:
        if not isinstance(line, dict):
            continue
        if line.get("catalog_item_id") or line.get("service_code"):
            return True
    return False


def _void_mismatched_invoice(
    db: Session,
    invoice: Invoice,
    *,
    expected_total: float,
    billing_period_key: Optional[str],
) -> None:
    if invoice.stripe_invoice_id:
        try:
            _configure_stripe()
            remote_invoice = stripe.Invoice.retrieve(invoice.stripe_invoice_id)
            remote_status = _normalize_invoice_status(remote_invoice.get("status"))
            if remote_status not in {"paid", "void"}:
                stripe.Invoice.void_invoice(invoice.stripe_invoice_id)
        except Exception as exc:
            logger.warning("Could not void Stripe invoice %s: %s", invoice.stripe_invoice_id, exc)

    invoice.status = InvoiceStatus.void
    note = (
        f"reconciled_price_mismatch:{billing_period_key or 'unknown'}:"
        f"expected={round(expected_total, 2)} found={round(invoice.total or 0, 2)}"
    )
    if note not in (invoice.notes or ""):
        invoice.notes = f"{(invoice.notes or '').strip()} {note}".strip()


# ═══════════════════════════════════════════════════════════════
#  1. CREAR CLIENTE EN STRIPE (si no existe)
# ═══════════════════════════════════════════════════════════════

def ensure_stripe_customer(db: Session, customer: Customer) -> str:
    """
    Asegura que el cliente tenga stripe_customer_id.
    Si no lo tiene, crea uno en Stripe.
    Retorna el stripe_customer_id.
    """
    _configure_stripe()
    if customer.stripe_customer_id:
        return customer.stripe_customer_id

    # Buscar en Stripe por email
    try:
        existing = stripe.Customer.list(email=customer.email, limit=1)
        if existing["data"]:
            customer.stripe_customer_id = existing["data"][0]["id"]
            db.commit()
            logger.info(f"Stripe customer found by email: {customer.email} → {customer.stripe_customer_id}")
            return customer.stripe_customer_id
    except stripe.error.StripeError as e:
        logger.warning(f"Error buscando customer en Stripe: {e}")

    # Crear nuevo
    try:
        s_cust = stripe.Customer.create(
            email=customer.email,
            name=customer.company_name or customer.full_name or customer.email,
            metadata={
                "erp_customer_id": str(customer.id),
                "source": "erp_core",
            },
        )
        customer.stripe_customer_id = s_cust["id"]
        db.commit()
        logger.info(f"Stripe customer created: {customer.email} → {s_cust['id']}")
        return s_cust["id"]
    except stripe.error.StripeError as e:
        logger.error(f"Error creando customer en Stripe: {e}")
        raise


# ═══════════════════════════════════════════════════════════════
#  2. PUSH INVOICE A STRIPE (BD → Stripe)
# ═══════════════════════════════════════════════════════════════

def push_invoice_to_stripe(
    db: Session,
    invoice: Invoice,
) -> Dict[str, Any]:
    """
    Crea una factura en Stripe basada en la factura local.
    Pasos:
    1. Asegurar que el customer tiene stripe_customer_id
    2. Crear InvoiceItems en Stripe
    3. Crear Invoice en Stripe
    4. Finalizar (auto_advance=True) para que Stripe envíe email y genere payment link
    5. Guardar stripe_invoice_id y hosted_invoice_url en BD

    Returns:
        {stripe_invoice_id, hosted_invoice_url, pdf_url, status}
    """
    _configure_stripe()
    if invoice.stripe_invoice_id:
        # Ya tiene — obtener URL actualizada
        try:
            s_inv = stripe.Invoice.retrieve(invoice.stripe_invoice_id)
            return {
                "stripe_invoice_id": s_inv["id"],
                "hosted_invoice_url": s_inv.get("hosted_invoice_url"),
                "pdf_url": s_inv.get("invoice_pdf"),
                "status": s_inv.get("status"),
                "already_exists": True,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving existing Stripe invoice: {e}")
            raise

    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if not customer:
        raise ValueError(f"Customer {invoice.customer_id} not found")

    # Asegurar stripe_customer_id
    stripe_cust_id = ensure_stripe_customer(db, customer)

    # Crear invoice items
    lines = invoice.lines_json or []
    if not lines:
        lines = [{
            "description": f"Factura {invoice.invoice_number}",
            "qty": 1,
            "unit_price": invoice.total,
            "subtotal": invoice.total,
        }]

    for line in lines:
        stripe.InvoiceItem.create(
            customer=stripe_cust_id,
            amount=int((line.get("subtotal", 0)) * 100),  # Centavos
            currency=(invoice.currency or "USD").lower(),
            description=line.get("description", "Suscripción"),
        )

    # Crear la factura en Stripe
    invoice_params = {
        "customer": stripe_cust_id,
        "auto_advance": True,  # Finaliza y envía automáticamente
        "collection_method": "send_invoice",
        "days_until_due": 30,
        "metadata": {
            "erp_invoice_id": str(invoice.id),
            "erp_invoice_number": invoice.invoice_number,
            "source": "erp_core",
        },
    }

    # Si hay suscripción con stripe_subscription_id, vincular
    if invoice.subscription_id:
        sub = db.query(Subscription).filter(Subscription.id == invoice.subscription_id).first()
        if sub and sub.stripe_subscription_id:
            invoice_params["subscription"] = sub.stripe_subscription_id

    try:
        s_inv = stripe.Invoice.create(**invoice_params)

        # Finalizar para generar el payment link
        s_inv = stripe.Invoice.finalize_invoice(s_inv["id"])

        # Actualizar BD local
        invoice.stripe_invoice_id = s_inv["id"]
        invoice.stripe_payment_intent_id = s_inv.get("payment_intent")
        if invoice.status == InvoiceStatus.draft:
            invoice.status = InvoiceStatus.issued
            invoice.issued_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        logger.info(
            f"Invoice pushed to Stripe: {invoice.invoice_number} → {s_inv['id']} | "
            f"URL: {s_inv.get('hosted_invoice_url')}"
        )

        return {
            "stripe_invoice_id": s_inv["id"],
            "hosted_invoice_url": s_inv.get("hosted_invoice_url"),
            "pdf_url": s_inv.get("invoice_pdf"),
            "status": s_inv.get("status"),
            "already_exists": False,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe invoice for {invoice.invoice_number}: {e}")
        raise


# ═══════════════════════════════════════════════════════════════
#  3. PAYMENT LINK VÍA CHECKOUT SESSION
# ═══════════════════════════════════════════════════════════════

def create_checkout_for_invoice(
    db: Session,
    invoice: Invoice,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Crea un Stripe Checkout Session para pagar una factura pendiente.
    Útil cuando no se quiere usar hosted_invoice_url (p.ej. para partners).

    Returns:
        {checkout_url, session_id}
    """
    _configure_stripe()
    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
    if not customer:
        raise ValueError("Customer not found")

    stripe_cust_id = ensure_stripe_customer(db, customer)

    # Si ya tiene stripe_invoice_id, usar el Stripe Invoice directamente
    if invoice.stripe_invoice_id:
        try:
            s_inv = stripe.Invoice.retrieve(invoice.stripe_invoice_id)
            if s_inv.get("hosted_invoice_url"):
                return {
                    "checkout_url": s_inv["hosted_invoice_url"],
                    "session_id": None,
                    "method": "hosted_invoice",
                }
        except stripe.error.StripeError:
            pass

    # Crear Checkout Session
    line_items = []
    for line in (invoice.lines_json or []):
        line_items.append({
            "price_data": {
                "currency": (invoice.currency or "USD").lower(),
                "product_data": {
                    "name": line.get("description", f"Factura {invoice.invoice_number}"),
                },
                "unit_amount": int((line.get("unit_price", 0)) * 100),
            },
            "quantity": line.get("qty", 1),
        })

    if not line_items:
        line_items.append({
            "price_data": {
                "currency": (invoice.currency or "USD").lower(),
                "product_data": {
                    "name": f"Factura {invoice.invoice_number}",
                },
                "unit_amount": int((invoice.total or 0) * 100),
            },
            "quantity": 1,
        })

    session = stripe.checkout.Session.create(
        customer=stripe_cust_id,
        mode="payment",
        line_items=line_items,
        success_url=success_url or f"{_app_url()}/tenant/portal?payment_success=true&invoice={invoice.invoice_number}",
        cancel_url=cancel_url or f"{_app_url()}/tenant/portal?payment_cancelled=true",
        metadata={
            "erp_invoice_id": str(invoice.id),
            "erp_invoice_number": invoice.invoice_number,
        },
    )

    return {
        "checkout_url": session.url,
        "session_id": session.id,
        "method": "checkout_session",
    }


# ═══════════════════════════════════════════════════════════════
#  4. SYNC SUBSCRIPTION QTY (DB → Stripe)
# ═══════════════════════════════════════════════════════════════

def sync_subscription_quantity(
    db: Session,
    subscription: Subscription,
    new_qty: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Actualiza la cantidad de usuarios (qty) en Stripe
    cuando cambia el user_count en el ERP.

    Si new_qty no se proporciona, usa subscription.user_count actual.
    """
    _configure_stripe()
    if not subscription.stripe_subscription_id:
        return {"error": "No stripe_subscription_id", "synced": False}

    qty = new_qty or subscription.user_count or 1

    try:
        s_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        items = s_sub.get("items", {}).get("data", [])
        if not items:
            return {"error": "No subscription items in Stripe", "synced": False}

        # Actualizar qty del primer item
        si_id = items[0]["id"]
        stripe.SubscriptionItem.modify(si_id, quantity=qty)

        # Actualizar BD local
        subscription.user_count = qty
        recalculate_subscription_monthly_amount(db, subscription, user_count=qty)
        subscription.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        logger.info(
            f"Subscription qty synced to Stripe: {subscription.stripe_subscription_id} → qty={qty}"
        )

        return {
            "synced": True,
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "quantity": qty,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error syncing qty: {e}")
        return {"error": str(e), "synced": False}


# ═══════════════════════════════════════════════════════════════
#  5. UPGRADE / CAMBIO DE PLAN (DB → Stripe)
# ═══════════════════════════════════════════════════════════════

def change_subscription_plan(
    db: Session,
    subscription: Subscription,
    new_plan: Plan,
) -> Dict[str, Any]:
    """
    Cambia el plan de una suscripción en Stripe.
    Proration automática.
    """
    _configure_stripe()
    if not subscription.stripe_subscription_id:
        return {"error": "No stripe_subscription_id", "changed": False}

    if not new_plan.stripe_price_id:
        return {"error": "New plan has no stripe_price_id", "changed": False}

    try:
        s_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        items = s_sub.get("items", {}).get("data", [])
        if not items:
            return {"error": "No subscription items", "changed": False}

        si_id = items[0]["id"]

        # Actualizar plan en Stripe con proration
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            items=[{
                "id": si_id,
                "price": new_plan.stripe_price_id,
                "quantity": subscription.user_count or 1,
            }],
            proration_behavior="create_prorations",
        )

        # Actualizar BD local
        old_plan = subscription.plan_name
        subscription.plan_name = new_plan.name
        recalculate_subscription_monthly_amount(
            db,
            subscription,
            plan=new_plan,
            user_count=subscription.user_count or 1,
        )
        subscription.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        logger.info(
            f"Plan changed: {old_plan} → {new_plan.name} "
            f"for sub {subscription.stripe_subscription_id}"
        )

        return {
            "changed": True,
            "old_plan": old_plan,
            "new_plan": new_plan.name,
            "new_price": subscription.monthly_amount,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error changing plan: {e}")
        return {"error": str(e), "changed": False}


# ═══════════════════════════════════════════════════════════════
#  6. GENERAR FACTURA MENSUAL DESDE CONSUMO
# ═══════════════════════════════════════════════════════════════

def generate_consumption_invoice(
    db: Session,
    subscription_id: int,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Genera una factura local basada en el consumo real de Stripe
    (plan + users). Luego la pushea a Stripe para cobro.

    Returns:
        {invoice_id, invoice_number, total, stripe_result}
    """
    _configure_stripe()
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise ValueError(f"Subscription {subscription_id} not found")

    customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
    if not customer:
        raise ValueError(f"Customer for sub {subscription_id} not found")

    plan = db.query(Plan).filter(Plan.name == sub.plan_name, Plan.is_active == True).first()
    period_start, period_end, billing_period_key = _resolve_billing_period(
        sub,
        period_start=period_start,
        period_end=period_end,
    )

    existing_invoice = None
    for candidate in db.query(Invoice).filter(
        Invoice.subscription_id == sub.id,
    ).order_by(Invoice.id.asc()).all():
        if candidate.status == InvoiceStatus.void:
            continue
        reference_dt = candidate.period_start or candidate.issued_at or candidate.created_at
        if candidate.billing_period_key == billing_period_key or (
            reference_dt and period_start <= reference_dt < period_end
        ):
            existing_invoice = candidate
            break
    if existing_invoice:
        return {
            "invoice_id": existing_invoice.id,
            "invoice_number": existing_invoice.invoice_number,
            "total": existing_invoice.total,
            "lines": existing_invoice.lines_json or [],
            "billing_period_key": existing_invoice.billing_period_key,
            "period_start": existing_invoice.period_start.isoformat() if existing_invoice.period_start else None,
            "period_end": existing_invoice.period_end.isoformat() if existing_invoice.period_end else None,
            "pricing_source": "existing_invoice",
            "stripe_result": {
                "stripe_invoice_id": existing_invoice.stripe_invoice_id,
                "status": existing_invoice.status.value if existing_invoice.status else None,
                "already_exists": True,
            },
        }

    lines = []
    total = 0.0
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    period_user_count, usage_source = _resolve_period_user_count(
        db,
        sub,
        customer=customer,
        period_start=period_start,
        period_end=period_end,
    )

    usage_meta = {}
    if _is_partner_billed_subscription(sub):
        period_user_count, usage_source, usage_meta = _resolve_partner_billable_user_count(
            db,
            sub,
            period_start=period_start,
            period_end=period_end,
            fallback_count=period_user_count,
        )

    pricing_snapshot = get_effective_plan_snapshot(
        db,
        sub,
        customer=customer,
        plan=plan,
        user_count=period_user_count,
    )

    if plan:
        base = pricing_snapshot["base_price"]
        lines.append({
            "description": f"Plan {plan.name} — base mensual",
            "qty": 1,
            "unit_price": base,
            "subtotal": base,
        })
        total += base

        # Usuarios adicionales
        extra = pricing_snapshot["extra_users"]
        price_per_user = pricing_snapshot["price_per_user"]
        if extra > 0 and price_per_user:
            user_cost = extra * price_per_user
            lines.append({
                "description": f"Usuarios adicionales ({extra} × ${price_per_user}/u)",
                "qty": extra,
                "unit_price": price_per_user,
                "subtotal": user_cost,
            })
            total += user_cost
    else:
        # Sin plan match — usar monto de suscripción
        total = sub.monthly_amount or 0
        lines.append({
            "description": f"Suscripción mensual — {sub.plan_name}",
            "qty": 1,
            "unit_price": total,
            "subtotal": total,
        })

    # Servicios adicionales recurrentes adquiridos por el cliente.
    addon_rows = (
        db.query(CustomerAddonSubscription)
        .filter(
            CustomerAddonSubscription.customer_id == customer.id,
            CustomerAddonSubscription.status == "active",
        )
        .all()
    )
    for addon in addon_rows:
        if addon.last_invoiced_year == now.year and addon.last_invoiced_month == now.month:
            continue

        qty = max(1, int(addon.quantity or 1))
        unit_price = float(addon.unit_price_monthly or 0)
        line_total = round(qty * unit_price, 6)
        item_name = addon.catalog_item.name if addon.catalog_item else (addon.service_code or "Add-on")

        lines.append({
            "description": f"Servicio adicional — {item_name}",
            "qty": qty,
            "unit_price": unit_price,
            "subtotal": line_total,
            "catalog_item_id": addon.catalog_item_id,
            "service_code": addon.service_code,
            "metadata_json": addon.metadata_json or {},
        })
        total += line_total
        addon.last_invoiced_year = now.year
        addon.last_invoiced_month = now.month

    # Determinar partner
    partner = None
    if sub.owner_partner_id:
        partner = db.query(Partner).filter(Partner.id == sub.owner_partner_id).first()

    # Crear invoice local
    from .stripe_sync import _next_invoice_number
    invoice = Invoice(
        invoice_number=_next_invoice_number(db),
        subscription_id=sub.id,
        customer_id=customer.id,
        partner_id=partner.id if partner else None,
        invoice_type=InvoiceType.SUBSCRIPTION,
        billing_mode=sub.billing_mode or BillingMode.JETURING_DIRECT_SUBSCRIPTION,
        issuer=InvoiceIssuer.JETURING,
        subtotal=total,
        tax_amount=0,
        total=total,
        currency=sub.currency or "USD",
        lines_json=lines,
        status=InvoiceStatus.draft,
        billing_period_key=billing_period_key,
        period_start=period_start,
        period_end=period_end,
    )
    db.add(invoice)
    db.flush()

    recalculate_subscription_monthly_amount(
        db,
        sub,
        customer=customer,
        plan=plan,
        user_count=max(1, int(sub.user_count or customer.user_count or pricing_snapshot["user_count"])),
    )

    # Push a Stripe
    if _is_partner_billed_subscription(sub):
        if invoice.status == InvoiceStatus.draft:
            invoice.status = InvoiceStatus.issued
            invoice.issued_at = datetime.now(timezone.utc).replace(tzinfo=None)
        note = "partner_billing_local_invoice_only"
        if note not in (invoice.notes or ""):
            invoice.notes = f"{(invoice.notes or '').strip()} {note}".strip()
        stripe_result = {
            "skipped": True,
            "reason": "partner_billed_subscription",
            "stripe_invoice_id": None,
        }
    else:
        try:
            stripe_result = push_invoice_to_stripe(db, invoice)
        except Exception as e:
            stripe_result = {"error": str(e), "stripe_invoice_id": None}
            logger.error(f"Error pushing invoice to Stripe: {e}")

    db.commit()

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "total": total,
        "lines": lines,
        "billing_period_key": billing_period_key,
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "pricing_source": pricing_snapshot["pricing_source"],
        "usage_source": usage_source,
        "usage_meta": usage_meta,
        "resolved_user_count": pricing_snapshot["user_count"],
        "stripe_result": stripe_result,
    }


def reconcile_billing_periods(db: Session) -> Dict[str, Any]:
    """
    Reconciliación idempotente por período:
    - enlaza/void duplicados locales del mismo período
    - genera factura local solo para suscripciones sin Stripe cuando falta el período actual
    """
    results = {
        "checked": 0,
        "generated": 0,
        "voided_duplicates": 0,
        "reissued_mismatches": 0,
        "pending_stripe_sync": 0,
        "details": [],
    }

    subscriptions = db.query(Subscription).filter(
        Subscription.status.in_([
            SubscriptionStatus.active,
            SubscriptionStatus.trialing,
            SubscriptionStatus.past_due,
        ])
    ).all()

    for sub in subscriptions:
        customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
        plan = db.query(Plan).filter(Plan.name == sub.plan_name, Plan.is_active == True).first()
        current_snapshot = get_effective_plan_snapshot(
            db,
            sub,
            customer=customer,
            plan=plan,
            user_count=sub.user_count or (customer.user_count if customer else None) or 1,
        )
        recalculate_subscription_monthly_amount(
            db,
            sub,
            customer=customer,
            plan=plan,
            user_count=current_snapshot["user_count"],
        )
        period_start, period_end, billing_period_key = _resolve_billing_period(sub)
        results["checked"] += 1

        invoices = db.query(Invoice).filter(
            Invoice.subscription_id == sub.id,
        ).order_by(Invoice.id.asc()).all()

        period_invoices = []
        for invoice in invoices:
            if invoice.billing_period_key == billing_period_key:
                period_invoices.append(invoice)
                continue

            reference_dt = invoice.period_start or invoice.issued_at or invoice.created_at
            if reference_dt and period_start <= reference_dt < period_end:
                period_invoices.append(invoice)

        valid_invoices = [inv for inv in period_invoices if inv.status != InvoiceStatus.void]
        stripe_backed = [inv for inv in valid_invoices if inv.stripe_invoice_id]
        manual_invoices = [inv for inv in valid_invoices if not inv.stripe_invoice_id]

        if stripe_backed and manual_invoices:
            for manual in manual_invoices:
                manual.status = InvoiceStatus.void
                note = f"replaced_by_stripe_period:{billing_period_key}"
                if note not in (manual.notes or ""):
                    manual.notes = f"{(manual.notes or '').strip()} {note}".strip()
                results["voided_duplicates"] += 1
            results["details"].append({
                "subscription_id": sub.id,
                "billing_period_key": billing_period_key,
                "action": "void_manual_duplicates",
            })
            continue

        if len(valid_invoices) > 1 and not stripe_backed:
            keeper = valid_invoices[0]
            for duplicate in valid_invoices[1:]:
                duplicate.status = InvoiceStatus.void
                note = f"duplicate_period_invoice:{billing_period_key}"
                if note not in (duplicate.notes or ""):
                    duplicate.notes = f"{(duplicate.notes or '').strip()} {note}".strip()
                results["voided_duplicates"] += 1
            results["details"].append({
                "subscription_id": sub.id,
                "billing_period_key": billing_period_key,
                "action": "void_duplicate_manual_periods",
                "keeper_invoice_id": keeper.id,
            })
            continue

        if valid_invoices:
            continue

        if sub.stripe_subscription_id:
            results["pending_stripe_sync"] += 1
            results["details"].append({
                "subscription_id": sub.id,
                "billing_period_key": billing_period_key,
                "action": "await_stripe_invoice_sync",
            })
            continue

        generate_consumption_invoice(
            db,
            sub.id,
            period_start=period_start,
            period_end=period_end,
        )
        results["generated"] += 1
        results["details"].append({
            "subscription_id": sub.id,
            "billing_period_key": billing_period_key,
            "action": "generated_local_invoice",
        })

    historical_candidates = (
        db.query(Invoice)
        .filter(
            Invoice.subscription_id.isnot(None),
            Invoice.invoice_type == InvoiceType.SUBSCRIPTION,
            Invoice.status.in_([InvoiceStatus.draft, InvoiceStatus.issued, InvoiceStatus.overdue]),
        )
        .order_by(Invoice.created_at.desc())
        .all()
    )

    for invoice in historical_candidates:
        if _invoice_has_metered_addons(invoice):
            continue

        subscription = db.query(Subscription).filter(Subscription.id == invoice.subscription_id).first()
        if not subscription:
            continue

        customer = db.query(Customer).filter(Customer.id == subscription.customer_id).first()
        snapshot = get_effective_plan_snapshot(
            db,
            subscription,
            customer=customer,
            plan=db.query(Plan).filter(Plan.name == subscription.plan_name, Plan.is_active == True).first(),
        )
        if not snapshot.get("partner_id"):
            continue

        invoice_period_start = invoice.period_start
        invoice_period_end = invoice.period_end
        if not invoice_period_start or not invoice_period_end:
            invoice_period_start, invoice_period_end, _ = _resolve_billing_period(subscription)
        invoice_period_key = invoice.billing_period_key or f"{invoice_period_start.date().isoformat()}__{invoice_period_end.date().isoformat()}"

        period_user_count, usage_source = _resolve_period_user_count(
            db,
            subscription,
            customer=customer,
            period_start=invoice_period_start,
            period_end=invoice_period_end,
        )
        expected_snapshot = get_effective_plan_snapshot(
            db,
            subscription,
            customer=customer,
            plan=snapshot["plan"],
            user_count=period_user_count,
        )
        expected_total = round(expected_snapshot["total"], 2)
        found_total = round(float(invoice.total or 0), 2)
        if abs(found_total - expected_total) <= 0.01:
            continue

        _void_mismatched_invoice(
            db,
            invoice,
            expected_total=expected_total,
            billing_period_key=invoice_period_key,
        )
        regenerate = generate_consumption_invoice(
            db,
            subscription.id,
            period_start=invoice_period_start,
            period_end=invoice_period_end,
        )
        results["reissued_mismatches"] += 1
        results["details"].append(
            {
                "subscription_id": subscription.id,
                "invoice_id": invoice.id,
                "billing_period_key": invoice_period_key,
                "action": "void_and_reissue_partner_mismatch",
                "expected_total": expected_total,
                "found_total": found_total,
                "usage_source": usage_source,
                "replacement_invoice_id": regenerate["invoice_id"],
            }
        )

    db.commit()
    return results
