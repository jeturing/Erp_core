import { api } from './client';

export interface Role {
  id: number;
  name: string;
  description?: string;
  permissions: string[];
  is_system?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RolesListResponse {
  roles: Role[];
  total: number;
}

export const rolesApi = {
  list(): Promise<RolesListResponse> {
    return api.get('/api/roles');
  },

  create(data: { name: string; description?: string; permissions: string[] }): Promise<Role> {
    return api.post('/api/roles', data);
  },

  update(id: number, data: { name?: string; description?: string; permissions?: string[] }): Promise<Role> {
    return api.put(`/api/roles/${id}`, data);
  },
};
