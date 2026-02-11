from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Enum, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

Base = declarative_base()


# ===== ENUMS =====
class SubscriptionStatus(enum.Enum):
    pending = "pending"
    active = "active"
    cancelled = "cancelled"
    past_due = "past_due"


class NodeStatus(enum.Enum):
    online = "online"
    offline = "offline"
    maintenance = "maintenance"
    full = "full"


class ContainerStatus(enum.Enum):
    running = "running"
    stopped = "stopped"
    provisioning = "provisioning"
    error = "error"


class PlanType(enum.Enum):
    basic = "basic"           # Compartido - recursos limitados
    pro = "pro"               # Semi-dedicado
    enterprise = "enterprise" # Dedicado - recursos garantizados

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    company_name = Column(String)
    subdomain = Column(String, unique=True, index=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)
    stripe_subscription_id = Column(String, unique=True, index=True)
    stripe_checkout_session_id = Column(String, unique=True, index=True)
    plan_name = Column(String, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.pending)
    tenant_provisioned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StripeEvent(Base):
    __tablename__ = "stripe_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ===== MULTI-PROXMOX MODELS =====

class ProxmoxNode(Base):
    """Nodo de Proxmox en el cluster distribuido"""
    __tablename__ = "proxmox_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # ej: "node-us-east-1"
    hostname = Column(String(255), nullable=False)            # ej: "172.16.16.100"
    api_port = Column(Integer, default=8006)
    ssh_port = Column(Integer, default=22)
    proxmox_version = Column(String(20))                      # ej: "8.1.3"
    
    # Capacidad total del nodo
    total_cpu_cores = Column(Integer, default=0)
    total_ram_gb = Column(Float, default=0)
    total_storage_gb = Column(Float, default=0)
    
    # Uso actual (actualizado por monitoreo)
    used_cpu_percent = Column(Float, default=0)
    used_ram_gb = Column(Float, default=0)
    used_storage_gb = Column(Float, default=0)
    
    # Límites para auto-provisioning
    max_containers = Column(Integer, default=50)
    current_containers = Column(Integer, default=0)
    
    # Estado y configuración
    status = Column(Enum(NodeStatus), default=NodeStatus.online)
    is_database_node = Column(Boolean, default=False)  # Si es nodo de BD centralizada
    priority = Column(Integer, default=100)            # Mayor = más prioridad para nuevos tenants
    region = Column(String(50))                        # ej: "us-east", "eu-west"
    
    # Credenciales (encriptadas en producción)
    api_token_id = Column(String(255))                 # ej: "root@pam!onboarding"
    api_token_secret = Column(Text)                    # Token encriptado
    ssh_user = Column(String(50), default="root")
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = Column(DateTime)
    
    # Relaciones
    containers = relationship("LXCContainer", back_populates="node")


class LXCContainer(Base):
    """Contenedor LXC individual en un nodo Proxmox"""
    __tablename__ = "lxc_containers"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("proxmox_nodes.id"), nullable=False)
    vmid = Column(Integer, nullable=False)             # ID del contenedor en Proxmox
    hostname = Column(String(255), nullable=False)      # Hostname del contenedor
    
    # Recursos asignados
    cpu_cores = Column(Integer, default=1)
    ram_mb = Column(Integer, default=2048)
    disk_gb = Column(Float, default=20)
    
    # Uso actual
    cpu_usage_percent = Column(Float, default=0)
    ram_usage_mb = Column(Float, default=0)
    disk_usage_gb = Column(Float, default=0)
    
    # Red
    ip_address = Column(String(45))                     # IPv4 o IPv6
    mac_address = Column(String(17))
    
    # Estado
    status = Column(Enum(ContainerStatus), default=ContainerStatus.provisioning)
    
    # Tipo de contenedor
    is_shared = Column(Boolean, default=True)           # True = Basic plan (compartido)
    template_used = Column(String(100))                 # ej: "odoo-17-template"
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_backup = Column(DateTime)
    
    # Relaciones
    node = relationship("ProxmoxNode", back_populates="containers")
    deployments = relationship("TenantDeployment", back_populates="container")


class TenantDeployment(Base):
    """Relación entre Subscription y LXCContainer - donde está desplegado cada tenant"""
    __tablename__ = "tenant_deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    container_id = Column(Integer, ForeignKey("lxc_containers.id"), nullable=False)
    
    # Configuración del tenant
    subdomain = Column(String(100), nullable=False)
    database_name = Column(String(100))
    odoo_port = Column(Integer, default=8069)
    
    # URLs de acceso
    tunnel_url = Column(String(255))                    # ej: "acme.sajet.us"
    direct_url = Column(String(255))                    # ej: "172.16.16.105:8069"
    
    # Estado del tunnel
    tunnel_active = Column(Boolean, default=False)
    tunnel_id = Column(String(100))                     # ID del tunnel en Cloudflare
    
    # Plan y recursos
    plan_type = Column(Enum(PlanType), default=PlanType.basic)
    
    # Metadatos
    deployed_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    
    # Relaciones
    container = relationship("LXCContainer", back_populates="deployments")


class ResourceMetric(Base):
    """Historial de métricas de recursos para monitoreo"""
    __tablename__ = "resource_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("proxmox_nodes.id"))
    container_id = Column(Integer, ForeignKey("lxc_containers.id"))
    
    # Métricas
    cpu_percent = Column(Float)
    ram_mb = Column(Float)
    disk_gb = Column(Float)
    network_in_mb = Column(Float)
    network_out_mb = Column(Float)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class SystemConfig(Base):
    """
    Configuración del sistema administrable desde /admin
    
    Permite cambiar configuraciones sin reiniciar la app.
    Los valores aquí sobreescriben las variables de entorno.
    """
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(500))
    category = Column(String(50), default="general")  # odoo, stripe, security, etc.
    is_secret = Column(Boolean, default=False)  # Si es contraseña/token, no mostrar valor
    is_editable = Column(Boolean, default=True)  # Si se puede editar desde UI
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))  # Usuario que hizo el último cambio
    
    def __repr__(self):
        return f"<SystemConfig {self.key}={self.value if not self.is_secret else '***'}>"


# ===== HELPER FUNCTIONS PARA CONFIGURACIÓN =====

def get_config(key: str, default: str = None) -> str:
    """
    Obtiene valor de configuración.
    Prioridad: BD > Variable de entorno > Default
    """
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            return config.value
        return os.getenv(key, default)
    except:
        return os.getenv(key, default)
    finally:
        db.close()


def set_config(key: str, value: str, description: str = None, category: str = "general", 
               is_secret: bool = False, updated_by: str = "system") -> bool:
    """Guarda o actualiza un valor de configuración en la BD"""
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config:
            config.value = value
            config.updated_by = updated_by
            if description:
                config.description = description
        else:
            config = SystemConfig(
                key=key,
                value=value,
                description=description,
                category=category,
                is_secret=is_secret,
                updated_by=updated_by
            )
            db.add(config)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()


def get_all_configs(category: str = None) -> list:
    """Obtiene todas las configuraciones, opcionalmente filtradas por categoría"""
    db = SessionLocal()
    try:
        query = db.query(SystemConfig)
        if category:
            query = query.filter(SystemConfig.category == category)
        configs = query.all()
        return [
            {
                "key": c.key,
                "value": c.value if not c.is_secret else "********",
                "description": c.description,
                "category": c.category,
                "is_secret": c.is_secret,
                "is_editable": c.is_editable,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "updated_by": c.updated_by
            }
            for c in configs
        ]
    finally:
        db.close()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jeturing:321Abcd@localhost/onboarding_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
