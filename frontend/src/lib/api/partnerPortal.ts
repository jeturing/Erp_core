import api from './client';
import type {
  PartnerOnboardingStatus,
  PartnerDashboard,
  PartnerLeadsResponse,
  PartnerLeadItem,
  PartnerProfile,
  PartnerClientItem,
  PartnerCommissionItem,
} from '../types';

const BASE = '/api/partner-portal';

export const partnerPortalApi = {
  // ── Onboarding ──
  async getOnboardingStatus(): Promise<PartnerOnboardingStatus> {
    return api.get<PartnerOnboardingStatus>(`${BASE}/onboarding/status`);
  },

  async setPassword(password: string, password_confirm: string): Promise<{ message: string; onboarding_step: number }> {
    return api.post(`${BASE}/onboarding/set-password`, { password, password_confirm });
  },

  async updateProfile(data: Record<string, string | null>): Promise<{ message: string; onboarding_step: number }> {
    return api.post(`${BASE}/onboarding/update-profile`, data);
  },

  async startStripe(): Promise<{ account_id?: string; onboarding_url?: string; message?: string }> {
    return api.post(`${BASE}/onboarding/start-stripe`);
  },

  async verifyStripe(): Promise<{
    charges_enabled: boolean;
    details_submitted: boolean;
    payouts_enabled: boolean;
    onboarding_step: number;
    onboarding_complete: boolean;
  }> {
    return api.post(`${BASE}/onboarding/verify-stripe`);
  },

  async skipStripe(): Promise<{ message: string; onboarding_step: number }> {
    return api.post(`${BASE}/onboarding/skip-stripe`);
  },

  // ── Dashboard ──
  async getDashboard(): Promise<PartnerDashboard> {
    return api.get<PartnerDashboard>(`${BASE}/dashboard`);
  },

  // ── Leads ──
  async getLeads(status?: string): Promise<PartnerLeadsResponse> {
    const qs = status ? `?status_filter=${status}` : '';
    return api.get<PartnerLeadsResponse>(`${BASE}/leads${qs}`);
  },

  async createLead(data: {
    company_name: string;
    contact_name?: string;
    contact_email?: string;
    phone?: string;
    country?: string;
    notes?: string;
    estimated_monthly_value?: number;
  }): Promise<{ message: string; lead_id: number }> {
    return api.post(`${BASE}/leads`, data);
  },

  async updateLead(leadId: number, data: Record<string, unknown>): Promise<{ message: string }> {
    return api.put(`${BASE}/leads/${leadId}`, data);
  },

  // ── Clients ──
  async getClients(): Promise<{ items: PartnerClientItem[]; total: number }> {
    return api.get(`${BASE}/clients`);
  },

  async createClient(data: {
    company_name: string;
    contact_email: string;
    subdomain: string;
    plan_name?: string;
    user_count?: number;
    contact_name?: string;
    notes?: string;
  }): Promise<{
    message: string;
    customer_id: number;
    subscription_id: number;
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
    return api.post(`${BASE}/clients`, data);
  },

  // ── Commissions ──
  async getCommissions(): Promise<{
    items: PartnerCommissionItem[];
    total: number;
    summary: { total_earned: number; pending: number; paid: number };
  }> {
    return api.get(`${BASE}/commissions`);
  },

  // ── Stripe ──
  async getStripeStatus(): Promise<Record<string, unknown>> {
    return api.get(`${BASE}/stripe/status`);
  },

  async getStripeDashboardLink(): Promise<{ success: boolean; url?: string }> {
    return api.get(`${BASE}/stripe/dashboard-link`);
  },

  async getStripeBalance(): Promise<Record<string, unknown>> {
    return api.get(`${BASE}/stripe/balance`);
  },

  // ── Profile ──
  async getProfile(): Promise<PartnerProfile> {
    return api.get<PartnerProfile>(`${BASE}/profile`);
  },

  async updateProfileSelf(data: Record<string, string | null>): Promise<{ message: string }> {
    return api.put(`${BASE}/profile`, data);
  },

  async changePassword(password: string, password_confirm: string): Promise<{ message: string }> {
    return api.post(`${BASE}/change-password`, { password, password_confirm });
  },

  // ── Pricing ──
  async getPricing(): Promise<{ items: Array<Record<string, unknown>> }> {
    return api.get(`${BASE}/pricing`);
  },

  // ── Admin endpoints ──
  async invitePartner(partner_id: number, temp_password: string, portal_email?: string): Promise<Record<string, unknown>> {
    return api.post(`${BASE}/admin/invite`, { partner_id, temp_password, portal_email });
  },

  async resetPartnerPassword(partner_id: number, temp_password: string, portal_email?: string): Promise<Record<string, unknown>> {
    return api.post(`${BASE}/admin/reset-password`, { partner_id, temp_password, portal_email });
  },
};

export default partnerPortalApi;
