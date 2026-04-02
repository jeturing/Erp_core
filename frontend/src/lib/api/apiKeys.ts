// API Keys Management — Stripe-style key management
import { api } from './client';

// ── Types ──

export type ApiKeyStatus = 'active' | 'revoked' | 'expired' | 'rotated';
export type ApiKeyScope = 'read_only' | 'read_write' | 'admin';
export type ApiKeyTier = 'free' | 'standard' | 'premium' | 'enterprise' | 'unlimited';

export interface RateLimits {
  requests_per_minute: number;
  requests_per_day: number | null;
  monthly_quota_tokens: number | null;
}

export interface ApiKeyUsage {
  today: number;
  month: number;
  total: number;
}

export interface ApiKeyItem {
  key_id: string;
  name: string;
  description: string | null;
  status: ApiKeyStatus;
  scope: ApiKeyScope;
  tier: ApiKeyTier;
  permissions: string[];
  tags: string[];
  tenant_id: number | null;
  customer_id: number | null;
  rate_limits: RateLimits;
  usage: ApiKeyUsage;
  last_used_at: string | null;
  last_used_ip: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string | null;
  rotated_at: string | null;
  /** Only present on create/rotate — shown ONCE */
  api_key?: string;
  _note?: string;
}

export interface ApiKeyListResponse {
  data: ApiKeyItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ApiKeyCreateRequest {
  name: string;
  description?: string;
  scope?: ApiKeyScope;
  tier?: ApiKeyTier;
  permissions?: string[];
  tenant_id?: number;
  customer_id?: number;
  expires_in_days?: number;
  tags?: string[];
  requests_per_minute?: number;
  requests_per_day?: number;
  monthly_quota_tokens?: number;
}

export interface ApiKeyUpdateRequest {
  name?: string;
  description?: string;
  scope?: ApiKeyScope;
  tier?: ApiKeyTier;
  permissions?: string[];
  tags?: string[];
  expires_in_days?: number;
  requests_per_minute?: number;
  requests_per_day?: number;
  monthly_quota_tokens?: number;
}

export interface TierInfo {
  name: string;
  requests_per_minute: number;
  requests_per_day: number | null;
  monthly_quota_tokens: number | null;
  unlimited_rpd: boolean;
  unlimited_tokens: boolean;
}

export interface UsageBucket {
  hour: string;
  count: number;
}

// ── API Client ──

export const apiKeysApi = {
  /** List API keys with optional filters and pagination */
  async list(params?: {
    status_filter?: ApiKeyStatus;
    tier_filter?: ApiKeyTier;
    customer_id?: number;
    tenant_id?: number;
    page?: number;
    per_page?: number;
  }): Promise<ApiKeyListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.status_filter) searchParams.set('status_filter', params.status_filter);
    if (params?.tier_filter) searchParams.set('tier_filter', params.tier_filter);
    if (params?.customer_id) searchParams.set('customer_id', String(params.customer_id));
    if (params?.tenant_id) searchParams.set('tenant_id', String(params.tenant_id));
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.per_page) searchParams.set('per_page', String(params.per_page));
    const qs = searchParams.toString();
    return api.get<ApiKeyListResponse>(`/api/api-keys${qs ? `?${qs}` : ''}`);
  },

  /** Create a new API key — returns secret ONCE */
  async create(data: ApiKeyCreateRequest): Promise<{ success: boolean; data: ApiKeyItem }> {
    return api.post('/api/api-keys', data);
  },

  /** Get a single API key by key_id */
  async get(keyId: string): Promise<ApiKeyItem> {
    return api.get<ApiKeyItem>(`/api/api-keys/${keyId}`);
  },

  /** Update an API key */
  async update(keyId: string, data: ApiKeyUpdateRequest): Promise<{ success: boolean; data: ApiKeyItem }> {
    return api.put(`/api/api-keys/${keyId}`, data);
  },

  /** Rotate an API key (Stripe-style) — returns new secret ONCE */
  async rotate(keyId: string): Promise<{ success: boolean; data: ApiKeyItem }> {
    return api.post(`/api/api-keys/${keyId}/rotate`, {});
  },

  /** Revoke (delete) an API key */
  async revoke(keyId: string): Promise<{ success: boolean; message: string }> {
    return api.delete(`/api/api-keys/${keyId}`);
  },

  /** Get usage histogram for a key */
  async getUsage(keyId: string, hours?: number): Promise<{ key_id: string; buckets: UsageBucket[]; total: number }> {
    const qs = hours ? `?hours=${hours}` : '';
    return api.get(`/api/api-keys/${keyId}/usage${qs}`);
  },

  /** Get available rate limit tiers (public) */
  async getTiers(): Promise<{ tiers: TierInfo[] }> {
    return api.get('/api/api-keys/tiers');
  },
};
