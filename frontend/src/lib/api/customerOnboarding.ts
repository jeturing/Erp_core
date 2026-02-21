import api from './client';

const BASE = '/api/customer-onboarding';

export interface OnboardingStatus {
  customer_id: number;
  onboarding_step: number;
  onboarding_completed: boolean;
  full_name: string;
  company_name: string;
  email: string;
  phone: string | null;
  country: string | null;
  plan: string | null;
  partner_id: number | null;
  is_dominican: boolean;
  needs_ecf_step: boolean;
  requires_ecf: boolean;
  ecf_rnc: string | null;
  ecf_business_name: string | null;
  ecf_establishment_type: string | null;
  ecf_ncf_series: string | null;
  ecf_environment: string | null;
}

export interface StepResponse {
  message: string;
  onboarding_step: number;
  is_dominican?: boolean;
  needs_ecf_step?: boolean;
}

export const customerOnboardingApi = {
  async getStatus(): Promise<OnboardingStatus> {
    return api.get<OnboardingStatus>(`${BASE}/status`);
  },

  async setPassword(password: string, password_confirm: string): Promise<StepResponse> {
    return api.post(`${BASE}/set-password`, { password, password_confirm });
  },

  async updateProfile(data: {
    full_name?: string;
    company_name?: string;
    phone?: string;
    country?: string;
    notes?: string;
  }): Promise<StepResponse> {
    return api.post(`${BASE}/update-profile`, data);
  },

  async submitECFQuestionnaire(data: {
    requires_ecf: boolean;
    ecf_rnc: string;
    ecf_business_name: string;
    ecf_establishment_type: string;
    ecf_ncf_series?: string;
    ecf_environment?: string;
  }): Promise<StepResponse> {
    return api.post(`${BASE}/ecf-questionnaire`, data);
  },

  async skipECF(): Promise<StepResponse> {
    return api.post(`${BASE}/skip-ecf`, { skip: true });
  },

  async completeOnboarding(): Promise<StepResponse> {
    return api.post(`${BASE}/complete`);
  },

  // Admin
  async getPendingOnboardings(): Promise<{ items: any[]; total: number }> {
    return api.get(`${BASE}/admin/pending`);
  },

  async advanceOnboarding(customerId: number): Promise<StepResponse> {
    return api.post(`${BASE}/admin/advance/${customerId}`);
  },

  async getECFCustomers(): Promise<{ items: any[]; total: number }> {
    return api.get(`${BASE}/admin/ecf-customers`);
  },
};

export default customerOnboardingApi;
