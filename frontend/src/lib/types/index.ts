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
  plan_distribution: {
    basic: { count: number; revenue: number };
    pro: { count: number; revenue: number };
    enterprise: { count: number; revenue: number };
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
  currency: string;
  status: 'paid' | 'pending' | 'failed' | 'cancelled' | string;
  stripe_subscription_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
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
