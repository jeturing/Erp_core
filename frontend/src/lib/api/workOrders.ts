import api from './client';
import type {
  WorkOrderItem,
  WorkOrdersListResponse,
  BlueprintPackage,
} from '../types';

export const workOrdersApi = {
  async create(data: {
    customer_id: number;
    partner_id?: number;
    subscription_id?: number;
    work_type?: string;
    description: string;
    blueprint_package_id?: number;
    selected_modules?: string[];
    requested_by?: string;
  }): Promise<{ message: string; work_order: WorkOrderItem }> {
    return api.post('/api/work-orders', data);
  },

  async list(params?: {
    customer_id?: number;
    partner_id?: number;
    subscription_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<WorkOrdersListResponse> {
    const qs = new URLSearchParams();
    if (params?.customer_id) qs.set('customer_id', String(params.customer_id));
    if (params?.partner_id) qs.set('partner_id', String(params.partner_id));
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
    notes?: string;
    completed_by?: string;
  }): Promise<{ message: string; work_order: WorkOrderItem }> {
    return api.put(`/api/work-orders/${id}/status`, data);
  },

  async approveModules(id: number, data: {
    approved_modules: string[];
    rejected_modules?: string[];
    notes?: string;
    approved_by?: string;
  }): Promise<{ message: string; approved: string[]; rejected: string[] }> {
    return api.post(`/api/work-orders/${id}/approve-modules`, data);
  },

  async getBlueprints(): Promise<BlueprintPackage[]> {
    return api.get('/api/work-orders/catalog/packages');
  },

  async getCatalogModules(category?: string): Promise<{
    items: Array<{
      id: number;
      technical_name: string;
      display_name: string;
      category: string | null;
      is_core: boolean;
      partner_allowed: boolean;
    }>;
    categories: string[];
  }> {
    const qs = category ? `?category=${encodeURIComponent(category)}` : '';
    return api.get(`/api/work-orders/catalog/modules${qs}`);
  },
};

export default workOrdersApi;
