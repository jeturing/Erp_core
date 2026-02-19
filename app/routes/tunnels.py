"""
Rutas API para gestión de Cloudflare Tunnels
Usa la API REST de Cloudflare v4 (sin dependencia de cloudflared CLI).
"""
from fastapi import APIRouter, HTTPException, Cookie, Query
from typing import Dict, Any, Optional
import logging

from ..services.cloudflare_manager import CloudflareManager
from ..models.database import SessionLocal, TenantDeployment, Subscription
from ..security.tokens import TokenManager

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

                    tunnel["deployment"] = {
                        "id": deployment.id,
                        "subdomain": deployment.subdomain,
                        "domain": getattr(deployment, "domain", None),
                        "url": deployment.tunnel_url,
                        "direct_url": deployment.direct_url,
                        "plan": deployment.plan_type,
                        "database_name": deployment.database_name,
                        "subscription_id": deployment.subscription_id,
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
