"""
Main application entry point
Onboarding System API - Modular architecture with production security
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os

# Config loads the correct .env file based on ERP_ENV
from .config import validate_required, ENVIRONMENT, FORCE_HTTPS, ENABLE_WAF, APP_URL, get_env_info, ACTIVE_ENV_FILE
validate_required()

# Import routers
from .routes import auth, dashboard, tenants, onboarding, roles, tenant_portal, secure_auth, nodes, tunnels, provisioning, settings, billing, logs, domains, plans, customers, partners, leads, commissions, quotations, stripe_connect, suspension
from .routes import blueprints, seats, invoices, settlements, reconciliation, work_orders, branding, audit
from .routes import reports, quotas

# Import security middleware
from .security.middleware import SecurityMiddleware, WAFMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Onboarding System API",
    description="Sistema de onboarding automático con integración de Stripe y Odoo",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,  # Disable docs in prod
    redoc_url="/redoc" if ENVIRONMENT != "production" else None
)

# CORS configuration
# Permite origenes administrables por env y soporte multi-dominio.
default_origins = ",".join([
    "http://localhost:4443",
    "http://localhost:5173",
    "https://sajet.us",
    "https://techeels.sajet.us",
    "https://tcs.sajet.us",
    "https://boocking.sajet.us",
    "https://cliente1.sajet.us",
    "https://demo_cliente.sajet.us",
    "https://techeels.io",
    "https://www.techeels.io",
    "https://evolucionamujer.com",
    "https://www.evolucionamujer.com",
    "https://impulse-max.com",
    "https://www.impulse-max.com",
])

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", default_origins).split(",") if o.strip()]
ALLOWED_ORIGIN_REGEX = os.getenv(
    "ALLOWED_ORIGIN_REGEX",
    r"https://([a-z0-9-]+\.)?sajet\.us$|https://(www\.)?(techeels\.io|evolucionamujer\.com|impulse-max\.com)$|https://[a-z0-9-]+\.use\.devtunnels\.ms$"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security Middleware (HTTPS enforcement, security headers)
app.add_middleware(SecurityMiddleware, force_https=FORCE_HTTPS)

# WAF Middleware (SQL injection, XSS, etc. protection)
app.add_middleware(WAFMiddleware, enabled=ENABLE_WAF)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Include routers - Legacy auth (backward compatibility)
app.include_router(auth.router)
app.include_router(roles.router)

# Include new secure auth router
app.include_router(secure_auth.router)

# Application routers
app.include_router(dashboard.router)
app.include_router(tenants.router)
app.include_router(onboarding.router)
app.include_router(tenant_portal.router)
app.include_router(nodes.router)  # Multi-Proxmox management
app.include_router(tunnels.router)  # Cloudflare Tunnel management
app.include_router(provisioning.router)  # Auto-provisioning de tenants Odoo
app.include_router(settings.router)  # Configuración administrable
app.include_router(billing.router)  # Facturación y métricas de pagos
app.include_router(logs.router)  # Logs del sistema en tiempo real
app.include_router(domains.router)  # Gestión de dominios personalizados
app.include_router(plans.router)  # CRUD de planes y precios
app.include_router(customers.router)  # Gestión de clientes y facturación
app.include_router(partners.router)  # Gestión de socios comerciales
app.include_router(leads.router)  # Pipeline de prospectos por partner
app.include_router(commissions.router)  # Comisiones 50/50
app.include_router(quotations.router)  # Cotizaciones y catálogo de servicios
app.include_router(stripe_connect.router)  # Stripe Connect Express para partners
app.include_router(suspension.router)  # Páginas y API de suspensión de tenants

# ── Épicas SaaS Billing & Partner ──
app.include_router(blueprints.router)       # Catálogo de módulos y paquetes
app.include_router(seats.router)            # Seat events, HWM, Stripe qty sync
app.include_router(invoices.router)         # Facturas, intercompany
app.include_router(settlements.router)      # Settlement 50/50 partner ↔ Jeturing
app.include_router(reconciliation.router)   # Stripe ↔ DB reconciliation
app.include_router(work_orders.router)      # Órdenes de trabajo con gating
app.include_router(branding.router)         # White-label partner branding
app.include_router(audit.router)            # Audit events persistentes
app.include_router(reports.router)          # Reportes consolidados / analytics
app.include_router(quotas.router)           # Resource quotas por cliente/plan


# ── Startup log ──
_env_info = get_env_info()
logger.info(f"🚀 ERP Core starting — ERP_ENV={_env_info['erp_env']} | env_file={ACTIVE_ENV_FILE}")
logger.info(f"   DB → {_env_info['database_host']}/{_env_info['database_name']} | Stripe={_env_info['stripe_mode']}")


@app.get("/api/env")
async def env_info():
    """Returns current environment configuration (non-sensitive)."""
    return get_env_info()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "erp_env": _env_info["erp_env"],
        "database_host": _env_info["database_host"],
        "stripe_mode": _env_info["stripe_mode"],
        "security": {
            "https_enforced": FORCE_HTTPS,
            "waf_enabled": ENABLE_WAF
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4443)
