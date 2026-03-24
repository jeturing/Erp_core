"""
Domains API Routes
Endpoints para gestión de dominios personalizados de clientes.
Épica 8: Verificación temprana desde TENANT_REQUESTED, no bloqueante.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Cookie, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
import logging
from urllib.parse import urlparse

from ..models.database import get_db
from ..services.domain_manager import DomainManager
from .roles import verify_token_with_role

router = APIRouter(prefix="/api/domains", tags=["domains"])
logger = logging.getLogger(__name__)


def _background_domain_verify(domain_id: int, db_url: str):
    """
    Épica 8 — Background task: verificación temprana de dominio.
    Se ejecuta async, no bloquea el flujo de onboarding.
    """
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from ..models.database import CustomDomain

    from ..config import DATABASE_URL as _cfg_db_url
    url = db_url or _cfg_db_url
    engine = create_engine(url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        domain = db.query(CustomDomain).filter(CustomDomain.id == domain_id).first()
        if not domain:
            logger.warning(f"Background verify: domain {domain_id} not found")
            return
        manager = DomainManager(db)
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(manager.verify_domain(domain_id))
        loop.close()
        logger.info(f"Background verify domain {domain.external_domain}: {result.get('verification_status', 'unknown')}")
    except Exception as e:
        logger.error(f"Background verify domain {domain_id} failed: {e}")
    finally:
        db.close()


def _check_domain_limit(db: Session, customer_id: int):
    """Verifica que el cliente no exceda el límite de dominios de su plan."""
    from ..models.database import Customer, Subscription, SubscriptionStatus, Plan, CustomDomain

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    sub = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.status == SubscriptionStatus.active,
    ).first()

    if not sub:
        raise HTTPException(status_code=400, detail="Cliente no tiene suscripción activa")

    plan = db.query(Plan).filter(Plan.name == sub.plan_name, Plan.is_active == True).first()
    if not plan:
        # Sin plan definido → permitir (backward compat)
        return

    max_domains = plan.max_domains if plan.max_domains is not None else 0
    # -1 = ilimitado, 0 = sin dominios custom
    if max_domains == -1:
        return  # Sin límite

    current_count = db.query(CustomDomain).filter(
        CustomDomain.customer_id == customer_id,
        CustomDomain.is_active == True,
    ).count()

    if current_count >= max_domains:
        raise HTTPException(
            status_code=403,
            detail=f"Límite de dominios alcanzado ({current_count}/{max_domains}). "
                   f"El plan '{plan.display_name or plan.name}' permite máximo {max_domains} dominio(s). "
                   f"Actualice a Enterprise para dominios ilimitados.",
        )


def _extract_hostname(raw_domain: Optional[str]) -> Optional[str]:
    """Extrae hostname normalizado desde URL o dominio plano."""
    if not raw_domain:
        return None

    value = raw_domain.strip()
    if not value:
        return None

    candidate = value if "://" in value else f"//{value}"
    parsed = urlparse(candidate)
    host = (parsed.netloc or parsed.path or "").strip().lower().strip(".")
    if not host:
        return None

    # Eliminar path accidental y puerto
    host = host.split("/")[0].split(":")[0]
    if not host or "." not in host:
        return None

    return host


# ==================== Auth Dependencies ====================

async def get_current_admin(access_token: str = Cookie(None)):
    """Dependency para verificar token de admin desde cookie"""
    if not access_token:
        raise HTTPException(status_code=401, detail="No autorizado")
    return verify_token_with_role(access_token, required_role="admin")


async def get_current_tenant(access_token: str = Cookie(None)):
    """Dependency para verificar token de tenant desde cookie"""
    if not access_token:
        raise HTTPException(status_code=401, detail="No autorizado")
    return verify_token_with_role(access_token, required_role="tenant")


# ==================== Schemas ====================

class DomainCreate(BaseModel):
    external_domain: str = Field(..., description="Dominio del cliente (ej: www.impulse-max.com)")
    customer_id: int = Field(..., description="ID del cliente")
    tenant_deployment_id: Optional[int] = Field(None, description="ID del deployment asociado")

class DomainUpdate(BaseModel):
    is_primary: Optional[bool] = None
    target_node_ip: Optional[str] = None
    target_port: Optional[int] = None
    tenant_deployment_id: Optional[int] = None

class DomainResponse(BaseModel):
    id: int
    customer_id: int
    tenant_deployment_id: Optional[int]
    external_domain: str
    sajet_subdomain: str
    sajet_full_domain: str
    verification_status: str
    verification_token: Optional[str]
    verified_at: Optional[str]
    cloudflare_configured: bool
    tunnel_ingress_configured: bool
    nginx_configured: bool = False
    ssl_status: Optional[str]
    is_active: bool
    is_primary: bool
    target_node_ip: str
    target_port: int
    created_at: str
    updated_at: Optional[str]

class DomainListResponse(BaseModel):
    items: List[DomainResponse]
    total: int
    limit: int
    offset: int


# ==================== Endpoints ====================

@router.get("/quota/{customer_id}", response_model=dict)
async def get_domain_quota(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Obtiene la cuota de dominios del cliente según su plan.
    Retorna: used, max (-1=ilimitado, 0=no permitido), plan_name, can_add
    """
    from ..models.database import Customer, Subscription, SubscriptionStatus, Plan, CustomDomain

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    used = db.query(CustomDomain).filter(
        CustomDomain.customer_id == customer_id,
    ).count()

    active = db.query(CustomDomain).filter(
        CustomDomain.customer_id == customer_id,
        CustomDomain.is_active == True,
    ).count()

    sub = db.query(Subscription).filter(
        Subscription.customer_id == customer_id,
        Subscription.status == SubscriptionStatus.active,
    ).first()

    plan_name = sub.plan_name if sub else customer.plan.value if customer.plan else "basic"
    plan = db.query(Plan).filter(Plan.name == plan_name, Plan.is_active == True).first()

    max_domains = plan.max_domains if plan and plan.max_domains is not None else 0
    can_add = max_domains == -1 or used < max_domains

    return {
        "customer_id": customer_id,
        "company_name": customer.company_name,
        "plan_name": plan.display_name if plan else plan_name,
        "used": used,
        "active": active,
        "max": max_domains,
        "can_add": can_add,
        "unlimited": max_domains == -1,
    }


@router.get("/customers-with-plans", response_model=dict)
async def list_customers_with_domain_info(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Lista todos los clientes con info de plan y cuota de dominios.
    Útil para el selector de cliente en el formulario de dominios.
    """
    from ..models.database import Customer, Subscription, SubscriptionStatus, Plan, CustomDomain

    customers = db.query(Customer).order_by(Customer.company_name).all()
    result = []

    for c in customers:
        sub = db.query(Subscription).filter(
            Subscription.customer_id == c.id,
            Subscription.status == SubscriptionStatus.active,
        ).first()

        plan_name = sub.plan_name if sub else (c.plan.value if c.plan else "basic")
        plan = db.query(Plan).filter(Plan.name == plan_name, Plan.is_active == True).first()
        max_d = plan.max_domains if plan and plan.max_domains is not None else 0

        used = db.query(CustomDomain).filter(CustomDomain.customer_id == c.id).count()

        result.append({
            "id": c.id,
            "company_name": c.company_name,
            "subdomain": c.subdomain,
            "plan_name": plan.display_name if plan else plan_name,
            "plan_key": plan_name,
            "max_domains": max_d,
            "used_domains": used,
            "can_add": max_d == -1 or used < max_d,
            "unlimited": max_d == -1,
        })

    return {"items": result, "total": len(result)}


@router.get("/linked-domains/{customer_id}", response_model=dict)
async def get_linked_domains_for_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Devuelve los dominios vinculados/visibles de un cliente combinando:
    - Dominio base del tenant: {subdomain}.sajet.us
    - Dominios custom registrados en ERP Core
    - Dominios detectados en websites de Odoo (tenant DB)
    """
    from ..models.database import Customer, CustomDomain, TenantDeployment
    from ..services.odoo_website_configurator import OdooWebsiteConfigurator

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    tenant_db = customer.subdomain
    deployment = (
        db.query(TenantDeployment)
        .filter(TenantDeployment.customer_id == customer_id)
        .order_by(TenantDeployment.id.desc())
        .first()
    )
    if deployment and deployment.database_name:
        tenant_db = deployment.database_name

    domain_map = {}

    def _add_domain(
        name: Optional[str],
        source: str,
        *,
        is_active: Optional[bool] = None,
        verification_status: Optional[str] = None,
        custom_domain_id: Optional[int] = None,
        website_id: Optional[int] = None,
        website_name: Optional[str] = None,
    ):
        host = _extract_hostname(name)
        if not host:
            return

        item = domain_map.get(host)
        if not item:
            item = {
                "domain": host,
                "sources": [],
                "is_active": False,
                "verification_status": None,
                "custom_domain_id": None,
                "odoo_website_ids": [],
                "odoo_website_names": [],
            }
            domain_map[host] = item

        if source not in item["sources"]:
            item["sources"].append(source)

        if is_active is True:
            item["is_active"] = True

        if verification_status and not item["verification_status"]:
            item["verification_status"] = verification_status

        if custom_domain_id and not item["custom_domain_id"]:
            item["custom_domain_id"] = custom_domain_id

        if website_id and website_id not in item["odoo_website_ids"]:
            item["odoo_website_ids"].append(website_id)

        if website_name and website_name not in item["odoo_website_names"]:
            item["odoo_website_names"].append(website_name)

    # 1) Dominio base del tenant
    base_domain = f"{customer.subdomain}.sajet.us"
    _add_domain(base_domain, "base", is_active=True, verification_status="verified")

    # 2) Dominios custom registrados en ERP Core
    custom_domains = db.query(CustomDomain).filter(CustomDomain.customer_id == customer_id).all()
    for d in custom_domains:
        _add_domain(
            d.external_domain,
            "custom",
            is_active=bool(d.is_active),
            verification_status=d.verification_status.value if d.verification_status else None,
            custom_domain_id=d.id,
        )

    # 3) Dominios detectados desde websites Odoo
    odoo_error = None
    try:
        configurator = OdooWebsiteConfigurator()
        websites_result = configurator.list_websites(tenant_db)
        if websites_result.get("success"):
            for w in websites_result.get("websites", []):
                _add_domain(
                    w.get("domain"),
                    "odoo",
                    website_id=w.get("id"),
                    website_name=w.get("name"),
                )
        else:
            odoo_error = websites_result.get("error") or "No se pudo consultar websites de Odoo"
    except Exception as e:
        odoo_error = str(e)

    domains = []
    for _, item in domain_map.items():
        item["sources"] = sorted(item["sources"])
        item["source_count"] = len(item["sources"])
        domains.append(item)

    domains.sort(key=lambda x: x["domain"])

    summary = {
        "total": len(domains),
        "base": sum(1 for d in domains if "base" in d["sources"]),
        "custom": sum(1 for d in domains if "custom" in d["sources"]),
        "odoo": sum(1 for d in domains if "odoo" in d["sources"]),
    }

    return {
        "success": True,
        "customer_id": customer.id,
        "company_name": customer.company_name,
        "subdomain": customer.subdomain,
        "tenant_db": tenant_db,
        "domains": domains,
        "summary": summary,
        "odoo_error": odoo_error,
    }


@router.post("", response_model=dict)
async def create_domain(
    data: DomainCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Registra un nuevo dominio personalizado.
    Verifica límite de dominios del plan antes de crear.
    
    El sistema:
    1. Verifica límite de dominios del plan del cliente
    2. Genera un subdominio de sajet.us automáticamente
    3. Devuelve instrucciones para configurar el CNAME en el DNS del cliente
    """
    # Verificar límite de dominios del plan
    _check_domain_limit(db, data.customer_id)

    manager = DomainManager(db)
    result = manager.create_domain(
        external_domain=data.external_domain,
        customer_id=data.customer_id,
        tenant_deployment_id=data.tenant_deployment_id,
        created_by=current_user.get("email", "system")
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    # Auto-configurar CNAME interno en Cloudflare (zona sajet.us)
    # No bloquea el alta del dominio si falla Cloudflare: se informa en response.
    domain_id = (result.get("domain") or {}).get("id")
    cloudflare_result = None
    if domain_id:
        try:
            cloudflare_result = await manager.configure_cloudflare(domain_id)
        except Exception as cf_err:
            cloudflare_result = {"success": False, "error": str(cf_err)}

    if cloudflare_result:
        result["cloudflare"] = cloudflare_result
    
    return result


@router.get("", response_model=DomainListResponse)
async def list_domains(
    customer_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    status: Optional[str] = Query(None, description="Filtrar por estado de verificación"),
    is_active: Optional[bool] = Query(None, description="Filtrar por activo/inactivo"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Lista todos los dominios con filtros opcionales (solo admin)"""
    manager = DomainManager(db)
    return manager.list_domains(
        customer_id=customer_id,
        status=status,
        is_active=is_active,
        limit=limit,
        offset=offset
    )


@router.get("/my-domains", response_model=DomainListResponse)
async def list_my_domains(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_tenant)
):
    """Lista los dominios del cliente autenticado (portal de cliente)"""
    tenant_id = current_user.get("tenant_id") or current_user.get("user_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No se encontró ID de tenant")
    
    manager = DomainManager(db)
    return manager.list_domains(
        customer_id=tenant_id,
        limit=100,
        offset=0
    )


@router.get("/{domain_id}", response_model=dict)
async def get_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Obtiene detalles de un dominio específico"""
    manager = DomainManager(db)
    domain = manager.get_domain(domain_id=domain_id)
    
    if not domain:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")
    
    return {"success": True, "domain": manager._domain_to_dict(domain)}


@router.put("/{domain_id}", response_model=dict)
async def update_domain(
    domain_id: int,
    data: DomainUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Actualiza configuración de un dominio"""
    manager = DomainManager(db)
    update_data = data.dict(exclude_unset=True)
    result = manager.update_domain(domain_id, **update_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.delete("/{domain_id}", response_model=dict)
async def delete_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Elimina un dominio personalizado.
    También elimina la configuración de Cloudflare asociada.
    """
    manager = DomainManager(db)
    result = manager.delete_domain(domain_id=domain_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{domain_id}/configure-cloudflare", response_model=dict)
async def configure_cloudflare(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Configura el DNS CNAME en Cloudflare.
    Crea: {subdomain}.sajet.us → {tunnel}.cfargotunnel.com
    """
    manager = DomainManager(db)
    result = await manager.configure_cloudflare(domain_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Error configurando Cloudflare"))
    
    return result


@router.post("/{domain_id}/verify", response_model=dict)
async def verify_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Verifica que el dominio externo tenga el CNAME configurado correctamente.
    Busca que apunte a {subdomain}.sajet.us
    """
    manager = DomainManager(db)
    result = await manager.verify_domain(domain_id)
    
    return result


@router.post("/{domain_id}/activate", response_model=dict)
async def activate_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Activa manualmente un dominio (bypass verificación)"""
    manager = DomainManager(db)
    result = manager.activate_domain(domain_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{domain_id}/deactivate", response_model=dict)
async def deactivate_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """Desactiva un dominio"""
    manager = DomainManager(db)
    result = manager.deactivate_domain(domain_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/{domain_id}/configure-nginx", response_model=dict)
async def configure_nginx(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Configura (o reconfigura) nginx en PCT160 y CT105 para un dominio.
    Útil para re-aplicar configuración si hubo un fallo previo.
    El dominio debe estar activo.
    """
    manager = DomainManager(db)
    result = manager.configure_nginx_manual(domain_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Error configurando nginx"))

    return result


@router.get("/{domain_id}/nginx-status", response_model=dict)
async def nginx_status(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Verifica si un dominio está configurado en nginx de ambos servidores.
    """
    from ..services.nginx_domain_configurator import NginxDomainConfigurator

    manager = DomainManager(db)
    domain = manager.get_domain(domain_id=domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")

    configurator = NginxDomainConfigurator()
    status = configurator.check_domain_configured(domain.external_domain)

    return {
        "domain": domain.external_domain,
        "nginx_configured_db": domain.nginx_configured,
        "pct160_configured": status["pct160"],
        "ct105_configured": status["ct105"],
        "in_sync": domain.nginx_configured == (status["pct160"] and status["ct105"]),
    }


# ==================== Odoo Website Configuration ====================

@router.post("/{domain_id}/configure-odoo-website", response_model=dict)
async def configure_odoo_website(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Configura el website de Odoo en la BD del tenant para multi-website.
    Crea o actualiza un registro website con el dominio externo.
    El dominio debe estar activo.
    """
    manager = DomainManager(db)
    result = manager.configure_odoo_website_manual(domain_id)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Error configurando Odoo website")
        )

    return result


@router.get("/{domain_id}/odoo-websites", response_model=dict)
async def list_odoo_websites(
    domain_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Lista los websites de Odoo del tenant asociado al dominio.
    """
    from ..services.odoo_website_configurator import OdooWebsiteConfigurator

    manager = DomainManager(db)
    domain = manager.get_domain(domain_id=domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Dominio no encontrado")

    info = manager._resolve_tenant_info(domain)
    configurator = OdooWebsiteConfigurator()
    result = configurator.list_websites(info["tenant_db"])

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return {
        "domain": domain.external_domain,
        "tenant_db": info["tenant_db"],
        "websites": result["websites"],
    }


# ==================== Épica 8: Early Domain Verification ====================

class EarlyDomainRequest(BaseModel):
    external_domain: str = Field(..., description="Dominio que el cliente quiere usar")
    customer_id: int
    tenant_deployment_id: Optional[int] = None


@router.post("/early-verify", response_model=dict)
async def early_domain_verification(
    data: EarlyDomainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Épica 8 — Inicia verificación de dominio en TENANT_REQUESTED.
    NO bloquea el flujo de onboarding.
    
    1. Registra el dominio custom inmediatamente
    2. Lanza verificación DNS en background
    3. Retorna instrucciones CNAME al frontend para que el cliente
       pueda ir configurando mientras el tenant se provisiona
    """
    import os

    # Crear dominio sin requerir suscripción activa (early)
    manager = DomainManager(db)
    result = manager.create_domain(
        external_domain=data.external_domain,
        customer_id=data.customer_id,
        tenant_deployment_id=data.tenant_deployment_id,
        created_by="early_verification"
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error creating domain"))

    domain_id = result.get("domain", {}).get("id")

    # Lanzar verificación en background (no bloqueante)
    if domain_id:
        from ..config import DATABASE_URL as _cfg_db_url
        background_tasks.add_task(_background_domain_verify, domain_id, _cfg_db_url)

    return {
        "success": True,
        "message": "Dominio registrado. Verificación DNS iniciada en background.",
        "domain": result.get("domain"),
        "instructions": {
            "step_1": f"Crear CNAME: {data.external_domain} → {result.get('domain', {}).get('sajet_full_domain', 'N/A')}",
            "step_2": "La verificación se completará automáticamente cuando el DNS propague",
            "note": "El flujo de onboarding NO se bloquea por la verificación del dominio",
        },
        "non_blocking": True,
    }


# ==================== Bulk Operations ====================

@router.post("/bulk/sync-cloudflare", response_model=dict)
async def bulk_sync_cloudflare(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Sincroniza todos los dominios pendientes con Cloudflare.
    Crea los registros CNAME faltantes.
    """
    from ..models.database import CustomDomain
    
    manager = DomainManager(db)
    domains = db.query(CustomDomain).filter(
        CustomDomain.cloudflare_configured == False
    ).all()
    
    results = {
        "total": len(domains),
        "configured": 0,
        "failed": 0,
        "errors": []
    }
    
    for domain in domains:
        result = await manager.configure_cloudflare(domain.id)
        if result["success"]:
            results["configured"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "domain": domain.external_domain,
                "error": result.get("error", "Unknown error")
            })
    
    return results


@router.post("/bulk/sync-nginx", response_model=dict)
async def bulk_sync_nginx(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Sincroniza configuración nginx para todos los dominios activos
    que aún no tienen nginx_configured = true.
    """
    from ..models.database import CustomDomain

    manager = DomainManager(db)
    domains = db.query(CustomDomain).filter(
        CustomDomain.is_active == True,
        CustomDomain.nginx_configured == False
    ).all()

    results = {
        "total": len(domains),
        "configured": 0,
        "failed": 0,
        "errors": []
    }

    for domain in domains:
        result = manager._configure_nginx_for_domain(domain)
        if result.get("success"):
            results["configured"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "domain": domain.external_domain,
                "error": result.get("error", "Unknown error")
            })

    return results


@router.get("/export/tunnel-config", response_model=dict)
async def export_tunnel_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Exporta configuración de ingress rules para cloudflared tunnel.
    Formato YAML compatible con config.yml del tunnel.
    """
    from ..models.database import CustomDomain
    
    domains = db.query(CustomDomain).filter(
        CustomDomain.is_active == True,
        CustomDomain.cloudflare_configured == True
    ).all()
    
    ingress_rules = []
    
    for domain in domains:
        # Regla para el subdominio de sajet.us
        ingress_rules.append({
            "hostname": domain.sajet_full_domain,
            "service": f"http://{domain.target_node_ip}:{domain.target_port}"
        })
        
        # También agregar el dominio externo si está verificado
        if domain.verification_status == "verified":
            ingress_rules.append({
                "hostname": domain.external_domain,
                "service": f"http://{domain.target_node_ip}:{domain.target_port}"
            })
    
    # Agregar catch-all al final
    ingress_rules.append({
        "service": "http_status:404"
    })
    
    return {
        "success": True,
        "total_domains": len(domains),
        "ingress": ingress_rules,
        "yaml_example": _generate_yaml_config(ingress_rules)
    }


def _generate_yaml_config(rules: list) -> str:
    """Genera configuración YAML para cloudflared"""
    lines = ["ingress:"]
    
    for rule in rules:
        if "hostname" in rule:
            lines.append(f"  - hostname: {rule['hostname']}")
            lines.append(f"    service: {rule['service']}")
        else:
            # Catch-all rule
            lines.append(f"  - service: {rule['service']}")
    
    return "\n".join(lines)
