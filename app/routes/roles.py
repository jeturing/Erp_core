"""
Role-based authentication - Admin y Tenant user roles
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
import jwt
import os

from fastapi import APIRouter, Cookie, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..models.database import Customer, SessionLocal, SystemConfig
from ..services.spa_shell import render_spa_shell

router = APIRouter(tags=["Roles"])

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
ROLES_CONFIG_KEY = "SPA_ROLES_JSON"

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

DEFAULT_ROLES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "admin",
        "description": "Acceso total a la plataforma",
        "permissions": ["*"],
        "system": True,
        "updated_at": None,
    },
    {
        "id": 2,
        "name": "operator",
        "description": "Operacion diaria de tenants y dominios",
        "permissions": ["tenants:read", "tenants:write", "domains:read", "domains:write", "nodes:read", "billing:read"],
        "system": True,
        "updated_at": None,
    },
    {
        "id": 3,
        "name": "viewer",
        "description": "Solo lectura",
        "permissions": ["dashboard:read", "tenants:read", "domains:read", "billing:read", "logs:read"],
        "system": True,
        "updated_at": None,
    },
    {
        "id": 4,
        "name": "tenant",
        "description": "Portal de cliente",
        "permissions": ["portal:read", "billing:self", "domains:self"],
        "system": True,
        "updated_at": None,
    },
]


# DTOs
class LoginRequest(BaseModel):
    email: str
    password: str
    role: str  # 'admin' o 'tenant'


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    role: str
    user_id: int = None
    tenant_id: int = None


class RolePayload(BaseModel):
    name: str
    description: str = ""
    permissions: List[str] = []


def create_access_token(username: str, role: str, user_id: int = None, tenant_id: int = None) -> str:
    """Crea un token JWT con informacion de rol."""
    payload = {
        "sub": username,
        "role": role,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token_with_role(token: str, required_role: str = None) -> dict:
    """Verifica un token JWT y retorna los datos del usuario."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        if required_role and payload.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: se requiere rol {required_role}",
            )

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )


def _extract_token(request: Request, access_token: Optional[str] = None) -> Optional[str]:
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    return token


def _require_admin(request: Request, access_token: Optional[str] = None) -> dict:
    token = _extract_token(request, access_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return verify_token_with_role(token, required_role="admin")


def _normalize_role(raw: Dict[str, Any], fallback_id: int) -> Dict[str, Any]:
    permissions = raw.get("permissions") or []
    if not isinstance(permissions, list):
        permissions = [str(permissions)]

    return {
        "id": int(raw.get("id", fallback_id)),
        "name": str(raw.get("name", f"role-{fallback_id}")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "permissions": [str(item).strip() for item in permissions if str(item).strip()],
        "system": bool(raw.get("system", False)),
        "updated_at": raw.get("updated_at"),
    }


def _load_roles(db) -> List[Dict[str, Any]]:
    config = db.query(SystemConfig).filter(SystemConfig.key == ROLES_CONFIG_KEY).first()

    if not config or not config.value:
        return [role.copy() for role in DEFAULT_ROLES]

    try:
        payload = json.loads(config.value)
        if not isinstance(payload, list):
            raise ValueError("Roles payload invalido")
        roles: List[Dict[str, Any]] = []
        for index, item in enumerate(payload, start=1):
            if isinstance(item, dict):
                roles.append(_normalize_role(item, index))
        if roles:
            return roles
    except Exception:
        # fallback para no bloquear administracion si el payload esta corrupto
        return [role.copy() for role in DEFAULT_ROLES]

    return [role.copy() for role in DEFAULT_ROLES]


def _save_roles(db, roles: List[Dict[str, Any]], updated_by: str) -> None:
    serialized = json.dumps(roles, ensure_ascii=True)
    config = db.query(SystemConfig).filter(SystemConfig.key == ROLES_CONFIG_KEY).first()

    if config:
        config.value = serialized
        config.updated_by = updated_by
    else:
        config = SystemConfig(
            key=ROLES_CONFIG_KEY,
            value=serialized,
            description="Catalogo de roles editable para la SPA",
            category="security",
            is_secret=False,
            is_editable=True,
            updated_by=updated_by,
        )
        db.add(config)

    db.commit()


# Routes
@router.get("/login/{role}", response_class=HTMLResponse)
async def role_login_page(request: Request, role: str):
    """Entrada publica de login unificado en SPA."""
    if role not in ["admin", "tenant"]:
        raise HTTPException(status_code=404, detail="Rol no valido")

    return render_spa_shell("login", {"loginRole": role})


@router.post("/api/logout")
async def logout():
    """Endpoint de logout que invalida la cookie."""
    response = JSONResponse(content={"message": "Sesion cerrada"})
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")  # Also clear refresh token
    response.delete_cookie(key="token", path="/")  # Backward compatibility
    return response


@router.get("/api/roles")
async def list_roles(request: Request, access_token: Optional[str] = Cookie(None)):
    """Lista de roles disponibles para administracion en SPA."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        roles = _load_roles(db)
        return {"items": roles, "total": len(roles)}
    finally:
        db.close()


@router.post("/api/roles")
async def create_role(payload: RolePayload, request: Request, access_token: Optional[str] = Cookie(None)):
    """Crea un rol personalizado."""
    auth_data = _require_admin(request, access_token)
    role_name = payload.name.strip().lower()
    if not role_name:
        raise HTTPException(status_code=400, detail="El nombre del rol es obligatorio")

    db = SessionLocal()
    try:
        roles = _load_roles(db)
        if any(role["name"].lower() == role_name for role in roles):
            raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre")

        max_id = max((int(role["id"]) for role in roles), default=99)
        new_role = {
            "id": max_id + 1,
            "name": role_name,
            "description": payload.description.strip(),
            "permissions": [perm.strip() for perm in payload.permissions if perm.strip()],
            "system": False,
            "updated_at": datetime.utcnow().isoformat(),
        }
        roles.append(new_role)

        _save_roles(db, roles, updated_by=auth_data.get("sub", "admin"))
        return {"success": True, "role": new_role}
    finally:
        db.close()


@router.put("/api/roles/{role_id}")
async def update_role(role_id: int, payload: RolePayload, request: Request, access_token: Optional[str] = Cookie(None)):
    """Actualiza metadata y permisos de un rol."""
    auth_data = _require_admin(request, access_token)
    role_name = payload.name.strip().lower()
    if not role_name:
        raise HTTPException(status_code=400, detail="El nombre del rol es obligatorio")

    db = SessionLocal()
    try:
        roles = _load_roles(db)
        target = next((role for role in roles if int(role["id"]) == role_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Rol no encontrado")

        duplicate = next(
            (
                role
                for role in roles
                if int(role["id"]) != role_id and role["name"].lower() == role_name
            ),
            None,
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre")

        target["name"] = role_name
        target["description"] = payload.description.strip()
        target["permissions"] = [perm.strip() for perm in payload.permissions if perm.strip()]
        target["updated_at"] = datetime.utcnow().isoformat()

        _save_roles(db, roles, updated_by=auth_data.get("sub", "admin"))
        return {"success": True, "role": target}
    finally:
        db.close()


# DEPRECATED ENDPOINTS REMOVED:
# - /api/login/unified -> Use /api/auth/login instead (secure_auth.py)
