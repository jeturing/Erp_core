"""
Stripe → Mercury SAVINGS Integration

Gestiona la redirección de payouts de Stripe Connected Accounts
hacia la cuenta SAVINGS (Jeturing Reserve) en lugar de la anterior.

Flujo:
1. Stripe Connect recibe pagos de conectados (marketplace)
2. Payouts automáticos van a SAVINGS account (202559492947)
3. Auto-replenish transfiere SAVINGS → CHECKING cuando es necesario
4. CHECKING dispersa a proveedores
"""

import os
import logging
import stripe
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class StripePayoutStatus(str, Enum):
    """Estados de payout en Stripe."""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    PAID = "paid"
    FAILED = "failed"
    CANCELED = "canceled"


class StripeSavingsIntegration:
    """
    Integración Stripe → Mercury SAVINGS
    
    Responsabilidades:
    - Configurar payouts para ir a SAVINGS account
    - Monitorear payouts entrantes
    - Triggear auto-replenish cuando SAVINGS recibe fondos
    - Auditar todos los pagos
    """
    
    def __init__(self):
        """Inicializar integración Stripe-Mercury."""
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.payout_destination_account = os.getenv("STRIPE_PAYOUT_DESTINATION_ACCOUNT", "")
        self.payout_destination_routing = os.getenv("STRIPE_PAYOUT_DESTINATION_ROUTING", "")
        self.payout_currency = os.getenv("STRIPE_PAYOUT_CURRENCY", "usd")
        self.payout_schedule = os.getenv("STRIPE_PAYOUT_SCHEDULE", "manual")
        
        # Configurar cliente Stripe
        stripe.api_key = self.stripe_secret_key
        
        logger.info(f"✅ Stripe → SAVINGS Integration initialized")
        logger.info(f"   Payout Destination: {self.payout_destination_account} (SAVINGS)")
        logger.info(f"   Payout Currency: {self.payout_currency}")
        logger.info(f"   Payout Schedule: {self.payout_schedule}")
    
    def get_stripe_connected_accounts(self) -> List[Dict[str, Any]]:
        """
        Obtener todas las cuentas conectadas en Stripe.
        
        Returns:
            Lista de cuentas conectadas con detalles
        """
        try:
            accounts = stripe.Account.list(limit=100)
            
            connected = []
            for account in accounts.data:
                if account.id == "acct_test" or not account.charges_enabled:
                    continue
                
                connected.append({
                    "account_id": account.id,
                    "email": account.email,
                    "country": account.country,
                    "business_name": account.business_profile.get("name") if account.business_profile else None,
                    "charges_enabled": account.charges_enabled,
                    "payouts_enabled": account.payouts_enabled,
                })
            
            logger.info(f"Found {len(connected)} Stripe connected accounts")
            return connected
        
        except stripe.error.StripeError as e:
            logger.error(f"Error fetching Stripe connected accounts: {e}")
            raise
    
    def update_payout_destination(
        self,
        account_id: str,
        routing_number: str,
        account_number: str,
        account_holder: str = "Jeturing Inc."
    ) -> Dict[str, Any]:
        """
        Actualizar destino de payout para una cuenta conectada.
        
        Este es el paso CRÍTICO que redirecciona los payouts
        de Stripe a nuestra cuenta SAVINGS.
        
        Args:
            account_id: ID de la cuenta Stripe conectada
            routing_number: Routing number (091311229)
            account_number: Account number (202559492947 - SAVINGS)
            account_holder: Nombre del titular (Jeturing Inc.)
        
        Returns:
            Resultado de actualización con detalles de la nueva cuenta bancaria
        """
        try:
            # Crear banco para payout
            bank_account = stripe.Account.create_external_account(
                account_id,
                external_account={
                    "object": "bank_account",
                    "country": "US",
                    "currency": self.payout_currency,
                    "account_holder_name": account_holder,
                    "account_holder_type": "company",
                    "routing_number": routing_number,
                    "account_number": account_number,
                }
            )
            
            logger.info(f"✅ Bank account added to {account_id}")
            logger.info(f"   Routing: {routing_number}")
            logger.info(f"   Account: {account_number} (SAVINGS)")
            
            # Establecer como destino de payout por defecto
            stripe.Account.modify(
                account_id,
                external_account=bank_account.id  # Usar este banco para payouts
            )
            
            logger.info(f"✅ Payout destination updated: {account_id} → {account_number}")
            
            return {
                "account_id": account_id,
                "bank_account_id": bank_account.id,
                "routing_number": routing_number,
                "account_number": account_number,
                "status": "configured",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Error updating payout destination: {e}")
            raise
    
    def get_pending_payouts(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Obtener payouts pendientes de una cuenta conectada.
        
        Args:
            account_id: ID de cuenta Stripe conectada
        
        Returns:
            Lista de payouts pendientes
        """
        try:
            payouts = stripe.Payout.list(
                stripe_account=account_id,
                status="pending",
                limit=50
            )
            
            pending = []
            for payout in payouts.data:
                pending.append({
                    "payout_id": payout.id,
                    "amount": payout.amount / 100,  # Convertir centavos a dólares
                    "currency": payout.currency.upper(),
                    "status": payout.status,
                    "arrival_date": datetime.fromtimestamp(payout.arrival_date).isoformat() if payout.arrival_date else None,
                    "automatic": payout.automatic,
                })
            
            logger.info(f"Found {len(pending)} pending payouts for {account_id}")
            return pending
        
        except stripe.error.StripeError as e:
            logger.error(f"Error fetching payouts: {e}")
            raise
    
    def get_payout_details(self, account_id: str, payout_id: str) -> Dict[str, Any]:
        """
        Obtener detalles completos de un payout específico.
        
        Args:
            account_id: ID de cuenta Stripe
            payout_id: ID del payout
        
        Returns:
            Detalles completos del payout
        """
        try:
            payout = stripe.Payout.retrieve(
                payout_id,
                stripe_account=account_id
            )
            
            return {
                "payout_id": payout.id,
                "amount": payout.amount / 100,
                "currency": payout.currency.upper(),
                "status": payout.status,
                "arrival_date": datetime.fromtimestamp(payout.arrival_date).isoformat() if payout.arrival_date else None,
                "automatic": payout.automatic,
                "method": payout.method,
                "type": payout.type,
                "failure_code": payout.failure_code,
                "failure_message": payout.failure_message,
                "statement_descriptor": payout.statement_descriptor,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Error fetching payout details: {e}")
            raise
    
    def trigger_auto_replenish_on_payout(
        self,
        payout_amount: float,
        account_manager=None
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger auto-replenish cuando Stripe deposita en SAVINGS.
        
        Si CHECKING está bajo, transfiere desde SAVINGS después
        de que el payout se acredita.
        
        Args:
            payout_amount: Monto del payout recibido
            account_manager: Instancia de MercuryAccountManager
        
        Returns:
            Resultado del auto-replenish o None si no fue necesario
        """
        if not account_manager:
            logger.warning("account_manager not provided, skipping auto-replenish")
            return None
        
        try:
            # Obtener balances actuales
            balances = account_manager.get_both_balances()
            checking_balance = balances.get("checking", {}).get("balance", 0)
            
            logger.info(f"Payout received: ${payout_amount}")
            logger.info(f"Current CHECKING balance: ${checking_balance}")
            
            # Si CHECKING está bajo, triggear auto-replenish
            if checking_balance < account_manager.checking_minimum_balance:
                logger.info(f"Triggering auto-replenish (balance < ${account_manager.checking_minimum_balance})")
                
                replenish_result = account_manager.auto_replenish_checking()
                
                if replenish_result:
                    logger.info(f"✅ Auto-replenish triggered: {replenish_result}")
                    return replenish_result
            
            return None
        
        except Exception as e:
            logger.error(f"Error triggering auto-replenish: {e}")
            return None


def initialize_stripe_savings_integration() -> StripeSavingsIntegration:
    """Inicializar la integración Stripe → SAVINGS globalmente."""
    return StripeSavingsIntegration()
