import api from './client';
import type { DashboardMetrics } from '../types';

export interface DashboardAll {
  metrics: DashboardMetrics;
  tenants: any[];
  infrastructure: {
    nodes: any[];
    containers: any[];
  };
  timestamp: string;
}

export const dashboardApi = {
  async getMetrics(): Promise<DashboardMetrics> {
    return api.get<DashboardMetrics>('/api/dashboard/metrics');
  },

  async getAll(): Promise<DashboardAll> {
    return api.get<DashboardAll>('/api/dashboard/all');
  },
};

export default dashboardApi;
