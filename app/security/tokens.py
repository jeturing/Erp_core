"""
Token Management - Access tokens and Refresh tokens.
Refresh tokens se persisten en BD (tabla refresh_tokens) para sobrevivir reinicios.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
import os
import secrets
import hashlib
import logging

from ..config import (
    JWT_SECRET_KEY,
    JWT_REFRESH_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
)

logger = logging.getLogger(__name__)


def _db():
    """Retorna (RefreshToken model, session) — import lazy para evitar circular imports."""
    from ..models.database import RefreshToken, SessionLocal
    return RefreshToken, SessionLocal()

# Token expiry config
ACCESS_TOKEN_EXPIRE_MINUTES = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
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
    Gestiona refresh tokens persistidos en base de datos.
    Los tokens en claro NUNCA se almacenan — solo su SHA-256.
    """

    @classmethod
    def create_refresh_token(
        cls,
        username: str,
        role: str,
        user_id: int = None,
        tenant_id: int = None
    ) -> Tuple[str, datetime]:
        """Crea un refresh token opaco de larga duración y lo persiste en BD."""
        token = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        RefreshToken, session = _db()
        try:
            record = RefreshToken(
                token_hash=token_hash,
                username=username,
                role=role,
                user_id=user_id,
                tenant_id=tenant_id,
                expires_at=expires_at,
            )
            session.add(record)
            session.commit()
            logger.info(f"Refresh token created for user {username}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating refresh token: {e}")
            raise
        finally:
            session.close()

        return token, expires_at

    @classmethod
    def verify_refresh_token(cls, token: str) -> dict:
        """Verifica un refresh token contra la BD."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        RefreshToken, session = _db()
        try:
            record = session.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash
            ).first()

            if not record:
                raise ValueError("Refresh token inválido")
            if record.revoked:
                logger.warning(f"Attempted use of revoked token for {record.username}")
                raise ValueError("Refresh token revocado")
            if datetime.utcnow() > record.expires_at:
                session.delete(record)
                session.commit()
                raise ValueError("Refresh token expirado")

            return {
                "username": record.username,
                "role": record.role,
                "user_id": record.user_id,
                "tenant_id": record.tenant_id,
            }
        finally:
            session.close()

    @classmethod
    def revoke_refresh_token(cls, token: str) -> bool:
        """Revoca un refresh token específico."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        RefreshToken, session = _db()
        try:
            record = session.query(RefreshToken).filter(
                RefreshToken.token_hash == token_hash
            ).first()
            if record:
                record.revoked = True
                session.commit()
                logger.info(f"Refresh token revoked for {record.username}")
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    @classmethod
    def revoke_all_user_tokens(cls, username: str) -> int:
        """Revoca todos los refresh tokens de un usuario."""
        RefreshToken, session = _db()
        try:
            count = session.query(RefreshToken).filter(
                RefreshToken.username == username,
                RefreshToken.revoked == False
            ).update({"revoked": True})
            session.commit()
            logger.info(f"Revoked {count} refresh tokens for user {username}")
            return count
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()

    @classmethod
    def rotate_refresh_token(
        cls,
        old_token: str,
        username: str,
        role: str,
        user_id: int = None,
        tenant_id: int = None
    ) -> Tuple[str, datetime]:
        """Rota un refresh token: revoca el viejo, crea uno nuevo."""
        cls.revoke_refresh_token(old_token)
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
            samesite="lax",
            max_age=max_age,
            path="/api/auth",
        )

    @classmethod
    def delete_refresh_token_cookie(cls, response):
        """Elimina la cookie del refresh token."""
        response.delete_cookie(
            key="refresh_token",
            path="/api/auth",
            httponly=True,
            secure=USE_SECURE_COOKIES,
            samesite="lax",
        )

    @classmethod
    def cleanup_expired_tokens(cls):
        """Elimina tokens expirados de la BD (para mantenimiento periódico)."""
        RefreshToken, session = _db()
        try:
            deleted = session.query(RefreshToken).filter(
                RefreshToken.expires_at < datetime.utcnow()
            ).delete()
            session.commit()
            if deleted:
                logger.info(f"Cleaned up {deleted} expired refresh tokens from DB")
        except Exception:
            session.rollback()
        finally:
            session.close()
