"""
Domains API Routes
Endpoints para gestión de dominios personalizados de clientes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Cookie
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..services.domain_manager import DomainManager
from .roles import verify_token_with_role

router = APIRouter(prefix="/api/domains", tags=["domains"])


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

@router.post("", response_model=dict)
async def create_domain(
    data: DomainCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_admin)
):
    """
    Registra un nuevo dominio personalizado.
    
    El sistema:
    1. Genera un subdominio de sajet.us automáticamente
    2. Devuelve instrucciones para configurar el CNAME en el DNS del cliente
    """
    manager = DomainManager(db)
    result = manager.create_domain(
        external_domain=data.external_domain,
        customer_id=data.customer_id,
        tenant_deployment_id=data.tenant_deployment_id,
        created_by=current_user.get("email", "system")
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
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
