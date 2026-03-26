"""
Billing Routes - API para métricas de facturación y pagos
"""
from fastapi import APIRouter, HTTPException, Request, Cookie
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..models.database import (
    Customer, Subscription, SubscriptionStatus, 
    StripeEvent, Plan, SessionLocal
)
from .roles import _require_admin as _require_admin_base, verify_token_with_role
from ..services.pricing import get_plan_prices as _shared_get_plan_prices, get_plan_price_for_sub as _shared_get_plan_price_for_sub
import logging

router = APIRouter(prefix="/api/billing", tags=["Billing"])
logger = logging.getLogger(__name__)


def _get_plan_prices(db) -> dict:
    """Obtiene precios de planes desde la BD. Delega a pricing service."""
    return _shared_get_plan_prices(db)


def _get_plan_price_for_sub(db, sub) -> float:
    """Obtiene precio para una suscripción. Delega a pricing service."""
    return _shared_get_plan_price_for_sub(db, sub)


def _verify_admin(token: str):
    """Verifica que el usuario sea admin"""
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        verify_token_with_role(token, required_role="admin")
    except HTTPException:
        raise


@router.get("/metrics")
async def get_billing_metrics(
    request: Request, 
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """
    Obtiene métricas de facturación para el dashboard de billing.
    
    Retorna:
    - MRR total y del mes
    - Distribución por plan
    - Pagos pendientes
    - Churn rate (últimos 30 días)
    """
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        # Conteos por estado y plan
        active_subs = db.query(Subscription).filter_by(status=SubscriptionStatus.active).all()
        pending_subs = db.query(Subscription).filter_by(status=SubscriptionStatus.pending).all()
        cancelled_30d = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.cancelled,
            Subscription.updated_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Calcular MRR por plan (dinámico desde BD)
        plan_prices = _get_plan_prices(db)
        plan_names = list(set(list(plan_prices.keys()) + ["basic", "pro", "enterprise"]))
        plan_counts = {p: 0 for p in plan_names}
        plan_revenue = {p: 0 for p in plan_names}
        total_mrr = 0
        total_users = 0
        
        for sub in active_subs:
            plan = sub.plan_name or "basic"
            price = _get_plan_price_for_sub(db, sub)
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
            plan_revenue[plan] = plan_revenue.get(plan, 0) + price
            total_mrr += price
            total_users += (sub.user_count or 1)
        
        # Calcular pendiente de cobro
        pending_amount = 0
        for sub in pending_subs:
            pending_amount += _get_plan_price_for_sub(db, sub)
        
        # Calcular churn rate
        total_subs_30d_ago = len(active_subs) + cancelled_30d
        churn_rate = (cancelled_30d / total_subs_30d_ago * 100) if total_subs_30d_ago > 0 else 0
        
        return {
            "mrr_total": total_mrr,
            "month_revenue": total_mrr,  # Simplificado - mismo que MRR
            "pending_amount": pending_amount,
            "pending_count": len(pending_subs),
            "churn_rate": round(churn_rate, 1),
            "plan_distribution": {
                "basic": {
                    "count": plan_counts["basic"],
                    "revenue": plan_revenue["basic"]
                },
                "pro": {
                    "count": plan_counts["pro"],
                    "revenue": plan_revenue["pro"]
                },
                "enterprise": {
                    "count": plan_counts["enterprise"],
                    "revenue": plan_revenue["enterprise"]
                }
            },
            "total_active": len(active_subs),
            "total_pending": len(pending_subs),
            "cancelled_30d": cancelled_30d,
            "total_users": total_users
        }
    except Exception as e:
        logger.error(f"Error obteniendo métricas de billing: {e}")
        # Retornar datos por defecto si hay error
        return {
            "mrr_total": 0,
            "month_revenue": 0,
            "pending_amount": 0,
            "pending_count": 0,
            "churn_rate": 0,
            "plan_distribution": {
                "basic": {"count": 0, "revenue": 0},
                "pro": {"count": 0, "revenue": 0},
                "enterprise": {"count": 0, "revenue": 0}
            },
            "total_active": 0,
            "total_pending": 0,
            "cancelled_30d": 0
        }
    finally:
        db.close()


@router.get("/comparison")
async def get_billing_comparison(
    request: Request,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """
    Comparación mes actual vs mes anterior para el dashboard de billing.
    
    Retorna:
    - MRR actual vs anterior
    - Revenue actual vs anterior
    - Nuevos clientes vs perdidos
    """
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Suscripciones activas actuales
        current_active = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.active
        ).all()
        
        # Nuevos clientes este mes
        new_customers = db.query(Customer).filter(
            Customer.created_at >= current_month_start
        ).count()
        
        # Cancelaciones este mes
        lost_customers = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.cancelled,
            Subscription.updated_at >= current_month_start
        ).count()
        
        # Calcular MRR actual (dinámico con user_count)
        current_mrr = 0
        for sub in current_active:
            current_mrr += _get_plan_price_for_sub(db, sub)
        
        # Estimación mes anterior
        plan_prices = _get_plan_prices(db)
        avg_price = sum(plan_prices.values()) / len(plan_prices) if plan_prices else 29
        previous_mrr = current_mrr
        for _ in range(lost_customers):
            previous_mrr += avg_price
        for _ in range(new_customers):
            previous_mrr -= avg_price
        previous_mrr = max(0, previous_mrr)
        
        # Nombres de meses en español
        month_names = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        current_month_name = f"{month_names[now.month]} {now.year}"
        prev_month = previous_month_start.month
        prev_year = previous_month_start.year
        previous_month_name = f"{month_names[prev_month]} {prev_year}"
        
        return {
            "current_month": current_month_name,
            "previous_month": previous_month_name,
            "current_mrr": current_mrr,
            "previous_mrr": previous_mrr,
            "current_revenue": current_mrr,
            "previous_revenue": previous_mrr,
            "new_customers": new_customers,
            "lost_customers": lost_customers
        }
    except Exception as e:
        logger.error(f"Error obteniendo comparación de billing: {e}")
        now = datetime.utcnow()
        return {
            "current_month": f"Febrero {now.year}",
            "previous_month": f"Enero {now.year}",
            "current_mrr": 0,
            "previous_mrr": 0,
            "current_revenue": 0,
            "previous_revenue": 0,
            "new_customers": 0,
            "lost_customers": 0
        }
    finally:
        db.close()


@router.get("/invoices")
async def get_invoices(
    request: Request,
    access_token: str = Cookie(None),
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Lista facturas/pagos del sistema.
    
    Args:
        limit: Número máximo de resultados (default 20)
        offset: Offset para paginación
        status: Filtrar por estado (paid, pending, failed)
    """
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        query = db.query(Subscription).join(Customer)
        
        if status == "paid":
            query = query.filter(Subscription.status == SubscriptionStatus.active)
        elif status == "pending":
            query = query.filter(Subscription.status == SubscriptionStatus.pending)
        elif status == "failed":
            query = query.filter(Subscription.status == SubscriptionStatus.past_due)
        
        total = query.count()
        subscriptions = query.order_by(Subscription.created_at.desc()).offset(offset).limit(limit).all()
        
        invoices = []
        for sub in subscriptions:
            customer = sub.customer
            plan = sub.plan_name or "basic"
            price = _get_plan_price_for_sub(db, sub)
            user_count = sub.user_count or 1
            
            # Determinar estado de pago
            payment_status = "paid" if sub.status == SubscriptionStatus.active else \
                           "pending" if sub.status == SubscriptionStatus.pending else \
                           "failed" if sub.status == SubscriptionStatus.past_due else "cancelled"
            
            invoices.append({
                "id": sub.id,
                "customer_id": customer.id,
                "company_name": customer.company_name,
                "email": customer.email,
                "subdomain": customer.subdomain,
                "plan": plan,
                "amount": round(price, 2),
                "user_count": user_count,
                "is_admin_account": customer.is_admin_account or False,
                "currency": "USD",
                "status": payment_status,
                "stripe_subscription_id": sub.stripe_subscription_id,
                "created_at": sub.created_at.isoformat() if sub.created_at else None,
                "updated_at": sub.updated_at.isoformat() if sub.updated_at else None
            })
        
        return {
            "invoices": invoices,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error obteniendo facturas: {e}")
        return {"invoices": [], "total": 0, "limit": limit, "offset": offset}
    finally:
        db.close()


@router.get("/stripe-events")
async def get_stripe_events(
    request: Request,
    access_token: str = Cookie(None),
    limit: int = 20
) -> Dict[str, Any]:
    """Obtiene los eventos de Stripe recientes."""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        events = db.query(StripeEvent).order_by(
            StripeEvent.created_at.desc()
        ).limit(limit).all()
        
        return {
            "events": [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "processed": e.processed,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in events
            ],
            "total": len(events)
        }
    except Exception as e:
        logger.error(f"Error obteniendo eventos Stripe: {e}")
        return {"events": [], "total": 0}
    finally:
        db.close()
