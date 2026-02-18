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

// ── Reports Overview (consolidated analytics) ──
export interface PlanDistItem {
  count: number;
  revenue: number;
  users: number;
}

export interface ReportsOverview {
  generated_at: string;

  revenue: {
    mrr: number;
    arr: number;
    pending_amount: number;
    pending_count: number;
    churn_rate: number;
    total_users: number;
    plan_distribution: Record<string, PlanDistItem>;
    new_this_month: number;
    cancelled_30d: number;
  };

  customers: {
    total: number;
    active: number;
    suspended: number;
    active_subscriptions: number;
  };

  partners: {
    total: number;
    active: number;
    pending: number;
    top: Array<{
      id: number;
      company_name: string;
      leads: number;
      total_revenue: number;
      total_commissions: number;
    }>;
  };

  leads: {
    total: number;
    active: number;
    won: number;
    pipeline_value: number;
    pipeline: Record<string, number>;
  };

  commissions: {
    total_partner: number;
    pending: number;
    paid: number;
    jeturing_share: number;
  };

  infrastructure: {
    nodes_total: number;
    nodes_online: number;
    containers_total: number;
    containers_running: number;
    cpu: { used: number; total: number; percent: number };
    ram: { used: number; total: number; percent: number };
    disk: { used: number; total: number; percent: number };
  };

  settlements: {
    open: number;
    closed: number;
    total_partner_payout: number;
  };

  work_orders: {
    total: number;
    requested: number;
    in_progress: number;
    completed: number;
  };

  reconciliation: {
    total_runs: number;
    clean: number;
    issues: number;
  };

  invoices: {
    total: number;
    paid: number;
    pending: number;
    total_amount: number;
    paid_amount: number;
  };

  system_health: Array<{
    name: string;
    status: 'ok' | 'warning' | 'error';
    detail: string;
  }>;

  recent_activity: Array<{
    id: number;
    company_name: string;
    email: string;
    subdomain: string;
    status: string;
    plan: string;
    user_count: number;
    monthly_amount: number;
    created_at: string | null;
  }>;

  recent_stripe_events: Array<{
    event_id: string;
    event_type: string;
    processed: boolean;
    created_at: string | null;
  }>;
}

export const dashboardApi = {
  async getMetrics(): Promise<DashboardMetrics> {
    return api.get<DashboardMetrics>('/api/dashboard/metrics');
  },

  async getAll(): Promise<DashboardAll> {
    return api.get<DashboardAll>('/api/dashboard/all');
  },

  async getOverview(): Promise<ReportsOverview> {
    return api.get<ReportsOverview>('/api/reports/overview');
  },
};

export default dashboardApi;
