import { api } from './client';

export interface Plan {
  id: number;
  name: string;
  display_name: string;
  base_price: number;
  max_domains: number;
  max_users: number;
  max_storage_mb: number;
  max_stock_sku: number;
  is_active: boolean;
  is_public: boolean;
  is_highlighted: boolean;
  trial_days: number;
  annual_discount_percent: number;
  quota_warning_percent: number;
  quota_recommend_percent: number;
  quota_block_percent: number;
  fair_use_new_customers_only: boolean;
}

type PlansListResponse = {
  items?: Plan[];
  total?: number;
};

function normalizePlansResponse(payload: Plan[] | PlansListResponse): Plan[] {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.items)) return payload.items;
  return [];
}

export const plansApi = {
  list: async (): Promise<Plan[]> => {
    const response = await api.get<Plan[] | PlansListResponse>('/api/plans');
    return normalizePlansResponse(response);
  },

  update: (planId: number, data: Partial<Plan>) =>
    api.put(`/api/plans/${planId}`, data),

  /** Atajo para editar solo max_domains de un plan */
  setMaxDomains: (planId: number, maxDomains: number) =>
    api.put(`/api/plans/${planId}`, { max_domains: maxDomains }),
};
