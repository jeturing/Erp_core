"""
Rutas API para gestión de Cloudflare Tunnels
Usa la API REST de Cloudflare v4 (sin dependencia de cloudflared CLI).
"""
from fastapi import APIRouter, HTTPException, Cookie, Query
from typing import Dict, Any, Optional
import logging

from ..services.cloudflare_manager import CloudflareManager
from ..services.tunnel_lifecycle import (
    link_tunnel_to_customer,
    sync_tunnel_lifecycle,
    sync_all_tunnels,
    get_customer_tunnel_info,
    provision_tunnel_for_customer,
)
from ..models.database import SessionLocal, TenantDeployment, Subscription, Customer
from ..security.tokens import TokenManager
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tunnels", tags=["tunnels"])


def verify_admin(access_token: str) -> bool:
    """Verifica que el token sea de admin"""
    if not access_token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        payload = TokenManager.verify_access_token(access_token)
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return True
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# ═══════════════════════════════════════════════════════
# DTOs
# ═══════════════════════════════════════════════════════

class LinkTunnelRequest(BaseModel):
    """Vincular un tunnel de Cloudflare a un tenant deployment."""
    deployment_id: int = Field(..., description="ID del TenantDeployment a vincular")


class LinkStripeRequest(BaseModel):
    """Vincular un deployment a una suscripción Stripe."""
    subscription_id: int = Field(..., description="ID de la Subscription local")


class LinkCustomerRequest(BaseModel):
    """Vincular un tunnel directamente a un cliente."""
    customer_id: int = Field(..., description="ID del cliente")
    deployment_id: Optional[int] = Field(None, description="ID del deployment (auto-detecta si no se envía)")


class ProvisionTunnelRequest(BaseModel):
    """Provisionar un tunnel nuevo para un cliente."""
    customer_id: int = Field(..., description="ID del cliente")
    tunnel_name: Optional[str] = Field(None, description="Nombre del tunnel (usa subdomain si no se envía)")


# ═══════════════════════════════════════════════════════
# Dashboard — Resumen completo (tunnels + DNS + stats)
# ═══════════════════════════════════════════════════════
@router.get("", summary="Dashboard de Cloudflare Tunnels")
async def list_tunnels(access_token: str = Cookie(None)):
    """
    Obtiene resumen completo de tunnels con DNS y estadísticas.
    Usa la API REST de Cloudflare (no requiere cloudflared instalado).
    """
    verify_admin(access_token)

    try:
        result = await CloudflareManager.get_dashboard_summary()

        if not result.get("success"):
            return {
                "success": True,
                "total": 0,
                "tunnels": [],
                "stats": {"healthy": 0, "down": 0, "inactive": 0, "total_dns_cnames": 0},
                "warning": result.get("error", "Cloudflare API no disponible"),
            }

        tunnels = result.get("tunnels", [])

        # Enriquecer con datos de BD (TenantDeployment)
        db = SessionLocal()
        try:
            for tunnel in tunnels:
                deployment = (
                    db.query(TenantDeployment)
                    .filter_by(tunnel_id=tunnel["id"])
                    .first()
                )
                if not deployment:
                    deployment = (
                        db.query(TenantDeployment)
                        .filter_by(tunnel_id=tunnel["name"])
                        .first()
                    )

                if deployment:
                    subscription = None
                    if deployment.subscription_id:
                        subscription = (
                            db.query(Subscription)
                            .filter_by(id=deployment.subscription_id)
                            .first()
                        )

                    # Obtener cliente directo o vía subscription
                    customer = None
                    if deployment.customer_id:
                        customer = db.query(Customer).filter_by(id=deployment.customer_id).first()
                    elif subscription and subscription.customer_id:
                        customer = db.query(Customer).filter_by(id=subscription.customer_id).first()

                    tunnel["deployment"] = {
                        "id": deployment.id,
                        "subdomain": deployment.subdomain,
                        "domain": getattr(deployment, "domain", None),
                        "url": deployment.tunnel_url,
                        "direct_url": deployment.direct_url,
                        "plan": deployment.plan_type,
                        "database_name": deployment.database_name,
                        "subscription_id": deployment.subscription_id,
                        "customer": {
                            "id": customer.id,
                            "company_name": customer.company_name,
                            "email": customer.email,
                        } if customer else None,
                        "stripe": {
                            "subscription_id": subscription.stripe_subscription_id
                            if subscription and hasattr(subscription, "stripe_subscription_id")
                            else None,
                            "status": subscription.status
                            if subscription and hasattr(subscription, "status")
                            else None,
                            "plan_name": subscription.plan_name
                            if subscription and hasattr(subscription, "plan_name")
                            else None,
                        } if subscription else None,
                    }
                else:
                    tunnel["deployment"] = None
        finally:
            db.close()

        return {
            "success": True,
            "total": result.get("total", len(tunnels)),
            "tunnels": tunnels,
            "stats": result.get("stats", {}),
        }

    except Exception as e:
        logger.exception(f"Error en dashboard tunnels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════
# RUTAS FIJAS — DEBEN ir ANTES de /{tunnel_id}
# ═══════════════════════════════════════════════════════

@router.get("/dns/records", summary="Listar registros DNS")
async def list_dns_records(
    domain: str = Query("sajet.us", description="Dominio/zona"),
    record_type: Optional[str] = Query(None, description="Tipo de registro (CNAME, A, etc.)"),
    access_token: str = Cookie(None),
):
    """Lista registros DNS de una zona de Cloudflare."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.list_dns_records(
            domain=domain, record_type=record_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/api-token", summary="Verificar token de Cloudflare API")
async def verify_api_token(access_token: str = Cookie(None)):
    """Verifica que el token de la API de Cloudflare sea válido."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.verify_api_token()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments/available", summary="Deployments disponibles para vincular")
async def list_available_deployments(access_token: str = Cookie(None)):
    """Lista todos los TenantDeployments para vincular a tunnels."""
    verify_admin(access_token)
    db = SessionLocal()
    try:
        deployments = db.query(TenantDeployment).all()
        items = []
        for d in deployments:
            customer = None
            sub = None
            if d.subscription_id:
                sub = db.query(Subscription).filter_by(id=d.subscription_id).first()
                if sub and sub.customer_id:
                    customer = db.query(Customer).filter_by(id=sub.customer_id).first()
            items.append({
                "id": d.id,
                "subdomain": d.subdomain,
                "database_name": d.database_name,
                "tunnel_id": d.tunnel_id or None,
                "tunnel_active": d.tunnel_active,
                "tunnel_url": d.tunnel_url,
                "direct_url": d.direct_url,
                "plan_type": str(d.plan_type.value) if d.plan_type else None,
                "subscription_id": d.subscription_id,
                "company_name": customer.company_name if customer else None,
                "stripe_subscription_id": sub.stripe_subscription_id if sub else None,
                "stripe_status": str(sub.status.value) if sub and sub.status else None,
            })
        return {"success": True, "deployments": items, "total": len(items)}
    finally:
        db.close()


@router.post("/{tunnel_id}/link", summary="Vincular tunnel a un tenant deployment")
async def link_tunnel_to_deployment(
    tunnel_id: str,
    payload: LinkTunnelRequest,
    access_token: str = Cookie(None),
):
    """
    Vincula un Cloudflare Tunnel a un TenantDeployment.
    Actualiza tunnel_id y tunnel_active en la BD.
    """
    verify_admin(access_token)
    db = SessionLocal()
    try:
        deployment = db.query(TenantDeployment).filter_by(id=payload.deployment_id).first()
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment no encontrado")

        # Verificar que el tunnel existe en CF
        result = await CloudflareManager.get_tunnel(tunnel_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail="Tunnel no existe en Cloudflare")

        tunnel_name = result["tunnel"].get("name", tunnel_id)

        # Desvincular otros deployments de este tunnel
        existing = db.query(TenantDeployment).filter_by(tunnel_id=tunnel_id).all()
        for ex in existing:
            if ex.id != payload.deployment_id:
                ex.tunnel_id = None
                ex.tunnel_active = False

        deployment.tunnel_id = tunnel_id
        deployment.tunnel_active = result["tunnel"].get("status") == "healthy"
        db.commit()

        logger.info(f"Tunnel {tunnel_id} ({tunnel_name}) vinculado a deployment {deployment.subdomain}")
        return {
            "success": True,
            "message": f"Tunnel '{tunnel_name}' vinculado a '{deployment.subdomain}'",
            "tunnel_id": tunnel_id,
            "deployment_id": deployment.id,
            "subdomain": deployment.subdomain,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error vinculando tunnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{tunnel_id}/link", summary="Desvincular tunnel de un tenant")
async def unlink_tunnel_from_deployment(
    tunnel_id: str,
    access_token: str = Cookie(None),
):
    """Desvincula un tunnel de su TenantDeployment."""
    verify_admin(access_token)
    db = SessionLocal()
    try:
        deployments = db.query(TenantDeployment).filter_by(tunnel_id=tunnel_id).all()
        if not deployments:
            raise HTTPException(status_code=404, detail="No hay deployment vinculado a este tunnel")

        for d in deployments:
            d.tunnel_id = None
            d.tunnel_active = False
        db.commit()

        names = [d.subdomain for d in deployments]
        logger.info(f"Tunnel {tunnel_id} desvinculado de: {names}")
        return {
            "success": True,
            "message": f"Tunnel desvinculado de: {', '.join(names)}",
            "unlinked": names,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{tunnel_id}/link-stripe", summary="Vincular deployment/tunnel a Stripe")
async def link_tunnel_stripe(
    tunnel_id: str,
    payload: LinkStripeRequest,
    access_token: str = Cookie(None),
):
    """
    Vincula el TenantDeployment de un tunnel a una Subscription (Stripe).
    """
    verify_admin(access_token)
    db = SessionLocal()
    try:
        deployment = db.query(TenantDeployment).filter_by(tunnel_id=tunnel_id).first()
        if not deployment:
            raise HTTPException(status_code=404, detail="No hay deployment vinculado a este tunnel")

        subscription = db.query(Subscription).filter_by(id=payload.subscription_id).first()
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription no encontrada")

        deployment.subscription_id = subscription.id
        db.commit()

        logger.info(f"Deployment {deployment.subdomain} vinculado a subscription {subscription.id}")
        return {
            "success": True,
            "message": f"Deployment '{deployment.subdomain}' vinculado a subscription #{subscription.id}",
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "plan_name": subscription.plan_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/subscription/{subscription_id}/tunnel", summary="Tunnel de una suscripción")
async def get_subscription_tunnel(subscription_id: str, access_token: str = Cookie(None)):
    """Obtiene información del tunnel asociado a una suscripción."""
    verify_admin(access_token)
    try:
        db = SessionLocal()
        try:
            deployment = db.query(TenantDeployment).filter_by(
                subscription_id=subscription_id
            ).first()
        finally:
            db.close()

        if not deployment or not deployment.tunnel_id:
            raise HTTPException(status_code=404, detail="No hay tunnel para esta suscripción")

        result = await CloudflareManager.get_tunnel(deployment.tunnel_id)
        tunnel = result.get("tunnel", {}) if result.get("success") else {}

        return {
            "tunnel_id": deployment.tunnel_id,
            "tunnel_name": tunnel.get("name", deployment.tunnel_id),
            "domain": deployment.tunnel_url,
            "status": tunnel.get("status", "unknown"),
            "active": deployment.tunnel_active,
            "connections_count": tunnel.get("connections_count", 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════
# Crear tunnel (POST sin path param)
# ═══════════════════════════════════════════════════════
@router.post("", summary="Crear nuevo Cloudflare Tunnel")
async def create_tunnel(
    name: str = Query(..., description="Nombre del tunnel"),
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Crea un nuevo Cloudflare Tunnel vía API REST."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.create_tunnel(name=name)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Error creando tunnel"))

        logger.info(f"Tunnel creado vía API: {name}")
        return {
            "success": True,
            "message": f"Tunnel '{name}' creado exitosamente",
            "tunnel": result.get("tunnel"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creando tunnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════
# CLIENTE ↔ TUNNEL — Vinculación directa + Lifecycle
# ═══════════════════════════════════════════════════════

@router.post("/{tunnel_id}/link-customer", summary="Vincular tunnel a un cliente")
async def link_tunnel_customer(
    tunnel_id: str,
    payload: LinkCustomerRequest,
    access_token: str = Cookie(None),
):
    """
    Vincula un Cloudflare Tunnel directamente a un cliente.
    Activa DNS automáticamente si la suscripción está activa.
    """
    verify_admin(access_token)
    result = await link_tunnel_to_customer(
        customer_id=payload.customer_id,
        tunnel_id=tunnel_id,
        deployment_id=payload.deployment_id,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/provision-for-customer", summary="Provisionar tunnel nuevo para cliente")
async def provision_customer_tunnel(
    payload: ProvisionTunnelRequest,
    access_token: str = Cookie(None),
):
    """
    Crea un Cloudflare Tunnel nuevo y lo vincula al cliente.
    End-to-end: crea tunnel → vincula deployment → crea DNS → activa si suscripción activa.
    """
    verify_admin(access_token)
    result = await provision_tunnel_for_customer(
        customer_id=payload.customer_id,
        tunnel_name=payload.tunnel_name,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/customer/{customer_id}", summary="Tunnel de un cliente")
async def get_customer_tunnel(customer_id: int, access_token: str = Cookie(None)):
    """
    Obtiene información completa del tunnel vinculado a un cliente.
    Incluye: estado Cloudflare, suscripción Stripe, DNS, URLs.
    """
    verify_admin(access_token)
    result = await get_customer_tunnel_info(customer_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/sync-lifecycle/{subscription_id}", summary="Sincronizar tunnel con suscripción")
async def sync_tunnel_subscription(subscription_id: int, access_token: str = Cookie(None)):
    """
    Sincroniza el estado del tunnel con el estado de la suscripción.
    Si activa → tunnel ON + DNS. Si past_due/cancelled → tunnel OFF + DNS removido.
    """
    verify_admin(access_token)
    result = await sync_tunnel_lifecycle(subscription_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/sync-all", summary="Sincronizar TODOS los tunnels con Stripe")
async def sync_all_tunnel_lifecycles(access_token: str = Cookie(None)):
    """
    Reconciliación masiva: sincroniza TODOS los tunnels con el estado actual
    de sus suscripciones Stripe. Activa/suspende según corresponda.
    """
    verify_admin(access_token)
    result = await sync_all_tunnels()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/customer-map", summary="Mapa completo Cliente↔Tunnel")
async def get_customer_tunnel_map(access_token: str = Cookie(None)):
    """
    Dashboard de vinculación: todos los clientes con sus tunnels y estado Stripe.
    """
    verify_admin(access_token)
    db = SessionLocal()
    try:
        deployments = db.query(TenantDeployment).filter(
            TenantDeployment.tunnel_id.isnot(None)
        ).all()

        items = []
        for dep in deployments:
            customer = None
            subscription = None

            if dep.customer_id:
                customer = db.query(Customer).filter_by(id=dep.customer_id).first()

            if dep.subscription_id:
                subscription = db.query(Subscription).filter_by(id=dep.subscription_id).first()
                if not customer and subscription and subscription.customer_id:
                    customer = db.query(Customer).filter_by(id=subscription.customer_id).first()

            items.append({
                "deployment_id": dep.id,
                "subdomain": dep.subdomain,
                "tunnel_id": dep.tunnel_id,
                "tunnel_active": dep.tunnel_active,
                "tunnel_url": dep.tunnel_url,
                "plan_type": dep.plan_type.value if dep.plan_type else None,
                "customer": {
                    "id": customer.id,
                    "company_name": customer.company_name,
                    "email": customer.email,
                    "subdomain": customer.subdomain,
                } if customer else None,
                "subscription": {
                    "id": subscription.id,
                    "status": subscription.status.value,
                    "plan_name": subscription.plan_name,
                    "stripe_subscription_id": subscription.stripe_subscription_id,
                } if subscription else None,
            })

        active_count = sum(1 for i in items if i["tunnel_active"])
        return {
            "success": True,
            "total": len(items),
            "active": active_count,
            "suspended": len(items) - active_count,
            "mappings": items,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════
# RUTAS PARAMETRIZADAS — /{tunnel_id} DESPUÉS de fijas
# ═══════════════════════════════════════════════════════

@router.get("/{tunnel_id}", summary="Detalle de un tunnel")
async def get_tunnel_detail(tunnel_id: str, access_token: str = Cookie(None)):
    """Obtiene detalles completos de un tunnel específico incluyendo configuración."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.get_tunnel(tunnel_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Tunnel no encontrado"))

        config = await CloudflareManager.get_tunnel_config(tunnel_id)
        tunnel_data = result["tunnel"]
        tunnel_data["config"] = config if config.get("success") else None

        return {"success": True, "tunnel": tunnel_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error obteniendo tunnel {tunnel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tunnel_id}/status", summary="Estado y conexiones de un tunnel")
async def get_tunnel_status(tunnel_id: str, access_token: str = Cookie(None)):
    """Obtiene estado actual y conexiones activas de un tunnel."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.get_tunnel(tunnel_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))

        tunnel = result["tunnel"]
        return {
            "tunnel_id": tunnel_id,
            "name": tunnel.get("name", ""),
            "status": tunnel.get("status", "unknown"),
            "active": tunnel.get("status") == "healthy",
            "connections_count": tunnel.get("connections_count", 0),
            "connections": tunnel.get("connections", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tunnel_id}/config", summary="Configuración de ingress de un tunnel")
async def get_tunnel_config(tunnel_id: str, access_token: str = Cookie(None)):
    """Obtiene las reglas de ingress de un tunnel (hostnames -> services)."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.get_tunnel_config(tunnel_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tunnel_id}/token", summary="Obtener token de instalación")
async def get_tunnel_token(tunnel_id: str, access_token: str = Cookie(None)):
    """Obtiene el token de cloudflared para instalar un tunnel en un servidor."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.get_tunnel_token(tunnel_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tunnel_id}", summary="Eliminar un tunnel")
async def delete_tunnel(tunnel_id: str, access_token: str = Cookie(None)) -> Dict[str, Any]:
    """Elimina un Cloudflare Tunnel vía API REST."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.delete_tunnel(tunnel_id)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Error eliminando tunnel"))

        db = SessionLocal()
        try:
            deployment = db.query(TenantDeployment).filter_by(tunnel_id=tunnel_id).first()
            if deployment:
                deployment.tunnel_active = False
                db.commit()
        finally:
            db.close()

        logger.info(f"Tunnel eliminado vía API: {tunnel_id}")
        return {"success": True, "message": f"Tunnel {tunnel_id} eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error eliminando tunnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tunnel_id}/restart", summary="Limpiar conexiones de un tunnel")
async def restart_tunnel(tunnel_id: str, access_token: str = Cookie(None)) -> Dict[str, Any]:
    """Limpia las conexiones activas de un tunnel (fuerza reconexión vía API)."""
    verify_admin(access_token)
    try:
        result = await CloudflareManager.clean_tunnel_connections(tunnel_id)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        return {"success": True, "message": f"Conexiones de tunnel {tunnel_id} limpiadas"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
