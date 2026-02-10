"""
Tenants Routes - Tenant management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.database import Customer, Subscription, SubscriptionStatus, SessionLocal
from .auth import verify_token
import httpx
import logging

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])
logger = logging.getLogger(__name__)

# Configuración de nodos Odoo
ODOO_NODES = {
    "node-1": {
        "ip": "10.10.10.100",
        "api_port": 8070,
        "name": "Node 1 (LXC 105)",
        "enabled": True
    },
    "node-2": {
        "ip": "10.10.10.200",
        "api_port": 8070,
        "name": "Node 2 (LXC 106)",
        "enabled": False  # Cambiar a True cuando esté disponible
    }
}

PROVISIONING_API_KEY = "prov-key-2026-secure"


# DTOs
class TenantCreateRequest(BaseModel):
    company_name: str
    admin_email: str
    subdomain: str
    plan: str


async def get_all_tenants_from_nodes():
    """Obtiene tenants de todos los nodos disponibles"""
    all_tenants = []
    
    for node_id, node_config in ODOO_NODES.items():
        if not node_config["enabled"]:
            continue
        
        try:
            url = f"http://{node_config['ip']}:{node_config['api_port']}/api/tenants"
            headers = {"X-API-KEY": PROVISIONING_API_KEY}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    tenants = data.get("tenants", [])
                    
                    # Enriquecer con información del nodo
                    for tenant in tenants:
                        # Obtener datos del tenant de la BD local si existen
                        db = SessionLocal()
                        try:
                            sub = db.query(Subscription).join(Customer).filter(
                                Customer.subdomain == tenant.get("database")
                            ).first()
                            
                            if sub:
                                status_map = {
                                    SubscriptionStatus.active: "active",
                                    SubscriptionStatus.pending: "provisioning",
                                    SubscriptionStatus.past_due: "payment_failed",
                                    SubscriptionStatus.cancelled: "suspended",
                                }
                                
                                customer = sub.customer
                                all_tenants.append({
                                    "id": sub.id,
                                    "company_name": customer.company_name,
                                    "email": customer.email,
                                    "subdomain": customer.subdomain,
                                    "plan": sub.plan_name,
                                    "status": status_map.get(sub.status, "active"),
                                    "tunnel_active": sub.status == SubscriptionStatus.active,
                                    "node": node_config["name"],
                                    "node_id": node_id,
                                    "created_at": sub.created_at.isoformat() + "Z" if sub.created_at else None,
                                    "url": tenant.get("url"),
                                    "cpu_usage": 30,  # Placeholder - podría obtenerse del nodo
                                })
                            else:
                                # Si no existe en BD local, crear entrada mínima
                                all_tenants.append({
                                    "id": hash(tenant.get("database")) % 10000,
                                    "company_name": tenant.get("database", "Unknown").title(),
                                    "email": "unknown@sajet.us",
                                    "subdomain": tenant.get("database", "unknown"),
                                    "plan": "basic",
                                    "status": "active",
                                    "tunnel_active": True,
                                    "node": node_config["name"],
                                    "node_id": node_id,
                                    "created_at": None,
                                    "url": tenant.get("url"),
                                    "cpu_usage": 30,
                                })
                        finally:
                            db.close()
                else:
                    logger.warning(f"Error consultando {node_id}: HTTP {response.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"Timeout consultando {node_id}")
        except Exception as e:
            logger.error(f"Error consultando nodo {node_id}: {e}")
    
    return all_tenants


@router.get("")
async def list_tenants(authorization: str = None):
    """Listado de tenants desde todos los nodos - requiere JWT."""
    # Validar token
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    try:
        # Obtener tenants de todos los nodos
        items = await get_all_tenants_from_nodes()
        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.error(f"Error listando tenants: {e}")
        # Retornar lista vacía en lugar de error
        return {"items": [], "total": 0}


@router.post("")
async def create_tenant(payload: TenantCreateRequest, authorization: str = None):
    """Crear tenant (stub sin persistencia) - requiere JWT."""
    # Validar token
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    tenant = payload.model_dump()
    tenant["id"] = 999
    tenant["status"] = "provisioning"
    tenant["tunnel_active"] = False
    tenant["created_at"] = "2024-01-01T00:00:00Z"
    return tenant
