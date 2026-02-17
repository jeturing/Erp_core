import api from './client';
import type {
  BillingInvoicesResponse,
  BillingMetrics,
  StripeEventsResponse,
} from '../types';

export interface BillingComparison {
  current_month: string;
  previous_month: string;
  current_mrr: number;
  previous_mrr: number;
  current_revenue: number;
  previous_revenue: number;
  new_customers: number;
  lost_customers: number;
}

export const billingApi = {
  async getMetrics(): Promise<BillingMetrics> {
    return api.get<BillingMetrics>('/api/billing/metrics');
  },

  async getInvoices(limit = 20, offset = 0): Promise<BillingInvoicesResponse> {
    return api.get<BillingInvoicesResponse>(`/api/billing/invoices?limit=${limit}&offset=${offset}`);
  },

  async getComparison(): Promise<BillingComparison> {
    return api.get<BillingComparison>('/api/billing/comparison');
  },

  async getStripeEvents(limit = 20): Promise<StripeEventsResponse> {
    return api.get<StripeEventsResponse>(`/api/billing/stripe-events?limit=${limit}`);
  },
};

export default billingApi;
