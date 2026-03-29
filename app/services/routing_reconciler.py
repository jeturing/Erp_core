"""
Routing Reconciler — Regenera la configuración de routing nginx en PCT160
a partir del estado deseado en BD (TenantDeployment + CustomDomain).

Responsabilidades:
  1. Leer todos los TenantDeployments activos → generar odoo_http_routes.map
     y odoo_chat_routes.map con overrides por subdomain.sajet.us
  2. Leer todos los CustomDomains activos → generar bloque external-domains
     (maps + server_name + backend override)
  3. Escribir los archivos en PCT160 (local si corre ahí, SSH si corre en otro host)
  4. Validar con nginx -t → reload → rollback si falla

Arquitectura nginx en PCT160:
  - /etc/nginx/sites-available/erp contiene:
      map $host $odoo_http_upstream {
          default "";
          ~^([a-z0-9-]+)\.sajet\.us$  10.10.10.100:8069;  ← fallback
          include /etc/nginx/conf.d/odoo_http_routes.map;  ← overrides
      }
      map $host $odoo_chat_upstream { ... similar ... }
  - Los .map files contienen líneas: dominio  ip:puerto;
  - /etc/nginx/sites-available/external-domains contiene server block
    para dominios externos con map $external_tenant_db

Uso:
    from app.services.routing_reconciler import RoutingReconciler

    reconciler = RoutingReconciler()
    result = await reconciler.reconcile()
    # result = {"success": True, "tenants": 4, "domains": 2, "changes": [...]}

    # Solo generar sin aplicar (dry-run):
    result = await reconciler.reconcile(dry_run=True)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..config import (
    CT105_IP,
    CT105_NGINX_PORT,
    ODOO_PRIMARY_IP,
    ODOO_PRIMARY_PORT,
)
from ..models.database import (
    CustomDomain,
    DomainVerificationStatus,
    NodeStatus,
    ProxmoxNode,
    SessionLocal,
    TenantDeployment,
)
from .nginx_domain_configurator import (
    CT105_ODOO_CONF,
    PCT160_CHAT_MAP,
    PCT160_HTTP_MAP,
    _add_to_map,
    _add_to_server_name,
    _external_domain_aliases,
    _read_file_local,
    _read_file_node,
    _run_local,
    _run_node,
    _write_file_local,
    _write_file_node,
)

logger = logging.getLogger("routing_reconciler")

# ── Constantes ────────────────────────────────────────────────────────────────

# Puerto chat/longpolling del nodo (si no tiene override)
_DEFAULT_CHAT_PORT = 8072

# Header de los map files generados
_HTTP_MAP_HEADER = """\
# Generado automáticamente por RoutingReconciler — NO EDITAR A MANO
# Overrides por tenant: subdomain.sajet.us → node_ip:http_port
# Dominios externos → node_ip:nginx_port (para Host rewrite en el nodo)
"""

_CHAT_MAP_HEADER = """\
# Generado automáticamente por RoutingReconciler — NO EDITAR A MANO
# Overrides por tenant: subdomain.sajet.us → node_ip:chat_port
# Dominios externos → node_ip:nginx_port (para Host rewrite en el nodo)
"""


# ── Dataclasses intermedias ───────────────────────────────────────────────────

@dataclass
class _TenantRoute:
    """Ruta de un tenant .sajet.us."""
    subdomain: str
    backend_host: str
    http_port: int
    chat_port: int
    database_name: str

    @property
    def full_domain(self) -> str:
        return f"{self.subdomain}.sajet.us"

    @property
    def http_backend(self) -> str:
        return f"{self.backend_host}:{self.http_port}"

    @property
    def chat_backend(self) -> str:
        return f"{self.backend_host}:{self.chat_port}"


@dataclass
class _ExternalRoute:
    """Ruta de un dominio externo → tenant."""
    external_domain: str
    tenant_db: str
    sajet_subdomain: str
    backend_host: str
    nginx_port: int  # Puerto nginx del nodo (no Odoo directo) — para Host rewrite

    @property
    def backend(self) -> str:
        return f"{self.backend_host}:{self.nginx_port}"


@dataclass
class _ReconcileState:
    """Estado deseado calculado desde BD."""
    tenant_routes: List[_TenantRoute] = field(default_factory=list)
    external_routes: List[_ExternalRoute] = field(default_factory=list)


# ── RoutingReconciler ─────────────────────────────────────────────────────────

class RoutingReconciler:
    """
    Lee BD y regenera los archivos de routing nginx en PCT160.
    
    Garantías:
      - Idempotente: si no hay cambios, no reescribe ni recarga
      - Atómico: nginx -t antes de reload; rollback si falla
      - Trazable: retorna diff de cambios aplicados
    """

    def __init__(self, db: Optional[Session] = None) -> None:
        self._external_db = db

    # ── API pública ───────────────────────────────────────────────────────

    async def reconcile(
        self,
        *,
        dry_run: bool = False,
        include_remote_nodes: bool = True,
    ) -> Dict[str, Any]:
        """
        Reconcilia el estado de routing nginx con la BD.

        Args:
            dry_run: si True, calcula cambios pero no los aplica
            include_remote_nodes: si True, también reconcilia nodos remotos (incremental)

        Returns:
            {
                "success": bool,
                "tenants": int,
                "external_domains": int,
                "changes": [str, ...],
                "remote_nodes": [{node_ip, status, changes}],
                "dry_run": bool,
            }
        """
        changes: List[str] = []
        remote_results: List[Dict[str, Any]] = []

        try:
            # 1. Leer estado deseado desde BD
            state = self._load_desired_state()

            # 2. Generar contenido de map files
            http_map_content = self._render_http_map(state)
            chat_map_content = self._render_chat_map(state)

            # 3. Comparar con estado actual
            current_http = self._safe_read(PCT160_HTTP_MAP)
            current_chat = self._safe_read(PCT160_CHAT_MAP)

            http_changed = self._content_differs(current_http, http_map_content)
            chat_changed = self._content_differs(current_chat, chat_map_content)

            if http_changed:
                changes.append(f"odoo_http_routes.map: {self._diff_summary(current_http, http_map_content)}")
            if chat_changed:
                changes.append(f"odoo_chat_routes.map: {self._diff_summary(current_chat, chat_map_content)}")

            if not changes:
                logger.info("RoutingReconciler: sin cambios detectados en PCT160")
                # Aún así, verificar nodos remotos si se solicita
                if include_remote_nodes and not dry_run:
                    remote_results = self._reconcile_remote_nodes(state)

                return {
                    "success": True,
                    "tenants": len(state.tenant_routes),
                    "external_domains": len(state.external_routes),
                    "changes": [],
                    "remote_nodes": remote_results,
                    "dry_run": dry_run,
                }

            if dry_run:
                logger.info(f"RoutingReconciler dry-run: {len(changes)} cambios pendientes")
                return {
                    "success": True,
                    "tenants": len(state.tenant_routes),
                    "external_domains": len(state.external_routes),
                    "changes": changes,
                    "remote_nodes": [],
                    "dry_run": True,
                }

            # 4. Aplicar cambios con rollback
            result = self._apply_maps(
                http_map_content if http_changed else None,
                chat_map_content if chat_changed else None,
                current_http,
                current_chat,
            )

            if result["success"]:
                logger.info(
                    f"RoutingReconciler: {len(changes)} cambios aplicados — "
                    f"{len(state.tenant_routes)} tenants, "
                    f"{len(state.external_routes)} dominios externos"
                )

                # 5. Reconciliar nodos remotos incrementalmente
                if include_remote_nodes:
                    remote_results = self._reconcile_remote_nodes(state)
            else:
                changes.append(f"ERROR: {result.get('error', 'desconocido')}")

            return {
                "success": result["success"],
                "tenants": len(state.tenant_routes),
                "external_domains": len(state.external_routes),
                "changes": changes,
                "remote_nodes": remote_results,
                "dry_run": False,
                **({} if result["success"] else {"error": result.get("error")}),
            }

        except Exception as e:
            logger.error(f"RoutingReconciler error: {e}", exc_info=True)
            return {
                "success": False,
                "tenants": 0,
                "external_domains": 0,
                "changes": [f"ERROR: {e}"],
                "dry_run": dry_run,
            }

    async def get_desired_state_summary(self) -> Dict[str, Any]:
        """Retorna resumen del estado deseado sin aplicar cambios."""
        state = self._load_desired_state()
        return {
            "tenants": [
                {
                    "subdomain": r.subdomain,
                    "backend": r.http_backend,
                    "chat": r.chat_backend,
                    "database": r.database_name,
                }
                for r in state.tenant_routes
            ],
            "external_domains": [
                {
                    "domain": r.external_domain,
                    "tenant_db": r.tenant_db,
                    "backend": r.backend,
                    "sajet_subdomain": r.sajet_subdomain,
                }
                for r in state.external_routes
            ],
        }

    async def diagnose_routing(self) -> Dict[str, Any]:
        """
        Compara estado deseado (BD) vs estado real (nginx maps) por nodo.
        Retorna discrepancias para validación post-reconciliación.
        """
        state = self._load_desired_state()
        discrepancies: List[Dict[str, Any]] = []

        # --- PCT160: comparar map files ---
        desired_http = self._render_http_map(state)
        desired_chat = self._render_chat_map(state)
        current_http = self._safe_read(PCT160_HTTP_MAP)
        current_chat = self._safe_read(PCT160_CHAT_MAP)

        pct160_http_ok = not self._content_differs(current_http, desired_http)
        pct160_chat_ok = not self._content_differs(current_chat, desired_chat)

        pct160_status = {
            "node": "PCT160 (local)",
            "http_map_synced": pct160_http_ok,
            "chat_map_synced": pct160_chat_ok,
        }
        if not pct160_http_ok:
            pct160_status["http_diff"] = self._diff_summary(current_http, desired_http)
        if not pct160_chat_ok:
            pct160_status["chat_diff"] = self._diff_summary(current_chat, desired_chat)
        discrepancies.append(pct160_status)

        # --- Nodos remotos: verificar que los subdominios del nodo están en su nginx ---
        nodes_with_tenants = self._group_routes_by_node(state)

        for node_ip, routes in nodes_with_tenants.items():
            node_result: Dict[str, Any] = {
                "node": node_ip,
                "tenants_expected": len(routes),
                "missing_in_nginx": [],
                "reachable": True,
            }
            try:
                node_conf = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
                for route in routes:
                    # Verificar que el subdomain.sajet.us aparezca en tenant_db map
                    if route.full_domain not in node_conf:
                        node_result["missing_in_nginx"].append(route.full_domain)
            except Exception as e:
                node_result["reachable"] = False
                node_result["error"] = str(e)

            node_result["synced"] = (
                node_result["reachable"]
                and len(node_result["missing_in_nginx"]) == 0
            )
            discrepancies.append(node_result)

        all_synced = all(d.get("synced", d.get("http_map_synced", False)) for d in discrepancies)

        return {
            "synced": all_synced,
            "nodes_checked": len(discrepancies),
            "total_tenants": len(state.tenant_routes),
            "total_external_domains": len(state.external_routes),
            "details": discrepancies,
        }

    # ── Reconciliación remota incremental ─────────────────────────────────

    def _reconcile_remote_nodes(self, state: _ReconcileState) -> List[Dict[str, Any]]:
        """
        Reconcilia la configuración nginx en cada nodo remoto,
        solo para los tenants que pertenecen a ese nodo.
        Incremental: un nodo falla → los demás se procesan igual.
        """
        results: List[Dict[str, Any]] = []
        nodes_routes = self._group_routes_by_node(state)

        for node_ip, routes in nodes_routes.items():
            node_result: Dict[str, Any] = {
                "node_ip": node_ip,
                "tenants": len(routes),
                "status": "ok",
                "changes": [],
            }
            try:
                node_conf = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
                original_conf = node_conf
                changed = False

                for route in routes:
                    full_domain = route.full_domain
                    # Verificar y agregar a map $tenant_db
                    if full_domain not in node_conf or f"{full_domain} {route.subdomain};" not in node_conf.replace("    ", ""):
                        node_conf = _add_to_map(node_conf, "tenant_db", full_domain, route.subdomain)
                        changed = True
                        node_result["changes"].append(f"+tenant_db: {full_domain}")

                    # Verificar y agregar a map $odoo_proxy_host
                    expected_proxy = f"{route.subdomain}.sajet.us"
                    if f"{full_domain} {expected_proxy};" not in node_conf.replace("    ", ""):
                        node_conf = _add_to_map(node_conf, "odoo_proxy_host", full_domain, expected_proxy)
                        changed = True
                        node_result["changes"].append(f"+odoo_proxy_host: {full_domain}")

                    # server_name
                    if full_domain not in node_conf:
                        node_conf = _add_to_server_name(node_conf, "listen 8080", full_domain)
                        changed = True
                        node_result["changes"].append(f"+server_name: {full_domain}")

                if changed:
                    _write_file_node(CT105_ODOO_CONF, node_conf, node_ip=node_ip)
                    rc, _, err = _run_node("nginx -t", node_ip=node_ip)
                    if rc != 0:
                        # Rollback
                        _write_file_node(CT105_ODOO_CONF, original_conf, node_ip=node_ip)
                        node_result["status"] = "rollback"
                        node_result["error"] = f"nginx -t failed: {err}"
                        logger.error(f"RoutingReconciler: rollback nodo {node_ip}: {err}")
                    else:
                        _run_node("systemctl reload nginx", node_ip=node_ip)
                        logger.info(f"RoutingReconciler: nodo {node_ip} actualizado ({len(node_result['changes'])} cambios)")
                else:
                    node_result["status"] = "no_changes"

            except Exception as e:
                node_result["status"] = "error"
                node_result["error"] = str(e)
                logger.warning(f"RoutingReconciler: error en nodo {node_ip}: {e}")

            results.append(node_result)

        return results

    @staticmethod
    def _group_routes_by_node(state: _ReconcileState) -> Dict[str, List[_TenantRoute]]:
        """Agrupa tenant routes por backend_host (nodo IP)."""
        groups: Dict[str, List[_TenantRoute]] = {}
        for route in state.tenant_routes:
            ip = route.backend_host
            if ip not in groups:
                groups[ip] = []
            groups[ip].append(route)
        return groups

    # ── Carga desde BD ────────────────────────────────────────────────────

    def _load_desired_state(self) -> _ReconcileState:
        """Lee TenantDeployments y CustomDomains activos de BD."""
        state = _ReconcileState()

        db = self._external_db or SessionLocal()
        owns_session = self._external_db is None

        try:
            # --- Nodos: construir lookup vmid → node para resolver puertos ---
            nodes_by_id: Dict[int, ProxmoxNode] = {}
            for node in db.execute(select(ProxmoxNode)).scalars().all():
                nodes_by_id[node.id] = node

            # --- TenantDeployments activos ---
            deployments = (
                db.execute(
                    select(TenantDeployment)
                    .where(TenantDeployment.subdomain.isnot(None))
                )
                .scalars()
                .all()
            )

            for dep in deployments:
                backend_host = dep.backend_host or ODOO_PRIMARY_IP
                http_port = dep.http_port or CT105_NGINX_PORT
                chat_port = dep.chat_port or _DEFAULT_CHAT_PORT
                database_name = dep.database_name or dep.subdomain

                state.tenant_routes.append(
                    _TenantRoute(
                        subdomain=dep.subdomain,
                        backend_host=backend_host,
                        http_port=http_port,
                        chat_port=chat_port,
                        database_name=database_name,
                    )
                )

            # --- CustomDomains activos (no .sajet.us) ---
            custom_domains = (
                db.execute(
                    select(CustomDomain)
                    .where(
                        CustomDomain.is_active == True,
                        ~CustomDomain.external_domain.endswith(".sajet.us"),
                    )
                )
                .scalars()
                .all()
            )

            for cd in custom_domains:
                # Resolver el backend del tenant
                backend_host = cd.target_node_ip or ODOO_PRIMARY_IP
                # Para dominios externos, el tráfico va al nginx del nodo (no Odoo directo)
                # porque el nginx del nodo hace el Host rewrite
                nginx_port = CT105_NGINX_PORT  # 8080 por defecto

                # Si tiene deployment vinculado, usar sus datos
                if cd.tenant_deployment_id:
                    dep = db.get(TenantDeployment, cd.tenant_deployment_id)
                    if dep:
                        backend_host = dep.backend_host or backend_host
                        nginx_port = dep.http_port or nginx_port

                sajet_sub = cd.sajet_subdomain or ""
                if not sajet_sub:
                    continue  # Sin subdomain sajet → no podemos enrutar

                state.external_routes.append(
                    _ExternalRoute(
                        external_domain=cd.external_domain,
                        tenant_db=sajet_sub,  # sajet_subdomain = nombre BD en la mayoría de casos
                        sajet_subdomain=sajet_sub,
                        backend_host=backend_host,
                        nginx_port=nginx_port,
                    )
                )

        finally:
            if owns_session:
                db.close()

        return state

    # ── Renderizado de maps ───────────────────────────────────────────────

    def _render_http_map(self, state: _ReconcileState) -> str:
        """Genera contenido de odoo_http_routes.map."""
        lines = [_HTTP_MAP_HEADER]

        # Tenant subdomain overrides (solo si difieren del default)
        if state.tenant_routes:
            lines.append("# --- Subdominios .sajet.us ---")
            for r in sorted(state.tenant_routes, key=lambda x: x.subdomain):
                lines.append(f"{r.full_domain} {r.http_backend};")
            lines.append("")

        # Dominios externos
        if state.external_routes:
            lines.append("# --- Dominios externos ---")
            external_hosts: Dict[str, str] = {}
            for r in sorted(state.external_routes, key=lambda x: x.external_domain):
                for domain_host in _external_domain_aliases(r.external_domain):
                    external_hosts[domain_host] = r.backend
            for domain_host in sorted(external_hosts):
                lines.append(f"{domain_host} {external_hosts[domain_host]};")
            lines.append("")

        return "\n".join(lines) + "\n"

    def _render_chat_map(self, state: _ReconcileState) -> str:
        """Genera contenido de odoo_chat_routes.map."""
        lines = [_CHAT_MAP_HEADER]

        # Tenant subdomain chat overrides
        if state.tenant_routes:
            lines.append("# --- Subdominios .sajet.us ---")
            for r in sorted(state.tenant_routes, key=lambda x: x.subdomain):
                lines.append(f"{r.full_domain} {r.chat_backend};")
            lines.append("")

        # Dominios externos — chat también va al nginx del nodo
        if state.external_routes:
            lines.append("# --- Dominios externos ---")
            external_hosts: Dict[str, str] = {}
            for r in sorted(state.external_routes, key=lambda x: x.external_domain):
                for domain_host in _external_domain_aliases(r.external_domain):
                    external_hosts[domain_host] = r.backend
            for domain_host in sorted(external_hosts):
                lines.append(f"{domain_host} {external_hosts[domain_host]};")
            lines.append("")

        return "\n".join(lines) + "\n"

    # ── Aplicación y rollback ─────────────────────────────────────────────

    def _apply_maps(
        self,
        http_content: Optional[str],
        chat_content: Optional[str],
        backup_http: str,
        backup_chat: str,
    ) -> Dict[str, Any]:
        """
        Escribe los map files, valida con nginx -t, recarga.
        Rollback automático si nginx -t falla.
        """
        try:
            # Escribir archivos
            if http_content is not None:
                _write_file_local(PCT160_HTTP_MAP, http_content)
            if chat_content is not None:
                _write_file_local(PCT160_CHAT_MAP, chat_content)

            # Validar
            rc, _, err = _run_local("nginx -t")
            if rc != 0:
                logger.error(f"RoutingReconciler: nginx -t falló: {err}")
                # Rollback
                self._rollback_maps(backup_http, backup_chat)
                return {"success": False, "error": f"nginx -t falló: {err}"}

            # Recargar
            rc, _, err = _run_local("systemctl reload nginx")
            if rc != 0:
                logger.error(f"RoutingReconciler: reload falló: {err}")
                self._rollback_maps(backup_http, backup_chat)
                return {"success": False, "error": f"reload falló: {err}"}

            logger.info("RoutingReconciler: nginx recargado exitosamente ✅")
            return {"success": True}

        except Exception as e:
            logger.error(f"RoutingReconciler: error aplicando maps: {e}")
            self._rollback_maps(backup_http, backup_chat)
            return {"success": False, "error": str(e)}

    def _rollback_maps(self, http_backup: str, chat_backup: str) -> None:
        """Restaura maps al estado anterior."""
        logger.warning("RoutingReconciler: ejecutando rollback...")
        try:
            if http_backup:
                _write_file_local(PCT160_HTTP_MAP, http_backup)
            if chat_backup:
                _write_file_local(PCT160_CHAT_MAP, chat_backup)
            _run_local("nginx -t && systemctl reload nginx")
        except Exception as e:
            logger.error(f"RoutingReconciler: rollback falló: {e}")

    # ── Utilidades ────────────────────────────────────────────────────────

    @staticmethod
    def _safe_read(path: str) -> str:
        """Lee un archivo, retorna cadena vacía si no existe."""
        try:
            return _read_file_local(path)
        except (FileNotFoundError, RuntimeError):
            return ""

    @staticmethod
    def _content_differs(current: str, desired: str) -> bool:
        """Compara contenido ignorando comentarios y whitespace extra."""
        def _normalize(text: str) -> List[str]:
            return sorted(
                line.strip()
                for line in text.splitlines()
                if line.strip() and not line.strip().startswith("#")
            )
        return _normalize(current) != _normalize(desired)

    @staticmethod
    def _diff_summary(current: str, desired: str) -> str:
        """Genera resumen legible de cambios entre dos versiones."""
        def _entries(text: str) -> set:
            return {
                line.strip()
                for line in text.splitlines()
                if line.strip() and not line.strip().startswith("#")
            }

        old = _entries(current)
        new = _entries(desired)
        added = new - old
        removed = old - new

        parts = []
        if added:
            parts.append(f"+{len(added)} entradas")
        if removed:
            parts.append(f"-{len(removed)} entradas")
        if not parts:
            parts.append("formato actualizado")
        return ", ".join(parts)
