# 🏗️ Sajet ERP Core

> **Plataforma SaaS multi-tenant** para operar instancias Odoo con onboarding comercial, facturación, gestión de partners, provisioning de tenants y operaciones de dominios/infraestructura.

[![Estado](https://img.shields.io/badge/estado-vigente-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)]()
[![Svelte](https://img.shields.io/badge/Svelte_5-TypeScript-FF3E00?logo=svelte&logoColor=white)]()
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1?logo=postgresql&logoColor=white)]()
[![License](https://img.shields.io/badge/license-Propietario-red)]()

**Validado:** 2026-02-22 · **Entorno objetivo:** `/opt/Erp_core` (desarrollo local + despliegue PCT160)

---

## �� Tabla de Contenido

- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Estructura del Repositorio](#-estructura-del-repositorio)
- [Módulos API Activos](#-módulos-api-activos)
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
| **Backend** | FastAPI + SQLAlchemy + PostgreSQL |
| **Frontend** | Svelte 5 + TypeScript + Vite + Tailwind CSS |
| **Autenticación** | JWT (cookies httpOnly) + TOTP 2FA + roles granulares |
| **Pagos** | Stripe (Direct + Connect Express) |
| **Infraestructura** | Proxmox LXC + Cloudflare Tunnels + Nginx |
| **Seguridad** | Middleware WAF + Basic Auth OpenAPI + Rate Limiting |
| **Migraciones** | Alembic (versionadas) |

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
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
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

## 📁 Estructura del Repositorio

```
Erp_core/
├── app/                     # Backend FastAPI
│   ├── main.py              # Entry point — registra 35+ routers
│   ├── config.py            # Configuración centralizada (env vars)
│   ├── models/
│   │   └── database.py      # SQLAlchemy ORM models + enums
│   ├── routes/              # Endpoints API (1 archivo por dominio)
│   ├── security/            # JWT, WAF, rate limiting, TOTP, audit
│   └── services/            # Email, Stripe, provisioning
├── frontend/                # SPA Svelte 5
│   ├── src/
│   │   ├── App.svelte       # Router principal (hash-based)
│   │   ├── pages/           # Páginas admin (30+)
│   │   ├── routes/          # Landing, Login, Portales
│   │   └── lib/
│   │       ├── api/         # API clients tipados
│   │       ├── components/  # Layout, Toast, Spinner, etc.
│   │       ├── stores/      # Auth, dashboard, domains
│   │       └── types/       # TypeScript interfaces
│   └── dist/                # Build output → deploy a /static/spa/
├── alembic/                 # Migraciones de BD
│   └── versions/            # 000-011 migrations
├── docs/                    # Documentación funcional y operativa
├── scripts/                 # Build, deploy, smoke tests
├── tests/                   # Suite pytest + scripts de smoke
├── mcp/                     # MCP server local para consultar API
├── nodo/                    # Paquete operativo para nodos Odoo
└── static/                  # Assets estáticos servidos por FastAPI
```

---

## 🔌 Módulos API Activos

35+ routers registrados en `app/main.py`:

<details>
<summary><strong>Expandir lista completa</strong></summary>

| Grupo | Routers |
|-------|---------|
| **Auth & Seguridad** | `auth` · `secure_auth` · `roles` |
| **Dashboard & Sistema** | `dashboard` · `settings` · `logs` · `audit` · `reports` |
| **Tenants & Provisioning** | `tenants` · `tenant_portal` · `customer_onboarding` · `onboarding_config` · `onboarding` · `provisioning` · `suspension` |
| **Infraestructura** | `nodes` · `tunnels` · `domains` |
| **Facturación** | `billing` · `plans` · `customers` · `invoices` · `reconciliation` · `seats` · `quotas` |
| **Partners & Comercial** | `partners` · `partner_portal` · `leads` · `commissions` · `settlements` · `stripe_connect` · `branding` |
| **Operaciones** | `blueprints` · `work_orders` · `quotations` · `communications` |
| **Administración** | `admin_users` |

</details>

---

## 📌 Requisitos

| Requisito | Versión mínima |
|-----------|---------------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | 10+ |
| PostgreSQL | 16+ |
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
cd frontend
npm ci
cd ..

# Variables de entorno
cp .env.example .env
```

---

## 🌍 Entornos (`ERP_ENV`)

`app/config.py` selecciona el archivo de entorno según `ERP_ENV`:

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
cd /opt/Erp_core
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload
```

**Terminal 2 — SPA:**

```bash
cd /opt/Erp_core/frontend
npm run dev
```

### Rutas útiles

| Ruta | URL |
|------|-----|
| API Health | `http://localhost:4443/health` |
| API Env | `http://localhost:4443/api/env` |
| Frontend Dev | `http://localhost:5173` |
| OpenAPI (protegida) | `http://localhost:4443/sajet-api-docs` |

---

## 📦 Build, Smoke & Deploy

```bash
# Build SPA → static/spa/
./scripts/build_static.sh

# Smoke test local/remoto
APP_BASE_URL=http://127.0.0.1:4443 ./scripts/smoke_pct160.sh

# Deploy remoto (perfil PCT160)
./scripts/deploy_to_server.sh --profile pct160
```

**Opciones:**

| Flag | Descripción |
|------|-------------|
| `--dry-run` | Simular sin ejecutar |
| `--skip-build` | Omitir build local |

---

## 🧪 Testing

```bash
cd /opt/Erp_core
source .venv/bin/activate
pytest -q
```

**Test JWT shell:**

```bash
bash tests/test_jwt.sh
```

---

## 🤖 MCP Local

Servidor MCP del proyecto para consultar la API desde herramientas de IA:

- **Implementación:** `mcp/api-server.js`
- **Config:** `mcp_config.json`

```bash
node mcp/api-server.js
```

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

Toda actualización funcional o técnica debe reflejarse en el mismo cambio en:

1. **`README.md`** — si afecta operación general
2. **`docs/INDICE.md`** — si agrega/mueve documentos
3. **Documentos de dominio** (`docs/0x-*`) — según el área impactada

---

<div align="center">

**Desarrollado por [Jeturing SRL](https://jeturing.com)** · Licencia Propietaria

</div>
