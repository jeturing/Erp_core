"""
Billing Routes - API para métricas de facturación y pagos
"""
from fastapi import APIRouter, HTTPException, Request, Cookie
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..models.database import (
    Customer, Subscription, SubscriptionStatus, 
    StripeEvent, SessionLocal
)
from .roles import verify_token_with_role
import logging

router = APIRouter(prefix="/api/billing", tags=["Billing"])
logger = logging.getLogger(__name__)

# Precios por plan (USD)
PLAN_PRICES = {
    "basic": 29,
    "pro": 49,
    "enterprise": 99
}


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
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
    db = SessionLocal()
    try:
        # Conteos por estado y plan
        active_subs = db.query(Subscription).filter_by(status=SubscriptionStatus.active).all()
        pending_subs = db.query(Subscription).filter_by(status=SubscriptionStatus.pending).all()
        cancelled_30d = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.cancelled,
            Subscription.updated_at >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Calcular MRR por plan
        plan_counts = {"basic": 0, "pro": 0, "enterprise": 0}
        plan_revenue = {"basic": 0, "pro": 0, "enterprise": 0}
        total_mrr = 0
        
        for sub in active_subs:
            plan = sub.plan_name or "basic"
            price = PLAN_PRICES.get(plan, 29)
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
            plan_revenue[plan] = plan_revenue.get(plan, 0) + price
            total_mrr += price
        
        # Calcular pendiente de cobro
        pending_amount = 0
        for sub in pending_subs:
            plan = sub.plan_name or "basic"
            pending_amount += PLAN_PRICES.get(plan, 29)
        
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
            "cancelled_30d": cancelled_30d
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
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
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
            price = PLAN_PRICES.get(plan, 29)
            
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
                "amount": price,
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
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
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
