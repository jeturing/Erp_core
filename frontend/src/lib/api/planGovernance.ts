import api from './client';

export interface GovernancePlan {
  id: number;
  name: string;
  display_name: string;
  max_users: number;
  max_storage_mb: number;
  max_stock_sku: number;
  quota_warning_percent: number;
  quota_recommend_percent: number;
  quota_block_percent: number;
  fair_use_new_customers_only: boolean;
}

export interface GovernanceCustomerSummary {
  customer_id: number;
  company_name: string;
  subdomain: string;
  plan_name: string;
  plan_key: string;
  fair_use_enabled: boolean;
  top_resource: string | null;
  top_resource_label: string | null;
  top_usage_percent: number;
  top_status: 'ok' | 'warning' | 'critical' | 'exceeded' | string;
  recommendation?: {
    plan_name: string;
    display_name: string;
    resource: string;
    resource_label: string;
    new_limit: number;
  } | null;
  resources: Record<string, {
    used: number;
    limit: number;
    unlimited: boolean;
    exceeded: boolean;
    status?: string;
  }>;
}

export interface PlanGovernanceSummaryResponse {
  success: boolean;
  new_only: boolean;
  total: number;
  plans: GovernancePlan[];
  customers: GovernanceCustomerSummary[];
}

export const planGovernanceApi = {
  async getSummary(newOnly = true): Promise<PlanGovernanceSummaryResponse> {
    return api.get(`/api/plan-governance/summary?new_only=${newOnly}`);
  },

  async getCustomer(customerId: number): Promise<any> {
    return api.get(`/api/plan-governance/customer/${customerId}`);
  },
};

export default planGovernanceApi;
