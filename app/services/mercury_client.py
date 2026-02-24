"""
Mercury Banking API Client

Interfaz de cliente para Mercury Banking API.
Maneja transferencias ACH, Wire, balance, y validación de cuentas bancarias.

Documentación: https://mercury.com/docs
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BankAccount:
    """Estructura de datos para cuenta bancaria."""
    account_number: str
    routing_number: str
    account_holder: str
    account_type: str  # "checking" o "savings"
    bank_name: Optional[str] = None


@dataclass
class TransferRequest:
    """Solicitud de transferencia."""
    amount: float
    currency: str
    description: str
    beneficiary_account: BankAccount
    transfer_type: str  # "ach" o "wire"


class MercuryAPIException(Exception):
    """Excepción base para errores de Mercury API."""
    pass


class MercuryClient:
    """
    Cliente de Mercury Banking API.
    
    Características:
    - Obtener balance de cuenta
    - Crear transferencias (ACH, Wire)
    - Validar cuentas bancarias
    - Listar transacciones
    - Consultar estado de transferencias
    """
    
    def __init__(self):
        """Inicializar cliente con credenciales desde .env"""
        self.api_key = os.getenv("MERCURY_API_KEY", "")
        self.api_url = os.getenv("MERCURY_API_URL", "https://api.mercury.com/api/v1")
        self.account_id = os.getenv("MERCURY_ACCOUNT_ID", "")
        self.webhook_secret = os.getenv("MERCURY_WEBHOOK_SECRET", "")
        
        if not all([self.api_key, self.account_id]):
            logger.warning("⚠️ Mercury API credentials not fully configured. Some features may be limited.")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
    
    # ═══════════════════════════════════════════════════════════════
    # Account Management
    # ═══════════════════════════════════════════════════════════════
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Obtener balance actual de la cuenta de Jeturing en Mercury.
        
        Returns:
            {
                "account_id": "...",
                "balance": 25000.50,
                "currency": "USD",
                "available": 25000.50,
                "pending": 0,
                "last_updated": "2026-02-24T15:30:00Z"
            }
        """
        try:
            url = f"{self.api_url}/accounts/{self.account_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return {
                "account_id": self.account_id,
                "balance": data.get("balance", 0),
                "currency": data.get("currency", "USD"),
                "available": data.get("available_balance", 0),
                "pending": data.get("pending_balance", 0),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Mercury account balance: {e}")
            raise MercuryAPIException(f"Failed to get account balance: {str(e)}")
    
    def get_account_details(self) -> Dict[str, Any]:
        """
        Obtener información completa de la cuenta.
        
        Returns:
            {
                "account_id": "...",
                "account_name": "Jeturing Labs",
                "account_type": "business",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "routing_number": "...",
                "account_number": "..."
            }
        """
        try:
            url = f"{self.api_url}/accounts/{self.account_id}"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Mercury account details: {e}")
            raise MercuryAPIException(f"Failed to get account details: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════
    # Transfers (ACH, Wire)
    # ═══════════════════════════════════════════════════════════════
    
    def create_ach_transfer(
        self,
        amount: float,
        description: str,
        beneficiary: BankAccount,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crear transferencia ACH (domestic, bajo costo).
        
        Args:
            amount: Monto en USD
            description: Descripción (invoice ref, provider name, etc.)
            beneficiary: Datos de la cuenta beneficiaria
            idempotency_key: Para evitar duplicados
        
        Returns:
            {
                "transfer_id": "xfr_...",
                "status": "pending",
                "amount": 5000,
                "type": "ach_debit",
                "created_at": "2026-02-24T15:30:00Z",
                "expected_delivery": "2026-02-26T00:00:00Z"
            }
        """
        try:
            payload = {
                "account_id": self.account_id,
                "transfer_type": "ach_debit",
                "amount": round(amount * 100),  # En centavos
                "currency": "USD",
                "description": description[:200],
                "beneficiary": {
                    "account_number": beneficiary.account_number,
                    "routing_number": beneficiary.routing_number,
                    "account_holder_name": beneficiary.account_holder,
                    "account_type": beneficiary.account_type,
                },
            }
            
            if idempotency_key:
                self.session.headers["Idempotency-Key"] = idempotency_key
            
            url = f"{self.api_url}/transfers"
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"ACH transfer created: {data.get('transfer_id')} - ${amount}")
            
            return {
                "transfer_id": data.get("id") or data.get("transfer_id"),
                "status": data.get("status", "pending"),
                "amount": amount,
                "type": "ach",
                "created_at": data.get("created_at"),
                "expected_delivery": data.get("expected_delivery_date"),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating ACH transfer: {e}")
            raise MercuryAPIException(f"Failed to create ACH transfer: {str(e)}")
    
    def create_wire_transfer(
        self,
        amount: float,
        description: str,
        beneficiary: BankAccount,
        swift_code: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crear transferencia Wire (internacional, más rápido, más caro).
        
        Args:
            amount: Monto en USD
            description: Descripción
            beneficiary: Datos de la cuenta beneficiaria
            swift_code: Para transferencias internacionales
            idempotency_key: Para evitar duplicados
        
        Returns:
            {
                "transfer_id": "xfr_...",
                "status": "pending",
                "amount": 50000,
                "type": "wire",
                "fee": 15,
                "created_at": "2026-02-24T15:30:00Z"
            }
        """
        try:
            payload = {
                "account_id": self.account_id,
                "transfer_type": "wire",
                "amount": round(amount * 100),  # En centavos
                "currency": "USD",
                "description": description[:200],
                "beneficiary": {
                    "account_number": beneficiary.account_number,
                    "routing_number": beneficiary.routing_number,
                    "account_holder_name": beneficiary.account_holder,
                    "account_type": beneficiary.account_type,
                },
            }
            
            if swift_code:
                payload["beneficiary"]["swift_code"] = swift_code
            
            if idempotency_key:
                self.session.headers["Idempotency-Key"] = idempotency_key
            
            url = f"{self.api_url}/transfers"
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Wire transfer created: {data.get('transfer_id')} - ${amount}")
            
            return {
                "transfer_id": data.get("id") or data.get("transfer_id"),
                "status": data.get("status", "pending"),
                "amount": amount,
                "type": "wire",
                "fee": data.get("fee", 15),
                "created_at": data.get("created_at"),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating Wire transfer: {e}")
            raise MercuryAPIException(f"Failed to create Wire transfer: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════
    # Transfer Status & History
    # ═══════════════════════════════════════════════════════════════
    
    def get_transfer_status(self, transfer_id: str) -> Dict[str, Any]:
        """
        Obtener estado actual de una transferencia.
        
        Returns:
            {
                "transfer_id": "xfr_...",
                "status": "posted" | "pending" | "failed" | "canceled",
                "amount": 5000,
                "type": "ach" | "wire",
                "created_at": "2026-02-24T15:30:00Z",
                "posted_at": "2026-02-26T12:00:00Z" (si fue exitosa),
                "failure_reason": "..." (si falló)
            }
        """
        try:
            url = f"{self.api_url}/transfers/{transfer_id}"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return {
                "transfer_id": transfer_id,
                "status": data.get("status"),
                "amount": (data.get("amount", 0) or 0) / 100,
                "type": data.get("transfer_type", "").replace("ach_debit", "ach"),
                "created_at": data.get("created_at"),
                "posted_at": data.get("posted_at"),
                "failure_reason": data.get("failure_reason"),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching transfer status: {e}")
            raise MercuryAPIException(f"Failed to get transfer status: {str(e)}")
    
    def list_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Listar transacciones recientes de la cuenta.
        
        Returns:
            {
                "transactions": [
                    {
                        "id": "txn_...",
                        "type": "transfer_out" | "transfer_in" | "fee" | "interest",
                        "amount": 5000,
                        "status": "posted" | "pending",
                        "counterparty": "Provider Name",
                        "description": "...",
                        "created_at": "2026-02-24T15:30:00Z",
                        "posted_at": "2026-02-26T12:00:00Z"
                    },
                    ...
                ],
                "total": 150,
                "limit": 50,
                "offset": 0
            }
        """
        try:
            params = {
                "limit": limit,
                "offset": offset,
            }
            if start_date:
                params["start_date"] = start_date
            if end_date:
                params["end_date"] = end_date
            
            url = f"{self.api_url}/accounts/{self.account_id}/transactions"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            transactions = []
            for txn in data.get("transactions", []):
                transactions.append({
                    "id": txn.get("id"),
                    "type": txn.get("type"),
                    "amount": (txn.get("amount", 0) or 0) / 100,
                    "status": txn.get("status"),
                    "counterparty": txn.get("counterparty_name"),
                    "description": txn.get("description"),
                    "created_at": txn.get("created_at"),
                    "posted_at": txn.get("posted_at"),
                })
            
            return {
                "transactions": transactions,
                "total": data.get("total", len(transactions)),
                "limit": limit,
                "offset": offset,
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing transactions: {e}")
            raise MercuryAPIException(f"Failed to list transactions: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════
    # Bank Account Validation (KYC)
    # ═══════════════════════════════════════════════════════════════
    
    def validate_bank_account(
        self,
        account_number: str,
        routing_number: str,
        account_type: str = "checking",
    ) -> Dict[str, Any]:
        """
        Validar que una cuenta bancaria sea válida.
        
        Usa Mercury API si está disponible, o fallback a validación local.
        
        Returns:
            {
                "is_valid": True | False,
                "account_number": "...",
                "routing_number": "...",
                "bank_name": "Wells Fargo",
                "account_type": "checking",
                "message": "Valid bank account" | error message
            }
        """
        try:
            # Validación básica
            if not account_number or len(account_number) < 8:
                return {
                    "is_valid": False,
                    "account_number": account_number,
                    "routing_number": routing_number,
                    "message": "Invalid account number (too short)",
                }
            
            if not routing_number or len(routing_number) != 9:
                return {
                    "is_valid": False,
                    "account_number": account_number,
                    "routing_number": routing_number,
                    "message": "Invalid routing number (must be 9 digits)",
                }
            
            # Si Mercury API disponible, validar en su servidor
            if self.api_key:
                payload = {
                    "account_number": account_number,
                    "routing_number": routing_number,
                    "account_type": account_type,
                }
                url = f"{self.api_url}/verify/bank-account"
                response = self.session.post(url, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "is_valid": data.get("valid", True),
                        "account_number": account_number,
                        "routing_number": routing_number,
                        "bank_name": data.get("bank_name"),
                        "account_type": account_type,
                        "message": "Valid bank account" if data.get("valid") else "Invalid bank account",
                    }
            
            # Fallback: solo validación local
            return {
                "is_valid": True,
                "account_number": account_number,
                "routing_number": routing_number,
                "bank_name": "Unknown",
                "account_type": account_type,
                "message": "Bank account passed basic validation (Mercury verification not available)",
            }
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error validating bank account: {e}")
            # Permitir si Mercury no está disponible, pero marcar como no verificado
            return {
                "is_valid": False,
                "account_number": account_number,
                "routing_number": routing_number,
                "message": f"Validation error: {str(e)}",
            }
    
    # ═══════════════════════════════════════════════════════════════
    # Webhook Verification
    # ═══════════════════════════════════════════════════════════════
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verificar que un webhook proviene realmente de Mercury.
        
        Mercury usa HMAC-SHA256 con el secret configurado.
        
        Args:
            payload: Body raw del webhook
            signature: Header X-Mercury-Signature
        
        Returns:
            True si la firma es válida, False caso contrario
        """
        import hmac
        import hashlib
        
        if not self.webhook_secret:
            logger.warning("⚠️ Mercury webhook secret not configured")
            return False
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False


# Singleton para fácil acceso global
_mercury_client: Optional[MercuryClient] = None


def get_mercury_client() -> MercuryClient:
    """Obtener instancia singleton del cliente Mercury."""
    global _mercury_client
    if _mercury_client is None:
        _mercury_client = MercuryClient()
    return _mercury_client
