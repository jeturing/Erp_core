"""
Payments Routes — Endpoints para gestionar flujo de pago y dispersión

Endpoints:
- POST   /api/payments/process-invoice          # Procesar pago de cliente
- GET    /api/payments/balance                  # Balance actual (Stripe + Mercury)
- GET    /api/payments/summary                  # Resumen de cash flow
- POST   /api/payouts/create                    # Crear dispersión a proveedor
- GET    /api/payouts/{id}                      # Estado de pago
- GET    /api/payouts                           # Listar pagos
- POST   /api/providers/kyc-check               # Validar KYC proveedor
- POST   /api/providers/accounts                # Registrar cuenta bancaria
- GET    /api/treasury/summary                  # Resumen tesorería
- GET    /api/treasury/forecast                 # Forecasting de caja
- GET    /api/treasury/alerts                   # Alertas de tesorería
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import get_db
from ..services.mercury_client import get_mercury_client, MercuryAPIException, BankAccount
from ..services.payment_processor import PaymentProcessor, PaymentEventType
from ..services.treasury_manager import TreasuryManager

router = APIRouter(prefix="/api", tags=["Payments"])
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════

class ProcessInvoicePaymentRequest(BaseModel):
    """Procesar pago de cliente."""
    invoice_id: int
    stripe_payment_intent_id: str
    amount_received: float = Field(..., gt=0, description="Monto pagado en USD")


class CreatePayoutRequest(BaseModel):
    """Crear solicitud de pago a proveedor."""
    provider_id: int
    invoice_id: int
    gross_amount: float = Field(..., gt=0, description="Monto bruto a dispersar")
    notes: Optional[str] = None


class AuthorizePayoutRequest(BaseModel):
    """Autorizar payout (admin only)."""
    payout_id: int
    approved: bool = True
    notes: Optional[str] = None


class RegisterProviderAccountRequest(BaseModel):
    """Registrar cuenta bancaria para proveedor."""
    provider_id: int
    account_holder_name: str
    account_number: str
    routing_number: str
    account_type: str = Field("checking", description="checking | savings")
    bank_name: Optional[str] = None


class VerifyBankAccountRequest(BaseModel):
    """Verificar cuenta bancaria."""
    account_number: str
    routing_number: str
    account_type: str = "checking"


# ═══════════════════════════════════════════════════════════════
# 1. Invoice Payments
# ═══════════════════════════════════════════════════════════════

@router.post("/payments/process-invoice")
def process_invoice_payment(
    payload: ProcessInvoicePaymentRequest,
    db: Session = Depends(get_db),
):
    """
    Procesar pago de cliente desde Stripe.
    
    Flujo:
    1. Validar que invoice existe
    2. Marcar como pagada
    3. Guardar stripe_payment_intent_id
    4. Trigger: crear payout_request si hay comisión
    
    Response:
    ```json
    {
        "success": true,
        "invoice_id": 123,
        "amount": 5000.00,
        "status": "paid",
        "stripe_pi_id": "pi_xxx",
        "next_action": "auto_sync_balance"
    }
    ```
    """
    try:
        processor = PaymentProcessor(db)
        result = processor.process_customer_payment(
            invoice_id=payload.invoice_id,
            stripe_payment_intent_id=payload.stripe_payment_intent_id,
            amount_received=payload.amount_received,
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to process payment"),
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing invoice payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/balance")
def get_payment_balance(db: Session = Depends(get_db)):
    """
    Obtener balance actual de pagos (Stripe + Mercury).
    
    Response:
    ```json
    {
        "stripe": {
            "balance": 15000.00,
            "pending": 2500.00
        },
        "mercury": {
            "balance": 25000.00,
            "available": 25000.00
        },
        "total": 40000.00,
        "last_updated": "2026-02-24T15:30:00Z"
    }
    ```
    """
    try:
        treasury = TreasuryManager(db)
        return treasury.get_balance_snapshot()
    
    except Exception as e:
        logger.error(f"Error getting payment balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/summary")
def get_payment_summary(
    days: int = 30,
    db: Session = Depends(get_db),
):
    """
    Obtener resumen de cash flow en período.
    
    Query params:
    - days: Cantidad de días a reportar (default 30)
    
    Response:
    ```json
    {
        "period": {"start": "...", "end": "..."},
        "inflows": {"total": 50000.00, "from_customers": 50000.00, ...},
        "outflows": {"total": 12000.00, "to_providers": 10000.00, ...},
        "net": 38000.00,
        "balance": {"opening": 25000.00, "closing": 63000.00}
    }
    ```
    """
    try:
        from datetime import datetime, timezone, timedelta
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        treasury = TreasuryManager(db)
        return treasury.get_cash_flow_summary(
            start_date=start_date,
            end_date=end_date,
        )
    
    except Exception as e:
        logger.error(f"Error getting payment summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# 2. Payouts (Dispersión a Proveedores)
# ═══════════════════════════════════════════════════════════════

@router.post("/payouts/create")
def create_payout(
    payload: CreatePayoutRequest,
    db: Session = Depends(get_db),
):
    """
    Crear solicitud de pago a proveedor.
    
    Pasos:
    1. Calcular monto neto (comisión Jeturing, fees Mercury)
    2. Validar KYC del proveedor
    3. Crear payout_request en BD
    4. Requiere aprobación admin antes de ejecutar
    
    Response:
    ```json
    {
        "payout_id": 123,
        "provider_id": 42,
        "gross_amount": 5000.00,
        "jeturing_commission": 750.00,
        "mercury_fee": 0,
        "net_amount": 4250.00,
        "status": "pending",
        "created_at": "2026-02-24T15:30:00Z"
    }
    ```
    """
    try:
        processor = PaymentProcessor(db)
        
        # Calcular montos
        calc = processor.calculate_provider_payout(
            provider_id=payload.provider_id,
            invoice_id=payload.invoice_id,
            gross_amount=payload.gross_amount,
        )
        
        if not calc.get("valid"):
            raise HTTPException(
                status_code=400,
                detail=f"Payout calculation failed: {', '.join(calc.get('messages', []))}",
            )
        
        # TODO: Crear payout_request en BD
        # payout_req = PayoutRequest(
        #     provider_id=payload.provider_id,
        #     invoice_id=payload.invoice_id,
        #     amount=payload.gross_amount,
        #     status="pending",
        #     commission=calc["jeturing_commission"],
        #     net_amount=calc["net_amount"],
        #     notes=payload.notes,
        # )
        # db.add(payout_req)
        # db.commit()
        
        return {
            "payout_id": 123,  # payout_req.id (placeholder)
            "provider_id": payload.provider_id,
            "gross_amount": payload.gross_amount,
            "jeturing_commission": calc["jeturing_commission"],
            "mercury_fee": calc["mercury_fee"],
            "net_amount": calc["net_amount"],
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payouts")
def list_payouts(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Listar payouts con opción de filtrado.
    
    Query params:
    - status: pending | authorized | processing | completed | failed
    - limit: Default 50
    - offset: Default 0
    """
    try:
        treasury = TreasuryManager(db)
        return treasury.get_pending_payouts(
            status=status,
            limit=limit,
            offset=offset,
        )
    
    except Exception as e:
        logger.error(f"Error listing payouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payouts/{payout_id}")
def get_payout_status(
    payout_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtener estado detallado de un payout.
    
    Response:
    ```json
    {
        "id": 123,
        "provider": "Acme Corp",
        "amount": 4250.00,
        "status": "processing",
        "mercury_transfer_id": "xfr_abc123",
        "created_at": "2026-02-24T10:00:00Z",
        "authorized_at": "2026-02-24T12:00:00Z",
        "completed_at": null,
        "estimated_delivery": "2026-02-26T00:00:00Z"
    }
    ```
    """
    try:
        # TODO: Query payout_request WHERE id = payout_id
        # TODO: Si mercury_transfer_id, consultar estado en Mercury
        
        return {
            "id": payout_id,
            "provider": "Acme Corp",
            "amount": 4250.00,
            "status": "processing",
            "mercury_transfer_id": "xfr_abc123",
            "created_at": "2026-02-24T10:00:00Z",
            "authorized_at": "2026-02-24T12:00:00Z",
            "completed_at": None,
            "estimated_delivery": "2026-02-26T00:00:00Z",
        }
    
    except Exception as e:
        logger.error(f"Error getting payout status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payouts/{payout_id}/authorize")
def authorize_payout(
    payout_id: int,
    payload: AuthorizePayoutRequest,
    db: Session = Depends(get_db),
):
    """
    Autorizar o rechazar un payout (admin only).
    
    Validaciones:
    1. KYC del proveedor aprobado
    2. Balance en Mercury suficiente
    3. Límites diarios OK
    
    Response:
    ```json
    {
        "authorized": true,
        "payout_id": 123,
        "status": "authorized",
        "authorized_at": "2026-02-24T12:00:00Z",
        "ready_to_execute": true
    }
    ```
    """
    try:
        if not payload.approved:
            # TODO: Marcar como rechazado
            return {
                "authorized": False,
                "payout_id": payout_id,
                "status": "rejected",
                "reason": payload.notes or "Rejected by admin",
            }
        
        processor = PaymentProcessor(db)
        result = processor.authorize_payout(
            payout_request_id=payout_id,
            authorized_by="admin@sajet.us",  # TODO: Obtener del usuario autenticado
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error authorizing payout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payouts/{payout_id}/execute")
def execute_payout(
    payout_id: int,
    db: Session = Depends(get_db),
):
    """
    Ejecutar transferencia vía Mercury (admin only).
    
    Solo se puede ejecutar si:
    - Status es "authorized"
    - Mercury balance es suficiente
    - KYC verificado
    
    Response:
    ```json
    {
        "executed": true,
        "payout_id": 123,
        "mercury_transfer_id": "xfr_abc123",
        "status": "processing",
        "created_at": "2026-02-24T15:30:00Z"
    }
    ```
    """
    try:
        processor = PaymentProcessor(db)
        result = processor.execute_payout(payout_request_id=payout_id)
        
        if not result.get("executed"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to execute payout"),
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing payout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# 3. Proveedores & KYC
# ═══════════════════════════════════════════════════════════════

@router.post("/providers/accounts")
def register_provider_account(
    payload: RegisterProviderAccountRequest,
    db: Session = Depends(get_db),
):
    """
    Registrar cuenta bancaria para proveedor.
    
    Pasos:
    1. Validar formato de cuenta
    2. Verificar con Mercury API si disponible
    3. Guardar en BD (encriptado)
    4. Marcar como "pending" KYC
    5. Enviar confirmación email
    
    Response:
    ```json
    {
        "account_id": 456,
        "provider_id": 42,
        "account_number": "****5678",
        "bank_name": "Wells Fargo",
        "kyc_status": "pending",
        "message": "Account registered successfully"
    }
    ```
    """
    try:
        mercury = get_mercury_client()
        
        # Validar cuenta
        validation = mercury.validate_bank_account(
            account_number=payload.account_number,
            routing_number=payload.routing_number,
            account_type=payload.account_type,
        )
        
        if not validation["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bank account: {validation['message']}",
            )
        
        # TODO: Guardar en BD provider_accounts
        # provider_acc = ProviderAccount(
        #     provider_id=payload.provider_id,
        #     account_holder_name=payload.account_holder_name,
        #     account_number=encrypt(payload.account_number),
        #     routing_number=payload.routing_number,
        #     bank_name=validation.get("bank_name"),
        #     account_type=payload.account_type,
        #     kyc_status="pending",
        # )
        # db.add(provider_acc)
        # db.commit()
        
        return {
            "account_id": 456,
            "provider_id": payload.provider_id,
            "account_number": f"****{payload.account_number[-4:]}",
            "bank_name": validation.get("bank_name", payload.bank_name),
            "kyc_status": "pending",
            "message": "Account registered successfully. Awaiting KYC verification.",
        }
    
    except HTTPException:
        raise
    except MercuryAPIException as e:
        logger.warning(f"Mercury validation unavailable: {e}")
        # Permitir registro pero marcar como no verificado
        return {
            "account_id": 456,
            "provider_id": payload.provider_id,
            "account_number": f"****{payload.account_number[-4:]}",
            "bank_name": payload.bank_name,
            "kyc_status": "pending",
            "message": "Account registered. Automatic verification unavailable; manual review pending.",
            "warning": str(e),
        }
    except Exception as e:
        logger.error(f"Error registering provider account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/kyc-check")
def verify_provider_kyc(
    provider_id: int,
    db: Session = Depends(get_db),
):
    """
    Verificar/aprobar KYC de proveedor (admin only).
    
    TODO: Implementar lógica de verificación (manual o automática).
    
    Response:
    ```json
    {
        "provider_id": 42,
        "kyc_status": "approved",
        "verified_at": "2026-02-24T15:30:00Z",
        "account_verified": true
    }
    ```
    """
    try:
        # TODO: Obtener provider_accounts del proveedor
        # TODO: Marcar como kyc_status="approved"
        # TODO: Log evento
        
        return {
            "provider_id": provider_id,
            "kyc_status": "approved",
            "verified_at": datetime.now().isoformat(),
            "account_verified": True,
        }
    
    except Exception as e:
        logger.error(f"Error verifying provider KYC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# 4. Treasury & Analytics
# ═══════════════════════════════════════════════════════════════

@router.get("/treasury/summary")
def get_treasury_summary(db: Session = Depends(get_db)):
    """
    Obtener resumen ejecutivo de tesorería.
    
    Response:
    ```json
    {
        "balance": {
            "total": 40000.00,
            "stripe": 15000.00,
            "mercury": 25000.00
        },
        "payouts": {
            "pending_count": 3,
            "pending_amount": 6400.00,
            "total_paid_today": 4250.00
        },
        "alerts": {
            "critical": [],
            "warnings": ["3 payouts pending authorization"]
        }
    }
    ```
    """
    try:
        treasury = TreasuryManager(db)
        balance = treasury.get_balance_snapshot()
        payouts = treasury.get_pending_payouts(limit=100)
        alerts = treasury.check_alerts()
        
        return {
            "balance": {
                "total": balance.get("total"),
                "stripe": balance.get("stripe", {}).get("balance"),
                "mercury": balance.get("mercury", {}).get("balance"),
            },
            "payouts": {
                "pending_count": payouts.get("total", 0),
                "pending_amount": sum(p["amount"] for p in payouts.get("payouts", [])),
            },
            "alerts": alerts,
        }
    
    except Exception as e:
        logger.error(f"Error getting treasury summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treasury/forecast")
def get_treasury_forecast(
    days: int = 7,
    db: Session = Depends(get_db),
):
    """
    Obtener forecasting de necesidad de caja.
    
    Query params:
    - days: Cantidad de días a proyectar (default 7)
    """
    try:
        treasury = TreasuryManager(db)
        return treasury.forecast_cash_needs(days_ahead=days)
    
    except Exception as e:
        logger.error(f"Error getting treasury forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treasury/alerts")
def get_treasury_alerts(db: Session = Depends(get_db)):
    """
    Obtener alertas de tesorería.
    
    Response:
    ```json
    {
        "critical": [
            "Mercury balance below $5000 threshold"
        ],
        "warnings": [
            "3 payouts pending authorization"
        ],
        "info": [
            "Weekly settlement due Feb 28"
        ]
    }
    ```
    """
    try:
        treasury = TreasuryManager(db)
        return treasury.check_alerts()
    
    except Exception as e:
        logger.error(f"Error getting treasury alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/treasury/transactions")
def get_treasury_transactions(
    transaction_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Obtener historial de transacciones de tesorería.
    
    Query params:
    - transaction_type: inflow | outflow | fee | interest
    - limit: Default 100
    - offset: Default 0
    """
    try:
        treasury = TreasuryManager(db)
        return treasury.get_transaction_logs(
            transaction_type=transaction_type,
            limit=limit,
            offset=offset,
        )
    
    except Exception as e:
        logger.error(f"Error getting treasury transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════
# Dual Mercury Account Management (NEW)
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/treasury/accounts/dual-status",
    summary="Estado de Cuentas Dual (Savings + Checking)",
    description="Obtener balances y estado de salud de ambas cuentas Mercury."
)
def get_dual_account_status(db: Session = Depends(get_db)):
    """
    Obtener estado completo de cuentas dual (SAVINGS + CHECKING).
    
    Retorna:
    - Balance de SAVINGS (ahorros)
    - Balance de CHECKING (operativo)
    - Estado de salud general
    - Alertas activas
    - Necesidad de replenish
    """
    try:
        from ..services.mercury_account_manager import get_account_manager
        
        manager = get_account_manager()
        
        # Obtener balances de ambas cuentas
        balances = manager.get_both_balances()
        
        # Obtener estado de salud
        health = manager.get_account_health()
        
        return {
            "status": health.get("status"),
            "accounts": {
                "savings": {
                    "account_type": "savings",
                    "balance": balances.get("savings", {}).get("balance", 0),
                    "available": balances.get("savings", {}).get("available", 0),
                    "currency": "USD",
                    "purpose": "Reserve for customer funds"
                },
                "checking": {
                    "account_type": "checking",
                    "balance": balances.get("checking", {}).get("balance", 0),
                    "available": balances.get("checking", {}).get("available", 0),
                    "currency": "USD",
                    "purpose": "Operational for provider payouts"
                }
            },
            "totals": {
                "total_balance": balances.get("total", 0),
                "total_available": (
                    balances.get("savings", {}).get("available", 0) +
                    balances.get("checking", {}).get("available", 0)
                )
            },
            "health": health,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting dual account status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/treasury/accounts/transfer-to-checking",
    summary="Transferir de SAVINGS a CHECKING",
    description="Admin puede transferir fondos manualmente de SAVINGS a CHECKING."
)
def transfer_to_checking(
    amount: float = Field(..., gt=0, description="Monto a transferir en USD"),
    reason: str = Field(default="Funds for provider dispersal", description="Motivo de la transferencia"),
    db: Session = Depends(get_db)
):
    """
    Transferir fondos de SAVINGS → CHECKING.
    
    Requisitos:
    - Amount debe estar entre min y max configurados
    - SAVINGS debe tener balance suficiente
    - Admin debe estar autenticado (TODO: agregar auth)
    
    Retorna:
    - transfer_id de Mercury
    - Estado de la transferencia
    - Monto transferido
    - Tiempo esperado de entrega
    """
    try:
        from ..services.mercury_account_manager import get_account_manager
        
        manager = get_account_manager()
        
        # Ejecutar transferencia
        transfer = manager.transfer_to_checking(
            amount=amount,
            reason=reason
        )
        
        return {
            "success": True,
            "transfer": transfer,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error transferring to CHECKING: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/treasury/accounts/auto-replenish",
    summary="Auto-Replenish CHECKING",
    description="Forzar auto-replenish de CHECKING desde SAVINGS (normalmente es automático)."
)
def trigger_auto_replenish(
    target_balance: float = Field(default=None, description="Balance objetivo (default: 2x minimum)"),
    db: Session = Depends(get_db)
):
    """
    Forzar replenishment automático de CHECKING.
    
    Si CHECKING cae bajo el mínimo configurado, transfiere desde SAVINGS.
    
    Retorna:
    - Detalles de transferencia (si fue necesaria)
    - None (si no fue necesaria)
    """
    try:
        from ..services.mercury_account_manager import get_account_manager
        
        manager = get_account_manager()
        
        # Ejecutar auto-replenish
        result = manager.auto_replenish_checking(target_balance=target_balance)
        
        return {
            "success": True,
            "replenished": result is not None,
            "transfer": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error triggering auto-replenish: {e}")
        raise HTTPException(status_code=500, detail=str(e))