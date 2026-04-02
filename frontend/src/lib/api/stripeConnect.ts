// Stripe Connect — Partner onboarding & account management
import { api } from './client';

// ── Types ──

export interface ConnectAccountResult {
  success: boolean;
  account_id: string;
  onboarding_url: string | null;
  message: string;
}

export interface OnboardingLinkResult {
  success: boolean;
  url: string;
}

export interface DashboardLinkResult {
  success: boolean;
  url: string;
}

export interface ConnectStatus {
  success: boolean;
  has_account: boolean;
  partner_id: number;
  account_id?: string;
  charges_enabled?: boolean;
  payouts_enabled?: boolean;
  onboarding_ready?: boolean;
  details_submitted?: boolean;
  requirements?: {
    currently_due: string[];
    eventually_due: string[];
    past_due: string[];
  };
}

export interface ConnectBalance {
  success: boolean;
  available: Array<{ amount: number; currency: string }>;
  pending: Array<{ amount: number; currency: string }>;
}

export interface TransferResult {
  success: boolean;
  transfer_id: string;
  amount_cents: number;
  currency: string;
}

export interface TransferRequest {
  partner_id: number;
  amount: number;
  description?: string;
  commission_id?: number;
}

// ── API Client ──

export const stripeConnectApi = {
  /** Create a Stripe Connect Express account for a partner */
  async createAccount(partnerId: number, country = 'US'): Promise<ConnectAccountResult> {
    return api.post('/api/stripe-connect/create-account', {
      partner_id: partnerId,
      country,
    });
  },

  /** Generate or regenerate onboarding link */
  async getOnboardingLink(partnerId: number): Promise<OnboardingLinkResult> {
    return api.get<OnboardingLinkResult>(`/api/stripe-connect/${partnerId}/onboarding-link`);
  },

  /** Get Express Dashboard link for a partner */
  async getDashboardLink(partnerId: number): Promise<DashboardLinkResult> {
    return api.get<DashboardLinkResult>(`/api/stripe-connect/${partnerId}/dashboard-link`);
  },

  /** Get account status and verification info */
  async getStatus(partnerId: number): Promise<ConnectStatus> {
    return api.get<ConnectStatus>(`/api/stripe-connect/${partnerId}/status`);
  },

  /** Get partner's Stripe balance */
  async getBalance(partnerId: number): Promise<ConnectBalance> {
    return api.get<ConnectBalance>(`/api/stripe-connect/${partnerId}/balance`);
  },

  /** Execute a manual transfer to partner */
  async transfer(data: TransferRequest): Promise<TransferResult> {
    return api.post('/api/stripe-connect/transfer', data);
  },
};
