import api from './client';
import type { Role, RolesListResponse } from '../types';

export interface RolePayload {
  name: string;
  description?: string;
  permissions?: string[];
}

export const rolesApi = {
  async listRoles(): Promise<RolesListResponse> {
    return api.get<RolesListResponse>('/api/roles');
  },

  async createRole(payload: RolePayload): Promise<{ success: boolean; role: Role }> {
    return api.post('/api/roles', {
      name: payload.name,
      description: payload.description || '',
      permissions: payload.permissions || [],
    });
  },

  async updateRole(roleId: number, payload: RolePayload): Promise<{ success: boolean; role: Role }> {
    return api.put(`/api/roles/${roleId}`, {
      name: payload.name,
      description: payload.description || '',
      permissions: payload.permissions || [],
    });
  },
};

export default rolesApi;
