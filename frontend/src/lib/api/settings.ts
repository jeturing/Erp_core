import api from './client';
import type { OdooSettingsResponse, SettingsResponse } from '../types';

export interface CredentialItem {
  key: string;
  value: string;
  raw_length: number;
  description: string;
  is_secret: boolean;
  is_set: boolean;
  source: 'database' | 'env' | 'not_set';
}

export interface CredentialCategory {
  label: string;
  items: CredentialItem[];
}

export interface CredentialsResponse {
  success: boolean;
  credentials: Record<string, CredentialCategory>;
}

export interface StripeModeResponse {
  success: boolean;
  app: 'sajet' | 'med';
  app_label: string;
  app_host: string;
  mode: 'test' | 'sandbox' | 'live';
  mode_label: string;
  detected_mode: string;
  active_secret_key_prefix: string;
  active_publishable_key: string;
  has_test_keys: boolean;
  has_sandbox_keys: boolean;
  has_live_keys: boolean;
  coherence_warning?: string | null;
  requires_restart?: boolean;
  cache_ttl_seconds?: number;
}

export interface StripeModeSetResponse {
  success: boolean;
  app: 'sajet' | 'med';
  mode: string;
  mode_label?: string;
  message: string;
  active_key_prefix: string;
  requires_restart: boolean;
  cache_ttl_seconds?: number;
}

export interface EnvironmentInfo {
  key: string;
  label: string;
  description: string;
  env_file: string;
  color: string;
  available: boolean;
  is_active: boolean;
  db_host: string;
  stripe_mode: string;
}

export interface EnvironmentResponse {
  success: boolean;
  current: string;
  env_file: string;
  database_host: string;
  database_name: string;
  stripe_mode: string;
  app_url: string;
  environments: EnvironmentInfo[];
}

export interface EnvironmentSwitchResponse {
  success: boolean;
  message: string;
  requires_restart: boolean;
  previous?: string;
  current: string;
  target_db?: string;
}

export const settingsApi = {
  async getAll(category?: string): Promise<SettingsResponse> {
    const suffix = category ? `?category=${encodeURIComponent(category)}` : '';
    return api.get<SettingsResponse>(`/api/settings${suffix}`);
  },

  async updateConfig(key: string, value: string, description?: string): Promise<{ success: boolean; key: string; message: string }> {
    return api.put(`/api/settings/${encodeURIComponent(key)}`, {
      key,
      value,
      description,
    });
  },

  async getOdooCurrent(): Promise<OdooSettingsResponse> {
    return api.get<OdooSettingsResponse>('/api/settings/odoo/current');
  },

  async updateOdooConfig(payload: {
    admin_login?: string;
    admin_password?: string;
    master_password?: string;
    db_user?: string;
    db_password?: string;
    default_lang?: string;
    default_country?: string;
    base_domain?: string;
    template_db?: string;
  }): Promise<{ success: boolean; message: string }> {
    return api.put('/api/settings/odoo', payload);
  },

  // ── Credential Management ──

  async getCredentials(category?: string): Promise<CredentialsResponse> {
    const suffix = category ? `?category=${encodeURIComponent(category)}` : '';
    return api.get<CredentialsResponse>(`/api/settings/credentials${suffix}`);
  },

  async updateCredential(key: string, value: string, category: string = 'general', is_secret: boolean = true): Promise<{ success: boolean }> {
    return api.put(`/api/settings/credentials/${encodeURIComponent(key)}`, {
      key,
      value,
      category,
      is_secret,
    });
  },

  // ── Stripe Mode ──

  async getStripeMode(app: 'sajet' | 'med' = 'sajet'): Promise<StripeModeResponse> {
    return api.get<StripeModeResponse>(`/api/settings/stripe/mode?app=${encodeURIComponent(app)}`);
  },

  async setStripeMode(payload: {
    mode: 'test' | 'sandbox' | 'live';
    test_secret_key?: string;
    test_publishable_key?: string;
    test_webhook_secret?: string;
    sandbox_secret_key?: string;
    sandbox_publishable_key?: string;
    sandbox_webhook_secret?: string;
    live_secret_key?: string;
    live_publishable_key?: string;
    live_webhook_secret?: string;
  }, app: 'sajet' | 'med' = 'sajet'): Promise<StripeModeSetResponse> {
    return api.post(`/api/settings/stripe/mode?app=${encodeURIComponent(app)}`, payload);
  },

  // ── Environment ──

  async getEnvironment(): Promise<EnvironmentResponse> {
    return api.get<EnvironmentResponse>('/api/settings/environment/current');
  },

  async switchEnvironment(environment: string): Promise<EnvironmentSwitchResponse> {
    return api.put<EnvironmentSwitchResponse>('/api/settings/environment/switch', { environment });
  },
};

export default settingsApi;
