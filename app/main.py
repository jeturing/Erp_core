"""
Main application entry point
Onboarding System API - Modular architecture with production security
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import routers
from .routes import auth, dashboard, tenants, onboarding, roles, tenant_portal, secure_auth, nodes, tunnels, provisioning, settings

# Import security middleware
from .security.middleware import SecurityMiddleware, WAFMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
ENABLE_WAF = os.getenv("ENABLE_WAF", "true").lower() == "true"

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
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:4443,https://sajet.us").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "security": {
            "https_enforced": FORCE_HTTPS,
            "waf_enabled": ENABLE_WAF
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4443)
