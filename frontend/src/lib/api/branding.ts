import api from './client';
import type {
  BrandingProfile,
  BrandingProfilesResponse,
} from '../types';

export const brandingApi = {
  async create(data: {
    partner_id: number;
    brand_name: string;
    logo_url?: string;
    favicon_url?: string;
    primary_color?: string;
    secondary_color?: string;
    support_email?: string;
    support_url?: string;
    custom_css?: string;
  }): Promise<{ message: string; profile: BrandingProfile }> {
    return api.post('/api/branding/profiles', data);
  },

  async list(): Promise<BrandingProfilesResponse> {
    return api.get<BrandingProfilesResponse>('/api/branding/profiles');
  },

  async get(id: number): Promise<BrandingProfile> {
    return api.get(`/api/branding/profiles/${id}`);
  },

  async update(id: number, data: Partial<BrandingProfile>): Promise<{ message: string; profile: BrandingProfile }> {
    return api.put(`/api/branding/profiles/${id}`, data);
  },

  async resolveByDomain(domain: string): Promise<BrandingProfile> {
    return api.get(`/api/branding/resolve/${encodeURIComponent(domain)}`);
  },

  async uploadAsset(profileId: number, assetType: 'logo' | 'favicon' | 'og', file: File): Promise<{
    success: boolean;
    data: {
      profile_id: number;
      asset_type: string;
      asset_url: string;
      updated_field?: string | null;
    };
    meta: {
      content_type?: string;
      size: number;
    };
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const token = api.getToken();
    const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/branding/profiles/${profileId}/assets/${assetType}`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  },
};

export default brandingApi;
