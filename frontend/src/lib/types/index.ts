// Shared frontend types for ERP Core SPA

export type UserRole = 'admin' | 'operator' | 'viewer' | 'tenant' | 'partner';

export interface User {
  id?: number;
  user_id?: number | null;
  tenant_id?: number | null;
  partner_id?: number | null;
  admin_user_id?: number | null;
  username: string;
  email: string;
  role: UserRole;
  display_name?: string;
  is_active?: boolean;
  created_at?: string;
  company_name?: string;
  full_name?: string;
  plan?: 'basic' | 'pro' | 'enterprise' | string;
  // Partner-specific
  onboarding_step?: number;
  stripe_connected?: boolean;
  commission_rate?: number;
}

// ── Partner Portal Types ──

export interface PartnerOnboardingStatus {
  current_step: number;
  steps: Array<{
    step: number;
    name: string;
    label: string;
    completed: boolean;
  }>;
  completed: boolean;
  completed_at: string | null;
  stripe_account_id: string | null;
  stripe_onboarding_complete: boolean;
  stripe_charges_enabled: boolean;
  stripe_payouts_enabled: boolean;
  stripe_requirements: string[];
  stripe_disabled_reason: string | null;
  billing_scenario: string | null;
  contract_signed_at: string | null;
  can_skip_stripe: boolean;
  settlement_mode: 'domestic' | 'cross_border';
}

export interface PartnerDashboard {
  partner: {
    id: number;
    company_name: string;
    status: string;
    commission_rate: number;
    onboarding_step: number;
    stripe_onboarding_complete: boolean;
    stripe_charges_enabled: boolean;
  };
  kpis: {
    total_leads: number;
    active_leads: number;
    won_leads: number;
    conversion_rate: number;
    active_clients: number;
    total_earned: number;
    pending_commissions: number;
    paid_commissions: number;
    estimated_pipeline: number;
  };
  stripe_balance: {
    success: boolean;
    available: number;
    pending: number;
  } | null;
}

export interface PartnerLeadItem {
  id: number;
  company_name: string;
  contact_name: string | null;
  contact_email: string | null;
  phone: string | null;
  country: string | null;
  status: string | null;
  estimated_monthly_value: number;
  notes: string | null;
  registered_at: string | null;
  updated_at: string | null;
}

export interface PartnerLeadsResponse {
  items: PartnerLeadItem[];
  total: number;
  pipeline: Record<string, number>;
}

export interface PartnerDeploymentPhase {
  key: string;
  label: string;
  week: number;
  target: number;
}

export interface PartnerDeploymentChecklistItem {
  key: string;
  label: string;
  phase: string;
  done: boolean;
}

export interface PartnerDeploymentEvent {
  event: string;
  detail: Record<string, unknown>;
  at: string;
}

export interface PartnerDeploymentItem {
  id: number;
  lead_id: number | null;
  customer_id: number | null;
  subscription_id: number | null;
  tenant_deployment_id: number | null;
  invoice_id: number | null;
  company_name: string;
  contact_name: string | null;
  contact_email: string;
  phone: string | null;
  country_code: string | null;
  subdomain: string;
  tenant_url: string | null;
  plan_name: string;
  user_count: number;
  is_running: boolean;
  billing_mode: string;
  industry: string | null;
  blueprint_package_name: string | null;
  package_snapshot: {
    id?: number;
    name?: string;
    display_name?: string;
    description?: string | null;
    module_list?: string[];
    module_count?: number;
    base_price_monthly?: number;
  };
  kpis: Array<Record<string, unknown>>;
  checklist: PartnerDeploymentChecklistItem[];
  events: PartnerDeploymentEvent[];
  phase: string;
  week: number;
  progress_percent: number;
  status: string;
  provisioning_status: string;
  invoice_status: string;
  handoff_status: string;
  last_error: string | null;
  started_at: string | null;
  tenant_ready_at: string | null;
  invoiced_at: string | null;
  completed_at: string | null;
  availability_test: {
    status: string;
    ok?: boolean;
    url?: string;
    status_code?: number;
    error?: string;
    reason?: string;
  } | null;
  invoice: {
    id: number;
    invoice_number: string;
    total: number;
    currency: string;
    status: string | null;
    payment_url: string | null;
    download_url: string | null;
    view_url: string | null;
  } | null;
  phases: PartnerDeploymentPhase[];
}

export interface PartnerDeploymentsResponse {
  items: PartnerDeploymentItem[];
  total: number;
  summary: {
    total: number;
    active: number;
    in_progress: number;
    blocked: number;
    avg_progress: number;
    pipeline: Record<string, number>;
  };
  phases: PartnerDeploymentPhase[];
}

export interface BlueprintPackageItem {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  plan_type: string | null;
  base_price_monthly: number;
  is_default: boolean;
  is_active: boolean;
  module_list: string[];
  module_count: number;
  partner_allowed?: boolean;
}

export interface PartnerClientItem {
  subscription_id: number;
  customer_id: number;
  company_name: string;
  contact_name?: string | null;
  email: string;
  phone?: string | null;
  country?: string | null;
  notes?: string | null;
  subdomain?: string | null;
  plan: string;
  status: string | null;
  billing_mode: string | null;
  monthly_amount: number;
  user_count: number;
  created_at: string | null;
  updated_at?: string | null;
}

export interface PartnerCommissionItem {
  id: number;
  period_start: string | null;
  period_end: string | null;
  gross_revenue: number;
  net_revenue: number;
  partner_amount: number;
  jeturing_amount: number;
  status: string | null;
  paid_at: string | null;
  payment_reference: string | null;
}

export interface PartnerProfile {
  id: number;
  company_name: string;
  legal_name: string | null;
  tax_id: string | null;
  contact_name: string | null;
  contact_email: string;
  portal_email: string | null;
  phone: string | null;
  country: string | null;
  address: string | null;
  billing_scenario: string | null;
  commission_rate: number;
  status: string | null;
  stripe_account_id: string | null;
  stripe_onboarding_complete: boolean;
  stripe_charges_enabled: boolean;
  onboarding_step: number;
  contract_signed_at: string | null;
  contract_reference: string | null;
  created_at: string | null;
}

export interface LoginRequest {
  username: string;
  password: string;
  totp_code?: string;
  email_verify_code?: string;
}

export interface LoginResponse {
  message: string;
  role: UserRole;
  requires_totp: boolean;
  requires_email_verify: boolean;
  redirect_url?: string | null;
  user_id?: number | null;
}

// ── Agreement Types ──

export type AgreementType = 'nda' | 'service_agreement' | 'terms_of_service' | 'privacy_policy';
export type AgreementTarget = 'partner' | 'customer' | 'both';

export interface AgreementTemplate {
  id: number;
  agreement_type: AgreementType;
  target: AgreementTarget;
  title: string;
  version: string;
  html_content: string;
  is_active: boolean;
  is_required: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface SignedAgreement {
  id: number;
  template_id: number;
  template_title?: string;
  template_type?: AgreementType;
  partner_id: number | null;
  customer_id: number | null;
  signer_name: string;
  signer_email?: string;
  document_hash: string;
  pdf_path: string | null;
  signed_at: string;
}

export interface AgreementTemplatesResponse {
  items: AgreementTemplate[];
  total: number;
}

export interface SignedAgreementsResponse {
  items: SignedAgreement[];
  total: number;
}

// ── Developer Portal Types ──

export type DeveloperAppMode = 'test' | 'production';

export type DeveloperAppStatusValue =
  | 'created'
  | 'org_linked'
  | 'agreements_pending'
  | 'sandbox_granted'
  | 'verification_requested'
  | 'verified'
  | 'rejected';

export type AgreementFlowStatus =
  | 'generated'
  | 'pending'
  | 'viewed'
  | 'in_review'
  | 'signed'
  | 'rejected';

export interface DeveloperApp {
  id: number;
  name: string;
  description: string | null;
  api_suite: string;
  app_mode: DeveloperAppMode;
  status: DeveloperAppStatusValue;
  organization_name: string | null;
  organization_linked: boolean;
  sandbox_access: boolean;
  webhook_url: string | null;
  client_id: string | null;
  created_by: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DeveloperAgreementFlowItem {
  id: number;
  template_id: number;
  template_title: string | null;
  template_type: string | null;
  status: AgreementFlowStatus;
  generated_at: string | null;
  viewed_at: string | null;
  submitted_at: string | null;
  signed_at: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
  has_pdf_preview: boolean;
  signed_agreement_id: number | null;
}

export interface DeveloperAppProgress {
  app_created: boolean;
  org_linked: boolean;
  agreements_signed: boolean;
  sandbox_access: boolean;
  verification_requested: boolean;
  verified: boolean;
}

export interface DeveloperAppSummary extends DeveloperApp {
  progress: DeveloperAppProgress;
  agreements: DeveloperAgreementFlowItem[];
  agreements_total: number;
  agreements_signed: number;
}

export interface DeveloperAgreementFlow {
  id: number;
  app_id: number;
  template_id: number;
  template_title: string | null;
  template_type: string | null;
  template_version: string | null;
  html_content: string;
  status: AgreementFlowStatus;
  generated_at: string | null;
  viewed_at: string | null;
  submitted_at: string | null;
  signed_at: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
  has_pdf_preview: boolean;
  signed_agreement_id: number | null;
}

export type DeveloperApiSuiteTargetType = 'api' | 'bda' | 'route' | 'webhook' | 'other';

export interface DeveloperApiSuite {
  code: string;
  name: string;
  description?: string;
  target_type: DeveloperApiSuiteTargetType;
  target?: string;
  enabled: boolean;
  is_builtin?: boolean;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface Tenant {
  id: number;
  company_name: string;
  email: string;
  subdomain: string;
  plan: 'basic' | 'pro' | 'enterprise' | string;
  status: 'active' | 'provisioning' | 'pending' | 'payment_failed' | 'suspended' | string;
  tunnel_active?: boolean;
  server?: string;
  server_id?: string;
  node_name?: string | null;
  backend_host?: string | null;
  created_at?: string | null;
  url?: string;
  partner_id?: number | null;
  partner_name?: string | null;
  monthly_amount?: number;
  user_count?: number;
  billing_mode?: string | null;
  deployment?: TenantDeploymentSummary | null;
}

export interface TenantListResponse {
  items: Tenant[];
  total: number;
}

export interface DashboardMetrics {
  total_revenue: number;
  active_tenants: number;
  pending_setup: number;
  cluster_load: {
    cpu: number;
    ram: number;
  };
}

export interface BillingMetrics {
  mrr_total: number;
  month_revenue: number;
  pending_amount: number;
  pending_count: number;
  churn_rate: number;
  total_active: number;
  total_pending: number;
  cancelled_30d: number;
  total_users?: number;
  plan_distribution: {
    [key: string]: { count: number; revenue: number };
  };
}

export interface BillingSubscriptionItem {
  id: number;
  customer_id: number;
  company_name: string;
  email: string;
  subdomain: string;
  plan: string;
  amount: number;
  user_count?: number;
  is_admin_account?: boolean;
  currency: string;
  status: 'paid' | 'pending' | 'failed' | 'cancelled' | string;
  stripe_subscription_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export type BillingInvoice = BillingSubscriptionItem;

// Plans Management
export interface Plan {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  base_price: number;
  price_per_user: number;
  included_users: number;
  max_users: number;
  max_domains: number;
  max_storage_mb: number;
  max_stock_sku: number;
  max_websites: number;
  max_companies: number;
  max_backups: number;
  max_api_calls_day: number;
  currency: string;
  stripe_price_id?: string | null;
  stripe_product_id?: string | null;
  features: string[];
  is_active: boolean;
  is_public: boolean;
  is_highlighted: boolean;
  trial_days: number;
  annual_discount_percent: number;
  quota_warning_percent: number;
  quota_recommend_percent: number;
  quota_block_percent: number;
  fair_use_new_customers_only: boolean;
  storage_gb?: number;
  sort_order: number;
  active_subscribers: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PlansResponse {
  items: Plan[];
  total: number;
}

export interface PlanCalculation {
  plan: string;
  user_count: number;
  included_users: number;
  extra_users: number;
  base_price: number;
  extra_cost: number;
  monthly_total: number;
  currency: string;
}

// Customer Management
export interface CustomerItem {
  id: number;
  company_name: string;
  email: string;
  phone: string | null;
  full_name: string;
  subdomain: string;
  user_count: number;
  is_admin_account: boolean;
  stripe_customer_id?: string | null;
  subscription: {
    id: number;
    plan_name: string;
    status: string;
    monthly_amount: number;
    calculated_amount: number;
    user_count: number;
    start_date?: string | null;
  } | null;
  plan: {
    name: string;
    display_name: string;
    base_price: number;
    price_per_user: number;
    included_users: number;
  } | null;
  deployment: {
    subdomain: string;
    database_name?: string;
    tunnel_active?: boolean;
  } | null;
  created_at?: string | null;
}

export interface CustomersResponse {
  items: CustomerItem[];
  total: number;
  summary: {
    total_users: number;
    total_mrr: number;
    admin_accounts: number;
    billable_accounts: number;
  };
}

export interface BillingInvoicesResponse {
  kind?: string;
  items?: BillingSubscriptionItem[];
  invoices: BillingSubscriptionItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface BillingSubscriptionsResponse {
  items: BillingSubscriptionItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface StripeEventItem {
  event_id: string;
  event_type: string;
  processed: boolean;
  created_at?: string | null;
}

export interface StripeEventsResponse {
  events: StripeEventItem[];
  total: number;
}

export interface Domain {
  id: number;
  customer_id: number;
  tenant_deployment_id: number | null;
  external_domain: string;
  sajet_subdomain: string;
  sajet_full_domain: string;
  verification_status: 'pending' | 'verifying' | 'verified' | 'failed' | 'expired' | string;
  verification_token: string | null;
  verified_at: string | null;
  cloudflare_configured: boolean;
  tunnel_ingress_configured: boolean;
  nginx_configured: boolean;
  ssl_status: string | null;
  is_active: boolean;
  is_primary: boolean;
  target_node_ip: string;
  target_port: number;
  created_at: string;
  updated_at: string | null;
}

export interface DomainsListResponse {
  items: Domain[];
  total: number;
  limit: number;
  offset: number;
}

export interface DomainCreateResponse {
  success: boolean;
  domain: Domain;
  instructions?: {
    step1: string;
    record_type: string;
    record_name: string;
    record_value: string;
    step2: string;
  };
}

export interface NodeSummary {
  id: number;
  name: string;
  hostname: string;
  region: string;
  status: 'online' | 'offline' | 'maintenance' | string;
  proxmox_version?: string | null;
  is_database_node: boolean;
  can_host_tenants: boolean;
  active_deployments_count: number;
  available_slots: number;
  active_migrations_count: number;
  supported_runtime_modes: RuntimeMode[];
  priority: number;
  containers: {
    current: number;
    max: number;
  };
  resources: {
    cpu: {
      total_cores: number;
      usage_percent: number;
    };
    ram: {
      total_gb: number;
      used_gb: number;
      usage_percent: number;
    };
    storage: {
      total_gb: number;
      used_gb: number;
      usage_percent: number;
    };
  };
  last_health_check?: string | null;
  created_at?: string | null;
}

export interface NodesListResponse {
  items: NodeSummary[];
  total: number;
}

export interface NodeCreatePayload {
  name: string;
  hostname: string;
  total_cpu_cores: number;
  total_ram_gb: number;
  total_storage_gb: number;
  region?: string;
  ssh_port?: number;
  api_port?: number;
  max_containers?: number;
  is_database_node?: boolean;
  ssh_user?: string;
  api_token_id?: string | null;
}

export interface ClusterStatus {
  total_nodes: number;
  online_nodes: number;
  total_containers: number;
  cluster_health: 'healthy' | 'warning' | 'critical' | string;
  total_ram_gb: number;
  used_ram_gb: number;
  ram_percent: number;
  nodes: Array<{
    id: number;
    name: string;
    region: string;
    status: string;
    containers: number;
    max_containers: number;
    cpu_percent: number;
    ram_used_gb: number;
    ram_total_gb: number;
    storage_used_gb: number;
    storage_total_gb: number;
  }>;
}

export interface ClusterSummary {
  health: 'healthy' | 'warning' | 'critical' | string;
  nodes: {
    total: number;
    online: number;
  };
  containers: {
    total: number;
    running: number;
  };
  resources: {
    cpu: {
      cores: number;
      usage_percent: number;
    };
    ram: {
      total_gb: number;
      used_gb: number;
      usage_percent: number;
    };
    storage: {
      total_gb: number;
      used_gb: number;
      usage_percent: number;
    };
  };
}

export interface ContainerItem {
  id: number;
  node: string | null;
  vmid: number;
  hostname: string;
  status: 'running' | 'stopped' | 'paused' | string;
  ip: string | null;
  resources: {
    cpu: number;
    ram_mb: number;
    disk_gb: number;
  };
  usage: {
    cpu_percent: number;
    ram_mb: number;
    disk_gb: number;
  };
  is_shared: boolean;
  created_at?: string | null;
}

export interface ContainersListResponse {
  items: ContainerItem[];
  total: number;
}

export interface LogEntry {
  line: string;
  class: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  file?: string;
  source?: string;
  error?: string;
}

export interface SystemStatusResponse {
  postgresql: {
    status: string;
    latency_ms?: number | null;
    error?: string;
  };
  fastapi: {
    status: string;
    port?: number;
  };
  lxc_105: {
    status: string;
    name?: string;
  };
  disk: {
    usage_percent: number;
    free_gb: number;
  };
}

export interface TunnelDeployment {
  subdomain: string;
  domain?: string;
  url?: string;
  plan?: string;
  subscription_id?: number;
}

export interface Tunnel {
  id: string;
  name: string;
  status: string;
  deployment?: TunnelDeployment | null;
}

export interface TunnelsListResponse {
  success: boolean;
  total: number;
  tunnels: Tunnel[];
  warning?: string;
  error?: string;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  permissions: string[];
  system: boolean;
  updated_at?: string | null;
}

export interface RolesListResponse {
  items: Role[];
  total: number;
}

export interface TenantPortalInfo {
  id: number;
  company_name: string;
  email: string;
  subdomain: string;
  plan: string | null;
  status: string;
  subscription_id: number | null;
  stripe_subscription_id: string | null;
  created_at: string | null;
  odoo_url: string | null;
}

export interface TenantPortalBilling {
  invoices: Array<{
    id: string;
    amount: number;
    currency: string;
    status: string;
    date: string;
    pdf_url?: string | null;
    hosted_url?: string | null;
    download_url?: string | null;
    payment_url?: string | null;
    view_url?: string | null;
    preferred_action?: 'pay' | 'download' | 'view' | null;
  }>;
  payment_method: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
  } | null;
}

export interface SettingsEntry {
  key: string;
  value: string;
  description?: string;
  category?: string;
  is_secret?: boolean;
  is_editable?: boolean;
  updated_at?: string;
}

export interface SettingsResponse {
  configs: SettingsEntry[];
  by_category: Record<string, SettingsEntry[]>;
  total: number;
}

export interface OdooSettingsResponse {
  config: {
    admin_login: string;
    admin_password: string;
    master_password: string;
    db_user: string;
    db_password: string;
    default_lang: string;
    default_country: string;
    base_domain: string;
    template_db: string;
  };
  source: string;
  editable_via: string;
}

// ── Partner Ecosystem Types ──

export type PartnerStatusType = 'pending' | 'active' | 'suspended' | 'terminated';
export type LeadStatusType = 'new' | 'contacted' | 'qualified' | 'proposal' | 'won' | 'lost' | 'invalid';
export type CommissionStatusType = 'pending' | 'approved' | 'paid' | 'disputed' | 'offset';
export type QuotationStatusType = 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired' | 'invoiced';

export interface PartnerItem {
  id: number;
  customer_id: number | null;
  company_name: string;
  legal_name: string | null;
  tax_id: string | null;
  contact_name: string | null;
  contact_email: string;
  phone: string | null;
  country: string | null;
  address: string | null;
  billing_scenario: 'jeturing_collects' | 'partner_collects';
  commission_rate: number;
  margin_cap: number;
  status: PartnerStatusType;
  portal_access: boolean;
  white_label_enabled: boolean;
  partner_code: string | null;
  stripe_account_id: string | null;
  contract_signed_at: string | null;
  contract_reference: string | null;
  notes: string | null;
  leads_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface PartnersResponse {
  items: PartnerItem[];
  total: number;
  summary: {
    active: number;
    pending: number;
    total_leads: number;
  };
}

export interface LeadItem {
  id: number;
  partner_id: number;
  partner_name: string;
  company_name: string;
  contact_name: string | null;
  contact_email: string | null;
  phone: string | null;
  country: string | null;
  status: LeadStatusType;
  notes: string | null;
  estimated_monthly_value: number;
  converted_customer_id: number | null;
  converted_at: string | null;
  lost_reason: string | null;
  registered_at: string | null;
  updated_at: string | null;
}

export interface LeadsResponse {
  items: LeadItem[];
  total: number;
  pipeline: Record<string, number>;
  total_estimated_value: number;
}

export interface CommissionItem {
  id: number;
  partner_id: number;
  partner_name: string;
  subscription_id: number | null;
  lead_id: number | null;
  period_start: string | null;
  period_end: string | null;
  gross_revenue: number;
  net_revenue: number;
  deductions: Record<string, number>;
  partner_amount: number;
  jeturing_amount: number;
  status: CommissionStatusType;
  paid_at: string | null;
  payment_reference: string | null;
  notes: string | null;
  created_at: string | null;
}

export interface CommissionsResponse {
  items: CommissionItem[];
  total: number;
  summary: {
    total_partner_amount: number;
    total_jeturing_amount: number;
    total_pending_payout: number;
    total_gross: number;
  };
}

export interface QuotationLineItem {
  service_id?: number | null;
  name: string;
  unit: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface QuotationItem {
  id: number;
  quote_number: string;
  created_by_partner_id: number | null;
  created_by_admin: boolean;
  partner_name: string | null;
  customer_id: number | null;
  prospect_name: string | null;
  prospect_email: string | null;
  prospect_company: string | null;
  prospect_phone: string | null;
  lines: QuotationLineItem[];
  subtotal: number;
  partner_margin: number;
  total_monthly: number;
  currency: string;
  status: QuotationStatusType;
  valid_until: string | null;
  notes: string | null;
  terms: string | null;
  sent_at: string | null;
  accepted_at: string | null;
  rejected_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface QuotationsResponse {
  items: QuotationItem[];
  total: number;
  summary: {
    total_value: number;
    draft: number;
    sent: number;
    accepted: number;
  };
}

export interface ServiceCatalogItemType {
  id: number;
  category: string;
  name: string;
  description: string | null;
  unit: string;
  price_monthly: number;
  price_max: number | null;
  is_addon: boolean;
  requires_service_id: number | null;
  min_quantity: number;
  service_code?: string | null;
  metadata_json?: {
    kind?: string;
    email_quota_monthly?: number;
    email_burst_limit_60m?: number;
    email_overage_price?: number;
    [key: string]: unknown;
  };
  effective_price_monthly?: number;
  discount_percent?: number;
  included_quantity?: number;
  is_included_in_plan?: boolean;
  active_quantity?: number;
  is_active: boolean;
  sort_order: number;
  created_at: string | null;
  linked_plans?: Array<{
    link_id: number;
    plan_id: number;
    plan_name: string | null;
    included_quantity: number;
    is_included: boolean;
    discount_percent: number;
  }>;
}

export interface CatalogResponse {
  items: ServiceCatalogItemType[];
  total: number;
  by_category: Record<string, ServiceCatalogItemType[]>;
  categories: Array<{ value: string; label: string }>;
}

export interface AddonSubscriptionItem {
  id: number;
  customer_id: number;
  subscription_id: number | null;
  partner_id: number | null;
  catalog_item_id: number;
  status: string;
  quantity: number;
  unit_price_monthly: number;
  currency: string;
  service_code?: string | null;
  metadata_json?: Record<string, unknown>;
  acquired_via: string;
  starts_at: string | null;
  last_invoiced_year?: number | null;
  last_invoiced_month?: number | null;
  catalog_item: ServiceCatalogItemType | null;
}

// ── Plan ↔ Catalog Link Types ──

export interface PlanCatalogLinkType {
  id: number;
  plan_id: number;
  catalog_item_id: number;
  included_quantity: number;
  is_included: boolean;
  discount_percent: number;
  notes: string | null;
  catalog_item: ServiceCatalogItemType | null;
  plan_name: string | null;
  created_at: string | null;
}

export interface PlanCatalogLinksResponse {
  links: PlanCatalogLinkType[];
  total: number;
  by_plan: Record<number, { plan_name: string; items: PlanCatalogLinkType[] }>;
}

// ── Blueprint / Module Package Types (Épica 2) ──

export interface BlueprintModule {
  id: number;
  technical_name: string;
  display_name: string;
  description: string | null;
  category: string | null;
  version: string | null;
  is_core: boolean;
  partner_allowed: boolean;
  price_monthly: number;
  requires_module_id: number | null;
  is_active: boolean;
  sort_order: number;
  created_at: string | null;
}

export interface BlueprintModulesResponse {
  items: BlueprintModule[];
  total: number;
}

export interface BlueprintPackage {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  plan_type: string | null;
  base_price_monthly: number;
  is_default: boolean;
  is_active: boolean;
  module_list: string[];
  module_count: number;
  partner_allowed: boolean;
  modules?: BlueprintModule[];
  created_at?: string | null;
}

export interface BlueprintPackagesResponse {
  items: BlueprintPackage[];
  total: number;
}

// ── Seat Types (Épicas 3-4) ──

export type SeatEventType = 'USER_CREATED' | 'USER_DEACTIVATED' | 'USER_REACTIVATED' | 'FIRST_LOGIN' | 'HWM_SNAPSHOT';

export interface SeatEvent {
  id: number;
  subscription_id: number;
  event_type: SeatEventType;
  odoo_user_id: number | null;
  odoo_login: string | null;
  user_count_after: number;
  is_billable: boolean;
  grace_expires_at: string | null;
  source: string | null;
  metadata_json: string | null;
  created_at: string | null;
}

export interface SeatHWMRecord {
  id: number;
  subscription_id: number;
  period_date: string;
  hwm_count: number;
  stripe_qty_updated: boolean;
  stripe_qty_updated_at: string | null;
}

export interface SeatEventsResponse {
  items: SeatEvent[];
  total: number;
}

export interface SeatHWMResponse {
  records?: SeatHWMRecord[];
  items: SeatHWMRecord[];
  total: number;
  subscription_id?: number;
  days?: number;
}

export interface SeatSummaryResponse {
  subscription_id: number;
  current_user_count?: number;
  current_count: number;
  month_hwm?: number;
  hwm_count: number;
  grace_active_count?: number;
  grace_count: number;
  billable_count: number;
  recent_events?: SeatEvent[];
  last_event: SeatEvent | null;
  period: string;
  billing_mode?: string | null;
  is_partner_metered?: boolean;
}

export interface SeatOverviewItem {
  subscription_id: number;
  stripe_subscription_id?: string | null;
  customer_id: number;
  company_name: string;
  subdomain: string;
  email?: string | null;
  partner_id?: number | null;
  partner_name?: string | null;
  plan_name?: string | null;
  status?: string | null;
  billing_mode?: string | null;
  current_user_count: number;
  month_hwm: number;
  grace_active_count: number;
  billable_count: number;
  is_partner_metered: boolean;
}

export interface SeatOverviewGroup {
  partner_id: number | null;
  partner_name: string;
  customers: number;
  subscriptions: number;
  current_user_count: number;
  billable_count: number;
  tenants: SeatOverviewItem[];
}

export interface SeatOverviewResponse {
  items: SeatOverviewItem[];
  groups: SeatOverviewGroup[];
  total: number;
  generated_at?: string;
}

// ── Invoice Types (Épica 5) ──

export type InvoiceStatus = 'draft' | 'issued' | 'paid' | 'overdue' | 'void' | 'credited';
export type InvoiceType = 'SUBSCRIPTION' | 'SETUP' | 'ADDON' | 'INTERCOMPANY' | 'CREDIT_NOTE';

export interface InvoiceItem {
  id: number;
  invoice_number: string;
  subscription_id: number | null;
  customer_id: number | null;
  partner_id: number | null;
  company_name: string | null;
  email: string | null;
  subdomain: string | null;
  invoice_type: InvoiceType;
  billing_mode: string | null;
  issuer: string | null;
  subtotal: number;
  tax_amount: number;
  total: number;
  currency: string;
  lines_json: string | null;
  stripe_invoice_id: string | null;
  stripe_payment_intent_id: string | null;
  billing_period_key?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  status: InvoiceStatus;
  issued_at: string | null;
  paid_at: string | null;
  due_date: string | null;
  notes: string | null;
  created_at: string | null;
  pdf_url?: string | null;
  hosted_url?: string | null;
  download_url?: string | null;
  payment_url?: string | null;
  view_url?: string | null;
  preferred_action?: 'pay' | 'download' | 'view' | null;
}

export interface PartnerPortalInvoiceItem {
  id: number;
  invoice_number: string;
  customer_name: string | null;
  customer_email: string | null;
  total: number;
  currency: string;
  status: string | null;
  billing_mode: string | null;
  issuer: string | null;
  issued_at: string | null;
  due_date: string | null;
  paid_at: string | null;
  stripe_invoice_id: string | null;
  pdf_url?: string | null;
  hosted_url?: string | null;
  download_url?: string | null;
  payment_url?: string | null;
  view_url?: string | null;
  preferred_action?: 'pay' | 'download' | 'view' | null;
}

export interface InvoicesListResponse {
  invoices: InvoiceItem[];
  total: number;
}

// ── Settlement Types (Épica 6) ──

export type SettlementStatus = 'draft' | 'pending_approval' | 'approved' | 'transferred' | 'disputed';

export interface SettlementPeriod {
  id: number;
  partner_id: number;
  period_start: string;
  period_end: string;
  gross_revenue: number;
  net_revenue: number;
  jeturing_share: number;
  partner_share: number;
  offset_amount: number;
  final_partner_payout: number;
  status: SettlementStatus;
  approved_by: string | null;
  transfer_reference: string | null;
  transferred_at: string | null;
  notes: string | null;
  created_at: string | null;
}

export interface SettlementLine {
  id: number;
  settlement_id: number;
  subscription_id: number | null;
  invoice_id: number | null;
  description: string | null;
  gross_amount: number;
  stripe_fee: number;
  refunds: number;
  chargebacks: number;
  net_amount: number;
  jeturing_amount: number;
  partner_amount: number;
}

export interface SettlementsListResponse {
  items: SettlementPeriod[];
  total: number;
}

export interface SettlementDetailResponse extends SettlementPeriod {
  lines: SettlementLine[];
}

// ── Reconciliation Types (Épica 7) ──

export interface ReconciliationRun {
  id: number;
  period_start: string;
  period_end: string;
  stripe_total: number;
  local_total: number;
  discrepancy: number;
  discrepancy_details: Record<string, unknown> | null;
  status: string;
  run_by: string | null;
  created_at: string | null;
}

export interface ReconciliationListResponse {
  items: ReconciliationRun[];
  total: number;
}

// ── Work Order Types (Épica 9) ──

export type WorkOrderStatus = 'requested' | 'approved' | 'in_progress' | 'completed' | 'rejected' | 'cancelled';

export interface ModuleDetail {
  technical_name: string;
  display_name: string;
  category: string | null;
  approved: boolean;
  rejected: boolean;
}

// BlueprintPackage — definición principal en línea ~937

export interface WorkOrderItem {
  id: number;
  order_number: string;
  subscription_id: number | null;
  customer_id: number | null;
  partner_id: number | null;
  work_type: string;
  description: string;
  // Blueprint y módulos (Épica 9)
  blueprint_package_id: number | null;
  blueprint_name?: string;
  selected_modules: string[] | null;
  approved_modules: string[] | null;
  rejected_modules: string[] | null;
  selected_modules_detail?: ModuleDetail[];
  // Credenciales del tenant
  tenant_admin_email: string | null;
  tenant_user_email: string | null;
  // Estado y actores
  status: WorkOrderStatus;
  requested_by: string | null;
  approved_by: string | null;
  completed_by: string | null;
  // Nombres enriquecidos (GET /{id})
  customer_name?: string;
  customer_subdomain?: string;
  partner_name?: string;
  requested_at: string | null;
  approved_at: string | null;
  completed_at: string | null;
  notes: string | null;
  created_at: string | null;
}

export interface WorkOrdersListResponse {
  items: WorkOrderItem[];
  total: number;
}

// ── Audit Types (Épica 10) ──

export interface AuditEvent {
  id: number;
  event_type: string;
  actor_id: number | null;
  actor_username: string | null;
  actor_role: string | null;
  ip_address: string | null;
  user_agent: string | null;
  resource: string | null;
  action: string | null;
  status: string | null;
  details: Record<string, unknown> | null;
  created_at: string | null;
}

export interface AuditEventsResponse {
  items: AuditEvent[];
  total: number;
}

// ── Branding Types (Épica 10) ──

export interface BrandingProfile {
  id: number;
  partner_id: number;
  brand_name: string;
  logo_url: string | null;
  favicon_url: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  support_email: string | null;
  support_url: string | null;
  custom_css: string | null;
  is_active: boolean;
  created_at: string | null;
}

export interface BrandingProfilesResponse {
  items: BrandingProfile[];
  total: number;
}

// ── Partner Pricing Override Types ──

export type SupportLevelType = 'helpdesk_only' | 'priority' | 'dedicated';

export interface PartnerPricingOverrideItem {
  id: number;
  partner_id: number;
  plan_name: string;
  base_price_override: number | null;
  price_per_user_override: number | null;
  included_users_override: number | null;
  max_users_override: number | null;
  max_storage_mb_override: number | null;
  max_stock_sku_override: number | null;
  setup_fee: number;
  customization_hourly_rate: number | null;
  support_level: SupportLevelType | null;
  ecf_passthrough: boolean;
  ecf_monthly_cost: number | null;
  label: string | null;
  notes: string | null;
  is_active: boolean;
  valid_from: string | null;
  valid_until: string | null;
  created_at: string | null;
  updated_at: string | null;
  // Enriched from backend
  global_base_price?: number;
  global_price_per_user?: number;
  global_included_users?: number;
  global_max_users?: number;
  global_max_storage_mb?: number;
  global_max_stock_sku?: number;
}

export interface PartnerPricingOverridesResponse {
  items: PartnerPricingOverrideItem[];
  total: number;
  partner_id: number;
}

export interface PricingSimulation {
  plan: string;
  user_count: number;
  public_price: number;
  partner_price: number;
  discount_pct: number;
  setup_fee: number;
  customization_rate: number | null;
  support_level?: string;
  ecf_passthrough?: boolean;
  ecf_monthly_cost?: number | null;
  partner: string;
}

// ── Multi-Node Migration Types (Fase 3) ──

export type RuntimeMode = 'shared_pool' | 'dedicated_service';

export type MigrationState =
  | 'idle'
  | 'queued'
  | 'preflight'
  | 'preparing_target'
  | 'warming_target'
  | 'cutover'
  | 'verifying'
  | 'rollback'
  | 'completed'
  | 'failed';

export interface TenantDeploymentSummary {
  active_node_id: number | null;
  active_node_name: string | null;
  desired_node_id: number | null;
  desired_node_name: string | null;
  runtime_mode: RuntimeMode | string | null;
  routing_mode: string | null;
  migration_state: MigrationState | string | null;
  backend_host: string | null;
  http_port: number | null;
  chat_port: number | null;
  service_name: string | null;
  addons_overlay_path: string | null;
  has_active_migration: boolean;
  active_job_id: string | null;
}

export interface MigrationJob {
  id: string;
  deployment_id: number;
  subdomain: string;
  source_node_id: number;
  target_node_id: number;
  source_node_name: string | null;
  target_node_name: string | null;
  state: MigrationState | string;
  source_runtime_mode: string | null;
  target_runtime_mode: string | null;
  initiated_by: string;
  error_log: string | null;
  preflight_result: Record<string, unknown> | null;
  filestore_size_bytes: number | null;
  filestore_synced_at: string | null;
  cutover_started_at: string | null;
  cutover_ended_at: string | null;
  cutover_duration_seconds: number | null;
  rollback_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
  completed_at: string | null;
}

export interface MigrationJobListItem {
  id: string;
  subdomain: string;
  state: MigrationState | string;
  source_node_id: number;
  target_node_id: number;
  source_node_name: string | null;
  target_node_name: string | null;
  initiated_by: string;
  created_at: string | null;
  completed_at: string | null;
}

export interface MigrationStartResponse {
  success: boolean;
  data: MigrationJob;
  meta: { message?: string };
}

export interface MigrationStatusResponse {
  success: boolean;
  data: MigrationJob | null;
  meta: { has_active_migration?: boolean };
}

export interface MigrationJobListResponse {
  success: boolean;
  data: MigrationJobListItem[];
  meta: { total?: number; limit?: number; offset?: number };
}
