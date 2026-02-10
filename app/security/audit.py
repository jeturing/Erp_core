"""
Audit Logging - Security event tracking and logging
"""
from datetime import datetime
from typing import Optional
from enum import Enum
import json
import logging
import os

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# File handler for audit logs - use local logs directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

audit_file_handler = logging.FileHandler(f"{LOG_DIR}/audit.log")
audit_file_handler.setLevel(logging.INFO)

# JSON formatter for structured logs
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "audit_data"):
            log_data.update(record.audit_data)
        return json.dumps(log_data)

audit_file_handler.setFormatter(JSONFormatter())
audit_logger.addHandler(audit_file_handler)

# También log a consola en desarrollo
if os.getenv("ENVIRONMENT", "development") != "production":
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    audit_logger.addHandler(console_handler)


class AuditEvent(str, Enum):
    """Tipos de eventos de auditoría."""
    
    # Autenticación
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"
    
    # 2FA
    TOTP_ENABLED = "TOTP_ENABLED"
    TOTP_DISABLED = "TOTP_DISABLED"
    TOTP_VERIFIED = "TOTP_VERIFIED"
    TOTP_FAILED = "TOTP_FAILED"
    
    # Seguridad
    WAF_BLOCKED = "WAF_BLOCKED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    
    # Admin actions
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    ROLE_CHANGED = "ROLE_CHANGED"
    
    # Tenant actions
    TENANT_CREATED = "TENANT_CREATED"
    TENANT_PROVISIONED = "TENANT_PROVISIONED"
    TENANT_SUSPENDED = "TENANT_SUSPENDED"
    TENANT_DELETED = "TENANT_DELETED"
    
    # Billing
    SUBSCRIPTION_CREATED = "SUBSCRIPTION_CREATED"
    SUBSCRIPTION_UPDATED = "SUBSCRIPTION_UPDATED"
    SUBSCRIPTION_CANCELLED = "SUBSCRIPTION_CANCELLED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    
    # Data access
    DATA_EXPORTED = "DATA_EXPORTED"
    DATA_IMPORTED = "DATA_IMPORTED"
    SENSITIVE_DATA_ACCESSED = "SENSITIVE_DATA_ACCESSED"


class AuditLogger:
    """
    Logger de auditoría para eventos de seguridad.
    """
    
    @staticmethod
    def log(
        event: AuditEvent,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        role: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        details: Optional[dict] = None,
        request = None
    ):
        """
        Registra un evento de auditoría.
        
        Args:
            event: Tipo de evento
            user_id: ID del usuario
            username: Nombre de usuario
            role: Rol del usuario
            ip_address: IP del cliente
            user_agent: User-Agent del cliente
            resource: Recurso afectado
            action: Acción realizada
            status: success/failure
            details: Detalles adicionales
            request: Request object para extraer IP y UA
        """
        # Extraer datos del request si está disponible
        if request:
            if not ip_address:
                forwarded = request.headers.get("X-Forwarded-For")
                if forwarded:
                    ip_address = forwarded.split(",")[0].strip()
                elif hasattr(request, "client") and request.client:
                    ip_address = request.client.host
            
            if not user_agent:
                user_agent = request.headers.get("User-Agent", "")[:200]
        
        audit_data = {
            "event": event.value,
            "user_id": user_id,
            "username": username,
            "role": role,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "resource": resource,
            "action": action,
            "status": status,
            "details": details or {}
        }
        
        # Crear record con datos extra
        record = logging.LogRecord(
            name="audit",
            level=logging.INFO if status == "success" else logging.WARNING,
            pathname="",
            lineno=0,
            msg=f"{event.value}: {status}",
            args=(),
            exc_info=None
        )
        record.audit_data = audit_data
        
        audit_logger.handle(record)
    
    @staticmethod
    def log_login_success(
        username: str,
        role: str,
        user_id: int = None,
        request = None
    ):
        """Registra un login exitoso."""
        AuditLogger.log(
            event=AuditEvent.LOGIN_SUCCESS,
            username=username,
            role=role,
            user_id=user_id,
            status="success",
            request=request
        )
    
    @staticmethod
    def log_login_failed(
        username: str,
        reason: str = "Invalid credentials",
        request = None
    ):
        """Registra un intento de login fallido."""
        AuditLogger.log(
            event=AuditEvent.LOGIN_FAILED,
            username=username,
            status="failure",
            details={"reason": reason},
            request=request
        )
    
    @staticmethod
    def log_logout(
        username: str,
        user_id: int = None,
        request = None
    ):
        """Registra un logout."""
        AuditLogger.log(
            event=AuditEvent.LOGOUT,
            username=username,
            user_id=user_id,
            status="success",
            request=request
        )
    
    @staticmethod
    def log_rate_limit(
        username: str = None,
        request = None
    ):
        """Registra cuando se excede el rate limit."""
        AuditLogger.log(
            event=AuditEvent.RATE_LIMIT_EXCEEDED,
            username=username,
            status="blocked",
            request=request
        )
    
    @staticmethod
    def log_waf_blocked(
        attack_type: str,
        target: str,
        request = None
    ):
        """Registra cuando el WAF bloquea una solicitud."""
        AuditLogger.log(
            event=AuditEvent.WAF_BLOCKED,
            status="blocked",
            details={
                "attack_type": attack_type,
                "target": target
            },
            request=request
        )
    
    @staticmethod
    def log_totp_event(
        event: AuditEvent,
        username: str,
        user_id: int = None,
        success: bool = True,
        request = None
    ):
        """Registra eventos de 2FA/TOTP."""
        AuditLogger.log(
            event=event,
            username=username,
            user_id=user_id,
            status="success" if success else "failure",
            request=request
        )
    
    @staticmethod
    def log_admin_action(
        event: AuditEvent,
        admin_username: str,
        target_resource: str,
        action: str,
        details: dict = None,
        request = None
    ):
        """Registra acciones administrativas."""
        AuditLogger.log(
            event=event,
            username=admin_username,
            role="admin",
            resource=target_resource,
            action=action,
            status="success",
            details=details,
            request=request
        )


# Almacenamiento de logs en BD (opcional)
class AuditLogStore:
    """
    Almacena logs de auditoría en la base de datos.
    Útil para búsquedas y reportes.
    """
    
    _logs = []  # En memoria para demo, usar DB en producción
    
    @classmethod
    def store(cls, audit_data: dict):
        """Almacena un log en la BD."""
        audit_data["id"] = len(cls._logs) + 1
        audit_data["created_at"] = datetime.utcnow().isoformat()
        cls._logs.append(audit_data)
    
    @classmethod
    def search(
        cls,
        event: str = None,
        username: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> list:
        """Busca logs de auditoría."""
        results = []
        
        for log in reversed(cls._logs):
            if event and log.get("event") != event:
                continue
            if username and log.get("username") != username:
                continue
            # Agregar filtros de fecha si es necesario
            
            results.append(log)
            if len(results) >= limit:
                break
        
        return results
    
    @classmethod
    def get_recent(cls, limit: int = 50) -> list:
        """Obtiene los logs más recientes."""
        return list(reversed(cls._logs[-limit:]))
