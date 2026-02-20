"""
Plans Management Routes - CRUD de planes y cálculo de facturación por usuarios
"""
from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from ..models.database import Plan, Customer, Subscription, SubscriptionStatus, SessionLocal
from .roles import verify_token_with_role
import json
import logging

router = APIRouter(prefix="/api/plans", tags=["Plans"])
logger = logging.getLogger(__name__)


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


# DTOs
class PlanCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    base_price: float
    price_per_user: float = 0
    included_users: int = 1
    max_users: int = 0
    max_domains: int = 0
    max_storage_mb: int = 0
    max_websites: int = 1
    max_companies: int = 1
    max_backups: int = 0
    max_api_calls_day: int = 0
    currency: str = "USD"
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    features: Optional[str] = None  # JSON string
    sort_order: int = 0


class PlanUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    price_per_user: Optional[float] = None
    included_users: Optional[int] = None
    max_users: Optional[int] = None
    max_domains: Optional[int] = None
    max_storage_mb: Optional[int] = None
    max_websites: Optional[int] = None
    max_companies: Optional[int] = None
    max_backups: Optional[int] = None
    max_api_calls_day: Optional[int] = None
    stripe_price_id: Optional[str] = None
    stripe_product_id: Optional[str] = None
    features: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanCalculateRequest(BaseModel):
    plan_name: str
    user_count: int


# Routes
@router.get("")
async def list_plans(
    request: Request,
    access_token: str = Cookie(None),
    include_inactive: bool = False
) -> Dict[str, Any]:
    """Lista todos los planes disponibles."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        query = db.query(Plan)
        if not include_inactive:
            query = query.filter(Plan.is_active == True)
        plans = query.order_by(Plan.sort_order, Plan.base_price).all()

        items = []
        for p in plans:
            # Contar suscriptores activos de este plan
            sub_count = db.query(Subscription).filter(
                Subscription.plan_name == p.name,
                Subscription.status == SubscriptionStatus.active
            ).count()

            items.append({
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "description": p.description,
                "base_price": p.base_price,
                "price_per_user": p.price_per_user,
                "included_users": p.included_users,
                "max_users": p.max_users,
                "max_domains": p.max_domains,
                "max_storage_mb": p.max_storage_mb,
                "max_websites": p.max_websites,
                "max_companies": p.max_companies,
                "max_backups": p.max_backups,
                "max_api_calls_day": p.max_api_calls_day,
                "currency": p.currency,
                "stripe_price_id": p.stripe_price_id,
                "stripe_product_id": p.stripe_product_id,
                "features": json.loads(p.features) if p.features else [],
                "is_active": p.is_active,
                "sort_order": p.sort_order,
                "active_subscribers": sub_count,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })

        return {"items": items, "total": len(items)}
    finally:
        db.close()


@router.post("")
async def create_plan(
    request: Request,
    payload: PlanCreate,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Crea un nuevo plan."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        existing = db.query(Plan).filter(Plan.name == payload.name).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Plan '{payload.name}' ya existe")

        plan = Plan(
            name=payload.name,
            display_name=payload.display_name,
            description=payload.description,
            base_price=payload.base_price,
            price_per_user=payload.price_per_user,
            included_users=payload.included_users,
            max_users=payload.max_users,
            max_domains=payload.max_domains,
            max_storage_mb=payload.max_storage_mb,
            max_websites=payload.max_websites,
            max_companies=payload.max_companies,
            max_backups=payload.max_backups,
            max_api_calls_day=payload.max_api_calls_day,
            currency=payload.currency,
            stripe_price_id=payload.stripe_price_id,
            stripe_product_id=payload.stripe_product_id,
            features=payload.features,
            sort_order=payload.sort_order,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        return {"message": "Plan creado", "plan": {"id": plan.id, "name": plan.name}}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/{plan_id}")
async def update_plan(
    plan_id: int,
    request: Request,
    payload: PlanUpdate,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Actualiza un plan existente."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan no encontrado")

        update_data = payload.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan, key, value)

        db.commit()

        # Si cambiaron precios, recalcular montos de suscripciones activas
        if "base_price" in update_data or "price_per_user" in update_data or "included_users" in update_data:
            recalculated = _recalculate_subscriptions(db, plan.name)
            return {"message": f"Plan actualizado. {recalculated} suscripciones recalculadas."}

        return {"message": "Plan actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int,
    request: Request,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Desactiva un plan (soft delete). No permite eliminar con suscriptores."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan no encontrado")

        active_subs = db.query(Subscription).filter(
            Subscription.plan_name == plan.name,
            Subscription.status == SubscriptionStatus.active
        ).count()

        if active_subs > 0:
            raise HTTPException(
                status_code=409,
                detail=f"No se puede eliminar: {active_subs} suscripciones activas"
            )

        plan.is_active = False
        db.commit()
        return {"message": f"Plan '{plan.name}' desactivado"}
    finally:
        db.close()


@router.post("/calculate")
async def calculate_price(
    request: Request,
    payload: PlanCalculateRequest,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Calcula el precio mensual para un plan y cantidad de usuarios."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter(Plan.name == payload.plan_name, Plan.is_active == True).first()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan '{payload.plan_name}' no encontrado")

        monthly = plan.calculate_monthly(payload.user_count)
        extra_users = max(0, payload.user_count - plan.included_users)

        return {
            "plan": plan.name,
            "user_count": payload.user_count,
            "included_users": plan.included_users,
            "extra_users": extra_users,
            "base_price": plan.base_price,
            "extra_cost": extra_users * plan.price_per_user,
            "monthly_total": monthly,
            "currency": plan.currency
        }
    finally:
        db.close()


def _recalculate_subscriptions(db, plan_name: str) -> int:
    """Recalcula monthly_amount de todas las suscripciones activas de un plan."""
    plan = db.query(Plan).filter(Plan.name == plan_name).first()
    if not plan:
        return 0

    subs = db.query(Subscription).filter(
        Subscription.plan_name == plan_name,
        Subscription.status == SubscriptionStatus.active
    ).all()

    count = 0
    for sub in subs:
        user_count = sub.user_count or 1
        new_amount = plan.calculate_monthly(user_count)
        if sub.monthly_amount != new_amount:
            sub.monthly_amount = new_amount
            count += 1

    db.commit()
    return count


def recalculate_all_subscriptions():
    """Recalcula todos los montos. Llamar al actualizar precios de planes."""
    db = SessionLocal()
    try:
        plans = db.query(Plan).filter(Plan.is_active == True).all()
        total = 0
        for plan in plans:
            total += _recalculate_subscriptions(db, plan.name)
        return total
    finally:
        db.close()
