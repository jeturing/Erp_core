# Security Implementation Guide

## Resumen

Este documento describe las características de seguridad implementadas para entornos de producción.

## Características Implementadas

### 1. ✅ HTTPS/TLS Only

**Archivo:** `app/security/middleware.py` - `SecurityMiddleware`

```python
# Configuración en .env
ENVIRONMENT=production
FORCE_HTTPS=true
```

**Características:**
- Redirección automática HTTP → HTTPS
- Header HSTS (Strict-Transport-Security)
- Excepción para `/health` (health checks)

**Headers de seguridad incluidos:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy`
- `Referrer-Policy`
- `Permissions-Policy`

---

### 2. ✅ Tokens en httpOnly Cookies

**Archivo:** `app/security/tokens.py` - `TokenManager`

```python
# Access token de corta duración (15 min por defecto)
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Refresh token de larga duración (7 días por defecto)
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Configuración de cookies:**
```python
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,      # No accesible desde JavaScript
    secure=True,        # Solo HTTPS (en producción)
    samesite="lax",     # Protección CSRF
    max_age=900,        # 15 minutos
    path="/"
)
```

**Ventajas:**
- Tokens no expuestos a XSS
- Rotación automática de refresh tokens
- Revocación de todas las sesiones

---

### 3. ✅ Refresh Tokens

**Archivo:** `app/security/tokens.py` - `RefreshTokenManager`

**Flujo:**
1. Login exitoso → Access token (15 min) + Refresh token (7 días)
2. Access token expira → `POST /api/auth/refresh`
3. Server verifica refresh token → Nuevo access token + Nuevo refresh token

**Endpoints:**
```
POST /api/auth/refresh          # Renovar tokens
POST /api/auth/logout           # Cerrar sesión actual
POST /api/auth/logout/all       # Cerrar TODAS las sesiones
```

**Seguridad:**
- Refresh token rotation (cada uso genera nuevo token)
- Tokens opacos (no JWT) para refresh
- Almacenados como hash SHA-256
- Detección de token robado (reutilización de token revocado)

---

### 4. ✅ Rate Limiting en Login

**Archivo:** `app/security/middleware.py` - `RateLimiter`

```python
# Configuración por defecto
MAX_REQUESTS = 5          # 5 intentos
WINDOW_SECONDS = 300      # en 5 minutos
BLOCK_DURATION = 900      # 15 minutos de bloqueo
```

**Comportamiento:**
- 5 intentos fallidos → Bloqueo temporal de 15 min
- Identificación por IP (considerando X-Forwarded-For)
- Reset automático en login exitoso
- Headers `Retry-After` en respuestas 429

**Endpoint de estado:**
```
GET /api/auth/rate-limit/status
```

---

### 5. ✅ Audit Logging

**Archivo:** `app/security/audit.py` - `AuditLogger`

**Logs almacenados en:** `/opt/onboarding-system/logs/audit.log`

**Eventos registrados:**
- `LOGIN_SUCCESS` / `LOGIN_FAILED`
- `LOGOUT` / `TOKEN_REFRESH`
- `RATE_LIMIT_EXCEEDED`
- `TOTP_ENABLED` / `TOTP_VERIFIED` / `TOTP_FAILED`
- `WAF_BLOCKED`
- `TENANT_CREATED` / `SUBSCRIPTION_CREATED`
- Y más...

**Formato JSON:**
```json
{
  "timestamp": "2026-01-19T10:30:00.000Z",
  "level": "INFO",
  "event": "LOGIN_SUCCESS",
  "username": "admin",
  "role": "admin",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "status": "success"
}
```

---

### 6. ✅ Two-Factor Authentication (2FA/TOTP)

**Archivo:** `app/security/totp.py` - `TOTPManager`

**Compatible con:**
- Google Authenticator
- Microsoft Authenticator
- Authy
- 1Password
- Cualquier app TOTP

**Endpoints:**
```
POST /api/auth/2fa/setup                    # Iniciar configuración
POST /api/auth/2fa/verify                   # Verificar y habilitar
POST /api/auth/2fa/disable                  # Deshabilitar
GET  /api/auth/2fa/status                   # Estado actual
POST /api/auth/2fa/backup-codes/regenerate  # Regenerar códigos
```

**Flujo de configuración:**
1. `POST /2fa/setup` → Recibe QR code + secreto + códigos de respaldo
2. Escanear QR con app
3. `POST /2fa/verify` con código de la app → 2FA habilitado

**Códigos de respaldo:**
- 10 códigos de un solo uso
- Para acceso si se pierde el dispositivo
- Regenerables con código TOTP válido

---

### 7. ✅ Web Application Firewall (WAF)

**Archivo:** `app/security/middleware.py` - `WAFMiddleware`

```python
# Activar/desactivar
ENABLE_WAF=true
```

**Protección contra:**
- SQL Injection
- Cross-Site Scripting (XSS)
- Path Traversal
- Command Injection

**Escanea:**
- URL path
- Query parameters
- Headers sospechosos (User-Agent, Referer, Cookie)

**Respuesta ante ataque:**
```json
{
  "detail": "Solicitud bloqueada por razones de seguridad"
}
```
Status: 403 Forbidden

---

## Variables de Entorno de Seguridad

```bash
# .env para producción

# JWT
JWT_SECRET_KEY=<clave-segura-aleatoria-256-bits>
JWT_REFRESH_SECRET_KEY=<otra-clave-segura>
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Seguridad
ENVIRONMENT=production
FORCE_HTTPS=true
ENABLE_WAF=true

# CORS
ALLOWED_ORIGINS=https://tudominio.com,https://app.tudominio.com

# Logging
LOG_DIR=/var/log/onboarding-system
```

---

## Endpoints de Autenticación Segura

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login con rate limiting y 2FA |
| POST | `/api/auth/refresh` | Renovar access token |
| POST | `/api/auth/logout` | Cerrar sesión |
| POST | `/api/auth/logout/all` | Cerrar todas las sesiones |
| POST | `/api/auth/2fa/setup` | Configurar 2FA |
| POST | `/api/auth/2fa/verify` | Verificar y activar 2FA |
| POST | `/api/auth/2fa/disable` | Desactivar 2FA |
| GET | `/api/auth/2fa/status` | Estado de 2FA |
| GET | `/api/auth/rate-limit/status` | Estado de rate limiting |

---

## Ejemplo de Login con JavaScript

```javascript
// Login
async function login(email, password, role = 'tenant', totpCode = null) {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',  // Importante para cookies
        body: JSON.stringify({
            email,
            password,
            role,
            totp_code: totpCode
        })
    });
    
    const data = await response.json();
    
    if (data.requires_totp) {
        // Mostrar formulario de 2FA
        return showTOTPForm();
    }
    
    if (response.ok) {
        window.location.href = data.redirect_url;
    }
}

// Renovar token automáticamente
async function refreshToken() {
    const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include'
    });
    
    return response.ok;
}

// Logout
async function logout() {
    await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
    });
    window.location.href = '/login/tenant';
}
```

---

## Migración desde Autenticación Legacy

Los endpoints legacy (`/api/admin/login`, `/api/login/unified`) siguen funcionando para compatibilidad. Para migrar:

1. Actualizar frontend para usar `/api/auth/login`
2. Cambiar almacenamiento de token a cookies (automático)
3. Implementar renovación automática de tokens
4. Ofrecer activación de 2FA a usuarios

---

## Checklist de Producción

- [ ] Generar claves JWT seguras (`openssl rand -hex 32`)
- [ ] Configurar `ENVIRONMENT=production`
- [ ] Habilitar `FORCE_HTTPS=true`
- [ ] Configurar CORS con dominios específicos
- [ ] Revisar logs de auditoría regularmente
- [ ] Configurar rotación de logs
- [ ] Implementar backup de códigos 2FA
- [ ] Configurar alertas para `RATE_LIMIT_EXCEEDED` y `WAF_BLOCKED`
