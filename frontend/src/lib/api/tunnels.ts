import { api } from './client';

export interface TunnelDeployment {
  subdomain: string;
  domain: string;
  url: string;
  plan: string;
  subscription_id: string;
}

export interface Tunnel {
  id: string;
  name: string;
  status: string;
  created_at?: string;
  deployment?: TunnelDeployment | null;
}

export interface TunnelsListResponse {
  success: boolean;
  total: number;
  tunnels: Tunnel[];
  warning?: string;
  error?: string;
}

export const tunnelsApi = {
  list(): Promise<TunnelsListResponse> {
    return api.get('/api/tunnels');
  },

  getStatus(tunnelId: string): Promise<Record<string, unknown>> {
    return api.get(`/api/tunnels/${tunnelId}/status`);
  },

  getLogs(tunnelId: string, lines = 50): Promise<{ tunnel_id: string; lines_count: number; logs: string[] }> {
    return api.get(`/api/tunnels/${tunnelId}/logs?lines=${lines}`);
  },

  create(subscriptionId: string, containerId: number, localPort = 8069): Promise<Record<string, unknown>> {
    return api.post(`/api/tunnels?subscription_id=${subscriptionId}&container_id=${containerId}&local_port=${localPort}`, {});
  },

  delete(tunnelId: string): Promise<{ success: boolean; message: string }> {
    return api.delete(`/api/tunnels/${tunnelId}`);
  },

  restart(tunnelId: string): Promise<Record<string, unknown>> {
    return api.post(`/api/tunnels/${tunnelId}/restart`, {});
  },
};
