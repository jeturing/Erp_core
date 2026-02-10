"""
Provisioning Routes - Auto-provisioning de tenants Odoo
Conecta con API local en cada servidor Odoo para provisioning
"""
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List
import httpx
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/provisioning", tags=["Provisioning"])

# Configuración de servidores Odoo - cada uno con su API local en puerto 8070
ODOO_SERVERS = {
    "primary": {
        "name": "SRV-Odoo-server",
        "ip": "10.10.10.100",
        "api_port": 8070,  # Puerto de la API local
        "domain": "sajet.us",
        "tunnel_id": "da2bc763-a93b-41f5-9a22-1731403127e3"
    }
}

# Configuración Cloudflare
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "_PQbnJMV_8WjjyloFsswy20u1L8DQtgX-oruh0Qu")
CF_ZONES = {
    "sajet.us": "4a83b88793ac3688486ace69b6ae80f9",
    "jeturing.com": "0004e8b57924141f4758f3b3ba02dd9e",
    "gmfcllc.com": "67515031fb2b16a5daf3cb09da010c02",
    "lslogistic.net": "d5d4702bbcd7e6751bb1d4e090ae9433",
    "aysautorepair.com": "5d152d21ef579da1025bafab212a9d6c",
    "esecure.do": "ce7d0136b71576ffd9dbb00cbde568f6"
}

# API Key interna para autenticación
PROVISIONING_API_KEY = os.getenv("PROVISIONING_API_KEY", "prov-key-2026-secure")


# DTOs
class TenantProvisionRequest(BaseModel):
    """Request para crear un nuevo tenant"""
    subdomain: str = Field(..., min_length=3, max_length=30, pattern="^[a-z0-9_]+$")
    admin_password: str = Field(default="admin", min_length=4)
    domain: str = Field(default="sajet.us")
    server: str = Field(default="primary")
    template_db: str = Field(default="tcs")
    language: str = Field(default="es_DO")
    install_modules: Optional[List[str]] = None
    with_demo: bool = False


class TenantProvisionResponse(BaseModel):
    """Response de provisioning"""
    success: bool
    subdomain: str
    url: str
    message: str
    database: str
    dns_created: bool
    server: str


class CloudflareDNSRequest(BaseModel):
    """Request para crear DNS en Cloudflare"""
    subdomain: str
    domain: str = "sajet.us"
    tunnel_id: Optional[str] = None


class TenantDeleteRequest(BaseModel):
    """Request para eliminar tenant"""
    subdomain: str
    domain: str = "sajet.us"
    delete_dns: bool = True


# Funciones auxiliares
async def create_cloudflare_dns(subdomain: str, domain: str, tunnel_id: str) -> bool:
    """Crea registro CNAME en Cloudflare"""
    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        logger.error(f"Zone ID no encontrado para {domain}")
        return False
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Verificar si ya existe
    async with httpx.AsyncClient() as client:
        check_resp = await client.get(
            url,
            headers=headers,
            params={"type": "CNAME", "name": f"{subdomain}.{domain}"}
        )
        if check_resp.status_code == 200:
            result = check_resp.json()
            if result.get("result"):
                logger.info(f"DNS ya existe: {subdomain}.{domain}")
                return True
        
        # Crear nuevo registro
        data = {
            "type": "CNAME",
            "name": subdomain,
            "content": f"{tunnel_id}.cfargotunnel.com",
            "ttl": 1,
            "proxied": True,
            "comment": f"Auto-provisioned tenant {subdomain}"
        }
        
        resp = await client.post(url, headers=headers, json=data)
        result = resp.json()
        
        if result.get("success"):
            logger.info(f"DNS creado: {subdomain}.{domain}")
            return True
        else:
            errors = result.get("errors", [])
            logger.error(f"Error creando DNS: {errors}")
            return False


async def delete_cloudflare_dns(subdomain: str, domain: str) -> bool:
    """Elimina registro DNS en Cloudflare"""
    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        return False
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Buscar el registro
        resp = await client.get(
            url,
            headers=headers,
            params={"type": "CNAME", "name": f"{subdomain}.{domain}"}
        )
        result = resp.json()
        
        if not result.get("result"):
            return True  # No existe
        
        record_id = result["result"][0]["id"]
        
        # Eliminar
        del_resp = await client.delete(f"{url}/{record_id}", headers=headers)
        return del_resp.json().get("success", False)


async def call_odoo_local_api(server_config: dict, method: str, endpoint: str, data: dict = None) -> dict:
    """Llama a la API local del servidor Odoo"""
    ip = server_config["ip"]
    port = server_config.get("api_port", 8070)
    url = f"http://{ip}:{port}{endpoint}"
    
    headers = {"X-API-KEY": PROVISIONING_API_KEY}
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                resp = await client.post(url, headers=headers, json=data)
            elif method == "DELETE":
                resp = await client.request("DELETE", url, headers=headers, json=data)
            else:
                raise ValueError(f"Método no soportado: {method}")
            
            if resp.status_code >= 400:
                error_detail = resp.json().get("detail", resp.text)
                raise HTTPException(status_code=resp.status_code, detail=error_detail)
            
            return resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout conectando con servidor Odoo")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"No se puede conectar con servidor Odoo en {ip}:{port}")


# Endpoints
@router.post("/tenant", response_model=TenantProvisionResponse)
async def provision_tenant(
    request: TenantProvisionRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None)
):
    """
    Provisiona un nuevo tenant de Odoo automáticamente.
    
    Este endpoint llama a la API local del servidor Odoo para:
    1. Crear la base de datos
    2. Configurar web.base.url
    3. Crear el registro DNS en Cloudflare
    """
    # Validar API key
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    # Validar servidor
    server_config = ODOO_SERVERS.get(request.server)
    if not server_config:
        raise HTTPException(status_code=400, detail=f"Servidor '{request.server}' no encontrado")
    
    # Validar dominio
    if request.domain not in CF_ZONES:
        raise HTTPException(status_code=400, detail=f"Dominio '{request.domain}' no soportado")
    
    subdomain = request.subdomain.lower().replace("-", "_")
    
    # Llamar a la API local del servidor Odoo
    result = await call_odoo_local_api(
        server_config,
        "POST",
        "/api/tenant",
        {
            "subdomain": subdomain,
            "admin_password": request.admin_password,
            "domain": request.domain,
            "template_db": request.template_db
        }
    )
    
    return TenantProvisionResponse(
        success=result.get("success", True),
        subdomain=result.get("subdomain", subdomain),
        url=result.get("url", f"https://{subdomain}.{request.domain}"),
        message=f"Tenant {subdomain} creado exitosamente",
        database=result.get("database", subdomain),
        dns_created=result.get("dns_created", False),
        server=request.server
    )


@router.delete("/tenant")
async def delete_tenant(
    request: TenantDeleteRequest,
    x_api_key: str = Header(None)
):
    """Elimina un tenant (BD + DNS) via API local"""
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    server_config = ODOO_SERVERS["primary"]
    
    result = await call_odoo_local_api(
        server_config,
        "DELETE",
        "/api/tenant",
        {
            "subdomain": request.subdomain,
            "delete_dns": request.delete_dns
        }
    )
    
    return {
        "success": True,
        "message": f"Tenant {request.subdomain} eliminado",
        "database_deleted": result.get("database_deleted", False),
        "dns_deleted": result.get("dns_deleted", False)
    }


@router.get("/tenants")
async def list_provisioned_tenants(x_api_key: str = Header(None)):
    """Lista todos los tenants provisionados via API local"""
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    server_config = ODOO_SERVERS["primary"]
    
    result = await call_odoo_local_api(server_config, "GET", "/api/tenants")
    
    # Enriquecer datos con info del servidor
    tenants = []
    for tenant in result.get("tenants", []):
        tenants.append({
            **tenant,
            "subdomain": tenant.get("database"),
            "server": "primary"
        })
    
    return {
        "tenants": tenants,
        "total": result.get("total", len(tenants)),
        "server": server_config["name"]
    }


@router.post("/dns")
async def create_dns_record(
    request: CloudflareDNSRequest,
    x_api_key: str = Header(None)
):
    """Crea un registro DNS en Cloudflare"""
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    tunnel_id = request.tunnel_id or ODOO_SERVERS["primary"]["tunnel_id"]
    
    success = await create_cloudflare_dns(
        request.subdomain,
        request.domain,
        tunnel_id
    )
    
    if success:
        return {
            "success": True,
            "message": f"DNS creado: {request.subdomain}.{request.domain}",
            "url": f"https://{request.subdomain}.{request.domain}"
        }
    else:
        raise HTTPException(status_code=500, detail="Error creando registro DNS")


@router.get("/servers")
async def list_odoo_servers(x_api_key: str = Header(None)):
    """Lista servidores Odoo disponibles"""
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    servers = []
    for key, config in ODOO_SERVERS.items():
        servers.append({
            "id": key,
            "name": config["name"],
            "ip": config["ip"],
            "domain": config["domain"]
        })
    
    return {"servers": servers}


@router.get("/domains")
async def list_available_domains():
    """Lista dominios disponibles para provisioning (público)"""
    return {
        "domains": list(CF_ZONES.keys()),
        "default": "sajet.us"
    }
