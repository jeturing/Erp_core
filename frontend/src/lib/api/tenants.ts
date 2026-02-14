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
  use_fast_method?: boolean;
}

export interface ChangeTenantPasswordRequest {
  subdomain: string;
  new_password: string;
  server?: string;
}

export interface SuspendTenantRequest {
  subdomain: string;
  suspend: boolean;
  reason?: string;
  server?: string;
}

export const tenantsApi = {
  async list(): Promise<TenantListResponse> {
    return api.get<TenantListResponse>('/api/tenants');
  },

  async create(payload: CreateTenantRequest): Promise<{ success: boolean; message: string; tenant?: Tenant }> {
    return api.post('/api/tenants', payload);
  },

  async delete(subdomain: string): Promise<{ success: boolean; message: string }> {
    return api.delete(`/api/tenants/${encodeURIComponent(subdomain)}?confirm=true`);
  },

  async changePassword(payload: ChangeTenantPasswordRequest): Promise<{ success: boolean; message: string }> {
    return api.put(
      '/api/provisioning/tenant/password',
      {
        subdomain: payload.subdomain,
        new_password: payload.new_password,
        server: payload.server || 'primary',
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
        server: payload.server || 'primary',
      },
      { 'X-API-KEY': PROVISIONING_API_KEY },
    );
  },
};

export default tenantsApi;
