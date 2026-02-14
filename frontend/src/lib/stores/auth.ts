import { writable, derived } from 'svelte/store';
import { api } from '../api';
import type { LoginRequest, User } from '../types';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

export interface AuthLoginResult {
  success: boolean;
  requiresTotp: boolean;
  error?: string;
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

    login: async (credentials: LoginRequest): Promise<AuthLoginResult> => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        const result = credentials.totp_code ? await api.verifyTotp(credentials) : await api.login(credentials);
        if (result.requires_totp) {
          update((state) => ({ ...state, isLoading: false, error: null }));
          return {
            success: false,
            requiresTotp: true,
          };
        }

        const user = await api.get<User>('/api/auth/me');
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return {
          success: true,
          requiresTotp: false,
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error de autenticacion';
        update((state) => ({ ...state, error: message, isLoading: false }));
        return {
          success: false,
          requiresTotp: false,
          error: message,
        };
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
