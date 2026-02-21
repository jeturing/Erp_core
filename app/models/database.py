from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Enum, Float, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

Base = declarative_base()


# ═══════════════════════════════════════════════════════
# ENUMS — Épica 1: BillingMode + Tenant Origin Rules
# ═══════════════════════════════════════════════════════

class SubscriptionStatus(enum.Enum):
    pending = "pending"
    active = "active"
    cancelled = "cancelled"
    past_due = "past_due"
    suspended = "suspended"


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


# ─── NUEVOS ENUMS (Épica 1) ───

class BillingMode(enum.Enum):
    """Modo de facturación de la suscripción — decide quién cobra y quién paga."""
    JETURING_DIRECT_SUBSCRIPTION = "jeturing_direct_subscription"  # Cliente paga directo a Jeturing vía Stripe
    PARTNER_DIRECT = "partner_direct"                              # Escenario A: Jeturing cobra, partner gana 50%
    PARTNER_PAYS_FOR_CLIENT = "partner_pays_for_client"            # Escenario B: Partner cobra a su cliente y paga a Jeturing
    LEGACY_IMPORTED = "legacy_imported"                            # Tenant migrado / legacy — solo reconciliación, DB readonly


class InvoiceIssuer(enum.Enum):
    """Quién emite la factura fiscal."""
    JETURING = "jeturing"     # Factura de Jeturing SRL con EIN/RNC Jeturing
    PARTNER = "partner"       # Factura del partner con su NCF local


class CollectorType(enum.Enum):
    """Quién procesa el cobro del dinero."""
    STRIPE_DIRECT = "stripe_direct"           # Stripe cobra directo (Jeturing es merchant)
    STRIPE_CONNECT = "stripe_connect"         # Stripe cobra a través de Stripe Connect (partner)
    PARTNER_EXTERNAL = "partner_external"     # Partner cobra externamente y paga a Jeturing


class PayerType(enum.Enum):
    """Quién es el pagador en la suscripción."""
    CLIENT = "client"       # El cliente final paga
    PARTNER = "partner"     # El partner paga por su cliente


class LeadStatus(enum.Enum):
    """Pipeline extendido: desde prospecto hasta tenant activo."""
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    in_qualification = "in_qualification"       # Partner calificando al prospecto
    proposal = "proposal"
    won = "won"
    tenant_requested = "tenant_requested"       # Cliente/Partner solicitó tenant
    provisioning_running = "provisioning_running"  # Provisionando en PCT105
    tenant_ready = "tenant_ready"               # Tenant listo — dispara factura
    invoiced = "invoiced"                       # Primera factura emitida
    active = "active"                           # En operación normal
    suspended = "suspended"                     # Suspendido por impago
    closed = "closed"                           # Cerrado definitivamente
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


class SupportLevel(enum.Enum):
    """Nivel de soporte asignado a un partner/pricing tier."""
    helpdesk_only = "helpdesk_only"      # Solo vía ticket en helpdesk
    priority = "priority"                # Soporte prioritario
    dedicated = "dedicated"              # Soporte dedicado con SLA


class SeatEventType(enum.Enum):
    """Tipos de evento de asientos/usuarios."""
    USER_CREATED = "user_created"       # Usuario creado en Odoo
    USER_DEACTIVATED = "user_deactivated"
    USER_REACTIVATED = "user_reactivated"
    FIRST_LOGIN = "first_login"         # Primer login = billable (Épica 4)
    HWM_SNAPSHOT = "hwm_snapshot"       # Snapshot diario de high-water mark


class InvoiceStatus(enum.Enum):
    draft = "draft"
    issued = "issued"
    paid = "paid"
    overdue = "overdue"
    void = "void"
    credited = "credited"


class InvoiceType(enum.Enum):
    """Tipo de factura."""
    SUBSCRIPTION = "subscription"
    SETUP = "setup"
    ADDON = "addon"
    INTERCOMPANY = "intercompany"       # Factura intercompany Partner→Jeturing (Esc B)
    CREDIT_NOTE = "credit_note"


class SettlementStatus(enum.Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    transferred = "transferred"
    disputed = "disputed"


class WorkOrderStatus(enum.Enum):
    requested = "requested"
    approved = "approved"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"
    cancelled = "cancelled"


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=False, index=True, nullable=False)
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

    # ─── Épica 1: Billing Mode + Origin Rules ───
    billing_mode = Column(Enum(BillingMode), default=BillingMode.JETURING_DIRECT_SUBSCRIPTION, nullable=True)
    invoice_issuer = Column(Enum(InvoiceIssuer), default=InvoiceIssuer.JETURING, nullable=True)
    collector = Column(Enum(CollectorType), default=CollectorType.STRIPE_DIRECT, nullable=True)
    payer_type = Column(Enum(PayerType), default=PayerType.CLIENT, nullable=True)
    owner_partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)  # Partner que trajo este cliente
    package_id = Column(Integer, ForeignKey("module_packages.id"), nullable=True)  # Épica 2: Paquete de módulos

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    customer = relationship("Customer", back_populates="subscriptions")
    owner_partner = relationship("Partner", foreign_keys=[owner_partner_id])
    package = relationship("ModulePackage", foreign_keys=[package_id])
    seat_events = relationship("SeatEvent", back_populates="subscription", cascade="all, delete-orphan")
    seat_high_waters = relationship("SeatHighWater", back_populates="subscription", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="subscription")

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
    # ── Quotas de recursos (Phase 2) ──
    max_storage_mb = Column(Integer, default=0)                  # 0 = ilimitado, MB de almacenamiento
    max_websites = Column(Integer, default=1)                    # Websites Odoo (multi-website)
    max_companies = Column(Integer, default=1)                   # Multi-company
    max_backups = Column(Integer, default=0)                     # Backups automáticos retenidos, 0=ilimitado
    max_api_calls_day = Column(Integer, default=0)               # Llamadas API diarias, 0=ilimitado
    currency = Column(String(3), default="USD")
    stripe_price_id = Column(String(100))                        # Price ID de Stripe (recurrente)
    stripe_product_id = Column(String(100))                      # Product ID de Stripe
    features = Column(Text)                                      # JSON con features del plan
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)                      # Orden de visualización
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_monthly(self, user_count: int, partner_id: int = None) -> float:
        """Calcula precio mensual según cantidad de usuarios y override de partner."""
        base = self.base_price
        ppu = self.price_per_user
        included = self.included_users

        if partner_id:
            try:
                from . import database as _db
                db = _db.SessionLocal()
                try:
                    override = db.query(PartnerPricingOverride).filter(
                        PartnerPricingOverride.partner_id == partner_id,
                        PartnerPricingOverride.plan_name == self.name,
                        PartnerPricingOverride.is_active == True,
                    ).first()
                    if override:
                        base = override.base_price_override if override.base_price_override is not None else base
                        ppu = override.price_per_user_override if override.price_per_user_override is not None else ppu
                        included = override.included_users_override if override.included_users_override is not None else included
                finally:
                    db.close()
            except Exception:
                pass  # Fallback a precios globales

        extra = max(0, user_count - included)
        return base + (extra * ppu)
    
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

    # ── Portal Auth (Épica Partners) ──
    password_hash = Column(String(255), nullable=True)   # Hash salt:sha256 para login propio
    portal_email = Column(String(200), nullable=True, unique=True, index=True)  # Email de login (default=contact_email)
    onboarding_step = Column(Integer, default=0)         # 0=invited, 1=credentials, 2=profile, 3=stripe_kyc, 4=complete
    onboarding_completed_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    invited_at = Column(DateTime, nullable=True)
    invited_by = Column(String(150), nullable=True)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    customer = relationship("Customer", backref="partner_profile")
    leads = relationship("Lead", back_populates="partner", cascade="all, delete-orphan")
    commissions = relationship("Commission", back_populates="partner")
    pricing_overrides = relationship("PartnerPricingOverride", back_populates="partner", cascade="all, delete-orphan")


class PartnerPricingOverride(Base):
    """
    Override de precios por partner — permite tarifas diferenciadas.
    Ej: Techeels paga $120 base + $30/user vs el precio público del plan.
    Si un campo es NULL, se usa el valor del plan global.
    """
    __tablename__ = "partner_pricing_overrides"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id", ondelete="CASCADE"), nullable=False)
    plan_name = Column(String(50), nullable=False)                    # basic, pro, enterprise

    # Overrides de precio (NULL = usar valor global del plan)
    base_price_override = Column(Float, nullable=True)                # Precio base mensual USD
    price_per_user_override = Column(Float, nullable=True)            # Precio por usuario adicional
    included_users_override = Column(Integer, nullable=True)          # Usuarios incluidos en base

    # Tarifas adicionales del partner
    setup_fee = Column(Float, default=0)                              # Fee de setup/implementación
    customization_hourly_rate = Column(Float, nullable=True)          # Tarifa hora personalización
    support_level = Column(Enum(SupportLevel), default=SupportLevel.helpdesk_only)
    ecf_passthrough = Column(Boolean, default=False)                  # Si e-CF es costo pass-through
    ecf_monthly_cost = Column(Float, nullable=True)                   # Costo mensual e-CF por empresa

    # Metadata
    label = Column(String(100), nullable=True)                        # Ej: "Plan Partner SMB"
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)                      # Vigencia (NULL = siempre)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("partner_id", "plan_name", name="uq_partner_plan_override"),
    )

    # Relaciones
    partner = relationship("Partner", back_populates="pricing_overrides")

    def effective_price(self, plan: 'Plan', user_count: int) -> float:
        """Calcula el precio mensual usando overrides o fallback al plan."""
        base = self.base_price_override if self.base_price_override is not None else plan.base_price
        ppu = self.price_per_user_override if self.price_per_user_override is not None else plan.price_per_user
        included = self.included_users_override if self.included_users_override is not None else plan.included_users
        extra = max(0, user_count - included)
        return base + (extra * ppu)


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


# ═══════════════════════════════════════════════════════
# ÉPICA 2: Module Catalog & Packages (Blueprints)
# ═══════════════════════════════════════════════════════

class ModuleCatalog(Base):
    """
    Catálogo de módulos Odoo disponibles.
    Cada registro es un módulo instalable (ej: jeturing_finance_core).
    """
    __tablename__ = "module_catalog"

    id = Column(Integer, primary_key=True, index=True)
    technical_name = Column(String(150), unique=True, nullable=False, index=True)  # ej: jeturing_finance_core
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))                         # ej: "Finanzas", "CRM", "Inventario"
    version = Column(String(20), default="17.0.1.0")
    is_core = Column(Boolean, default=False)               # Viene siempre incluido (base)
    partner_allowed = Column(Boolean, default=True)        # Disponible para partners (Épica 5A: allowlist)
    price_monthly = Column(Float, default=0)               # Precio adicional mensual USD
    requires_module_id = Column(Integer, ForeignKey("module_catalog.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    requires = relationship("ModuleCatalog", remote_side=[id])


class ModulePackage(Base):
    """
    Paquete de módulos (Blueprint) — configurable.
    Ejemplo: "Pack Financiero", "Pack Retail", "Pack Completo".
    """
    __tablename__ = "module_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    plan_type = Column(Enum(PlanType), nullable=True)      # Si está atado a un plan específico
    base_price_monthly = Column(Float, default=0)          # Precio base del paquete
    is_default = Column(Boolean, default=False)            # Paquete por defecto para plan
    is_active = Column(Boolean, default=True)
    # JSON array de technical_names de módulos incluidos
    module_list = Column(JSON, default=list)               # ["jeturing_finance_core", "account", ...]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModulePackageItem(Base):
    """Relación N:N entre ModulePackage y ModuleCatalog."""
    __tablename__ = "module_package_items"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("module_packages.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("module_catalog.id", ondelete="CASCADE"), nullable=False)
    is_optional = Column(Boolean, default=False)           # Si es opcional dentro del paquete
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("package_id", "module_id", name="uq_package_module"),)

    package = relationship("ModulePackage", backref="items")
    module = relationship("ModuleCatalog")


# ═══════════════════════════════════════════════════════
# ÉPICA 3 & 4: Seats — High-Water Mark + Partner Metered
# ═══════════════════════════════════════════════════════

class SeatEvent(Base):
    """
    Evento de asiento/usuario en un tenant.
    Registra cada creación, desactivación, reactivación y primer login.
    Épica 3 = Direct (HWM→Stripe qty), Épica 4 = Partner (first_login + grace 8h).
    """
    __tablename__ = "seat_events"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    event_type = Column(Enum(SeatEventType), nullable=False)
    odoo_user_id = Column(Integer, nullable=True)          # res.users ID en Odoo
    odoo_login = Column(String(150), nullable=True)
    user_count_after = Column(Integer, nullable=False)     # Total active users después del evento
    is_billable = Column(Boolean, default=False)           # True si genera cobro
    grace_expires_at = Column(DateTime, nullable=True)     # Épica 4: gracia 8h desde first_login
    source = Column(String(50), default="webhook")         # webhook, api, cron, manual
    metadata_json = Column(JSON, nullable=True)            # Datos adicionales
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relaciones
    subscription = relationship("Subscription", back_populates="seat_events")


class SeatHighWater(Base):
    """
    Snapshot diario del high-water mark de usuarios activos.
    Se usa para actualizar Stripe quantity en modo Direct (Épica 3).
    """
    __tablename__ = "seat_high_water"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    period_date = Column(DateTime, nullable=False)         # Fecha del período (día)
    hwm_count = Column(Integer, nullable=False)            # Máximo de usuarios activos ese día
    stripe_qty_updated = Column(Boolean, default=False)    # Si ya se actualizó Stripe
    stripe_qty_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("subscription_id", "period_date", name="uq_sub_period"),
        Index("ix_seat_hwm_sub_date", "subscription_id", "period_date"),
    )

    subscription = relationship("Subscription", back_populates="seat_high_waters")


# ═══════════════════════════════════════════════════════
# ÉPICA 5: Invoices — emitidas en TENANT_READY
# ═══════════════════════════════════════════════════════

class Invoice(Base):
    """
    Factura interna (no fiscal, espejo de Stripe).
    Se crea automáticamente cuando Lead alcanza tenant_ready.
    Incluye subscription + setup. Intercompany en Escenario B.
    """
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(30), unique=True, nullable=False)  # INV-2026-0001
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)

    # Tipo y modo
    invoice_type = Column(Enum(InvoiceType), default=InvoiceType.SUBSCRIPTION)
    billing_mode = Column(Enum(BillingMode), nullable=True)
    issuer = Column(Enum(InvoiceIssuer), default=InvoiceIssuer.JETURING)

    # Montos
    subtotal = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total = Column(Float, default=0)
    currency = Column(String(3), default="USD")
    lines_json = Column(JSON, default=list)                # [{description, qty, unit_price, subtotal}]

    # Stripe reference
    stripe_invoice_id = Column(String(100), nullable=True)
    stripe_payment_intent_id = Column(String(100), nullable=True)

    # Estado
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.draft)
    issued_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    subscription = relationship("Subscription", back_populates="invoices")
    customer = relationship("Customer")
    partner = relationship("Partner")


# ═══════════════════════════════════════════════════════
# ÉPICA 6: Settlements — 50/50 + offsets
# ═══════════════════════════════════════════════════════

class SettlementPeriod(Base):
    """
    Período de liquidación mensual entre Jeturing y un Partner.
    Agrupa todas las líneas del mes para un 50/50 split.
    """
    __tablename__ = "settlement_periods"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    gross_revenue = Column(Float, default=0)
    net_revenue = Column(Float, default=0)                 # Gross - fees - refunds - chargebacks
    jeturing_share = Column(Float, default=0)              # 50%
    partner_share = Column(Float, default=0)               # 50%
    offset_amount = Column(Float, default=0)               # Créditos/débitos previos
    final_partner_payout = Column(Float, default=0)        # partner_share - offset
    status = Column(Enum(SettlementStatus), default=SettlementStatus.draft)
    approved_by = Column(String(100), nullable=True)
    transfer_reference = Column(String(200), nullable=True)
    transferred_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("partner_id", "period_start", name="uq_partner_period"),
    )

    partner = relationship("Partner")
    lines = relationship("SettlementLine", back_populates="settlement", cascade="all, delete-orphan")


class SettlementLine(Base):
    """Línea individual de un settlement (una suscripción en un período)."""
    __tablename__ = "settlement_lines"

    id = Column(Integer, primary_key=True, index=True)
    settlement_id = Column(Integer, ForeignKey("settlement_periods.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    description = Column(String(300), nullable=False)
    gross_amount = Column(Float, default=0)
    stripe_fee = Column(Float, default=0)
    refunds = Column(Float, default=0)
    chargebacks = Column(Float, default=0)
    net_amount = Column(Float, default=0)
    jeturing_amount = Column(Float, default=0)
    partner_amount = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    settlement = relationship("SettlementPeriod", back_populates="lines")


# ═══════════════════════════════════════════════════════
# ÉPICA 7: Stripe Reconciliation + Infra Assets
# ═══════════════════════════════════════════════════════

class InfraAsset(Base):
    """
    Activo de infraestructura (LXC, DNS, dominio, etc.) asociado a facturación.
    Permite reconciliar qué se cobra vs qué recursos consume.
    """
    __tablename__ = "infra_assets"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    asset_type = Column(String(50), nullable=False)        # "lxc", "domain", "backup", "addon"
    asset_reference = Column(String(200), nullable=False)  # vmid, domain name, etc.
    monthly_cost = Column(Float, default=0)                # Costo mensual de este asset
    is_billable = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscription = relationship("Subscription")


class ReconciliationRun(Base):
    """Registro de cada corrida de reconciliación Stripe vs BD local."""
    __tablename__ = "reconciliation_runs"

    id = Column(Integer, primary_key=True, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    stripe_total = Column(Float, default=0)
    local_total = Column(Float, default=0)
    discrepancy = Column(Float, default=0)
    discrepancy_details = Column(JSON, nullable=True)      # [{sub_id, expected, actual, diff}]
    status = Column(String(20), default="completed")       # completed, discrepancy_found
    run_by = Column(String(100), default="cron")
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════
# ÉPICA 9: Work Orders
# ═══════════════════════════════════════════════════════

class WorkOrder(Base):
    """
    Orden de trabajo — gating de operaciones costosas/irreversibles.
    Ej: upgrade de plan, migración, instalación de módulo adicional.
    """
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(30), unique=True, nullable=False)  # WO-2026-0001
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)

    # Tipo y descripción
    work_type = Column(String(100), nullable=False)        # plan_upgrade, module_install, migration, etc.
    description = Column(Text, nullable=False)
    parameters_json = Column(JSON, nullable=True)          # Parámetros de la operación

    # Estado
    status = Column(Enum(WorkOrderStatus), default=WorkOrderStatus.requested)
    requested_by = Column(String(150), nullable=False)
    approved_by = Column(String(150), nullable=True)
    completed_by = Column(String(150), nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result_json = Column(JSON, nullable=True)              # Resultado de la ejecución
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════
# ÉPICA 10: Audit Persistente + White-label Branding
# ═══════════════════════════════════════════════════════

class AuditEventRecord(Base):
    """
    Evento de auditoría persistido en PostgreSQL.
    Reemplaza el AuditLogStore en memoria.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    actor_id = Column(Integer, nullable=True)              # user_id del actor
    actor_username = Column(String(150), nullable=True)
    actor_role = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    resource = Column(String(200), nullable=True)
    action = Column(String(100), nullable=True)
    status = Column(String(20), default="success")         # success, failure, blocked
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_type_created", "event_type", "created_at"),
        Index("ix_audit_actor_created", "actor_username", "created_at"),
    )


class PlanCatalogLink(Base):
    """
    Vínculo N:N entre Plan y ServiceCatalogItem.
    Permite asignar items del catálogo de servicios a cada plan
    para que el admin vea qué servicios incluye cada plan.
    """
    __tablename__ = "plan_catalog_links"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    catalog_item_id = Column(Integer, ForeignKey("service_catalog.id", ondelete="CASCADE"), nullable=False)
    included_quantity = Column(Integer, default=1)         # Cantidad incluida en el plan
    is_included = Column(Boolean, default=True)            # True = incluido, False = addon con descuento
    discount_percent = Column(Float, default=0)            # Descuento sobre precio_catalogo para este plan
    notes = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("plan_id", "catalog_item_id", name="uq_plan_catalog"),
    )

    plan = relationship("Plan", backref="catalog_links")
    catalog_item = relationship("ServiceCatalogItem", backref="plan_links")


class PartnerBrandingProfile(Base):
    """
    Perfil de white-label/branding de un partner.
    Define colores, logo, nombre para la interfaz del cliente final.
    """
    __tablename__ = "partner_branding_profiles"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), unique=True, nullable=False)
    brand_name = Column(String(200), nullable=True)        # Nombre mostrado en vez de "Sajet"
    logo_url = Column(String(500), nullable=True)
    favicon_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#4F46E5")   # Hex color
    secondary_color = Column(String(7), default="#7C3AED")
    support_email = Column(String(200), nullable=True)
    support_url = Column(String(500), nullable=True)
    custom_css = Column(Text, nullable=True)               # CSS adicional
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    partner = relationship("Partner", backref="branding_profile")


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

# Database connection — uses centralized config (no hardcoded credentials)
from ..config import DATABASE_URL as _CONFIG_DB_URL

# Allow SQLALCHEMY_DATABASE_URL override for testing
if os.getenv("ENABLE_SQLITE_FALLBACK") == "true" and os.getenv("SQLALCHEMY_DATABASE_URL"):
    DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
else:
    DATABASE_URL = _CONFIG_DB_URL

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
