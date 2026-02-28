/**
 * API client for admin-configurable onboarding configuration.
 * Endpoints under /api/onboarding-config/
 */

import type { ComponentType } from 'svelte';

const BASE = '/api/onboarding-config';

export interface OnboardingStep {
  step: number;
  key: string;
  label: string;
  required: boolean;
  visible: boolean;
  condition: { country_in?: string[] } | null;
  icon?: ComponentType;
}

export interface PortalMenuItem {
  key: string;
  label: string;
  icon: string;
  visible: boolean;
  order: number;
}

export interface PlanDetail {
  name: string;
  display_name: string;
  description: string;
  base_price: number;
  price_per_user: number;
  included_users: number;
  max_users: number;
  features: string[];
  stripe_price_id: string | null;
}

export interface AvailablePlan {
  name: string;
  display_name: string;
  base_price: number;
}

export interface OnboardingConfig {
  id?: number;
  config_key: string;
  display_name: string;
  steps_config: OnboardingStep[];
  visible_plans: string[];
  plans_detail?: PlanDetail[];
  portal_menu: PortalMenuItem[];
  welcome_title: string;
  welcome_subtitle: string;
  allow_plan_change: boolean;
  allow_cancel: boolean;
  allow_email_change: boolean;
  show_invoices: boolean;
  show_usage: boolean;
  ecf_countries: string[];
  is_active?: boolean;
  available_plans?: AvailablePlan[];
  created_at?: string;
  updated_at?: string;
}

export interface ConfigListResponse {
  items: OnboardingConfig[];
  total: number;
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data as T;
}

export const onboardingConfigApi = {
  /** Obtiene la configuración activa (pública, sin auth) */
  getActive(): Promise<OnboardingConfig> {
    return request<OnboardingConfig>(`${BASE}/active`);
  },

  // ── Admin ──────────────────────────────────────────────────

  list(): Promise<ConfigListResponse> {
    return request<ConfigListResponse>(`${BASE}/admin`);
  },

  get(key: string): Promise<OnboardingConfig> {
    return request<OnboardingConfig>(`${BASE}/admin/${key}`);
  },

  create(data: Partial<OnboardingConfig> & { config_key: string }): Promise<{ message: string; config: OnboardingConfig }> {
    return request(`${BASE}/admin`, { method: 'POST', body: JSON.stringify(data) });
  },

  update(key: string, data: Partial<OnboardingConfig>): Promise<{ message: string; config: OnboardingConfig }> {
    return request(`${BASE}/admin/${key}`, { method: 'PUT', body: JSON.stringify(data) });
  },

  delete(key: string): Promise<{ message: string }> {
    return request(`${BASE}/admin/${key}`, { method: 'DELETE' });
  },

  activate(key: string): Promise<{ message: string; is_active: boolean }> {
    return request(`${BASE}/admin/${key}/activate`, { method: 'POST' });
  },
};
