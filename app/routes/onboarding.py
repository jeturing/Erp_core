"""
Onboarding Routes - Customer registration and Stripe integration
Includes billing_mode routing: Direct, Partner A, Partner B (Escenario B)
"""
from fastapi import APIRouter, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import stripe
import os
from datetime import datetime
from ..models.database import (
    Customer, Subscription, StripeEvent, SubscriptionStatus, SessionLocal,
    BillingMode, InvoiceIssuer, CollectorType, PayerType,
    Partner, Plan, Lead, LeadStatus,
)
from ..services.tunnel_lifecycle import handle_stripe_subscription_event
from ..services.odoo_provisioner import provision_tenant
from ..services.spa_shell import render_spa_shell
from ..services.email_service import send_payment_failed_email, send_subscription_cancelled_email
import logging

router = APIRouter(tags=["Onboarding"])

# Stripe configuration
from ..config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, APP_URL
stripe.api_key = STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


# DTOs
class CheckoutRequest(BaseModel):
    full_name: str
    email: str
    company_name: str
    subdomain: str
    plan: str
    user_count: int = 1                  # Cantidad de usuarios (asientos)
    billing_period: str = "monthly"      # "monthly" | "annual"
    partner_code: Optional[str] = None      # Si viene de un partner
    custom_domain: Optional[str] = None      # Épica 8: dominio temprano
    is_accountant: bool = False              # True = registro como contador/CPA


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Página de marketing principal - SPA"""
    return render_spa_shell("landing")


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, plan: str = "pro"):
    """Formulario de registro inicial en /signup - SPA"""
    return render_spa_shell("signup", {"plan": plan})


@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding_alias(request: Request, plan: str = "pro"):
    """Alias compatible para el formulario de registro"""
    return await signup_page(request, plan=plan)


@router.post("/api/checkout")
async def create_checkout_session(payload: CheckoutRequest, background_tasks: BackgroundTasks):
    """
    Crea un customer en BD y redirige a Stripe Checkout.
    Routing por billing_mode:
    - Sin partner_code → JETURING_DIRECT_SUBSCRIPTION (Jeturing cobra)
    - Con partner_code escenario A → PARTNER_DIRECT (Partner cobra con Stripe Connect)
    - Con partner_code escenario B → PARTNER_PAYS_FOR_CLIENT (Partner paga, Jeturing emite intercompany)
    """
    db = SessionLocal()
    try:
        # ── Resolver partner si viene partner_code ──
        partner = None
        billing_mode = BillingMode.JETURING_DIRECT_SUBSCRIPTION
        invoice_issuer = InvoiceIssuer.JETURING
        collector = CollectorType.STRIPE_DIRECT
        payer_type = PayerType.END_CUSTOMER

        if payload.partner_code:
            partner = db.query(Partner).filter(
                Partner.partner_code == payload.partner_code,
                Partner.is_active == True,
            ).first()
            if not partner:
                raise HTTPException(404, f"Partner code '{payload.partner_code}' not found or inactive")

            # Determinar billing mode según configuración del partner
            if partner.billing_scenario == "B":
                billing_mode = BillingMode.PARTNER_PAYS_FOR_CLIENT
                invoice_issuer = InvoiceIssuer.JETURING
                collector = CollectorType.PARTNER_COLLECTS
                payer_type = PayerType.PARTNER
            else:
                # Escenario A (default partner)
                billing_mode = BillingMode.PARTNER_DIRECT
                invoice_issuer = InvoiceIssuer.PARTNER
                collector = CollectorType.STRIPE_CONNECT
                payer_type = PayerType.END_CUSTOMER

        # ── Resolver plan desde DB ──
        plan = db.query(Plan).filter(
            Plan.name == payload.plan,
            Plan.is_active == True,
        ).first()

        if not plan:
            # No fallback con IDs ficticios — el plan debe existir en BD con stripe_price_id
            logger.error(f"Plan '{payload.plan}' not found or inactive in DB")
            raise HTTPException(
                status_code=400,
                detail=f"El plan '{payload.plan}' no está disponible. Contacte soporte."
            )
        # Validar que el plan tenga un stripe_price_id real
        if not plan.stripe_price_id:
            logger.error(f"Plan '{plan.name}' exists but has no stripe_price_id configured")
            raise HTTPException(
                status_code=500,
                detail=f"Plan '{plan.name}' no tiene precio configurado en Stripe. Contacte soporte."
            )
        
        price_id = plan.stripe_price_id
        user_count = max(payload.user_count, plan.included_users)
        # Calcular precio mensual dinámico con partner override
        monthly_amount = plan.calculate_monthly(
            user_count,
            partner.id if partner else None
        )

        # ── Crear customer en BD ──
        customer = Customer(
            email=payload.email,
            full_name=payload.full_name,
            company_name=payload.company_name,
            subdomain=payload.subdomain,
            user_count=user_count,
            is_accountant=payload.is_accountant,
            accountant_firm_name=payload.company_name if payload.is_accountant else None,
        )
        db.add(customer)
        db.flush()

        # ── Crear Lead en pipeline ──
        lead = Lead(
            customer_id=customer.id,
            partner_id=partner.id if partner else None,
            company_name=payload.company_name,
            contact_email=payload.email,
            contact_name=payload.full_name,
            plan_interest=payload.plan,
            status=LeadStatus.new,
            source="onboarding_checkout",
            notes=f"billing_mode={billing_mode.value}",
        )
        db.add(lead)
        db.flush()

        # ── Épica 8: Early domain verification (no bloqueante) ──
        if payload.custom_domain:
            try:
                from ..services.domain_manager import DomainManager
                domain_mgr = DomainManager(db)
                domain_result = domain_mgr.create_domain(
                    external_domain=payload.custom_domain,
                    customer_id=customer.id,
                    created_by="onboarding_early",
                )
                logger.info(f"Early domain registered: {payload.custom_domain} → {domain_result.get('success')}")
            except Exception as e:
                logger.warning(f"Early domain registration failed (non-blocking): {e}")

        db.commit()
        db.refresh(customer)

        # ── Crear Stripe Checkout Session ──
        checkout_params = {
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": user_count}],
            "mode": "subscription",
            "success_url": f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{APP_URL}/signup",
            "client_reference_id": str(customer.id),
            "customer_email": payload.email,
            "metadata": {
                "billing_mode": billing_mode.value,
                "partner_id": str(partner.id) if partner else "",
                "lead_id": str(lead.id),
                "plan": payload.plan,
                "user_count": str(user_count),
                "is_accountant": str(payload.is_accountant),
            },
        }

        # Escenario A con Stripe Connect: application_fee_percent 50%
        if billing_mode == BillingMode.PARTNER_DIRECT and partner and partner.stripe_account_id:
            checkout_params["subscription_data"] = {
                "application_fee_percent": 50,
            }
            checkout_params["stripe_account"] = partner.stripe_account_id

        session = stripe.checkout.Session.create(**checkout_params)

        return {
            "checkout_url": session.url,
            "billing_mode": billing_mode.value,
            "partner": partner.company_name if partner else None,
        }
    except HTTPException:
        raise
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
            metadata = session.get("metadata", {})

            # Extraer billing_mode de metadata
            bm_str = metadata.get("billing_mode", "jeturing_direct_subscription")
            try:
                billing_mode = BillingMode(bm_str)
            except ValueError:
                billing_mode = BillingMode.JETURING_DIRECT_SUBSCRIPTION

            partner_id = int(metadata.get("partner_id")) if metadata.get("partner_id") else None
            plan_name = metadata.get("plan", "enterprise")

            # Obtener customer
            customer = db.query(Customer).filter_by(id=customer_id).first()
            if customer:
                # Crear suscripción con billing_mode
                subscription = Subscription(
                    customer_id=customer.id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_checkout_session_id=session["id"],
                    plan_name=plan_name,
                    status=SubscriptionStatus.pending,
                    billing_mode=billing_mode,
                    owner_partner_id=partner_id,
                )

                # Configurar campos de billing según modo
                if billing_mode == BillingMode.JETURING_DIRECT_SUBSCRIPTION:
                    subscription.invoice_issuer = InvoiceIssuer.JETURING
                    subscription.collector = CollectorType.STRIPE_DIRECT
                    subscription.payer_type = PayerType.END_CUSTOMER
                elif billing_mode == BillingMode.PARTNER_DIRECT:
                    subscription.invoice_issuer = InvoiceIssuer.PARTNER
                    subscription.collector = CollectorType.STRIPE_CONNECT
                    subscription.payer_type = PayerType.END_CUSTOMER
                elif billing_mode == BillingMode.PARTNER_PAYS_FOR_CLIENT:
                    subscription.invoice_issuer = InvoiceIssuer.JETURING
                    subscription.collector = CollectorType.PARTNER_COLLECTS
                    subscription.payer_type = PayerType.PARTNER

                db.add(subscription)
                db.commit()
                db.refresh(subscription)

                # Actualizar lead status
                lead_id = metadata.get("lead_id")
                if lead_id:
                    lead = db.query(Lead).filter(Lead.id == int(lead_id)).first()
                    if lead:
                        lead.status = LeadStatus.tenant_ready
                        db.commit()

                # Provisionar tenant en background con subscription_id
                background_tasks.add_task(
                    provision_tenant,
                    customer.subdomain,
                    customer.email,
                    customer.company_name,
                    subscription.id  # Pasar ID para actualizar estado
                )

        # ═══ Tunnel Lifecycle — Sincronizar tunnel con estado de suscripción ═══
        elif event["type"] in (
            "customer.subscription.updated",
            "customer.subscription.paused",
            "customer.subscription.resumed",
        ):
            stripe_sub = event["data"]["object"]
            stripe_sub_id = stripe_sub.get("id")
            new_status = stripe_sub.get("status", "")
            if stripe_sub_id:
                background_tasks.add_task(
                    handle_stripe_subscription_event,
                    stripe_sub_id,
                    new_status,
                )
                logger.info(f"📋 Tunnel lifecycle queued: {stripe_sub_id} → {new_status}")

        elif event["type"] == "invoice.payment_failed":
            invoice_obj = event["data"]["object"]
            stripe_sub_id = invoice_obj.get("subscription")
            attempt_count = invoice_obj.get("attempt_count", 1)
            next_payment_attempt = invoice_obj.get("next_payment_attempt")
            amount_due = (invoice_obj.get("amount_due", 0) / 100)  # cents → dollars

            if stripe_sub_id:
                # Tunnel lifecycle — marcar como past_due
                background_tasks.add_task(
                    handle_stripe_subscription_event,
                    stripe_sub_id,
                    "past_due",
                )
                logger.info(f"📋 Payment failed → tunnel lifecycle queued: {stripe_sub_id}")

                # Dunning email — notificar al cliente
                sub = db.query(Subscription).filter_by(
                    stripe_subscription_id=stripe_sub_id
                ).first()
                if sub and sub.customer:
                    next_retry = None
                    if next_payment_attempt:
                        from datetime import datetime
                        next_retry = datetime.fromtimestamp(next_payment_attempt).strftime("%d/%m/%Y %H:%M")

                    background_tasks.add_task(
                        send_payment_failed_email,
                        to_email=sub.customer.email,
                        company_name=sub.customer.company_name or "Su empresa",
                        plan_name=sub.plan_name or "pro",
                        amount=amount_due if amount_due > 0 else 49.0,
                        attempt_count=attempt_count,
                        next_retry_date=next_retry,
                        customer_id=sub.customer.id,
                    )
                    logger.info(f"📧 Dunning email queued for {sub.customer.email} (attempt #{attempt_count})")

        # ═══ Suscripción cancelada — notificar al cliente ═══
        elif event["type"] == "customer.subscription.deleted":
            stripe_sub = event["data"]["object"]
            stripe_sub_id = stripe_sub.get("id")
            if stripe_sub_id:
                background_tasks.add_task(
                    handle_stripe_subscription_event,
                    stripe_sub_id,
                    "canceled",
                )

                sub = db.query(Subscription).filter_by(
                    stripe_subscription_id=stripe_sub_id
                ).first()
                if sub and sub.customer:
                    background_tasks.add_task(
                        send_subscription_cancelled_email,
                        to_email=sub.customer.email,
                        company_name=sub.customer.company_name or "Su empresa",
                        plan_name=sub.plan_name or "pro",
                        customer_id=sub.customer.id,
                    )
                    logger.info(f"📧 Cancellation email queued for {sub.customer.email}")

        return JSONResponse(content={"status": "success"})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.get("/success", response_class=HTMLResponse)
async def success_page(request: Request, session_id: str = None):
    """Página de éxito post-checkout - SPA"""
    subdomain = None
    odoo_url = None

    if session_id:
        db = SessionLocal()
        try:
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

    if not odoo_url:
        odoo_url = "https://sajet.us"
        subdomain = "tu-empresa"

    return render_spa_shell("success", {
        "sessionId": session_id or "",
        "subdomain": subdomain,
        "odooUrl": odoo_url,
    })
