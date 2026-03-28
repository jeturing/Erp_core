"""
Node Registry — Fuente unificada de nodos Odoo.

Puente entre:
  - ProxmoxNode (BD, tabla proxmox_nodes) — fuente de verdad persistente
  - OdooServer  (dataclass in-memory)     — interfaz operativa que consume el
    provisioning y el OdooDatabaseManager

Objetivo Fase 0: proveer un catálogo que lea de BD con fallback a config/env,
sin romper ningún consumidor existente de OdooServer.

Uso:
    from app.services.node_registry import NodeRegistry

    registry = NodeRegistry()
    servers  = await registry.get_servers()            # Dict[str, OdooServer]
    primary  = await registry.get_primary()            # OdooServer | None
    best     = await registry.select_best_for_tenant() # OdooServer | None
    node     = await registry.get_node_for_deployment(deployment)  # OdooServer
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import (
    ODOO_PRIMARY_IP,
    ODOO_PRIMARY_PCT_ID,
    ODOO_PRIMARY_PORT,
)
from ..models.database import (
    NodeStatus,
    ProxmoxNode,
    TenantDeployment,
    SessionLocal,
)
from .odoo_database_manager import (
    OdooServer,
    OdooDatabaseManager,
    ServerStatus,
    _build_odoo_servers,
    _PRIMARY_SERVER_ID,
)

logger = logging.getLogger(__name__)


# ── helpers ────────────────────────────────────────────────────────────

def _node_status_to_server_status(ns: NodeStatus) -> ServerStatus:
    """Mapea NodeStatus (modelo BD) a ServerStatus (dataclass in-memory)."""
    _MAP = {
        NodeStatus.online: ServerStatus.online,
        NodeStatus.offline: ServerStatus.offline,
        NodeStatus.maintenance: ServerStatus.maintenance,
    }
    return _MAP.get(ns, ServerStatus.offline)


def _proxmox_node_to_odoo_server(node: ProxmoxNode) -> OdooServer:
    """Convierte un registro ProxmoxNode → OdooServer operativo."""
    pct_id = node.vmid or 0
    return OdooServer(
        id=f"pct-{pct_id}" if pct_id else f"node-{node.id}",
        name=node.name or f"Nodo {node.hostname}",
        pct_id=pct_id,
        ip=node.hostname,
        port=node.odoo_port or ODOO_PRIMARY_PORT,
        max_databases=node.max_containers or 50,
        current_databases=node.current_containers or 0,
        status=_node_status_to_server_status(node.status),
        region=node.region or "default",
        priority=node.priority or 1,
        can_host_tenants=not node.is_database_node,
    )


# ── NodeRegistry ───────────────────────────────────────────────────────

class NodeRegistry:
    """
    Catálogo unificado de nodos Odoo.

    Estrategia:
      1. Intenta leer de la tabla ``proxmox_nodes`` en BD.
      2. Si la tabla está vacía o la query falla, cae al pool in-memory
         construido desde config/env (``_build_odoo_servers``).
      3. Siempre expone ``Dict[str, OdooServer]`` — la interfaz que ya
         consumen todos los servicios.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, OdooServer] | None = None

    # ── Catálogo ───────────────────────────────────────────────────────

    async def get_servers(self, *, force_refresh: bool = False) -> Dict[str, OdooServer]:
        """Retorna catálogo completo de servidores Odoo."""
        if self._cache is not None and not force_refresh:
            return self._cache

        servers = self._load_from_db()
        if not servers:
            logger.info("NodeRegistry: proxmox_nodes vacío/inaccesible — fallback a config/env")
            servers = _build_odoo_servers()

        self._cache = servers
        return servers

    def invalidate(self) -> None:
        """Fuerza recarga en el siguiente acceso."""
        self._cache = None

    async def get_primary(self) -> Optional[OdooServer]:
        """Retorna el servidor primario (mayor prioridad, region=primary)."""
        servers = await self.get_servers()
        # Primero intentar por ID estable
        if _PRIMARY_SERVER_ID in servers:
            return servers[_PRIMARY_SERVER_ID]
        # Fallback: mayor prioridad con can_host_tenants
        candidates = [s for s in servers.values() if s.can_host_tenants]
        if candidates:
            return max(candidates, key=lambda s: s.priority)
        return None

    async def get_server(self, server_id: str) -> Optional[OdooServer]:
        """Busca servidor por id."""
        servers = await self.get_servers()
        return servers.get(server_id)

    async def get_server_by_ip(self, ip: str) -> Optional[OdooServer]:
        """Busca servidor por IP."""
        servers = await self.get_servers()
        for s in servers.values():
            if s.ip == ip:
                return s
        return None

    # ── Selección para provisioning ────────────────────────────────────

    async def select_best_for_tenant(self) -> Optional[OdooServer]:
        """
        Selecciona el mejor servidor disponible para un nuevo tenant.
        Lógica idéntica a ``select_best_server`` pero usando el registry.
        """
        servers = await self.get_servers(force_refresh=True)
        best: Optional[OdooServer] = None
        best_score: int = -1

        for server in servers.values():
            if not server.can_host_tenants:
                continue
            if server.status != ServerStatus.online:
                continue

            try:
                async with OdooDatabaseManager(server) as manager:
                    databases = await manager.list_databases()
                    server.current_databases = len(databases)

                    if server.available_slots <= 0:
                        continue

                    score = server.priority * server.available_slots
                    if score > best_score:
                        best_score = score
                        best = server
            except Exception as e:
                logger.warning(f"NodeRegistry: nodo {server.id} no disponible: {e}")
                continue

        return best

    # ── Resolución para un deployment existente ────────────────────────

    async def get_node_for_deployment(self, deployment: TenantDeployment) -> OdooServer:
        """
        Resuelve el OdooServer que corresponde a un TenantDeployment.

        Orden de resolución:
          1. ``backend_host`` + ``http_port`` del deployment (campos multi-nodo)
          2. ``active_node_id`` → ProxmoxNode → OdooServer
          3. Parse de ``direct_url`` (legacy)
          4. Fallback al servidor primario
        """
        # 1. Campos multi-nodo explícitos
        if deployment.backend_host:
            server = await self.get_server_by_ip(deployment.backend_host)
            if server:
                return server
            # Crear OdooServer efímero con la info que tenemos
            return OdooServer(
                id=f"dyn-{deployment.id}",
                name=f"Backend {deployment.backend_host}",
                pct_id=0,
                ip=deployment.backend_host,
                port=deployment.http_port or ODOO_PRIMARY_PORT,
                can_host_tenants=True,
            )

        # 2. active_node → BD
        if deployment.active_node_id:
            try:
                with SessionLocal() as db:
                    node = db.get(ProxmoxNode, deployment.active_node_id)
                    if node:
                        return _proxmox_node_to_odoo_server(node)
            except Exception as e:
                logger.warning(f"NodeRegistry: error leyendo nodo {deployment.active_node_id}: {e}")

        # 3. Legacy: parsear direct_url ("IP:PORT/db")
        if deployment.direct_url:
            try:
                host_part = deployment.direct_url.split("/")[0]
                parts = host_part.split(":")
                ip = parts[0]
                port = int(parts[1]) if len(parts) > 1 else ODOO_PRIMARY_PORT
                server = await self.get_server_by_ip(ip)
                if server:
                    return server
                return OdooServer(
                    id=f"legacy-{deployment.id}",
                    name=f"Legacy {ip}",
                    pct_id=0,
                    ip=ip,
                    port=port,
                    can_host_tenants=True,
                )
            except Exception:
                pass

        # 4. Fallback: primario
        primary = await self.get_primary()
        if primary:
            return primary

        # Último recurso: constantes de config
        return OdooServer(
            id=_PRIMARY_SERVER_ID,
            name="Primary (fallback)",
            pct_id=ODOO_PRIMARY_PCT_ID,
            ip=ODOO_PRIMARY_IP,
            port=ODOO_PRIMARY_PORT,
            can_host_tenants=True,
        )

    # ── Carga desde BD ─────────────────────────────────────────────────

    def _load_from_db(self) -> Dict[str, OdooServer]:
        """Lee proxmox_nodes y convierte a Dict[str, OdooServer]."""
        servers: Dict[str, OdooServer] = {}
        try:
            with SessionLocal() as db:
                nodes: List[ProxmoxNode] = db.execute(
                    select(ProxmoxNode).order_by(ProxmoxNode.priority.desc())
                ).scalars().all()

                for node in nodes:
                    server = _proxmox_node_to_odoo_server(node)
                    servers[server.id] = server

        except Exception as e:
            logger.warning(f"NodeRegistry: no se pudo leer proxmox_nodes: {e}")
            return {}

        return servers


# ── Singleton global ───────────────────────────────────────────────────

_registry: NodeRegistry | None = None


def get_node_registry() -> NodeRegistry:
    """Retorna el singleton del NodeRegistry."""
    global _registry
    if _registry is None:
        _registry = NodeRegistry()
    return _registry
