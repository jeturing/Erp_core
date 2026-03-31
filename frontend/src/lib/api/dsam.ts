/**
 * DSAM — Dynamic Session & Anti-Theft Monitor API Client
 * Endpoints para monitoreo de sesiones, reglas de seguridad, geo-mapa y playbook.
 */
import api from './client';

// ── Types ──

export interface SessionEntry {
  id: number;
  redis_key: string;
  tenant_db: string;
  odoo_login: string | null;
  odoo_uid: number | null;
  ip_address: string;
  country: string | null;
  country_code: string | null;
  region: string | null;
  city: string | null;
  lat: number | null;
  lon: number | null;
  session_start: string | null;
  last_activity: string | null;
  first_seen: string | null;
  is_active: boolean;
}

export interface DashboardStats {
  total_active: number;
  by_tenant: { tenant: string; count: number }[];
  by_country: { code: string; country: string; count: number }[];
  unresolved_alerts: number;
  critical_alerts: number;
}

export interface SecurityRule {
  id: number;
  rule_type: string;
  tenant_db: string | null;
  is_enabled: boolean;
  config: Record<string, any>;
  exempt_users: string[];
  exempt_tenants: string[];
  description: string | null;
}

export interface SecurityAction {
  id: number;
  action_type: string;
  severity: string;
  tenant_db: string;
  odoo_login: string | null;
  ip_address: string | null;
  details: Record<string, any>;
  actor_username: string | null;
  resolved: boolean;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_note: string | null;
  created_at: string | null;
}

export interface TenantSessionConfig {
  id: number;
  tenant_db: string;
  allow_multiple_sessions: boolean;
  max_concurrent_sessions: number;
  enforce_geo_restrictions: boolean;
  enforce_impossible_travel: boolean;
  allowed_countries: string[];
  session_timeout_minutes: number;
  notify_on_new_device: boolean;
  seat_audit_enabled: boolean;
  last_seat_audit_at: string | null;
}

export interface GeoPoint {
  country_code: string;
  country: string;
  city: string;
  lat: number;
  lon: number;
  count: number;
}

export interface LiveSession {
  tenant_db: string;
  odoo_login: string;
  ip: string;
  country: string;
  city: string;
  lat: number;
  lon: number;
  last_activity: string | null;
}

export interface SeatAuditEntry {
  tenant_db: string;
  subscription_id: number;
  seats_purchased: number;
  unique_active_users: number;
  total_active_sessions: number;
  seats_diff: number;
  over_limit: boolean;
  plan: string | null;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta: Record<string, any>;
}

// ── API Client ──

export const dsamApi = {
  // Dashboard
  async getDashboard(): Promise<ApiResponse<DashboardStats>> {
    return api.get('/api/dsam/dashboard');
  },

  // Sync Redis → DB
  async syncSessions(): Promise<ApiResponse<{ scanned: number; created: number; updated: number; removed: number }>> {
    return api.post('/api/dsam/sync', {});
  },

  // Sessions
  async listSessions(params?: {
    tenant?: string;
    active_only?: boolean;
    page?: number;
    limit?: number;
  }): Promise<ApiResponse<SessionEntry[]>> {
    const query = new URLSearchParams();
    if (params?.tenant) query.set('tenant', params.tenant);
    if (params?.active_only !== undefined) query.set('active_only', String(params.active_only));
    if (params?.page) query.set('page', String(params.page));
    if (params?.limit) query.set('limit', String(params.limit));
    const qs = query.toString();
    return api.get(`/api/dsam/sessions${qs ? '?' + qs : ''}`);
  },

  async getSessionsByTenant(tenantDb: string): Promise<ApiResponse<SessionEntry[]>> {
    return api.get(`/api/dsam/sessions/tenant/${tenantDb}`);
  },

  async terminateSession(sessionKey: string, reason: string = 'Admin requested'): Promise<ApiResponse<any>> {
    return api.post('/api/dsam/sessions/terminate', { session_key: sessionKey, reason });
  },

  // Geo
  async getGeoHeatmap(days: number = 30): Promise<ApiResponse<GeoPoint[]>> {
    return api.get(`/api/dsam/geo/heatmap?days=${days}`);
  },

  async getGeoLive(): Promise<ApiResponse<LiveSession[]>> {
    return api.get('/api/dsam/geo/live');
  },

  // Rules
  async listRules(tenant?: string): Promise<ApiResponse<SecurityRule[]>> {
    const qs = tenant ? `?tenant=${tenant}` : '';
    return api.get(`/api/dsam/rules${qs}`);
  },

  async createRule(rule: {
    rule_type: string;
    tenant_db?: string | null;
    config?: Record<string, any>;
    exempt_users?: string[];
    exempt_tenants?: string[];
    description?: string;
    is_enabled?: boolean;
  }): Promise<ApiResponse<{ id: number }>> {
    return api.post('/api/dsam/rules', rule);
  },

  async updateRule(ruleId: number, rule: any): Promise<ApiResponse<{ id: number }>> {
    return api.put(`/api/dsam/rules/${ruleId}`, rule);
  },

  async deleteRule(ruleId: number): Promise<ApiResponse<{ deleted: number }>> {
    return api.delete(`/api/dsam/rules/${ruleId}`);
  },

  // Tenant Config
  async getTenantConfig(tenantDb: string): Promise<ApiResponse<TenantSessionConfig | null>> {
    return api.get(`/api/dsam/config/${tenantDb}`);
  },

  async upsertTenantConfig(tenantDb: string, config: Partial<TenantSessionConfig>): Promise<ApiResponse<any>> {
    return api.put(`/api/dsam/config/${tenantDb}`, config);
  },

  // Security Actions / Playbook
  async listActions(params?: {
    tenant?: string;
    severity?: string;
    resolved?: boolean;
    page?: number;
    limit?: number;
  }): Promise<ApiResponse<SecurityAction[]>> {
    const query = new URLSearchParams();
    if (params?.tenant) query.set('tenant', params.tenant);
    if (params?.severity) query.set('severity', params.severity);
    if (params?.resolved !== undefined) query.set('resolved', String(params.resolved));
    if (params?.page) query.set('page', String(params.page));
    if (params?.limit) query.set('limit', String(params.limit));
    const qs = query.toString();
    return api.get(`/api/dsam/actions${qs ? '?' + qs : ''}`);
  },

  async resolveAction(actionId: number, note: string): Promise<ApiResponse<any>> {
    return api.put(`/api/dsam/actions/${actionId}/resolve`, { resolution_note: note });
  },

  // Account Lock/Unlock
  async lockAccount(tenantDb: string, odooLogin: string, reason: string): Promise<ApiResponse<any>> {
    return api.post('/api/dsam/accounts/lock', { tenant_db: tenantDb, odoo_login: odooLogin, reason });
  },

  async unlockAccount(tenantDb: string, odooLogin: string, reason: string): Promise<ApiResponse<any>> {
    return api.post('/api/dsam/accounts/unlock', { tenant_db: tenantDb, odoo_login: odooLogin, reason });
  },

  // Security Scan
  async runScan(): Promise<ApiResponse<any>> {
    return api.post('/api/dsam/scan', {});
  },

  // Seat Audit
  async runSeatAudit(): Promise<ApiResponse<any>> {
    return api.post('/api/dsam/audit/seats', {});
  },

  async getSeatReconciliation(tenant?: string): Promise<ApiResponse<any>> {
    const qs = tenant ? `?tenant=${tenant}` : '';
    return api.get(`/api/dsam/audit/reconciliation${qs}`);
  },
};

export default dsamApi;
