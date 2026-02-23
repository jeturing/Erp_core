"""
Accountant Portal API — Endpoints para contadores/CPA con acceso multi-empresa.

Flujo:
1. Contador se registra como is_accountant=true
2. Admin o cliente le otorga acceso a tenants via AccountantTenantAccess
3. Contador ve lista de empresas en su dashboard
4. Contador puede "switch" entre empresas emitiendo un nuevo JWT

Endpoints:
- GET  /api/accountant/tenants          → Lista empresas asignadas
- POST /api/accountant/switch-tenant    → Emitir nuevo JWT con otro tenant_id
- GET  /api/accountant/dashboard        → KPIs consolidados multi-empresa
- POST /api/accountant/invite-client    → Invitar un cliente a dar acceso
"""

from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from ..models.database import (
    Customer, AccountantTenantAccess, AccountantAccessLevel,
    Subscription, SubscriptionStatus, SessionLocal,
)
from ..routes.secure_auth import TokenManager
from ..security.tokens import RefreshTokenManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accountant", tags=["Accountant Portal"])


# ═══════════════════════════════════════════
#  AUTH HELPERS
# ═══════════════════════════════════════════

def _extract_token(request: Request, access_token: Optional[str] = None) -> str:
    token = access_token or request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "No autenticado")
    return token


def _require_accountant(request: Request, access_token: str = Cookie(None)) -> dict:
    """Valida que el usuario sea un contador registrado."""
    token = _extract_token(request, access_token)
    try:
        payload = TokenManager.verify_access_token(token)
    except Exception:
        raise HTTPException(401, "Token inválido")

    # Verificar que sea tenant y accountant
    db = SessionLocal()
    try:
        user_id = payload.get("user_id") or payload.get("tenant_id")
        if not user_id:
            raise HTTPException(403, "Acceso denegado")

        customer = db.query(Customer).filter(Customer.id == int(user_id)).first()
        if not customer:
            raise HTTPException(404, "Usuario no encontrado")

        is_accountant = getattr(customer, "is_accountant", False)
        if not is_accountant:
            raise HTTPException(403, "Este endpoint es solo para contadores registrados")

        return {
            "user_id": customer.id,
            "email": customer.email,
            "role": payload.get("role", "tenant"),
            "payload": payload,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════
#  DTOs
# ═══════════════════════════════════════════

class SwitchTenantRequest(BaseModel):
    tenant_id: int


class InviteClientRequest(BaseModel):
    client_email: str
    access_level: str = "readonly"    # readonly, readwrite, full
    notes: Optional[str] = None


# ═══════════════════════════════════════════
#  GET /api/accountant/tenants
# ═══════════════════════════════════════════

@router.get("/tenants")
async def list_accountant_tenants(request: Request, access_token: str = Cookie(None)):
    """
    Lista todas las empresas a las que el contador tiene acceso.
    Incluye datos de suscripción y estado.
    """
    user = _require_accountant(request, access_token)
    db = SessionLocal()
    try:
        accesses = db.query(AccountantTenantAccess).filter(
            AccountantTenantAccess.accountant_id == user["user_id"],
            AccountantTenantAccess.is_active == True,
        ).all()

        tenants = []
        for access in accesses:
            tenant = db.query(Customer).filter(Customer.id == access.tenant_id).first()
            if not tenant:
                continue

            # Obtener suscripción activa
            subscription = db.query(Subscription).filter(
                Subscription.customer_id == tenant.id,
                Subscription.status == SubscriptionStatus.active,
            ).first()

            tenants.append({
                "tenant_id": tenant.id,
                "company_name": tenant.company_name,
                "email": tenant.email,
                "subdomain": tenant.subdomain,
                "status": tenant.status.value if tenant.status else "unknown",
                "access_level": access.access_level.value,
                "granted_at": access.granted_at.isoformat() if access.granted_at else None,
                "plan": subscription.plan_name if subscription else None,
                "user_count": tenant.user_count,
                "url": f"https://{tenant.subdomain}.sajet.us",
            })

        return {
            "tenants": tenants,
            "total": len(tenants),
            "accountant": {
                "id": user["user_id"],
                "email": user["email"],
            }
        }
    finally:
        db.close()


# ═══════════════════════════════════════════
#  POST /api/accountant/switch-tenant
# ═══════════════════════════════════════════

@router.post("/switch-tenant")
async def switch_tenant(
    payload: SwitchTenantRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """
    Emite un nuevo JWT válido para un tenant específico.
    Verifica que el contador tenga acceso al tenant solicitado.
    El token actual se invalida y se emite uno nuevo.
    """
    user = _require_accountant(request, access_token)
    db = SessionLocal()
    try:
        # Verificar acceso al tenant solicitado
        access = db.query(AccountantTenantAccess).filter(
            AccountantTenantAccess.accountant_id == user["user_id"],
            AccountantTenantAccess.tenant_id == payload.tenant_id,
            AccountantTenantAccess.is_active == True,
        ).first()

        if not access:
            raise HTTPException(403, "No tienes acceso a esta empresa")

        # Verificar que el tenant existe y está activo
        tenant = db.query(Customer).filter(Customer.id == payload.tenant_id).first()
        if not tenant:
            raise HTTPException(404, "Empresa no encontrada")

        # Emitir nuevo JWT con el tenant_id del cliente
        new_token = TokenManager.create_access_token(
            subject=user["email"],
            role="tenant",
            user_id=user["user_id"],
            tenant_id=payload.tenant_id,
            extra_claims={
                "is_accountant": True,
                "accountant_id": user["user_id"],
                "access_level": access.access_level.value,
            }
        )

        logger.info(
            f"Accountant {user['email']} switched to tenant {tenant.company_name} "
            f"(id={payload.tenant_id}, access={access.access_level.value})"
        )

        return {
            "message": f"Switched to {tenant.company_name}",
            "access_token": new_token,
            "tenant": {
                "id": tenant.id,
                "company_name": tenant.company_name,
                "subdomain": tenant.subdomain,
                "url": f"https://{tenant.subdomain}.sajet.us",
            },
            "access_level": access.access_level.value,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/accountant/dashboard
# ═══════════════════════════════════════════

@router.get("/dashboard")
async def accountant_dashboard(request: Request, access_token: str = Cookie(None)):
    """
    Dashboard consolidado del contador con KPIs de todas sus empresas.
    """
    user = _require_accountant(request, access_token)
    db = SessionLocal()
    try:
        accesses = db.query(AccountantTenantAccess).filter(
            AccountantTenantAccess.accountant_id == user["user_id"],
            AccountantTenantAccess.is_active == True,
        ).all()

        total_tenants = len(accesses)
        active_tenants = 0
        total_users = 0

        for access in accesses:
            tenant = db.query(Customer).filter(Customer.id == access.tenant_id).first()
            if tenant:
                if tenant.status and tenant.status.value == "active":
                    active_tenants += 1
                total_users += tenant.user_count or 0

        return {
            "kpis": {
                "total_clients": total_tenants,
                "active_clients": active_tenants,
                "total_users_managed": total_users,
            },
            "accountant": {
                "id": user["user_id"],
                "email": user["email"],
            }
        }
    finally:
        db.close()


# ═══════════════════════════════════════════
#  POST /api/accountant/invite-client
# ═══════════════════════════════════════════

@router.post("/invite-client")
async def invite_client(
    payload: InviteClientRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """
    Un contador puede solicitar acceso a un cliente existente.
    Crea un registro pendiente en AccountantTenantAccess.
    El admin o el cliente deben aprobar.
    """
    user = _require_accountant(request, access_token)
    db = SessionLocal()
    try:
        # Buscar cliente por email
        client = db.query(Customer).filter(
            Customer.email == payload.client_email,
        ).first()

        if not client:
            raise HTTPException(404, f"No se encontró cliente con email '{payload.client_email}'")

        # Verificar que no exista ya el acceso
        existing = db.query(AccountantTenantAccess).filter(
            AccountantTenantAccess.accountant_id == user["user_id"],
            AccountantTenantAccess.tenant_id == client.id,
        ).first()

        if existing:
            if existing.is_active:
                raise HTTPException(400, "Ya tienes acceso a esta empresa")
            # Reactivar
            existing.is_active = True
            existing.revoked_at = None
            existing.access_level = AccountantAccessLevel(payload.access_level)
            existing.notes = payload.notes
            db.commit()
            return {"message": "Acceso reactivado", "tenant_id": client.id}

        # Crear acceso
        try:
            access_level = AccountantAccessLevel(payload.access_level)
        except ValueError:
            access_level = AccountantAccessLevel.readonly

        access = AccountantTenantAccess(
            accountant_id=user["user_id"],
            tenant_id=client.id,
            access_level=access_level,
            granted_by=user["email"],
            notes=payload.notes,
        )
        db.add(access)
        db.commit()

        logger.info(f"Accountant {user['email']} granted {access_level.value} access to tenant {client.company_name}")

        return {
            "message": f"Acceso otorgado a {client.company_name}",
            "tenant_id": client.id,
            "access_level": access_level.value,
        }
    finally:
        db.close()
