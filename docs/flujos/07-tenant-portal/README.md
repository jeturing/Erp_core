# 07 - Portal Tenant

Estado: vigente  
Validado: 2026-03-28  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Permitir al tenant autenticado ver su plan, estado, facturas y acciones de pago.

## Disparador
- Ruta pública shell: `/tenant/portal`
- APIs: `/tenant/api/*`

## Secuencia ASCII

```text
[Usuario tenant]
   |
   | abre /tenant/portal
   v
[tenant_portal.py]
   |
   +--> valida token role=tenant
   +--> resuelve tenant_id (directo o por email claim)
   v
[SPA route #/portal]
   |
   +--> GET /tenant/api/info
   +--> GET /tenant/api/billing
   v
[Portal con datos del tenant]
```

## Endpoints
- `GET /tenant/api/info`
- `GET /tenant/api/billing`
- `POST /tenant/api/update-payment`
- `POST /tenant/api/cancel-subscription`

## Runtime config
- El portal tenant ya resuelve `STRIPE_SECRET_KEY` y `APP_URL` en runtime desde `system_config` con fallback a `.env`.
- Cambios de Stripe o URL base en BD aplican sin reinicio para las rutas del portal ya migradas.
- Facturas pendientes pueden volver a consultar `hosted_invoice_url` en Stripe con la clave activa del momento.

## Errores típicos
- `403 contexto tenant inválido`
- `404 tenant no encontrado` (antes de fix de resolución por email)
- fallos Stripe al listar facturas
