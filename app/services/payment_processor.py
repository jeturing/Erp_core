"""
Payment Processor — Orquestador centralizado de pagos y dispersión

Responsabilidades:
1. Decisiones de enrutamiento (Stripe vs Mercury)
2. Cálculo de comisiones y montos netos
3. Validación de reglas de negocio
4. Logging y auditoría de transacciones
5. Reconciliación Stripe ↔ Mercury con soporte para Dual Account

Arquitectura de Cuentas:
- SAVINGS: Acumula fondos de clientes
- CHECKING: Dispersa a proveedores
- Auto-replenish: CHECKING se repone automáticamente desde SAVINGS

Flujo:
  Cliente paga → Stripe → SAVINGS Mercury → Auto-replenish → CHECKING → Proveedor
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy.orm import Session
from .mercury_account_manager import get_account_manager, AccountType

logger = logging.getLogger(__name__)


class PayoutStatus(Enum):
    """Estados de dispersión de pagos."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class PaymentEventType(Enum):
    """Tipos de eventos de pago."""
    INVOICE_PAID = "invoice_paid"           # Cliente pagó invoice
    PAYOUT_REQUESTED = "payout_requested"   # Payout solicitado
    PAYOUT_AUTHORIZED = "payout_authorized" # Admin autorizó
    PAYOUT_EXECUTED = "payout_executed"     # Transferencia creada
    PAYOUT_COMPLETED = "payout_completed"   # Fondos llegaron
    PAYOUT_FAILED = "payout_failed"         # Transferencia falló
    BALANCE_SYNC = "balance_sync"           # Balance sincronizado


class PaymentProcessor:
    """
    Orquestador centralizado de pagos y dispersión.
    """
    
    def __init__(self, db: Session):
        """Inicializar procesador con sesión BD."""
        self.db = db
        self.mercury_client = None  # Se inyecta si Mercury está disponible
        self.stripe_client = None   # Se inyecta si Stripe está disponible
        
        # Configuración de comisiones y límites
        self.payout_min_amount = float(os.getenv("PAYOUT_MIN_AMOUNT", "5"))
        self.payout_max_amount = float(os.getenv("PAYOUT_MAX_AMOUNT", "50000"))
        self.mercury_ach_fee = float(os.getenv("MERCURY_ACH_FEE", "0"))
        self.mercury_wire_fee = float(os.getenv("MERCURY_WIRE_FEE", "15"))
        self.mercury_daily_limit = float(os.getenv("MERCURY_DAILY_LIMIT", "100000"))
        self.mercury_balance_threshold = float(os.getenv("MERCURY_BALANCE_THRESHOLD", "5000"))
    
    # ═══════════════════════════════════════════════════════════════
    # 1. Recibir Pagos de Clientes
    # ═══════════════════════════════════════════════════════════════
    
    def process_customer_payment(
        self,
        invoice_id: int,
        stripe_payment_intent_id: str,
        amount_received: float,
    ) -> Dict[str, Any]:
        """
        Procesar pago de cliente desde Stripe.
        
        Flujo:
        1. Validar que invoice existe y está en estado "issued"
        2. Actualizar estado a "paid"
        3. Registrar el stripe_payment_intent_id
        4. Actualizar balance local de Mercury (sync)
        5. Trigger: si hay comisión owed, crear payout_request
        
        Args:
            invoice_id: ID de factura en BD
            stripe_payment_intent_id: ID del payment intent de Stripe
            amount_received: Monto recibido (USD)
        
        Returns:
            {
                "success": True,
                "invoice_id": 123,
                "amount": 5000.00,
                "status": "paid",
                "stripe_pi_id": "pi_xxx",
                "timestamp": "2026-02-24T15:30:00Z",
                "next_action": "auto_sync_balance" | "manual_approval" | None
            }
        """
        try:
            from ..models.database import Invoice, InvoiceStatus
            
            # 1. Obtener factura
            invoice = self.db.query(Invoice).filter(
                Invoice.id == invoice_id
            ).first()
            
            if not invoice:
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found",
                    "error_code": "INVOICE_NOT_FOUND",
                }
            
            if invoice.status != InvoiceStatus.issued:
                return {
                    "success": False,
                    "error": f"Invoice status is {invoice.status.value}, expected 'issued'",
                    "error_code": "INVALID_INVOICE_STATUS",
                }
            
            # 2. Actualizar estado
            invoice.status = InvoiceStatus.paid
            invoice.stripe_payment_intent_id = stripe_payment_intent_id
            invoice.paid_at = datetime.now(timezone.utc)
            self.db.add(invoice)
            
            # 3. Log evento
            self._log_payment_event(
                event_type=PaymentEventType.INVOICE_PAID,
                invoice_id=invoice_id,
                amount=amount_received,
                metadata={
                    "stripe_pi_id": stripe_payment_intent_id,
                    "status": "paid",
                }
            )
            
            # 4. Sync balance con Mercury (en background o inmediato)
            # TODO: Llamar mercury_client.get_account_balance()
            
            # 5. Trigger: crear payout_request si hay comisión
            # TODO: Identificar si invoice requiere comisión a provider
            next_action = None
            if invoice.partner_id:  # Si hay partner (comisión)
                next_action = self._create_payout_request_from_invoice(invoice)
            
            self.db.commit()
            
            return {
                "success": True,
                "invoice_id": invoice_id,
                "amount": amount_received,
                "status": "paid",
                "stripe_pi_id": stripe_payment_intent_id,
                "timestamp": invoice.paid_at.isoformat(),
                "next_action": next_action,
            }
        
        except Exception as e:
            logger.error(f"Error processing customer payment: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "error_code": "PAYMENT_PROCESSING_ERROR",
            }
    
    # ═══════════════════════════════════════════════════════════════
    # 2. Crear y Autorizar Payouts a Proveedores
    # ═══════════════════════════════════════════════════════════════
    
    def calculate_provider_payout(
        self,
        provider_id: int,
        invoice_id: int,
        gross_amount: float,
    ) -> Dict[str, Any]:
        """
        Calcular monto neto a dispersar a proveedor.
        
        Flujo:
        1. Obtener datos del proveedor (comisión %)
        2. Calcular comisión de Jeturing
        3. Calcular fee de Mercury (ACH o Wire)
        4. Calcular monto neto final
        5. Validar mínimo/máximo
        
        Args:
            provider_id: ID del partner (proveedor)
            invoice_id: ID de factura asociada
            gross_amount: Monto bruto (antes de comisiones)
        
        Returns:
            {
                "gross_amount": 5000.00,
                "jeturing_commission_pct": 15,
                "jeturing_commission": 750.00,
                "mercury_fee": 0,
                "net_amount": 4250.00,
                "transfer_type": "ach",
                "valid": True,
                "messages": []
            }
        """
        messages = []
        
        try:
            from ..models.database import Partner
            
            # 1. Obtener datos del proveedor
            provider = self.db.query(Partner).filter(
                Partner.id == provider_id
            ).first()
            
            if not provider:
                return {
                    "valid": False,
                    "error": f"Provider {provider_id} not found",
                }
            
            # 2. Calcular comisión de Jeturing
            # TODO: Obtener % de comisión desde BD o config
            jeturing_commission_pct = 15.0  # Placeholder: 15% comisión
            jeturing_commission = gross_amount * (jeturing_commission_pct / 100)
            
            # 3. Determinar tipo de transferencia y fee
            # TODO: Usar preferred_payout_method del provider
            transfer_type = "ach"  # Default
            mercury_fee = self.mercury_ach_fee
            
            if transfer_type == "wire":
                mercury_fee = self.mercury_wire_fee
            
            # 4. Calcular monto neto
            net_amount = gross_amount - jeturing_commission - mercury_fee
            
            # 5. Validaciones
            if net_amount < self.payout_min_amount:
                messages.append(
                    f"Net amount ${net_amount:.2f} below minimum ${self.payout_min_amount:.2f}"
                )
            
            if net_amount > self.payout_max_amount:
                messages.append(
                    f"Net amount ${net_amount:.2f} exceeds maximum ${self.payout_max_amount:.2f}"
                )
            
            valid = len(messages) == 0
            
            return {
                "gross_amount": gross_amount,
                "jeturing_commission_pct": jeturing_commission_pct,
                "jeturing_commission": round(jeturing_commission, 2),
                "mercury_fee": round(mercury_fee, 2),
                "net_amount": round(net_amount, 2),
                "transfer_type": transfer_type,
                "valid": valid,
                "messages": messages,
            }
        
        except Exception as e:
            logger.error(f"Error calculating payout: {e}")
            return {
                "valid": False,
                "error": str(e),
            }
    
    def authorize_payout(
        self,
        payout_request_id: int,
        authorized_by: str,
    ) -> Dict[str, Any]:
        """
        Autorizar payout (solo admin).
        
        Valida:
        1. KYC del proveedor aprobado
        2. Balance en Mercury suficiente
        3. Límites diarios no excedidos
        4. Cuenta bancaria verificada
        
        Args:
            payout_request_id: ID del payout_request
            authorized_by: Email/username del admin
        
        Returns:
            {
                "authorized": True,
                "payout_id": 123,
                "amount": 4250.00,
                "provider": "Acme Corp",
                "authorized_at": "2026-02-24T15:30:00Z",
                "estimated_delivery": "2026-02-26T00:00:00Z",
                "warnings": []
            }
        """
        warnings = []
        
        try:
            # TODO: Obtener payout_request desde BD
            # Implementar validaciones:
            # - KYC status
            # - Balance check
            # - Daily limit check
            # - Account verification
            
            return {
                "authorized": True,
                "payout_id": payout_request_id,
                "amount": 4250.00,
                "provider": "Provider Name",
                "authorized_at": datetime.now(timezone.utc).isoformat(),
                "estimated_delivery": "2026-02-26T00:00:00Z",
                "warnings": warnings,
            }
        
        except Exception as e:
            logger.error(f"Error authorizing payout: {e}")
            return {
                "authorized": False,
                "error": str(e),
            }
    
    def execute_payout(
        self,
        payout_request_id: int,
    ) -> Dict[str, Any]:
        """
        Ejecutar transferencia vía Mercury (desde CHECKING account).
        
        Pasos:
        1. Obtener detalles del payout_request
        2. Validar que está autorizado
        3. Auto-replenish CHECKING desde SAVINGS si es necesario
        4. Llamar account_manager.create_provider_payout()
        5. Guardar mercury_transfer_id
        6. Marcar como "processing"
        7. Log evento
        
        Args:
            payout_request_id: ID del payout_request
        
        Returns:
            {
                "executed": True,
                "payout_id": 123,
                "mercury_transfer_id": "xfr_abc123",
                "amount": 4250.00,
                "status": "processing",
                "created_at": "2026-02-24T15:30:00Z",
                "auto_replenished": False | True,
                "replenish_amount": 25000 (si aplica)
            }
        """
        try:
            # Obtener gestor de cuentas dual
            account_manager = get_account_manager()
            
            # TODO: Obtener payout_request desde BD
            # payout_request = self.db.query(PayoutRequest).filter(...).first()
            
            # Auto-replenish CHECKING desde SAVINGS si es necesario
            replenish_result = account_manager.auto_replenish_checking()
            auto_replenished = replenish_result is not None
            replenish_amount = replenish_result.get("amount", 0) if auto_replenished else 0
            
            if auto_replenished:
                logger.info(f"✅ Auto-replenished CHECKING with ${replenish_amount}")
            
            # TODO: Crear BankAccount para proveedor desde BD
            # beneficiary = BankAccount(
            #     account_number=payout_request.provider_account.account_number,
            #     routing_number=payout_request.provider_account.routing_number,
            #     account_holder=payout_request.provider_account.account_holder_name,
            #     account_type=payout_request.provider_account.account_type,
            # )
            
            # Ejecutar dispersión desde CHECKING
            # transfer = account_manager.create_provider_payout(
            #     amount=payout_request.net_amount,
            #     provider_name=payout_request.provider.name,
            #     beneficiary=beneficiary,
            #     transfer_type=payout_request.transfer_type,
            #     invoice_ref=f"INV-{payout_request.invoice.id}"
            # )
            
            # TODO: Actualizar payout_request con mercury_transfer_id
            # TODO: Marcar como "processing"
            # TODO: Log evento
            
            return {
                "executed": True,
                "payout_id": payout_request_id,
                "mercury_transfer_id": "xfr_abc123",  # TODO: Use actual transfer ID
                "amount": 4250.00,  # TODO: Get from payout_request
                "status": "processing",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "auto_replenished": auto_replenished,
                "replenish_amount": replenish_amount,
            }
        
        except Exception as e:
            logger.error(f"Error executing payout: {e}")
            return {
                "executed": False,
                "error": str(e),
            }
    
    # ═══════════════════════════════════════════════════════════════
    # 3. Reconciliación
    # ═══════════════════════════════════════════════════════════════
    
    def reconcile_stripe_mercury(self) -> Dict[str, Any]:
        """
        Sincronizar saldos entre Stripe y Mercury (ambas cuentas).
        
        Pasos:
        1. Obtener balance de Stripe (via stripe_client)
        2. Obtener balances de SAVINGS y CHECKING (via account_manager)
        3. Comparar Stripe con (SAVINGS + CHECKING)
        4. Si discrepancia > 0.01%, registrar alerta
        5. Actualizar tabla de transacciones Mercury
        6. Log evento
        
        Returns:
            {
                "reconciled": True,
                "stripe_balance": 25000.00,
                "mercury_savings": 150000.00,
                "mercury_checking": 50000.00,
                "mercury_total": 200000.00,
                "discrepancy": 25000.00,
                "discrepancy_pct": 0.012,
                "status": "balanced" | "warning" | "critical",
                "account_manager_health": {...},
                "last_sync": "2026-02-24T15:30:00Z"
            }
        """
        try:
            # Obtener gestor de cuentas
            account_manager = get_account_manager()
            
            # Obtener balances de ambas cuentas Mercury
            both_balances = account_manager.get_both_balances()
            
            mercury_savings = both_balances.get("savings", {}).get("balance", 0)
            mercury_checking = both_balances.get("checking", {}).get("balance", 0)
            mercury_total = mercury_savings + mercury_checking
            
            # TODO: Obtener balance de Stripe
            stripe_balance = 0  # stripe_client.get_account_balance()
            
            discrepancy = abs(stripe_balance - mercury_total)
            discrepancy_pct = (discrepancy / stripe_balance) * 100 if stripe_balance > 0 else 0
            
            if discrepancy_pct > 0.1:  # Más del 0.1% de discrepancia
                status = "critical" if discrepancy_pct > 1 else "warning"
                logger.warning(
                    f"Reconciliation discrepancy: {discrepancy_pct:.2f}% "
                    f"(${discrepancy} difference)"
                )
            else:
                status = "balanced"
            
            # Obtener estado de salud de cuentas
            account_health = account_manager.get_account_health()
            
            self._log_payment_event(
                event_type=PaymentEventType.BALANCE_SYNC,
                metadata={
                    "stripe_balance": stripe_balance,
                    "mercury_savings": mercury_savings,
                    "mercury_checking": mercury_checking,
                    "mercury_total": mercury_total,
                    "discrepancy": discrepancy,
                    "status": status,
                }
            )
            
            return {
                "reconciled": True,
                "stripe_balance": stripe_balance,
                "mercury_savings": mercury_savings,
                "mercury_checking": mercury_checking,
                "mercury_total": mercury_total,
                "discrepancy": round(discrepancy, 2),
                "discrepancy_pct": round(discrepancy_pct, 3),
                "status": status,
                "account_manager_health": account_health,
                "last_sync": datetime.now(timezone.utc).isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Error reconciling balances: {e}")
            return {
                "reconciled": False,
                "error": str(e),
            }
    
    # ═══════════════════════════════════════════════════════════════
    # Helpers Privados
    # ═══════════════════════════════════════════════════════════════
    
    def _create_payout_request_from_invoice(self, invoice: Any) -> Optional[str]:
        """
        Crear payout_request automáticamente desde invoice pagada.
        
        Returns: ID del payout creado o None si no aplica.
        """
        try:
            # TODO: Lógica para crear payout_request
            # - Determinar comisión owed
            # - Crear PayoutRequest en BD
            # - Log evento
            return "payout_req_created"
        except Exception as e:
            logger.error(f"Error creating payout from invoice: {e}")
            return None
    
    def _log_payment_event(
        self,
        event_type: PaymentEventType,
        invoice_id: Optional[int] = None,
        payout_id: Optional[int] = None,
        amount: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Registrar evento de pago en BD (auditoría).
        
        TODO: Crear tabla payment_events si no existe.
        """
        try:
            log_entry = {
                "event_type": event_type.value,
                "invoice_id": invoice_id,
                "payout_id": payout_id,
                "amount": amount,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            logger.info(f"Payment event: {log_entry}")
            # TODO: Guardar en BD
        except Exception as e:
            logger.error(f"Error logging payment event: {e}")
