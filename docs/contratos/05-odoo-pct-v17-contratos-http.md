# Contratos Odoo PCT v17 — HTTP

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: controladores Odoo en `/opt/odoo/Extra/*/controllers/*.py` y decoradores `@http.route`.

Inventario exhaustivo de contratos HTTP publicados por addons Odoo 17 en `Extra`. Se listan rutas publicas, privadas, JSON-RPC, website y webhooks.

## Cobertura

- Decoradores `@http.route` observados en v17/v19: **219**
- Rutas HTTP resueltas solo para `Extra`: **136**
- Addons con superficie HTTP en `Extra`: **13**

## Entradas y salidas

- `jeturing_universal_api` y `jeturing_meta_hub` son las superficies publicas mas sensibles: exponen rutas HTTP consumibles por clientes externos.
- `jeturing_kds` expone webhooks (`uber`, `doordash`) y JSON internos para kitchen dashboard.
- `jeturing_branding` expone lookup de errores y branding dinamico consumido por frontend/Odoo JS.
- `auction_portal`, `jeturing_finance_core` y `jeturing_pass_control` son contratos website/portal con fuerte acoplamiento a UI.

## Addon `JE_Cert`

Contratos HTTP resueltos: **3**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /certificate/search | auth=public; type=http; csrf=True | browser website/portal | Odoo → JE_Cert | odoo/Extra/JE_Cert/controllers/main.py | portal, publico | activo |
| GET | /certificate/verify | auth=public; type=http; csrf=True | browser website/portal | Odoo → JE_Cert | odoo/Extra/JE_Cert/controllers/main.py | portal, publico | activo |
| GET | /certificate/verify/<string:cert_number> | auth=public; type=http; csrf=True | browser website/portal | Odoo → JE_Cert | odoo/Extra/JE_Cert/controllers/main.py | portal, publico | activo |

## Addon `auction_portal`

Contratos HTTP resueltos: **21**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /auction/start | auth=public; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/main.py | portal, publico | activo |
| GET,POST | /auction/start/choose | auth=public; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/main.py | portal, publico | activo |
| GET | /auctions | auth=public; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/main.py | portal, publico | activo |
| GET | /auctions/<int:auction_id> | auth=public; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/main.py | portal, publico | activo |
| GET | /auctions/<int:auction_id>/bid | auth=user; type=json; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/main.py | jsonrpc, portal, interno_ui | activo |
| GET | /auctions/<int:auction_id>/watch | auth=user; type=json; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/main.py | jsonrpc, portal, interno_ui | activo |
| GET | /checkout/<int:checkout_id> | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| GET | /my/bids | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| GET | /my/kyc | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| POST | /my/kyc/bank | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| POST | /my/kyc/identity | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| POST | /my/kyc/tax | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| GET | /my/notifications | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| GET | /my/seller | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| POST | /my/seller/activate | auth=user; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | portal, interno_ui | activo |
| GET | /my/seller/dashboard_data | auth=user; type=json; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/portal.py | jsonrpc, portal, interno_ui | activo |
| GET | /partners | auth=public; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/partners.py | portal, publico | activo |
| GET | /partners/<int:seller_id> | auth=public; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/partners.py | portal, publico | activo; alias/ruta multiple |
| GET | /partners/<int:seller_id>/review | auth=user; type=json; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/partners.py | jsonrpc, portal, interno_ui | activo |
| GET | /partners/<string:seller_slug> | auth=public; type=http; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/partners.py | portal, publico | activo; alias/ruta multiple |
| GET | /partners/review/<int:review_id>/reply | auth=user; type=json; csrf=True | browser website/portal | Odoo → auction_portal | odoo/Extra/auction_portal/controllers/partners.py | jsonrpc, portal, interno_ui | activo |

## Addon `jerturing_score`

Contratos HTTP resueltos: **8**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /jerturing_score/api/v1/contract | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |
| GET | /jerturing_score/api/v1/dashboard | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |
| GET | /jerturing_score/api/v1/partners/<int:partner_id>/decision | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |
| GET | /jerturing_score/api/v1/partners/<int:partner_id>/ecosystem | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |
| POST | /jerturing_score/api/v1/partners/<int:partner_id>/recalculate | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |
| GET | /jerturing_score/api/v1/partners/<int:partner_id>/score | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |
| GET | /jerturing_score/api/v1/providers | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |
| GET | /jerturing_score/api/v1/scores | auth=none; type=http; csrf=False | browser/API externo | Odoo → jerturing_score | odoo/Extra/jerturing_score/controllers/api.py | publico | activo |

## Addon `jeturing_branding`

Contratos HTTP resueltos: **3**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /jeturing/branding/info | auth=public; type=json; csrf=False | browser/API JS | Odoo → jeturing_branding | odoo/Extra/jeturing_branding/controllers/error_handler.py | jsonrpc, publico | activo |
| POST | /jeturing/error/catalog | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_branding | odoo/Extra/jeturing_branding/controllers/error_handler.py | jsonrpc, interno_ui | activo |
| POST | /jeturing/error/lookup | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_branding | odoo/Extra/jeturing_branding/controllers/error_handler.py | jsonrpc, interno_ui | activo |

## Addon `jeturing_e_nfc`

Contratos HTTP resueltos: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /jeturing_e_nfc/download_ri/<int:invoice_id> | auth=user; type=http; csrf=True | usuario autenticado Odoo | Odoo → jeturing_e_nfc | odoo/Extra/jeturing_e_nfc/controllers/website_sale.py | interno_ui | activo |
| GET | /jeturing_e_nfc/prepare_view_context | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_e_nfc | odoo/Extra/jeturing_e_nfc/controllers/main.py | jsonrpc, interno_ui | activo |

## Addon `jeturing_finance_core`

Contratos HTTP resueltos: **3**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /loan/view/detail/<model("loan.request"):loan> | auth=public; type=http; csrf=True | browser website/portal | Odoo → jeturing_finance_core | odoo/Extra/jeturing_finance_core/controllers/main.py | portal, publico | activo |
| GET | /my/loan | auth=user; type=http; csrf=True | browser website/portal | Odoo → jeturing_finance_core | odoo/Extra/jeturing_finance_core/controllers/main.py | portal, interno_ui | activo; alias/ruta multiple |
| GET | /my/loan/page/<int:page> | auth=user; type=http; csrf=True | browser website/portal | Odoo → jeturing_finance_core | odoo/Extra/jeturing_finance_core/controllers/main.py | portal, interno_ui | activo; alias/ruta multiple |

## Addon `jeturing_kds`

Contratos HTTP resueltos: **15**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /kds/dashboard/escalate | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_dashboard.py | jsonrpc, interno_ui | activo |
| POST | /kds/dashboard/live_data | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_dashboard.py | jsonrpc, interno_ui | activo |
| POST | /kds/dashboard/resolve_alert | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_dashboard.py | jsonrpc, interno_ui | activo |
| POST | /kds/dashboard/staff_detail | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_dashboard.py | jsonrpc, interno_ui | activo |
| POST | /kds/doordash/create_delivery | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/doordash_webhook.py | jsonrpc, interno_ui | activo |
| POST | /kds/init | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/line/done | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/line/recall | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/line/start | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/order/bump | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/order/recall | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/orders | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/stations | auth=user; type=json; csrf=True | web client / JS Odoo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/kds_api.py | jsonrpc, interno_ui | activo |
| POST | /kds/webhook/doordash | auth=none; type=json; csrf=False | sistema externo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/doordash_webhook.py | jsonrpc, publico, webhook | activo |
| POST | /kds/webhook/uber | auth=none; type=json; csrf=False | sistema externo | Odoo → jeturing_kds | odoo/Extra/jeturing_kds/controllers/uber_webhook.py | jsonrpc, publico, webhook | activo |

## Addon `jeturing_meta_hub`

Contratos HTTP resueltos: **14**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /jeturing_meta/ai/chat | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| POST | /jeturing_meta/ai/messages | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| POST | /jeturing_meta/ai/providers | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| POST | /jeturing_meta/ai/session/create | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| POST | /jeturing_meta/ai/session/delete | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| POST | /jeturing_meta/ai/sessions | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| GET | /jeturing_meta/api/v1/contract | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | publico | activo |
| GET | /jeturing_meta/api/v1/conversations | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | publico | activo |
| GET | /jeturing_meta/api/v1/conversations/<int:conversation_id> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | publico | activo |
| POST | /jeturing_meta/api/v1/conversations/<int:conversation_id>/send | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | publico | activo |
| POST | /jeturing_meta/dashboard/stats | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| POST | /jeturing_meta/social/dashboard/stats | auth=user; type=json; csrf=False | web client / JS Odoo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | jsonrpc, interno_ui | activo |
| GET | /jeturing_meta/webhook | auth=none; type=http; csrf=False | sistema externo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | publico, webhook | activo |
| POST | /jeturing_meta/webhook | auth=none; type=http; csrf=False | sistema externo | Odoo → jeturing_meta_hub | odoo/Extra/jeturing_meta_hub/controllers/api.py | publico, webhook | activo |

## Addon `jeturing_pass_control`

Contratos HTTP resueltos: **4**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /pass-control/kiosk | auth=user; type=http; csrf=True | usuario autenticado Odoo | Odoo → jeturing_pass_control | odoo/Extra/jeturing_pass_control/controllers/kiosk.py | interno_ui | activo |
| GET | /pass-control/kiosk/public/<string:token> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_pass_control | odoo/Extra/jeturing_pass_control/controllers/kiosk.py | publico | activo |
| GET | /pass-control/kiosk/public/scan | auth=public; type=json; csrf=False | browser/API JS | Odoo → jeturing_pass_control | odoo/Extra/jeturing_pass_control/controllers/kiosk.py | jsonrpc, publico | activo |
| GET | /resident/id/verify/<string:qr_token> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_pass_control | odoo/Extra/jeturing_pass_control/controllers/kiosk.py | publico | activo |

## Addon `jeturing_smart_push`

Contratos HTTP resueltos: **13**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /spc/push/behavior | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| GET | /spc/push/content-recommendations/<string:device_id> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| POST | /spc/push/feedback | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| GET | /spc/push/health | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| PUT | /spc/push/preferences | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| GET | /spc/push/preferences/<string:device_id> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| POST | /spc/push/register | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| POST | /spc/push/send | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| GET | /spc/push/smart-timing/<string:device_id> | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| POST | /spc/push/subscribe | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| GET | /spc/push/topics | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| POST | /spc/push/unregister | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |
| POST | /spc/push/unsubscribe | auth=public; type=http; csrf=False | browser/API externo | Odoo → jeturing_smart_push | odoo/Extra/jeturing_smart_push/controllers/api.py | publico | activo |

## Addon `jeturing_stripe_onboarding`

Contratos HTTP resueltos: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /jeturing/stripe/callback | auth=user; type=http; csrf=True | usuario autenticado Odoo | Odoo → jeturing_stripe_onboarding | odoo/Extra/jeturing_stripe_onboarding/controllers/onboarding.py | interno_ui | activo |
| GET | /jeturing/stripe/register | auth=user; type=http; csrf=True | usuario autenticado Odoo | Odoo → jeturing_stripe_onboarding | odoo/Extra/jeturing_stripe_onboarding/controllers/onboarding.py | interno_ui | activo |
| POST | /jeturing/stripe/webhook | auth=public; type=http; csrf=False | sistema externo | Odoo → jeturing_stripe_onboarding | odoo/Extra/jeturing_stripe_onboarding/controllers/webhooks.py | publico, webhook | activo |
| GET | /my/stripe/onboarding | auth=user; type=http; csrf=True | browser website/portal | Odoo → jeturing_stripe_onboarding | odoo/Extra/jeturing_stripe_onboarding/controllers/portal.py | portal, interno_ui | activo |
| POST | /my/stripe/onboarding/session | auth=user; type=json; csrf=True | browser website/portal | Odoo → jeturing_stripe_onboarding | odoo/Extra/jeturing_stripe_onboarding/controllers/portal.py | jsonrpc, portal, interno_ui | activo |
| POST | /my/stripe/onboarding/start | auth=user; type=http; csrf=True | browser website/portal | Odoo → jeturing_stripe_onboarding | odoo/Extra/jeturing_stripe_onboarding/controllers/portal.py | portal, interno_ui | activo |

## Addon `jeturing_universal_api`

Contratos HTTP resueltos: **38**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET,POST | /api/v1/accounting/invoices | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /api/v1/accounting/payments | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/apikeys | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/calendar/events | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/contacts | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/crm/leads | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| POST | /api/v1/execute | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /api/v1/info | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| POST | /api/v1/mail/send | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST,PUT,PATCH,DELETE | /api/v1/model/<string:model_name> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /api/v1/models | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /api/v1/ping | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/products | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/projects | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/projects/tasks | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /api/v1/report/<int:report_id> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /api/v1/sales/orders | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /api/v1/schema/<string:model_name> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /api/v1/search | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/accounting/invoices | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /claude/api/v1/accounting/payments | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/apikeys | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/calendar/events | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/contacts | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/crm/leads | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| POST | /claude/api/v1/execute | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /claude/api/v1/info | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| POST | /claude/api/v1/mail/send | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST,PUT,PATCH,DELETE | /claude/api/v1/model/<string:model_name> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /claude/api/v1/models | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /claude/api/v1/ping | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/products | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/projects | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/projects/tasks | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /claude/api/v1/report/<int:report_id> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET,POST | /claude/api/v1/sales/orders | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /claude/api/v1/schema/<string:model_name> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |
| GET | /claude/api/v1/search | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_universal_api | odoo/Extra/jeturing_universal_api/controllers/main.py | publico | activo; alias/ruta multiple |

## Addon `jeturing_whatsapp_hub`

Contratos HTTP resueltos: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /jeturing_whatsapp/api/v1/contract | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/Extra/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| GET | /jeturing_whatsapp/api/v1/conversations | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/Extra/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| GET | /jeturing_whatsapp/api/v1/conversations/<int:conversation_id> | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/Extra/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| POST | /jeturing_whatsapp/api/v1/conversations/<int:conversation_id>/send | auth=none; type=http; csrf=False | browser/API externo | Odoo → jeturing_whatsapp_hub | odoo/Extra/jeturing_whatsapp_hub/controllers/api.py | publico | activo |
| GET | /jeturing_whatsapp/webhook | auth=none; type=http; csrf=False | sistema externo | Odoo → jeturing_whatsapp_hub | odoo/Extra/jeturing_whatsapp_hub/controllers/api.py | publico, webhook | activo |
| POST | /jeturing_whatsapp/webhook | auth=none; type=http; csrf=False | sistema externo | Odoo → jeturing_whatsapp_hub | odoo/Extra/jeturing_whatsapp_hub/controllers/api.py | publico, webhook | activo |

## Puntos de quiebre

- `jeturing_universal_api`: requiere API key y DB multitenant; cualquier drift en `X-Odoo-Db` o autenticacion rompe clientes Claude/GPT/MCP.
- `jeturing_meta_hub` y `jeturing_kds`: combinan webhooks publicos con APIs internas; errores de firma, CSRF o payload afectan mensajeria y delivery.
- `auction_portal` y `website` routes: dependen de templates, sesión web y modelos de portal.
- `jeturing_smart_push`: expone endpoints publicos de push; drift de token/dispositivo o CORS afecta notificaciones web/mobile.

## Observabilidad

- Verificar controller fuente en cada fila y los logs Odoo del tenant/nodo.
- Las rutas `type='json'` normalmente son llamadas por JS del web client; revisar network traces del navegador y logs de Odoo.
- Los webhooks publicos (`jeturing_kds`, `jeturing_meta_hub`, `jeturing_whatsapp_hub`) deben correlacionarse con secretos/config en `ir.config_parameter` o modelos de configuración.
