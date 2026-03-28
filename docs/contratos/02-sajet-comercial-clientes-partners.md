# Contratos SAJET — Comercial, Clientes y Partners

Estado: vigente  
Validado: 2026-03-27  
Fuente de verdad: `app.main`, routers FastAPI en `app/routes/` y OpenAPI runtime.

Contratos comerciales, públicos y de portales que conectan landing, clientes, partners y onboarding.

## Cobertura

- Contratos unicos documentados en este archivo: **144**
- Registros duplicados detectados en runtime dentro de este dominio: **16**
- Los duplicados se marcan en la columna `estado` para no inflar el inventario.

## Entradas y salidas

### `/api/branding/tenant/{subdomain}`

- Entrada: `subdomain` por path.
- Salida: branding resuelto para Odoo o frontend público. Si no existe partner/profile retorna defaults Jeturing.

Response típica:

```json
{
  "brand_name": "Partner Name",
  "product_name": "Partner Name",
  "logo_url": "/jeturing_branding/static/img/JEturing.png",
  "favicon_url": null,
  "primary_color": "#4F46E5",
  "secondary_color": "#7C3AED",
  "support_email": "help@jeturing.com",
  "support_url": "https://jeturing.com/help",
  "custom_css": null,
  "is_partner_branded": true
}
```

### `/api/customers/*`, `/api/partners/*`, `/api/partner-portal/*`

- Entrada: cookies JWT por rol o payload JSON de formularios admin/portal.
- Salida: CRUD de clientes/socios, vínculo comercial, pricing y onboarding asociado.

### `/api/customer-onboarding/*`

- Entrada: flujo mixto de onboarding de cliente, con pasos públicos/controlados y pasos admin.
- Salida: estado, avance de paso, carga de perfil, bypass y reseteo operativo.

## Inventario /api/accountant

Contratos unicos en este grupo: **4**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/accountant/dashboard | cookie JWT accountant/admin | portal accountant | FastAPI → accountant_portal.py | app/routes/accountant_portal.py | portal | activo; registro duplicado x2 |
| POST | /api/accountant/invite-client | cookie JWT accountant/admin | portal accountant | FastAPI → accountant_portal.py | app/routes/accountant_portal.py | portal | activo; registro duplicado x2 |
| POST | /api/accountant/switch-tenant | cookie JWT accountant/admin | portal accountant | FastAPI → accountant_portal.py | app/routes/accountant_portal.py | portal | activo; registro duplicado x2 |
| GET | /api/accountant/tenants | cookie JWT accountant/admin | portal accountant | FastAPI → accountant_portal.py | app/routes/accountant_portal.py | portal | activo; registro duplicado x2 |

## Inventario /api/agreements

Contratos unicos en este grupo: **9**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/agreements/required/{target_type} | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| POST | /api/agreements/sign | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| GET | /api/agreements/signed | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| GET | /api/agreements/signed/{signed_id}/pdf | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| GET | /api/agreements/templates | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| POST | /api/agreements/templates | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| DELETE | /api/agreements/templates/{template_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| GET | /api/agreements/templates/{template_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |
| PUT | /api/agreements/templates/{template_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → agreements.py | app/routes/agreements.py | admin | activo |

## Inventario /api/blueprints

Contratos unicos en este grupo: **9**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/blueprints/modules | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| POST | /api/blueprints/modules | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| GET | /api/blueprints/modules/categories | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| POST | /api/blueprints/modules/import-fs | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| PUT | /api/blueprints/modules/{module_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| GET | /api/blueprints/packages | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| POST | /api/blueprints/packages | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| GET | /api/blueprints/packages/{package_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |
| PUT | /api/blueprints/packages/{package_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → blueprints.py | app/routes/blueprints.py | admin | activo |

## Inventario /api/branding

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/branding/profiles | cookie JWT / rol aplicado | frontend/admin | FastAPI → branding.py | app/routes/branding.py | admin | activo |
| POST | /api/branding/profiles | cookie JWT / rol aplicado | frontend/admin | FastAPI → branding.py | app/routes/branding.py | admin | activo |
| GET | /api/branding/profiles/{profile_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → branding.py | app/routes/branding.py | admin | activo |
| PUT | /api/branding/profiles/{profile_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → branding.py | app/routes/branding.py | admin | activo |
| GET | /api/branding/resolve/{domain} | publico | frontend/admin | FastAPI → branding.py | app/routes/branding.py | admin | activo |
| GET | /api/branding/tenant/{subdomain} | publico | frontend/admin | FastAPI → branding.py | app/routes/branding.py | admin | activo |

## Inventario /api/catalog

Contratos unicos en este grupo: **9**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/catalog | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| POST | /api/catalog | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| GET | /api/catalog/plan-links | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| POST | /api/catalog/plan-links | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| DELETE | /api/catalog/plan-links/{link_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| PUT | /api/catalog/plan-links/{link_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| DELETE | /api/catalog/{item_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| PUT | /api/catalog/{item_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| PUT | /api/catalog/{item_id}/reactivate | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |

## Inventario /api/communications

Contratos unicos en este grupo: **3**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/communications/history | cookie JWT / rol aplicado | frontend/admin | FastAPI → communications.py | app/routes/communications.py | admin | activo |
| GET | /api/communications/history/{log_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → communications.py | app/routes/communications.py | admin | activo |
| GET | /api/communications/stats | cookie JWT / rol aplicado | frontend/admin | FastAPI → communications.py | app/routes/communications.py | admin | activo |

## Inventario /api/customer-onboarding

Contratos unicos en este grupo: **12**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/customer-onboarding/admin/advance/{customer_id} | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| GET | /api/customer-onboarding/admin/ecf-customers | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| GET | /api/customer-onboarding/admin/pending | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/admin/{customer_id}/bypass | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/admin/{customer_id}/reset-onboarding | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/admin/{customer_id}/set-step | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/complete | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/ecf-questionnaire | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/set-password | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/skip-ecf | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| GET | /api/customer-onboarding/status | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |
| POST | /api/customer-onboarding/update-profile | mixto onboarding | frontend/admin | FastAPI → customer_onboarding.py | app/routes/customer_onboarding.py | portal | activo |

## Inventario /api/customers

Contratos unicos en este grupo: **11**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/customers | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers/bulk-create-stripe | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers/recalculate-all | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| PUT | /api/customers/{customer_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers/{customer_id}/create-stripe-customer | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers/{customer_id}/portal-bypass | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers/{customer_id}/portal-credentials | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers/{customer_id}/reset-password | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| POST | /api/customers/{customer_id}/send-credentials | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |
| PUT | /api/customers/{customer_id}/users | cookie JWT / rol aplicado | frontend/admin | FastAPI → customers.py | app/routes/customers.py | admin | activo |

## Inventario /api/dashboard

Contratos unicos en este grupo: **2**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/dashboard/all | cookie JWT / rol aplicado | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | admin | activo |
| GET | /api/dashboard/metrics | cookie JWT / rol aplicado | frontend/admin | FastAPI → dashboard.py | app/routes/dashboard.py | admin | activo |

## Inventario /api/leads

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/leads | cookie JWT / rol aplicado | frontend/admin | FastAPI → leads.py | app/routes/leads.py | admin | activo |
| POST | /api/leads | cookie JWT / rol aplicado | frontend/admin | FastAPI → leads.py | app/routes/leads.py | admin | activo |
| DELETE | /api/leads/{lead_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → leads.py | app/routes/leads.py | admin | activo |
| GET | /api/leads/{lead_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → leads.py | app/routes/leads.py | admin | activo |
| PUT | /api/leads/{lead_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → leads.py | app/routes/leads.py | admin | activo |
| POST | /api/leads/{lead_id}/convert | cookie JWT / rol aplicado | frontend/admin | FastAPI → leads.py | app/routes/leads.py | admin | activo |

## Inventario /api/onboarding-config

Contratos unicos en este grupo: **8**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/onboarding-config/active | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |
| GET | /api/onboarding-config/admin | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |
| POST | /api/onboarding-config/admin | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |
| DELETE | /api/onboarding-config/admin/{config_key} | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |
| GET | /api/onboarding-config/admin/{config_key} | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |
| PUT | /api/onboarding-config/admin/{config_key} | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |
| POST | /api/onboarding-config/admin/{config_key}/activate | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |
| GET | /api/onboarding-config/admin/{config_key}/preview | cookie JWT / rol aplicado | frontend/admin | FastAPI → onboarding_config.py | app/routes/onboarding_config.py | admin | activo |

## Inventario /api/partner-portal

Contratos unicos en este grupo: **24**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/partner-portal/admin/invite | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/admin/reset-password | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/change-password | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/clients | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/clients | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/commissions | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/dashboard | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/invoices | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/invoices/{invoice_id}/pay | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/leads | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/leads | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| PUT | /api/partner-portal/leads/{lead_id} | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/onboarding/set-password | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/onboarding/skip-stripe | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/onboarding/start-stripe | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/onboarding/status | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/onboarding/update-profile | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| POST | /api/partner-portal/onboarding/verify-stripe | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/pricing | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/profile | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| PUT | /api/partner-portal/profile | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/stripe/balance | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/stripe/dashboard-link | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |
| GET | /api/partner-portal/stripe/status | cookie JWT partner | portal partner | FastAPI → partner_portal.py | app/routes/partner_portal.py | portal | activo |

## Inventario /api/partners

Contratos unicos en este grupo: **16**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/partners | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| POST | /api/partners | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| POST | /api/partners/request-partner-change | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| DELETE | /api/partners/{partner_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| GET | /api/partners/{partner_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| PUT | /api/partners/{partner_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| POST | /api/partners/{partner_id}/activate | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| GET | /api/partners/{partner_id}/available-customers | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| POST | /api/partners/{partner_id}/link-customer | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| GET | /api/partners/{partner_id}/pricing | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| POST | /api/partners/{partner_id}/pricing | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| DELETE | /api/partners/{partner_id}/pricing/{override_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| PUT | /api/partners/{partner_id}/pricing/{override_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| GET | /api/partners/{partner_id}/simulate-pricing | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| POST | /api/partners/{partner_id}/transfer-customer | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |
| POST | /api/partners/{partner_id}/unlink-customer/{customer_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → partners.py | app/routes/partners.py | admin | activo |

## Inventario /api/public

Contratos unicos en este grupo: **12**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| POST | /api/public/calculate | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/catalog | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/content | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/modules | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/packages | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| POST | /api/public/partner-signup | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/partner/{code} | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/partners | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/plans | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/stats | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/testimonials | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |
| GET | /api/public/translations | publico | landing/browser | FastAPI → public_landing.py | app/routes/public_landing.py | publico | activo; registro duplicado x2 |

## Inventario /api/quotations

Contratos unicos en este grupo: **6**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/quotations | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| POST | /api/quotations | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| DELETE | /api/quotations/{quote_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| GET | /api/quotations/{quote_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| PUT | /api/quotations/{quote_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |
| POST | /api/quotations/{quote_id}/send | cookie JWT / rol aplicado | frontend/admin | FastAPI → quotations.py | app/routes/quotations.py | admin | activo |

## Inventario /api/work-orders

Contratos unicos en este grupo: **7**.

| método | ruta | auth | caller | target | módulo/archivo fuente | tipo | estado |
|---|---|---|---|---|---|---|---|
| GET | /api/work-orders | cookie JWT / rol aplicado | frontend/admin | FastAPI → work_orders.py | app/routes/work_orders.py | admin | activo |
| POST | /api/work-orders | cookie JWT / rol aplicado | frontend/admin | FastAPI → work_orders.py | app/routes/work_orders.py | admin | activo |
| GET | /api/work-orders/catalog/modules | cookie JWT / rol aplicado | frontend/admin | FastAPI → work_orders.py | app/routes/work_orders.py | admin | activo |
| GET | /api/work-orders/catalog/packages | cookie JWT / rol aplicado | frontend/admin | FastAPI → work_orders.py | app/routes/work_orders.py | admin | activo |
| GET | /api/work-orders/{wo_id} | cookie JWT / rol aplicado | frontend/admin | FastAPI → work_orders.py | app/routes/work_orders.py | admin | activo |
| POST | /api/work-orders/{wo_id}/approve-modules | cookie JWT / rol aplicado | frontend/admin | FastAPI → work_orders.py | app/routes/work_orders.py | admin | activo |
| PUT | /api/work-orders/{wo_id}/status | cookie JWT / rol aplicado | frontend/admin | FastAPI → work_orders.py | app/routes/work_orders.py | admin | activo |

## Puntos de quiebre

- `branding.py`: si falla la resolución `subdomain -> customer -> partner -> profile`, Odoo cae a defaults y se pierde white-label.
- `customers.py`, `partners.py`, `partner_portal.py`: drift entre partner, customer y suscripción genera inconsistencias de ownership, pricing y acceso al portal.
- `customer_onboarding.py` y `agreements.py`: si cambia la secuencia de onboarding o el estado requerido, se rompen altas de clientes y contratos firmados.
- `work_orders.py`, `blueprints.py`, `quotations.py`: un desalineamiento entre catálogo, paquetes y aprobación de módulos rompe el handoff comercial -> operativo.

## Observabilidad

- Branding público verificable en `/api/branding/tenant/{subdomain}` y `/api/branding/resolve/{domain}`.
- Portales y onboarding dependen de cookies JWT y del estado persistido en PostgreSQL; revisar `customers`, `partners`, `subscriptions`, `agreements`.
- Las rutas públicas y comerciales están incluidas en OpenAPI; conviene contrastarlas con `docs/flujos/08-clientes-stripe-email` y `docs/flujos/09-ecosistema-partners`.
