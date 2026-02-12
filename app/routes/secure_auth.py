"""
Secure Authentication Routes - Production-ready authentication with all security features
"""
from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import os

from ..models.database import Customer, SessionLocal
from ..security.tokens import TokenManager, RefreshTokenManager
from ..security.middleware import RateLimiter
from ..security.audit import AuditLogger, AuditEvent
from ..security.totp import TOTPManager

router = APIRouter(prefix="/api/auth", tags=["Secure Authentication"])

# Rate limiter instance (compartida)
login_rate_limiter = RateLimiter(
    max_requests=5,  # 5 intentos
    window_seconds=300,  # en 5 minutos
    block_duration_seconds=900  # bloqueo de 15 minutos
)

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


# DTOs
class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None


class TOTPSetupRequest(BaseModel):
    password: str


class TOTPVerifyRequest(BaseModel):
    code: str


class TokenRefreshRequest(BaseModel):
    pass  # El refresh token viene en la cookie


class LoginResponse(BaseModel):
    message: str
    role: str
    requires_totp: bool = False
    redirect_url: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    user_id: Optional[int] = None


# Helper functions
def get_client_ip(request: Request) -> str:
    """Obtiene la IP real del cliente."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Routes
@router.post("/login", response_model=LoginResponse)
async def secure_login(request: Request, login_data: LoginRequest):
    """
    Login seguro con detección automática de tipo de usuario.
    
    - Si es admin: usuario sin @ (ej: admin)
    - Si es tenant: email con @ (ej: cliente@demo.com)
    - Rate limiting: 5 intentos en 5 minutos, bloqueo de 15 minutos
    - Tokens en cookies httpOnly
    - Soporte para TOTP (2FA)
    - Audit logging de todos los intentos
    """
    # Verificar rate limit
    allowed, rate_info = login_rate_limiter.check_rate_limit(request)
    if not allowed:
        AuditLogger.log_rate_limit(username=login_data.email, request=request)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_info["message"],
            headers={"Retry-After": str(rate_info["retry_after"])}
        )
    
    db = SessionLocal()
    try:
        user_id = None
        tenant_id = None
        
        # Auto-detectar tipo de usuario basándose en el formato
        is_admin_login = '@' not in login_data.email or login_data.email == ADMIN_USERNAME
        
        if is_admin_login:
            # Login de admin
            if login_data.email != ADMIN_USERNAME or login_data.password != ADMIN_PASSWORD:
                AuditLogger.log_login_failed(
                    username=login_data.email,
                    reason="Invalid admin credentials",
                    request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            
            username = ADMIN_USERNAME
            role = "admin"
            redirect_url = "/admin"
            
        else:
            # Login de tenant (tiene @)
            customer = db.query(Customer).filter_by(email=login_data.email).first()
            
            if not customer:
                AuditLogger.log_login_failed(
                    username=login_data.email,
                    reason="Email not found",
                    request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            
            # Verificar password hasheado (formato: salt:hash)
            if customer.password_hash:
                import hashlib
                parts = customer.password_hash.split(':')
                if len(parts) == 2:
                    salt, stored_hash = parts
                    computed_hash = hashlib.sha256((login_data.password + salt).encode()).hexdigest()
                    if computed_hash != stored_hash:
                        AuditLogger.log_login_failed(
                            username=login_data.email,
                            reason="Invalid password",
                            request=request
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciales inválidas"
                        )
                else:
                    # Hash inválido, rechazar
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Credenciales inválidas"
                    )
            else:
                # Sin password configurada
                AuditLogger.log_login_failed(
                    username=login_data.email,
                    reason="No password set",
                    request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Cuenta sin contraseña configurada. Contacte al administrador."
                )
            
            username = customer.email
            role = "tenant"
            user_id = customer.id
            tenant_id = customer.id
            redirect_url = "/tenant/portal"
        
        # Verificar 2FA si está habilitado
        effective_user_id = user_id if user_id else 0  # 0 para admin
        if TOTPManager.is_enabled(effective_user_id):
            if not login_data.totp_code:
                return LoginResponse(
                    message="Se requiere código 2FA",
                    role=role,
                    requires_totp=True
                )
            
            # Verificar código TOTP o código de respaldo
            if not TOTPManager.verify_code(effective_user_id, login_data.totp_code):
                if not TOTPManager.verify_backup_code(effective_user_id, login_data.totp_code):
                    AuditLogger.log_totp_event(
                        AuditEvent.TOTP_FAILED,
                        username=username,
                        user_id=effective_user_id,
                        success=False,
                        request=request
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Código 2FA inválido"
                    )
            
            AuditLogger.log_totp_event(
                AuditEvent.TOTP_VERIFIED,
                username=username,
                user_id=effective_user_id,
                success=True,
                request=request
            )
        
        # Login exitoso - resetear rate limiter
        login_rate_limiter.reset(request)
        
        # Crear tokens
        access_token = TokenManager.create_access_token(
            username=username,
            role=role,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        refresh_token, refresh_expires = RefreshTokenManager.create_refresh_token(
            username=username,
            role=role,
            user_id=user_id,
            tenant_id=tenant_id
        )
        
        # Log de auditoría
        AuditLogger.log_login_success(
            username=username,
            role=role,
            user_id=user_id,
            request=request
        )
        
        # Crear respuesta con cookies
        response = JSONResponse(content={
            "message": "Login exitoso",
            "role": role,
            "requires_totp": False,
            "redirect_url": redirect_url,
            "user_id": user_id
        })
        
        # Configurar cookies httpOnly
        TokenManager.set_token_cookie(response, access_token)
        RefreshTokenManager.set_refresh_token_cookie(response, refresh_token)
        
        return response
        
    finally:
        db.close()


@router.get("/me")
async def get_current_user(request: Request):
    """
    Obtiene información del usuario autenticado actual.
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        payload = TokenManager.verify_access_token(access_token)
        
        user_data = {
            "username": payload.get("sub"),
            "email": payload.get("sub"),
            "role": payload.get("role"),
            "user_id": payload.get("user_id"),
            "tenant_id": payload.get("tenant_id")
        }
        
        # Si es tenant, obtener más info del cliente
        if payload.get("role") == "tenant" and payload.get("user_id"):
            db = SessionLocal()
            try:
                customer = db.query(Customer).filter(
                    Customer.id == payload.get("user_id")
                ).first()
                if customer:
                    user_data["company_name"] = customer.company_name
                    user_data["plan"] = customer.plan
            finally:
                db.close()
        
        return user_data
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Renueva el access token usando el refresh token.
    Implementa refresh token rotation.
    """
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no encontrado"
        )
    
    try:
        # Verificar refresh token
        user_data = RefreshTokenManager.verify_refresh_token(refresh_token)
        
        # Crear nuevo access token
        new_access_token = TokenManager.create_access_token(
            username=user_data["username"],
            role=user_data["role"],
            user_id=user_data["user_id"],
            tenant_id=user_data["tenant_id"]
        )
        
        # Rotar refresh token (revoca viejo, crea nuevo)
        new_refresh_token, _ = RefreshTokenManager.rotate_refresh_token(
            old_token=refresh_token,
            username=user_data["username"],
            role=user_data["role"],
            user_id=user_data["user_id"],
            tenant_id=user_data["tenant_id"]
        )
        
        AuditLogger.log(
            event=AuditEvent.TOKEN_REFRESH,
            username=user_data["username"],
            user_id=user_data["user_id"],
            role=user_data["role"],
            request=request
        )
        
        # Respuesta con nuevos tokens en cookies
        response = JSONResponse(content={
            "message": "Token renovado exitosamente"
        })
        
        TokenManager.set_token_cookie(response, new_access_token)
        RefreshTokenManager.set_refresh_token_cookie(response, new_refresh_token)
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout")
async def secure_logout(request: Request):
    """
    Logout seguro que revoca tokens y elimina cookies.
    """
    # Obtener refresh token para revocarlo
    refresh_token = request.cookies.get("refresh_token")
    access_token = request.cookies.get("access_token")
    
    username = None
    user_id = None
    
    # Intentar obtener info del usuario para logging
    if access_token:
        try:
            payload = TokenManager.verify_access_token(access_token)
            username = payload.get("sub")
            user_id = payload.get("user_id")
        except:
            pass
    
    # Revocar refresh token
    if refresh_token:
        RefreshTokenManager.revoke_refresh_token(refresh_token)
    
    AuditLogger.log_logout(username=username, user_id=user_id, request=request)
    
    # Eliminar cookies
    response = JSONResponse(content={
        "message": "Sesión cerrada exitosamente"
    })
    
    TokenManager.delete_token_cookie(response)
    RefreshTokenManager.delete_refresh_token_cookie(response)
    
    return response


@router.post("/logout/all")
async def logout_all_sessions(request: Request):
    """
    Cierra todas las sesiones del usuario (revoca todos los refresh tokens).
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        payload = TokenManager.verify_access_token(access_token)
        username = payload.get("sub")
        
        # Revocar todos los refresh tokens del usuario
        count = RefreshTokenManager.revoke_all_user_tokens(username)
        
        AuditLogger.log(
            event=AuditEvent.TOKEN_REVOKED,
            username=username,
            details={"tokens_revoked": count},
            request=request
        )
        
        # Eliminar cookies
        response = JSONResponse(content={
            "message": f"Se cerraron {count} sesiones activas"
        })
        
        TokenManager.delete_token_cookie(response)
        RefreshTokenManager.delete_refresh_token_cookie(response)
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


# 2FA Endpoints
@router.post("/2fa/setup")
async def setup_2fa(request: Request):
    """
    Inicia la configuración de 2FA.
    Retorna el QR code y códigos de respaldo.
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        payload = TokenManager.verify_access_token(access_token)
        user_id = payload.get("user_id") or 0  # 0 para admin
        username = payload.get("sub")
        
        # Verificar si ya tiene 2FA
        if TOTPManager.is_enabled(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA ya está habilitado"
            )
        
        # Generar configuración
        setup_data = TOTPManager.setup_totp(user_id, username)
        
        return {
            "message": "Escanea el código QR con tu app de autenticación",
            "qr_code": setup_data["qr_code_base64"],
            "secret": setup_data["secret"],
            "backup_codes": setup_data["backup_codes"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


@router.post("/2fa/verify")
async def verify_and_enable_2fa(request: Request, data: TOTPVerifyRequest):
    """
    Verifica el código TOTP y habilita 2FA.
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        payload = TokenManager.verify_access_token(access_token)
        user_id = payload.get("user_id") or 0
        username = payload.get("sub")
        
        if TOTPManager.verify_and_enable(user_id, data.code):
            AuditLogger.log_totp_event(
                AuditEvent.TOTP_ENABLED,
                username=username,
                user_id=user_id,
                success=True,
                request=request
            )
            return {"message": "2FA habilitado exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido"
            )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


@router.post("/2fa/disable")
async def disable_2fa(request: Request, data: TOTPVerifyRequest):
    """
    Deshabilita 2FA (requiere código válido).
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        payload = TokenManager.verify_access_token(access_token)
        user_id = payload.get("user_id") or 0
        username = payload.get("sub")
        
        if TOTPManager.disable_totp(user_id, data.code):
            AuditLogger.log_totp_event(
                AuditEvent.TOTP_DISABLED,
                username=username,
                user_id=user_id,
                success=True,
                request=request
            )
            return {"message": "2FA deshabilitado"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido"
            )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


@router.get("/2fa/status")
async def get_2fa_status(request: Request):
    """
    Verifica el estado de 2FA del usuario.
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        payload = TokenManager.verify_access_token(access_token)
        user_id = payload.get("user_id") or 0
        
        enabled = TOTPManager.is_enabled(user_id)
        remaining_codes = TOTPManager.get_remaining_backup_codes(user_id) if enabled else 0
        
        return {
            "enabled": enabled,
            "remaining_backup_codes": remaining_codes
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


@router.post("/2fa/backup-codes/regenerate")
async def regenerate_backup_codes(request: Request, data: TOTPVerifyRequest):
    """
    Regenera los códigos de respaldo (requiere código TOTP válido).
    """
    access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    try:
        payload = TokenManager.verify_access_token(access_token)
        user_id = payload.get("user_id") or 0
        
        # Verificar código TOTP primero
        if not TOTPManager.verify_code(user_id, data.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código inválido"
            )
        
        new_codes = TOTPManager.regenerate_backup_codes(user_id)
        
        if new_codes:
            return {
                "message": "Códigos de respaldo regenerados",
                "backup_codes": new_codes
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al regenerar códigos"
            )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


# Verificación de estado de rate limit
@router.get("/rate-limit/status")
async def get_rate_limit_status(request: Request):
    """
    Verifica el estado de rate limiting para el cliente actual.
    """
    is_blocked = login_rate_limiter.is_blocked(request)
    
    return {
        "blocked": is_blocked,
        "max_requests": login_rate_limiter.max_requests,
        "window_seconds": login_rate_limiter.window_seconds
    }
