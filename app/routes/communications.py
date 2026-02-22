"""
Communications Routes — Historial de emails transaccionales y gestión de notificaciones.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Cookie, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import desc

from ..models.database import SessionLocal, EmailLog, Customer, Partner
from .roles import _require_admin

router = APIRouter(prefix="/api/communications", tags=["Communications"])


class EmailLogOut(BaseModel):
    id: int
    recipient: str
    subject: Optional[str]
    email_type: str
    status: Optional[str]
    error_message: Optional[str]
    customer_id: Optional[int]
    partner_id: Optional[int]
    related_id: Optional[int]
    sent_at: Optional[datetime]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class EmailLogsResponse(BaseModel):
    items: List[EmailLogOut]
    total: int
    limit: int
    offset: int


@router.get("/history", response_model=EmailLogsResponse)
async def get_email_history(
    request: Request,
    access_token: str = Cookie(None),
    email_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    recipient: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Lista paginada de emails transaccionales enviados."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(EmailLog)
        if email_type:
            q = q.filter(EmailLog.email_type == email_type)
        if status:
            q = q.filter(EmailLog.status == status)
        if recipient:
            q = q.filter(EmailLog.recipient.ilike(f"%{recipient}%"))

        total = q.count()
        items = q.order_by(desc(EmailLog.created_at)).offset(offset).limit(limit).all()

        return EmailLogsResponse(
            items=[EmailLogOut.from_orm(e) for e in items],
            total=total,
            limit=limit,
            offset=offset,
        )
    finally:
        db.close()


@router.get("/history/{log_id}", response_model=EmailLogOut)
async def get_email_log(
    log_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Detalle de un email específico."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        record = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Email log not found")
        return EmailLogOut.from_orm(record)
    finally:
        db.close()


@router.get("/stats")
async def get_email_stats(
    request: Request,
    access_token: str = Cookie(None),
):
    """Estadísticas de emails: totales por tipo y estado."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        from sqlalchemy import func
        total = db.query(EmailLog).count()
        sent = db.query(EmailLog).filter(EmailLog.status == "sent").count()
        failed = db.query(EmailLog).filter(EmailLog.status == "failed").count()

        by_type = db.query(
            EmailLog.email_type,
            func.count(EmailLog.id).label("count")
        ).group_by(EmailLog.email_type).all()

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "by_type": {row.email_type: row.count for row in by_type},
        }
    finally:
        db.close()
