import api from './client';
import type {
  SeatEventsResponse,
  SeatHWMResponse,
  SeatSummaryResponse,
} from '../types';

export const seatsApi = {
  async postEvent(data: {
    subscription_id: number;
    event_type: string;
    odoo_user_id?: number;
    odoo_login?: string;
    user_count_after: number;
    source?: string;
  }): Promise<{ message: string; event_id: number; billable: boolean }> {
    return api.post('/api/seats/event', data);
  },

  async getHWM(subscriptionId?: number): Promise<SeatHWMResponse> {
    const params = subscriptionId ? `?subscription_id=${subscriptionId}` : '';
    return api.get<SeatHWMResponse>(`/api/seats/hwm${params}`);
  },

  async syncStripe(): Promise<{ message: string; synced: number; errors: number }> {
    return api.post('/api/seats/sync-stripe');
  },

  async getSummary(subscriptionId?: number): Promise<SeatSummaryResponse> {
    const params = subscriptionId ? `?subscription_id=${subscriptionId}` : '';
    return api.get<SeatSummaryResponse>(`/api/seats/summary${params}`);
  },
};

export default seatsApi;
