"""
NPM Proxy Manager — Integración directa con Nginx Proxy Manager.

NPM REST API: http://10.10.20.205:81/api  (PCT 205, red interna)
Autenticación: JWT por email/contraseña (POST /api/tokens).

También admite llamadas vía sidecar (http://10.10.20.205:8888) si
NPM_USE_SIDECAR=true, pero el modo directo es el default ya que el
sidecar usa credenciales de Docker interno (`npm:81`) que pueden fallar.

Config (via system_config o .env):
  NPM_API_URL        → http://10.10.20.205:81/api  (NPM API directo)
  NPM_ADMIN_EMAIL    → soc@jeturing.com
  NPM_ADMIN_PASSWORD → required for direct NPM auth
  NPM_SIDECAR_URL    → http://10.10.20.205:8888    (sidecar, opcional)
  NPM_ADMIN_API_KEY  → jt_api_...                  (key del sidecar)
  NPM_ODOO17_FORWARD_PORT → 80                     (puerto Odoo en PCT 201)

Operaciones:
  - create_tenant_proxy_host()            → {subdomain}.sajet.us → PCT 201
  - create_custom_domain_proxy_host()     → dominio externo → PCT 201
  - delete_proxy_host_by_domain()         → elimina por nombre de dominio
  - delete_tenant_proxy_hosts()           → elimina proxy de tenant completo
  - list_proxy_hosts()                    → lista todos los proxy hosts
  - npm_health()                          → verifica conectividad
"""

import logging
import httpx
from typing import Optional

from ..config import get_runtime_setting

logger = logging.getLogger(__name__)

# ── Config helpers ──────────────────────────────────────────────────────────

def _npm_use_sidecar() -> bool:
    """Si true, usa la API sidecar de PCT 205 (recomendado)."""
    return str(get_runtime_setting("NPM_USE_SIDECAR", "true")).lower() == "true"

def _npm_api_url() -> str:
    """URL base de la API de NPM (modo directo)."""
    return get_runtime_setting("NPM_API_URL", "http://10.10.20.205:81/api")


def _npm_admin_email() -> str:
    return get_runtime_setting("NPM_ADMIN_EMAIL", "soc@jeturing.com")


def _npm_admin_password() -> str:
    return get_runtime_setting("NPM_ADMIN_PASSWORD", "")


def _npm_sidecar_url() -> str:
    return get_runtime_setting("NPM_SIDECAR_URL", "http://100.99.42.18:8888")


def _npm_admin_api_key() -> str:
    return get_runtime_setting("NPM_ADMIN_API_KEY", "")


def _sidecar_headers() -> dict:
    """Headers para API sidecar (admite X-API-Key/Bearer)."""
    key = _npm_admin_api_key().strip()
    if not key:
        return {}
    return {
        "X-API-Key": key,
        "Authorization": f"Bearer {key}",
    }


def _sidecar_path(path: str) -> str:
    """Mapea rutas NPM nativas a rutas del sidecar."""
    if path.startswith("/nginx/proxy-hosts"):
        mapped = path.replace("/nginx/proxy-hosts", "/proxy-hosts", 1)
        # FastAPI redirects collection routes without trailing slash. httpx does
        # not follow redirects by default, and POST redirects lose the request in
        # some clients, so call the canonical sidecar route directly.
        return "/proxy-hosts/" if mapped == "/proxy-hosts" else mapped
    return path


def _npm_odoo17_host() -> str:
    """IP del servidor Odoo 17 (PCT 201) para forward_host."""
    return get_runtime_setting("ODOO_PRIMARY_IP", "10.10.20.201")


def _npm_odoo17_port() -> int:
    try:
        return int(get_runtime_setting("NPM_ODOO17_FORWARD_PORT", "80"))
    except (ValueError, TypeError):
        return 80


# ── JWT token cache (en memoria, por proceso) ────────────────────────────────

_npm_jwt_token: Optional[str] = None


async def _get_npm_token(force_refresh: bool = False) -> str:
    """Obtiene o refresca el JWT token de NPM."""
    if _npm_use_sidecar():
        # En sidecar no se requiere JWT /tokens.
        return "sidecar-mode"

    global _npm_jwt_token
    if _npm_jwt_token and not force_refresh:
        return _npm_jwt_token or ""

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{_npm_api_url()}/tokens",
            json={"identity": _npm_admin_email(), "secret": _npm_admin_password()},
        )
        resp.raise_for_status()
        _npm_jwt_token = resp.json().get("token")
        return _npm_jwt_token or ""


def _get_npm_token_sync(force_refresh: bool = False) -> str:
    """Versión síncrona de _get_npm_token."""
    if _npm_use_sidecar():
        return "sidecar-mode"

    global _npm_jwt_token
    if _npm_jwt_token and not force_refresh:
        return _npm_jwt_token or ""

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(
            f"{_npm_api_url()}/tokens",
            json={"identity": _npm_admin_email(), "secret": _npm_admin_password()},
        )
        resp.raise_for_status()
        _npm_jwt_token = resp.json().get("token")
        return _npm_jwt_token or ""


# ── Cliente HTTP (async) ────────────────────────────────────────────────────

async def _npm_request(method: str, path: str, **kwargs) -> dict | list:
    """Request autenticado a la API de NPM con reintento si el token expira."""
    if _npm_use_sidecar():
        mapped = _sidecar_path(path)
        headers = _sidecar_headers()
        if "headers" in kwargs and isinstance(kwargs["headers"], dict):
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.request(method, f"{_npm_sidecar_url()}{mapped}", **kwargs)
                resp.raise_for_status()
                return resp.json() if resp.content else {}
        except Exception as exc:
            logger.warning(f"NPM sidecar no disponible, fallback a API directa: {exc}")

    token = await _get_npm_token()
    extra_headers = kwargs.pop("headers", {}) if isinstance(kwargs.get("headers"), dict) else {}
    headers = {"Authorization": f"Bearer {token}", **extra_headers}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(method, f"{_npm_api_url()}{path}", headers=headers, **kwargs)
        if resp.status_code == 401:
            # Token expirado → refresca y reintenta
            token = await _get_npm_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            resp = await client.request(method, f"{_npm_api_url()}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}


# ── Cliente HTTP (síncrono) ─────────────────────────────────────────────────

def _npm_request_sync(method: str, path: str, **kwargs) -> dict | list:
    """Request síncrono autenticado a la API de NPM."""
    if _npm_use_sidecar():
        mapped = _sidecar_path(path)
        headers = _sidecar_headers()
        if "headers" in kwargs and isinstance(kwargs["headers"], dict):
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.request(method, f"{_npm_sidecar_url()}{mapped}", **kwargs)
                resp.raise_for_status()
                return resp.json() if resp.content else {}
        except Exception as exc:
            logger.warning(f"NPM sidecar no disponible (sync), fallback a API directa: {exc}")

    token = _get_npm_token_sync()
    extra_headers = kwargs.pop("headers", {}) if isinstance(kwargs.get("headers"), dict) else {}
    headers = {"Authorization": f"Bearer {token}", **extra_headers}

    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, f"{_npm_api_url()}{path}", headers=headers, **kwargs)
        if resp.status_code == 401:
            token = _get_npm_token_sync(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            resp = client.request(method, f"{_npm_api_url()}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}


# ── Operaciones de alto nivel (async) ──────────────────────────────────────

async def list_proxy_hosts() -> list[dict]:
    """Lista todos los proxy hosts registrados en NPM."""
    try:
        result = await _npm_request("GET", "/nginx/proxy-hosts")
        return result if isinstance(result, list) else []
    except Exception as exc:
        logger.warning(f"NPM list_proxy_hosts falló: {exc}")
        return []


async def find_proxy_host_by_domain(domain: str) -> Optional[dict]:
    """Busca un proxy host existente por nombre de dominio."""
    hosts = await list_proxy_hosts()
    domain_lower = domain.lower()
    for host in hosts:
        if domain_lower in [d.lower() for d in host.get("domain_names", [])]:
            return host
    return None


async def create_tenant_proxy_host(
    subdomain: str,
    base_domain: str = "sajet.us",
    forward_host: Optional[str] = None,
    forward_port: Optional[int] = None,
    ssl_forced: bool = False,
    allow_websocket_upgrade: bool = True,
) -> dict:
    """
    Crea un proxy host en NPM para un nuevo tenant.

    Crea la entrada: {subdomain}.{base_domain} → forward_host:forward_port

    Args:
        subdomain: nombre del tenant (ej: "acme")
        base_domain: dominio raíz (default: "sajet.us")
        forward_host: IP del backend Odoo (default: ODOO_PRIMARY_IP)
        forward_port: puerto del backend (default: NPM_ODOO17_FORWARD_PORT=80)
    """
    domain = f"{subdomain}.{base_domain}"
    forward_host = forward_host or _npm_odoo17_host()
    forward_port = forward_port or _npm_odoo17_port()

    try:
        existing = await find_proxy_host_by_domain(domain)
        if existing:
            logger.info(f"NPM: proxy host ya existe para {domain} (id={existing.get('id')})")
            return {
                "success": True,
                "npm_host_id": existing.get("id"),
                "domain": domain,
                "already_existed": True,
                "message": f"Proxy host ya existía para {domain}",
            }

        payload = {
            "domain_names": [domain],
            "forward_scheme": "http",
            "forward_host": forward_host,
            "forward_port": forward_port,
            "ssl_forced": ssl_forced,
            "block_exploits": True,
            "allow_websocket_upgrade": allow_websocket_upgrade,
            "caching_enabled": False,
            "access_list_id": 0,
            "advanced_config": "",
            "meta": {
                "tenant": subdomain,
                "base_domain": base_domain,
                "role": "odoo17-tenant",
                "provisioned_by": "sajet-erp",
            },
        }

        result = await _npm_request("POST", "/nginx/proxy-hosts", json=payload)
        host_id = result.get("id") if isinstance(result, dict) else None

        logger.info(f"✅ NPM: proxy host creado para {domain} (id={host_id})")
        return {
            "success": True,
            "npm_host_id": host_id,
            "domain": domain,
            "forward_to": f"{forward_host}:{forward_port}",
            "message": f"Proxy host creado en NPM: {domain}",
        }

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response else str(exc)
        logger.error(f"NPM create_tenant_proxy_host HTTP error para {domain}: {exc.response.status_code} — {detail}")
        return {"success": False, "domain": domain, "error": f"HTTP {exc.response.status_code}: {detail}"}
    except Exception as exc:
        logger.error(f"NPM create_tenant_proxy_host falló para {domain}: {exc}")
        return {"success": False, "domain": domain, "error": str(exc)}


async def create_custom_domain_proxy_host(
    external_domain: str,
    forward_host: Optional[str] = None,
    forward_port: Optional[int] = None,
    tenant_subdomain: Optional[str] = None,
    ssl_forced: bool = False,
    allow_websocket_upgrade: bool = True,
) -> dict:
    """
    Crea un proxy host en NPM para un dominio externo del cliente.
    Crea entradas para dominio y www.dominio.
    """
    forward_host = forward_host or _npm_odoo17_host()
    forward_port = forward_port or _npm_odoo17_port()

    domain = external_domain.lower().lstrip("www.").strip(".")
    domain_names = [domain, f"www.{domain}"]

    try:
        for d in domain_names:
            existing = await find_proxy_host_by_domain(d)
            if existing:
                logger.info(f"NPM: proxy host ya existe para {d} (id={existing.get('id')})")
                return {
                    "success": True,
                    "npm_host_id": existing.get("id"),
                    "domain": domain,
                    "domain_names": domain_names,
                    "already_existed": True,
                    "message": f"Proxy host ya existía para {d}",
                }

        payload = {
            "domain_names": domain_names,
            "forward_scheme": "http",
            "forward_host": forward_host,
            "forward_port": forward_port,
            "ssl_forced": ssl_forced,
            "block_exploits": True,
            "allow_websocket_upgrade": allow_websocket_upgrade,
            "caching_enabled": False,
            "access_list_id": 0,
            "advanced_config": "",
            "meta": {
                "tenant": tenant_subdomain or "",
                "external_domain": domain,
                "role": "odoo17-custom-domain",
                "provisioned_by": "sajet-erp",
            },
        }

        result = await _npm_request("POST", "/nginx/proxy-hosts", json=payload)
        host_id = result.get("id") if isinstance(result, dict) else None

        logger.info(f"✅ NPM: proxy host de dominio externo creado para {domain} (id={host_id})")
        return {
            "success": True,
            "npm_host_id": host_id,
            "domain": domain,
            "domain_names": domain_names,
            "forward_to": f"{forward_host}:{forward_port}",
            "message": f"Proxy host creado en NPM: {', '.join(domain_names)}",
        }

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response else str(exc)
        logger.error(f"NPM create_custom_domain_proxy_host HTTP error para {domain}: {exc.response.status_code} — {detail}")
        return {"success": False, "domain": domain, "error": f"HTTP {exc.response.status_code}: {detail}"}
    except Exception as exc:
        logger.error(f"NPM create_custom_domain_proxy_host falló para {domain}: {exc}")
        return {"success": False, "domain": domain, "error": str(exc)}


async def delete_proxy_host_by_domain(domain: str) -> dict:
    """Elimina el proxy host de NPM correspondiente a un dominio."""
    try:
        domain_lower = domain.lower()
        host = await find_proxy_host_by_domain(domain_lower)
        if not host:
            www = f"www.{domain_lower}" if not domain_lower.startswith("www.") else domain_lower
            host = await find_proxy_host_by_domain(www)

        if not host:
            return {
                "success": True,
                "domain": domain,
                "deleted": False,
                "message": "Proxy host no encontrado en NPM (ya eliminado)",
            }

        host_id = host.get("id")
        await _npm_request("DELETE", f"/nginx/proxy-hosts/{host_id}")

        logger.info(f"✅ NPM: proxy host eliminado para {domain} (id={host_id})")
        return {
            "success": True,
            "npm_host_id": host_id,
            "domain": domain,
            "deleted": True,
            "message": f"Proxy host {host_id} eliminado de NPM",
        }

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response else str(exc)
        logger.error(f"NPM delete_proxy_host_by_domain HTTP error para {domain}: {exc.response.status_code} — {detail}")
        return {"success": False, "domain": domain, "error": f"HTTP {exc.response.status_code}: {detail}"}
    except Exception as exc:
        logger.error(f"NPM delete_proxy_host_by_domain falló para {domain}: {exc}")
        return {"success": False, "domain": domain, "error": str(exc)}


async def delete_tenant_proxy_hosts(subdomain: str, base_domain: str = "sajet.us") -> dict:
    """Elimina los proxy hosts de NPM para un tenant."""
    domain = f"{subdomain}.{base_domain}"
    return await delete_proxy_host_by_domain(domain)


async def npm_health() -> dict:
    """Verifica conectividad con NPM."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if _npm_use_sidecar():
                resp = await client.get(f"{_npm_sidecar_url()}/")
            else:
                resp = await client.get(f"{_npm_api_url().replace('/api', '')}/")
        return {"reachable": resp.status_code in (200, 301, 302, 307), "status_code": resp.status_code}
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}


# ── Variantes síncronas (para domain_manager y otros contextos síncronos) ─────

def _list_proxy_hosts_sync() -> list[dict]:
    try:
        result = _npm_request_sync("GET", "/nginx/proxy-hosts")
        return result if isinstance(result, list) else []
    except Exception as exc:
        logger.warning(f"NPM sync list_proxy_hosts falló: {exc}")
        return []


def create_custom_domain_proxy_host_sync(
    external_domain: str,
    forward_host: Optional[str] = None,
    forward_port: Optional[int] = None,
    tenant_subdomain: Optional[str] = None,
    ssl_forced: bool = False,
    allow_websocket_upgrade: bool = True,
) -> dict:
    """
    Versión síncrona de create_custom_domain_proxy_host.
    Para uso desde domain_manager.py (contexto síncrono).
    """
    forward_host = forward_host or _npm_odoo17_host()
    forward_port = forward_port or _npm_odoo17_port()

    domain = external_domain.lower().lstrip("www.").strip(".")
    domain_names = [domain, f"www.{domain}"]

    try:
        hosts = _list_proxy_hosts_sync()
        for host in hosts:
            if any(d.lower() in domain_names for d in host.get("domain_names", [])):
                logger.info(f"NPM sync: proxy host ya existe para {domain} (id={host.get('id')})")
                return {
                    "success": True,
                    "npm_host_id": host.get("id"),
                    "domain": domain,
                    "already_existed": True,
                    "message": f"Proxy host ya existía para {domain}",
                }

        payload = {
            "domain_names": domain_names,
            "forward_scheme": "http",
            "forward_host": forward_host,
            "forward_port": forward_port,
            "ssl_forced": ssl_forced,
            "block_exploits": True,
            "allow_websocket_upgrade": allow_websocket_upgrade,
            "caching_enabled": False,
            "access_list_id": 0,
            "advanced_config": "",
            "meta": {
                "tenant": tenant_subdomain or "",
                "external_domain": domain,
                "role": "odoo17-custom-domain",
                "provisioned_by": "sajet-erp",
            },
        }

        result = _npm_request_sync("POST", "/nginx/proxy-hosts", json=payload)
        host_id = result.get("id") if isinstance(result, dict) else None
        logger.info(f"✅ NPM sync: proxy host creado para {domain} (id={host_id})")
        return {
            "success": True,
            "npm_host_id": host_id,
            "domain": domain,
            "domain_names": domain_names,
            "forward_to": f"{forward_host}:{forward_port}",
            "message": f"Proxy host creado en NPM: {', '.join(domain_names)}",
        }

    except Exception as exc:
        logger.warning(f"NPM sync create_custom_domain falló para {domain} (no bloquea): {exc}")
        return {"success": False, "domain": domain, "error": str(exc)}


def delete_proxy_host_by_domain_sync(domain: str) -> dict:
    """
    Versión síncrona de delete_proxy_host_by_domain.
    Para uso desde domain_manager.py (contexto síncrono).
    """
    try:
        hosts = _list_proxy_hosts_sync()
        domain_lower = domain.lower().lstrip("www.").strip(".")
        target = None
        for host in hosts:
            if any(d.lower().lstrip("www.").strip(".") == domain_lower for d in host.get("domain_names", [])):
                target = host
                break

        if not target:
            return {
                "success": True,
                "domain": domain,
                "deleted": False,
                "message": "Proxy host no encontrado en NPM",
            }

        host_id = target.get("id")
        _npm_request_sync("DELETE", f"/nginx/proxy-hosts/{host_id}")
        logger.info(f"✅ NPM sync: proxy host eliminado para {domain} (id={host_id})")
        return {
            "success": True,
            "npm_host_id": host_id,
            "domain": domain,
            "deleted": True,
            "message": f"Proxy host {host_id} eliminado de NPM",
        }

    except Exception as exc:
        logger.warning(f"NPM sync delete falló para {domain} (no bloquea): {exc}")
        return {"success": False, "domain": domain, "error": str(exc)}
