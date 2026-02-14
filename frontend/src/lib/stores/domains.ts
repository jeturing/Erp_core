import { writable, derived } from 'svelte/store';
import { api } from '../api/client';
import type { Domain, DomainCreateResponse, DomainsListResponse } from '../types';

export type CustomDomain = Domain;

interface DomainsState {
  items: CustomDomain[];
  total: number;
  loading: boolean;
  error: string | null;
  selectedDomain: CustomDomain | null;
}

function createDomainsStore() {
  const { subscribe, set, update } = writable<DomainsState>({
    items: [],
    total: 0,
    loading: false,
    error: null,
    selectedDomain: null,
  });

  return {
    subscribe,

    async load(params?: {
      customer_id?: number;
      status?: string;
      is_active?: boolean;
      limit?: number;
      offset?: number;
    }) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const queryParams = new URLSearchParams();
        if (params?.customer_id) queryParams.set('customer_id', String(params.customer_id));
        if (params?.status) queryParams.set('status', params.status);
        if (params?.is_active !== undefined) queryParams.set('is_active', String(params.is_active));
        if (params?.limit) queryParams.set('limit', String(params.limit));
        if (params?.offset) queryParams.set('offset', String(params.offset));

        const query = queryParams.toString();
        const response = await api.get<DomainsListResponse>(`/api/domains${query ? `?${query}` : ''}`);

        update((s) => ({
          ...s,
          items: response.items,
          total: response.total,
          loading: false,
        }));

        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Error cargando dominios';
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },

    async get(domainId: number) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.get<{ domain: CustomDomain }>(`/api/domains/${domainId}`);
        update((s) => ({
          ...s,
          selectedDomain: response.domain,
          loading: false,
        }));
        return response.domain;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Error obteniendo dominio';
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },

    async create(data: {
      external_domain: string;
      customer_id: number;
      tenant_deployment_id?: number;
    }) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.post<DomainCreateResponse>('/api/domains', data);

        if (response.success && response.domain) {
          update((s) => ({
            ...s,
            items: [response.domain, ...s.items],
            total: s.total + 1,
            loading: false,
          }));
        }

        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Error creando dominio';
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },

    async update(
      domainId: number,
      data: {
        is_primary?: boolean;
        target_node_ip?: string;
        target_port?: number;
        tenant_deployment_id?: number;
      },
    ) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.put<{ success: boolean; domain: CustomDomain }>(`/api/domains/${domainId}`, data);

        if (response.success && response.domain) {
          update((s) => ({
            ...s,
            items: s.items.map((d) => (d.id === domainId ? response.domain : d)),
            selectedDomain: s.selectedDomain?.id === domainId ? response.domain : s.selectedDomain,
            loading: false,
          }));
        }

        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Error actualizando dominio';
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },

    async delete(domainId: number) {
      update((s) => ({ ...s, loading: true, error: null }));
      try {
        const response = await api.delete<{ success: boolean; message: string }>(`/api/domains/${domainId}`);

        if (response.success) {
          update((s) => ({
            ...s,
            items: s.items.filter((d) => d.id !== domainId),
            total: Math.max(0, s.total - 1),
            selectedDomain: s.selectedDomain?.id === domainId ? null : s.selectedDomain,
            loading: false,
          }));
        }

        return response;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Error eliminando dominio';
        update((s) => ({ ...s, loading: false, error: message }));
        throw error;
      }
    },

    async configureCloudflare(domainId: number) {
      const response = await api.post<{ success: boolean; message: string; record_id?: string }>(
        `/api/domains/${domainId}/configure-cloudflare`,
      );

      if (response.success) {
        await this.get(domainId);
      }

      return response;
    },

    async verify(domainId: number) {
      const response = await api.post<{
        success: boolean;
        status: string;
        message: string;
        cname_detected?: string;
        expected?: string;
        instructions?: string;
      }>(`/api/domains/${domainId}/verify`);

      update((s) => ({
        ...s,
        items: s.items.map((d) =>
          d.id === domainId
            ? {
                ...d,
                verification_status: response.status,
                is_active: response.success,
              }
            : d,
        ),
      }));

      return response;
    },

    async activate(domainId: number) {
      const response = await api.post<{ success: boolean; message: string }>(`/api/domains/${domainId}/activate`);
      if (response.success) {
        update((s) => ({
          ...s,
          items: s.items.map((d) => (d.id === domainId ? { ...d, is_active: true, verification_status: 'verified' } : d)),
        }));
      }
      return response;
    },

    async deactivate(domainId: number) {
      const response = await api.post<{ success: boolean; message: string }>(`/api/domains/${domainId}/deactivate`);
      if (response.success) {
        update((s) => ({
          ...s,
          items: s.items.map((d) => (d.id === domainId ? { ...d, is_active: false } : d)),
        }));
      }
      return response;
    },

    select(domain: CustomDomain | null) {
      update((s) => ({ ...s, selectedDomain: domain }));
    },

    clearError() {
      update((s) => ({ ...s, error: null }));
    },

    reset() {
      set({
        items: [],
        total: 0,
        loading: false,
        error: null,
        selectedDomain: null,
      });
    },
  };
}

export const domainsStore = createDomainsStore();

export const activeDomains = derived(domainsStore, ($store) => $store.items.filter((d) => d.is_active));

export const pendingDomains = derived(domainsStore, ($store) =>
  $store.items.filter((d) => d.verification_status === 'pending'),
);

export const domainStats = derived(domainsStore, ($store) => ({
  total: $store.total,
  active: $store.items.filter((d) => d.is_active).length,
  pending: $store.items.filter((d) => d.verification_status === 'pending').length,
  verified: $store.items.filter((d) => d.verification_status === 'verified').length,
  failed: $store.items.filter((d) => d.verification_status === 'failed').length,
}));
