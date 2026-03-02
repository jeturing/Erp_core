import api from './client';
import type {
  ReconciliationRun,
  ReconciliationListResponse,
} from '../types';

export const reconciliationApi = {
  async run(data?: {
    period_start?: string;
    period_end?: string;
  }): Promise<{ message: string; run: ReconciliationRun }> {
    return api.post('/api/reconciliation/run', data || {});
  },

  async list(params?: {
    limit?: number;
    offset?: number;
  }): Promise<ReconciliationListResponse> {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    const q = qs.toString();
    return api.get<ReconciliationListResponse>(`/api/reconciliation/runs${q ? '?' + q : ''}`);
  },

  async get(id: number): Promise<ReconciliationRun> {
    return api.get(`/api/reconciliation/runs/${id}`);
  },
};

export default reconciliationApi;
