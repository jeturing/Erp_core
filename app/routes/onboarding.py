"""
Onboarding Routes - Customer registration and Stripe integration
Includes billing_mode routing: Direct, Partner A, Partner B (Escenario B)
"""
from fastapi import APIRouter, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import json
import stripe
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from ..models.database import (
    Customer, Subscription, StripeEvent, SubscriptionStatus, SessionLocal,
    BillingMode, BillingScenario, InvoiceIssuer, CollectorType, PayerType,
    Partner, PartnerStatus, Plan, Lead, LeadStatus, Invoice, InvoiceStatus,
    AuditEventRecord, TenantDeployment,
)
from ..services.tunnel_lifecycle import handle_stripe_subscription_event
from ..services.odoo_database_manager import (
    create_tenant_from_template,
    provision_tenant as provision_tenant_standard,
    COUNTRY_LOCALIZATION,
)
from ..services.deployment_writer import ensure_tenant_deployment
from ..services.nginx_domain_configurator import provision_sajet_subdomain
from ..services.tenant_credentials import build_tenant_admin_credentials
from ..services.spa_shell import render_spa_shell
from ..services.email_service import (
    send_payment_failed_email,
    send_subscription_cancelled_email,
    send_tenant_credentials,
)
from ..services.stripe_connect import compute_application_fee_percent, should_use_on_behalf_of
from ..config import get_runtime_setting
import logging

router = APIRouter(tags=["Onboarding"])

logger = logging.getLogger(__name__)


def _configure_stripe() -> str:
    stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
    return stripe.api_key


def _stripe_webhook_secret() -> str:
    return get_runtime_setting("STRIPE_WEBHOOK_SECRET", "")


def _stripe_webhook_secret_candidates() -> list[tuple[str, str]]:
    """Prueba secreto activo y secretos del modo configurado antes de fallar firma."""
    mode = str(get_runtime_setting("STRIPE_MODE", "live") or "live").strip().lower()
    candidates = [
        ("STRIPE_WEBHOOK_SECRET", _stripe_webhook_secret()),
        (
            "ACTIVE_MODE_WEBHOOK_SECRET",
            get_runtime_setting(
                "STRIPE_LIVE_WEBHOOK_SECRET" if mode == "live" else "STRIPE_TEST_WEBHOOK_SECRET",
                "",
            ),
        ),
        ("STRIPE_LIVE_WEBHOOK_SECRET", get_runtime_setting("STRIPE_LIVE_WEBHOOK_SECRET", "")),
        ("STRIPE_TEST_WEBHOOK_SECRET", get_runtime_setting("STRIPE_TEST_WEBHOOK_SECRET", "")),
    ]

    deduped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for label, secret in candidates:
        secret = (secret or "").strip()
        if not secret or secret in seen:
            continue
        seen.add(secret)
        deduped.append((label, secret))
    return deduped


def _construct_verified_event(payload: bytes, sig_header: Optional[str]) -> tuple[dict, str]:
    """Construye evento Stripe probando múltiples secretos configurados."""
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    last_error = None
    candidates = _stripe_webhook_secret_candidates()
    if not candidates:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")

    for label, secret in candidates:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
            logger.info("Stripe webhook validated with %s", label)
            return event, label
        except stripe.error.SignatureVerificationError as exc:
            last_error = exc

    raise last_error


def _map_invoice_status(status: Optional[str]) -> Optional[InvoiceStatus]:
    mapping = {
        "paid": InvoiceStatus.paid,
        "open": InvoiceStatus.issued,
        "draft": InvoiceStatus.draft,
        "void": InvoiceStatus.void,
        "voided": InvoiceStatus.void,
        "uncollectible": InvoiceStatus.overdue,
    }
    return mapping.get((status or "").lower())


def _update_local_subscription_from_event(db, stripe_sub: dict) -> Optional[Subscription]:
    """Refleja el estado local mínimo de la suscripción desde un evento Stripe."""
    from ..services.stripe_sync import upsert_stripe_subscription

    results = {"linked": 0, "created": 0, "updated": 0, "skipped": 0, "errors": [], "details": []}
    try:
        upsert_stripe_subscription(db, stripe_sub, results)
    except Exception:
        # Fallback mínimo si el objeto del evento no trae suficiente contexto expandido.
        pass

    stripe_sub_id = stripe_sub.get("id")
    if not stripe_sub_id:
        return None

    local_sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_sub_id
    ).first()
    if not local_sub:
        return None

    new_status = stripe_sub.get("status")
    if new_status:
        try:
            local_sub.status = SubscriptionStatus(new_status)
        except ValueError:
            pass

    if stripe_sub.get("current_period_start"):
        local_sub.current_period_start = datetime.utcfromtimestamp(stripe_sub["current_period_start"])
    if stripe_sub.get("current_period_end"):
        local_sub.current_period_end = datetime.utcfromtimestamp(stripe_sub["current_period_end"])
    local_sub.updated_at = datetime.utcnow()
    return local_sub


def _sync_local_invoice_from_event(db, invoice_obj: dict) -> Optional[Invoice]:
    """Actualiza la factura local desde el payload del evento o la crea vía lógica compartida."""
    from ..services.stripe_sync import upsert_stripe_invoice

    results = {"imported": 0, "updated": 0, "skipped_existing": 0, "skipped_no_match": 0, "errors": [], "details": []}
    upsert_stripe_invoice(db, invoice_obj, results)
    if results["errors"]:
        raise RuntimeError(results["errors"][0]["error"])
    return db.query(Invoice).filter(Invoice.stripe_invoice_id == invoice_obj.get("id")).first()


def _app_url() -> str:
    return get_runtime_setting("APP_URL", "http://localhost:4443")


# DTOs
class CheckoutRequest(BaseModel):
    full_name: str
    email: str
    company_name: str
    subdomain: str
    plan: str
    user_count: int = 1                          # Cantidad de usuarios (asientos)
    billing_period: str = "monthly"              # "monthly" | "annual"
    partner_code: Optional[str] = None           # Si viene de un partner
    custom_domain: Optional[str] = None          # Épica 8: dominio temprano
    is_accountant: bool = False                  # True = registro como contador/CPA
    country_code: Optional[str] = None           # Código ISO país (DO, US, MX, etc.)
    blueprint_package_name: Optional[str] = None # Blueprint de módulos predefinido


# ─────────────────────────────────────────────────────────────────
#  Helper: Auditoría de provisioning (sin Request object)
# ─────────────────────────────────────────────────────────────────
def _log_provisioning_audit(
    action: str,
    *,
    subdomain: str,
    detail: str = "",
    success: bool = True,
    subscription_id: int | None = None,
):
    """Registra un evento de auditoría desde un background task (sin Request)."""
    try:
        db = SessionLocal()
        record = AuditEventRecord(
            actor_username="stripe_webhook",
            actor_ip="background",
            action=action,
            target_type="tenant",
            target_id=subdomain,
            detail=detail[:2000] if detail else "",
            success=success,
        )
        db.add(record)
        db.commit()
    except Exception as exc:
        logger.warning("Audit log failed for %s/%s: %s", action, subdomain, exc)
    finally:
        try:
            db.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────
#  Motor maduro de provisioning desde Stripe checkout (background)
# ─────────────────────────────────────────────────────────────────

async def _provision_tenant_from_checkout(
    *,
    subdomain: str,
    company_name: str,
    admin_email: str,
    subscription_id: int,
    customer_id: int,
    plan_name: str = "enterprise",
    partner_id: int | None = None,
    country_code: str | None = None,
    blueprint_package_name: str | None = None,
):
    """
    Provisiona un tenant Odoo completo tras un pago exitoso en Stripe.

    Delega TODA la lógica al orquestador único (`TenantLifecycleOrchestrator`),
    el mismo que usa el admin SPA. Garantiza un único camino end-to-end.
    """
    from ..services.tenant_lifecycle import orchestrator, TenantSpec

    log_prefix = f"[provision:{subdomain}]"
    spec = TenantSpec(
        subdomain=subdomain,
        company_name=company_name,
        admin_email=admin_email,
        plan_name=plan_name,
        partner_id=partner_id,
        country_code=country_code,
        blueprint_package_name=blueprint_package_name,
        customer_id=customer_id,
        subscription_id=subscription_id,
        send_credentials_email=True,
    )

    op = await orchestrator.provision(spec, source="onboarding")

    # Auditoría agregada
    _log_provisioning_audit(
        "tenant.provisioned" if op.success else "tenant.provision.failed",
        subdomain=subdomain,
        detail=f"plan={plan_name} partner_id={partner_id} country={country_code} steps={len(op.steps)} error={op.error}",
        success=op.success,
        subscription_id=subscription_id,
    )

    if op.success:
        # Marcar suscripción ACTIVE + tenant_provisioned (la columna odoo_db_name
        # NO existe en el schema; el subdominio actúa como nombre de BD por
        # convención y se persiste en TenantDeployment.subdomain).
        try:
            db_session = SessionLocal()
            sub = db_session.query(Subscription).filter_by(id=subscription_id).first()
            if sub:
                sub.status = SubscriptionStatus.ACTIVE
                sub.tenant_provisioned = True
                db_session.commit()
        except Exception as e:
            logger.warning("%s Subscription update falló: %s", log_prefix, e)
        finally:
            try:
                db_session.close()
            except Exception:
                pass
        logger.info("%s 🎉 Provisioning completo via orchestrator", log_prefix)
    else:
        logger.error("%s ❌ Provisioning falló: %s", log_prefix, op.error)
    return op


async def _provision_tenant_from_checkout_LEGACY(
    *,
    subdomain: str,
    company_name: str,
    admin_email: str,
    subscription_id: int,
    customer_id: int,
    plan_name: str = "enterprise",
    partner_id: int | None = None,
    country_code: str | None = None,
    blueprint_package_name: str | None = None,
):
    """
    [DEPRECATED 2026-04-22] Implementación inline anterior, mantenida como
    referencia. NO usar — el callsite invoca la versión que delega al
    orquestador (`TenantLifecycleOrchestrator`).
    """
    from ..config import ODOO_PRIMARY_IP
    log_prefix = f"[provision:{subdomain}]"

    # 1 ── Credenciales
    admin_login, admin_password = build_tenant_admin_credentials(subdomain)
    logger.info("%s Generando credenciales admin_login=%s", log_prefix, admin_login)

    # 2 ── Crear base de datos Odoo (fast-path SQL → fallback HTTP) ─ MISMA ruta que admin
    db_name = subdomain
    loc = COUNTRY_LOCALIZATION.get((country_code or "US").upper(), COUNTRY_LOCALIZATION["US"])
    creation_mode = None
    server_id_used = None

    try:
        # Fast path: SQL CREATE DATABASE WITH TEMPLATE (firma: subdomain=, no new_db=)
        fast = await create_tenant_from_template(
            subdomain=db_name,
            company_name=company_name,
            admin_login=admin_login,
            admin_password=admin_password,
            partner_id=partner_id,
            country_code=(country_code or "US").upper(),
            blueprint_package_name=blueprint_package_name,
        )
        if fast and fast.get("success"):
            creation_mode = "fast"
            server_id_used = fast.get("server")
            logger.info("%s DB creada vía SQL fast-path ✅ (server=%s)", log_prefix, server_id_used)
        else:
            raise RuntimeError(fast.get("error") if fast else "fast-path returned None")
    except Exception as e:
        logger.warning("%s SQL fast-path falló: %s — fallback HTTP", log_prefix, e)
        try:
            result = await provision_tenant_standard(
                subdomain=db_name,
                company_name=company_name,
                admin_login=admin_login,
                admin_password=admin_password,
                country_code=(country_code or "US").upper(),
                lang=loc.get("lang", "en_US"),
                blueprint_package_name=blueprint_package_name,
            )
            if not result.get("success"):
                raise RuntimeError(result.get("error", "provision_tenant_standard failed"))
            creation_mode = "fallback_standard"
            server_id_used = result.get("server")
            logger.info("%s DB creada vía HTTP fallback ✅ (server=%s)", log_prefix, server_id_used)
        except Exception as e2:
            logger.error("%s ❌ Provisioning DB falló: %s", log_prefix, e2)
            _log_provisioning_audit(
                "tenant.provision.failed",
                subdomain=subdomain,
                detail=str(e2),
                success=False,
                subscription_id=subscription_id,
            )
            return

    # 3 ── Registrar deployment (resuelve node desde server_id, sin IP hardcoded)
    deployment_node_ip: str | None = None
    deployment_http_port: int = 8080
    deployment_chat_port: int = 8072
    try:
        db_session = SessionLocal()
        ensure_tenant_deployment(
            subdomain=subdomain,
            subscription_id=subscription_id,
            customer_id=customer_id,
            server_id=server_id_used,
            plan_name=plan_name,
            db=db_session,
        )
        db_session.commit()
        # Resolver datos reales del deployment para nginx + cloudflared
        dep = db_session.query(TenantDeployment).filter(
            TenantDeployment.subdomain == subdomain
        ).first()
        if dep:
            deployment_node_ip = dep.backend_host or ODOO_PRIMARY_IP
            deployment_http_port = dep.http_port or 8080
            deployment_chat_port = dep.chat_port or 8072
        logger.info("%s Deployment registrado ✅ host=%s http=%s chat=%s",
                    log_prefix, deployment_node_ip, deployment_http_port, deployment_chat_port)
    except Exception as e:
        logger.warning("%s Deployment write falló: %s", log_prefix, e)
    finally:
        try:
            db_session.close()
        except Exception:
            pass

    # Si no logramos resolver, usar el primary actual (NUNCA 10.10.10.100 hardcodeado)
    deployment_node_ip = deployment_node_ip or ODOO_PRIMARY_IP

    # 4 ── Configurar nginx en el nodo Odoo real
    try:
        nginx_result = provision_sajet_subdomain(
            subdomain=subdomain,
            node_ip=deployment_node_ip,
            http_port=deployment_http_port,
            chat_port=deployment_chat_port,
        )
        logger.info("%s Nginx configurado en %s: %s ✅", log_prefix, deployment_node_ip, nginx_result)
    except Exception as e:
        logger.warning("%s Nginx config falló (no bloquea): %s", log_prefix, e)

    # 4b ── Cloudflared gateway en PCT 205: añadir routes y reiniciar tunnel
    try:
        from ..services.cloudflare_tunnel_gate import add_tenant_route
        gate_result = add_tenant_route(
            subdomain=subdomain,
            node_ip=deployment_node_ip,
            http_port=deployment_http_port,
            chat_port=deployment_chat_port,
        )
        if gate_result.get("success"):
            logger.info("%s Cloudflared route registrado ✅: %s", log_prefix, gate_result.get("changed"))
        else:
            logger.warning("%s Cloudflared route falló: %s", log_prefix, gate_result.get("error"))
    except Exception as e:
        logger.warning("%s Cloudflared gate falló: %s", log_prefix, e)

    # 5 ── Actualizar subscription status
    try:
        db_session = SessionLocal()
        sub = db_session.query(Subscription).filter_by(id=subscription_id).first()
        if sub:
            sub.status = SubscriptionStatus.ACTIVE
            sub.odoo_db_name = db_name
            db_session.commit()
        logger.info("%s Subscription %s → ACTIVE ✅", log_prefix, subscription_id)
    except Exception as e:
        logger.warning("%s Subscription update falló: %s", log_prefix, e)
    finally:
        try:
            db_session.close()
        except Exception:
            pass

    # 6 ── Auditoría
    _log_provisioning_audit(
        "tenant.provisioned",
        subdomain=subdomain,
        detail=f"plan={plan_name} partner_id={partner_id} country={country_code}",
        success=True,
        subscription_id=subscription_id,
    )

    # 7 ── Enviar credenciales por email
    try:
        send_tenant_credentials(
            to_email=admin_email,
            company_name=company_name,
            subdomain=subdomain,
            admin_login=admin_login,
            admin_password=admin_password,
            plan_name=plan_name,
        )
        logger.info("%s Email de credenciales enviado a %s ✅", log_prefix, admin_email)
    except Exception as e:
        logger.warning("%s Email de credenciales falló: %s", log_prefix, e)

    logger.info(
        "%s 🎉 Provisioning completo — %s.sajet.us listo para %s",
        log_prefix, subdomain, admin_email,
    )


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
    _configure_stripe()
    db = SessionLocal()
    try:
        # ── Resolver partner si viene partner_code ──
        partner = None
        billing_mode = BillingMode.JETURING_DIRECT_SUBSCRIPTION
        invoice_issuer = InvoiceIssuer.JETURING
        collector = CollectorType.STRIPE_DIRECT
        payer_type = PayerType.CLIENT

        if payload.partner_code:
            partner = db.query(Partner).filter(
                Partner.partner_code == payload.partner_code,
                Partner.status == PartnerStatus.active,
            ).first()
            if not partner:
                raise HTTPException(404, f"Partner code '{payload.partner_code}' not found or inactive")

            # Determinar billing mode según configuración del partner
            scenario = partner.billing_scenario or BillingScenario.jeturing_collects

            if scenario == BillingScenario.partner_collects:
                billing_mode = BillingMode.PARTNER_PAYS_FOR_CLIENT
                invoice_issuer = InvoiceIssuer.JETURING
                collector = CollectorType.PARTNER_EXTERNAL
                payer_type = PayerType.PARTNER
            else:
                # Escenario A: SAJET cobra en Stripe y dispersa al partner por Connect.
                if not partner.stripe_account_id or not partner.stripe_onboarding_complete:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"El partner '{partner.company_name}' aún no tiene Stripe Connect listo "
                            "para cobrar y dispersar fondos."
                        ),
                    )
                billing_mode = BillingMode.PARTNER_DIRECT
                invoice_issuer = InvoiceIssuer.PARTNER
                collector = CollectorType.STRIPE_CONNECT
                payer_type = PayerType.CLIENT

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
            fair_use_enabled=True,
            partner_id=partner.id if partner else None,
            is_accountant=payload.is_accountant,
            accountant_firm_name=payload.company_name if payload.is_accountant else None,
        )
        db.add(customer)
        db.flush()

        # ── Crear Lead en pipeline solo cuando el alta viene por un partner ──
        lead = None
        if partner:
            lead = Lead(
                partner_id=partner.id,
                company_name=payload.company_name,
                contact_email=payload.email,
                contact_name=payload.full_name,
                status=LeadStatus.new,
                notes=(
                    f"billing_mode={billing_mode.value}; "
                    f"plan={payload.plan}; users={user_count}; source=onboarding_checkout"
                ),
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
            "success_url": f"{_app_url()}/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{_app_url()}/signup",
            "client_reference_id": str(customer.id),
            "customer_email": payload.email,
            "metadata": {
                "billing_mode": billing_mode.value,
                "partner_id": str(partner.id) if partner else "",
                "lead_id": str(lead.id) if lead else "",
                "plan": payload.plan,
                "user_count": str(user_count),
                "is_accountant": str(payload.is_accountant),
                "country_code": payload.country_code or "",
                "blueprint_package_name": payload.blueprint_package_name or "",
            },
        }

        # Escenario A con Stripe Connect:
        # destination charge en la plataforma + dispersión automática al partner.
        if billing_mode == BillingMode.PARTNER_DIRECT and partner and partner.stripe_account_id:
            subscription_data = {
                "application_fee_percent": compute_application_fee_percent(partner.commission_rate),
                "transfer_data": {
                    "destination": partner.stripe_account_id,
                },
                "metadata": {
                    "partner_id": str(partner.id),
                    "billing_scenario": (partner.billing_scenario.value if partner.billing_scenario else ""),
                    "commission_rate": str(partner.commission_rate or 0),
                },
            }
            if should_use_on_behalf_of(partner.country, partner.stripe_charges_enabled):
                subscription_data["on_behalf_of"] = partner.stripe_account_id
            checkout_params["subscription_data"] = subscription_data

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
    _configure_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event, validated_with = _construct_verified_event(payload, sig_header)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    db = SessionLocal()
    try:
        existing_event = db.query(StripeEvent).filter(
            StripeEvent.event_id == event["id"]
        ).first()
        if existing_event:
            logger.info("Stripe webhook duplicate ignored: %s", event["id"])
            return JSONResponse(content={"status": "success", "duplicate": True})

        stripe_event = StripeEvent(
            event_id=event["id"],
            event_type=event["type"],
            payload=json.dumps(event, default=str),
            processed=False,
        )
        db.add(stripe_event)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            logger.info("Stripe webhook duplicate on insert ignored: %s", event["id"])
            return JSONResponse(content={"status": "success", "duplicate": True})

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
            country_code = metadata.get("country_code") or None
            blueprint_package_name = metadata.get("blueprint_package_name") or None

            # Obtener customer
            customer = db.query(Customer).filter_by(id=customer_id).first()
            if customer:
                if partner_id and customer.partner_id != partner_id:
                    customer.partner_id = partner_id

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
                    subscription.payer_type = PayerType.CLIENT
                elif billing_mode == BillingMode.PARTNER_DIRECT:
                    subscription.invoice_issuer = InvoiceIssuer.PARTNER
                    subscription.collector = CollectorType.STRIPE_CONNECT
                    subscription.payer_type = PayerType.CLIENT
                elif billing_mode == BillingMode.PARTNER_PAYS_FOR_CLIENT:
                    subscription.invoice_issuer = InvoiceIssuer.JETURING
                    subscription.collector = CollectorType.PARTNER_EXTERNAL
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
                        lead.converted_customer_id = customer.id
                        if not lead.converted_at:
                            lead.converted_at = datetime.utcnow()
                        db.commit()

                # ═══ Provisionar tenant con motor maduro (background) ═══
                background_tasks.add_task(
                    _provision_tenant_from_checkout,
                    subdomain=customer.subdomain,
                    company_name=customer.company_name,
                    admin_email=customer.email,
                    subscription_id=subscription.id,
                    customer_id=customer.id,
                    plan_name=plan_name,
                    partner_id=partner_id,
                    country_code=country_code,
                    blueprint_package_name=blueprint_package_name,
                )

        elif event["type"] == "account.updated":
            account = event["data"]["object"]
            partner = db.query(Partner).filter(
                Partner.stripe_account_id == account.get("id")
            ).first()
            if partner:
                requirements = account.get("requirements", {}) or {}
                currently_due = requirements.get("currently_due") or []
                disabled_reason = requirements.get("disabled_reason")
                details_submitted = bool(account.get("details_submitted"))
                charges_enabled = bool(account.get("charges_enabled"))
                payouts_enabled = bool(account.get("payouts_enabled"))
                onboarding_ready = (
                    details_submitted
                    and not currently_due
                    and not disabled_reason
                    and (payouts_enabled or charges_enabled)
                )

                partner.stripe_charges_enabled = charges_enabled
                partner.stripe_onboarding_complete = onboarding_ready
                if onboarding_ready and partner.onboarding_step < 4:
                    partner.onboarding_step = 4
                    partner.onboarding_completed_at = datetime.utcnow()
                db.commit()
                logger.info(
                    "Stripe Connect sync partner=%s account=%s ready=%s payouts=%s charges=%s",
                    partner.id,
                    account.get("id"),
                    onboarding_ready,
                    payouts_enabled,
                    charges_enabled,
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
            _update_local_subscription_from_event(db, stripe_sub)
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
            _sync_local_invoice_from_event(db, invoice_obj)

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

        elif event["type"] in (
            "invoice.paid",
            "invoice.finalized",
            "invoice.voided",
            "invoice.marked_uncollectible",
        ):
            invoice_obj = event["data"]["object"]
            local_invoice = _sync_local_invoice_from_event(db, invoice_obj)

            stripe_sub_id = invoice_obj.get("subscription")
            if stripe_sub_id:
                local_sub = db.query(Subscription).filter_by(
                    stripe_subscription_id=stripe_sub_id
                ).first()
                if local_sub:
                    if event["type"] == "invoice.paid":
                        local_sub.status = SubscriptionStatus.active
                    elif event["type"] == "invoice.marked_uncollectible":
                        local_sub.status = SubscriptionStatus.past_due
                    local_sub.updated_at = datetime.utcnow()

            if event["type"] == "invoice.paid" and local_invoice and local_invoice.paid_at is None:
                local_invoice.paid_at = datetime.utcnow()

        # ═══ Suscripción cancelada — notificar al cliente ═══
        elif event["type"] == "customer.subscription.deleted":
            stripe_sub = event["data"]["object"]
            stripe_sub_id = stripe_sub.get("id")
            local_sub = _update_local_subscription_from_event(db, stripe_sub)
            if local_sub:
                local_sub.status = SubscriptionStatus.cancelled
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

        else:
            logger.info(
                "Stripe webhook event acknowledged without business handler: type=%s secret=%s",
                event["type"],
                validated_with,
            )

        stripe_event = db.query(StripeEvent).filter(
            StripeEvent.event_id == event["id"]
        ).first()
        if stripe_event:
            stripe_event.processed = True
        db.commit()

        return JSONResponse(content={"status": "success"})
    except Exception as e:
        db.rollback()
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
