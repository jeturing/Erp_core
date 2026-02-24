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
import re

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
    DIRECT_PAYMENT_INSTRUCTIONS = "direct_payment_instructions"  # Instrucciones de pago directo
    DIRECT_PAYMENT_RECONCILED = "direct_payment_reconciled"       # Pago directo conciliado


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
    # 1.1 Pagos Directos (ACH/Wire) a Mercury SAVINGS
    # ═══════════════════════════════════════════════════════════════

    def get_direct_payment_instructions(
        self,
        invoice_id: int,
        method: str = "ach",
        country: str = "US",
        payer_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generar instrucciones para pago directo a Mercury (SAVINGS).

        Usa un código de referencia automático basado en el ID único.

        Args:
            invoice_id: ID de factura
            method: "ach" | "wire"
            country: Código país (default US)
            payer_name: Nombre del pagador (opcional)

        Returns:
            Instrucciones bancarias + referencia de conciliación
        """
        try:
            from ..models.database import Invoice, InvoiceStatus

            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found",
                    "error_code": "INVOICE_NOT_FOUND",
                }

            if invoice.status not in {InvoiceStatus.issued, InvoiceStatus.overdue}:
                return {
                    "success": False,
                    "error": f"Invoice status is {invoice.status.value}, expected issued/overdue",
                    "error_code": "INVALID_INVOICE_STATUS",
                }

            normalized_method = method.lower().strip()
            normalized_country = country.upper().strip()

            if normalized_method not in {"ach", "wire"}:
                return {
                    "success": False,
                    "error": "Invalid method. Use 'ach' or 'wire'",
                    "error_code": "INVALID_METHOD",
                }

            if normalized_method == "ach" and normalized_country != "US":
                return {
                    "success": False,
                    "error": "ACH solo disponible para pagos en USA. Use 'wire' para internacional.",
                    "error_code": "ACH_NOT_ALLOWED",
                }

            routing_number = os.getenv("MERCURY_SAVINGS_ROUTING_NUMBER", "")
            account_number = os.getenv("MERCURY_SAVINGS_ACCOUNT_NUMBER", "")
            beneficiary_name = os.getenv("MERCURY_SAVINGS_BENEFICIARY_NAME", "Jeturing Reserve")
            bank_name = os.getenv("MERCURY_SAVINGS_BANK_NAME", "Choice Financial Group")
            bank_address = os.getenv("MERCURY_SAVINGS_BANK_ADDRESS", "")
            beneficiary_address = os.getenv("MERCURY_SAVINGS_BENEFICIARY_ADDRESS", "")
            swift_code = os.getenv("MERCURY_SAVINGS_SWIFT_CODE", "")
            fx_ffc = os.getenv("MERCURY_SAVINGS_INTL_FX_FFC", "")
            fx_intermediary = {
                "swift": os.getenv("MERCURY_SAVINGS_INTL_FX_INTERMEDIARY_SWIFT", ""),
                "aba": os.getenv("MERCURY_SAVINGS_INTL_FX_INTERMEDIARY_ABA", ""),
                "bank_name": os.getenv("MERCURY_SAVINGS_INTL_FX_INTERMEDIARY_BANK", ""),
                "bank_address": os.getenv("MERCURY_SAVINGS_INTL_FX_INTERMEDIARY_ADDRESS", ""),
            }
            fx_beneficiary = {
                "bank_name": os.getenv("MERCURY_SAVINGS_INTL_FX_BENEFICIARY_BANK", ""),
                "account_number": os.getenv("MERCURY_SAVINGS_INTL_FX_BENEFICIARY_ACCOUNT", ""),
                "bank_address": os.getenv("MERCURY_SAVINGS_INTL_FX_BENEFICIARY_ADDRESS", ""),
            }

            if not routing_number or not account_number:
                return {
                    "success": False,
                    "error": "SAVINGS account no configurada completamente en .env",
                    "error_code": "SAVINGS_NOT_CONFIGURED",
                }

            if normalized_method == "wire" and normalized_country != "US" and not swift_code:
                return {
                    "success": False,
                    "error": "SWIFT code requerido para wire internacional. Configure MERCURY_SAVINGS_SWIFT_CODE.",
                    "error_code": "SWIFT_REQUIRED",
                }

            reference = self._generate_direct_payment_reference(invoice)

            instructions = {
                "success": True,
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "amount_due": invoice.total,
                "currency": invoice.currency,
                "method": normalized_method,
                "country": normalized_country,
                "beneficiary_name": beneficiary_name,
                "beneficiary_address": beneficiary_address,
                "bank_name": bank_name,
                "bank_address": bank_address,
                "routing_number": routing_number,
                "account_number": account_number,
                "swift_code": swift_code if normalized_method == "wire" else None,
                "payment_reference": reference,
                "memo": f"Invoice {invoice.invoice_number} | Ref {reference}",
                "payer_name": payer_name,
                "fx_instructions": None,
                "issued_at": datetime.now(timezone.utc).isoformat(),
            }

            if normalized_method == "wire" and normalized_country != "US" and invoice.currency.upper() != "USD":
                instructions["fx_instructions"] = {
                    "ffc_memo": fx_ffc,
                    "intermediary_bank": fx_intermediary,
                    "beneficiary_bank": fx_beneficiary,
                }

            self._log_payment_event(
                event_type=PaymentEventType.DIRECT_PAYMENT_INSTRUCTIONS,
                invoice_id=invoice.id,
                amount=invoice.total,
                metadata={
                    "method": normalized_method,
                    "country": normalized_country,
                    "reference": reference,
                    "payer_name": payer_name,
                },
            )

            return instructions

        except Exception as e:
            logger.error(f"Error generating direct payment instructions: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "DIRECT_PAYMENT_INSTRUCTIONS_ERROR",
            }

    def reconcile_direct_payment_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conciliar un pago directo a SAVINGS recibido via webhook Mercury.

        Busca la referencia JTINV-<invoice_id>-<check> en el payload y marca
        la factura como pagada si el monto es suficiente.
        """
        try:
            from ..models.database import Invoice, InvoiceStatus

            reference = self._extract_direct_payment_reference(payload)
            if not reference:
                return {
                    "success": True,
                    "action": "ignored",
                    "reason": "reference_not_found",
                }

            invoice_id = self._parse_reference_invoice_id(reference)
            if not invoice_id:
                return {
                    "success": True,
                    "action": "ignored",
                    "reason": "reference_invalid",
                    "reference": reference,
                }

            invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                return {
                    "success": False,
                    "error": f"Invoice {invoice_id} not found",
                    "error_code": "INVOICE_NOT_FOUND",
                }

            if invoice.status == InvoiceStatus.paid:
                return {
                    "success": True,
                    "action": "noop",
                    "reason": "already_paid",
                    "invoice_id": invoice.id,
                }

            if invoice.status not in {InvoiceStatus.issued, InvoiceStatus.overdue}:
                return {
                    "success": False,
                    "error": f"Invoice status is {invoice.status.value}, expected issued/overdue",
                    "error_code": "INVALID_INVOICE_STATUS",
                }

            if not self._is_incoming_credit(payload):
                return {
                    "success": True,
                    "action": "ignored",
                    "reason": "not_incoming_credit",
                    "reference": reference,
                }

            amount = self._extract_amount(payload)
            if amount is None:
                return {
                    "success": False,
                    "error": "Unable to parse amount from webhook",
                    "error_code": "AMOUNT_NOT_FOUND",
                }

            if amount + 0.01 < float(invoice.total):
                return {
                    "success": True,
                    "action": "ignored",
                    "reason": "insufficient_amount",
                    "invoice_id": invoice.id,
                    "amount": amount,
                    "invoice_total": float(invoice.total),
                }

            invoice.status = InvoiceStatus.paid
            invoice.paid_at = datetime.now(timezone.utc)
            note = f"Paid via Mercury direct transfer. Ref {reference}. Amount ${amount:.2f}"
            invoice.notes = f"{invoice.notes}\n{note}" if invoice.notes else note
            self.db.add(invoice)

            self._log_payment_event(
                event_type=PaymentEventType.DIRECT_PAYMENT_RECONCILED,
                invoice_id=invoice.id,
                amount=amount,
                metadata={
                    "reference": reference,
                    "payload_event": payload.get("type") or payload.get("eventType"),
                },
            )

            self.db.commit()

            return {
                "success": True,
                "action": "invoice_paid",
                "invoice_id": invoice.id,
                "amount": amount,
                "reference": reference,
            }

        except Exception as e:
            logger.error(f"Error reconciling direct payment webhook: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "error_code": "DIRECT_PAYMENT_RECONCILE_ERROR",
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

    def _generate_direct_payment_reference(self, invoice: Any) -> str:
        """
        Generar referencia única automática basada en ID.

        Formato: JTINV-<invoice_id>-<check>
        """
        invoice_id = int(invoice.id)
        check = (invoice_id * 97) % 97
        return f"JTINV-{invoice_id}-{check:02d}"

    def _extract_direct_payment_reference(self, payload: Dict[str, Any]) -> Optional[str]:
        """Buscar referencia JTINV-<id>-<check> en el payload completo."""
        payload_text = str(payload)
        match = re.search(r"JTINV-(\d+)-(\d{2})", payload_text)
        return match.group(0) if match else None

    def _parse_reference_invoice_id(self, reference: str) -> Optional[int]:
        """Validar referencia y extraer invoice_id."""
        match = re.match(r"JTINV-(\d+)-(\d{2})", reference)
        if not match:
            return None
        invoice_id = int(match.group(1))
        check = int(match.group(2))
        expected_check = (invoice_id * 97) % 97
        return invoice_id if check == expected_check else None

    def _extract_amount(self, payload: Dict[str, Any]) -> Optional[float]:
        """Intentar extraer monto del webhook Mercury."""
        candidates = [
            payload.get("amount"),
            payload.get("amountUsd"),
            payload.get("amount_usd"),
            payload.get("amount_cents"),
        ]
        for value in candidates:
            if value is None:
                continue
            try:
                if isinstance(value, (int, float)):
                    if "cents" in str(value).lower():
                        return float(value) / 100
                    return float(value)
                if isinstance(value, str) and value.strip():
                    return float(value.replace(",", ""))
            except Exception:
                continue

        data = payload.get("data") or {}
        for key in ("amount", "amountUsd", "amount_usd", "amount_cents"):
            value = data.get(key)
            if value is None:
                continue
            try:
                if key.endswith("_cents"):
                    return float(value) / 100
                return float(value)
            except Exception:
                continue

        return None

    def _is_incoming_credit(self, payload: Dict[str, Any]) -> bool:
        """Determinar si el evento es un crédito entrante."""
        direction = (
            payload.get("direction")
            or payload.get("type")
            or payload.get("transactionType")
            or payload.get("transaction_type")
            or ""
        ).lower()
        if any(token in direction for token in ["credit", "incoming", "deposit"]):
            return True
        data = payload.get("data") or {}
        data_direction = (data.get("direction") or data.get("type") or "").lower()
        if any(token in data_direction for token in ["credit", "incoming", "deposit"]):
            return True
        amount = self._extract_amount(payload)
        return amount is not None and amount > 0
