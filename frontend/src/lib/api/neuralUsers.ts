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
    return res.data;
  },

  getTokens: async (userType: string, userId: string | number) => {
    const res = await api.get<UserTokensResponse>(`/api/neural-users/tokens/${userType}/${userId}`);
    return res.data;
  },

  generateToken: async (userType: string, userId: string | number, tokenType: 'verification' | 'refresh' = 'verification') => {
    const res = await api.post<{ success: boolean; data: any }>(`/api/neural-users/tokens/generate`, {
      user_type: userType,
      user_id: userId,
      token_type: tokenType
    });
    return res.data;
  },

  revokeToken: async (tokenId: number) => {
    const res = await api.post<{ success: boolean }>(`/api/neural-users/tokens/revoke/${tokenId}`, {});
    return res.data;
  },

  toggleBypassMfa: async (userType: string, userId: string | number) => {
    const res = await api.post<{ success: boolean; data: any }>(`/api/neural-users/bypass-mfa`, {
      user_type: userType,
      user_id: userId
    });
    return res.data;
  }
};
