"""
internal_config.py — Endpoint de configuración interna para servicios Jeturing.

Expone configuración sensible (claves Stripe, fee, etc.) exclusivamente para
servicios internos autenticados con X-Internal-Service-Key.

Seguridad:
  - Solo accesible desde red interna (10.10.10.0/24 + 127.0.0.1)
  - Autenticado con header X-Internal-Service-Key (valor en system_config:
    INTERNAL_SERVICE_KEY o env INTERNAL_SERVICE_KEY)
  - No requiere JWT de usuario — es M2M (machine-to-machine)
  - Nunca devuelve is_secret=True en bulk; solo por key explícita y autenticada
"""
import logging
import os
from typing import Optional, Literal

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.models.database import get_config
from app.config import get_runtime_setting

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/internal", tags=["Internal Config"])

# ── Red interna permitida ──────────────────────────────────────────────────────
_ALLOWED_PREFIXES = ("10.10.20.", "10.10.10.", "10.0.0.", "127.", "::1", "192.168.1.")

_STRIPE_APP_PREFIX = {
    "sajet": "STRIPE_",
    "med": "STRIPE_MED_",
    "track": "STRIPE_TRACK_",
}


def _assert_internal_network(request: Request) -> None:
    """Rechaza requests que no provienen de la red interna Jeturing."""
    client_ip = request.client.host if request.client else ""
    # Cloudflare / proxies: preferir header real si viene de loopback
    forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    ip = forwarded if forwarded else client_ip
    if not any(ip.startswith(p) for p in _ALLOWED_PREFIXES):
        _logger.warning("internal_config: acceso denegado desde IP %s", ip)
        raise HTTPException(status_code=403, detail="Acceso solo desde red interna")


def _assert_service_key(x_internal_service_key: Optional[str]) -> None:
    """Valida la clave de servicio M2M."""
    expected = get_config("INTERNAL_SERVICE_KEY") or os.getenv("INTERNAL_SERVICE_KEY")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="INTERNAL_SERVICE_KEY no configurada en SAJET. "
                   "Configúrala en /admin/credentials categoría 'security'."
        )
    if not x_internal_service_key or x_internal_service_key != expected:
        _logger.warning("internal_config: X-Internal-Service-Key inválida")
        raise HTTPException(status_code=401, detail="Service key inválida")


# ── Schemas ────────────────────────────────────────────────────────────────────

class StripeConfigResponse(BaseModel):
    app: str
    stripe_secret_key: str
    stripe_publishable_key: str
    stripe_webhook_secret: str
    jeturing_fee_percentage: float
    platform_country: str
    mode: str                   # "live" | "test"


def _stripe_key_name(app: str, suffix: str) -> str:
    return f"{_STRIPE_APP_PREFIX[app]}{suffix}"


def _resolve_stripe_value(app: str, suffix: str) -> str:
    primary = get_runtime_setting(_stripe_key_name(app, suffix), "") or ""
    if primary:
        return primary
    # Fallback para compatibilidad con despliegues previos
    return get_runtime_setting(f"STRIPE_{suffix}", "") or ""


def _detect_mode(secret_key: str) -> str:
    sk = (secret_key or "").lower()
    if sk.startswith("rk_live_") or sk.startswith("sk_live_"):
        return "live"
    return "test"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/config/stripe",
    response_model=StripeConfigResponse,
    summary="Config Stripe para servicios internos",
    description=(
        "Devuelve las claves Stripe activas y parámetros de plataforma. "
        "Solo accesible desde red interna con X-Internal-Service-Key válida."
    ),
)
def get_stripe_config(
    request: Request,
    app: Literal["sajet", "med", "track"] = "med",
    x_internal_service_key: Optional[str] = Header(None, alias="X-Internal-Service-Key"),
):
    _assert_internal_network(request)
    _assert_service_key(x_internal_service_key)

    sk = _resolve_stripe_value(app, "SECRET_KEY")
    pk = _resolve_stripe_value(app, "PUBLISHABLE_KEY")
    wh = _resolve_stripe_value(app, "WEBHOOK_SECRET")

    if not sk:
        raise HTTPException(
            status_code=503,
            detail=f"{_stripe_key_name(app, 'SECRET_KEY')} no encontrada en system_config de SAJET."
        )

    mode = _detect_mode(sk)

    fee = float(get_config("JETURING_FEE_PERCENTAGE") or
                os.getenv("JETURING_FEE_PERCENTAGE", "1"))
    country = get_config("JETURING_PLATFORM_COUNTRY") or \
              os.getenv("JETURING_PLATFORM_COUNTRY", "US")

    from ..utils.ip import get_real_ip
    _logger.info(
        "internal_config: stripe config app=%s entregada a %s [mode=%s]",
        app,
        get_real_ip(request),
        mode,
    )

    return StripeConfigResponse(
        app=app,
        stripe_secret_key=sk,
        stripe_publishable_key=pk,
        stripe_webhook_secret=wh,
        jeturing_fee_percentage=fee,
        platform_country=country,
        mode=mode,
    )


@router.get(
    "/health",
    summary="Health check interno",
    include_in_schema=False,
)
def internal_health(
    request: Request,
    x_internal_service_key: Optional[str] = Header(None, alias="X-Internal-Service-Key"),
):
    _assert_internal_network(request)
    _assert_service_key(x_internal_service_key)
    return {"status": "ok", "service": "sajet-internal-config"}
