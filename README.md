# ERP Core SaaS (Jeturing) - Estado Vigente

Estado: vigente  
Validado: 2026-02-14  
Entorno objetivo: `/opt/Erp_core` + publicación en PCT160

## Resumen
Repositorio de operación SaaS para onboarding, administración multi-tenant, dominios, infraestructura y facturación.

La interfaz oficial de administración/portal es una SPA Svelte servida por FastAPI en:
- `/admin` (admin core)
- `/tenant/portal` (portal tenant)

Se mantiene compatibilidad operativa legacy para:
- `/admin/logs`
- `/admin/tunnels`

## Arquitectura real
- Backend: FastAPI (`app/main.py`) con routers en `app/routes/`
- Frontend SPA: Svelte + Vite en `frontend/`
- Assets SPA publicados en `static/spa/`
- Templates legacy en `templates/`
- Scripts operativos en `scripts/`

## Rutas web públicas vigentes
- `/` landing pública
- `/signup` onboarding público
- `/login/admin` -> entrada login unificado SPA
- `/login/tenant` -> entrada login unificado SPA
- `/admin` -> SPA shell admin
- `/tenant/portal` -> SPA shell tenant
- `/admin/logs` y `/admin/tunnels` -> vistas legacy operativas

## Endpoints API vigentes (core)
Auth:
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Admin core:
- `GET /api/dashboard/metrics`
- `GET|POST /api/tenants`
- `PUT /api/provisioning/tenant/password`
- `PUT /api/provisioning/tenant/suspend`
- `GET|POST|PUT|DELETE /api/domains*`
- `GET /api/nodes`
- `GET /api/nodes/status`
- `GET /api/nodes/metrics/summary`
- `GET /api/nodes/containers/all`
- `GET /api/billing/metrics`
- `GET /api/billing/invoices`
- `GET /api/billing/stripe-events`
- `GET /api/settings`
- `PUT /api/settings/{key}`
- `GET /api/settings/odoo/current`
- `PUT /api/settings/odoo`

Portal tenant:
- `GET /tenant/api/info`
- `GET /tenant/api/billing`
- `POST /tenant/api/update-payment`
- `POST /tenant/api/cancel-subscription`
- `GET /api/domains/my-domains`

## Frontend SPA (hash routes)
- `#/dashboard`
- `#/tenants`
- `#/domains`
- `#/infrastructure`
- `#/billing`
- `#/settings`
- `#/portal`
- `#/login`

## Build, deploy y verificación
Build SPA + publicación de assets:
```bash
cd /opt/Erp_core
./scripts/build_static.sh
```

Deploy (perfil PCT160):
```bash
cd /opt/Erp_core
./scripts/deploy_to_server.sh --profile pct160
```

Smoke tests:
```bash
cd /opt/Erp_core
./scripts/smoke_pct160.sh
```

## Notas operativas
- `scripts/smoke_pct160.sh` carga `.env` local para credenciales admin.
- El deploy reinicia servicio vía `APP_SERVICE` (parametrizable).
- Si falta build SPA, backend responde `503` en shell SPA hasta ejecutar `build_static.sh`.

## Automatización de dominios (fallback)
- Documento operativo: `docs/DOMAIN_AUTOMATION_FALLBACK.md`
- Sync script: `scripts/domain_sync.sh`
- Instalación de timer systemd en PCT: `scripts/install_domain_sync_timer.sh`
- Servicio túnel esperado en PCT 105: `cloudflared-tcs-sajet-tunnel`

## Documentación
Índice maestro: `docs/INDICE.md`
