"""
Invoices Routes — Épica 5: Facturas bidireccionales + Payment Links
- POST /api/invoices/generate-on-ready    → Genera factura cuando lead llega a tenant_ready
- POST /api/invoices/generate-consumption → Genera factura por consumo real (plan + usuarios)
- GET  /api/invoices                      → Lista facturas
- GET  /api/invoices/{id}                 → Detalle de factura
- POST /api/invoices/{id}/mark-paid       → Marcar como pagada
- POST /api/invoices/{id}/payment-link    → Genera payment link en Stripe
- POST /api/invoices/{id}/push-to-stripe  → Crea factura en Stripe desde BD
- POST /api/invoices/{id}/checkout        → Checkout Session para pago
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Cookie
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta, timezone
import logging

from ..models.database import (
    Invoice, InvoiceStatus, InvoiceType, InvoiceIssuer,
    Subscription, Customer, Partner, Plan, BillingMode, SubscriptionStatus,
    AuditEventRecord, CustomerAddonSubscription, SeatHighWater, SeatEvent, get_db
)
from ..services.stripe_billing import (
    push_invoice_to_stripe,
    create_checkout_for_invoice,
    generate_consumption_invoice,
    sync_subscription_quantity,
    change_subscription_plan,
    build_invoice_action_urls,
    fetch_stripe_invoice_links,
)
from ..services.pricing import get_effective_plan_snapshot
from .roles import _require_admin as _require_admin_base

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])
logger = logging.getLogger(__name__)

INTERNAL_BILLING_EMAIL_DOMAINS = {"sajet.us", "jeturing.com"}


def _is_internal_billing_email(value: Optional[str]) -> bool:
    email = (value or "").strip().lower()
    if "@" not in email:
        return False
    return email.split("@", 1)[1] in INTERNAL_BILLING_EMAIL_DOMAINS


def _resolve_preview_user_count(
    db: Session,
    sub: Subscription,
    customer: Optional[Customer],
    period_start: datetime,
    period_end: datetime,
) -> tuple[int, str, dict]:
    hwm = (
        db.query(SeatHighWater)
        .filter(
            SeatHighWater.subscription_id == sub.id,
            SeatHighWater.period_date >= period_start,
            SeatHighWater.period_date < period_end,
        )
        .order_by(SeatHighWater.hwm_count.desc(), SeatHighWater.period_date.desc())
        .first()
    )

    base_count = 1
    source = "live_user_count"
    if hwm and hwm.hwm_count is not None:
        base_count = max(1, int(hwm.hwm_count))
        source = "seat_high_water"
    else:
        base_count = max(1, int(sub.user_count or (customer.user_count if customer else 1) or 1))

    usage_meta = {
        "fallback_count": int(base_count),
        "internal_accounts_detected": 0,
    }

    if sub.owner_partner_id or sub.billing_mode in {BillingMode.PARTNER_DIRECT, BillingMode.PARTNER_PAYS_FOR_CLIENT}:
        internal_logins = (
            db.query(SeatEvent.odoo_login)
            .filter(
                SeatEvent.subscription_id == sub.id,
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
        usage_meta["internal_accounts_detected"] = len(internal_unique)
        base_count = max(1, base_count - len(internal_unique))
        source = "partner_excluding_internal_domains"

    return base_count, source, usage_meta


def _next_invoice_number(db: Session) -> str:
    """Genera siguiente número de factura: INV-YYYY-NNNN."""
    year = datetime.now(timezone.utc).replace(tzinfo=None).year
    last = db.query(Invoice).filter(
        Invoice.invoice_number.like(f"INV-{year}-%")
    ).order_by(Invoice.id.desc()).first()
    if last:
        seq = int(last.invoice_number.split("-")[-1]) + 1
    else:
        seq = 1
    return f"INV-{year}-{seq:04d}"


class InvoiceGenerateRequest(BaseModel):
    subscription_id: int
    include_setup: bool = True
    setup_fee: float = 0


class InvoiceMarkPaid(BaseModel):
    stripe_payment_intent_id: Optional[str] = None
    notes: Optional[str] = None
    mode: Optional[str] = "stripe_only"  # stripe_only | auditable_override
    override_reason: Optional[str] = None


@router.post("/generate-on-ready")
def generate_invoice_on_tenant_ready(
    payload: InvoiceGenerateRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Genera factura cuando Lead alcanza tenant_ready.
    - Direct: Factura de suscripción (Jeturing emite)
    - Partner A: Factura al cliente + 50/50 partner
    - Partner B (intercompany): Factura de Jeturing al Partner
    """
    _require_admin_base(request, access_token)
    sub = db.query(Subscription).filter(Subscription.id == payload.subscription_id).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")

    partner = None
    if sub.owner_partner_id:
        partner = db.query(Partner).filter(Partner.id == sub.owner_partner_id).first()

    billing_mode = sub.billing_mode or BillingMode.JETURING_DIRECT_SUBSCRIPTION
    invoices_created = []

    # ── Factura principal (suscripción) ──
    lines = []
    subtotal = sub.monthly_amount or 0

    lines.append({
        "description": f"Suscripción mensual — {sub.plan_name}",
        "qty": 1,
        "unit_price": subtotal,
        "subtotal": subtotal,
    })

    if payload.include_setup and payload.setup_fee > 0:
        lines.append({
            "description": "Cargo de setup inicial",
            "qty": 1,
            "unit_price": payload.setup_fee,
            "subtotal": payload.setup_fee,
        })
        subtotal += payload.setup_fee

    # Determinar quién emite
    if billing_mode == BillingMode.PARTNER_PAYS_FOR_CLIENT:
        # Escenario B: Jeturing emite factura intercompany al Partner
        issuer = InvoiceIssuer.JETURING
        inv_type = InvoiceType.INTERCOMPANY
    else:
        issuer = InvoiceIssuer.JETURING
        inv_type = InvoiceType.SUBSCRIPTION

    invoice = Invoice(
        invoice_number=_next_invoice_number(db),
        subscription_id=sub.id,
        customer_id=customer.id,
        partner_id=partner.id if partner else None,
        invoice_type=inv_type,
        billing_mode=billing_mode,
        issuer=issuer,
        subtotal=subtotal,
        tax_amount=0,
        total=subtotal,
        currency=sub.currency or "USD",
        lines_json=lines,
        status=InvoiceStatus.issued,
        issued_at=datetime.now(timezone.utc).replace(tzinfo=None),
        due_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
    )
    db.add(invoice)
    db.flush()
    invoices_created.append({
        "invoice_number": invoice.invoice_number,
        "type": inv_type.value,
        "issuer": issuer.value,
        "total": subtotal,
    })

    # ── Escenario B: factura intercompany adicional si Partner cobra ──
    if billing_mode == BillingMode.PARTNER_PAYS_FOR_CLIENT and partner:
        ic_lines = [{
            "description": f"Intercompany — Pago de {partner.company_name} por {customer.company_name or customer.full_name}",
            "qty": 1,
            "unit_price": subtotal,
            "subtotal": subtotal,
        }]
        ic_invoice = Invoice(
            invoice_number=_next_invoice_number(db),
            subscription_id=sub.id,
            customer_id=customer.id,
            partner_id=partner.id,
            invoice_type=InvoiceType.INTERCOMPANY,
            billing_mode=billing_mode,
            issuer=InvoiceIssuer.PARTNER,
            subtotal=subtotal,
            tax_amount=0,
            total=subtotal,
            currency=sub.currency or "USD",
            lines_json=ic_lines,
            status=InvoiceStatus.issued,
            issued_at=datetime.now(timezone.utc).replace(tzinfo=None),
            due_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
        )
        db.add(ic_invoice)
        invoices_created.append({
            "invoice_number": ic_invoice.invoice_number,
            "type": "intercompany_partner",
            "issuer": "partner",
            "total": subtotal,
        })

    db.commit()

    return {
        "subscription_id": sub.id,
        "billing_mode": billing_mode.value,
        "invoices_created": invoices_created,
    }


@router.get("")
def list_invoices(
    request: Request,
    access_token: str = Cookie(None),
    status: Optional[str] = None,
    subscription_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Lista facturas con filtros opcionales."""
    _require_admin_base(request, access_token)
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    if subscription_id:
        q = q.filter(Invoice.subscription_id == subscription_id)
    if customer_id:
        q = q.filter(Invoice.customer_id == customer_id)
    if partner_id:
        q = q.filter(Invoice.partner_id == partner_id)

    total = q.count()
    invoices = q.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()

    # Precargar relaciones customer para evitar N+1
    items = []
    for inv in invoices:
        customer = db.query(Customer).filter(Customer.id == inv.customer_id).first() if inv.customer_id else None
        item = {
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "subscription_id": inv.subscription_id,
            "customer_id": inv.customer_id,
            "partner_id": inv.partner_id,
            "company_name": customer.company_name if customer else None,
            "email": customer.email if customer else None,
            "subdomain": customer.subdomain if customer else None,
            "invoice_type": inv.invoice_type.value if inv.invoice_type else None,
            "billing_mode": inv.billing_mode.value if inv.billing_mode else None,
            "issuer": inv.issuer.value if inv.issuer else None,
            "subtotal": inv.subtotal or 0,
            "tax_amount": inv.tax_amount or 0,
            "total": inv.total or 0,
            "currency": inv.currency,
            "stripe_invoice_id": inv.stripe_invoice_id,
            "stripe_payment_intent_id": inv.stripe_payment_intent_id,
            "billing_period_key": inv.billing_period_key,
            "period_start": inv.period_start.isoformat() if inv.period_start else None,
            "period_end": inv.period_end.isoformat() if inv.period_end else None,
            "status": inv.status.value if inv.status else None,
            "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
            "due_date": inv.due_date.isoformat() if inv.due_date else None,
            "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "notes": inv.notes,
            "pdf_url": None,
            "hosted_url": None,
            "download_url": None,
            "payment_url": None,
            "view_url": None,
            "preferred_action": None,
        }
        if inv.stripe_invoice_id:
            try:
                item.update(fetch_stripe_invoice_links(inv.stripe_invoice_id))
            except Exception:
                item.update(build_invoice_action_urls(status=inv.status))
        else:
            item.update(build_invoice_action_urls(status=inv.status))
        items.append(item)

    return {
        "total": total,
        "invoices": items,
    }


@router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """Detalle completo de una factura."""
    _require_admin_base(request, access_token)
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    item = {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "subscription_id": inv.subscription_id,
        "customer_id": inv.customer_id,
        "partner_id": inv.partner_id,
        "invoice_type": inv.invoice_type.value if inv.invoice_type else None,
        "billing_mode": inv.billing_mode.value if inv.billing_mode else None,
        "issuer": inv.issuer.value if inv.issuer else None,
        "subtotal": inv.subtotal,
        "tax_amount": inv.tax_amount,
        "total": inv.total,
        "currency": inv.currency,
        "lines": inv.lines_json,
        "stripe_invoice_id": inv.stripe_invoice_id,
        "stripe_payment_intent_id": inv.stripe_payment_intent_id,
        "billing_period_key": inv.billing_period_key,
        "period_start": inv.period_start.isoformat() if inv.period_start else None,
        "period_end": inv.period_end.isoformat() if inv.period_end else None,
        "status": inv.status.value if inv.status else None,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "notes": inv.notes,
        "pdf_url": None,
        "hosted_url": None,
        "download_url": None,
        "payment_url": None,
        "view_url": None,
        "preferred_action": None,
    }
    if inv.stripe_invoice_id:
        try:
            item.update(fetch_stripe_invoice_links(inv.stripe_invoice_id))
        except Exception:
            item.update(build_invoice_action_urls(status=inv.status))
    else:
        item.update(build_invoice_action_urls(status=inv.status))
    return item


@router.post("/{invoice_id}/mark-paid")
def mark_invoice_paid(
    invoice_id: int,
    payload: InvoiceMarkPaid,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """Marca una factura como pagada."""
    actor = _require_admin_base(request, access_token)
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    mode = (payload.mode or "stripe_only").strip().lower()
    if mode not in {"stripe_only", "auditable_override"}:
        raise HTTPException(400, "mode inválido. Usa stripe_only o auditable_override")

    if mode == "stripe_only" and not (payload.stripe_payment_intent_id or inv.stripe_payment_intent_id or inv.stripe_invoice_id):
        raise HTTPException(400, "Stripe-only mode requiere stripe_payment_intent_id o stripe_invoice_id")

    if mode == "auditable_override" and not (payload.override_reason or "").strip():
        raise HTTPException(400, "override_reason es obligatorio en auditable_override")

    inv.status = InvoiceStatus.paid
    inv.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if payload.stripe_payment_intent_id:
        inv.stripe_payment_intent_id = payload.stripe_payment_intent_id
    note_parts = []
    if payload.notes:
        note_parts.append(payload.notes.strip())
    if mode == "auditable_override":
        note_parts.append(f"auditable_override_reason={payload.override_reason}")
    if note_parts:
        merged = " | ".join([p for p in note_parts if p])
        inv.notes = f"{(inv.notes or '').strip()} {merged}".strip()

    db.add(AuditEventRecord(
        event_type="invoice_mark_paid",
        actor_username=(actor or {}).get("sub", "admin"),
        actor_role=(actor or {}).get("role", "admin"),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        resource=f"invoice:{inv.id}",
        action=mode,
        status="success",
        details={
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "mode": mode,
            "override_reason": payload.override_reason,
            "stripe_payment_intent_id": payload.stripe_payment_intent_id or inv.stripe_payment_intent_id,
        },
    ))

    db.commit()
    return {
        "success": True,
        "data": {
            "invoice_number": inv.invoice_number,
            "status": "paid",
            "mode": mode,
        },
        "meta": {},
    }


@router.get("/reconciliation/summary")
def reconciliation_summary(
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """Resumen de conciliación: Stripe automático vs pago manual/override."""
    _require_admin_base(request, access_token)

    total = db.query(Invoice).count()
    stripe_backed = db.query(Invoice).filter(Invoice.stripe_invoice_id.isnot(None)).count()
    paid = db.query(Invoice).filter(Invoice.status == InvoiceStatus.paid).count()
    paid_without_stripe = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.paid,
        Invoice.stripe_invoice_id.is_(None),
        Invoice.stripe_payment_intent_id.is_(None),
    ).count()
    auditable_overrides = db.query(Invoice).filter(
        Invoice.status == InvoiceStatus.paid,
        Invoice.notes.ilike("%auditable_override_reason=%"),
    ).count()

    return {
        "success": True,
        "data": {
            "total_invoices": total,
            "stripe_backed_invoices": stripe_backed,
            "manual_invoices": max(0, total - stripe_backed),
            "paid_invoices": paid,
            "paid_without_stripe_trace": paid_without_stripe,
            "auditable_overrides": auditable_overrides,
        },
        "meta": {
            "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        },
    }


# ═══════════════════════════════════════════════════════════════
#  PAYMENT LINK — genera enlace de pago Stripe
# ═══════════════════════════════════════════════════════════════

@router.post("/{invoice_id}/payment-link")
def get_payment_link(
    invoice_id: int,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Genera/obtiene el payment link de Stripe para una factura.
    Si la factura no existe en Stripe, la crea primero.
    Retorna la URL de pago hosted de Stripe.
    """
    _require_admin_base(request, access_token)
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    if inv.status == InvoiceStatus.paid:
        raise HTTPException(400, "La factura ya está pagada")

    try:
        result = push_invoice_to_stripe(db, inv)
        return {
            "invoice_number": inv.invoice_number,
            "payment_url": result.get("hosted_invoice_url"),
            "pdf_url": result.get("pdf_url"),
            "stripe_invoice_id": result.get("stripe_invoice_id"),
            "status": result.get("status"),
        }
    except Exception as e:
        logger.error(f"Error generating payment link: {e}")
        raise HTTPException(500, f"Error generando enlace de pago: {str(e)}")


@router.post("/{invoice_id}/push-to-stripe")
def push_to_stripe(
    invoice_id: int,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Crea la factura en Stripe desde la BD local (push bidireccional).
    """
    _require_admin_base(request, access_token)
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    try:
        result = push_invoice_to_stripe(db, inv)
        return {
            "invoice_number": inv.invoice_number,
            **result,
        }
    except Exception as e:
        logger.error(f"Error pushing invoice to Stripe: {e}")
        raise HTTPException(500, f"Error enviando factura a Stripe: {str(e)}")


class CheckoutRequest(BaseModel):
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.post("/{invoice_id}/checkout")
def create_checkout(
    invoice_id: int,
    request: Request,
    access_token: str = Cookie(None),
    payload: CheckoutRequest = CheckoutRequest(),
    db: Session = Depends(get_db),
):
    """
    Crea un Stripe Checkout Session para pagar una factura.
    Alternativa al hosted_invoice_url — útil para partners.
    """
    _require_admin_base(request, access_token)
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")

    if inv.status == InvoiceStatus.paid:
        raise HTTPException(400, "La factura ya está pagada")

    try:
        result = create_checkout_for_invoice(
            db, inv,
            success_url=payload.success_url,
            cancel_url=payload.cancel_url,
        )
        return {
            "invoice_number": inv.invoice_number,
            **result,
        }
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(500, f"Error creando checkout: {str(e)}")


# ═══════════════════════════════════════════════════════════════
#  FACTURA POR CONSUMO REAL (plan + usuarios)
# ═══════════════════════════════════════════════════════════════

class ConsumptionInvoiceRequest(BaseModel):
    subscription_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class PartnerMonthlyInvoiceRequest(BaseModel):
    partner_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None


@router.post("/generate-partner-monthly-preview")
def preview_partner_monthly_invoice(
    payload: PartnerMonthlyInvoiceRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """Preview consolidado mensual del partner sin emitir facturas."""
    _require_admin_base(request, access_token)

    partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    period_start_dt = datetime.combine(payload.period_start, time.min) if payload.period_start else datetime.now(timezone.utc).replace(tzinfo=None).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end_dt = datetime.combine(payload.period_end, time.min) if payload.period_end else (period_start_dt + timedelta(days=32)).replace(day=1)

    subscriptions = db.query(Subscription).filter(
        Subscription.owner_partner_id == partner.id,
        Subscription.status.in_([
            SubscriptionStatus.active,
            SubscriptionStatus.trialing,
            SubscriptionStatus.past_due,
        ]),
    ).all()

    if not subscriptions:
        return {
            "success": True,
            "data": {
                "partner_id": partner.id,
                "partner_name": partner.company_name,
                "tenants": [],
                "totals": {
                    "subtotal": 0,
                    "tax": 0,
                    "total": 0,
                    "currency": "USD",
                },
            },
            "meta": {
                "period_start": period_start_dt.isoformat(),
                "period_end": period_end_dt.isoformat(),
                "tenants_count": 0,
            },
        }

    tenants = []
    consolidated_total = 0.0

    for sub in subscriptions:
        customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
        if not customer:
            continue

        plan = db.query(Plan).filter(Plan.name == sub.plan_name, Plan.is_active == True).first()
        user_count, usage_source, usage_meta = _resolve_preview_user_count(
            db,
            sub,
            customer,
            period_start_dt,
            period_end_dt,
        )

        pricing_snapshot = get_effective_plan_snapshot(
            db,
            sub,
            customer=customer,
            plan=plan,
            user_count=user_count,
        )

        lines = []
        tenant_total = 0.0

        if plan:
            base = float(pricing_snapshot.get("base_price") or 0)
            lines.append({
                "component": "base_plan",
                "description": f"Plan {plan.name} — base mensual",
                "qty": 1,
                "unit_price": round(base, 2),
                "subtotal": round(base, 2),
            })
            tenant_total += base

            extra = int(pricing_snapshot.get("extra_users") or 0)
            ppu = float(pricing_snapshot.get("price_per_user") or 0)
            if extra > 0 and ppu > 0:
                extra_total = round(extra * ppu, 2)
                lines.append({
                    "component": "extra_users",
                    "description": f"Usuarios adicionales ({extra} × ${ppu}/u)",
                    "qty": extra,
                    "unit_price": round(ppu, 2),
                    "subtotal": extra_total,
                })
                tenant_total += extra_total
        else:
            monthly = float(sub.monthly_amount or 0)
            lines.append({
                "component": "subscription_fallback",
                "description": f"Suscripción mensual — {sub.plan_name}",
                "qty": 1,
                "unit_price": round(monthly, 2),
                "subtotal": round(monthly, 2),
            })
            tenant_total += monthly

        addon_rows = (
            db.query(CustomerAddonSubscription)
            .filter(
                CustomerAddonSubscription.customer_id == customer.id,
                CustomerAddonSubscription.status == "active",
            )
            .all()
        )
        for addon in addon_rows:
            qty = max(1, int(addon.quantity or 1))
            unit_price = float(addon.unit_price_monthly or 0)
            line_total = round(qty * unit_price, 2)
            item_name = addon.catalog_item.name if addon.catalog_item else (addon.service_code or "Add-on")
            lines.append({
                "component": "addon",
                "description": f"Servicio adicional — {item_name}",
                "qty": qty,
                "unit_price": round(unit_price, 2),
                "subtotal": line_total,
                "service_code": addon.service_code,
            })
            tenant_total += line_total

        tenant_total = round(tenant_total, 2)
        consolidated_total += tenant_total

        tenants.append({
            "subscription_id": sub.id,
            "customer_id": customer.id,
            "customer_name": customer.company_name or customer.full_name or customer.subdomain,
            "subdomain": customer.subdomain,
            "currency": sub.currency or "USD",
            "resolved_user_count": int(pricing_snapshot.get("user_count") or user_count),
            "usage_source": usage_source,
            "usage_meta": usage_meta,
            "pricing_source": pricing_snapshot.get("pricing_source"),
            "lines": lines,
            "tenant_total": tenant_total,
        })

    consolidated_total = round(consolidated_total, 2)

    return {
        "success": True,
        "data": {
            "partner_id": partner.id,
            "partner_name": partner.company_name,
            "tenants": tenants,
            "totals": {
                "subtotal": consolidated_total,
                "tax": 0,
                "total": consolidated_total,
                "currency": "USD",
            },
        },
        "meta": {
            "period_start": period_start_dt.isoformat(),
            "period_end": period_end_dt.isoformat(),
            "tenants_count": len(tenants),
        },
    }


@router.post("/generate-consumption")
def generate_consumption(
    payload: ConsumptionInvoiceRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Genera factura basada en consumo real: plan base + usuarios adicionales.
    La crea en BD local Y en Stripe simultáneamente.
    """
    _require_admin_base(request, access_token)
    try:
        period_start_dt = datetime.combine(payload.period_start, time.min) if payload.period_start else None
        period_end_dt = datetime.combine(payload.period_end, time.min) if payload.period_end else None
        result = generate_consumption_invoice(
            db,
            payload.subscription_id,
            period_start=period_start_dt,
            period_end=period_end_dt,
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.error(f"Error generating consumption invoice: {e}")
        raise HTTPException(500, f"Error generando factura: {str(e)}")


@router.post("/generate-partner-monthly")
def generate_partner_monthly_invoice(
    payload: PartnerMonthlyInvoiceRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Cierre mensual consolidado para partner:
    - genera/actualiza facturas por tenant (local)
    - crea factura consolidada partner (intercompany)
    """
    _require_admin_base(request, access_token)

    partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    period_start_dt = datetime.combine(payload.period_start, time.min) if payload.period_start else None
    period_end_dt = datetime.combine(payload.period_end, time.min) if payload.period_end else None

    subscriptions = db.query(Subscription).filter(
        Subscription.owner_partner_id == partner.id,
        Subscription.status.in_([
            SubscriptionStatus.active,
            SubscriptionStatus.trialing,
            SubscriptionStatus.past_due,
        ]),
    ).all()

    if not subscriptions:
        raise HTTPException(400, "El partner no tiene suscripciones activas para facturar")

    tenant_lines = []
    total = 0.0
    generated_invoice_ids = []

    for sub in subscriptions:
        result = generate_consumption_invoice(
            db,
            sub.id,
            period_start=period_start_dt,
            period_end=period_end_dt,
        )

        customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
        company_label = (customer.company_name if customer else None) or (customer.subdomain if customer else None) or f"tenant-{sub.id}"
        line_total = round(float(result.get("total") or 0), 2)
        total += line_total
        generated_invoice_ids.append(result.get("invoice_id"))
        tenant_lines.append({
            "description": f"Tenant {company_label} ({customer.subdomain if customer else 'n/a'})",
            "qty": 1,
            "unit_price": line_total,
            "subtotal": line_total,
            "metadata": {
                "subscription_id": sub.id,
                "tenant_invoice_id": result.get("invoice_id"),
                "resolved_user_count": result.get("resolved_user_count"),
                "usage_source": result.get("usage_source"),
                "usage_meta": result.get("usage_meta") or {},
            },
        })

    customer_id_for_invoice = partner.customer_id or subscriptions[0].customer_id

    consolidated = Invoice(
        invoice_number=_next_invoice_number(db),
        subscription_id=None,
        customer_id=customer_id_for_invoice,
        partner_id=partner.id,
        invoice_type=InvoiceType.INTERCOMPANY,
        billing_mode=BillingMode.PARTNER_PAYS_FOR_CLIENT,
        issuer=InvoiceIssuer.JETURING,
        subtotal=round(total, 2),
        tax_amount=0,
        total=round(total, 2),
        currency="USD",
        lines_json=tenant_lines,
        status=InvoiceStatus.issued,
        issued_at=datetime.now(timezone.utc).replace(tzinfo=None),
        due_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=15),
        notes="partner_monthly_consolidated_invoice",
    )
    db.add(consolidated)
    db.commit()
    db.refresh(consolidated)

    return {
        "success": True,
        "data": {
            "partner_id": partner.id,
            "partner_name": partner.company_name,
            "consolidated_invoice_id": consolidated.id,
            "consolidated_invoice_number": consolidated.invoice_number,
            "total": consolidated.total,
            "currency": consolidated.currency,
            "tenant_invoice_ids": [inv_id for inv_id in generated_invoice_ids if inv_id],
            "tenants_count": len(tenant_lines),
        },
        "meta": {
            "period_start": period_start_dt.isoformat() if period_start_dt else None,
            "period_end": period_end_dt.isoformat() if period_end_dt else None,
        },
    }


# ═══════════════════════════════════════════════════════════════
#  SYNC BIDIRECCIONAL — qty y plan
# ═══════════════════════════════════════════════════════════════

class SyncQtyRequest(BaseModel):
    subscription_id: int
    new_quantity: Optional[int] = None


@router.post("/sync-quantity")
def sync_qty_to_stripe(
    payload: SyncQtyRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Sincroniza la cantidad de usuarios de una suscripción a Stripe (DB → Stripe).
    Se llama cuando se agregan/eliminan usuarios en el ERP.
    """
    _require_admin_base(request, access_token)
    sub = db.query(Subscription).filter(Subscription.id == payload.subscription_id).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    result = sync_subscription_quantity(db, sub, payload.new_quantity)
    return result


class ChangePlanRequest(BaseModel):
    subscription_id: int
    new_plan_name: str


@router.post("/change-plan")
def change_plan(
    payload: ChangePlanRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Cambia el plan de una suscripción en Stripe con proration.
    """
    _require_admin_base(request, access_token)
    sub = db.query(Subscription).filter(Subscription.id == payload.subscription_id).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    plan = db.query(Plan).filter(
        Plan.name == payload.new_plan_name,
        Plan.is_active == True,
    ).first()
    if not plan:
        raise HTTPException(404, f"Plan '{payload.new_plan_name}' not found")

    result = change_subscription_plan(db, sub, plan)
    return result
