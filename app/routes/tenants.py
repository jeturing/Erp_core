"""
Tenants Routes - Tenant management endpoints
Integrado con OdooDatabaseManager para provisioning real
"""
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from ..models.database import Customer, Subscription, SubscriptionStatus, SessionLocal
from ..services.odoo_database_manager import (
    get_available_servers,
    get_servers_status,
    provision_tenant,
    delete_tenant,
    create_tenant_from_template,
    create_tenant_api,
    OdooDatabaseManager,
    ODOO_SERVERS,
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD
)
from .auth import verify_token
import httpx
import logging

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])
logger = logging.getLogger(__name__)

PROVISIONING_API_KEY = "prov-key-2026-secure"


# DTOs
class TenantCreateRequest(BaseModel):
    """Request para crear un nuevo tenant"""
    subdomain: str = Field(..., min_length=3, max_length=30, description="Nombre del tenant (será subdominio y BD)")
    company_name: Optional[str] = Field(None, description="Nombre de la empresa")
    admin_email: Optional[str] = Field(DEFAULT_ADMIN_LOGIN, description="Email del admin")
    admin_password: Optional[str] = Field(DEFAULT_ADMIN_PASSWORD, description="Password del admin")
    server_id: Optional[str] = Field(None, description="ID del servidor (None = automático)")
    plan: Optional[str] = Field("basic", description="Plan de suscripción")
    use_fast_method: Optional[bool] = Field(True, description="Usar método SQL directo (más rápido)")


class TenantDeleteRequest(BaseModel):
    """Request para eliminar un tenant"""
    subdomain: str = Field(..., description="Nombre del tenant a eliminar")
    server_id: Optional[str] = Field(None, description="ID del servidor donde está el tenant")
    confirm: bool = Field(False, description="Confirmación de eliminación")


async def get_all_tenants_from_servers():
    """Obtiene tenants de todos los servidores disponibles usando OdooDatabaseManager"""
    all_tenants = []
    
    servers = await get_available_servers()
    
    for server_info in servers:
        if server_info.get("status") == "offline":
            continue
        
        databases = server_info.get("databases", [])
        
        for db_name in databases:
            # Saltar BDs del sistema
            if db_name in ['postgres', 'template0', 'template1']:
                continue
            
            # Buscar en BD local si existe info del tenant
            db = SessionLocal()
            try:
                sub = db.query(Subscription).join(Customer).filter(
                    Customer.subdomain == db_name
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
                        "server": server_info.get("name"),
                        "server_id": server_info.get("id"),
                        "created_at": sub.created_at.isoformat() + "Z" if sub.created_at else None,
                        "url": f"https://{customer.subdomain}.sajet.us",
                    })
                else:
                    # Si no existe en BD local, crear entrada desde la BD de Odoo
                    all_tenants.append({
                        "id": abs(hash(db_name)) % 10000,
                        "company_name": db_name.replace("_", " ").title(),
                        "email": DEFAULT_ADMIN_LOGIN,
                        "subdomain": db_name,
                        "plan": "basic",
                        "status": "active",
                        "tunnel_active": True,
                        "server": server_info.get("name"),
                        "server_id": server_info.get("id"),
                        "created_at": None,
                        "url": f"https://{db_name}.sajet.us",
                    })
            except Exception as e:
                logger.error(f"Error consultando BD local para {db_name}: {e}")
            finally:
                db.close()
    
    return all_tenants


# =====================================================
# ENDPOINTS DE SERVIDORES
# =====================================================

@router.get("/servers")
async def list_servers():
    """Lista todos los servidores disponibles con su estado"""
    try:
        return await get_servers_status()
    except Exception as e:
        logger.error(f"Error obteniendo servidores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/databases")
async def list_server_databases(server_id: str):
    """Lista las bases de datos de un servidor específico"""
    if server_id not in ODOO_SERVERS:
        raise HTTPException(status_code=404, detail=f"Servidor '{server_id}' no encontrado")
    
    server = ODOO_SERVERS[server_id]
    
    try:
        async with OdooDatabaseManager(server) as manager:
            databases = await manager.list_databases()
            
            # Obtener info de cada BD
            db_info = []
            for db_name in databases:
                if db_name not in ['postgres', 'template0', 'template1']:
                    info = await manager.get_database_info(db_name)
                    db_info.append(info)
            
            return {
                "server": server_id,
                "server_name": server.name,
                "databases": db_info,
                "total": len(db_info)
            }
    except Exception as e:
        logger.error(f"Error obteniendo BDs de {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# ENDPOINTS DE TENANTS
# =====================================================

@router.get("")
async def list_tenants(authorization: Optional[str] = Header(None)):
    """Listado de tenants desde todos los servidores"""
    # Validar token si se proporciona
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    try:
        items = await get_all_tenants_from_servers()
        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.error(f"Error listando tenants: {e}")
        return {"items": [], "total": 0, "error": str(e)}


@router.post("")
async def create_tenant(
    payload: TenantCreateRequest, 
    authorization: Optional[str] = Header(None)
):
    """
    Crear un nuevo tenant (base de datos Odoo).
    
    - Si no se especifica server_id, se selecciona automáticamente el mejor servidor
    - Credenciales por defecto: admin@sajet.us / 321Abcd.
    - Por defecto usa método SQL rápido (duplica template_tenant)
    """
    # Validar token
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    try:
        # Usar método rápido por defecto
        if payload.use_fast_method:
            # Método SQL directo - más rápido (duplica template_tenant)
            result = await create_tenant_from_template(
                subdomain=payload.subdomain,
                company_name=payload.company_name,
                server_id=payload.server_id
            )
        else:
            # Método tradicional via HTTP API de Odoo
            result = await provision_tenant(
                subdomain=payload.subdomain,
                admin_login=payload.admin_email or DEFAULT_ADMIN_LOGIN,
                admin_password=payload.admin_password or DEFAULT_ADMIN_PASSWORD,
                server_id=payload.server_id,
                demo=False,
                lang="es_MX"
            )
        
        if result.get("success"):
            # Registrar en BD local (opcional)
            db = SessionLocal()
            try:
                # Verificar si ya existe
                existing = db.query(Customer).filter(Customer.subdomain == payload.subdomain).first()
                if not existing:
                    customer = Customer(
                        company_name=payload.company_name or payload.subdomain.title(),
                        email=payload.admin_email or DEFAULT_ADMIN_LOGIN,
                        subdomain=payload.subdomain
                    )
                    db.add(customer)
                    db.commit()
                    db.refresh(customer)
                    
                    # Crear suscripción
                    subscription = Subscription(
                        customer_id=customer.id,
                        plan_name=payload.plan or "basic",
                        status=SubscriptionStatus.active
                    )
                    db.add(subscription)
                    db.commit()
                    db.refresh(subscription)
                    
                    result["customer_id"] = customer.id
                    result["subscription_id"] = subscription.id
            except Exception as db_err:
                logger.warning(f"No se pudo registrar tenant en BD local: {db_err}")
            finally:
                db.close()
            
            return {
                "success": True,
                "message": f"Tenant '{payload.subdomain}' creado exitosamente",
                "tenant": {
                    "subdomain": payload.subdomain,
                    "url": result.get("url"),
                    "server": result.get("server"),
                    "admin_login": payload.admin_email or DEFAULT_ADMIN_LOGIN,
                    "status": "active"
                },
                "details": result
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=result.get("error", "Error creando tenant")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{subdomain}")
async def delete_tenant_endpoint(
    subdomain: str,
    server_id: Optional[str] = Query(None, description="ID del servidor"),
    confirm: bool = Query(False, description="Confirmar eliminación"),
    authorization: Optional[str] = Header(None)
):
    """
    Eliminar un tenant (base de datos Odoo).
    
    - Requiere confirm=true para ejecutar
    - Si no se especifica server_id, busca en todos los servidores
    """
    # Validar token
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    if not confirm:
        return {
            "success": False,
            "message": f"Debe confirmar la eliminación con ?confirm=true",
            "warning": f"Esta acción eliminará permanentemente la base de datos '{subdomain}'"
        }
    
    try:
        result = await delete_tenant(subdomain, server_id)
        
        if result.get("success"):
            # Eliminar de BD local si existe
            db = SessionLocal()
            try:
                customer = db.query(Customer).filter(Customer.subdomain == subdomain).first()
                if customer:
                    # Eliminar suscripciones asociadas
                    db.query(Subscription).filter(Subscription.customer_id == customer.id).delete()
                    db.delete(customer)
                    db.commit()
                    logger.info(f"Eliminado registro local de tenant: {subdomain}")
            except Exception as db_err:
                logger.warning(f"No se pudo eliminar registro local: {db_err}")
            finally:
                db.close()
            
            return {
                "success": True,
                "message": f"Tenant '{subdomain}' eliminado exitosamente",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Error eliminando tenant")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subdomain}")
async def get_tenant_details(
    subdomain: str,
    authorization: Optional[str] = Header(None)
):
    """Obtener detalles de un tenant específico"""
    # Validar token
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    try:
        all_tenants = await get_all_tenants_from_servers()
        
        for tenant in all_tenants:
            if tenant.get("subdomain") == subdomain:
                return tenant
        
        raise HTTPException(status_code=404, detail=f"Tenant '{subdomain}' no encontrado")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))
