import api from './client';
import type { TunnelsListResponse } from '../types';

export interface CreateTunnelPayload {
  subscription_id: string;
  container_id: number;
  local_port?: number;
}

export const tunnelsApi = {
  async listTunnels(): Promise<TunnelsListResponse> {
    return api.get<TunnelsListResponse>('/api/tunnels');
  },

  async createTunnel(payload: CreateTunnelPayload): Promise<{ success: boolean; message?: string }> {
    const params = new URLSearchParams({
      subscription_id: payload.subscription_id,
      container_id: String(payload.container_id),
      local_port: String(payload.local_port ?? 8069),
    });
    return api.post(`/api/tunnels?${params.toString()}`);
  },

  async deleteTunnel(tunnelId: string): Promise<{ success: boolean; message?: string }> {
    return api.delete(`/api/tunnels/${encodeURIComponent(tunnelId)}`);
  },
};

export default tunnelsApi;
