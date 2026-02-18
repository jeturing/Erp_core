import api from './client';
import type {
  BlueprintModule,
  BlueprintPackage,
  BlueprintModulesResponse,
  BlueprintPackagesResponse,
} from '../types';

export const blueprintsApi = {
  // ── Module Catalog ──
  async getModules(): Promise<BlueprintModulesResponse> {
    return api.get<BlueprintModulesResponse>('/api/blueprints/modules');
  },

  async createModule(data: Partial<BlueprintModule>): Promise<{ message: string; module: BlueprintModule }> {
    return api.post('/api/blueprints/modules', data);
  },

  async updateModule(id: number, data: Partial<BlueprintModule>): Promise<{ message: string; module: BlueprintModule }> {
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
    module_ids?: number[];
  }): Promise<{ message: string; package: BlueprintPackage }> {
    return api.post('/api/blueprints/packages', data);
  },

  async updatePackage(id: number, data: Partial<BlueprintPackage & { module_ids?: number[] }>): Promise<{ message: string; package: BlueprintPackage }> {
    return api.put(`/api/blueprints/packages/${id}`, data);
  },

  async getPackage(id: number): Promise<BlueprintPackage> {
    return api.get(`/api/blueprints/packages/${id}`);
  },
};

export default blueprintsApi;
