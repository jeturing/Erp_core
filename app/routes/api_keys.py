"""
API Key Management — Estilo Stripe
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GET    /api/api-keys              → Listar todas las keys (RBAC: api_keys:read)
POST   /api/api-keys              → Crear nueva key — devuelve secret UNA vez (api_keys:write)
GET    /api/api-keys/tiers        → Tiers de rate limit disponibles (público)
GET    /api/api-keys/{key_id}     → Detalle + stats de uso (api_keys:read | api_keys:self)
PUT    /api/api-keys/{key_id}     → Actualizar nombre / permisos / tier (api_keys:write)
POST   /api/api-keys/{key_id}/rotate   → Rotación estilo Stripe (api_keys:rotate)
DELETE /api/api-keys/{key_id}     → Revocar (api_keys:delete)
GET    /api/api-keys/{key_id}/usage    → Histograma de uso por hora (api_keys:billing)
"""

import hashlib
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.database import (
    ApiKey, ApiKeyStatus, ApiKeyScope, ApiKeyTier, ApiKeyUsageLog,
    ApiKeyRotationRequest, ApiKeyRotationStatus,
    API_KEY_TIER_LIMITS, get_db,
)
from .roles import _extract_token, verify_token_with_role

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])

# ─────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────

_SAFE_CHARS = string.ascii_letters + string.digits  # sin - _ para evitar confusiones


def _generate_key() -> tuple[str, str, str]:
    """
    Genera un par (key_id, full_key, key_hash).
      key_id   → "sk_live_<16 chars>"  — se almacena, se muestra siempre
      full_key → "sk_live_<16>_<32>"   — solo se devuelve en creación/rotación
      key_hash → SHA-256(full_key)      — se almacena para verificación
    """
    prefix  = "".join(secrets.choice(_SAFE_CHARS) for _ in range(16))
    secret  = "".join(secrets.choice(_SAFE_CHARS) for _ in range(32))
    key_id  = f"sk_live_{prefix}"
    full_key = f"sk_live_{prefix}_{secret}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return key_id, full_key, key_hash


def _hash_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()


def _resolve_tier_limits(key: ApiKey) -> Dict[str, Any]:
    base = API_KEY_TIER_LIMITS.get(key.tier.value, API_KEY_TIER_LIMITS["standard"])
    return {
        "rpm":    key.requests_per_minute  or base["rpm"],
        "rpd":    key.requests_per_day     or base["rpd"],
        "tokens": key.monthly_quota_tokens or base["rpm_tokens"],
    }


# ── Constantes de roles ────────────────────────────────────────────────────
ROLE_ADMIN   = "admin"
ROLE_SUPPORT = "support"


def _require_permission(token_data: dict, *perms: str) -> bool:
    """Retorna True si el usuario tiene alguno de los permisos o wildcard '*'."""
    user_perms: list = token_data.get("permissions", [])
    if "*" in user_perms:
        return True
    return any(p in user_perms for p in perms)


def _is_admin(token_data: dict) -> bool:
    return token_data.get("role") == ROLE_ADMIN or "*" in token_data.get("permissions", [])


def _is_support(token_data: dict) -> bool:
    return token_data.get("role") == ROLE_SUPPORT


def _tenant_id_from_token(token_data: dict) -> Optional[int]:
    """Extrae el tenant_id del JWT (para tenants autenticados)."""
    return token_data.get("tenant_id")


def _auth(request: Request, access_token: Optional[str]) -> dict:
    """Extrae y valida JWT; lanza 401 si no hay token."""
    token = _extract_token(request, access_token)
    if not token:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    try:
        return verify_token_with_role(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


def _assert_tenant_access(token_data: dict, key: ApiKey) -> None:
    """
    Verifica que el usuario autenticado tenga acceso a la key dada.
    Reglas:
      - admin  → acceso total
      - support → acceso total (lectura); escritura requiere rotation_request
      - tenant (api_keys:self) → solo ve sus keys con mismo tenant_id
    """
    if _is_admin(token_data):
        return
    if _is_support(token_data):
        return  # support puede leer todo; restricción de escritura se aplica por endpoint

    # tenant / usuario normal: aislar por tenant_id
    token_tenant = _tenant_id_from_token(token_data)
    uid          = token_data.get("user_id")
    cid          = token_data.get("customer_id")

    if token_tenant and key.tenant_id and key.tenant_id != token_tenant:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta API key")
    if not token_tenant and key.created_by != uid and key.customer_id != cid:
        raise HTTPException(status_code=403, detail="No tienes acceso a esta API key")


# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scope: ApiKeyScope = ApiKeyScope.read_only
    tier: ApiKeyTier = ApiKeyTier.standard
    permissions: List[str] = []
    tenant_id: Optional[int] = None
    customer_id: Optional[int] = None
    expires_in_days: Optional[int] = None   # None = no expira
    tags: List[str] = []
    # Overrides opcionales de rate limit
    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    monthly_quota_tokens: Optional[int] = None


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scope: Optional[ApiKeyScope] = None
    tier: Optional[ApiKeyTier] = None
    permissions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    expires_in_days: Optional[int] = None
    requests_per_minute: Optional[int] = None
    requests_per_day: Optional[int] = None
    monthly_quota_tokens: Optional[int] = None


def _key_summary(key: ApiKey, *, include_secret: str = None) -> dict:
    """Serializa un ApiKey para respuesta JSON."""
    limits = _resolve_tier_limits(key)
    data = {
        "key_id":         key.key_id,
        "name":           key.name,
        "description":    key.description,
        "status":         key.status.value,
        "scope":          key.scope.value,
        "tier":           key.tier.value,
        "permissions":    key.permissions,
        "tags":           key.tags,
        "tenant_id":      key.tenant_id,
        "customer_id":    key.customer_id,
        "rate_limits": {
            "requests_per_minute":   limits["rpm"],
            "requests_per_day":      limits["rpd"],
            "monthly_quota_tokens":  limits["tokens"],
        },
        "usage": {
            "today":   key.usage_today,
            "month":   key.usage_this_month,
            "total":   key.total_requests,
        },
        "last_used_at":  key.last_used_at.isoformat() if key.last_used_at else None,
        "last_used_ip":  key.last_used_ip,
        "expires_at":    key.expires_at.isoformat() if key.expires_at else None,
        "created_at":    key.created_at.isoformat(),
        "updated_at":    key.updated_at.isoformat() if key.updated_at else None,
        "rotated_at":    key.rotated_at.isoformat() if key.rotated_at else None,
    }
    if include_secret:
        # Solo en creación / rotación — se muestra UNA sola vez
        data["api_key"] = include_secret
        data["_note"] = "⚠️ Guarda esta clave ahora. No se volverá a mostrar."
    return data


# ─────────────────────────────────────────────
# Tiers — endpoint público
# ─────────────────────────────────────────────

@router.get("/tiers", summary="Tiers de rate limit disponibles")
def list_tiers():
    """Devuelve los límites de cada tier. Endpoint público (sin auth)."""
    return {
        "tiers": [
            {
                "name":                  tier,
                "requests_per_minute":   limits["rpm"],
                "requests_per_day":      limits["rpd"],
                "monthly_quota_tokens":  limits["rpm_tokens"],
                "unlimited_rpd":         limits["rpd"] is None,
                "unlimited_tokens":      limits["rpm_tokens"] is None,
            }
            for tier, limits in API_KEY_TIER_LIMITS.items()
        ]
    }


# ─────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────

@router.get("", summary="Listar API keys")
def list_api_keys(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    status_filter: Optional[str] = None,
    tier_filter: Optional[str] = None,
    customer_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    token_data = _auth(request, access_token)

    # Verificar algún permiso mínimo
    has_access = (
        _is_admin(token_data)
        or _is_support(token_data)
        or _require_permission(token_data, "api_keys:read", "api_keys:self")
        or _tenant_id_from_token(token_data) is not None
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Se requiere permiso api_keys:read")

    q = db.query(ApiKey)

    if _is_admin(token_data):
        pass  # ve todo
    elif _is_support(token_data):
        pass  # soporte también ve todo en lectura
    elif _tenant_id_from_token(token_data) or _require_permission(token_data, "api_keys:self"):
        # Tenant: filtra estrictamente por su tenant_id
        token_tenant = _tenant_id_from_token(token_data)
        if token_tenant:
            q = q.filter(ApiKey.tenant_id == token_tenant)
        else:
            cid = token_data.get("customer_id")
            uid = token_data.get("user_id")
            q = q.filter(
                (ApiKey.customer_id == cid) | (ApiKey.created_by == uid)
            )
    else:
        raise HTTPException(status_code=403, detail="Se requiere permiso api_keys:read")

    if status_filter:
        try:
            q = q.filter(ApiKey.status == ApiKeyStatus(status_filter))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Estado inválido: {status_filter}")

    if tier_filter:
        try:
            q = q.filter(ApiKey.tier == ApiKeyTier(tier_filter))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Tier inválido: {tier_filter}")

    if customer_id:
        q = q.filter(ApiKey.customer_id == customer_id)
    if tenant_id:
        q = q.filter(ApiKey.tenant_id == tenant_id)

    total = q.count()
    keys  = q.order_by(ApiKey.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "data":     [_key_summary(k) for k in keys],
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    (total + per_page - 1) // per_page,
    }


# ─────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────

@router.post("", status_code=201, summary="Crear API key")
def create_api_key(
    payload: ApiKeyCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    token_data = _auth(request, access_token)
    if not _require_permission(token_data, "api_keys:write"):
        raise HTTPException(status_code=403, detail="Se requiere permiso api_keys:write")

    key_id, full_key, key_hash = _generate_key()

    expires_at = None
    if payload.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=payload.expires_in_days)

    new_key = ApiKey(
        key_id    = key_id,
        key_hash  = key_hash,
        name      = payload.name,
        description = payload.description,
        scope     = payload.scope,
        tier      = payload.tier,
        permissions = payload.permissions,
        tenant_id  = payload.tenant_id,
        customer_id = payload.customer_id,
        created_by  = token_data.get("user_id"),
        expires_at  = expires_at,
        tags        = payload.tags,
        requests_per_minute  = payload.requests_per_minute,
        requests_per_day     = payload.requests_per_day,
        monthly_quota_tokens = payload.monthly_quota_tokens,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    return _key_summary(new_key, include_secret=full_key)


# ─────────────────────────────────────────────
# GET ONE
# ─────────────────────────────────────────────

@router.get("/{key_id}", summary="Detalle de API key")
def get_api_key(
    key_id: str,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    token_data = _auth(request, access_token)
    key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key no encontrada")

    _assert_tenant_access(token_data, key)
    return _key_summary(key)


# ─────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────

@router.put("/{key_id}", summary="Actualizar API key")
def update_api_key(
    key_id: str,
    payload: ApiKeyUpdate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    token_data = _auth(request, access_token)
    if not _require_permission(token_data, "api_keys:write"):
        raise HTTPException(status_code=403, detail="Se requiere permiso api_keys:write")

    key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key no encontrada")

    _assert_tenant_access(token_data, key)
    if key.status == ApiKeyStatus.revoked:
        raise HTTPException(status_code=409, detail="No se puede editar una key revocada")

    if payload.name is not None:
        key.name = payload.name
    if payload.description is not None:
        key.description = payload.description
    if payload.scope is not None:
        key.scope = payload.scope
    if payload.tier is not None:
        key.tier = payload.tier
    if payload.permissions is not None:
        key.permissions = payload.permissions
    if payload.tags is not None:
        key.tags = payload.tags
    if payload.expires_in_days is not None:
        key.expires_at = datetime.utcnow() + timedelta(days=payload.expires_in_days)
    if payload.requests_per_minute is not None:
        key.requests_per_minute = payload.requests_per_minute
    if payload.requests_per_day is not None:
        key.requests_per_day = payload.requests_per_day
    if payload.monthly_quota_tokens is not None:
        key.monthly_quota_tokens = payload.monthly_quota_tokens

    key.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(key)

    return _key_summary(key)


# ─────────────────────────────────────────────
# ROTATE  (Stripe-style)
# ─────────────────────────────────────────────

class RotationVerifyBody(BaseModel):
    verify_token: Optional[str] = None  # Requerido si quien rota es soporte


@router.post("/{key_id}/rotate", status_code=201, summary="Rotar API key")
def rotate_api_key(
    key_id: str,
    body: RotationVerifyBody,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Genera una nueva clave para el mismo recurso.
    La clave OLD pasa a estado `rotating` con 24h de gracia antes de ser revocada.
    La clave NUEVA hereda todos los atributos (tier, permisos, tenant…).
    El secreto completo se devuelve UNA sola vez.

    RBAC:
    - admin: puede rotar sin restricciones
    - support: SOLO puede rotar si existe un ApiKeyRotationRequest pendiente del tenant
      y se provee el verify_token correcto (enviado al tenant por email)
    - tenant (api_keys:rotate): puede rotar sus propias keys directamente
    """
    token_data = _auth(request, access_token)
    if not _require_permission(token_data, "api_keys:rotate"):
        raise HTTPException(status_code=403, detail="Se requiere permiso api_keys:rotate")

    old_key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if not old_key:
        raise HTTPException(status_code=404, detail="API key no encontrada")
    if old_key.status == ApiKeyStatus.revoked:
        raise HTTPException(status_code=409, detail="No se puede rotar una key ya revocada")

    _assert_tenant_access(token_data, old_key)

    # ── Validación especial para rol soporte ────────────────────────────────
    if _is_support(token_data):
        if not body.verify_token:
            raise HTTPException(
                status_code=403,
                detail="El rol soporte requiere verify_token (solicitado por el tenant desde módulo de correo)",
            )
        rot_req = db.query(ApiKeyRotationRequest).filter(
            ApiKeyRotationRequest.key_id       == key_id,
            ApiKeyRotationRequest.verify_token == body.verify_token,
            ApiKeyRotationRequest.status       == ApiKeyRotationStatus.pending,
        ).first()
        if not rot_req:
            raise HTTPException(
                status_code=403,
                detail="verify_token inválido o ya usado. El tenant debe solicitar la rotación desde el módulo de correo.",
            )
        if rot_req.expires_at < datetime.utcnow():
            rot_req.status = ApiKeyRotationStatus.expired
            db.commit()
            raise HTTPException(
                status_code=403,
                detail="La solicitud de rotación ha expirado. El tenant debe generar una nueva.",
            )
        # Marcar el request como aprobado
        rot_req.status         = ApiKeyRotationStatus.approved
        rot_req.support_user_id = token_data.get("user_id")
        rot_req.resolved_at    = datetime.utcnow()

    # Marcar la clave vieja como "rotating" (grace 24h)
    old_key.status    = ApiKeyStatus.rotating
    old_key.rotated_at = datetime.utcnow()
    old_key.expires_at = datetime.utcnow() + timedelta(hours=24)

    # Crear la nueva clave heredando los atributos
    new_id, new_full, new_hash = _generate_key()
    new_key = ApiKey(
        key_id    = new_id,
        key_hash  = new_hash,
        name      = old_key.name,
        description = old_key.description,
        scope     = old_key.scope,
        tier      = old_key.tier,
        permissions = list(old_key.permissions),
        tenant_id   = old_key.tenant_id,
        customer_id = old_key.customer_id,
        created_by  = token_data.get("user_id"),
        tags        = list(old_key.tags),
        requests_per_minute  = old_key.requests_per_minute,
        requests_per_day     = old_key.requests_per_day,
        monthly_quota_tokens = old_key.monthly_quota_tokens,
        rotation_old_key_id  = old_key.key_id,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    result = _key_summary(new_key, include_secret=new_full)
    result["rotated_from"] = key_id
    result["old_key_expires_at"] = old_key.expires_at.isoformat()
    result["_grace_note"] = "La clave anterior expirará en 24 horas. Actualiza tus integraciones."
    return result


# ─────────────────────────────────────────────
# REVOKE / DELETE
# ─────────────────────────────────────────────

@router.delete("/{key_id}", summary="Revocar API key")
def revoke_api_key(
    key_id: str,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    token_data = _auth(request, access_token)
    if not _require_permission(token_data, "api_keys:delete"):
        raise HTTPException(status_code=403, detail="Se requiere permiso api_keys:delete")

    key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key no encontrada")

    _assert_tenant_access(token_data, key)
    if _is_support(token_data):
        raise HTTPException(
            status_code=403,
            detail="El rol soporte no puede revocar keys directamente. Contacta al admin.",
        )

    key.status = ApiKeyStatus.revoked
    key.updated_at = datetime.utcnow()
    db.commit()

    return {"revoked": True, "key_id": key_id, "revoked_at": key.updated_at.isoformat()}


# ─────────────────────────────────────────────
# USAGE STATS (histograma por hora)
# ─────────────────────────────────────────────

@router.get("/{key_id}/usage", summary="Estadísticas de uso de una API key")
def get_key_usage(
    key_id: str,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    days: int = 7,
    db: Session = Depends(get_db),
):
    token_data = _auth(request, access_token)
    if not _require_permission(token_data, "api_keys:billing", "api_keys:read"):
        # También permite que el dueño vea sus propias stats
        uid = token_data.get("user_id")
        cid = token_data.get("customer_id")
        key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
        if not key or (key.created_by != uid and key.customer_id != cid):
            raise HTTPException(status_code=403, detail="Sin acceso a las estadísticas de esta key")

    key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key no encontrada")

    since = datetime.utcnow() - timedelta(days=days)
    logs = (
        db.query(ApiKeyUsageLog)
        .filter(ApiKeyUsageLog.key_id == key_id, ApiKeyUsageLog.hour_bucket >= since)
        .order_by(ApiKeyUsageLog.hour_bucket.asc())
        .all()
    )

    total_requests = sum(l.request_count for l in logs)
    total_tokens   = sum(l.token_count   for l in logs)
    total_errors   = sum(l.error_count   for l in logs)

    limits = _resolve_tier_limits(key)

    return {
        "key_id":   key_id,
        "tier":     key.tier.value,
        "period_days": days,
        "summary": {
            "total_requests":  total_requests,
            "total_tokens":    total_tokens,
            "total_errors":    total_errors,
            "usage_today":     key.usage_today,
            "usage_this_month": key.usage_this_month,
        },
        "rate_limits": limits,
        "hourly": [
            {
                "hour":     l.hour_bucket.isoformat(),
                "requests": l.request_count,
                "tokens":   l.token_count,
                "errors":   l.error_count,
                "endpoint": l.endpoint,
            }
            for l in logs
        ],
    }


# ─────────────────────────────────────────────
# ROTATION REQUEST (tenant inicia desde módulo correo)
# ─────────────────────────────────────────────

class RotationRequestBody(BaseModel):
    reason: Optional[str] = None   # nota opcional del tenant


@router.post("/{key_id}/request-rotation", status_code=201,
             summary="Solicitar rotación de key (tenant → soporte por email)")
def request_rotation(
    key_id: str,
    body: RotationRequestBody,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    El tenant solicita la rotación de su API key desde el módulo de correo.
    Genera un verify_token de un solo uso (TTL 24h) que se envía al tenant
    por email. El soporte deberá presentar ese token al llamar /rotate.
    """
    token_data   = _auth(request, access_token)
    tenant_token = _tenant_id_from_token(token_data)
    if not tenant_token and not _is_admin(token_data):
        raise HTTPException(status_code=403, detail="Solo tenants autenticados pueden solicitar rotación")

    key = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key no encontrada")

    _assert_tenant_access(token_data, key)
    if key.status == ApiKeyStatus.revoked:
        raise HTTPException(status_code=409, detail="No se puede solicitar rotación de una key revocada")

    # Cancelar solicitudes pendientes previas para la misma key
    db.query(ApiKeyRotationRequest).filter(
        ApiKeyRotationRequest.key_id == key_id,
        ApiKeyRotationRequest.status == ApiKeyRotationStatus.pending,
    ).update({"status": ApiKeyRotationStatus.expired, "resolved_at": datetime.utcnow()})

    verify_token = secrets.token_hex(32)
    rot_req = ApiKeyRotationRequest(
        key_id             = key_id,
        tenant_id          = key.tenant_id or tenant_token,
        customer_id        = key.customer_id,
        verify_token       = verify_token,
        requested_by_email = token_data.get("email") or token_data.get("sub", "unknown"),
        reason             = body.reason,
        expires_at         = datetime.utcnow() + timedelta(hours=24),
    )
    db.add(rot_req)
    db.commit()
    db.refresh(rot_req)

    # TODO: Enviar verify_token por email al tenant vía el servicio de comunicaciones
    # from ..services.communications import send_rotation_request_email
    # send_rotation_request_email(rot_req)

    return {
        "rotation_request_id": rot_req.id,
        "key_id":   key_id,
        "status":   "pending",
        "expires_at": rot_req.expires_at.isoformat(),
        "_note": (
            "Solicitud registrada. El equipo de soporte recibirá el token de verificación. "
            "Tienen 24 horas para ejecutar la rotación."
        ),
    }


@router.get("/{key_id}/rotation-requests", summary="Ver solicitudes de rotación (admin/soporte)")
def list_rotation_requests(
    key_id: str,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """Solo admin y soporte pueden ver el historial de solicitudes."""
    token_data = _auth(request, access_token)
    if not _is_admin(token_data) and not _is_support(token_data):
        raise HTTPException(status_code=403, detail="Se requiere rol admin o soporte")

    requests_ = (
        db.query(ApiKeyRotationRequest)
        .filter(ApiKeyRotationRequest.key_id == key_id)
        .order_by(ApiKeyRotationRequest.created_at.desc())
        .all()
    )
    return {
        "key_id": key_id,
        "requests": [
            {
                "id":               r.id,
                "status":           r.status.value,
                "requested_by":     r.requested_by_email,
                "reason":           r.reason,
                "reject_note":      r.reject_note,
                "tenant_id":        r.tenant_id,
                "created_at":       r.created_at.isoformat(),
                "expires_at":       r.expires_at.isoformat(),
                "resolved_at":      r.resolved_at.isoformat() if r.resolved_at else None,
                "support_user_id":  r.support_user_id,
            }
            for r in requests_
        ],
    }


# ─────────────────────────────────────────────
# VERIFY (uso interno — otros módulos pueden llamar esto)
# ─────────────────────────────────────────────

def verify_api_key(raw_key: str, db: Session) -> Optional[ApiKey]:
    """
    Verifica una API key cruda (formato: sk_live_<16>_<32>).
    Retorna el objeto ApiKey si es válida y activa, None en caso contrario.
    Actualiza contadores de uso en la misma transacción.
    """
    if not raw_key or not raw_key.startswith("sk_live_"):
        return None

    # Extraer key_id del formato sk_live_<prefix>_<secret>
    parts = raw_key.split("_")
    # sk  live  <prefix16>  <secret32>  → partes: ['sk', 'live', prefix, secret]
    if len(parts) < 4:
        return None

    key_id = f"sk_live_{parts[2]}"
    key_hash = _hash_key(raw_key)

    key = db.query(ApiKey).filter(
        ApiKey.key_id   == key_id,
        ApiKey.key_hash == key_hash,
        ApiKey.status.in_([ApiKeyStatus.active, ApiKeyStatus.rotating]),
    ).first()

    if not key:
        return None

    # Comprobar expiración
    if key.expires_at and key.expires_at < datetime.utcnow():
        key.status = ApiKeyStatus.expired
        db.commit()
        return None

    # Incrementar contadores
    key.total_requests  += 1
    key.usage_today     += 1
    key.usage_this_month += 1
    key.last_used_at    = datetime.utcnow()
    db.commit()

    return key
