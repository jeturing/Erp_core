# Copilot Instructions - Jeturing ERP Core

Estado: vigente  
Validado: 2026-06-12  
Entorno objetivo: `/opt/Erp_core`


## 📋 Project Overview

Multi-tenant ERP platform (Jeturing Core) for Odoo instance management, built with:
- **Backend**: FastAPI (Python 3.11+) with SQLAlchemy ORM
- **Database**: PostgreSQL (`erp_core_db`) on PCT 160 (localhost)
- **Current Frontend**: Jinja2 templates + Tailwind CSS (migrating to Svelte)
- **Infrastructure**: Proxmox LXC containers on host `atenea`, Cloudflare Tunnels
- **Payments**: Stripe integration with webhooks
- **Domain**: `*.sajet.us`

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  FastAPI App    │────▶│  PostgreSQL DB   │     │  LXC Container  │
│ PCT 160 (:4443) │     │  erp_core_db     │     │  PCT 105 (Odoo) │
└────────┬────────┘     │  (PCT 160 local) │     └────────▲────────┘
         │              └──────────────────┘              │
         │  Webhook                                       │ pct exec / SSH
         ▼                                                │
┌─────────────────┐     ┌──────────────────┐     ┌───────┴─────────┐
│  Stripe API     │     │ Cloudflare API   │     │  PostgreSQL 15  │
└─────────────────┘     │ (Tunnels/DNS)    │     │  PCT 137 (PRIMARY)│
                        └──────────────────┘     │  Odoo databases │
                                                 └─────────────────┘
```

---

## 🏗️ Infrastructure Map (Proxmox - Host: atenea)

### Host: `atenea`
- **Hardware**: 64 CPUs, 125 GB RAM, 1.8 TB Disk
- **Network Bridges**:
  - `vmbr0`: 208.115.125.26/29 (public)
  - `vmbr1`: 10.10.10.1/24 (internal LXC network)
  - `vmbr2`: 172.16.16.1/24
  - `tailscale0`: 100.103.65.2 (Tailscale VPN)

### ⚠️ CRITICAL: Database Topology

```
PCT 105 (Odoo 17) ──db_host=10.10.10.137──▶ PCT 137 (PostgreSQL 15 PRIMARY)
PCT 161 (Odoo 19) ──db_host=10.10.10.137──▶ PCT 137 (PostgreSQL 15 PRIMARY)
PCT 110 (Esecure)  ──db_host=127.0.0.1────▶ PCT 110 (PG 17 LOCAL)
PCT 155 (Flujo)    ──db_host=127.0.0.1────▶ PCT 155 (PG 17 LOCAL)
PCT 160 (ERP Core) ──db_host=10.10.10.20──▶ PCT 160 (PG LOCAL)
```

> **IMPORTANTE**: PCT 105 tiene PG 17 local pero Odoo NO lo usa. Odoo conecta a PG 15 en PCT 137.
> Al hacer queries SQL para Odoo (techeels, tcs, etc.), SIEMPRE usar PCT 137:
> ```bash
> pct exec 137 -- su - postgres -c "psql -d techeels -c 'SELECT ...'"
> ```
> NUNCA usar `pct exec 105 -- sudo -u postgres psql` para datos de Odoo.

### LXC Containers (Running)

| PCT | Nombre | IP | Rol | Servicios | Base de Datos |
|-----|--------|-----|-----|-----------|---------------|
| **105** | SRV-Odoo-server | 10.10.10.100 | Odoo 17 Multi-Tenant | odoo, nginx(:8080/:8443), cloudflared(da2bc763), PG17(local-NO USADO por Odoo), odoo-local-api(:8070), odoo-db-watcher | **db_host=10.10.10.137** |
| **110** | SRV-Esecure | 10.10.10.110 | Odoo (Esecure) | odoo(:8069), nginx, cloudflared(esecure-sajet), PG17 local | PG local: Esecure, cliente1, tcs |
| **137** | SRV-4-PGBK01 | 10.10.10.137 | **PRIMARY DB SERVER** | PostgreSQL 15, WAL archival, cron | techeels, tcs, jeturing, agroliferd, boocking, cliente1, erp_core_db, joficreditosrd, sattra, template_tenant |
| **146** | WL-DEPLOY-146 | 208.115.125.27 | WL Backend Deploy | Docker, nginx, ports 8000-8002/5000/9000/9443 | — |
| **147** | WL-STORAGE-147 | 10.10.10.5 | Object Storage | Docker, MinIO(:9000/:9001), :8085 | — |
| **149** | WL-CACHE-149 | 10.10.10.7 | Cache | Redis(:6379) | — |
| **150** | IA | 10.10.10.150 | AI Services | Docker, Ollama(:11434), Open-WebUI(:8080) | — |
| **154** | mcp-forensics | 208.115.125.28 | Security/SIEM | Docker, Wazuh(:55000/:1514/:1515), Kibana(:5601), PG local, cloudflared | — |
| **155** | SRV-FE | 10.10.10.155 | Odoo (Flujo Electrónico) | odoo, nginx, cloudflared(flujoeletronic), PG17 local | PG local: Flujo_electronic |
| **160** | SRV-Sajet | 10.10.10.20 / 208.115.125.29 | **ERP Core API** | FastAPI/uvicorn(:4443), nginx(:80/:443), PG local, cloudflared(f3620999) | PG local: erp_core_db |
| **161** | srv-Server-19 | 10.10.10.161 | Odoo 19 | odoo19(:8069), nginx(:80/:443), PG14 local, cloudflared(b3d4c13e) | **db_host=10.10.10.137**, db_name=jeturing |

### LXC Containers (Stopped)

| PCT | Nombre | IP | Rol |
|-----|--------|-----|-----|
| 106 | SRV-0 | 10.10.10.106 | Desconocido |
| 124 | SRV-101-Jeturing | 192.168.1.101 (vmbr0) | Legacy |
| 141 | SRV-4-PGBK01-standby | 192.168.1.141 (vmbr0) | PG Standby (inactivo) |
| 143 | wl-143 | 10.10.10.3 | WL (deprecated) |
| 148 | WL-DATABASE-148 | 10.10.10.6 | WL Database (deprecated) |
| 151 | WLkong-gateway | 10.10.10.8 | API Gateway (deprecated) |
| 152 | WL-gravitee-portal | 10.10.10.9 | API Portal (deprecated) |
| 153 | WL-DEV-153 | 10.10.10.13 | WL Dev (deprecated) |

### Cloudflare Tunnels

| PCT | Tunnel ID | Dominios |
|-----|-----------|----------|
| 105 | da2bc763 | *.sajet.us, techeels.io, evolucionamujer.com, impulse-max.com, joficreditosrd.com |
| 160 | f3620999 | sajet.us, *.sajet.us (ERP Core) |
| 161 | b3d4c13e | Token-based (Odoo 19) |
| 110 | esecure-sajet | esecure.sajet.us |
| 155 | flujoeletronic | flujoelectronic.sajet.us |

### Odoo 17 Configuration (PCT 105)
```ini
[options]
db_host = 10.10.10.137
db_port = 5432
db_user = Jeturing
db_password = 321Abcd
dbfilter = ^%d$
proxy_mode = True
workers = 4
addons_path = /opt/odoo/addons,/opt/odoo/Extra,/opt/odoo/custom_addons,/opt/odoo/extra-addons
```

---

## 🎨 Jeturing Brand Identity

### Brand Positioning
Technology company focused on:
- Enterprise innovation & ERP / Odoo solutions
- Cybersecurity & digital infrastructure
- Automation & intelligent systems

**Brand Image**: Trust, advanced technology, professionalism, sophistication
**Visual References**: Stripe / Cloudflare / Microsoft corporate style

### 🎨 Official Color Palette

| Type | Color | Hex | Tailwind | CSS Variable |
|------|-------|-----|----------|--------------|
| **Primary** | Deep Blue | `#003B73` | `primary-500` | `--brand-primary` |
| **Secondary** | Metallic Gray | `#6C757D` | `secondary-500` | `--brand-secondary` |
| **Base** | White | `#FFFFFF` | `white` | `--brand-base` |
| **Tech Accent** | Electric Green | `#00FF9F` | `accent-500` | `--brand-accent` |
| **Innovation** | Futuristic Purple | `#8F00FF` | `innovation-500` | `--brand-innovation` |

### Extended UI Palette (Dark Mode)
```css
/* Primary shades */
--primary-50: #E6EEF5;
--primary-100: #B3CDE0;
--primary-200: #80ABCB;
--primary-300: #4D89B6;
--primary-400: #1A67A1;
--primary-500: #003B73; /* Main brand color */
--primary-600: #003265;
--primary-700: #002952;
--primary-800: #00203F;
--primary-900: #00172C;

/* Accent shades (Electric Green) */
--accent-50: #E6FFF5;
--accent-100: #B3FFE0;
--accent-200: #80FFCB;
--accent-300: #4DFFB6;
--accent-400: #1AFFA9;
--accent-500: #00FF9F; /* Main accent */
--accent-600: #00CC7F;
--accent-700: #00995F;
--accent-800: #00663F;
--accent-900: #00331F;

/* Surface colors (Dark theme) */
--surface-dark: #0F1419;
--surface-card: #1A1F26;
--surface-highlight: #252B33;
--surface-border: #2F3640;

/* Status colors */
--status-success: #10B981;
--status-warning: #F59E0B;
--status-error: #EF4444;
--status-info: #3B82F6;
```

### Typography
- **Primary Font**: Inter (Sans-serif, modern, clean)
- **Monospace**: JetBrains Mono (for code, IDs, technical data)
- **Style**: Corporate, technological, high readability in UI and documents

### ⚠️ Visual Style Rules

**ALWAYS USE**:
- Deep Blue (#003B73) as primary color for headers, buttons, links
- Electric Green (#00FF9F) for success states, CTAs, highlights
- Dark surfaces (#0F1419, #1A1F26) for dashboard backgrounds
- Clean, minimal gradients (single-color or blue→darker blue)

**NEVER USE**:
- Purple gradients (`purple-*`, `violet-*`) - except `#8F00FF` sparingly for innovation badges
- Pink colors (`pink-*`, `rose-*`) anywhere in UI
- Rainbow/colorful gradients
- "AI-style" neon effects or glowing borders
- Cyan/turquoise as primary (previous brand color, deprecated)

---

## 🗄️ Database Schema

### Core Tables
```sql
customers          -- Client data (email, company_name, subdomain, stripe_customer_id)
subscriptions      -- Plans (customer_id, plan_name, status, stripe_subscription_id, mrr)
stripe_events      -- Webhooks (event_id, event_type, payload, processed)
proxmox_nodes      -- Cluster nodes (hostname, status, cpu_total, ram_total, disk_total)
lxc_containers     -- Containers (vmid, node_id, ip_address, cpu_cores, ram_mb)
tenant_deployments -- Deployments (subdomain, tunnel_id, tunnel_url, plan_type, status)
resource_metrics   -- Historical (container_id, cpu, ram, disk, network, timestamp)
system_config      -- Settings (key, value, category, is_secret, updated_at)
```

### Connection (ERP Core - PCT 160)
```python
DATABASE_URL = "postgresql+psycopg2://jeturing:321Abcd@10.10.10.20:5432/erp_core_db"
```

### Connection (Odoo databases - PCT 137)
```python
# Odoo 17 (PCT 105) y Odoo 19 (PCT 161) conectan aquí
ODOO_DB_HOST = "10.10.10.137"
ODOO_DB_PORT = 5432
ODOO_DB_USER = "Jeturing"
ODOO_DB_PASSWORD = "321Abcd"
# BDs: techeels, tcs, jeturing, agroliferd, boocking, cliente1, joficreditosrd, sattra, template_tenant
```

---

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard/metrics` - Main metrics (tenants, MRR, cluster load)
- `GET /api/dashboard/all` - Consolidated endpoint (metrics + tenants + cluster)

### Tenants
- `GET /api/tenants` - List all tenants with pagination
- `POST /api/tenants` - Create new tenant (provisions Odoo + Cloudflare)
- `DELETE /api/tenants/{id}` - Delete tenant and cleanup
- `PUT /api/tenants/{id}/suspend` - Suspend tenant
- `PUT /api/tenants/{id}/reactivate` - Reactivate tenant
- `GET /api/tenants/servers` - Odoo server status and capacity

### Billing
- `GET /api/billing/metrics` - MRR, revenue, churn rate (real calculations)
- `GET /api/billing/invoices` - Invoice list from Stripe
- `GET /api/billing/comparison` - Month-over-month comparison

### System
- `GET /api/logs/provisioning` - Provisioning logs
- `GET /api/logs/status` - Service health (PostgreSQL, FastAPI, LXC, Disk)
- `GET /api/tunnels` - Cloudflare tunnel list
- `GET /api/settings/odoo/current` - Current Odoo configuration

---

## 📁 File Structure

```
/opt/Erp_core/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── models/
│   │   └── database.py      # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py          # JWT authentication
│   │   ├── dashboard.py     # Dashboard metrics
│   │   ├── tenants.py       # Tenant CRUD
│   │   ├── billing.py       # Billing/invoices
│   │   ├── provisioning.py  # Tenant provisioning
│   │   ├── tunnels.py       # Cloudflare tunnels
│   │   ├── logs.py          # System logs
│   │   └── settings.py      # Configuration
│   ├── services/
│   │   ├── odoo_manager.py  # OdooDatabaseManager
│   │   └── cloudflare.py    # CloudflareManager
│   └── security/
│       └── jwt_handler.py   # JWT utilities
├── templates/               # Jinja2 (legacy, migrating to Svelte)
├── static/                  # CSS, JS assets
├── frontend/                # Svelte SPA (new)
└── .github/
    └── copilot-instructions.md
```

---

## 🚀 Frontend Migration Plan

### Phase 1: Backend Data Integrity ✅
- Remove all mocked/hardcoded data from endpoints
- Create consolidated endpoints to reduce API calls
- Add historical data tracking for metrics comparison

### Phase 2: Svelte Project Setup
- Initialize Vite + Svelte + TypeScript
- Configure Tailwind with Jeturing brand colors
- Create base components (Layout, Sidebar, Cards, Tables)

### Phase 3: Page Migration
1. Login page (corporate design, no purple)
2. Dashboard (real metrics, charts)
3. Tenants management
4. Billing & invoices
5. System logs
6. Settings

### Phase 4: Deployment
- Build static assets
- Serve from FastAPI or Nginx
- Maintain API compatibility

---

## 📝 Code Standards

### Python (Backend)
```python
# Use async/await for DB operations
async def get_tenants(db: AsyncSession):
    result = await db.execute(select(Customer))
    return result.scalars().all()

# Type hints everywhere
def calculate_mrr(subscriptions: list[Subscription]) -> Decimal:
    return sum(s.mrr for s in subscriptions if s.status == "active")

# Pydantic for validation
class TenantCreate(BaseModel):
    company_name: str
    email: EmailStr
    subdomain: str = Field(regex=r"^[a-z0-9-]+$")
    plan: Literal["basic", "pro", "enterprise"]
```

### Svelte (Frontend)
```svelte
<!-- TypeScript, Tailwind, brand colors -->
<script lang="ts">
  import { onMount } from 'svelte';
  import type { Tenant } from '$lib/types';
  
  let tenants: Tenant[] = [];
  
  onMount(async () => {
    const res = await fetch('/api/tenants');
    tenants = await res.json();
  });
</script>

<div class="bg-surface-dark min-h-screen">
  <button class="bg-primary-500 hover:bg-primary-600 text-white">
    Nuevo Tenant
  </button>
</div>
```

### API Response Format
```json
// Success
{
  "success": true,
  "data": { ... },
  "meta": { "total": 10, "page": 1 }
}

// Error
{
  "success": false,
  "error": "TENANT_NOT_FOUND",
  "detail": "El tenant con ID 123 no existe"
}
```

---

## ⚠️ Critical Rules

1. **NO MOCKED DATA** - All endpoints must return real data from PostgreSQL
2. **Brand colors only** - Use Jeturing palette (#003B73, #00FF9F), no purple/pink
3. **Performance** - Consolidate API calls, implement Redis caching for dashboard
4. **Type safety** - TypeScript in frontend, type hints in backend
5. **Spanish UI** - All user-facing text in Spanish
6. **Dark mode** - Primary theme for admin dashboard
7. **Real calculations** - MRR, churn rate, comparisons from actual subscription data

---

## 🔧 Development Commands

```bash
# Backend
cd /opt/Erp_core
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload

# Frontend (Svelte)
cd /opt/Erp_core/frontend
npm run dev

# Build
npm run build
```

## Environment Variables
```env
DATABASE_URL=postgresql://jeturing:321Abcd@localhost/erp_core_db
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
JWT_SECRET_KEY=your-secret-key
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ZONE_ID=...
```
