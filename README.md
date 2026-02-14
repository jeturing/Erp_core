# Sajet.us – SaaS ERP Platform | Phase 2 + Phase 3 (Partner-Led Onboarding)

## Overview
Sistema de onboarding SaaS multi-canal que automatiza registro de clientes vía **Stripe Checkout** (directo) o **Partners/Implementadores** (partner-led), con provisioning de instancias Odoo multitenant en contenedores LXC. Incluye landing pública, formularios sin precios, panel admin avanzado, portal de socios y portal del cliente.

**Current Status**: ✅ Phase 2 Complete | 🚧 Phase 3 (Partner-Led) – En Documentación  
**Last Updated**: Febrero 14, 2026

---

## 🎯 Phase 2 Deliverables - All Complete ✅

### Nuevas Funcionalidades (Phase 2)
1. ✅ **Landing Page** - Página de marketing en `/` con CTAs a signup
2. ✅ **Signup Flow** - Formulario en `/signup` con selección de plan + checkout Stripe
3. ✅ **Dual Auth System** - Login admin/tenant con cookies httpOnly
4. ✅ **Admin Dashboard Mejorado** - Navbar Core, páginas de logs y billing
5. ✅ **Tenant Portal** - Portal cliente con facturación Stripe
6. ✅ **MCP Integration** - Model Context Protocol para API, logs y PostgreSQL
7. ✅ **Templates Core** - Sistema de plantillas base reutilizables

---

## 🚀 Phase 3 – Partner-Led Onboarding (En Documentación)

### Nuevas Funcionalidades (Phase 3)
1. 📋 **Onboarding Público Sin Precios** - Formulario multi-etapa (`/onboarding/leads`) para captar leads sin mostrar dinero
2. 🤝 **Rol Proveedor de Servicio (Partner)** - Portal de socios con acceso a leads asignados y creación de tenants
3. 📊 **Cotizador Interno** - Dimensionamiento técnico (complejidad, migración, requerimientos) con gating automático
4. 💼 **Gestión de Partners** - Administración de proveedores, comisiones (50/50), trazabilidad de leads
5. ⚙️ **Flujo Partner-Led** - Lead → Partner califica → Tenant activo → Factura + Comisión
6. 🎯 **Gating de Jeturing** - Custom (integraciones, MRP, multi-empresa) solo si Jeturing lo aprueba

**Documentación Phase 3**:
- [RESUMEN_EJECUTIVO_PHASE_3.md](docs/RESUMEN_EJECUTIVO_PHASE_3.md) – Visión ejecutiva
- [ONBOARDING_PUBLICO_SIN_PRECIOS.md](docs/ONBOARDING_PUBLICO_SIN_PRECIOS.md) – Flujo, API, BD, gating
- [ROLES_PERMISOS_MATRIZ.md](docs/ROLES_PERMISOS_MATRIZ.md) – ACL y permisos por rol
- [PR_TEMPLATE_ONBOARDING_PARTNER.md](docs/PR_TEMPLATE_ONBOARDING_PARTNER.md) – Checklist de integración
- [VALIDACION_NO_REGRESION.md](docs/VALIDACION_NO_REGRESION.md) – Pruebas de no-regresión

### Rutas Principales
| Ruta | Descripción |
|------|-------------|
| `/` | Landing page pública |
| `/signup` | Formulario de registro (alias: `/onboarding`) |
| `/login/admin` | Login de administrador |
| `/login/tenant` | Login de cliente |
| `/admin` | Dashboard administrativo |
| `/admin/logs` | Logs del sistema |
| `/admin/billing` | Facturación y pagos |
| `/tenant/portal` | Portal del cliente |
| `/success` | Página post-checkout |

### Technology Stack
- **Backend**: FastAPI 0.115+, SQLAlchemy 2.0+, PostgreSQL
- **Frontend**: HTML5, Tailwind CSS 3, Vanilla JavaScript
- **Authentication**: PyJWT con cookies httpOnly + localStorage backup
- **Payments**: Stripe Checkout + Webhooks
- **Provisioning**: LXC containers (ID 105) + pct exec
- **MCP**: Node.js MCP servers para API, filesystem, PostgreSQL

---

## 🔒 Autenticación Phase 2

### Flujo de Login
1. Usuario accede a `/login/admin` o `/login/tenant`
2. POST a `/api/login/unified` con `{email, password, role}`
3. Servidor valida y retorna JWT + establece cookie `token` (httpOnly)
4. Redirección a `/admin` o `/tenant/portal` según rol

### Endpoints de Auth
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/login/{role}` | GET | Página de login |
| `/api/login/unified` | POST | Login unificado |
| `/api/logout` | POST | Invalida cookie |

### Cookies + localStorage
- Cookie `token` httpOnly para requests del servidor
- localStorage `access_token` como backup para JS

---

## 📊 API Endpoints

### Admin
| Endpoint | Descripción |
|----------|-------------|
| `/api/dashboard/metrics` | Métricas (MRR, tenants, etc.) |
| `/api/tenants` | Lista de tenants |
| `/api/admin/stripe-events` | Eventos Stripe recientes |

### Tenant
| Endpoint | Descripción |
|----------|-------------|
| `/tenant/api/info` | Info del tenant actual |
| `/tenant/api/billing` | Facturas y método de pago |
| `/tenant/api/update-payment` | Actualizar método de pago |
| `/tenant/api/cancel-subscription` | Cancelar suscripción |

### Onboarding
| Endpoint | Descripción |
|----------|-------------|
| `/api/plans` | Planes disponibles |
| `/api/checkout` | Crear sesión Stripe |
| `/webhook/stripe` | Webhook de Stripe |

---

## 🎨 Templates Core

### Base Template
`base_admin.html` - Layout base con:
- Sidebar navegable
- Header con título dinámico
- Área de contenido
- Scripts compartidos (logout, fetch interceptor)

### Uso
```jinja2
{% extends "base_admin.html" %}

{% block title %}Mi Página{% endblock %}
{% block page_title %}Título{% endblock %}
{% block content %}
  <!-- Contenido aquí -->
{% endblock %}
```

---

## 🚀 Getting Started

### 1. Start the Server
```bash
cd /opt/onboarding-system
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload
```

### 2. Access the System
| URL | Descripción |
|-----|-------------|
| http://localhost:4443/ | Landing page |
| http://localhost:4443/signup | Registro de clientes |
| http://localhost:4443/login/admin | Login admin |
| http://localhost:4443/login/tenant | Login cliente |
| http://localhost:4443/admin | Dashboard admin |
| http://localhost:4443/tenant/portal | Portal cliente |
| http://localhost:4443/docs | API Swagger |

### 3. Credenciales Demo
```
Admin:   admin / admin123
Tenant:  [email registrado] / [cualquier password - demo mode]
```

---

## 📂 Estructura del Proyecto (Phase 2)

```
/opt/onboarding-system/
├── app/
│   ├── main.py                    # Entry point, registra routers
│   ├── models/database.py         # SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py                # JWT auth básico
│   │   ├── roles.py               # Login unificado admin/tenant
│   │   ├── dashboard.py           # Admin dashboard + logs + billing
│   │   ├── tenants.py             # API de tenants
│   │   ├── tenant_portal.py       # Portal del cliente
│   │   └── onboarding.py          # Landing, signup, checkout, webhook
│   └── services/
│       └── odoo_provisioner.py    # Provisioning LXC
├── templates/
│   ├── base_admin.html            # Layout base admin
│   ├── partials/
│   │   └── admin_sidebar.html     # Sidebar compartido
│   ├── landing.html               # Landing page
│   ├── onboarding_form.html       # Signup form
│   ├── role_login.html            # Login dual
│   ├── admin_dashboard.html       # Dashboard
│   ├── admin_logs.html            # System logs
│   ├── admin_billing.html         # Facturación
│   ├── tenant_portal.html         # Portal cliente
│   └── success.html               # Post-checkout
├── mcp/
│   └── api-server.js              # MCP server para API
├── mcp_config.json                # Configuración MCP
├── .github/copilot-instructions.md
├── docs/                          # Documentación
└── requirements.txt
```

---

## 🔧 MCP (Model Context Protocol)

Configurado para integrar con Copilot/Claude:

```json
{
  "mcpServers": {
    "onboarding-api": {
      "command": "node",
      "args": ["/opt/onboarding-system/mcp/api-server.js"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://..."]
    },
    "filesystem-logs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/opt/onboarding-system/logs"]
    }
  }
}
```

### MCP Tools Disponibles
- `health_check` - Estado del sistema
- `admin_login` - Autenticación
- `get_dashboard_metrics` - Métricas
- `list_tenants` - Listar tenants
- `get_stripe_events` - Eventos de Stripe

---
│   ├── ADMIN_DASHBOARD.md         ✅ API docs
│   └── INTEGRATION_SUMMARY.md     ✅ Overview
├── .github/
│   └── copilot-instructions.md    ✅ AI agent guide
├── DELIVERABLES.md                ✅ Complete checklist
├── test_jwt.sh                    ✅ Automated tests
├── requirements.txt               ✅ Dependencies
├── venv/                          ✅ Virtual environment
└── README.md                      (recommended to add)
```

---

## 🧪 Testing

### Automated Testing
```bash
bash /opt/onboarding-system/test_jwt.sh
```

### Manual Testing Checklist
- [ ] Login with valid credentials → redirects to dashboard
- [ ] Login with invalid credentials → shows error
- [ ] Access /admin without token → redirects to /login
- [ ] Dashboard metrics load with valid token
- [ ] Tenant list displays correctly
- [ ] Logout button clears token and redirects
- [ ] API endpoints return 401 with invalid token

---

## 🔒 Security Status

### Phase 1 Implementation ✅
- ✅ JWT token-based authentication
- ✅ HMAC-SHA256 signing
- ✅ 24-hour token expiration
- ✅ Secure credential validation
- ✅ Protected routes enforcement
- ✅ Bearer token validation

### Production Recommendations ⏳
- [ ] Use HTTPS/TLS only
- [ ] Store tokens in httpOnly cookies
- [ ] Implement refresh tokens
- [ ] Add rate limiting to login
- [ ] Enable audit logging
- [ ] Implement 2FA
- [ ] Configure WAF (Web Application Firewall)

---

## 📊 Key Metrics

| Component | Status | Lines | Files |
|-----------|--------|-------|-------|
| Backend Code | ✅ | 446 | 1 |
| Frontend Code | ✅ | 390+ | 2 |
| Documentation | ✅ | 2000+ | 7 |
| Tests | ✅ | 100+ | 1 |
| **Total** | ✅ | 2936+ | 11 |

---

## 🎯 Phase 3 Preview

### Funcionalidades Planificadas
- [ ] Chart.js para analytics avanzados
- [ ] html2pdf.js para exportar reportes PDF
- [ ] WebSocket para logs en tiempo real
- [ ] Configuración de tenant (CRUD completo)
- [ ] Gestión avanzada de clientes
- [ ] 2FA / autenticación reforzada
- [ ] Rate limiting y WAF

---

## 🌐 Variables de Entorno

```bash
# .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
DATABASE_URL=postgresql://jeturing:321Abcd@localhost/onboarding_db
APP_PORT=4443
APP_URL=http://localhost:4443
JWT_SECRET_KEY=your-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

## 🧪 Testing

```bash
# Test de autenticación
curl -X POST http://localhost:4443/api/login/unified \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"admin123","role":"admin"}'

# Test de métricas (con cookie o header)
curl http://localhost:4443/api/dashboard/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"

# Health check
curl http://localhost:4443/health
```

---

## ✅ Checklist Phase 2

- [x] Landing page en `/`
- [x] Signup en `/signup` con selección de plan
- [x] Login dual admin/tenant con cookies
- [x] Endpoint `/api/logout` para invalidar cookie
- [x] Admin dashboard con sidebar Core
- [x] Página de logs `/admin/logs`
- [x] Página de billing `/admin/billing`
- [x] Tenant portal con info de suscripción
- [x] Stripe events API
- [x] MCP configurado (api, postgres, filesystem)
- [x] Templates base reutilizables
- [x] README actualizado

---

**Status**: ✅ **PHASE 2 COMPLETE**

Listo para Phase 3 y despliegue en producción.
