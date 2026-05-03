"""
Node Capacity Service — Dynamic capacity scoring, evaluation and alerts
for Proxmox nodes hosting Odoo tenants.

Scoring formula (0-100):
  RAM weight   40%  — most critical for Odoo (800MB/tenant)
  CPU weight   25%  — secondary bottleneck
  Storage      20%  — can be expanded more easily
  I/O headroom 15%  — loop device limits (max 8 tenants)

Auto-drain: when a node crosses a critical threshold the service sets
`can_host_tenants = False` and creates a `scale_out` alert, signaling
the provisioning system to skip the node for new tenants.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from ..models.database import SessionLocal, ProxmoxNode, NodeStatus

logger = logging.getLogger(__name__)


# ── Weight constants ─────────────────────────────────────────────────────
W_RAM = 0.40
W_CPU = 0.25
W_STORAGE = 0.20
W_IO = 0.15


class NodeCapacityService:
    """Centralized capacity intelligence for multi-node Odoo cluster."""

    # ── Core scoring ─────────────────────────────────────────────────────

    @classmethod
    def compute_score(cls, node: ProxmoxNode, active_tenants: int = 0) -> float:
        """
        Compute a capacity score from 0 (full) to 100 (empty).
        Higher = more headroom for new tenants.
        """
        total_ram = float(getattr(node, "total_ram_gb", 0) or 0) * 1024  # MB
        used_ram = float(getattr(node, "used_ram_gb", 0) or 0) * 1024
        total_storage = float(getattr(node, "total_storage_gb", 0) or 0)
        used_storage = float(getattr(node, "used_storage_gb", 0) or 0)
        cpu_pct = float(getattr(node, "used_cpu_percent", 0) or 0)
        io_max = int(getattr(node, "io_max_tenants", 8) or 8)

        # RAM score (0-100)
        ram_score = max(0, (1 - used_ram / total_ram) * 100) if total_ram > 0 else 0

        # CPU score (0-100)
        cpu_score = max(0, 100 - cpu_pct)

        # Storage score (0-100)
        storage_score = max(0, (1 - used_storage / total_storage) * 100) if total_storage > 0 else 0

        # I/O score — how many tenant slots remain vs io_max
        io_score = max(0, (1 - active_tenants / io_max) * 100) if io_max > 0 else 0

        weighted = (
            ram_score * W_RAM
            + cpu_score * W_CPU
            + storage_score * W_STORAGE
            + io_score * W_IO
        )
        return round(max(0, min(100, weighted)), 1)

    @classmethod
    def max_tenants_by_ram(cls, node: ProxmoxNode) -> int:
        """Calculate max tenants that fit in RAM given overhead policy."""
        total_mb = float(getattr(node, "total_ram_gb", 0) or 0) * 1024
        overhead = int(getattr(node, "system_overhead_mb", 1200) or 1200)
        per_tenant = int(getattr(node, "tenant_ram_mb", 800) or 800)
        if per_tenant <= 0:
            return 0
        return max(0, int((total_mb - overhead) / per_tenant))

    @classmethod
    def max_tenants_by_io(cls, node: ProxmoxNode) -> int:
        """Return I/O-based tenant limit from storage type."""
        return int(getattr(node, "io_max_tenants", 8) or 8)

    @classmethod
    def effective_max_tenants(cls, node: ProxmoxNode) -> int:
        """The real limit: min(ram_limit, io_limit, override)."""
        ram_limit = cls.max_tenants_by_ram(node)
        io_limit = cls.max_tenants_by_io(node)
        override = getattr(node, "max_tenants_override", None)
        candidates = [ram_limit, io_limit]
        if override is not None and int(override) > 0:
            candidates.append(int(override))
        return min(candidates)

    @classmethod
    def available_slots(cls, node: ProxmoxNode, active_tenants: int = 0) -> int:
        """How many more tenants this node can accept."""
        return max(0, cls.effective_max_tenants(node) - active_tenants)

    # ── Threshold evaluation ─────────────────────────────────────────────

    @classmethod
    def evaluate_thresholds(
        cls, node: ProxmoxNode, active_tenants: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Check all thresholds and return a list of alert dicts.
        Each dict: {alert_type, severity, metric_name, current_value,
                    threshold_value, message}
        """
        alerts: List[Dict[str, Any]] = []

        total_ram = float(getattr(node, "total_ram_gb", 0) or 0)
        used_ram = float(getattr(node, "used_ram_gb", 0) or 0)
        total_storage = float(getattr(node, "total_storage_gb", 0) or 0)
        used_storage = float(getattr(node, "used_storage_gb", 0) or 0)
        cpu_pct = float(getattr(node, "used_cpu_percent", 0) or 0)

        ram_pct = (used_ram / total_ram * 100) if total_ram > 0 else 0
        storage_pct = (used_storage / total_storage * 100) if total_storage > 0 else 0

        node_name = getattr(node, "name", "unknown")

        # ── RAM ───────────────────────────────────────────────────────────
        ram_warn = float(getattr(node, "ram_threshold_warning", 75) or 75)
        ram_crit = float(getattr(node, "ram_threshold_critical", 90) or 90)
        if ram_pct >= ram_crit:
            alerts.append({
                "alert_type": "capacity_critical",
                "severity": "critical",
                "metric_name": "ram",
                "current_value": round(ram_pct, 1),
                "threshold_value": ram_crit,
                "message": f"[{node_name}] RAM {ram_pct:.1f}% ≥ umbral crítico {ram_crit}%. "
                           f"Considere migrar tenants o escalar RAM.",
            })
        elif ram_pct >= ram_warn:
            alerts.append({
                "alert_type": "capacity_warning",
                "severity": "warning",
                "metric_name": "ram",
                "current_value": round(ram_pct, 1),
                "threshold_value": ram_warn,
                "message": f"[{node_name}] RAM {ram_pct:.1f}% ≥ umbral advertencia {ram_warn}%.",
            })

        # ── CPU ───────────────────────────────────────────────────────────
        cpu_warn = float(getattr(node, "cpu_threshold_warning", 70) or 70)
        cpu_crit = float(getattr(node, "cpu_threshold_critical", 90) or 90)
        if cpu_pct >= cpu_crit:
            alerts.append({
                "alert_type": "capacity_critical",
                "severity": "critical",
                "metric_name": "cpu",
                "current_value": round(cpu_pct, 1),
                "threshold_value": cpu_crit,
                "message": f"[{node_name}] CPU {cpu_pct:.1f}% ≥ umbral crítico {cpu_crit}%.",
            })
        elif cpu_pct >= cpu_warn:
            alerts.append({
                "alert_type": "capacity_warning",
                "severity": "warning",
                "metric_name": "cpu",
                "current_value": round(cpu_pct, 1),
                "threshold_value": cpu_warn,
                "message": f"[{node_name}] CPU {cpu_pct:.1f}% ≥ umbral advertencia {cpu_warn}%.",
            })

        # ── Storage ───────────────────────────────────────────────────────
        stor_warn = float(getattr(node, "storage_threshold_warning", 70) or 70)
        stor_crit = float(getattr(node, "storage_threshold_critical", 85) or 85)
        if storage_pct >= stor_crit:
            alerts.append({
                "alert_type": "capacity_critical",
                "severity": "critical",
                "metric_name": "storage",
                "current_value": round(storage_pct, 1),
                "threshold_value": stor_crit,
                "message": f"[{node_name}] Disco {storage_pct:.1f}% ≥ umbral crítico {stor_crit}%. "
                           f"Expandir disco o limpiar logs.",
            })
        elif storage_pct >= stor_warn:
            alerts.append({
                "alert_type": "capacity_warning",
                "severity": "warning",
                "metric_name": "storage",
                "current_value": round(storage_pct, 1),
                "threshold_value": stor_warn,
                "message": f"[{node_name}] Disco {storage_pct:.1f}% ≥ umbral advertencia {stor_warn}%.",
            })

        # ── Tenants vs capacity ───────────────────────────────────────────
        max_t = cls.effective_max_tenants(node)
        if active_tenants >= max_t:
            alerts.append({
                "alert_type": "scale_out",
                "severity": "critical",
                "metric_name": "tenants",
                "current_value": active_tenants,
                "threshold_value": max_t,
                "message": f"[{node_name}] {active_tenants}/{max_t} tenants — SIN SLOTS DISPONIBLES. "
                           f"Escalar a nuevo PCT o migrar tenants.",
            })
        elif active_tenants >= max_t - 1:
            alerts.append({
                "alert_type": "capacity_warning",
                "severity": "warning",
                "metric_name": "tenants",
                "current_value": active_tenants,
                "threshold_value": max_t,
                "message": f"[{node_name}] {active_tenants}/{max_t} tenants — solo 1 slot libre.",
            })

        return alerts

    # ── Full evaluation with persistence ─────────────────────────────────

    @classmethod
    def evaluate_all_nodes(cls, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Evaluate capacity of every node, persist alerts, apply auto-drain,
        return full cluster report.
        """
        own_session = db is None
        if own_session:
            db = SessionLocal()

        try:
            from sqlalchemy import func
            from ..models.database import TenantDeployment

            nodes = db.query(ProxmoxNode).filter(
                ProxmoxNode.is_database_node == False
            ).all()

            # Active tenant count per node
            tenant_counts: Dict[int, int] = dict(
                db.query(
                    TenantDeployment.active_node_id,
                    func.count(TenantDeployment.id),
                )
                .filter(TenantDeployment.active_node_id.isnot(None))
                .group_by(TenantDeployment.active_node_id)
                .all()
            )

            results = []
            new_alerts = []
            total_slots = 0
            total_tenants = 0

            for node in nodes:
                nid = node.id
                active = tenant_counts.get(nid, 0)
                total_tenants += active

                score = cls.compute_score(node, active)
                max_t = cls.effective_max_tenants(node)
                slots = cls.available_slots(node, active)
                total_slots += slots

                # Persist score
                db.query(ProxmoxNode).filter_by(id=nid).update({
                    ProxmoxNode.capacity_score: score
                })

                # Evaluate thresholds
                threshold_alerts = cls.evaluate_thresholds(node, active)

                # Auto-drain logic
                auto_drain = bool(getattr(node, "auto_drain", False))
                drained = False
                if auto_drain:
                    has_critical = any(
                        a["severity"] == "critical" for a in threshold_alerts
                    )
                    can_host = bool(getattr(node, "can_host_tenants", True))
                    if has_critical and can_host:
                        db.query(ProxmoxNode).filter_by(id=nid).update({
                            ProxmoxNode.can_host_tenants: False
                        })
                        drained = True
                        threshold_alerts.append({
                            "alert_type": "auto_drain",
                            "severity": "critical",
                            "metric_name": "auto_drain",
                            "current_value": 1,
                            "threshold_value": 0,
                            "message": f"[{node.name}] AUTO-DRAIN activado. Nodo excluido de provisioning.",
                        })

                # Persist new alerts (resolve old ones first)
                cls._persist_alerts(db, nid, threshold_alerts)
                new_alerts.extend(threshold_alerts)

                results.append({
                    "node_id": nid,
                    "name": node.name,
                    "hostname": node.hostname,
                    "vmid": getattr(node, "vmid", None),
                    "status": node.status.value if node.status else "unknown",
                    "can_host_tenants": bool(getattr(node, "can_host_tenants", False)),
                    "capacity_score": score,
                    "tenants": {
                        "active": active,
                        "max": max_t,
                        "max_by_ram": cls.max_tenants_by_ram(node),
                        "max_by_io": cls.max_tenants_by_io(node),
                        "available_slots": slots,
                    },
                    "resources": {
                        "ram_gb": {
                            "total": float(getattr(node, "total_ram_gb", 0) or 0),
                            "used": float(getattr(node, "used_ram_gb", 0) or 0),
                            "pct": round(
                                float(getattr(node, "used_ram_gb", 0) or 0)
                                / max(float(getattr(node, "total_ram_gb", 1) or 1), 0.001) * 100, 1
                            ),
                        },
                        "cpu_pct": float(getattr(node, "used_cpu_percent", 0) or 0),
                        "storage_gb": {
                            "total": float(getattr(node, "total_storage_gb", 0) or 0),
                            "used": float(getattr(node, "used_storage_gb", 0) or 0),
                            "pct": round(
                                float(getattr(node, "used_storage_gb", 0) or 0)
                                / max(float(getattr(node, "total_storage_gb", 1) or 1), 0.001) * 100, 1
                            ),
                        },
                    },
                    "policy": {
                        "tenant_ram_mb": int(getattr(node, "tenant_ram_mb", 800) or 800),
                        "system_overhead_mb": int(getattr(node, "system_overhead_mb", 1200) or 1200),
                        "storage_type": getattr(node, "storage_type", "loop"),
                        "io_max_tenants": int(getattr(node, "io_max_tenants", 8) or 8),
                        "stagger_delay_sec": int(getattr(node, "stagger_delay_sec", 12) or 12),
                        "auto_drain": auto_drain,
                    },
                    "auto_drained": drained,
                    "alerts": threshold_alerts,
                })

            db.commit()

            # Determine cluster action
            cluster_action = "OK"
            if total_slots == 0:
                cluster_action = "SCALE_OUT_REQUIRED"
            elif total_slots <= 2:
                cluster_action = "SCALE_OUT_RECOMMENDED"
            elif any(r["auto_drained"] for r in results):
                cluster_action = "NODE_DRAINED"

            return {
                "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                "cluster": {
                    "total_nodes": len(results),
                    "total_tenants": total_tenants,
                    "total_available_slots": total_slots,
                    "action": cluster_action,
                },
                "nodes": sorted(results, key=lambda r: r["capacity_score"], reverse=True),
                "alerts": new_alerts,
            }

        finally:
            if own_session:
                db.close()

    @classmethod
    def get_best_node(cls, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """
        Select the best node for a new tenant deployment.
        Uses dynamic scoring instead of static priority.
        Returns node info dict or None if no capacity.
        """
        own_session = db is None
        if own_session:
            db = SessionLocal()

        try:
            from sqlalchemy import func
            from ..models.database import TenantDeployment

            nodes = db.query(ProxmoxNode).filter(
                ProxmoxNode.status == NodeStatus.online,
                ProxmoxNode.is_database_node == False,
                ProxmoxNode.can_host_tenants == True,
            ).all()

            tenant_counts: Dict[int, int] = dict(
                db.query(
                    TenantDeployment.active_node_id,
                    func.count(TenantDeployment.id),
                )
                .filter(TenantDeployment.active_node_id.isnot(None))
                .group_by(TenantDeployment.active_node_id)
                .all()
            )

            best = None
            best_score = -1

            for node in nodes:
                active = tenant_counts.get(node.id, 0)
                slots = cls.available_slots(node, active)
                if slots <= 0:
                    continue
                score = cls.compute_score(node, active)
                if score > best_score:
                    best_score = score
                    best = {
                        "node": node,
                        "score": score,
                        "active_tenants": active,
                        "available_slots": slots,
                    }

            return best

        finally:
            if own_session:
                db.close()

    @classmethod
    def get_rebalance_recommendations(cls, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """
        Suggest tenant migrations to balance the cluster.
        Identifies overloaded nodes and suggests moving tenants
        to nodes with more headroom.
        """
        own_session = db is None
        if own_session:
            db = SessionLocal()

        try:
            from sqlalchemy import func
            from ..models.database import TenantDeployment

            nodes = db.query(ProxmoxNode).filter(
                ProxmoxNode.is_database_node == False,
                ProxmoxNode.status == NodeStatus.online,
            ).all()

            tenant_counts: Dict[int, int] = dict(
                db.query(
                    TenantDeployment.active_node_id,
                    func.count(TenantDeployment.id),
                )
                .filter(TenantDeployment.active_node_id.isnot(None))
                .group_by(TenantDeployment.active_node_id)
                .all()
            )

            # Classify nodes
            overloaded = []
            available = []
            for node in nodes:
                active = tenant_counts.get(node.id, 0)
                max_t = cls.effective_max_tenants(node)
                score = cls.compute_score(node, active)
                info = {
                    "node": node,
                    "active": active,
                    "max": max_t,
                    "score": score,
                    "slots": max(0, max_t - active),
                }
                if active >= max_t:
                    overloaded.append(info)
                elif info["slots"] >= 2:  # at least 2 free slots
                    available.append(info)

            available.sort(key=lambda x: x["score"], reverse=True)

            recommendations = []
            for over in overloaded:
                excess = over["active"] - over["max"]
                for _ in range(max(1, excess)):
                    if available:
                        target = available[0]
                        recommendations.append({
                            "action": "migrate_tenant",
                            "reason": f"Nodo {over['node'].name} sobrecargado ({over['active']}/{over['max']} tenants)",
                            "source_node": over["node"].name,
                            "source_node_id": over["node"].id,
                            "target_node": target["node"].name,
                            "target_node_id": target["node"].id,
                            "target_score": target["score"],
                            "target_slots": target["slots"],
                        })
                        target["slots"] -= 1
                        if target["slots"] <= 0:
                            available.pop(0)

            if not recommendations and not overloaded:
                return []

            if overloaded and not available:
                recommendations.append({
                    "action": "scale_out",
                    "reason": "No hay nodos con capacidad suficiente para rebalanceo. "
                              "Provisionar un nuevo PCT.",
                    "overloaded_nodes": [
                        {"name": o["node"].name, "active": o["active"], "max": o["max"]}
                        for o in overloaded
                    ],
                })

            return recommendations

        finally:
            if own_session:
                db.close()

    # ── Internal helpers ─────────────────────────────────────────────────

    @classmethod
    def _persist_alerts(
        cls, db: Session, node_id: int, alerts: List[Dict[str, Any]]
    ):
        """
        Resolve stale alerts and insert new ones.
        Only create a new alert if there isn't already an active one
        with the same node_id + metric_name + severity.
        """
        from ..models.database import Base
        # Dynamically check if NodeCapacityAlert table exists
        try:
            # Import or create a lightweight ORM model
            nca_table = Base.metadata.tables.get("node_capacity_alerts")
            if nca_table is None:
                return  # table doesn't exist yet (migration not run)
        except Exception:
            return

        # Current active alert types for this node
        active_keys = set()
        try:
            rows = db.execute(
                nca_table.select().where(
                    and_(
                        nca_table.c.node_id == node_id,
                        nca_table.c.is_active == True,
                    )
                )
            ).fetchall()
            for r in rows:
                active_keys.add((r.metric_name, r.severity))
        except Exception:
            pass

        # Current alert keys
        new_keys = set()
        for a in alerts:
            key = (a["metric_name"], a["severity"])
            new_keys.add(key)

            if key not in active_keys:
                try:
                    db.execute(nca_table.insert().values(
                        node_id=node_id,
                        alert_type=a["alert_type"],
                        severity=a["severity"],
                        metric_name=a["metric_name"],
                        current_value=a["current_value"],
                        threshold_value=a["threshold_value"],
                        message=a["message"],
                        is_active=True,
                    ))
                except Exception as e:
                    logger.warning(f"Could not insert alert: {e}")

        # Resolve alerts that are no longer active
        resolved_keys = active_keys - new_keys
        if resolved_keys:
            for mk, sv in resolved_keys:
                try:
                    db.execute(
                        nca_table.update()
                        .where(and_(
                            nca_table.c.node_id == node_id,
                            nca_table.c.metric_name == mk,
                            nca_table.c.severity == sv,
                            nca_table.c.is_active == True,
                        ))
                        .values(is_active=False, resolved_at=datetime.now(timezone.utc).replace(tzinfo=None))
                    )
                except Exception as e:
                    logger.warning(f"Could not resolve alert: {e}")
