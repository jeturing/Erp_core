"""
Quotas API — Phase 2: Resource Quotas
Endpoints para consultar y verificar cuotas de recursos por cliente.
"""
from fastapi import APIRouter, HTTPException, Request, Cookie, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..models.database import (
    SessionLocal,
    Customer,
    ServiceCatalogItem,
    CustomerAddonSubscription,
    Subscription,
    SubscriptionStatus,
)
from ..services.quota_service import QuotaService
from ..services.postal_rate_limiter import resolve_email_limits
from .roles import verify_token_with_role
import logging

router = APIRouter(prefix="/api/quotas", tags=["Quotas"])
logger = logging.getLogger(__name__)
EMAIL_PACKAGE_SERVICE_CODE = "postal_email_package"


def _verify_admin(request: Request, token: str = None):
    """Extrae y verifica token de admin."""
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    verify_token_with_role(token, required_role="admin")


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.get("/{customer_id}")
async def get_customer_quotas(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Retorna el estado consolidado de todas las cuotas de un cliente.
    Incluye: límite del plan, uso actual, porcentaje, si puede agregar más.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        result = svc.get_customer_quotas(customer_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Error"))
        return result
    finally:
        db.close()


@router.get("/{customer_id}/{resource}")
async def get_resource_quota(
    customer_id: int,
    resource: str,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Retorna la cuota de un recurso específico para un cliente.
    Recursos: users, domains, websites, companies, storage_mb, backups, api_calls.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        result = svc.get_resource_quota(customer_id, resource)
        if not result.get("success"):
            raise HTTPException(
                status_code=400 if "desconocido" in result.get("error", "") else 404,
                detail=result.get("error", "Error"),
            )
        return result
    finally:
        db.close()


@router.get("/{customer_id}/check/{resource}")
async def check_quota(
    customer_id: int,
    resource: str,
    request: Request,
    access_token: str = Cookie(None),
    increment: int = Query(1, ge=1, description="Unidades a agregar"),
) -> Dict[str, Any]:
    """
    Verifica si el cliente puede agregar N unidades de un recurso.
    Retorna allowed=True si puede, 403 si no.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        result = svc.check_quota(customer_id, resource, increment)
        if not result.get("success"):
            if result.get("allowed") is False:
                raise HTTPException(status_code=403, detail=result.get("message", "Cuota excedida"))
            raise HTTPException(status_code=400, detail=result.get("error", "Error"))
        return result
    finally:
        db.close()


@router.get("")
async def get_all_quotas(
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Retorna resumen de cuotas de todos los clientes (admin dashboard).
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        customers = svc.get_all_customers_quotas()
        return {
            "success": True,
            "total": len(customers),
            "customers": customers,
        }
    finally:
        db.close()


class CustomerEmailLimitsUpdate(BaseModel):
    max_emails_monthly: int
    email_rate_per_minute: int
    email_rate_per_hour: int
    email_rate_per_day: int


@router.get("/{customer_id}/email-limits")
async def get_customer_email_limits(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Devuelve límites efectivos de correo para un tenant."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

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

        return {
            "success": True,
            "customer_id": customer.id,
            "subdomain": customer.subdomain,
            "limits": resolve_email_limits(db, customer.subdomain),
            "source": "addon" if addon else "plan_or_partner",
            "addon_id": addon.id if addon else None,
            "metadata": addon.metadata_json if addon and addon.metadata_json else {},
        }
    finally:
        db.close()


@router.put("/{customer_id}/email-limits")
async def update_customer_email_limits(
    customer_id: int,
    payload: CustomerEmailLimitsUpdate,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Actualiza límites de correo por tenant.
    Persistencia: metadata_json en addon activo `postal_email_package`.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

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

        if not addon:
            item = (
                db.query(ServiceCatalogItem)
                .filter(
                    ServiceCatalogItem.service_code == EMAIL_PACKAGE_SERVICE_CODE,
                    ServiceCatalogItem.is_active == True,
                )
                .order_by(ServiceCatalogItem.sort_order, ServiceCatalogItem.id)
                .first()
            )
            if not item:
                raise HTTPException(
                    status_code=404,
                    detail="No hay paquetes de correo activos en catálogo",
                )

            active_subscription = (
                db.query(Subscription)
                .filter(
                    Subscription.customer_id == customer.id,
                    Subscription.status.in_([
                        SubscriptionStatus.active,
                        SubscriptionStatus.pending,
                        SubscriptionStatus.trialing,
                        SubscriptionStatus.past_due,
                    ]),
                )
                .order_by(Subscription.created_at.desc())
                .first()
            )

            addon = CustomerAddonSubscription(
                customer_id=customer.id,
                subscription_id=active_subscription.id if active_subscription else None,
                partner_id=customer.partner_id,
                catalog_item_id=item.id,
                status="active",
                quantity=1,
                unit_price_monthly=float(item.price_monthly or 0),
                currency="USD",
                service_code=EMAIL_PACKAGE_SERVICE_CODE,
                acquired_via="admin_quota_override",
                starts_at=datetime.utcnow(),
            )
            db.add(addon)
            db.flush()

        metadata = dict(addon.metadata_json or {})
        metadata.update({
            "kind": EMAIL_PACKAGE_SERVICE_CODE,
            "max_emails_monthly": int(payload.max_emails_monthly),
            "email_rate_per_minute": int(payload.email_rate_per_minute),
            "email_rate_per_hour": int(payload.email_rate_per_hour),
            "email_rate_per_day": int(payload.email_rate_per_day),
            # Compat keys legacy
            "email_quota_monthly": int(payload.max_emails_monthly),
            "email_burst_limit_60m": int(payload.email_rate_per_hour),
        })
        addon.metadata_json = metadata

        db.commit()

        return {
            "success": True,
            "message": "Límites de correo actualizados",
            "customer_id": customer.id,
            "subdomain": customer.subdomain,
            "addon_id": addon.id,
            "limits": resolve_email_limits(db, customer.subdomain),
        }
    finally:
        db.close()
