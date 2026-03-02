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
      throw new Error('subscriptionId requerido para consultar HWM');
    }
    return api.get<SeatHWMResponse>(`/api/seats/hwm/${subscriptionId}`);
  },

  async syncStripe(): Promise<{ message: string; synced: number; errors: number }> {
    return api.post('/api/seats/sync-stripe');
  },

  async getSummary(subscriptionId?: number): Promise<SeatSummaryResponse> {
    if (!subscriptionId) {
      throw new Error('subscriptionId requerido para consultar summary');
    }
    return api.get<SeatSummaryResponse>(`/api/seats/summary/${subscriptionId}`);
  },
};

export default seatsApi;
