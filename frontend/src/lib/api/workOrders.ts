import api from './client';
import type {
  WorkOrderItem,
  WorkOrdersListResponse,
} from '../types';

export const workOrdersApi = {
  async create(data: {
    subscription_id: number;
    customer_id?: number;
    partner_id?: number;
    work_type: string;
    description: string;
    parameters?: Record<string, unknown>;
  }): Promise<{ message: string; work_order: WorkOrderItem }> {
    return api.post('/api/work-orders', data);
  },

  async list(params?: {
    subscription_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<WorkOrdersListResponse> {
    const qs = new URLSearchParams();
    if (params?.subscription_id) qs.set('subscription_id', String(params.subscription_id));
    if (params?.status) qs.set('status', params.status);
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    const q = qs.toString();
    return api.get<WorkOrdersListResponse>(`/api/work-orders${q ? '?' + q : ''}`);
  },

  async get(id: number): Promise<WorkOrderItem> {
    return api.get(`/api/work-orders/${id}`);
  },

  async updateStatus(id: number, data: {
    status: string;
    result?: Record<string, unknown>;
    notes?: string;
  }): Promise<{ message: string; work_order: WorkOrderItem }> {
    return api.put(`/api/work-orders/${id}`, data);
  },
};

export default workOrdersApi;
