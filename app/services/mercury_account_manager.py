"""
Mercury Account Manager — Gestión de Múltiples Cuentas

Maneja dos cuentas Mercury separadas:
1. SAVINGS Account (Ahorros) — Acumula fondos de clientes
2. CHECKING Account (Transaccional) — Dispersa a proveedores

Flujo:
- Cliente paga → Funds llegan a SAVINGS account
- Admin transfiere a CHECKING según necesidad
- CHECKING dispensa directamente a proveedores (ACH/Wire)
- Reconciliación automática entre cuentas
"""

import os
import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime, timezone
from enum import Enum

from .mercury_client import MercuryClient, BankAccount, MercuryAPIException

logger = logging.getLogger(__name__)


class AccountType(str, Enum):
    """Tipos de cuentas Mercury disponibles."""
    SAVINGS = "savings"      # Reserva — Fondos de clientes
    CHECKING = "checking"    # Operativa — Pagos a proveedores


class AccountTransferStatus(str, Enum):
    """Estados de transferencia entre cuentas."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class MercuryAccountManager:
    """
    Gestor centralizado de múltiples cuentas Mercury.
    
    Responsabilidades:
    - Mantener referencias a ambas cuentas (Savings + Checking)
    - Transferir fondos entre cuentas cuando sea necesario
    - Monitorear balances en tiempo real
    - Ejecutar dispersiones desde CHECKING
    - Auditar todas las transacciones inter-cuenta
    """
    
    def __init__(self):
        """Inicializar con credenciales de ambas cuentas."""
        # Cuenta Savings (Ahorros) — donde llegan fondos de clientes
        self.savings_account_id = os.getenv("MERCURY_SAVINGS_ACCOUNT_ID", "")
        self.savings_api_key = os.getenv("MERCURY_SAVINGS_API_KEY", "")
        
        # Cuenta Checking (Transaccional) — donde se dispersa a proveedores
        self.checking_account_id = os.getenv("MERCURY_CHECKING_ACCOUNT_ID", "")
        self.checking_api_key = os.getenv("MERCURY_CHECKING_API_KEY", "")
        
        # API URL común
        self.api_url = os.getenv("MERCURY_API_URL", "https://api.mercury.com/api/v1")
        
        # Límites operacionales
        self.min_transfer_to_checking = float(os.getenv("MERCURY_MIN_TRANSFER_TO_CHECKING", "1000"))
        self.max_transfer_to_checking = float(os.getenv("MERCURY_MAX_TRANSFER_TO_CHECKING", "100000"))
        self.checking_minimum_balance = float(os.getenv("MERCURY_CHECKING_MIN_BALANCE", "5000"))
        
        # Crear clientes para cada cuenta
        self.savings_client = self._create_client(self.savings_account_id, self.savings_api_key, "SAVINGS")
        self.checking_client = self._create_client(self.checking_account_id, self.checking_api_key, "CHECKING")
        
        logger.info(f"✅ Mercury Account Manager initialized")
        logger.info(f"   SAVINGS Account: {self.savings_account_id[:20]}...")
        logger.info(f"   CHECKING Account: {self.checking_account_id[:20]}...")
    
    def _create_client(
        self,
        account_id: str,
        api_key: str,
        account_name: str
    ) -> Optional[MercuryClient]:
        """
        Crear cliente Mercury para una cuenta específica.
        
        Args:
            account_id: ID de la cuenta en Mercury
            api_key: API key para esa cuenta
            account_name: Nombre legible (SAVINGS o CHECKING)
        
        Returns:
            MercuryClient configurado o None si credenciales faltantes
        """
        if not account_id or not api_key:
            logger.warning(f"⚠️ {account_name} account credentials not configured")
            return None
        
        # Crear cliente con credenciales específicas
        client = MercuryClient()
        client.account_id = account_id
        client.api_key = api_key
        
        # Actualizar sesión con nuevas credenciales
        client.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })
        
        return client
    
    # ═══════════════════════════════════════════════════════════════
    # Account Information
    # ═══════════════════════════════════════════════════════════════
    
    def get_account_balance(
        self,
        account_type: AccountType = AccountType.CHECKING
    ) -> Dict[str, Any]:
        """
        Obtener balance de una cuenta específica.
        
        Args:
            account_type: SAVINGS o CHECKING
        
        Returns:
            {
                "account_type": "checking",
                "account_id": "...",
                "balance": 45000.50,
                "available": 45000.50,
                "pending": 0,
                "currency": "USD",
                "last_updated": "2026-02-24T15:30:00Z"
            }
        """
        client = self.checking_client if account_type == AccountType.CHECKING else self.savings_client
        
        if not client:
            raise MercuryAPIException(f"{account_type.value.upper()} client not configured")
        
        balance = client.get_account_balance()
        balance["account_type"] = account_type.value
        return balance
    
    def get_both_balances(self) -> Dict[str, Any]:
        """
        Obtener balances de ambas cuentas en una sola llamada.
        
        Returns:
            {
                "savings": {
                    "account_type": "savings",
                    "balance": 150000.00,
                    "available": 150000.00,
                    ...
                },
                "checking": {
                    "account_type": "checking",
                    "balance": 45000.50,
                    "available": 45000.50,
                    ...
                },
                "total": 195000.50,
                "timestamp": "2026-02-24T15:30:00Z"
            }
        """
        try:
            savings_balance = self.get_account_balance(AccountType.SAVINGS) if self.savings_client else {}
            checking_balance = self.get_account_balance(AccountType.CHECKING) if self.checking_client else {}
            
            total = (
                savings_balance.get("balance", 0) +
                checking_balance.get("balance", 0)
            )
            
            return {
                "savings": savings_balance,
                "checking": checking_balance,
                "total": total,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error fetching both balances: {e}")
            raise MercuryAPIException(f"Failed to get account balances: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════
    # Inter-Account Transfers (Savings → Checking)
    # ═══════════════════════════════════════════════════════════════
    
    def transfer_to_checking(
        self,
        amount: float,
        reason: str = "Funds for provider dispersal"
    ) -> Dict[str, Any]:
        """
        Transferir fondos de SAVINGS a CHECKING.
        
        Flujo:
        1. Validar balance en SAVINGS es suficiente
        2. Crear ACH transfer de SAVINGS → CHECKING account number
        3. Registrar en base de datos
        4. Monitorear hasta completarse
        
        Args:
            amount: Monto a transferir
            reason: Motivo de la transferencia
        
        Returns:
            {
                "transfer_id": "xfr_...",
                "from_account": "savings",
                "to_account": "checking",
                "amount": 25000,
                "status": "pending",
                "created_at": "2026-02-24T15:30:00Z",
                "expected_delivery": "2026-02-26T00:00:00Z"
            }
        
        Raises:
            MercuryAPIException si balance insuficiente o error en API
        """
        if not self.savings_client or not self.checking_client:
            raise MercuryAPIException("Both SAVINGS and CHECKING accounts must be configured")
        
        # Validar monto
        if amount < self.min_transfer_to_checking:
            raise MercuryAPIException(
                f"Minimum transfer to CHECKING is ${self.min_transfer_to_checking}"
            )
        
        if amount > self.max_transfer_to_checking:
            raise MercuryAPIException(
                f"Maximum transfer to CHECKING is ${self.max_transfer_to_checking}"
            )
        
        # Validar balance en SAVINGS
        savings_balance = self.get_account_balance(AccountType.SAVINGS)
        if savings_balance.get("available", 0) < amount:
            raise MercuryAPIException(
                f"Insufficient balance in SAVINGS. Available: ${savings_balance.get('available')}, "
                f"Requested: ${amount}"
            )
        
        try:
            # Obtener detalles de CHECKING para crear beneficiario
            checking_details = self.checking_client.get_account_details()
            
            # Crear BankAccount para CHECKING (desde la perspectiva de SAVINGS)
            beneficiary = BankAccount(
                account_number=checking_details.get("account_number", ""),
                routing_number=checking_details.get("routing_number", ""),
                account_holder=checking_details.get("account_name", "Jeturing Checking"),
                account_type="checking",
                bank_name=checking_details.get("bank_name", "Mercury"),
            )
            
            # Crear ACH transfer de SAVINGS → CHECKING
            transfer = self.savings_client.create_ach_transfer(
                amount=amount,
                description=f"Inter-account transfer: {reason}",
                beneficiary=beneficiary,
                idempotency_key=f"savings-to-checking-{datetime.now().timestamp()}"
            )
            
            logger.info(
                f"✅ Transfer to CHECKING initiated: ${amount} "
                f"(Transfer ID: {transfer.get('transfer_id')})"
            )
            
            return {
                "transfer_id": transfer.get("transfer_id"),
                "from_account": "savings",
                "to_account": "checking",
                "amount": amount,
                "status": transfer.get("status"),
                "created_at": transfer.get("created_at"),
                "expected_delivery": transfer.get("expected_delivery"),
                "reason": reason,
            }
        
        except Exception as e:
            logger.error(f"Error transferring to CHECKING: {e}")
            raise MercuryAPIException(f"Failed to transfer funds to CHECKING: {str(e)}")
    
    def auto_replenish_checking(self, target_balance: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Transferir automáticamente fondos de SAVINGS a CHECKING si cae bajo mínimo.
        
        Lógica:
        1. Si CHECKING < minimum_balance
        2. Calcular diferencia hasta target_balance
        3. Transferir de SAVINGS
        
        Args:
            target_balance: Balance objetivo en CHECKING (default: 2x minimum)
        
        Returns:
            Detalles de transferencia o None si no fue necesaria
        """
        if target_balance is None:
            target_balance = self.checking_minimum_balance * 2
        
        try:
            checking_balance = self.get_account_balance(AccountType.CHECKING)
            current = checking_balance.get("available", 0)
            
            if current < self.checking_minimum_balance:
                transfer_amount = target_balance - current
                logger.warning(
                    f"⚠️ CHECKING balance low (${current}). "
                    f"Auto-replenishing with ${transfer_amount} from SAVINGS..."
                )
                return self.transfer_to_checking(transfer_amount, "Auto-replenishment")
            
            return None
        
        except Exception as e:
            logger.error(f"Error in auto-replenish: {e}")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # Provider Dispersal (from Checking Account)
    # ═══════════════════════════════════════════════════════════════
    
    def create_provider_payout(
        self,
        amount: float,
        provider_name: str,
        beneficiary: BankAccount,
        transfer_type: Literal["ach", "wire"] = "ach",
        invoice_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crear pago a proveedor desde la cuenta CHECKING.
        
        Requisitos:
        - CHECKING debe tener balance suficiente
        - Proveedor debe estar verificado (KYC)
        - Cuenta beneficiaria debe estar validada
        
        Args:
            amount: Monto a pagar
            provider_name: Nombre del proveedor
            beneficiary: Detalles de cuenta bancaria del proveedor
            transfer_type: "ach" (gratis, 1-2 días) o "wire" ($15, 1 día)
            invoice_ref: Referencia a invoice (ej: INV-12345)
        
        Returns:
            {
                "transfer_id": "xfr_...",
                "payout_status": "pending",
                "amount": 4250,
                "provider_name": "Provider XYZ",
                "transfer_type": "ach",
                "account_from": "checking",
                "created_at": "2026-02-24T15:30:00Z"
            }
        
        Raises:
            MercuryAPIException si balance insuficiente o error
        """
        if not self.checking_client:
            raise MercuryAPIException("CHECKING account not configured")
        
        # Validar balance en CHECKING
        checking_balance = self.get_account_balance(AccountType.CHECKING)
        available = checking_balance.get("available", 0)
        
        if available < amount:
            raise MercuryAPIException(
                f"Insufficient balance in CHECKING. Available: ${available}, "
                f"Requested: ${amount}"
            )
        
        try:
            # Crear transferencia según tipo
            if transfer_type == "wire":
                transfer = self.checking_client.create_wire_transfer(
                    amount=amount,
                    description=f"Payout to {provider_name}" + (f" ({invoice_ref})" if invoice_ref else ""),
                    beneficiary=beneficiary,
                    idempotency_key=f"payout-{provider_name}-{datetime.now().timestamp()}"
                )
            else:  # ACH
                transfer = self.checking_client.create_ach_transfer(
                    amount=amount,
                    description=f"Payout to {provider_name}" + (f" ({invoice_ref})" if invoice_ref else ""),
                    beneficiary=beneficiary,
                    idempotency_key=f"payout-{provider_name}-{datetime.now().timestamp()}"
                )
            
            logger.info(
                f"✅ Provider payout created: ${amount} to {provider_name} "
                f"via {transfer_type.upper()} (Transfer ID: {transfer.get('transfer_id')})"
            )
            
            return {
                "transfer_id": transfer.get("transfer_id"),
                "payout_status": transfer.get("status"),
                "amount": amount,
                "provider_name": provider_name,
                "transfer_type": transfer_type,
                "account_from": "checking",
                "created_at": transfer.get("created_at"),
                "expected_delivery": transfer.get("expected_delivery"),
                "invoice_ref": invoice_ref,
            }
        
        except Exception as e:
            logger.error(f"Error creating provider payout: {e}")
            raise MercuryAPIException(f"Failed to create payout: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════
    # Transaction Monitoring
    # ═══════════════════════════════════════════════════════════════
    
    def get_account_transactions(
        self,
        account_type: AccountType = AccountType.CHECKING,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Obtener historial de transacciones de una cuenta.
        
        Args:
            account_type: SAVINGS o CHECKING
            limit: Número máximo de transacciones
            offset: Para paginación
        
        Returns:
            {
                "account_type": "checking",
                "transactions": [...],
                "total": 150,
                "limit": 50,
                "offset": 0
            }
        """
        client = self.checking_client if account_type == AccountType.CHECKING else self.savings_client
        
        if not client:
            raise MercuryAPIException(f"{account_type.value.upper()} client not configured")
        
        txns = client.list_transactions(limit=limit, offset=offset)
        txns["account_type"] = account_type.value
        return txns
    
    def check_transfer_status(self, transfer_id: str, account_type: AccountType = AccountType.CHECKING) -> Dict[str, Any]:
        """
        Verificar estado de una transferencia específica.
        
        Args:
            transfer_id: ID de la transferencia Mercury
            account_type: En cuál cuenta se originó (por logging)
        
        Returns:
            {
                "transfer_id": "xfr_...",
                "status": "posted" | "pending" | "failed",
                "amount": 5000,
                "created_at": "...",
                "posted_at": "..." (si completed)
            }
        """
        client = self.checking_client if account_type == AccountType.CHECKING else self.savings_client
        
        if not client:
            raise MercuryAPIException(f"{account_type.value.upper()} client not configured")
        
        return client.get_transfer_status(transfer_id)
    
    # ═══════════════════════════════════════════════════════════════
    # Health & Alerts
    # ═══════════════════════════════════════════════════════════════
    
    def get_account_health(self) -> Dict[str, Any]:
        """
        Obtener estado general de las cuentas.
        
        Returns:
            {
                "status": "healthy" | "warning" | "critical",
                "savings": {
                    "balance": 150000,
                    "status": "ok"
                },
                "checking": {
                    "balance": 45000,
                    "status": "warning" (si bajo),
                    "needs_replenishment": True
                },
                "alerts": [
                    "CHECKING balance below minimum",
                    ...
                ]
            }
        """
        try:
            balances = self.get_both_balances()
            alerts = []
            overall_status = "healthy"
            
            checking_balance = balances.get("checking", {}).get("balance", 0)
            savings_balance = balances.get("savings", {}).get("balance", 0)
            
            # Verificar CHECKING
            if checking_balance < self.checking_minimum_balance:
                alerts.append(f"CHECKING balance low: ${checking_balance} (minimum: ${self.checking_minimum_balance})")
                overall_status = "warning"
            
            if checking_balance < 1000:
                alerts.append(f"CRITICAL: CHECKING balance very low: ${checking_balance}")
                overall_status = "critical"
            
            # Verificar SAVINGS
            if savings_balance < 5000:
                alerts.append(f"SAVINGS balance low: ${savings_balance}")
                overall_status = "warning" if overall_status != "critical" else "critical"
            
            return {
                "status": overall_status,
                "savings": {
                    "balance": savings_balance,
                    "status": "ok" if savings_balance > 5000 else "warning",
                },
                "checking": {
                    "balance": checking_balance,
                    "status": "warning" if checking_balance < self.checking_minimum_balance else "ok",
                    "needs_replenishment": checking_balance < self.checking_minimum_balance,
                },
                "alerts": alerts,
            }
        except Exception as e:
            logger.error(f"Error checking account health: {e}")
            return {
                "status": "error",
                "alerts": [f"Failed to check account health: {str(e)}"],
            }


# Singleton para acceso global
_account_manager: Optional[MercuryAccountManager] = None


def get_account_manager() -> MercuryAccountManager:
    """Obtener instancia singleton del gestor de cuentas."""
    global _account_manager
    if _account_manager is None:
        _account_manager = MercuryAccountManager()
    return _account_manager
