"""
DSAM — Session Monitoring API Routes
Endpoints para monitorear sesiones activas, reglas de seguridad,
geo-mapa, acciones de seguridad y auditoría de seats.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Cookie
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    ActiveSession, SessionSecurityRule, SessionGeoEvent,
    AccountSecurityAction, TenantSessionConfig,
    SessionRuleType, SessionActionType, SessionAlertSeverity,
    get_db,
)
from ..services.session_monitor import (
    sync_sessions_to_db, terminate_redis_session,
    get_active_sessions_by_tenant, get_active_sessions_by_user,
    get_session_stats, get_geo_heatmap_data,
)
from ..security.session_rules import (
    run_full_security_scan, log_security_action, evaluate_rules_for_session,
)
from ..tasks.seat_audit import run_seat_audit, get_seat_reconciliation_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dsam", tags=["DSAM – Session Monitoring"])


# ── Auth helper (reuses admin auth from roles) ──
def _require_admin(request: Request, access_token: str = Cookie(None)):
    """Valida que el usuario es admin. Reutiliza auth existente."""
    from ..routes.roles import _require_admin as base_require_admin
    return base_require_admin(request, access_token)


# ═══════════════════════════════════════════════════════
# DTOs
# ═══════════════════════════════════════════════════════

class SyncResponse(BaseModel):
    success: bool
    data: dict[str, Any]
    meta: dict[str, Any] = Field(default_factory=dict)


class TerminateSessionRequest(BaseModel):
    session_key: str
    reason: str = "Admin requested termination"


class LockAccountRequest(BaseModel):
    tenant_db: str
    odoo_login: str
    reason: str = "Security violation"


class CreateRuleRequest(BaseModel):
    rule_type: str  # SessionRuleType value
    tenant_db: Optional[str] = None
    config: dict[str, Any] = Field(default_factory=dict)
    exempt_users: list[str] = Field(default_factory=list)
    exempt_tenants: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    is_enabled: bool = True


class UpdateTenantConfigRequest(BaseModel):
    allow_multiple_sessions: Optional[bool] = None
    max_concurrent_sessions: Optional[int] = None
    enforce_geo_restrictions: Optional[bool] = None
    enforce_impossible_travel: Optional[bool] = None
    allowed_countries: Optional[list[str]] = None
    session_timeout_minutes: Optional[int] = None
    notify_on_new_device: Optional[bool] = None
    seat_audit_enabled: Optional[bool] = None


class ResolveActionRequest(BaseModel):
    resolution_note: str


# ═══════════════════════════════════════════════════════
# Dashboard & Stats
# ═══════════════════════════════════════════════════════

@router.get("/dashboard")
async def get_dashboard(
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard principal DSAM con estadísticas globales."""
    _require_admin(request, access_token)
    stats = await get_session_stats(db)

    # Alertas sin resolver
    unresolved = await db.execute(
        select(func.count(AccountSecurityAction.id)).where(
            AccountSecurityAction.resolved == False
        )
    )
    critical_unresolved = await db.execute(
        select(func.count(AccountSecurityAction.id)).where(
            and_(
                AccountSecurityAction.resolved == False,
                AccountSecurityAction.severity == SessionAlertSeverity.CRITICAL,
            )
        )
    )

    return {
        "success": True,
        "data": {
            **stats,
            "unresolved_alerts": unresolved.scalar() or 0,
            "critical_alerts": critical_unresolved.scalar() or 0,
        },
        "meta": {"timestamp": datetime.utcnow().isoformat()},
    }


# ═══════════════════════════════════════════════════════
# Active Sessions
# ═══════════════════════════════════════════════════════

@router.post("/sync")
async def sync_sessions(
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Fuerza sincronización de sesiones desde Redis."""
    _require_admin(request, access_token)
    stats = await sync_sessions_to_db(db)
    return {"success": True, "data": stats, "meta": {}}


@router.get("/sessions")
async def list_all_sessions(
    request: Request,
    access_token: str = Cookie(None),
    tenant: Optional[str] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Lista sesiones activas, opcionalmente filtradas por tenant."""
    _require_admin(request, access_token)
    query = select(ActiveSession)
    count_query = select(func.count(ActiveSession.id))

    if tenant:
        query = query.where(ActiveSession.tenant_db == tenant)
        count_query = count_query.where(ActiveSession.tenant_db == tenant)
    if active_only:
        query = query.where(ActiveSession.is_active == True)
        count_query = count_query.where(ActiveSession.is_active == True)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * limit
    query = query.order_by(ActiveSession.last_activity.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "redis_key": s.redis_session_key,
                "tenant_db": s.tenant_db,
                "odoo_login": s.odoo_login,
                "odoo_uid": s.odoo_uid,
                "ip_address": s.ip_address,
                "country": s.geo_country,
                "country_code": s.geo_country_code,
                "region": s.geo_region,
                "city": s.geo_city,
                "lat": s.geo_lat,
                "lon": s.geo_lon,
                "session_start": s.session_start.isoformat() if s.session_start else None,
                "last_activity": s.last_activity.isoformat() if s.last_activity else None,
                "first_seen": s.first_seen_at.isoformat() if s.first_seen_at else None,
                "is_active": s.is_active,
            }
            for s in sessions
        ],
        "meta": {"total": total, "page": page, "limit": limit},
    }


@router.get("/sessions/tenant/{tenant_db}")
async def sessions_by_tenant(
    tenant_db: str,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Sesiones activas para un tenant específico."""
    _require_admin(request, access_token)
    sessions = await get_active_sessions_by_tenant(db, tenant_db)
    return {
        "success": True,
        "data": [
            {
                "id": s.id,
                "redis_key": s.redis_session_key,
                "odoo_login": s.odoo_login,
                "ip_address": s.ip_address,
                "country": s.geo_country,
                "city": s.geo_city,
                "last_activity": s.last_activity.isoformat() if s.last_activity else None,
            }
            for s in sessions
        ],
        "meta": {"tenant": tenant_db, "count": len(sessions)},
    }


@router.post("/sessions/terminate")
async def terminate_session(
    body: TerminateSessionRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Termina una sesión específica de Redis + marca inactiva en BD."""
    admin = _require_admin(request, access_token)
    terminated = await terminate_redis_session(body.session_key)

    # Marcar inactiva en BD
    result = await db.execute(
        select(ActiveSession).where(
            ActiveSession.redis_session_key == body.session_key
        )
    )
    session = result.scalar_one_or_none()
    if session:
        session.is_active = False
        await log_security_action(
            db=db,
            action_type=SessionActionType.SESSION_TERMINATED,
            tenant_db=session.tenant_db,
            severity=SessionAlertSeverity.MEDIUM,
            odoo_login=session.odoo_login,
            ip_address=session.ip_address,
            details={"reason": body.reason, "session_key": body.session_key},
            actor_username=getattr(admin, "username", None) or getattr(admin, "email", None),
        )
        await db.commit()

    return {
        "success": terminated,
        "data": {
            "session_key": body.session_key,
            "redis_deleted": terminated,
            "db_updated": session is not None,
        },
        "meta": {},
    }


# ═══════════════════════════════════════════════════════
# Geo Map & Heatmap
# ═══════════════════════════════════════════════════════

@router.get("/geo/heatmap")
async def geo_heatmap(
    request: Request,
    access_token: str = Cookie(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Datos de mapa de calor geográfico."""
    _require_admin(request, access_token)
    data = await get_geo_heatmap_data(db, days=days)
    return {"success": True, "data": data, "meta": {"days": days}}


@router.get("/geo/live")
async def geo_live_map(
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Posiciones actuales de sesiones activas para mapa en vivo."""
    _require_admin(request, access_token)
    result = await db.execute(
        select(ActiveSession).where(
            and_(
                ActiveSession.is_active == True,
                ActiveSession.geo_lat.isnot(None),
            )
        )
    )
    sessions = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "tenant_db": s.tenant_db,
                "odoo_login": s.odoo_login,
                "ip": s.ip_address,
                "country": s.geo_country,
                "city": s.geo_city,
                "lat": s.geo_lat,
                "lon": s.geo_lon,
                "last_activity": s.last_activity.isoformat() if s.last_activity else None,
            }
            for s in sessions
        ],
        "meta": {"count": len(sessions)},
    }


# ═══════════════════════════════════════════════════════
# Security Rules CRUD
# ═══════════════════════════════════════════════════════

@router.get("/rules")
async def list_rules(
    request: Request,
    access_token: str = Cookie(None),
    tenant: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas las reglas de seguridad."""
    _require_admin(request, access_token)
    query = select(SessionSecurityRule)
    if tenant:
        query = query.where(
            (SessionSecurityRule.tenant_db == tenant) | (SessionSecurityRule.tenant_db == None)
        )
    result = await db.execute(query.order_by(SessionSecurityRule.id))
    rules = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": r.id,
                "rule_type": r.rule_type.value,
                "tenant_db": r.tenant_db,
                "is_enabled": r.is_enabled,
                "config": r.config,
                "exempt_users": r.exempt_users,
                "exempt_tenants": r.exempt_tenants,
                "description": r.description,
            }
            for r in rules
        ],
        "meta": {"count": len(rules)},
    }


@router.post("/rules")
async def create_rule(
    body: CreateRuleRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Crea una nueva regla de seguridad."""
    _require_admin(request, access_token)
    try:
        rule_type = SessionRuleType(body.rule_type)
    except ValueError:
        raise HTTPException(400, f"Invalid rule_type: {body.rule_type}")

    rule = SessionSecurityRule(
        rule_type=rule_type,
        tenant_db=body.tenant_db,
        is_enabled=body.is_enabled,
        config=body.config,
        exempt_users=body.exempt_users,
        exempt_tenants=body.exempt_tenants,
        description=body.description,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return {
        "success": True,
        "data": {"id": rule.id, "rule_type": rule.rule_type.value},
        "meta": {},
    }


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    body: CreateRuleRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza una regla existente."""
    _require_admin(request, access_token)
    result = await db.execute(
        select(SessionSecurityRule).where(SessionSecurityRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")

    rule.is_enabled = body.is_enabled
    rule.config = body.config
    rule.exempt_users = body.exempt_users
    rule.exempt_tenants = body.exempt_tenants
    rule.description = body.description
    rule.tenant_db = body.tenant_db
    await db.commit()

    return {"success": True, "data": {"id": rule.id}, "meta": {}}


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Elimina una regla de seguridad."""
    _require_admin(request, access_token)
    result = await db.execute(
        select(SessionSecurityRule).where(SessionSecurityRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"success": True, "data": {"deleted": rule_id}, "meta": {}}


# ═══════════════════════════════════════════════════════
# Tenant Session Config
# ═══════════════════════════════════════════════════════

@router.get("/config/{tenant_db}")
async def get_tenant_config(
    tenant_db: str,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Obtiene la configuración DSAM de un tenant."""
    _require_admin(request, access_token)
    result = await db.execute(
        select(TenantSessionConfig).where(TenantSessionConfig.tenant_db == tenant_db)
    )
    config = result.scalar_one_or_none()
    if not config:
        return {
            "success": True,
            "data": None,
            "meta": {"tenant_db": tenant_db, "note": "No config found, using defaults"},
        }
    return {
        "success": True,
        "data": {
            "id": config.id,
            "tenant_db": config.tenant_db,
            "allow_multiple_sessions": config.allow_multiple_sessions,
            "max_concurrent_sessions": config.max_concurrent_sessions,
            "enforce_geo_restrictions": config.enforce_geo_restrictions,
            "enforce_impossible_travel": config.enforce_impossible_travel,
            "allowed_countries": config.allowed_countries,
            "session_timeout_minutes": config.session_timeout_minutes,
            "notify_on_new_device": config.notify_on_new_device,
            "seat_audit_enabled": config.seat_audit_enabled,
            "last_seat_audit_at": config.last_seat_audit_at.isoformat() if config.last_seat_audit_at else None,
        },
        "meta": {},
    }


@router.put("/config/{tenant_db}")
async def upsert_tenant_config(
    tenant_db: str,
    body: UpdateTenantConfigRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Crea o actualiza la configuración DSAM de un tenant."""
    _require_admin(request, access_token)
    result = await db.execute(
        select(TenantSessionConfig).where(TenantSessionConfig.tenant_db == tenant_db)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = TenantSessionConfig(tenant_db=tenant_db)
        db.add(config)

    update_data = body.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return {"success": True, "data": {"id": config.id, "tenant_db": tenant_db}, "meta": {}}


# ═══════════════════════════════════════════════════════
# Security Actions / Playbook
# ═══════════════════════════════════════════════════════

@router.get("/actions")
async def list_security_actions(
    request: Request,
    access_token: str = Cookie(None),
    tenant: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Lista acciones de seguridad con filtros."""
    _require_admin(request, access_token)
    query = select(AccountSecurityAction)
    count_query = select(func.count(AccountSecurityAction.id))

    filters = []
    if tenant:
        filters.append(AccountSecurityAction.tenant_db == tenant)
    if severity:
        try:
            sev = SessionAlertSeverity(severity)
            filters.append(AccountSecurityAction.severity == sev)
        except ValueError:
            pass
    if resolved is not None:
        filters.append(AccountSecurityAction.resolved == resolved)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * limit
    result = await db.execute(
        query.order_by(desc(AccountSecurityAction.created_at)).offset(offset).limit(limit)
    )
    actions = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": a.id,
                "action_type": a.action_type.value,
                "severity": a.severity.value,
                "tenant_db": a.tenant_db,
                "odoo_login": a.odoo_login,
                "ip_address": a.ip_address,
                "details": a.details,
                "actor_username": a.actor_username,
                "resolved": a.resolved,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "resolved_by": a.resolved_by,
                "resolution_note": a.resolution_note,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ],
        "meta": {"total": total, "page": page, "limit": limit},
    }


@router.put("/actions/{action_id}/resolve")
async def resolve_action(
    action_id: int,
    body: ResolveActionRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Marca una acción de seguridad como resuelta (playbook)."""
    admin = _require_admin(request, access_token)
    result = await db.execute(
        select(AccountSecurityAction).where(AccountSecurityAction.id == action_id)
    )
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(404, "Action not found")

    action.resolved = True
    action.resolved_at = datetime.utcnow()
    action.resolved_by = getattr(admin, "username", None) or getattr(admin, "email", "admin")
    action.resolution_note = body.resolution_note
    await db.commit()

    return {"success": True, "data": {"id": action_id, "resolved": True}, "meta": {}}


# ═══════════════════════════════════════════════════════
# Account Lock/Unlock (Odoo webhook integration)
# ═══════════════════════════════════════════════════════

@router.post("/accounts/lock")
async def lock_account(
    body: LockAccountRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Bloquea una cuenta: termina todas las sesiones del usuario
    y opcionalmente notifica a Odoo vía webhook.
    """
    admin = _require_admin(request, access_token)

    # Terminar todas las sesiones del usuario
    result = await db.execute(
        select(ActiveSession).where(
            and_(
                ActiveSession.tenant_db == body.tenant_db,
                ActiveSession.odoo_login == body.odoo_login,
                ActiveSession.is_active == True,
            )
        )
    )
    sessions = result.scalars().all()
    terminated_count = 0
    for s in sessions:
        if await terminate_redis_session(s.redis_session_key):
            s.is_active = False
            terminated_count += 1

    # Registrar acción
    await log_security_action(
        db=db,
        action_type=SessionActionType.ACCOUNT_LOCKED,
        tenant_db=body.tenant_db,
        severity=SessionAlertSeverity.HIGH,
        odoo_login=body.odoo_login,
        details={
            "reason": body.reason,
            "sessions_terminated": terminated_count,
        },
        actor_username=getattr(admin, "username", None) or getattr(admin, "email", None),
    )

    # TODO: Notificar Odoo vía webhook para desactivar el usuario
    # (integrar con jeturing_erp_sync cuando esté listo)

    return {
        "success": True,
        "data": {
            "tenant_db": body.tenant_db,
            "odoo_login": body.odoo_login,
            "sessions_terminated": terminated_count,
            "locked": True,
        },
        "meta": {},
    }


@router.post("/accounts/unlock")
async def unlock_account(
    body: LockAccountRequest,
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Desbloquea una cuenta previamente bloqueada."""
    admin = _require_admin(request, access_token)

    await log_security_action(
        db=db,
        action_type=SessionActionType.ACCOUNT_UNLOCKED,
        tenant_db=body.tenant_db,
        severity=SessionAlertSeverity.LOW,
        odoo_login=body.odoo_login,
        details={"reason": body.reason},
        actor_username=getattr(admin, "username", None) or getattr(admin, "email", None),
    )

    # TODO: Notificar Odoo vía webhook para reactivar el usuario

    return {
        "success": True,
        "data": {
            "tenant_db": body.tenant_db,
            "odoo_login": body.odoo_login,
            "unlocked": True,
        },
        "meta": {},
    }


# ═══════════════════════════════════════════════════════
# Security Scan
# ═══════════════════════════════════════════════════════

@router.post("/scan")
async def run_scan(
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Ejecuta un ciclo completo: sync Redis → evaluar reglas → enforce."""
    _require_admin(request, access_token)
    result = await run_full_security_scan(db)
    return {"success": True, "data": result, "meta": {}}


# ═══════════════════════════════════════════════════════
# Seat Audit
# ═══════════════════════════════════════════════════════

@router.post("/audit/seats")
async def audit_seats(
    request: Request,
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Ejecuta auditoría de seats vs sesiones activas."""
    _require_admin(request, access_token)
    result = await run_seat_audit(db)
    return {"success": True, "data": result, "meta": {}}


@router.get("/audit/reconciliation")
async def seat_reconciliation(
    request: Request,
    access_token: str = Cookie(None),
    tenant: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Reporte de reconciliación de seats."""
    _require_admin(request, access_token)
    report = await get_seat_reconciliation_report(db, tenant_db=tenant)
    return {"success": True, "data": report, "meta": {}}
