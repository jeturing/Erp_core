"""
cloudflare_tunnel_api — Gestiona ingress rules del tunnel vía Cloudflare API
(no edita config.yml local — ese archivo es ignorado cuando el tunnel usa
configuración remota desde Cloudflare Zero Trust).

Endpoints Cloudflare:
  GET /accounts/{acc}/cfd_tunnel/{tunnel}/configurations
  PUT /accounts/{acc}/cfd_tunnel/{tunnel}/configurations

Diseño:
  - add_tenant_routes(subdomain, http_port, ws_port) inserta 3 reglas (ws, lp, http)
    antes del fallback (último ingress sin hostname).
  - remove_tenant_routes(subdomain) elimina todas las reglas con hostname == subdomain.sajet.us
  - Idempotente: detecta duplicados.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from ..config import (
    CLOUDFLARE_TUNNEL_ID,
    get_runtime_setting,
)

logger = logging.getLogger(__name__)


def _account_id() -> str:
    return get_runtime_setting("CLOUDFLARE_ACCOUNT_ID", "")


def _tunnel_id() -> str:
    return get_runtime_setting("CLOUDFLARE_TUNNEL_ID", CLOUDFLARE_TUNNEL_ID)


def _api_token() -> str:
    return get_runtime_setting("CLOUDFLARE_API_TOKEN", "")


def _api_url() -> str:
    return (
        f"https://api.cloudflare.com/client/v4/accounts/{_account_id()}"
        f"/cfd_tunnel/{_tunnel_id()}/configurations"
    )


def _request(method: str, payload: Optional[dict] = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        _api_url(),
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {_api_token()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        logger.error("Cloudflare API HTTP %s: %s", e.code, body[:500])
        return {"success": False, "errors": [{"message": body[:500]}]}
    except Exception as e:
        logger.exception("Cloudflare API error")
        return {"success": False, "errors": [{"message": str(e)}]}


def _get_config() -> Dict[str, Any]:
    res = _request("GET")
    if not res.get("success"):
        raise RuntimeError(f"Cloudflare GET configurations failed: {res.get('errors')}")
    return res["result"]["config"]


def _put_config(config: dict) -> dict:
    return _request("PUT", {"config": config})


def add_tenant_routes(
    subdomain: str,
    *,
    node_ip: str,
    http_port: int,
    ws_port: int,
    base_domain: str = "sajet.us",
) -> Dict[str, Any]:
    """
    Añade 3 reglas ingress (websocket, longpolling, http) para `subdomain.base_domain`
    al config remoto del tunnel. Idempotente: si ya existen, no duplica.
    """
    hostname = f"{subdomain}.{base_domain}"
    new_rules = [
        {"hostname": hostname, "path": "/websocket*", "service": f"http://{node_ip}:{ws_port}"},
        {"hostname": hostname, "path": "/longpolling*", "service": f"http://{node_ip}:{ws_port}"},
        {"hostname": hostname, "service": f"http://{node_ip}:{http_port}"},
    ]

    try:
        config = _get_config()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}

    ingress: List[dict] = config.get("ingress", [])

    # Idempotencia: eliminar reglas previas con el mismo hostname
    ingress = [r for r in ingress if r.get("hostname") != hostname]

    # Insertar antes del fallback (última regla sin hostname)
    fallback_idx = next(
        (i for i, r in enumerate(ingress) if "hostname" not in r),
        len(ingress),
    )
    ingress[fallback_idx:fallback_idx] = new_rules
    config["ingress"] = ingress

    res = _put_config(config)
    if res.get("success"):
        logger.info("[tunnel-api] add %s → %d reglas (versión %s)",
                    hostname, len(new_rules), res.get("result", {}).get("version"))
        return {
            "success": True,
            "hostname": hostname,
            "rules_added": len(new_rules),
            "version": res["result"].get("version"),
        }
    return {"success": False, "error": res.get("errors")}


def remove_tenant_routes(
    subdomain: str,
    *,
    base_domain: str = "sajet.us",
) -> Dict[str, Any]:
    """Elimina todas las reglas ingress con hostname == subdomain.base_domain."""
    hostname = f"{subdomain}.{base_domain}"
    try:
        config = _get_config()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}

    before = len(config.get("ingress", []))
    config["ingress"] = [r for r in config.get("ingress", []) if r.get("hostname") != hostname]
    removed = before - len(config["ingress"])

    if removed == 0:
        return {"success": True, "hostname": hostname, "rules_removed": 0, "note": "no existía"}

    res = _put_config(config)
    if res.get("success"):
        logger.info("[tunnel-api] remove %s → %d reglas (versión %s)",
                    hostname, removed, res.get("result", {}).get("version"))
        return {
            "success": True,
            "hostname": hostname,
            "rules_removed": removed,
            "version": res["result"].get("version"),
        }
    return {"success": False, "error": res.get("errors")}


def list_tenant_routes() -> Dict[str, Any]:
    """Devuelve todas las reglas ingress actuales."""
    try:
        config = _get_config()
    except RuntimeError as e:
        return {"success": False, "error": str(e)}
    return {"success": True, "ingress": config.get("ingress", [])}
