# 01 - Auth/Login/JWT

Estado: vigente  
Validado: 2026-03-28  
Entorno objetivo: `/opt/Erp_core`


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

## Runtime config
- JWT y credenciales admin críticas se resuelven en runtime vía `get_runtime_setting()`.
- Prioridad efectiva: `system_config` (BD) → `.env` → default.
- En los módulos migrados, cambiar `JWT_SECRET_KEY`, `JWT_ALGORITHM`, expiraciones o `ADMIN_USERNAME/ADMIN_PASSWORD` en BD ya no requiere reinicio del servicio.
- Fuente principal del flujo: `app/routes/auth.py`, `app/routes/roles.py`, `app/routes/secure_auth.py`, `app/security/tokens.py`.

## Hallazgos operativos 2026-03-28
- Partner y tenant requieren verificación por email después de validar contraseña; no es un error, es parte del login nominal. `POST /api/auth/login` responde `requires_email_verify=true` y luego exige reenviar `email_verify_code`. — Confirmado 2026-03-28 [HTTP E2E + código]
- El frontend de login ya soporta este segundo paso en `#/login`. — Confirmado 2026-03-28 [inspección `Login.svelte`]
- `#/recover-account` no ejecuta forgot-password real; hoy solo deriva a soporte por `mailto:`. Un usuario con contraseña perdida no puede completar autoservicio desde esa vista. — Confirmado 2026-03-28 [inspección frontend]

## Operación
1. Si cambia una clave JWT o credencial admin, validar el cambio con login nuevo y `/api/auth/me`.
2. Si el cambio no se refleja, revisar si el endpoint está en un módulo ya migrado a runtime DB-first.
3. `DATABASE_URL` sigue siendo bootstrap; el servicio necesita `.env` para arrancar aunque luego lea secretos desde BD.

## Errores típicos
- `401 Credenciales inválidas`
- `401 Token expirado`
- `429 Rate limit`
- `401 Código 2FA inválido`

## Diagnóstico rápido
1. Revisar cookies `access_token` y `refresh_token`.
2. Verificar `/api/auth/me`.
3. Revisar auditoría/rate limit en logs.
