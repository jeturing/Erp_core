"""
Stripe Connect Express — Pagos automáticos a partners.
El dinero del partner nunca pasa por Jeturing; Stripe divide automáticamente.

Flujo:
1. Admin crea cuenta Express para partner → onboarding_url
2. Partner completa KYC en Stripe
3. Al cobrar suscripción, Stripe divide: X% a partner, resto a Jeturing
4. Partner ve sus pagos en Stripe Express dashboard
"""
import logging
from typing import Any, Dict, Optional

import stripe

from ..config import get_runtime_setting

logger = logging.getLogger(__name__)

EEA_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
}

SELF_SERVE_CROSS_BORDER_COUNTRIES = EEA_COUNTRIES | {"US", "GB", "CA", "CH"}


def _configure_stripe() -> str:
    stripe.api_key = get_runtime_setting("STRIPE_SECRET_KEY", "")
    return stripe.api_key


def _app_url() -> str:
    return get_runtime_setting("APP_URL", "https://sajet.us")


def _platform_country() -> str:
    return normalize_country_code(get_runtime_setting("STRIPE_PLATFORM_COUNTRY", "US"), "US")


def normalize_country_code(country_code: Optional[str], default: str = "US") -> str:
    code = (country_code or default or "US").strip().upper()
    return code if len(code) == 2 else default


def is_cross_border_country(partner_country: Optional[str], platform_country: Optional[str] = None) -> bool:
    platform = normalize_country_code(platform_country, _platform_country())
    partner = normalize_country_code(partner_country, platform)
    return partner != platform


def supports_self_serve_cross_border(
    partner_country: Optional[str],
    platform_country: Optional[str] = None,
) -> bool:
    platform = normalize_country_code(platform_country, _platform_country())
    partner = normalize_country_code(partner_country, platform)
    if partner == platform:
        return True
    return platform in SELF_SERVE_CROSS_BORDER_COUNTRIES and partner in SELF_SERVE_CROSS_BORDER_COUNTRIES


def should_request_card_payments(
    partner_country: Optional[str],
    platform_country: Optional[str] = None,
) -> bool:
    return not is_cross_border_country(partner_country, platform_country)


def should_use_on_behalf_of(
    partner_country: Optional[str],
    charges_enabled: bool,
    platform_country: Optional[str] = None,
) -> bool:
    return bool(charges_enabled) and not is_cross_border_country(partner_country, platform_country)


def compute_application_fee_percent(partner_commission_pct: Optional[float]) -> float:
    try:
        partner_pct = float(partner_commission_pct or 0)
    except (TypeError, ValueError):
        partner_pct = 0.0
    partner_pct = max(0.0, min(100.0, partner_pct))
    return round(100.0 - partner_pct, 2)


def _read_value(container: Any, field: str, default: Any = None) -> Any:
    if container is None:
        return default
    if isinstance(container, dict):
        return container.get(field, default)
    return getattr(container, field, default)


def serialize_account_status(account: Any) -> Dict[str, Any]:
    requirements = _read_value(account, "requirements", {}) or {}
    capabilities = _read_value(account, "capabilities", {}) or {}

    country = normalize_country_code(_read_value(account, "country", "US"), "US")
    currently_due = list(_read_value(requirements, "currently_due", []) or [])
    eventually_due = list(_read_value(requirements, "eventually_due", []) or [])
    past_due = list(_read_value(requirements, "past_due", []) or [])
    disabled_reason = _read_value(requirements, "disabled_reason")

    details_submitted = bool(_read_value(account, "details_submitted", False))
    charges_enabled = bool(_read_value(account, "charges_enabled", False))
    payouts_enabled = bool(_read_value(account, "payouts_enabled", False))
    onboarding_ready = (
        details_submitted
        and not currently_due
        and not disabled_reason
        and (payouts_enabled or charges_enabled)
    )

    settlement_mode = "cross_border" if is_cross_border_country(country) else "domestic"

    return {
        "success": True,
        "account_id": _read_value(account, "id"),
        "email": _read_value(account, "email"),
        "charges_enabled": charges_enabled,
        "payouts_enabled": payouts_enabled,
        "details_submitted": details_submitted,
        "country": country,
        "business_type": _read_value(account, "business_type"),
        "created": _read_value(account, "created"),
        "requirements_currently_due": currently_due,
        "requirements_eventually_due": eventually_due,
        "requirements_past_due": past_due,
        "requirements_disabled_reason": disabled_reason,
        "transfers_status": _read_value(capabilities, "transfers"),
        "card_payments_status": _read_value(capabilities, "card_payments"),
        "onboarding_ready": onboarding_ready,
        "settlement_mode": settlement_mode,
        "supports_self_serve_cross_border": supports_self_serve_cross_border(country),
    }


async def create_connect_account(
    partner_email: str,
    partner_company: str,
    partner_country: str = "US",
) -> Dict[str, Any]:
    """
    Crea una cuenta Stripe Connect Express para un partner.
    
    Express = Stripe maneja KYC, dashboard, 1099s.
    El partner solo completa un formulario de onboarding.
    
    Returns:
        {"success": True, "account_id": "acct_XXX", "onboarding_url": "https://..."}
    """
    _configure_stripe()
    try:
        normalized_country = normalize_country_code(partner_country, "US")
        capabilities = {
            "transfers": {"requested": True},
        }
        if should_request_card_payments(normalized_country):
            capabilities["card_payments"] = {"requested": True}

        account = stripe.Account.create(
            type="express",
            email=partner_email,
            country=normalized_country,
            business_type="company",
            company={"name": partner_company},
            capabilities=capabilities,
            metadata={
                "platform": "sajet",
                "partner_email": partner_email,
                "settlement_mode": "cross_border" if is_cross_border_country(normalized_country) else "domestic",
            },
        )

        logger.info(f"✅ Stripe Connect account creada: {account.id} para {partner_email}")

        return {
            "success": True,
            "account_id": account.id,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error creando Connect account: {e}")
        return {"success": False, "error": str(e)}


async def create_onboarding_link(
    account_id: str,
    return_path: str = "/admin/partners",
) -> Dict[str, Any]:
    """
    Genera URL de onboarding para que el partner complete KYC.
    Redirige de vuelta a la plataforma al completar.
    """
    _configure_stripe()
    try:
        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=f"{_app_url()}{return_path}?stripe_refresh=true",
            return_url=f"{_app_url()}{return_path}?stripe_onboarded=true&account={account_id}",
            type="account_onboarding",
        )

        return {
            "success": True,
            "url": link.url,
            "expires_at": link.expires_at,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error creando onboarding link: {e}")
        return {"success": False, "error": str(e)}


async def create_login_link(account_id: str) -> Dict[str, Any]:
    """
    Genera link para que partner acceda a su Stripe Express Dashboard.
    Solo funciona si onboarding está completo.
    """
    _configure_stripe()
    try:
        link = stripe.Account.create_login_link(account_id)
        return {"success": True, "url": link.url}
    except stripe.error.StripeError as e:
        logger.error(f"Error creando login link: {e}")
        return {"success": False, "error": str(e)}


async def get_account_status(account_id: str) -> Dict[str, Any]:
    """
    Verifica estado de la cuenta Connect del partner.
    """
    _configure_stripe()
    try:
        account = stripe.Account.retrieve(account_id)
        return serialize_account_status(account)

    except stripe.error.StripeError as e:
        logger.error(f"Error consultando Connect account: {e}")
        return {"success": False, "error": str(e)}


async def create_transfer(
    destination_account_id: str,
    amount_cents: int,
    currency: str = "usd",
    description: str = "",
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Transfiere fondos a la cuenta Connect del partner.
    
    Usar este método cuando Jeturing cobra y luego split manual.
    Para split automático en checkout, usar `payment_intent_data.transfer_data`.
    
    Args:
        destination_account_id: "acct_XXX"
        amount_cents: Monto en centavos (ej: 5000 = $50.00)
        currency: USD por defecto
        description: Descripción de la transferencia
        metadata: Metadatos adicionales
    """
    _configure_stripe()
    try:
        transfer = stripe.Transfer.create(
            amount=amount_cents,
            currency=currency,
            destination=destination_account_id,
            description=description or "Comisión SAJET Partner",
            metadata=metadata or {},
        )

        logger.info(f"✅ Transfer {transfer.id}: ${amount_cents/100:.2f} → {destination_account_id}")

        return {
            "success": True,
            "transfer_id": transfer.id,
            "amount": amount_cents / 100,
            "currency": currency,
            "destination": destination_account_id,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error en transfer: {e}")
        return {"success": False, "error": str(e)}


async def create_checkout_with_split(
    customer_stripe_id: str,
    price_id: str,
    partner_account_id: str,
    partner_commission_pct: float = 50.0,
    success_url: str = None,
    cancel_url: str = None,
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Crea Checkout Session donde Stripe divide automáticamente el pago.
    
    El dinero del partner NUNCA pasa por la cuenta de Jeturing.
    Stripe envía application_fee a Jeturing y el resto al partner.
    
    Ejemplo: Suscripción $100/mes
    - Partner recibe: $50 (50%)
    - Jeturing recibe: $50 (50% como application_fee)
    """
    _configure_stripe()
    try:
        # application_fee_percent = lo que se queda Jeturing (inverso de la comisión del partner)
        jeturing_pct = compute_application_fee_percent(partner_commission_pct)

        session = stripe.checkout.Session.create(
            customer=customer_stripe_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            payment_intent_data={
                "application_fee_amount": None,  # Se calcula con subscription_data
            },
            subscription_data={
                "application_fee_percent": jeturing_pct,
                "transfer_data": {
                    "destination": partner_account_id,
                },
                "metadata": metadata or {},
            },
            success_url=success_url or f"{_app_url()}/onboarding/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url or f"{_app_url()}/onboarding?cancelled=true",
        )

        logger.info(f"✅ Checkout con split: {session.id} → partner {partner_account_id} ({partner_commission_pct}%)")

        return {
            "success": True,
            "session_id": session.id,
            "checkout_url": session.url,
            "partner_account": partner_account_id,
            "partner_pct": partner_commission_pct,
            "jeturing_pct": jeturing_pct,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error creando checkout con split: {e}")
        return {"success": False, "error": str(e)}


async def get_partner_balance(account_id: str) -> Dict[str, Any]:
    """
    Obtiene balance actual de la cuenta Connect del partner.
    """
    _configure_stripe()
    try:
        balance = stripe.Balance.retrieve(stripe_account=account_id)

        available = sum(b.amount for b in balance.available) / 100 if balance.available else 0
        pending = sum(b.amount for b in balance.pending) / 100 if balance.pending else 0

        return {
            "success": True,
            "available": available,
            "pending": pending,
            "currency": balance.available[0].currency if balance.available else "usd",
        }

    except stripe.error.StripeError as e:
        logger.error(f"Error consultando balance: {e}")
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════
#  Stripe API v2 — Cuentas Connect para países no self-serve (DO, etc.)
#  Docs: https://docs.stripe.com/connect/design-an-integration
#  Endpoint: POST /v2/core/accounts
#  Requiere Stripe-Version: 2025-01-27.acacia
# ═══════════════════════════════════════════════════════════════════

import requests as _requests

STRIPE_API_V2_BASE = "https://api.stripe.com/v2"
STRIPE_V2_VERSION = "2025-01-27.acacia"

# Países que requieren API v2 (no soportados por Express v1 self-serve)
API_V2_REQUIRED_COUNTRIES = {"DO", "PR", "VE", "CO", "PE", "EC", "BO", "PY", "UY", "CL", "AR", "PA", "CR", "GT", "HN", "NI", "SV"}


def requires_api_v2(country_code: Optional[str]) -> bool:
    """Determina si el país requiere la API v2 de Connect para crear cuentas."""
    code = normalize_country_code(country_code, "US")
    return code not in SELF_SERVE_CROSS_BORDER_COUNTRIES


def _stripe_request_v2(
    endpoint: str,
    payload: Dict[str, Any],
    method: str = "POST",
) -> Dict[str, Any]:
    """
    Ejecuta una solicitud directa al API v2 de Stripe.
    
    v2 usa JSON nativo (no form-encoded) y requiere header Stripe-Version.
    """
    api_key = _configure_stripe()
    url = f"{STRIPE_API_V2_BASE}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Stripe-Version": STRIPE_V2_VERSION,
    }

    response = _requests.request(
        method=method.upper(),
        url=url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code >= 400:
        error_body = response.json() if response.content else {}
        error_msg = error_body.get("error", {}).get("message", response.text[:500])
        logger.error(
            "Stripe API v2 %s %s → %s: %s",
            method, endpoint, response.status_code, error_msg,
        )
        return {"success": False, "error": error_msg, "status_code": response.status_code}

    return {"success": True, "data": response.json()}


def _get_connect_capabilities_v2(country_code: str) -> Dict[str, Any]:
    """
    Retorna las capabilities solicitadas según el país (API v2 format).
    
    Para países cross-border no self-serve (DO, LATAM) solo se pueden
    solicitar `transfers` con service_agreement = "recipient".
    """
    code = normalize_country_code(country_code, "US")
    if code in SELF_SERVE_CROSS_BORDER_COUNTRIES:
        caps: Dict[str, Any] = {"transfers": {"requested": True}}
        if should_request_card_payments(code):
            caps["card_payments"] = {"requested": True}
        return caps
    # Recipient accounts: solo transfers
    return {"transfers": {"requested": True}}


async def create_connected_account_v2(
    partner_email: str,
    partner_company: str,
    partner_country: str = "DO",
) -> Dict[str, Any]:
    """
    Crea una cuenta Connect usando la API v2 de Stripe.
    
    Esto es necesario para países fuera de SELF_SERVE_CROSS_BORDER_COUNTRIES
    (e.g., República Dominicana, Colombia, etc.).
    
    La cuenta se crea con:
    - controller.stripe_dashboard.type = "express" (misma UX que Express v1)
    - tos_acceptance.service_agreement = "recipient" (para cross-border)
    - capabilities: solo "transfers" (card_payments no disponible para recipient)
    
    Returns:
        {"success": True, "account_id": "acct_XXX"} o {"success": False, "error": "..."}
    """
    normalized_country = normalize_country_code(partner_country, "DO")
    is_recipient = normalized_country not in SELF_SERVE_CROSS_BORDER_COUNTRIES

    payload: Dict[str, Any] = {
        "contact_email": partner_email,
        "country": normalized_country,
        "include": ["identity.country_specs"],
        "controller": {
            "stripe_dashboard": {"type": "express"},
            "fees": {"payer": "application"},
            "losses": {"payments": "application"},
        },
        "capabilities": _get_connect_capabilities_v2(normalized_country),
        "business_details": {
            "company": {
                "name": partner_company,
            },
        },
        "metadata": {
            "platform": "sajet",
            "partner_email": partner_email,
            "api_version": "v2",
            "settlement_mode": "cross_border_recipient" if is_recipient else "cross_border",
        },
    }

    if is_recipient:
        payload["tos_acceptance"] = {"service_agreement": "recipient"}

    logger.info(
        "🌐 Stripe API v2: creando cuenta Connect para %s (país=%s, recipient=%s)",
        partner_email, normalized_country, is_recipient,
    )

    result = _stripe_request_v2("core/accounts", payload)

    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Unknown v2 error")}

    account_data = result["data"]
    account_id = account_data.get("id", "")

    logger.info("✅ Stripe Connect v2 account creada: %s para %s", account_id, partner_email)

    return {
        "success": True,
        "account_id": account_id,
        "api_version": "v2",
        "service_agreement": "recipient" if is_recipient else "full",
        "country": normalized_country,
    }


async def create_connect_account_auto(
    partner_email: str,
    partner_company: str,
    partner_country: str = "US",
) -> Dict[str, Any]:
    """
    Auto-detecta y crea cuenta Connect usando v1 (Express) o v2 según el país.
    
    - Países self-serve (US, EEA, GB, CA, CH) → API v1 (Express nativo)
    - Países no self-serve (DO, LATAM, otros) → API v2 (recipient)
    
    Returns:
        {"success": True, "account_id": "acct_XXX", "api_version": "v1"|"v2"}
    """
    normalized_country = normalize_country_code(partner_country, "US")

    if requires_api_v2(normalized_country):
        logger.info("País %s requiere API v2 → usando create_connected_account_v2", normalized_country)
        return await create_connected_account_v2(
            partner_email=partner_email,
            partner_company=partner_company,
            partner_country=normalized_country,
        )
    else:
        logger.info("País %s soportado por v1 → usando create_connect_account (Express)", normalized_country)
        result = await create_connect_account(
            partner_email=partner_email,
            partner_company=partner_company,
            partner_country=normalized_country,
        )
        if result.get("success"):
            result["api_version"] = "v1"
        return result
