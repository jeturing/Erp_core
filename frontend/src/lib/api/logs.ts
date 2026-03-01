import { api } from './client';

export interface LogEntry {
  line: string;
  class: string;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  file?: string;
  source?: string;
  error?: string;
}

export interface SystemStatus {
  postgresql: { status: string; latency_ms?: number | null; error?: string };
  fastapi: { status: string; port: number };
  lxc_105: { status: string; name: string };
  disk: { usage_percent: number; free_gb: number };
}

export const logsApi = {
  getProvisioningLogs(lines = 100, level?: string, tenant?: string): Promise<LogsResponse> {
    const params = new URLSearchParams({ lines: String(lines) });
    if (level) params.set('level', level);
    if (tenant) params.set('tenant', tenant);
    return api.get(`/api/logs/provisioning?${params}`);
  },

  getAppLogs(lines = 100, level?: string, tenant?: string): Promise<LogsResponse> {
    const params = new URLSearchParams({ lines: String(lines) });
    if (level) params.set('level', level);
    if (tenant) params.set('tenant', tenant);
    return api.get(`/api/logs/app?${params}`);
  },

  getSystemLogs(lines = 50): Promise<LogsResponse> {
    return api.get(`/api/logs/system?lines=${lines}`);
  },

  getSystemStatus(): Promise<SystemStatus> {
    return api.get('/api/logs/status');
  },
};
