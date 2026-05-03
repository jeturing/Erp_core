"""
Admin Users Routes — CRUD para gestionar usuarios administrativos de la plataforma.
Permite crear admins, operadores y viewers que pueden loguearse con email.
Solo accesible por admin.
"""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
import bcrypt
import logging

from ..models.database import AdminUser, AdminUserRole, SessionLocal
from ..security.tokens import TokenManager

router = APIRouter(prefix="/api/admin-users", tags=["Admin Users"])
logger = logging.getLogger(__name__)


# ── Auth helper ──

def _require_admin(request: Request):
    """Verifica que el usuario autenticado sea admin."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = TokenManager.verify_access_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acceso solo para administradores")
    return payload


# ── DTOs ──

class AdminUserCreate(BaseModel):
    email: str
    password: str
    display_name: str
    role: str = "admin"  # admin | operator | viewer | segrd-admin | segrd-user
    notes: Optional[str] = None


class AdminUserUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    new_password: Optional[str] = None


# ── Helpers ──

def _user_to_dict(u: AdminUser) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "display_name": u.display_name,
        "role": u.role.value if u.role else "admin",
        "is_active": u.is_active,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "login_count": u.login_count or 0,
        "notes": u.notes,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
        "created_by": u.created_by,
    }


# ── Endpoints ──

@router.get("")
async def list_admin_users(request: Request):
    """Lista todos los usuarios administrativos."""
    _require_admin(request)
    db = SessionLocal()
    try:
        users = db.query(AdminUser).order_by(AdminUser.created_at.asc()).all()
        return {
            "items": [_user_to_dict(u) for u in users],
            "total": len(users),
        }
    finally:
        db.close()


@router.get("/{user_id}")
async def get_admin_user(user_id: int, request: Request):
    """Obtiene un usuario admin por ID."""
    _require_admin(request)
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return _user_to_dict(user)
    finally:
        db.close()


@router.post("")
async def create_admin_user(payload: AdminUserCreate, request: Request):
    """Crea un nuevo usuario administrativo."""
    actor = _require_admin(request)
    db = SessionLocal()
    try:
        # Verificar email único
        existing = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Ya existe un usuario con email {payload.email}")

        # Validar rol
        try:
            role_enum = AdminUserRole(payload.role)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Rol inválido: {payload.role}. "
                    "Valores válidos: admin, operator, viewer, segrd-admin, segrd-user"
                ),
            )

        # Hash password
        pw_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()

        user = AdminUser(
            email=payload.email,
            password_hash=pw_hash,
            display_name=payload.display_name,
            role=role_enum,
            is_active=True,
            notes=payload.notes,
            created_by=actor.get("sub", "admin"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Admin user created: {payload.email} (role={payload.role}) by {actor.get('sub')}")
        return _user_to_dict(user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.put("/{user_id}")
async def update_admin_user(user_id: int, payload: AdminUserUpdate, request: Request):
    """Actualiza un usuario administrativo."""
    _require_admin(request)
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if payload.display_name is not None:
            user.display_name = payload.display_name

        if payload.role is not None:
            try:
                user.role = AdminUserRole(payload.role)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Rol inválido: {payload.role}")

        if payload.is_active is not None:
            user.is_active = payload.is_active

        if payload.notes is not None:
            user.notes = payload.notes

        if payload.new_password:
            user.password_hash = bcrypt.hashpw(payload.new_password.encode(), bcrypt.gensalt()).decode()

        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(user)

        logger.info(f"Admin user updated: {user.email} (id={user_id})")
        return _user_to_dict(user)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating admin user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.delete("/{user_id}")
async def delete_admin_user(user_id: int, request: Request):
    """Desactiva (soft delete) un usuario administrativo."""
    actor = _require_admin(request)
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # No permitir auto-eliminación
        if actor.get("sub") == user.email:
            raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")

        user.is_active = False
        user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        logger.info(f"Admin user deactivated: {user.email} (id={user_id}) by {actor.get('sub')}")
        return {"message": f"Usuario {user.email} desactivado", "id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
