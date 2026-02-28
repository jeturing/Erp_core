import api from './client';

export interface AdminUserItem {
  id: number;
  email: string;
  display_name: string;
  role: 'admin' | 'operator' | 'viewer' | 'segrd-admin' | 'segrd-user';
  is_active: boolean;
  last_login_at: string | null;
  login_count: number;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
  created_by: string | null;
}

export interface AdminUsersResponse {
  items: AdminUserItem[];
  total: number;
}

export const adminUsersApi = {
  async list(): Promise<AdminUsersResponse> {
    return api.get<AdminUsersResponse>('/api/admin-users');
  },

  async get(id: number): Promise<AdminUserItem> {
    return api.get<AdminUserItem>(`/api/admin-users/${id}`);
  },

  async create(data: {
    email: string;
    password: string;
    display_name: string;
    role: 'admin' | 'operator' | 'viewer' | 'segrd-admin' | 'segrd-user';
    notes?: string;
  }): Promise<AdminUserItem> {
    return api.post<AdminUserItem>('/api/admin-users', data);
  },

  async update(id: number, data: {
    display_name?: string;
    role?: 'admin' | 'operator' | 'viewer' | 'segrd-admin' | 'segrd-user';
    is_active?: boolean;
    notes?: string;
    new_password?: string;
  }): Promise<AdminUserItem> {
    return api.put<AdminUserItem>(`/api/admin-users/${id}`, data);
  },

  async delete(id: number): Promise<{ message: string; id: number }> {
    return api.delete(`/api/admin-users/${id}`);
  },
};

export default adminUsersApi;
