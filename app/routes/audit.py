"""
Audit Routes — Épica 10: Persistent Audit Event Log
- POST /api/audit/log           → Registrar evento de auditoría
- GET  /api/audit/events        → Consultar eventos
- GET  /api/audit/events/{id}   → Detalle de evento
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..models.database import AuditEventRecord, get_db

router = APIRouter(prefix="/api/audit", tags=["Audit"])
logger = logging.getLogger(__name__)


class AuditLogRequest(BaseModel):
    event_type: str          # subscription.created, seat.hwm_updated, invoice.paid, etc.
    actor: Optional[str] = None       # email o system
    entity_type: Optional[str] = None # subscription, customer, invoice, etc.
    entity_id: Optional[int] = None
    description: Optional[str] = None
    metadata_json: Optional[dict] = None


@router.post("/log")
def log_audit_event(
    payload: AuditLogRequest,
    db: Session = Depends(get_db),
):
    """Registra un evento de auditoría persistente en la DB."""
    event = AuditEventRecord(
        event_type=payload.event_type,
        actor=payload.actor or "system",
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        description=payload.description,
        metadata_json=payload.metadata_json or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "id": event.id,
        "event_type": event.event_type,
        "timestamp": event.created_at.isoformat() if event.created_at else None,
    }


@router.get("/events")
def list_audit_events(
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    actor: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Consulta eventos de auditoría con filtros."""
    q = db.query(AuditEventRecord)
    if event_type:
        q = q.filter(AuditEventRecord.event_type == event_type)
    if entity_type:
        q = q.filter(AuditEventRecord.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditEventRecord.entity_id == entity_id)
    if actor:
        q = q.filter(AuditEventRecord.actor == actor)

    total = q.count()
    events = q.order_by(AuditEventRecord.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "actor": e.actor,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "description": e.description,
                "metadata": e.metadata_json,
                "timestamp": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


@router.get("/events/{event_id}")
def get_audit_event(event_id: int, db: Session = Depends(get_db)):
    e = db.query(AuditEventRecord).filter(AuditEventRecord.id == event_id).first()
    if not e:
        raise HTTPException(404, "Audit event not found")
    return {
        "id": e.id,
        "event_type": e.event_type,
        "actor": e.actor,
        "entity_type": e.entity_type,
        "entity_id": e.entity_id,
        "description": e.description,
        "metadata": e.metadata_json,
        "timestamp": e.created_at.isoformat() if e.created_at else None,
    }
