"""
Main application entry point
Onboarding System API - Modular architecture
"""
from fastapi import FastAPI
import logging

# Import routers
from .routes import auth, dashboard, tenants, onboarding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Onboarding System API",
    description="Sistema de onboarding automático con integración de Stripe y Odoo",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(tenants.router)
app.include_router(onboarding.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4443)
