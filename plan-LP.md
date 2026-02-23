# Plan de Producción Sajet.us — Landing Page, Onboarding, Partners y Portal Contadores

## 1. Objetivo General
Rediseñar Sajet.us para convertirlo en una landing page dinámica, conectada al backend, con onboarding flexible (selección de usuarios, partners, contadores), URLs personalizadas para socios, y un portal específico para contadores. Todo el contenido y diseño debe ser gestionable desde el backend, permitiendo al equipo de marketing iterar sin depender de IT.

---

## 2. Alcance
- **Landing principal:** 11 secciones, diseño Ocean Blue, datos dinámicos (planes, features, stats, testimonios).
- **Onboarding:** Selector de usuarios, flujo dual (plan directo o socio), checkout Stripe con cantidad dinámica.
- **Partners:** URLs personalizadas (`/plt/{partner}`), branding, landing propia, onboarding vinculado.
- **Contadores:** Portal específico (`/accountants`), rol y acceso multi-empresa, landing dedicada, onboarding diferenciado.

---

## 3. Estado de Implementación

### ✅ FASE 1 — Backend (COMPLETADA)

#### 3.1. Modelos Nuevos (`app/models/database.py`)
| Modelo                   | Campos clave                                           | Estado |
|--------------------------|--------------------------------------------------------|--------|
| `Testimonial`            | name, role, company, text, stars, avatar_url, locale   | ✅     |
| `AccountantTenantAccess` | accountant_id, tenant_id, access_level, granted_by     | ✅     |
| `AccountantAccessLevel`  | Enum: readonly, readwrite, full                        | ✅     |
| `LandingSection`         | section_key, title, subtitle, badge, ctas, content_json| ✅     |

#### 3.2. Campos Añadidos a Modelos Existentes
| Modelo     | Campo nuevo                  | Propósito                          |
|------------|------------------------------|------------------------------------|
| `Partner`  | `slug`                       | URLs friendly `/plt/{slug}`        |
| `Plan`     | `is_public`                  | Visibilidad en landing             |
| `Plan`     | `is_highlighted`             | Badge "Most Popular"               |
| `Plan`     | `trial_days` (default 14)    | Período de prueba configurable     |
| `Plan`     | `annual_discount_percent`    | Descuento anual configurable (20%) |
| `Customer` | `is_accountant`              | Marca de rol contador              |
| `Customer` | `accountant_firm_name`       | Nombre de firma contable           |

#### 3.3. Endpoints Públicos (`app/routes/public_landing.py`)
| Endpoint                        | Método | Descripción                                  |
|---------------------------------|--------|----------------------------------------------|
| `/api/public/plans`             | GET    | Planes activos + features, filtro is_public   |
| `/api/public/stats`             | GET    | Conteos reales desde DB                       |
| `/api/public/modules`           | GET    | Módulos agrupados por categoría               |
| `/api/public/packages`          | GET    | Blueprints/industrias                         |
| `/api/public/testimonials`      | GET    | Testimonios filtrados por locale              |
| `/api/public/partners`          | GET    | Partners activos con branding                 |
| `/api/public/partner/{code}`    | GET    | Branding + pricing overrides (slug o code)    |
| `/api/public/calculate`         | POST   | Calculadora de precios (users×plan×annual)    |
| `/api/public/content`           | GET    | Secciones CMS por locale                      |
| `/api/public/catalog`           | GET    | Catálogo de servicios agrupado                |

#### 3.4. Endpoints Contadores (`app/routes/accountant_portal.py`)
| Endpoint                         | Método | Descripción                            |
|----------------------------------|--------|----------------------------------------|
| `/api/accountant/tenants`        | GET    | Listar empresas asignadas              |
| `/api/accountant/switch-tenant`  | POST   | Emitir nuevo JWT con tenant_id         |
| `/api/accountant/dashboard`      | GET    | KPIs consolidados multi-cliente        |
| `/api/accountant/invite-client`  | POST   | Solicitar acceso a empresa por email   |

#### 3.5. Onboarding Extendido (`app/routes/onboarding.py`)
- `CheckoutRequest` ahora acepta: `user_count`, `billing_period`, `is_accountant`
- Stripe `line_items.quantity` = `user_count` (antes hardcoded a 1)
- `Customer` se crea con `user_count` e `is_accountant`
- Precio calculado via `plan.calculate_monthly(user_count, partner_id)`

---

### ✅ FASE 2 — Design System + Frontend (COMPLETADA)

#### 4.1. Design System Ocean Blue (`frontend/tailwind.config.js`)
| Token            | Valor          | Uso                          |
|------------------|----------------|------------------------------|
| `primary`        | `#1B4FD8`      | CTAs, links, badges          |
| `primary-light`  | `#E8EEFB`      | Fondos de iconos             |
| `navy`           | `#0F2D7A`      | Hover de CTAs, nav           |
| `secondary`      | `#0EA5E9`      | Acentos horizon              |
| `accent`         | `#10B981`      | Éxito, partners              |
| `slate-dark`     | `#1E293B`      | Títulos                      |
| `slate`          | `#64748B`      | Texto body                   |
| `cloud`          | `#F8FAFC`      | Fondos claros                |
| `border`         | `#E2E8F0`      | Bordes                       |
| `font-jakarta`   | Plus Jakarta Sans | Headlines                |
| `font-inter`     | Inter           | Body text                   |

#### 4.2. Componentes Landing (`frontend/src/lib/components/landing/`)
| # | Componente           | Sección               | Props dinámicas                    |
|---|----------------------|-----------------------|------------------------------------|
| 1 | `NavBar.svelte`      | Navegación sticky     | `partnerBranding`                  |
| 2 | `Hero.svelte`        | Hero + stats          | `stats`, `partnerBranding`         |
| 3 | `SocialProof.svelte` | Logos industrias      | —                                  |
| 4 | `ValueProp.svelte`   | 3 pilares             | —                                  |
| 5 | `FeaturesGrid.svelte`| 6 módulos             | `features`                         |
| 6 | `HowItWorks.svelte`  | 4 pasos               | —                                  |
| 7 | `PricingPreview.svelte`| Planes + UserSelector | `plans`, `partnerCode`            |
| 8 | `ForPartners.svelte` | Programa de socios    | —                                  |
| 9 | `Testimonials.svelte`| Testimonios           | `testimonials`                     |
| 10| `FinalCTA.svelte`    | CTA final             | —                                  |
| 11| `Footer.svelte`      | Footer 4 columnas     | —                                  |

#### 4.3. Páginas de Ruta
| Ruta                  | Componente                | Descripción                            |
|-----------------------|---------------------------|----------------------------------------|
| `#/`                  | `Landing.svelte`          | Landing principal (refactorizada)      |
| `#/accountants`       | `AccountantsLanding.svelte`| Landing para CPAs (7 secciones)       |
| `#/plt/{slug}`        | `PartnerLanding.svelte`   | Landing white-label por partner        |
| `#/accountant-portal` | `AccountantPortal.svelte` | Dashboard multi-tenant contadores      |

#### 4.4. Routing (`App.svelte`)
- `AppPage` type extendido: `'accountants' | 'plt' | 'accountant-portal'`
- Parser de `#/plt/{slug}` → extrae `partnerSlug`
- Rutas públicas: `landing`, `accountants`, `plt` (no requieren auth)
- `accountant-portal` requiere auth + `is_accountant=true`

---

## 4. Arquitectura de Datos

### Landing → API Flow
```
Landing.svelte
  ├── onMount() → fetch /api/public/stats    → Hero stats
  ├── onMount() → fetch /api/public/plans    → PricingPreview
  └── onMount() → fetch /api/public/testimonials → Testimonials

PartnerLanding.svelte
  └── onMount() → fetch /api/public/partner/{slug} → partnerBranding
      └── Landing.svelte(partnerBranding, partnerCode)

PricingPreview.svelte
  ├── userCount selector (1-N)
  ├── annual/monthly toggle
  └── goCheckout() → #/customer-onboarding?plan=X&users=N&billing=annual&partner=slug
```

### Accountant Portal Flow
```
AccountantPortal.svelte
  ├── GET /api/accountant/tenants    → lista empresas
  ├── GET /api/accountant/dashboard  → KPIs consolidados
  └── POST /api/accountant/switch-tenant → nuevo JWT → redirect #/portal
```

---

## 5. Checklist de Migración DB

Ejecutar Alembic migration para:
- [ ] `Partner.slug` — VARCHAR(100), unique, nullable=True
- [ ] `Plan.is_public` — BOOLEAN, default=True
- [ ] `Plan.is_highlighted` — BOOLEAN, default=False
- [ ] `Plan.trial_days` — INTEGER, default=14
- [ ] `Plan.annual_discount_percent` — FLOAT, default=20.0
- [ ] `Customer.is_accountant` — BOOLEAN, default=False
- [ ] `Customer.accountant_firm_name` — VARCHAR(200), nullable=True
- [ ] Tabla `testimonials` — nueva
- [ ] Tabla `accountant_tenant_access` — nueva
- [ ] Tabla `landing_sections` — nueva

```bash
cd /opt/Erp_core
alembic revision --autogenerate -m "landing_page_models_and_fields"
alembic upgrade head
```

---

## 6. Pendientes (Post-implementación)
- [ ] Seed data: testimonios iniciales, secciones CMS
- [ ] Admin CRUD para testimonios y secciones landing
- [ ] Partner slug auto-generado en admin al crear Partner
- [ ] E2E tests para flujo onboarding con user_count
- [ ] Verificación Stripe webhook con user_count en metadata
- [ ] Meta tags OG / SEO en index.html por ruta
- [ ] Analytics: GTM events en CTAs del landing
- [ ] A11y review de todos los componentes landing
- [ ] Performance: lazy load de componentes below-fold

---

## 7. Equipo
- **Desarrollo:** Jeturing
- **Marketing:** Equipo interno de diseño y contenido

---

**Fin del plan-LP.md — Actualizado con estado de implementación completo.**
