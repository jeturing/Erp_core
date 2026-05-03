"""
Commissions Routes — Tracking de comisiones 50/50
Cláusula 8 del contrato: Split sobre Ingresos Netos
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Request
from pydantic import BaseModel

from ..models.database import (
    Commission, Partner, Subscription, Lead, SessionLocal,
    CommissionStatus,
)
from .roles import _require_admin

router = APIRouter(prefix="/api/commissions", tags=["Commissions"])


# ── DTOs ──

class CommissionCreate(BaseModel):
    partner_id: int
    subscription_id: Optional[int] = None
    lead_id: Optional[int] = None
    period_start: str  # ISO date
    period_end: str
    gross_revenue: float = 0
    deductions: Optional[dict] = None  # {fees, refunds, chargebacks, taxes}
    notes: Optional[str] = None


class CommissionUpdate(BaseModel):
    status: Optional[str] = None
    gross_revenue: Optional[float] = None
    deductions: Optional[dict] = None
    notes: Optional[str] = None
    payment_reference: Optional[str] = None


def _commission_to_dict(c: Commission) -> dict:
    return {
        "id": c.id,
        "partner_id": c.partner_id,
        "subscription_id": c.subscription_id,
        "lead_id": c.lead_id,
        "period_start": c.period_start.isoformat() if c.period_start else None,
        "period_end": c.period_end.isoformat() if c.period_end else None,
        "gross_revenue": c.gross_revenue,
        "net_revenue": c.net_revenue,
        "deductions": json.loads(c.deductions_json) if c.deductions_json else {},
        "partner_amount": c.partner_amount,
        "jeturing_amount": c.jeturing_amount,
        "status": c.status.value if c.status else None,
        "paid_at": c.paid_at.isoformat() if c.paid_at else None,
        "payment_reference": c.payment_reference,
        "notes": c.notes,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _calculate_commission(gross: float, deductions: dict, rate: float) -> dict:
    """Calcula comisión según Cláusula 8: Ingresos Netos = Bruto - Deducciones."""
    fees = deductions.get("fees", 0)
    refunds = deductions.get("refunds", 0)
    chargebacks = deductions.get("chargebacks", 0)
    taxes = deductions.get("taxes", 0)
    total_deductions = fees + refunds + chargebacks + taxes

    net = gross - total_deductions
    if net < 0:
        net = 0

    partner_amount = round(net * (rate / 100), 2)
    jeturing_amount = round(net - partner_amount, 2)

    return {
        "net_revenue": round(net, 2),
        "partner_amount": partner_amount,
        "jeturing_amount": jeturing_amount,
    }


# ── Routes ──

@router.get("")
async def list_commissions(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    partner_id: Optional[int] = None,
    status_filter: Optional[str] = None,
):
    """Lista comisiones con filtros opcionales."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(Commission)
        if partner_id:
            q = q.filter(Commission.partner_id == partner_id)
        if status_filter:
            try:
                q = q.filter(Commission.status == CommissionStatus(status_filter))
            except ValueError:
                pass

        comms = q.order_by(Commission.created_at.desc()).all()
        items = []
        for c in comms:
            d = _commission_to_dict(c)
            partner = db.query(Partner).filter(Partner.id == c.partner_id).first()
            d["partner_name"] = partner.company_name if partner else "—"
            items.append(d)

        # Resumen
        total_partner = sum(i["partner_amount"] or 0 for i in items)
        total_jeturing = sum(i["jeturing_amount"] or 0 for i in items)
        total_pending = sum(i["partner_amount"] or 0 for i in items if i["status"] == "pending")

        return {
            "items": items,
            "total": len(items),
            "summary": {
                "total_partner_amount": round(total_partner, 2),
                "total_jeturing_amount": round(total_jeturing, 2),
                "total_pending_payout": round(total_pending, 2),
                "total_gross": round(sum(i["gross_revenue"] or 0 for i in items), 2),
            },
        }
    finally:
        db.close()


@router.get("/{commission_id}")
async def get_commission(
    commission_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        c = db.query(Commission).filter(Commission.id == commission_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Comisión no encontrada")

        data = _commission_to_dict(c)
        partner = db.query(Partner).filter(Partner.id == c.partner_id).first()
        data["partner_name"] = partner.company_name if partner else "—"
        return data
    finally:
        db.close()


@router.post("")
async def create_commission(
    payload: CommissionCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Crea una comisión con cálculo automático de split 50/50."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        deductions = payload.deductions or {}
        calc = _calculate_commission(payload.gross_revenue, deductions, partner.commission_rate)

        try:
            p_start = datetime.fromisoformat(payload.period_start)
            p_end = datetime.fromisoformat(payload.period_end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido (ISO 8601)")

        commission = Commission(
            partner_id=payload.partner_id,
            subscription_id=payload.subscription_id,
            lead_id=payload.lead_id,
            period_start=p_start,
            period_end=p_end,
            gross_revenue=payload.gross_revenue,
            net_revenue=calc["net_revenue"],
            deductions_json=json.dumps(deductions),
            partner_amount=calc["partner_amount"],
            jeturing_amount=calc["jeturing_amount"],
            status=CommissionStatus.pending,
            notes=payload.notes,
        )
        db.add(commission)
        db.commit()
        db.refresh(commission)

        return {"message": "Comisión creada", "commission": _commission_to_dict(commission)}
    finally:
        db.close()


@router.put("/{commission_id}")
async def update_commission(
    commission_id: int,
    payload: CommissionUpdate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Actualiza una comisión (estado, montos, referencia de pago)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        c = db.query(Commission).filter(Commission.id == commission_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Comisión no encontrada")

        partner = db.query(Partner).filter(Partner.id == c.partner_id).first()

        changes = []
        for field, value in payload.dict(exclude_unset=True).items():
            if field == "status" and value:
                try:
                    new_status = CommissionStatus(value)
                    if new_status == CommissionStatus.paid:
                        c.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    value = new_status
                except ValueError:
                    continue
                setattr(c, field, value)
                changes.append(field)
            elif field == "deductions" and value:
                c.deductions_json = json.dumps(value)
                # Recalcular
                rate = partner.commission_rate if partner else 50.0
                calc = _calculate_commission(c.gross_revenue, value, rate)
                c.net_revenue = calc["net_revenue"]
                c.partner_amount = calc["partner_amount"]
                c.jeturing_amount = calc["jeturing_amount"]
                changes.extend(["deductions", "net_revenue", "partner_amount", "jeturing_amount"])
            elif field == "gross_revenue" and value is not None:
                c.gross_revenue = value
                deductions = json.loads(c.deductions_json) if c.deductions_json else {}
                rate = partner.commission_rate if partner else 50.0
                calc = _calculate_commission(value, deductions, rate)
                c.net_revenue = calc["net_revenue"]
                c.partner_amount = calc["partner_amount"]
                c.jeturing_amount = calc["jeturing_amount"]
                changes.extend(["gross_revenue", "net_revenue", "partner_amount", "jeturing_amount"])
            else:
                old = getattr(c, field, None)
                if old != value:
                    setattr(c, field, value)
                    changes.append(field)

        db.commit()
        db.refresh(c)

        return {"message": "Comisión actualizada", "changes": changes, "commission": _commission_to_dict(c)}
    finally:
        db.close()


@router.post("/{commission_id}/approve")
async def approve_commission(
    commission_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Aprueba una comisión pendiente."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        c = db.query(Commission).filter(Commission.id == commission_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Comisión no encontrada")

        c.status = CommissionStatus.approved
        db.commit()

        return {"message": "Comisión aprobada", "commission": _commission_to_dict(c)}
    finally:
        db.close()


@router.post("/{commission_id}/pay")
async def mark_commission_paid(
    commission_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    payment_reference: Optional[str] = None,
):
    """Marca una comisión como pagada."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        c = db.query(Commission).filter(Commission.id == commission_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="Comisión no encontrada")

        c.status = CommissionStatus.paid
        c.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if payment_reference:
            c.payment_reference = payment_reference
        db.commit()

        return {"message": "Comisión marcada como pagada", "commission": _commission_to_dict(c)}
    finally:
        db.close()
