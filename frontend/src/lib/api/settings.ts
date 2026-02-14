import api from './client';
import type { OdooSettingsResponse, SettingsResponse } from '../types';

export const settingsApi = {
  async getAll(category?: string): Promise<SettingsResponse> {
    const suffix = category ? `?category=${encodeURIComponent(category)}` : '';
    return api.get<SettingsResponse>(`/api/settings${suffix}`);
  },

  async updateConfig(key: string, value: string, description?: string): Promise<{ success: boolean; key: string; message: string }> {
    return api.put(`/api/settings/${encodeURIComponent(key)}`, {
      key,
      value,
      description,
    });
  },

  async getOdooCurrent(): Promise<OdooSettingsResponse> {
    return api.get<OdooSettingsResponse>('/api/settings/odoo/current');
  },

  async updateOdooConfig(payload: {
    admin_login?: string;
    admin_password?: string;
    master_password?: string;
    db_user?: string;
    db_password?: string;
    default_lang?: string;
    default_country?: string;
    base_domain?: string;
    template_db?: string;
  }): Promise<{ success: boolean; message: string }> {
    return api.put('/api/settings/odoo', payload);
  },
};

export default settingsApi;
