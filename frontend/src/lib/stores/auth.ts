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

    login: async (usernameOrEmail: string, password: string) => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        const result = await api.login({ username: usernameOrEmail, password });
        if (result.requires_totp) {
          update((state) => ({ ...state, isLoading: false, error: null }));
          return { requires_totp: true };
        }
        if (result.requires_email_verify) {
          update((state) => ({ ...state, isLoading: false, error: null }));
          return { requires_email_verify: true, message: result.message };
        }
        const user = await api.get<User>('/api/auth/me');
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return { success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Error de autenticacion';
        update((state) => ({ ...state, error: message, isLoading: false }));
        return { error: message };
      }
    },

    loginWithTotp: async (usernameOrEmail: string, password: string, totpCode: string) => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        // Login with TOTP code included
        const result = await api.post<{ access_token?: string; message?: string; requires_email_verify?: boolean }>('/api/auth/login', {
          email: usernameOrEmail,
          password,
          totp_code: totpCode,
        });
        if ((result as any).requires_email_verify) {
          update((state) => ({ ...state, isLoading: false, error: null }));
          return { requires_email_verify: true, message: (result as any).message };
        }
        if (result.access_token) {
          api.setToken(result.access_token);
        }
        const user = await api.get<User>('/api/auth/me');
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return { success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Codigo TOTP invalido';
        update((state) => ({ ...state, error: message, isLoading: false }));
        return { error: message };
      }
    },

    loginWithEmailVerify: async (
      usernameOrEmail: string,
      password: string,
      emailVerifyCode: string,
      totpCode?: string
    ) => {
      update((state) => ({ ...state, isLoading: true, error: null }));
      try {
        const payload: Record<string, string> = {
          email: usernameOrEmail,
          password,
          email_verify_code: emailVerifyCode,
        };
        if (totpCode) payload.totp_code = totpCode;

        const result = await api.post<{ access_token?: string; message?: string }>('/api/auth/login', payload);
        if (result.access_token) {
          api.setToken(result.access_token);
        }
        const user = await api.get<User>('/api/auth/me');
        update((state) => ({ ...state, user, isLoading: false, error: null }));
        return { success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Código de verificación inválido';
        update((state) => ({ ...state, error: message, isLoading: false }));
        return { error: message };
      }
    },

    setError: (message: string) => {
      update((state) => ({ ...state, error: message }));
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
