import api from './client';
import type {
  PartnersResponse,
  PartnerItem,
  LeadsResponse,
  LeadItem,
  CommissionsResponse,
  CommissionItem,
  QuotationsResponse,
  QuotationItem,
  CatalogResponse,
  ServiceCatalogItemType,
} from '../types';

export const partnersApi = {
  // ── Partners ──
  async getPartners(statusFilter?: string): Promise<PartnersResponse> {
    const params = statusFilter ? `?status_filter=${statusFilter}` : '';
    return api.get<PartnersResponse>(`/api/partners${params}`);
  },

  async getPartner(id: number): Promise<PartnerItem & { leads_summary: any; commissions_summary: any }> {
    return api.get(`/api/partners/${id}`);
  },

  async createPartner(data: Partial<PartnerItem>): Promise<{ message: string; partner: PartnerItem }> {
    return api.post('/api/partners', data);
  },

  async updatePartner(id: number, data: Partial<PartnerItem>): Promise<{ message: string; changes: string[]; partner: PartnerItem }> {
    return api.put(`/api/partners/${id}`, data);
  },

  async deletePartner(id: number): Promise<{ message: string }> {
    return api.delete(`/api/partners/${id}`);
  },

  async activatePartner(id: number): Promise<{ message: string; partner: PartnerItem }> {
    return api.post(`/api/partners/${id}/activate`);
  },

  // ── Leads ──
  async getLeads(partnerId?: number, statusFilter?: string): Promise<LeadsResponse> {
    const params = new URLSearchParams();
    if (partnerId) params.set('partner_id', String(partnerId));
    if (statusFilter) params.set('status_filter', statusFilter);
    const qs = params.toString();
    return api.get<LeadsResponse>(`/api/leads${qs ? '?' + qs : ''}`);
  },

  async getLead(id: number): Promise<LeadItem> {
    return api.get(`/api/leads/${id}`);
  },

  async createLead(data: {
    partner_id: number;
    company_name: string;
    contact_name?: string;
    contact_email?: string;
    phone?: string;
    country?: string;
    notes?: string;
    estimated_monthly_value?: number;
  }): Promise<{ message: string; lead: LeadItem }> {
    return api.post('/api/leads', data);
  },

  async updateLead(id: number, data: Partial<LeadItem>): Promise<{ message: string; changes: string[]; lead: LeadItem }> {
    return api.put(`/api/leads/${id}`, data);
  },

  async deleteLead(id: number): Promise<{ message: string }> {
    return api.delete(`/api/leads/${id}`);
  },

  async convertLead(id: number, customerId?: number): Promise<{ message: string; lead: LeadItem }> {
    const params = customerId ? `?customer_id=${customerId}` : '';
    return api.post(`/api/leads/${id}/convert${params}`);
  },

  // ── Commissions ──
  async getCommissions(partnerId?: number, statusFilter?: string): Promise<CommissionsResponse> {
    const params = new URLSearchParams();
    if (partnerId) params.set('partner_id', String(partnerId));
    if (statusFilter) params.set('status_filter', statusFilter);
    const qs = params.toString();
    return api.get<CommissionsResponse>(`/api/commissions${qs ? '?' + qs : ''}`);
  },

  async createCommission(data: {
    partner_id: number;
    subscription_id?: number;
    lead_id?: number;
    period_start: string;
    period_end: string;
    gross_revenue: number;
    deductions?: Record<string, number>;
    notes?: string;
  }): Promise<{ message: string; commission: CommissionItem }> {
    return api.post('/api/commissions', data);
  },

  async updateCommission(id: number, data: Partial<CommissionItem>): Promise<{ message: string; changes: string[]; commission: CommissionItem }> {
    return api.put(`/api/commissions/${id}`, data);
  },

  async approveCommission(id: number): Promise<{ message: string; commission: CommissionItem }> {
    return api.post(`/api/commissions/${id}/approve`);
  },

  async payCommission(id: number, paymentReference?: string): Promise<{ message: string; commission: CommissionItem }> {
    const params = paymentReference ? `?payment_reference=${encodeURIComponent(paymentReference)}` : '';
    return api.post(`/api/commissions/${id}/pay${params}`);
  },

  // ── Quotations ──
  async getQuotations(partnerId?: number, statusFilter?: string): Promise<QuotationsResponse> {
    const params = new URLSearchParams();
    if (partnerId) params.set('partner_id', String(partnerId));
    if (statusFilter) params.set('status_filter', statusFilter);
    const qs = params.toString();
    return api.get<QuotationsResponse>(`/api/quotations${qs ? '?' + qs : ''}`);
  },

  async getQuotation(id: number): Promise<QuotationItem> {
    return api.get(`/api/quotations/${id}`);
  },

  async createQuotation(data: {
    partner_id?: number;
    customer_id?: number;
    prospect_name?: string;
    prospect_email?: string;
    prospect_company?: string;
    prospect_phone?: string;
    lines: Array<{ service_id?: number; name: string; unit: string; quantity: number; unit_price: number }>;
    partner_margin?: number;
    notes?: string;
    terms?: string;
    valid_days?: number;
    currency?: string;
  }): Promise<{ message: string; quotation: QuotationItem }> {
    return api.post('/api/quotations', data);
  },

  async updateQuotation(id: number, data: Partial<QuotationItem & { valid_days?: number }>): Promise<{ message: string; changes: string[]; quotation: QuotationItem }> {
    return api.put(`/api/quotations/${id}`, data);
  },

  async sendQuotation(id: number): Promise<{ message: string }> {
    return api.post(`/api/quotations/${id}/send`);
  },

  async deleteQuotation(id: number): Promise<{ message: string }> {
    return api.delete(`/api/quotations/${id}`);
  },

  // ── Service Catalog ──
  async getCatalog(category?: string): Promise<CatalogResponse> {
    const params = category ? `?category=${category}` : '';
    return api.get<CatalogResponse>(`/api/catalog${params}`);
  },

  async createCatalogItem(data: Partial<ServiceCatalogItemType>): Promise<{ message: string; item: ServiceCatalogItemType }> {
    return api.post('/api/catalog', data);
  },

  async updateCatalogItem(id: number, data: Partial<ServiceCatalogItemType>): Promise<{ message: string; item: ServiceCatalogItemType }> {
    return api.put(`/api/catalog/${id}`, data);
  },

  async deleteCatalogItem(id: number): Promise<{ message: string }> {
    return api.delete(`/api/catalog/${id}`);
  },
};

export default partnersApi;
