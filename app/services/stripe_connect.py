"""
Stripe Connect Express — Pagos automáticos a partners.
El dinero del partner nunca pasa por Jeturing; Stripe divide automáticamente.

Flujo:
1. Admin crea cuenta Express para partner → onboarding_url
2. Partner completa KYC en Stripe
3. Al cobrar suscripción, Stripe divide: X% a partner, resto a Jeturing
4. Partner ve sus pagos en Stripe Express dashboard
"""
import stripe
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
APP_URL = os.getenv("APP_URL", "https://sajet.us")


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
    try:
        account = stripe.Account.create(
            type="express",
            email=partner_email,
            country=partner_country,
            business_type="company",
            company={"name": partner_company},
            capabilities={
                "transfers": {"requested": True},
            },
            metadata={
                "platform": "sajet",
                "partner_email": partner_email,
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
    try:
        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=f"{APP_URL}{return_path}?stripe_refresh=true",
            return_url=f"{APP_URL}{return_path}?stripe_onboarded=true&account={account_id}",
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
    try:
        account = stripe.Account.retrieve(account_id)

        return {
            "success": True,
            "account_id": account.id,
            "email": account.email,
            "charges_enabled": account.charges_enabled,
            "payouts_enabled": account.payouts_enabled,
            "details_submitted": account.details_submitted,
            "country": account.country,
            "business_type": account.business_type,
            "created": account.created,
        }

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
    try:
        # application_fee_percent = lo que se queda Jeturing (inverso de la comisión del partner)
        jeturing_pct = 100.0 - partner_commission_pct

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
            success_url=success_url or f"{APP_URL}/onboarding/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url or f"{APP_URL}/onboarding?cancelled=true",
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
