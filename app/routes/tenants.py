"""
Tenants Routes - Tenant management endpoints
Integrado con OdooDatabaseManager para provisioning real
"""
from fastapi import APIRouter, Cookie, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re
from ..models.database import Customer, Subscription, SubscriptionStatus, SessionLocal, Partner, Plan, BillingMode, PayerType, CollectorType, InvoiceIssuer
from ..models.database import CustomDomain, DomainVerificationStatus, TenantDeployment
from ..services.odoo_database_manager import (
    get_available_servers,
    get_servers_status,
    provision_tenant,
    delete_tenant,
    backup_tenant,
    is_tenant_protected,
    create_tenant_from_template,
    create_tenant_api,
    OdooDatabaseManager,
    ODOO_SERVERS,
    refresh_odoo_servers,
    DEFAULT_ADMIN_LOGIN,
    DEFAULT_ADMIN_PASSWORD,
    query_admin_login_pg,
    COUNTRY_LOCALIZATION,
    _resolve_blueprint_modules,
)
from ..services.email_service import send_tenant_backup_deleted
from .auth import verify_token
from .roles import verify_token_with_role, _extract_token, _require_admin as _require_admin_base
from ..services.nginx_domain_configurator import provision_sajet_subdomain, remove_sajet_subdomain
import httpx
import logging
import psycopg
import os
import xmlrpc.client
import secrets
import string
from ..models.database import AuditEventRecord

from ..config import PROVISIONING_API_KEY, ODOO_DB_USER, ODOO_DB_PASSWORD, ODOO_DB_HOST, DATABASE_URL
from ..services.cloudflare_manager import CloudflareManager

# BDs del sistema que NUNCA deben aparecer en el listado de tenants ni poder borrarse.
# Se extrae dinámicamente el nombre de la BD propia de la app desde DATABASE_URL.
def _get_own_db_name() -> str:
    """Extrae el nombre de la BD interna del sistema desde DATABASE_URL."""
    try:
        return DATABASE_URL.rsplit("/", 1)[-1].split("?")[0].strip() or "erp_core_db"
    except Exception:
        return "erp_core_db"

_SYSTEM_DBS: set = {
    'postgres', 'template0', 'template1',
    'template_tenant',
    _get_own_db_name(),   # BD interna del ERP (erp_core_db o la que configure DATABASE_URL)
    'root',               # BD de postgres generada al instalar
}

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])
logger = logging.getLogger(__name__)

_SUBDOMAIN_RE = re.compile(r'^[a-z0-9][a-z0-9_]{1,28}[a-z0-9]$')


def _generate_bootstrap_password(length: int = 20) -> str:
    """Genera una contraseña robusta (sin comillas simples para evitar problemas SQL legacy)."""
    alphabet = string.ascii_letters + string.digits + "@#$%!-_"
    return "".join(secrets.choice(alphabet) for _ in range(max(12, length)))


def _build_tenant_admin_credentials(subdomain: str, base_domain: str = "sajet.us") -> tuple[str, str]:
    """Credenciales bootstrap del admin del tenant: <subdomain>@<base_domain> + password aleatoria."""
    login = f"{subdomain}@{base_domain}"
    password = _generate_bootstrap_password()
    return login, password


def _safe_actor_from_request(request: Request) -> tuple[Optional[int], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Extrae actor básico para auditoría sin romper el flujo principal."""
    try:
        token = _extract_token(request)
        if not token:
            return None, None, None, request.client.host if request.client else None, request.headers.get("user-agent")
        payload = verify_token_with_role(token)
        return (
            payload.get("user_id"),
            payload.get("username") or payload.get("email"),
            payload.get("role"),
            request.client.host if request.client else None,
            request.headers.get("user-agent"),
        )
    except Exception:
        return None, None, None, request.client.host if request.client else None, request.headers.get("user-agent")


def _log_tenant_audit(
    request: Request,
    *,
    event_type: str,
    resource: str,
    action: str,
    status: str,
    details: Optional[dict] = None,
) -> None:
    """Registra evento de auditoría persistente para operaciones de tenant."""
    db = SessionLocal()
    try:
        actor_id, actor_username, actor_role, ip_address, user_agent = _safe_actor_from_request(request)
        evt = AuditEventRecord(
            event_type=event_type,
            actor_id=actor_id,
            actor_username=actor_username,
            actor_role=actor_role,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:500] if user_agent else None,
            resource=resource,
            action=action,
            status=status,
            details=details or {},
        )
        db.add(evt)
        db.commit()
    except Exception as audit_err:
        db.rollback()
        logger.warning(f"No se pudo registrar auditoría tenant ({event_type}): {audit_err}")
    finally:
        db.close()


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
    country_code: Optional[str] = Field("DO", description="Código ISO del país (DO, US, MX, CO, ES, PA, CL, AR, PE)")
    blueprint_package_name: Optional[str] = Field(None, description="Nombre del paquete/blueprint (ej: pkg_restaurantes, pkg_retail)")
    use_fast_method: Optional[bool] = Field(True, description="Usar método SQL directo (más rápido)")


class TenantDeleteRequest(BaseModel):
    """Request para eliminar un tenant"""
    subdomain: str = Field(..., description="Nombre del tenant a eliminar")
    server_id: Optional[str] = Field(None, description="ID del servidor donde está el tenant")
    confirm: bool = Field(False, description="Confirmación de eliminación")


def _get_tenant_primary_url(customer: Customer, subdomain: str) -> str:
    """
    Retorna la URL primaria del tenant.
    Prioridad: dominio personalizado verificado > dominio personalizado activo > sajet.us
    """
    try:
        # Buscar custom domain primario verificado
        primary_domain = None
        for domain in customer.custom_domains:
            if domain.is_primary and domain.verification_status == DomainVerificationStatus.verified:
                primary_domain = domain.external_domain
                break
        
        # Si no hay primario verificado, buscar cualquiera activo
        if not primary_domain:
            for domain in customer.custom_domains:
                if domain.is_active and domain.verification_status == DomainVerificationStatus.verified:
                    primary_domain = domain.external_domain
                    break
        
        # Fallback a sajet.us
        if not primary_domain:
            primary_domain = f"{subdomain}.sajet.us"
        
        # Asegurar https://
        if not primary_domain.startswith("http"):
            primary_domain = f"https://{primary_domain}"
        
        return primary_domain
    except Exception as e:
        logger.warning(f"Error obteniendo URL primaria para {subdomain}: {e}")
        return f"https://{subdomain}.sajet.us"


async def get_all_tenants_from_servers():
    """Obtiene tenants de todos los servidores disponibles usando OdooDatabaseManager"""
    all_tenants = []

    # Precargar TenantDeployment + nodo activo por subdomain
    _deploy_map: dict = {}  # subdomain -> {node_name, backend_host}
    try:
        _db_pre = SessionLocal()
        from ..models.database import ProxmoxNode
        _deployments = (
            _db_pre.query(TenantDeployment)
            .options()
            .all()
        )
        for _dep in _deployments:
            _node_name = None
            if _dep.active_node_id:
                _node = _db_pre.query(ProxmoxNode).filter(ProxmoxNode.id == _dep.active_node_id).first()
                _node_name = _node.hostname if _node else None
            _deploy_map[_dep.subdomain] = {
                "node_name": _node_name or _dep.backend_host,
                "backend_host": _dep.backend_host,
            }
        _db_pre.close()
    except Exception as _e:
        logger.warning(f"No se pudo precargar deploy_map: {_e}")

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
            # Saltar BDs del sistema (incluyendo la BD interna del ERP)
            if db_name in _SYSTEM_DBS:
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
                    
                    _dep_info = _deploy_map.get(customer.subdomain, {})
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
                        "node_name": _dep_info.get("node_name") or server_info.get("name"),
                        "backend_host": _dep_info.get("backend_host") or server_info.get("ip"),
                        "created_at": sub.created_at.isoformat() + "Z" if sub.created_at else None,
                            "url": _get_tenant_primary_url(customer, customer.subdomain),
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
                        
                        _dep_info2 = _deploy_map.get(db_name, {})
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
                            "node_name": _dep_info2.get("node_name") or server_info.get("name"),
                            "backend_host": _dep_info2.get("backend_host") or server_info.get("ip"),
                            "created_at": new_customer.created_at.isoformat() + "Z" if new_customer.created_at else None,
                                "url": _get_tenant_primary_url(new_customer, db_name),
                            "partner_id": None,
                            "partner_name": None,
                            "monthly_amount": 0,
                            "user_count": 1,
                            "billing_mode": None,
                        })
                    except Exception as auto_err:
                        logger.warning(f"No se pudo auto-registrar {db_name}: {auto_err}")
                        db.rollback()
                        _dep_info3 = _deploy_map.get(db_name, {})
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
                            "node_name": _dep_info3.get("node_name") or server_info.get("name"),
                            "backend_host": _dep_info3.get("backend_host") or server_info.get("ip"),
                            "created_at": None,
                            "url": f"https://{db_name}.sajet.us",
                                # Fallback: no customer object, usa sajet.us
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
    db_host = ODOO_DB_HOST
    db_port = int(os.getenv("ODOO_DB_PORT", "5432"))

    try:
        with psycopg.connect(
            host=db_host,
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
                dbs = [row[0] for row in rows if row and row[0] and row[0] not in _SYSTEM_DBS]
                logger.info(
                    f"PostgreSQL fallback: {len(dbs)} BDs detectadas via {db_host}:{db_port} (server={server.id})"
                )
                return dbs
    except Exception as e:
        logger.warning(f"No se pudo listar BDs via PostgreSQL en {db_host}:{db_port} (server={server.id}): {e}")
        return []


async def _verify_remote_tenant_absence(
    subdomain: str,
    server_id: Optional[str],
) -> dict:
    """
    Verifica de forma estricta si la BD del tenant sigue existiendo en PostgreSQL remoto.
    Retorna:
      - exists: True/False
      - verified: si al menos un servidor pudo ser consultado
      - errors: lista de errores por servidor
    - server_id: id donde se encontró (si aplica)
    - active_connections: conexiones activas detectadas cuando existe
    """
    normalized = (subdomain or "").strip().lower()
    servers_to_check = []

    if server_id:
        server = ODOO_SERVERS.get(server_id)
        if not server:
            return {
                "exists": False,
                "verified": False,
                "errors": [f"Servidor '{server_id}' no encontrado"],
                "server_id": None,
                "active_connections": 0,
            }
        servers_to_check = [server]
    else:
        servers_to_check = list(ODOO_SERVERS.values())

    db_port = int(os.getenv("ODOO_DB_PORT", "5432"))
    db_host = ODOO_DB_HOST
    verified = False
    errors: List[str] = []

    for server in servers_to_check:
        if not server:
            continue
        try:
            with psycopg.connect(
                host=db_host,
                port=db_port,
                dbname="postgres",
                user=ODOO_DB_USER,
                password=ODOO_DB_PASSWORD,
                connect_timeout=5,
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s LIMIT 1",
                        (normalized,),
                    )
                    exists = cur.fetchone() is not None
                    verified = True
                    if exists:
                        active_connections = 0
                        try:
                            cur.execute(
                                "SELECT count(*) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                                (normalized,),
                            )
                            c_row = cur.fetchone()
                            active_connections = int(c_row[0]) if c_row and c_row[0] is not None else 0
                        except Exception:
                            active_connections = 0
                        return {
                            "exists": True,
                            "verified": True,
                            "errors": errors,
                            "server_id": server.id,
                            "active_connections": active_connections,
                        }
        except Exception as check_err:
            errors.append(f"{server.id} via {db_host}:{db_port}: {check_err}")

    return {
        "exists": False,
        "verified": verified,
        "errors": errors,
        "server_id": None,
        "active_connections": 0,
    }


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
async def list_tenants(request: Request, access_token: str = Cookie(None)):
    """Listado de tenants desde todos los servidores"""
    _require_admin_base(request, access_token)
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
    access_token: str = Cookie(None)
):
    """
    Crear un nuevo tenant (base de datos Odoo). Requiere rol admin.

    - Si no se especifica server_id, se selecciona automáticamente el mejor servidor
    - Credenciales por defecto: configuradas en variables de entorno
    - Por defecto usa método SQL rápido (duplica template_tenant)
    """
    _require_admin_base(request, access_token)

    # Política SAJET: credenciales bootstrap siempre derivadas del nombre de BD.
    # - Login: <nombrebda>@sajet.us
    # - Password: generada aleatoriamente
    # Se persisten en auditoría (acceso admin-only en /api/audit).
    effective_admin_login, effective_admin_password = _build_tenant_admin_credentials(
        payload.subdomain,
        "sajet.us",
    )

    # Verificar idempotencia local. Si existe localmente pero no existe en remoto,
    # permitir reprovisionar para recuperar estados parciales.
    db = SessionLocal()
    existing_local_customer: Optional[Customer] = None
    try:
        existing_local_customer = db.query(Customer).filter(Customer.subdomain == payload.subdomain).first()
    finally:
        db.close()

    if existing_local_customer:
        remote_exists = False
        remote_server_id = None
        if payload.server_id:
            servers_to_check = [ODOO_SERVERS.get(payload.server_id)] if payload.server_id in ODOO_SERVERS else []
        else:
            servers_to_check = list(ODOO_SERVERS.values())

        for server in servers_to_check:
            if not server:
                continue
            try:
                async with OdooDatabaseManager(server) as manager:
                    if await manager.database_exists(payload.subdomain):
                        remote_exists = True
                        remote_server_id = server.id
                        break
            except Exception as e:
                logger.warning(
                    f"No se pudo verificar existencia remota de '{payload.subdomain}' en {getattr(server, 'id', 'unknown')}: {e}"
                )

        if remote_exists:
            raise HTTPException(status_code=409, detail=f"El subdominio '{payload.subdomain}' ya existe")

        logger.warning(
            f"Recover mode: existe registro local para '{payload.subdomain}' pero no BD remota. "
            f"Se intentará reprovisionar (server_hint={payload.server_id}, remote_found={remote_server_id})."
        )

    try:
        creation_mode: Optional[str] = None
        fallback_reason: Optional[str] = None

        # Usar método rápido por defecto con fallback automático
        if payload.use_fast_method:
            fast_result = await create_tenant_from_template(
                subdomain=payload.subdomain,
                company_name=payload.company_name,
                server_id=payload.server_id,
                admin_login=effective_admin_login,
                admin_password=effective_admin_password,
                country_code=payload.country_code,
                blueprint_package_name=payload.blueprint_package_name,
            )
            fast_error_code = str(fast_result.get("error_code") or "")

            # Si fast path falla por causas recuperables, usar ruta estándar automáticamente
            recoverable_fast_failures = {
                "template_missing",
                "template_check_failed",
                "proxmox_ssh_unavailable",
                "fast_path_unavailable",
                "filestore_sync_failed",
            }
            if not fast_result.get("success") and fast_error_code in recoverable_fast_failures:
                fallback_reason = fast_result.get("error") or "Fast path no disponible"
                logger.warning(
                    f"Fast path falló para '{payload.subdomain}' ({fast_error_code}). "
                    f"Aplicando fallback estándar. Detalle: {fallback_reason}"
                )
                _loc = COUNTRY_LOCALIZATION.get((payload.country_code or 'DO').upper(), {})
                result = await provision_tenant(
                    subdomain=payload.subdomain,
                    admin_login=effective_admin_login,
                    admin_password=effective_admin_password,
                    server_id=payload.server_id,
                    demo=False,
                    lang=_loc.get('lang', 'es_DO'),
                    country_code=payload.country_code,
                    blueprint_package_name=payload.blueprint_package_name,
                )
                creation_mode = "fallback_standard"
            else:
                result = fast_result
                if result.get("success"):
                    creation_mode = "fast"
        else:
            # Método tradicional via HTTP API de Odoo
            _loc2 = COUNTRY_LOCALIZATION.get((payload.country_code or 'DO').upper(), {})
            result = await provision_tenant(
                subdomain=payload.subdomain,
                admin_login=effective_admin_login,
                admin_password=effective_admin_password,
                server_id=payload.server_id,
                demo=False,
                lang=_loc2.get('lang', 'es_DO'),
                country_code=payload.country_code,
                blueprint_package_name=payload.blueprint_package_name,
            )
            creation_mode = "fallback_standard"
        
        if result.get("success"):
            already_existed = result.get("already_existed", False)
            # Registrar en BD local
            db = SessionLocal()
            try:
                existing = db.query(Customer).filter(Customer.subdomain == payload.subdomain).first()
                if not existing:
                    customer = Customer(
                        company_name=payload.company_name or result.get("company_name") or payload.subdomain.title(),
                        full_name=payload.company_name or result.get("company_name") or payload.subdomain.title(),
                        email=effective_admin_login,
                        subdomain=payload.subdomain
                    )
                    db.add(customer)
                    db.commit()
                    db.refresh(customer)
                    
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
                    logger.info(f"Tenant '{payload.subdomain}' registrado en BD local (customer={customer.id})")

                    # ── Crear TenantDeployment con campos multi-nodo ──
                    from ..services.deployment_writer import ensure_tenant_deployment
                    dep_result = ensure_tenant_deployment(
                        subdomain=payload.subdomain,
                        subscription_id=subscription.id,
                        customer_id=customer.id,
                        server_id=result.get("server"),
                        server_ip=None,
                        plan_name=payload.plan or "basic",
                        tunnel_id=None,
                        db=db,
                    )
                    if dep_result.get("success"):
                        db.commit()
                        result["deployment_id"] = dep_result["deployment_id"]
                        logger.info(
                            f"✅ TenantDeployment #{dep_result['deployment_id']} "
                            f"({dep_result['status']}) para '{payload.subdomain}'"
                        )
                    else:
                        logger.warning(
                            f"⚠️ TenantDeployment no creado para '{payload.subdomain}': "
                            f"{dep_result.get('error')}"
                        )
                else:
                    result["customer_id"] = existing.id
                    # Verificar que tenga suscripción activa
                    sub = db.query(Subscription).filter(
                        Subscription.customer_id == existing.id,
                        Subscription.status == SubscriptionStatus.active
                    ).first()
                    if sub:
                        result["subscription_id"] = sub.id
                    else:
                        # Crear suscripción si no existe
                        new_sub = Subscription(
                            customer_id=existing.id,
                            plan_name=payload.plan or "basic",
                            status=SubscriptionStatus.active,
                            billing_mode=BillingMode.JETURING_DIRECT_SUBSCRIPTION,
                        )
                        db.add(new_sub)
                        db.commit()
                        db.refresh(new_sub)
                        result["subscription_id"] = new_sub.id
                        logger.info(f"Suscripción creada para tenant existente '{payload.subdomain}'")

                    # ── Asegurar TenantDeployment para tenant existente ──
                    _sub_id = result.get("subscription_id")
                    if _sub_id:
                        from ..services.deployment_writer import ensure_tenant_deployment
                        dep_result = ensure_tenant_deployment(
                            subdomain=payload.subdomain,
                            subscription_id=_sub_id,
                            customer_id=existing.id,
                            server_id=result.get("server"),
                            plan_name=payload.plan or "basic",
                            db=db,
                        )
                        if dep_result.get("success"):
                            db.commit()
                            result["deployment_id"] = dep_result["deployment_id"]
            except Exception as db_err:
                logger.warning(f"No se pudo registrar tenant en BD local: {db_err}")
                db.rollback()
            finally:
                db.close()
            
            status_msg = "vinculado" if already_existed else "creado"

            # Provisionar subdominio .sajet.us en nginx automáticamente
            try:
                nginx_result = provision_sajet_subdomain(payload.subdomain)
                if nginx_result.get("success"):
                    logger.info(f"✅ Subdominio {payload.subdomain}.sajet.us provisionado en nginx")
                    result["nginx_provisioned"] = True
                else:
                    ng_err = nginx_result.get("error") or "Error no especificado al provisionar nginx"
                    logger.error(
                        f"❌ Tenant '{payload.subdomain}' creado en BD pero nginx no quedó configurado: {ng_err}"
                    )
                    _log_tenant_audit(
                        request,
                        event_type="TENANT_CREATE_NGINX_FAILED",
                        resource=f"tenant:{payload.subdomain}",
                        action="create",
                        status="error",
                        details={
                            "subdomain": payload.subdomain,
                            "server_id": result.get("server"),
                            "nginx_error": ng_err,
                            "creation_mode": creation_mode,
                        },
                    )
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            f"Tenant '{payload.subdomain}' creado, pero no se pudo publicar el subdominio en nginx: {ng_err}. "
                            "Revise conectividad/permiso en CT105 y PCT160."
                        ),
                    )
            except HTTPException:
                raise
            except Exception as ng_err:
                logger.error(f"❌ Error provisionando nginx para {payload.subdomain}: {ng_err}")
                _log_tenant_audit(
                    request,
                    event_type="TENANT_CREATE_NGINX_FAILED",
                    resource=f"tenant:{payload.subdomain}",
                    action="create",
                    status="error",
                    details={
                        "subdomain": payload.subdomain,
                        "server_id": result.get("server"),
                        "nginx_error": str(ng_err),
                        "creation_mode": creation_mode,
                    },
                )
                raise HTTPException(
                    status_code=502,
                    detail=(
                        f"Tenant '{payload.subdomain}' creado, pero falló la publicación nginx: {ng_err}. "
                        "Revise logs de nginx y conectividad CT105/PCT160."
                    ),
                )

            _log_tenant_audit(
                request,
                event_type="TENANT_CREATED",
                resource=f"tenant:{payload.subdomain}",
                action="create",
                status="success",
                details={
                    "subdomain": payload.subdomain,
                    "server_id": result.get("server"),
                    "already_existed": already_existed,
                    "creation_mode": creation_mode,
                    "partner_id": payload.partner_id,
                    "url": result.get("url"),
                    "admin_login": effective_admin_login,
                    "generated_admin_password": effective_admin_password,
                },
            )

            response_payload = {
                "success": True,
                "already_existed": already_existed,
                "message": f"Tenant '{payload.subdomain}' {status_msg} exitosamente",
                "tenant": {
                    "subdomain": payload.subdomain,
                    "url": result.get("url"),
                    "server": result.get("server"),
                    "admin_login": effective_admin_login,
                    "admin_password": effective_admin_password,
                    "status": "active"
                },
                "details": result
            }
            if creation_mode:
                response_payload["creation_mode"] = creation_mode
            if fallback_reason:
                response_payload["fallback_reason"] = fallback_reason
            if existing_local_customer is not None:
                response_payload["recovered_from_partial_state"] = True
            return response_payload
        else:
            error_msg = result.get("error", "Error creando tenant")
            _log_tenant_audit(
                request,
                event_type="TENANT_CREATE_FAILED",
                resource=f"tenant:{payload.subdomain}",
                action="create",
                status="error",
                details={
                    "subdomain": payload.subdomain,
                    "server_id": payload.server_id,
                    "error": error_msg,
                    "creation_mode": creation_mode,
                    "fallback_reason": fallback_reason,
                },
            )
            # Si el error indica que ya existe, dar 409 (no 400)
            if "ya existe" in error_msg.lower():
                raise HTTPException(status_code=409, detail=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando tenant: {e}")
        _log_tenant_audit(
            request,
            event_type="TENANT_CREATE_EXCEPTION",
            resource=f"tenant:{payload.subdomain}",
            action="create",
            status="error",
            details={"error": str(e), "subdomain": payload.subdomain, "server_id": payload.server_id},
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{subdomain}")
async def delete_tenant_endpoint(
    subdomain: str,
    request: Request,
    server_id: Optional[str] = Query(None, description="ID del servidor"),
    confirm: bool = Query(False, description="Confirmar eliminación"),
    confirm_name: Optional[str] = Query(None, description="Escriba el subdominio para confirmar"),
    access_token: str = Cookie(None)
):
    """
    Eliminar un tenant (base de datos Odoo). Requiere rol admin.

    - Requiere confirm=true para ejecutar
    - Requiere confirm_name igual al subdominio
    - Si no se especifica server_id, busca en todos los servidores
    """
    _require_admin_base(request, access_token)
    if not confirm:
        return {
            "success": False,
            "message": f"Debe confirmar la eliminación con ?confirm=true",
            "warning": f"Esta acción eliminará permanentemente la base de datos '{subdomain}'"
        }
    if not confirm_name or confirm_name.strip().lower() != subdomain.strip().lower():
        raise HTTPException(
            status_code=400,
            detail=f"Confirmación inválida. Debe escribir exactamente '{subdomain}'"
        )
    # Bloquear BDs del sistema (la propia BD del ERP + protegidas por env)
    normalized_sub = subdomain.strip().lower()
    if normalized_sub in _SYSTEM_DBS or is_tenant_protected(subdomain):
        reason = "system_database" if normalized_sub in _SYSTEM_DBS else "protected_tenant"
        msg = (
            f"'{subdomain}' es la base de datos interna del sistema y no puede eliminarse desde el panel."
            if normalized_sub in _SYSTEM_DBS
            else f"'{subdomain}' está protegido y no puede eliminarse"
        )
        _log_tenant_audit(
            request,
            event_type="TENANT_DELETE_BLOCKED",
            resource=f"tenant:{subdomain}",
            action="delete",
            status="blocked",
            details={"reason": reason, "server_id": server_id},
        )
        raise HTTPException(status_code=403, detail=msg)
    
    try:
        # 1) Eliminar primero registro local (BDA), conservando datos para respaldo/email
        local_deleted = False
        tenant_email = None
        tenant_company = subdomain
        db = SessionLocal()
        try:
            customer = db.query(Customer).filter(Customer.subdomain == subdomain).first()
            if customer:
                tenant_email = customer.email
                tenant_company = customer.company_name or subdomain
                db.query(Subscription).filter(Subscription.customer_id == customer.id).delete()
                db.delete(customer)
                db.commit()
                local_deleted = True
                logger.info(f"Eliminado registro local de tenant: {subdomain}")
        except Exception as db_err:
            db.rollback()
            logger.warning(f"No se pudo eliminar registro local: {db_err}")
        finally:
            db.close()

        # 2) Crear backup de la BD Odoo antes de borrarla
        backup_result = await backup_tenant(subdomain, server_id)

        # 3) Enviar backup al correo del cliente (si existe y se generó)
        email_result = None
        if backup_result.get("success") and tenant_email:
            try:
                email_result = send_tenant_backup_deleted(
                    to_email=tenant_email,
                    company_name=tenant_company,
                    subdomain=subdomain,
                    backup_path=backup_result["backup_path"],
                    backup_filename=backup_result.get("backup_file"),
                )
            except Exception as mail_err:
                logger.warning(f"No se pudo enviar backup por email para {subdomain}: {mail_err}")
                email_result = {"success": False, "error": str(mail_err)}

        # 4) Eliminar BD del tenant en Odoo
        result = await delete_tenant(subdomain, server_id)
        deleted_remote = bool(result.get("success"))

        # 4.1) Verificar estrictamente que la BD ya no exista en remoto.
        verification = await _verify_remote_tenant_absence(subdomain, server_id)
        if verification.get("exists"):
            srv = verification.get("server_id") or "servidor remoto"
            detail = (
                f"No se confirmó eliminación remota. La BD '{subdomain}' aún existe en {srv}. "
                f"Conexiones activas detectadas: {verification.get('active_connections', 0)}."
            )
            if result.get("error"):
                detail = f"{detail} Último error de eliminación: {result.get('error')}"
            _log_tenant_audit(
                request,
                event_type="TENANT_DELETE_CONFLICT",
                resource=f"tenant:{subdomain}",
                action="delete",
                status="error",
                details={
                    "subdomain": subdomain,
                    "server_id": server_id,
                    "verification": verification,
                    "delete_result": result,
                    "local_deleted": local_deleted,
                },
            )
            raise HTTPException(
                status_code=409,
                detail=detail,
            )
        if not verification.get("verified"):
            detail = "No se pudo verificar la eliminación remota"
            if verification.get("errors"):
                detail = f"{detail}: {'; '.join(verification['errors'])}"
            _log_tenant_audit(
                request,
                event_type="TENANT_DELETE_UNVERIFIED",
                resource=f"tenant:{subdomain}",
                action="delete",
                status="warning",
                details={
                    "subdomain": subdomain,
                    "server_id": server_id,
                    "verification": verification,
                    "delete_result": result,
                    "local_deleted": local_deleted,
                },
            )
            raise HTTPException(status_code=503, detail=detail)

        # 5) Limpiar nginx solo si se eliminó la BD remota
        if deleted_remote:
            try:
                remove_sajet_subdomain(subdomain)
                logger.info(f"Subdominio {subdomain}.sajet.us eliminado de nginx")
            except Exception as ng_err:
                logger.warning(f"No se pudo limpiar nginx para {subdomain}: {ng_err}")

        # 5.1) Eliminar registro DNS de Cloudflare
        cloudflare_result: dict = {}
        if deleted_remote:
            try:
                cloudflare_result = await CloudflareManager.delete_subdomain_dns(
                    subdomain=subdomain,
                    domain="sajet.us",
                )
                if cloudflare_result.get("deleted", 0) > 0:
                    logger.info(
                        f"DNS Cloudflare eliminado para {subdomain}.sajet.us "
                        f"({cloudflare_result['deleted']} registro/s)"
                    )
                elif cloudflare_result.get("total_found", 0) == 0:
                    logger.info(f"No había registro DNS en Cloudflare para {subdomain}.sajet.us")
                else:
                    logger.warning(
                        f"Problemas eliminando DNS Cloudflare para {subdomain}: "
                        f"{cloudflare_result.get('errors')}"
                    )
            except Exception as cf_err:
                logger.warning(f"No se pudo eliminar DNS Cloudflare para {subdomain}: {cf_err}")
                cloudflare_result = {"success": False, "error": str(cf_err)}

        # 6) Respuesta final idempotente
        if deleted_remote:
            _log_tenant_audit(
                request,
                event_type="TENANT_DELETED",
                resource=f"tenant:{subdomain}",
                action="delete",
                status="success",
                details={
                    "subdomain": subdomain,
                    "server_id": server_id,
                    "local_deleted": local_deleted,
                    "backup_success": backup_result.get("success"),
                    "email_success": email_result.get("success") if isinstance(email_result, dict) else None,
                    "delete_result": result,
                },
            )
            return {
                "success": True,
                "message": f"Tenant '{subdomain}' eliminado exitosamente",
                "details": result,
                "local_deleted": local_deleted,
                "backup": backup_result,
                "email": email_result,
                "verified_remote_absence": True,
                "cloudflare_dns": cloudflare_result,
            }

        # Si la BD remota no existe pero el registro local sí se limpió, tratar como éxito parcial
        err = (result.get("error") or "Error eliminando tenant").strip()
        if "no encontrado" in err.lower() and local_deleted:
            _log_tenant_audit(
                request,
                event_type="TENANT_DELETE_PARTIAL",
                resource=f"tenant:{subdomain}",
                action="delete",
                status="warning",
                details={
                    "subdomain": subdomain,
                    "server_id": server_id,
                    "warning": err,
                    "local_deleted": local_deleted,
                    "delete_result": result,
                },
            )
            return {
                "success": True,
                "message": f"Registro local de '{subdomain}' eliminado. La BD remota ya no existía.",
                "warning": err,
                "details": result,
                "local_deleted": local_deleted,
                "backup": backup_result,
                "email": email_result,
                "verified_remote_absence": True,
            }

        # Si no existe en local ni remoto, devolver 404
        if "no encontrado" in err.lower() and not local_deleted:
            _log_tenant_audit(
                request,
                event_type="TENANT_DELETE_NOT_FOUND",
                resource=f"tenant:{subdomain}",
                action="delete",
                status="warning",
                details={"subdomain": subdomain, "server_id": server_id, "error": err},
            )
            raise HTTPException(status_code=404, detail=err)

        _log_tenant_audit(
            request,
            event_type="TENANT_DELETE_FAILED",
            resource=f"tenant:{subdomain}",
            action="delete",
            status="error",
            details={
                "subdomain": subdomain,
                "server_id": server_id,
                "error": err,
                "delete_result": result,
                "local_deleted": local_deleted,
            },
        )
        raise HTTPException(status_code=400, detail=err)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando tenant: {e}")
        _log_tenant_audit(
            request,
            event_type="TENANT_DELETE_EXCEPTION",
            resource=f"tenant:{subdomain}",
            action="delete",
            status="error",
            details={"subdomain": subdomain, "server_id": server_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{subdomain}")
async def get_tenant_details(
    subdomain: str,
    request: Request,
    access_token: str = Cookie(None)
):
    """Obtener detalles de un tenant específico. Requiere autenticación."""
    _require_admin_base(request, access_token)
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


# ═══════════════════════════════════════════════════════
# INSTALACIÓN DE MÓDULOS ON-DEMAND
# ═══════════════════════════════════════════════════════

class ModuleInstallRequest(BaseModel):
    """Request para instalar módulos en un tenant existente"""
    modules: List[str] = Field(..., min_length=1, description="Lista de technical_names de módulos a instalar")
    blueprint_package_name: Optional[str] = Field(None, description="Instalar todos los módulos de un paquete/blueprint")


@router.post("/{subdomain}/modules/install")
async def install_modules_on_tenant(
    subdomain: str,
    payload: ModuleInstallRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """
    Instala módulos Odoo en un tenant existente.

    Accesible desde:
    - Panel admin (rol admin)
    - Panel socio (rol partner — solo módulos partner_allowed)
    - Panel cliente (rol client — solo módulos de su plan)

    Los módulos se instalan via XML-RPC al servidor Odoo donde vive el tenant.
    """
    _require_admin_base(request, access_token)

    refresh_odoo_servers()

    # Resolver módulos del blueprint si se proporcionó
    modules_to_install: List[str] = list(payload.modules) if payload.modules else []
    if payload.blueprint_package_name:
        bp_mods = _resolve_blueprint_modules(payload.blueprint_package_name)
        for m in bp_mods:
            if m not in modules_to_install:
                modules_to_install.append(m)

    if not modules_to_install:
        raise HTTPException(400, "No hay módulos para instalar")

    # Buscar en qué servidor está el tenant
    target_server = None
    for server in ODOO_SERVERS.values():
        if not server:
            continue
        try:
            async with OdooDatabaseManager(server) as manager:
                if await manager.database_exists(subdomain):
                    target_server = server
                    break
        except Exception:
            continue

    if not target_server:
        raise HTTPException(404, f"Tenant '{subdomain}' no encontrado en ningún servidor")

    # Instalar via XML-RPC
    url = f"http://{target_server.ip}:{target_server.port}"

    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        # Intentar con login del tenant
        tenant_login = f"{subdomain}@sajet.us"
        uid = common.authenticate(subdomain, tenant_login, DEFAULT_ADMIN_PASSWORD, {})
        if not uid:
            uid = common.authenticate(subdomain, DEFAULT_ADMIN_LOGIN, DEFAULT_ADMIN_PASSWORD, {})
        if not uid:
            raise HTTPException(500, f"No se pudo autenticar en '{subdomain}' para instalar módulos")

        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

        installed = []
        failed = []
        already = []

        for module_name in modules_to_install:
            try:
                module_ids = models.execute_kw(
                    subdomain, uid, DEFAULT_ADMIN_PASSWORD,
                    'ir.module.module', 'search',
                    [[('name', '=', module_name)]]
                )
                if module_ids:
                    module_data = models.execute_kw(
                        subdomain, uid, DEFAULT_ADMIN_PASSWORD,
                        'ir.module.module', 'read',
                        [module_ids], {'fields': ['state']}
                    )
                    state = module_data[0]['state'] if module_data else 'uninstalled'

                    if state in ('installed', 'to upgrade'):
                        already.append(module_name)
                    else:
                        models.execute_kw(
                            subdomain, uid, DEFAULT_ADMIN_PASSWORD,
                            'ir.module.module', 'button_immediate_install',
                            [module_ids]
                        )
                        installed.append(module_name)
                else:
                    failed.append(f"{module_name}(not_found)")
            except Exception as e:
                failed.append(f"{module_name}({str(e)[:50]})")

        return {
            "success": True,
            "subdomain": subdomain,
            "server": target_server.id,
            "installed": installed,
            "already_installed": already,
            "failed": failed,
            "total_requested": len(modules_to_install),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error instalando módulos en '{subdomain}': {e}")
        raise HTTPException(500, f"Error instalando módulos: {str(e)}")
