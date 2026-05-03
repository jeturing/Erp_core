"""
Centro Neurálgico de Usuarios (SAJET Neural)
Gestiona todos los tipos de usuarios: Admins, Tenants (Customers), Partners y SSO.
Permite gestión de tokens, bypass de MFA, reseteo de TOTP y consulta de accesos de otros aplicativos.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, timedelta, timezone
import logging
import secrets
import hashlib

from ..models.database import (
    AdminUser, Customer, Partner,
    EmailVerificationToken, SessionLocal, 
    AuditEventRecord, RefreshToken
)
from ..security.tokens import TokenManager, RefreshTokenManager

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
    try:
        payload = TokenManager.verify_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso solo para administradores de plataforma")
    return payload

# ── DTOs ──

class GenerateTokenPayload(BaseModel):
    user_type: Optional[Literal["admin", "customer", "tenant", "partner"]] = None
    user_id: Optional[int] = None
    token_type: Literal["verification", "refresh"] = "verification"
    # Compatibilidad legacy
    email: Optional[str] = None


class BypassMfaPayload(BaseModel):
    user_type: Optional[Literal["admin", "customer", "tenant", "partner"]] = None
    user_id: Optional[int] = None
    enabled: Optional[bool] = None
    # Compatibilidad legacy
    email: Optional[str] = None
    action: Optional[str] = None


def _normalize_user_type(user_type: str) -> str:
    if user_type == "tenant":
        return "customer"
    return user_type


def _resolve_user(db, user_type: str, user_id: int):
    normalized = _normalize_user_type(user_type)

    if normalized == "admin":
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    elif normalized == "customer":
        user = db.query(Customer).filter(Customer.id == user_id).first()
    elif normalized == "partner":
        user = db.query(Partner).filter(Partner.id == user_id).first()
    else:
        raise HTTPException(status_code=400, detail="Tipo de usuario inválido")

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return normalized, user


def _user_email(user_type: str, user) -> str:
    if user_type == "admin":
        return user.email
    if user_type == "customer":
        return user.email
    return user.contact_email


def _build_tokens_payload(db, email: str):
    verification_tokens = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.email == email,
        EmailVerificationToken.is_used == False,
    ).all()
    refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.username == email,
        RefreshToken.revoked == False,
    ).all()

    data = [
        {
            "id": t.id,
            "type": "verification",
            "token": t.token,
            "identifier": t.email,
            "expires_at": t.expires_at,
            "created_at": t.created_at,
        }
        for t in verification_tokens
    ]

    data.extend(
        [
            {
                "id": r.id,
                "type": "refresh",
                "token": "••••••••",
                "identifier": r.username,
                "expires_at": r.expires_at,
                "created_at": r.created_at,
            }
            for r in refresh_tokens
        ]
    )

    data.sort(key=lambda item: item["created_at"] or datetime.min, reverse=True)
    return data

# ── Endpoints de Listado Multi-Tipo ──

@router.get("/search")
async def search_users(q: str, db=Depends(get_db), auth=Depends(_require_admin)):
    """Busca en todas las tablas de usuarios (Admin, Customer, Partner)."""
    query = q.strip()
    if not query:
        return {"success": True, "data": [], "meta": {"count": 0, "query": ""}}

    # Admins
    admins = db.query(AdminUser).filter(AdminUser.email.contains(query) | AdminUser.display_name.contains(query)).all()
    # Customers (Tenants/Clientes)
    customers = db.query(Customer).filter(Customer.email.contains(query) | Customer.full_name.contains(query) | Customer.subdomain.contains(query)).all()
    # Partners
    partners = db.query(Partner).filter(Partner.contact_email.contains(query) | Partner.company_name.contains(query) | Partner.partner_code.contains(query)).all()

    data = [
        {
            "id": a.id,
            "email": a.email,
            "display_name": a.display_name,
            "type": "admin",
            "role": a.role,
            "is_active": a.is_active,
            "onboarding_bypass": False,
            "totp_enabled": False,
            "last_login_at": a.last_login_at,
            "created_at": a.created_at,
        }
        for a in admins
    ]

    data.extend(
        [
            {
                "id": c.id,
                "email": c.email,
                "display_name": c.full_name,
                "type": "customer",
                "role": "tenant",
                "is_active": c.status.value == "active" if c.status else True,
                "onboarding_bypass": c.onboarding_bypass,
                "totp_enabled": c.totp_enabled,
                "last_login_at": None,
                "created_at": c.created_at,
            }
            for c in customers
        ]
    )

    data.extend(
        [
            {
                "id": p.id,
                "email": p.contact_email,
                "display_name": p.company_name,
                "type": "partner",
                "role": p.status.value if p.status else "partner",
                "is_active": p.status.value == "active" if p.status else True,
                "onboarding_bypass": p.onboarding_bypass,
                "totp_enabled": p.totp_enabled,
                "last_login_at": p.last_login_at,
                "created_at": p.created_at,
            }
            for p in partners
        ]
    )

    return {
        "success": True,
        "data": data,
        "meta": {
            "count": len(data),
            "query": query,
        },
    }

# ── Gestión de Tokens / SSO ──

@router.get("/tokens/{user_type}/{user_id}")
async def list_user_tokens(user_type: str, user_id: int, db=Depends(get_db), auth=Depends(_require_admin)):
    """Lista tokens activos para un usuario por tipo e id (contrato frontend)."""
    normalized, user = _resolve_user(db, user_type, user_id)
    email = _user_email(normalized, user)
    data = _build_tokens_payload(db, email)

    return {
        "success": True,
        "data": data,
        "meta": {
            "email": email,
            "count": len(data),
        },
    }


@router.get("/tokens/{email}")
async def list_user_tokens_legacy(email: str, db=Depends(get_db), auth=Depends(_require_admin)):
    """Compatibilidad legacy: lista tokens por email."""
    data = _build_tokens_payload(db, email)
    return {
        "success": True,
        "data": data,
        "meta": {
            "email": email,
            "count": len(data),
            "legacy": True,
        },
    }

@router.post("/tokens/generate")
async def generate_manual_token(payload: GenerateTokenPayload, db=Depends(get_db), auth=Depends(_require_admin)):
    """Genera token de verificación o refresh usando user_type+user_id (o email legacy)."""
    email = payload.email
    normalized_user_type = "customer"
    user_id = None

    if payload.user_type and payload.user_id:
        normalized_user_type, user = _resolve_user(db, payload.user_type, payload.user_id)
        email = _user_email(normalized_user_type, user)
        user_id = payload.user_id

    if not email:
        raise HTTPException(status_code=422, detail="Debe enviar user_type+user_id o email")

    if payload.token_type == "refresh":
        refresh_token, expires_at = RefreshTokenManager.create_refresh_token(
            username=email,
            role=normalized_user_type,
            user_id=user_id,
            tenant_id=user_id if normalized_user_type == "customer" else None,
        )
        logger.info(f"Refresh token generated for {email} by {auth.get('sub')}")
        return {
            "success": True,
            "data": {
                "type": "refresh",
                "token": refresh_token,
                "expires_at": expires_at,
            },
            "meta": {
                "email": email,
            },
        }

    raw_token = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    token_user_type = "tenant" if normalized_user_type == "customer" else normalized_user_type
    new_token = EmailVerificationToken(
        email=email,
        token=raw_token,
        token_hash=token_hash,
        user_type=token_user_type,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=2),
        is_used=False,
    )
    db.add(new_token)
    db.commit()

    logger.info(f"Verification token generated for {email} by {auth.get('sub')}")
    return {
        "success": True,
        "data": {
            "type": "verification",
            "token": raw_token,
            "expires_at": new_token.expires_at,
        },
        "meta": {
            "email": email,
        },
    }


def _revoke_token_internal(db, token_id: int):
    verification = db.query(EmailVerificationToken).filter(EmailVerificationToken.id == token_id).first()
    if verification:
        verification.is_used = True
        db.commit()
        return "verification"

    refresh = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if refresh:
        refresh.revoked = True
        db.commit()
        return "refresh"

    raise HTTPException(status_code=404, detail="Token no encontrado")


@router.post("/tokens/revoke/{token_id}")
async def revoke_token_post(token_id: int, db=Depends(get_db), auth=Depends(_require_admin)):
    """Revoca token por id (contrato frontend)."""
    revoked_type = _revoke_token_internal(db, token_id)
    return {
        "success": True,
        "data": {
            "token_id": token_id,
            "type": revoked_type,
            "revoked": True,
        },
        "meta": {},
    }

@router.delete("/tokens/{token_id}")
async def revoke_token(token_id: int, type: str = "verification", db=Depends(get_db), auth=Depends(_require_admin)):
    """Compatibilidad legacy: revoca token por DELETE."""
    revoked_type = _revoke_token_internal(db, token_id)
    return {
        "success": True,
        "data": {
            "token_id": token_id,
            "type": revoked_type,
            "revoked": True,
        },
        "meta": {
            "legacy": True,
        },
    }

# ── Bypass MFA ──

@router.post("/bypass-mfa")
async def toggle_bypass_mfa(payload: BypassMfaPayload, db=Depends(get_db), auth=Depends(_require_admin)):
    """
    Habilita o deshabilita bypass MFA/Onboarding por user_type + user_id.
    También soporta payload legacy por email + action.
    """
    target_user = None
    normalized_user_type = None

    if payload.user_type and payload.user_id:
        normalized_user_type, target_user = _resolve_user(db, payload.user_type, payload.user_id)
    elif payload.email:
        target_user = db.query(Customer).filter(Customer.email == payload.email).first()
        normalized_user_type = "customer"
        if not target_user:
            target_user = db.query(Partner).filter(Partner.contact_email == payload.email).first()
            normalized_user_type = "partner"
        if not target_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    else:
        raise HTTPException(status_code=422, detail="Debe enviar user_type+user_id o email")

    current_state = bool(getattr(target_user, "onboarding_bypass", False))
    if payload.enabled is not None:
        next_state = payload.enabled
    elif payload.action in {"bypass", "enforce"}:
        next_state = payload.action == "bypass"
    else:
        next_state = not current_state

    target_user.onboarding_bypass = next_state
    if next_state and hasattr(target_user, "totp_enabled"):
        target_user.totp_enabled = False

    email = _user_email(normalized_user_type, target_user)

    audit = AuditEventRecord(
        event_type="neural_mfa_bypass",
        actor_username=auth.get("sub"),
        action="bypass" if next_state else "enforce",
        resource=email,
        details={
            "email": email,
            "user_type": normalized_user_type,
            "user_id": target_user.id,
            "previous_state": current_state,
            "new_state": next_state,
        }
    )
    db.add(audit)
    db.commit()

    logger.info(f"MFA bypass set to {next_state} for {email} by {auth.get('sub')}")

    return {
        "success": True,
        "data": {
            "email": email,
            "user_type": normalized_user_type,
            "user_id": target_user.id,
            "onboarding_bypass": next_state,
        },
        "meta": {},
    }

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
