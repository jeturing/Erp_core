"""
PCT Resolver — Resolución dinámica IP → PCT ID desde tabla proxmox_nodes.

Reemplaza los diccionarios hardcodeados NODE_IP_TO_PCT que existían en
dedicated_service_manager.py y nginx_domain_configurator.py.

La tabla proxmox_nodes tiene:
  - hostname  = IP del nodo (ej: "10.10.10.100")
  - vmid      = PCT ID en Proxmox (ej: 105)

Se cachea en memoria con TTL de 5 minutos para evitar queries repetitivos.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, Optional

from ..models.database import ProxmoxNode, SessionLocal

logger = logging.getLogger(__name__)

# ── Cache en memoria ──────────────────────────────────────────────────
_cache: Dict[str, int] = {}
_cache_ts: float = 0.0
_CACHE_TTL = 300  # 5 minutos


def _refresh_cache() -> None:
    """Recarga el mapeo IP → PCT desde la BD."""
    global _cache, _cache_ts
    db = SessionLocal()
    try:
        nodes = db.query(ProxmoxNode.hostname, ProxmoxNode.vmid).filter(
            ProxmoxNode.vmid.isnot(None)
        ).all()
        _cache = {row.hostname: row.vmid for row in nodes if row.hostname and row.vmid}
        _cache_ts = time.monotonic()
        logger.debug("pct_resolver cache refreshed: %d nodes", len(_cache))
    except Exception as exc:
        logger.warning("pct_resolver failed to refresh cache: %s", exc)
    finally:
        db.close()


def resolve_pct_id(node_ip: str) -> Optional[int]:
    """
    Resuelve la IP de un nodo Odoo a su PCT ID de Proxmox.

    Flujo:
      1. Cache en memoria (TTL 5 min)
      2. Refresh desde BD si el cache expiró
      3. None si no se encuentra

    Args:
        node_ip: IP del nodo (ej: "10.10.10.100")

    Returns:
        PCT ID (ej: 105) o None si no se encuentra
    """
    if not node_ip:
        return None

    now = time.monotonic()
    if now - _cache_ts > _CACHE_TTL or not _cache:
        _refresh_cache()

    pct_id = _cache.get(node_ip)
    if pct_id is not None:
        return pct_id

    # Si no está en cache, intentar refresh inmediato (nodo recién agregado)
    if _cache:  # Ya hicimos refresh pero no lo encontró
        _refresh_cache()
        return _cache.get(node_ip)

    return None


def get_all_mappings() -> Dict[str, int]:
    """Retorna el mapeo completo IP → PCT (para debug/logs)."""
    now = time.monotonic()
    if now - _cache_ts > _CACHE_TTL or not _cache:
        _refresh_cache()
    return dict(_cache)


def invalidate_cache() -> None:
    """Fuerza refresh en el próximo resolve_pct_id."""
    global _cache_ts
    _cache_ts = 0.0
