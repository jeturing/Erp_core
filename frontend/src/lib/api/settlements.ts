import api from './client';
import type {
  SettlementPeriod,
  SettlementsListResponse,
  SettlementDetailResponse,
} from '../types';

export const settlementsApi = {
  async create(data: {
    partner_id: number;
    period_start: string;
    period_end: string;
  }): Promise<{ message: string; settlement: SettlementPeriod }> {
    return api.post('/api/settlements', data);
  },

  async list(params?: {
    partner_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<SettlementsListResponse> {
    const qs = new URLSearchParams();
    if (params?.partner_id) qs.set('partner_id', String(params.partner_id));
    if (params?.status) qs.set('status', params.status);
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    const q = qs.toString();
    return api.get<SettlementsListResponse>(`/api/settlements${q ? '?' + q : ''}`);
  },

  async get(id: number): Promise<SettlementDetailResponse> {
    return api.get(`/api/settlements/${id}`);
  },

  async close(id: number): Promise<{ message: string; settlement: SettlementPeriod }> {
    return api.post(`/api/settlements/${id}/close`);
  },
};

export default settlementsApi;
