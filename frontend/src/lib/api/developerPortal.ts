import { api } from './client';
import type {
  DeveloperApp,
  DeveloperAppSummary,
  DeveloperAgreementFlow,
  DeveloperApiSuite,
} from '../types';

export const developerPortalApi = {
  // ── Apps CRUD ──

  async listApps(): Promise<{ items: DeveloperAppSummary[]; total: number }> {
    return api.get('/api/developer-portal/apps');
  },

  async getApp(id: number): Promise<DeveloperAppSummary> {
    return api.get(`/api/developer-portal/apps/${id}`);
  },

  async createApp(data: {
    name: string;
    description?: string;
    api_suite?: string;
    organization_name?: string;
  }): Promise<{ message: string; app: DeveloperAppSummary }> {
    return api.post('/api/developer-portal/apps', data);
  },

  async updateApp(id: number, data: {
    name?: string;
    description?: string;
    webhook_url?: string;
    organization_name?: string;
  }): Promise<{ message: string }> {
    return api.put(`/api/developer-portal/apps/${id}`, data);
  },

  async deleteApp(id: number): Promise<{ message: string }> {
    return api.delete(`/api/developer-portal/apps/${id}`);
  },

  // ── Organization ──

  async linkOrganization(appId: number, organizationName: string): Promise<{ message: string; app: DeveloperAppSummary }> {
    return api.post(`/api/developer-portal/apps/${appId}/link-organization`, {
      organization_name: organizationName,
    });
  },

  // ── Agreement Flows ──

  async getFlow(flowId: number): Promise<DeveloperAgreementFlow> {
    return api.get(`/api/developer-portal/flows/${flowId}`);
  },

  async markViewed(flowId: number): Promise<{ message: string; status: string }> {
    return api.post(`/api/developer-portal/flows/${flowId}/view`, {});
  },

  async signFlow(flowId: number, data: {
    signer_name: string;
    signer_title?: string;
    signer_company?: string;
    signature_data: string;
  }): Promise<{ message: string; flow_id: number; signed_id: number; document_hash: string; status: string }> {
    return api.post(`/api/developer-portal/flows/${flowId}/sign`, data);
  },

  async reviewFlow(flowId: number, data: {
    action: 'approve' | 'reject';
    reason?: string;
  }): Promise<{ message: string; status: string }> {
    return api.post(`/api/developer-portal/flows/${flowId}/review`, data);
  },

  getPreviewPdfUrl(flowId: number): string {
    return `/api/developer-portal/flows/${flowId}/preview-pdf`;
  },

  // ── Production ──

  async requestProduction(appId: number): Promise<{ message: string; status: string }> {
    return api.post(`/api/developer-portal/apps/${appId}/request-production`, {});
  },

  async verifyApp(appId: number): Promise<{ message: string; status: string }> {
    return api.post(`/api/developer-portal/apps/${appId}/verify`, {});
  },

  // ── API Suites Catalog ──

  async listApiSuites(): Promise<{ items: DeveloperApiSuite[]; total: number }> {
    return api.get('/api/developer-portal/api-suites');
  },

  async listApiSuitesAdmin(): Promise<{ items: DeveloperApiSuite[]; total: number }> {
    return api.get('/api/developer-portal/admin/api-suites');
  },

  async saveApiSuitesAdmin(items: DeveloperApiSuite[]): Promise<{ message: string; items: DeveloperApiSuite[]; total: number }> {
    return api.put('/api/developer-portal/admin/api-suites', { items });
  },
};
