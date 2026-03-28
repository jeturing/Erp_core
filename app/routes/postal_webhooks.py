"""
Postal Webhooks — Recibe eventos de delivery de Postal Mail Server.

Dirección: Postal (CT 200) → ERP Core
Eventos: MessageDelivered, MessageBounced, MessageFailed, MessageHeld

Configurar en Postal:
  Panel → Servidores → Sajet Relay → Webhooks → Agregar URL:
  https://api.sajet.us/api/v1/webhooks/postal-delivery
"""
import hashlib
import hmac
import logging
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request

from ..services.postal_service import (
    handle_postal_webhook,
    get_tenant_email_usage,
    get_all_tenants_email_usage_summary,
    sync_postal_stats,
)
from ..config import PROVISIONING_API_KEY, get_runtime_setting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["postal-webhooks"])


def _provisioning_api_key() -> str:
    return get_runtime_setting("PROVISIONING_API_KEY", PROVISIONING_API_KEY)


def _postal_webhook_secret() -> str:
    return get_runtime_setting("POSTAL_WEBHOOK_SECRET", "")


def _verify_postal_signature(body: bytes, signature: str) -> bool:
    """
    Verifica la firma HMAC-SHA256 del webhook de Postal.
    Postal envía: X-Postal-Signature: <hmac-sha256-hex>
    Si no está configurado POSTAL_WEBHOOK_SECRET se acepta todo (dev mode).
    """
    webhook_secret = _postal_webhook_secret()
    if not webhook_secret:
        return True
    expected = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/postal-delivery")
async def postal_delivery_webhook(
    request: Request,
    x_postal_signature: str = Header(default=""),
):
    """
    Recibe eventos de delivery de Postal.
    Actualiza postal_email_usage con el conteo y costo del tenant.
    """
    body = await request.body()

    if _postal_webhook_secret() and not _verify_postal_signature(body, x_postal_signature):
        logger.warning("Postal webhook: firma inválida rechazada")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        import json
        payload = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    result = handle_postal_webhook(payload)
    return result


# ──────────────────────────────────────────────
# Rutas admin — stats de uso (requieren API key)
# ──────────────────────────────────────────────

@router.get("/postal/usage/{tenant_subdomain}")
async def get_tenant_usage(
    tenant_subdomain: str,
    year: int = None,
    month: int = None,
    x_api_key: str = Header(default=""),
):
    """
    Retorna el uso de correo del tenant en el período.
    Requiere: X-Api-Key de administrador.
    """
    if x_api_key != _provisioning_api_key():
        raise HTTPException(status_code=403, detail="Forbidden")
    return get_tenant_email_usage(tenant_subdomain, year, month)


@router.get("/postal/usage-summary")
async def get_usage_summary(
    year: int = None,
    month: int = None,
    x_api_key: str = Header(default=""),
):
    """
    Resumen de uso de correo de todos los tenants.
    Útil para panel de facturación.
    """
    if x_api_key != _provisioning_api_key():
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"summary": get_all_tenants_email_usage_summary(year, month)}


@router.post("/postal/sync")
async def trigger_postal_sync(
    year: int = None,
    month: int = None,
    x_api_key: str = Header(default=""),
):
    """
    Dispara sincronización manual de estadísticas desde la API de Postal.
    """
    if x_api_key != _provisioning_api_key():
        raise HTTPException(status_code=403, detail="Forbidden")
    return await sync_postal_stats(year, month)
