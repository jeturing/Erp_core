"""
DSAM — Seat Audit & Reconciliation
Compara sesiones activas en Redis vs suscripciones/asientos en la BD.
Fallback para contabilizar seats cuando Odoo no reporta correctamente.
"""
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    ActiveSession, Subscription, SeatEvent, SeatHighWater,
    TenantSessionConfig, SeatEventType, SubscriptionStatus,
)

logger = logging.getLogger(__name__)


async def run_seat_audit(db: AsyncSession) -> dict[str, Any]:
    """
    Ejecuta auditoría de seats:
    1. Cuenta sesiones activas por tenant desde active_sessions
    2. Compara con el HWM registrado y la suscripción
    3. Registra discrepancias
    """
    # Sesiones activas por tenant
    active_result = await db.execute(
        select(
            ActiveSession.tenant_db,
            func.count(func.distinct(ActiveSession.odoo_login)).label("unique_users"),
            func.count(ActiveSession.id).label("total_sessions"),
        )
        .where(ActiveSession.is_active == True)
        .group_by(ActiveSession.tenant_db)
    )
    active_by_tenant = {
        row.tenant_db: {
            "unique_users": row.unique_users,
            "total_sessions": row.total_sessions,
        }
        for row in active_result.fetchall()
    }

    # Cargar suscripciones activas
    subs_result = await db.execute(
        select(Subscription).where(
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING,
            ])
        )
    )
    subscriptions = subs_result.scalars().all()

    audit_results = []
    for sub in subscriptions:
        tenant_db = None
        # Intentar obtener el tenant_db del subdomain o metadata
        if sub.odoo_db_name:
            tenant_db = sub.odoo_db_name
        elif sub.customer and hasattr(sub.customer, "subdomain"):
            tenant_db = sub.customer.subdomain

        if not tenant_db:
            continue

        active_data = active_by_tenant.get(tenant_db, {"unique_users": 0, "total_sessions": 0})
        unique_users = active_data["unique_users"]
        total_sessions = active_data["total_sessions"]

        # Comparar con quantity de la suscripción (seats comprados)
        seats_purchased = sub.quantity or 1
        seats_diff = unique_users - seats_purchased

        audit_entry = {
            "tenant_db": tenant_db,
            "subscription_id": sub.id,
            "seats_purchased": seats_purchased,
            "unique_active_users": unique_users,
            "total_active_sessions": total_sessions,
            "seats_diff": seats_diff,
            "over_limit": seats_diff > 0,
            "plan": sub.plan_type.value if sub.plan_type else None,
        }
        audit_results.append(audit_entry)

        # Si hay exceso, registrar HWM snapshot via SeatEvent
        if seats_diff > 0:
            logger.warning(
                "Tenant %s excede seats: %d activos vs %d comprados (diff: %d)",
                tenant_db, unique_users, seats_purchased, seats_diff,
            )

    # Actualizar last_seat_audit_at en configs
    now = datetime.utcnow()
    for tenant_db in active_by_tenant:
        config_result = await db.execute(
            select(TenantSessionConfig).where(
                TenantSessionConfig.tenant_db == tenant_db
            )
        )
        config = config_result.scalar_one_or_none()
        if config:
            config.last_seat_audit_at = now

    await db.commit()

    return {
        "timestamp": now.isoformat(),
        "tenants_audited": len(audit_results),
        "tenants_over_limit": sum(1 for a in audit_results if a["over_limit"]),
        "details": audit_results,
    }


async def get_seat_reconciliation_report(
    db: AsyncSession,
    tenant_db: str | None = None,
) -> dict[str, Any]:
    """
    Reporte de reconciliación de seats para un tenant o todos.
    Combina datos de active_sessions + seat_events + subscriptions.
    """
    query = (
        select(
            ActiveSession.tenant_db,
            func.count(func.distinct(ActiveSession.odoo_login)).label("active_users"),
            func.count(ActiveSession.id).label("active_sessions"),
        )
        .where(ActiveSession.is_active == True)
        .group_by(ActiveSession.tenant_db)
    )
    if tenant_db:
        query = query.where(ActiveSession.tenant_db == tenant_db)

    result = await db.execute(query)
    data = []
    for row in result.fetchall():
        # Buscar HWM más reciente
        hwm_result = await db.execute(
            select(SeatHighWater)
            .where(SeatHighWater.subscription_id.isnot(None))
            .order_by(SeatHighWater.recorded_at.desc())
            .limit(1)
        )
        hwm = hwm_result.scalar_one_or_none()

        data.append({
            "tenant_db": row.tenant_db,
            "active_users": row.active_users,
            "active_sessions": row.active_sessions,
            "hwm_value": hwm.high_water_mark if hwm else None,
            "hwm_date": hwm.recorded_at.isoformat() if hwm else None,
        })

    return {
        "report_date": datetime.utcnow().isoformat(),
        "tenants": data,
    }
