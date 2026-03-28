# Contrato del Sincronizador Odoo → SAJET

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: `jeturing_erp_sync` en Odoo 17, `app/routes/odoo_webhooks.py`, `app/routes/domains.py`, `app/routes/branding.py`, y pruebas `tests/test_odoo_webhooks.py` + `tests/test_domains.py`.

## Mapa rápido del contrato

- Emisor: addon Odoo `jeturing_erp_sync`.
- Receptor: `POST /api/webhooks/odoo` en SAJET.
- Health probe: `GET /api/webhooks/odoo/health`.
- Objetivo: sincronizar users, partners y snapshot del tenant para poblar `Customer`, `Subscription` y `CustomDomain`.

## Entradas y salidas

### Endpoint receptor SAJET

- Ruta: `POST /api/webhooks/odoo`
- Auth admitida por SAJET:
  - `X-API-KEY` igual a `PROVISIONING_API_KEY`, o
  - `X-Webhook-Signature` HMAC SHA-256 del body usando `ODOO_WEBHOOK_SECRET`.
- Auth actual emitida por Odoo:
  - `X-API-KEY` desde `jeturing_erp_sync.api_key`.
  - El módulo Odoo todavía no emite HMAC.

### Eventos soportados por SAJET

- `user.created`
- `user.updated`
- `user.deleted`
- `partner.created`
- `tenant.config_changed`
- `tenant.snapshot`

### Payload `user.created`

```json
{
  "event": "user.created",
  "tenant_db": "techeels",
  "data": {
    "user_id": 15,
    "login": "usuario@empresa.com",
    "name": "Usuario",
    "active": true,
    "share": false,
    "is_admin": false,
    "groups": ["base.group_user"]
  },
  "timestamp": "2026-03-27T16:00:00Z"
}
```

### Payload `partner.created`

```json
{
  "event": "partner.created",
  "tenant_db": "techeels",
  "data": {
    "partner_id": 220,
    "name": "Cliente Demo",
    "email": "cliente@example.com",
    "phone": "+1 809 555 0000",
    "is_company": true,
    "type": "contact",
    "vat": "101010101",
    "country": "Dominican Republic"
  }
}
```

### Payload `tenant.snapshot` / `tenant.config_changed`

```json
{
  "event": "tenant.snapshot",
  "tenant_db": "latazacuriosa",
  "data": {
    "company_id": 1,
    "company_name": "La Taza Curiosa SRL",
    "company_email": "adm@latazacuriosa.net",
    "company_phone": "+1 809 000 0000",
    "country": "Dominican Republic",
    "vat": "101010101",
    "admin_email": "adm@latazacuriosa.net",
    "user_count": 4,
    "plan_name": "basic",
    "owner_partner_id": null,
    "billing_mode": "legacy_imported",
    "base_url": "https://latazacuriosa.com",
    "domains": [
      {"domain": "latazacuriosa.com", "source": "web.base.url", "is_primary": true},
      {"domain": "www.latazacuriosa.com", "source": "website:1", "is_primary": false}
    ],
    "source": {
      "system": "odoo",
      "database": "latazacuriosa",
      "odoo_version": "17.0"
    }
  }
}
```

### Salida SAJET

Respuesta base:

```json
{
  "success": true,
  "event": "tenant.snapshot",
  "status": "processed",
  "synced": true,
  "customer_created": true,
  "subscription_created": true,
  "customer_id": 10,
  "subscription_id": 22,
  "plan_name": "basic",
  "billing_mode": "legacy_imported",
  "user_count": 4,
  "domains_created": 2,
  "domains_updated": 0,
  "domain_conflicts": [],
  "domains_seen": ["latazacuriosa.com", "www.latazacuriosa.com"]
}
```

## Flujo funcional

1. Odoo detecta evento en `res.users`, `res.partner`, `res.company` o por cron `erp.sync.service`.
2. `erp_sync_mixin` arma payload y lo envía en thread separado a `jeturing_erp_sync.webhook_url`.
3. SAJET valida `X-API-KEY` o HMAC.
4. `odoo_webhooks.py` despacha el evento.
5. Para `tenant.snapshot` / `tenant.config_changed`, SAJET ejecuta `_sync_tenant_snapshot()`.
6. SAJET hace upsert de `Customer` y `Subscription`.
7. SAJET normaliza `domains`, ignora `*.sajet.us` y hace sync hacia `CustomDomain`.
8. Se registra auditoría en `audit_events` con `event_type=ODOO_WEBHOOK_*`.

## Reglas y defaults importantes

- Los dominios `*.sajet.us` se excluyen como externos.
- `plan_name`, `billing_mode` y `owner_partner_id` vienen de `ir.config_parameter` en Odoo.
- `billing_mode` default: `legacy_imported`.
- `tenant.config_changed` en SAJET se trata como snapshot completo.
- El cron `ir_cron_erp_sync_tenant_snapshot` reenvía snapshot cada 15 minutos.

## Pruebas y cobertura vigente

- `tests/test_odoo_webhooks.py`
  - crea customer, subscription y domains desde snapshot.
  - valida que `tenant.config_changed` ignore dominios internos `*.sajet.us`.
- `tests/test_domains.py`
  - valida asociación de dominios, múltiples dominios externos y verificación.
- Resultado verificado el `2026-03-27`: **7 passed**.

## Puntos de quiebre

- Odoo emite solo `X-API-KEY`; si se endurece SAJET a HMAC-only sin actualizar el addon, el sync cae completo.
- `jeturing_erp_sync.api_key` viene sembrado en `ir_config_parameter.xml`; alto riesgo de drift/rotación incompleta.
- Si `web.base.url` o `website.domain` están mal, `CustomDomain` se crea/desactualiza con datos incorrectos.
- Si no existe `TenantDeployment`, SAJET puede asociar dominios con target por defecto y degradar Nginx/tunnel mapping.
- Cambios en `BillingMode`, `Plan` o `Customer.subdomain` impactan reconciliación y ownership.

## Observabilidad

- Odoo PCT105:
  - logs: `/var/log/odoo/odoo.log`
  - stderr: `/var/log/odoo/stderr.log`
  - mensajes del addon: `jeturing_erp_sync: webhook ...`
- SAJET:
  - health: `GET /api/webhooks/odoo/health`
  - auditoría: `GET /api/audit?tenant=<db>&event_type=ODOO_WEBHOOK_*`
  - tablas: `customers`, `subscriptions`, `custom_domains`, `audit_events`
- Verificación manual recomendada:
  1. revisar logs Odoo del tenant,
  2. consultar auditoría SAJET,
  3. confirmar `Customer`, `Subscription` y `CustomDomain` resultantes.
