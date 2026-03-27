"""
Customers Management Routes - Mantenimiento de clientes, montos y user_count
"""
from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..models.database import (
    Customer, Subscription, SubscriptionStatus, Plan,
    TenantDeployment, CustomDomain, SessionLocal
)
from .roles import verify_token_with_role
import stripe
import logging
import os
import secrets

router = APIRouter(prefix="/api/customers", tags=["Customers"])
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


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
    user_count: Optional[int] = None
    is_admin_account: Optional[bool] = None
    plan_name: Optional[str] = None  # Cambiar plan de la suscripción
    stripe_customer_id: Optional[str] = None
    stripe_action: Optional[str] = None  # 'link' (buscar/crear en Stripe) o 'unlink'


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
    """Actualiza un cliente: user_count, plan, is_admin, email, Stripe vinculación, etc."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        messages = []

        # Actualizar email
        if payload.email is not None:
            old_email = customer.email
            customer.email = payload.email
            messages.append(f"Email: {old_email} → {payload.email}")

        # Actualizar campos simples
        if payload.company_name is not None:
            customer.company_name = payload.company_name
            messages.append(f"Empresa: {payload.company_name}")

        if payload.is_admin_account is not None:
            customer.is_admin_account = payload.is_admin_account
            if payload.is_admin_account:
                messages.append("Marcado como cuenta admin (exento de facturación)")

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
                    new_amount = plan.calculate_monthly(payload.user_count, partner_id=effective_pid)
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
                effective_pid = sub.owner_partner_id or customer.partner_id
                sub.monthly_amount = new_plan.calculate_monthly(user_count, partner_id=effective_pid)
                messages.append(f"Plan: {old_plan} → {new_plan.name} (${sub.monthly_amount:.2f}/mes)")

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
                new_amount = plan.calculate_monthly(payload.user_count, partner_id=effective_pid)
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


class CreateCustomerRequest(BaseModel):
    company_name: str
    email: str
    full_name: Optional[str] = ""
    subdomain: str
    plan_name: str = "basic"
    user_count: int = 1
    partner_id: Optional[int] = None


@router.post("")
async def create_customer(
    payload: CreateCustomerRequest,
    request: Request,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """Crear un nuevo cliente con suscripción básica."""
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        # Validar subdominio único
        existing = db.query(Customer).filter(Customer.subdomain == payload.subdomain).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Subdominio '{payload.subdomain}' ya está en uso")

        # Validar plan
        plan = db.query(Plan).filter(Plan.name == payload.plan_name, Plan.is_active == True).first()
        if not plan:
            raise HTTPException(status_code=400, detail=f"Plan '{payload.plan_name}' no existe o no está activo")

        # Crear cliente
        customer = Customer(
            email=payload.email,
            full_name=payload.full_name or "",
            company_name=payload.company_name,
            subdomain=payload.subdomain,
            user_count=payload.user_count,
            partner_id=payload.partner_id,
        )
        db.add(customer)
        db.flush()

        # Crear suscripción activa
        calculated_amount = plan.calculate_monthly(payload.user_count, payload.partner_id)
        sub = Subscription(
            customer_id=customer.id,
            plan_name=payload.plan_name,
            status=SubscriptionStatus.active,
            user_count=payload.user_count,
            monthly_amount=calculated_amount,
        )
        db.add(sub)
        db.commit()
        db.refresh(customer)
        return {"id": customer.id, "message": f"Cliente '{payload.company_name}' creado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando cliente: {e}")
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
            effective_pid = sub.owner_partner_id or (customer.partner_id if customer else None)
            new_amount = plan.calculate_monthly(user_count, partner_id=effective_pid)
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

        # Crear en Stripe
        stripe_customer = stripe.Customer.create(
            email=customer.email,
            name=customer.company_name or customer.full_name,
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
        customer.last_password_changed_at = datetime.utcnow()
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
                ip_address=request.client.host if request.client else None,
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
            customer.onboarding_completed_at = datetime.utcnow()

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
