"""
Pricing Service — Cálculo dinámico de precios para suscripciones.

Módulo compartido usado por:
- dashboard.py (MRR metrics)
- billing.py (billing metrics + invoice list)
- plans.py (recálculo de suscripciones)

Elimina duplicación de lógica de pricing y el price_map hardcodeado.
"""
import logging
from ..models.database import Customer, Plan, SessionLocal

logger = logging.getLogger(__name__)


def get_plan_prices(db) -> dict:
    """Obtiene precios base de planes desde la BD. Fallback a defaults si no hay planes."""
    plans = db.query(Plan).filter(Plan.is_active == True).all()
    if plans:
        return {p.name: p.base_price for p in plans}
    # Fallback — solo si la tabla plans está vacía
    logger.warning("No se encontraron planes activos en BD, usando fallback")
    return {"basic": 160, "pro": 200, "enterprise": 400}


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
    
    # Si monthly_amount está definido en BD, usarlo como fuente de verdad
    if sub.monthly_amount and sub.monthly_amount > 0:
        return sub.monthly_amount
    
    # Si no, calcular desde Plan (incluye partner overrides)
    plan = db.query(Plan).filter(Plan.name == sub.plan_name, Plan.is_active == True).first()
    if plan:
        user_count = sub.user_count or 1
        partner_id = customer.partner_id if customer else None
        return plan.calculate_monthly(user_count, partner_id=partner_id)
    
    # Fallback con precios reales
    fallback = get_plan_prices(db)
    return fallback.get(sub.plan_name or "basic", 160)
