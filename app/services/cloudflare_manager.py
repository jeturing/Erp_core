"""
Cloudflare Tunnel Manager — REST API Integration
Gestiona tunnels, DNS y conexiones vía Cloudflare API v4.
NO depende de cloudflared CLI; usa httpx async para todas las operaciones.
"""
import logging
import json
import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import (
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_ZONE_ID,
    CLOUDFLARE_ZONES,
)

logger = logging.getLogger(__name__)

CF_API_BASE = "https://api.cloudflare.com/client/v4"


class CloudflareManager:
    """Gestiona Cloudflare Tunnels mediante la API REST v4"""

    # ─── Headers ────────────────────────────────────────
    @classmethod
    def _headers(cls) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json",
        }

    @classmethod
    def _account_id(cls) -> str:
        return CLOUDFLARE_ACCOUNT_ID

    @classmethod
    def _zone_id(cls, domain: str = "sajet.us") -> str:
        """Retorna zone_id para el dominio dado."""
        if CLOUDFLARE_ZONES.get(domain):
            return CLOUDFLARE_ZONES[domain]
        return CLOUDFLARE_ZONE_ID

    # ─── Listar todos los tunnels ───────────────────────
    @classmethod
    async def list_tunnels(
        cls,
        include_deleted: bool = False,
        name_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Lista todos los Cloudflare Tunnels de la cuenta vía REST API.
        GET /accounts/{account_id}/cfd_tunnel
        """
        account_id = cls._account_id()
        if not account_id or not CLOUDFLARE_API_TOKEN:
            return {
                "success": False,
                "tunnels": [],
                "error": "Cloudflare API no configurada. Defina CLOUDFLARE_API_TOKEN y CLOUDFLARE_ACCOUNT_ID.",
            }

        try:
            params: Dict[str, Any] = {"per_page": 100}
            if not include_deleted:
                params["is_deleted"] = "false"
            if name_filter:
                params["name"] = name_filter

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel",
                    headers=cls._headers(),
                    params=params,
                )
                data = resp.json()

            if not data.get("success"):
                errors = data.get("errors", [])
                msg = errors[0].get("message") if errors else "Error desconocido"
                return {"success": False, "tunnels": [], "error": msg}

            tunnels: List[Dict[str, Any]] = []
            for t in data.get("result", []):
                conns = t.get("connections", [])
                active_conns = [c for c in conns if c.get("is_pending_reconnect") is not True]
                if active_conns:
                    status = "healthy"
                elif t.get("deleted_at"):
                    status = "deleted"
                elif conns:
                    status = "down"
                else:
                    status = "inactive"

                tunnels.append({
                    "id": t["id"],
                    "name": t.get("name", ""),
                    "status": status,
                    "created_at": t.get("created_at", ""),
                    "connections_count": len(active_conns),
                    "connections": [
                        {
                            "colo_name": c.get("colo_name", ""),
                            "is_pending_reconnect": c.get("is_pending_reconnect", False),
                            "origin_ip": c.get("origin_ip", ""),
                            "opened_at": c.get("opened_at", ""),
                        }
                        for c in conns
                    ],
                    "tunnel_type": t.get("tun_type", "cfd_tunnel"),
                    "remote_config": t.get("remote_config", False),
                })

            return {
                "success": True,
                "tunnels": tunnels,
                "total": len(tunnels),
            }

        except httpx.TimeoutException:
            logger.error("Timeout listando tunnels vía Cloudflare API")
            return {"success": False, "tunnels": [], "error": "Timeout en Cloudflare API"}
        except Exception as e:
            logger.exception(f"Error listando tunnels: {e}")
            return {"success": False, "tunnels": [], "error": str(e)}

    # ─── Obtener tunnel específico ──────────────────────
    @classmethod
    async def get_tunnel(cls, tunnel_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles de un tunnel específico.
        GET /accounts/{account_id}/cfd_tunnel/{tunnel_id}
        """
        account_id = cls._account_id()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel/{tunnel_id}",
                    headers=cls._headers(),
                )
                data = resp.json()

            if not data.get("success"):
                errors = data.get("errors", [])
                msg = errors[0].get("message") if errors else "Tunnel no encontrado"
                return {"success": False, "error": msg}

            t = data["result"]
            conns = t.get("connections", [])
            active_conns = [c for c in conns if c.get("is_pending_reconnect") is not True]

            return {
                "success": True,
                "tunnel": {
                    "id": t["id"],
                    "name": t.get("name", ""),
                    "status": "healthy" if active_conns else ("down" if conns else "inactive"),
                    "created_at": t.get("created_at", ""),
                    "connections_count": len(active_conns),
                    "connections": [
                        {
                            "colo_name": c.get("colo_name", ""),
                            "is_pending_reconnect": c.get("is_pending_reconnect", False),
                            "origin_ip": c.get("origin_ip", ""),
                            "opened_at": c.get("opened_at", ""),
                        }
                        for c in conns
                    ],
                    "tunnel_type": t.get("tun_type", "cfd_tunnel"),
                    "remote_config": t.get("remote_config", False),
                },
            }
        except Exception as e:
            logger.exception(f"Error obteniendo tunnel {tunnel_id}: {e}")
            return {"success": False, "error": str(e)}

    # ─── Obtener configuración de un tunnel ─────────────
    @classmethod
    async def get_tunnel_config(cls, tunnel_id: str) -> Dict[str, Any]:
        """
        Obtiene la configuración (ingress rules) de un tunnel.
        GET /accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations
        """
        account_id = cls._account_id()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations",
                    headers=cls._headers(),
                )
                data = resp.json()

            if not data.get("success"):
                return {"success": False, "error": "No se pudo obtener configuración"}

            config = data.get("result", {}).get("config", {})
            ingress_rules = config.get("ingress", [])

            hostnames = [
                {
                    "hostname": rule.get("hostname", "*"),
                    "service": rule.get("service", ""),
                    "path": rule.get("path", ""),
                }
                for rule in ingress_rules
            ]

            return {
                "success": True,
                "tunnel_id": tunnel_id,
                "ingress": hostnames,
                "total_rules": len(ingress_rules),
            }
        except Exception as e:
            logger.exception(f"Error obteniendo config tunnel {tunnel_id}: {e}")
            return {"success": False, "error": str(e)}

    # ─── Obtener conexiones activas ─────────────────────
    @classmethod
    async def get_tunnel_connections(cls, tunnel_id: str) -> Dict[str, Any]:
        """
        Obtiene las conexiones activas de un tunnel.
        GET /accounts/{account_id}/cfd_tunnel/{tunnel_id}/connections
        """
        account_id = cls._account_id()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/connections",
                    headers=cls._headers(),
                )
                data = resp.json()

            if not data.get("success"):
                return {"success": False, "connections": [], "error": "Error obteniendo conexiones"}

            connections = [
                {
                    "id": c.get("id", ""),
                    "colo_name": c.get("colo_name", ""),
                    "is_pending_reconnect": c.get("is_pending_reconnect", False),
                    "origin_ip": c.get("origin_ip", ""),
                    "opened_at": c.get("opened_at", ""),
                    "client_id": c.get("client_id", ""),
                    "client_version": c.get("client_version", ""),
                }
                for c in data.get("result", [])
            ]

            return {
                "success": True,
                "tunnel_id": tunnel_id,
                "connections": connections,
                "total": len(connections),
            }
        except Exception as e:
            logger.exception(f"Error obteniendo conexiones {tunnel_id}: {e}")
            return {"success": False, "connections": [], "error": str(e)}

    # ─── Crear tunnel ───────────────────────────────────
    @classmethod
    async def create_tunnel(
        cls,
        name: str,
        tunnel_secret: Optional[str] = None,
        config_src: str = "cloudflare",
    ) -> Dict[str, Any]:
        """
        Crea un nuevo Cloudflare Tunnel vía API.
        POST /accounts/{account_id}/cfd_tunnel
        """
        account_id = cls._account_id()
        if not account_id:
            return {"success": False, "error": "CLOUDFLARE_ACCOUNT_ID no configurado"}

        import secrets as _secrets

        body: Dict[str, Any] = {
            "name": name,
            "tunnel_secret": tunnel_secret or _secrets.token_urlsafe(32),
            "config_src": config_src,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel",
                    headers=cls._headers(),
                    json=body,
                )
                data = resp.json()

            if not data.get("success"):
                errors = data.get("errors", [])
                msg = errors[0].get("message") if errors else "Error creando tunnel"
                return {"success": False, "error": msg}

            t = data["result"]
            return {
                "success": True,
                "tunnel": {
                    "id": t["id"],
                    "name": t.get("name", ""),
                    "created_at": t.get("created_at", ""),
                    "token": t.get("token", ""),
                },
            }
        except Exception as e:
            logger.exception(f"Error creando tunnel {name}: {e}")
            return {"success": False, "error": str(e)}

    # ─── Eliminar tunnel ────────────────────────────────
    @classmethod
    async def delete_tunnel(cls, tunnel_id: str) -> Dict[str, Any]:
        """
        Elimina un Cloudflare Tunnel vía API.
        DELETE /accounts/{account_id}/cfd_tunnel/{tunnel_id}
        """
        account_id = cls._account_id()
        try:
            # Primero limpiar conexiones activas
            await cls.clean_tunnel_connections(tunnel_id)

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.delete(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel/{tunnel_id}",
                    headers=cls._headers(),
                )
                data = resp.json()

            if not data.get("success"):
                errors = data.get("errors", [])
                msg = errors[0].get("message") if errors else "Error eliminando tunnel"
                return {"success": False, "error": msg}

            return {"success": True, "message": f"Tunnel {tunnel_id} eliminado"}
        except Exception as e:
            logger.exception(f"Error eliminando tunnel {tunnel_id}: {e}")
            return {"success": False, "error": str(e)}

    # ─── Limpiar conexiones de un tunnel ────────────────
    @classmethod
    async def clean_tunnel_connections(cls, tunnel_id: str) -> Dict[str, Any]:
        """
        Limpia todas las conexiones activas de un tunnel.
        DELETE /accounts/{account_id}/cfd_tunnel/{tunnel_id}/connections
        """
        account_id = cls._account_id()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.delete(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/connections",
                    headers=cls._headers(),
                )
                data = resp.json()
            return {"success": data.get("success", False)}
        except Exception as e:
            logger.warning(f"Error limpiando conexiones tunnel {tunnel_id}: {e}")
            return {"success": False, "error": str(e)}

    # ─── Obtener token de un tunnel ─────────────────────
    @classmethod
    async def get_tunnel_token(cls, tunnel_id: str) -> Dict[str, Any]:
        """
        Obtiene el token de instalación de un tunnel.
        GET /accounts/{account_id}/cfd_tunnel/{tunnel_id}/token
        """
        account_id = cls._account_id()
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token",
                    headers=cls._headers(),
                )
                data = resp.json()

            if not data.get("success"):
                return {"success": False, "error": "No se pudo obtener token"}

            return {"success": True, "token": data.get("result", "")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── DNS: Listar registros de una zona ──────────────
    @classmethod
    async def list_dns_records(
        cls,
        domain: str = "sajet.us",
        record_type: Optional[str] = None,
        name_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Lista registros DNS de una zona."""
        zone_id = cls._zone_id(domain)
        if not zone_id:
            return {"success": False, "records": [], "error": f"Zone ID no encontrado para {domain}"}

        try:
            params: Dict[str, Any] = {"per_page": 100}
            if record_type:
                params["type"] = record_type
            if name_filter:
                params["name"] = name_filter

            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    f"{CF_API_BASE}/zones/{zone_id}/dns_records",
                    headers=cls._headers(),
                    params=params,
                )
                data = resp.json()

            if not data.get("success"):
                return {"success": False, "records": [], "error": "Error listando DNS"}

            records = [
                {
                    "id": r["id"],
                    "type": r["type"],
                    "name": r["name"],
                    "content": r["content"],
                    "proxied": r.get("proxied", False),
                    "ttl": r.get("ttl", 1),
                    "created_on": r.get("created_on", ""),
                }
                for r in data.get("result", [])
            ]

            return {"success": True, "records": records, "total": len(records)}
        except Exception as e:
            logger.exception(f"Error listando DNS para {domain}: {e}")
            return {"success": False, "records": [], "error": str(e)}

    # ─── DNS: Crear registro CNAME para tunnel ──────────
    @classmethod
    async def create_dns_record(
        cls,
        subdomain: str,
        tunnel_id: str,
        domain: str = "sajet.us",
        proxied: bool = True,
    ) -> Dict[str, Any]:
        """Crea un registro CNAME apuntando al tunnel."""
        zone_id = cls._zone_id(domain)
        if not zone_id:
            return {"success": False, "error": f"Zone ID no encontrado para {domain}"}

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    f"{CF_API_BASE}/zones/{zone_id}/dns_records",
                    headers=cls._headers(),
                    json={
                        "type": "CNAME",
                        "name": subdomain,
                        "content": f"{tunnel_id}.cfargotunnel.com",
                        "proxied": proxied,
                        "ttl": 1,
                    },
                )
                data = resp.json()

            if not data.get("success"):
                errors = data.get("errors", [])
                msg = errors[0].get("message") if errors else "Error creando DNS"
                return {"success": False, "error": msg}

            return {
                "success": True,
                "record_id": data["result"]["id"],
                "name": data["result"]["name"],
                "content": data["result"]["content"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── DNS: Eliminar registro ─────────────────────────
    @classmethod
    async def delete_dns_record(
        cls, record_id: str, domain: str = "sajet.us"
    ) -> Dict[str, Any]:
        """Elimina un registro DNS."""
        zone_id = cls._zone_id(domain)
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.delete(
                    f"{CF_API_BASE}/zones/{zone_id}/dns_records/{record_id}",
                    headers=cls._headers(),
                )
                data = resp.json()
            return {"success": data.get("success", False)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Obtener resumen completo para dashboard ────────
    @classmethod
    async def get_dashboard_summary(cls) -> Dict[str, Any]:
        """
        Obtiene resumen completo: tunnels + DNS CNAMEs apuntando a tunnels.
        Ideal para el dashboard del SPA.
        """
        tunnels_result = await cls.list_tunnels()
        if not tunnels_result.get("success"):
            return tunnels_result

        tunnels = tunnels_result.get("tunnels", [])

        # Contar estados
        healthy = sum(1 for t in tunnels if t["status"] == "healthy")
        down = sum(1 for t in tunnels if t["status"] == "down")
        inactive = sum(1 for t in tunnels if t["status"] == "inactive")

        # Obtener DNS CNAMEs que apuntan a tunnels
        dns_result = await cls.list_dns_records(record_type="CNAME")
        dns_records = dns_result.get("records", []) if dns_result.get("success") else []

        # Mapear DNS -> tunnel
        tunnel_dns_map: Dict[str, List[Dict]] = {}
        for record in dns_records:
            content = record.get("content", "")
            if ".cfargotunnel.com" in content:
                tid = content.replace(".cfargotunnel.com", "")
                if tid not in tunnel_dns_map:
                    tunnel_dns_map[tid] = []
                tunnel_dns_map[tid].append({
                    "record_id": record["id"],
                    "name": record["name"],
                    "proxied": record.get("proxied", False),
                })

        # Enriquecer tunnels con DNS
        for tunnel in tunnels:
            tunnel["dns_records"] = tunnel_dns_map.get(tunnel["id"], [])
            tunnel["dns_count"] = len(tunnel["dns_records"])

        return {
            "success": True,
            "tunnels": tunnels,
            "total": len(tunnels),
            "stats": {
                "healthy": healthy,
                "down": down,
                "inactive": inactive,
                "total_dns_cnames": len(dns_records),
            },
        }

    # ─── Verificar estado de la API ─────────────────────
    @classmethod
    async def verify_api_token(cls) -> Dict[str, Any]:
        """Verifica que el token de API sea válido."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{CF_API_BASE}/user/tokens/verify",
                    headers=cls._headers(),
                )
                data = resp.json()

            if data.get("success") and data.get("result", {}).get("status") == "active":
                return {"success": True, "status": "active"}
            return {"success": False, "status": "invalid"}
        except Exception as e:
            return {"success": False, "status": "error", "error": str(e)}

    # ─── Carga de dominios desde archivo JSON ───────────
    @classmethod
    def load_domains_file(cls) -> List[Dict[str, str]]:
        """Carga lista de dominios desde dominios.json (legacy helper)."""
        domains_file = os.getenv(
            "CF_DOMAINS_FILE",
            os.path.join(os.path.dirname(__file__), "../../Cloudflare/dominios.json"),
        )
        try:
            with open(domains_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"No se pudo cargar dominios.json: {e}")
            return []
