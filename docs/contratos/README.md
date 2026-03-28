# Contratos del Ecosistema SAJET ↔ Odoo

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: inventario generado desde código (`app.main`, `@http.route`, integraciones salientes detectadas en addons).

## Alcance

- SAJET FastAPI: **468** contratos HTTP únicos deduplicados por `metodo+ruta`.
- Odoo HTTP: **219** decoradores `@http.route` observados y **241** contratos/rutas resueltas contando aliases y listas de paths.
- Integraciones salientes críticas: sync Odoo→SAJET, branding, FEL, Meta Graph API, AI providers, Uber, DoorDash, Stripe, Firebase, FX APIs.

## Índice

1. [01-sajet-auth-admin-acceso.md](01-sajet-auth-admin-acceso.md)
2. [02-sajet-comercial-clientes-partners.md](02-sajet-comercial-clientes-partners.md)
3. [03-sajet-tenants-provisioning-infra.md](03-sajet-tenants-provisioning-infra.md)
4. [04-sajet-billing-pagos-webhooks.md](04-sajet-billing-pagos-webhooks.md)
5. [05-odoo-pct-v17-contratos-http.md](05-odoo-pct-v17-contratos-http.md)
6. [06-odoo-pct-v19-contratos-http.md](06-odoo-pct-v19-contratos-http.md)
7. [07-odoo-integraciones-salientes.md](07-odoo-integraciones-salientes.md)
8. [08-sync-odoo-sajet.md](08-sync-odoo-sajet.md)
9. [09-mapa-ecosistema-y-puntos-de-quiebre.md](09-mapa-ecosistema-y-puntos-de-quiebre.md)

## Convenciones

- `método + ruta` es la unidad canónica de contrato en SAJET.
- En Odoo, una sola función puede exponer múltiples rutas; por eso el conteo de contratos puede ser mayor que el de decoradores.
- La columna `tipo` usa estas etiquetas: `publico`, `admin`, `tenant`, `portal`, `jsonrpc`, `webhook`, `integracion_saliente`, `interno_ui`, `legacy`, `vendor`.
- La columna `estado` marca también duplicados runtime, aliases y superficies legacy/compatibilidad.

## Glosario rápido

- **contrato**: la combinación de ruta, método, auth, payload esperado y efectos laterales.
- **caller**: sistema o actor que inicia la llamada.
- **target**: servicio/controlador que recibe y procesa el contrato.
- **punto de quiebre**: zona donde el contrato puede romperse por auth, red, schema, permisos o drift.

## Uso recomendado

- Para soporte operativo: empezar por `09-mapa-ecosistema-y-puntos-de-quiebre.md`.
- Para SAJET: usar `01` a `04` según dominio.
- Para Odoo: usar `05`, `06` y `07`.
- Para el sincronizador Odoo→SAJET: usar `08`.
