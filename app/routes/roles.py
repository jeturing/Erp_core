"""
Role-based authentication - Admin y Tenant user roles
"""
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
from ..models.database import Customer, SessionLocal
from ..services.spa_shell import render_spa_shell

router = APIRouter(tags=["Roles"])

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


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


def create_access_token(username: str, role: str, user_id: int = None, tenant_id: int = None) -> str:
    """Crea un token JWT con información de rol."""
    payload = {
        "sub": username,
        "role": role,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
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
                detail=f"Acceso denegado: se requiere rol {required_role}"
            )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


# Routes
@router.get("/login/{role}", response_class=HTMLResponse)
async def role_login_page(request: Request, role: str):
    """Entrada pública de login unificado en SPA."""
    if role not in ["admin", "tenant"]:
        raise HTTPException(status_code=404, detail="Rol no válido")

    return render_spa_shell("login", {"loginRole": role})


@router.post("/api/logout")
async def logout():
    """Endpoint de logout que invalida la cookie."""
    response = JSONResponse(content={"message": "Sesión cerrada"})
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")  # Also clear refresh token
    response.delete_cookie(key="token", path="/")  # Backward compatibility
    return response


# DEPRECATED ENDPOINTS REMOVED:
# - /api/login/unified -> Use /api/auth/login instead (secure_auth.py)
