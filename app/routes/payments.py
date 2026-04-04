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
from fastapi import APIRouter, Cookie, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from datetime import datetime, timezone

from ..models.database import (
    get_db, PayoutRequest as PayoutRequestModel, ProviderAccount,
    PaymentEvent, PayoutStatus as PayoutStatusEnum, KYCStatus,
    Partner, Invoice, InvoiceStatus,
)
from ..services.mercury_client import get_mercury_client, MercuryAPIException, BankAccount
from ..services.payment_processor import PaymentProcessor, PaymentEventType
from ..services.treasury_manager import TreasuryManager
from ..routes.roles import _require_admin

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


class DirectPaymentInstructionsRequest(BaseModel):
    """Instrucciones para pago directo (ACH/Wire) a Mercury SAVINGS."""
    invoice_id: int
    method: str = Field("ach", description="ach | wire")
    country: str = Field("US", description="ISO country code, default US")
    payer_name: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# 1. Invoice Payments
# ═══════════════════════════════════════════════════════════════

@router.post("/payments/process-invoice")
def process_invoice_payment(
    payload: ProcessInvoicePaymentRequest,
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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


@router.post("/payments/direct/instructions")
def get_direct_payment_instructions(
    payload: DirectPaymentInstructionsRequest,
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    """
    Generar instrucciones de pago directo a Mercury (ACH/Wire).

    Response:
    ```json
    {
        "success": true,
        "invoice_id": 123,
        "amount_due": 5000.00,
        "currency": "USD",
        "method": "ach",
        "routing_number": "091311229",
        "account_number": "202559492947",
        "payment_reference": "JTINV-123-12",
        "memo": "Invoice INV-2026-0001 | Ref JTINV-123-12"
    }
    ```
    """
    try:
        processor = PaymentProcessor(db)
        result = processor.get_direct_payment_instructions(
            invoice_id=payload.invoice_id,
            method=payload.method,
            country=payload.country,
            payer_name=payload.payer_name,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to generate instructions"),
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating direct payment instructions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/balance")
def get_payment_balance(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
    request: Request = None,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    """
    Crear solicitud de pago a proveedor.
    Requiere aprobación admin antes de ejecutar.
    """
    admin = _require_admin(request, access_token)
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
        
        # Persistir payout_request en BD
        payout_req = PayoutRequestModel(
            partner_id=payload.provider_id,
            invoice_id=payload.invoice_id,
            gross_amount=payload.gross_amount,
            jeturing_commission_pct=calc["jeturing_commission_pct"],
            jeturing_commission=calc["jeturing_commission"],
            mercury_fee=calc["mercury_fee"],
            net_amount=calc["net_amount"],
            transfer_type=calc.get("transfer_type", "ach"),
            status=PayoutStatusEnum.pending,
            notes=payload.notes,
        )
        db.add(payout_req)
        db.flush()

        # Log evento
        db.add(PaymentEvent(
            event_type=PaymentEventType.PAYOUT_REQUESTED.value,
            invoice_id=payload.invoice_id,
            payout_id=payout_req.id,
            amount=payout_req.net_amount,
            actor=admin.get("sub", "admin"),
            metadata_json={
                "gross": payload.gross_amount,
                "commission": calc["jeturing_commission"],
            },
        ))
        db.commit()
        
        return {
            "payout_id": payout_req.id,
            "provider_id": payload.provider_id,
            "gross_amount": payload.gross_amount,
            "jeturing_commission": calc["jeturing_commission"],
            "mercury_fee": calc["mercury_fee"],
            "net_amount": calc["net_amount"],
            "status": "pending",
            "created_at": payout_req.created_at.isoformat() if payout_req.created_at else datetime.now(timezone.utc).isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating payout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payouts")
def list_payouts(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    request: Request = None,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    """
    Listar payouts con opción de filtrado.
    """
    _require_admin(request, access_token)
    try:
        query = db.query(PayoutRequestModel).join(
            Partner, PayoutRequestModel.partner_id == Partner.id
        )
        if status:
            try:
                status_enum = PayoutStatusEnum(status)
                query = query.filter(PayoutRequestModel.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        total = query.count()
        payouts = query.order_by(PayoutRequestModel.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "payouts": [
                {
                    "id": p.id,
                    "provider": p.partner.company_name if p.partner else "—",
                    "amount": p.net_amount,
                    "gross_amount": p.gross_amount,
                    "commission": p.jeturing_commission,
                    "status": p.status.value if p.status else "pending",
                    "transfer_type": p.transfer_type or "ach",
                    "mercury_transfer_id": p.mercury_transfer_id,
                    "requested_at": p.created_at.isoformat() if p.created_at else None,
                    "authorized_at": p.authorized_at.isoformat() if p.authorized_at else None,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                    "estimated_delivery": p.estimated_delivery.isoformat() if p.estimated_delivery else None,
                }
                for p in payouts
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing payouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payouts/{payout_id}")
def get_payout_status(
    payout_id: int,
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    """Obtener estado detallado de un payout."""
    _require_admin(request, access_token)
    try:
        payout = db.query(PayoutRequestModel).filter(PayoutRequestModel.id == payout_id).first()
        if not payout:
            raise HTTPException(status_code=404, detail=f"Payout {payout_id} not found")

        partner = db.query(Partner).filter(Partner.id == payout.partner_id).first()

        # Si hay mercury_transfer_id, intentar consultar estado live
        mercury_status = None
        if payout.mercury_transfer_id:
            try:
                mercury = get_mercury_client()
                mercury_status = mercury.get_transfer_status(payout.mercury_transfer_id)
            except Exception:
                pass  # Graceful fallback

        return {
            "id": payout.id,
            "provider": partner.company_name if partner else "—",
            "partner_id": payout.partner_id,
            "gross_amount": payout.gross_amount,
            "amount": payout.net_amount,
            "commission": payout.jeturing_commission,
            "status": payout.status.value if payout.status else "pending",
            "transfer_type": payout.transfer_type,
            "mercury_transfer_id": payout.mercury_transfer_id,
            "mercury_live_status": mercury_status,
            "created_at": payout.created_at.isoformat() if payout.created_at else None,
            "authorized_at": payout.authorized_at.isoformat() if payout.authorized_at else None,
            "executed_at": payout.executed_at.isoformat() if payout.executed_at else None,
            "completed_at": payout.completed_at.isoformat() if payout.completed_at else None,
            "estimated_delivery": payout.estimated_delivery.isoformat() if payout.estimated_delivery else None,
            "notes": payout.notes,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payout status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payouts/{payout_id}/authorize")
def authorize_payout(
    payout_id: int,
    payload: AuthorizePayoutRequest,
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    """Autorizar o rechazar un payout (admin only)."""
    admin = _require_admin(request, access_token)
    admin_email = admin.get("sub", "admin")
    try:
        payout = db.query(PayoutRequestModel).filter(PayoutRequestModel.id == payout_id).first()
        if not payout:
            raise HTTPException(status_code=404, detail=f"Payout {payout_id} not found")

        if payout.status != PayoutStatusEnum.pending:
            raise HTTPException(status_code=400, detail=f"Payout status is {payout.status.value}, expected pending")

        now = datetime.now(timezone.utc)

        if not payload.approved:
            payout.status = PayoutStatusEnum.rejected
            payout.notes = payload.notes or "Rejected by admin"
            payout.authorized_by = admin_email
            payout.authorized_at = now
            db.add(PaymentEvent(
                event_type="payout_rejected",
                payout_id=payout.id,
                amount=payout.net_amount,
                actor=admin_email,
                metadata_json={"reason": payout.notes},
            ))
            db.commit()
            return {
                "authorized": False,
                "payout_id": payout_id,
                "status": "rejected",
                "reason": payout.notes,
            }

        payout.status = PayoutStatusEnum.authorized
        payout.authorized_by = admin_email
        payout.authorized_at = now
        db.add(PaymentEvent(
            event_type=PaymentEventType.PAYOUT_AUTHORIZED.value,
            payout_id=payout.id,
            amount=payout.net_amount,
            actor=admin_email,
        ))
        db.commit()

        return {
            "authorized": True,
            "payout_id": payout_id,
            "amount": payout.net_amount,
            "provider_id": payout.partner_id,
            "status": "authorized",
            "authorized_at": now.isoformat(),
            "authorized_by": admin_email,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error authorizing payout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payouts/{payout_id}/execute")
def execute_payout(
    payout_id: int,
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
        
        # Persistir en BD
        provider_acc = ProviderAccount(
            partner_id=payload.provider_id,
            account_holder_name=payload.account_holder_name,
            account_number_masked=f"****{payload.account_number[-4:]}",
            routing_number=payload.routing_number,
            account_type=payload.account_type,
            bank_name=validation.get("bank_name", payload.bank_name),
            kyc_status=KYCStatus.pending,
        )
        db.add(provider_acc)
        db.commit()
        
        return {
            "account_id": provider_acc.id,
            "provider_id": payload.provider_id,
            "account_number": provider_acc.account_number_masked,
            "bank_name": provider_acc.bank_name,
            "kyc_status": "pending",
            "message": "Account registered successfully. Awaiting KYC verification.",
        }
    
    except HTTPException:
        raise
    except MercuryAPIException as e:
        logger.warning(f"Mercury validation unavailable: {e}")
        # Persistir de todas formas, marcar como no verificado
        provider_acc = ProviderAccount(
            partner_id=payload.provider_id,
            account_holder_name=payload.account_holder_name,
            account_number_masked=f"****{payload.account_number[-4:]}",
            routing_number=payload.routing_number,
            account_type=payload.account_type,
            bank_name=payload.bank_name,
            kyc_status=KYCStatus.pending,
        )
        db.add(provider_acc)
        db.commit()
        return {
            "account_id": provider_acc.id,
            "provider_id": payload.provider_id,
            "account_number": provider_acc.account_number_masked,
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
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    """Verificar/aprobar KYC de proveedor (admin only)."""
    admin = _require_admin(request, access_token)
    try:
        accounts = db.query(ProviderAccount).filter(
            ProviderAccount.partner_id == provider_id,
            ProviderAccount.is_active == True,
        ).all()

        if not accounts:
            raise HTTPException(
                status_code=404,
                detail=f"No active bank accounts found for provider {provider_id}",
            )

        now = datetime.now(timezone.utc)
        verified_count = 0
        for acc in accounts:
            if acc.kyc_status != KYCStatus.approved:
                acc.kyc_status = KYCStatus.approved
                acc.kyc_verified_at = now
                acc.kyc_notes = f"Approved by {admin.get('sub', 'admin')}"
                verified_count += 1

        db.add(PaymentEvent(
            event_type="provider_kyc_approved",
            amount=None,
            actor=admin.get("sub", "admin"),
            metadata_json={"provider_id": provider_id, "accounts_verified": verified_count},
        ))
        db.commit()

        return {
            "provider_id": provider_id,
            "kyc_status": "approved",
            "verified_at": now.isoformat(),
            "accounts_verified": verified_count,
            "account_verified": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error verifying provider KYC: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# 4. Treasury & Analytics
# ═══════════════════════════════════════════════════════════════

@router.get("/treasury/summary")
def get_treasury_summary(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
    request: Request = None,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
def get_treasury_alerts(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
    request: Request = None,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
def get_dual_account_status(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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


class TransferToCheckingRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Monto a transferir en USD")
    reason: str = Field(default="Funds for provider dispersal", description="Motivo de la transferencia")


@router.post(
    "/treasury/accounts/transfer-to-checking",
    summary="Transferir de SAVINGS a CHECKING",
    description="Admin puede transferir fondos manualmente de SAVINGS a CHECKING."
)
def transfer_to_checking(
    body: TransferToCheckingRequest,
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
            amount=body.amount,
            reason=body.reason
        )
        
        return {
            "success": True,
            "transfer": transfer,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error transferring to CHECKING: {e}")
        raise HTTPException(status_code=400, detail=str(e))


class AutoReplenishRequest(BaseModel):
    target_balance: Optional[float] = Field(default=None, description="Balance objetivo (default: 2x minimum)")


@router.post(
    "/treasury/accounts/auto-replenish",
    summary="Auto-Replenish CHECKING",
    description="Forzar auto-replenish de CHECKING desde SAVINGS (normalmente es automático)."
)
def trigger_auto_replenish(
    body: AutoReplenishRequest = AutoReplenishRequest(),
    request: Request = None,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
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
        result = manager.auto_replenish_checking(target_balance=body.target_balance)
        
        return {
            "success": True,
            "replenished": result is not None,
            "transfer": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error triggering auto-replenish: {e}")
        raise HTTPException(status_code=500, detail=str(e))