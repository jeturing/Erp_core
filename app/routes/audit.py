"""
Audit Routes — Épica 10: Persistent Audit Event Log
- POST /api/audit/log     → Registrar evento de auditoría
- GET  /api/audit         → Consultar eventos (filtros + paginación)
- GET  /api/audit/{id}    → Detalle de evento
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Cookie
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import String, or_
import logging

from ..models.database import AuditEventRecord, get_db
from .roles import _extract_token, _require_admin as _require_admin_base

router = APIRouter(prefix="/api/audit", tags=["Audit"])
logger = logging.getLogger(__name__)


class AuditLogRequest(BaseModel):
    event_type: str
    resource: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = "success"
    details: Optional[dict] = None


@router.post("/log")
def log_audit_event(
    payload: AuditLogRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    """Registra un evento de auditoría persistente en la DB."""
    actor_id = None
    actor_username = "system"
    actor_role = None
    from ..utils.ip import get_real_ip
    ip_address = get_real_ip(request)
    user_agent = request.headers.get("user-agent")

    try:
        token = _extract_token(request, access_token)
        if token:
            # Endpoint de auditoría visible en UI admin; si hay token debe ser admin.
            _require_admin_base(request, token)
            from .roles import verify_token_with_role
            p = verify_token_with_role(token)
            actor_id = p.get("user_id")
            actor_username = p.get("username") or p.get("email") or actor_username
            actor_role = p.get("role")
    except HTTPException:
        raise
    except Exception:
        # Mantener log del sistema aunque no haya payload de usuario.
        pass

    event = AuditEventRecord(
        event_type=payload.event_type,
        actor_id=actor_id,
        actor_username=actor_username,
        actor_role=actor_role,
        ip_address=ip_address,
        user_agent=(user_agent or "")[:500] if user_agent else None,
        resource=payload.resource,
        action=payload.action,
        status=(payload.status or "success")[:20],
        details=payload.details or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "message": "Evento registrado",
        "event_id": event.id,
    }


@router.get("")
def list_audit_events(
    request: Request,
    access_token: str = Cookie(None),
    event_type: Optional[str] = None,
    actor_id: Optional[int] = None,
    resource: Optional[str] = None,
    tenant: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Consulta eventos de auditoría con filtros (incluye filtro por tenant)."""
    _require_admin_base(request, access_token)

    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    q = db.query(AuditEventRecord)

    if event_type:
        q = q.filter(AuditEventRecord.event_type == event_type)
    if actor_id is not None:
        q = q.filter(AuditEventRecord.actor_id == actor_id)
    if resource:
        q = q.filter(AuditEventRecord.resource.ilike(f"%{resource}%"))
    if status:
        q = q.filter(AuditEventRecord.status == status)
    if tenant:
        tenant_like = f"%{tenant}%"
        q = q.filter(
            or_(
                AuditEventRecord.resource.ilike(tenant_like),
                AuditEventRecord.details.cast(String).ilike(tenant_like),
            )
        )

    total = q.count()
    events = q.order_by(AuditEventRecord.created_at.desc()).offset(offset).limit(limit).all()

    items = [
        {
            "id": e.id,
            "event_type": e.event_type,
            "actor_id": e.actor_id,
            "actor_username": e.actor_username,
            "actor_role": e.actor_role,
            "ip_address": e.ip_address,
            "user_agent": e.user_agent,
            "resource": e.resource,
            "action": e.action,
            "status": e.status,
            "details": e.details,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

    return {
        "total": total,
        "items": items,
        # Backward compatibility
        "events": items,
    }


@router.get("/{event_id:int}")
def get_audit_event(
    event_id: int,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    _require_admin_base(request, access_token)

    e = db.query(AuditEventRecord).filter(AuditEventRecord.id == event_id).first()
    if not e:
        raise HTTPException(404, "Audit event not found")
    return {
        "id": e.id,
        "event_type": e.event_type,
        "actor_id": e.actor_id,
        "actor_username": e.actor_username,
        "actor_role": e.actor_role,
        "ip_address": e.ip_address,
        "user_agent": e.user_agent,
        "resource": e.resource,
        "action": e.action,
        "status": e.status,
        "details": e.details,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.get("/events")
def list_audit_events_legacy(
    request: Request,
    access_token: str = Cookie(None),
    event_type: Optional[str] = None,
    actor_id: Optional[int] = None,
    resource: Optional[str] = None,
    tenant: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return list_audit_events(
        request=request,
        access_token=access_token,
        event_type=event_type,
        actor_id=actor_id,
        resource=resource,
        tenant=tenant,
        status=status,
        limit=limit,
        offset=offset,
        db=db,
    )


@router.get("/events/{event_id:int}")
def get_audit_event_legacy(
    event_id: int,
    request: Request,
    access_token: str = Cookie(None),
    db: Session = Depends(get_db),
):
    return get_audit_event(
        event_id=event_id,
        request=request,
        access_token=access_token,
        db=db,
    )
