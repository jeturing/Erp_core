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
    Subscription, Customer, Partner, Plan, BillingMode,
    get_db
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
from .roles import _require_admin as _require_admin_base

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])
logger = logging.getLogger(__name__)


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
    _require_admin_base(request, access_token)
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    inv.status = InvoiceStatus.paid
    inv.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if payload.stripe_payment_intent_id:
        inv.stripe_payment_intent_id = payload.stripe_payment_intent_id
    if payload.notes:
        inv.notes = payload.notes
    db.commit()
    return {"invoice_number": inv.invoice_number, "status": "paid"}


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
