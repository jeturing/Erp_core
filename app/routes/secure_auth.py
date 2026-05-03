"""
Secure Authentication Routes - Production-ready authentication with all security features
"""
from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone

from ..models.database import Customer, Partner, PartnerStatus, AdminUser, AdminUserRole, SessionLocal
from ..security.tokens import TokenManager, RefreshTokenManager
from ..security.middleware import RateLimiter
from ..security.audit import AuditLogger, AuditEvent
from ..security.totp import TOTPManager
from ..security.email_verify import create_verification_token, verify_token, send_verification_email

from ..config import get_runtime_setting, require_config_secret

router = APIRouter(prefix="/api/auth", tags=["Secure Authentication"])


def _admin_username() -> str:
    return get_runtime_setting("ADMIN_USERNAME", "admin@sajet.us")


def _admin_password() -> str:
    return require_config_secret("ADMIN_PASSWORD", get_runtime_setting("ADMIN_PASSWORD", ""), production_only=True)

# Rate limiter instance (compartida)
login_rate_limiter = RateLimiter(
    max_requests=5,  # 5 intentos
    window_seconds=300,  # en 5 minutos
    block_duration_seconds=900  # bloqueo de 15 minutos
)


# DTOs
class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None
    email_verify_code: Optional[str] = None


class TOTPSetupRequest(BaseModel):
    password: str


class TOTPVerifyRequest(BaseModel):
    code: str


class TOTPLoginRequest(BaseModel):
    email: str
    password: str
    totp_code: str


class TokenRefreshRequest(BaseModel):
    pass  # El refresh token viene en la cookie


class LoginResponse(BaseModel):
    message: str
    role: str
    requires_totp: bool = False
    requires_email_verify: bool = False
    requires_tenant_selection: bool = False
    available_tenants: Optional[list] = None
    redirect_url: Optional[str] = None
    email: Optional[str] = None
    email_domain: Optional[str] = None
    user_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    user_id: Optional[int] = None


# Helper — usa utilidad centralizada con soporte Cloudflare
from ..utils.ip import get_real_ip as get_client_ip


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
        username = None
        role = None
        redirect_url = None
        
        # Auto-detectar tipo de usuario basándose en el formato
        admin_username = _admin_username()
        admin_password = _admin_password()
        is_admin_login = '@' not in login_data.email or login_data.email == admin_username

        if is_admin_login:
            # Login de admin por env vars (fallback)
            if not admin_password:
                AuditLogger.log_login_failed(
                    username=login_data.email,
                    reason="Admin password not configured",
                    request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            if login_data.email != admin_username or login_data.password != admin_password:
                AuditLogger.log_login_failed(
                    username=login_data.email,
                    reason="Invalid admin credentials",
                    request=request
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas"
                )
            
            username = admin_username
            role = "admin"
            redirect_url = "/admin"
            
        else:
            import bcrypt as _bcrypt
            import hashlib

            # ── PRIMERO verificar si hay múltiples tenants con este email ──
            # Si hay múltiples, saltear admin_user/partner y ir directo a selector
            customers_count = db.query(Customer).filter_by(email=login_data.email).count()
            
            # ── Intentar login como admin_user (BD) solo si NO hay múltiples tenants ──
            admin_user = None
            if customers_count <= 1:
                admin_user = db.query(AdminUser).filter(
                    AdminUser.email == login_data.email,
                    AdminUser.is_active == True
                ).first()

            if admin_user:
                if _bcrypt.checkpw(login_data.password.encode(), admin_user.password_hash.encode()):
                    username = admin_user.email
                    role = admin_user.role.value if admin_user.role else "admin"
                    user_id = admin_user.id
                    redirect_url = "/admin"
                    admin_user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    admin_user.login_count = (admin_user.login_count or 0) + 1
                    db.commit()
                else:
                    AuditLogger.log_login_failed(
                        username=login_data.email,
                        reason="Invalid admin_user password",
                        request=request
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Credenciales inválidas"
                    )
            else:
                # Login con email (@) — puede ser partner o tenant

                def _verify_and_migrate_password(password: str, stored_hash: str):
                    """
                    Verifica password y migra transparentemente de SHA256 a bcrypt.
                    Retorna (ok: bool, nuevo_hash: str|None).
                    El nuevo_hash != None indica que hay que persistir el hash migrado.
                    """
                    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
                        ok = _bcrypt.checkpw(password.encode(), stored_hash.encode())
                        return ok, None
                    # Formato legacy: 'salt:sha256hex'
                    parts = stored_hash.split(":", 1)
                    if len(parts) == 2:
                        salt, sha_hash = parts
                        computed = hashlib.sha256((password + salt).encode()).hexdigest()
                        if computed == sha_hash:
                            new_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
                            return True, new_hash
                    return False, None

                # ── Intentar login como partner primero ──
                partner = db.query(Partner).filter(
                    (Partner.portal_email == login_data.email) |
                    (Partner.contact_email == login_data.email)
                ).first()

                partner_authenticated = False
                if partner:
                    partner_can_authenticate = (
                        bool(partner.password_hash)
                        and partner.portal_access
                        and partner.status in (PartnerStatus.active, PartnerStatus.pending)
                    )

                    if partner_can_authenticate:
                        ok, migrated_hash = _verify_and_migrate_password(login_data.password, partner.password_hash)
                        if ok:
                            if migrated_hash:
                                partner.password_hash = migrated_hash
                            username = partner.portal_email or partner.contact_email
                            role = "partner"
                            user_id = partner.id
                            tenant_id = None
                            redirect_url = "/partner/portal"
                            partner_authenticated = True
                            partner.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
                            partner.login_count = (partner.login_count or 0) + 1
                            db.commit()
                        else:
                            AuditLogger.log_login_failed(
                                username=login_data.email,
                                reason="Invalid partner password",
                                request=request
                            )
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Credenciales inválidas"
                            )
                    elif customers_count == 0:
                        if not partner.portal_access:
                            reason = "Partner portal disabled"
                            detail = "El acceso al portal de partners está deshabilitado para esta cuenta."
                        elif partner.status not in (PartnerStatus.active, PartnerStatus.pending):
                            reason = f"Partner inactive ({partner.status.value if partner.status else 'unknown'})"
                            detail = "Tu cuenta de partner no está activa. Contacte al administrador."
                        elif not partner.password_hash:
                            reason = "Partner password not set"
                            detail = (
                                "Tu cuenta de partner aún no tiene contraseña configurada. "
                                "Solicita la invitación inicial al administrador."
                            )
                        else:
                            reason = "Partner login unavailable"
                            detail = "No se pudo iniciar sesión con esta cuenta de partner."

                        AuditLogger.log_login_failed(
                            username=login_data.email,
                            reason=reason,
                            request=request
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=detail
                        )

                # ── Si no es partner, intentar como tenant ──
                if not partner_authenticated:
                    # Buscar TODOS los customers con este email
                    customers = db.query(Customer).filter_by(email=login_data.email).all()

                    if not customers:
                        AuditLogger.log_login_failed(
                            username=login_data.email,
                            reason="Email not found",
                            request=request
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Credenciales inválidas"
                        )

                    # Verificar password con el PRIMER customer (todos deberían tener el mismo)
                    first_customer = customers[0]
                    if first_customer.password_hash:
                        ok, migrated_hash = _verify_and_migrate_password(login_data.password, first_customer.password_hash)
                        if not ok:
                            AuditLogger.log_login_failed(
                                username=login_data.email,
                                reason="Invalid password",
                                request=request
                            )
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Credenciales inválidas"
                            )
                        if migrated_hash:
                            first_customer.password_hash = migrated_hash
                            db.commit()
                    else:
                        AuditLogger.log_login_failed(
                            username=login_data.email,
                            reason="No password set",
                            request=request
                        )
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Cuenta sin contraseña configurada. Contacte al administrador."
                        )

                    # Si hay MÚLTIPLES tenants, requerir selección
                    if len(customers) > 1:
                        tenants_list = [
                            {
                                "tenant_id": c.id,
                                "company_name": c.company_name,
                                "subdomain": c.subdomain,
                                "email": c.email
                            }
                            for c in customers
                        ]
                        return LoginResponse(
                            message="Seleccione el tenant",
                            role="tenant",
                            requires_tenant_selection=True,
                            available_tenants=tenants_list,
                            email=login_data.email,
                            user_id=first_customer.id
                        )

                    # Si solo hay UNO, continuar normalmente
                    customer = first_customer
                    username = customer.email
                    role = "tenant"
                    user_id = customer.id
                    tenant_id = customer.id
                    redirect_url = "/tenant/portal"
        
        # Verificar 2FA si está habilitado
        effective_user_id = user_id if user_id else 0  # 0 para admin
        if TOTPManager.is_enabled(effective_user_id):
            if not login_data.totp_code:
                email_value = username if username and "@" in username else None
                email_domain = (
                    email_value.rsplit("@", 1)[1].strip().lower() if email_value and "@" in email_value else None
                )
                return LoginResponse(
                    message="Se requiere código 2FA",
                    role=role,
                    requires_totp=True,
                    email=email_value,
                    email_domain=email_domain,
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
        
        # ── Email Verification (Steam-style) ──
        # Required for partner/tenant; optional for admin (per admin_users.require_email_verify)
        needs_email_verify = False
        if role in ("partner", "tenant"):
            needs_email_verify = True
        elif role in ("admin", "operator", "viewer") and user_id:
            admin_user_obj = db.query(AdminUser).filter(AdminUser.id == user_id).first()
            if admin_user_obj and admin_user_obj.require_email_verify:
                needs_email_verify = True

        if needs_email_verify:
            if not login_data.email_verify_code:
                # Generate and send token
                client_ip = get_client_ip(request)
                token = create_verification_token(
                    email=username,
                    user_type=role,
                    user_id=user_id,
                    ip_address=client_ip,
                    user_agent=request.headers.get("User-Agent", "")[:500],
                )
                send_verification_email(username, token, role)

                return LoginResponse(
                    message="Código de verificación enviado a tu email",
                    role=role,
                    requires_email_verify=True,
                    email=username if username and "@" in username else None,
                    email_domain=(
                        username.rsplit("@", 1)[1].strip().lower()
                        if username and "@" in username
                        else None
                    ),
                )
            else:
                # Verify the code
                if not verify_token(username, login_data.email_verify_code):
                    AuditLogger.log_login_failed(
                        username=username,
                        reason="Invalid email verification code",
                        request=request,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Código de verificación inválido o expirado",
                    )

        # Login exitoso - resetear rate limiter
        login_rate_limiter.reset(request)

        email_value = username if username and "@" in username else None
        email_domain = (
            email_value.rsplit("@", 1)[1].strip().lower()
            if email_value and "@" in email_value
            else None
        )
        
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
        
        # Crear respuesta con cookies Y token en JSON (para sincronización frontend)
        response = JSONResponse(content={
            "message": "Login exitoso",
            "role": role,
            "requires_totp": False,
            "requires_email_verify": False,
            "redirect_url": redirect_url,
            "user_id": user_id,
            "email": email_value,
            "email_domain": email_domain,
            "access_token": access_token,
            "token_type": "bearer"
        })
        
        # Configurar cookies httpOnly
        TokenManager.set_token_cookie(response, access_token)
        RefreshTokenManager.set_refresh_token_cookie(response, refresh_token)
        
        return response
        
    finally:
        db.close()


@router.post("/totp/verify", response_model=LoginResponse)
async def verify_totp_login(request: Request, payload: TOTPLoginRequest):
    """
    Completa login 2FA reutilizando el flujo principal de autenticación.
    """
    login_data = LoginRequest(
        email=payload.email,
        password=payload.password,
        totp_code=payload.totp_code,
    )
    return await secure_login(request, login_data)


@router.get("/me")
async def get_current_user(request: Request):
    """
    Obtiene información del usuario autenticado actual.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            access_token = auth_header[7:]
    
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

        # Si es admin con user_id, buscar en admin_users para obtener display_name
        if payload.get("role") in ("admin", "operator", "viewer") and payload.get("user_id"):
            db = SessionLocal()
            try:
                admin_user = db.query(AdminUser).filter(
                    AdminUser.id == payload.get("user_id")
                ).first()
                if admin_user:
                    user_data["username"] = admin_user.display_name
                    user_data["email"] = admin_user.email
                    user_data["display_name"] = admin_user.display_name
                    user_data["admin_user_id"] = admin_user.id
            finally:
                db.close()
        
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
                    user_data["onboarding_step"] = customer.onboarding_step
                    user_data["onboarding_bypass"] = customer.onboarding_bypass or False
                    user_data["onboarding_completed"] = customer.onboarding_completed_at is not None
                    user_data["country"] = customer.country
                    user_data["requires_ecf"] = customer.requires_ecf
            finally:
                db.close()

        # Si es partner, obtener info del partner
        if payload.get("role") == "partner" and payload.get("user_id"):
            db = SessionLocal()
            try:
                partner = db.query(Partner).filter(
                    Partner.id == payload.get("user_id")
                ).first()
                if partner:
                    user_data["company_name"] = partner.company_name
                    user_data["partner_id"] = partner.id
                    user_data["onboarding_step"] = partner.onboarding_step
                    user_data["onboarding_bypass"] = partner.onboarding_bypass or False
                    user_data["onboarding_completed"] = partner.onboarding_completed_at is not None
                    user_data["stripe_onboarding_complete"] = partner.stripe_onboarding_complete
                    user_data["stripe_charges_enabled"] = partner.stripe_charges_enabled
                    user_data["commission_rate"] = partner.commission_rate
                    user_data["status"] = partner.status.value if partner.status else None
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
        
        # Respuesta con nuevos tokens en cookies Y en JSON (para sincronización frontend)
        response = JSONResponse(content={
            "message": "Token renovado exitosamente",
            "access_token": new_access_token,
            "token_type": "bearer"
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


@router.post("/select-tenant")
async def select_tenant(request: Request, tenant_id: int = None):
    """
    Completa el login seleccionando un tenant específico cuando hay múltiples con el mismo email.
    Recibe tenant_id via JSON body.
    """
    from pydantic import BaseModel
    
    class TenantSelectRequest(BaseModel):
        email: str
        tenant_id: int
    
    try:
        body = await request.json()
        tenant_select = TenantSelectRequest(**body)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request inválido, se requiere email y tenant_id"
        )
    
    db = SessionLocal()
    try:
        # Verificar que el customer existe
        customer = db.query(Customer).filter(
            Customer.id == tenant_select.tenant_id,
            Customer.email == tenant_select.email
        ).first()
        
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado"
            )
        
        # Generar tokens
        access_token_str = TokenManager.create_access_token(
            username=customer.email,
            role="tenant",
            user_id=customer.id,
            tenant_id=customer.id
        )
        refresh_token_str = TokenManager.create_refresh_token(customer.email)
        
        # Crear respuesta con cookies
        response = JSONResponse({
            "message": "Login exitoso",
            "role": "tenant",
            "redirect_url": "/tenant/portal",
            "email": customer.email,
            "user_id": customer.id,
            "tenant_id": customer.id,
            "access_token": access_token_str,
            "token_type": "bearer"
        })
        
        # Configurar cookies
        response.set_cookie(
            key="access_token",
            value=access_token_str,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token_str,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=30 * 24 * 3600
        )
        
        # Audit log
        AuditLogger.log_login_success(
            username=customer.email,
            role="tenant",
            user_id=customer.id,
            tenant_id=customer.id,
            request=request
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )
    finally:
        db.close()


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
