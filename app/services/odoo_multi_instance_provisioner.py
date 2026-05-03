"""
OdooMultiInstanceProvisioner — Provisiona tenants Odoo en arquitectura
multi-instance (un proceso Odoo por tenant) en PCT 201.

Diseñado para reemplazar la asunción "Odoo monolítico en :8069" del provisioner
legacy. Cada tenant obtiene:
  - Puerto HTTP propio (rango 9001-9099)
  - Puerto longpolling propio (puerto + 500)
  - Archivo `/etc/odoo/tenant-<sub>.conf` derivado del template de techeels
  - Servicio systemd `odoo-tenant@<sub>.service`
  - Mapping en `/etc/nginx/sites-available/odoo` (maps `$odoo_http_upstream`
    y `$odoo_chat_upstream`)
  - BD clonada de `template_tenant`

Acceso: SSH desde PCT 202 → host `miami-pve` (10.10.20.1) → `pct exec 201/200`.
La key `~/.ssh/id_ed25519` ya está autorizada.

Operaciones:
  - provision(spec)   → crea todo end-to-end (idempotente)
  - deprovision(sub)  → elimina servicio + BD + nginx mapping
  - list_active()     → lista tenants vivos
  - allocate_port()   → puerto HTTP libre ≥ 9010
"""
from __future__ import annotations

import json
import logging
import os
import re
import secrets
import string
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── Config — coincide con cloudflare_tunnel_gate.py ─────────────────
SSH_KEY = "/root/.ssh/id_ed25519"
SSH_HOST = "10.10.20.1"
SSH_USER = "root"
SSH_OPTS = ["-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=10"]

ODOO_PCT_ID = 201
PG_PCT_ID = 200
NPM_PCT_ID = 205

PORT_RANGE_START = 9010
PORT_RANGE_END = 9099
LONGPOLLING_OFFSET = 500   # 9010 → 9510, etc.

ODOO_PG_HOST = "10.10.20.200"
ODOO_PG_USER = "Jeturing"
ODOO_PG_PASSWORD = os.getenv("ODOO_DB_PASSWORD", "")
TEMPLATE_DB = "template_tenant"

REDIS_URL = os.getenv("ODOO_REDIS_URL", "")
NGINX_CONF = "/etc/nginx/sites-available/odoo"
ODOO_LOCAL_IP = "127.0.0.1"  # tenants viven en el mismo nodo que nginx


@dataclass
class TenantInstanceSpec:
    subdomain: str
    company_name: Optional[str] = None
    admin_login: Optional[str] = None
    admin_password: Optional[str] = None
    workers: int = 2
    db_maxconn: int = 6
    extra_addons: list[str] = field(default_factory=list)


@dataclass
class ProvisionResult:
    success: bool
    subdomain: str
    http_port: Optional[int] = None
    longpolling_port: Optional[int] = None
    backend_host: str = "10.10.20.201"
    db_created: bool = False
    service_started: bool = False
    nginx_updated: bool = False
    admin_login: Optional[str] = None
    admin_password: Optional[str] = None
    error: Optional[str] = None
    steps: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


# ─── SSH primitives ─────────────────────────────────────────────────

def _ssh(cmd: str, *, timeout: int = 60, input_data: Optional[str] = None) -> tuple[int, str, str]:
    """Ejecuta comando bash en el host miami-pve vía SSH."""
    full = ["ssh", "-i", SSH_KEY, *SSH_OPTS, f"{SSH_USER}@{SSH_HOST}", cmd]
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=timeout, input=input_data)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"SSH timeout after {timeout}s"


def _pct_exec(pct_id: int, cmd: str, *, timeout: int = 60, input_data: Optional[str] = None) -> tuple[int, str, str]:
    """Ejecuta `pct exec <pct_id> -- bash -c '<cmd>'` en miami-pve."""
    # Escape simple comillas para el wrapper -c
    escaped = cmd.replace("'", "'\"'\"'")
    return _ssh(f"pct exec {pct_id} -- bash -c '{escaped}'", timeout=timeout, input_data=input_data)


def _pct_push_text(pct_id: int, content: str, dest_path: str) -> tuple[bool, str]:
    """Sube un texto a un archivo dentro de un PCT."""
    # Escribir primero a /tmp del host, luego pct push
    tmp_host = f"/tmp/_provisioner_{secrets.token_hex(8)}.tmp"
    rc, _, err = _ssh(f"cat > {tmp_host}", input_data=content)
    if rc != 0:
        return False, f"write tmp host failed: {err}"
    rc, _, err = _ssh(f"pct push {pct_id} {tmp_host} {dest_path} && rm -f {tmp_host}")
    if rc != 0:
        return False, f"pct push failed: {err}"
    return True, dest_path


# ─── Provisioner ─────────────────────────────────────────────────────

class OdooMultiInstanceProvisioner:

    # ── Discovery ────────────────────────────────────────────────────

    def list_active_tenants(self) -> list[dict[str, Any]]:
        """Devuelve [{subdomain, http_port, longpolling_port, state}, ...]."""
        rc, out, err = _pct_exec(
            ODOO_PCT_ID,
            "for f in /etc/odoo/tenant-*.conf; do "
            " sub=$(basename $f .conf | sed s/tenant-//); "
            " hp=$(grep -E '^http_port' $f | awk '{print $3}'); "
            " lp=$(grep -E '^longpolling_port' $f | awk '{print $3}'); "
            " state=$(systemctl is-active odoo-tenant@${sub} 2>/dev/null); "
            " echo \"${sub}|${hp}|${lp}|${state}\"; "
            "done",
        )
        if rc != 0:
            return []
        items = []
        for line in out.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                items.append({
                    "subdomain": parts[0],
                    "http_port": int(parts[1]) if parts[1].isdigit() else None,
                    "longpolling_port": int(parts[2]) if parts[2].isdigit() else None,
                    "state": parts[3],
                })
        return items

    def allocate_port(self) -> int:
        """Devuelve un puerto HTTP libre en [9010, 9099]."""
        used = {t["http_port"] for t in self.list_active_tenants() if t["http_port"]}
        for p in range(PORT_RANGE_START, PORT_RANGE_END + 1):
            if p not in used:
                return p
        raise RuntimeError("Sin puertos disponibles en [9010, 9099]")

    def tenant_exists(self, subdomain: str) -> bool:
        """¿Existe ya el conf y/o servicio?"""
        rc, _, _ = _pct_exec(ODOO_PCT_ID, f"test -f /etc/odoo/tenant-{subdomain}.conf")
        return rc == 0

    def db_exists(self, subdomain: str) -> bool:
        rc, out, _ = _pct_exec(
            PG_PCT_ID,
            f"su - postgres -c \"psql -lqt | cut -d\\| -f1 | tr -d ' ' | grep -Fxq {subdomain}\""
        )
        return rc == 0

    # ── Build conf ───────────────────────────────────────────────────

    def _render_conf(self, spec: TenantInstanceSpec, http_port: int, lp_port: int) -> str:
        sub = spec.subdomain
        return f"""[options]
; Tenant: {sub}
; Auto-provisioned via OdooMultiInstanceProvisioner
admin_passwd = False
db_host = {ODOO_PG_HOST}
db_port = 5432
db_user = {ODOO_PG_USER}
db_password = {ODOO_PG_PASSWORD}
db_maxconn = {spec.db_maxconn}
db_name = {sub}
dbfilter = ^{sub}$
http_port = {http_port}
longpolling_port = {lp_port}
gevent_port = {lp_port}
workers = {spec.workers}
max_cron_threads = 1
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 600
limit_time_real = 1200
data_dir = /opt/odoo/.local/share/Odoo-{sub}
logfile = /var/log/odoo/tenant-{sub}.log
log_level = info
addons_path = /opt/odoo/tenant-addons/{sub},/opt/odoo/addons,/opt/odoo/Extra,/opt/odoo/custom_addons,/opt/odoo/extra-addons
server_wide_modules = base,web,redis_session_store
session_redis_url = {REDIS_URL}
session_redis_expire = 604800
proxy_mode = True
list_db = False
"""

    # ── Steps ────────────────────────────────────────────────────────

    def _create_db_from_template(self, subdomain: str) -> tuple[bool, str]:
        """CREATE DATABASE WITH TEMPLATE template_tenant. Idempotente."""
        if self.db_exists(subdomain):
            return True, "already_exists"
        # Paso 1: terminar conexiones al template (en su propia sentencia)
        terminate_sql = (
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            f"WHERE datname='{TEMPLATE_DB}' AND pid<>pg_backend_pid();"
        )
        rc, _, err = _pct_exec(
            PG_PCT_ID,
            f'su - postgres -c "psql -c \\"{terminate_sql}\\""',
            timeout=30,
        )
        if rc != 0:
            logger.warning("terminate_backend warn: %s", err)
        # Paso 2: CREATE DATABASE — debe ir solo, sin transacción
        create_sql = (
            f"CREATE DATABASE \\\"{subdomain}\\\" WITH TEMPLATE \\\"{TEMPLATE_DB}\\\" "
            f"OWNER \\\"{ODOO_PG_USER}\\\";"
        )
        rc, out, err = _pct_exec(
            PG_PCT_ID,
            f'su - postgres -c "psql -c \\"{create_sql}\\""',
            timeout=120,
        )
        if rc != 0:
            return False, f"CREATE DATABASE falló: {err or out}"
        return True, "created"

    def _write_conf_and_setup_dirs(self, spec: TenantInstanceSpec, http_port: int, lp_port: int) -> tuple[bool, str]:
        sub = spec.subdomain
        conf = self._render_conf(spec, http_port, lp_port)
        # Subir conf
        ok, msg = _pct_push_text(ODOO_PCT_ID, conf, f"/etc/odoo/tenant-{sub}.conf")
        if not ok:
            return False, msg
        # Setup directorios + permisos
        rc, _, err = _pct_exec(
            ODOO_PCT_ID,
            f"chown odoo:odoo /etc/odoo/tenant-{sub}.conf && "
            f"chmod 640 /etc/odoo/tenant-{sub}.conf && "
            f"mkdir -p /opt/odoo/.local/share/Odoo-{sub} /opt/odoo/tenant-addons/{sub} && "
            f"chown -R odoo:odoo /opt/odoo/.local/share/Odoo-{sub} /opt/odoo/tenant-addons/{sub} && "
            f"touch /var/log/odoo/tenant-{sub}.log && "
            f"chown odoo:odoo /var/log/odoo/tenant-{sub}.log",
        )
        if rc != 0:
            return False, f"setup dirs falló: {err}"
        return True, "ok"

    def _start_service(self, subdomain: str) -> tuple[bool, str]:
        rc, out, err = _pct_exec(
            ODOO_PCT_ID,
            f"systemctl daemon-reload && systemctl enable odoo-tenant@{subdomain} && "
            f"systemctl restart odoo-tenant@{subdomain} && "
            f"sleep 3 && systemctl is-active odoo-tenant@{subdomain}",
            timeout=120,
        )
        active = (out.strip().splitlines() or [""])[-1].strip()
        if rc != 0 or active != "active":
            # Capturar logs para diagnóstico
            _, log, _ = _pct_exec(
                ODOO_PCT_ID,
                f"journalctl -u odoo-tenant@{subdomain} --no-pager -n 30",
            )
            return False, f"service no quedó active (state={active}): {err or log[-500:]}"
        return True, "active"

    def _update_nginx_maps(self, subdomain: str, http_port: int, lp_port: int) -> tuple[bool, str]:
        """
        Inserta el host→upstream del tenant en los maps `$odoo_http_upstream`
        y `$odoo_chat_upstream`. Idempotente: si ya existe la línea, no duplica.
        """
        sub = subdomain
        http_line = f"    {sub}.sajet.us http://{ODOO_LOCAL_IP}:{http_port};"
        chat_line = f"    {sub}.sajet.us http://{ODOO_LOCAL_IP}:{lp_port};"

        # Backup
        rc, _, _ = _pct_exec(
            ODOO_PCT_ID,
            f"cp -f {NGINX_CONF} {NGINX_CONF}.bak.$(date +%s) 2>/dev/null; true",
        )

        # Script Python para insertar en cada map de forma idempotente
        py = '''
import re, pathlib
p = pathlib.Path(NGINX_CONF_PATH)
src = p.read_text()

def inject(src, marker_var, new_line, sub):
    pat = re.compile(r"(map \\$host \\$" + marker_var + r" \\{[^}]*?)(\\n\\})", re.DOTALL)
    m = pat.search(src)
    if not m:
        return src, False
    block = m.group(1)
    if sub + ".sajet.us" in block:
        return src, False
    new_block = block + "\\n" + new_line
    return src[:m.start()] + new_block + m.group(2) + src[m.end():], True

src, c1 = inject(src, "odoo_http_upstream", HTTP_LINE, SUB)
src, c2 = inject(src, "odoo_chat_upstream", CHAT_LINE, SUB)
p.write_text(src)
print("changed" if (c1 or c2) else "noop")
'''
        # Sustituir placeholders sin f-string para no chocar con regex/braces
        py = (py
              .replace("NGINX_CONF_PATH", repr(NGINX_CONF))
              .replace("HTTP_LINE", repr(http_line))
              .replace("CHAT_LINE", repr(chat_line))
              .replace("SUB", repr(sub)))
        # Subir script y ejecutar
        ok, _ = _pct_push_text(ODOO_PCT_ID, py, "/tmp/_inject_nginx.py")
        if not ok:
            return False, "no se pudo subir script de inyección"
        rc, out, err = _pct_exec(ODOO_PCT_ID, "python3 /tmp/_inject_nginx.py && rm -f /tmp/_inject_nginx.py")
        if rc != 0:
            return False, f"inyección falló: {err}"
        # Validar nginx
        rc, _, err = _pct_exec(ODOO_PCT_ID, "nginx -t 2>&1")
        if rc != 0:
            return False, f"nginx -t falló: {err}"
        rc, _, err = _pct_exec(ODOO_PCT_ID, "systemctl reload nginx")
        if rc != 0:
            return False, f"reload nginx falló: {err}"
        return True, out.strip()

    # ── Public API ───────────────────────────────────────────────────

    def provision(self, spec: TenantInstanceSpec) -> ProvisionResult:
        sub = spec.subdomain.lower().strip()
        sub = re.sub(r"[^a-z0-9_-]", "", sub)
        if len(sub) < 3:
            return ProvisionResult(success=False, subdomain=spec.subdomain,
                                   error="subdomain debe tener ≥3 chars")
        spec.subdomain = sub

        if not spec.admin_login:
            spec.admin_login = f"{sub}@sajet.us"
        if not spec.admin_password:
            alphabet = string.ascii_letters + string.digits + "@#$%!-_"
            spec.admin_password = "".join(secrets.choice(alphabet) for _ in range(20))

        result = ProvisionResult(
            success=True, subdomain=sub,
            admin_login=spec.admin_login, admin_password=spec.admin_password,
        )

        # 1. Asignar puerto si no existe ya
        if self.tenant_exists(sub):
            # Releer puerto del conf existente
            rc, out, _ = _pct_exec(ODOO_PCT_ID,
                f"grep '^http_port' /etc/odoo/tenant-{sub}.conf | awk '{{print $3}}'")
            if rc == 0 and out.strip().isdigit():
                http_port = int(out.strip())
                lp_port = http_port + LONGPOLLING_OFFSET
                result.steps.append({"step": "reuse_existing_conf", "http_port": http_port})
            else:
                result.success = False; result.error = "conf existente sin http_port"
                return result
        else:
            try:
                http_port = self.allocate_port()
                lp_port = http_port + LONGPOLLING_OFFSET
                result.steps.append({"step": "allocate_port", "http_port": http_port, "lp_port": lp_port})
            except Exception as e:
                result.success = False; result.error = str(e); return result

        result.http_port = http_port
        result.longpolling_port = lp_port

        # 2. Crear BD desde template (idempotente)
        ok, msg = self._create_db_from_template(sub)
        result.steps.append({"step": "create_database", "ok": ok, "msg": msg})
        if not ok:
            result.success = False; result.error = msg; return result
        result.db_created = True

        # 3. Escribir conf + dirs (siempre re-escribe por si cambió port)
        ok, msg = self._write_conf_and_setup_dirs(spec, http_port, lp_port)
        result.steps.append({"step": "write_conf", "ok": ok, "msg": msg})
        if not ok:
            result.success = False; result.error = msg; return result

        # 4. Levantar servicio
        ok, msg = self._start_service(sub)
        result.steps.append({"step": "start_service", "ok": ok, "msg": msg})
        if not ok:
            result.success = False; result.error = msg; return result
        result.service_started = True

        # 5. Actualizar nginx
        ok, msg = self._update_nginx_maps(sub, http_port, lp_port)
        result.steps.append({"step": "nginx_update", "ok": ok, "msg": msg})
        if not ok:
            # No abortar — el tenant funciona localmente; solo loguear
            logger.warning("Nginx no actualizado: %s", msg)
        else:
            result.nginx_updated = True

        return result

    def deprovision(self, subdomain: str, *, drop_db: bool = True) -> dict[str, Any]:
        sub = subdomain.lower().strip()
        steps = []
        # Stop + disable servicio
        rc, out, err = _pct_exec(ODOO_PCT_ID,
            f"systemctl stop odoo-tenant@{sub} 2>/dev/null; "
            f"systemctl disable odoo-tenant@{sub} 2>/dev/null; "
            f"rm -f /etc/odoo/tenant-{sub}.conf; "
            f"rm -rf /opt/odoo/.local/share/Odoo-{sub}; "
            f"rm -f /var/log/odoo/tenant-{sub}.log; echo done")
        steps.append({"stop_service": out.strip(), "rc": rc})
        # Drop DB
        if drop_db:
            sql = (f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='{sub}'; "
                   f"DROP DATABASE IF EXISTS \\\"{sub}\\\";")
            rc, out, err = _pct_exec(PG_PCT_ID, f'su - postgres -c "psql -c \\"{sql}\\""', timeout=120)
            steps.append({"drop_db": out.strip()[:100], "rc": rc, "err": err[:200] if err else ""})
        return {"success": True, "subdomain": sub, "steps": steps}


# Singleton
multi_instance_provisioner = OdooMultiInstanceProvisioner()
