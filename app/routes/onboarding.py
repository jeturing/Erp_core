"""
Onboarding Routes - Customer registration and Stripe integration
"""
from fastapi import APIRouter, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import stripe
import os
from datetime import datetime
from ..models.database import Customer, Subscription, StripeEvent, SubscriptionStatus, SessionLocal
from ..services.odoo_provisioner import provision_tenant
import logging

router = APIRouter(tags=["Onboarding"])

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy_key_replace_with_real_key")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_dummy_secret")
APP_URL = os.getenv("APP_URL", "http://localhost:4443")

# Templates - use relative path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

logger = logging.getLogger(__name__)


# DTOs
class CheckoutRequest(BaseModel):
    full_name: str
    email: str
    company_name: str
    subdomain: str
    plan: str


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Página de marketing principal"""
    return templates.TemplateResponse("landing.html", {"request": request})


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, plan: str = "pro"):
    """Formulario de registro inicial en /signup"""
    return templates.TemplateResponse("onboarding_form.html", {"request": request, "plan": plan})


@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding_alias(request: Request, plan: str = "pro"):
    """Alias compatible para el formulario de registro"""
    return await signup_page(request, plan=plan)


@router.post("/api/checkout")
async def create_checkout_session(payload: CheckoutRequest):
    """Crea un customer en BD y redirige a Stripe Checkout."""
    db = SessionLocal()
    try:
        # Crear customer en BD
        customer = Customer(
            email=payload.email,
            full_name=payload.full_name,
            company_name=payload.company_name,
            subdomain=payload.subdomain
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Crear Stripe checkout session
        price_map = {
            "basic": "price_1234_basic",
            "pro": "price_1234_pro",
            "enterprise": "price_1234_enterprise",
        }
        price_id = price_map.get(payload.plan, "price_1234_basic")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_URL}/signup",
            client_reference_id=str(customer.id),
            customer_email=payload.email,
        )

        return {"checkout_url": session.url}
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Error al crear sesión de pago")
    finally:
        db.close()


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook de Stripe para eventos de pago."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    db = SessionLocal()
    try:
        # Guardar evento
        db.add(StripeEvent(
            event_id=event["id"],
            event_type=event["type"],
            payload=str(event),
            processed=False
        ))
        db.commit()

        # Procesar evento checkout.session.completed
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            customer_id = int(session.get("client_reference_id"))
            stripe_subscription_id = session.get("subscription")

            # Obtener customer
            customer = db.query(Customer).filter_by(id=customer_id).first()
            if customer:
                # Crear suscripción
                subscription = Subscription(
                    customer_id=customer.id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_checkout_session_id=session["id"],
                    plan_name="enterprise",  # TODO: obtener plan real
                    status=SubscriptionStatus.pending
                )
                db.add(subscription)
                db.commit()
                db.refresh(subscription)  # Obtener el ID asignado

                # Provisionar tenant en background con subscription_id
                background_tasks.add_task(
                    provision_tenant,
                    customer.subdomain,
                    customer.email,
                    customer.company_name,
                    subscription.id  # Pasar ID para actualizar estado
                )

        return JSONResponse(content={"status": "success"})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, session_id: str = None):
    """Página de éxito post-checkout"""
    subdomain = None
    odoo_url = None
    
    if session_id:
        db = SessionLocal()
        try:
            # Buscar la suscripción por session_id
            subscription = db.query(Subscription).filter_by(
                stripe_checkout_session_id=session_id
            ).first()
            
            if subscription and subscription.customer:
                subdomain = subscription.customer.subdomain
                odoo_url = f"https://{subdomain}.sajet.us"
        except Exception as e:
            logger.warning(f"Error fetching subscription: {e}")
        finally:
            db.close()
    
    # Si no se encontró, usar URL genérica
    if not odoo_url:
        odoo_url = "https://sajet.us"
        subdomain = "tu-empresa"
    
    return templates.TemplateResponse("success.html", {
        "request": request,
        "session_id": session_id,
        "subdomain": subdomain,
        "url": odoo_url
    })
