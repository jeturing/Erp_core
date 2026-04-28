#!/usr/bin/env python3
"""
Tenant Agent — Servicio HTTP local en PCT 201 (puerto 8070)

Expone una API mínima para que SAJET (PCT 202) provisione tenants Odoo:
  - POST   /api/tenant   → crea DB desde template + .conf + systemd service
  - DELETE /api/tenant   → elimina DB + .conf + systemd service + filestore
  - GET    /api/tenants  → lista tenants instalados
  - GET    /api/health   → healthcheck

Autenticación: header X-API-KEY (debe coincidir con PROVISIONING_API_KEY).

Diseño:
  - Solo stdlib + psycopg2 (ya disponible en venv Odoo).
  - Asignación automática de puertos http_port / longpolling_port (rango 9001-9099 / 9501-9599).
  - El servicio systemd `odoo-tenant@<sub>.service` debe existir (template).

Uso:
  /opt/odoo/venv/bin/python3 /opt/tenant-agent/tenant_agent.py
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2 import sql

# ---------- Configuración ----------
API_KEY = os.environ.get("TENANT_AGENT_API_KEY", "change-me")
LISTEN_HOST = os.environ.get("TENANT_AGENT_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("TENANT_AGENT_PORT", "8070"))

DB_HOST = os.environ.get("ODOO_DB_HOST", "10.10.20.200")
DB_PORT = int(os.environ.get("ODOO_DB_PORT", "5432"))
DB_USER = os.environ.get("ODOO_DB_USER", "Jeturing")
DB_PASS = os.environ.get("ODOO_DB_PASSWORD", "321Abcd")
TEMPLATE_DB = os.environ.get("ODOO_TEMPLATE_DB", "template_tenant")

REDIS_URL = os.environ.get(
    "ODOO_REDIS_URL", "redis://:JtrRedis2026!@10.10.20.203:6379/0"
)

CONF_DIR = Path("/etc/odoo")
ADDONS_BASE = Path("/opt/odoo/tenant-addons")
DATA_BASE = Path("/opt/odoo/.local/share")
LOG_DIR = Path("/var/log/odoo")

PORT_HTTP_RANGE = (9001, 9099)
PORT_WS_OFFSET = 500  # http_port + 500 = longpolling_port
SAFE_SUBDOMAIN = re.compile(r"^[A-Za-z0-9_]{3,30}$")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("tenant-agent")


# ---------- Helpers ----------
def _pg_connect(dbname: str = "postgres"):
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=dbname,
    )


def _db_exists(name: str) -> bool:
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        return cur.fetchone() is not None


def _list_tenant_databases() -> list[str]:
    with _pg_connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT datname FROM pg_database "
            "WHERE datistemplate = false "
            "  AND datname NOT IN ('postgres', %s) "
            "ORDER BY datname",
            (TEMPLATE_DB,),
        )
        return [r[0] for r in cur.fetchall()]


def _terminate_db_connections(name: str) -> None:
    with _pg_connect() as conn:
        conn.set_isolation_level(0)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (name,),
            )


def _drop_database(name: str) -> None:
    _terminate_db_connections(name)
    with _pg_connect() as conn:
        conn.set_isolation_level(0)
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))


def _clone_database(name: str) -> None:
    _terminate_db_connections(TEMPLATE_DB)
    with _pg_connect() as conn:
        conn.set_isolation_level(0)
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE DATABASE {} WITH TEMPLATE {} OWNER {}").format(
                    sql.Identifier(name),
                    sql.Identifier(TEMPLATE_DB),
                    sql.Identifier(DB_USER),
                )
            )


def _used_ports() -> set[int]:
    used: set[int] = set()
    if not CONF_DIR.exists():
        return used
    for conf in CONF_DIR.glob("tenant-*.conf"):
        try:
            for line in conf.read_text().splitlines():
                m = re.match(r"\s*http_port\s*=\s*(\d+)", line)
                if m:
                    used.add(int(m.group(1)))
        except OSError:
            continue
    return used


def _allocate_port() -> int:
    used = _used_ports()
    for port in range(*PORT_HTTP_RANGE):
        if port not in used:
            return port
    raise RuntimeError("No hay puertos http disponibles en el rango")


def _conf_path(sub: str) -> Path:
    return CONF_DIR / f"tenant-{sub}.conf"


def _addons_path(sub: str) -> Path:
    return ADDONS_BASE / sub


def _data_path(sub: str) -> Path:
    return DATA_BASE / f"Odoo-{sub}"


def _log_path(sub: str) -> Path:
    return LOG_DIR / f"tenant-{sub}.log"


def _write_tenant_conf(sub: str, http_port: int) -> None:
    ws_port = http_port + PORT_WS_OFFSET
    addons = ",".join(
        [
            str(_addons_path(sub)),
            "/opt/odoo/addons",
            "/opt/odoo/Extra",
            "/opt/odoo/custom_addons",
            "/opt/odoo/extra-addons",
        ]
    )
    body = f"""[options]
; Tenant: {sub}
; Auto-provisioned by tenant_agent.py
admin_passwd = False
db_host = {DB_HOST}
db_port = {DB_PORT}
db_user = {DB_USER}
db_password = {DB_PASS}
db_maxconn = 6
db_name = {sub}
dbfilter = ^{sub}$
http_port = {http_port}
longpolling_port = {ws_port}
gevent_port = {ws_port}
workers = 2
max_cron_threads = 1
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 600
limit_time_real = 1200
data_dir = {_data_path(sub)}
logfile = {_log_path(sub)}
log_level = info
addons_path = {addons}
server_wide_modules = base,web,redis_session_store
session_redis_url = {REDIS_URL}
session_redis_expire = 604800
proxy_mode = True
list_db = False
"""
    _conf_path(sub).write_text(body)
    os.chmod(_conf_path(sub), 0o644)


def _systemctl(*args: str) -> subprocess.CompletedProcess:
    cmd = ["systemctl", *args]
    log.info("$ %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _service_name(sub: str) -> str:
    return f"odoo-tenant@{sub}.service"


# ---------- Acciones de alto nivel ----------
def create_tenant(sub: str, admin_password: str | None = None) -> dict[str, Any]:
    if not SAFE_SUBDOMAIN.match(sub):
        raise ValueError(f"subdomain inválido: {sub}")

    if _db_exists(sub):
        raise ValueError(f"La base de datos '{sub}' ya existe")

    if _conf_path(sub).exists():
        raise ValueError(f"Ya existe configuración para '{sub}'")

    http_port = _allocate_port()
    log.info("Provisionando tenant '%s' en puerto %d", sub, http_port)

    # 1. Clonar DB
    _clone_database(sub)

    # 2. Crear directorios
    _addons_path(sub).mkdir(parents=True, exist_ok=True)
    _data_path(sub).mkdir(parents=True, exist_ok=True)
    shutil.chown(_addons_path(sub), user="odoo", group="odoo")
    shutil.chown(_data_path(sub), user="odoo", group="odoo")

    # 3. Escribir conf
    _write_tenant_conf(sub, http_port)

    # 4. Habilitar e iniciar servicio
    _systemctl("daemon-reload")
    enable = _systemctl("enable", _service_name(sub))
    start = _systemctl("start", _service_name(sub))

    if start.returncode != 0:
        log.error("Falló start: %s", start.stderr)

    # 5. Cambiar admin_password si se pidió (requiere Odoo arriba; lo omitimos aquí
    #    porque template_tenant ya viene con admin/admin — el endpoint público lo
    #    actualiza después por XML-RPC si lo desea)
    return {
        "subdomain": sub,
        "database": sub,
        "http_port": http_port,
        "longpolling_port": http_port + PORT_WS_OFFSET,
        "service": _service_name(sub),
        "service_enabled": enable.returncode == 0,
        "service_started": start.returncode == 0,
        "service_stderr": start.stderr.strip() if start.stderr else None,
    }


def delete_tenant(sub: str) -> dict[str, Any]:
    if not SAFE_SUBDOMAIN.match(sub):
        raise ValueError(f"subdomain inválido: {sub}")

    log.info("Eliminando tenant '%s'", sub)

    # 1. Stop + disable + reset systemd state
    _systemctl("stop", _service_name(sub))
    _systemctl("disable", _service_name(sub))
    _systemctl("reset-failed", _service_name(sub))

    # 2. Borrar conf
    conf_deleted = False
    if _conf_path(sub).exists():
        _conf_path(sub).unlink()
        conf_deleted = True

    # 3. Borrar filestore
    fs_deleted = False
    if _data_path(sub).exists():
        shutil.rmtree(_data_path(sub), ignore_errors=True)
        fs_deleted = True

    # 4. Borrar carpeta addons (solo si está vacía — protección)
    addons_deleted = False
    addons = _addons_path(sub)
    if addons.exists() and not any(addons.iterdir()):
        addons.rmdir()
        addons_deleted = True

    # 5. Borrar DB
    db_deleted = False
    if _db_exists(sub):
        _drop_database(sub)
        db_deleted = True

    # 6. Borrar log
    log_deleted = False
    if _log_path(sub).exists():
        try:
            _log_path(sub).unlink()
            log_deleted = True
        except OSError:
            pass

    return {
        "subdomain": sub,
        "database_deleted": db_deleted,
        "conf_deleted": conf_deleted,
        "filestore_deleted": fs_deleted,
        "addons_dir_deleted": addons_deleted,
        "log_deleted": log_deleted,
    }


# ---------- HTTP server ----------
class Handler(BaseHTTPRequestHandler):
    server_version = "TenantAgent/1.0"

    # Silenciar logs por defecto
    def log_message(self, fmt: str, *args: Any) -> None:
        log.info("%s - %s", self.address_string(), fmt % args)

    # ---- helpers
    def _check_auth(self) -> bool:
        key = self.headers.get("X-API-KEY") or self.headers.get("x-api-key")
        if key != API_KEY:
            self._send_json(401, {"detail": "API key inválida"})
            return False
        return True

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode())
        except Exception:
            return {}

    # ---- rutas
    def do_GET(self):  # noqa: N802
        if self.path == "/api/health":
            return self._send_json(200, {"status": "ok"})
        if not self._check_auth():
            return
        if self.path == "/api/tenants":
            try:
                tenants = _list_tenant_databases()
                return self._send_json(
                    200,
                    {"tenants": [{"database": t} for t in tenants], "total": len(tenants)},
                )
            except Exception as e:
                return self._send_json(500, {"detail": str(e)})
        return self._send_json(404, {"detail": "Not found"})

    def do_POST(self):  # noqa: N802
        if not self._check_auth():
            return
        if self.path == "/api/tenant":
            data = self._read_json()
            sub = (data.get("subdomain") or "").strip()
            try:
                result = create_tenant(sub, data.get("admin_password"))
                return self._send_json(200, {"success": True, **result})
            except ValueError as e:
                return self._send_json(400, {"detail": str(e)})
            except Exception as e:
                log.exception("Error creando tenant")
                return self._send_json(500, {"detail": str(e)})
        return self._send_json(404, {"detail": "Not found"})

    def do_DELETE(self):  # noqa: N802
        if not self._check_auth():
            return
        if self.path == "/api/tenant":
            data = self._read_json()
            sub = (data.get("subdomain") or "").strip()
            try:
                result = delete_tenant(sub)
                return self._send_json(200, {"success": True, **result})
            except ValueError as e:
                return self._send_json(400, {"detail": str(e)})
            except Exception as e:
                log.exception("Error eliminando tenant")
                return self._send_json(500, {"detail": str(e)})
        return self._send_json(404, {"detail": "Not found"})


def main() -> None:
    log.info("Tenant Agent listening on %s:%d", LISTEN_HOST, LISTEN_PORT)
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
