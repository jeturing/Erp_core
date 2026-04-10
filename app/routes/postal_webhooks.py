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
from ..services.postal_rate_limiter import (
    check_rate_limit,
    record_email_sent,
    get_rate_limit_status,
    resolve_email_limits,
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
# Rate Limiting API — Para bridges SMTP en PCTs remotos
# Requieren: X-Api-Key de provisioning (interno, no expuesto)
# ──────────────────────────────────────────────────────────────────

class RateLimitCheckRequest(BaseModel):
    tenant_subdomain: str
    n_emails: int = 1


@router.post("/postal/rate-limit/check")
async def rate_limit_check(
    payload: RateLimitCheckRequest,
    x_api_key: str = Header(default=""),
):
    """
    Verifica si un tenant puede enviar n emails ahora.
    Usado por los bridges SMTP de PCT 105/110 antes de forwarding.
    Retorna: {allowed: bool, reason: str, limits: dict}
    """
    if x_api_key != _provisioning_api_key():
        raise HTTPException(status_code=403, detail="Forbidden")
    db = SessionLocal()
    try:
        allowed, reason = check_rate_limit(
            db, payload.tenant_subdomain, n_emails=payload.n_emails
        )
        return {"allowed": allowed, "reason": reason}
    finally:
        db.close()


@router.post("/postal/rate-limit/record")
async def rate_limit_record(
    payload: RateLimitCheckRequest,
    x_api_key: str = Header(default=""),
):
    """
    Registra n emails enviados para un tenant en las ventanas de rate limiting.
    Llamado por el bridge SMTP DESPUÉS de enviar exitosamente vía Postal.
    """
    if x_api_key != _provisioning_api_key():
        raise HTTPException(status_code=403, detail="Forbidden")
    db = SessionLocal()
    try:
        record_email_sent(db, payload.tenant_subdomain, payload.n_emails)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error recording rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/postal/rate-limit/status/{tenant_subdomain}")
async def rate_limit_status(
    tenant_subdomain: str,
    x_api_key: str = Header(default=""),
):
    """
    Retorna el estado de rate limiting de un tenant (uso actual vs límites).
    """
    if x_api_key != _provisioning_api_key():
        raise HTTPException(status_code=403, detail="Forbidden")
    db = SessionLocal()
    try:
        status = get_rate_limit_status(db, tenant_subdomain)
        limits = resolve_email_limits(db, tenant_subdomain)
        return {"status": status, "effective_limits": limits}
    finally:
        db.close()


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


# ──────────────────────────────────────────────────────────────────
# Provisioning API — Llamado por módulo Odoo jeturing_postal_limit
# Actualiza partner_pricing_overrides con los límites del plan comprado
# ──────────────────────────────────────────────────────────────────

class ProvisionEmailLimitsRequest(BaseModel):
    tenant_subdomain: str
    max_emails_monthly: int
    email_rate_per_minute: int
    email_rate_per_hour: int
    email_rate_per_day: int
    plan_label: str = ""


@router.post("/postal/provision-email-limits")
async def provision_email_limits(
    payload: ProvisionEmailLimitsRequest,
    x_api_key: str = Header(default=""),
):
    """
    Aprovisiona límites de correo para un tenant.
    Llamado por el módulo Odoo jeturing_postal_limit cuando un partner compra un plan.

    Flujo:
      1. Busca el customer por subdomain
      2. Busca/crea el partner_pricing_override correspondiente
      3. Actualiza los campos email_rate_* con los valores del plan
      4. Si plan_label == '__reset__', pone los overrides en NULL (vuelta a defaults)
    """
    if x_api_key != _provisioning_api_key():
        raise HTTPException(status_code=403, detail="Forbidden")

    from ..models.database import Customer, PartnerPricingOverride

    db = SessionLocal()
    try:
        # 1. Buscar customer
        customer = (
            db.query(Customer)
            .filter(Customer.subdomain == payload.tenant_subdomain)
            .first()
        )
        if not customer:
            raise HTTPException(
                status_code=404,
                detail=f"Tenant '{payload.tenant_subdomain}' no encontrado en SAJET"
            )
        if not customer.partner_id:
            raise HTTPException(
                status_code=400,
                detail=f"Tenant '{payload.tenant_subdomain}' no tiene partner asociado"
            )

        # 2. Resolver plan_name del customer
        plan_name = getattr(customer, "plan", None)
        if plan_name:
            if hasattr(plan_name, "value"):
                plan_name = plan_name.value
        if not plan_name:
            plan_name = "pro"  # fallback

        # 3. Buscar o crear override
        override = (
            db.query(PartnerPricingOverride)
            .filter(
                PartnerPricingOverride.partner_id == customer.partner_id,
                PartnerPricingOverride.plan_name == plan_name,
            )
            .first()
        )

        if payload.plan_label == "__reset__":
            # Reset: poner overrides en NULL para volver a defaults del plan
            if override:
                override.max_emails_monthly_override = None
                override.email_rate_per_minute_override = None
                override.email_rate_per_hour_override = None
                override.email_rate_per_day_override = None
                override.label = None
                db.commit()
            return {
                "success": True,
                "message": "Límites reseteados a valores del plan",
                "tenant": payload.tenant_subdomain,
            }

        if not override:
            override = PartnerPricingOverride(
                partner_id=customer.partner_id,
                plan_name=plan_name,
                is_active=True,
            )
            db.add(override)

        # 4. Actualizar límites
        override.max_emails_monthly_override = payload.max_emails_monthly
        override.email_rate_per_minute_override = payload.email_rate_per_minute
        override.email_rate_per_hour_override = payload.email_rate_per_hour
        override.email_rate_per_day_override = payload.email_rate_per_day
        override.label = f"Postal Plan: {payload.plan_label}"

        db.commit()

        # Verificar que los límites se resuelven correctamente
        effective = resolve_email_limits(db, payload.tenant_subdomain)

        logger.info(
            "✅ Provisioned email limits for %s: %s/month, %s/min, %s/hr, %s/day (plan: %s)",
            payload.tenant_subdomain,
            payload.max_emails_monthly,
            payload.email_rate_per_minute,
            payload.email_rate_per_hour,
            payload.email_rate_per_day,
            payload.plan_label,
        )

        return {
            "success": True,
            "message": f"Límites aprovisionados para {payload.tenant_subdomain}",
            "tenant": payload.tenant_subdomain,
            "plan_label": payload.plan_label,
            "provisioned_limits": {
                "max_emails_monthly": payload.max_emails_monthly,
                "email_rate_per_minute": payload.email_rate_per_minute,
                "email_rate_per_hour": payload.email_rate_per_hour,
                "email_rate_per_day": payload.email_rate_per_day,
            },
            "effective_limits": effective,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("Error provisioning email limits: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
