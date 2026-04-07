import api from './client';
import type {
  BillingInvoicesResponse,
  BillingSubscriptionsResponse,
  BillingMetrics,
  StripeEventsResponse,
  PlansResponse,
  Plan,
  PlanCalculation,
  CustomersResponse,
  CustomerItem,
} from '../types';

export interface BillingComparison {
  current_month: string;
  previous_month: string;
  current_mrr: number;
  previous_mrr: number;
  current_revenue: number;
  previous_revenue: number;
  new_customers: number;
  lost_customers: number;
}

export const billingApi = {
  // Billing
  async getMetrics(): Promise<BillingMetrics> {
    return api.get<BillingMetrics>('/api/billing/metrics');
  },

  async getInvoices(limit = 20, offset = 0): Promise<BillingInvoicesResponse> {
    return api.get<BillingInvoicesResponse>(`/api/billing/invoices?limit=${limit}&offset=${offset}`);
  },

  async getSubscriptions(limit = 20, offset = 0): Promise<BillingSubscriptionsResponse> {
    return api.get<BillingSubscriptionsResponse>(`/api/billing/subscriptions?limit=${limit}&offset=${offset}`);
  },

  async getComparison(): Promise<BillingComparison> {
    return api.get<BillingComparison>('/api/billing/comparison');
  },

  async getStripeEvents(limit = 20): Promise<StripeEventsResponse> {
    return api.get<StripeEventsResponse>(`/api/billing/stripe-events?limit=${limit}`);
  },

  // Plans CRUD
  async getPlans(includeInactive = false): Promise<PlansResponse> {
    return api.get<PlansResponse>(`/api/plans?include_inactive=${includeInactive}`);
  },

  async createPlan(data: Partial<Plan>): Promise<{ message: string; plan: { id: number; name: string } }> {
    return api.post('/api/plans', data);
  },

  async updatePlan(id: number, data: Partial<Plan>): Promise<{ message: string }> {
    return api.put(`/api/plans/${id}`, data);
  },

  async deletePlan(id: number): Promise<{ message: string }> {
    return api.delete(`/api/plans/${id}`);
  },

  async calculatePrice(planName: string, userCount: number): Promise<PlanCalculation> {
    return api.post<PlanCalculation>('/api/plans/calculate', { plan_name: planName, user_count: userCount });
  },

  // Customers Management
  async getCustomers(partnerId?: number): Promise<CustomersResponse> {
    const qs = partnerId ? `?partner_id=${partnerId}` : '';
    return api.get<CustomersResponse>(`/api/customers${qs}`);
  },

  async createCustomer(data: {
    company_name: string;
    email: string;
    full_name?: string;
    subdomain: string;
    plan_name?: string;
    user_count?: number;
    partner_id?: number;
    auto_provision?: boolean;
  }): Promise<{
    id: number;
    message: string;
    customer?: { id: number };
    tenant?: {
      admin_login: string;
      admin_password: string;
      subdomain: string;
      url: string;
      server: string;
      status: string;
    };
    tenant_error?: string;
  }> {
    return api.post('/api/customers', data);
  },

  async updateCustomer(id: number, data: {
    company_name?: string;
    user_count?: number;
    is_admin_account?: boolean;
    plan_name?: string;
    stripe_customer_id?: string;
        email?: string;
        stripe_action?: string;
  }): Promise<{ message: string; changes: string[] }> {
    return api.put(`/api/customers/${id}`, data);
  },

  async updateUserCount(id: number, userCount: number): Promise<{
    customer_id: number;
    old_user_count: number;
    new_user_count: number;
    plan?: string;
    old_monthly?: number;
    new_monthly?: number;
    difference?: number;
  }> {
    return api.put(`/api/customers/${id}/users`, { user_count: userCount });
  },

  async recalculateAll(): Promise<{ message: string; admin_accounts: number; details: any[] }> {
    return api.post('/api/customers/recalculate-all', {});
  },

  async createStripeCustomer(id: number): Promise<{
    success: boolean;
    already_exists: boolean;
    stripe_customer_id?: string;
        email?: string;
        stripe_action?: string;
    message: string;
  }> {
    return api.post(`/api/customers/${id}/create-stripe-customer`, {});
  },

  async sendCredentials(id: number): Promise<{
    success: boolean;
    message: string;
    email_to?: string;
  }> {
    return api.post(`/api/customers/${id}/send-credentials`, {});
  },

  async resetPassword(id: number): Promise<{
    success: boolean;
    password_reset: boolean;
    email_sent: boolean;
    message: string;
  }> {
    return api.post(`/api/customers/${id}/reset-password`, {});
  },
};

export default billingApi;
