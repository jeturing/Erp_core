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
    if (!subscriptionId) {
      return { items: [], records: [], total: 0 };
    }
    return api.get<SeatHWMResponse>(`/api/seats/hwm/${subscriptionId}`);
  },

  async syncStripe(): Promise<{ message: string; synced: number; errors: number }> {
    return api.post('/api/seats/sync-stripe');
  },

  async getSummary(subscriptionId?: number): Promise<SeatSummaryResponse> {
    if (!subscriptionId) {
      return {
        subscription_id: 0,
        current_count: 0,
        hwm_count: 0,
        grace_count: 0,
        billable_count: 0,
        last_event: null,
        period: '',
      };
    }
    return api.get<SeatSummaryResponse>(`/api/seats/summary/${subscriptionId}`);
  },
};

export default seatsApi;
