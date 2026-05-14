"""
Modelo DgiiRncCache: Caché local del padrón RNC oficial.

Propósito: Evitar consultas repetidas a API DGII (si está disponible)
y mantener validaciones locales rápidas.

TTL: 30 días (configurable)
"""
from sqlalchemy import Column, String, DateTime, Enum, Index, Integer, Boolean, JSON, Numeric, func
from sqlalchemy.sql import expression
from datetime import datetime, timedelta
from app.models.database import Base
import enum


class RncStatus(str, enum.Enum):
    """Estados posibles de un RNC."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    NOT_FOUND = "not_found"
    SUSPENDED = "suspended"


class DgiiRncCache(Base):
    """Cache local del padrón RNC."""
    __tablename__ = 'dgii_rnc_cache'
    
    # Clave primaria
    rnc_number = Column(String(11), primary_key=True, unique=True, index=True)
    
    # Datos del RNC
    business_name = Column(String(255), nullable=True)
    status = Column(
        Enum(RncStatus),
        default=RncStatus.NOT_FOUND,
        nullable=False
    )
    
    # Auditoría
    last_updated = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    ttl_expires = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30),
        nullable=False,
        index=True
    )
    
    # Control
    update_count = Column(
        Integer,
        default=1,
        comment="Número de veces consultado"
    )
    
    # Índices
    __table_args__ = (
        Index('ix_dgii_rnc_cache_ttl', 'ttl_expires'),
        Index('ix_dgii_rnc_cache_status', 'status'),
    )
    
    def __repr__(self):
        return f"<DgiiRncCache {self.rnc_number} [{self.status.value}]>"
    
    @property
    def is_expired(self) -> bool:
        """Verificar si el cache ha expirado."""
        return self.ttl_expires < datetime.utcnow()
    
    def refresh_ttl(self, days: int = 30):
        """Refrescar TTL."""
        self.ttl_expires = datetime.utcnow() + timedelta(days=days)
        self.last_updated = datetime.utcnow()
        self.update_count += 1


class DgiiValidationLog(Base):
    """Log de validaciones DGII realizadas."""
    __tablename__ = 'dgii_validation_log'
    
    # Identificadores
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, nullable=False, index=True)
    
    # Documento validado
    document_type = Column(String(3), nullable=False)  # "606", "607", "608"
    ncf = Column(String(13), nullable=True, index=True)
    amount = Column(Numeric(16, 2), nullable=True)
    
    # Resultado validación
    is_valid = Column(Boolean, default=False)
    issues_found = Column(Integer, default=0)
    error_codes = Column(JSON, nullable=True)  # Lista de issue codes
    
    # Auditoría
    validated_at = Column(DateTime, default=func.now(), index=True)
    validated_by = Column(Integer, nullable=True)  # user_id
    
    def __repr__(self):
        return f"<DgiiValidationLog {self.document_type} {self.ncf} [{self.is_valid}]>"


class DgiiDataServiceConfig(Base):
    """Configuración del DGII Data Service."""
    __tablename__ = 'dgii_data_service_config'
    
    # Identificadores
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, unique=True, nullable=False)
    
    # API Endpoints
    rnc_api_url = Column(String(255), nullable=True)
    rnc_api_key = Column(String(255), nullable=True)
    
    # Cache settings
    cache_ttl_days = Column(Integer, default=30)
    cache_enabled = Column(Boolean, default=True)
    
    # Validation rules
    auto_enrich_partner = Column(Boolean, default=True)
    auto_fix_common_errors = Column(Boolean, default=False)
    reject_duplicate_ncf = Column(Boolean, default=True)
    
    # Auditoría
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DgiiDataServiceConfig company_id={self.company_id}>"
