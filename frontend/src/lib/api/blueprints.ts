import api from './client';
import type {
  BlueprintModule,
  BlueprintPackage,
  BlueprintModulesResponse,
  BlueprintPackagesResponse,
} from '../types';

export const blueprintsApi = {
  // ── Module Catalog ──
  async getModules(params?: { active_only?: boolean; partner_only?: boolean; category?: string }): Promise<BlueprintModulesResponse> {
    const qs = new URLSearchParams();
    if (params?.active_only === false) qs.set('active_only', 'false');
    if (params?.partner_only) qs.set('partner_only', 'true');
    if (params?.category) qs.set('category', params.category);
    const q = qs.toString() ? `?${qs}` : '';
    return api.get<BlueprintModulesResponse>(`/api/blueprints/modules${q}`);
  },

  async getCategories(): Promise<string[]> {
    return api.get<string[]>('/api/blueprints/modules/categories');
  },

  async importFromFilesystem(): Promise<{ status: string; created: number; updated: number; skipped: number; total_in_catalog: number }> {
    return api.post('/api/blueprints/modules/import-fs', {});
  },

  async createModule(data: Partial<BlueprintModule>): Promise<{ message: string; id: number }> {
    return api.post('/api/blueprints/modules', data);
  },

  async updateModule(id: number, data: Partial<BlueprintModule>): Promise<{ message: string }> {
    return api.put(`/api/blueprints/modules/${id}`, data);
  },

  // ── Packages ──
  async getPackages(): Promise<BlueprintPackagesResponse> {
    return api.get<BlueprintPackagesResponse>('/api/blueprints/packages');
  },

  async createPackage(data: {
    name: string;
    display_name: string;
    description?: string;
    plan_type?: string;
    base_price_monthly?: number;
    is_default?: boolean;
    module_list?: string[];
  }): Promise<{ message: string; id: number; name: string }> {
    return api.post('/api/blueprints/packages', data);
  },

  async updatePackage(id: number, data: Partial<BlueprintPackage & { module_list?: string[] }>): Promise<{ message: string }> {
    return api.put(`/api/blueprints/packages/${id}`, data);
  },

  async getPackage(id: number): Promise<BlueprintPackage> {
    return api.get(`/api/blueprints/packages/${id}`);
  },
};

export default blueprintsApi;
