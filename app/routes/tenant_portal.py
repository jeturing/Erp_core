"""
Portal del Tenant - Vista de facturación y gestión de suscripción
"""
from fastapi import APIRouter, HTTPException, Request, status, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from ..models.database import (
    Customer, Subscription, SessionLocal, SubscriptionStatus,
    CustomDomain, SeatEvent, Invoice, InvoiceStatus, Plan,
)
from .roles import verify_token_with_role
from ..services.spa_shell import render_spa_shell
from ..services.stripe_billing import (
    push_invoice_to_stripe,
    create_checkout_for_invoice,
    build_invoice_action_urls,
    fetch_stripe_invoice_links,
)
from ..config import get_runtime_setting
from ..services.tunnel_lifecycle import get_customer_tunnel_info
import stripe
import hashlib
import secrets
import logging
from datetime import datetime
from ..services.domain_manager import DomainManager
from ..services.addon_billing_service import (
    list_available_addon_services,
    list_customer_addon_subscriptions,
    purchase_customer_addon,
)
from ..services.tenant_accounts import fetch_tenant_accounts_snapshot

router = APIRouter(prefix="/tenant", tags=["Tenant Portal"])
logger = logging.getLogger(__name__)


def _serialize_seat_event(event: SeatEvent) -> dict:
    return {
        "id": event.id,
        "event_type": event.event_type.name if hasattr(event.event_type, "name") else str(event.event_type),
        "login": event.odoo_login,
        "user_id": event.odoo_user_id,
        "user_count_after": event.user_count_after,
        "is_billable": event.is_billable,
        "source": event.source,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def _configure_stripe() -> str:
    stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
    return stripe.api_key


def _app_url() -> str:
    return get_runtime_setting("APP_URL", "http://localhost:4443")


def get_current_tenant(request: Request, access_token: str = Cookie(None)):
    """Obtiene el tenant actual desde el token JWT (cookie o header)."""
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización requerido"
        )
    
    token_data = verify_token_with_role(token, required_role="tenant")

    # Compatibilidad: tokens antiguos o incompletos pueden venir sin tenant_id.
    # En ese caso, intentar resolver por user_id y luego por email (claim sub).
    if not token_data.get("tenant_id"):
        db = SessionLocal()
        try:
            customer = None

            token_user_id = token_data.get("user_id")
            if token_user_id:
                customer = db.query(Customer).filter(Customer.id == token_user_id).first()

            if not customer:
                username = token_data.get("sub")
                if username and "@" in username:
                    customer = db.query(Customer).filter(Customer.email == username).first()

            if customer:
                token_data["tenant_id"] = customer.id
        finally:
            db.close()

    return token_data


@router.get("/portal", response_class=HTMLResponse)
async def tenant_portal_page(request: Request, access_token: str = Cookie(None)):
    """SPA shell del portal del tenant."""
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        return RedirectResponse(url="/login/tenant", status_code=302)
    
    try:
        verify_token_with_role(token, required_role="tenant")
        return render_spa_shell("portal")
    except HTTPException:
        return RedirectResponse(url="/login/tenant", status_code=302)


@router.get("/api/info")
async def get_tenant_info(request: Request, access_token: str = Cookie(None)):
    """Obtiene información del tenant actual."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Portal disponible solo para usuarios tenant con contexto válido"
        )
    
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=tenant_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        subscription = db.query(Subscription).filter_by(customer_id=customer.id).first()
        
        # Map status
        status_map = {
            SubscriptionStatus.pending: "pending",
            SubscriptionStatus.active: "active",
            SubscriptionStatus.cancelled: "cancelled",
            SubscriptionStatus.past_due: "past_due"
        }
        
        return {
            "id": customer.id,
            "company_name": customer.company_name,
            "email": customer.email,
            "subdomain": customer.subdomain,
            "plan": subscription.plan_name if subscription else None,
            "status": status_map.get(subscription.status) if subscription else "no_subscription",
            "subscription_id": subscription.id if subscription else None,
            "stripe_subscription_id": subscription.stripe_subscription_id if subscription else None,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
            "odoo_url": f"https://{customer.subdomain}.sajet.us" if subscription and subscription.status == SubscriptionStatus.active else None
        }
    finally:
        db.close()


@router.get("/api/billing")
async def get_tenant_billing(request: Request, access_token: str = Cookie(None)):
    """Obtiene información de facturación del tenant."""
    _configure_stripe()
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Portal disponible solo para usuarios tenant con contexto válido"
        )
    
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=tenant_id).first()
        if not customer or not customer.stripe_customer_id:
            return {"invoices": [], "payment_method": None}
        
        # Obtener facturas de Stripe
        invoices = stripe.Invoice.list(
            customer=customer.stripe_customer_id,
            limit=10
        )
        
        # Obtener método de pago
        payment_methods = stripe.PaymentMethod.list(
            customer=customer.stripe_customer_id,
            type="card"
        )
        
        invoice_list = []
        for inv in invoices.data:
            urls = build_invoice_action_urls(
                status=inv.status,
                pdf_url=inv.invoice_pdf,
                hosted_url=inv.hosted_invoice_url,
            )
            invoice_list.append({
                "id": inv.id,
                "amount": (inv.total or inv.amount_due or inv.amount_paid or 0) / 100,
                "currency": inv.currency,
                "status": inv.status,
                "date": datetime.fromtimestamp(inv.created).isoformat(),
                "pdf_url": inv.invoice_pdf,
                "hosted_url": inv.hosted_invoice_url,
                **urls,
            })
        
        payment_method = None
        if payment_methods.data:
            pm = payment_methods.data[0]
            payment_method = {
                "brand": pm.card.brand,
                "last4": pm.card.last4,
                "exp_month": pm.card.exp_month,
                "exp_year": pm.card.exp_year
            }
        
        return {
            "invoices": invoice_list,
            "payment_method": payment_method
        }
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/api/update-payment")
async def update_payment_method(request: Request, access_token: str = Cookie(None)):
    """Crea una sesión de Stripe para actualizar el método de pago."""
    _configure_stripe()
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Portal disponible solo para usuarios tenant con contexto válido"
        )
    
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=tenant_id).first()
        if not customer or not customer.stripe_customer_id:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Crear sesión de checkout para actualizar pago
        session = stripe.checkout.Session.create(
            customer=customer.stripe_customer_id,
            mode="setup",
            success_url=f"{_app_url()}/tenant/portal?payment_updated=true",
            cancel_url=f"{_app_url()}/tenant/portal",
        )
        
        return {"checkout_url": session.url}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/api/cancel-subscription")
async def cancel_subscription(request: Request, access_token: str = Cookie(None)):
    """Cancela la suscripción del tenant."""
    _configure_stripe()
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Portal disponible solo para usuarios tenant con contexto válido"
        )
    
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=tenant_id).first()
        subscription = db.query(Subscription).filter_by(customer_id=customer.id).first()
        
        if not subscription or not subscription.stripe_subscription_id:
            raise HTTPException(status_code=404, detail="Suscripción no encontrada")
        
        # Cancelar en Stripe
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        # Actualizar en BD
        subscription.status = SubscriptionStatus.cancelled
        db.commit()
        
        return {"message": "Suscripción cancelada exitosamente"}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# DTOs
# ─────────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class DomainRequestBody(BaseModel):
    external_domain: str = Field(..., min_length=3, example="miempresa.com")


class PortalAddonPurchaseRequest(BaseModel):
    catalog_item_id: int
    quantity: int = Field(default=1, ge=1)


# ─────────────────────────────────────────────────────────
# Cambio de contraseña
# ─────────────────────────────────────────────────────────

@router.post("/api/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    access_token: str = Cookie(None)
):
    """Permite al tenant cambiar su contraseña del portal."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Las contraseñas nuevas no coinciden")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=tenant_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        if not customer.password_hash:
            raise HTTPException(status_code=400, detail="Este usuario no tiene contraseña configurada")

        # Verificar contraseña actual (formato salt:sha256)
        parts = customer.password_hash.split(":")
        if len(parts) != 2:
            raise HTTPException(status_code=500, detail="Hash de contraseña inválido en base de datos")

        stored_salt, stored_digest = parts[0], parts[1]
        current_digest = hashlib.sha256((body.current_password + stored_salt).encode()).hexdigest()

        if current_digest != stored_digest:
            raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

        # Generar nuevo hash
        new_salt = secrets.token_hex(16)
        new_hash = f"{new_salt}:{hashlib.sha256((body.new_password + new_salt).encode()).hexdigest()}"
        customer.password_hash = new_hash
        db.commit()

        return {"message": "Contraseña actualizada exitosamente"}
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# Dominios del tenant
# ─────────────────────────────────────────────────────────

@router.get("/api/my-domains")
async def get_my_domains(request: Request, access_token: str = Cookie(None)):
    """Lista los dominios del tenant: dominio base + custom domains."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.id == tenant_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        result = []

        # Dominio base (.sajet.us) — siempre presente
        base_domain = f"{customer.subdomain}.sajet.us"
        result.append({
            "id": None,
            "external_domain": base_domain,
            "verification_status": "verified",
            "is_active": True,
            "sajet_subdomain": customer.subdomain,
            "sajet_full_domain": base_domain,
            "source": "base",
            "created_at": customer.created_at.isoformat() if hasattr(customer, "created_at") and customer.created_at else None,
        })

        # Custom domains
        domains = db.query(CustomDomain).filter_by(customer_id=tenant_id).all()
        for d in domains:
            # Omitir el dominio base si fue registrado como custom (duplicado)
            if d.external_domain == base_domain:
                continue
            result.append({
                "id": d.id,
                "external_domain": d.external_domain,
                "verification_status": d.verification_status.value if d.verification_status else None,
                "is_active": d.is_active,
                "sajet_subdomain": d.sajet_subdomain,
                "sajet_full_domain": d.sajet_full_domain,
                "source": "custom",
                "created_at": d.created_at.isoformat() if hasattr(d, "created_at") and d.created_at else None,
            })

        return {"domains": result}
    finally:
        db.close()


@router.post("/api/request-domain")
async def request_domain(
    body: DomainRequestBody,
    request: Request,
    access_token: str = Cookie(None)
):
    """Solicita un dominio personalizado para el tenant."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        result = DomainManager(db).create_domain(
            external_domain=body.external_domain,
            customer_id=tenant_id,
            created_by="tenant_portal"
        )

        if not result.get("success"):
            raise HTTPException(status_code=409, detail=result.get("error", "No se pudo registrar el dominio"))

        domain = result["domain"]
        return {
            "message": "Dominio registrado. Pendiente de verificación DNS.",
            "domain": {
                "id": domain["id"],
                "external_domain": domain["external_domain"],
                "verification_status": domain["verification_status"],
                "is_active": domain["is_active"],
            }
        }
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# Usuarios / Seats del tenant
# ─────────────────────────────────────────────────────────

@router.get("/api/users")
async def get_tenant_users(request: Request, access_token: str = Cookie(None)):
    """Retorna usuarios vivos de la instancia y su historial de licencias."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=tenant_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.customer_id == tenant_id,
                Subscription.status.in_([
                    SubscriptionStatus.active,
                    SubscriptionStatus.pending,
                    SubscriptionStatus.past_due,
                ]),
            )
            .order_by(Subscription.created_at.desc())
            .first()
        )

        seat_events = []
        accounts_snapshot = {
            "accounts": [],
            "active_accounts": 0,
            "billable_active_accounts": customer.user_count or 0,
        }
        if customer.subdomain:
            try:
                accounts_snapshot = fetch_tenant_accounts_snapshot(
                    customer.subdomain,
                    include_inactive=True,
                    customer=customer,
                )
            except Exception as exc:
                logger.warning("No se pudo cargar snapshot vivo de cuentas para %s: %s", customer.subdomain, exc)

        if subscription:
            events = (
                db.query(SeatEvent)
                .filter_by(subscription_id=subscription.id)
                .order_by(SeatEvent.created_at.desc())
                .limit(50)
                .all()
            )
            seat_events = [_serialize_seat_event(event) for event in events]

        plan = None
        if subscription and subscription.plan_name:
            plan = db.query(Plan).filter(Plan.name == subscription.plan_name).first()

        plan_user_limit = 0
        return {
            "accounts": accounts_snapshot["accounts"],
            "active_accounts": accounts_snapshot.get("active_accounts", 0),
            "billable_active_accounts": accounts_snapshot.get("billable_active_accounts", customer.user_count or 0),
            "current_user_count": accounts_snapshot.get("billable_active_accounts", customer.user_count or 0),
            "plan_user_limit": plan.max_users if plan and plan.max_users is not None else plan_user_limit,
            "seat_events": seat_events,
        }
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# Servicios adicionales / add-ons
# ─────────────────────────────────────────────────────────

@router.get("/api/services/catalog")
async def get_tenant_service_catalog(request: Request, access_token: str = Cookie(None)):
    """Catálogo de add-ons disponibles para el tenant actual."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        items = list_available_addon_services(db, tenant_id)
        return {"items": items, "total": len(items)}
    finally:
        db.close()


@router.get("/api/services/subscriptions")
async def get_tenant_service_subscriptions(request: Request, access_token: str = Cookie(None)):
    """Servicios adicionales activos del tenant."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        items = list_customer_addon_subscriptions(db, tenant_id)
        return {"items": items, "total": len(items)}
    finally:
        db.close()


@router.post("/api/services/purchase")
async def purchase_tenant_service(
    body: PortalAddonPurchaseRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """Compra un add-on para el tenant y genera factura automática."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        result = purchase_customer_addon(
            db=db,
            customer_id=tenant_id,
            catalog_item_id=body.catalog_item_id,
            quantity=body.quantity,
            acquired_via="tenant_portal",
        )
        return {
            "message": "Servicio adicional adquirido y facturado",
            **result,
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        db.close()


# ─────────────────────────────────────────────────────────
# Facturas ERP (BD local) con payment links
# ─────────────────────────────────────────────────────────

@router.get("/api/invoices")
async def get_tenant_invoices(request: Request, access_token: str = Cookie(None)):
    """
    Lista facturas del ERP (BD local) del tenant.
    Incluye payment_url de Stripe para facturas pendientes.
    """
    _configure_stripe()
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        invoices = db.query(Invoice).filter(
            Invoice.customer_id == tenant_id
        ).order_by(Invoice.created_at.desc()).limit(50).all()

        result = []
        for inv in invoices:
            item = {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "total": inv.total,
                "currency": inv.currency,
                "status": inv.status.value if inv.status else None,
                "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                "stripe_invoice_id": inv.stripe_invoice_id,
                "payment_url": None,
                "pdf_url": None,
                "hosted_url": None,
                "download_url": None,
                "view_url": None,
                "preferred_action": None,
            }

            if inv.stripe_invoice_id:
                try:
                    item.update(fetch_stripe_invoice_links(inv.stripe_invoice_id))
                except Exception:
                    item.update(build_invoice_action_urls(status=inv.status))
            else:
                item.update(build_invoice_action_urls(status=inv.status))

            result.append(item)

        return {"invoices": result, "total": len(result)}
    finally:
        db.close()


@router.post("/api/invoices/{invoice_id}/pay")
async def pay_invoice(invoice_id: int, request: Request, access_token: str = Cookie(None)):
    """
    Genera un link de pago para una factura pendiente del tenant.
    Si la factura ya está en Stripe, retorna hosted_invoice_url.
    Si no, crea la factura en Stripe y devuelve el link.
    """
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        inv = db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.customer_id == tenant_id,
        ).first()

        if not inv:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        if inv.status == InvoiceStatus.paid:
            raise HTTPException(status_code=400, detail="La factura ya está pagada")

        # Intentar generar payment link via Stripe Invoice
        try:
            result = push_invoice_to_stripe(db, inv)
            if result.get("hosted_invoice_url"):
                return {
                    "payment_url": result["hosted_invoice_url"],
                    "method": "stripe_invoice",
                    "invoice_number": inv.invoice_number,
                }
        except Exception as e:
            logger.warning(f"Push to Stripe failed, trying checkout: {e}")

        # Fallback: Checkout Session
        result = create_checkout_for_invoice(db, inv)
        return {
            "payment_url": result["checkout_url"],
            "method": result.get("method", "checkout_session"),
            "invoice_number": inv.invoice_number,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando pago: {str(e)}")
    finally:
        db.close()


# ═══════════════════════════════════════════════════════
# Tunnel Info — Estado del servicio del tenant
# ═══════════════════════════════════════════════════════

@router.get("/api/tunnel")
async def get_tenant_tunnel(request: Request, access_token: str = Cookie(None)):
    """
    Obtiene información del tunnel/servicio del tenant.
    El tenant ve: URL de acceso, estado del servicio, plan, próxima factura.
    """
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Portal disponible solo para tenants")

    result = await get_customer_tunnel_info(tenant_id)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    # Filtrar info sensible — el tenant solo ve lo que necesita
    deployment = result.get("deployment", {})
    subscription = result.get("subscription", {})
    cloudflare = result.get("cloudflare", {})

    return {
        "has_service": result.get("has_tunnel", False),
        "service_active": deployment.get("tunnel_active", False),
        "url": deployment.get("tunnel_url"),
        "subdomain": deployment.get("subdomain"),
        "plan": deployment.get("plan_type"),
        "subscription_status": subscription.get("status") if subscription else None,
        "plan_name": subscription.get("plan_name") if subscription else None,
        "next_billing": subscription.get("current_period_end") if subscription else None,
        "connection_health": cloudflare.get("status") if cloudflare else "unknown",
    }
