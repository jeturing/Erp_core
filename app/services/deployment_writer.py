"""
Deployment Writer — Centraliza la creación/actualización de TenantDeployment
con campos multi-nodo correctamente poblados.

Cada path de provisioning (tenants.py, customers.py, odoo_provisioner.py)
debe llamar a este módulo después de crear la BD Odoo para registrar
el deployment con toda la metadata de routing.

Fase 1 — SAJET Multi-Node Architecture
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..config import ODOO_PRIMARY_IP, ODOO_PRIMARY_PCT_ID
from ..models.database import (
    LXCContainer,
    MigrationState,
    PlanType,
    ProxmoxNode,
    RoutingMode,
    RuntimeMode,
    SessionLocal,
    TenantDeployment,
)

logger = logging.getLogger(__name__)

# ── Mapeo plan_name → PlanType enum ────────────────────────────────────

_PLAN_MAP: Dict[str, PlanType] = {
    "basic": PlanType.basic,
    "pro": PlanType.pro,
    "enterprise": PlanType.enterprise,
}


def _resolve_plan_type(plan_name: Optional[str]) -> PlanType:
    """Convierte un plan_name string al enum PlanType."""
    if not plan_name:
        return PlanType.basic
    key = plan_name.strip().lower().split("_")[0]
    return _PLAN_MAP.get(key, PlanType.basic)


def _resolve_node_from_server_id(
    db: Session, server_id: Optional[str]
) -> Optional[ProxmoxNode]:
    """
    Resuelve un ProxmoxNode a partir de un server_id string (ej: 'pct-105').
    Intenta por vmid primero, luego por hostname/IP.
    """
    if not server_id:
        return None

    # Extraer pct_id numérico de "pct-105" → 105
    pct_id: Optional[int] = None
    if server_id.startswith("pct-"):
        try:
            pct_id = int(server_id.split("-", 1)[1])
        except (ValueError, IndexError):
            pass

    if pct_id:
        node = db.query(ProxmoxNode).filter(ProxmoxNode.vmid == pct_id).first()
        if node:
            return node

    # Fallback: buscar por hostname o nombre
    node = db.query(ProxmoxNode).filter(
        (ProxmoxNode.hostname == server_id) | (ProxmoxNode.name == server_id)
    ).first()
    return node


def _resolve_container(
    db: Session, node: Optional[ProxmoxNode]
) -> Optional[LXCContainer]:
    """
    Resuelve el LXCContainer asociado a un ProxmoxNode.
    Fallback: devuelve el primer contenedor existente (legacy single-node).
    """
    if node:
        container = (
            db.query(LXCContainer)
            .filter(LXCContainer.node_id == node.id)
            .first()
        )
        if container:
            return container

    # Fallback: primer contenedor (para compatibilidad con el setup actual)
    return db.query(LXCContainer).first()


# ── Defaults por nodo ──────────────────────────────────────────────────

# Puertos HTTP/chat por nodo (hasta que exista odoo_port en proxmox_nodes)
_NODE_PORT_DEFAULTS: Dict[int, Dict[str, int]] = {
    105: {"http_port": 8080, "chat_port": 8072},
    161: {"http_port": 8080, "chat_port": 8072},
    201: {"http_port": 9000, "chat_port": 9500},  # dedicated service base
}


def _get_node_ports(pct_id: int) -> Dict[str, int]:
    """Retorna http_port y chat_port según el nodo."""
    return _NODE_PORT_DEFAULTS.get(pct_id, {"http_port": 8080, "chat_port": 8072})


# ── API pública ────────────────────────────────────────────────────────


def ensure_tenant_deployment(
    *,
    subdomain: str,
    subscription_id: int,
    customer_id: Optional[int] = None,
    server_id: Optional[str] = None,
    server_ip: Optional[str] = None,
    plan_name: Optional[str] = None,
    tunnel_id: Optional[str] = None,
    http_port: Optional[int] = None,
    chat_port: Optional[int] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Crea o actualiza un TenantDeployment con campos multi-nodo poblados.

    Idempotente: si ya existe un deployment para la subscription, actualiza
    los campos multi-nodo sin duplicar el registro.

    Args:
        subdomain:       Nombre del tenant / BD Odoo
        subscription_id: FK a subscriptions
        customer_id:     FK a customers (opcional)
        server_id:       ID del servidor Odoo usado (ej: "pct-105")
        server_ip:       IP del servidor (fallback si server_id no resuelve)
        plan_name:       Nombre del plan ("basic", "pro", etc.)
        tunnel_id:       ID del tunnel Cloudflare (si existe)
        db:              Sesión SQLAlchemy (si se omite, crea una nueva)

    Returns:
        Dict con deployment_id y status
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        # 1. Resolver ProxmoxNode
        node = _resolve_node_from_server_id(db, server_id)
        if not node and server_ip:
            node = db.query(ProxmoxNode).filter(
                ProxmoxNode.hostname == server_ip
            ).first()
        if not node:
            # Fallback: buscar nodo primario por IP conocida
            node = db.query(ProxmoxNode).filter(
                ProxmoxNode.hostname == ODOO_PRIMARY_IP
            ).first()

        # 2. Resolver LXCContainer (FK obligatorio)
        container = _resolve_container(db, node)
        if not container:
            return {
                "success": False,
                "error": "No hay LXCContainer registrado para crear TenantDeployment",
            }

        # 3. Determinar puertos y host
        pct_id = node.vmid if node and node.vmid else ODOO_PRIMARY_PCT_ID
        ports = _get_node_ports(pct_id)
        # Override con puertos explícitos del provisioner (servicio dedicado)
        if http_port:
            ports["http_port"] = http_port
        if chat_port:
            ports["chat_port"] = chat_port
        backend_host = (
            server_ip
            or (node.hostname if node else None)
            or ODOO_PRIMARY_IP
        )

        # 4. Buscar deployment existente (idempotencia)
        existing = (
            db.query(TenantDeployment)
            .filter_by(subscription_id=subscription_id)
            .first()
        )

        if existing:
            # Actualizar campos multi-nodo si estaban vacíos
            updated_fields = []
            if not existing.active_node_id and node:
                existing.active_node_id = node.id
                updated_fields.append("active_node_id")
            if not existing.backend_host:
                existing.backend_host = backend_host
                updated_fields.append("backend_host")
            if existing.http_port is None or existing.http_port == 8080:
                existing.http_port = ports["http_port"]
            if existing.chat_port is None or existing.chat_port == 8072:
                existing.chat_port = ports["chat_port"]
            if not existing.runtime_mode:
                existing.runtime_mode = RuntimeMode.shared_pool
            if not existing.routing_mode:
                existing.routing_mode = RoutingMode.node_proxy
            if not existing.migration_state:
                existing.migration_state = MigrationState.idle

            if own_session:
                db.commit()

            logger.info(
                f"ℹ️  TenantDeployment #{existing.id} actualizado para "
                f"'{subdomain}' (campos: {updated_fields or 'sin cambios'})"
            )
            return {
                "success": True,
                "deployment_id": existing.id,
                "status": "updated",
                "updated_fields": updated_fields,
            }

        # 5. Crear nuevo TenantDeployment con todos los campos multi-nodo
        from ..config import ODOO_BASE_DOMAIN

        base_domain = ODOO_BASE_DOMAIN

        deployment = TenantDeployment(
            subscription_id=subscription_id,
            container_id=container.id,
            customer_id=customer_id,
            subdomain=subdomain,
            database_name=subdomain,
            odoo_port=8069,
            tunnel_url=f"https://{subdomain}.{base_domain}",
            direct_url=f"http://{backend_host}:8069",
            tunnel_active=bool(tunnel_id),
            tunnel_id=tunnel_id,
            plan_type=_resolve_plan_type(plan_name),
            # ── Multi-nodo ──
            active_node_id=node.id if node else None,
            runtime_mode=RuntimeMode.shared_pool,
            routing_mode=RoutingMode.node_proxy,
            backend_host=backend_host,
            http_port=ports["http_port"],
            chat_port=ports["chat_port"],
            migration_state=MigrationState.idle,
            deployed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(deployment)

        if own_session:
            db.commit()
            db.refresh(deployment)

        logger.info(
            f"✅ TenantDeployment #{deployment.id} creado: "
            f"{subdomain} → node={node.id if node else '?'}, "
            f"host={backend_host}, http={ports['http_port']}, "
            f"chat={ports['chat_port']}, customer={customer_id}"
        )

        # Disparar reconciliación de routing en background
        _schedule_routing_reconcile()

        return {
            "success": True,
            "deployment_id": deployment.id,
            "status": "created",
        }

    except Exception as e:
        logger.error(f"❌ Error en ensure_tenant_deployment para '{subdomain}': {e}")
        if own_session:
            db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        if own_session:
            db.close()


# ── Reconciliación automática de routing ──────────────────────────────

def _schedule_routing_reconcile() -> None:
    """
    Dispara reconciliación de routing nginx en background (fire-and-forget).
    No bloquea el flujo de provisioning; errores se loguean pero no fallan.
    """
    import asyncio
    import threading

    def _run():
        try:
            from .routing_reconciler import RoutingReconciler

            loop = asyncio.new_event_loop()
            reconciler = RoutingReconciler()
            result = loop.run_until_complete(reconciler.reconcile())
            loop.close()

            if result.get("success"):
                changes = result.get("changes", [])
                if changes:
                    logger.info(
                        f"🔄 Routing reconciliado post-provisioning: "
                        f"{len(changes)} cambios"
                    )
            else:
                logger.warning(
                    f"⚠️  Routing reconcile post-provisioning falló: "
                    f"{result.get('error', 'desconocido')}"
                )
        except Exception as e:
            logger.warning(f"⚠️  Error en routing reconcile background: {e}")

    thread = threading.Thread(target=_run, daemon=True, name="routing-reconcile")
    thread.start()
