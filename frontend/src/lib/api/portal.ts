import api from './client';
import type { TenantPortalBilling, TenantPortalInfo } from '../types';

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
};

export default portalApi;
