"""
Reports Routes — Endpoint consolidado de analítica y reportes para el Dashboard.
Agrega datos de: billing, customers, partners, leads, comisiones,
settlements, work orders, seats, reconciliation, auditoría e infra.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import APIRouter, Cookie, HTTPException, Request
from sqlalchemy import func, case, and_

from ..models.database import (
    SessionLocal,
    Customer, CustomerStatus,
    Subscription, SubscriptionStatus,
    Plan, Partner, PartnerStatus,
    Lead, LeadStatus,
    Commission, CommissionStatus,
    ProxmoxNode, LXCContainer, NodeStatus, ContainerStatus,
    SettlementPeriod, SettlementStatus,
    WorkOrder, WorkOrderStatus,
    ReconciliationRun,
    SeatEvent,
    AuditEventRecord,
    Invoice, InvoiceStatus, InvoiceType,
    StripeEvent,
)
from .roles import _require_admin

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _get_plan_price(db, sub) -> float:
    """Precio real de una suscripción."""
    customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
    if customer and customer.is_admin_account:
        return 0
    if sub.monthly_amount and sub.monthly_amount > 0:
        return float(sub.monthly_amount)
    plan = db.query(Plan).filter(
        Plan.name == sub.plan_name, Plan.is_active == True
    ).first()
    if plan:
        return plan.calculate_monthly(sub.user_count or 1)
    fallback = {"basic": 29, "pro": 49, "enterprise": 99}
    return fallback.get(sub.plan_name or "basic", 29)


@router.get("/overview")
async def get_overview(request: Request, access_token: str = Cookie(None)) -> Dict[str, Any]:
    """
    Reporte consolidado para el dashboard principal.
    Un solo request → todos los KPIs del negocio.
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
        thirty_days_ago = now - timedelta(days=30)

        # ── 1. REVENUE & SUBSCRIPTIONS ──
        active_subs = db.query(Subscription).filter_by(
            status=SubscriptionStatus.active
        ).all()
        pending_subs = db.query(Subscription).filter_by(
            status=SubscriptionStatus.pending
        ).all()
        cancelled_30d = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.cancelled,
            Subscription.updated_at >= thirty_days_ago
        ).count()

        total_mrr = 0.0
        total_users = 0
        plan_dist: Dict[str, Dict[str, Any]] = {}
        for sub in active_subs:
            p = sub.plan_name or "basic"
            price = _get_plan_price(db, sub)
            total_mrr += price
            total_users += (sub.user_count or 1)
            if p not in plan_dist:
                plan_dist[p] = {"count": 0, "revenue": 0.0, "users": 0}
            plan_dist[p]["count"] += 1
            plan_dist[p]["revenue"] += price
            plan_dist[p]["users"] += (sub.user_count or 1)

        # Pending amount
        pending_amount = sum(_get_plan_price(db, s) for s in pending_subs)

        # Churn
        total_base = len(active_subs) + cancelled_30d
        churn_rate = round(cancelled_30d / total_base * 100, 1) if total_base else 0

        # ARR
        arr = total_mrr * 12

        # New customers this month
        new_this_month = db.query(Customer).filter(
            Customer.created_at >= month_start
        ).count()

        # ── 2. CUSTOMERS ──
        total_customers = db.query(Customer).count()
        active_customers = db.query(Customer).filter(
            Customer.status == CustomerStatus.active
        ).count()
        suspended_customers = db.query(Customer).filter(
            Customer.status == CustomerStatus.suspended
        ).count()

        # ── 3. PARTNERS ──
        total_partners = db.query(Partner).count()
        active_partners = db.query(Partner).filter(
            Partner.status == PartnerStatus.active
        ).count()
        pending_partners = db.query(Partner).filter(
            Partner.status == PartnerStatus.pending
        ).count()

        # ── 4. LEADS PIPELINE ──
        total_leads = db.query(Lead).count()
        leads_pipeline: Dict[str, int] = {}
        try:
            lead_statuses = db.query(
                Lead.status, func.count(Lead.id)
            ).group_by(Lead.status).all()
            for st, count in lead_statuses:
                leads_pipeline[st.value if hasattr(st, 'value') else str(st)] = count
        except Exception:
            pass

        active_lead_statuses = ("new", "contacted", "qualified", "in_qualification", "proposal")
        try:
            pipeline_value = db.query(
                func.coalesce(func.sum(Lead.estimated_monthly_value), 0)
            ).filter(
                Lead.status.in_([
                    LeadStatus.new, LeadStatus.contacted,
                    LeadStatus.qualified, LeadStatus.in_qualification,
                    LeadStatus.proposal
                ])
            ).scalar() or 0
        except Exception:
            pipeline_value = 0

        leads_won = leads_pipeline.get("won", 0)
        leads_active = sum(
            v for k, v in leads_pipeline.items()
            if k in active_lead_statuses
        )

        # ── 5. COMMISSIONS ──
        comm_total = db.query(func.coalesce(func.sum(Commission.partner_amount), 0)).scalar() or 0
        comm_pending = db.query(func.coalesce(func.sum(Commission.partner_amount), 0)).filter(
            Commission.status == CommissionStatus.pending
        ).scalar() or 0
        comm_paid = db.query(func.coalesce(func.sum(Commission.partner_amount), 0)).filter(
            Commission.status == CommissionStatus.paid
        ).scalar() or 0
        jeturing_share = db.query(func.coalesce(func.sum(Commission.jeturing_amount), 0)).scalar() or 0

        # ── 6. INFRASTRUCTURE ──
        nodes = db.query(ProxmoxNode).all()
        containers = db.query(LXCContainer).all()
        total_nodes = len(nodes)
        online_nodes = sum(1 for n in nodes if n.status == NodeStatus.online)
        total_containers = len(containers)
        running_containers = sum(
            1 for c in containers if c.status == ContainerStatus.running
        )

        # Cluster aggregate — use real model field names
        cluster_cpu_total = sum(n.total_cpu_cores or 0 for n in nodes)
        cluster_cpu_used_pct = sum(n.used_cpu_percent or 0 for n in nodes)
        cluster_ram_total = sum(n.total_ram_gb or 0 for n in nodes)
        cluster_ram_used = sum(n.used_ram_gb or 0 for n in nodes)
        cluster_disk_total = sum(n.total_storage_gb or 0 for n in nodes)
        cluster_disk_used = sum(n.used_storage_gb or 0 for n in nodes)

        cpu_pct = round(cluster_cpu_used_pct / total_nodes, 1) if total_nodes else 0
        ram_pct = round(cluster_ram_used / cluster_ram_total * 100, 1) if cluster_ram_total else 0
        disk_pct = round(cluster_disk_used / cluster_disk_total * 100, 1) if cluster_disk_total else 0

        # ── 7. SETTLEMENTS ──
        try:
            open_settlements = db.query(SettlementPeriod).filter(
                SettlementPeriod.status.in_([
                    SettlementStatus.draft, SettlementStatus.pending_approval
                ])
            ).count()
            closed_settlements = db.query(SettlementPeriod).filter(
                SettlementPeriod.status.in_([
                    SettlementStatus.approved, SettlementStatus.transferred
                ])
            ).count()
            total_partner_payout = db.query(
                func.coalesce(func.sum(SettlementPeriod.partner_share), 0)
            ).scalar() or 0
        except Exception:
            open_settlements = closed_settlements = 0
            total_partner_payout = 0

        # ── 8. WORK ORDERS ──
        try:
            wo_total = db.query(WorkOrder).count()
            wo_requested = db.query(WorkOrder).filter(
                WorkOrder.status == WorkOrderStatus.requested
            ).count()
            wo_in_progress = db.query(WorkOrder).filter(
                WorkOrder.status == WorkOrderStatus.in_progress
            ).count()
            wo_completed = db.query(WorkOrder).filter(
                WorkOrder.status == WorkOrderStatus.completed
            ).count()
        except Exception:
            wo_total = wo_requested = wo_in_progress = wo_completed = 0

        # ── 9. RECONCILIATION ──
        try:
            recon_total = db.query(ReconciliationRun).count()
            recon_clean = db.query(ReconciliationRun).filter(
                ReconciliationRun.status == "clean"
            ).count()
            recon_issues = db.query(ReconciliationRun).filter(
                ReconciliationRun.status == "issues_found"
            ).count()
        except Exception:
            recon_total = recon_clean = recon_issues = 0

        # ── 10. INVOICES (Épica 5) ──
        try:
            inv_total = db.query(Invoice).count()
            inv_paid = db.query(Invoice).filter(
                Invoice.status == InvoiceStatus.paid
            ).count()
            inv_pending = db.query(Invoice).filter(
                Invoice.status == InvoiceStatus.pending
            ).count()
            inv_total_amount = db.query(
                func.coalesce(func.sum(Invoice.total), 0)
            ).scalar() or 0
            inv_paid_amount = db.query(
                func.coalesce(func.sum(Invoice.total), 0)
            ).filter(Invoice.status == InvoiceStatus.paid).scalar() or 0
        except Exception:
            inv_total = inv_paid = inv_pending = 0
            inv_total_amount = inv_paid_amount = 0

        # ── 11. RECENT ACTIVITY ──
        recent_customers = db.query(Customer).order_by(
            Customer.created_at.desc()
        ).limit(8).all()
        recent_activity = []
        for c in recent_customers:
            sub = db.query(Subscription).filter(
                Subscription.customer_id == c.id
            ).first()
            recent_activity.append({
                "id": c.id,
                "company_name": c.company_name,
                "email": c.email,
                "subdomain": c.subdomain,
                "status": c.status.value if hasattr(c.status, 'value') else str(c.status or "unknown"),
                "plan": sub.plan_name if sub else "—",
                "user_count": sub.user_count if sub else 0,
                "monthly_amount": _get_plan_price(db, sub) if sub else 0,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

        # ── 12. SYSTEM HEALTH ──
        system_health = []
        # PostgreSQL
        try:
            db.execute(
                __import__('sqlalchemy').text("SELECT 1")
            )
            system_health.append({"name": "PostgreSQL", "status": "ok", "detail": "Connected"})
        except Exception:
            system_health.append({"name": "PostgreSQL", "status": "error", "detail": "Unreachable"})

        # FastAPI
        system_health.append({"name": "FastAPI", "status": "ok", "detail": "Running v2.0.0"})

        # Nodes
        if total_nodes > 0:
            system_health.append({
                "name": f"Cluster ({total_nodes} nodos)",
                "status": "ok" if online_nodes == total_nodes else "warning",
                "detail": f"{online_nodes}/{total_nodes} online"
            })
        else:
            system_health.append({"name": "Cluster", "status": "warning", "detail": "No nodes"})

        # Containers
        system_health.append({
            "name": f"Contenedores",
            "status": "ok" if running_containers > 0 else "warning",
            "detail": f"{running_containers}/{total_containers} running"
        })

        # ── 13. STRIPE EVENTS (últimos 10) ──
        try:
            stripe_events = db.query(StripeEvent).order_by(
                StripeEvent.created_at.desc()
            ).limit(10).all()
            recent_stripe = [{
                "event_id": e.event_id,
                "event_type": e.event_type,
                "processed": e.processed,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            } for e in stripe_events]
        except Exception:
            recent_stripe = []

        # ── 14. TOP PARTNERS (by revenue) ──
        top_partners = []
        try:
            partners_list = db.query(Partner).filter(
                Partner.status == PartnerStatus.active
            ).all()
            for p in partners_list:
                p_leads = db.query(Lead).filter(Lead.partner_id == p.id).count()
                p_rev = db.query(
                    func.coalesce(func.sum(Commission.gross_revenue), 0)
                ).filter(Commission.partner_id == p.id).scalar() or 0
                p_comms = db.query(
                    func.coalesce(func.sum(Commission.partner_amount), 0)
                ).filter(Commission.partner_id == p.id).scalar() or 0
                top_partners.append({
                    "id": p.id,
                    "company_name": p.company_name,
                    "leads": p_leads,
                    "total_revenue": float(p_rev),
                    "total_commissions": float(p_comms),
                })
            top_partners.sort(key=lambda x: x["total_revenue"], reverse=True)
            top_partners = top_partners[:5]
        except Exception:
            pass

        # ══════════════════════════════════════
        # RESPUESTA CONSOLIDADA
        # ══════════════════════════════════════
        return {
            "generated_at": now.isoformat(),

            # Revenue
            "revenue": {
                "mrr": round(total_mrr, 2),
                "arr": round(arr, 2),
                "pending_amount": round(pending_amount, 2),
                "pending_count": len(pending_subs),
                "churn_rate": churn_rate,
                "total_users": total_users,
                "plan_distribution": plan_dist,
                "new_this_month": new_this_month,
                "cancelled_30d": cancelled_30d,
            },

            # Customers
            "customers": {
                "total": total_customers,
                "active": active_customers,
                "suspended": suspended_customers,
                "active_subscriptions": len(active_subs),
            },

            # Partners
            "partners": {
                "total": total_partners,
                "active": active_partners,
                "pending": pending_partners,
                "top": top_partners,
            },

            # Leads
            "leads": {
                "total": total_leads,
                "active": leads_active,
                "won": leads_won,
                "pipeline_value": float(pipeline_value),
                "pipeline": leads_pipeline,
            },

            # Commissions
            "commissions": {
                "total_partner": float(comm_total),
                "pending": float(comm_pending),
                "paid": float(comm_paid),
                "jeturing_share": float(jeturing_share),
            },

            # Infrastructure
            "infrastructure": {
                "nodes_total": total_nodes,
                "nodes_online": online_nodes,
                "containers_total": total_containers,
                "containers_running": running_containers,
                "cpu": {"used": cluster_cpu_used_pct, "total": cluster_cpu_total, "percent": cpu_pct},
                "ram": {"used": round(cluster_ram_used, 1), "total": round(cluster_ram_total, 1), "percent": ram_pct},
                "disk": {"used": round(cluster_disk_used, 1), "total": round(cluster_disk_total, 1), "percent": disk_pct},
            },

            # Settlements
            "settlements": {
                "open": open_settlements,
                "closed": closed_settlements,
                "total_partner_payout": float(total_partner_payout),
            },

            # Work Orders
            "work_orders": {
                "total": wo_total,
                "requested": wo_requested,
                "in_progress": wo_in_progress,
                "completed": wo_completed,
            },

            # Reconciliation
            "reconciliation": {
                "total_runs": recon_total,
                "clean": recon_clean,
                "issues": recon_issues,
            },

            # Invoices (Épica 5)
            "invoices": {
                "total": inv_total,
                "paid": inv_paid,
                "pending": inv_pending,
                "total_amount": float(inv_total_amount),
                "paid_amount": float(inv_paid_amount),
            },

            # System
            "system_health": system_health,
            "recent_activity": recent_activity,
            "recent_stripe_events": recent_stripe,
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error en /api/reports/overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
