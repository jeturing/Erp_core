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
    return api.get(`/api/branding/resolve?domain=${encodeURIComponent(domain)}`);
  },
};

export default brandingApi;
