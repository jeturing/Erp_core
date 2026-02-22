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
    CustomDomain, SeatEvent, Invoice, InvoiceStatus,
)
from .roles import verify_token_with_role
from ..services.spa_shell import render_spa_shell
from ..services.stripe_billing import (
    push_invoice_to_stripe,
    create_checkout_for_invoice,
)
from ..services.tunnel_lifecycle import get_customer_tunnel_info
import stripe
import os
import hashlib
import secrets
import logging
from datetime import datetime
from ..services.domain_manager import DomainManager

router = APIRouter(prefix="/tenant", tags=["Tenant Portal"])
logger = logging.getLogger(__name__)

# Stripe config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


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
    # En ese caso, intentar resolver por email (claim sub).
    if not token_data.get("tenant_id"):
        username = token_data.get("sub")
        if username and "@" in username:
            db = SessionLocal()
            try:
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
            invoice_list.append({
                "id": inv.id,
                "amount": inv.amount_paid / 100,  # Convert from cents
                "currency": inv.currency,
                "status": inv.status,
                "date": datetime.fromtimestamp(inv.created).isoformat(),
                "pdf_url": inv.invoice_pdf,
                "hosted_url": inv.hosted_invoice_url
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
            success_url=f"{os.getenv('APP_URL', 'http://localhost:4443')}/tenant/portal?payment_updated=true",
            cancel_url=f"{os.getenv('APP_URL', 'http://localhost:4443')}/tenant/portal",
        )
        
        return {"checkout_url": session.url}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/api/cancel-subscription")
async def cancel_subscription(request: Request, access_token: str = Cookie(None)):
    """Cancela la suscripción del tenant."""
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
    """Lista los dominios personalizados del tenant."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        domains = db.query(CustomDomain).filter_by(customer_id=tenant_id).all()
        return {
            "domains": [
                {
                    "id": d.id,
                    "external_domain": d.external_domain,
                    "verification_status": d.verification_status,
                    "is_active": d.is_active,
                    "sajet_subdomain": d.sajet_subdomain,
                    "sajet_full_domain": d.sajet_full_domain,
                    "created_at": d.created_at.isoformat() if hasattr(d, "created_at") and d.created_at else None,
                }
                for d in domains
            ]
        }
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
    """Retorna historial de usuarios (seat events) del tenant."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")

    if not tenant_id:
        raise HTTPException(status_code=403, detail="Contexto de tenant requerido")

    db = SessionLocal()
    try:
        customer = db.query(Customer).filter_by(id=tenant_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        # Obtener la suscripción activa
        subscription = db.query(Subscription).filter_by(customer_id=tenant_id).first()

        seat_events = []
        current_user_count = customer.user_count or 0

        if subscription:
            events = (
                db.query(SeatEvent)
                .filter_by(subscription_id=subscription.id)
                .order_by(SeatEvent.created_at.desc())
                .limit(50)
                .all()
            )
            seat_events = [
                {
                    "id": e.id,
                    "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
                    "odoo_login": e.odoo_login,
                    "odoo_user_id": e.odoo_user_id,
                    "user_count_after": e.user_count_after,
                    "is_billable": e.is_billable,
                    "source": e.source,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]
            if events:
                current_user_count = events[0].user_count_after

        return {
            "current_user_count": current_user_count,
            "plan_user_limit": subscription.user_count if subscription else 1,
            "seat_events": seat_events,
        }
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
            }

            # Si tiene stripe_invoice_id, obtener URLs actualizadas
            if inv.stripe_invoice_id and inv.status != InvoiceStatus.paid:
                try:
                    s_inv = stripe.Invoice.retrieve(inv.stripe_invoice_id)
                    item["payment_url"] = s_inv.get("hosted_invoice_url")
                    item["pdf_url"] = s_inv.get("invoice_pdf")
                except Exception:
                    pass

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
