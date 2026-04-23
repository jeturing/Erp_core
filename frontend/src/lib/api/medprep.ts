/**
 * MedPrep Admin API — gestión de estudiantes y suscripciones desde SAJET DSM
 */
import api from './client';

export interface MedSubStats {
  total: number;
  active: number;
  canceled: number;
  past_due: number;
  active_students: number;
  banks_with_subs: number;
  arr_usd: number;
  new_last_30d: number;
  by_bank: { name: string; slug: string; color: string; active: number; total: number }[];
}

export interface MedSubscription {
  id: number;
  status: string;
  stripe_subscription_id: string | null;
  stripe_customer_id: string | null;
  period_start: string | null;
  period_end: string | null;
  canceled_at: string | null;
  created_at: string | null;
  is_active: boolean;
  user: {
    med_user_id: number;
    sajet_user_id: number;
    display_name: string;
    role: string;
  };
  bank: { id: number; slug: string; name: string; color: string };
  price: { amount: number; currency: string };
}

export interface MedSession {
  sajet_user_id: number;
  email: string;
  role: string;
  product: string;
  login_at: string;
  ip: string;
  user_agent: string;
}

export interface MedBank {
  id: number;
  slug: string;
  name: string;
  color: string;
  icon: string;
  question_count: number;
  flashcard_count: number;
  stripe_price_id: string | null;
  price_usd: number;
  active_subscriptions: number;
}

export const medprepApi = {
  stats: () =>
    api.get<{ success: boolean; data: MedSubStats }>('/api/medprep/subscriptions/stats'),

  subscriptions: (params: {
    status?: string;
    bank_slug?: string;
    search?: string;
    page?: number;
    limit?: number;
  } = {}) => {
    const qs = new URLSearchParams();
    if (params.status) qs.set('status', params.status);
    if (params.bank_slug) qs.set('bank_slug', params.bank_slug);
    if (params.search) qs.set('search', params.search);
    if (params.page) qs.set('page', String(params.page));
    if (params.limit) qs.set('limit', String(params.limit));
    return api.get<{ success: boolean; data: MedSubscription[]; meta: any }>(
      `/api/medprep/subscriptions?${qs}`
    );
  },

  sessions: () =>
    api.get<{ success: boolean; data: MedSession[]; total: number }>('/api/medprep/sessions'),

  cancelSubscription: (id: number) =>
    api.post<{ success: boolean; message: string }>(`/api/medprep/subscriptions/${id}/cancel`),

  banks: () =>
    api.get<{ success: boolean; data: MedBank[] }>('/api/medprep/banks'),
};
