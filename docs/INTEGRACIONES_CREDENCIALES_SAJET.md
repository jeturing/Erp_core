# Credenciales de Integraciones saliendo desde sajet.us

Estado: vigente para panel de administración en `/api/settings/credentials`.

## Objetivo

Centralizar en SAJET (`sajet.us`) las credenciales y endpoints públicos de integraciones externas para evitar drift entre `.env`, Odoo y webhooks por tenant.

---

## Integraciones y endpoints públicos

| Integración | Endpoint público SAJET                        | Estado                      |
| ----------- | --------------------------------------------- | --------------------------- |
| Meta        | `https://sajet.us/meta/webhook`               | Activo                      |
| DoorDash    | `https://sajet.us/kds/webhook/doordash-drive` | Activo                      |
| Gusto       | `https://sajet.us/api/v1/gusto/webhook`       | Activo                      |
| Uber        | `https://sajet.us/kds/webhook/uber`           | Documentado en credenciales |
| PedidosYa   | `https://sajet.us/kds/webhook/pedidosya`      | Documentado en credenciales |

---

## Claves disponibles en el panel de credenciales

### Gusto (`gusto`)

- `GUSTO_ENV`
- `GUSTO_CLIENT_ID`
- `GUSTO_CLIENT_SECRET`
- `GUSTO_API_VERSION`
- `GUSTO_REDIRECT_URI`
- `GUSTO_WEBHOOK_URL`
- `GUSTO_WEBHOOK_SECRET`
- `GUSTO_BACKEND_API_TOKEN`
- `GUSTO_SCOPES`
- `GUSTO_STATE_SECRET`

### Meta (`meta`)

- `META_PROXY_BASE_URL`
- `META_OAUTH_REDIRECT_URI`
- `META_WEBHOOK_URL`
- `META_WEBHOOK_BEARER`
- `META_WEBHOOK_TARGETS`
- `META_WEBHOOK_TARGET_PATHS`

### DoorDash (`delivery_doordash`)

- `DOORDASH_WEBHOOK_URL`
- `DOORDASH_WEBHOOK_BEARER`
- `DOORDASH_WEBHOOK_TARGETS`

### Uber (`delivery_uber`)

- `UBER_WEBHOOK_URL`
- `UBER_WEBHOOK_BEARER`
- `UBER_WEBHOOK_TARGETS`
- `UBER_CLIENT_ID`
- `UBER_CLIENT_SECRET`

### PedidosYa (`delivery_pedidosya`)

- `PEDIDOSYA_WEBHOOK_URL`
- `PEDIDOSYA_WEBHOOK_BEARER`
- `PEDIDOSYA_WEBHOOK_TARGETS`
- `PEDIDOSYA_CLIENT_ID`
- `PEDIDOSYA_CLIENT_SECRET`

---

## Operación recomendada

1. Configurar/rotar secretos desde panel admin (categoría correspondiente).
2. Mantener webhooks públicos con dominio `sajet.us`.
3. Usar `*_WEBHOOK_TARGETS` para enrutar a tenants específicos cuando aplique.
4. No guardar secretos en código ni hardcodearlos en módulos Odoo.

---

## Referencias técnicas

- Router Meta fanout: `app/routes/meta_webhooks.py`
- Router DoorDash fanout: `app/routes/doordash_webhooks.py`
- Router Gusto: `app/routes/gusto_payroll.py`
- Catálogo de credenciales: `app/routes/settings.py`
