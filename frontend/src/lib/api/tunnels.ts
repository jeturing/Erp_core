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

export interface DeploymentItem {
  id: number;
  subdomain: string;
  database_name: string | null;
  tunnel_id: string | null;
  tunnel_active: boolean;
  tunnel_url: string | null;
  direct_url: string | null;
  plan_type: string | null;
  subscription_id: number | null;
  company_name: string | null;
  stripe_subscription_id: string | null;
  stripe_status: string | null;
}

export interface AuthorizedDomain {
  domain: string;
  zone_id: string;
  source: string;
}

export interface CreateTunnelOptions {
  name: string;
  domain?: string;
  hostname?: string;
  deployment_id?: number;
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

  createAdvanced(options: CreateTunnelOptions): Promise<Record<string, unknown>> {
    const qs = new URLSearchParams();
    qs.set('name', options.name);
    if (options.domain) qs.set('domain', options.domain);
    if (options.hostname) qs.set('hostname', options.hostname);
    if (typeof options.deployment_id === 'number') qs.set('deployment_id', String(options.deployment_id));
    return api.post(`/api/tunnels?${qs.toString()}`, {});
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

  /** Deployments disponibles para vincular */
  listDeployments(): Promise<{ success: boolean; deployments: DeploymentItem[]; total: number }> {
    return api.get('/api/tunnels/deployments/available');
  },

  listAuthorizedDomains(): Promise<{ success: boolean; domains: AuthorizedDomain[]; total: number }> {
    return api.get('/api/tunnels/domains/available');
  },

  /** Vincular tunnel → deployment */
  linkDeployment(tunnelId: string, deploymentId: number): Promise<Record<string, unknown>> {
    return api.post(`/api/tunnels/${tunnelId}/link`, { deployment_id: deploymentId });
  },

  /** Desvincular tunnel de deployment */
  unlinkDeployment(tunnelId: string): Promise<Record<string, unknown>> {
    return api.delete(`/api/tunnels/${tunnelId}/link`);
  },

  /** Vincular deployment/tunnel a subscription Stripe */
  linkStripe(tunnelId: string, subscriptionId: number): Promise<Record<string, unknown>> {
    return api.post(`/api/tunnels/${tunnelId}/link-stripe`, { subscription_id: subscriptionId });
  },
};
