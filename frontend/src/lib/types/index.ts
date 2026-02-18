// Shared frontend types for ERP Core SPA

export type UserRole = 'admin' | 'operator' | 'viewer' | 'tenant';

export interface User {
  id?: number;
  user_id?: number | null;
  tenant_id?: number | null;
  username: string;
  email: string;
  role: UserRole;
  is_active?: boolean;
  created_at?: string;
  company_name?: string;
  full_name?: string;
  plan?: 'basic' | 'pro' | 'enterprise' | string;
}

export interface LoginRequest {
  username: string;
  password: string;
  totp_code?: string;
}

export interface LoginResponse {
  message: string;
  role: UserRole;
  requires_totp: boolean;
  redirect_url?: string | null;
  user_id?: number | null;
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
  created_at?: string | null;
  url?: string;
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

export interface BillingInvoice {
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
  currency: string;
  stripe_price_id?: string | null;
  stripe_product_id?: string | null;
  features: string[];
  is_active: boolean;
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
  invoices: BillingInvoice[];
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
  is_active: boolean;
  sort_order: number;
  created_at: string | null;
}

export interface CatalogResponse {
  items: ServiceCatalogItemType[];
  total: number;
  by_category: Record<string, ServiceCatalogItemType[]>;
  categories: Array<{ value: string; label: string }>;
}
