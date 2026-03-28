# Contratos Odoo — Integraciones Salientes

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: llamadas `requests.*`, `httpx` y servicios externos detectados en addons Odoo seleccionados.

Este archivo documenta los contratos outbound que cruzan el borde del sistema y pueden romper el ecosistema aunque no expongan endpoint propio.

## Inventario

| módulo | caller | target | auth/secret | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|
| `jeturing_erp_sync` | Odoo tenant event hooks / cron | `POST https://sajet.us/api/webhooks/odoo` | `X-API-KEY` actual; HMAC pendiente | `odoo/Extra/jeturing_erp_sync/models/erp_sync_mixin.py` | integracion_saliente | activo |
| `jeturing_branding` | Odoo branding resolver | `GET <base_url>/api/branding/tenant/{subdomain}` | sin auth; usa base derivada de `jeturing_erp_sync.webhook_url` | `odoo/Extra/jeturing_branding/controllers/error_handler.py`, `odoo/Extra/jeturing_branding/models/branding_helper.py` | integracion_saliente | activo |
| `jeturing_e_nfc` | certificacion fiscal Odoo | API FEL / DGII desde `jeturing_e_nfc.api_url` | usuario, password, entity configurados en `ir.config_parameter` | `odoo/Extra/jeturing_e_nfc/models/api_service.py` | integracion_saliente | activo |
| `jeturing_meta_hub` | social hub / AI | Meta Graph API, Facebook Login, OpenAI, Anthropic, Gemini, GitHub Models, Ollama/vLLM, custom endpoints | bearer/API keys/provider keys | `odoo/Extra/jeturing_meta_hub/models/social_account.py`, `meta_ai_agent.py`, `wizard/social_connect_wizard.py` | integracion_saliente | activo |
| `jeturing_kds` | kitchen & delivery | Uber OAuth2 + Eats API, DoorDash Drive API | client credentials Uber; JWT HS256 DoorDash | `odoo/Extra/jeturing_kds/services/uber_eats_service.py`, `doordash_service.py` | integracion_saliente | activo |
| `jeturing_ceo_dashboard` | wizard dashboard | `https://api.stripe.com/v1/*` | Stripe secret key ingresada en wizard | `odoo/custom_addons-v19/jeturing_ceo_dashboard/models/stripe_sync.py` | integracion_saliente | activo |
| `jeturing_invoice_stripe_terminal` | terminal/payment transaction | `https://open.er-api.com/*` para FX | sin auth | `odoo/Extra/jeturing_invoice_stripe_terminal/models/payment_transaction.py` | integracion_saliente | activo |
| `spiffy_theme_backend` | chat/push notifications | Firebase Cloud Messaging v1 | service account Google/Firebase | `odoo/custom_addons-v19/spiffy_theme_backend/models/mail_channel.py` | integracion_saliente,vendor | activo |

## Detalle por módulo

### `jeturing_erp_sync`

- Emite `user.created`, `user.updated`, `user.deleted`, `partner.created`, `tenant.config_changed`, `tenant.snapshot`.
- La URL sale de `jeturing_erp_sync.webhook_url`; el módulo trae por defecto `https://sajet.us/api/webhooks/odoo`.
- Riesgo actual: el API key sigue sembrado en `ir_config_parameter.xml`, mientras SAJET ya acepta HMAC opcional.

### `jeturing_branding`

- Deriva `base_url` desde `jeturing_erp_sync.webhook_url` y consulta `/api/branding/tenant/{subdomain}`.
- Si SAJET no responde o no resuelve `Customer -> PartnerBrandingProfile`, Odoo cae a defaults Jeturing.

### `jeturing_e_nfc`

- Empaqueta credenciales y JSON e-CF hacia la API externa configurada por `jeturing_e_nfc.api_url`.
- Usa `POST_DOCUMENT_DO_PDF` y depende de `api_user`, `api_password`, `api_rnc` y formato JSON del builder.
- Drift típico: error 80/82, credenciales, estructura JSON o timeouts del certificador.

### `jeturing_meta_hub`

- `social_account.py` consume `https://graph.facebook.com` para perfiles, insights y cuentas sociales.
- `meta_ai_agent.py` consume varios proveedores (`api.openai.com`, `api.anthropic.com`, `generativelanguage.googleapis.com`, `models.inference.ai.azure.com`, endpoints locales y custom).
- El wizard de conexión arma el Facebook Login/OAuth y redirige usando `web.base.url`.

### `jeturing_kds`

- `uber_eats_service.py` usa `https://login.uber.com/oauth/v2/token` y `https://api.uber.com/v1/eats`.
- `doordash_service.py` usa `https://openapi.doordash.com/drive/v2` con JWT firmado (`developer_id`, `key_id`, `signing_secret`).
- Fallan si expiran credenciales, cambian scopes/claims o se desalinean `store_id` y webhooks entrantes.

### `jeturing_ceo_dashboard`

- Wizard operativo, no backend SAJET: consulta `https://api.stripe.com/v1/*` directamente desde Odoo 19.
- El secreto Stripe se ingresa manualmente en el wizard; esto implica contrato sensible y no centralizado.

### `jeturing_invoice_stripe_terminal`

- Usa `open.er-api.com` para convertir monedas no soportadas por Stripe Terminal a USD.
- Si falla la API de FX, la transacción levanta `UserError` y el cobro queda bloqueado.

### `spiffy_theme_backend`

- Envía push notifications a FCM v1 con service account Google.
- Además de ser vendor, introduce dependencia de credenciales JSON sensibles y de la estructura de Firebase.

## Puntos de quiebre

- Rotación o pérdida de secretos (`API key`, bearer tokens, JWT signing secrets, Stripe keys, Firebase service accounts).
- Drift de URL base: branding depende indirectamente del valor de `jeturing_erp_sync.webhook_url`.
- Timeouts/retries: la mayoría de módulos no centraliza retry/backoff ni circuit breaker.
- Cambios de schema externos: Meta, FEL, Uber, DoorDash, Stripe y Firebase pueden romper sin tocar Odoo.
- Riesgo de hardcode/config default: `jeturing_erp_sync` y algunos fallbacks de URLs/keys siguen siendo frágiles.

## Observabilidad

- Odoo logs del nodo/tenant y logs específicos de cada addon (`jeturing.enfc.log.handler`, `_logger` de Meta/KDS, etc.).
- En SAJET, verificar branding y sync en `/api/branding/tenant/{subdomain}`, `/api/webhooks/odoo/health` y `/api/audit`.
- Para Stripe/Firebase/Meta/Uber/DoorDash/FEL, el contrato real debe verificarse también contra los portales/proveedores externos.
