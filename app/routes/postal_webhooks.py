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
from typing import Any, Dict, Optional

from fastapi import APIRouter, Cookie, Header, HTTPException, Request
from pydantic import BaseModel

from ..services.postal_service import (
    handle_postal_webhook,
    get_tenant_email_usage,
    get_all_tenants_email_usage_summary,
    sync_postal_stats,
)
from ..config import PROVISIONING_API_KEY, get_runtime_setting
from ..models.database import SessionLocal, ServiceCatalogItem, ServiceCategory
from .roles import _require_admin

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


# ──────────────────────────────────────────────────────────────────
# Admin CRUD — Email Packages en el catálogo de servicios
# Requieren sesión admin activa (cookie access_token)
# ──────────────────────────────────────────────────────────────────

EMAIL_PACKAGE_SERVICE_CODE = "postal_email_package"


class EmailPackageCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price_monthly: float
    email_quota_monthly: int          # correos incluidos por mes
    email_burst_limit_60m: int = 500  # límite de envío en ventana 60 min
    email_overage_price: float = 0.00020  # USD por correo extra
    sort_order: int = 0


def _email_pkg_to_dict(item: ServiceCatalogItem) -> dict:
    meta = item.metadata_json or {}
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price_monthly": item.price_monthly,
        "is_active": item.is_active,
        "sort_order": item.sort_order,
        "service_code": item.service_code,
        "email_quota_monthly": meta.get("email_quota_monthly", 0),
        "email_burst_limit_60m": meta.get("email_burst_limit_60m", 500),
        "email_overage_price": meta.get("email_overage_price", 0.00020),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("/admin/email-packages")
async def list_email_packages(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    include_inactive: bool = False,
):
    """Lista los paquetes de correo del catálogo."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(ServiceCatalogItem).filter(
            ServiceCatalogItem.service_code == EMAIL_PACKAGE_SERVICE_CODE,
        )
        if not include_inactive:
            q = q.filter(ServiceCatalogItem.is_active == True)
        items = q.order_by(ServiceCatalogItem.sort_order, ServiceCatalogItem.id).all()
        return {"items": [_email_pkg_to_dict(i) for i in items], "total": len(items)}
    finally:
        db.close()


@router.post("/admin/email-packages")
async def create_email_package(
    payload: EmailPackageCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Crea un paquete de correo en el catálogo."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = ServiceCatalogItem(
            category=ServiceCategory.email_service,
            name=payload.name,
            description=payload.description,
            unit="correos/mes",
            price_monthly=payload.price_monthly,
            is_addon=True,
            service_code=EMAIL_PACKAGE_SERVICE_CODE,
            metadata_json={
                "email_quota_monthly": payload.email_quota_monthly,
                "email_burst_limit_60m": payload.email_burst_limit_60m,
                "email_overage_price": payload.email_overage_price,
            },
            sort_order=payload.sort_order,
            is_active=True,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"message": "Paquete de correo creado", "item": _email_pkg_to_dict(item)}
    finally:
        db.close()


@router.put("/admin/email-packages/{item_id}")
async def update_email_package(
    item_id: int,
    payload: EmailPackageCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Actualiza un paquete de correo existente."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = db.query(ServiceCatalogItem).filter(
            ServiceCatalogItem.id == item_id,
            ServiceCatalogItem.service_code == EMAIL_PACKAGE_SERVICE_CODE,
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Paquete no encontrado")

        item.name = payload.name
        item.description = payload.description
        item.price_monthly = payload.price_monthly
        item.sort_order = payload.sort_order
        item.metadata_json = {
            "email_quota_monthly": payload.email_quota_monthly,
            "email_burst_limit_60m": payload.email_burst_limit_60m,
            "email_overage_price": payload.email_overage_price,
        }
        db.commit()
        db.refresh(item)
        return {"message": "Paquete actualizado", "item": _email_pkg_to_dict(item)}
    finally:
        db.close()


@router.delete("/admin/email-packages/{item_id}")
async def deactivate_email_package(
    item_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Desactiva (soft-delete) un paquete de correo."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = db.query(ServiceCatalogItem).filter(
            ServiceCatalogItem.id == item_id,
            ServiceCatalogItem.service_code == EMAIL_PACKAGE_SERVICE_CODE,
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Paquete no encontrado")
        item.is_active = False
        db.commit()
        return {"message": "Paquete desactivado"}
    finally:
        db.close()


@router.put("/admin/email-packages/{item_id}/reactivate")
async def reactivate_email_package(
    item_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Reactiva un paquete de correo desactivado."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        item = db.query(ServiceCatalogItem).filter(
            ServiceCatalogItem.id == item_id,
            ServiceCatalogItem.service_code == EMAIL_PACKAGE_SERVICE_CODE,
        ).first()
        if not item:
            raise HTTPException(status_code=404, detail="Paquete no encontrado")
        item.is_active = True
        db.commit()
        return {"message": "Paquete reactivado", "item": _email_pkg_to_dict(item)}
    finally:
        db.close()
