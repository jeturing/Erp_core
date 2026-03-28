#!/usr/bin/env python3
"""
Odoo Node Provisioning API v2
API REST local para provisionar tenants en cada nodo Odoo.
Escucha en puerto 8070 (accesible internamente desde PCT160).

Cambios vs v1:
  - Usa psycopg2 contra PG remoto (PCT137) — no depende de sudo psql local
  - Todas las queries parametrizadas (sin SQL injection)
  - Compatible API: mismos endpoints y payloads
  - createdb/dropdb via SQL (CREATE DATABASE … TEMPLATE …)

Variables de entorno requeridas:
  PG_HOST        = 10.10.10.137 (default)
  PG_PORT        = 5432
  PG_USER        = odoo
  PG_PASSWORD    = <password>
  PG_ADMIN_DB    = postgres
  ODOO_DOMAIN    = sajet.us
  PROVISIONING_API_KEY = prov-key-2026-secure
  CLOUDFLARE_API_TOKEN = (opcional)
  CF_TUNNEL_ID   = (opcional)
"""

from __future__ import annotations

import json
import logging
import os
import re
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extensions
import psycopg2.sql as sql
import requests
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo Node Provisioning API",
    description="API interna para provisionar tenants Odoo en este nodo (v2 — PG remoto, parametrizado)",
    version="2.0.0",
)

# ── Configuración ─────────────────────────────────────────────────────────────

PG_HOST = os.getenv("PG_HOST", "10.10.10.137")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_USER = os.getenv("PG_USER", "odoo")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")
PG_ADMIN_DB = os.getenv("PG_ADMIN_DB", "postgres")
DOMAIN = os.getenv("ODOO_DOMAIN", "sajet.us")
API_KEY = os.getenv("PROVISIONING_API_KEY", "prov-key-2026-secure")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CF_TUNNEL_ID = os.getenv("CF_TUNNEL_ID", "")
CF_ZONES: Dict[str, str] = {}

DOMAINS_CONFIG_FILE = "/opt/odoo/config/domains.json"
if os.path.exists(DOMAINS_CONFIG_FILE):
    try:
        with open(DOMAINS_CONFIG_FILE, "r") as f:
            _cfg = json.load(f)
            CF_ZONES = _cfg.get("zones", {})
            CF_TUNNEL_ID = _cfg.get("tunnel_id", CF_TUNNEL_ID)
    except Exception as e:
        logger.warning(f"No se pudo cargar {DOMAINS_CONFIG_FILE}: {e}")


# ── Database helpers ──────────────────────────────────────────────────────────

def _connect(dbname: str = PG_ADMIN_DB) -> psycopg2.extensions.connection:
    """Abre conexión a PostgreSQL remoto."""
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        dbname=dbname,
        connect_timeout=10,
    )


@contextmanager
def _db_conn(dbname: str = PG_ADMIN_DB, autocommit: bool = False):
    """Context manager para conexiones PG."""
    conn = _connect(dbname)
    if autocommit:
        conn.autocommit = True
    try:
        yield conn
    finally:
        conn.close()


def _db_exists(dbname: str) -> bool:
    """Verifica si una base de datos existe."""
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (dbname,),
            )
            return cur.fetchone() is not None


def _terminate_connections(dbname: str) -> None:
    """Termina todas las conexiones a una BD (excepto la nuestra)."""
    with _db_conn(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (dbname,),
            )


def _list_databases() -> List[str]:
    """Lista todas las bases de datos no-sistema."""
    system_dbs = {"postgres", "template0", "template1"}
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT datname FROM pg_database "
                "WHERE datistemplate = false "
                "ORDER BY datname"
            )
            return [
                row[0]
                for row in cur.fetchall()
                if row[0] not in system_dbs
            ]


# ── Cloudflare helpers ────────────────────────────────────────────────────────

def _create_cloudflare_dns(subdomain: str, domain: str) -> bool:
    """Crea registro CNAME en Cloudflare."""
    if not CF_API_TOKEN or not CF_ZONES:
        logger.warning("Cloudflare no configurado, saltando DNS")
        return False

    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        logger.error(f"Zone ID no encontrado para {domain}")
        return False

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(
            url,
            headers=headers,
            params={"type": "CNAME", "name": f"{subdomain}.{domain}"},
            timeout=10,
        )
        if resp.status_code == 200 and resp.json().get("result"):
            logger.info(f"DNS ya existe: {subdomain}.{domain}")
            return True

        data = {
            "type": "CNAME",
            "name": subdomain,
            "content": f"{CF_TUNNEL_ID}.cfargotunnel.com",
            "ttl": 1,
            "proxied": True,
            "comment": f"Auto-provisioned {subdomain}",
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


def _delete_cloudflare_dns(subdomain: str, domain: str) -> bool:
    """Elimina registro DNS en Cloudflare."""
    if not CF_API_TOKEN or not CF_ZONES:
        return False

    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        return False

    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.get(
            url,
            headers=headers,
            params={"type": "CNAME", "name": f"{subdomain}.{domain}"},
            timeout=10,
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


# ── Pydantic models ───────────────────────────────────────────────────────────

class TenantCreateRequest(BaseModel):
    subdomain: str = Field(..., min_length=3, max_length=30)
    admin_password: str = Field(default="admin")
    domain: str = Field(default=DOMAIN)
    template_db: str = Field(default="tcs")


class TenantDeleteRequest(BaseModel):
    subdomain: str
    delete_dns: bool = True


class TenantPasswordRequest(BaseModel):
    subdomain: str
    new_password: str = Field(..., min_length=6)


class TenantSuspendRequest(BaseModel):
    subdomain: str
    suspend: bool = True
    reason: Optional[str] = Field(None)


class TenantAccountCredentialsRequest(BaseModel):
    subdomain: str
    user_id: Optional[int] = None
    login: Optional[str] = None
    new_email: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6)
    active: Optional[bool] = None


# ── Validación de nombres de BD ───────────────────────────────────────────────

_VALID_DB_NAME = re.compile(r"^[a-z0-9_]{3,63}$")
SYSTEM_DBS = frozenset({
    "postgres", "template0", "template1",
    "erp_core_db", "erp_core",
})


def _validate_dbname(name: str) -> str:
    """Valida y normaliza un nombre de BD. Retorna nombre limpio o lanza."""
    clean = name.lower().strip().replace("-", "_")
    if not _VALID_DB_NAME.match(clean):
        raise HTTPException(
            status_code=400,
            detail="Nombre de BD inválido: solo letras, números y _ (3-63 chars)",
        )
    if clean in SYSTEM_DBS:
        raise HTTPException(
            status_code=400,
            detail=f"'{clean}' es una BD del sistema — no se puede operar",
        )
    return clean


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Healthcheck endpoint."""
    pg_ok = False
    try:
        conn = _connect()
        conn.close()
        pg_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if pg_ok else "degraded",
        "service": "odoo-provisioning",
        "pg_host": PG_HOST,
        "pg_reachable": pg_ok,
    }


@app.get("/api/tenants")
async def list_tenants(x_api_key: str = Header(None)):
    """Lista todos los tenants en este nodo."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        dbs = _list_databases()
        tenants = [
            {"database": db, "url": f"https://{db}.{DOMAIN}"}
            for db in dbs
        ]
        logger.info(f"Listando {len(tenants)} tenants")
        return {"tenants": tenants, "total": len(tenants)}
    except Exception as e:
        logger.error(f"Error listando tenants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tenant")
async def create_tenant(
    request: TenantCreateRequest,
    x_api_key: str = Header(None),
):
    """Crea un nuevo tenant."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    subdomain = _validate_dbname(request.subdomain)
    template = _validate_dbname(request.template_db)
    domain = request.domain

    logger.info(f"Creando tenant: {subdomain} desde template {template}")

    if _db_exists(subdomain):
        raise HTTPException(
            status_code=409,
            detail=f"Database {subdomain} already exists",
        )

    if not _db_exists(template):
        raise HTTPException(
            status_code=404,
            detail=f"Template database {template} not found",
        )

    # Terminar conexiones a BD plantilla
    _terminate_connections(template)

    # Crear BD desde template
    try:
        with _db_conn(autocommit=True) as conn:
            with conn.cursor() as cur:
                # CREATE DATABASE no soporta parámetros — usar sql.Identifier
                cur.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {} TEMPLATE {}").format(
                        sql.Identifier(subdomain),
                        sql.Identifier(PG_USER),
                        sql.Identifier(template),
                    )
                )
    except Exception as e:
        logger.error(f"Error creando BD {subdomain}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating database: {e}",
        )

    # Configurar BD del nuevo tenant (todo parametrizado)
    try:
        with _db_conn(subdomain) as conn:
            with conn.cursor() as cur:
                # Resetear password admin
                cur.execute(
                    "UPDATE res_users SET password = %s WHERE login = 'admin'",
                    (request.admin_password,),
                )
                # Resetear nombre empresa
                cur.execute(
                    "UPDATE res_company SET name = %s WHERE id = 1",
                    (subdomain,),
                )
                cur.execute(
                    "UPDATE res_partner SET name = %s WHERE id = 1",
                    (subdomain,),
                )
                # Regenerar UUID
                cur.execute(
                    "UPDATE ir_config_parameter "
                    "SET value = gen_random_uuid()::text "
                    "WHERE key = 'database.uuid'"
                )
                # Limpiar sesiones
                cur.execute("DELETE FROM ir_sessions")
                # Base URL
                base_url = f"https://{subdomain}.{domain}"
                cur.execute(
                    "INSERT INTO ir_config_parameter "
                    "(key, value, create_date, write_date, create_uid, write_uid) "
                    "VALUES ('web.base.url', %s, NOW(), NOW(), 1, 1) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    (base_url,),
                )
                cur.execute(
                    "UPDATE ir_config_parameter "
                    "SET value = 'False' WHERE key = 'web.base.url.freeze'"
                )
            conn.commit()
    except Exception as e:
        logger.error(f"Error configurando BD {subdomain}: {e}")
        # BD fue creada pero config falló — seguir, no es fatal

    # Crear DNS
    dns_created = _create_cloudflare_dns(subdomain, domain)

    logger.info(f"Tenant {subdomain} creado exitosamente")
    return {
        "success": True,
        "subdomain": subdomain,
        "url": f"https://{subdomain}.{domain}",
        "database": subdomain,
        "dns_created": dns_created,
    }


@app.delete("/api/tenant")
async def delete_tenant(
    request: TenantDeleteRequest,
    x_api_key: str = Header(None),
):
    """Elimina un tenant."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    subdomain = _validate_dbname(request.subdomain)
    logger.info(f"Eliminando tenant: {subdomain}")

    if not _db_exists(subdomain):
        raise HTTPException(status_code=404, detail=f"Database {subdomain} not found")

    _terminate_connections(subdomain)

    try:
        with _db_conn(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(
                        sql.Identifier(subdomain)
                    )
                )
        db_deleted = True
    except Exception as e:
        logger.error(f"Error eliminando BD {subdomain}: {e}")
        db_deleted = False

    dns_deleted = (
        _delete_cloudflare_dns(subdomain, "sajet.us")
        if request.delete_dns
        else False
    )

    logger.info(f"Tenant {subdomain} eliminado")
    return {
        "success": True,
        "database_deleted": db_deleted,
        "dns_deleted": dns_deleted,
    }


@app.get("/api/domains")
async def list_domains():
    """Lista dominios configurados."""
    return {"domains": list(CF_ZONES.keys())}


@app.get("/api/tenant/accounts")
async def list_tenant_accounts(
    subdomain: str,
    include_inactive: bool = True,
    x_api_key: str = Header(None),
):
    """Lista cuentas de un tenant y resume asientos facturables."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    db_name = _validate_dbname(subdomain)

    if not _db_exists(db_name):
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    try:
        with _db_conn(db_name) as conn:
            with conn.cursor() as cur:
                query = (
                    "SELECT u.id, u.login, u.email, p.name, "
                    "u.active, COALESCE(u.share, false), "
                    "u.write_date, u.create_date "
                    "FROM res_users u "
                    "LEFT JOIN res_partner p ON p.id = u.partner_id "
                )
                if not include_inactive:
                    query += "WHERE u.active = true "
                query += "ORDER BY u.active DESC, u.id ASC"

                cur.execute(query)
                rows = cur.fetchall()

        accounts = []
        active_accounts = 0
        billable_active_accounts = 0

        for row in rows:
            uid, login, email, name, active, share, write_date, create_date = row

            login_str = (login or "").strip().lower()
            is_admin = login_str in {"admin", "admin@sajet.us"}
            is_billable = bool(active) and not bool(share) and not is_admin

            account = {
                "id": uid,
                "login": login,
                "email": email,
                "name": name,
                "active": active,
                "share": share,
                "write_date": str(write_date) if write_date else None,
                "create_date": str(create_date) if create_date else None,
                "is_admin": is_admin,
                "is_billable": is_billable,
            }

            if active:
                active_accounts += 1
            if is_billable:
                billable_active_accounts += 1

            accounts.append(account)

        return {
            "success": True,
            "subdomain": db_name,
            "accounts": accounts,
            "total_accounts": len(accounts),
            "active_accounts": active_accounts,
            "billable_active_accounts": billable_active_accounts,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando cuentas de {db_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tenant/account/credentials")
async def update_tenant_account_credentials(
    request: TenantAccountCredentialsRequest,
    x_api_key: str = Header(None),
):
    """Actualiza credenciales o estado de una cuenta de tenant."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not request.user_id and not request.login:
        raise HTTPException(
            status_code=400,
            detail="user_id o login es requerido",
        )

    db_name = _validate_dbname(request.subdomain)

    if not _db_exists(db_name):
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    # Construir SET dinámico con parámetros
    set_parts: List[str] = []
    params: List[Any] = []

    if request.new_email is not None:
        set_parts.append("login = %s")
        params.append(request.new_email)
        set_parts.append("email = %s")
        params.append(request.new_email)
    if request.new_password is not None:
        set_parts.append("password = %s")
        params.append(request.new_password)
    if request.active is not None:
        set_parts.append("active = %s")
        params.append(request.active)

    if not set_parts:
        raise HTTPException(
            status_code=400,
            detail="No hay cambios para aplicar",
        )

    set_parts.append("write_date = NOW()")

    # WHERE clause
    if request.user_id:
        where = "id = %s"
        params.append(request.user_id)
    else:
        where = "login = %s"
        params.append(request.login)

    query = f"UPDATE res_users SET {', '.join(set_parts)} WHERE {where}"

    try:
        with _db_conn(db_name) as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                if cur.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="Usuario no encontrado",
                    )
            conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando credenciales: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error actualizando credenciales de cuenta",
        )

    return {
        "success": True,
        "subdomain": db_name,
        "message": "Cuenta actualizada exitosamente",
    }


@app.put("/api/tenant/password")
async def change_password(
    request: TenantPasswordRequest,
    x_api_key: str = Header(None),
):
    """Cambia la contraseña del admin de un tenant."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    db_name = _validate_dbname(request.subdomain)

    if not _db_exists(db_name):
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    logger.info(f"Cambiando contraseña para tenant: {db_name}")

    try:
        with _db_conn(db_name) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE res_users SET password = %s, write_date = NOW() "
                    "WHERE login = 'admin'",
                    (request.new_password,),
                )
                if cur.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="Admin user not found",
                    )
            conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando contraseña: {e}")
        raise HTTPException(status_code=500, detail="Error updating password")

    return {
        "success": True,
        "subdomain": db_name,
        "message": "Contraseña actualizada exitosamente",
    }


@app.put("/api/tenant/suspend")
async def suspend_tenant(
    request: TenantSuspendRequest,
    x_api_key: str = Header(None),
):
    """Suspende o reactiva un tenant."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    db_name = _validate_dbname(request.subdomain)

    if not _db_exists(db_name):
        raise HTTPException(status_code=404, detail=f"Database {db_name} not found")

    reason = request.reason or "Suspension por falta de pago"
    action = "Suspendiendo" if request.suspend else "Reactivando"
    logger.info(f"{action} tenant: {db_name}")

    try:
        with _db_conn(db_name) as conn:
            with conn.cursor() as cur:
                if request.suspend:
                    # Deshabilitar todos los usuarios excepto superuser
                    cur.execute(
                        "UPDATE res_users SET active = false WHERE id != 1"
                    )
                    # Marcar como suspendido
                    cur.execute(
                        "INSERT INTO ir_config_parameter "
                        "(key, value, create_date, write_date, create_uid, write_uid) "
                        "VALUES ('tenant.suspended', 'true', NOW(), NOW(), 1, 1) "
                        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
                    )
                    cur.execute(
                        "INSERT INTO ir_config_parameter "
                        "(key, value, create_date, write_date, create_uid, write_uid) "
                        "VALUES ('tenant.suspend_reason', %s, NOW(), NOW(), 1, 1) "
                        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                        (reason,),
                    )
                else:
                    cur.execute(
                        "UPDATE res_users SET active = true WHERE id != 1"
                    )
                    cur.execute(
                        "UPDATE ir_config_parameter "
                        "SET value = 'false' WHERE key = 'tenant.suspended'"
                    )
            conn.commit()
    except Exception as e:
        logger.error(f"Error cambiando estado de {db_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error changing tenant status: {e}",
        )

    logger.info(
        f"Tenant {db_name} {'suspendido' if request.suspend else 'reactivado'}"
    )
    return {
        "success": True,
        "subdomain": db_name,
        "suspended": request.suspend,
        "reason": reason if request.suspend else None,
        "message": (
            "Tenant suspendido exitosamente"
            if request.suspend
            else "Tenant reactivado exitosamente"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(
        f"Iniciando Odoo Local Provisioning API v2 en puerto 8070 "
        f"(PG: {PG_USER}@{PG_HOST}:{PG_PORT})"
    )
    uvicorn.run(app, host="0.0.0.0", port=8070)