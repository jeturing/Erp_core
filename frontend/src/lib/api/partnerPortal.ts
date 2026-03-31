import api from './client';
import type {
  AddonSubscriptionItem,
  PartnerOnboardingStatus,
  PartnerDashboard,
  PartnerLeadsResponse,
  PartnerLeadItem,
  PartnerProfile,
  PartnerClientItem,
  PartnerCommissionItem,
  PartnerPortalInvoiceItem,
  ServiceCatalogItemType,
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
    requirements_currently_due: string[];
    requirements_disabled_reason: string | null;
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

  async getClientServiceCatalog(customerId: number): Promise<{ items: ServiceCatalogItemType[]; total: number }> {
    return api.get(`${BASE}/clients/${customerId}/services/catalog`);
  },

  async getClientDomains(customerId: number): Promise<{
    customer_id: number;
    company_name: string;
    subdomain: string;
    domains: Array<{
      domain: string;
      sources: string[];
      is_active: boolean;
      verification_status: string | null;
      custom_domain_id: number | null;
    }>;
    summary: { total: number; base: number; custom: number; odoo: number };
    odoo_error: string | null;
  }> {
    return api.get(`${BASE}/clients/${customerId}/domains`);
  },

  async getClientServiceSubscriptions(customerId: number): Promise<{ items: AddonSubscriptionItem[]; total: number }> {
    return api.get(`${BASE}/clients/${customerId}/services/subscriptions`);
  },

  async purchaseClientService(customerId: number, catalog_item_id: number, quantity = 1): Promise<{
    message: string;
    addon: AddonSubscriptionItem;
    invoice?: { id: number; invoice_number: string; total: number; currency: string; status: string; stripe_invoice_id?: string | null; payment_url?: string | null } | null;
  }> {
    return api.post(`${BASE}/clients/${customerId}/services/purchase`, { catalog_item_id, quantity });
  },

  // ── Commissions ──
  async getCommissions(): Promise<{
    items: PartnerCommissionItem[];
    total: number;
    summary: { total_earned: number; pending: number; paid: number };
  }> {
    return api.get(`${BASE}/commissions`);
  },

  async getInvoices(status?: string): Promise<{
    items: PartnerPortalInvoiceItem[];
    total: number;
    summary: { total_billed: number; total_paid: number; total_pending: number };
  }> {
    const qs = status ? `?status_filter=${status}` : '';
    return api.get(`${BASE}/invoices${qs}`);
  },

  async getInvoicePaymentLink(invoiceId: number): Promise<{ payment_url?: string; method?: string; invoice_number: string }> {
    return api.post(`${BASE}/invoices/${invoiceId}/pay`);
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

  // ── Branding (Mi Marca) ──
  async getBranding(): Promise<{
    is_configured: boolean;
    white_label_enabled: boolean;
    profile_id?: number;
    brand_name: string;
    logo_url: string | null;
    favicon_url: string | null;
    primary_color: string;
    secondary_color: string;
    support_email: string | null;
    support_url: string | null;
    portal_url: string | null;
    terms_url: string | null;
    privacy_url: string | null;
    custom_css: string | null;
    is_active: boolean;
    updated_at?: string | null;
  }> {
    return api.get(`${BASE}/branding`);
  },

  async updateBranding(data: {
    brand_name?: string;
    logo_url?: string;
    favicon_url?: string;
    primary_color?: string;
    secondary_color?: string;
    support_email?: string;
    support_url?: string;
    portal_url?: string;
    terms_url?: string;
    privacy_url?: string;
    custom_css?: string;
  }): Promise<{
    success: boolean;
    message: string;
    profile_id: number;
    is_active: boolean;
    updated_fields: string[];
  }> {
    return api.put(`${BASE}/branding`, data);
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
