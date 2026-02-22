"""
Stripe Sync Routes — Endpoints para sincronización Stripe ↔ BD.

Stripe es la fuente de verdad:
- POST /api/stripe-sync/full          → Sync completo (customers + subs + invoices)
- POST /api/stripe-sync/subscriptions → Solo sincronizar suscripciones
- POST /api/stripe-sync/invoices      → Solo importar facturas
- POST /api/stripe-sync/customers     → Solo vincular stripe_customer_id
- GET  /api/stripe-sync/status        → Estado de la última sincronización
"""
from fastapi import APIRouter, HTTPException, Request, Cookie, Depends
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Invoice,
    SessionLocal, get_db,
)
from .roles import verify_token_with_role
from ..services.stripe_sync import (
    full_stripe_sync,
    sync_subscriptions,
    sync_invoices,
    sync_stripe_customers,
)

router = APIRouter(prefix="/api/stripe-sync", tags=["Stripe Sync"])
logger = logging.getLogger(__name__)

# Cache del último resultado de sync
_last_sync_result: Dict[str, Any] = {}
_last_sync_time: Optional[datetime] = None


def _verify_admin(request: Request, token: str = None):
    """Extrae y verifica token de admin."""
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    verify_token_with_role(token, required_role="admin")


@router.post("/full")
async def run_full_sync(
    request: Request,
    access_token: str = Cookie(None),
    months_back: int = 3,
) -> Dict[str, Any]:
    """
    Sincronización completa: Stripe → BD.
    
    1. Vincula stripe_customer_id por email
    2. Sincroniza suscripciones (crea/actualiza)
    3. Importa facturas reales de Stripe
    
    Args:
        months_back: Meses hacia atrás para importar facturas (default 3)
    """
    global _last_sync_result, _last_sync_time
    _verify_admin(request, access_token)

    db = SessionLocal()
    try:
        result = full_stripe_sync(db, months_back=months_back)
        _last_sync_result = result
        _last_sync_time = datetime.utcnow()
        return {
            "success": True,
            "synced_at": _last_sync_time.isoformat(),
            **result,
        }
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/subscriptions")
async def run_subscription_sync(
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Sincroniza solo suscripciones de Stripe → BD."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        result = sync_subscriptions(db)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/invoices")
async def run_invoice_sync(
    request: Request,
    access_token: str = Cookie(None),
    months_back: int = 3,
) -> Dict[str, Any]:
    """Importa facturas reales de Stripe → BD."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        result = sync_invoices(db, months_back=months_back)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/customers")
async def run_customer_sync(
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Vincula stripe_customer_id para clientes sin vincular."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        result = sync_stripe_customers(db)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/status")
async def get_sync_status(
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Estado actual: última sincronización + resumen de BD."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        total_customers = db.query(Customer).count()
        linked_customers = db.query(Customer).filter(
            Customer.stripe_customer_id != None
        ).count()
        admin_customers = db.query(Customer).filter(
            Customer.is_admin_account == True
        ).count()

        total_subs = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.active
        ).count()
        linked_subs = db.query(Subscription).filter(
            Subscription.stripe_subscription_id != None,
            Subscription.status == SubscriptionStatus.active,
        ).count()

        total_invoices = db.query(Invoice).count()
        stripe_invoices = db.query(Invoice).filter(
            Invoice.stripe_invoice_id != None
        ).count()

        return {
            "last_sync": _last_sync_time.isoformat() if _last_sync_time else None,
            "last_result": _last_sync_result or None,
            "database": {
                "customers": {
                    "total": total_customers,
                    "stripe_linked": linked_customers,
                    "admin_accounts": admin_customers,
                    "unlinked": total_customers - linked_customers - admin_customers,
                },
                "subscriptions": {
                    "active": total_subs,
                    "stripe_linked": linked_subs,
                    "unlinked": total_subs - linked_subs,
                },
                "invoices": {
                    "total": total_invoices,
                    "from_stripe": stripe_invoices,
                    "manual": total_invoices - stripe_invoices,
                },
            },
        }
    finally:
        db.close()
