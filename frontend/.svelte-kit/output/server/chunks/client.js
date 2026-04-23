const API_BASE_URL = "";
class ApiClient {
  baseUrl;
  token = null;
  refreshing = null;
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.loadToken();
  }
  loadToken() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
  }
  setToken(token) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("access_token", token);
      } else {
        localStorage.removeItem("access_token");
      }
    }
  }
  getToken() {
    return this.token;
  }
  isAuthenticated() {
    return Boolean(this.token);
  }
  /**
   * Intenta renovar el access token usando el refresh token (cookie httpOnly).
   * Si el servidor devuelve un nuevo token en JSON, lo guarda en localStorage.
   * Retorna true si se renovó exitosamente.
   */
  async tryRefresh() {
    try {
      const res = await fetch(`${this.baseUrl}/api/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (data.access_token) {
        this.setToken(data.access_token);
      }
      return true;
    } catch {
      return false;
    }
  }
  /**
   * Singleton refresh: evita múltiples refreshes simultáneos.
   */
  async ensureRefresh() {
    if (!this.refreshing) {
      this.refreshing = this.tryRefresh().finally(() => {
        this.refreshing = null;
      });
    }
    return this.refreshing;
  }
  async request(endpoint, options = {}, _isRetry = false) {
    const headers = {
      "Content-Type": "application/json",
      ...options.headers
    };
    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1e4);
    let response;
    try {
      response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers,
        credentials: "include",
        signal: options.signal ?? controller.signal
      });
    } finally {
      clearTimeout(timeoutId);
    }
    if (response.status === 401 && !_isRetry) {
      const refreshed = await this.ensureRefresh();
      if (refreshed) {
        return this.request(endpoint, options, true);
      }
      this.setToken(null);
      throw new Error("Sesion expirada");
    }
    if (response.status === 401) {
      this.setToken(null);
      throw new Error("Sesion expirada");
    }
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }
  async get(endpoint, headers) {
    return this.request(endpoint, { method: "GET", headers });
  }
  async post(endpoint, data, headers) {
    return this.request(endpoint, {
      method: "POST",
      headers,
      body: data ? JSON.stringify(data) : void 0
    });
  }
  async put(endpoint, data, headers) {
    return this.request(endpoint, {
      method: "PUT",
      headers,
      body: data ? JSON.stringify(data) : void 0
    });
  }
  async patch(endpoint, data, headers) {
    return this.request(endpoint, {
      method: "PATCH",
      headers,
      body: data ? JSON.stringify(data) : void 0
    });
  }
  async delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
  async authenticate(endpoint, payload) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
      credentials: "include"
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Credenciales invalidas" }));
      throw new Error(error.detail || "Credenciales invalidas");
    }
    return response.json();
  }
  async login(credentials) {
    const payload = {
      email: credentials.username.trim(),
      password: credentials.password
    };
    if (credentials.totp_code?.trim()) {
      payload.totp_code = credentials.totp_code.trim();
    }
    if (credentials.email_verify_code?.trim()) {
      payload.email_verify_code = credentials.email_verify_code.trim();
    }
    return this.authenticate("/api/auth/login", payload);
  }
  async verifyTotp(credentials) {
    const payload = {
      email: credentials.username.trim(),
      password: credentials.password,
      totp_code: credentials.totp_code?.trim() || ""
    };
    if (!payload.totp_code) {
      throw new Error("Codigo 2FA requerido");
    }
    return this.authenticate("/api/auth/totp/verify", payload);
  }
  async logout() {
    try {
      await fetch(`${this.baseUrl}/api/auth/logout`, {
        method: "POST",
        credentials: "include"
      });
    } catch {
    }
    this.setToken(null);
  }
}
const api = new ApiClient(API_BASE_URL);
export {
  api as a
};
