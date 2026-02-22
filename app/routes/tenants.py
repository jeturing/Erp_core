"""
Tenants Routes - Tenant management endpoints
Integrado con OdooDatabaseManager para provisioning real
"""
from fastapi import APIRouter, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re
from ..models.database import Customer, Subscription, SubscriptionStatus, SessionLocal, Partner, Plan, BillingMode, PayerType, CollectorType, InvoiceIssuer
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
    DEFAULT_ADMIN_PASSWORD,
    query_admin_login_pg,
)
from .auth import verify_token
from .roles import verify_token_with_role, _extract_token
import httpx
import logging
import psycopg
import os

from ..config import PROVISIONING_API_KEY, ODOO_DB_USER, ODOO_DB_PASSWORD

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])
logger = logging.getLogger(__name__)

_SUBDOMAIN_RE = re.compile(r'^[a-z0-9][a-z0-9_]{1,28}[a-z0-9]$')


def _require_admin(request: Request, authorization: Optional[str] = None):
    """Verifica que la request tenga un token de admin válido."""
    token = _extract_token(request, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = verify_token_with_role(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso solo para administradores")
    return payload


# DTOs
class TenantCreateRequest(BaseModel):
    """Request para crear un nuevo tenant"""
    subdomain: str = Field(..., min_length=3, max_length=30, description="Nombre del tenant (será subdominio y BD)")

    @field_validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        v = v.lower()
        if not _SUBDOMAIN_RE.match(v):
            raise ValueError("El subdominio solo puede contener letras minúsculas, números y guiones bajos, y debe empezar y terminar con alfanumérico")
        return v
    company_name: Optional[str] = Field(None, description="Nombre de la empresa")
    admin_email: Optional[str] = Field(DEFAULT_ADMIN_LOGIN, description="Email del admin")
    admin_password: Optional[str] = Field(DEFAULT_ADMIN_PASSWORD, description="Password del admin")
    server_id: Optional[str] = Field(None, description="ID del servidor (None = automático)")
    plan: Optional[str] = Field("basic", description="Plan de suscripción")
    partner_id: Optional[int] = Field(None, description="ID del partner que origina este tenant")
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
        if not databases:
            # Fallback: leer directamente PostgreSQL del nodo Odoo.
            databases = _list_databases_via_postgres(server_info.get("id"))
        
        # Obtener IP del servidor para consultar login real
        server_obj = ODOO_SERVERS.get(server_info.get("id"))
        server_ip = server_obj.ip if server_obj else None
        db_port = int(os.getenv("ODOO_DB_PORT", "5432"))
        
        for db_name in databases:
            # Saltar BDs del sistema
            if db_name in ['postgres', 'template0', 'template1', 'template_tenant']:
                continue
            
            # Consultar login real desde Odoo PostgreSQL
            real_login = None
            if server_ip:
                real_login = query_admin_login_pg(server_ip, db_name, db_port)
            
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
                    
                    # Si el login real difiere del almacenado, actualizar BD local
                    if real_login and customer.email != real_login:
                        try:
                            logger.info(f"Sync email '{customer.subdomain}': {customer.email} → {real_login}")
                            customer.email = real_login
                            db.commit()
                        except Exception as sync_err:
                            logger.warning(f"No se pudo sincronizar email de {customer.subdomain}: {sync_err}")
                            db.rollback()
                    
                    email_to_show = real_login or customer.email
                    
                    # Obtener info de partner si está vinculado
                    partner_name = None
                    if sub.owner_partner_id:
                        partner = db.query(Partner).filter(Partner.id == sub.owner_partner_id).first()
                        if partner:
                            partner_name = partner.company_name
                    
                    all_tenants.append({
                        "id": sub.id,
                        "company_name": customer.company_name,
                        "email": email_to_show,
                        "subdomain": customer.subdomain,
                        "plan": sub.plan_name,
                        "status": status_map.get(sub.status, "active"),
                        "tunnel_active": sub.status == SubscriptionStatus.active,
                        "server": server_info.get("name"),
                        "server_id": server_info.get("id"),
                        "created_at": sub.created_at.isoformat() + "Z" if sub.created_at else None,
                        "url": f"https://{customer.subdomain}.sajet.us",
                        "partner_id": sub.owner_partner_id,
                        "partner_name": partner_name,
                        "monthly_amount": sub.monthly_amount or 0,
                        "user_count": sub.user_count or 1,
                        "billing_mode": sub.billing_mode.value if sub.billing_mode else None,
                    })
                else:
                    # Tenant existe en Odoo pero no en BD local — auto-registrar
                    email_to_show = real_login or DEFAULT_ADMIN_LOGIN
                    try:
                        new_customer = Customer(
                            company_name=db_name.replace("_", " ").title(),
                            email=email_to_show,
                            full_name=db_name.replace("_", " ").title(),
                            subdomain=db_name
                        )
                        db.add(new_customer)
                        db.commit()
                        db.refresh(new_customer)
                        
                        new_sub = Subscription(
                            customer_id=new_customer.id,
                            plan_name="basic",
                            status=SubscriptionStatus.active
                        )
                        db.add(new_sub)
                        db.commit()
                        db.refresh(new_sub)
                        
                        logger.info(f"Auto-registrado tenant '{db_name}' en BD local (email={email_to_show})")
                        
                        all_tenants.append({
                            "id": new_sub.id,
                            "company_name": new_customer.company_name,
                            "email": email_to_show,
                            "subdomain": db_name,
                            "plan": "basic",
                            "status": "active",
                            "tunnel_active": True,
                            "server": server_info.get("name"),
                            "server_id": server_info.get("id"),
                            "created_at": new_customer.created_at.isoformat() + "Z" if new_customer.created_at else None,
                            "url": f"https://{db_name}.sajet.us",
                            "partner_id": None,
                            "partner_name": None,
                            "monthly_amount": 0,
                            "user_count": 1,
                            "billing_mode": None,
                        })
                    except Exception as auto_err:
                        logger.warning(f"No se pudo auto-registrar {db_name}: {auto_err}")
                        db.rollback()
                        all_tenants.append({
                            "id": abs(hash(db_name)) % 10000,
                            "company_name": db_name.replace("_", " ").title(),
                            "email": email_to_show,
                            "subdomain": db_name,
                            "plan": "basic",
                            "status": "active",
                            "tunnel_active": True,
                            "server": server_info.get("name"),
                            "server_id": server_info.get("id"),
                            "created_at": None,
                            "url": f"https://{db_name}.sajet.us",
                            "partner_id": None,
                            "partner_name": None,
                            "monthly_amount": 0,
                            "user_count": 1,
                            "billing_mode": None,
                        })
            except Exception as e:
                logger.error(f"Error consultando BD local para {db_name}: {e}")
            finally:
                db.close()
    
    return all_tenants


def _list_databases_via_postgres(server_id: Optional[str]) -> List[str]:
    """Lista bases de datos conectando directo a PostgreSQL del servidor Odoo."""
    if not server_id:
        return []

    server = ODOO_SERVERS.get(server_id)
    if not server:
        return []

    db_user = ODOO_DB_USER
    db_password = ODOO_DB_PASSWORD
    db_port = int(os.getenv("ODOO_DB_PORT", "5432"))

    try:
        with psycopg.connect(
            host=server.ip,
            port=db_port,
            dbname="postgres",
            user=db_user,
            password=db_password,
            connect_timeout=5,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT datname
                    FROM pg_database
                    WHERE datistemplate = false
                    ORDER BY datname
                    """
                )
                rows = cur.fetchall()
                dbs = [row[0] for row in rows if row and row[0]]
                logger.info(f"PostgreSQL fallback: {len(dbs)} BDs detectadas en {server.id}")
                return dbs
    except Exception as e:
        logger.warning(f"No se pudo listar BDs via PostgreSQL en {server.id}: {e}")
        return []


async def get_all_tenants_from_local_db():
    """Obtiene tenants desde la BD local como fallback cuando Odoo no responde."""
    items = []
    db = SessionLocal()
    try:
        customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
        status_map = {
            SubscriptionStatus.active: "active",
            SubscriptionStatus.pending: "provisioning",
            SubscriptionStatus.past_due: "payment_failed",
            SubscriptionStatus.cancelled: "suspended",
        }

        for customer in customers:
            # Prioridad: suscripción activa, si no la más reciente
            sub = db.query(Subscription).filter(
                Subscription.customer_id == customer.id,
                Subscription.status == SubscriptionStatus.active
            ).first()

            if not sub:
                sub = db.query(Subscription).filter(
                    Subscription.customer_id == customer.id
                ).order_by(Subscription.created_at.desc()).first()

            plan_name = (sub.plan_name if sub and sub.plan_name else (customer.plan.value if customer.plan else "basic"))
            status_value = status_map.get(sub.status, "active") if sub else "active"

            items.append({
                "id": customer.id,
                "company_name": customer.company_name,
                "email": customer.email,
                "subdomain": customer.subdomain,
                "plan": plan_name,
                "status": status_value,
                "tunnel_active": status_value == "active",
                "server": None,
                "server_id": None,
                "created_at": customer.created_at.isoformat() + "Z" if customer.created_at else None,
                "url": f"https://{customer.subdomain}.sajet.us",
            })
    finally:
        db.close()

    return items


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
async def list_tenants(request: Request, authorization: Optional[str] = Header(None)):
    """Listado de tenants desde todos los servidores"""
    _require_admin(request, authorization)
    try:
        items = await get_all_tenants_from_servers()
        if not items:
            logger.warning("No se detectaron tenants desde Odoo; usando fallback de BD local")
            items = await get_all_tenants_from_local_db()
        else:
            # Merge de seguridad: incluir tenants locales faltantes
            local_items = await get_all_tenants_from_local_db()
            by_subdomain = {item.get("subdomain"): item for item in items}
            for local_item in local_items:
                sub = local_item.get("subdomain")
                if sub and sub not in by_subdomain:
                    items.append(local_item)

        return {"items": items, "total": len(items)}
    except Exception as e:
        logger.error(f"Error listando tenants: {e}")
        fallback_items = await get_all_tenants_from_local_db()
        return {"items": fallback_items, "total": len(fallback_items), "error": str(e)}


@router.post("")
async def create_tenant(
    payload: TenantCreateRequest,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Crear un nuevo tenant (base de datos Odoo). Requiere rol admin.

    - Si no se especifica server_id, se selecciona automáticamente el mejor servidor
    - Credenciales por defecto: configuradas en variables de entorno
    - Por defecto usa método SQL rápido (duplica template_tenant)
    """
    _require_admin(request, authorization)
    # Verificar idempotencia: si el subdominio ya existe en BD local, rechazar
    db = SessionLocal()
    try:
        existing = db.query(Customer).filter(Customer.subdomain == payload.subdomain).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"El subdominio '{payload.subdomain}' ya existe")
    finally:
        db.close()
    try:
        # Usar método rápido por defecto
        if payload.use_fast_method:
            # Método SQL directo - más rápido (duplica template_tenant)
            result = await create_tenant_from_template(
                subdomain=payload.subdomain,
                company_name=payload.company_name,
                server_id=payload.server_id,
                admin_login=payload.admin_email,
                admin_password=payload.admin_password,
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
                        full_name=payload.company_name or payload.subdomain.title(),
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
                        status=SubscriptionStatus.active,
                        owner_partner_id=payload.partner_id,
                        billing_mode=BillingMode.PARTNER_DIRECT if payload.partner_id else BillingMode.JETURING_DIRECT_SUBSCRIPTION,
                        payer_type=PayerType.PARTNER if payload.partner_id else PayerType.CLIENT,
                        collector=CollectorType.STRIPE_CONNECT if payload.partner_id else CollectorType.STRIPE_DIRECT,
                        invoice_issuer=InvoiceIssuer.JETURING,
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
    request: Request,
    server_id: Optional[str] = Query(None, description="ID del servidor"),
    confirm: bool = Query(False, description="Confirmar eliminación"),
    authorization: Optional[str] = Header(None)
):
    """
    Eliminar un tenant (base de datos Odoo). Requiere rol admin.

    - Requiere confirm=true para ejecutar
    - Si no se especifica server_id, busca en todos los servidores
    """
    _require_admin(request, authorization)
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
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """Obtener detalles de un tenant específico. Requiere autenticación."""
    _require_admin(request, authorization)
    try:
        all_tenants = await get_all_tenants_from_servers()
        if not all_tenants:
            all_tenants = await get_all_tenants_from_local_db()
        
        for tenant in all_tenants:
            if tenant.get("subdomain") == subdomain:
                return tenant
        
        raise HTTPException(status_code=404, detail=f"Tenant '{subdomain}' no encontrado")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))
