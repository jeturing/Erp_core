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
import os
import logging

from ..models.database import (
    SeatEvent, SeatHighWater, Subscription, SeatEventType,
    BillingMode, get_db
)

router = APIRouter(prefix="/api/seats", tags=["Seats"])
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

GRACE_HOURS = int(os.getenv("SEAT_GRACE_HOURS", "8"))


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
    return sub.billing_mode in (
        BillingMode.PARTNER_DIRECT,
        BillingMode.PARTNER_PAYS_FOR_CLIENT,
    )


def _update_hwm(db: Session, sub_id: int, count: int) -> SeatHighWater:
    """Actualiza high-water mark para hoy. Retorna o crea registro."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    hwm = db.query(SeatHighWater).filter(
        SeatHighWater.subscription_id == sub_id,
        SeatHighWater.period_date == today,
    ).first()

    if hwm:
        if count > hwm.hwm_count:
            hwm.hwm_count = count
    else:
        hwm = SeatHighWater(
            subscription_id=sub_id,
            period_date=today,
            hwm_count=count,
        )
        db.add(hwm)
    return hwm


def _sync_stripe_quantity(sub: Subscription, qty: int) -> bool:
    """Actualiza quantity en Stripe subscription item."""
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

    # Determinar si es billable
    is_billable = False
    grace_expires = None

    if is_partner:
        # Épica 4: Solo FIRST_LOGIN es billable, con grace de 8h
        if event_type == SeatEventType.FIRST_LOGIN:
            is_billable = True
            grace_expires = datetime.utcnow() + timedelta(hours=GRACE_HOURS)
    else:
        # Épica 3: Todo evento que incrementa cuenta es billable
        if event_type in (SeatEventType.USER_CREATED, SeatEventType.USER_REACTIVATED, SeatEventType.FIRST_LOGIN):
            is_billable = True

    # Crear evento
    event = SeatEvent(
        subscription_id=sub.id,
        event_type=event_type,
        odoo_user_id=payload.odoo_user_id,
        odoo_login=payload.odoo_login,
        user_count_after=payload.user_count_after,
        is_billable=is_billable,
        grace_expires_at=grace_expires,
        source=payload.source,
        metadata_json=payload.metadata,
    )
    db.add(event)

    # Actualizar HWM
    hwm = _update_hwm(db, sub.id, payload.user_count_after)

    # Épica 3: Sync Stripe quantity en real-time si Direct
    stripe_synced = False
    if not is_partner and is_billable and sub.stripe_subscription_id:
        stripe_synced = _sync_stripe_quantity(sub, payload.user_count_after)
        if stripe_synced:
            hwm.stripe_qty_updated = True
            hwm.stripe_qty_updated_at = datetime.utcnow()

    # Actualizar user_count en subscription
    sub.user_count = payload.user_count_after
    sub.updated_at = datetime.utcnow()

    db.commit()

    return {
        "event_id": event.id,
        "subscription_id": sub.id,
        "event_type": event_type.value,
        "user_count_after": payload.user_count_after,
        "is_billable": is_billable,
        "is_partner_metered": is_partner,
        "grace_expires_at": grace_expires.isoformat() if grace_expires else None,
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
                "date": r.period_date.isoformat(),
                "hwm_count": r.hwm_count,
                "stripe_qty_updated": r.stripe_qty_updated,
            }
            for r in records
        ],
    }


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
        "billing_mode": sub.billing_mode.value if sub.billing_mode else None,
        "is_partner_metered": _is_partner_metered(sub),
        "month_hwm": max_hwm,
        "grace_active_count": grace_count,
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
    }
