"""
Pricing Service — Cálculo dinámico de precios para suscripciones.

Módulo compartido usado por:
- dashboard.py (MRR metrics)
- billing.py (billing metrics + invoice list)
- plans.py (recálculo de suscripciones)

Elimina duplicación de lógica de pricing y el price_map hardcodeado.
"""
import logging
from typing import Optional

from ..models.database import Customer, PartnerPricingOverride, Plan, SessionLocal

logger = logging.getLogger(__name__)


def get_plan_prices(db) -> dict:
    """Obtiene precios base de planes desde la BD. Fallback a defaults si no hay planes."""
    plans = db.query(Plan).filter(Plan.is_active == True).all()
    if plans:
        return {p.name: p.base_price for p in plans}
    # Fallback — solo si la tabla plans está vacía
    logger.warning("No se encontraron planes activos en BD, usando fallback")
    return {"basic": 160, "pro": 200, "enterprise": 400}


def get_subscription_customer(db, sub, customer: Optional[Customer] = None) -> Optional[Customer]:
    """Obtiene el customer de una suscripción sin repetir queries."""
    if customer is not None:
        return customer
    if getattr(sub, "customer", None) is not None:
        return sub.customer
    if not getattr(sub, "customer_id", None):
        return None
    return db.query(Customer).filter(Customer.id == sub.customer_id).first()


def resolve_subscription_partner_id(db, sub, customer: Optional[Customer] = None) -> Optional[int]:
    """Partner efectivo: owner_partner_id tiene prioridad sobre customer.partner_id."""
    if getattr(sub, "owner_partner_id", None):
        return sub.owner_partner_id

    customer = get_subscription_customer(db, sub, customer=customer)
    return customer.partner_id if customer else None


def get_effective_plan_snapshot(
    db,
    sub,
    *,
    customer: Optional[Customer] = None,
    plan: Optional[Plan] = None,
    user_count: Optional[int] = None,
) -> dict:
    """
    Resuelve el pricing efectivo de una suscripción usando override de partner si aplica.

    Returns:
        {
            plan, customer, partner_id, user_count,
            base_price, price_per_user, included_users,
            extra_users, total, pricing_source
        }
    """
    customer = get_subscription_customer(db, sub, customer=customer)
    plan = plan or db.query(Plan).filter(
        Plan.name == sub.plan_name,
        Plan.is_active == True,
    ).first()

    normalized_users = user_count
    if normalized_users is None:
        normalized_users = getattr(sub, "user_count", None) or (customer.user_count if customer else None) or 1
    try:
        normalized_users = max(1, int(normalized_users))
    except (TypeError, ValueError):
        normalized_users = 1

    snapshot = {
        "plan": plan,
        "customer": customer,
        "partner_id": resolve_subscription_partner_id(db, sub, customer=customer),
        "user_count": normalized_users,
        "base_price": 0.0,
        "price_per_user": 0.0,
        "included_users": 1,
        "extra_users": 0,
        "total": 0.0,
        "pricing_source": "fallback_zero",
        "override": None,
    }

    if not plan:
        fallback_prices = get_plan_prices(db)
        fallback_total = float(getattr(sub, "monthly_amount", 0) or fallback_prices.get(sub.plan_name or "basic", 160))
        snapshot.update({
            "base_price": fallback_total,
            "total": fallback_total,
            "pricing_source": "subscription_monthly_amount" if getattr(sub, "monthly_amount", 0) else "fallback_plan_price",
        })
        return snapshot

    base_price = float(plan.base_price or 0)
    price_per_user = float(plan.price_per_user or 0)
    included_users = int(plan.included_users or 1)
    pricing_source = "plan_default"

    partner_id = snapshot["partner_id"]
    if partner_id:
        override = db.query(PartnerPricingOverride).filter(
            PartnerPricingOverride.partner_id == partner_id,
            PartnerPricingOverride.plan_name == plan.name,
            PartnerPricingOverride.is_active == True,
        ).first()
        if override:
            if override.base_price_override is not None:
                base_price = float(override.base_price_override)
            if override.price_per_user_override is not None:
                price_per_user = float(override.price_per_user_override)
            if override.included_users_override is not None:
                included_users = int(override.included_users_override)
            pricing_source = "partner_override"
            snapshot["override"] = override

    extra_users = max(0, normalized_users - included_users)
    total = base_price + (extra_users * price_per_user)

    snapshot.update({
        "base_price": base_price,
        "price_per_user": price_per_user,
        "included_users": included_users,
        "extra_users": extra_users,
        "total": float(total),
        "pricing_source": pricing_source,
    })
    return snapshot


def calculate_effective_subscription_amount(
    db,
    sub,
    *,
    customer: Optional[Customer] = None,
    plan: Optional[Plan] = None,
    user_count: Optional[int] = None,
) -> float:
    """Monto efectivo de la suscripción según plan + override de partner."""
    snapshot = get_effective_plan_snapshot(
        db,
        sub,
        customer=customer,
        plan=plan,
        user_count=user_count,
    )
    return float(snapshot["total"])


def recalculate_subscription_monthly_amount(
    db,
    sub,
    *,
    customer: Optional[Customer] = None,
    plan: Optional[Plan] = None,
    user_count: Optional[int] = None,
) -> float:
    """Recalcula y persiste monthly_amount usando el pricing efectivo."""
    snapshot = get_effective_plan_snapshot(
        db,
        sub,
        customer=customer,
        plan=plan,
        user_count=user_count,
    )
    sub.monthly_amount = snapshot["total"]
    if user_count is not None:
        sub.user_count = snapshot["user_count"]
    return float(snapshot["total"])


def get_plan_price_for_sub(db, sub) -> float:
    """Obtiene precio para una suscripción específica.
    
    Prioridad:
    1. Admin account → $0
    2. monthly_amount de la BD (ya calculado con overrides) → usar directo
    3. Cálculo dinámico desde Plan.calculate_monthly() → incluye partner overrides
    4. Fallback a precios base
    
    Args:
        db: Sesión SQLAlchemy
        sub: Objeto Subscription
    
    Returns:
        float: Precio mensual de la suscripción
    """
    # Check if customer is admin account
    customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
    if customer and customer.is_admin_account:
        return 0  # Admin account exento
    
    snapshot = get_effective_plan_snapshot(db, sub, customer=customer)
    return float(snapshot["total"])
