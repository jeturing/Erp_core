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

export interface AvailableUser {
  id: number;
  email: string;
  display_name: string;
  role: string;
}

export interface RoleUser {
  id: number;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
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
  assigned_users?: number[];
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
  assigned_users?: number[];
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

  getAvailableUsers(): Promise<{ users: AvailableUser[]; total: number }> {
    return api.get('/api/roles/available-users');
  },

  getRoleUsers(roleId: number): Promise<{ users: RoleUser[]; total: number; role_id: number }> {
    return api.get(`/api/roles/${roleId}/users`);
  },

  assignUsers(roleId: number, userIds: number[]): Promise<{ success: boolean; role_id: number; assigned_users: number[] }> {
    return api.post(`/api/roles/${roleId}/users`, { user_ids: userIds });
  },

  removeUser(roleId: number, userId: number): Promise<{ success: boolean; role_id: number; removed_user_id: number }> {
    return api.delete(`/api/roles/${roleId}/users/${userId}`);
  },
};
