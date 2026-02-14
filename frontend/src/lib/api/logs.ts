import api from './client';
import type { LogsResponse, SystemStatusResponse } from '../types';

export const logsApi = {
  async getProvisioningLogs(lines = 100, level?: string): Promise<LogsResponse> {
    const params = new URLSearchParams({ lines: String(lines) });
    if (level) params.set('level', level);
    return api.get<LogsResponse>(`/api/logs/provisioning?${params.toString()}`);
  },

  async getSystemLogs(lines = 50): Promise<LogsResponse> {
    return api.get<LogsResponse>(`/api/logs/system?lines=${lines}`);
  },

  async getSystemStatus(): Promise<SystemStatusResponse> {
    return api.get<SystemStatusResponse>('/api/logs/status');
  },
};

export default logsApi;
