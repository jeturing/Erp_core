"""
Settlements Routes — Épica 6: Settlement 50/50 Partner ↔ Jeturing
- POST /api/settlements/create-period → Crear período de settlement
- GET  /api/settlements                → Lista períodos
- GET  /api/settlements/{id}           → Detalle con líneas
- POST /api/settlements/{id}/close     → Cerrar período y calcular neto
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timezone
import logging

from ..models.database import (
    SettlementPeriod, SettlementLine, SettlementStatus,
    Invoice, InvoiceStatus, Partner,
    get_db
)

router = APIRouter(prefix="/api/settlements", tags=["Settlements"])
logger = logging.getLogger(__name__)

JETURING_SHARE = 0.50
PARTNER_SHARE = 0.50


class CreatePeriodRequest(BaseModel):
    partner_id: int
    period_start: date
    period_end: date
    notes: Optional[str] = None


class ClosePeriodRequest(BaseModel):
    adjustments: float = 0
    notes: Optional[str] = None


@router.post("/create-period")
def create_settlement_period(
    payload: CreatePeriodRequest,
    db: Session = Depends(get_db),
):
    """
    Crea un período de liquidación para un partner.
    Típicamente mensual: 1er día → último día del mes.
    """
    partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    existing = db.query(SettlementPeriod).filter(
        SettlementPeriod.partner_id == payload.partner_id,
        SettlementPeriod.period_start == payload.period_start,
        SettlementPeriod.period_end == payload.period_end,
    ).first()
    if existing:
        raise HTTPException(409, f"Settlement period already exists: id={existing.id}")

    period = SettlementPeriod(
        partner_id=payload.partner_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        status=SettlementStatus.open,
        total_collected=0,
        jeturing_share=0,
        partner_share=0,
        adjustments=0,
        net_to_partner=0,
        notes=payload.notes,
    )
    db.add(period)
    db.commit()
    db.refresh(period)

    return {
        "id": period.id,
        "partner_id": period.partner_id,
        "period": f"{period.period_start} → {period.period_end}",
        "status": period.status.value,
    }


@router.get("")
def list_settlement_periods(
    partner_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(SettlementPeriod)
    if partner_id:
        q = q.filter(SettlementPeriod.partner_id == partner_id)
    if status:
        q = q.filter(SettlementPeriod.status == status)
    total = q.count()
    periods = q.order_by(SettlementPeriod.period_start.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "periods": [
            {
                "id": p.id,
                "partner_id": p.partner_id,
                "period_start": p.period_start.isoformat(),
                "period_end": p.period_end.isoformat(),
                "status": p.status.value if p.status else None,
                "total_collected": p.total_collected,
                "jeturing_share": p.jeturing_share,
                "partner_share": p.partner_share,
                "net_to_partner": p.net_to_partner,
            }
            for p in periods
        ],
    }


@router.get("/{period_id}")
def get_settlement_detail(period_id: int, db: Session = Depends(get_db)):
    """Detalle de período con líneas de settlement."""
    period = db.query(SettlementPeriod).filter(SettlementPeriod.id == period_id).first()
    if not period:
        raise HTTPException(404, "Settlement period not found")

    lines = db.query(SettlementLine).filter(
        SettlementLine.settlement_period_id == period.id
    ).order_by(SettlementLine.id).all()

    return {
        "id": period.id,
        "partner_id": period.partner_id,
        "period_start": period.period_start.isoformat(),
        "period_end": period.period_end.isoformat(),
        "status": period.status.value if period.status else None,
        "total_collected": period.total_collected,
        "jeturing_share": period.jeturing_share,
        "partner_share": period.partner_share,
        "adjustments": period.adjustments,
        "net_to_partner": period.net_to_partner,
        "notes": period.notes,
        "closed_at": period.closed_at.isoformat() if period.closed_at else None,
        "lines": [
            {
                "id": ln.id,
                "invoice_id": ln.invoice_id,
                "subscription_id": ln.subscription_id,
                "concept": ln.concept,
                "amount": ln.amount,
                "jeturing_cut": ln.jeturing_cut,
                "partner_cut": ln.partner_cut,
            }
            for ln in lines
        ],
    }


@router.post("/{period_id}/close")
def close_settlement_period(
    period_id: int,
    payload: ClosePeriodRequest,
    db: Session = Depends(get_db),
):
    """
    Cierra un período de settlement:
    1. Toma todas las facturas pagadas del partner en el rango de fechas
    2. Calcula 50/50 para cada una
    3. Crea SettlementLine por cada factura
    4. Suma totales y marca período como closed
    """
    period = db.query(SettlementPeriod).filter(SettlementPeriod.id == period_id).first()
    if not period:
        raise HTTPException(404, "Settlement period not found")
    if period.status != SettlementStatus.open:
        raise HTTPException(400, f"Period already {period.status.value}")

    # Buscar facturas pagadas de este partner en el rango
    paid_invoices = db.query(Invoice).filter(
        Invoice.partner_id == period.partner_id,
        Invoice.status == InvoiceStatus.paid,
        Invoice.paid_at >= datetime.combine(period.period_start, datetime.min.time()),
        Invoice.paid_at <= datetime.combine(period.period_end, datetime.max.time()),
    ).all()

    total_collected = 0
    lines_created = 0

    for inv in paid_invoices:
        amount = inv.total or 0
        j_cut = round(amount * JETURING_SHARE, 2)
        p_cut = round(amount * PARTNER_SHARE, 2)

        line = SettlementLine(
            settlement_period_id=period.id,
            invoice_id=inv.id,
            subscription_id=inv.subscription_id,
            concept=f"Invoice {inv.invoice_number} — 50/50",
            amount=amount,
            jeturing_cut=j_cut,
            partner_cut=p_cut,
        )
        db.add(line)
        total_collected += amount
        lines_created += 1

    j_total = round(total_collected * JETURING_SHARE, 2)
    p_total = round(total_collected * PARTNER_SHARE, 2)
    adjustments = payload.adjustments or 0
    net = round(p_total + adjustments, 2)

    period.total_collected = total_collected
    period.jeturing_share = j_total
    period.partner_share = p_total
    period.adjustments = adjustments
    period.net_to_partner = net
    period.status = SettlementStatus.closed
    period.closed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if payload.notes:
        period.notes = (period.notes or "") + f"\n[Close] {payload.notes}"

    db.commit()

    logger.info(f"Settlement {period.id} closed: collected={total_collected}, net_partner={net}")

    return {
        "period_id": period.id,
        "status": "closed",
        "total_collected": total_collected,
        "jeturing_share": j_total,
        "partner_share": p_total,
        "adjustments": adjustments,
        "net_to_partner": net,
        "lines_created": lines_created,
    }
