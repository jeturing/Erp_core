"""
Seats Routes — Épica 3 (Direct HWM) + Épica 4 (Partner Metered + Grace 8h)

- POST /api/seats/event       → Registra evento de usuario (webhook desde Odoo)
- GET  /api/seats/hwm/{sub}   → High-water mark actual
- POST /api/seats/sync-stripe → Sincroniza HWM con Stripe quantity
- GET  /api/seats/summary/{sub} → Resumen de asientos
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import stripe
import logging

from ..models.database import (
    SeatEvent, SeatHighWater, Subscription, SeatEventType,
    BillingMode, Customer, Partner, SubscriptionStatus, get_db
)
from ..config import get_runtime_int, get_runtime_setting
from ..services.seat_events import (
    is_partner_metered as _service_is_partner_metered,
    record_hwm_snapshot,
    record_seat_event as _service_record_seat_event,
)

router = APIRouter(prefix="/api/seats", tags=["Seats"])
logger = logging.getLogger(__name__)


def _configure_stripe() -> str:
    stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
    return stripe.api_key


def _grace_hours() -> int:
    return get_runtime_int("SEAT_GRACE_HOURS", 8)


# ── DTOs ──

class SeatEventCreate(BaseModel):
    subscription_id: int
    event_type: str                       # USER_CREATED, USER_DEACTIVATED, USER_REACTIVATED, FIRST_LOGIN
    odoo_user_id: Optional[int] = None
    odoo_login: Optional[str] = None
    user_count_after: int
    source: str = "webhook"
    metadata: Optional[dict] = None


# ── HELPERS ──

def _is_partner_metered(sub: Subscription) -> bool:
    """Determina si la suscripción es partner metered (Épica 4)."""
    return _service_is_partner_metered(sub)


def _sync_stripe_quantity(sub: Subscription, qty: int) -> bool:
    """Actualiza quantity en Stripe subscription item."""
    _configure_stripe()
    if not sub.stripe_subscription_id:
        logger.warning(f"No stripe_subscription_id for sub {sub.id}")
        return False
    try:
        stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
        if stripe_sub.get("items") and stripe_sub["items"]["data"]:
            item_id = stripe_sub["items"]["data"][0]["id"]
            stripe.SubscriptionItem.modify(item_id, quantity=qty)
            logger.info(f"Stripe qty updated: sub={sub.id} qty={qty}")
            return True
    except stripe.error.StripeError as e:
        logger.error(f"Stripe qty update failed for sub {sub.id}: {e}")
    return False


# ── ENDPOINTS ──

@router.post("/event")
def record_seat_event(payload: SeatEventCreate, db: Session = Depends(get_db)):
    """
    Registra un evento de asiento/usuario.
    Llamado por webhook de Odoo o cron.
    
    - Direct (Épica 3): Actualiza HWM y sincroniza Stripe quantity inmediatamente.
    - Partner metered (Épica 4): Billable por FIRST_LOGIN + grace 8h.
    """
    sub = db.query(Subscription).filter(Subscription.id == payload.subscription_id).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    try:
        event_type = SeatEventType(payload.event_type)
    except ValueError:
        raise HTTPException(400, f"Invalid event_type: {payload.event_type}")

    is_partner = _is_partner_metered(sub)
    event, hwm = _service_record_seat_event(
        db,
        sub,
        event_type=event_type,
        user_count_after=payload.user_count_after,
        odoo_user_id=payload.odoo_user_id,
        odoo_login=payload.odoo_login,
        source=payload.source,
        metadata=payload.metadata,
    )

    # Épica 3: Sync Stripe quantity en real-time si Direct
    stripe_synced = False
    if not is_partner and event.is_billable and sub.stripe_subscription_id:
        stripe_synced = _sync_stripe_quantity(sub, payload.user_count_after)
        if stripe_synced:
            hwm.stripe_qty_updated = True
            hwm.stripe_qty_updated_at = datetime.utcnow()

    db.commit()

    return {
        "event_id": event.id,
        "subscription_id": sub.id,
        "event_type": event_type.value,
        "user_count_after": payload.user_count_after,
        "is_billable": event.is_billable,
        "is_partner_metered": is_partner,
        "grace_expires_at": event.grace_expires_at.isoformat() if event.grace_expires_at else None,
        "stripe_synced": stripe_synced,
        "hwm_today": hwm.hwm_count,
    }


@router.get("/hwm/{subscription_id}")
def get_hwm(subscription_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Obtiene historial de high-water mark."""
    since = datetime.utcnow() - timedelta(days=days)
    records = db.query(SeatHighWater).filter(
        SeatHighWater.subscription_id == subscription_id,
        SeatHighWater.period_date >= since,
    ).order_by(SeatHighWater.period_date.desc()).all()

    return {
        "subscription_id": subscription_id,
        "days": days,
        "records": [
            {
                "id": r.id,
                "subscription_id": r.subscription_id,
                "period_date": r.period_date.date().isoformat(),
                "date": r.period_date.isoformat(),
                "hwm_count": r.hwm_count,
                "stripe_qty_updated": r.stripe_qty_updated,
                "stripe_qty_updated_at": r.stripe_qty_updated_at.isoformat() if r.stripe_qty_updated_at else None,
            }
            for r in records
        ],
        "items": [
            {
                "id": r.id,
                "subscription_id": r.subscription_id,
                "period_date": r.period_date.date().isoformat(),
                "hwm_count": r.hwm_count,
                "stripe_qty_updated": r.stripe_qty_updated,
                "stripe_qty_updated_at": r.stripe_qty_updated_at.isoformat() if r.stripe_qty_updated_at else None,
            }
            for r in records
        ],
        "total": len(records),
    }


@router.get("/hwm")
def get_hwm_compat(
    subscription_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Compat: soporta GET /api/seats/hwm?subscription_id=123"""
    if not subscription_id:
        raise HTTPException(status_code=400, detail="subscription_id es requerido")
    return get_hwm(subscription_id=subscription_id, days=days, db=db)


@router.post("/sync-stripe")
def sync_stripe_all(db: Session = Depends(get_db)):
    """
    Sincroniza HWM con Stripe quantity para todas las suscripciones Direct activas.
    Pensado para un cron diario como fallback del real-time.
    """
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    pending = db.query(SeatHighWater).filter(
        SeatHighWater.period_date == today,
        SeatHighWater.stripe_qty_updated == False,
    ).all()

    results = []
    for hwm in pending:
        sub = db.query(Subscription).filter(Subscription.id == hwm.subscription_id).first()
        if not sub or _is_partner_metered(sub) or not sub.stripe_subscription_id:
            continue

        ok = _sync_stripe_quantity(sub, hwm.hwm_count)
        if ok:
            hwm.stripe_qty_updated = True
            hwm.stripe_qty_updated_at = datetime.utcnow()
            results.append({"sub_id": sub.id, "qty": hwm.hwm_count, "synced": True})
        else:
            results.append({"sub_id": sub.id, "qty": hwm.hwm_count, "synced": False})

    db.commit()
    return {"synced": len([r for r in results if r["synced"]]), "failed": len([r for r in results if not r["synced"]]), "details": results}


@router.get("/summary/{subscription_id}")
def seat_summary(subscription_id: int, db: Session = Depends(get_db)):
    """Resumen de asientos para una suscripción."""
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(404, "Subscription not found")

    # Últimos 10 eventos
    events = db.query(SeatEvent).filter(
        SeatEvent.subscription_id == subscription_id,
    ).order_by(SeatEvent.created_at.desc()).limit(10).all()

    # HWM del mes actual
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    max_hwm = db.query(func.max(SeatHighWater.hwm_count)).filter(
        SeatHighWater.subscription_id == subscription_id,
        SeatHighWater.period_date >= month_start,
    ).scalar() or 0

    # Contar usuarios en gracia activa (Épica 4)
    now = datetime.utcnow()
    grace_count = db.query(SeatEvent).filter(
        SeatEvent.subscription_id == subscription_id,
        SeatEvent.event_type == SeatEventType.FIRST_LOGIN,
        SeatEvent.grace_expires_at > now,
    ).count()

    return {
        "subscription_id": subscription_id,
        "current_user_count": sub.user_count or 0,
        "current_count": sub.user_count or 0,
        "billing_mode": sub.billing_mode.value if sub.billing_mode else None,
        "is_partner_metered": _is_partner_metered(sub),
        "month_hwm": max_hwm,
        "hwm_count": max_hwm,
        "grace_active_count": grace_count,
        "grace_count": grace_count,
        "billable_count": max_hwm if not _is_partner_metered(sub) else max(0, max_hwm - grace_count),
        "period": month_start.strftime("%Y-%m"),
        "recent_events": [
            {
                "id": e.id,
                "event_type": e.event_type.value,
                "odoo_login": e.odoo_login,
                "user_count_after": e.user_count_after,
                "is_billable": e.is_billable,
                "grace_expires_at": e.grace_expires_at.isoformat() if e.grace_expires_at else None,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
        "last_event": (
            {
                "id": events[0].id,
                "event_type": events[0].event_type.value,
                "odoo_login": events[0].odoo_login,
                "user_count_after": events[0].user_count_after,
                "is_billable": events[0].is_billable,
                "grace_expires_at": events[0].grace_expires_at.isoformat() if events[0].grace_expires_at else None,
                "created_at": events[0].created_at.isoformat() if events[0].created_at else None,
            }
            if events else None
        ),
    }


@router.get("/summary")
def seat_summary_compat(
    subscription_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Compat: soporta GET /api/seats/summary?subscription_id=123"""
    if not subscription_id:
        raise HTTPException(status_code=400, detail="subscription_id es requerido")
    return seat_summary(subscription_id=subscription_id, db=db)


@router.get("/overview")
def seats_overview(
    search: Optional[str] = None,
    partner_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Vista agregada de seats por tenant + agrupación por partner.
    Se usa en UI admin para evitar depender de `subscription_id` manual.
    """
    active_statuses = [
        SubscriptionStatus.active,
        SubscriptionStatus.pending,
        SubscriptionStatus.trialing,
        SubscriptionStatus.past_due,
    ]

    query = (
        db.query(Subscription, Customer, Partner)
        .join(Customer, Customer.id == Subscription.customer_id)
        .outerjoin(Partner, Partner.id == Customer.partner_id)
        .filter(Subscription.status.in_(active_statuses))
    )

    if partner_id:
        query = query.filter(Customer.partner_id == partner_id)

    raw_search = (search or "").strip()
    parsed_subscription_id: Optional[int] = None
    if raw_search:
        if raw_search.isdigit():
            parsed_subscription_id = int(raw_search)
        like = f"%{raw_search}%"
        filter_expr = (
            (Customer.company_name.ilike(like))
            | (Customer.subdomain.ilike(like))
            | (Customer.email.ilike(like))
            | (Partner.company_name.ilike(like))
            | (Subscription.stripe_subscription_id.ilike(like))
            | (Subscription.plan_name.ilike(like))
        )
        if parsed_subscription_id is not None:
            filter_expr = filter_expr | (Subscription.id == parsed_subscription_id)
        query = query.filter(filter_expr)

    rows = query.order_by(
        Partner.company_name.asc().nullsfirst(),
        Customer.company_name.asc(),
    ).all()

    if not rows:
        return {
            "items": [],
            "groups": [],
            "total": 0,
            "generated_at": datetime.utcnow().isoformat(),
        }

    subscription_ids = [sub.id for sub, _, _ in rows]
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    now = datetime.utcnow()

    hwm_rows = (
        db.query(SeatHighWater.subscription_id, func.max(SeatHighWater.hwm_count))
        .filter(
            SeatHighWater.subscription_id.in_(subscription_ids),
            SeatHighWater.period_date >= month_start,
        )
        .group_by(SeatHighWater.subscription_id)
        .all()
    )
    hwm_map = {sid: int(max_hwm or 0) for sid, max_hwm in hwm_rows}

    grace_rows = (
        db.query(SeatEvent.subscription_id, func.count(SeatEvent.id))
        .filter(
            SeatEvent.subscription_id.in_(subscription_ids),
            SeatEvent.event_type == SeatEventType.FIRST_LOGIN,
            SeatEvent.grace_expires_at > now,
        )
        .group_by(SeatEvent.subscription_id)
        .all()
    )
    grace_map = {sid: int(count or 0) for sid, count in grace_rows}

    items = []
    grouped: dict[str, dict] = {}

    for sub, customer, partner in rows:
        month_hwm = hwm_map.get(sub.id, 0)
        grace_count = grace_map.get(sub.id, 0)
        partner_metered = _is_partner_metered(sub)
        billable_count = max(0, month_hwm - grace_count) if partner_metered else month_hwm

        row = {
            "subscription_id": sub.id,
            "stripe_subscription_id": sub.stripe_subscription_id,
            "customer_id": customer.id,
            "company_name": customer.company_name,
            "subdomain": customer.subdomain,
            "email": customer.email,
            "partner_id": partner.id if partner else None,
            "partner_name": partner.company_name if partner else None,
            "plan_name": sub.plan_name,
            "status": sub.status.value if sub.status else None,
            "billing_mode": sub.billing_mode.value if sub.billing_mode else None,
            "current_user_count": int(sub.user_count or 0),
            "month_hwm": month_hwm,
            "grace_active_count": grace_count,
            "billable_count": billable_count,
            "is_partner_metered": partner_metered,
        }
        items.append(row)

        group_key = str(partner.id) if partner else "no-partner"
        if group_key not in grouped:
            grouped[group_key] = {
                "partner_id": partner.id if partner else None,
                "partner_name": partner.company_name if partner else "Sin partner",
                "customers": 0,
                "subscriptions": 0,
                "current_user_count": 0,
                "billable_count": 0,
                "tenants": [],
            }

        group = grouped[group_key]
        group["subscriptions"] += 1
        group["customers"] += 1
        group["current_user_count"] += row["current_user_count"]
        group["billable_count"] += billable_count
        group["tenants"].append(row)

    groups = sorted(grouped.values(), key=lambda g: (g["partner_name"] or "").lower())

    return {
        "items": items,
        "groups": groups,
        "total": len(items),
        "generated_at": datetime.utcnow().isoformat(),
    }
