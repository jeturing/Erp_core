# Copilot Instructions - Onboarding System

## Project Overview
Sistema de onboarding SaaS que automatiza el registro de clientes, pagos con Stripe, y provisioning de instancias Odoo multitenant en contenedores LXC. Incluye landing pública, flujo de alta en `/signup`, panel admin y portal del cliente.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  FastAPI App    │────▶│  PostgreSQL DB   │     │  LXC Container  │
│  (Port 4443)    │     │  onboarding_db   │     │  (ID: 105)      │
└────────┬────────┘     └──────────────────┘     └────────▲────────┘
         │                                                 │
         │  Webhook                                        │ SSH/pct exec
         ▼                                                 │
┌─────────────────┐                              ┌─────────┴────────┐
│  Stripe API     │                              │ create_tenant.sh │
└─────────────────┘                              │ (Odoo provision) │
                                                 └──────────────────┘
```

### Data Flow
1. User submits form → `POST /api/checkout` → Creates `Customer` in DB → Stripe checkout session
2. Stripe payment success → `POST /webhook/stripe` → Creates `Subscription` → Provisions Odoo tenant
3. Tenant provisioning → `pct exec` to LXC 105 → `create_tenant.sh {subdomain}` → `{subdomain}.sajet.us`

## Key Files
- `app/main.py` - Registra routers FastAPI (auth, dashboard, tenants, onboarding)
- `app/routes/onboarding.py` - Landing `/`, signup `/signup` (alias `/onboarding`), checkout `/api/checkout`, webhook `/webhook/stripe`, success `/success`
- `app/routes/auth.py` y `app/routes/roles.py` - JWT básico y login unificado admin/tenant
- `app/routes/dashboard.py` - Vista admin `/admin` y métricas `/api/dashboard/metrics`
- `app/routes/tenant_portal.py` - Portal cliente `/tenant/portal` y APIs de billing
- `app/routes/tenants.py` - Listado/creación de tenants para admin
- `app/models/database.py` - SQLAlchemy models (`Customer`, `Subscription`, `StripeEvent`)
- `app/services/odoo_provisioner.py` - Provisioning LXC vía `pct exec`
- `templates/` - Jinja2 (UI en español): `landing.html`, `onboarding_form.html`, `admin_dashboard.html`, `tenant_portal.html`, etc.

## Development Commands

```bash
# Activate virtual environment
source /opt/onboarding-system/venv/bin/activate

# Run development server (port 4443)
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload

# API documentation available at:
# - /docs (Swagger UI)
# - /redoc (ReDoc)
```

## Database
- **PostgreSQL**: `postgresql://jeturing:321Abcd@localhost/onboarding_db`
- **Models**: SQLAlchemy ORM. Session pattern via `SessionLocal()` (cierre manual).
- **Status Enum**: `SubscriptionStatus` - `pending`, `active`, `cancelled`, `past_due`

## Conventions & Patterns

### Session Management
```python
# Pattern used throughout - manual session management
db = SessionLocal()
try:
    # ... operations
    db.commit()
finally:
    db.close()
```

### Stripe Integration
- Webhook en `/webhook/stripe` valida firma con `STRIPE_WEBHOOK_SECRET`
- `client_reference_id` enlaza sesión de checkout con `Customer.id`
- Events almacenados en `StripeEvent` para auditoría
- `APP_URL` usado en `success_url` y `cancel_url` de Stripe

### Tenant Provisioning
- Async function pero usa `subprocess.run` bloqueante
- Timeout 5 minutos para aprovisionamiento
- Dominio: `{subdomain}.sajet.us`
- LXC ID `105` hardcoded en provisioner

## Environment Variables (.env)
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=postgresql://...
APP_PORT=5000
APP_URL=http://localhost:4443
JWT_SECRET_KEY=...
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## Important Notes
- UI en **español**
- Templates en `/opt/onboarding-system/templates`
- Precios en **cents** (2900 = $29.00)
- Rutas ya modularizadas en `app/routes/`
