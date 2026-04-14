import { api } from './client';

export interface FunnelLeadPayload {
  niche: 'mpos' | 'build' | 'partners' | 'cpa' | 'smb' | 'general';
  full_name: string;
  email: string;
  phone?: string;
  company_name?: string;
  country?: string;
  language?: string;
  // Qualification
  has_entity?: boolean;
  monthly_volume?: string;
  budget_range?: string;
  timeline?: string;
  client_count?: number;
  has_sales_team?: boolean;
  industry?: string;
  main_goal?: string;
  // Tracking
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  referrer?: string;
}

export interface FunnelLeadResponse {
  id: number;
  qualified: boolean;
  redirect: string;
}

function getUTMParams(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const p = new URLSearchParams(window.location.search);
  return {
    utm_source:   p.get('utm_source')   || '',
    utm_medium:   p.get('utm_medium')   || '',
    utm_campaign: p.get('utm_campaign') || '',
  };
}

export async function submitFunnelLead(payload: FunnelLeadPayload): Promise<FunnelLeadResponse> {
  const utm = getUTMParams();
  return api.post<FunnelLeadResponse>('/api/public/funnel/lead', {
    ...payload,
    utm_source:   payload.utm_source   || utm.utm_source   || undefined,
    utm_medium:   payload.utm_medium   || utm.utm_medium   || undefined,
    utm_campaign: payload.utm_campaign || utm.utm_campaign || undefined,
    referrer:     typeof document !== 'undefined' ? document.referrer : undefined,
    language:     payload.language || (typeof navigator !== 'undefined' ? navigator.language.slice(0,2) : 'es'),
  });
}
