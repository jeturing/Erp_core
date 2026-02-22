import { api } from './client';
import type {
  AgreementTemplate,
  AgreementTemplatesResponse,
  SignedAgreement,
  SignedAgreementsResponse,
} from '../types';

export const agreementsApi = {
  // ── Templates (Admin) ──

  async listTemplates(params?: {
    agreement_type?: string;
    target?: string;
    active_only?: boolean;
  }): Promise<AgreementTemplatesResponse> {
    const qs = new URLSearchParams();
    if (params?.agreement_type) qs.set('agreement_type', params.agreement_type);
    if (params?.target) qs.set('target', params.target);
    if (params?.active_only !== undefined) qs.set('active_only', String(params.active_only));
    const query = qs.toString();
    return api.get<AgreementTemplatesResponse>(`/api/agreements/templates${query ? `?${query}` : ''}`);
  },

  async getTemplate(id: number): Promise<AgreementTemplate> {
    return api.get<AgreementTemplate>(`/api/agreements/templates/${id}`);
  },

  async createTemplate(data: Partial<AgreementTemplate>): Promise<AgreementTemplate> {
    return api.post<AgreementTemplate>('/api/agreements/templates', data);
  },

  async updateTemplate(id: number, data: Partial<AgreementTemplate>): Promise<AgreementTemplate> {
    return api.put<AgreementTemplate>(`/api/agreements/templates/${id}`, data);
  },

  async deleteTemplate(id: number): Promise<{ message: string }> {
    return api.delete<{ message: string }>(`/api/agreements/templates/${id}`);
  },

  // ── Required agreements (partner/customer flow) ──

  async getRequired(targetType: 'partner' | 'customer'): Promise<{ items: AgreementTemplate[]; total: number }> {
    return api.get(`/api/agreements/required/${targetType}`);
  },

  // ── Signing ──

  async sign(data: {
    template_id: number;
    signer_name: string;
    signature_data: string;
  }): Promise<SignedAgreement> {
    return api.post<SignedAgreement>('/api/agreements/sign', data);
  },

  // ── Signed agreements ──

  async listSigned(params?: {
    partner_id?: number;
    customer_id?: number;
  }): Promise<SignedAgreementsResponse> {
    const qs = new URLSearchParams();
    if (params?.partner_id) qs.set('partner_id', String(params.partner_id));
    if (params?.customer_id) qs.set('customer_id', String(params.customer_id));
    const query = qs.toString();
    return api.get<SignedAgreementsResponse>(`/api/agreements/signed${query ? `?${query}` : ''}`);
  },

  getPdfUrl(id: number): string {
    return `/api/agreements/signed/${id}/pdf`;
  },
};
