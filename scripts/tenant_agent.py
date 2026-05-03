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
DB_PASS = os.environ.get("ODOO_DB_PASSWORD", "")
TEMPLATE_DB = os.environ.get("ODOO_TEMPLATE_DB", "template_tenant")
STRICT_FILESTORE_COPY = os.environ.get("ODOO_STRICT_FILESTORE_COPY", "false").strip().lower() in {"1", "true", "yes", "on"}

REDIS_URL = os.environ.get("ODOO_REDIS_URL", "")

CONF_DIR = Path("/etc/odoo")
ADDONS_BASE = Path("/opt/odoo/tenant-addons")
DATA_BASE = Path("/opt/odoo/.local/share")
LOG_DIR = Path("/var/log/odoo")

PORT_HTTP_RANGE = (9001, 9099)
PORT_WS_OFFSET = 500  # http_port + 500 = longpolling_port
SAFE_SUBDOMAIN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
SAFE_DB_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]{3,63}$")

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
    conn = _pg_connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (name,),
            )
    finally:
        conn.close()


def _drop_database(name: str) -> None:
    _terminate_db_connections(name)
    conn = _pg_connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))
    finally:
        conn.close()


def _clone_database(name: str) -> None:
    _clone_database_from_template(name, TEMPLATE_DB)


def _clone_database_from_template(name: str, template_db: str) -> None:
    _terminate_db_connections(template_db)
    conn = _pg_connect()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE DATABASE {} WITH TEMPLATE {} OWNER {}").format(
                    sql.Identifier(name),
                    sql.Identifier(template_db),
                    sql.Identifier(DB_USER),
                )
            )
    finally:
        conn.close()


def _normalize_db_identifier(value: str | None, fallback: str = TEMPLATE_DB) -> str:
    candidate = (value or fallback or "").strip().lower().replace("-", "_").replace(" ", "_")
    candidate = "".join(ch for ch in candidate if ch.isalnum() or ch == "_")
    if not SAFE_DB_IDENTIFIER.match(candidate):
        raise ValueError(f"identificador de DB inválido: {value}")
    return candidate


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


def _filestore_path(db_name: str, data_dir: Path | None = None) -> Path:
    return (data_dir or _data_path(db_name)) / "filestore" / db_name


def _template_filestore_candidates(template_db: str) -> list[Path]:
    configured = os.environ.get("ODOO_TEMPLATE_FILESTORE_SOURCE", "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        [
            _filestore_path(template_db),
            DATA_BASE / "Odoo-techeels" / "filestore" / template_db,
            Path("/var/lib/odoo") / "filestore" / template_db,
        ]
    )
    return candidates


def _chown_tree(path: Path, user: str = "odoo", group: str = "odoo") -> None:
    if not path.exists():
        return
    try:
        shutil.chown(path, user=user, group=group)
    except LookupError:
        return
    for child in path.rglob("*"):
        try:
            shutil.chown(child, user=user, group=group)
        except (FileNotFoundError, PermissionError):
            continue


def _copy_template_filestore(template_db: str, new_db: str) -> dict[str, Any]:
    """Copia el filestore físico del template al tenant nuevo si existe."""
    target = _filestore_path(new_db)
    target.mkdir(parents=True, exist_ok=True)

    source = next((p for p in _template_filestore_candidates(template_db) if p.exists() and p.is_dir()), None)
    if not source:
        message = f"No se encontró filestore fuente para template {template_db}"
        log.warning(message)
        _chown_tree(target)
        if STRICT_FILESTORE_COPY:
            raise RuntimeError(message)
        return {"success": False, "copied": False, "source": None, "target": str(target), "warning": message}

    shutil.copytree(source, target, dirs_exist_ok=True)
    _chown_tree(target)
    return {"success": True, "copied": True, "source": str(source), "target": str(target)}


def _stored_attachment_names(db_name: str) -> list[str]:
    with _pg_connect(db_name) as conn, conn.cursor() as cur:
        cur.execute("SELECT store_fname FROM ir_attachment WHERE store_fname IS NOT NULL ORDER BY id")
        return [row[0] for row in cur.fetchall() if row and row[0]]


def _find_existing_filestore_file(store_fname: str, target: Path) -> Path | None:
    roots = [DATA_BASE, Path("/var/lib/odoo/filestore")]
    for root in roots:
        if not root.exists():
            continue
        patterns = [f"*/filestore/*/{store_fname}", f"*/{store_fname}"]
        for pattern in patterns:
            for candidate in root.glob(pattern):
                if candidate == target / store_fname:
                    continue
                if candidate.is_file() and candidate.stat().st_size > 0:
                    return candidate
    return None


def _repair_missing_filestore_files(db_name: str) -> dict[str, Any]:
    """Busca archivos faltantes por hash en otros filestores locales y copia los encontrados."""
    target = _filestore_path(db_name)
    target.mkdir(parents=True, exist_ok=True)
    repaired: list[str] = []
    missing: list[str] = []

    for store_fname in _stored_attachment_names(db_name):
        destination = target / store_fname
        if destination.exists():
            continue
        source = _find_existing_filestore_file(store_fname, target)
        if source:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            repaired.append(store_fname)
        else:
            missing.append(store_fname)

    _chown_tree(target)
    return {
        "success": not missing,
        "target": str(target),
        "repaired_count": len(repaired),
        "missing_count": len(missing),
        "sample_missing": missing[:10],
    }


def _validate_filestore(db_name: str) -> dict[str, Any]:
    target = _filestore_path(db_name)
    missing: list[str] = []
    total = 0
    for store_fname in _stored_attachment_names(db_name):
        total += 1
        if not (target / store_fname).exists():
            missing.append(store_fname)
    return {
        "success": not missing,
        "target": str(target),
        "stored_attachments": total,
        "missing_count": len(missing),
        "sample_missing": missing[:10],
    }


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


def _upsert_ir_config_parameter(cur, key: str, value: str) -> None:
    cur.execute("SELECT id FROM ir_config_parameter WHERE key = %s LIMIT 1", (key,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE ir_config_parameter SET value = %s WHERE id = %s", (value, row[0]))
    else:
        cur.execute(
            "INSERT INTO ir_config_parameter (key, value, create_date, write_date) VALUES (%s, %s, now(), now())",
            (key, value),
        )


def _post_clone_config_db(
    db_name: str,
    *,
    subdomain: str,
    domain: str = "sajet.us",
    admin_email: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Ajusta parámetros heredados del template antes de arrancar Odoo."""
    fqdn = f"{subdomain}.{domain}"
    changed: list[str] = []
    with _pg_connect(db_name) as conn, conn.cursor() as cur:
        _upsert_ir_config_parameter(cur, "web.base.url", f"https://{fqdn}")
        _upsert_ir_config_parameter(cur, "web.base.url.freeze", "True")
        _upsert_ir_config_parameter(cur, "mail.catchall.domain", fqdn)
        changed.extend(["web.base.url", "web.base.url.freeze", "mail.catchall.domain"])

        if company_name:
            cur.execute("UPDATE res_company SET name = %s WHERE id = 1", (company_name,))
            changed.append("res_company.name")

        if admin_email:
            cur.execute(
                "SELECT id, partner_id FROM res_users WHERE login IN ('admin', 'admin@sajet.us') OR id = 2 ORDER BY id LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                user_id, partner_id = row
                cur.execute("UPDATE res_users SET login = %s WHERE id = %s", (admin_email, user_id))
                if partner_id:
                    cur.execute("UPDATE res_partner SET email = %s WHERE id = %s", (admin_email, partner_id))
                changed.append("admin_email")
        conn.commit()
    return {"success": True, "fqdn": fqdn, "changed": changed}


def _post_clone_config_orm(
    db_name: str,
    *,
    subdomain: str,
    domain: str = "sajet.us",
    admin_email: str | None = None,
    admin_password: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Aplica ajustes que requieren ORM de Odoo, como hashear contraseña."""
    if not admin_password and not admin_email and not company_name:
        return {"success": True, "skipped": True, "reason": "sin cambios ORM solicitados"}

    code = r'''
import json
fqdn = __fqdn__
admin_email = __admin_email__
admin_password = __admin_password__
company_name = __company_name__
changed = []
ICP = env["ir.config_parameter"].sudo()
ICP.set_param("web.base.url", "https://" + fqdn)
ICP.set_param("web.base.url.freeze", "True")
ICP.set_param("mail.catchall.domain", fqdn)
changed.extend(["web.base.url", "web.base.url.freeze", "mail.catchall.domain"])
if company_name:
    company = env["res.company"].sudo().browse(1)
    if company.exists():
        company.write({"name": company_name})
        changed.append("res_company.name")
if admin_email or admin_password:
    Users = env["res.users"].sudo()
    user = Users.search([("login", "=", admin_email)], limit=1) if admin_email else Users.browse()
    if not user:
        user = Users.search([("login", "in", ["admin@sajet.us", "admin"])], limit=1) or Users.browse(2)
    values = {}
    if admin_email:
        values["login"] = admin_email
        if user.partner_id:
            user.partner_id.write({"email": admin_email})
        changed.append("admin_email")
    if admin_password:
        values["password"] = admin_password
        changed.append("admin_password")
    if user and user.exists() and values:
        user.write(values)
env.cr.commit()
print(json.dumps({"success": True, "changed": changed}))
'''
    replacements = {
        "__fqdn__": json.dumps(f"{subdomain}.{domain}"),
        "__admin_email__": json.dumps(admin_email),
        "__admin_password__": json.dumps(admin_password),
        "__company_name__": json.dumps(company_name),
    }
    for marker, value in replacements.items():
        code = code.replace(marker, value)

    cmd = [
        "/opt/odoo/venv/bin/python3",
        "/opt/odoo/odoo-bin",
        "shell",
        "-c",
        str(_conf_path(db_name)),
        "-d",
        db_name,
        "--no-http",
    ]
    try:
        result = subprocess.run(cmd, input=code, capture_output=True, text=True, timeout=90, check=False)
        if result.returncode != 0:
            return {"success": False, "error": result.stderr[-1000:] or result.stdout[-1000:]}
        stdout = result.stdout.strip()
        start = stdout.rfind("{")
        return json.loads(stdout[start:]) if start >= 0 else {"success": True, "stdout": stdout[-500:]}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---------- Acciones de alto nivel ----------
def create_tenant(
    sub: str,
    admin_password: str | None = None,
    *,
    template_db: str | None = None,
    domain: str = "sajet.us",
    admin_email: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    if not SAFE_SUBDOMAIN.match(sub):
        raise ValueError(f"subdomain inválido: {sub}")

    source_template_db = _normalize_db_identifier(template_db, TEMPLATE_DB)
    if not _db_exists(source_template_db):
        raise ValueError(f"Template DB '{source_template_db}' no existe")

    if _db_exists(sub):
        raise ValueError(f"La base de datos '{sub}' ya existe")

    if _conf_path(sub).exists():
        raise ValueError(f"Ya existe configuración para '{sub}'")

    http_port = _allocate_port()
    log.info("Provisionando tenant '%s' en puerto %d", sub, http_port)

    # 1. Clonar DB
    _clone_database_from_template(sub, source_template_db)

    # 2. Crear directorios
    _addons_path(sub).mkdir(parents=True, exist_ok=True)
    _data_path(sub).mkdir(parents=True, exist_ok=True)
    shutil.chown(_addons_path(sub), user="odoo", group="odoo")
    shutil.chown(_data_path(sub), user="odoo", group="odoo")

    # 2.1 Copiar y reparar filestore físico del template
    filestore_copy = _copy_template_filestore(source_template_db, sub)
    filestore_repair = _repair_missing_filestore_files(sub)

    # 2.2 Ajustar parámetros heredados del template antes del primer arranque
    post_config = _post_clone_config_db(
        sub,
        subdomain=sub,
        domain=domain,
        admin_email=admin_email,
        company_name=company_name,
    )

    # 3. Escribir conf
    _write_tenant_conf(sub, http_port)

    # 3.1 Ajustes ORM: contraseña admin y cache-safe config antes del arranque público
    orm_config = _post_clone_config_orm(
        sub,
        subdomain=sub,
        domain=domain,
        admin_email=admin_email,
        admin_password=admin_password,
        company_name=company_name,
    )

    # 4. Habilitar e iniciar servicio
    _systemctl("daemon-reload")
    enable = _systemctl("enable", _service_name(sub))
    start = _systemctl("start", _service_name(sub))

    if start.returncode != 0:
        log.error("Falló start: %s", start.stderr)

    filestore_validation = _validate_filestore(sub)

    return {
        "subdomain": sub,
        "database": sub,
        "template_db": source_template_db,
        "http_port": http_port,
        "longpolling_port": http_port + PORT_WS_OFFSET,
        "service": _service_name(sub),
        "service_enabled": enable.returncode == 0,
        "service_started": start.returncode == 0,
        "service_stderr": start.stderr.strip() if start.stderr else None,
        "filestore": {
            "copy": filestore_copy,
            "repair": filestore_repair,
            "validation": filestore_validation,
        },
        "post_config": post_config,
        "orm_config": orm_config,
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
                result = create_tenant(
                    sub,
                    data.get("admin_password"),
                    template_db=data.get("template_db"),
                    domain=data.get("domain") or "sajet.us",
                    admin_email=data.get("admin_email"),
                    company_name=data.get("company_name"),
                )
                return self._send_json(200, {"success": True, **result})
            except ValueError as e:
                return self._send_json(400, {"detail": str(e)})
            except Exception as e:
                log.exception("Error creando tenant")
                return self._send_json(500, {"detail": str(e)})
        if self.path.startswith("/api/tenant/") and self.path.endswith("/repair"):
            sub = self.path.split("/")[3].strip()
            try:
                if not SAFE_SUBDOMAIN.match(sub):
                    raise ValueError(f"subdomain inválido: {sub}")
                if not _db_exists(sub):
                    raise ValueError(f"La base de datos '{sub}' no existe")
                repair = _repair_missing_filestore_files(sub)
                validation = _validate_filestore(sub)
                return self._send_json(200, {"success": validation.get("success", False), "subdomain": sub, "repair": repair, "validation": validation})
            except ValueError as e:
                return self._send_json(400, {"detail": str(e)})
            except Exception as e:
                log.exception("Error reparando tenant")
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
