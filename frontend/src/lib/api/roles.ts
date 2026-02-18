import { api } from './client';

export interface PermissionInfo {
  [permKey: string]: string;
}

export interface PermissionModule {
  label: string;
  icon: string;
  permissions: PermissionInfo;
}

export interface PermissionCatalog {
  modules: Record<string, PermissionModule>;
}

export interface RolePreset {
  name: string;
  description: string;
  permissions: string[];
  color: string;
}

export interface AvailableTenant {
  id: number;
  tenant_name: string;
  domain: string;
  customer_name: string;
  customer_id: number;
}

export interface Role {
  id: number;
  name: string;
  description?: string;
  permissions: string[];
  system?: boolean;
  created_at?: string;
  updated_at?: string;
  color?: string;
  assigned_tenants?: number[];
}

export interface RolesListResponse {
  items: Role[];
  total: number;
}

export interface RolePayload {
  name: string;
  description?: string;
  permissions: string[];
  color?: string;
  assigned_tenants?: number[];
}

export const rolesApi = {
  list(): Promise<RolesListResponse> {
    return api.get('/api/roles');
  },

  create(data: RolePayload): Promise<{ success: boolean; role: Role }> {
    return api.post('/api/roles', data);
  },

  update(id: number, data: RolePayload): Promise<{ success: boolean; role: Role }> {
    return api.put(`/api/roles/${id}`, data);
  },

  delete(id: number): Promise<{ success: boolean; message: string }> {
    return api.delete(`/api/roles/${id}`);
  },

  getPermissionsCatalog(): Promise<PermissionCatalog> {
    return api.get('/api/roles/permissions-catalog');
  },

  getPresets(): Promise<{ presets: Record<string, RolePreset> }> {
    return api.get('/api/roles/presets');
  },

  getAvailableTenants(): Promise<{ tenants: AvailableTenant[]; total: number }> {
    return api.get('/api/roles/available-tenants');
  },
};
