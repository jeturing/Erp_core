// Quotas API — Resource quota management
import { api } from './client';

export interface QuotaResource {
  limit: number;
  used: number;
  available: number | null;
  percentage: number;
  unlimited: boolean;
  can_add: boolean;
  exceeded: boolean;
  status?: 'ok' | 'warning' | 'critical' | 'exceeded' | string;
}

export interface CustomerQuotas {
  success: boolean;
  customer_id: number;
  company_name: string;
  plan_name: string;
  plan_key: string;
  fair_use_enabled?: boolean;
  quotas: Record<string, QuotaResource>;
}

export interface CustomerQuotaSummary {
  customer_id: number;
  company_name: string;
  subdomain: string;
  plan_name: string;
  plan_key: string;
  fair_use_enabled?: boolean;
  resources: Record<string, {
    used: number;
    limit: number;
    unlimited: boolean;
    exceeded: boolean;
    status?: 'ok' | 'warning' | 'critical' | 'exceeded' | string;
  }>;
}

export interface AllQuotasResponse {
  success: boolean;
  total: number;
  customers: CustomerQuotaSummary[];
}

export const quotasApi = {
  /** Get all quotas for a customer */
  async getCustomerQuotas(customerId: number): Promise<CustomerQuotas> {
    return api.get<CustomerQuotas>(`/api/quotas/${customerId}`);
  },

  /** Get a single resource quota for a customer */
  async getResourceQuota(customerId: number, resource: string): Promise<QuotaResource & { success: boolean }> {
    return api.get(`/api/quotas/${customerId}/${resource}`);
  },

  /** Check if customer can add N units of a resource */
  async checkQuota(customerId: number, resource: string, increment = 1): Promise<{ success: boolean; allowed: boolean }> {
    return api.get(`/api/quotas/${customerId}/check/${resource}?increment=${increment}`);
  },

  /** Get quota summary for all customers (admin dashboard) */
  async getAllQuotas(): Promise<AllQuotasResponse> {
    return api.get<AllQuotasResponse>('/api/quotas');
  },
};
