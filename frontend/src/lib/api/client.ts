// API Client for ERP Core backend
import type { LoginRequest, LoginResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    this.loadToken();
  }

  private loadToken() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('access_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('access_token', token);
      } else {
        localStorage.removeItem('access_token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  isAuthenticated(): boolean {
    return Boolean(this.token);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      (headers as Record<string, string>).Authorization = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (response.status === 401) {
      this.setToken(null);
      throw new Error('Sesion expirada');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json() as Promise<T>;
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown, headers?: HeadersInit): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown, headers?: HeadersInit): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(endpoint: string, data?: unknown, headers?: HeadersInit): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  private async authenticate(endpoint: string, payload: { email: string; password: string; totp_code?: string }): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      credentials: 'include',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Credenciales invalidas' }));
      throw new Error(error.detail || 'Credenciales invalidas');
    }

    return response.json() as Promise<LoginResponse>;
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const payload: { email: string; password: string; totp_code?: string } = {
      email: credentials.username.trim(),
      password: credentials.password,
    };
    if (credentials.totp_code?.trim()) {
      payload.totp_code = credentials.totp_code.trim();
    }
    return this.authenticate('/api/auth/login', payload);
  }

  async verifyTotp(credentials: LoginRequest): Promise<LoginResponse> {
    const payload = {
      email: credentials.username.trim(),
      password: credentials.password,
      totp_code: credentials.totp_code?.trim() || '',
    };
    if (!payload.totp_code) {
      throw new Error('Codigo 2FA requerido');
    }
    return this.authenticate('/api/auth/totp/verify', payload);
  }

  async logout() {
    try {
      await fetch(`${this.baseUrl}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Ignore logout network errors
    }
    this.setToken(null);
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;
