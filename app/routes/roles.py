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
from pydantic import BaseModel

from ..models.database import Customer, SessionLocal, SystemConfig
from ..services.spa_shell import render_spa_shell

from ..config import get_runtime_setting

router = APIRouter(tags=["Roles"])

# JWT Configuration
JWT_EXPIRATION_HOURS = 24
ROLES_CONFIG_KEY = "SPA_ROLES_JSON"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _jwt_secret_key() -> str:
    return get_runtime_setting("JWT_SECRET_KEY", "")


def _jwt_algorithm() -> str:
    return get_runtime_setting("JWT_ALGORITHM", "HS256")

# ── Catálogo maestro de permisos agrupados por módulo ──
PERMISSION_CATALOG: Dict[str, Dict[str, Any]] = {
    "dashboard": {
        "label": "Dashboard",
        "icon": "LayoutDashboard",
        "permissions": {
            "dashboard:read": "Ver métricas y resumen general",
        },
    },
    "tenants": {
        "label": "Tenants",
        "icon": "Building2",
        "permissions": {
            "tenants:read": "Ver lista de tenants",
            "tenants:write": "Crear y editar tenants",
            "tenants:delete": "Eliminar tenants",
            "tenants:assign": "Asignar tenants a usuarios/roles",
        },
    },
    "customers": {
        "label": "Clientes",
        "icon": "UserCheck",
        "permissions": {
            "customers:read": "Ver lista de clientes",
            "customers:write": "Editar datos de clientes",
            "customers:users": "Gestionar usuarios por cliente",
        },
    },
    "billing": {
        "label": "Facturación",
        "icon": "CreditCard",
        "permissions": {
            "billing:read": "Ver métricas de facturación",
            "billing:write": "Editar suscripciones y montos",
            "billing:self": "Ver solo su propia facturación",
        },
    },
    "plans": {
        "label": "Planes",
        "icon": "Package",
        "permissions": {
            "plans:read": "Ver planes disponibles",
            "plans:write": "Crear y editar planes",
            "plans:delete": "Eliminar planes",
        },
    },
    "domains": {
        "label": "Dominios",
        "icon": "Globe",
        "permissions": {
            "domains:read": "Ver dominios configurados",
            "domains:write": "Gestionar dominios y DNS",
            "domains:self": "Ver solo sus propios dominios",
        },
    },
    "nodes": {
        "label": "Infraestructura",
        "icon": "Server",
        "permissions": {
            "nodes:read": "Ver nodos y servidores",
            "nodes:write": "Gestionar nodos",
            "provisioning:execute": "Ejecutar aprovisionamiento",
        },
    },
    "tunnels": {
        "label": "Túneles",
        "icon": "Network",
        "permissions": {
            "tunnels:read": "Ver túneles Cloudflare",
            "tunnels:write": "Gestionar túneles",
        },
    },
    "settings": {
        "label": "Configuración",
        "icon": "Settings",
        "permissions": {
            "settings:read": "Ver configuraciones del sistema",
            "settings:write": "Modificar configuraciones",
        },
    },
    "logs": {
        "label": "Logs",
        "icon": "FileText",
        "permissions": {
            "logs:read": "Ver logs del sistema",
        },
    },
    "roles": {
        "label": "Roles",
        "icon": "Shield",
        "permissions": {
            "roles:read": "Ver roles definidos",
            "roles:write": "Crear y editar roles",
            "roles:delete": "Eliminar roles",
        },
    },
    "portal": {
        "label": "Portal Tenant",
        "icon": "ExternalLink",
        "permissions": {
            "portal:read": "Acceso al portal de cliente",
        },
    },
    "partners": {
        "label": "Partners",
        "icon": "Handshake",
        "permissions": {
            "partners:read": "Ver socios comerciales",
            "partners:write": "Crear y editar partners",
            "partners:delete": "Desactivar partners",
        },
    },
    "leads": {
        "label": "Leads",
        "icon": "Target",
        "permissions": {
            "leads:read": "Ver pipeline de prospectos",
            "leads:write": "Crear y editar leads",
            "leads:delete": "Eliminar leads",
        },
    },
    "commissions": {
        "label": "Comisiones",
        "icon": "Percent",
        "permissions": {
            "commissions:read": "Ver comisiones",
            "commissions:write": "Crear y aprobar comisiones",
            "commissions:pay": "Marcar comisiones como pagadas",
        },
    },
    "quotations": {
        "label": "Cotizaciones",
        "icon": "FileSpreadsheet",
        "permissions": {
            "quotations:read": "Ver cotizaciones",
            "quotations:write": "Crear y editar cotizaciones",
            "quotations:send": "Enviar cotizaciones",
            "quotations:delete": "Eliminar cotizaciones",
        },
    },
    "catalog": {
        "label": "Catálogo",
        "icon": "ShoppingBag",
        "permissions": {
            "catalog:read": "Ver catálogo de servicios",
            "catalog:write": "Editar catálogo y precios",
        },
    },
    "api_keys": {
        "label": "API Keys",
        "icon": "Key",
        "permissions": {
            "api_keys:read":    "Ver todas las API keys del sistema",
            "api_keys:write":   "Crear y editar API keys",
            "api_keys:rotate":  "Rotar API keys (genera nueva, invalida anterior)",
            "api_keys:delete":  "Revocar / eliminar API keys",
            "api_keys:self":    "Ver y gestionar solo sus propias API keys",
            "api_keys:billing": "Ver métricas de uso y facturación de API keys",
        },
    },
}

# Lista plana de todos los permisos válidos
ALL_PERMISSIONS = []
for module_data in PERMISSION_CATALOG.values():
    ALL_PERMISSIONS.extend(module_data["permissions"].keys())
ALL_PERMISSIONS.append("*")  # wildcard admin

DEFAULT_ROLES: List[Dict[str, Any]] = [
    {
        "id": 1,
        "name": "admin",
        "description": "Acceso total a la plataforma",
        "permissions": ["*"],
        "system": True,
        "updated_at": None,
        "color": "#e74c3c",
        "assigned_tenants": [],
        "assigned_users": [],
    },
    {
        "id": 2,
        "name": "operator",
        "description": "Operación diaria de tenants, clientes y dominios",
        "permissions": [
            "dashboard:read", "tenants:read", "tenants:write", "tenants:assign",
            "customers:read", "customers:write", "customers:users",
            "domains:read", "domains:write", "nodes:read", "billing:read",
            "plans:read", "tunnels:read", "logs:read",
        ],
        "system": True,
        "updated_at": None,
        "color": "#f39c12",
        "assigned_tenants": [],
        "assigned_users": [],
    },
    {
        "id": 3,
        "name": "viewer",
        "description": "Solo lectura de datos y métricas",
        "permissions": [
            "dashboard:read", "tenants:read", "customers:read",
            "domains:read", "billing:read", "plans:read", "logs:read",
        ],
        "system": True,
        "updated_at": None,
        "color": "#3498db",
        "assigned_tenants": [],
        "assigned_users": [],
    },
    {
        "id": 4,
        "name": "tenant",
        "description": "Portal de cliente – acceso limitado a su cuenta",
        "permissions": ["portal:read", "billing:self", "domains:self"],
        "system": True,
        "updated_at": None,
        "color": "#2ecc71",
        "assigned_tenants": [],
        "assigned_users": [],
    },
    {
        "id": 5,
        "name": "partner",
        "description": "Socio comercial – gestión de leads, comisiones y cotizaciones propias",
        "permissions": [
            "dashboard:read", "partners:read",
            "leads:read", "leads:write",
            "commissions:read",
            "quotations:read", "quotations:write", "quotations:send",
            "catalog:read", "billing:self",
        ],
        "system": True,
        "updated_at": None,
        "color": "#8e44ad",
        "assigned_tenants": [],
        "assigned_users": [],
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
    color: str = "#6b7280"
    assigned_tenants: List[int] = []
    assigned_users: List[int] = []


class RoleUserAssign(BaseModel):
    user_ids: List[int]


# ── Plantillas predefinidas para nuevos roles ──
ROLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "account_manager": {
        "name": "Account Manager",
        "description": "Gestiona clientes, suscripciones y facturación",
        "permissions": [
            "dashboard:read", "customers:read", "customers:write", "customers:users",
            "billing:read", "billing:write", "plans:read", "tenants:read",
        ],
        "color": "#9b59b6",
    },
    "support": {
        "name": "Soporte",
        "description": "Soporte técnico – lectura + gestión de tenants y rotación de API keys previa solicitud del tenant",
        "permissions": [
            "dashboard:read", "tenants:read", "tenants:write",
            "domains:read", "domains:write", "nodes:read",
            "tunnels:read", "logs:read", "customers:read",
            "api_keys:read", "api_keys:rotate",  # rotate solo con verify_token del tenant
        ],
        "color": "#1abc9c",
    },
    "billing_only": {
        "name": "Facturación",
        "description": "Solo acceso a facturación y planes",
        "permissions": [
            "billing:read", "billing:write", "plans:read", "plans:write",
            "customers:read", "customers:write",
        ],
        "color": "#e67e22",
    },
    "readonly": {
        "name": "Auditor",
        "description": "Lectura completa para auditoría",
        "permissions": [
            "dashboard:read", "tenants:read", "customers:read",
            "billing:read", "plans:read", "domains:read",
            "nodes:read", "tunnels:read", "settings:read", "logs:read", "roles:read",
            "partners:read", "leads:read", "commissions:read", "quotations:read", "catalog:read",
        ],
        "color": "#95a5a6",
    },
    "partner_manager": {
        "name": "Gestor de Partners",
        "description": "Administra partners, leads, comisiones y cotizaciones",
        "permissions": [
            "dashboard:read", "partners:read", "partners:write",
            "leads:read", "leads:write", "leads:delete",
            "commissions:read", "commissions:write", "commissions:pay",
            "quotations:read", "quotations:write", "quotations:send",
            "catalog:read", "catalog:write",
            "customers:read", "billing:read",
        ],
        "color": "#8e44ad",
    },
}


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
    encoded_jwt = jwt.encode(payload, _jwt_secret_key(), algorithm=_jwt_algorithm())
    return encoded_jwt


def verify_token_with_role(token: str, required_role: str = None) -> dict:
    """Verifica un token JWT y retorna los datos del usuario.
    El rol 'admin' tiene acceso universal a todos los endpoints."""
    try:
        payload = jwt.decode(token, _jwt_secret_key(), algorithms=[_jwt_algorithm()])

        user_role = payload.get("role")

        # Admin tiene acceso universal — puede actuar en cualquier contexto
        if required_role and user_role != required_role and user_role != "admin":
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
    """
    Extrae el token de autenticación en este orden:
    1. Si access_token viene como parámetro (ej: Cookie), usa eso
    2. Si no, intenta extraer del header Authorization (Bearer)
    3. Si tampoco, intenta leer directamente de cookies
    Esto permite compatibilidad con tanto cookies como headers Bearer.
    """
    token = access_token
    if token:
        # Si viene como parámetro, asumir que es el token puro (sin "Bearer")
        return token
    
    # Intentar extraer del header Authorization
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    # Si aún no tenemos token, intentar leer de cookie directamente
    if not token:
        token = request.cookies.get("access_token")
    
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

    assigned_tenants = raw.get("assigned_tenants") or []
    if not isinstance(assigned_tenants, list):
        assigned_tenants = []

    assigned_users = raw.get("assigned_users") or []
    if not isinstance(assigned_users, list):
        assigned_users = []

    return {
        "id": int(raw.get("id", fallback_id)),
        "name": str(raw.get("name", f"role-{fallback_id}")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "permissions": [str(item).strip() for item in permissions if str(item).strip()],
        "system": bool(raw.get("system", False)),
        "updated_at": raw.get("updated_at"),
        "color": raw.get("color", "#6b7280"),
        "assigned_tenants": [int(t) for t in assigned_tenants if str(t).isdigit()],
        "assigned_users": [int(u) for u in assigned_users if str(u).isdigit()],
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
            "color": payload.color or "#6b7280",
            "assigned_tenants": payload.assigned_tenants or [],
            "assigned_users": payload.assigned_users or [],
        }
        roles.append(new_role)

        _save_roles(db, roles, updated_by=auth_data.get("sub", "admin"))
        return {"success": True, "role": new_role}
    finally:
        db.close()


@router.get("/api/roles/permissions-catalog")
async def permissions_catalog_early(request: Request, access_token: Optional[str] = Cookie(None)):
    """Catálogo completo de permisos agrupados por módulo (ruta prioritaria)."""
    _require_admin(request, access_token)
    return {"modules": PERMISSION_CATALOG}


@router.get("/api/roles/presets")
async def role_presets_early(request: Request, access_token: Optional[str] = Cookie(None)):
    """Plantillas predefinidas para crear roles rápidamente (ruta prioritaria)."""
    _require_admin(request, access_token)
    return {"presets": ROLE_PRESETS}


@router.get("/api/roles/available-tenants")
async def available_tenants_early(request: Request, access_token: Optional[str] = Cookie(None)):
    """Lista de tenants disponibles para asignar a roles (ruta prioritaria)."""
    _require_admin(request, access_token)
    from ..models.database import TenantDeployment, Subscription
    db = SessionLocal()
    try:
        deployments = db.query(TenantDeployment).all()
        tenants = []
        for d in deployments:
            sub = db.query(Subscription).filter(Subscription.id == d.subscription_id).first()
            customer = None
            if sub:
                customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
            tenants.append({
                "id": d.id,
                "tenant_name": d.subdomain or f"tenant-{d.id}",
                "domain": d.tunnel_url or d.direct_url or "—",
                "customer_name": customer.company_name if customer else "—",
                "customer_id": sub.customer_id if sub else None,
            })
        return {"tenants": tenants, "total": len(tenants)}
    finally:
        db.close()


@router.get("/api/roles/available-users")
async def available_users_early(request: Request, access_token: Optional[str] = Cookie(None)):
    """Lista de usuarios admin disponibles para asignar a roles (ruta prioritaria)."""
    _require_admin(request, access_token)
    from ..models.database import AdminUser
    db = SessionLocal()
    try:
        users = db.query(AdminUser).filter(AdminUser.is_active == True).order_by(AdminUser.display_name).all()
        result = [
            {
                "id": u.id,
                "email": u.email,
                "display_name": u.display_name,
                "role": u.role.value if u.role else "admin",
            }
            for u in users
        ]
        return {"users": result, "total": len(result)}
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
        target["color"] = payload.color or target.get("color", "#6b7280")
        target["assigned_tenants"] = payload.assigned_tenants if payload.assigned_tenants is not None else target.get("assigned_tenants", [])
        target["assigned_users"] = payload.assigned_users if payload.assigned_users is not None else target.get("assigned_users", [])

        _save_roles(db, roles, updated_by=auth_data.get("sub", "admin"))
        return {"success": True, "role": target}
    finally:
        db.close()


# DEPRECATED ENDPOINTS REMOVED:
# - /api/login/unified -> Use /api/auth/login instead (secure_auth.py)
# - Duplicate permissions-catalog, presets, available-tenants, available-users
#   (kept "early" versions above for correct route priority)


@router.get("/api/roles/{role_id}/users")
async def get_role_users(role_id: int, request: Request, access_token: Optional[str] = Cookie(None)):
    """Obtiene los usuarios asignados a un rol."""
    _require_admin(request, access_token)
    from ..models.database import AdminUser
    db = SessionLocal()
    try:
        roles = _load_roles(db)
        target = next((r for r in roles if int(r["id"]) == role_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        user_ids = target.get("assigned_users", [])
        users = []
        if user_ids:
            users_db = db.query(AdminUser).filter(AdminUser.id.in_(user_ids)).all()
            users = [
                {
                    "id": u.id,
                    "email": u.email,
                    "display_name": u.display_name,
                    "role": u.role.value if u.role else "admin",
                    "is_active": u.is_active,
                }
                for u in users_db
            ]
        return {"users": users, "total": len(users), "role_id": role_id}
    finally:
        db.close()


@router.post("/api/roles/{role_id}/users")
async def assign_users_to_role(
    role_id: int,
    payload: RoleUserAssign,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Asigna usuarios a un rol (reemplaza la lista completa)."""
    auth_data = _require_admin(request, access_token)
    from ..models.database import AdminUser
    db = SessionLocal()
    try:
        roles = _load_roles(db)
        target = next((r for r in roles if int(r["id"]) == role_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Rol no encontrado")

        # Validar que los user_ids existen
        if payload.user_ids:
            existing = db.query(AdminUser.id).filter(AdminUser.id.in_(payload.user_ids)).all()
            existing_ids = {row.id for row in existing}
            invalid = set(payload.user_ids) - existing_ids
            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Usuarios no encontrados: {list(invalid)}",
                )

        target["assigned_users"] = list(set(payload.user_ids))
        target["updated_at"] = datetime.utcnow().isoformat()
        _save_roles(db, roles, updated_by=auth_data.get("sub", "admin"))
        return {"success": True, "role_id": role_id, "assigned_users": target["assigned_users"]}
    finally:
        db.close()


@router.delete("/api/roles/{role_id}/users/{user_id}")
async def remove_user_from_role(
    role_id: int,
    user_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Quita un usuario de un rol."""
    auth_data = _require_admin(request, access_token)
    db = SessionLocal()
    try:
        roles = _load_roles(db)
        target = next((r for r in roles if int(r["id"]) == role_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Rol no encontrado")

        current = target.get("assigned_users", [])
        if user_id not in current:
            raise HTTPException(status_code=404, detail="Usuario no asignado a este rol")

        target["assigned_users"] = [uid for uid in current if uid != user_id]
        target["updated_at"] = datetime.utcnow().isoformat()
        _save_roles(db, roles, updated_by=auth_data.get("sub", "admin"))
        return {"success": True, "role_id": role_id, "removed_user_id": user_id}
    finally:
        db.close()


@router.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, request: Request, access_token: Optional[str] = Cookie(None)):
    """Elimina un rol personalizado (los roles de sistema no pueden eliminarse)."""
    auth_data = _require_admin(request, access_token)
    db = SessionLocal()
    try:
        roles = _load_roles(db)
        target = next((role for role in roles if int(role["id"]) == role_id), None)
        if not target:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        if target.get("system"):
            raise HTTPException(status_code=403, detail="No se puede eliminar un rol de sistema")

        roles = [role for role in roles if int(role["id"]) != role_id]
        _save_roles(db, roles, updated_by=auth_data.get("sub", "admin"))
        return {"success": True, "message": f"Rol '{target['name']}' eliminado"}
    finally:
        db.close()
