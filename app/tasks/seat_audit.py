"""
DSAM — Seat Audit & Reconciliation
Compara sesiones activas en Redis vs suscripciones/asientos en la BD.
Fallback para contabilizar seats cuando Odoo no reporta correctamente.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from ..models.database import (
    ActiveSession, Subscription, SeatHighWater,
    TenantSessionConfig, SubscriptionStatus, Customer,
)
from ..services.seat_events import get_non_billable_logins, record_hwm_snapshot

logger = logging.getLogger(__name__)


async def run_seat_audit(db: Session) -> dict[str, Any]:
    """
    Ejecuta auditoría de seats:
    1. Cuenta sesiones activas por tenant desde active_sessions
    2. Compara con el HWM registrado y la suscripción
    3. Registra discrepancias
    """
    # Sesiones activas por tenant
    active_sessions = db.execute(
        select(ActiveSession).where(ActiveSession.is_active == True)
    ).scalars().all()

    tenant_logins: dict[str, set[str]] = {}
    tenant_total_sessions: dict[str, int] = {}
    for session in active_sessions:
        tenant_total_sessions[session.tenant_db] = tenant_total_sessions.get(session.tenant_db, 0) + 1
        login = (session.odoo_login or "").strip().lower()
        if login:
            tenant_logins.setdefault(session.tenant_db, set()).add(login)

    # Cargar suscripciones activas
    subs_result = db.execute(
        select(Subscription).where(
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.PAST_DUE,
            ])
        )
    )
    subscriptions = subs_result.scalars().all()

    audit_results = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for sub in subscriptions:
        customer = sub.customer
        tenant_db = customer.subdomain if customer and customer.subdomain else None

        if not tenant_db:
            continue

        logins = tenant_logins.get(tenant_db, set())
        excluded_logins = get_non_billable_logins(tenant_db, customer=customer, admin_email=customer.email if customer else None)
        billable_logins = {login for login in logins if login not in excluded_logins}
        operational_logins = {login for login in logins if login in excluded_logins}

        unique_users = len(billable_logins)
        operational_users = len(operational_logins)
        total_sessions = tenant_total_sessions.get(tenant_db, 0)

        seats_purchased = sub.user_count or (customer.user_count if customer else 0) or 1
        seats_diff = unique_users - seats_purchased

        audit_entry = {
            "tenant_db": tenant_db,
            "subscription_id": sub.id,
            "customer_name": customer.company_name if customer else None,
            "seats_purchased": seats_purchased,
            "unique_active_users": unique_users,
            "operational_users": operational_users,
            "total_active_sessions": total_sessions,
            "seats_diff": seats_diff,
            "over_limit": seats_diff > 0,
            "plan": sub.plan_name,
            "active_logins": sorted(billable_logins),
            "operational_logins": sorted(operational_logins),
        }
        audit_results.append(audit_entry)

        try:
            config = db.execute(
                select(TenantSessionConfig).where(TenantSessionConfig.tenant_db == tenant_db)
            ).scalar_one_or_none()
            if config:
                config.last_seat_audit_at = now

            record_hwm_snapshot(
                db,
                sub,
                user_count_after=unique_users,
                source="dsam-seat-audit",
                metadata={
                    "tenant_db": tenant_db,
                    "operational_users": operational_users,
                    "total_sessions": total_sessions,
                },
            )
        except Exception:
            logger.exception("Error registrando HWM de auditoría para tenant=%s subscription=%s", tenant_db, sub.id)

        if seats_diff > 0:
            logger.warning(
                "Tenant %s excede seats: %d activos vs %d comprados (diff: %d)",
                tenant_db, unique_users, seats_purchased, seats_diff,
            )

    db.commit()

    return {
        "timestamp": now.isoformat(),
        "tenants_audited": len(audit_results),
        "tenants_over_limit": sum(1 for a in audit_results if a["over_limit"]),
        "details": audit_results,
    }


async def get_seat_reconciliation_report(
    db: Session,
    tenant_db: str | None = None,
) -> dict[str, Any]:
    """
    Reporte de reconciliación de seats para un tenant o todos.
    Combina datos de active_sessions + seat_events + subscriptions.
    """
    subscriptions_query = select(Subscription).where(
        Subscription.status.in_([
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.PAST_DUE,
        ])
    )
    subscriptions = db.execute(subscriptions_query).scalars().all()

    active_sessions = db.execute(
        select(ActiveSession).where(ActiveSession.is_active == True)
    ).scalars().all()

    tenant_logins: dict[str, set[str]] = {}
    tenant_total_sessions: dict[str, int] = {}
    for session in active_sessions:
        tenant_total_sessions[session.tenant_db] = tenant_total_sessions.get(session.tenant_db, 0) + 1
        login = (session.odoo_login or "").strip().lower()
        if login:
            tenant_logins.setdefault(session.tenant_db, set()).add(login)

    data = []
    for sub in subscriptions:
        customer = sub.customer
        current_tenant = customer.subdomain if customer and customer.subdomain else None
        if not current_tenant:
            continue
        if tenant_db and current_tenant != tenant_db:
            continue

        excluded_logins = get_non_billable_logins(current_tenant, customer=customer, admin_email=customer.email if customer else None)
        active_logins = tenant_logins.get(current_tenant, set())
        billable_logins = sorted(login for login in active_logins if login not in excluded_logins)
        operational_logins = sorted(login for login in active_logins if login in excluded_logins)

        hwm = db.execute(
            select(SeatHighWater)
            .where(SeatHighWater.subscription_id == sub.id)
            .order_by(SeatHighWater.period_date.desc(), SeatHighWater.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        seats_purchased = sub.user_count or (customer.user_count if customer else 0) or 1
        active_users = len(billable_logins)

        data.append({
            "tenant_db": current_tenant,
            "customer_name": customer.company_name if customer else None,
            "subscription_id": sub.id,
            "plan": sub.plan_name,
            "subscription_status": sub.status.value if sub.status else None,
            "seats_purchased": seats_purchased,
            "active_users": active_users,
            "operational_users": len(operational_logins),
            "active_sessions": tenant_total_sessions.get(current_tenant, 0),
            "hwm_value": hwm.hwm_count if hwm else None,
            "hwm_date": hwm.period_date.isoformat() if hwm else None,
            "last_snapshot_at": hwm.created_at.isoformat() if hwm else None,
            "seats_diff": active_users - seats_purchased,
            "over_limit": active_users > seats_purchased,
            "billable_logins": billable_logins,
            "operational_logins": operational_logins,
        })

    return {
        "report_date": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "tenants": data,
    }
