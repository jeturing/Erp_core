#!/usr/bin/env python3
"""
Odoo Local Provisioning API
API REST local para provisionar tenants en cada nodo Odoo
Escucha en puerto 8070 (accesible internamente desde otros nodos)

Este servicio debe ejecutarse con permisos de root para acceder a PostgreSQL
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, List
import subprocess
import json
import os
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo Node Provisioning API",
    description="API interna para provisionar tenants Odoo en este nodo",
    version="1.0.0"
)

# Configuración desde variables de entorno o valores por defecto
DOMAIN = os.getenv("ODOO_DOMAIN", "sajet.us")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CF_ZONES = {}
CF_TUNNEL_ID = os.getenv("CF_TUNNEL_ID", "")
API_KEY = os.getenv("PROVISIONING_API_KEY", "prov-key-2026-secure")
PG_USER = None

# Cargar configuración de dominios desde archivo si existe
DOMAINS_CONFIG_FILE = "/opt/odoo/config/domains.json"
if os.path.exists(DOMAINS_CONFIG_FILE):
    try:
        with open(DOMAINS_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            CF_ZONES = config.get("zones", {})
            CF_TUNNEL_ID = config.get("tunnel_id", CF_TUNNEL_ID)
    except Exception as e:
        logger.warning(f"No se pudo cargar {DOMAINS_CONFIG_FILE}: {e}")


class TenantCreateRequest(BaseModel):
    subdomain: str = Field(..., min_length=3, max_length=30)
    admin_password: str = Field(default="admin")
    domain: str = Field(default=DOMAIN)
    template_db: str = Field(default="tcs")


class TenantDeleteRequest(BaseModel):
    subdomain: str
    delete_dns: bool = True


def get_pg_user():
    """Detecta automáticamente el usuario PostgreSQL"""
    global PG_USER
    if PG_USER:
        return PG_USER
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-t', '-c',
             "SELECT usename FROM pg_user WHERE usename NOT IN ('postgres') LIMIT 1;"],
            capture_output=True, text=True, timeout=5
        )
        PG_USER = result.stdout.strip() or 'odoo'
        logger.info(f"PostgreSQL user detectado: {PG_USER}")
    except Exception as e:
        logger.error(f"Error detectando usuario PostgreSQL: {e}")
        PG_USER = 'odoo'
    return PG_USER


def run_sql(db, sql):
    """Ejecuta SQL en una base de datos específica"""
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-d', db, '-c', sql],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            logger.error(f"Error ejecutando SQL en {db}: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error ejecutando SQL: {e}")
        return False


def create_cloudflare_dns(subdomain, domain):
    """Crea registro CNAME en Cloudflare"""
    if not CF_API_TOKEN or not CF_ZONES:
        logger.warning("Cloudflare no configurado, saltando DNS")
        return False
    
    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        logger.error(f"Zone ID no encontrado para {domain}")
        return False
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    
    try:
        # Verificar si ya existe
        resp = requests.get(
            url, headers=headers,
            params={"type": "CNAME", "name": f"{subdomain}.{domain}"},
            timeout=10
        )
        if resp.status_code == 200 and resp.json().get("result"):
            logger.info(f"DNS ya existe: {subdomain}.{domain}")
            return True
        
        # Crear nuevo registro
        data = {
            "type": "CNAME",
            "name": subdomain,
            "content": f"{CF_TUNNEL_ID}.cfargotunnel.com",
            "ttl": 1,
            "proxied": True,
            "comment": f"Auto-provisioned {subdomain}"
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        if resp.json().get("success"):
            logger.info(f"DNS creado: {subdomain}.{domain}")
            return True
        else:
            logger.error(f"Error Cloudflare: {resp.json().get('errors')}")
            return False
    except Exception as e:
        logger.error(f"Error accediendo Cloudflare: {e}")
        return False


def delete_cloudflare_dns(subdomain, domain):
    """Elimina registro DNS en Cloudflare"""
    if not CF_API_TOKEN or not CF_ZONES:
        return False
    
    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        return False
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    
    try:
        resp = requests.get(
            url, headers=headers,
            params={"type": "CNAME", "name": f"{subdomain}.{domain}"},
            timeout=10
        )
        if resp.status_code != 200:
            return False
        
        result = resp.json().get("result", [])
        if not result:
            return True
        
        record_id = result[0]["id"]
        resp = requests.delete(f"{url}/{record_id}", headers=headers, timeout=10)
        return resp.json().get("success", False)
    except Exception as e:
        logger.error(f"Error eliminando DNS: {e}")
        return False


@app.get("/health")
async def health():
    """Healthcheck endpoint"""
    return {"status": "ok", "service": "odoo-provisioning"}


@app.get("/api/tenants")
async def list_tenants(x_api_key: str = Header(None)):
    """Lista todos los tenants en este nodo"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-t', '-c',
             "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');"],
            capture_output=True, text=True, timeout=10
        )
        
        dbs = [db.strip() for db in result.stdout.split('\n') if db.strip()]
        tenants = [{"database": db, "url": f"https://{db}.{DOMAIN}"} for db in dbs]
        
        logger.info(f"Listando {len(tenants)} tenants")
        return {"tenants": tenants, "total": len(tenants)}
    except Exception as e:
        logger.error(f"Error listando tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tenant")
async def create_tenant(request: TenantCreateRequest, x_api_key: str = Header(None)):
    """Crea un nuevo tenant"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    subdomain = request.subdomain.lower().replace("-", "_")
    domain = request.domain
    pg_user = get_pg_user()
    
    logger.info(f"Creando tenant: {subdomain}")
    
    # Verificar si ya existe
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-lqt'],
        capture_output=True, text=True
    )
    if subdomain in result.stdout:
        raise HTTPException(status_code=409, detail=f"Database {subdomain} already exists")
    
    # Terminar conexiones a BD plantilla
    run_sql('postgres', 
        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{request.template_db}' AND pid <> pg_backend_pid();")
    
    # Crear BD
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'createdb', '-O', pg_user, '-T', request.template_db, subdomain],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        logger.error(f"Error creando BD {subdomain}: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Error creating database: {result.stderr}")
    
    # Configurar BD
    config_sql = f"""
    UPDATE res_users SET password = '{request.admin_password}' WHERE login = 'admin';
    UPDATE res_company SET name = '{subdomain}' WHERE id = 1;
    UPDATE res_partner SET name = '{subdomain}' WHERE id = 1;
    UPDATE ir_config_parameter SET value = gen_random_uuid()::text WHERE key = 'database.uuid';
    INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
    VALUES ('web.base.url', 'https://{subdomain}.{domain}', NOW(), NOW(), 1, 1)
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
    """
    run_sql(subdomain, config_sql)
    
    # Crear DNS
    dns_created = create_cloudflare_dns(subdomain, domain)
    
    logger.info(f"Tenant {subdomain} creado exitosamente")
    return {
        "success": True,
        "subdomain": subdomain,
        "url": f"https://{subdomain}.{domain}",
        "database": subdomain,
        "dns_created": dns_created
    }


@app.delete("/api/tenant")
async def delete_tenant(request: TenantDeleteRequest, x_api_key: str = Header(None)):
    """Elimina un tenant"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    subdomain = request.subdomain.lower()
    
    logger.info(f"Eliminando tenant: {subdomain}")
    
    # Terminar conexiones
    run_sql('postgres', 
        f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{subdomain}';")
    
    # Eliminar BD
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'dropdb', subdomain],
        capture_output=True, text=True
    )
    
    # Eliminar DNS
    dns_deleted = delete_cloudflare_dns(subdomain, "sajet.us") if request.delete_dns else False
    
    logger.info(f"Tenant {subdomain} eliminado")
    return {
        "success": True,
        "database_deleted": result.returncode == 0,
        "dns_deleted": dns_deleted
    }


@app.get("/api/domains")
async def list_domains():
    """Lista dominios configurados"""
    return {"domains": list(CF_ZONES.keys())}


if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando Odoo Local Provisioning API en puerto 8070")
    uvicorn.run(app, host="0.0.0.0", port=8070)
