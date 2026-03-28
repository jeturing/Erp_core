# Contratos Odoo PCT v19 — HTTP

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: controladores Odoo en `/opt/odoo/custom_addons-v19/*/controllers/*.py` y decoradores `@http.route`.

Inventario exhaustivo de rutas HTTP publicadas en Odoo 19. Se separa superficie Jeturing de superficie vendor/custom theme para aislar riesgos.

## Cobertura

- Rutas HTTP resueltas para `custom_addons-v19`: **105**
- Addons Jeturing con superficie HTTP: **5**
- Addons vendor/custom con superficie HTTP: **2**

## Entradas y salidas

- `jeturing_claude_api` es la superficie publica mas amplia de v19 y hereda el patron de API universal con alias `/claude/api/v1/*`.
- `jeturing_sign` expone contratos publicos para firma, OTP, descarga y upload.
- `jeturing_stripe_onboarding` y `jeturing_whatsapp_hub` abren contratos externos de onboarding/webhook.
- `spiffy_theme_backend` expone una gran cantidad de rutas JSON/HTTP del web client y debe tratarse como contrato vendor.

## Jeturing

## Addon `jeturing_ceo_dashboard`

Contratos HTTP resueltos: **9**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /jeturing/dashboard/data | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/email/generate | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/email/send | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/sale_orders | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/status/note | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/status/set | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/stripe/sync | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/task/create | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |
| GET | /jeturing/dashboard/task/update | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_ceo_dashboard | odoo/custom_addons-v19/jeturing_ceo_dashboard/controllers/dashboard_controller.py | jsonrpc, interno_ui | activo |

## Addon `jeturing_claude_api`

Contratos HTTP resueltos: **29**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET,POST | /api/v1/accounting/invoices | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /api/v1/accounting/payments | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/apikeys | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/calendar/events | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/contacts | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/crm/leads | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| POST | /api/v1/execute | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /api/v1/info | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| POST | /api/v1/mail/send | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST,PUT,PATCH,DELETE | /api/v1/model/<string:model_name> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /api/v1/models | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /api/v1/ping | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/products | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/projects | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/projects/tasks | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /api/v1/report/<int:report_id> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /api/v1/sales/orders | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /api/v1/schema/<string:model_name> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /api/v1/search | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /claude/api/v1/accounting/invoices | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /claude/api/v1/apikeys | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /claude/api/v1/contacts | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST | /claude/api/v1/crm/leads | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| POST | /claude/api/v1/execute | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /claude/api/v1/info | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| POST | /claude/api/v1/mail/send | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET,POST,PUT,PATCH,DELETE | /claude/api/v1/model/<string:model_name> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /claude/api/v1/ping | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |
| GET | /claude/api/v1/search | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_claude_api | odoo/custom_addons-v19/jeturing_claude_api/controllers/main.py | publico | activo |

## Addon `jeturing_sign`

Contratos HTTP resueltos: **10**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /sajet/sign | auth=public; type=http; csrf=True | browser website/portal | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | portal, publico | activo |
| POST | /sajet/sign/upload | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | publico | activo |
| GET | /sign/certificate/<string:token>/download | auth=user; type=http; csrf=True | usuario autenticado Odoo | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/certificate_download.py | interno_ui | activo |
| GET | /sign/document/<string:token> | auth=public; type=http; csrf=True | browser website/portal | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | portal, publico | activo |
| POST | /sign/document/<string:token>/decline | auth=public; type=json; csrf=False | browser/API JS | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | jsonrpc, publico | activo |
| GET | /sign/document/<string:token>/download | auth=public; type=http; csrf=True | browser/API externo | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | publico | activo |
| POST | /sign/document/<string:token>/otp/send | auth=public; type=json; csrf=False | browser/API JS | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | jsonrpc, publico | activo |
| POST | /sign/document/<string:token>/otp/verify | auth=public; type=json; csrf=False | browser/API JS | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | jsonrpc, publico | activo |
| GET | /sign/document/<string:token>/pdf | auth=public; type=http; csrf=True | browser/API externo | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | publico | activo |
| POST | /sign/document/<string:token>/submit | auth=public; type=json; csrf=False | browser/API JS | Odoo → jeturing_sign | odoo/custom_addons-v19/jeturing_sign/controllers/main.py | jsonrpc, publico | activo |

## Addon `jeturing_stripe_onboarding`

Contratos HTTP resueltos: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /jeturing/stripe/callback | auth=user; type=http; csrf=True | usuario autenticado Odoo | Odoo → jeturing_stripe_onboarding | odoo/custom_addons-v19/jeturing_stripe_onboarding/controllers/onboarding.py | interno_ui | activo |
| GET | /jeturing/stripe/register | auth=user; type=http; csrf=True | usuario autenticado Odoo | Odoo → jeturing_stripe_onboarding | odoo/custom_addons-v19/jeturing_stripe_onboarding/controllers/onboarding.py | interno_ui | activo |
| POST | /jeturing/stripe/webhook | auth=public; type=http; csrf=False | sistema externo | Odoo → jeturing_stripe_onboarding | odoo/custom_addons-v19/jeturing_stripe_onboarding/controllers/webhooks.py | publico, webhook | activo |
| GET | /my/stripe/onboarding | auth=user; type=http; csrf=True | browser website/portal | Odoo → jeturing_stripe_onboarding | odoo/custom_addons-v19/jeturing_stripe_onboarding/controllers/portal.py | portal, interno_ui | activo |
| POST | /my/stripe/onboarding/session | auth=user; type=json; csrf=True | browser website/portal | Odoo → jeturing_stripe_onboarding | odoo/custom_addons-v19/jeturing_stripe_onboarding/controllers/portal.py | jsonrpc, portal, interno_ui | activo |
| POST | /my/stripe/onboarding/start | auth=user; type=http; csrf=True | browser website/portal | Odoo → jeturing_stripe_onboarding | odoo/custom_addons-v19/jeturing_stripe_onboarding/controllers/portal.py | portal, interno_ui | activo |

## Addon `jeturing_whatsapp_hub`

Contratos HTTP resueltos: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /jeturing_whatsapp/api/v1/contract | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/custom_addons-v19/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| GET | /jeturing_whatsapp/api/v1/conversations | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/custom_addons-v19/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| GET | /jeturing_whatsapp/api/v1/conversations/<int:conversation_id> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/custom_addons-v19/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| POST | /jeturing_whatsapp/api/v1/conversations/<int:conversation_id>/send | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/custom_addons-v19/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| GET | /jeturing_whatsapp/webhook | auth=none; type=http; csrf=False | sistema externo | Odoo → jeturing_whatsapp_hub | odoo/custom_addons-v19/jeturing_whatsapp_hub/controllers/api.py | publico, webhook | activo |
| POST | /jeturing_whatsapp/webhook | auth=none; type=http; csrf=False | sistema externo | Odoo → jeturing_whatsapp_hub | odoo/custom_addons-v19/jeturing_whatsapp_hub/controllers/api.py | publico, webhook | activo |

## Vendor / custom theme

## Addon `atlas_form`

Contratos HTTP resueltos: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /atlas/countries | auth=public; type=http; csrf=True | browser website/portal | Odoo → atlas_form | odoo/custom_addons-v19/atlas_form/controllers/main.py | portal, publico, vendor | activo |
| POST | /atlas/submit | auth=public; type=http; csrf=True | browser website/portal | Odoo → atlas_form | odoo/custom_addons-v19/atlas_form/controllers/main.py | portal, publico, vendor | activo |

## Addon `spiffy_theme_backend`

Contratos HTTP resueltos: **43**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /active/dark/mode | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /add/bookmark/link | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /add/mutli/tab | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| POST | /app/attachment/upload | auth=public; type=http; csrf=False | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | publico, vendor | activo |
| GET | /attach/get_data | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, interno_ui, vendor | activo |
| GET | /change/active/lang | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /color/pallet/ | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /color/pallet/data/ | auth=public; type=http; csrf=True | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | publico, vendor | activo |
| GET | /create/todo | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /delete/todo | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get-favorite-apps | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/active/lang | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/active/menu | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/appsearch/data | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/attachment/data | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/bookmark/link | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/dark/mode/data | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/irmenu/icondata | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/model/record | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/mutli/tab | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /get/records/data | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/global_search_main.py | jsonrpc, publico, vendor | activo |
| GET | /get/records/global/search | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/global_search_main.py | jsonrpc, interno_ui, vendor | activo |
| GET | /get/tab/title/ | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /pwa/enabled | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/pwa.py | jsonrpc, publico, vendor | activo |
| GET | /pwa/offline | auth=public; type=http; csrf=True | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/pwa.py | publico, vendor | activo |
| GET | /remove-user-fav-apps | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /remove/bookmark/link | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /remove/multi/tab | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /service_worker.js | auth=public; type=http; csrf=True | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/pwa.py | publico, vendor | activo |
| GET | /show/user/todo/list/ | auth=public; type=http; csrf=True | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | publico, vendor | activo |
| GET | /sidebar/behavior/update | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| POST | /spiffy/js_error | auth=public; type=http; csrf=False | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/js_error.py | publico, vendor | activo |
| GET | /spiffy_theme_backend/<int:company_id>/manifest.json | auth=public; type=http; csrf=True | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/pwa.py | publico, vendor | activo |
| GET | /text_color/label_color | auth=none; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /theme_color/parameter_check | auth=none; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /update-user-fav-apps | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /update/bookmark/link | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /update/bookmark/panel/show | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /update/tab/details | auth=public; type=json; csrf=True | browser/API JS | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, publico, vendor | activo |
| GET | /web/dataset/call_kw | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, interno_ui, vendor | activo; alias/ruta multiple |
| GET | /web/dataset/call_kw/<path:path> | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | jsonrpc, interno_ui, vendor | activo; alias/ruta multiple |
| GET,POST | /web/login/totp | auth=public; type=http; csrf=True | browser website/portal | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | portal, publico, vendor | activo |
| GET | /web/offline | auth=public; type=http; csrf=True | browser/API externo | Odoo → spiffy_theme_backend | odoo/custom_addons-v19/spiffy_theme_backend/controllers/main.py | publico, vendor | activo |

## Puntos de quiebre

- `jeturing_claude_api`: API keys publicas y CRUD generico sobre modelos; alto riesgo de drift funcional y de permisos.
- `jeturing_sign`: cualquier cambio en tokens publicos, OTP o storage rompe flujos de firma y descarga.
- `spiffy_theme_backend`: al ser vendor/custom theme, una actualizacion del tema puede romper contratos JSON usados por el frontend Odoo.

## Observabilidad

- Revisar logs Odoo y network traces del browser para rutas `type='json'`.
- Para `jeturing_sign`, correlacionar con modelos `document.sign.*`, almacenamiento y correo.
- Para `jeturing_claude_api`, revisar API keys en `claude.api.key` y uso por IP.
