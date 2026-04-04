import api from './client';
import type { Tenant, TenantListResponse } from '../types';

const PROVISIONING_API_KEY = import.meta.env.VITE_PROVISIONING_API_KEY || 'prov-key-2026-secure';

export interface CreateTenantRequest {
  subdomain: string;
  company_name?: string;
  admin_email?: string;
  admin_password?: string;
  server_id?: string;
  plan?: 'basic' | 'pro' | 'enterprise';
  partner_id?: number | null;
  country_code?: string;
  blueprint_package_name?: string;
  use_fast_method?: boolean;
}

export interface ModuleInstallRequest {
  modules: string[];
  blueprint_package_name?: string;
}

export interface ModuleInstallResponse {
  success: boolean;
  subdomain: string;
  server: string;
  installed: string[];
  already_installed: string[];
  failed: string[];
  total_requested: number;
}

export interface ChangeTenantPasswordRequest {
  subdomain: string;
  new_password: string;
  server_id?: string;
  server?: string;
}

export interface SuspendTenantRequest {
  subdomain: string;
  suspend: boolean;
  reason?: string;
  server_id?: string;
  server?: string;
}

export interface UpdateTenantEmailRequest {
  subdomain: string;
  new_email: string;
  server_id?: string;
  server?: string;
}

export interface TenantAccountItem {
  id: number;
  login: string;
  email?: string | null;
  name?: string | null;
  active: boolean;
  share: boolean;
  is_admin?: boolean;
  is_billable?: boolean;
  write_date?: string | null;
  create_date?: string | null;
}

export interface TenantAccountsResponse {
  success: boolean;
  subdomain: string;
  server: string;
  accounts: TenantAccountItem[];
  total_accounts: number;
  active_accounts: number;
  billable_active_accounts: number;
  seat_sync?: {
    customer_found: boolean;
    subscription_found: boolean;
    subscription_id?: number | null;
    plan?: string | null;
    plan_user_limit?: number | null;
    extra_over_plan?: number;
  };
}

export interface UpdateTenantAccountCredentialsRequest {
  subdomain: string;
  user_id?: number;
  login?: string;
  new_email?: string;
  new_password?: string;
  active?: boolean;
  server_id?: string;
  server?: string;
}

// ─── Phantom Tenants ───
export interface PhantomTenant {
  subdomain: string;
  company_name: string | null;
  customer_id: number | null;
  subscription_id: number | null;
  has_deployment: boolean;
  reason: string;
}

export interface PhantomDetectResponse {
  success: boolean;
  phantoms: PhantomTenant[];
  total: number;
  scanned: number;
}

export interface PhantomPurgeResponse {
  success: boolean;
  message: string;
  deleted: {
    customer: boolean;
    subscription: boolean;
    deployment: boolean;
    dns_cleaned: boolean;
  };
}

export interface PhantomPurgeAllResponse {
  success: boolean;
  message: string;
  purged: number;
  failed: number;
  details: Array<{ subdomain: string; status: string; error?: string }>;
}

export interface ReservedSubdomain {
  id: number;
  subdomain: string;
  reason: string | null;
  category: string;
  is_active: boolean;
  created_at: string;
}

export interface ReservedSubdomainListResponse {
  success: boolean;
  items: ReservedSubdomain[];
  total: number;
}

export const tenantsApi = {
  async list(): Promise<TenantListResponse> {
    return api.get<TenantListResponse>('/api/tenants');
  },

  async create(payload: CreateTenantRequest): Promise<{ success: boolean; message: string; tenant?: Tenant }> {
    return api.post('/api/tenants', payload);
  },

  async delete(subdomain: string, confirmName: string, serverId?: string): Promise<{ success: boolean; message: string }> {
    const qs = new URLSearchParams({
      confirm: 'true',
      confirm_name: confirmName,
    });
    if (serverId) qs.set('server_id', serverId);
    return api.delete(`/api/tenants/${encodeURIComponent(subdomain)}?${qs.toString()}`);
  },

  async changePassword(payload: ChangeTenantPasswordRequest): Promise<{ success: boolean; message: string }> {
    return api.put(
      '/api/provisioning/tenant/password',
      {
        subdomain: payload.subdomain,
        new_password: payload.new_password,
        server: payload.server_id || payload.server || 'primary',
      },
      { 'X-API-KEY': PROVISIONING_API_KEY },
    );
  },

  async suspend(payload: SuspendTenantRequest): Promise<{ success: boolean; message: string; status?: string }> {
    return api.put(
      '/api/provisioning/tenant/suspend',
      {
        subdomain: payload.subdomain,
        suspend: payload.suspend,
        reason: payload.reason || (payload.suspend ? 'Suspension manual desde admin SPA' : 'Reactivacion manual desde admin SPA'),
        server: payload.server_id || payload.server || 'primary',
      },
      { 'X-API-KEY': PROVISIONING_API_KEY },
    );
  },

  async updateEmail(payload: UpdateTenantEmailRequest): Promise<{ success: boolean; message: string }> {
    return api.put(
      '/api/provisioning/tenant/email',
      {
        subdomain: payload.subdomain,
        new_email: payload.new_email,
        server: payload.server_id || payload.server || 'primary',
      },
      { 'X-API-KEY': PROVISIONING_API_KEY },
    );
  },

  async listAccounts(subdomain: string, server?: string): Promise<TenantAccountsResponse> {
    const qs = new URLSearchParams({
      subdomain,
      include_inactive: 'true',
      server: server || 'primary',
    });
    return api.get<TenantAccountsResponse>(`/api/provisioning/tenant/accounts?${qs.toString()}`, { 'X-API-KEY': PROVISIONING_API_KEY });
  },

  async updateAccountCredentials(payload: UpdateTenantAccountCredentialsRequest): Promise<{ success: boolean; message: string }> {
    return api.put(
      '/api/provisioning/tenant/account/credentials',
      {
        subdomain: payload.subdomain,
        user_id: payload.user_id,
        login: payload.login,
        new_email: payload.new_email,
        new_password: payload.new_password,
        active: payload.active,
        server: payload.server_id || payload.server || 'primary',
      },
      { 'X-API-KEY': PROVISIONING_API_KEY },
    );
  },

  async syncSeatCount(subdomain: string, server?: string): Promise<TenantAccountsResponse> {
    return api.post(
      '/api/provisioning/tenant/accounts/sync-seat-count',
      {
        subdomain,
        server: server || 'primary',
      },
      { 'X-API-KEY': PROVISIONING_API_KEY },
    );
  },

  async installModules(subdomain: string, payload: ModuleInstallRequest): Promise<ModuleInstallResponse> {
    return api.post<ModuleInstallResponse>(
      `/api/tenants/${encodeURIComponent(subdomain)}/modules/install`,
      payload,
    );
  },

  // ─── Phantom Tenants ───
  async detectPhantoms(): Promise<PhantomDetectResponse> {
    return api.get<PhantomDetectResponse>('/api/tenants/phantoms/detect');
  },

  async purgePhantom(subdomain: string, cleanDns = true): Promise<PhantomPurgeResponse> {
    const qs = cleanDns ? '?clean_dns=true' : '';
    return api.delete<PhantomPurgeResponse>(`/api/tenants/${encodeURIComponent(subdomain)}/purge-phantom${qs}`);
  },

  async purgeAllPhantoms(cleanDns = true): Promise<PhantomPurgeAllResponse> {
    return api.post<PhantomPurgeAllResponse>('/api/tenants/phantoms/purge-all', { clean_dns: cleanDns });
  },

  // ─── Reserved Subdomains ───
  async listReservedSubdomains(): Promise<ReservedSubdomainListResponse> {
    return api.get<ReservedSubdomainListResponse>('/api/tenants/reserved-subdomains');
  },

  async addReservedSubdomain(subdomain: string, reason?: string, category?: string): Promise<{ success: boolean; item: ReservedSubdomain }> {
    return api.post('/api/tenants/reserved-subdomains', { subdomain, reason, category });
  },

  async removeReservedSubdomain(subdomain: string): Promise<{ success: boolean; message: string }> {
    return api.delete(`/api/tenants/reserved-subdomains/${encodeURIComponent(subdomain)}`);
  },
};

export default tenantsApi;
