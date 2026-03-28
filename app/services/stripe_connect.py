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
