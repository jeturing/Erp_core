import { writable, derived } from 'svelte/store';
import { api } from '../api';
import type { LoginRequest, User } from '../types';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>({
    user: null,
    isLoading: true,
    error: null,
  });

  return {
    subscribe,

    init: async () => {
      try {
        const user = await api.get<User>('/api/auth/me');
        update((state) => ({ ...state, user, isLoading: false, error: null }));
      } catch {
        update((state) => ({ ...state, user: null, isLoading: false }));
      }
    },

    login: async (credentials: LoginRequest) => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        const result = await api.login(credentials);
        if (result.requires_totp) {
          update((state) => ({
            ...state,
            isLoading: false,
            error: 'Este usuario requiere codigo 2FA. Flujo 2FA pendiente en SPA.',
          }));
          return false;
        }

        const user = await api.get<User>('/api/auth/me');
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error de autenticacion';
        update((state) => ({ ...state, error: message, isLoading: false }));
        return false;
      }
    },

    logout: async () => {
      await api.logout();
      set({ user: null, isLoading: false, error: null });
    },

    clearError: () => {
      update((state) => ({ ...state, error: null }));
    },
  };
}

export const auth = createAuthStore();
export const isAuthenticated = derived(auth, ($auth) => !!$auth.user);
export const currentUser = derived(auth, ($auth) => $auth.user);
