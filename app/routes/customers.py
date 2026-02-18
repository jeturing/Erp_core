"""
Customers Management Routes - Mantenimiento de clientes, montos y user_count
"""
from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Plan,
    TenantDeployment, SessionLocal
)
from .roles import verify_token_with_role
import logging

router = APIRouter(prefix="/api/customers", tags=["Customers"])
logger = logging.getLogger(__name__)


def _verify_admin(request: Request, token: str = None):
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    verify_token_with_role(token, required_role="admin")


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    user_count: Optional[int] = None
    is_admin_account: Optional[bool] = None
    plan_name: Optional[str] = None  # Cambiar plan de la suscripción
    stripe_customer_id: Optional[str] = None


class UserCountUpdate(BaseModel):
    user_count: int


@router.get("")
async def list_customers(
    request: Request,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Lista todos los clientes con sus suscripciones, montos y user_count."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
        items = []

        for c in customers:
            # Obtener suscripción activa
            sub = db.query(Subscription).filter(
                Subscription.customer_id == c.id,
                Subscription.status == SubscriptionStatus.active
            ).first()

            # Obtener plan si existe
            plan_data = None
            calculated_amount = 0
            if sub:
                plan = db.query(Plan).filter(
                    Plan.name == sub.plan_name,
                    Plan.is_active == True
                ).first()
                if plan:
                    user_count = c.user_count or sub.user_count or 1
                    calculated_amount = plan.calculate_monthly(user_count)
                    plan_data = {
                        "name": plan.name,
                        "display_name": plan.display_name,
                        "base_price": plan.base_price,
                        "price_per_user": plan.price_per_user,
                        "included_users": plan.included_users,
                    }

            # Deployment info (via subscription)
            deployment = None
            if sub:
                deployment = db.query(TenantDeployment).filter(
                    TenantDeployment.subscription_id == sub.id
                ).first()

            items.append({
                "id": c.id,
                "company_name": c.company_name,
                "email": c.email,
                "full_name": c.full_name,
                "subdomain": c.subdomain,
                "user_count": c.user_count or 1,
                "is_admin_account": c.is_admin_account or False,
                "stripe_customer_id": c.stripe_customer_id,
                "subscription": {
                    "id": sub.id,
                    "plan_name": sub.plan_name,
                    "status": sub.status.value if sub.status else None,
                    "monthly_amount": sub.monthly_amount,
                    "calculated_amount": calculated_amount,
                    "user_count": sub.user_count or 1,
                    "start_date": sub.current_period_start.isoformat() if sub.current_period_start else (sub.created_at.isoformat() if sub.created_at else None),
                } if sub else None,
                "plan": plan_data,
                "deployment": {
                    "subdomain": deployment.subdomain,
                    "database_name": deployment.database_name,
                    "tunnel_active": deployment.tunnel_active,
                } if deployment else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

        # Resumen
        total_users = sum(i.get("user_count", 1) for i in items if not i.get("is_admin_account"))
        total_mrr = sum(
            (i["subscription"]["calculated_amount"] if i["subscription"] else 0)
            for i in items if not i.get("is_admin_account")
        )
        admin_count = sum(1 for i in items if i.get("is_admin_account"))

        return {
            "items": items,
            "total": len(items),
            "summary": {
                "total_users": total_users,
                "total_mrr": round(total_mrr, 2),
                "admin_accounts": admin_count,
                "billable_accounts": len(items) - admin_count,
            }
        }
    finally:
        db.close()


@router.put("/{customer_id}")
async def update_customer(
    customer_id: int,
    request: Request,
    payload: CustomerUpdate,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Actualiza un cliente: user_count, plan, is_admin, etc."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        messages = []

        # Actualizar campos simples
        if payload.company_name is not None:
            customer.company_name = payload.company_name
        if payload.stripe_customer_id is not None:
            # Convertir string vacío a None para evitar violación de unique constraint
            customer.stripe_customer_id = payload.stripe_customer_id.strip() or None
        if payload.is_admin_account is not None:
            customer.is_admin_account = payload.is_admin_account
            if payload.is_admin_account:
                messages.append("Marcado como cuenta admin (exento de facturación)")

        # Actualizar user_count y recalcular
        if payload.user_count is not None:
            old_count = customer.user_count or 1
            customer.user_count = payload.user_count
            messages.append(f"Usuarios: {old_count} → {payload.user_count}")

            # Recalcular suscripción
            sub = db.query(Subscription).filter(
                Subscription.customer_id == customer.id,
                Subscription.status == SubscriptionStatus.active
            ).first()
            if sub:
                sub.user_count = payload.user_count
                plan = db.query(Plan).filter(Plan.name == sub.plan_name).first()
                if plan:
                    new_amount = plan.calculate_monthly(payload.user_count)
                    old_amount = sub.monthly_amount or 0
                    sub.monthly_amount = new_amount
                    messages.append(f"Monto: ${old_amount:.2f} → ${new_amount:.2f}")

        # Cambiar plan
        if payload.plan_name is not None:
            sub = db.query(Subscription).filter(
                Subscription.customer_id == customer.id,
                Subscription.status == SubscriptionStatus.active
            ).first()
            if sub:
                new_plan = db.query(Plan).filter(
                    Plan.name == payload.plan_name,
                    Plan.is_active == True
                ).first()
                if not new_plan:
                    raise HTTPException(status_code=404, detail=f"Plan '{payload.plan_name}' no encontrado")

                old_plan = sub.plan_name
                sub.plan_name = new_plan.name
                user_count = customer.user_count or sub.user_count or 1
                sub.monthly_amount = new_plan.calculate_monthly(user_count)
                messages.append(f"Plan: {old_plan} → {new_plan.name} (${sub.monthly_amount:.2f}/mes)")

        db.commit()
        return {
            "message": "Cliente actualizado",
            "changes": messages,
            "customer_id": customer_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando cliente {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/{customer_id}/users")
async def update_user_count(
    customer_id: int,
    request: Request,
    payload: UserCountUpdate,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Endpoint dedicado para incrementar/decrementar usuarios y recalcular factura."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if customer.is_admin_account:
            raise HTTPException(status_code=400, detail="Cuenta admin exenta de facturación")

        if payload.user_count < 1:
            raise HTTPException(status_code=400, detail="Mínimo 1 usuario")

        old_count = customer.user_count or 1
        customer.user_count = payload.user_count

        sub = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active
        ).first()

        result = {
            "customer_id": customer_id,
            "old_user_count": old_count,
            "new_user_count": payload.user_count,
        }

        if sub:
            sub.user_count = payload.user_count
            plan = db.query(Plan).filter(Plan.name == sub.plan_name).first()
            if plan:
                old_amount = sub.monthly_amount or 0
                new_amount = plan.calculate_monthly(payload.user_count)
                sub.monthly_amount = new_amount

                extra_users = max(0, payload.user_count - plan.included_users)
                result.update({
                    "plan": plan.name,
                    "included_users": plan.included_users,
                    "extra_users": extra_users,
                    "old_monthly": round(old_amount, 2),
                    "new_monthly": round(new_amount, 2),
                    "difference": round(new_amount - old_amount, 2),
                })

        db.commit()
        return result
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/recalculate-all")
async def recalculate_all(
    request: Request,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Recalcula montos de todas las suscripciones activas basado en planes actuales."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        plans = {p.name: p for p in db.query(Plan).filter(Plan.is_active == True).all()}
        subs = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.active
        ).all()

        updated = 0
        skipped_admin = 0
        details = []

        for sub in subs:
            # Check if admin account
            customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
            if customer and customer.is_admin_account:
                if sub.monthly_amount != 0:
                    sub.monthly_amount = 0
                    updated += 1
                skipped_admin += 1
                continue

            plan = plans.get(sub.plan_name)
            if not plan:
                continue

            user_count = (customer.user_count if customer else None) or sub.user_count or 1
            new_amount = plan.calculate_monthly(user_count)
            old_amount = sub.monthly_amount or 0

            if abs(new_amount - old_amount) > 0.01:
                sub.monthly_amount = new_amount
                sub.user_count = user_count
                updated += 1
                details.append({
                    "customer": customer.company_name if customer else f"ID:{sub.customer_id}",
                    "plan": sub.plan_name,
                    "users": user_count,
                    "old": round(old_amount, 2),
                    "new": round(new_amount, 2),
                })

        db.commit()
        return {
            "message": f"{updated} suscripciones actualizadas",
            "admin_accounts": skipped_admin,
            "details": details,
        }
    finally:
        db.close()
