"""
Token Management - Access tokens and Refresh tokens
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
import os
import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", JWT_SECRET_KEY + "-refresh")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Cookie security configuration
# Solo usar cookies secure si FORCE_HTTPS está habilitado
USE_SECURE_COOKIES = os.getenv("FORCE_HTTPS", "false").lower() == "true"


class TokenManager:
    """Gestiona la creación y validación de access tokens."""
    
    @staticmethod
    def create_access_token(
        username: str,
        role: str,
        user_id: int = None,
        tenant_id: int = None,
        expires_delta: timedelta = None
    ) -> str:
        """
        Crea un access token JWT de corta duración.
        
        Args:
            username: Nombre de usuario o email
            role: Rol del usuario (admin, tenant)
            user_id: ID del usuario
            tenant_id: ID del tenant
            expires_delta: Tiempo de expiración personalizado
        
        Returns:
            Token JWT codificado
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        now = datetime.utcnow()
        expire = now + expires_delta
        
        payload = {
            "sub": username,
            "role": role,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "type": "access",
            "exp": expire,
            "iat": now,
            "jti": secrets.token_hex(16)  # JWT ID único
        }
        
        encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_access_token(token: str, required_role: str = None) -> dict:
        """
        Verifica un access token y retorna el payload.
        
        Args:
            token: Token JWT a verificar
            required_role: Rol requerido (opcional)
        
        Returns:
            Payload del token
        
        Raises:
            jwt.ExpiredSignatureError: Token expirado
            jwt.InvalidTokenError: Token inválido
            ValueError: Tipo de token incorrecto o rol no autorizado
        """
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verificar tipo de token
        if payload.get("type") != "access":
            raise ValueError("Tipo de token inválido")
        
        # Verificar rol si es requerido
        if required_role and payload.get("role") != required_role:
            raise ValueError(f"Rol requerido: {required_role}")
        
        return payload
    
    @staticmethod
    def get_token_from_cookie(request) -> Optional[str]:
        """Extrae el token de la cookie httpOnly."""
        return request.cookies.get("access_token")
    
    @staticmethod
    def set_token_cookie(response, token: str, max_age: int = None):
        """Configura la cookie httpOnly con el token."""
        if max_age is None:
            max_age = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=USE_SECURE_COOKIES,
            samesite="lax",
            max_age=max_age,
            path="/"
        )
    
    @staticmethod
    def delete_token_cookie(response):
        """Elimina la cookie del token."""
        response.delete_cookie(
            key="access_token",
            path="/",
            httponly=True,
            secure=USE_SECURE_COOKIES,
            samesite="lax"
        )


class RefreshTokenManager:
    """
    Gestiona refresh tokens.
    Los refresh tokens se almacenan como hash en la base de datos.
    """
    
    # Almacenamiento en memoria (usar DB en producción)
    _refresh_tokens = {}  # token_hash -> {user_id, role, expires_at, revoked}
    
    @classmethod
    def create_refresh_token(
        cls,
        username: str,
        role: str,
        user_id: int = None,
        tenant_id: int = None
    ) -> Tuple[str, datetime]:
        """
        Crea un refresh token opaco de larga duración.
        
        Returns:
            Tuple[token, expires_at]
        """
        # Generar token opaco seguro
        token = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Almacenar hash del token
        cls._refresh_tokens[token_hash] = {
            "username": username,
            "role": role,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "expires_at": expires_at,
            "revoked": False,
            "created_at": datetime.utcnow()
        }
        
        logger.info(f"Refresh token created for user {username}")
        
        return token, expires_at
    
    @classmethod
    def verify_refresh_token(cls, token: str) -> dict:
        """
        Verifica un refresh token.
        
        Returns:
            Datos del usuario asociado al token
        
        Raises:
            ValueError: Token inválido, expirado o revocado
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash not in cls._refresh_tokens:
            raise ValueError("Refresh token inválido")
        
        token_data = cls._refresh_tokens[token_hash]
        
        if token_data["revoked"]:
            # Token revocado - posible robo, revocar toda la familia
            logger.warning(f"Attempted use of revoked refresh token for {token_data['username']}")
            raise ValueError("Refresh token revocado")
        
        if datetime.utcnow() > token_data["expires_at"]:
            # Limpiar token expirado
            del cls._refresh_tokens[token_hash]
            raise ValueError("Refresh token expirado")
        
        return {
            "username": token_data["username"],
            "role": token_data["role"],
            "user_id": token_data["user_id"],
            "tenant_id": token_data["tenant_id"]
        }
    
    @classmethod
    def revoke_refresh_token(cls, token: str) -> bool:
        """Revoca un refresh token específico."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash in cls._refresh_tokens:
            cls._refresh_tokens[token_hash]["revoked"] = True
            logger.info(f"Refresh token revoked for {cls._refresh_tokens[token_hash]['username']}")
            return True
        
        return False
    
    @classmethod
    def revoke_all_user_tokens(cls, username: str) -> int:
        """Revoca todos los refresh tokens de un usuario."""
        count = 0
        for token_hash, data in cls._refresh_tokens.items():
            if data["username"] == username and not data["revoked"]:
                data["revoked"] = True
                count += 1
        
        logger.info(f"Revoked {count} refresh tokens for user {username}")
        return count
    
    @classmethod
    def rotate_refresh_token(
        cls,
        old_token: str,
        username: str,
        role: str,
        user_id: int = None,
        tenant_id: int = None
    ) -> Tuple[str, datetime]:
        """
        Rota un refresh token (revoca el viejo, crea uno nuevo).
        Implementa refresh token rotation para mayor seguridad.
        """
        # Revocar token antiguo
        cls.revoke_refresh_token(old_token)
        
        # Crear nuevo token
        return cls.create_refresh_token(username, role, user_id, tenant_id)
    
    @classmethod
    def set_refresh_token_cookie(cls, response, token: str):
        """Configura la cookie httpOnly con el refresh token."""
        max_age = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        
        response.set_cookie(
            key="refresh_token",
            value=token,
            httponly=True,
            secure=USE_SECURE_COOKIES,
            samesite="strict",  # Más restrictivo para refresh tokens
            max_age=max_age,
            path="/api/auth/refresh"  # Solo accesible en endpoint de refresh
        )
    
    @classmethod
    def delete_refresh_token_cookie(cls, response):
        """Elimina la cookie del refresh token."""
        response.delete_cookie(
            key="refresh_token",
            path="/api/auth/refresh",
            httponly=True,
            secure=USE_SECURE_COOKIES,
            samesite="strict"
        )
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """Limpia tokens expirados de la memoria."""
        now = datetime.utcnow()
        expired = [
            token_hash for token_hash, data in cls._refresh_tokens.items()
            if data["expires_at"] < now
        ]
        
        for token_hash in expired:
            del cls._refresh_tokens[token_hash]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired refresh tokens")
