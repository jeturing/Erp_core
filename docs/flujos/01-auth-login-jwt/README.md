# 01 - Auth/Login/JWT

## Objetivo
Autenticar usuarios admin o tenant, emitir access token + refresh token y exponer sesión activa a la SPA.

## Disparador
- Frontend: login en `#/login`
- API: `POST /api/auth/login`

## Secuencia ASCII

```text
[Browser]
   |
   | email/password (+ opcional TOTP)
   v
[SPA Svelte]
   |
   | POST /api/auth/login
   v
[secure_auth.py]
   |
   +--> valida rate limit
   +--> detecta tipo (admin/tenant)
   +--> valida credenciales
   +--> valida TOTP (si aplica)
   +--> crea access token (JWT)
   +--> crea refresh token (rotativo)
   +--> set-cookie httpOnly
   v
[Response]
   |
   +--> role
   +--> redirect_url
   v
[SPA]
   |
   +--> GET /api/auth/me
   v
[Sesión activa]
```

## Endpoints
- `POST /api/auth/login`
- `POST /api/auth/totp/verify`
- `GET /api/auth/me`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

## Modelos/servicios
- `Customer`
- `app/security/tokens.py`
- `app/security/totp.py`
- `app/security/middleware.py`

## Errores típicos
- `401 Credenciales inválidas`
- `401 Token expirado`
- `429 Rate limit`
- `401 Código 2FA inválido`

## Diagnóstico rápido
1. Revisar cookies `access_token` y `refresh_token`.
2. Verificar `/api/auth/me`.
3. Revisar auditoría/rate limit en logs.
