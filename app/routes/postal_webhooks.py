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
from ..services.addon_billing_service import purchase_customer_addon
from ..services.stripe_billing import create_checkout_for_invoice
from ..config import PROVISIONING_API_KEY, get_runtime_setting
from ..models.database import (
    SessionLocal,
    ServiceCatalogItem,
    ServiceCategory,
    Customer,
    Subscription,
    CustomerAddonSubscription,
    Invoice,
    InvoiceType,
    InvoiceStatus,
)
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


def _build_email_limits_metadata(
    *,
    email_quota_monthly: int,
    email_burst_limit_60m: int,
    email_overage_price: float,
) -> dict:
    """
    Estandariza metadata para paquetes de correo.

    Mantiene compatibilidad hacia atrás con keys históricas
    (email_quota_monthly / email_burst_limit_60m) y además
    publica las keys canónicas usadas por el rate limiter:
      - max_emails_monthly
      - email_rate_per_minute
      - email_rate_per_hour
      - email_rate_per_day
    """
    quota = max(0, int(email_quota_monthly or 0))
    burst_60m = max(0, int(email_burst_limit_60m or 0))
    per_hour = burst_60m
    per_minute = max(1, per_hour // 60) if per_hour > 0 else 0
    per_day = min(quota, per_hour * 24) if (quota > 0 and per_hour > 0) else (quota or per_hour * 24)

    return {
        "kind": EMAIL_PACKAGE_SERVICE_CODE,
        # Keys legacy (UI/compat)
        "email_quota_monthly": quota,
        "email_burst_limit_60m": burst_60m,
        "email_overage_price": float(email_overage_price or 0.00020),
        # Keys canónicas (rate limiter)
        "max_emails_monthly": quota,
        "email_rate_per_minute": per_minute,
        "email_rate_per_hour": per_hour,
        "email_rate_per_day": per_day,
    }


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
            metadata_json=_build_email_limits_metadata(
                email_quota_monthly=payload.email_quota_monthly,
                email_burst_limit_60m=payload.email_burst_limit_60m,
                email_overage_price=payload.email_overage_price,
            ),
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
        item.metadata_json = _build_email_limits_metadata(
            email_quota_monthly=payload.email_quota_monthly,
            email_burst_limit_60m=payload.email_burst_limit_60m,
            email_overage_price=payload.email_overage_price,
        )
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


class AssignTenantEmailPackageRequest(BaseModel):
    customer_id: int
    catalog_item_id: int
    quantity: int = 1
    charge_now: bool = True
    notes: Optional[str] = None


@router.get("/admin/email-packages/tenant-overview")
async def admin_email_tenant_overview(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    search: str = "",
    limit: int = 100,
    offset: int = 0,
):
    """
    Vista administrativa por tenant para perfiles/cobros de correo.
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(Customer)
        if search:
            like = f"%{search.strip()}%"
            q = q.filter(
                (Customer.company_name.ilike(like)) |
                (Customer.subdomain.ilike(like)) |
                (Customer.email.ilike(like))
            )

        total = q.count()
        customers = (
            q.order_by(Customer.id.desc())
            .offset(max(0, offset))
            .limit(max(1, min(limit, 500)))
            .all()
        )

        items = []
        for customer in customers:
            sub = (
                db.query(Subscription)
                .filter(Subscription.customer_id == customer.id)
                .order_by(Subscription.id.desc())
                .first()
            )

            addon = (
                db.query(CustomerAddonSubscription)
                .filter(
                    CustomerAddonSubscription.customer_id == customer.id,
                    CustomerAddonSubscription.service_code == EMAIL_PACKAGE_SERVICE_CODE,
                    CustomerAddonSubscription.status == "active",
                )
                .order_by(CustomerAddonSubscription.id.desc())
                .first()
            )

            package_item = addon.catalog_item if addon else None
            effective_limits = resolve_email_limits(db, customer.subdomain)

            pending_invoice_count = 0
            pending_invoice_total = 0.0
            pending_invoices = (
                db.query(Invoice)
                .filter(
                    Invoice.customer_id == customer.id,
                    Invoice.invoice_type == InvoiceType.ADDON,
                    Invoice.status.in_([
                        InvoiceStatus.draft,
                        InvoiceStatus.issued,
                        InvoiceStatus.overdue,
                    ]),
                )
                .all()
            )
            if pending_invoices:
                pending_invoice_count = len(pending_invoices)
                pending_invoice_total = float(sum(float(inv.total or 0) for inv in pending_invoices))

            items.append({
                "customer_id": customer.id,
                "company_name": customer.company_name,
                "subdomain": customer.subdomain,
                "email": customer.email,
                "partner_id": customer.partner_id,
                "plan": customer.plan.value if hasattr(customer.plan, "value") else customer.plan,
                "subscription_id": sub.id if sub else None,
                "billing_mode": sub.billing_mode.value if (sub and sub.billing_mode) else None,
                "active_email_profile": {
                    "addon_id": addon.id,
                    "catalog_item_id": addon.catalog_item_id,
                    "name": package_item.name if package_item else None,
                    "quantity": addon.quantity,
                    "unit_price_monthly": addon.unit_price_monthly,
                    "starts_at": addon.starts_at.isoformat() if addon.starts_at else None,
                } if addon else None,
                "effective_limits": effective_limits,
                "pending_addon_invoices": {
                    "count": pending_invoice_count,
                    "total": round(pending_invoice_total, 6),
                    "currency": sub.currency if (sub and sub.currency) else "USD",
                },
            })

        packages = (
            db.query(ServiceCatalogItem)
            .filter(
                ServiceCatalogItem.service_code == EMAIL_PACKAGE_SERVICE_CODE,
                ServiceCatalogItem.is_active == True,
            )
            .order_by(ServiceCatalogItem.sort_order, ServiceCatalogItem.id)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "packages": [_email_pkg_to_dict(pkg) for pkg in packages],
        }
    finally:
        db.close()


@router.post("/admin/email-packages/assign")
async def admin_assign_email_package_to_tenant(
    payload: AssignTenantEmailPackageRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Asigna (compra) un perfil de correo a un tenant.

    - Partners: se agrega a su facturación regular (invoice ADDON).
    - Clientes directos: opcionalmente retorna checkout inmediato (charge_now=true).
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        item = (
            db.query(ServiceCatalogItem)
            .filter(
                ServiceCatalogItem.id == payload.catalog_item_id,
                ServiceCatalogItem.service_code == EMAIL_PACKAGE_SERVICE_CODE,
                ServiceCatalogItem.is_active == True,
            )
            .first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Paquete de correo no encontrado")

        result = purchase_customer_addon(
            db=db,
            customer_id=customer.id,
            catalog_item_id=item.id,
            quantity=max(1, int(payload.quantity or 1)),
            acquired_via="admin_email_profiles",
            notes=payload.notes or "Asignación manual desde consola admin",
        )

        charge = None
        invoice_data = result.get("invoice") if isinstance(result, dict) else None
        is_direct_customer = customer.partner_id is None
        if payload.charge_now and is_direct_customer and invoice_data and invoice_data.get("id"):
            inv = db.query(Invoice).filter(Invoice.id == int(invoice_data["id"])).first()
            if inv:
                checkout = create_checkout_for_invoice(db, inv)
                charge = {
                    "required": True,
                    "checkout_url": checkout.get("checkout_url"),
                    "method": checkout.get("method", "checkout_session"),
                }

        effective_limits = resolve_email_limits(db, customer.subdomain)

        return {
            "message": "Perfil de correo asignado correctamente",
            "customer": {
                "id": customer.id,
                "company_name": customer.company_name,
                "subdomain": customer.subdomain,
                "partner_id": customer.partner_id,
            },
            "assignment": result,
            "charge": charge,
            "effective_limits": effective_limits,
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        db.close()


@router.put("/admin/email-packages/tenant-subscriptions/{addon_id}")
async def admin_update_tenant_email_subscription(
    addon_id: int,
    quantity: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Actualiza cantidad de una suscripción de perfil de correo activa."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        addon = (
            db.query(CustomerAddonSubscription)
            .filter(
                CustomerAddonSubscription.id == addon_id,
                CustomerAddonSubscription.service_code == EMAIL_PACKAGE_SERVICE_CODE,
                CustomerAddonSubscription.status == "active",
            )
            .first()
        )
        if not addon:
            raise HTTPException(status_code=404, detail="Suscripción de correo no encontrada")
        addon.quantity = max(1, int(quantity or 1))
        db.commit()
        return {"message": "Suscripción actualizada", "addon_id": addon.id, "quantity": addon.quantity}
    finally:
        db.close()


@router.delete("/admin/email-packages/tenant-subscriptions/{addon_id}")
async def admin_deactivate_tenant_email_subscription(
    addon_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Desactiva el perfil de correo de un tenant (fallback a límites base)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        addon = (
            db.query(CustomerAddonSubscription)
            .filter(
                CustomerAddonSubscription.id == addon_id,
                CustomerAddonSubscription.service_code == EMAIL_PACKAGE_SERVICE_CODE,
                CustomerAddonSubscription.status == "active",
            )
            .first()
        )
        if not addon:
            raise HTTPException(status_code=404, detail="Suscripción de correo no encontrada")

        addon.status = "cancelled"
        db.commit()
        return {"message": "Perfil de correo desactivado", "addon_id": addon.id}
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
