import api from './client';
import type {
  BillingInvoicesResponse,
  BillingMetrics,
  StripeEventsResponse,
} from '../types';

export const billingApi = {
  async getMetrics(): Promise<BillingMetrics> {
    return api.get<BillingMetrics>('/api/billing/metrics');
  },

  async getInvoices(limit = 20, offset = 0): Promise<BillingInvoicesResponse> {
    return api.get<BillingInvoicesResponse>(`/api/billing/invoices?limit=${limit}&offset=${offset}`);
  },

  async getStripeEvents(limit = 20): Promise<StripeEventsResponse> {
    return api.get<StripeEventsResponse>(`/api/billing/stripe-events?limit=${limit}`);
  },
};

export default billingApi;
