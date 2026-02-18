"""
Invoices Routes — Épica 5: Facturas en TENANT_READY + Intercompany
- POST /api/invoices/generate-on-ready → Genera factura cuando lead llega a tenant_ready
- GET  /api/invoices                   → Lista facturas
- GET  /api/invoices/{id}              → Detalle de factura
- POST /api/invoices/{id}/mark-paid    → Marcar como pagada
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from ..models.database import (
    Invoice, InvoiceStatus, InvoiceType, InvoiceIssuer,
    Subscription, Customer, Partner, Plan, BillingMode,
    get_db
)

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])
logger = logging.getLogger(__name__)


def _next_invoice_number(db: Session) -> str:
    """Genera siguiente número de factura: INV-YYYY-NNNN."""
    year = datetime.utcnow().year
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
    db: Session = Depends(get_db),
):
    """
    Genera factura cuando Lead alcanza tenant_ready.
    - Direct: Factura de suscripción (Jeturing emite)
    - Partner A: Factura al cliente + 50/50 partner
    - Partner B (intercompany): Factura de Jeturing al Partner
    """
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
        issued_at=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=30),
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
            issued_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
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
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Lista facturas con filtros opcionales."""
    q = db.query(Invoice)
    if status:
        q = q.filter(Invoice.status == status)
    if customer_id:
        q = q.filter(Invoice.customer_id == customer_id)
    if partner_id:
        q = q.filter(Invoice.partner_id == partner_id)

    total = q.count()
    invoices = q.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_id": inv.customer_id,
                "partner_id": inv.partner_id,
                "invoice_type": inv.invoice_type.value if inv.invoice_type else None,
                "billing_mode": inv.billing_mode.value if inv.billing_mode else None,
                "issuer": inv.issuer.value if inv.issuer else None,
                "total": inv.total,
                "currency": inv.currency,
                "status": inv.status.value if inv.status else None,
                "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
            }
            for inv in invoices
        ],
    }


@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Detalle completo de una factura."""
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return {
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
        "status": inv.status.value if inv.status else None,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "notes": inv.notes,
    }


@router.post("/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: int, payload: InvoiceMarkPaid, db: Session = Depends(get_db)):
    """Marca una factura como pagada."""
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    inv.status = InvoiceStatus.paid
    inv.paid_at = datetime.utcnow()
    if payload.stripe_payment_intent_id:
        inv.stripe_payment_intent_id = payload.stripe_payment_intent_id
    if payload.notes:
        inv.notes = payload.notes
    db.commit()
    return {"invoice_number": inv.invoice_number, "status": "paid"}
