import { api } from './client';

export interface Plan {
  id: number;
  name: string;
  display_name: string;
  base_price: number;
  max_domains: number;
  max_users: number;
  max_storage_mb: number;
  is_active: boolean;
}

export const plansApi = {
  list: (): Promise<Plan[]> =>
    api.get('/api/plans'),

  update: (planId: number, data: Partial<Plan>) =>
    api.put(`/api/plans/${planId}`, data),

  /** Atajo para editar solo max_domains de un plan */
  setMaxDomains: (planId: number, maxDomains: number) =>
    api.put(`/api/plans/${planId}`, { max_domains: maxDomains }),
};
