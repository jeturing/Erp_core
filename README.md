# Sajet ERP Core

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core` (desarrollo local + despliegue PCT160)
Auditoria documental: 2026-02-22 (enlaces Markdown internos verificados)

Plataforma SaaS multi-tenant para operar instancias Odoo con onboarding comercial, facturacion, gestion de partners, provisioning de tenants y operaciones de dominios/infraestructura.

## Resumen rapido

- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: Svelte 5 + TypeScript + Vite + Tailwind
- API activa: `app/main.py` registra 35 routers (`app/routes/*.py`)
- Seguridad: JWT con cookies, TOTP 2FA, middleware WAF, proteccion Basic Auth para OpenAPI
- Operacion: scripts para build SPA, smoke tests y despliegue remoto

## Estructura del repositorio

```text
Erp_core/
├── app/                    # Backend FastAPI (rutas, servicios, seguridad, modelos)
├── frontend/               # SPA Svelte (admin, partner, tenant)
├── docs/                   # Documentacion funcional y operativa
├── scripts/                # Utilidades de build/deploy/migracion/provisioning
├── tests/                  # Suite pytest + scripts de smoke
├── mcp/                    # MCP server local para consultar API
├── migration_reports/      # Reportes de migracion Odoo
└── nodo/                   # Paquete operativo para nodos Odoo/provisioning remoto
```

## Modulos API activos

Routers registrados en `app/main.py`:

- `auth`, `secure_auth`, `roles`
- `dashboard`, `settings`, `logs`, `reports`, `audit`
- `tenants`, `tenant_portal`, `customer_onboarding`, `onboarding_config`, `onboarding`
- `provisioning`, `nodes`, `tunnels`, `domains`
- `billing`, `plans`, `customers`, `invoices`, `reconciliation`
- `partners`, `partner_portal`, `leads`, `commissions`, `settlements`, `stripe_connect`, `branding`
- `blueprints`, `seats`, `quotations`, `quotas`, `work_orders`, `suspension`

## Requisitos

- Python 3.11+
- Node.js 20+
- npm 10+
- PostgreSQL 16+
- `rsync` + `ssh` (si haras deploy remoto)

## Configuracion local

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

## Entornos (`ERP_ENV`)

`app/config.py` selecciona el archivo de entorno segun `ERP_ENV`:

- `development` -> `.env`
- `test` -> `.env.test`
- `production` -> `.env.production`

Ejemplo:

```bash
export ERP_ENV=development
```

## Ejecutar en desarrollo

Terminal 1 (API):

```bash
cd /opt/Erp_core
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload
```

Terminal 2 (SPA):

```bash
cd /opt/Erp_core/frontend
npm run dev
```

Rutas utiles:

- API health: `http://localhost:4443/health`
- API env: `http://localhost:4443/api/env`
- Frontend dev: `http://localhost:5173`
- OpenAPI protegida: `http://localhost:4443/sajet-api-docs`

## Build, smoke y deploy

Build SPA y publicacion a `static/spa/`:

```bash
./scripts/build_static.sh
```

Smoke test local/remoto:

```bash
APP_BASE_URL=http://127.0.0.1:4443 ./scripts/smoke_pct160.sh
```

Deploy remoto (perfil PCT160):

```bash
./scripts/deploy_to_server.sh --profile pct160
```

Opciones frecuentes:

- `--dry-run` para simular
- `--skip-build` para omitir build local

## Testing

```bash
cd /opt/Erp_core
source .venv/bin/activate
pytest -q
```

Prueba shell JWT:

```bash
bash tests/test_jwt.sh
```

## MCP local

Servidor MCP del proyecto:

- Implementacion: `mcp/api-server.js`
- Config de servidores: `mcp_config.json`

Ejecucion manual (si instalas dependencias MCP en el entorno):

```bash
node mcp/api-server.js
```

## Documentacion

Indice maestro: `docs/INDICE.md`

Accesos directos:

- Arquitectura base: `docs/00-base/ARQUITECTURA_OPERATIVA_MAESTRA.md`
- Frontend: `docs/01-frontend/`
- Seguridad/Auth: `docs/02-security-auth/`
- Tenants/Provisioning: `docs/03-tenants-provisioning/`
- Dominios/Cloudflare: `docs/04-domains-cloudflare/`
- Deploy/Operacion: `docs/05-deploy-operacion/`
- Migracion Odoo: `docs/06-migracion-odoo/`
- Flujos funcionales: `docs/flujos/`

## Regla de mantenimiento documental

Toda actualizacion funcional o tecnica debe reflejarse en el mismo cambio en:

1. `README.md` (si afecta operacion general)
2. `docs/INDICE.md` (si agrega/mueve documentos)
3. Documentos de dominio impactado (`docs/0x-*`)
