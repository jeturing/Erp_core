import { api } from './client';

export interface NeuralUserItem {
  id: number | string;
  email: string;
  display_name: string;
  type: 'admin' | 'customer' | 'partner';
  role?: string;
  is_active: boolean;
  onboarding_bypass: boolean;
  totp_enabled: boolean;
  last_login_at?: string;
  created_at: string;
}

export interface UserTokenItem {
  id: number;
  type: 'verification' | 'refresh';
  token: string;
  identifier: string;
  expires_at: string;
  created_at: string;
}

export interface NeuralUsersResponse {
  success: boolean;
  data: NeuralUserItem[];
}

export interface UserTokensResponse {
  success: boolean;
  data: UserTokenItem[];
}

export const neuralUsersApi = {
  search: async (q: string) => {
    const res = await api.get<NeuralUsersResponse>(`/api/neural-users/search?q=${encodeURIComponent(q)}`);
    if (Array.isArray(res as unknown)) {
      return res as unknown as NeuralUserItem[];
    }
    return (res as unknown as NeuralUsersResponse).data ?? [];
  },

  getTokens: async (userType: string, userId: string | number) => {
    const res = await api.get<UserTokensResponse>(`/api/neural-users/tokens/${userType}/${userId}`);
    if (Array.isArray(res as unknown)) {
      return res as unknown as UserTokenItem[];
    }
    return (res as unknown as UserTokensResponse).data ?? [];
  },

  generateToken: async (userType: string, userId: string | number, tokenType: 'verification' | 'refresh' = 'verification') => {
    const res = await api.post<{ success: boolean; data: any }>(`/api/neural-users/tokens/generate`, {
      user_type: userType,
      user_id: userId,
      token_type: tokenType
    });
    return res;
  },

  revokeToken: async (tokenId: number) => {
    const res = await api.post<{ success: boolean }>(`/api/neural-users/tokens/revoke/${tokenId}`, {});
    return res;
  },

  toggleBypassMfa: async (userType: string, userId: string | number) => {
    const res = await api.post<{ success: boolean; data: any }>(`/api/neural-users/bypass-mfa`, {
      user_type: userType,
      user_id: userId
    });
    return res;
  },

  setPartnerTemporaryActivation: async (data: {
    user_id: number;
    action?: 'activate' | 'deactivate' | 'extend';
    duration?: '24h' | '7d';
    extension_duration?: '24h' | '7d';
    enable_onboarding_bypass?: boolean;
    enable_portal_access?: boolean;
    justification: string;
    external_ticket: string;
  }) => {
    const res = await api.post<{
      success: boolean;
      data: {
        partner_id: number;
        portal_access: boolean;
        onboarding_bypass: boolean;
        temporary_access_enabled: boolean;
        temporary_access_expires_at: string | null;
        temporary_access_scope: string | null;
        temporary_access_ticket: string | null;
      };
      meta: {
        action: string;
        processed_at: string;
      };
    }>(`/api/neural-users/partner/temporary-activation`, data);
    return res;
  }
};
