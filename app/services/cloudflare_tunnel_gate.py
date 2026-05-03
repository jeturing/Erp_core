"""
cloudflare_tunnel_gate — Bloquea/desbloquea el acceso web público a un tenant
manipulando la config de cloudflared en PCT 205 vía SSH+pct exec.

Esto NO afecta el servicio Odoo en PCT 201 ni la base de datos. Solo cambia
el upstream del tunnel a `http_status:503` (bloquear) o restaura la URL
original (desbloquear), preservada como comentario `# original-service:`
por el script remoto `/usr/local/bin/tenant-web-gate.py`.

Uso desde código:
    from app.services.cloudflare_tunnel_gate import set_web_access, get_web_access_status
    res = set_web_access("flujoeletronic", blocked=True, reason="Suspendido manual")
    res = set_web_access("flujoeletronic", blocked=False)
    st  = get_web_access_status("flujoeletronic")
"""
from __future__ import annotations

import json
import logging
import os
import shlex
import shutil
import subprocess
from typing import Any, Dict, List, Optional

from ..config import (
    PROXMOX_SSH_HOST,
    PROXMOX_SSH_KEY,
    PROXMOX_SSH_USER,
)

logger = logging.getLogger(__name__)

SSH_BIN = shutil.which("ssh") or "/usr/bin/ssh"
SUDO_BIN = shutil.which("sudo") or "/usr/bin/sudo"
PROXMOX_ADMIN_HELPER = os.getenv("PROXMOX_ADMIN_HELPER", "/usr/local/bin/sajet-proxmox-admin")

# PCT del NPM/cloudflared sidecar
NPM_PCT_ID = int(os.getenv("NPM_PCT_ID", "205"))
GATE_SCRIPT = "/usr/local/bin/tenant-web-gate.py"


def _should_use_proxmox_helper() -> bool:
    return (
        os.geteuid() != 0
        and os.path.exists(PROXMOX_ADMIN_HELPER)
        and (
            not PROXMOX_SSH_KEY
            or not os.path.exists(PROXMOX_SSH_KEY)
            or not os.access(PROXMOX_SSH_KEY, os.R_OK)
        )
    )


def _build_pct_exec_cmd(remote_cmd: str) -> List[str]:
    if _should_use_proxmox_helper():
        return [SUDO_BIN, "-n", PROXMOX_ADMIN_HELPER, "pct-exec", str(NPM_PCT_ID), remote_cmd]
    full_remote = shlex.join(["pct", "exec", str(NPM_PCT_ID), "--", *shlex.split(remote_cmd)])
    return [
        SSH_BIN, "-i", PROXMOX_SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "IdentitiesOnly=yes",
        "-o", "ConnectTimeout=10",
        f"{PROXMOX_SSH_USER}@{PROXMOX_SSH_HOST}",
        full_remote,
    ]


def _run_gate(action: str, *args: str, timeout: int = 30) -> Dict[str, Any]:
    """Invoca tenant-web-gate.py en PCT 205 y devuelve su JSON."""
    quoted = " ".join(shlex.quote(a) for a in args)
    remote_cmd = f"{GATE_SCRIPT} {action} {quoted}".strip()
    cmd = _build_pct_exec_cmd(remote_cmd)
    logger.info(f"[tunnel-gate] {action} {args}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0 and not r.stdout.strip():
            return {
                "success": False,
                "error": f"gate exit {r.returncode}: {r.stderr.strip() or 'sin salida'}",
            }
        try:
            stdout = r.stdout.strip()
            # El gate imprime JSON; tomar desde el primer '{' hasta el final del primer objeto válido
            start = stdout.find("{")
            payload = json.loads(stdout[start:]) if start >= 0 else json.loads(stdout)
        except (json.JSONDecodeError, IndexError):
            return {
                "success": False,
                "error": f"respuesta no JSON: {r.stdout[-300:]}",
                "stderr": r.stderr[-200:],
            }
        if r.returncode != 0 and "success" not in payload:
            payload["success"] = False
        return payload
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"timeout {timeout}s ejecutando gate"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─── API pública ────────────────────────────────────────────────────

def get_web_access_status(subdomain: str) -> Dict[str, Any]:
    """Retorna {found, blocked, entries[]} para el subdominio."""
    return _run_gate("status", subdomain, timeout=15)


def list_blocked_tenants() -> Dict[str, Any]:
    """Retorna {blocked: [hostnames], total}."""
    return _run_gate("list", timeout=15)


def set_web_access(subdomain: str, *, blocked: bool, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Bloquea o desbloquea el acceso web público al tenant.
    - blocked=True  → cloudflared devuelve HTTP 503 directamente desde el edge
    - blocked=False → restaura el upstream original (preservado en marker)
    
    No afecta el servicio Odoo, BD ni usuarios. Solo controla el tunnel público.
    """
    if blocked:
        args = [subdomain]
        if reason:
            args.extend(["--reason", reason])
        return _run_gate("block", *args, timeout=30)
    return _run_gate("unblock", subdomain, timeout=30)


def add_tenant_route(
    subdomain: str,
    *,
    node_ip: str,
    http_port: int = 8080,
    chat_port: int = 8072,
    base_domain: str = "sajet.us",
) -> Dict[str, Any]:
    """
    Añade entries HTTP + websocket/longpolling al cloudflared/config.yml para un tenant nuevo.
    Idempotente: si el hostname ya existe, no duplica. Reinicia cloudflared al final.
    """
    return _run_gate(
        "add",
        subdomain,
        "--node-ip", str(node_ip),
        "--http-port", str(http_port),
        "--chat-port", str(chat_port),
        "--base-domain", base_domain,
        timeout=45,
    )


def remove_tenant_route(subdomain: str, *, base_domain: str = "sajet.us") -> Dict[str, Any]:
    """Elimina TODOS los entries (http + ws + lp) del tenant en cloudflared/config.yml."""
    return _run_gate(
        "remove",
        subdomain,
        "--base-domain", base_domain,
        timeout=45,
    )
