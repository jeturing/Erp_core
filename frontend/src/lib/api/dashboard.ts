import api from './client';
import type { DashboardMetrics } from '../types';

export const dashboardApi = {
  async getMetrics(): Promise<DashboardMetrics> {
    return api.get<DashboardMetrics>('/api/dashboard/metrics');
  },
};

export default dashboardApi;
