import { api } from './client';

export interface DispersionStatus {
  enabled: boolean;
  feature_flag_source: string;
  mercury_connected: boolean;
  checking_balance: number | null;
  savings_balance: number | null;
  pending_count: number;
  authorized_count: number;
  processing_count: number;
  completed_today: number;
  failed_today: number;
  daily_limit_usd: number;
  used_today_usd: number;
  remaining_today_usd: number;
  last_updated: string;
}

export interface PayoutRequest {
  id: number;
  provider_name: string;
  provider_account: string;
  provider_routing: string;
  amount_usd: number;
  payment_method: string;
  concept: string;
  reference: string | null;
  notes: string | null;
  status: string;
  created_by: string;
  created_at: string;
  authorized_by: string | null;
  authorized_at: string | null;
  authorization_note: string | null;
  rejected_by: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
  mercury_payment_id: string | null;
  executed_at: string | null;
  error_message: string | null;
}

export interface CreatePayoutBody {
  provider_name: string;
  provider_account: string;
  provider_routing: string;
  amount_usd: number;
  payment_method: string;
  concept: string;
  reference?: string;
  notes?: string;
}

export const dispersionApi = {
  getStatus: (): Promise<DispersionStatus> =>
    api.get('/api/dispersion/status'),

  setFeatureFlag: (enabled: boolean, reason?: string) =>
    api.post('/api/dispersion/feature-flag', { enabled, reason }),

  listPayouts: (status?: string): Promise<{ payouts: PayoutRequest[]; total: number }> =>
    api.get('/api/dispersion/payouts' + (status ? `?status=${status}` : '')),

  createPayout: (body: CreatePayoutBody) =>
    api.post('/api/dispersion/payouts/create', body),

  authorizePayout: (payout_id: number, authorization_note?: string) =>
    api.post('/api/dispersion/payouts/authorize', { payout_id, authorization_note }),

  rejectPayout: (payout_id: number, rejection_reason: string) =>
    api.post('/api/dispersion/payouts/reject', { payout_id, rejection_reason }),
};
