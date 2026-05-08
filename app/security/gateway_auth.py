"""Gateway API key authentication helpers.

Dual-stack authentication:
- Managed API keys (sk_live_*) validated against ApiKey table.
- Legacy provisioning key validated from runtime config (temporary compatibility).
"""

from __future__ import annotations

from datetime import datetime, timezone
import hmac
import logging
from typing import Any, Callable

# Python 3.11+ compatibility
UTC = timezone.utc

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..config import PROVISIONING_API_KEY, get_runtime_setting
from ..models.database import get_db
from ..routes.api_keys import verify_api_key_detailed
from .api_scopes import ApiAccessLevel, has_level_permission, normalize_level
from ..services.api_key_audit import log_api_key_event
from ..services.rate_limiter import consume_rate_limit

logger = logging.getLogger(__name__)


def _expected_legacy_key() -> str:
    return str(get_runtime_setting("PROVISIONING_API_KEY", PROVISIONING_API_KEY) or "").strip()


def _is_valid_legacy_key(raw_key: str) -> bool:
    expected = _expected_legacy_key()
    if not expected:
        return False
    return hmac.compare_digest(raw_key, expected)


def _legacy_gateway_block_reason() -> str | None:
    """Returns block reason when legacy gateway key must be denied.

    Runtime settings:
    - LEGACY_GATEWAY_DISABLED: bool-like (default false)
    - LEGACY_GATEWAY_SUNSET_UTC: ISO datetime string (optional). If now >= sunset => blocked.
    """
    disabled_raw = str(get_runtime_setting("LEGACY_GATEWAY_DISABLED", "false") or "").strip().lower()
    if disabled_raw in {"1", "true", "t", "yes", "y", "on"}:
        return "legacy_gateway_disabled"

    sunset_raw = str(get_runtime_setting("LEGACY_GATEWAY_SUNSET_UTC", "") or "").strip()
    if not sunset_raw:
        return None

    try:
        parsed = datetime.fromisoformat(sunset_raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        now_utc = datetime.now(UTC)
        if now_utc >= parsed.astimezone(UTC):
            return "legacy_gateway_sunset"
    except Exception as exc:
        logger.warning("GW-010 invalid LEGACY_GATEWAY_SUNSET_UTC '%s': %s", sunset_raw, exc)

    return None


def _extract_client_ip(request: Request) -> str | None:
    remote = request.client.host if request.client else None
    xff = (request.headers.get("x-forwarded-for") or "").strip()
    xri = (request.headers.get("x-real-ip") or "").strip()

    # Trust forwarded headers only when request comes from local reverse proxy
    if remote in {"127.0.0.1", "::1", "localhost"}:
        if xff:
            return xff.split(",")[0].strip()
        if xri:
            return xri
    return remote


def _audit_event(
    db: Session,
    key_id: str,
    auth_mode: str,
    request: Request,
    status_code: int,
    reject_reason: str | None,
) -> None:
    try:
        client_ip = _extract_client_ip(request)
        log_api_key_event(
            db=db,
            key_id=key_id,
            auth_mode=auth_mode,
            path=request.url.path,
            method=request.method,
            ip_address=client_ip,
            status_code=status_code,
            reject_reason=reject_reason,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("GW-006 audit failed: %s", exc)


def _resolve_legacy_limits() -> tuple[int | None, int | None]:
    rpm_raw = str(get_runtime_setting("LEGACY_GATEWAY_RPM", "120") or "").strip()
    rpd_raw = str(get_runtime_setting("LEGACY_GATEWAY_RPD", "50000") or "").strip()

    rpm = int(rpm_raw) if rpm_raw.isdigit() and int(rpm_raw) > 0 else None
    rpd = int(rpd_raw) if rpd_raw.isdigit() and int(rpd_raw) > 0 else None
    return rpm, rpd


def _enforce_access_level(
    *,
    auth_mode: str,
    required_level: ApiAccessLevel,
    managed_permissions: list[str] | None,
) -> tuple[bool, str | None]:
    if required_level == ApiAccessLevel.INTERNAL:
        return True, None

    if auth_mode == "legacy_provisioning_key":
        if required_level in {ApiAccessLevel.INTERNAL, ApiAccessLevel.PARTNER}:
            return True, None
        return False, "insufficient_scope_sensitive"

    if auth_mode == "managed_api_key":
        if has_level_permission(managed_permissions, required_level):
            return True, None
        return False, "insufficient_scope"

    return False, "insufficient_scope"


def require_gateway_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
    required_level: ApiAccessLevel = ApiAccessLevel.INTERNAL,
) -> dict[str, Any]:
    """Enforces gateway authentication using API key header.

    Returns auth metadata and stores it in request.state for downstream usage.
    """
    required_level = normalize_level(required_level)
    raw_key = (x_api_key or request.headers.get("x-api-key") or "").strip()
    if not raw_key:
        _audit_event(
            db=db,
            key_id="missing",
            auth_mode="unknown",
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            reject_reason="missing_api_key",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key requerida")

    if raw_key.startswith("sk_live_"):
        client_ip = _extract_client_ip(request)
        managed_key, reason = verify_api_key_detailed(
            raw_key=raw_key,
            db=db,
            endpoint=request.url.path,
            ip_address=client_ip,
        )

        if managed_key is None:
            if reason in {"rate_limit_minute", "rate_limit_day", "quota_month"}:
                _audit_event(
                    db=db,
                    key_id="managed-unknown",
                    auth_mode="managed_api_key",
                    request=request,
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    reject_reason=reason,
                )
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=reason)
            if reason == "expired":
                _audit_event(
                    db=db,
                    key_id="managed-unknown",
                    auth_mode="managed_api_key",
                    request=request,
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    reject_reason="expired",
                )
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expirada")
            _audit_event(
                db=db,
                key_id="managed-unknown",
                auth_mode="managed_api_key",
                request=request,
                status_code=status.HTTP_401_UNAUTHORIZED,
                reject_reason=reason or "invalid_api_key",
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")

        allowed, deny_reason = _enforce_access_level(
            auth_mode="managed_api_key",
            required_level=required_level,
            managed_permissions=list(managed_key.permissions or []),
        )
        if not allowed:
            _audit_event(
                db=db,
                key_id=managed_key.key_id,
                auth_mode="managed_api_key",
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                reject_reason=deny_reason,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="scope_denied")

        auth_info = {
            "auth_mode": "managed_api_key",
            "key_id": managed_key.key_id,
            "tenant_id": managed_key.tenant_id,
            "customer_id": managed_key.customer_id,
            "required_level": required_level.value,
        }
        _audit_event(
            db=db,
            key_id=managed_key.key_id,
            auth_mode="managed_api_key",
            request=request,
            status_code=status.HTTP_200_OK,
            reject_reason=None,
        )
        request.state.gateway_auth = auth_info
        return auth_info

    if _is_valid_legacy_key(raw_key):
        block_reason = _legacy_gateway_block_reason()
        if block_reason:
            _audit_event(
                db=db,
                key_id="legacy-provisioning",
                auth_mode="legacy_provisioning_key",
                request=request,
                status_code=410,
                reject_reason=block_reason,
            )
            raise HTTPException(status_code=410, detail="legacy_key_sunset")

        rpm, rpd = _resolve_legacy_limits()
        legacy_decision = consume_rate_limit(
            identifier="legacy-provisioning",
            rpm=rpm,
            rpd=rpd,
        )
        if not legacy_decision.allowed:
            _audit_event(
                db=db,
                key_id="legacy-provisioning",
                auth_mode="legacy_provisioning_key",
                request=request,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                reject_reason=legacy_decision.reason or "rate_limit_exceeded",
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=legacy_decision.reason or "rate_limit_exceeded",
            )

        allowed, deny_reason = _enforce_access_level(
            auth_mode="legacy_provisioning_key",
            required_level=required_level,
            managed_permissions=None,
        )
        if not allowed:
            _audit_event(
                db=db,
                key_id="legacy-provisioning",
                auth_mode="legacy_provisioning_key",
                request=request,
                status_code=status.HTTP_403_FORBIDDEN,
                reject_reason=deny_reason,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="scope_denied")

        auth_info = {
            "auth_mode": "legacy_provisioning_key",
            "key_id": "legacy-provisioning",
            "tenant_id": None,
            "customer_id": None,
            "required_level": required_level.value,
        }
        _audit_event(
            db=db,
            key_id="legacy-provisioning",
            auth_mode="legacy_provisioning_key",
            request=request,
            status_code=status.HTTP_200_OK,
            reject_reason=None,
        )
        request.state.gateway_auth = auth_info
        return auth_info

    _audit_event(
        db=db,
        key_id="invalid",
        auth_mode="unknown",
        request=request,
        status_code=status.HTTP_401_UNAUTHORIZED,
        reject_reason="invalid_api_key",
    )
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")


def gateway_api_key_dependency(
    required_level: ApiAccessLevel | str = ApiAccessLevel.INTERNAL,
) -> Callable[..., dict[str, Any]]:
    level = normalize_level(required_level)

    def _dependency(
        request: Request,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return require_gateway_api_key(
            request=request,
            x_api_key=x_api_key,
            db=db,
            required_level=level,
        )

    return _dependency
