import { writable } from 'svelte/store';
import { dashboardApi } from '../api/dashboard';
import type { DashboardMetrics } from '../types';
import type { ReportsOverview } from '../api/dashboard';

interface DashboardState {
  data: DashboardMetrics | null;
  report: ReportsOverview | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

function createDashboardStore() {
  const { subscribe, set, update } = writable<DashboardState>({
    data: null,
    report: null,
    isLoading: false,
    error: null,
    lastUpdated: null,
  });

  let refreshInterval: number | null = null;

  const refreshData = async () => {
    const [data, report] = await Promise.all([
      dashboardApi.getMetrics(),
      dashboardApi.getOverview().catch(() => null),
    ]);
    update((state) => ({
      ...state,
      data,
      report: report ?? state.report,
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
        report: null,
        isLoading: false,
        error: null,
        lastUpdated: null,
      });
    },
  };
}

export const dashboard = createDashboardStore();
