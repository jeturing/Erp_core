"""
Treasury Manager — Gestor de tesorería y análisis de flujo de caja

Responsabilidades:
1. Dashboard de balance actual
2. Reportes de ingresos/egresos
3. Forecasting de pagos pendientes
4. Alertas de saldo bajo
5. Histórico de transacciones
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.database import (
    PayoutRequest, PayoutStatus, Invoice, InvoiceStatus,
    PaymentEvent, Partner,
)

logger = logging.getLogger(__name__)


class CashFlowType(Enum):
    """Tipo de movimiento de caja."""
    INFLOW = "inflow"      # Dinero entrante
    OUTFLOW = "outflow"    # Dinero saliente
    FEE = "fee"            # Comisión o gasto
    INTEREST = "interest"  # Interés


class TreasuryManager:
    """Gestor centralizado de tesorería."""
    
    def __init__(self, db: Session):
        """Inicializar con sesión BD."""
        self.db = db
    
    # ═══════════════════════════════════════════════════════════════
    # 1. Dashboard & Balance
    # ═══════════════════════════════════════════════════════════════
    
    def get_cash_flow_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Obtener resumen de flujo de caja en período.
        
        Returns:
            {
                "period": {
                    "start": "2026-02-01T00:00:00Z",
                    "end": "2026-02-24T23:59:59Z"
                },
                "inflows": {
                    "total": 50000.00,
                    "from_customers": 50000.00,
                    "from_interest": 0,
                    "transactions_count": 12
                },
                "outflows": {
                    "total": 12000.00,
                    "to_providers": 10000.00,
                    "bank_fees": 500.00,
                    "other": 1500.00,
                    "transactions_count": 8
                },
                "net": 38000.00,
                "balance": {
                    "opening": 25000.00,
                    "closing": 63000.00
                }
            }
        """
        try:
            if not start_date:
                start_date = datetime.now(timezone.utc).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # TODO: Query BD para:
            # - Sumar invoices pagadas en período
            # - Sumar payouts completados en período
            # - Sumar fees Mercury en período
            # - Calcular saldo de apertura/cierre

            # Inflows: invoices pagadas en período
            inflow_result = self.db.query(
                func.coalesce(func.sum(Invoice.total), 0),
                func.count(Invoice.id),
            ).filter(
                Invoice.status == InvoiceStatus.paid,
                Invoice.paid_at >= start_date,
                Invoice.paid_at <= end_date,
            ).first()
            inflow_total = float(inflow_result[0]) if inflow_result else 0
            inflow_count = inflow_result[1] if inflow_result else 0

            # Outflows: payouts completados en período
            outflow_result = self.db.query(
                func.coalesce(func.sum(PayoutRequest.net_amount), 0),
                func.coalesce(func.sum(PayoutRequest.mercury_fee), 0),
                func.count(PayoutRequest.id),
            ).filter(
                PayoutRequest.status == PayoutStatus.completed,
                PayoutRequest.completed_at >= start_date,
                PayoutRequest.completed_at <= end_date,
            ).first()
            outflow_providers = float(outflow_result[0]) if outflow_result else 0
            outflow_fees = float(outflow_result[1]) if outflow_result else 0
            outflow_count = outflow_result[2] if outflow_result else 0
            outflow_total = outflow_providers + outflow_fees

            net = inflow_total - outflow_total
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "inflows": {
                    "total": round(inflow_total, 2),
                    "from_customers": round(inflow_total, 2),
                    "from_interest": 0,
                    "transactions_count": inflow_count,
                },
                "outflows": {
                    "total": round(outflow_total, 2),
                    "to_providers": round(outflow_providers, 2),
                    "bank_fees": round(outflow_fees, 2),
                    "other": 0,
                    "transactions_count": outflow_count,
                },
                "net": round(net, 2),
                "balance": {
                    "opening": 0,
                    "closing": round(net, 2),
                },
            }
        
        except Exception as e:
            logger.error(f"Error getting cash flow summary: {e}")
            return {
                "error": str(e),
                "period": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None,
                }
            }
    
    def get_balance_snapshot(self) -> Dict[str, Any]:
        """
        Obtener snapshot actual de balances (Stripe + Mercury).
        
        Returns:
            {
                "timestamp": "2026-02-24T15:30:00Z",
                "stripe": {
                    "balance": 15000.00,
                    "pending": 2500.00,
                    "connected_accounts": 3
                },
                "mercury": {
                    "balance": 25000.00,
                    "available": 25000.00,
                    "pending": 0,
                    "account_name": "Jeturing Labs"
                },
                "total": 40000.00,
                "reserved": 5000.00,  # Monto reservado para pagos pendientes
                "available": 35000.00
            }
        """
        try:
            from ..services.mercury_account_manager import get_account_manager
            from ..services.mercury_client import get_mercury_client
            import stripe

            # Mercury balances (real API)
            try:
                account_manager = get_account_manager()
                mercury_balances = account_manager.get_both_balances()
                mercury_savings = mercury_balances.get("savings", {}).get("balance", 0)
                mercury_checking = mercury_balances.get("checking", {}).get("balance", 0)
                mercury_total = mercury_savings + mercury_checking
            except Exception as e:
                logger.warning(f"Mercury balance unavailable: {e}")
                mercury_total = 0
                mercury_savings = 0
                mercury_checking = 0

            # Stripe balance (real API)
            try:
                stripe_bal = stripe.Balance.retrieve()
                stripe_available = sum(b.get("amount", 0) for b in stripe_bal.get("available", [])) / 100
                stripe_pending = sum(b.get("amount", 0) for b in stripe_bal.get("pending", [])) / 100
            except Exception as e:
                logger.warning(f"Stripe balance unavailable: {e}")
                stripe_available = 0
                stripe_pending = 0

            # Reservas: payouts pendientes en BD
            reserved_result = self.db.query(
                func.coalesce(func.sum(PayoutRequest.net_amount), 0)
            ).filter(
                PayoutRequest.status.in_([PayoutStatus.pending, PayoutStatus.authorized, PayoutStatus.processing])
            ).scalar()
            reserved = float(reserved_result) if reserved_result else 0

            total = stripe_available + mercury_total
            available = total - reserved
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stripe": {
                    "balance": round(stripe_available, 2),
                    "pending": round(stripe_pending, 2),
                },
                "mercury": {
                    "savings": round(mercury_savings, 2),
                    "checking": round(mercury_checking, 2),
                    "balance": round(mercury_total, 2),
                    "available": round(mercury_total, 2),
                },
                "total": round(total, 2),
                "reserved": round(reserved, 2),
                "available": round(available, 2),
            }
        
        except Exception as e:
            logger.error(f"Error getting balance snapshot: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
    
    # ═══════════════════════════════════════════════════════════════
    # 2. Payouts & Pending
    # ═══════════════════════════════════════════════════════════════
    
    def get_pending_payouts(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Listar payouts pendientes (no completados).
        
        Args:
            status: Filter por status (pending, authorized, processing)
            limit: Limit de resultados
            offset: Offset para paginación
        
        Returns:
            {
                "payouts": [
                    {
                        "id": 123,
                        "provider": "Acme Corp",
                        "amount": 4250.00,
                        "status": "authorized",
                        "transfer_type": "ach",
                        "requested_at": "2026-02-24T10:00:00Z",
                        "authorized_at": "2026-02-24T12:00:00Z",
                        "estimated_delivery": "2026-02-26T00:00:00Z"
                    },
                    ...
                ],
                "total": 15,
                "limit": 50,
                "offset": 0
            }
        """
        try:
            query = self.db.query(PayoutRequest)
            if status:
                try:
                    status_enum = PayoutStatus(status)
                    query = query.filter(PayoutRequest.status == status_enum)
                except ValueError:
                    pass  # Ignorar filtro inválido

            total = query.count()
            payouts = query.order_by(PayoutRequest.created_at.desc()).offset(offset).limit(limit).all()

            return {
                "payouts": [
                    {
                        "id": p.id,
                        "provider": (
                            self.db.query(Partner.company_name)
                            .filter(Partner.id == p.partner_id).scalar() or "—"
                        ),
                        "amount": p.net_amount,
                        "status": p.status.value if p.status else "pending",
                        "transfer_type": p.transfer_type or "ach",
                        "requested_at": p.created_at.isoformat() if p.created_at else None,
                        "authorized_at": p.authorized_at.isoformat() if p.authorized_at else None,
                        "estimated_delivery": p.estimated_delivery.isoformat() if p.estimated_delivery else None,
                    }
                    for p in payouts
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        
        except Exception as e:
            logger.error(f"Error getting pending payouts: {e}")
            return {
                "error": str(e),
                "payouts": [],
                "total": 0,
            }
    
    def get_total_pending_payout_amount(self) -> float:
        """
        Obtener monto total de payouts pendientes (no completados).
        
        Returns: Monto en USD
        """
        try:
            result = self.db.query(
                func.coalesce(func.sum(PayoutRequest.net_amount), 0)
            ).filter(
                PayoutRequest.status.in_([PayoutStatus.pending, PayoutStatus.authorized, PayoutStatus.processing])
            ).scalar()
            return float(result) if result else 0
        
        except Exception as e:
            logger.error(f"Error calculating pending payouts: {e}")
            return 0
    
    # ═══════════════════════════════════════════════════════════════
    # 3. Forecasting
    # ═══════════════════════════════════════════════════════════════
    
    def forecast_cash_needs(
        self,
        days_ahead: int = 7,
    ) -> Dict[str, Any]:
        """
        Forecasting de necesidad de caja para próximos N días.
        
        Considera:
        1. Payouts programados para los próximos N días
        2. Comisiones que se deben pagar
        3. Gastos recurrentes
        4. Margen de seguridad
        
        Args:
            days_ahead: Cantidad de días a proyectar (default 7)
        
        Returns:
            {
                "forecast_period": {
                    "start": "2026-02-24T00:00:00Z",
                    "end": "2026-03-03T23:59:59Z",
                    "days": 7
                },
                "projected_inflows": 0,  # Clientes nuevos, intereses, etc.
                "projected_outflows": 15000.00,  # Payouts programados
                "projected_balance": 25000.00,  # Saldo esperado
                "buffer": 10000.00,  # Saldo de seguridad recomendado
                "recommendation": "proceed" | "caution" | "stop",
                "timeline": [
                    {
                        "date": "2026-02-26",
                        "payout_count": 3,
                        "payout_total": 10000.00,
                        "balance_after": 15000.00
                    },
                    ...
                ]
            }
        """
        try:
            now = datetime.now(timezone.utc)
            end_date = now + timedelta(days=days_ahead)
            
            # Payouts pendientes y autorizados (próximas obligaciones)
            pending_payouts = self.db.query(
                func.coalesce(func.sum(PayoutRequest.net_amount), 0),
                func.count(PayoutRequest.id),
            ).filter(
                PayoutRequest.status.in_([PayoutStatus.pending, PayoutStatus.authorized]),
            ).first()
            projected_outflows = float(pending_payouts[0]) if pending_payouts else 0
            payout_count = pending_payouts[1] if pending_payouts else 0

            # Balance actual
            balance = self.get_balance_snapshot()
            current_balance = balance.get("available", 0)
            projected_balance = current_balance - projected_outflows
            buffer = 10000.00

            if projected_balance < 0:
                recommendation = "stop"
            elif projected_balance < buffer:
                recommendation = "caution"
            else:
                recommendation = "proceed"
            
            return {
                "forecast_period": {
                    "start": now.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days_ahead,
                },
                "projected_inflows": 0,
                "projected_outflows": round(projected_outflows, 2),
                "pending_payout_count": payout_count,
                "current_balance": round(current_balance, 2),
                "projected_balance": round(projected_balance, 2),
                "buffer": buffer,
                "recommendation": recommendation,
            }
        
        except Exception as e:
            logger.error(f"Error forecasting cash needs: {e}")
            return {
                "error": str(e),
                "recommendation": "caution",
            }
    
    # ═══════════════════════════════════════════════════════════════
    # 4. Reportes & Logs
    # ═══════════════════════════════════════════════════════════════
    
    def get_transaction_logs(
        self,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Obtener log de transacciones (filtrable).
        
        Args:
            transaction_type: Filter (inflow, outflow, fee, interest)
            start_date: Fecha inicio
            end_date: Fecha fin
            limit: Limit de resultados
            offset: Offset
        
        Returns:
            {
                "transactions": [
                    {
                        "id": "txn_abc123",
                        "type": "inflow" | "outflow",
                        "amount": 5000.00,
                        "source": "Stripe payment",
                        "destination": "Mercury account",
                        "status": "completed" | "pending",
                        "timestamp": "2026-02-24T15:30:00Z",
                        "reference": "INV-2026-0001"
                    },
                    ...
                ],
                "total": 250,
                "limit": 100,
                "offset": 0
            }
        """
        try:
            query = self.db.query(PaymentEvent)
            if transaction_type:
                type_map = {
                    "inflow": ["invoice_paid", "direct_payment_reconciled"],
                    "outflow": ["payout_executed", "payout_completed"],
                    "fee": ["fee"],
                    "interest": ["interest"],
                }
                types = type_map.get(transaction_type, [transaction_type])
                query = query.filter(PaymentEvent.event_type.in_(types))

            if start_date:
                query = query.filter(PaymentEvent.created_at >= start_date)
            if end_date:
                query = query.filter(PaymentEvent.created_at <= end_date)

            total = query.count()
            events = query.order_by(PaymentEvent.created_at.desc()).offset(offset).limit(limit).all()

            return {
                "transactions": [
                    {
                        "id": e.id,
                        "type": e.event_type,
                        "amount": e.amount,
                        "invoice_id": e.invoice_id,
                        "payout_id": e.payout_id,
                        "actor": e.actor,
                        "metadata": e.metadata_json or {},
                        "timestamp": e.created_at.isoformat() if e.created_at else None,
                    }
                    for e in events
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        
        except Exception as e:
            logger.error(f"Error getting transaction logs: {e}")
            return {
                "error": str(e),
                "transactions": [],
                "total": 0,
            }
    
    def get_provider_payment_history(
        self,
        provider_id: int,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Obtener historial de pagos a un proveedor específico.
        
        Returns:
            {
                "provider_id": 42,
                "provider_name": "Acme Corp",
                "total_paid": 25000.00,
                "payments": [
                    {
                        "id": 123,
                        "amount": 4250.00,
                        "status": "completed",
                        "transfer_type": "ach",
                        "mercury_transfer_id": "xfr_abc123",
                        "completed_at": "2026-02-20T12:00:00Z",
                        "invoice_ref": "INV-2026-0001"
                    },
                    ...
                ]
            }
        """
        try:
            partner = self.db.query(Partner).filter(Partner.id == provider_id).first()
            partner_name = partner.company_name if partner else "—"

            payouts = self.db.query(PayoutRequest).filter(
                PayoutRequest.partner_id == provider_id
            ).order_by(PayoutRequest.created_at.desc()).limit(limit).all()

            total_paid = sum(p.net_amount or 0 for p in payouts if p.status == PayoutStatus.completed)

            return {
                "provider_id": provider_id,
                "provider_name": partner_name,
                "total_paid": round(total_paid, 2),
                "payments": [
                    {
                        "id": p.id,
                        "amount": p.net_amount,
                        "gross_amount": p.gross_amount,
                        "commission": p.jeturing_commission,
                        "status": p.status.value if p.status else "pending",
                        "transfer_type": p.transfer_type,
                        "mercury_transfer_id": p.mercury_transfer_id,
                        "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in payouts
                ],
            }
        
        except Exception as e:
            logger.error(f"Error getting provider payment history: {e}")
            return {
                "error": str(e),
                "provider_id": provider_id,
                "payments": [],
            }
    
    # ═══════════════════════════════════════════════════════════════
    # 5. Alertas
    # ═══════════════════════════════════════════════════════════════
    
    def check_alerts(self) -> Dict[str, List[str]]:
        """
        Chequear condiciones que requieren alerta/acción.
        
        Returns:
            {
                "critical": [
                    "Mercury balance below $5000 threshold"
                ],
                "warnings": [
                    "3 payouts pending authorization",
                    "Daily payout limit 75% utilized"
                ],
                "info": [
                    "Weekly settlement due Feb 28"
                ]
            }
        """
        try:
            alerts = {
                "critical": [],
                "warnings": [],
                "info": [],
            }
            
            # 1. Payouts pendientes de autorización
            pending_count = self.db.query(func.count(PayoutRequest.id)).filter(
                PayoutRequest.status == PayoutStatus.pending
            ).scalar() or 0
            if pending_count > 0:
                alerts["warnings"].append(f"{pending_count} payouts pending authorization")

            # 2. Payouts fallidos recientes
            failed_count = self.db.query(func.count(PayoutRequest.id)).filter(
                PayoutRequest.status == PayoutStatus.failed,
                PayoutRequest.updated_at >= datetime.now(timezone.utc) - timedelta(days=7),
            ).scalar() or 0
            if failed_count > 0:
                alerts["critical"].append(f"{failed_count} failed payouts in last 7 days")

            # 3. Mercury balance check (si disponible)
            try:
                from ..services.mercury_account_manager import get_account_manager
                manager = get_account_manager()
                balances = manager.get_both_balances()
                checking_balance = balances.get("checking", {}).get("balance", 0)
                if checking_balance < 5000:
                    alerts["critical"].append(f"Mercury CHECKING balance ${checking_balance:.2f} below $5000 threshold")
                elif checking_balance < 10000:
                    alerts["warnings"].append(f"Mercury CHECKING balance ${checking_balance:.2f} approaching minimum")
            except Exception:
                alerts["info"].append("Mercury balance check unavailable")
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return {
                "critical": [f"Error checking alerts: {str(e)}"],
                "warnings": [],
                "info": [],
            }
