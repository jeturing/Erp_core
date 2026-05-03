"""
Authentication Routes - Login, JWT management
"""
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import timedelta
import jwt

from ..config import get_runtime_setting, require_config_secret
from ..utils.runtime_security import utc_now

router = APIRouter(prefix="/api/admin", tags=["Authentication"])

# JWT Configuration
JWT_EXPIRATION_HOURS = 24


def _jwt_secret_key() -> str:
    return require_config_secret("JWT_SECRET_KEY", get_runtime_setting("JWT_SECRET_KEY", ""), production_only=False)


def _jwt_algorithm() -> str:
    return get_runtime_setting("JWT_ALGORITHM", "HS256")


# DTOs
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: str


# JWT Utilities
def create_access_token(username: str) -> str:
    """Crea un token JWT."""
    now = utc_now()
    payload = {
        "sub": username,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": now,
    }
    encoded_jwt = jwt.encode(payload, _jwt_secret_key(), algorithm=_jwt_algorithm())
    return encoded_jwt


def verify_token(token: str) -> str:
    """Verifica un token JWT y retorna el username."""
    try:
        payload = jwt.decode(token, _jwt_secret_key(), algorithms=[_jwt_algorithm()])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Routes
# DEPRECATED: All login functionality moved to secure_auth.py (/api/auth/login)
# This router is kept for backward compatibility with verify_token function
