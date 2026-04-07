from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Enum, Float, ForeignKey, JSON, UniqueConstraint, Index, BigInteger
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os
import uuid

Base = declarative_base()


# ═══════════════════════════════════════════════════════
# ENUMS — Épica 1: BillingMode + Tenant Origin Rules
# ═══════════════════════════════════════════════════════

class SubscriptionStatus(enum.Enum):
    pending = "pending"
    active = "active"
    trialing = "trialing"
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


class StorageAlertStatus(enum.Enum):
    warning = "warning"      # 75% del límite
    critical = "critical"    # 90% del límite
    exceeded = "exceeded"     # 100%


# ═══════════════════════════════════════════════════════
# ENUMS — Épica API Keys: Gestión de claves estilo Stripe
# ═══════════════════════════════════════════════════════

class ApiKeyStatus(enum.Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"
    rotating = "rotating"   # Grace period: clave vieja válida 24h tras rotar


class ApiKeyScope(enum.Enum):
    read_only = "read_only"
    read_write = "read_write"
    admin = "admin"
    custom = "custom"


class ApiKeyTier(enum.Enum):
    free = "free"             # 10 RPM  / 100 RPD  / 10K tokens/mes
    standard = "standard"     # 60 RPM  / 10K RPD  / 100K tokens/mes
    pro = "pro"               # 300 RPM / 100K RPD / 500K tokens/mes
    enterprise = "enterprise" # 2K RPM  / unlimited / unlimited+ del límite


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
    email_service = "email_service"


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


class AdminUserRole(enum.Enum):
    admin = "admin"
    operator = "operator"
    viewer = "viewer"
    segrd_admin = "segrd-admin"
    segrd_user = "segrd-user"


# ═══════════════════════════════════════════════════════
# ENUMS — Multi-Nodo: Runtime, Routing y Migración
# ═══════════════════════════════════════════════════════

class RuntimeMode(enum.Enum):
    """Modo de ejecución del tenant en el nodo Odoo."""
    shared_pool = "shared_pool"             # Servicio Odoo multi-tenant compartido
    dedicated_service = "dedicated_service" # Instancia Odoo aislada por tenant


class RoutingMode(enum.Enum):
    """Cómo PCT160 enruta tráfico al backend del tenant."""
    node_proxy = "node_proxy"         # PCT160 → nginx del nodo (:8080/:8072) con rewrite
    direct_service = "direct_service" # PCT160 → backend_host:http_port/chat_port directo


class MigrationState(enum.Enum):
    """Estado de migración de un tenant entre nodos o modos de runtime."""
    idle = "idle"                         # Sin migración activa
    queued = "queued"                     # En cola para migrar
    preflight = "preflight"               # Validando nodo destino
    preparing_target = "preparing_target" # Creando runtime destino sin tráfico
    warming_target = "warming_target"     # Precalentando en nodo destino
    cutover = "cutover"                   # Cortando tráfico al destino
    verifying = "verifying"               # Verificando post-migración
    rollback = "rollback"                 # Revirtiendo al origen
    completed = "completed"               # Migración exitosa
    failed = "failed"                     # Migración fallida


class AdminUser(Base):
    """
    Usuarios administrativos de la plataforma.
    Permite múltiples admins, operadores y viewers con login por email.
    El admin hardcodeado (env vars) se mantiene como fallback.
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(200), nullable=False)
    role = Column(
        Enum(
            AdminUserRole,
            name="adminuserrole",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=AdminUserRole.admin.value,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    require_email_verify = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(150), nullable=True)


# ═══════════════════════════════════════════════════════
# EMAIL VERIFICATION TOKENS — Steam-style login verify
# ═══════════════════════════════════════════════════════

class EmailVerificationToken(Base):
    """
    Token alfanumérico de 6 caracteres enviado por email al hacer login.
    Estilo Steam Guard: tras verificar contraseña, se envía código al email.
    Configurable por rol: obligatorio partner/tenant, opcional admin.
    """
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(10), nullable=False)
    token_hash = Column(String(64), nullable=False, index=True)
    user_type = Column(String(30), nullable=False, default="tenant")
    user_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════
# AGREEMENT TEMPLATES + SIGNED AGREEMENTS (NDA, TOS)
# ═══════════════════════════════════════════════════════

class AgreementType(enum.Enum):
    nda = "nda"
    service_agreement = "service_agreement"
    terms_of_service = "terms_of_service"
    privacy_policy = "privacy_policy"
    developer_agreement = "developer_agreement"
    marketplace_nda = "marketplace_nda"


class AgreementTarget(enum.Enum):
    partner = "partner"
    customer = "customer"
    both = "both"
    developer = "developer"


class AgreementTemplate(Base):
    """
    Template editable de NDA/TOS/Acuerdos.
    HTML con variables: {{signer_name}}, {{signer_company}}, {{date}}, etc.
    El admin puede editar desde el panel. Se renderiza a PDF al firmar.
    """
    __tablename__ = "agreement_templates"

    id = Column(Integer, primary_key=True, index=True)
    agreement_type = Column(Enum(AgreementType), default=AgreementType.nda, nullable=False)
    target = Column(Enum(AgreementTarget), default=AgreementTarget.partner, nullable=False)
    title = Column(String(300), nullable=False)
    version = Column(String(20), nullable=False, default="1.0")
    html_content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0)
    created_by = Column(String(150), nullable=True)
    updated_by = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    signed_agreements = relationship("SignedAgreement", back_populates="template")


class SignedAgreement(Base):
    """
    Registro de firma digital — hash SHA256 del documento + firma + timestamp + IP.
    Almacena la firma como texto (typed signature, estilo Stripe).
    """
    __tablename__ = "signed_agreements"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("agreement_templates.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("partners.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    signer_name = Column(String(200), nullable=False)
    signer_email = Column(String(255), nullable=False)
    signer_title = Column(String(150), nullable=True)
    signer_company = Column(String(200), nullable=True)
    signature_data = Column(Text, nullable=False)          # Typed name as signature
    signature_type = Column(String(20), default="typed", nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    document_hash = Column(String(64), nullable=False)     # SHA256 of rendered HTML
    pdf_path = Column(String(500), nullable=True)
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    template = relationship("AgreementTemplate", back_populates="signed_agreements")
    partner = relationship("Partner", foreign_keys=[partner_id])
    customer = relationship("Customer", foreign_keys=[customer_id])


# ═══════════════════════════════════════════════════════
# Developer Portal — Apps & Agreement Workflows
# ═══════════════════════════════════════════════════════

class DeveloperAppStatus(enum.Enum):
    created = "created"
    org_linked = "org_linked"
    agreements_pending = "agreements_pending"
    sandbox_granted = "sandbox_granted"
    verification_requested = "verification_requested"
    verified = "verified"
    rejected = "rejected"


class AgreementFlowStatus(enum.Enum):
    generated = "generated"
    pending = "pending"
    viewed = "viewed"
    in_review = "in_review"
    signed = "signed"
    rejected = "rejected"


class DeveloperApp(Base):
    """
    Apps del Developer Portal — modelo estilo Uber Developer Dashboard.
    Cada app tiene un flujo de acuerdos multi-etapa antes de recibir acceso.
    """
    __tablename__ = "developer_apps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    api_suite = Column(String(100), nullable=False, default="eats_marketplace")
    app_mode = Column(String(20), nullable=False, default="test")  # test | production
    status = Column(String(50), nullable=False, default="created")
    partner_id = Column(Integer, ForeignKey("partners.id", ondelete="CASCADE"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=True)
    created_by = Column(String(150), nullable=True)
    organization_name = Column(String(200), nullable=True)
    organization_linked = Column(Boolean, default=False)
    sandbox_access = Column(Boolean, default=False)
    webhook_url = Column(String(500), nullable=True)
    access_token = Column(String(500), nullable=True)
    client_id = Column(String(200), nullable=True)
    client_secret = Column(String(500), nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agreement_flows = relationship("DeveloperAgreementFlow", back_populates="app", cascade="all, delete-orphan")
    partner = relationship("Partner", foreign_keys=[partner_id])
    customer = relationship("Customer", foreign_keys=[customer_id])


class DeveloperAgreementFlow(Base):
    """
    Flujo multi-etapa de acuerdos para apps del developer portal.
    Estados: generated → pending → viewed → in_review → signed | rejected
    """
    __tablename__ = "developer_agreement_flows"

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("developer_apps.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("agreement_templates.id", ondelete="RESTRICT"), nullable=False)
    signed_agreement_id = Column(Integer, ForeignKey("signed_agreements.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), nullable=False, default="generated")
    generated_at = Column(DateTime, default=datetime.utcnow)
    viewed_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    signed_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    pdf_preview_path = Column(String(500), nullable=True)
    reviewer_id = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    app = relationship("DeveloperApp", back_populates="agreement_flows")
    template = relationship("AgreementTemplate")
    signed_agreement = relationship("SignedAgreement")


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=False, index=True, nullable=False)
    password_hash = Column(String(255))  # Para autenticación de portal
    full_name = Column(String, nullable=False)
    company_name = Column(String)
    subdomain = Column(String, unique=True, index=True, nullable=False)
    stripe_customer_id = Column(String, index=True)
    plan = Column(Enum(PlanType), default=PlanType.basic)
    status = Column(Enum(CustomerStatus), default=CustomerStatus.active)
    phone = Column(String(50))
    notes = Column(Text)
    user_count = Column(Integer, default=1)              # Usuarios Odoo del tenant
    stock_sku_count = Column(Integer, default=0)         # SKUs únicos con stock real reportados desde Odoo
    is_admin_account = Column(Boolean, default=False)    # True = admin@sajet.us (no se cobra)
    is_accountant = Column(Boolean, default=False)       # True = Contador/CPA con acceso multi-tenant
    accountant_firm_name = Column(String(200), nullable=True)  # Nombre de la firma contable
    fair_use_enabled = Column(Boolean, default=False)    # Estrategia fair use aplica solo a clientes nuevos
    last_usage_sync_at = Column(DateTime, nullable=True) # Último snapshot de uso recibido desde Odoo

    # ── Onboarding flow ──
    onboarding_step = Column(Integer, default=0)         # 0=nuevo, 1=perfil, 2=ecf(si RD), 3=pago, 4=completo
    onboarding_completed_at = Column(DateTime, nullable=True)
    onboarding_bypass = Column(Boolean, default=False)   # True = salta onboarding, va directo al portal
    country = Column(String(100), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)

    # ── Dominican Republic e-CF (Comprobantes Fiscales Electrónicos) ──
    requires_ecf = Column(Boolean, default=False)
    ecf_rnc = Column(String(20), nullable=True)                      # RNC / Cédula fiscal
    ecf_business_name = Column(String(250), nullable=True)           # Razón social ante DGII
    ecf_establishment_type = Column(String(50), nullable=True)       # persona_fisica, persona_juridica, zona_franca
    ecf_ncf_series = Column(String(20), nullable=True)               # Serie NCF autorizada (B01, B02, B14, B15)
    ecf_environment = Column(String(20), default="test_ecf")         # test_ecf | production
    ecf_certificate_expiry = Column(DateTime, nullable=True)         # Vencimiento certificado digital DGII
    ecf_authorized_sequences = Column(Text, nullable=True)           # JSON: rangos autorizados DGII

    # ── 2FA / TOTP (persistido en BD) ──
    totp_secret = Column(String(64), nullable=True)          # Base32 secret cifrado
    totp_enabled = Column(Boolean, default=False)
    totp_backup_codes = Column(Text, nullable=True)          # JSON list de códigos de respaldo
    totp_backup_codes_used = Column(Text, nullable=True)     # JSON list de códigos ya usados

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_password_changed_at = Column(DateTime, nullable=True)  # Último cambio de contraseña en Odoo

    # Relaciones
    custom_domains = relationship("CustomDomain", back_populates="customer", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="customer")
    referral_partner = relationship("Partner", foreign_keys=[partner_id])

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
    max_stock_sku = Column(Integer, default=0)                   # 0 = ilimitado; SKUs únicos con stock real permitidos
    quota_warning_percent = Column(Integer, default=80)          # Banner amarillo a partir de este %
    quota_recommend_percent = Column(Integer, default=95)        # Recomendación de upgrade a partir de este %
    quota_block_percent = Column(Integer, default=100)           # Fase 2: bloqueo a partir de este %
    fair_use_new_customers_only = Column(Boolean, default=True)  # Política aplica solo a clientes nuevos
    currency = Column(String(3), default="USD")
    stripe_price_id = Column(String(100))                        # Price ID de Stripe (recurrente)
    stripe_product_id = Column(String(100))                      # Product ID de Stripe
    features = Column(Text)                                      # JSON con features del plan
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)                    # Visible en landing page pricing
    is_highlighted = Column(Boolean, default=False)              # "Most Popular" badge en pricing
    trial_days = Column(Integer, default=14)                     # Días de prueba gratis
    annual_discount_percent = Column(Float, default=20)          # Descuento por pago anual
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
    service_code = Column(String(100), nullable=True, index=True)   # Ej: postal_email_package
    metadata_json = Column(JSON, nullable=True)                     # Metadata flexible por servicio
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CustomerAddonSubscription(Base):
    """
    Servicios/add-ons comprados por un cliente fuera del plan base.
    Se usan para:
      - Vender paquetes desde portal tenant/partner
      - Facturar add-ons de forma inmediata y recurrente
      - Mantener snapshot del precio/metadata al momento de la compra
    """
    __tablename__ = "customer_addon_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id", ondelete="SET NULL"), nullable=True, index=True)
    catalog_item_id = Column(Integer, ForeignKey("service_catalog.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)  # active | cancelled
    quantity = Column(Integer, nullable=False, default=1)
    unit_price_monthly = Column(Float, nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")
    service_code = Column(String(100), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    acquired_via = Column(String(50), nullable=False, default="tenant_portal")
    notes = Column(Text, nullable=True)
    starts_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ends_at = Column(DateTime, nullable=True)
    last_invoiced_year = Column(Integer, nullable=True)
    last_invoiced_month = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", foreign_keys=[customer_id], backref="addon_subscriptions")
    subscription = relationship("Subscription", foreign_keys=[subscription_id], backref="addon_subscriptions")
    partner = relationship("Partner", foreign_keys=[partner_id])
    catalog_item = relationship("ServiceCatalogItem", foreign_keys=[catalog_item_id])


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

    # Código único de partner (visible en dashboard, clientes lo usan para solicitar cambio)
    partner_code = Column(String(20), unique=True, index=True, nullable=True)
    # Slug amigable para URLs públicas: sajet.us/plt/{slug} — fallback a partner_code
    slug = Column(String(100), unique=True, index=True, nullable=True)

    # Stripe Connect Express
    stripe_account_id = Column(String(100))              # acct_XXXX — Stripe Connected Account ID
    stripe_onboarding_complete = Column(Boolean, default=False)  # KYC completado
    stripe_charges_enabled = Column(Boolean, default=False)      # Puede recibir pagos

    # Contrato
    contract_signed_at = Column(DateTime)
    contract_reference = Column(String(100))             # Nro de contrato

    # ── Portal Auth (Épica Partners) ──
    password_hash = Column(String(255), nullable=True)   # Hash bcrypt (migrado desde salt:sha256)
    portal_email = Column(String(200), nullable=True, unique=True, index=True)  # Email de login (default=contact_email)
    onboarding_step = Column(Integer, default=0)         # 0=invited, 1=credentials, 2=profile, 3=stripe_kyc, 4=complete
    onboarding_completed_at = Column(DateTime, nullable=True)
    onboarding_bypass = Column(Boolean, default=False)   # True = salta onboarding, va directo al portal
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    invited_at = Column(DateTime, nullable=True)
    invited_by = Column(String(150), nullable=True)

    # ── 2FA / TOTP (persistido en BD) ──
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    totp_backup_codes = Column(Text, nullable=True)
    totp_backup_codes_used = Column(Text, nullable=True)

    # ── Branding del partner (White-label) ──
    # Cuando un tenant es provisionado por este partner, los emails
    # se envían con el branding del partner en lugar del de SAJET.
    white_label_enabled = Column(Boolean, default=False, nullable=False, server_default="false")  # Habilita marca blanca (requiere plan con WL)
    brand_profile_id = Column(Integer, ForeignKey("partner_branding_profiles.id", ondelete="SET NULL"), nullable=True)  # Perfil de branding activo
    brand_name = Column(String(200), nullable=True)         # Nombre del partner en emails (ej: "TecHeels")
    brand_color_primary = Column(String(10), nullable=True) # Hex primary (ej: "#3498db")
    brand_color_accent = Column(String(10), nullable=True)  # Hex accent (ej: "#2ecc71")
    logo_url = Column(String(500), nullable=True)           # URL pública del logo (PNG/SVG, 200x60px rec.)
    smtp_from_name = Column(String(200), nullable=True)     # "From" name en email (ej: "TecHeels ERP")
    smtp_from_email = Column(String(200), nullable=True)    # "From" email si partner tiene SMTP propio

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    customer = relationship("Customer", foreign_keys=[customer_id], backref="partner_profile")
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
    max_users_override = Column(Integer, nullable=True)               # Override cuota de usuarios
    max_storage_mb_override = Column(Integer, nullable=True)          # Override cuota almacenamiento (MB)
    max_stock_sku_override = Column(Integer, nullable=True)           # Override SKUs con stock real

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
    can_host_tenants = Column(Boolean, default=False, server_default="false")  # Si acepta nuevos tenants
    priority = Column(Integer, default=100)            # Mayor = más prioridad para nuevos tenants
    region = Column(String(50))                        # ej: "us-east", "eu-west"
    
    # Credenciales (encriptadas en producción)
    api_token_id = Column(String(255))                 # ej: "root@pam!onboarding"
    api_token_secret = Column(Text)                    # Token encriptado
    ssh_user = Column(String(50), default="root")
    ssh_password = Column(String(255), nullable=True)  # Contraseña SSH (si no usa key)
    vmid = Column(Integer, nullable=True)              # VMID en Proxmox (para pct exec local)

    # Puerto Odoo del nodo (para multi-nodo, cada nodo puede correr en puerto distinto)
    odoo_port = Column(Integer, default=8069, nullable=True)  # ej: 8069 (CT105), 8089 (PCT161)

    # ── Capacity thresholds ───────────────────────────────────────────────
    cpu_threshold_warning = Column(Float, default=70, server_default="70")
    cpu_threshold_critical = Column(Float, default=90, server_default="90")
    ram_threshold_warning = Column(Float, default=75, server_default="75")
    ram_threshold_critical = Column(Float, default=90, server_default="90")
    storage_threshold_warning = Column(Float, default=70, server_default="70")
    storage_threshold_critical = Column(Float, default=85, server_default="85")

    # ── Odoo tenant capacity policy ───────────────────────────────────────
    tenant_ram_mb = Column(Integer, default=800, server_default="800",
                           comment="RAM estimada por tenant Odoo (MB)")
    system_overhead_mb = Column(Integer, default=1200, server_default="1200",
                                 comment="RAM reservada para sistema (MB)")
    max_tenants_override = Column(Integer, nullable=True,
                                   comment="Límite fijo de tenants (override)")
    storage_type = Column(String(20), default="loop", server_default="loop",
                           comment="loop, zfs, lvm, dir")
    io_max_tenants = Column(Integer, default=8, server_default="8",
                             comment="Máx tenants por límite I/O del storage")
    auto_drain = Column(Boolean, default=False, server_default="false",
                         comment="Excluir de provisioning al superar umbral crítico")
    capacity_score = Column(Float, default=0, server_default="0",
                             comment="Score calculado: 0-100")
    stagger_delay_sec = Column(Integer, default=12, server_default="12",
                                comment="Delay entre arranques de tenants (seg)")

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
    """Relación entre Subscription y LXCContainer - donde está desplegado cada tenant.
    
    Fuente de verdad del runtime activo del tenant. Los campos multi-nodo
    (active_node_id, runtime_mode, routing_mode, backend_host, etc.) permiten
    desacoplar el tenant de un nodo fijo y habilitar migración entre nodos.
    """
    __tablename__ = "tenant_deployments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    container_id = Column(Integer, ForeignKey("lxc_containers.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)  # Vínculo directo cliente↔tunnel
    
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
    
    # ── Multi-nodo: runtime y routing ─────────────────────────────────────
    active_node_id = Column(Integer, ForeignKey("proxmox_nodes.id"), nullable=True, index=True)
    desired_node_id = Column(Integer, ForeignKey("proxmox_nodes.id"), nullable=True)
    runtime_mode = Column(Enum(RuntimeMode), default=RuntimeMode.shared_pool, nullable=False,
                          server_default="shared_pool")
    routing_mode = Column(Enum(RoutingMode), default=RoutingMode.node_proxy, nullable=False,
                          server_default="node_proxy")
    backend_host = Column(String(100))                  # IP del nodo activo (ej: "10.10.10.100")
    http_port = Column(Integer, default=8080)            # Puerto HTTP del backend nginx/dedicado
    chat_port = Column(Integer, default=8072)            # Puerto websocket/longpolling
    service_name = Column(String(150))                   # Nombre systemd (dedicated: "odoo-tenant@acme")
    addons_overlay_path = Column(String(500))            # Path overlay addons (dedicated)
    
    # ── Migración ─────────────────────────────────────────────────────────
    migration_state = Column(Enum(MigrationState), default=MigrationState.idle, nullable=False,
                             server_default="idle")
    
    # ── Health & metadatos ────────────────────────────────────────────────
    last_healthcheck_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)
    
    # Relaciones
    container = relationship("LXCContainer", back_populates="deployments")
    customer = relationship("Customer", foreign_keys=[customer_id], backref="deployments")
    subscription = relationship("Subscription", foreign_keys=[subscription_id])
    custom_domains = relationship("CustomDomain", back_populates="deployment")
    active_node = relationship("ProxmoxNode", foreign_keys=[active_node_id],
                               backref="active_deployments")
    desired_node = relationship("ProxmoxNode", foreign_keys=[desired_node_id])


# ═══════════════════════════════════════════════════════
# INFRA TUNNELS — Túneles de infraestructura (separados de tenants)
# ═══════════════════════════════════════════════════════

class InfraTunnel(Base):
    """
    Túneles de infraestructura Cloudflare compartidos.
    
    Estos son los túneles que conectan PCTs con el exterior a través de Cloudflare.
    NO son tenants — son infraestructura compartida que puede servir a múltiples tenants.
    
    Separados de TenantDeployment para evitar confusión semántica:
    - InfraTunnel = infraestructura compartida (1 tunnel → N tenants)
    - TenantDeployment.tunnel_* = routing del tenant individual
    """
    __tablename__ = "infra_tunnels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)              # ej: "sajet-pct105", "segrd-pct154"
    cloudflare_tunnel_id = Column(String(100), nullable=True)            # UUID del tunnel en CF
    cloudflare_zone_id = Column(String(100), nullable=True)              # Zone ID en CF
    domain = Column(String(200), nullable=False)                         # ej: "sajet.us", "segrd.com"
    hostname_pattern = Column(String(200), nullable=True)                # ej: "*.sajet.us" o "segrd.com"
    target_pct = Column(Integer, nullable=True)                          # PCT destino (ej: 105, 154, 160)
    target_url = Column(String(300), nullable=True)                      # ej: "http://localhost:8069"
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<InfraTunnel {self.name}: {self.domain} → PCT {self.target_pct}>"


class ReservedSubdomain(Base):
    """
    Subdominios reservados que NO deben auto-registrarse como tenants.
    
    Incluye subdominios de infraestructura, servicios internos, 
    y cualquier nombre que no corresponda a una instancia Odoo real.
    
    Consultada por:
    - odoo_db_watcher (antes de crear CNAME)
    - get_all_tenants_from_servers() (antes de auto-registrar Customer)
    - provision_tenant() (antes de crear nuevo tenant)
    """
    __tablename__ = "reserved_subdomains"

    id = Column(Integer, primary_key=True, index=True)
    subdomain = Column(String(100), nullable=False, unique=True, index=True)  # ej: "api", "admin", "n8n"
    reason = Column(String(300), nullable=True)                               # ej: "Tunnel infraestructura PCT 154"
    category = Column(String(50), nullable=False, default="infrastructure")   # infrastructure, service, reserved, system
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ReservedSubdomain {self.subdomain} ({self.category})>"


class TenantMigrationJob(Base):
    """
    Job de migración de un tenant entre nodos.
    
    Cada job trackea una operación de migración completa:
    preflight → preparing_target → warming_target → cutover → verifying → completed/failed
    
    La BD (PostgreSQL 137) es centralizada — solo se migra el runtime + filestore.
    """
    __tablename__ = "tenant_migration_jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(
        Integer, ForeignKey("tenant_deployments.id", ondelete="CASCADE"), nullable=False
    )
    subdomain = Column(String(100), nullable=False)

    # Nodos origen y destino
    source_node_id = Column(Integer, ForeignKey("proxmox_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("proxmox_nodes.id"), nullable=False)

    # Estado de la máquina de estados
    state = Column(
        Enum(MigrationState), nullable=False, default=MigrationState.queued,
        server_default="queued",
    )

    # Modos de runtime (v1: shared_pool → shared_pool solamente)
    source_runtime_mode = Column(String(30), default="shared_pool")
    target_runtime_mode = Column(String(30), default="shared_pool")

    # Quién inició la migración
    initiated_by = Column(String(150), nullable=False)

    # Logging y diagnóstico
    error_log = Column(Text, nullable=True)
    preflight_result = Column(JSON, nullable=True)

    # Filestore metrics
    filestore_size_bytes = Column(BigInteger, nullable=True)
    filestore_synced_at = Column(DateTime, nullable=True)

    # Ventana de corte
    cutover_started_at = Column(DateTime, nullable=True)
    cutover_ended_at = Column(DateTime, nullable=True)

    # Rollback
    rollback_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    deployment = relationship("TenantDeployment", backref="migration_jobs")
    source_node = relationship("ProxmoxNode", foreign_keys=[source_node_id])
    target_node = relationship("ProxmoxNode", foreign_keys=[target_node_id])

    def append_error(self, msg: str) -> None:
        """Agrega un mensaje al log de errores acumulado."""
        ts = datetime.utcnow().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.error_log = f"{self.error_log}\n{entry}" if self.error_log else entry


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
    
    # Subdominio SAJET del tenant. Puede ser compartido por múltiples dominios
    # externos del mismo cliente.
    sajet_subdomain = Column(String(100), nullable=False, index=True)  # ej: "impulse-max"
    
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
    billing_period_key = Column(String(80), nullable=True, index=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

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

    # ── Épica 9: Blueprint + Aprobación de módulos ──────────────────────────
    blueprint_package_id = Column(Integer, ForeignKey("module_packages.id"), nullable=True)
    selected_modules = Column(JSON, nullable=True)      # technical_names elegidos por cliente/partner
    approved_modules = Column(JSON, nullable=True)      # aprobados por Jeturing
    rejected_modules = Column(JSON, nullable=True)      # rechazados por Jeturing
    tenant_admin_email = Column(String(200), nullable=True)
    tenant_admin_password = Column(String(200), nullable=True)
    tenant_user_email = Column(String(200), nullable=True)
    tenant_user_password = Column(String(200), nullable=True)

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
    portal_url = Column(String(500), nullable=True)        # URL del portal del partner (ej: erp.miempresa.com)
    custom_domain = Column(String(255), nullable=True, unique=True)  # Dominio custom para branding resolution
    terms_url = Column(String(500), nullable=True)         # URL a términos de servicio del partner
    privacy_url = Column(String(500), nullable=True)       # URL a política de privacidad del partner
    custom_css = Column(Text, nullable=True)               # CSS adicional
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    partner = relationship("Partner", backref="branding_profile", foreign_keys="[PartnerBrandingProfile.partner_id]")


# ═══════════════════════════════════════════════════════
# ONBOARDING CONFIG — Admin-configurable onboarding flow
# ═══════════════════════════════════════════════════════

class OnboardingConfig(Base):
    """
    Configuración de onboarding editable por admin.
    Define pasos visibles, planes mostrados, menú del portal y textos.
    """
    __tablename__ = "onboarding_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False)    # 'default', 'partner_referred', etc.
    display_name = Column(String(200), nullable=False, default='Onboarding Principal')

    # Steps: [{step, key, label, required, visible, condition}]
    steps_config = Column(JSON, nullable=False, default=list)
    # Plans shown in onboarding/portal pricing section
    visible_plans = Column(JSON, nullable=False, default=list)
    # Tenant portal menu: [{key, label, icon, visible, order}]
    portal_menu = Column(JSON, nullable=False, default=list)

    # Welcome texts
    welcome_title = Column(String(300), default='¡Bienvenido a Sajet ERP!')
    welcome_subtitle = Column(String(500), default='Configure su cuenta para comenzar.')

    # Account management toggles
    allow_plan_change = Column(Boolean, default=True)
    allow_cancel = Column(Boolean, default=True)
    allow_email_change = Column(Boolean, default=False)
    show_invoices = Column(Boolean, default=True)
    show_usage = Column(Boolean, default=True)

    # Countries that require e-CF questionnaire
    ecf_countries = Column(JSON, nullable=False, default=lambda: ["DO"])

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════
# REFRESH TOKENS — Persistencia en BD (reemplaza memoria)
# ═══════════════════════════════════════════════════════

class RefreshToken(Base):
    """
    Refresh tokens almacenados en BD para sobrevivir reinicios.
    Se guarda el SHA-256 del token opaco, nunca el token en claro.
    """
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    username = Column(String(150), nullable=False, index=True)
    role = Column(String(30), nullable=False)
    user_id = Column(Integer, nullable=True)
    tenant_id = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ═══════════════════════════════════════════════════════
# EMAIL LOG — Historial de emails transaccionales
# ═══════════════════════════════════════════════════════

class EmailLog(Base):
    """
    Registro de cada email transaccional enviado por el sistema.
    Permite historial, reenvío y diagnóstico de entregas.
    """
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    subject = Column(String(500))
    email_type = Column(String(80), nullable=False)   # credentials, reset, commission, work_order, quotation, etc.
    status = Column(String(20), default="sent")        # sent, failed, pending
    error_message = Column(Text, nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=True)
    related_id = Column(Integer, nullable=True)        # ID del objeto relacionado (work_order, commission, etc.)
    sent_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", foreign_keys=[customer_id])
    partner = relationship("Partner", foreign_keys=[partner_id])


class PostalEmailUsage(Base):
    """
    Registro de uso de correo enviado via Postal por tenant.

    Cada fila representa un lote de emails de un tenant en un período.
    Permite:
      - Billing de uso: cobrar al tenant por emails enviados
      - Auditoría: historial de volumen por tenant
      - Límites: bloquear envíos si supera el plan

    Fuente de datos:
      - Webhooks de Postal → POST /api/v1/webhooks/postal-delivery
      - O polling periódico de la API de Postal por servidor/organización
    """
    __tablename__ = "postal_email_usage"

    id = Column(Integer, primary_key=True, index=True)
    # Tenant y período
    tenant_subdomain = Column(String(100), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    period_year  = Column(Integer, nullable=False)     # YYYY
    period_month = Column(Integer, nullable=False)     # 1–12
    # Métricas de envío
    emails_sent = Column(Integer, default=0, nullable=False)
    emails_delivered = Column(Integer, default=0, nullable=False)
    emails_bounced  = Column(Integer, default=0, nullable=False)
    emails_failed   = Column(Integer, default=0, nullable=False)
    # Costo calculado
    cost_per_email  = Column(Float, default=0.00020, nullable=False)   # USD por email
    total_cost_usd  = Column(Float, default=0.0, nullable=False)       # emails_sent * cost_per_email
    # Fuente del dato
    postal_server_token = Column(String(50), nullable=True)            # token del servidor Postal
    last_synced_at = Column(DateTime, nullable=True)
    # Control
    is_billed = Column(Boolean, default=False, nullable=False)         # True cuando se incluyó en factura
    billed_at  = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_subdomain", "period_year", "period_month",
                         name="uq_postal_usage_tenant_period"),
    )

    customer = relationship("Customer", foreign_keys=[customer_id])


# ═══════════════════════════════════════════════════════
# TESTIMONIALS — Gestionables desde Admin
# ═══════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════
# ACCOUNTANT TENANT ACCESS — Multi-empresa para contadores
# ═══════════════════════════════════════════════════════

class AccountantAccessLevel(enum.Enum):
    readonly = "readonly"           # Solo lectura de contabilidad
    readwrite = "readwrite"         # Lectura/escritura (conciliación, asientos)
    full = "full"                   # Acceso completo al módulo contable


class AccountantTenantAccess(Base):
    """
    Tabla N:N que vincula un usuario-contador con múltiples tenants (clientes).
    Permite al contador acceder a la contabilidad de sus clientes sin ser
    usuario directo del tenant.
    """
    __tablename__ = "accountant_tenant_access"

    id = Column(Integer, primary_key=True, index=True)
    accountant_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    access_level = Column(Enum(AccountantAccessLevel), default=AccountantAccessLevel.readonly)
    granted_by = Column(String(200), nullable=True)          # Quién otorgó el acceso
    is_active = Column(Boolean, default=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("accountant_id", "tenant_id", name="uq_accountant_tenant"),
    )

    accountant = relationship("Customer", foreign_keys=[accountant_id], backref="accountant_clients")
    tenant = relationship("Customer", foreign_keys=[tenant_id], backref="accountant_advisors")


# ═══════════════════════════════════════════════════════
# LANDING PAGE i18n — Testimonials, Sections, Translations
# ═══════════════════════════════════════════════════════

class Testimonial(Base):
    """
    Testimonios de clientes — versiones en diferentes idiomas.
    Gestionables desde panel admin, con soporte para múltiples idiomas.
    """
    __tablename__ = "testimonials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    role = Column(String(150), nullable=True)
    company = Column(String(200), nullable=True)
    text = Column(Text, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    locale = Column(String(10), nullable=False, default="en")  # "en" | "es"
    featured = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_testimonials_locale', 'locale'),
        Index('ix_testimonials_featured', 'featured'),
    )


class LandingSection(Base):
    """
    Secciones de contenido para la landing page — gestionables desde admin.
    Permite al equipo de marketing cambiar textos, CTAs, badges sin tocar código.
    
    Estructura: (section_key, locale) = unique composite
    Ej: ("hero", "en"), ("hero", "es"), ("features", "en"), etc.
    """
    __tablename__ = "landing_sections"

    id = Column(Integer, primary_key=True, index=True)
    section_key = Column(String(100), nullable=False)  # "hero", "features", "pricing", "accountants", etc.
    locale = Column(String(10), nullable=False, default="en")  # "en" | "es"
    title = Column(String(300), nullable=True)
    content = Column(Text, nullable=True)
    meta_description = Column(String(500), nullable=True)
    meta_keywords = Column(String(300), nullable=True)
    og_title = Column(String(300), nullable=True)
    og_description = Column(String(500), nullable=True)
    og_image_url = Column(String(500), nullable=True)
    structured_data = Column(JSON, nullable=True)  # schema.org JSON-LD
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('section_key', 'locale', name='uq_landing_section_key_locale'),
        Index('ix_landing_sections_key', 'section_key'),
        Index('ix_landing_sections_locale', 'locale'),
    )


class Translation(Base):
    """
    Traducciones gestionables por admin — para strings CMS que vayan más allá del archivo estático.
    Estructura: (key, locale) = unique composite
    Ej: ("landing.hero.badge", "en"), ("landing.hero.badge", "es")
    """
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False)  # Ej: "landing.hero.badge", "landing.seo.title"
    locale = Column(String(10), nullable=False, default="en")  # "en" | "es"
    value = Column(Text, nullable=False)
    context = Column(String(100), nullable=True)  # "landing" | "seo" | "footer" | "pricing" para agrupar
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(150), nullable=True)
    created_by = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('key', 'locale', name='uq_translation_key_locale'),
        Index('ix_translations_key', 'key'),
        Index('ix_translations_locale', 'locale'),
        Index('ix_translations_context', 'context'),
        Index('ix_translations_approved', 'is_approved'),
        Index('ix_translations_updated', 'updated_at'),
    )


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
        try:
            from ..config import invalidate_runtime_config_cache
            invalidate_runtime_config_cache(key)
        except Exception:
            pass
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

class StorageAlert(Base):
    """Alertas de almacenamiento para tenants — Notificaciones antes de agotar límite"""
    __tablename__ = "storage_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    customer = relationship("Customer", backref="storage_alerts")
    
    # Status de la alerta
    status = Column(Enum(StorageAlertStatus), nullable=False)  # warning (75%), critical (90%), exceeded (100%)
    usage_percent = Column(Float, nullable=False)  # % actual de uso
    storage_limit_mb = Column(Integer, nullable=False)  # Límite en MB
    current_usage_mb = Column(Float, nullable=False)  # Consumo actual en MB
    
    # Notificación
    email_sent = Column(Boolean, default=False, nullable=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_recipient = Column(String(255), nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)  # Cuando el uso bajó de la alerta
    
    __table_args__ = (
        Index("idx_storage_alerts_customer_status", customer_id, status),
    )
    
    def __repr__(self):
        return f"<StorageAlert {self.customer_id} {self.status.value} ({self.usage_percent:.1f}%)>"


def get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


# ═══════════════════════════════════════════════════════
# MODELO — API Keys (Épica API Keys)
# ═══════════════════════════════════════════════════════

# Límites por tier (referencia estática, también en el router)
API_KEY_TIER_LIMITS = {
    "free":       {"rpm": 10,   "rpd": 100,     "rpm_tokens": 10_000,  "rpm_month": None},
    "standard":   {"rpm": 60,   "rpd": 10_000,  "rpm_tokens": 100_000, "rpm_month": None},
    "pro":        {"rpm": 300,  "rpd": 100_000, "rpm_tokens": 500_000, "rpm_month": None},
    "enterprise": {"rpm": 2000, "rpd": None,    "rpm_tokens": None,    "rpm_month": None},
}


class ApiKey(Base):
    """
    API Key estilo Stripe: prefix visible, secreto hasheado.
    Formato:  sk_live_<key_id>_<secret>
              ^^^^^^^^^^^^^^^^ solo esto se muestra post-creación
    """
    __tablename__ = "api_keys"

    id            = Column(Integer, primary_key=True, index=True)
    key_id        = Column(String(32),  unique=True, nullable=False, index=True)  # "sk_live_ABC123XYZ..."
    key_hash      = Column(String(128), nullable=False)                            # SHA-256 del key completo
    name          = Column(String(255), nullable=False)
    description   = Column(Text, nullable=True)

    # Ownership
    tenant_id     = Column(Integer, ForeignKey("tenant_deployments.id"), nullable=True, index=True)
    customer_id   = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    created_by    = Column(Integer, nullable=True)   # admin_user id (no FK para evitar cascade)

    # Estado
    status        = Column(Enum(ApiKeyStatus),   nullable=False, default=ApiKeyStatus.active)
    scope         = Column(Enum(ApiKeyScope),     nullable=False, default=ApiKeyScope.read_only)
    tier          = Column(Enum(ApiKeyTier),      nullable=False, default=ApiKeyTier.standard)

    # Permisos granulares opcionales (lista: ["tenants:read", "billing:read"])
    permissions   = Column(JSON, nullable=False, default=list)

    # Rate limits (override del tier — null = usa los del tier)
    requests_per_minute  = Column(Integer, nullable=True)
    requests_per_day     = Column(Integer, nullable=True)
    monthly_quota_tokens = Column(Integer, nullable=True)

    # Contadores de uso (se resetean por cron diario/mensual)
    usage_today          = Column(Integer, nullable=False, default=0)
    usage_this_month     = Column(Integer, nullable=False, default=0)
    total_requests       = Column(Integer, nullable=False, default=0)
    last_used_at         = Column(DateTime, nullable=True)
    last_used_ip         = Column(String(45), nullable=True)

    # Ciclo de vida
    expires_at           = Column(DateTime, nullable=True)
    created_at           = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at           = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    rotated_at           = Column(DateTime, nullable=True)
    rotation_old_key_id  = Column(String(32), nullable=True)  # key_id anterior en rotación

    # Metadata libre
    tags          = Column(JSON, nullable=False, default=list)   # ["prod", "internal"]
    metadata_     = Column("metadata", JSON, nullable=False, default=dict)

    __table_args__ = (
        Index("idx_api_keys_status_tier", "status", "tier"),
        Index("idx_api_keys_customer", "customer_id", "status"),
        Index("idx_api_keys_tenant", "tenant_id", "status"),
    )

    def __repr__(self):
        return f"<ApiKey {self.key_id!r} [{self.tier.value}/{self.status.value}]>"


class ApiKeyUsageLog(Base):
    """
    Log de requests por API key — granularidad por hora para billing.
    """
    __tablename__ = "api_key_usage_logs"

    id         = Column(Integer, primary_key=True, index=True)
    key_id     = Column(String(32), nullable=False, index=True)   # FK lógica a api_keys.key_id
    hour_bucket = Column(DateTime, nullable=False)                 # truncado a la hora (2025-01-10 14:00:00)
    request_count = Column(Integer, nullable=False, default=0)
    token_count   = Column(Integer, nullable=False, default=0)
    error_count   = Column(Integer, nullable=False, default=0)
    endpoint      = Column(String(255), nullable=True)
    ip_address    = Column(String(45), nullable=True)

    __table_args__ = (
        UniqueConstraint("key_id", "hour_bucket", "endpoint", name="uq_usage_key_hour_endpoint"),
        Index("idx_usage_key_bucket", "key_id", "hour_bucket"),
    )


# ── Solicitud de rotación iniciada por el tenant (flujo de soporte) ──────────

class ApiKeyRotationStatus(enum.Enum):
    pending  = "pending"   # Tenant solicitó; soporte aún no ejecutó
    approved = "approved"  # Soporte ejecutó la rotación
    rejected = "rejected"  # Soporte rechazó
    expired  = "expired"   # Pasó el TTL sin resolver


class ApiKeyRotationRequest(Base):
    """
    Solicitud de rotación iniciada desde el módulo de correo del tenant.
    El rol 'support' SOLO puede ejecutar rotate si existe un request pending
    asociado al mismo tenant y key_id. El token de verificación viaja
    en el email al tenant y debe incluirse en la llamada de soporte.
    """
    __tablename__ = "api_key_rotation_requests"

    id          = Column(Integer, primary_key=True, index=True)
    key_id      = Column(String(32),  nullable=False, index=True)   # api_keys.key_id
    tenant_id   = Column(Integer, ForeignKey("tenant_deployments.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    # Token de verificación firmado — viaja en el email del tenant
    verify_token = Column(String(64), nullable=False, unique=True)

    status      = Column(Enum(ApiKeyRotationStatus), nullable=False, default=ApiKeyRotationStatus.pending)
    requested_by_email = Column(String(255), nullable=False)   # email del usuario tenant
    support_user_id    = Column(Integer, nullable=True)        # quién del equipo ejecutó

    reason      = Column(Text, nullable=True)       # nota del tenant
    reject_note = Column(Text, nullable=True)       # nota del soporte si rechaza

    created_at  = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at  = Column(DateTime, nullable=False)  # TTL: 24h desde creación
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_rotation_req_key_status", "key_id", "status"),
        Index("idx_rotation_req_tenant",     "tenant_id", "status"),
    )


# ═══════════════════════════════════════════════════════
# DSAM — Dynamic Session & Anti-Theft Monitor
# ═══════════════════════════════════════════════════════

class SessionRuleType(enum.Enum):
    """Tipo de regla de seguridad de sesión."""
    SINGLE_SESSION = "single_session"              # Solo 1 sesión por usuario
    MAX_SESSIONS = "max_sessions"                  # Máximo N sesiones
    GEO_RESTRICTION = "geo_restriction"            # Solo ciertos países
    IMPOSSIBLE_TRAVEL = "impossible_travel"         # Distancia imposible en tiempo
    IP_WHITELIST = "ip_whitelist"                   # Solo IPs permitidas
    TIME_RESTRICTION = "time_restriction"           # Solo en horario laboral


class SessionActionType(enum.Enum):
    """Acciones de seguridad sobre cuentas."""
    SESSION_TERMINATED = "session_terminated"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SECURITY_ALERT = "security_alert"
    IMPOSSIBLE_TRAVEL_DETECTED = "impossible_travel_detected"
    CONCURRENT_SESSION_BLOCKED = "concurrent_session_blocked"
    RULE_VIOLATION = "rule_violation"


class SessionAlertSeverity(enum.Enum):
    """Severidad de la alerta."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActiveSession(Base):
    """
    Snapshot de sesión activa capturada desde Redis.
    Se actualiza periódicamente vía cron (cada 60s).
    Permite visualizar sesiones en dashboard sin leer Redis en cada request.
    """
    __tablename__ = "active_sessions"

    id = Column(Integer, primary_key=True, index=True)
    redis_session_key = Column(String(255), unique=True, nullable=False)

    # Datos del usuario/tenant
    tenant_db = Column(String(100), nullable=False, index=True)
    odoo_uid = Column(Integer, nullable=True)
    odoo_login = Column(String(150), nullable=True, index=True)
    user_display_name = Column(String(255), nullable=True)

    # Datos de conexión
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)

    # Geolocalización (GeoIP2)
    geo_country = Column(String(100), nullable=True)
    geo_country_code = Column(String(3), nullable=True, index=True)
    geo_region = Column(String(100), nullable=True)
    geo_city = Column(String(100), nullable=True)
    geo_lat = Column(Float, nullable=True)
    geo_lon = Column(Float, nullable=True)

    # Timestamps
    session_start = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, nullable=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_polled_at = Column(DateTime, default=datetime.utcnow)

    # Estado
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_active_sessions_tenant_user", "tenant_db", "odoo_login"),
        Index("ix_active_sessions_country", "geo_country_code"),
        Index("ix_active_sessions_active", "is_active", "tenant_db"),
    )


class SessionSecurityRule(Base):
    """
    Regla de seguridad configurable por tenant o global.
    Permite aplicar restricciones dinámicas por tenant.
    """
    __tablename__ = "session_security_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(Enum(SessionRuleType), nullable=False)
    tenant_db = Column(String(100), nullable=True, index=True)   # null = global (aplica a todos)
    is_enabled = Column(Boolean, default=True)

    # Configuración específica por tipo de regla (JSON flexible)
    config = Column(JSON, nullable=False, default=dict)
    # Ejemplos de config por rule_type:
    # SINGLE_SESSION:    {"allow_override_users": ["admin@sajet.us"]}
    # MAX_SESSIONS:      {"max": 3}
    # GEO_RESTRICTION:   {"allowed_countries": ["DO", "US", "ES"]}
    # IMPOSSIBLE_TRAVEL: {"min_hours": 3, "min_distance_km": 500}
    # IP_WHITELIST:      {"allowed_ips": ["10.10.10.0/24", "192.168.1.0/24"]}
    # TIME_RESTRICTION:  {"tz": "America/Santo_Domingo", "start": "07:00", "end": "22:00"}

    # Excepciones: usuarios o tenants que pueden ignorar la regla
    exempt_users = Column(JSON, default=list)   # ["admin@sajet.us", "root@tenant.com"]
    exempt_tenants = Column(JSON, default=list) # ["cliente1", "jeturing"]

    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_sec_rules_type_tenant", "rule_type", "tenant_db"),
    )


class SessionGeoEvent(Base):
    """
    Historial de accesos geográficos por usuario.
    Alimenta el mapa de calor y la detección de viaje imposible.
    """
    __tablename__ = "session_geo_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_db = Column(String(100), nullable=False, index=True)
    odoo_login = Column(String(150), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)

    # Geolocalización
    geo_country = Column(String(100), nullable=True)
    geo_country_code = Column(String(3), nullable=True)
    geo_region = Column(String(100), nullable=True)
    geo_city = Column(String(100), nullable=True)
    geo_lat = Column(Float, nullable=True)
    geo_lon = Column(Float, nullable=True)

    # User Agent parsed
    device_type = Column(String(20), nullable=True)   # desktop, mobile, tablet
    browser = Column(String(50), nullable=True)
    os_name = Column(String(50), nullable=True)

    event_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_geo_events_user_time", "tenant_db", "odoo_login", "event_at"),
        Index("ix_geo_events_country", "geo_country_code", "event_at"),
    )


class AccountSecurityAction(Base):
    """
    Log de acciones de seguridad tomadas (bloqueos, terminaciones, alertas).
    Playbook estilo Steam Guard para soporte técnico.
    """
    __tablename__ = "account_security_actions"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(Enum(SessionActionType), nullable=False)
    severity = Column(Enum(SessionAlertSeverity), default=SessionAlertSeverity.MEDIUM)

    # Target
    tenant_db = Column(String(100), nullable=False, index=True)
    odoo_login = Column(String(150), nullable=True)
    odoo_uid = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Detalles del evento
    details = Column(JSON, default=dict)
    # Ejemplo: {"reason": "Concurrent login from US while active in DO",
    #           "session_terminated": "session:cliente1:abc123",
    #           "previous_location": {"country": "DO", "city": "Santo Domingo"},
    #           "new_location": {"country": "US", "city": "Miami"}}

    # Quién tomó la acción (null = sistema automático)
    actor_id = Column(Integer, nullable=True)            # admin_users.id
    actor_username = Column(String(150), nullable=True)  # email del admin/support

    # Resolución
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(150), nullable=True)
    resolution_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_sec_actions_tenant_time", "tenant_db", "created_at"),
        Index("ix_sec_actions_type_sev", "action_type", "severity"),
        Index("ix_sec_actions_unresolved", "resolved", "severity"),
    )


class TenantSessionConfig(Base):
    """
    Configuración de sesión por tenant.
    Permite habilitar/deshabilitar funcionalidades DSAM por tenant.
    """
    __tablename__ = "tenant_session_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_db = Column(String(100), unique=True, nullable=False, index=True)

    # Permisos del tenant
    allow_multiple_sessions = Column(Boolean, default=False)
    max_concurrent_sessions = Column(Integer, default=1)
    enforce_geo_restrictions = Column(Boolean, default=False)
    enforce_impossible_travel = Column(Boolean, default=True)

    # Configuración
    allowed_countries = Column(JSON, default=list)    # ["DO", "US"] o [] = sin restricción
    session_timeout_minutes = Column(Integer, default=480)  # 8 horas default
    notify_on_new_device = Column(Boolean, default=True)

    # Seat audit
    seat_audit_enabled = Column(Boolean, default=True)
    last_seat_audit_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


# ═══════════════════════════════════════════════════════
# ÉPICA 10: Payments & Treasury — Payouts, KYC, Events
# ═══════════════════════════════════════════════════════

class PayoutStatus(enum.Enum):
    pending = "pending"
    authorized = "authorized"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"
    rejected = "rejected"


class KYCStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class PayoutRequest(Base):
    """
    Solicitud de dispersión a proveedor vía Mercury.
    Flujo: pending → authorized → processing → completed/failed
    """
    __tablename__ = "payout_requests"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    provider_account_id = Column(Integer, ForeignKey("provider_accounts.id"), nullable=True)

    # Montos
    gross_amount = Column(Float, nullable=False)
    jeturing_commission_pct = Column(Float, default=15.0)
    jeturing_commission = Column(Float, default=0)
    mercury_fee = Column(Float, default=0)
    net_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    # Transferencia Mercury
    transfer_type = Column(String(10), default="ach")  # ach | wire
    mercury_transfer_id = Column(String(100), nullable=True, index=True)
    estimated_delivery = Column(DateTime, nullable=True)

    # Estado y auditoría
    status = Column(Enum(PayoutStatus), default=PayoutStatus.pending, index=True)
    notes = Column(Text, nullable=True)
    authorized_by = Column(String(150), nullable=True)
    authorized_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_payout_partner_status", "partner_id", "status"),
        Index("ix_payout_created", "created_at"),
    )

    # Relaciones
    partner = relationship("Partner")
    invoice = relationship("Invoice")


class ProviderAccount(Base):
    """
    Cuenta bancaria registrada para un proveedor (partner).
    Los datos sensibles se almacenan cifrados.
    """
    __tablename__ = "provider_accounts"

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True)

    account_holder_name = Column(String(200), nullable=False)
    account_number_masked = Column(String(20), nullable=False)   # ****5678
    account_number_enc = Column(Text, nullable=True)              # encrypted full number
    routing_number = Column(String(20), nullable=False)
    account_type = Column(String(10), default="checking")         # checking | savings
    bank_name = Column(String(200), nullable=True)

    # KYC
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.pending, index=True)
    kyc_verified_at = Column(DateTime, nullable=True)
    kyc_notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    partner = relationship("Partner")


class PaymentEvent(Base):
    """
    Log de auditoría de eventos de pago (pagos recibidos, payouts, transferencias).
    Inmutable — solo INSERT, nunca UPDATE/DELETE.
    """
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # invoice_paid, payout_requested, etc.
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    payout_id = Column(Integer, ForeignKey("payout_requests.id"), nullable=True)
    amount = Column(Float, nullable=True)
    metadata_json = Column(JSON, default=dict)
    actor = Column(String(150), nullable=True)  # email del admin que ejecutó la acción

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_payment_events_type_time", "event_type", "created_at"),
    )
