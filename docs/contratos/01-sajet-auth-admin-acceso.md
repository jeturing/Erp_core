# Contratos SAJET — Auth, Admin y Acceso

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: `app.main`, routers FastAPI en `app/routes/` y OpenAPI runtime.

Contratos de acceso, autenticación, gobierno admin y superficies de entrada al producto.

## Cobertura

- Contratos unicos documentados en este archivo: **117**
- Registros duplicados detectados en runtime dentro de este dominio: **21**
- Los duplicados se marcan en la columna `estado` para no inflar el inventario.

## Entradas y salidas

### `/api/auth/login`

Request body principal:

```json
{
  "email": "user@example.com",
  "password": "secret",
  "totp_code": "123456",
  "email_verify_code": "654321"
}
```

Response esperada:

```json
{
  "message": "ok",
  "role": "admin|partner|tenant|accountant",
  "requires_totp": false,
  "requires_email_verify": false,
  "requires_tenant_selection": false,
  "available_tenants": [],
  "redirect_url": "/admin",
  "email": "user@example.com",
  "email_domain": "example.com",
  "user_id": 10
}
```

### `/api/auth/me`

- Entrada: `access_token` por cookie httpOnly.
- Salida: identidad efectiva del usuario autenticado y su contexto de rol/tenant.

### `/api/settings/*`

- Entrada: `Authorization` header del flujo admin.
- Salida: lectura/escritura de configuración centralizada, credenciales y cambio de ambiente.

## Inventario /

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | / | publico | landing/browser | FastAPI → onboarding.py | app/routes/onboarding.py | publico | activo |

## Inventario /admin

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /admin | publico | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | interno_ui | activo |
| GET | /admin/billing | publico | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | interno_ui | activo |
| GET | /admin/logs | publico | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | interno_ui | activo |
| GET | /admin/settings | publico | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | interno_ui | activo |
| GET | /admin/tenants | publico | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | interno_ui | activo |
| GET | /admin/tunnels | publico | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | interno_ui | activo |

## Inventario /api/admin

Contratos unicos en este grupo: **40**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/admin/cors/refresh | cookie JWT / rol aplicado | frontend/admin | FastAPI → main.py | app/main.py | admin | activo |
| GET | /api/admin/email-templates | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/email-templates | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/email-templates/stats | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/email-templates/{template_type} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| PUT | /api/admin/email-templates/{template_type} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/email-templates/{template_type}/preview | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/email-templates/{template_type}/toggle | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/health | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/landing-sections | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| POST | /api/admin/landing-sections | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| DELETE | /api/admin/landing-sections/{section_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| GET | /api/admin/landing-sections/{section_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| PUT | /api/admin/landing-sections/{section_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| GET | /api/admin/smtp/config | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/smtp/config | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| PUT | /api/admin/smtp/credential/{key} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/smtp/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/smtp/test | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/storage-alerts/active | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/storage-alerts/config | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| PUT | /api/admin/storage-alerts/config | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/storage-alerts/customer/{customer_id}/trends | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/storage-alerts/resolve-batch | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/storage-alerts/slack/enable | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/storage-alerts/stats | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| POST | /api/admin/storage-alerts/{alert_id}/resolve | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_control_panel.py | app/routes/admin_control_panel.py | admin | activo |
| GET | /api/admin/stripe-events | cookie JWT / rol aplicado | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | admin | activo |
| GET | /api/admin/testimonials | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| POST | /api/admin/testimonials | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| DELETE | /api/admin/testimonials/{testimonial_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| GET | /api/admin/testimonials/{testimonial_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| PATCH | /api/admin/testimonials/{testimonial_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| PUT | /api/admin/testimonials/{testimonial_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| GET | /api/admin/translations | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| POST | /api/admin/translations | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| DELETE | /api/admin/translations/{translation_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| GET | /api/admin/translations/{translation_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| PATCH | /api/admin/translations/{translation_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |
| PUT | /api/admin/translations/{translation_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_landing.py | app/routes/admin_landing.py | admin | activo; registro duplicado x2 |

## Inventario /api/admin-users

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/admin-users | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_users.py | app/routes/admin_users.py | admin | activo |
| POST | /api/admin-users | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_users.py | app/routes/admin_users.py | admin | activo |
| DELETE | /api/admin-users/{user_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_users.py | app/routes/admin_users.py | admin | activo |
| GET | /api/admin-users/{user_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_users.py | app/routes/admin_users.py | admin | activo |
| PUT | /api/admin-users/{user_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → admin_users.py | app/routes/admin_users.py | admin | activo |

## Inventario /api/api-keys

Contratos unicos en este grupo: **10**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/api-keys | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| POST | /api/api-keys | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| GET | /api/api-keys/tiers | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| DELETE | /api/api-keys/{key_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| GET | /api/api-keys/{key_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| PUT | /api/api-keys/{key_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| POST | /api/api-keys/{key_id}/request-rotation | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| POST | /api/api-keys/{key_id}/rotate | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| GET | /api/api-keys/{key_id}/rotation-requests | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |
| GET | /api/api-keys/{key_id}/usage | cookie JWT / rol aplicado | frontend/admin | FastAPI → api_keys.py | app/routes/api_keys.py | admin | activo |

## Inventario /api/audit

Contratos unicos en este grupo: **5**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/audit | cookie JWT / rol aplicado | frontend/admin | FastAPI → audit.py | app/routes/audit.py | admin | activo |
| GET | /api/audit/events | cookie JWT / rol aplicado | frontend/admin | FastAPI → audit.py | app/routes/audit.py | admin, legacy | activo; compatibilidad |
| GET | /api/audit/events/{event_id:int} | cookie JWT / rol aplicado | frontend/admin | FastAPI → audit.py | app/routes/audit.py | admin, legacy | activo; compatibilidad |
| POST | /api/audit/log | cookie JWT / rol aplicado | frontend/admin | FastAPI → audit.py | app/routes/audit.py | admin | activo |
| GET | /api/audit/{event_id:int} | cookie JWT / rol aplicado | frontend/admin | FastAPI → audit.py | app/routes/audit.py | admin | activo |

## Inventario /api/auth

Contratos unicos en este grupo: **13**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/auth/2fa/backup-codes/regenerate | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/2fa/disable | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/2fa/setup | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| GET | /api/auth/2fa/status | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/2fa/verify | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/login | publico + rate-limit | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/logout | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/logout/all | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| GET | /api/auth/me | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| GET | /api/auth/rate-limit/status | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/refresh | refresh cookie | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/select-tenant | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |
| POST | /api/auth/totp/verify | cookie JWT | frontend/admin | FastAPI → secure_auth.py | app/routes/secure_auth.py | admin | activo |

## Inventario /api/logout

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/logout | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |

## Inventario /api/roles

Contratos unicos en este grupo: **11**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/roles | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |
| POST | /api/roles | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |
| GET | /api/roles/available-tenants | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo; registro duplicado x2 |
| GET | /api/roles/available-users | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo; registro duplicado x2 |
| GET | /api/roles/permissions-catalog | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo; registro duplicado x2 |
| GET | /api/roles/presets | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo; registro duplicado x2 |
| DELETE | /api/roles/{role_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |
| PUT | /api/roles/{role_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |
| GET | /api/roles/{role_id}/users | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |
| POST | /api/roles/{role_id}/users | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |
| DELETE | /api/roles/{role_id}/users/{user_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → roles.py | app/routes/roles.py | admin | activo |

## Inventario /api/settings

Contratos unicos en este grupo: **15**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/settings | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| POST | /api/settings/bulk | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| GET | /api/settings/credentials | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| POST | /api/settings/credentials/bulk | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| PUT | /api/settings/credentials/{key} | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| GET | /api/settings/env | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| GET | /api/settings/environment/current | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| PUT | /api/settings/environment/switch | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| POST | /api/settings/init-defaults | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| PUT | /api/settings/odoo | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| GET | /api/settings/odoo/current | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| GET | /api/settings/stripe/mode | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| POST | /api/settings/stripe/mode | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| GET | /api/settings/{key} | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |
| PUT | /api/settings/{key} | Authorization header (admin) | frontend/admin | FastAPI → settings.py | app/routes/settings.py | admin | activo |

## Inventario /docs/oauth2-redirect

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /docs/oauth2-redirect | publico | frontend/admin | FastAPI → applications.py | /usr/local/lib/python3.11/dist-packages/fastapi/applications.py | publico | activo |

## Inventario /health

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /health | publico | frontend/admin | FastAPI → main.py | app/main.py | publico | activo |

## Inventario /login

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /login | publico | landing/browser | FastAPI → dashboard.py | app/routes/dashboard.py | publico | activo |

## Inventario /login/{role}

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /login/{role} | publico | landing/browser | FastAPI → roles.py | app/routes/roles.py | publico | activo |

## Inventario /onboarding

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /onboarding | publico | landing/browser | FastAPI → onboarding.py | app/routes/onboarding.py | publico | activo |

## Inventario /openapi.json

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /openapi.json | publico | frontend/admin | FastAPI → applications.py | /usr/local/lib/python3.11/dist-packages/fastapi/applications.py | publico | activo |

## Inventario /sajet-api-docs

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /sajet-api-docs | publico | frontend/admin | FastAPI → applications.py | /usr/local/lib/python3.11/dist-packages/fastapi/applications.py | publico | activo |

## Inventario /sajet-api-redoc

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /sajet-api-redoc | publico | frontend/admin | FastAPI → applications.py | /usr/local/lib/python3.11/dist-packages/fastapi/applications.py | publico | activo |

## Inventario /signup

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /signup | publico | landing/browser | FastAPI → onboarding.py | app/routes/onboarding.py | publico | activo |

## Inventario /success

Contratos unicos en este grupo: **1**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /success | publico | landing/browser | FastAPI → onboarding.py | app/routes/onboarding.py | publico | activo |

## Puntos de quiebre

- `secure_auth.py`: errores de login por rate-limit, cookies vencidas, TOTP y selección de tenant.
- `settings.py`: deriva en fallas operativas si hay drift entre `.env`, `config.py` y credenciales guardadas.
- `roles.py`, `audit.py`, `api_keys.py`: cualquier cambio de permisos o revocación impacta flujos admin, partner y tenant.
- Los duplicados de registro en `admin_landing.py`, `accountant_portal.py`, `public_landing.py`, `stripe_sync.py`, `payments.py`, `dispersion.py` aparecen como warning de OpenAPI y pueden confundir tooling externo aunque la app responda.

## Observabilidad

- OpenAPI viva: `/openapi.json`, `/sajet-api-docs`, `/sajet-api-redoc`.
- Auditoría persistente: `/api/audit` y tabla `audit_events`.
- Rutas críticas de acceso: `app/routes/secure_auth.py`, `app/routes/settings.py`, `app/routes/roles.py`, `app/routes/api_keys.py`.
- Para drift de documentación, el runtime emite warnings de `Duplicate Operation ID` al construir OpenAPI; esto es una señal útil de contrato duplicado.
