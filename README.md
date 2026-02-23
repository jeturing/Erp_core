# 🏗️ Sajet ERP Core

> **Plataforma SaaS multi-tenant** para operar instancias Odoo con onboarding comercial, facturación, gestión de partners, provisioning de tenants y operaciones de dominios/infraestructura.

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](DEPLOYMENT_NOTES.md)
[![Backend](https://img.shields.io/badge/backend-FastAPI_0.115-009688.svg?logo=fastapi&logoColor=white)](app/)
[![Frontend](https://img.shields.io/badge/frontend-Svelte_5-FF3E00.svg?logo=svelte&logoColor=white)](frontend/)
[![i18n](https://img.shields.io/badge/i18n-EN%2FES-green.svg)](I18N_STATUS_REPORT.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1?logo=postgresql&logoColor=white)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)]()
[![License](https://img.shields.io/badge/license-Propietario-red)]()

**Validado:** 2026-06-14 · **Entorno objetivo:** `/opt/Erp_core` → PCT 160

---

## 🆕 Novedades v2.1.0 — Internacionalización Completa

**Nueva funcionalidad**: Soporte i18n híbrido (svelte-i18n estática + CMS dinámico en BD), auto-detect de idioma, selector de idioma en navbar, testimonios multiidioma, secciones de landing traducibles.

### Características i18n:
- 🌍 **Auto-detect de Idioma** — Detecta `navigator.language` automáticamente, persiste en localStorage
- 🔄 **Selector de Idioma** — Globo terráqueo + toggle EN/ES en NavBar, cambio instantáneo
- 📖 **Diccionarios Estáticos** — 185 keys en en.json/es.json para UI (svelte-i18n)
- 💬 **Testimonios Multiidioma** — Tabla `testimonials` con soporte es/en, CRUD desde admin
- 📰 **Secciones CMS** — Tabla `landing_sections` con unique constraint (section_key, locale)
- 🔤 **Traducciones Editable** — Tabla `translations` para strings dinámicos, workflow de aprobación
- 📡 **API Locale-Aware** — Endpoints públicos filtran por locale: `/api/public/testimonials?locale=es`
- 🏷️ **Meta Tags Dinámicos** — OG tags, canonical, hreflang por idioma (en desarrollo)

**Archivos clave i18n:**
- Frontend: `lib/i18n/{index.ts, en.json, es.json}`, `lib/stores/locale.ts`
- Backend: `models/database.py` (3 nuevos modelos), `routes/public_landing.py` (endpoints mejorados)
- Migración: `alembic/versions/.../013_landing_i18n_internationalization.py`
- Scripts: `scripts/seed_landing_i18n.py`, `scripts/verify_i18n.sh`
- Documentación: [I18N_STATUS_REPORT.md](I18N_STATUS_REPORT.md), [I18N_IMPLEMENTATION_SUMMARY.md](I18N_IMPLEMENTATION_SUMMARY.md)

---

## 🆕 Novedades v2.0.0 — Seguridad & Contratos Digitales

**Nueva funcionalidad**: CORS dinámico desde BD, verificación de email Steam-style, firma digital de NDA/TOS, editor de plantillas admin, plan pricing en onboarding.

### Características principales:
- 🔐 **CORS Dinámico** — Orígenes cargados desde `custom_domains` + `tenant_deployments` con caché 60s y regex fallback
- 📧 **Email Verification (Steam-style)** — Código alfanumérico 6 chars, configurable por rol (obligatorio partner/tenant, toggle admin)
- 📝 **Firma Digital NDA/TOS** — Stripe-style: nombre escrito → cursiva, renderizado a PDF con weasyprint, hash SHA256
- ⚖️ **Acuerdos Editables** — Templates HTML con variables (`{{signer_name}}`, `{{date}}`), CRUD completo desde admin panel
- 💰 **Plan Pricing Cards** — Tarjetas de planes con precios desde BD en customer onboarding
- 👥 **Admin Users Multi-Rol** — CRUD de admins con roles (admin/operator/viewer), login by email, filtros avanzados

**Archivos clave:**
- Backend: `app/security/cors_dynamic.py`, `app/security/email_verify.py`, `app/routes/agreements.py`
- Frontend: `pages/Agreements.svelte`, `components/SignaturePanel.svelte`
- Migración: `alembic/versions/..._012_email_verify_agreements.py`

---

## 📚 Tabla de Contenido

- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Características](#-características)
- [Estructura del Repositorio](#-estructura-del-repositorio)
- [Módulos API Activos](#-módulos-api-activos)
- [i18n — Internacionalización](#-i18n--internacionalización)
- [Requisitos](#-requisitos)
- [Configuración Local](#-configuración-local)
- [Entornos](#-entornos-erp_env)
- [Ejecutar en Desarrollo](#-ejecutar-en-desarrollo)
- [Build, Smoke & Deploy](#-build-smoke--deploy)
- [Testing](#-testing)
- [MCP Local](#-mcp-local)
- [Documentación](#-documentación)
- [Regla de Mantenimiento](#-regla-de-mantenimiento-documental)

---

## 🔧 Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | FastAPI 0.115 + SQLAlchemy + PostgreSQL 16 |
| **Frontend** | Svelte 5 (runes mode) + TypeScript + Vite 7 + Tailwind CSS 3 |
| **i18n** | svelte-i18n 3.x (static dicts) + Backend Translation CMS (dynamic) |
| **Autenticación** | JWT (cookies httpOnly) + TOTP 2FA + Email Verify + Roles granulares |
| **Pagos** | Stripe (Direct + Connect Express) |
| **Infraestructura** | Proxmox LXC + Cloudflare Tunnels + Nginx |
| **Seguridad** | Dynamic CORS + WAF Middleware + Rate Limiting + Audit Logging |
| **Contratos** | NDA/TOS digitales + weasyprint PDF + Firma cursiva |
| **Migraciones** | Alembic (13 versiones) |
| **Email** | SMTP ipzmarketing (SSL/TLS :465) |

---

## 🏛️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     Cloudflare Edge                         │
│              (DNS + Tunnels + SSL + WAF)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    PCT 160 (Gateway)                        │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │  FastAPI      │  │  SPA Svelte   │  │  PostgreSQL      │ │
│  │  (uvicorn)    │  │  (static)     │  │  erp_core_db     │ │
│  │  :4443        │  │  /static/spa  │  │  :5432           │ │
│  └──────┬───────┘  └───────────────┘  └──────────────────┘ │
│         │                                                   │
│  ┌──────▼───────────────────────────────────────────┐      │
│  │  Security Layer                                   │      │
│  │  • DynamicCORSMiddleware (DB-backed origins)      │      │
│  │  • JWT httpOnly cookies + refresh rotation        │      │
│  │  • TOTP 2FA + Steam email verify                  │      │
│  │  • Rate limiting + WAF + Audit logger             │      │
│  └──────────────────────────────────────────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │ Proxmox API + SSH
┌──────────────────────▼──────────────────────────────────────┐
│               Nodos Odoo (LXC Containers)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Tenant A │  │ Tenant B │  │ Tenant C │  ...             │
│  │ :8069    │  │ :8069    │  │ :8069    │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Características

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| 🔐 **Auth Multi-layer** | Password → TOTP → Email Verify (configurable por rol) | ✅ |
| � **i18n Multiidioma** | Auto-detect ES/EN, selector en navbar, testimonios + CMS traducibles | ✅ |
| �🌐 **CORS Dinámico** | Orígenes desde BD con caché TTL + regex fallback | ✅ |
| 📝 **Firma Digital** | NDA/TOS Stripe-style → PDF weasyprint + hash SHA256 | ✅ |
| ⚖️ **Templates Admin** | Editor HTML de acuerdos con variables, CRUD completo | ✅ |
| 👥 **Admin Users** | Multi-admin con roles (admin/operator/viewer) | ✅ |
| 🏢 **Multi-tenant** | Provisioning LXC, dominios, tunnels, Odoo per-tenant | ✅ |
| 💳 **Stripe Connect** | Split 50/50 automático, onboarding KYC partners | ✅ |
| 📊 **Dashboard** | KPIs, revenue, cluster health, alertas | ✅ |
| 🤝 **Partner Ecosystem** | Leads, comisiones, liquidaciones, branding, cotizaciones | ✅ |
| 🇩🇴 **e-CF (DGII)** | Facturación electrónica RD integrada en onboarding | ✅ |
| 📦 **Blueprints** | Paquetes de módulos Odoo + work orders | ✅ |
| 💰 **Plan Pricing** | Planes con precios dinámicos en customer onboarding | ✅ |
| 📧 **Communications** | SMTP + email logs + templates | ✅ |
| 🔍 **Audit Trail** | Logging completo de login, TOTP, CRUD, tokens | ✅ |
| 📄 **Invoicing** | Facturas, reconciliación Stripe, seat-based billing | ✅ |

---

## 📁 Estructura del Repositorio

```
Erp_core/
├── app/                     # Backend FastAPI
│   ├── main.py              # Entry point — 35+ routers
│   ├── config.py            # Configuración centralizada (env vars)
│   ├── models/
│   │   └── database.py      # SQLAlchemy ORM (50+ models + enums)
│   ├── routes/              # Endpoints API (1 archivo por dominio)
│   │   ├── secure_auth.py   # Login: password → TOTP → email verify
│   │   ├── agreements.py    # NDA/TOS templates + signing + PDF
│   │   ├── admin_users.py   # Admin CRUD multi-rol
│   │   └── ...              # 30+ más
│   ├── security/
│   │   ├── cors_dynamic.py  # CORS desde BD (caché 60s)
│   │   ├── email_verify.py  # Steam-style email tokens
│   │   ├── tokens.py        # JWT access + refresh rotation
│   │   ├── totp.py          # TOTP 2FA (QR + backup codes)
│   │   ├── audit.py         # Event logging
│   │   └── middleware.py    # WAF + Rate limiting
│   └── services/            # Email, Stripe, provisioning
├── frontend/                # SPA Svelte 5
│   ├── src/
│   │   ├── App.svelte       # Router hash-based (30+ pages)
│   │   ├── pages/           # Admin pages
│   │   │   ├── Agreements.svelte    # Template editor + signed list
│   │   │   ├── AdminUsers.svelte    # Admin CRUD con filtros
│   │   │   └── ...
│   │   ├── routes/
│   │   │   └── Login.svelte # 3-step: password → TOTP → email verify
│   │   └── lib/
│   │       ├── api/         # API clients tipados (25+ modules)
│   │       ├── components/
│   │       │   ├── SignaturePanel.svelte  # Firma cursiva Stripe-style
│   │       │   ├── PartnerOnboarding.svelte # 5-step wizard con NDA
│   │       │   └── ...
│   │       ├── stores/      # Auth, dashboard, domains, toast
│   │       └── types/       # TypeScript interfaces (500+ lines)
│   └── dist/                # Build output → /static/spa/
├── alembic/versions/        # 12 migraciones versionadas
├── data/agreements/         # PDFs firmados (generados por weasyprint)
├── docs/                    # Documentación funcional y operativa
├── scripts/                 # Build, deploy, smoke tests
├── tests/                   # pytest + smoke scripts
└── mcp/                     # MCP server local
```

---

## 🔌 Módulos API Activos

35+ routers registrados en `app/main.py`:

<details>
<summary><strong>Expandir lista completa</strong></summary>

| Grupo | Routers |
|-------|---------|
| **Auth & Seguridad** | `secure_auth` · `auth` · `roles` · `admin_users` |
| **Dashboard & Sistema** | `dashboard` · `settings` · `logs` · `audit` · `reports` |
| **Tenants & Provisioning** | `tenants` · `tenant_portal` · `customer_onboarding` · `onboarding_config` · `onboarding` · `provisioning` · `suspension` |
| **Infraestructura** | `nodes` · `tunnels` · `domains` |
| **Facturación** | `billing` · `plans` · `customers` · `invoices` · `reconciliation` · `seats` · `quotas` |
| **Partners & Comercial** | `partners` · `partner_portal` · `leads` · `commissions` · `settlements` · `stripe_connect` · `branding` |
| **Operaciones** | `blueprints` · `work_orders` · `quotations` · `communications` |
| **Contratos** | `agreements` (templates + signing + PDF) |
| **Seguridad Avanzada** | `cors_dynamic` (middleware) · `email_verify` (module) |

</details>

---

## 🔐 Flujo de Autenticación

```
┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────┐
│ Password │ →  │  TOTP    │ →  │ Email Verify │ →  │  Token   │
│  Check   │    │ (si 2FA) │    │ (Steam code) │    │  Issue   │
└──────────┘    └──────────┘    └──────────────┘    └──────────┘
                                       │
                    ┌──────────────────────────────────┐
                    │ Configurable por rol:             │
                    │ • partner/tenant → siempre        │
                    │ • admin → toggle require_email_   │
                    │   verify en admin_users           │
                    └──────────────────────────────────┘
```

---

## 📌 Requisitos

| Requisito | Versión mínima |
|-----------|---------------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | 10+ |
| PostgreSQL | 16+ |
| weasyprint | Última (para PDF de acuerdos) |
| `rsync` + `ssh` | Para deploy remoto |

---

## ⚙️ Configuración Local

```bash
cd /opt/Erp_core

# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm ci && cd ..

# Variables de entorno
cp .env.example .env

# Migrar BD
alembic upgrade head
```

---

## 🌍 Entornos (`ERP_ENV`)

| Valor | Archivo | Uso |
|-------|---------|-----|
| `development` | `.env` | Desarrollo local |
| `test` | `.env.test` | Suite de tests |
| `production` | `.env.production` | Servidor PCT160 |

```bash
export ERP_ENV=development
```

---

## 🚀 Ejecutar en Desarrollo

**Terminal 1 — API:**

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload
```

**Terminal 2 — SPA:**

```bash
cd frontend && npm run dev
```

### Rutas útiles

| Ruta | URL |
|------|-----|
| API Health | `http://localhost:4443/health` |
| Frontend Dev | `http://localhost:5173` |
| OpenAPI | `http://localhost:4443/sajet-api-docs` |
| CORS Refresh | `POST /api/admin/cors/refresh` |

### Curl de ejemplo

```bash
# Login
curl -X POST http://localhost:4443/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin","password":"pass"}' -c cookies.txt

# Get required agreements for partner
curl http://localhost:4443/api/agreements/required/partner -b cookies.txt

# Refresh CORS cache
curl -X POST http://localhost:4443/api/admin/cors/refresh -b cookies.txt
```

---

## 📦 Build, Smoke & Deploy

```bash
# Build SPA → static/spa/
./scripts/build_static.sh

# Smoke test
APP_BASE_URL=http://127.0.0.1:4443 ./scripts/smoke_pct160.sh

# Deploy remoto (PCT160)
./scripts/deploy_to_server.sh --profile pct160
```

| Flag | Descripción |
|------|-------------|
| `--dry-run` | Simular sin ejecutar |
| `--skip-build` | Omitir build local |

---

## 🧪 Testing

```bash
source .venv/bin/activate
pytest -q
bash tests/test_jwt.sh
```

---

## 🤖 MCP Local

```bash
node mcp/api-server.js
```

Config: `mcp_config.json`

---

## 📚 Documentación

**Índice maestro:** [`docs/INDICE.md`](docs/INDICE.md)

| Área | Ruta |
|------|------|
| Arquitectura base | `docs/00-base/ARQUITECTURA_OPERATIVA_MAESTRA.md` |
| Frontend | `docs/01-frontend/` |
| Seguridad / Auth | `docs/02-security-auth/` |
| Tenants / Provisioning | `docs/03-tenants-provisioning/` |
| Dominios / Cloudflare | `docs/04-domains-cloudflare/` |
| Deploy / Operación | `docs/05-deploy-operacion/` |
| Migración Odoo | `docs/06-migracion-odoo/` |
| Flujos funcionales | `docs/flujos/` |

---

## 🔄 Regla de Mantenimiento Documental

Toda actualización funcional o técnica debe reflejarse en:

1. **`README.md`** — si afecta operación general
2. **`docs/INDICE.md`** — si agrega/mueve documentos
3. **Documentos de dominio** (`docs/0x-*`) — según el área impactada

---

<div align="center">

**Desarrollado por [Jeturing Inc ](https://jeturing.com)** · Licencia Propietaria · v2.0.0

</div>
