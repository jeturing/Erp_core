import api from './client';
import type {
  AuditEvent,
  AuditEventsResponse,
} from '../types';

export const auditApi = {
  async log(data: {
    event_type: string;
    resource?: string;
    action?: string;
    details?: Record<string, unknown>;
  }): Promise<{ message: string; event_id: number }> {
    return api.post('/api/audit/log', data);
  },

  async list(params?: {
    event_type?: string;
    actor_id?: number;
    resource?: string;
    tenant?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<AuditEventsResponse> {
    const qs = new URLSearchParams();
    if (params?.event_type) qs.set('event_type', params.event_type);
    if (params?.actor_id) qs.set('actor_id', String(params.actor_id));
    if (params?.resource) qs.set('resource', params.resource);
    if (params?.tenant) qs.set('tenant', params.tenant);
    if (params?.status) qs.set('status', params.status);
    if (params?.limit) qs.set('limit', String(params.limit));
    if (params?.offset) qs.set('offset', String(params.offset));
    const q = qs.toString();
    return api.get<AuditEventsResponse>(`/api/audit${q ? '?' + q : ''}`);
  },

  async get(id: number): Promise<AuditEvent> {
    return api.get(`/api/audit/${id}`);
  },
};

export default auditApi;
