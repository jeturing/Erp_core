"""
Rutas API para gestión de Cloudflare Tunnels
Endpoints para crear, listar y eliminar proxies/tunnels de tenants
"""
from fastapi import APIRouter, HTTPException, Cookie
from typing import Dict, Any, List, Optional
import logging

from ..services.cloudflare_manager import CloudflareManager
from ..models.database import SessionLocal, TenantDeployment, LXCContainer, Subscription
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
    except:
        raise HTTPException(status_code=401, detail="Token inválido")


@router.get("", summary="Listar todos los tunnels de Cloudflare")
async def list_tunnels(access_token: str = Cookie(None)):
    """
    Lista todos los Cloudflare Tunnels activos en el sistema.
    Requiere: Admin
    """
    verify_admin(access_token)
    
    try:
        result = CloudflareManager.list_tunnels()
        
        # Si cloudflared no está configurado, devolver lista vacía con mensaje
        if not result.get("success"):
            return {
                "success": True,
                "total": 0,
                "tunnels": [],
                "warning": "Cloudflare Tunnels no está configurado. Instale cloudflared y configure credenciales.",
                "error": result.get("error", "Cloudflared no disponible")
            }
        
        # Enriquecer con datos de BD
        db = SessionLocal()
        tunnels_enriched = []
        
        for tunnel in result.get("tunnels", []):
            deployment = db.query(TenantDeployment).filter_by(
                tunnel_id=tunnel["id"]
            ).first()
            
            tunnel_info = {
                **tunnel,
                "deployment": None
            }
            
            if deployment:
                tunnel_info["deployment"] = {
                    "subdomain": deployment.subdomain,
                    "domain": deployment.domain,
                    "url": deployment.tunnel_url,
                    "plan": deployment.plan_type,
                    "subscription_id": deployment.subscription_id
                }
            
            tunnels_enriched.append(tunnel_info)
        
        db.close()
        
        return {
            "success": True,
            "total": len(tunnels_enriched),
            "tunnels": tunnels_enriched
        }
        
    except Exception as e:
        logger.exception(f"Error listando tunnels: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/{tunnel_id}/status", summary="Obtener estado de un tunnel")
async def get_tunnel_status(
    tunnel_id: str,
    access_token: str = Cookie(None)
):
    """
    Obtiene el estado actual de un tunnel específico.
    Requiere: Admin
    """
    verify_admin(access_token)
    
    try:
        status_info = CloudflareManager.get_tunnel_status(tunnel_id)
        return status_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tunnel_id}/logs", summary="Obtener logs del tunnel")
async def get_tunnel_logs(
    tunnel_id: str,
    lines: int = 50,
    access_token: str = Cookie(None)
):
    """
    Obtiene los logs más recientes de un tunnel.
    Requiere: Admin
    """
    verify_admin(access_token)
    
    try:
        logs = CloudflareManager.get_tunnel_logs(tunnel_id, lines)
        return {
            "tunnel_id": tunnel_id,
            "lines_count": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", summary="Crear nuevo tunnel para un tenant")
async def create_tunnel(
    subscription_id: str,
    container_id: int,
    local_port: int = 8069,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """
    Crea un nuevo Cloudflare Tunnel para un tenant.
    
    Este endpoint:
    1. Crea el tunnel en Cloudflare
    2. Configura DNS routing
    3. Crea servicio systemd para auto-start
    4. Actualiza registro TenantDeployment
    
    Args:
        subscription_id: ID de la suscripción
        container_id: ID del contenedor LXC
        local_port: Puerto local del servicio (default 8069 para Odoo)
    
    Requiere: Admin
    """
    verify_admin(access_token)
    
    try:
        db = SessionLocal()
        
        # 1. Verificar subscription
        subscription = db.query(Subscription).filter_by(
            id=subscription_id
        ).first()
        
        if not subscription:
            db.close()
            raise HTTPException(
                status_code=404,
                detail=f"Suscripción {subscription_id} no encontrada"
            )
        
        # 2. Verificar contenedor
        container = db.query(LXCContainer).filter_by(id=container_id).first()
        
        if not container:
            db.close()
            raise HTTPException(
                status_code=404,
                detail=f"Contenedor {container_id} no encontrado"
            )
        
        # 3. Verificar deployment
        deployment = db.query(TenantDeployment).filter_by(
            subscription_id=subscription_id,
            container_id=container_id
        ).first()
        
        if not deployment:
            db.close()
            raise HTTPException(
                status_code=404,
                detail="Deployment no encontrado"
            )
        
        db.close()
        
        # 4. Crear tunnel
        result = await CloudflareManager.create_tunnel(
            subdomain=deployment.subdomain,
            container_id=container_id,
            local_port=local_port,
            domain=deployment.domain
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Error creando tunnel")
            )
        
        logger.info(f"Tunnel creado: {deployment.subdomain} → {container_id}")
        
        return {
            "success": True,
            "message": f"Tunnel creado exitosamente para {deployment.subdomain}",
            "tunnel": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error creando tunnel: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.delete("/{tunnel_id}", summary="Eliminar un tunnel")
async def delete_tunnel(
    tunnel_id: str,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """
    Elimina un Cloudflare Tunnel.
    
    Este endpoint:
    1. Detiene el servicio systemd
    2. Elimina el tunnel de Cloudflare
    3. Actualiza BD para marcar como inactivo
    
    Requiere: Admin
    """
    verify_admin(access_token)
    
    try:
        result = await CloudflareManager.delete_tunnel(tunnel_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Error eliminando tunnel")
            )
        
        logger.info(f"Tunnel eliminado: {tunnel_id}")
        
        return {
            "success": True,
            "message": f"Tunnel {tunnel_id} eliminado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error eliminando tunnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tunnel_id}/restart", summary="Reiniciar un tunnel")
async def restart_tunnel(
    tunnel_id: str,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """
    Reinicia un Cloudflare Tunnel.
    Requiere: Admin
    """
    verify_admin(access_token)
    
    try:
        result = CloudflareManager.restart_tunnel(tunnel_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscription/{subscription_id}/tunnel", summary="Obtener tunnel de una suscripción")
async def get_subscription_tunnel(
    subscription_id: str,
    access_token: str = Cookie(None)
):
    """
    Obtiene información del tunnel asociado a una suscripción.
    Requiere: Admin
    """
    verify_admin(access_token)
    
    try:
        db = SessionLocal()
        
        deployment = db.query(TenantDeployment).filter_by(
            subscription_id=subscription_id
        ).first()
        
        db.close()
        
        if not deployment or not deployment.tunnel_id:
            raise HTTPException(
                status_code=404,
                detail="No hay tunnel para esta suscripción"
            )
        
        status_info = CloudflareManager.get_tunnel_status(deployment.tunnel_id)
        
        return {
            "tunnel_id": deployment.tunnel_id,
            "tunnel_name": deployment.tunnel_id,
            "domain": deployment.tunnel_url,
            "status": status_info.get("status", "unknown"),
            "active": deployment.tunnel_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
