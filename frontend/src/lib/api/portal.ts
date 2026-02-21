import api from './client';
import type { TenantPortalBilling, TenantPortalInfo } from '../types';

export interface PortalDomain {
  id: number;
  external_domain: string;
  verification_status: string;
  is_active: boolean;
  sajet_subdomain: string | null;
  sajet_full_domain: string | null;
  created_at: string | null;
}

export interface SeatEventEntry {
  id: number;
  event_type: string;
  odoo_login: string | null;
  odoo_user_id: number | null;
  user_count_after: number;
  is_billable: boolean;
  source: string;
  created_at: string | null;
}

export interface PortalUsersResponse {
  current_user_count: number;
  plan_user_limit: number;
  seat_events: SeatEventEntry[];
}

export const portalApi = {
  async getInfo(): Promise<TenantPortalInfo> {
    return api.get<TenantPortalInfo>('/tenant/api/info');
  },

  async getBilling(): Promise<TenantPortalBilling> {
    return api.get<TenantPortalBilling>('/tenant/api/billing');
  },

  async updatePaymentMethod(): Promise<{ checkout_url?: string; message?: string }> {
    return api.post('/tenant/api/update-payment');
  },

  async cancelSubscription(): Promise<{ message: string }> {
    return api.post('/tenant/api/cancel-subscription');
  },

  async changePassword(body: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }): Promise<{ message: string }> {
    return api.post('/tenant/api/change-password', body);
  },

  async getMyDomains(): Promise<{ domains: PortalDomain[] }> {
    return api.get('/tenant/api/my-domains');
  },

  async requestDomain(external_domain: string): Promise<{ message: string; domain: PortalDomain }> {
    return api.post('/tenant/api/request-domain', { external_domain });
  },

  async getUsers(): Promise<PortalUsersResponse> {
    return api.get('/tenant/api/users');
  },
};

export default portalApi;
