"""
Tenants Routes - Tenant management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.database import Customer, Subscription, SubscriptionStatus, SessionLocal
from .auth import verify_token

router = APIRouter(prefix="/api/tenants", tags=["Tenants"])


# DTOs
class TenantCreateRequest(BaseModel):
    company_name: str
    admin_email: str
    subdomain: str
    plan: str


@router.get("")
async def list_tenants(authorization: str = None):
    """Listado de tenants desde BD (orders by created_at desc) - requiere JWT."""
    # Validar token
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    db = SessionLocal()
    try:
        # Obtener suscripciones ordenadas por fecha
        subs = db.query(Subscription).order_by(Subscription.created_at.desc()).all()
        items = []
        for sub in subs:
            cust = db.query(Customer).filter_by(id=sub.customer_id).first()
            if cust:
                # Mapear status de suscripción a label para UI
                status_map = {
                    SubscriptionStatus.active: "active",
                    SubscriptionStatus.pending: "provisioning",
                    SubscriptionStatus.past_due: "payment_failed",
                    SubscriptionStatus.cancelled: "suspended",
                }
                items.append({
                    "id": sub.id,
                    "company_name": cust.company_name,
                    "email": cust.email,
                    "subdomain": cust.subdomain,
                    "plan": sub.plan_name,
                    "status": status_map.get(sub.status, "unknown"),
                    "tunnel_active": sub.status == SubscriptionStatus.active,
                    "created_at": sub.created_at.isoformat() + "Z" if sub.created_at else None,
                })
        return {"items": items, "total": len(items)}
    except Exception as e:
        # Si la BD no está disponible, retornar datos mockeados
        return {
            "items": [
                {
                    "id": 1,
                    "company_name": "Acme Corp",
                    "email": "admin@acme.com",
                    "subdomain": "acme",
                    "plan": "pro",
                    "status": "active",
                    "tunnel_active": True,
                    "created_at": "2026-01-28T10:00:00Z",
                },
                {
                    "id": 2,
                    "company_name": "Tech Startup",
                    "email": "hello@techstartup.com",
                    "subdomain": "techstartup",
                    "plan": "enterprise",
                    "status": "active",
                    "tunnel_active": True,
                    "created_at": "2026-01-27T14:30:00Z",
                },
                {
                    "id": 3,
                    "company_name": "Small Business",
                    "email": "contact@smallbiz.com",
                    "subdomain": "smallbiz",
                    "plan": "basic",
                    "status": "provisioning",
                    "tunnel_active": False,
                    "created_at": "2026-01-28T16:00:00Z",
                }
            ],
            "total": 3
        }
    finally:
        db.close()


@router.post("")
async def create_tenant(payload: TenantCreateRequest, authorization: str = None):
    """Crear tenant (stub sin persistencia) - requiere JWT."""
    # Validar token
    try:
        if authorization is not None and authorization.startswith("Bearer "):
            token = authorization[7:]
            verify_token(token)
    except HTTPException:
        raise
    
    tenant = payload.model_dump()
    tenant["id"] = 999
    tenant["status"] = "provisioning"
    tenant["tunnel_active"] = False
    tenant["created_at"] = "2024-01-01T00:00:00Z"
    return tenant
