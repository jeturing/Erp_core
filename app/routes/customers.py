"""
Customers Management Routes - Mantenimiento de clientes, montos y user_count
"""
from fastapi import APIRouter, HTTPException, Request, Cookie, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Plan, CustomerStatus,
    TenantDeployment, CustomDomain, SessionLocal,
    BillingMode, PayerType, CollectorType, InvoiceIssuer,
    ProvisioningAuditLog,
)
from .roles import verify_token_with_role
from ..config import get_runtime_setting
from ..utils.ip import get_real_ip
import stripe
import logging
import secrets

router = APIRouter(prefix="/api/customers", tags=["Customers"])
logger = logging.getLogger(__name__)

PROVISIONING_PENDING_CUSTOMER_MESSAGE = (
    "Tu orden será trabajada por el equipo interno. "
    "Te notificaremos por correo cuando el tenant esté completado."
)


def _append_customer_note(customer: Customer, note: str) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    marker = f"[{now}] {note}"
    previous = (customer.notes or "").strip()
    if not previous:
        customer.notes = marker
        return
    lines = previous.splitlines()
    lines.append(marker)
    customer.notes = "\n".join(lines[-20:])


def _add_provisioning_audit(
    db,
    *,
    trace_id: str,
    subdomain: str,
    customer_id: Optional[int],
    subscription_id: Optional[int],
    source: str,
    action: str,
    status: str,
    message: str,
    error_detail: Optional[str] = None,
    payload: Optional[dict] = None,
) -> None:
    db.add(
        ProvisioningAuditLog(
            trace_id=trace_id,
            subdomain=subdomain,
            customer_id=customer_id,
            subscription_id=subscription_id,
            source=source,
            action=action,
            status=status,
            message=message,
            error_detail=error_detail,
            payload=payload or {},
        )
    )


def _persist_lifecycle_audit(
    db,
    *,
    trace_id: str,
    subdomain: str,
    customer_id: Optional[int],
    subscription_id: Optional[int],
    source: str,
    prefix: str,
    op_result,
) -> None:
    _add_provisioning_audit(
        db,
        trace_id=trace_id,
        subdomain=subdomain,
        customer_id=customer_id,
        subscription_id=subscription_id,
        source=source,
        action=f"{prefix}.summary",
        status="success" if op_result.success else "failed",
        message="Operación completada" if op_result.success else "Operación fallida",
        error_detail=op_result.error,
        payload=op_result.as_dict(),
    )

    for step in (op_result.steps or []):
        _add_provisioning_audit(
            db,
            trace_id=trace_id,
            subdomain=subdomain,
            customer_id=customer_id,
            subscription_id=subscription_id,
            source=source,
            action=f"{prefix}.{step.name}",
            status="success" if step.success else "failed",
            message="Paso completado" if step.success else "Paso fallido",
            error_detail=step.error,
            payload=step.detail or {},
        )

    for step in (op_result.compensations or []):
        _add_provisioning_audit(
            db,
            trace_id=trace_id,
            subdomain=subdomain,
            customer_id=customer_id,
            subscription_id=subscription_id,
            source=source,
            action=f"{prefix}.{step.name}",
            status="rolled_back" if step.success else "rollback_failed",
            message="Compensación ejecutada" if step.success else "Compensación fallida",
            error_detail=step.error,
            payload=step.detail or {},
        )


def _has_blocking_provisioning_failure(op_result) -> bool:
    required_steps = {
        "create_database",
        "write_deployment",
        "configure_nginx",
        "configure_cloudflared",
    }
    failed_required = {
        step.name for step in (op_result.steps or []) if (not step.success and step.name in required_steps)
    }
    return (not op_result.success) or bool(failed_required)


async def _run_provisioning_flow(
    db,
    *,
    customer: Customer,
    subscription: Subscription,
    source: str,
    send_credentials_email: bool,
) -> Dict[str, Any]:
    from ..services.tenant_lifecycle import orchestrator, TenantSpec

    trace_id = str(uuid.uuid4())
    _add_provisioning_audit(
        db,
        trace_id=trace_id,
        subdomain=customer.subdomain,
        customer_id=customer.id,
        subscription_id=subscription.id,
        source=source,
        action="provision.started",
        status="started",
        message="Inicio de provisioning",
        payload={
            "plan": subscription.plan_name,
            "partner_id": subscription.owner_partner_id,
            "country_code": customer.country,
        },
    )
    db.commit()

    spec = TenantSpec(
        subdomain=customer.subdomain,
        company_name=customer.company_name,
        admin_email=customer.email,
        plan_name=subscription.plan_name or "basic",
        partner_id=subscription.owner_partner_id,
        country_code=customer.country,
        customer_id=customer.id,
        subscription_id=subscription.id,
        send_credentials_email=send_credentials_email,
    )
    op = await orchestrator.provision(spec, source="customers_api")
    _persist_lifecycle_audit(
        db,
        trace_id=trace_id,
        subdomain=customer.subdomain,
        customer_id=customer.id,
        subscription_id=subscription.id,
        source=source,
        prefix="provision",
        op_result=op,
    )

    if _has_blocking_provisioning_failure(op):
        rollback = await orchestrator.deprovision(
            customer.subdomain,
            source="internal",
            backup=False,
            purge_local=False,
        )
        _persist_lifecycle_audit(
            db,
            trace_id=trace_id,
            subdomain=customer.subdomain,
            customer_id=customer.id,
            subscription_id=subscription.id,
            source=source,
            prefix="rollback",
            op_result=rollback,
        )

        subscription.status = SubscriptionStatus.pending
        subscription.tenant_provisioned = False
        _append_customer_note(
            customer,
            (
                f"Provisioning fallido (trace={trace_id}). "
                f"Error: {op.error or 'Fallo en uno o más pasos requeridos'}."
            ),
        )
        _add_provisioning_audit(
            db,
            trace_id=trace_id,
            subdomain=customer.subdomain,
            customer_id=customer.id,
            subscription_id=subscription.id,
            source=source,
            action="provision.mark_failed",
            status="failed",
            message="Suscripción marcada en estado pendiente por fallo de provisioning",
            error_detail=op.error,
        )
        db.commit()

        return {
            "success": False,
            "trace_id": trace_id,
            "error": op.error or "Fallo en provisioning",
            "user_message": PROVISIONING_PENDING_CUSTOMER_MESSAGE,
            "steps": op.as_dict().get("steps", []),
            "rollback": rollback.as_dict(),
        }

    subscription.status = SubscriptionStatus.active
    subscription.tenant_provisioned = True
    _add_provisioning_audit(
        db,
        trace_id=trace_id,
        subdomain=customer.subdomain,
        customer_id=customer.id,
        subscription_id=subscription.id,
        source=source,
        action="provision.completed",
        status="success",
        message="Provisioning completado",
        payload={
            "deployment_id": op.deployment_id,
            "backend_host": op.backend_host,
            "http_port": op.http_port,
            "chat_port": op.chat_port,
        },
    )
    db.commit()

    return {
        "success": True,
        "trace_id": trace_id,
        "url": f"https://{customer.subdomain}.sajet.us",
        "admin_login": op.admin_login,
        "admin_password": op.admin_password,
        "server": op.backend_host or "primary",
        "deployment_id": op.deployment_id,
        "steps": op.as_dict().get("steps", []),
    }


def _configure_stripe() -> str:
    stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
    return stripe.api_key


def _auto_link_customer_to_existing_stripe_by_email(
    db,
    customer: Customer,
    *,
    create_if_missing: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Vincula automáticamente el customer local con Stripe usando el email.

    - Si ya tiene `stripe_customer_id`, no hace nada.
    - Si encuentra una cuenta existente en Stripe con el mismo email, la vincula.
    - Si `create_if_missing=True`, crea una nueva cuenta solo cuando no existe.
    """
    if customer.stripe_customer_id:
        return {
            "stripe_customer_id": customer.stripe_customer_id,
            "linked": True,
            "created": False,
            "source": "existing_local_link",
        }

    stripe_key = _configure_stripe()
    if not stripe_key:
        logger.warning("Stripe no configurado; se omite auto-vinculación para customer %s", customer.id)
        return None

    email = (customer.email or "").strip()
    if not email:
        return None

    try:
        stripe_customers = stripe.Customer.list(email=email, limit=1)
        if stripe_customers.data:
            stripe_cust_id = stripe_customers.data[0].id
            customer.stripe_customer_id = stripe_cust_id
            db.flush()
            logger.info("Stripe auto-link por email: %s → %s", email, stripe_cust_id)
            return {
                "stripe_customer_id": stripe_cust_id,
                "linked": True,
                "created": False,
                "source": "matched_by_email",
            }

        if not create_if_missing:
            return None

        stripe_cust = stripe.Customer.create(
            name=customer.company_name or customer.full_name,
            email=email,
            phone=customer.phone,
            metadata={
                "sajet_customer_id": str(customer.id),
                "subdomain": customer.subdomain or "",
                "platform": "sajet",
            },
        )
        customer.stripe_customer_id = stripe_cust.id
        db.flush()
        logger.info("Stripe customer creado automáticamente: %s → %s", email, stripe_cust.id)
        return {
            "stripe_customer_id": stripe_cust.id,
            "linked": True,
            "created": True,
            "source": "created",
        }
    except stripe.error.StripeError as e:
        logger.warning("No se pudo auto-vincular customer %s en Stripe: %s", customer.id, e)
        return None


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
    email: Optional[str] = None
    phone: Optional[str] = None
    user_count: Optional[int] = None
    is_admin_account: Optional[bool] = None
    plan_name: Optional[str] = None  # Cambiar plan de la suscripción
    stripe_customer_id: Optional[str] = None
    stripe_action: Optional[str] = None  # 'link' (buscar/crear en Stripe) o 'unlink'
    discount_pct: Optional[float] = None
    discount_reason: Optional[str] = None
    partner_id: Optional[int] = -1  # -1 = no change, 0 = unassign, >0 = assign


class StripeCustomerLinkRequest(BaseModel):
    stripe_customer_id: str


def _apply_subscription_discount(base_amount: float, discount_pct: Optional[float]) -> tuple[float, float]:
    pct = max(0.0, min(100.0, float(discount_pct or 0.0)))
    discount_amount = round(base_amount * (pct / 100.0), 2)
    final_amount = round(base_amount - discount_amount, 2)
    return final_amount, discount_amount


@router.get("/stripe/search")
async def search_stripe_customers(
    request: Request,
    q: str = Query(..., min_length=2, description="Texto a buscar (email, nombre o id)"),
    limit: int = Query(10, ge=1, le=25),
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Buscar cuentas de Stripe para vincularlas a clientes existentes."""
    _configure_stripe()
    _verify_admin(request, access_token)

    query = q.strip()
    query_l = query.lower()
    items: List[Dict[str, Any]] = []

    try:
        # Intentar Stripe Search API (más precisa)
        try:
            escaped = query.replace("'", "\\'")
            search_q = (
                f"name:'{escaped}' OR email:'{escaped}' OR id:'{escaped}' OR "
                f"metadata['erp_customer_id']:'{escaped}'"
            )
            result = stripe.Customer.search(query=search_q, limit=limit)
            customers = result.data or []
        except Exception:
            # Fallback universal: listar y filtrar localmente
            sample = stripe.Customer.list(limit=min(max(limit * 10, 20), 100))
            customers = [
                c for c in (sample.data or [])
                if query_l in (getattr(c, "id", "") or "").lower()
                or query_l in (getattr(c, "email", "") or "").lower()
                or query_l in (getattr(c, "name", "") or "").lower()
            ][:limit]

        for c in customers:
            items.append({
                "id": c.id,
                "email": getattr(c, "email", None),
                "name": getattr(c, "name", None),
                "phone": getattr(c, "phone", None),
                "created": getattr(c, "created", None),
                "metadata": getattr(c, "metadata", {}) or {},
            })

        return {
            "success": True,
            "query": query,
            "items": items,
            "total": len(items),
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Error Stripe: {e}")


@router.post("/{customer_id}/stripe/link")
async def link_existing_stripe_customer(
    customer_id: int,
    payload: StripeCustomerLinkRequest,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Vincula manualmente un cliente local a un Stripe Customer existente."""
    _configure_stripe()
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        stripe_customer_id = (payload.stripe_customer_id or "").strip()
        if not stripe_customer_id:
            raise HTTPException(status_code=400, detail="stripe_customer_id es requerido")

        try:
            stripe_customer = stripe.Customer.retrieve(stripe_customer_id)
            if getattr(stripe_customer, "deleted", False):
                raise HTTPException(status_code=400, detail="La cuenta Stripe está eliminada")
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"No se pudo validar la cuenta Stripe: {e}")

        customer.stripe_customer_id = stripe_customer_id
        db.commit()

        return {
            "success": True,
            "message": f"Cliente vinculado a Stripe ({stripe_customer_id})",
            "customer_id": customer_id,
            "stripe_customer_id": stripe_customer_id,
        }
    finally:
        db.close()


class UserCountUpdate(BaseModel):
    user_count: int


@router.get("")
async def list_customers(
    request: Request,
    access_token: str = Cookie(None),
    partner_id: int = None,
) -> Dict[str, Any]:
    """Lista todos los clientes con sus suscripciones, montos y user_count."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(Customer)
        if partner_id is not None:
            q = q.filter(Customer.partner_id == partner_id)
        customers = q.order_by(Customer.created_at.desc()).all()
        items = []
        customer_ids = [c.id for c in customers]

        subscriptions_by_customer = {}
        if customer_ids:
            subscriptions = (
                db.query(Subscription)
                .filter(
                    Subscription.customer_id.in_(customer_ids),
                    Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.suspended]),
                )
                .order_by(Subscription.customer_id.asc(), Subscription.created_at.desc())
                .all()
            )
            for sub in subscriptions:
                subscriptions_by_customer.setdefault(sub.customer_id, sub)

        plan_names = {sub.plan_name for sub in subscriptions_by_customer.values() if sub.plan_name}
        plans_by_name = {}
        if plan_names:
            plans = (
                db.query(Plan)
                .filter(Plan.name.in_(plan_names), Plan.is_active == True)
                .all()
            )
            plans_by_name = {plan.name: plan for plan in plans}

        deployments_by_subscription = {}
        subscription_ids = [sub.id for sub in subscriptions_by_customer.values()]
        if subscription_ids:
            deployments = (
                db.query(TenantDeployment)
                .filter(TenantDeployment.subscription_id.in_(subscription_ids))
                .all()
            )
            deployments_by_subscription = {
                deployment.subscription_id: deployment for deployment in deployments
            }

        for c in customers:
            # Obtener suscripción activa
            sub = subscriptions_by_customer.get(c.id)

            # Obtener plan si existe
            plan_data = None
            calculated_amount = 0
            if sub:
                plan = plans_by_name.get(sub.plan_name)
                if plan:
                    user_count = c.user_count or sub.user_count or 1
                    # Use partner_id from subscription or customer for pricing overrides
                    effective_partner_id = sub.owner_partner_id or c.partner_id
                    calculated_amount = plan.calculate_monthly(user_count, partner_id=effective_partner_id)
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
                deployment = deployments_by_subscription.get(sub.id)

            items.append({
                "id": c.id,
                "company_name": c.company_name,
                "email": c.email,
                "phone": c.phone,
                "full_name": c.full_name,
                "subdomain": c.subdomain,
                "user_count": c.user_count or 1,
                "is_admin_account": c.is_admin_account or False,
                "status": c.status.value if c.status else "active",
                "stripe_customer_id": c.stripe_customer_id,
                "partner_id": c.partner_id,
                "subscription": {
                    "id": sub.id,
                    "plan_name": sub.plan_name,
                    "status": sub.status.value if sub.status else None,
                    "monthly_amount": sub.monthly_amount,
                    "calculated_amount": calculated_amount,
                    "discount_pct": sub.discount_pct or 0,
                    "discount_amount": sub.discount_amount or 0,
                    "discount_reason": sub.discount_reason,
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
    """Actualiza un cliente: user_count, plan, is_admin, email, Stripe vinculación, etc."""
    _configure_stripe()
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        messages = []
        email_changed = False

        # Actualizar email
        if payload.email is not None:
            old_email = customer.email
            customer.email = payload.email
            messages.append(f"Email: {old_email} → {payload.email}")
            email_changed = (old_email or "").strip().lower() != (payload.email or "").strip().lower()

        if payload.phone is not None:
            old_phone = customer.phone or ""
            customer.phone = payload.phone.strip()
            messages.append(f"Teléfono: {old_phone or 'N/D'} → {customer.phone}")

        # Actualizar campos simples
        if payload.company_name is not None:
            customer.company_name = payload.company_name
            messages.append(f"Empresa: {payload.company_name}")

        if payload.is_admin_account is not None:
            customer.is_admin_account = payload.is_admin_account
            if payload.is_admin_account:
                messages.append("Marcado como cuenta admin (exento de facturación)")

        # Reasignar partner
        if payload.partner_id is not None and payload.partner_id != -1:
            old_pid = customer.partner_id
            if payload.partner_id == 0:
                customer.partner_id = None
                messages.append("Partner desvinculado")
            else:
                from ..models.database import Partner
                partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
                if not partner:
                    raise HTTPException(status_code=404, detail=f"Partner {payload.partner_id} no encontrado")
                customer.partner_id = partner.id
                messages.append(f"Partner: {old_pid or 'ninguno'} → {partner.company_name} (#{partner.id})")
                # Update subscription owner too
                sub = db.query(Subscription).filter(
                    Subscription.customer_id == customer.id,
                    Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.suspended]),
                ).first()
                if sub:
                    sub.owner_partner_id = partner.id

        # Manejo de Stripe: buscar/crear/vincular cliente
        if payload.stripe_action == "link":
            # Buscar cliente existente en Stripe por email
            try:
                email_to_search = payload.email or customer.email
                stripe_customers = stripe.Customer.list(email=email_to_search, limit=1)
                
                if stripe_customers.data:
                    # Vincular existente
                    stripe_cust_id = stripe_customers.data[0].id
                    customer.stripe_customer_id = stripe_cust_id
                    messages.append(f"Vinculado a Stripe Customer: {stripe_cust_id}")
                else:
                    # Crear nuevo en Stripe
                    stripe_cust = stripe.Customer.create(
                        name=customer.company_name,
                        email=email_to_search,
                        phone=payload.phone or customer.phone,
                        metadata={"sajet_customer_id": customer.id}
                    )
                    customer.stripe_customer_id = stripe_cust.id
                    messages.append(f"Creado nuevo Stripe Customer: {stripe_cust.id}")
            except Exception as e:
                logger.error(f"Error manejando Stripe para cliente {customer_id}: {e}")
                raise HTTPException(status_code=400, detail=f"Error con Stripe: {str(e)}")
        elif payload.stripe_action == "unlink":
            # Desvincular
            customer.stripe_customer_id = None
            messages.append("Desvinculado de Stripe")
        elif payload.stripe_customer_id is not None:
            # Vincular manualmente si se proporciona ID
            customer.stripe_customer_id = payload.stripe_customer_id.strip() or None
            if customer.stripe_customer_id:
                messages.append(f"Vinculado a Stripe Customer: {customer.stripe_customer_id}")
        elif email_changed and not customer.stripe_customer_id:
            auto_link_result = _auto_link_customer_to_existing_stripe_by_email(
                db,
                customer,
                create_if_missing=False,
            )
            if auto_link_result:
                messages.append(
                    f"Vinculado automáticamente por email a Stripe Customer: {auto_link_result['stripe_customer_id']}"
                )

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
                    effective_pid = sub.owner_partner_id or customer.partner_id
                    base_amount = plan.calculate_monthly(payload.user_count, partner_id=effective_pid)
                    new_amount, discount_amount = _apply_subscription_discount(base_amount, sub.discount_pct)
                    old_amount = sub.monthly_amount or 0
                    sub.monthly_amount = new_amount
                    sub.discount_amount = discount_amount
                    messages.append(f"Monto: ${old_amount:.2f} → ${new_amount:.2f}")

        # Cambiar plan (si no hay suscripción activa, crear una nueva)
        if payload.plan_name is not None:
            requested_plan_name = (payload.plan_name or "").strip()
            if not requested_plan_name:
                raise HTTPException(status_code=400, detail="Debe seleccionar un plan válido")

            new_plan = db.query(Plan).filter(
                Plan.name == requested_plan_name,
                Plan.is_active == True
            ).first()
            if not new_plan:
                raise HTTPException(status_code=404, detail=f"Plan '{requested_plan_name}' no encontrado")

            sub = db.query(Subscription).filter(
                Subscription.customer_id == customer.id,
                Subscription.status == SubscriptionStatus.active
            ).first()

            if sub:
                old_plan = sub.plan_name
                sub.plan_name = new_plan.name
                user_count = customer.user_count or sub.user_count or 1
                effective_pid = sub.owner_partner_id or customer.partner_id
                base_amount = new_plan.calculate_monthly(user_count, partner_id=effective_pid)
                discounted_total, discount_amount = _apply_subscription_discount(base_amount, sub.discount_pct)
                sub.monthly_amount = discounted_total
                sub.discount_amount = discount_amount
                messages.append(f"Plan: {old_plan} → {new_plan.name} (${sub.monthly_amount:.2f}/mes)")
            else:
                user_count = customer.user_count or 1
                partner_id = customer.partner_id
                calculated_amount = new_plan.calculate_monthly(user_count, partner_id=partner_id)

                new_sub = Subscription(
                    customer_id=customer.id,
                    plan_name=new_plan.name,
                    status=SubscriptionStatus.active,
                    user_count=user_count,
                    monthly_amount=calculated_amount,
                    discount_pct=0,
                    discount_amount=0,
                    owner_partner_id=partner_id,
                    billing_mode=BillingMode.PARTNER_DIRECT if partner_id else BillingMode.JETURING_DIRECT_SUBSCRIPTION,
                    payer_type=PayerType.PARTNER if partner_id else PayerType.CLIENT,
                    collector=CollectorType.STRIPE_CONNECT if partner_id else CollectorType.STRIPE_DIRECT,
                    invoice_issuer=InvoiceIssuer.JETURING,
                )
                db.add(new_sub)
                db.flush()  # Ensure new subscription is visible for subsequent queries
                messages.append(f"Suscripción creada con plan {new_plan.name} (${calculated_amount:.2f}/mes)")

        # Aplicar descuento especial (solo si hay suscripción activa)
        # Skip if both values are effectively empty (frontend sends 0 and '' by default)
        has_real_discount = (
            (payload.discount_pct is not None and payload.discount_pct != 0)
            or (payload.discount_reason is not None and payload.discount_reason.strip())
        )
        if has_real_discount:
            sub = db.query(Subscription).filter(
                Subscription.customer_id == customer.id,
                Subscription.status == SubscriptionStatus.active
            ).first()
            if not sub:
                raise HTTPException(status_code=400, detail="El cliente no tiene suscripción activa para aplicar descuento")

            if payload.discount_pct is not None:
                if payload.discount_pct < 0 or payload.discount_pct > 100:
                    raise HTTPException(status_code=400, detail="discount_pct debe estar entre 0 y 100")
                sub.discount_pct = payload.discount_pct

            if payload.discount_reason is not None:
                sub.discount_reason = payload.discount_reason.strip() or None

            plan_for_discount = db.query(Plan).filter(Plan.name == sub.plan_name).first()
            if plan_for_discount:
                user_count = customer.user_count or sub.user_count or 1
                effective_pid = sub.owner_partner_id or customer.partner_id
                base_amount = plan_for_discount.calculate_monthly(user_count, partner_id=effective_pid)
                discounted_total, discount_amount = _apply_subscription_discount(base_amount, sub.discount_pct)
                sub.monthly_amount = discounted_total
                sub.discount_amount = discount_amount
                messages.append(
                    f"Descuento aplicado: {sub.discount_pct or 0:.2f}% (−${discount_amount:.2f})"
                )

        db.commit()
        return {
            "message": "Cliente actualizado",
            "changes": messages,
            "customer_id": customer_id,
            "stripe_customer_id": customer.stripe_customer_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error actualizando cliente {customer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


class CustomerStatusAction(BaseModel):
    action: str  # suspend_account, suspend_billing, reactivate
    reason: Optional[str] = None


@router.put("/{customer_id}/status")
async def update_customer_status(
    customer_id: int,
    request: Request,
    payload: CustomerStatusAction,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Acciones de cuenta:
    - suspend_account: suspende cuenta + suscripción
    - suspend_billing: suspende solo la suscripción (cuenta sigue activa)
    - reactivate: reactiva cuenta + suscripción
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        sub = db.query(Subscription).filter(
            Subscription.customer_id == customer_id,
            Subscription.status.in_([
                SubscriptionStatus.active,
                SubscriptionStatus.suspended,
                SubscriptionStatus.past_due,
            ])
        ).first()

        messages = []
        action = payload.action

        if action == "suspend_account":
            if customer.status == CustomerStatus.suspended:
                raise HTTPException(status_code=400, detail="La cuenta ya está suspendida")
            customer.status = CustomerStatus.suspended
            messages.append("Cuenta suspendida")
            if sub and sub.status == SubscriptionStatus.active:
                sub.suspension_previous_status = sub.status.value
                sub.status = SubscriptionStatus.suspended
                messages.append("Suscripción suspendida")

        elif action == "suspend_billing":
            if not sub:
                raise HTTPException(status_code=400, detail="No hay suscripción activa para suspender")
            if sub.status == SubscriptionStatus.suspended:
                raise HTTPException(status_code=400, detail="La suscripción ya está suspendida")
            sub.suspension_previous_status = sub.status.value
            sub.status = SubscriptionStatus.suspended
            messages.append("Suscripción suspendida (cuenta sigue activa)")

        elif action == "reactivate":
            if customer.status == CustomerStatus.suspended:
                customer.status = CustomerStatus.active
                messages.append("Cuenta reactivada")
            if sub and sub.status == SubscriptionStatus.suspended:
                prev = sub.suspension_previous_status or "active"
                sub.status = SubscriptionStatus(prev)
                sub.suspension_previous_status = None
                messages.append("Suscripción reactivada")
            if not messages:
                raise HTTPException(status_code=400, detail="La cuenta y suscripción ya están activas")

        else:
            raise HTTPException(status_code=400, detail=f"Acción no válida: {action}")

        if payload.reason:
            customer.notes = (customer.notes or "") + f"\n[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}] {action}: {payload.reason}"

        db.commit()
        return {
            "message": ", ".join(messages),
            "customer_id": customer_id,
            "customer_status": customer.status.value,
            "subscription_status": sub.status.value if sub else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en acción {payload.action} para cliente {customer_id}: {e}")
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
                effective_pid = sub.owner_partner_id or (customer.partner_id if customer else None)
                base_amount = plan.calculate_monthly(payload.user_count, partner_id=effective_pid)
                new_amount, discount_amount = _apply_subscription_discount(base_amount, sub.discount_pct)
                sub.monthly_amount = new_amount
                sub.discount_amount = discount_amount

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


class CreateCustomerRequest(BaseModel):
    company_name: str
    email: str
    phone: str
    full_name: Optional[str] = ""
    subdomain: str
    plan_name: str = "basic"
    user_count: int = 1
    partner_id: Optional[int] = None
    country_code: Optional[str] = None
    auto_provision: Optional[bool] = True  # Auto-provision tenant Odoo


@router.post("")
async def create_customer(
    payload: CreateCustomerRequest,
    request: Request,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """
    Crear un nuevo cliente con suscripción y, opcionalmente, provisionar
    el tenant Odoo automáticamente (auto_provision=true por defecto).

    Flujo completo:
    1. Crea Customer + Subscription en BD local
    2. Si auto_provision=true y hay subdomain: clona template_tenant como nueva BD Odoo
    3. Provisiona subdominio en nginx
    4. Devuelve credenciales del tenant en la respuesta
    """
    _configure_stripe()
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        from ..services.stripe_connect import normalize_country_code

        effective_country = normalize_country_code(payload.country_code, get_runtime_setting("ODOO_DEFAULT_COUNTRY", "DO"))

        # Validar subdominio único
        existing = db.query(Customer).filter(Customer.subdomain == payload.subdomain).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Subdominio '{payload.subdomain}' ya está en uso")

        # Validar plan
        plan = db.query(Plan).filter(Plan.name == payload.plan_name, Plan.is_active == True).first()
        if not plan:
            raise HTTPException(status_code=400, detail=f"Plan '{payload.plan_name}' no existe o no está activo")

        # Determinar partner para billing
        from ..models.database import BillingMode, PayerType, CollectorType, InvoiceIssuer
        partner_id = payload.partner_id

        # Crear cliente
        customer = Customer(
            email=payload.email,
            phone=payload.phone.strip(),
            full_name=payload.full_name or "",
            company_name=payload.company_name,
            subdomain=payload.subdomain,
            user_count=payload.user_count,
            country=effective_country,
            fair_use_enabled=True,
            partner_id=partner_id,
        )
        db.add(customer)
        db.flush()

        # Crear suscripción activa
        calculated_amount = plan.calculate_monthly(payload.user_count, partner_id)
        sub = Subscription(
            customer_id=customer.id,
            plan_name=payload.plan_name,
            status=SubscriptionStatus.active,
            user_count=payload.user_count,
            monthly_amount=calculated_amount,
            owner_partner_id=partner_id,
            billing_mode=BillingMode.PARTNER_DIRECT if partner_id else BillingMode.JETURING_DIRECT_SUBSCRIPTION,
            payer_type=PayerType.PARTNER if partner_id else PayerType.CLIENT,
            collector=CollectorType.STRIPE_CONNECT if partner_id else CollectorType.STRIPE_DIRECT,
            invoice_issuer=InvoiceIssuer.JETURING,
        )
        db.add(sub)

        auto_link_result = _auto_link_customer_to_existing_stripe_by_email(
            db,
            customer,
            create_if_missing=False,
        )

        db.commit()
        db.refresh(customer)
        db.refresh(sub)

        response = {
            "id": customer.id,
            "subscription_id": sub.id,
            "monthly_amount": calculated_amount,
            "welcome_email_sent": False,
            "message": f"Cliente '{payload.company_name}' creado exitosamente",
        }

        if auto_link_result:
            response["stripe_customer_id"] = auto_link_result["stripe_customer_id"]
            response["stripe_auto_linked"] = True
            response["message"] += " + Stripe vinculado por correo"

        try:
            from ..services.email_service import send_customer_registration_acknowledgement

            email_result = send_customer_registration_acknowledgement(
                to_email=customer.email,
                company_name=customer.company_name or customer.full_name or customer.email,
                phone=customer.phone,
                customer_id=customer.id,
            )
            response["welcome_email_sent"] = bool(email_result.get("success"))
            if not email_result.get("success"):
                response["welcome_email_error"] = email_result.get("error")
        except Exception as email_err:
            logger.warning(f"No se pudo enviar correo de registro a {customer.email}: {email_err}")
            response["welcome_email_error"] = str(email_err)

        # ── Auto-provision tenant Odoo ──
        if payload.auto_provision and payload.subdomain:
            try:
                tenant_result = await _run_provisioning_flow(
                    db,
                    customer=customer,
                    subscription=sub,
                    source="customers_create",
                    send_credentials_email=True,
                )
                if tenant_result.get("success"):
                    response["tenant"] = {
                        "subdomain": payload.subdomain,
                        "url": tenant_result.get("url", f"https://{payload.subdomain}.sajet.us"),
                        "admin_login": tenant_result.get("admin_login"),
                        "admin_password": tenant_result.get("admin_password"),
                        "server": tenant_result.get("server"),
                        "status": "active",
                        "trace_id": tenant_result.get("trace_id"),
                    }
                    response["message"] += " + Tenant Odoo provisionado"
                    logger.info(f"✅ Cliente + Tenant '{payload.subdomain}' creado exitosamente")
                else:
                    response["tenant_error"] = tenant_result.get("error", "Error provisionando tenant")
                    response["tenant_trace_id"] = tenant_result.get("trace_id")
                    response["tenant_status"] = "provisioning_failed"
                    response["retry_available"] = True
                    response["tenant_user_message"] = tenant_result.get("user_message", PROVISIONING_PENDING_CUSTOMER_MESSAGE)
                    response["message"] += " (provisioning fallido — orden enviada al equipo interno)"
                    logger.warning(
                        "⚠️ Cliente creado pero tenant falló (%s): %s",
                        tenant_result.get("trace_id"),
                        tenant_result.get("error"),
                    )
            except Exception as prov_err:
                response["tenant_error"] = str(prov_err)
                response["tenant_user_message"] = PROVISIONING_PENDING_CUSTOMER_MESSAGE
                response["tenant_status"] = "provisioning_failed"
                response["retry_available"] = True
                response["message"] += " (error en provisioning — orden enviada al equipo interno)"
                logger.error(f"Error en auto-provision de '{payload.subdomain}': {prov_err}")

        return response
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


async def _auto_provision_tenant(
    subdomain: str,
    company_name: str,
    partner_id: Optional[int] = None,
    country_code: Optional[str] = None,
    plan_name: str = "basic",
    subscription_id: Optional[int] = None,
    customer_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Provisiona un tenant Odoo automáticamente:
    1. Clona template_tenant via create_tenant_from_template (fast path)
    2. Provisiona subdominio en nginx
    3. Crea TenantDeployment con campos multi-nodo (si subscription_id disponible)
    4. Retorna credenciales generadas

    Esta función NO crea Customer/Subscription — eso lo hace el caller.
    """
    from ..services.odoo_database_manager import create_tenant_from_template
    from ..services.nginx_domain_configurator import provision_sajet_subdomain

    # Generar credenciales bootstrap
    admin_login = f"{subdomain}@sajet.us"
    admin_password = secrets.token_urlsafe(16)

    # 1. Crear BD Odoo desde template
    result = await create_tenant_from_template(
        subdomain=subdomain,
        company_name=company_name,
        server_id=None,  # auto-select
        admin_login=admin_login,
        admin_password=admin_password,
        country_code=country_code,
    )

    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "Error clonando template"),
            "error_code": result.get("error_code"),
        }

    # 2. Provisionar nginx
    try:
        # Resolver node_ip real desde el resultado del create_tenant_from_template
        # (NO usar default CT105_IP que apuntaría a IP muerta si no estuviera bien override)
        from ..services.deployment_writer import _resolve_node_from_server_id  # type: ignore
        from ..models.database import SessionLocal as _SL
        _ng_node_ip = None
        try:
            _ng_db = _SL()
            _node = _resolve_node_from_server_id(_ng_db, result.get("server"))
            if _node:
                _ng_node_ip = _node.hostname
            _ng_db.close()
        except Exception:
            pass
        if not _ng_node_ip:
            from ..config import ODOO_PRIMARY_IP as _PRIMARY_IP
            _ng_node_ip = _PRIMARY_IP

        nginx_result = provision_sajet_subdomain(subdomain, node_ip=_ng_node_ip)
        if not nginx_result.get("success"):
            logger.warning(f"Nginx provisioning failed for {subdomain}: {nginx_result.get('error')}")
    except Exception as ng_err:
        logger.warning(f"Nginx error for {subdomain}: {ng_err}")

    # 2b. Cloudflared gateway en PCT 205
    try:
        from ..services.cloudflare_tunnel_gate import add_tenant_route
        gate_res = add_tenant_route(subdomain=subdomain, node_ip=_ng_node_ip)
        if not gate_res.get("success"):
            logger.warning(f"Cloudflared gate failed for {subdomain}: {gate_res.get('error')}")
    except Exception as gate_err:
        logger.warning(f"Cloudflared gate error for {subdomain}: {gate_err}")

    # 3. Crear TenantDeployment con campos multi-nodo
    deployment_id = None
    if subscription_id:
        try:
            from ..services.deployment_writer import ensure_tenant_deployment
            dep_result = ensure_tenant_deployment(
                subdomain=subdomain,
                subscription_id=subscription_id,
                customer_id=customer_id,
                server_id=result.get("server"),
                plan_name=plan_name,
            )
            if dep_result.get("success"):
                deployment_id = dep_result["deployment_id"]
                logger.info(
                    f"✅ TenantDeployment #{deployment_id} ({dep_result['status']}) "
                    f"para '{subdomain}' via _auto_provision_tenant"
                )
            else:
                logger.warning(
                    f"⚠️ TenantDeployment no creado para '{subdomain}': {dep_result.get('error')}"
                )
        except Exception as dep_err:
            logger.warning(f"⚠️ Error creando TenantDeployment para '{subdomain}': {dep_err}")

    return {
        "success": True,
        "url": f"https://{subdomain}.sajet.us",
        "admin_login": admin_login,
        "admin_password": admin_password,
        "server": result.get("server", "primary"),
        "deployment_id": deployment_id,
    }


@router.post("/{customer_id}/retry-provisioning")
async def retry_customer_provisioning(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Reintenta provisioning de un tenant fallido con auditoría completa."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        subscription = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
        ).order_by(Subscription.created_at.desc()).first()
        if not subscription:
            raise HTTPException(status_code=400, detail="Cliente sin suscripción")

        result = await _run_provisioning_flow(
            db,
            customer=customer,
            subscription=subscription,
            source="customers_retry",
            send_credentials_email=True,
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "Provisioning reintentado y completado exitosamente",
                "trace_id": result.get("trace_id"),
                "tenant": {
                    "subdomain": customer.subdomain,
                    "url": result.get("url"),
                    "admin_login": result.get("admin_login"),
                    "admin_password": result.get("admin_password"),
                },
            }

        return {
            "success": False,
            "message": "El reintento falló. Se aplicó rollback y quedó pendiente para revisión interna.",
            "trace_id": result.get("trace_id"),
            "tenant_status": "provisioning_failed",
            "tenant_user_message": result.get("user_message", PROVISIONING_PENDING_CUSTOMER_MESSAGE),
            "error": result.get("error"),
        }
    finally:
        db.close()


@router.get("/{customer_id}/provisioning-audit")
async def get_customer_provisioning_audit(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
    limit: int = Query(100, ge=1, le=500),
) -> Dict[str, Any]:
    """Retorna el historial de auditoría de provisioning para un cliente."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        rows = db.query(ProvisioningAuditLog).filter(
            ProvisioningAuditLog.customer_id == customer_id,
        ).order_by(ProvisioningAuditLog.created_at.desc()).limit(limit).all()

        return {
            "success": True,
            "customer_id": customer_id,
            "subdomain": customer.subdomain,
            "items": [
                {
                    "id": r.id,
                    "trace_id": str(r.trace_id),
                    "action": r.action,
                    "status": r.status,
                    "message": r.message,
                    "error_detail": r.error_detail,
                    "payload": r.payload,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "total": len(rows),
        }
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
            effective_pid = sub.owner_partner_id or (customer.partner_id if customer else None)
            base_amount = plan.calculate_monthly(user_count, partner_id=effective_pid)
            new_amount, discount_amount = _apply_subscription_discount(base_amount, sub.discount_pct)
            old_amount = sub.monthly_amount or 0

            if abs(new_amount - old_amount) > 0.01:
                sub.monthly_amount = new_amount
                sub.user_count = user_count
                sub.discount_amount = discount_amount
                updated += 1
                details.append({
                    "customer": customer.company_name if customer else f"ID:{sub.customer_id}",
                    "plan": sub.plan_name,
                    "users": user_count,
                    "discount_pct": round(sub.discount_pct or 0, 2),
                    "discount_amount": round(discount_amount, 2),
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


# ──────────────────────────────────────────────────────
# Auto Stripe Customer + Credential Management
# ──────────────────────────────────────────────────────

class SendCredentialsRequest(BaseModel):
    customer_id: int
    custom_password: Optional[str] = None  # Si no se pasa, se genera uno aleatorio


@router.post("/{customer_id}/create-stripe-customer")
async def create_stripe_customer(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Crea automáticamente un Stripe Customer para este cliente.
    Si ya tiene stripe_customer_id, retorna error.
    """
    _configure_stripe()
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if customer.stripe_customer_id:
            return {
                "success": True,
                "already_exists": True,
                "stripe_customer_id": customer.stripe_customer_id,
                "message": "El cliente ya tiene Stripe Customer ID",
            }

        auto_link_result = _auto_link_customer_to_existing_stripe_by_email(
            db,
            customer,
            create_if_missing=False,
        )
        if auto_link_result:
            db.commit()
            return {
                "success": True,
                "already_exists": True,
                "stripe_customer_id": auto_link_result["stripe_customer_id"],
                "message": f"Stripe Customer vinculado automáticamente por email: {auto_link_result['stripe_customer_id']}",
            }

        # Crear en Stripe
        stripe_customer = stripe.Customer.create(
            email=customer.email,
            name=customer.company_name or customer.full_name,
            phone=customer.phone,
            metadata={
                "erp_customer_id": str(customer.id),
                "subdomain": customer.subdomain or "",
                "platform": "sajet",
            },
        )

        customer.stripe_customer_id = stripe_customer.id
        db.commit()

        logger.info(f"✅ Stripe Customer {stripe_customer.id} creado para {customer.company_name}")

        return {
            "success": True,
            "already_exists": False,
            "stripe_customer_id": stripe_customer.id,
            "message": f"Stripe Customer creado: {stripe_customer.id}",
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error Stripe: {e}")
        raise HTTPException(status_code=400, detail=f"Error Stripe: {e}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{customer_id}/send-credentials")
async def send_credentials(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Envía las credenciales de acceso al tenant por email.
    Usa las credenciales por defecto o genera una contraseña personalizada.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if not customer.subdomain:
            raise HTTPException(status_code=400, detail="Cliente no tiene subdominio asignado")

        # Credenciales por defecto de Odoo
        from ..services.odoo_database_manager import DEFAULT_ADMIN_LOGIN, DEFAULT_ADMIN_PASSWORD

        admin_login = DEFAULT_ADMIN_LOGIN
        admin_password = DEFAULT_ADMIN_PASSWORD

        # Obtener plan
        sub = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).first()
        plan_name = sub.plan_name if sub else "basic"

        # Enviar email
        from ..services.email_service import send_tenant_credentials

        result = send_tenant_credentials(
            to_email=customer.email,
            company_name=customer.company_name or customer.subdomain,
            subdomain=customer.subdomain,
            admin_login=admin_login,
            admin_password=admin_password,
            plan_name=plan_name,
        )

        return {
            "success": result["success"],
            "message": f"Credenciales enviadas a {customer.email}" if result["success"] else result.get("error"),
            "email_to": customer.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enviando credenciales: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{customer_id}/reset-password")
async def reset_customer_password(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Genera una nueva contraseña para el tenant en Odoo y la envía por email.
    Resetea la contraseña del usuario admin (id=2) en la BD Odoo del tenant.
    Registra el evento en auditoría.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if not customer.subdomain:
            raise HTTPException(status_code=400, detail="Cliente no tiene subdominio")

        # Generar nueva contraseña segura
        new_password = secrets.token_urlsafe(12)  # ~16 chars, URL-safe

        # Resetear en Odoo via SQL
        from ..services.odoo_database_manager import _run_pct_sql, ODOO_SERVERS

        server = list(ODOO_SERVERS.values())[0]
        reset_sql = f"UPDATE res_users SET password = '{new_password}' WHERE id = 2"
        success, output = _run_pct_sql(server.pct_id, customer.subdomain, reset_sql)

        if not success:
            raise HTTPException(status_code=500, detail=f"Error reseteando password en Odoo: {output}")

        # Actualizar timestamp de cambio de contraseña
        customer.last_password_changed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        # Enviar nueva contraseña por email
        from ..services.email_service import send_password_reset

        email_result = send_password_reset(
            to_email=customer.email,
            company_name=customer.company_name or customer.subdomain,
            subdomain=customer.subdomain,
            new_password=new_password,
        )

        # Registrar evento de auditoría
        try:
            from .audit import log_audit_event as audit_log
            from .audit import AuditLogRequest
            
            # Extraer info del token
            actor_username = "unknown"
            try:
                from ..utils.token import verify_token_with_role
                token_data = verify_token_with_role(access_token)
                actor_username = token_data.get("email") or token_data.get("username") or "admin"
            except:
                actor_username = "admin"
            
            audit_request = AuditLogRequest(
                event_type="PASSWORD_RESET",
                resource=f"customer:{customer.id}:{customer.subdomain}",
                action="reset_password",
                status="success",
                details={
                    "customer_id": customer_id,
                    "subdomain": customer.subdomain,
                    "email_sent": email_result["success"],
                    "actor": actor_username,
                }
            )
            # Log directo a auditoría
            from ..models.database import AuditEventRecord
            event = AuditEventRecord(
                event_type="PASSWORD_RESET",
                actor_id=None,
                actor_username=actor_username,
                actor_role="admin",
                ip_address=get_real_ip(request),
                resource=f"customer:{customer.id}:{customer.subdomain}",
                action="reset_password",
                status="success",
                details={
                    "customer_id": customer_id,
                    "subdomain": customer.subdomain,
                    "email_sent": email_result["success"],
                }
            )
            db.add(event)
            db.commit()
        except Exception as audit_err:
            logger.warning(f"No se pudo registrar evento de auditoría: {audit_err}")

        return {
            "success": True,
            "password_reset": True,
            "email_sent": email_result["success"],
            "message": f"Contraseña reseteada y enviada a {customer.email}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reseteando password: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/bulk-create-stripe")
async def bulk_create_stripe_customers(
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """Crea Stripe Customer para todos los clientes que no lo tengan."""
    _configure_stripe()
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customers = db.query(Customer).filter(
            Customer.stripe_customer_id == None,
            Customer.is_admin_account == False,
        ).all()

        created = 0
        errors = []

        for c in customers:
            try:
                sc = stripe.Customer.create(
                    email=c.email,
                    name=c.company_name or c.full_name,
                    metadata={
                        "erp_customer_id": str(c.id),
                        "subdomain": c.subdomain or "",
                        "platform": "sajet",
                    },
                )
                c.stripe_customer_id = sc.id
                created += 1
            except Exception as e:
                errors.append({"customer_id": c.id, "email": c.email, "error": str(e)})

        db.commit()
        return {
            "success": True,
            "created": created,
            "total_without_stripe": len(customers),
            "errors": errors,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════
#  CREDENCIALES DE PORTAL — Admin crea acceso para tenant/partner
# ═══════════════════════════════════════════════════════════════

class PortalCredentialsRequest(BaseModel):
    password: str
    send_email: bool = True


@router.post("/{customer_id}/portal-credentials")
async def create_portal_credentials(
    customer_id: int,
    payload: PortalCredentialsRequest,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Admin crea/resetea las credenciales del portal para un cliente.
    Genera password_hash (bcrypt) y habilita el login del tenant vía secure_auth.
    Opcionalmente envía email con las credenciales.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if len(payload.password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

        # Generar hash bcrypt
        import bcrypt
        password_hash = bcrypt.hashpw(
            payload.password.encode(), bcrypt.gensalt()
        ).decode()
        customer.password_hash = password_hash

        # Marcar onboarding step mínimo 1 si es 0
        if customer.onboarding_step < 1:
            customer.onboarding_step = 1

        db.commit()

        result = {
            "success": True,
            "message": f"Credenciales de portal creadas para {customer.company_name or customer.email}",
            "email": customer.email,
            "login_url": "https://sajet.us/#/login",
            "onboarding_step": customer.onboarding_step,
        }

        # Enviar email con credenciales
        if payload.send_email:
            try:
                from ..services.email_service import send_portal_credentials
                email_result = send_portal_credentials(
                    to_email=customer.email,
                    company_name=customer.company_name or customer.full_name or "Cliente",
                    password=payload.password,
                    login_url="https://sajet.us/#/login",
                )
                result["email_sent"] = email_result.get("success", False)
            except Exception as e:
                logger.warning(f"No se pudo enviar email de credenciales: {e}")
                result["email_sent"] = False
                result["email_error"] = str(e)

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando credenciales de portal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{customer_id}/portal-bypass")
async def set_portal_bypass(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Admin activa bypass de onboarding Y crea credenciales temporales en un solo paso.
    Útil para clientes legacy o que necesitan acceso inmediato.
    """
    _verify_admin(request, access_token)

    body = await request.json()
    password = body.get("password")
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Se requiere password de al menos 8 caracteres")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # Crear hash bcrypt
        import bcrypt
        customer.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Bypass onboarding
        customer.onboarding_bypass = True
        customer.onboarding_step = 4
        from datetime import datetime
        if not customer.onboarding_completed_at:
            customer.onboarding_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        db.commit()

        return {
            "success": True,
            "message": f"Acceso portal completo para {customer.company_name or customer.email}",
            "email": customer.email,
            "login_url": "https://sajet.us/#/login",
            "onboarding_bypass": True,
            "onboarding_step": 4,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
