import api from './client';

export interface EmailLog {
  id: number;
  recipient: string;
  subject: string | null;
  email_type: string;
  status: string | null;
  error_message: string | null;
  customer_id: number | null;
  partner_id: number | null;
  related_id: number | null;
  sent_at: string | null;
  created_at: string | null;
}

export interface EmailLogsResponse {
  items: EmailLog[];
  total: number;
  limit: number;
  offset: number;
}

export interface EmailStats {
  total: number;
  sent: number;
  failed: number;
  by_type: Record<string, number>;
}

export const communicationsApi = {
  async list(params?: {
    email_type?: string;
    status?: string;
    recipient?: string;
    limit?: number;
    offset?: number;
  }): Promise<EmailLogsResponse> {
    const qs = new URLSearchParams();
    if (params?.email_type) qs.set('email_type', params.email_type);
    if (params?.status) qs.set('status', params.status);
    if (params?.recipient) qs.set('recipient', params.recipient);
    if (params?.limit != null) qs.set('limit', String(params.limit));
    if (params?.offset != null) qs.set('offset', String(params.offset));
    const q = qs.toString();
    return api.get<EmailLogsResponse>(`/api/communications/history${q ? '?' + q : ''}`);
  },

  async get(id: number): Promise<EmailLog> {
    return api.get<EmailLog>(`/api/communications/history/${id}`);
  },

  async stats(): Promise<EmailStats> {
    return api.get<EmailStats>('/api/communications/stats');
  },
};

export default communicationsApi;
