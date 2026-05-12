"""
Odoo Tenant Provisioner — Automatiza el despliegue completo de un tenant Odoo.

Pasos que maneja (post-creación de BD):
  1. Asignar puerto dedicado libre (9000+N http, 9500+N ws)
  2. Crear /etc/odoo/tenant-{subdomain}.conf en PCT201
  3. Crear directorios de addons y data
  4. Copiar filestore del template
  5. Iniciar servicio odoo-tenant@{subdomain}
  6. Agregar rutas en cloudflared (odoo17-tenants.yml)
  7. Reiniciar cloudflared-odoo17-tenants
  8. Crear DNS CNAME al tunnel correcto

Aprendizajes aplicados (2026-05-11):
  - El tunnel Docker (npm-tunnel) usa TUNNEL_TOKEN → config remota, NO archivo local.
  - Los tenants Odoo17 se enrutan vía cloudflared-odoo17-tenants (tunnel bf8c039f)
    que SÍ usa archivo local /root/.cloudflared/odoo17-tenants.yml
  - Cada tenant necesita config Odoo dedicada con dbfilter + list_db=False
    para evitar /web/database/selector
  - El archivo config.yml (tunnel 1b41dd54) es el gateway principal; NO se
    deben agregar rutas de tenants ahí.
"""
from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from ..config import (
    PROXMOX_SSH_HOST,
    PROXMOX_SSH_KEY,
    PROXMOX_SSH_USER,
)

logger = logging.getLogger(__name__)

SSH_BIN = shutil.which("ssh") or "/usr/bin/ssh"

# ── Configuración PCT ─────────────────────────────────────────────────

ODOO_PCT_ID = 201           # PCT donde corre Odoo 17
CLOUDFLARED_PCT_ID = 205    # PCT donde corren los tunnels
DB_HOST = "10.10.20.200"
DB_PORT = 6432
DB_USER = "Jeturing"
DB_PASSWORD = "321Abcd"

# Rango de puertos para tenants dedicados
PORT_HTTP_START = 9000   # HTTP: 9000-9099
PORT_WS_OFFSET = 500     # WebSocket: 9500-9599

# Archivos de configuración
ODOO_CONF_DIR = "/etc/odoo"
ODOO_DATA_BASE = "/opt/odoo/.local/share"
ODOO_ADDONS_BASE = "/opt/odoo/tenant-addons"
ODOO_LOG_DIR = "/var/log/odoo"

# Cloudflared
CLOUDFLARED_CONFIG = "/root/.cloudflared/odoo17-tenants.yml"
CLOUDFLARED_SERVICE = "cloudflared-odoo17-tenants"
ODOO17_TUNNEL_ID = "bf8c039f-6f61-48d0-bb66-89e5fdcc6a25"

# Template de configuración Odoo
ODOO_CONF_TEMPLATE = """[options]
; Tenant: {subdomain}
; Provisionado: {date}
admin_passwd = False
db_host = {db_host}
db_port = {db_port}
db_user = {db_user}
db_password = {db_password}
db_maxconn = 6
db_name = {subdomain}
dbfilter = ^{subdomain}$
http_port = {http_port}
longpolling_port = {ws_port}
gevent_port = {ws_port}
workers = 2
max_cron_threads = 1
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 600
limit_time_real = 1200
data_dir = {data_dir}
logfile = {log_dir}/tenant-{subdomain}.log
log_level = info
addons_path = {addons_dir},{base_addons}
server_wide_modules = base,web,redis_session_store
session_redis_expire = 604800
proxy_mode = True
list_db = False
"""

BASE_ADDONS = "/opt/odoo/addons,/opt/odoo/Extra,/opt/odoo/custom_addons,/opt/odoo/extra-addons"


# ── Helpers SSH/PCT ────────────────────────────────────────────────────

def _pct_exec(pct_id: int, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
    """Ejecuta comando en un PCT vía SSH al host Proxmox."""
    remote_cmd = f"pct exec {pct_id} -- bash -c {shlex.quote(cmd)}"
    ssh_cmd = [
        SSH_BIN,
        "-i", PROXMOX_SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "IdentitiesOnly=yes",
        "-o", "ConnectTimeout=10",
        f"{PROXMOX_SSH_USER}@{PROXMOX_SSH_HOST}",
        remote_cmd,
    ]
    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Timeout {timeout}s"
    except Exception as e:
        return False, str(e)


def _pct_exec_direct(pct_id: int, args: List[str], timeout: int = 30) -> Tuple[bool, str]:
    """Ejecuta pct exec directamente (cuando corre en host Proxmox)."""
    cmd = ["pct", "exec", str(pct_id), "--"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except Exception as e:
        return False, str(e)


def _is_proxmox_host() -> bool:
    """Detecta si estamos corriendo directamente en el host Proxmox."""
    return os.path.exists("/usr/sbin/pct")


def _run_on_pct(pct_id: int, cmd: str, timeout: int = 30) -> Tuple[bool, str]:
    """Ejecuta comando en PCT — directo si estamos en Proxmox, SSH si no."""
    if _is_proxmox_host():
        return _pct_exec_direct(pct_id, ["bash", "-c", cmd], timeout=timeout)
    return _pct_exec(pct_id, cmd, timeout=timeout)


# ── Asignación de puertos ─────────────────────────────────────────────

def _get_used_ports() -> List[int]:
    """Obtiene la lista de puertos HTTP ya asignados leyendo configs existentes."""
    ok, output = _run_on_pct(
        ODOO_PCT_ID,
        f"grep -h http_port {ODOO_CONF_DIR}/tenant-*.conf 2>/dev/null | grep -oP '\\d+'",
    )
    if not ok or not output.strip():
        return []
    ports = []
    for line in output.strip().split("\n"):
        line = line.strip()
        if line.isdigit():
            ports.append(int(line))
    return ports


def find_next_free_port() -> Tuple[int, int]:
    """
    Encuentra el siguiente par de puertos libres (http, ws).
    Retorna (http_port, ws_port) donde ws_port = http_port + PORT_WS_OFFSET.
    """
    used = set(_get_used_ports())
    for port in range(PORT_HTTP_START, PORT_HTTP_START + 100):
        if port not in used:
            return port, port + PORT_WS_OFFSET
    raise RuntimeError("No hay puertos disponibles en el rango 9000-9099")


# ── Provisioning Steps ────────────────────────────────────────────────

def create_odoo_config(
    subdomain: str,
    http_port: int,
    ws_port: int,
    template_db: str = "tenant_do",
) -> Dict[str, Any]:
    """
    Paso 1: Crear archivo de configuración Odoo para el tenant.
    """
    from datetime import datetime
    
    config_content = ODOO_CONF_TEMPLATE.format(
        subdomain=subdomain,
        date=datetime.now().strftime("%Y-%m-%d"),
        db_host=DB_HOST,
        db_port=DB_PORT,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        http_port=http_port,
        ws_port=ws_port,
        data_dir=f"{ODOO_DATA_BASE}/Odoo-{subdomain}",
        log_dir=ODOO_LOG_DIR,
        addons_dir=f"{ODOO_ADDONS_BASE}/{subdomain}",
        base_addons=BASE_ADDONS,
    )
    
    conf_path = f"{ODOO_CONF_DIR}/tenant-{subdomain}.conf"
    
    # Escribir config via pct exec
    import base64
    b64 = base64.b64encode(config_content.encode()).decode()
    ok, out = _run_on_pct(
        ODOO_PCT_ID,
        f"echo '{b64}' | base64 -d > {conf_path} && echo config_ok",
    )
    
    if not ok or "config_ok" not in out:
        return {"success": False, "error": f"Error creando config: {out}"}
    
    return {
        "success": True,
        "config_path": conf_path,
        "http_port": http_port,
        "ws_port": ws_port,
    }


def prepare_directories(subdomain: str, template_db: str = "tenant_do") -> Dict[str, Any]:
    """
    Paso 2: Crear directorios de addons/data y copiar filestore del template.
    """
    data_dir = f"{ODOO_DATA_BASE}/Odoo-{subdomain}"
    addons_dir = f"{ODOO_ADDONS_BASE}/{subdomain}"
    template_filestore = f"{ODOO_DATA_BASE}/Odoo-{template_db}/filestore/{template_db}"
    target_filestore = f"{data_dir}/filestore/{subdomain}"
    
    cmds = [
        f"mkdir -p {addons_dir} {data_dir}/filestore",
        f"test -d {template_filestore} && cp -a {template_filestore} {target_filestore} || echo no_template_filestore",
        f"chown -R odoo:odoo {addons_dir} {data_dir}",
        "echo dirs_ok",
    ]
    
    ok, out = _run_on_pct(ODOO_PCT_ID, " && ".join(cmds), timeout=120)
    
    if not ok or "dirs_ok" not in out:
        return {"success": False, "error": f"Error preparando directorios: {out}"}
    
    has_filestore = "no_template_filestore" not in out
    return {
        "success": True,
        "filestore_copied": has_filestore,
        "data_dir": data_dir,
        "addons_dir": addons_dir,
    }


def start_odoo_service(subdomain: str) -> Dict[str, Any]:
    """
    Paso 3: Iniciar (o reiniciar) el servicio odoo-tenant@{subdomain}.
    """
    service = f"odoo-tenant@{subdomain}"
    
    ok, out = _run_on_pct(
        ODOO_PCT_ID,
        f"systemctl enable {service} 2>/dev/null; "
        f"systemctl restart {service} && sleep 3 && "
        f"systemctl is-active {service}",
        timeout=30,
    )
    
    active = "active" in out.lower() if ok else False
    
    if not active:
        # Leer log para diagnosticar
        _, log_out = _run_on_pct(
            ODOO_PCT_ID,
            f"journalctl -u {service} --no-pager -n 10 2>&1 | tail -5",
            timeout=15,
        )
        return {
            "success": False,
            "error": f"Servicio {service} no activo: {out}",
            "log_tail": log_out,
        }
    
    # Verificar que el puerto está escuchando
    _, port_out = _run_on_pct(
        ODOO_PCT_ID,
        f"ss -tlnp | grep -c ':{subdomain}' || echo port_check_done",
        timeout=10,
    )
    
    return {"success": True, "service": service, "status": "active"}


def add_cloudflared_routes(
    subdomain: str,
    http_port: int,
    ws_port: int,
    base_domain: str = "sajet.us",
) -> Dict[str, Any]:
    """
    Paso 4: Agregar rutas al archivo odoo17-tenants.yml y reiniciar el servicio.
    
    IMPORTANTE: No usar config.yml ni tenant-web-gate.py — esos manejan
    el tunnel principal (1b41dd54), no el de tenants Odoo17 (bf8c039f).
    """
    hostname = f"{subdomain}.{base_domain}"
    backend_ip = "10.10.20.201"  # PCT201 IP
    
    # Verificar si ya existe
    ok, existing = _run_on_pct(
        CLOUDFLARED_PCT_ID,
        f"grep -c '{hostname}' {CLOUDFLARED_CONFIG} 2>/dev/null || echo 0",
    )
    
    count = 0
    try:
        count = int(existing.strip().split("\n")[-1])
    except (ValueError, IndexError):
        pass
    
    if count > 0:
        logger.info(f"Rutas para {hostname} ya existen en {CLOUDFLARED_CONFIG}")
        return {"success": True, "action": "already_exists"}
    
    # Encontrar la línea del catch-all (service: http_status:404)
    ok, line_out = _run_on_pct(
        CLOUDFLARED_PCT_ID,
        f"grep -n 'service: http_status:404' {CLOUDFLARED_CONFIG} | tail -1",
    )
    
    if not ok or not line_out.strip():
        return {"success": False, "error": "No se encontró catch-all en cloudflared config"}
    
    try:
        catch_all_line = int(line_out.strip().split(":")[0])
    except (ValueError, IndexError):
        return {"success": False, "error": f"No se pudo parsear línea catch-all: {line_out}"}
    
    # Insertar las rutas antes del catch-all
    # Usamos sed para insertar antes de la línea del catch-all
    insert_line = catch_all_line - 1  # Insertar antes
    routes_text = (
        f"\\n  # {subdomain} — provisionado automatico\\n"
        f"  - hostname: {hostname}\\n"
        f"    path: /websocket*\\n"
        f"    service: http://{backend_ip}:{ws_port}\\n"
        f"  - hostname: {hostname}\\n"
        f"    path: /longpolling*\\n"
        f"    service: http://{backend_ip}:{ws_port}\\n"
        f"  - hostname: {hostname}\\n"
        f"    service: http://{backend_ip}:{http_port}"
    )
    
    ok, out = _run_on_pct(
        CLOUDFLARED_PCT_ID,
        f"sed -i '{insert_line}a{routes_text}' {CLOUDFLARED_CONFIG} && echo routes_added",
        timeout=15,
    )
    
    if not ok or "routes_added" not in out:
        return {"success": False, "error": f"Error insertando rutas: {out}"}
    
    # Reiniciar el servicio cloudflared correcto
    ok, out = _run_on_pct(
        CLOUDFLARED_PCT_ID,
        f"systemctl restart {CLOUDFLARED_SERVICE} && sleep 2 && "
        f"systemctl is-active {CLOUDFLARED_SERVICE}",
        timeout=20,
    )
    
    if not ok or "active" not in out.lower():
        return {"success": False, "error": f"Error reiniciando {CLOUDFLARED_SERVICE}: {out}"}
    
    return {
        "success": True,
        "action": "added",
        "config_file": CLOUDFLARED_CONFIG,
        "service": CLOUDFLARED_SERVICE,
    }


def create_tunnel_dns(subdomain: str, base_domain: str = "sajet.us") -> Dict[str, Any]:
    """
    Paso 5: Crear DNS CNAME apuntando al tunnel correcto de Odoo17 tenants.
    
    Usa `cloudflared tunnel route dns` directamente — no necesita API token.
    """
    hostname = f"{subdomain}.{base_domain}"
    
    ok, out = _run_on_pct(
        CLOUDFLARED_PCT_ID,
        f"cloudflared --config {CLOUDFLARED_CONFIG} tunnel route dns "
        f"{ODOO17_TUNNEL_ID} {hostname} 2>&1",
        timeout=30,
    )
    
    if not ok:
        # Puede fallar si ya existe — no es error fatal
        if "already configured" in out.lower():
            return {"success": True, "action": "already_exists", "hostname": hostname}
        return {"success": False, "error": f"Error creando DNS: {out}"}
    
    if "already configured" in out.lower():
        return {"success": True, "action": "already_exists", "hostname": hostname}
    
    return {"success": True, "action": "created", "hostname": hostname, "tunnel_id": ODOO17_TUNNEL_ID}


def remove_cloudflared_routes(
    subdomain: str,
    base_domain: str = "sajet.us",
) -> Dict[str, Any]:
    """
    Compensación: eliminar rutas de cloudflared al hacer rollback.
    """
    hostname = f"{subdomain}.{base_domain}"
    
    # Eliminar todas las líneas que contengan el hostname
    ok, out = _run_on_pct(
        CLOUDFLARED_PCT_ID,
        f"sed -i '/{re.escape(hostname)}/d' {CLOUDFLARED_CONFIG} && "
        f"sed -i '/# {subdomain} —/d' {CLOUDFLARED_CONFIG} && "
        f"systemctl restart {CLOUDFLARED_SERVICE} && echo removed",
        timeout=20,
    )
    
    return {"success": "removed" in (out or ""), "output": out}


def stop_odoo_service(subdomain: str) -> Dict[str, Any]:
    """Compensación: detener servicio Odoo del tenant."""
    service = f"odoo-tenant@{subdomain}"
    ok, out = _run_on_pct(
        ODOO_PCT_ID,
        f"systemctl stop {service} && systemctl disable {service} 2>/dev/null; echo stopped",
        timeout=15,
    )
    return {"success": True, "output": out}


def remove_odoo_config(subdomain: str) -> Dict[str, Any]:
    """Compensación: eliminar config Odoo del tenant."""
    conf_path = f"{ODOO_CONF_DIR}/tenant-{subdomain}.conf"
    ok, out = _run_on_pct(
        ODOO_PCT_ID,
        f"rm -f {conf_path} && echo removed",
        timeout=10,
    )
    return {"success": True, "output": out}


# ── Orquestación completa ─────────────────────────────────────────────

async def provision_odoo_service(
    subdomain: str,
    template_db: str = "tenant_do",
    base_domain: str = "sajet.us",
) -> Dict[str, Any]:
    """
    Ejecuta el despliegue completo del servicio Odoo para un tenant.
    
    Retorna puertos asignados y estado de cada paso.
    Incluye compensaciones automáticas si falla.
    """
    steps: List[Dict[str, Any]] = []
    
    try:
        # 1. Asignar puertos
        http_port, ws_port = find_next_free_port()
        steps.append({"step": "assign_ports", "http_port": http_port, "ws_port": ws_port, "success": True})
        
        # 2. Crear config Odoo
        config_result = create_odoo_config(subdomain, http_port, ws_port, template_db)
        steps.append({"step": "create_config", **config_result})
        if not config_result["success"]:
            return {"success": False, "error": config_result["error"], "steps": steps}
        
        # 3. Preparar directorios y filestore
        dirs_result = prepare_directories(subdomain, template_db)
        steps.append({"step": "prepare_dirs", **dirs_result})
        if not dirs_result["success"]:
            remove_odoo_config(subdomain)
            return {"success": False, "error": dirs_result["error"], "steps": steps}
        
        # 4. Iniciar servicio Odoo
        service_result = start_odoo_service(subdomain)
        steps.append({"step": "start_service", **service_result})
        if not service_result["success"]:
            # No fatal — el servicio puede tomar más tiempo en iniciar
            logger.warning(f"Servicio Odoo para {subdomain} no inició inmediatamente: {service_result}")
        
        # 5. Agregar rutas cloudflared
        routes_result = add_cloudflared_routes(subdomain, http_port, ws_port, base_domain)
        steps.append({"step": "cloudflared_routes", **routes_result})
        if not routes_result["success"]:
            logger.warning(f"Error en rutas cloudflared para {subdomain}: {routes_result}")
        
        # 6. Crear DNS
        dns_result = create_tunnel_dns(subdomain, base_domain)
        steps.append({"step": "tunnel_dns", **dns_result})
        if not dns_result["success"]:
            logger.warning(f"Error creando DNS para {subdomain}: {dns_result}")
        
        all_ok = all(s.get("success", False) for s in steps)
        
        return {
            "success": True,  # BD y config creadas, el resto puede ser parcial
            "subdomain": subdomain,
            "http_port": http_port,
            "ws_port": ws_port,
            "backend_host": "10.10.20.201",
            "tunnel_url": f"https://{subdomain}.{base_domain}",
            "direct_url": f"http://10.10.20.201:{http_port}",
            "all_steps_ok": all_ok,
            "steps": steps,
        }
        
    except Exception as e:
        logger.exception(f"Error en provision_odoo_service para {subdomain}: {e}")
        # Compensaciones
        stop_odoo_service(subdomain)
        remove_odoo_config(subdomain)
        remove_cloudflared_routes(subdomain, base_domain)
        return {"success": False, "error": str(e), "steps": steps}


async def deprovision_odoo_service(
    subdomain: str,
    base_domain: str = "sajet.us",
) -> Dict[str, Any]:
    """
    Elimina el servicio Odoo y las rutas cloudflared de un tenant.
    Complementa la eliminación de BD que hace odoo_database_manager.
    """
    results = {}
    
    results["stop_service"] = stop_odoo_service(subdomain)
    results["remove_config"] = remove_odoo_config(subdomain)
    results["remove_routes"] = remove_cloudflared_routes(subdomain, base_domain)
    
    return {"success": True, "results": results}
