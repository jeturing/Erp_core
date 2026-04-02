"""
DSAM — Session Security Rules Engine
Evalúa reglas de seguridad configurables por tenant/usuario.
Detecta: sesiones concurrentes, viaje imposible, restricciones geo, etc.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from ..config import (
    DSAM_IMPOSSIBLE_TRAVEL_MIN_HOURS,
    DSAM_IMPOSSIBLE_TRAVEL_MIN_KM,
)
from ..models.database import (
    ActiveSession, SessionSecurityRule, SessionGeoEvent,
    AccountSecurityAction, TenantSessionConfig,
    SessionRuleType, SessionActionType, SessionAlertSeverity,
)
from ..services.session_monitor import (
    haversine_km, terminate_redis_session, geolocate_ip,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Rule Evaluation
# ═══════════════════════════════════════════════════════

def evaluate_rules_for_session(
    db: Session,
    session: ActiveSession,
) -> list[dict[str, Any]]:
    """
    Evalúa TODAS las reglas aplicables a una sesión activa.
    Retorna lista de violaciones detectadas.
    """
    violations: list[dict[str, Any]] = []

    # Cargar reglas globales + del tenant
    result = db.execute(
        select(SessionSecurityRule).where(
            and_(
                SessionSecurityRule.is_enabled == True,
                (
                    (SessionSecurityRule.tenant_db == None) |
                    (SessionSecurityRule.tenant_db == session.tenant_db)
                ),
            )
        )
    )
    rules = result.scalars().all()

    # Cargar config del tenant
    config_result = db.execute(
        select(TenantSessionConfig).where(
            TenantSessionConfig.tenant_db == session.tenant_db
        )
    )
    tenant_config = config_result.scalar_one_or_none()

    for rule in rules:
        # Check exemptions
        if session.odoo_login and session.odoo_login in (rule.exempt_users or []):
            continue
        if session.tenant_db in (rule.exempt_tenants or []):
            continue

        violation = _evaluate_single_rule(db, rule, session, tenant_config)
        if violation:
            violations.append(violation)

    return violations


def _evaluate_single_rule(
    db: Session,
    rule: SessionSecurityRule,
    session: ActiveSession,
    tenant_config: Optional[TenantSessionConfig],
) -> Optional[dict[str, Any]]:
    """Evalúa una regla individual contra una sesión."""
    if rule.rule_type == SessionRuleType.SINGLE_SESSION:
        return _check_single_session(db, rule, session, tenant_config)
    elif rule.rule_type == SessionRuleType.MAX_SESSIONS:
        return _check_max_sessions(db, rule, session)
    elif rule.rule_type == SessionRuleType.GEO_RESTRICTION:
        return _check_geo_restriction(rule, session)
    elif rule.rule_type == SessionRuleType.IMPOSSIBLE_TRAVEL:
        return _check_impossible_travel(db, session)
    elif rule.rule_type == SessionRuleType.IP_WHITELIST:
        return _check_ip_whitelist(rule, session)
    elif rule.rule_type == SessionRuleType.TIME_RESTRICTION:
        return _check_time_restriction(rule, session)
    return None


# ── Rule Checkers ──

def _check_single_session(
    db: Session,
    rule: SessionSecurityRule,
    session: ActiveSession,
    tenant_config: Optional[TenantSessionConfig],
) -> Optional[dict[str, Any]]:
    """Verifica que el usuario solo tenga 1 sesión activa."""
    # Si el tenant permite múltiples sesiones, skip
    if tenant_config and tenant_config.allow_multiple_sessions:
        return None

    result = db.execute(
        select(func.count(ActiveSession.id)).where(
            and_(
                ActiveSession.tenant_db == session.tenant_db,
                ActiveSession.odoo_login == session.odoo_login,
                ActiveSession.is_active == True,
                ActiveSession.id != session.id,
            )
        )
    )
    count = result.scalar() or 0
    if count > 0:
        return {
            "rule_type": SessionRuleType.SINGLE_SESSION.value,
            "severity": SessionAlertSeverity.HIGH.value,
            "action": SessionActionType.CONCURRENT_SESSION_BLOCKED.value,
            "message": (
                f"Usuario {session.odoo_login} tiene {count + 1} sesiones activas "
                f"en tenant {session.tenant_db}"
            ),
            "details": {
                "concurrent_count": count + 1,
                "session_ip": session.ip_address,
                "session_country": session.geo_country,
            },
        }
    return None


def _check_max_sessions(
    db: Session,
    rule: SessionSecurityRule,
    session: ActiveSession,
) -> Optional[dict[str, Any]]:
    """Verifica límite máximo de sesiones por usuario."""
    max_allowed = (rule.config or {}).get("max", 3)
    result = db.execute(
        select(func.count(ActiveSession.id)).where(
            and_(
                ActiveSession.tenant_db == session.tenant_db,
                ActiveSession.odoo_login == session.odoo_login,
                ActiveSession.is_active == True,
            )
        )
    )
    count = result.scalar() or 0
    if count > max_allowed:
        return {
            "rule_type": SessionRuleType.MAX_SESSIONS.value,
            "severity": SessionAlertSeverity.MEDIUM.value,
            "action": SessionActionType.RULE_VIOLATION.value,
            "message": f"Usuario {session.odoo_login} excede el límite de {max_allowed} sesiones ({count} activas)",
            "details": {"max_allowed": max_allowed, "current_count": count},
        }
    return None


def _check_geo_restriction(
    rule: SessionSecurityRule,
    session: ActiveSession,
) -> Optional[dict[str, Any]]:
    """Verifica que el acceso provenga de un país permitido."""
    allowed = (rule.config or {}).get("allowed_countries", [])
    if not allowed or not session.geo_country_code:
        return None
    if session.geo_country_code == "XX":
        return None  # Private/LAN
    if session.geo_country_code not in allowed:
        return {
            "rule_type": SessionRuleType.GEO_RESTRICTION.value,
            "severity": SessionAlertSeverity.CRITICAL.value,
            "action": SessionActionType.SECURITY_ALERT.value,
            "message": (
                f"Acceso desde país no autorizado: {session.geo_country} ({session.geo_country_code}) "
                f"para {session.odoo_login}@{session.tenant_db}"
            ),
            "details": {
                "country": session.geo_country,
                "country_code": session.geo_country_code,
                "allowed_countries": allowed,
                "ip": session.ip_address,
            },
        }
    return None


def _check_impossible_travel(
    db: Session,
    session: ActiveSession,
) -> Optional[dict[str, Any]]:
    """
    Detección de viaje imposible: si la distancia entre la ubicación
    actual y la anterior es demasiado grande para el tiempo transcurrido.
    """
    if not session.geo_lat or not session.geo_lon or not session.odoo_login:
        return None

    # Buscar el evento geo anterior del mismo usuario
    result = db.execute(
        select(SessionGeoEvent)
        .where(
            and_(
                SessionGeoEvent.tenant_db == session.tenant_db,
                SessionGeoEvent.odoo_login == session.odoo_login,
                SessionGeoEvent.geo_lat.isnot(None),
            )
        )
        .order_by(desc(SessionGeoEvent.event_at))
        .limit(1)
    )
    prev_event = result.scalar_one_or_none()
    if not prev_event or not prev_event.geo_lat:
        return None

    distance_km = haversine_km(
        prev_event.geo_lat, prev_event.geo_lon,
        session.geo_lat, session.geo_lon,
    )
    time_diff = datetime.utcnow() - (prev_event.event_at or datetime.utcnow())
    hours_diff = time_diff.total_seconds() / 3600

    min_hours = DSAM_IMPOSSIBLE_TRAVEL_MIN_HOURS
    min_km = DSAM_IMPOSSIBLE_TRAVEL_MIN_KM

    if distance_km >= min_km and hours_diff <= min_hours:
        return {
            "rule_type": SessionRuleType.IMPOSSIBLE_TRAVEL.value,
            "severity": SessionAlertSeverity.CRITICAL.value,
            "action": SessionActionType.IMPOSSIBLE_TRAVEL_DETECTED.value,
            "message": (
                f"Viaje imposible detectado para {session.odoo_login}@{session.tenant_db}: "
                f"{distance_km:.0f}km en {hours_diff:.1f}h"
            ),
            "details": {
                "distance_km": round(distance_km, 1),
                "hours_diff": round(hours_diff, 2),
                "from": {
                    "country": prev_event.geo_country,
                    "city": prev_event.geo_city,
                    "lat": prev_event.geo_lat,
                    "lon": prev_event.geo_lon,
                },
                "to": {
                    "country": session.geo_country,
                    "city": session.geo_city,
                    "lat": session.geo_lat,
                    "lon": session.geo_lon,
                },
            },
        }
    return None


def _check_ip_whitelist(
    rule: SessionSecurityRule,
    session: ActiveSession,
) -> Optional[dict[str, Any]]:
    """Verifica que la IP esté en la lista blanca."""
    import ipaddress
    allowed_ips = (rule.config or {}).get("allowed_ips", [])
    if not allowed_ips:
        return None
    try:
        ip = ipaddress.ip_address(session.ip_address)
        for cidr in allowed_ips:
            if ip in ipaddress.ip_network(cidr, strict=False):
                return None
    except ValueError:
        pass
    return {
        "rule_type": SessionRuleType.IP_WHITELIST.value,
        "severity": SessionAlertSeverity.HIGH.value,
        "action": SessionActionType.SECURITY_ALERT.value,
        "message": f"IP {session.ip_address} no está en la lista blanca para {session.tenant_db}",
        "details": {
            "ip": session.ip_address,
            "allowed_ips": allowed_ips,
        },
    }


def _check_time_restriction(
    rule: SessionSecurityRule,
    session: ActiveSession,
) -> Optional[dict[str, Any]]:
    """Verifica restricción de horario laboral."""
    config = rule.config or {}
    start_str = config.get("start", "07:00")
    end_str = config.get("end", "22:00")
    tz_name = config.get("tz", "UTC")

    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(tz_name))
    except Exception:
        now = datetime.utcnow()

    start_h, start_m = map(int, start_str.split(":"))
    end_h, end_m = map(int, end_str.split(":"))
    current_minutes = now.hour * 60 + now.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    if not (start_minutes <= current_minutes <= end_minutes):
        return {
            "rule_type": SessionRuleType.TIME_RESTRICTION.value,
            "severity": SessionAlertSeverity.MEDIUM.value,
            "action": SessionActionType.RULE_VIOLATION.value,
            "message": (
                f"Acceso fuera de horario permitido ({start_str}–{end_str} {tz_name}) "
                f"para {session.odoo_login}@{session.tenant_db}"
            ),
            "details": {
                "current_time": now.strftime("%H:%M"),
                "allowed_start": start_str,
                "allowed_end": end_str,
                "timezone": tz_name,
            },
        }
    return None


# ═══════════════════════════════════════════════════════
# Action Logger
# ═══════════════════════════════════════════════════════

def log_security_action(
    db: Session,
    action_type: SessionActionType,
    tenant_db: str,
    severity: SessionAlertSeverity = SessionAlertSeverity.MEDIUM,
    odoo_login: Optional[str] = None,
    odoo_uid: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
    actor_id: Optional[int] = None,
    actor_username: Optional[str] = None,
) -> AccountSecurityAction:
    """Registra una acción de seguridad en la BD."""
    action = AccountSecurityAction(
        action_type=action_type,
        severity=severity,
        tenant_db=tenant_db,
        odoo_login=odoo_login,
        odoo_uid=odoo_uid,
        ip_address=ip_address,
        details=details or {},
        actor_id=actor_id,
        actor_username=actor_username,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    logger.info(
        "Security action logged: %s | %s | %s@%s | severity=%s",
        action_type.value, ip_address, odoo_login, tenant_db, severity.value,
    )
    return action


async def enforce_violations(
    db: Session,
    session: ActiveSession,
    violations: list[dict[str, Any]],
    auto_terminate: bool = True,
) -> list[AccountSecurityAction]:
    """
    Procesa violaciones detectadas: registra acciones y opcionalmente
    termina sesiones automáticamente.
    """
    actions: list[AccountSecurityAction] = []
    for v in violations:
        action = log_security_action(
            db=db,
            action_type=SessionActionType(v["action"]),
            tenant_db=session.tenant_db,
            severity=SessionAlertSeverity(v["severity"]),
            odoo_login=session.odoo_login,
            odoo_uid=session.odoo_uid,
            ip_address=session.ip_address,
            details=v.get("details", {}),
        )
        actions.append(action)

        # Auto-terminate en violaciones CRITICAL
        if auto_terminate and v["severity"] == SessionAlertSeverity.CRITICAL.value:
            terminated = await terminate_redis_session(session.redis_session_key)
            if terminated:
                log_security_action(
                    db=db,
                    action_type=SessionActionType.SESSION_TERMINATED,
                    tenant_db=session.tenant_db,
                    severity=SessionAlertSeverity.HIGH,
                    odoo_login=session.odoo_login,
                    ip_address=session.ip_address,
                    details={
                        "reason": v["message"],
                        "session_key": session.redis_session_key,
                        "auto_terminated": True,
                    },
                )

    return actions


# ═══════════════════════════════════════════════════════
# Full Scan & Enforce
# ═══════════════════════════════════════════════════════

async def run_full_security_scan(db: Session) -> dict[str, Any]:
    """
    Ejecuta un ciclo completo:
    1. Sync sessions from Redis
    2. Evaluate rules for each active session
    3. Enforce violations
    """
    from ..services.session_monitor import sync_sessions_to_db
    sync_stats = await sync_sessions_to_db(db)

    # Cargar todas las sesiones activas
    result = db.execute(
        select(ActiveSession).where(ActiveSession.is_active == True)
    )
    all_active = result.scalars().all()

    total_violations = 0
    total_actions = 0

    for session in all_active:
        violations = evaluate_rules_for_session(db, session)
        if violations:
            actions = await enforce_violations(db, session, violations)
            total_violations += len(violations)
            total_actions += len(actions)

    return {
        "sync": sync_stats,
        "sessions_checked": len(all_active),
        "violations_found": total_violations,
        "actions_taken": total_actions,
    }
