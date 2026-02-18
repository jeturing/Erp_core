"""
Work Orders Routes — Épica 9: Órdenes de Trabajo con gating
- POST /api/work-orders             → Crear work order
- GET  /api/work-orders             → Lista work orders
- GET  /api/work-orders/{id}        → Detalle
- PUT  /api/work-orders/{id}/status → Cambiar estado con validación de gating
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..models.database import (
    WorkOrder, WorkOrderStatus, Subscription, Customer,
    Invoice, InvoiceStatus,
    get_db
)

router = APIRouter(prefix="/api/work-orders", tags=["WorkOrders"])
logger = logging.getLogger(__name__)


class CreateWorkOrder(BaseModel):
    subscription_id: int
    customer_id: int
    title: str
    description: Optional[str] = None
    requested_by: Optional[str] = None


class UpdateWorkOrderStatus(BaseModel):
    new_status: str   # pending_payment | in_progress | completed | cancelled
    notes: Optional[str] = None


@router.post("")
def create_work_order(
    payload: CreateWorkOrder,
    db: Session = Depends(get_db),
):
    """Crea work order. Inicia en pending_payment."""
    sub = db.query(Subscription).filter(Subscription.id == payload.subscription_id).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    wo = WorkOrder(
        subscription_id=payload.subscription_id,
        customer_id=payload.customer_id,
        title=payload.title,
        description=payload.description,
        status=WorkOrderStatus.pending_payment,
        requested_by=payload.requested_by,
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)

    return {
        "id": wo.id,
        "title": wo.title,
        "status": wo.status.value,
        "created_at": wo.created_at.isoformat(),
    }


@router.get("")
def list_work_orders(
    customer_id: Optional[int] = None,
    subscription_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(WorkOrder)
    if customer_id:
        q = q.filter(WorkOrder.customer_id == customer_id)
    if subscription_id:
        q = q.filter(WorkOrder.subscription_id == subscription_id)
    if status:
        q = q.filter(WorkOrder.status == status)

    total = q.count()
    orders = q.order_by(WorkOrder.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "work_orders": [
            {
                "id": wo.id,
                "subscription_id": wo.subscription_id,
                "customer_id": wo.customer_id,
                "title": wo.title,
                "status": wo.status.value if wo.status else None,
                "requested_by": wo.requested_by,
                "created_at": wo.created_at.isoformat() if wo.created_at else None,
                "completed_at": wo.completed_at.isoformat() if wo.completed_at else None,
            }
            for wo in orders
        ],
    }


@router.get("/{wo_id}")
def get_work_order(wo_id: int, db: Session = Depends(get_db)):
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(404, "Work order not found")
    return {
        "id": wo.id,
        "subscription_id": wo.subscription_id,
        "customer_id": wo.customer_id,
        "title": wo.title,
        "description": wo.description,
        "status": wo.status.value if wo.status else None,
        "requested_by": wo.requested_by,
        "gating_invoice_id": wo.gating_invoice_id,
        "notes": wo.notes,
        "created_at": wo.created_at.isoformat() if wo.created_at else None,
        "completed_at": wo.completed_at.isoformat() if wo.completed_at else None,
    }


@router.put("/{wo_id}/status")
def update_work_order_status(
    wo_id: int,
    payload: UpdateWorkOrderStatus,
    db: Session = Depends(get_db),
):
    """
    Cambia estado de work order con gating:
    - pending_payment → in_progress: Solo si hay factura asociada pagada
    - in_progress → completed: Marca completed_at
    - Cualquiera → cancelled: Siempre permitido
    """
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(404, "Work order not found")

    new = payload.new_status
    current = wo.status.value if wo.status else "unknown"

    # Validaciones de transición
    if new == "in_progress" and current == "pending_payment":
        # GATING: verificar factura pagada
        if wo.gating_invoice_id:
            invoice = db.query(Invoice).filter(Invoice.id == wo.gating_invoice_id).first()
            if not invoice or invoice.status != InvoiceStatus.paid:
                raise HTTPException(
                    402,
                    "Cannot start work order: gating invoice not paid"
                )
        # Sin gating_invoice_id → permitir (work order sin costo)
        wo.status = WorkOrderStatus.in_progress

    elif new == "completed" and current == "in_progress":
        wo.status = WorkOrderStatus.completed
        wo.completed_at = datetime.utcnow()

    elif new == "cancelled":
        wo.status = WorkOrderStatus.cancelled

    else:
        raise HTTPException(
            400,
            f"Invalid status transition: {current} → {new}"
        )

    if payload.notes:
        wo.notes = (wo.notes or "") + f"\n[{new}] {payload.notes}"

    db.commit()

    return {
        "id": wo.id,
        "status": wo.status.value,
        "completed_at": wo.completed_at.isoformat() if wo.completed_at else None,
    }
