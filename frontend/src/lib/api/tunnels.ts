import { api } from './client';

// ─── Tipos ─────────────────────────────────────────────
export interface TunnelConnection {
  colo_name: string;
  is_pending_reconnect: boolean;
  origin_ip: string;
  opened_at: string;
}

export interface TunnelDnsRecord {
  record_id: string;
  name: string;
  proxied: boolean;
}

export interface TunnelStripeInfo {
  subscription_id: string | null;
  status: string | null;
  plan_name: string | null;
}

export interface TunnelDeployment {
  id?: number;
  subdomain: string;
  domain: string | null;
  url: string | null;
  direct_url: string | null;
  plan: string | null;
  database_name: string | null;
  subscription_id: string | null;
  stripe: TunnelStripeInfo | null;
}

export interface Tunnel {
  id: string;
  name: string;
  status: 'healthy' | 'down' | 'inactive' | 'deleted' | string;
  created_at: string;
  connections_count: number;
  connections: TunnelConnection[];
  tunnel_type: string;
  remote_config: boolean;
  dns_records: TunnelDnsRecord[];
  dns_count: number;
  deployment: TunnelDeployment | null;
}

export interface TunnelStats {
  healthy: number;
  down: number;
  inactive: number;
  total_dns_cnames: number;
}

export interface TunnelsListResponse {
  success: boolean;
  total: number;
  tunnels: Tunnel[];
  stats: TunnelStats;
  warning?: string;
  error?: string;
}

export interface TunnelDetailResponse {
  success: boolean;
  tunnel: Tunnel & {
    config?: {
      ingress: { hostname: string; service: string; path: string }[];
      total_rules: number;
    } | null;
  };
}

// ─── API ───────────────────────────────────────────────
export const tunnelsApi = {
  list(): Promise<TunnelsListResponse> {
    return api.get('/api/tunnels');
  },

  getDetail(tunnelId: string): Promise<TunnelDetailResponse> {
    return api.get(`/api/tunnels/${tunnelId}`);
  },

  getStatus(tunnelId: string): Promise<Record<string, unknown>> {
    return api.get(`/api/tunnels/${tunnelId}/status`);
  },

  getConfig(tunnelId: string): Promise<Record<string, unknown>> {
    return api.get(`/api/tunnels/${tunnelId}/config`);
  },

  getToken(tunnelId: string): Promise<{ success: boolean; token: string }> {
    return api.get(`/api/tunnels/${tunnelId}/token`);
  },

  create(name: string): Promise<Record<string, unknown>> {
    return api.post(`/api/tunnels?name=${encodeURIComponent(name)}`, {});
  },

  delete(tunnelId: string): Promise<{ success: boolean; message: string }> {
    return api.delete(`/api/tunnels/${tunnelId}`);
  },

  restart(tunnelId: string): Promise<Record<string, unknown>> {
    return api.post(`/api/tunnels/${tunnelId}/restart`, {});
  },

  verifyToken(): Promise<{ success: boolean; status: string }> {
    return api.get('/api/tunnels/verify/api-token');
  },

  listDns(domain = 'sajet.us', recordType?: string): Promise<Record<string, unknown>> {
    let url = `/api/tunnels/dns/records?domain=${encodeURIComponent(domain)}`;
    if (recordType) url += `&record_type=${recordType}`;
    return api.get(url);
  },
};
