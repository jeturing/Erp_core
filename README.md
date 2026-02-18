<div align="center">

# 🏢 Jeturing ERP Core

**Plataforma SaaS multi-tenant para gestión de instancias Odoo**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Svelte](https://img.shields.io/badge/Svelte-5.45-FF3E00?style=flat-square&logo=svelte&logoColor=white)](https://svelte.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-Proprietary-003B73?style=flat-square)]()

---

Onboarding automático · Provisioning Odoo · Billing con Stripe · Infraestructura Proxmox · Cloudflare Tunnels

</div>

---

## 📋 Descripción

ERP Core es el motor SaaS de **Jeturing** que automatiza el ciclo completo de un tenant Odoo: desde el registro público con pago via Stripe, hasta el provisioning de contenedores LXC en Proxmox, configuración de DNS/tunnels en Cloudflare, y administración centralizada via dashboard.

### Características principales

- 🔐 **Autenticación JWT + TOTP 2FA** — Login seguro con tokens rotativos y segundo factor
- 🏗️ **Provisioning automático** — Creación de instancias Odoo en contenedores LXC
- 💳 **Billing integrado** — Stripe checkout, webhooks, MRR tracking
- 🌐 **Dominios personalizados** — DNS automation con Cloudflare + Nginx reverse proxy
- 📊 **Dashboard en tiempo real** — Métricas de cluster, tenants, revenue
- 🛡️ **WAF + Security middleware** — Protección contra SQLi, XSS, rate limiting
- 🖥️ **Multi-nodo Proxmox** — Gestión de cluster con balanceo de carga

---

## 🏗️ Arquitectura

```
                    ┌─────────────────────────────────────────────┐
                    │              Cliente (Browser)               │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │           Cloudflare Tunnel                  │
                    │         *.sajet.us / custom domains          │
                    └──────────────────┬──────────────────────────┘
                                       │
         ┌─────────────────────────────▼─────────────────────────────┐
         │                    FastAPI (Port 4443)                     │
         │  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
         │  │  Auth/JWT  │  │ Tenants  │  │ Billing  │  │  Nodes  │ │
         │  │  + TOTP    │  │  CRUD    │  │ Stripe   │  │ Proxmox │ │
         │  └───────────┘  └──────────┘  └──────────┘  └─────────┘ │
         │  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
         │  │  Domains   │  │ Tunnels  │  │Settings  │  │  Logs   │ │
         │  │ CF + Nginx │  │Cloudflare│  │  Admin   │  │ System  │ │
         │  └───────────┘  └──────────┘  └──────────┘  └─────────┘ │
         │  ┌─────────────────────────────────────────────────────┐ │
         │  │           SPA Shell (static/spa/)                    │ │
         │  │              Svelte 5 + Vite 7                       │ │
         │  └─────────────────────────────────────────────────────┘ │
         └───────────┬─────────────────┬─────────────────┬─────────┘
                     │                 │                 │
         ┌───────────▼───┐  ┌─────────▼─────┐  ┌───────▼──────────┐
         │  PostgreSQL   │  │   Proxmox VE   │  │  Cloudflare API  │
         │  erp_core_db  │  │  LXC Containers│  │  DNS + Tunnels   │
         └───────────────┘  └────────────────┘  └──────────────────┘
```

---

## 📁 Estructura del proyecto

```
Erp_core/
├── app/                          # 🐍 Backend FastAPI
│   ├── main.py                   # Entry point de la aplicación
│   ├── models/
│   │   └── database.py           # SQLAlchemy models (9 tablas)
│   ├── routes/                   # Endpoints API (14 routers)
│   │   ├── auth.py               # Auth legacy (backward compat)
│   │   ├── secure_auth.py        # Auth JWT + TOTP 2FA
│   │   ├── billing.py            # Métricas de facturación
│   │   ├── dashboard.py          # Dashboard + SPA shell views
│   │   ├── domains.py            # Gestión de dominios custom
│   │   ├── logs.py               # Logs del sistema
│   │   ├── nodes.py              # Nodos Proxmox multi-cluster
│   │   ├── onboarding.py         # Registro público + Stripe checkout
│   │   ├── provisioning.py       # Auto-provisioning tenants Odoo
│   │   ├── roles.py              # Roles y permisos
│   │   ├── settings.py           # Configuración administrable
│   │   ├── tenant_portal.py      # Portal self-service tenant
│   │   ├── tenants.py            # CRUD de tenants
│   │   └── tunnels.py            # Cloudflare tunnels
│   ├── services/                 # Lógica de negocio
│   │   ├── cloudflare_manager.py # API Cloudflare (DNS, tunnels)
│   │   ├── domain_manager.py     # Orquestación de dominios
│   │   ├── nginx_domain_configurator.py
│   │   ├── odoo_database_manager.py
│   │   ├── odoo_provisioner.py   # Provisioning Odoo en LXC
│   │   ├── proxmox_manager.py    # API Proxmox VE
│   │   ├── resource_monitor.py   # Métricas de recursos
│   │   └── spa_shell.py          # SPA shell renderer
│   └── security/                 # Seguridad
│       ├── audit.py              # Audit logging
│       ├── middleware.py          # WAF + HTTPS enforcement
│       ├── tokens.py             # JWT token management
│       └── totp.py               # TOTP 2FA
│
├── frontend/                     # ⚡ Frontend Svelte 5 SPA
│   ├── src/
│   │   ├── App.svelte            # Router principal (hash-based)
│   │   ├── main.ts               # Entry point
│   │   ├── lib/
│   │   │   ├── api/              # Clientes API tipados (12 módulos)
│   │   │   ├── components/       # UI components (13 componentes)
│   │   │   ├── stores/           # Estado reactivo (5 stores)
│   │   │   ├── types/            # TypeScript interfaces
│   │   │   └── utils/            # Formatters, helpers
│   │   ├── pages/                # Páginas admin (8)
│   │   └── routes/               # Rutas principales (4)
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.app.json
│
├── scripts/                      # 🔧 Scripts operativos (28)
├── tests/                        # 🧪 Tests (12 archivos)
├── docs/                         # 📚 Documentación (61 archivos)
├── Cloudflare/                   # ☁️ Scripts Cloudflare
├── nodo/                         # 🖥️ Config nodo Proxmox
├── migration_reports/            # 📊 Reportes migración V17→V19
├── static/                       # Assets estáticos + SPA build
├── logs/                         # Logs de aplicación
└── mcp/                          # MCP server config
```

---

## 🚀 Quick Start

### Requisitos

- Python 3.11+
- Node.js 20+
- PostgreSQL 16
- Git

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/jeturing/Erp_core.git
cd Erp_core

# Backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Connection string PostgreSQL |
| `STRIPE_SECRET_KEY` | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `CLOUDFLARE_API_TOKEN` | Token API Cloudflare |
| `CLOUDFLARE_ZONE_ID` | Zone ID del dominio |
| `APP_PORT` | Puerto de la aplicación (default: `4443`) |
| `LOG_LEVEL` | Nivel de logging (`INFO`, `DEBUG`) |
| `ENVIRONMENT` | `development` \| `production` |
| `FORCE_HTTPS` | Forzar HTTPS (`true`/`false`) |
| `ENABLE_WAF` | Activar WAF middleware (`true`/`false`) |

### Desarrollo

```bash
# Terminal 1 — Backend (auto-reload)
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload

# Terminal 2 — Frontend (hot-reload + proxy a backend)
cd frontend
npm run dev
# → http://localhost:5173
```

### Build y deploy

```bash
# Build SPA + copiar a static/spa/
./scripts/build_static.sh

# Deploy a servidor producción (PCT160)
./scripts/deploy_to_server.sh --profile pct160

# Smoke tests post-deploy
./scripts/smoke_pct160.sh
```

---

## 🗄️ Base de datos

### Esquema (9 tablas)

| Tabla | Descripción |
|-------|-------------|
| `customers` | Datos de clientes (email, empresa, subdominio, Stripe ID) |
| `subscriptions` | Planes y suscripciones (status, MRR, Stripe sub ID) |
| `stripe_events` | Webhooks de Stripe (event_id, type, payload) |
| `proxmox_nodes` | Nodos del cluster (hostname, CPU, RAM, disco) |
| `lxc_containers` | Contenedores LXC (vmid, IP, recursos asignados) |
| `tenant_deployments` | Deployments activos (subdominio, tunnel, status) |
| `custom_domains` | Dominios personalizados (DNS, SSL, Nginx config) |
| `resource_metrics` | Métricas históricas (CPU, RAM, disco, red) |
| `system_config` | Configuración del sistema (key-value, secretos) |

---

## 🔌 API Reference

### Autenticación (`/api/auth`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login con JWT + optional TOTP |
| `POST` | `/api/auth/logout` | Cerrar sesión |
| `POST` | `/api/auth/refresh` | Renovar token |
| `GET` | `/api/auth/me` | Perfil del usuario autenticado |
| `POST` | `/api/auth/2fa/setup` | Configurar TOTP 2FA |
| `POST` | `/api/auth/2fa/verify` | Verificar código TOTP |

### Dashboard (`/api/dashboard`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/dashboard/metrics` | Métricas principales (tenants, MRR, cluster) |
| `GET` | `/api/dashboard/all` | Endpoint consolidado |

### Tenants (`/api/tenants`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/tenants` | Listar tenants con paginación |
| `POST` | `/api/tenants` | Crear nuevo tenant |
| `GET` | `/api/tenants/{subdomain}` | Detalle de tenant |
| `DELETE` | `/api/tenants/{subdomain}` | Eliminar tenant + cleanup |
| `GET` | `/api/tenants/servers` | Servidores Odoo disponibles |

#### Flujo de creación de tenant (template en PCT105)

```text
[Usuario en browser]
            |
            | Click en "NUEVO TENANT"
            v
[Frontend SPA en 10.10.10.20]
    frontend/src/pages/Tenants.svelte
            |
            | tenantsApi.create(payload)
            | POST /api/tenants
            v
[FastAPI en 10.10.10.20]
    app/routes/tenants.py -> create_tenant()
            |
            | use_fast_method=true
            v
[Odoo DB Manager]
    app/services/odoo_database_manager.py
    create_tenant_from_template()
            |
            | 1) valida subdomain
            | 2) verifica BD destino no exista
            | 3) verifica template_tenant exista
            | 4) CREATE DATABASE <subdomain> WITH TEMPLATE <template_tenant>
            | 5) post-config (web.base.url, company_name, database.uuid)
            v
[PCT105: PostgreSQL/Odoo]
    Se crea la nueva BD del tenant
            |
            v
[FastAPI en 10.10.10.20]
    Registra customer/subscription en BD local
    Responde success al frontend
            |
            v
[Frontend SPA]
    Toast "Tenant creado"
    Refresca listado con GET /api/tenants
```

Notas operativas:
- Si Odoo no devuelve bases de datos en `/web/database/list`, el backend usa fallback directo a PostgreSQL y fallback local de `customers/subscriptions` para no dejar la vista vacía.
- El template por defecto en provisioning está configurado como `template_tenant`.

### Billing (`/api/billing`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/billing/metrics` | MRR, revenue, churn rate |
| `GET` | `/api/billing/invoices` | Facturas desde Stripe |
| `GET` | `/api/billing/stripe-events` | Eventos de webhook |

### Dominios (`/api/domains`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/domains` | Listar dominios custom |
| `POST` | `/api/domains` | Registrar nuevo dominio |
| `POST` | `/api/domains/{id}/activate` | Activar dominio |
| `POST` | `/api/domains/{id}/verify` | Verificar DNS |
| `POST` | `/api/domains/{id}/configure-cloudflare` | Config Cloudflare |
| `POST` | `/api/domains/{id}/configure-nginx` | Config Nginx |

### Infraestructura (`/api/nodes`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/api/nodes` | Listar nodos Proxmox |
| `GET` | `/api/nodes/status` | Estado del cluster |
| `GET` | `/api/nodes/metrics/summary` | Resumen de métricas |
| `GET` | `/api/nodes/containers/all` | Todos los contenedores |
| `POST` | `/api/nodes/provision` | Provisionar nuevo contenedor |

### Portal Tenant (`/tenant`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/tenant/api/info` | Info del tenant autenticado |
| `GET` | `/tenant/api/billing` | Facturación del tenant |
| `POST` | `/tenant/api/update-payment` | Actualizar método de pago |
| `POST` | `/tenant/api/cancel-subscription` | Cancelar suscripción |

> 📖 Documentación interactiva disponible en `/docs` (Swagger UI) en entorno development.

---

## 🖥️ Frontend SPA

### Rutas (hash-based)

| Ruta | Página | Descripción |
|------|--------|-------------|
| `#/dashboard` | Dashboard | Métricas principales y gráficos |
| `#/tenants` | Tenants | Gestión de clientes/instancias |
| `#/domains` | Dominios | Dominios custom con verificación |
| `#/infrastructure` | Infra | Nodos Proxmox, contenedores |
| `#/billing` | Billing | Revenue, facturas, eventos Stripe |
| `#/settings` | Settings | Configuración del sistema |
| `#/login` | Login | Autenticación admin/tenant |
| `#/portal` | Portal | Self-service para tenants |

### Stack frontend

| Tecnología | Versión | Uso |
|------------|---------|-----|
| Svelte | 5.45 | Framework UI reactivo |
| Vite | 7.3 | Build tool + dev server |
| TypeScript | 5.9 | Type safety |
| Tailwind CSS | 3.4 | Utility-first styling |

### Componentes UI

13 componentes reutilizables: `Badge`, `Button`, `Card`, `DataTable`, `Icon`, `Input`, `Layout`, `Modal`, `Spinner`, `StatCard`, `Toast` (estilo Sileo con SVG gooey morphing), e `index` barrel export.

---

## 🔒 Seguridad

| Feature | Implementación |
|---------|---------------|
| **Autenticación** | JWT con refresh tokens rotativos |
| **2FA** | TOTP (Google Authenticator compatible) |
| **WAF** | Middleware anti-SQLi, XSS, path traversal |
| **HTTPS** | Enforcement configurable por entorno |
| **Audit** | Logging de acciones críticas |
| **Rate Limiting** | Por IP y por usuario |
| **CORS** | Whitelist de orígenes permitidos |

---

## 🧪 Tests

```bash
# Ejecutar todos los tests
source venv/bin/activate
pytest tests/ -v

# Con coverage
pytest tests/ --cov=app --cov-report=html
```

Cobertura de tests: `auth`, `dashboard`, `health`, `nodes`, `onboarding`, `tenants`, `tenant_portal`, `tunnels`.

---

## 📚 Documentación

Toda la documentación está en [`docs/`](docs/) (61 archivos). Índice maestro: [`docs/INDICE.md`](docs/INDICE.md)

**Documentos clave:**

| Documento | Contenido |
|-----------|-----------|
| [`DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Guía de deployment producción |
| [`SECURITY.md`](docs/SECURITY.md) | Arquitectura de seguridad |
| [`JWT_QUICKSTART.md`](docs/JWT_QUICKSTART.md) | Setup rápido JWT |
| [`CLOUDFLARE_INTEGRATION.md`](docs/CLOUDFLARE_INTEGRATION.md) | Integración Cloudflare |
| [`CUSTOM_DOMAINS_ARCHITECTURE.md`](docs/CUSTOM_DOMAINS_ARCHITECTURE.md) | Arquitectura de dominios custom |
| [`MODULAR_ARCHITECTURE.md`](docs/MODULAR_ARCHITECTURE.md) | Arquitectura modular del sistema |
| [`ROLES_PERMISOS_MATRIZ.md`](docs/ROLES_PERMISOS_MATRIZ.md) | Matriz de roles y permisos |

---

## 🛠️ Scripts operativos

| Script | Descripción |
|--------|-------------|
| `build_static.sh` | Build SPA + publicar en `static/spa/` |
| `deploy_to_server.sh` | Deploy a servidor producción |
| `smoke_pct160.sh` | Smoke tests post-deploy |
| `create_tenant.sh` | Crear tenant manualmente |
| `delete_tenant.sh` | Eliminar tenant + cleanup |
| `domain_sync.sh` | Sincronizar dominios con Cloudflare |
| `install_odoo19.sh` | Instalar Odoo 19 en nodo |

---

## 🎨 Brand

| | Color | Hex | Uso |
|-|-------|-----|-----|
| 🔵 | Deep Blue | `#003B73` | Primary — headers, botones, links |
| ⚫ | Surface Dark | `#0F1419` | Background dashboard |
| 🟢 | Electric Green | `#00FF9F` | Accent — success, CTAs |
| ⚪ | White | `#FFFFFF` | Texto sobre dark |
| 🟣 | Purple | `#8F00FF` | Innovation badges (uso limitado) |

**Tipografía:** Inter (UI) · JetBrains Mono (código/datos técnicos)

---

<div align="center">

**[Documentación](docs/INDICE.md)** · **[API Docs](http://localhost:4443/docs)** · **[Changelog](https://github.com/jeturing/Erp_core/commits/main)**

© 2026 Jeturing · All rights reserved

</div>
