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


class DomainVerificationStatus(enum.Enum):
    pending = "pending"
    verifying = "verifying"
    verified = "verified"
    failed = "failed"


class CustomerStatus(enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


class PartnerStatus(enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
    terminated = "terminated"


class BillingScenario(enum.Enum):
    jeturing_collects = "jeturing_collects"   # Escenario A: Jeturing cobra al cliente final
    partner_collects = "partner_collects"     # Escenario B: Partner cobra con NCF local


class LeadStatus(enum.Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    proposal = "proposal"
    won = "won"
    lost = "lost"
    invalid = "invalid"


class CommissionStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    paid = "paid"
    disputed = "disputed"
    offset = "offset"


class QuotationStatus(enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"
    invoiced = "invoiced"


class ServiceCategory(enum.Enum):
    saas_platform = "saas_platform"
    saas_support = "saas_support"
    core_financiero = "core_financiero"
    vciso = "vciso"
    soc = "soc"
    cloud_devops = "cloud_devops"
    payments_pos = "payments_pos"


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String(255))  # Para autenticación de portal
    full_name = Column(String, nullable=False)
    company_name = Column(String)
    subdomain = Column(String, unique=True, index=True, nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True)
    plan = Column(Enum(PlanType), default=PlanType.basic)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.active)
    phone = Column(String(50))
    notes = Column(Text)
    user_count = Column(Integer, default=1)              # Usuarios Odoo del tenant
    is_admin_account = Column(Boolean, default=False)    # True = admin@sajet.us (no se cobra)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    custom_domains = relationship("CustomDomain", back_populates="customer", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="customer")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, index=True)
    stripe_checkout_session_id = Column(String, unique=True, index=True)
    plan_name = Column(String, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.pending)
    tenant_provisioned = Column(Boolean, default=False)
    user_count = Column(Integer, default=1)              # Usuarios facturables
    monthly_amount = Column(Float, default=0)            # Monto calculado: base + (extra_users * price_per_user)
    currency = Column(String(3), default="USD")
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = relationship("Customer", back_populates="subscriptions")

class StripeEvent(Base):
    __tablename__ = "stripe_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Plan(Base):
    """
    Planes configurables desde el admin.
    El precio final se calcula: base_price + (price_per_user * user_count)
    """
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)       # basic, pro, enterprise
    display_name = Column(String(100), nullable=False)           # "Plan Básico"
    description = Column(Text)
    base_price = Column(Float, default=0, nullable=False)        # Precio base mensual USD
    price_per_user = Column(Float, default=0, nullable=False)    # Precio por usuario adicional
    included_users = Column(Integer, default=1, nullable=False)  # Usuarios incluidos en base_price
    max_users = Column(Integer, default=0)                       # 0 = ilimitado
    max_domains = Column(Integer, default=0)                     # 0 = sin dominios custom, -1 = ilimitado
    currency = Column(String(3), default="USD")
    stripe_price_id = Column(String(100))                        # Price ID de Stripe (recurrente)
    stripe_product_id = Column(String(100))                      # Product ID de Stripe
    features = Column(Text)                                      # JSON con features del plan
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)                      # Orden de visualización
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_monthly(self, user_count: int) -> float:
        """Calcula precio mensual según cantidad de usuarios."""
        extra = max(0, user_count - self.included_users)
        return self.base_price + (extra * self.price_per_user)
    
    def __repr__(self):
        return f"<Plan {self.name}: ${self.base_price} + ${self.price_per_user}/user>"


# ===== SERVICE CATALOG =====

class ServiceCatalogItem(Base):
    """Catálogo de servicios/productos cotizables — tabla de precios oficial"""
    __tablename__ = "service_catalog"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(Enum(ServiceCategory), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    unit = Column(String(50), nullable=False)            # "Por servidor", "Por usuario", "Por cuenta", "Por bloque"
    price_monthly = Column(Float, nullable=False)        # Precio mensual USD
    price_max = Column(Float)                            # Para rangos (ej: 350–650)
    is_addon = Column(Boolean, default=False)            # SOC requiere vCISO
    requires_service_id = Column(Integer, ForeignKey("service_catalog.id"))  # Dependencia
    min_quantity = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ===== PARTNER / SOCIO MODEL =====

class Partner(Base):
    """
    Socio comercial — Acuerdo Global de Partnership (No Exclusivo).
    Modelo 50/50 sobre Ingresos Netos. Puede tener Escenario A o B de cobro.
    """
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), unique=True)  # Cuenta de login del partner
    company_name = Column(String(200), nullable=False)
    legal_name = Column(String(200))
    tax_id = Column(String(50))                          # EIN/RNC/Tax ID
    contact_name = Column(String(150))
    contact_email = Column(String(150), nullable=False)
    phone = Column(String(50))
    country = Column(String(100))
    address = Column(Text)

    # Comercial
    billing_scenario = Column(Enum(BillingScenario), default=BillingScenario.jeturing_collects)
    commission_rate = Column(Float, default=50.0)        # % del partner (contrato: 50%)
    margin_cap = Column(Float, default=30.0)             # Máx % margen sobre precio base (cláusula 8.7)
    status = Column(Enum(PartnerStatus), default=PartnerStatus.pending)
    portal_access = Column(Boolean, default=True)

    # Stripe Connect Express
    stripe_account_id = Column(String(100))              # acct_XXXX — Stripe Connected Account ID
    stripe_onboarding_complete = Column(Boolean, default=False)  # KYC completado
    stripe_charges_enabled = Column(Boolean, default=False)      # Puede recibir pagos

    # Contrato
    contract_signed_at = Column(DateTime)
    contract_reference = Column(String(100))             # Nro de contrato

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    customer = relationship("Customer", backref="partner_profile")
    leads = relationship("Lead", back_populates="partner", cascade="all, delete-orphan")
    commissions = relationship("Commission", back_populates="partner")


class Lead(Base):
    """
    Prospecto registrado por un partner — Cláusula 7 del contrato.
    Debe registrarse en el Portal de Socios antes del cierre comercial.
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    company_name = Column(String(200), nullable=False)
    contact_name = Column(String(150))
    contact_email = Column(String(150))
    phone = Column(String(50))
    country = Column(String(100))
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    notes = Column(Text)
    estimated_monthly_value = Column(Float, default=0)   # Valor estimado mensual
    converted_customer_id = Column(Integer, ForeignKey("customers.id"))  # Si se convierte
    converted_at = Column(DateTime)
    lost_reason = Column(String(200))
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    partner = relationship("Partner", back_populates="leads")
    converted_customer = relationship("Customer", foreign_keys=[converted_customer_id])


class Commission(Base):
    """
    Comisiones — Cláusula 8: Split 50/50 sobre Ingresos Netos.
    Calculadas mensualmente sobre montos efectivamente cobrados.
    """
    __tablename__ = "commissions"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    gross_revenue = Column(Float, default=0)             # Monto bruto cobrado
    net_revenue = Column(Float, default=0)               # Ingresos Netos (§1.8)
    deductions_json = Column(Text)                       # JSON: {fees, refunds, chargebacks, taxes}
    partner_amount = Column(Float, default=0)            # 50% para partner
    jeturing_amount = Column(Float, default=0)           # 50% para Jeturing
    status = Column(Enum(CommissionStatus), default=CommissionStatus.pending)
    paid_at = Column(DateTime)
    payment_reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    partner = relationship("Partner", back_populates="commissions")
    subscription = relationship("Subscription")
    lead = relationship("Lead")


class Quotation(Base):
    """
    Cotizaciones enviables a clientes/prospectos.
    Pueden ser creadas por admin o por partner (con margen ≤ 30% cap).
    """
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String(20), unique=True, nullable=False)  # QT-2026-0001
    created_by_partner_id = Column(Integer, ForeignKey("partners.id"))
    created_by_admin = Column(Boolean, default=False)

    # Destinatario
    customer_id = Column(Integer, ForeignKey("customers.id"))       # Cliente existente
    prospect_name = Column(String(200))                             # O prospecto nuevo
    prospect_email = Column(String(150))
    prospect_company = Column(String(200))
    prospect_phone = Column(String(50))

    # Líneas de cotización almacenadas como JSON
    lines_json = Column(Text)  # [{service_id, name, unit, qty, unit_price, subtotal}]
    subtotal = Column(Float, default=0)
    partner_margin = Column(Float, default=0)            # Margen del partner (≤30% base)
    total_monthly = Column(Float, default=0)
    currency = Column(String(3), default="USD")

    # Estado
    status = Column(Enum(QuotationStatus), default=QuotationStatus.draft)
    valid_until = Column(DateTime)
    notes = Column(Text)
    terms = Column(Text)                                 # Términos/condiciones adicionales

    # Tracking
    sent_at = Column(DateTime)
    accepted_at = Column(DateTime)
    rejected_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    partner = relationship("Partner")
    customer = relationship("Customer")


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
    custom_domains = relationship("CustomDomain", back_populates="deployment")


class CustomDomain(Base):
    """
    Dominios personalizados de clientes.
    Cada cliente puede tener múltiples dominios externos que apuntan a su subdominio de sajet.us
    
    Ejemplo:
    - external_domain: "www.impulse-max.com"
    - sajet_subdomain: "impulse-max" 
    - sajet_full_domain: "impulse-max.sajet.us" (generado)
    """
    __tablename__ = "custom_domains"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    tenant_deployment_id = Column(Integer, ForeignKey("tenant_deployments.id", ondelete="SET NULL"), nullable=True)
    
    # Dominio externo del cliente
    external_domain = Column(String(255), unique=True, nullable=False, index=True)  # ej: "www.impulse-max.com"
    
    # Subdominio interno de sajet.us
    sajet_subdomain = Column(String(100), unique=True, nullable=False, index=True)  # ej: "impulse-max"
    
    # Estado de verificación
    verification_status = Column(Enum(DomainVerificationStatus), default=DomainVerificationStatus.pending)
    verification_token = Column(String(64))  # Token para verificar propiedad
    verified_at = Column(DateTime)
    
    # Configuración Cloudflare
    cloudflare_dns_record_id = Column(String(50))  # ID del registro CNAME en zona sajet.us
    cloudflare_configured = Column(Boolean, default=False)
    tunnel_ingress_configured = Column(Boolean, default=False)
    
    # Configuración Nginx (PCT160 + CT105)
    nginx_configured = Column(Boolean, default=False)
    
    # SSL (manejado por Cloudflare automáticamente)
    ssl_status = Column(String(20), default="pending")  # pending, active, error
    
    # Estado
    is_active = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)  # Dominio principal del tenant
    
    # Nodo asignado (para arquitectura multi-nodo)
    target_node_ip = Column(String(50))  # IP del nodo Odoo (Tailscale o privada)
    target_port = Column(Integer, default=8069)
    
    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    
    # Relaciones
    customer = relationship("Customer", back_populates="custom_domains")
    deployment = relationship("TenantDeployment", back_populates="custom_domains")
    
    @property
    def sajet_full_domain(self) -> str:
        """Genera el dominio completo de sajet.us"""
        return f"{self.sajet_subdomain}.sajet.us"
    
    def __repr__(self):
        return f"<CustomDomain {self.external_domain} → {self.sajet_full_domain}>"


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

# Database connection - PCT 160 (SRV-Sajet)
# Uses psycopg3 (postgresql+psycopg://) driver
# Intentar usar PostgreSQL, fallback a SQLite si no está disponible
_raw_url = os.getenv("DATABASE_URL", "postgresql://jeturing:321Abcd@10.10.10.20:5432/erp_core_db")
_psycopg_url = _raw_url.replace("postgresql://", "postgresql+psycopg://", 1) if _raw_url.startswith("postgresql://") and "+psycopg" not in _raw_url else _raw_url

# Usar SQLite como fallback si SQLALCHEMY_DATABASE_URL está definida
if os.getenv("ENABLE_SQLITE_FALLBACK") == "true" and os.getenv("SQLALCHEMY_DATABASE_URL"):
    DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
else:
    DATABASE_URL = _psycopg_url

# Lazy engine initialization - avoids import-time DB connection (helps testing)
_engine = None
_SessionLocal = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
    return _engine

def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal

# Backwards-compatible properties via module-level accessors
class _EngineProxy:
    """Proxy that lazily initializes the engine on first use."""
    def __getattr__(self, name):
        return getattr(_get_engine(), name)

class _SessionLocalProxy:
    """Proxy that lazily initializes SessionLocal on first use."""
    def __call__(self, *args, **kwargs):
        return _get_session_factory()(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(_get_session_factory(), name)

engine = _EngineProxy()
SessionLocal = _SessionLocalProxy()

def init_db():
    Base.metadata.create_all(bind=_get_engine())

def get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()
