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
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "inflows": {
                    "total": 50000.00,
                    "from_customers": 50000.00,
                    "from_interest": 0,
                    "transactions_count": 12,
                },
                "outflows": {
                    "total": 12000.00,
                    "to_providers": 10000.00,
                    "bank_fees": 500.00,
                    "other": 1500.00,
                    "transactions_count": 8,
                },
                "net": 38000.00,
                "balance": {
                    "opening": 25000.00,
                    "closing": 63000.00,
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
            # TODO: Llamar APIs de Stripe y Mercury
            stripe_balance = 15000.00
            mercury_balance = 25000.00
            
            # TODO: Calcular reservas de payouts pendientes
            reserved = 5000.00
            
            total = stripe_balance + mercury_balance
            available = total - reserved
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stripe": {
                    "balance": stripe_balance,
                    "pending": 2500.00,
                    "connected_accounts": 3,
                },
                "mercury": {
                    "balance": mercury_balance,
                    "available": mercury_balance,
                    "pending": 0,
                    "account_name": "Jeturing Labs",
                },
                "total": total,
                "reserved": reserved,
                "available": available,
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
            # TODO: Query BD para payout_requests
            # - Filter por status si se proporciona
            # - Order por requested_at DESC
            # - Join con partners para obtener nombre
            # - Paginate con limit/offset
            
            return {
                "payouts": [
                    {
                        "id": 123,
                        "provider": "Acme Corp",
                        "amount": 4250.00,
                        "status": "authorized",
                        "transfer_type": "ach",
                        "requested_at": "2026-02-24T10:00:00Z",
                        "authorized_at": "2026-02-24T12:00:00Z",
                        "estimated_delivery": "2026-02-26T00:00:00Z",
                    },
                    {
                        "id": 124,
                        "provider": "Tech Solutions",
                        "amount": 2150.00,
                        "status": "pending",
                        "transfer_type": "ach",
                        "requested_at": "2026-02-24T14:00:00Z",
                        "authorized_at": None,
                        "estimated_delivery": None,
                    },
                ],
                "total": 15,
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
            # TODO: Query BD para SUM(amount) WHERE status != 'completed' AND status != 'failed'
            return 6400.00  # Placeholder
        
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
            
            # TODO: Query BD para:
            # - Payouts scheduled en período
            # - Agrupar por fecha
            # - Calcular balance proyectado día a día
            
            return {
                "forecast_period": {
                    "start": now.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days_ahead,
                },
                "projected_inflows": 0,
                "projected_outflows": 15000.00,
                "projected_balance": 25000.00,
                "buffer": 10000.00,
                "recommendation": "proceed",
                "timeline": [
                    {
                        "date": "2026-02-26",
                        "payout_count": 3,
                        "payout_total": 10000.00,
                        "balance_after": 15000.00,
                    },
                ],
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
            # TODO: Query mercury_transactions + payout_requests
            # - Combinar ambas tablas
            # - Filter por type, date range
            # - Order by timestamp DESC
            # - Paginate
            
            return {
                "transactions": [
                    {
                        "id": "txn_abc123",
                        "type": "inflow",
                        "amount": 5000.00,
                        "source": "Stripe payment",
                        "destination": "Mercury account",
                        "status": "completed",
                        "timestamp": "2026-02-24T15:30:00Z",
                        "reference": "INV-2026-0001",
                    },
                    {
                        "id": "xfr_def456",
                        "type": "outflow",
                        "amount": 2150.00,
                        "source": "Mercury account",
                        "destination": "Acme Corp (ACH)",
                        "status": "processing",
                        "timestamp": "2026-02-24T14:00:00Z",
                        "reference": "PAYOUT-2026-0012",
                    },
                ],
                "total": 250,
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
            # TODO: Query payout_requests WHERE provider_id = ?
            # - Order by completed_at DESC
            # - Calculate total_paid
            
            return {
                "provider_id": provider_id,
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
                        "invoice_ref": "INV-2026-0001",
                    },
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
            
            # TODO: Implementar checks:
            # 1. Mercury balance < threshold
            # 2. Payouts vencidos sin autorizar
            # 3. Daily limit approaching
            # 4. Reconciliation discrepancies
            # 5. Failed transfers en retry
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
            return {
                "critical": [f"Error checking alerts: {str(e)}"],
                "warnings": [],
                "info": [],
            }
