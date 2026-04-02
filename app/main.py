"""
Main application entry point
Onboarding System API - Modular architecture with production security
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Cookie, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import base64
import hashlib
import logging
import os

# Config loads the correct .env file based on ERP_ENV
from .config import validate_required, ENVIRONMENT, FORCE_HTTPS, ENABLE_WAF, APP_URL, get_env_info, ACTIVE_ENV_FILE
validate_required()

# Background scheduler
from .services.background_scheduler import scheduler

# Import routers
from .routes import auth, dashboard, tenants, onboarding, roles, tenant_portal, secure_auth, nodes, tunnels, provisioning, settings, billing, logs, domains, plans, customers, partners, leads, commissions, quotations, stripe_connect, suspension
from .routes import blueprints, seats, invoices, settlements, reconciliation, work_orders, branding, audit
from .routes import reports, quotas, partner_portal
from .routes import customer_onboarding
from .routes import onboarding_config
from .routes import communications
from .routes import admin_users
from .routes import users_neural
from .routes import agreements
from .routes import stripe_sync
from .routes import public_landing
from .routes import accountant_portal
from .routes import admin_landing
from .routes import payments  # Nuevo: Pagos y dispersión a proveedores
from .routes import mercury_webhooks  # Webhooks Mercury para conciliación
from .routes import dispersion  # Dispersión Mercury con feature flag y auth 4-ojos
from .routes import plan_migration  # Migración automática de planes por consumo
from .routes import storage_alerts  # Alertas de almacenamiento con notificaciones
from .routes import monitoring_dashboard  # Dashboard de monitoreo completo
from .routes import admin_control_panel  # 🔧 Panel de control administrativo (SMTP, templates, alertas)
from .routes import api_keys             # 🔑 API Key Management (rate limit, RBAC, rotación estilo Stripe)
from .routes import odoo_webhooks        # 🔄 Webhooks Odoo → Portal (sync bidireccional)
from .routes import postal_webhooks      # 📧 Postal Mail webhooks + uso de correo
from .routes import gusto_payroll        # 💼 Gusto Payroll USA + OAuth + webhooks
from .routes import migration            # 🚚 Migración live de tenants entre nodos (Fase 2)
from .routes import session_monitoring   # 🛡️ DSAM — Dynamic Session & Anti-Theft Monitor
from .routes import developer_portal     # 🔧 Developer Portal — Apps & Agreement Flows
from .routes.roles import _require_admin as _require_admin_base

# Import security middleware
from .security.middleware import SecurityMiddleware, WAFMiddleware
from .security.cors_dynamic import DynamicCORSMiddleware, refresh_cors_cache

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Initialize Sentry if DSN is provided
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production-sajet"),
        traces_sample_rate=float(os.getenv("SENTRY_SAMPLE_RATE", "0.2")),
        server_name=os.getenv("SENTRY_SERVER_NAME", "sajet-pct160"),
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # GlitchTip specific: sessions are not supported
        auto_session_tracking=False,
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base directory for static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Lifespan: startup/shutdown hooks ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle."""
    logger.info("🚀 Starting background scheduler...")
    await scheduler.start()
    yield
    logger.info("🛑 Stopping background scheduler...")
    await scheduler.stop()


app = FastAPI(
    title="Sajet ERP API",
    lifespan=lifespan,
    description=(
        "## API del Sistema ERP Sajet\n\n"
        "Plataforma SaaS multi-tenant sobre con facturación Stripe, "
        "provisioning automático en nuestro cloud y portal self-service para clientes y partners.\n\n"
        "### Autenticación\n"
        "Todos los endpoints protegidos requieren un JWT en cookie `access_token` "
        "o header `Authorization: Bearer <token>`.\n\n"
        "### Entornos\n"
        "- **Producción**: `https://api.sajet.us`\n"
        "- **Staging**: `https://staging-api.sajet.us`\n"
    ),
    version="2.0.0",
    contact={
        "name": "Sajet ERP - Soporte Técnico",
        "url": "https://sajet.us",
        "email": "help@sajet.us",
    },
    license_info={
        "name": "Propietario - Jeturing SRL",
        "url": "https://sajet.us/legal",
    },
    docs_url="/sajet-api-docs",
    redoc_url="/sajet-api-redoc",
    openapi_tags=[
        {"name": "Auth", "description": "Autenticación JWT y 2FA"},
        {"name": "Tenant Portal", "description": "Portal self-service: plan, facturas, dominios, usuarios, contraseña"},
        {"name": "Customer Onboarding", "description": "Flujo de alta de nuevos clientes"},
        {"name": "Onboarding Config", "description": "Configuración admin del wizard de onboarding"},
        {"name": "Plans", "description": "CRUD de planes y precios Stripe"},
        {"name": "Customers", "description": "Gestión de clientes"},
        {"name": "Domains", "description": "Dominios personalizados por tenant"},
        {"name": "Billing", "description": "Métricas de facturación y Stripe"},
        {"name": "Seats", "description": "Usuarios Odoo: seat events y high-water mark"},
        {"name": "Partners", "description": "Socios comerciales y comisiones"},
        {"name": "Partner Portal", "description": "Portal self-service para partners"},
        {"name": "Provisioning", "description": "Auto-provisioning de instancias Odoo en Proxmox"},
        {"name": "Nodes", "description": "Gestión multi-Proxmox"},
        {"name": "Tunnels", "description": "Cloudflare Tunnels"},
        {"name": "Invoices", "description": "Facturas e intercompany"},
        {"name": "Settlements", "description": "Liquidaciones partner / Jeturing"},
        {"name": "Work Orders", "description": "Órdenes de trabajo con gating"},
        {"name": "Audit", "description": "Registro de auditoría"},
        {"name": "Reports", "description": "Analytics y reportes consolidados"},
        {"name": "Dashboard", "description": "Métricas del dashboard admin"},
        {"name": "Mercury", "description": "Webhooks y conciliación Mercury"},
    ],
)

# ── Protección Basic Auth para Swagger / OpenAPI ──
# Las rutas /sajet-api-docs, /sajet-api-redoc y /openapi.json requieren
# usuario y contraseña para evitar exposición pública del schema.
_DOCS_USER = os.getenv("API_DOCS_USER", "jeturing")
_DOCS_PASS_HASH = hashlib.sha256(
    os.getenv("API_DOCS_PASSWORD", "Jeturing2015@").encode()
).hexdigest()
_DOCS_PROTECTED_PATHS = ("/sajet-api-docs", "/sajet-api-redoc", "/openapi.json")


class DocsBasicAuthMiddleware(BaseHTTPMiddleware):
    """Middleware que protege las rutas de documentación con HTTP Basic Auth."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not any(path.startswith(p) for p in _DOCS_PROTECTED_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, _, password = decoded.partition(":")
                pass_hash = hashlib.sha256(password.encode()).hexdigest()
                if username == _DOCS_USER and pass_hash == _DOCS_PASS_HASH:
                    return await call_next(request)
            except Exception:
                pass

        return Response(
            content="Acceso denegado. Credenciales requeridas.",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Sajet API Docs"'},
        )


# CORS configuration — Dynamic from DB (custom_domains + tenant_deployments)
# Origins are cached in-memory with 60s TTL. Zero latency on requests.
# Refresh cache manually: POST /api/admin/cors/refresh
app.add_middleware(DynamicCORSMiddleware)

# Security Middleware (HTTPS enforcement, security headers)
app.add_middleware(SecurityMiddleware, force_https=FORCE_HTTPS)

# WAF Middleware (SQL injection, XSS, etc. protection)
app.add_middleware(WAFMiddleware, enabled=ENABLE_WAF)

# Docs Basic Auth — debe ser el último en add_middleware (se ejecuta primero al procesar requests)
app.add_middleware(DocsBasicAuthMiddleware)

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
app.include_router(partner_portal.router)  # Portal self-service para partners
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
app.include_router(customer_onboarding.router)  # Customer onboarding + RD e-CF flow
app.include_router(onboarding_config.router)    # Admin-configurable onboarding config
app.include_router(communications.router)        # Historial de emails transaccionales
app.include_router(admin_users.router)           # CRUD usuarios administrativos
app.include_router(users_neural.router)           # 🧠 Centro Neural de Gestión de Usuarios
app.include_router(agreements.router)            # NDA/TOS templates + signing flow
app.include_router(stripe_sync.router)           # Stripe webhook sync
app.include_router(public_landing.router)        # Landing page pública
app.include_router(accountant_portal.router)     # Portal para contadores
app.include_router(admin_landing.router)         # Landing admin-only
app.include_router(payments.router)              # Pagos y dispersión a proveedores
app.include_router(mercury_webhooks.router)      # Webhooks Mercury para conciliación
app.include_router(dispersion.router)            # Dispersión Mercury con feature flag y auth 4-ojos
app.include_router(plan_migration.router)        # Migración automática de planes por consumo
app.include_router(storage_alerts.router)        # Alertas de almacenamiento con notificaciones
app.include_router(monitoring_dashboard.router)  # Dashboard de monitoreo completo
app.include_router(admin_control_panel.router)   # 🔧 Panel de control: SMTP, templates, alertas
app.include_router(api_keys.router)              # 🔑 API Key Management (rate limit, rotación Stripe)
app.include_router(odoo_webhooks.router)         # 🔄 Webhooks Odoo → Portal (sync bidireccional)
app.include_router(postal_webhooks.router)       # 📧 Postal Mail webhooks + uso de correo
app.include_router(gusto_payroll.router)         # 💼 Gusto Payroll USA + OAuth + webhooks
app.include_router(migration.router)             # 🚚 Migración live de tenants entre nodos (Fase 2)
app.include_router(session_monitoring.router)    # 🛡️ DSAM — Dynamic Session & Anti-Theft Monitor
app.include_router(developer_portal.router)      # 🔧 Developer Portal — Apps & Agreement Flows


# ── CORS Cache Refresh endpoint ──
@app.post("/api/admin/cors/refresh", tags=["Admin"])
async def cors_refresh(request: Request, access_token: str = Cookie(None)):
    """Force refresh CORS allowed origins from DB."""
    _require_admin_base(request, access_token)
    refresh_cors_cache()
    return {"message": "CORS cache refreshed"}


# ── Startup log ──
_env_info = get_env_info()
logger.info(f"🚀 ERP Core starting — ERP_ENV={_env_info['erp_env']} | env_file={ACTIVE_ENV_FILE}")
logger.info(f"   DB → {_env_info['database_host']}/{_env_info['database_name']} | Stripe={_env_info['stripe_mode']}")


@app.get("/api/env")
async def env_info(request: Request, access_token: str = Cookie(None)):
    """Returns authenticated environment metadata without infrastructure internals."""
    _require_admin_base(request, access_token)
    return {
        "erp_env": _env_info["erp_env"],
        "environment": ENVIRONMENT,
        "stripe_mode": _env_info["stripe_mode"],
        "app_url": APP_URL,
        "security": {
            "https_enforced": FORCE_HTTPS,
            "waf_enabled": ENABLE_WAF,
        },
    }


@app.get("/health")
async def health_check():
    """Public health check endpoint with no infrastructure disclosure."""
    return {
        "sentry_test": 1/0 if os.getenv("SENTRY_DSN") else "no-dsn", "status": "healthy",
        "version": "2.0.0",
        "sentry_test": 1/0 if os.getenv("SENTRY_DSN") else "no-dsn",
    }


# ── SPA Catch-All (SvelteKit file-based routing) ──
# A route-based catch-all ({full_path:path}) does NOT work in FastAPI when
# there is an app.mount() for StaticFiles because Starlette resolves mounts
# before parameterised path routes.
# A BaseHTTPMiddleware also fails because Starlette returns 404 at the ASGI
# level before the response reaches the middleware dispatch.
# Solution: custom ASGI wrapper that intercepts 404 responses for SPA routes.
from .services.spa_shell import render_spa_shell as _render_spa  # noqa: E402

_SPA_SKIP_PREFIXES = (
    "/api/", "/static/", "/sajet-api-docs", "/sajet-api-redoc",
    "/openapi", "/health",
)

_SPA_ROUTES = {
    "/", "/dashboard", "/portal", "/partner-portal", "/customer-onboarding",
    "/accountant-portal", "/tenants", "/domains", "/infrastructure",
    "/billing", "/settings", "/logs", "/tunnels", "/roles", "/plans",
    "/clients", "/partners", "/leads", "/commissions", "/quotations",
    "/blueprints", "/seats", "/invoices", "/settlements", "/reconciliation",
    "/dispersion", "/workorders", "/audit", "/branding", "/catalog",
    "/onboarding-config", "/communications", "/reports", "/admin-users",
    "/agreements", "/testimonials", "/landing-sections", "/translations",
    "/migrations", "/accountants", "/partner-signup", "/onboarding-access",
    "/developer-portal", "/api-keys", "/stripe-connect", "/quotas",
    "/recover-account", "/about", "/privacy", "/terms", "/data-processing",
    "/security", "/sla", "/login", "/signup", "/pricing",
    "/session-monitoring", "/neural-users",
}


def _is_spa_path(path: str) -> bool:
    """Check if a URL path should be handled by the SPA router."""
    if any(path.startswith(p) for p in _SPA_SKIP_PREFIXES):
        return False
    return path in _SPA_ROUTES or path.startswith("/plt/")


class _SPAFallbackASGI:
    """ASGI wrapper that intercepts 404s for SPA paths."""

    def __init__(self, app_inner):
        self.app = app_inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("method", "GET") != "GET":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")
        if not _is_spa_path(path):
            await self.app(scope, receive, send)
            return

        # Buffer the response to check status code
        response_started = False
        response_completed = False
        status_code = 200
        initial_message = None

        async def send_wrapper(message):
            nonlocal response_started, response_completed, status_code, initial_message

            # Once we've sent a complete SPA replacement, ignore further messages
            if response_completed:
                return

            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                if status_code == 404:
                    # Don't send the 404 — we'll replace it
                    initial_message = message
                    return
                response_started = True
                await send(message)

            elif message["type"] == "http.response.body":
                if status_code == 404 and not response_started:
                    # Replace 404 with SPA shell
                    route_name = path.strip("/").split("/")[0] or "landing"
                    spa_response = _render_spa(route_name)
                    body_bytes = spa_response.body

                    await send({
                        "type": "http.response.start",
                        "status": 200,
                        "headers": [
                            [b"content-type", b"text/html; charset=utf-8"],
                            [b"content-length", str(len(body_bytes)).encode()],
                        ],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": body_bytes,
                        "more_body": False,
                    })
                    response_completed = True
                    return
                await send(message)

        await self.app(scope, receive, send_wrapper)


# Wrap the entire ASGI app
app = _SPAFallbackASGI(app)  # type: ignore[assignment]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4443)
