import { writable } from 'svelte/store';
import { dashboardApi } from '../api/dashboard';
import type { DashboardMetrics } from '../types';

interface DashboardState {
  data: DashboardMetrics | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

function createDashboardStore() {
  const { subscribe, set, update } = writable<DashboardState>({
    data: null,
    isLoading: false,
    error: null,
    lastUpdated: null,
  });

  let refreshInterval: number | null = null;

  const refreshData = async () => {
    const data = await dashboardApi.getMetrics();
    update((state) => ({
      ...state,
      data,
      lastUpdated: new Date(),
    }));
  };

  return {
    subscribe,

    load: async () => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        await refreshData();
        update((state) => ({ ...state, isLoading: false }));
      } catch (err) {
        const message = err instanceof Error ? err.message : 'No se pudo cargar el dashboard';
        update((state) => ({ ...state, error: message, isLoading: false }));
      }
    },

    refresh: async () => {
      try {
        await refreshData();
      } catch {
        // silent background refresh
      }
    },

    startAutoRefresh: (intervalMs = 30000) => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
      refreshInterval = window.setInterval(async () => {
        try {
          await refreshData();
        } catch {
          // silent background refresh
        }
      }, intervalMs);
    },

    stopAutoRefresh: () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
      }
    },

    reset: () => {
      set({
        data: null,
        isLoading: false,
        error: null,
        lastUpdated: null,
      });
    },
  };
}

export const dashboard = createDashboardStore();
