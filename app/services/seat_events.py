"""
Seat Events Service — helpers reutilizables para HWM y exclusión de cuentas no facturables.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..models.database import (
    BillingMode,
    Customer,
    SeatEvent,
    SeatEventType,
    SeatHighWater,
    Subscription,
)


def get_non_billable_logins(
    subdomain: str,
    *,
    customer: Optional[Customer] = None,
    admin_email: Optional[str] = None,
) -> set[str]:
    """Cuentas internas que no deben cobrarse como seat."""
    logins = {
        "admin",
        "__system__",
        f"{(subdomain or '').strip().lower()}@sajet.us",
    }

    if customer and customer.email:
        logins.add(customer.email.strip().lower())
    if admin_email:
        logins.add(admin_email.strip().lower())

    return {item for item in logins if item}


def is_billable_user(
    subdomain: str,
    *,
    login: Optional[str],
    share: bool = False,
    active: bool = True,
    customer: Optional[Customer] = None,
    admin_email: Optional[str] = None,
) -> bool:
    """Determina si una cuenta Odoo debe contarse como seat facturable."""
    if share or not active:
        return False

    normalized_login = (login or "").strip().lower()
    if not normalized_login:
        return False

    return normalized_login not in get_non_billable_logins(
        subdomain,
        customer=customer,
        admin_email=admin_email,
    )


def is_partner_metered(subscription: Subscription) -> bool:
    """Billing mode partner usa semántica distinta de billable events."""
    return subscription.billing_mode in (
        BillingMode.PARTNER_DIRECT,
        BillingMode.PARTNER_PAYS_FOR_CLIENT,
    )


def update_hwm(db: Session, subscription_id: int, count: int) -> SeatHighWater:
    """Actualiza o crea el snapshot diario del high-water mark."""
    today = datetime.now(timezone.utc).replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
    hwm = db.query(SeatHighWater).filter(
        SeatHighWater.subscription_id == subscription_id,
        SeatHighWater.period_date == today,
    ).first()

    if hwm:
        if count > hwm.hwm_count:
            hwm.hwm_count = count
    else:
        hwm = SeatHighWater(
            subscription_id=subscription_id,
            period_date=today,
            hwm_count=count,
        )
        db.add(hwm)

    return hwm


def record_seat_event(
    db: Session,
    subscription: Subscription,
    *,
    event_type: SeatEventType,
    user_count_after: int,
    odoo_user_id: Optional[int] = None,
    odoo_login: Optional[str] = None,
    source: str = "webhook",
    metadata: Optional[dict] = None,
) -> tuple[SeatEvent, SeatHighWater]:
    """Registra un seat event y actualiza HWM local."""
    partner_metered = is_partner_metered(subscription)
    is_billable = False
    grace_expires = None

    if partner_metered:
        if event_type == SeatEventType.FIRST_LOGIN:
            is_billable = True
            grace_expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8)
    else:
        if event_type in (
            SeatEventType.USER_CREATED,
            SeatEventType.USER_REACTIVATED,
            SeatEventType.FIRST_LOGIN,
        ):
            is_billable = True

    event = SeatEvent(
        subscription_id=subscription.id,
        event_type=event_type,
        odoo_user_id=odoo_user_id,
        odoo_login=odoo_login,
        user_count_after=user_count_after,
        is_billable=is_billable,
        grace_expires_at=grace_expires,
        source=source,
        metadata_json=metadata or {},
    )
    db.add(event)

    hwm = update_hwm(db, subscription.id, user_count_after)
    subscription.user_count = user_count_after
    subscription.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if subscription.customer is not None:
        subscription.customer.user_count = user_count_after

    return event, hwm


def record_hwm_snapshot(
    db: Session,
    subscription: Subscription,
    *,
    user_count_after: int,
    source: str = "snapshot",
    metadata: Optional[dict] = None,
) -> tuple[SeatEvent, SeatHighWater]:
    """Registra snapshot agregado de HWM sin tratarlo como evento facturable."""
    event = SeatEvent(
        subscription_id=subscription.id,
        event_type=SeatEventType.HWM_SNAPSHOT,
        user_count_after=user_count_after,
        is_billable=False,
        source=source,
        metadata_json=metadata or {},
    )
    db.add(event)

    hwm = update_hwm(db, subscription.id, user_count_after)
    subscription.user_count = user_count_after
    subscription.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if subscription.customer is not None:
        subscription.customer.user_count = user_count_after

    return event, hwm
