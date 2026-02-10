"""
Portal del Tenant - Vista de facturación y gestión de suscripción
"""
from fastapi import APIRouter, HTTPException, Request, status, Depends, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..models.database import Customer, Subscription, SessionLocal, SubscriptionStatus
from .roles import verify_token_with_role
import stripe
import os
from datetime import datetime

router = APIRouter(prefix="/tenant", tags=["Tenant Portal"])
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

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
    return token_data


@router.get("/portal", response_class=HTMLResponse)
async def tenant_portal_page(request: Request, access_token: str = Cookie(None)):
    """Página principal del portal del tenant."""
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        return RedirectResponse(url="/login/tenant", status_code=302)
    
    try:
        verify_token_with_role(token, required_role="tenant")
        return templates.TemplateResponse("tenant_portal.html", {
            "request": request
        })
    except HTTPException:
        return RedirectResponse(url="/login/tenant", status_code=302)


@router.get("/api/info")
async def get_tenant_info(request: Request, access_token: str = Cookie(None)):
    """Obtiene información del tenant actual."""
    token_data = get_current_tenant(request, access_token)
    tenant_id = token_data.get("tenant_id")
    
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
