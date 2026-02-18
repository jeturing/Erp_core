import api from './client';
import type {
  InvoiceItem,
  InvoicesListResponse,
} from '../types';

export const invoicesApi = {
  async generate(data: {
    subscription_id: number;
    period_start?: string;
    period_end?: string;
  }): Promise<{ message: string; invoice: InvoiceItem }> {
    return api.post('/api/invoices/generate', data);
  },

  async list(params?: {
    subscription_id?: number;
    customer_id?: number;
    partner_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<InvoicesListResponse> {
    const qs = new URLSearchParams();
    if (params?.subscription_id) qs.set('subscription_id', String(params.subscription_id));
    if (params?.customer_id) qs.set('customer_id', String(params.customer_id));
    if (params?.partner_id) qs.set('partner_id', String(params.partner_id));
    if (params?.status) qs.set('status', params.status);
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    const q = qs.toString();
    return api.get<InvoicesListResponse>(`/api/invoices${q ? '?' + q : ''}`);
  },

  async get(id: number): Promise<InvoiceItem> {
    return api.get(`/api/invoices/${id}`);
  },

  async markPaid(id: number, data?: {
    stripe_payment_intent_id?: string;
  }): Promise<{ message: string; invoice: InvoiceItem }> {
    return api.post(`/api/invoices/${id}/pay`, data || {});
  },
};

export default invoicesApi;
