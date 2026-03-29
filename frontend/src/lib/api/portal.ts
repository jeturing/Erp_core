import api from './client';
import type { AddonSubscriptionItem, ServiceCatalogItemType, TenantPortalBilling, TenantPortalInfo } from '../types';

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
  login: string | null;
  user_id: number | null;
  user_count_after: number;
  is_billable: boolean;
  source: string;
  created_at: string | null;
}

export interface PortalUserAccount {
  id: number;
  login: string | null;
  email: string | null;
  name: string | null;
  active: boolean;
  is_admin: boolean;
  is_excluded: boolean;
  is_billable: boolean;
  write_date: string | null;
  create_date: string | null;
}

export interface PortalUsersResponse {
  accounts: PortalUserAccount[];
  active_accounts: number;
  billable_active_accounts: number;
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

  async getServiceCatalog(): Promise<{ items: ServiceCatalogItemType[]; total: number }> {
    return api.get('/tenant/api/services/catalog');
  },

  async getServiceSubscriptions(): Promise<{ items: AddonSubscriptionItem[]; total: number }> {
    return api.get('/tenant/api/services/subscriptions');
  },

  async purchaseService(catalog_item_id: number, quantity = 1): Promise<{
    message: string;
    addon: AddonSubscriptionItem;
    invoice?: { id: number; invoice_number: string; total: number; currency: string; status: string; stripe_invoice_id?: string | null; payment_url?: string | null } | null;
  }> {
    return api.post('/tenant/api/services/purchase', { catalog_item_id, quantity });
  },
};

export default portalApi;
