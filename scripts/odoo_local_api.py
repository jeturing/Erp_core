#!/usr/bin/env python3
"""
Odoo Local Provisioning API
API REST local para provisionar tenants en este servidor Odoo
Escucha en puerto 8070 (interno)
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, List
import subprocess
import json
import os
import logging
import requests
import xmlrpc.client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo Local Provisioning API",
    description="API interna para provisionar tenants Odoo",
    version="1.0.0"
)

# Configuración
DOMAIN = "sajet.us"
CF_API_TOKEN = "_PQbnJMV_8WjjyloFsswy20u1L8DQtgX-oruh0Qu"
CF_ZONES = {
    "sajet.us": "4a83b88793ac3688486ace69b6ae80f9",
    "jeturing.com": "0004e8b57924141f4758f3b3ba02dd9e",
    "gmfcllc.com": "67515031fb2b16a5daf3cb09da010c02",
    "lslogistic.net": "d5d4702bbcd7e6751bb1d4e090ae9433",
    "aysautorepair.com": "5d152d21ef579da1025bafab212a9d6c",
    "esecure.do": "ce7d0136b71576ffd9dbb00cbde568f6"
}
CF_TUNNEL_ID = "da2bc763-a93b-41f5-9a22-1731403127e3"
API_KEY = os.getenv("PROVISIONING_API_KEY", "prov-key-2026-secure")
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
PG_USER = None
DEFAULT_MODULES = [
    "spiffy_theme_backend",
    "hide_powered_by_odoo",
]


class TenantCreateRequest(BaseModel):
    subdomain: str = Field(..., min_length=3, max_length=30)
    admin_password: str = Field(default="admin")
    domain: str = Field(default="sajet.us")
    template_db: str = Field(default="tcs")
    install_default_modules: bool = Field(default=True)
    modules: Optional[List[str]] = Field(default=None)


class TenantDeleteRequest(BaseModel):
    subdomain: str
    delete_dns: bool = True


def get_pg_user():
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
    except:
        PG_USER = 'odoo'
    return PG_USER


def run_sql(db, sql):
    try:
        subprocess.run(['sudo', '-u', 'postgres', 'psql', '-d', db, '-c', sql],
            capture_output=True, text=True, timeout=30)
        return True
    except:
        return False


def create_cloudflare_dns(subdomain, domain):
    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        return False
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    
    resp = requests.get(url, headers=headers, params={"type": "CNAME", "name": f"{subdomain}.{domain}"})
    if resp.status_code == 200 and resp.json().get("result"):
        return True
    
    data = {"type": "CNAME", "name": subdomain, "content": f"{CF_TUNNEL_ID}.cfargotunnel.com", "ttl": 1, "proxied": True}
    resp = requests.post(url, headers=headers, json=data)
    return resp.json().get("success", False)


def delete_cloudflare_dns(subdomain, domain):
    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        return False
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    
    resp = requests.get(url, headers=headers, params={"type": "CNAME", "name": f"{subdomain}.{domain}"})
    if resp.status_code != 200:
        return False
    
    result = resp.json().get("result", [])
    if not result:
        return True
    
    record_id = result[0]["id"]
    resp = requests.delete(f"{url}/{record_id}", headers=headers)
    return resp.json().get("success", False)


def install_modules_odoo(db_name: str, admin_password: str, modules: List[str]):
    """Instala módulos por XML-RPC y devuelve instalados/faltantes/errores."""
    installed = []
    missing = []
    errors = []

    if not modules:
        return installed, missing, errors

    try:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(db_name, "admin", admin_password, {})
        if not uid:
            errors.append("No se pudo autenticar con XML-RPC para instalar módulos")
            return installed, missing, errors

        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

        for module in modules:
            module = (module or "").strip()
            if not module:
                continue

            mod_ids = models.execute_kw(
                db_name,
                uid,
                admin_password,
                'ir.module.module',
                'search',
                [[["name", "=", module]]],
            )

            if not mod_ids:
                missing.append(module)
                continue

            mod_data = models.execute_kw(
                db_name,
                uid,
                admin_password,
                'ir.module.module',
                'read',
                [mod_ids, ["name", "state"]],
            )

            state = mod_data[0].get("state") if mod_data else None
            if state == "installed":
                installed.append(module)
                continue

            if state in ("uninstalled", "to install", "to upgrade"):
                try:
                    models.execute_kw(
                        db_name,
                        uid,
                        admin_password,
                        'ir.module.module',
                        'button_immediate_install',
                        [mod_ids],
                    )
                    installed.append(module)
                except Exception as install_error:
                    errors.append(f"{module}: {install_error}")
            else:
                errors.append(f"{module}: estado no instalable ({state})")

    except Exception as e:
        errors.append(f"Error general instalando módulos: {e}")

    return installed, missing, errors


@app.get("/health")
async def health():
    return {"status": "ok", "service": "odoo-provisioning"}


@app.get("/api/tenants")
async def list_tenants(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-t', '-c',
         "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');"],
        capture_output=True, text=True, timeout=10
    )
    
    dbs = [db.strip() for db in result.stdout.split('\n') if db.strip()]
    tenants = [{"database": db, "url": f"https://{db}.{DOMAIN}"} for db in dbs]
    
    return {"tenants": tenants, "total": len(tenants)}


@app.post("/api/tenant")
async def create_tenant(request: TenantCreateRequest, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    subdomain = request.subdomain.lower().replace("-", "_")
    domain = request.domain
    pg_user = get_pg_user()
    
    result = subprocess.run(['sudo', '-u', 'postgres', 'psql', '-lqt'], capture_output=True, text=True)
    if subdomain in result.stdout:
        raise HTTPException(status_code=409, detail=f"Database {subdomain} already exists")
    
    run_sql('postgres', f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{request.template_db}' AND pid <> pg_backend_pid();")
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'createdb', '-O', pg_user, '-T', request.template_db, subdomain],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Error creating database: {result.stderr}")
    
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
    
    dns_created = create_cloudflare_dns(subdomain, domain)

    modules_to_install: List[str] = []
    if request.install_default_modules:
        modules_to_install.extend(DEFAULT_MODULES)
    if request.modules:
        modules_to_install.extend(request.modules)
    # dedupe manteniendo orden
    modules_to_install = list(dict.fromkeys([m.strip() for m in modules_to_install if m and m.strip()]))

    installed_modules, missing_modules, module_errors = install_modules_odoo(
        subdomain,
        request.admin_password,
        modules_to_install,
    )
    
    return {
        "success": True,
        "subdomain": subdomain,
        "url": f"https://{subdomain}.{domain}",
        "database": subdomain,
        "dns_created": dns_created,
        "requested_modules": modules_to_install,
        "installed_modules": installed_modules,
        "missing_modules": missing_modules,
        "module_errors": module_errors,
    }


@app.delete("/api/tenant")
async def delete_tenant(request: TenantDeleteRequest, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    subdomain = request.subdomain.lower()
    run_sql('postgres', f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{subdomain}';")
    result = subprocess.run(['sudo', '-u', 'postgres', 'dropdb', subdomain], capture_output=True, text=True)
    
    dns_deleted = delete_cloudflare_dns(subdomain, "sajet.us") if request.delete_dns else False
    
    return {"success": True, "database_deleted": result.returncode == 0, "dns_deleted": dns_deleted}


@app.get("/api/domains")
async def list_domains():
    return {"domains": list(CF_ZONES.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8070)
