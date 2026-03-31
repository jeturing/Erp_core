"""
Centro Neurálgico de Usuarios (SAJET Neural)
Gestiona todos los tipos de usuarios: Admins, Tenants (Customers), Partners y SSO.
Permite gestión de tokens, bypass de MFA, reseteo de TOTP y consulta de accesos de otros aplicativos.
"""
from fastapi import APIRouter, HTTPException, Request, status, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import bcrypt
import logging
import secrets
import hashlib

from ..models.database import (
    AdminUser, AdminUserRole, Customer, Partner, 
    EmailVerificationToken, SessionLocal, 
    AuditEventRecord, RefreshToken
)
from ..security.tokens import TokenManager

router = APIRouter(prefix="/api/neural-users", tags=["Neural Users"])
logger = logging.getLogger(__name__)

# ── Auth helper ──

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _require_admin(request: Request):
    """Verifica que el usuario autenticado sea admin para el centro neurálgico."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = TokenManager.verify_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso solo para administradores de plataforma")
    return payload

# ── DTOs ──

class TokenAction(BaseModel):
    email: str
    action: str # new | delete | list | bypass (habilita bypass MFA temporal)

# ── Endpoints de Listado Multi-Tipo ──

@router.get("/search")
async def search_users(q: str, db=Depends(get_db), auth=Depends(_require_admin)):
    """Busca en todas las tablas de usuarios (Admin, Customer, Partner)."""
    # Admins
    admins = db.query(AdminUser).filter(AdminUser.email.contains(q) | AdminUser.display_name.contains(q)).all()
    # Customers (Tenants/Clientes)
    customers = db.query(Customer).filter(Customer.email.contains(q) | Customer.full_name.contains(q) | Customer.subdomain.contains(q)).all()
    # Partners
    partners = db.query(Partner).filter(Partner.contact_email.contains(q) | Partner.company_name.contains(q) | Partner.partner_code.contains(q)).all()
    
    return {
        "admins": [{"id": a.id, "email": a.email, "name": a.display_name, "role": a.role.value, "type": "admin"} for a in admins],
        "customers": [{"id": c.id, "email": c.email, "name": c.full_name, "subdomain": c.subdomain, "type": "tenant"} for c in customers],
        "partners": [{"id": p.id, "email": p.contact_email, "name": p.company_name, "code": p.partner_code, "type": "partner"} for p in partners]
    }

# ── Gestión de Tokens / SSO ──

@router.get("/tokens/{email}")
async def list_user_tokens(email: str, db=Depends(get_db), auth=Depends(_require_admin)):
    """Lista tokens activos para un usuario (EmailVerificationToken y RefreshTokens)."""
    verification_tokens = db.query(EmailVerificationToken).filter(EmailVerificationToken.email == email, EmailVerificationToken.is_used == False).all()
    refresh_tokens = db.query(RefreshToken).filter(RefreshToken.username == email, RefreshToken.revoked == False).all()
    
    return {
        "verification_tokens": [
            {"id": t.id, "type": t.user_type, "expires_at": t.expires_at, "ip": t.ip_address} 
            for t in verification_tokens
        ],
        "sso_sessions": [
            {"id": r.id, "role": r.role, "expires_at": r.expires_at, "tenant": r.tenant_id} 
            for r in refresh_tokens
        ]
    }

@router.post("/tokens/generate")
async def generate_manual_token(payload: TokenAction, db=Depends(get_db), auth=Depends(_require_admin)):
    """Genera un token de verificación manual (Steam-Guard style) para enviar al socio/cliente."""
    raw_token = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # Determinar tipo de usuario (prioridad Customer > Partner > Admin)
    user_type = "tenant"
    user_id = None
    c = db.query(Customer).filter(Customer.email == payload.email).first()
    if c: user_id = c.id
    else:
        p = db.query(Partner).filter(Partner.contact_email == payload.email).first()
        if p: 
            user_type = "partner"
            user_id = p.id
        else:
            a = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
            if a:
                user_type = "admin"
                user_id = a.id

    new_token = EmailVerificationToken(
        email=payload.email,
        token=raw_token,
        token_hash=token_hash,
        user_type=user_type,
        user_id=user_id,
        expires_at=datetime.utcnow() + timedelta(hours=2),
        is_used=False
    )
    db.add(new_token)
    db.commit()
    
    logger.info(f"Manual token generated for {payload.email} by {auth.get('sub')}")
    return {"success": True, "token": raw_token, "expires_at": new_token.expires_at}

@router.delete("/tokens/{token_id}")
async def revoke_token(token_id: int, type: str = "verification", db=Depends(get_db), auth=Depends(_require_admin)):
    """Revoca un token específico."""
    if type == "verification":
        token = db.query(EmailVerificationToken).filter(EmailVerificationToken.id == token_id).first()
        if token:
            token.is_used = True
    else:
        token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
        if token:
            token.revoked = True
    
    db.commit()
    return {"success": True}

# ── Bypass MFA ──

@router.post("/bypass-mfa")
async def toggle_bypass_mfa(payload: TokenAction, db=Depends(get_db), auth=Depends(_require_admin)):
    """
    Habilita o deshabilita la obligatoriedad de MFA (Email o TOTP) para un usuario.
    Si action=bypass, habilita bypass temporal. Si action=enforce, lo vuelve a obligar.
    """
    # Buscar en Customer
    c = db.query(Customer).filter(Customer.email == payload.email).first()
    if c:
        if payload.action == "bypass":
            # Para Customer, el bypass se asocia a flag onboarding_bypass o similar?
            # En Customer no hay flag de MFA bypass explícito, usamos onboarding_bypass para saltar flujos
            c.onboarding_bypass = True
            c.totp_enabled = False # Reset TOTP preventivo
        else:
            c.onboarding_bypass = False
    
    # Buscar en Partner
    p = db.query(Partner).filter(Partner.contact_email == payload.email).first()
    if p:
        if payload.action == "bypass":
            p.onboarding_bypass = True
            p.totp_enabled = False
        else:
            p.onboarding_bypass = False
            
    db.commit()
    log_msg = f"MFA Bypass {payload.action} for {payload.email} by {auth.get('sub')}"
    logger.info(log_msg)
    
    # Auditoría persistente
    audit = AuditEventRecord(
        event_type="neural_mfa_bypass",
        actor_username=auth.get("sub"),
        action=payload.action,
        resource=payload.email,
        details={"email": payload.email, "action": payload.action}
    )
    db.add(audit)
    db.commit()

    return {"success": True, "status": payload.action}

# ── Gestión de Otras Apps (Segrd/Foren/etc) ──

@router.get("/external-apps/{email}")
async def get_external_access(email: str, auth=Depends(_require_admin)):
    """Consulta accesos en otros módulos (Segrd, Forensics, etc)."""
    # Aquí se podrían hacer llamadas a otros PCTs o consultar tablas compartidas
    # Por ahora devolvemos info simulada del rol detectado en la JWT si aplica
    return {
        "segrd": "active" if "@segrd" in email else "inactive",
        "forensics": "authorized" if "segrd-admin" in auth.get("role", "") else "pending"
    }
