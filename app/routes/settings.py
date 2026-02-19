"""
Settings Routes - Configuración del sistema administrable desde /admin
"""
from fastapi import APIRouter, HTTPException, Header, Query, Cookie
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from ..models.database import (
    SystemConfig, SessionLocal, get_config, set_config, get_all_configs
)
from ..services.odoo_database_manager import get_odoo_config
from .auth import verify_token
import logging
import os
import re

router = APIRouter(prefix="/api/settings", tags=["Settings"])
logger = logging.getLogger(__name__)


# =====================================================
# DTOs
# =====================================================

class ConfigUpdateRequest(BaseModel):
    """Request para actualizar una configuración"""
    key: str = Field(..., description="Clave de la configuración")
    value: str = Field(..., description="Nuevo valor")
    description: Optional[str] = Field(None, description="Descripción opcional")


class ConfigBulkUpdateRequest(BaseModel):
    """Request para actualizar múltiples configuraciones"""
    configs: List[ConfigUpdateRequest]


class OdooConfigUpdateRequest(BaseModel):
    """Request para actualizar configuración de Odoo"""
    admin_login: Optional[str] = Field(None, description="Email admin por defecto")
    admin_password: Optional[str] = Field(None, description="Password admin por defecto")
    master_password: Optional[str] = Field(None, description="Master password de Odoo")
    db_user: Optional[str] = Field(None, description="Usuario PostgreSQL")
    db_password: Optional[str] = Field(None, description="Password PostgreSQL")
    default_lang: Optional[str] = Field(None, description="Idioma por defecto (es_DO, es_MX, en_US)")
    default_country: Optional[str] = Field(None, description="País por defecto (DO, MX, US)")
    base_domain: Optional[str] = Field(None, description="Dominio base para tenants")
    template_db: Optional[str] = Field(None, description="BD template para duplicar")


# =====================================================
# ENDPOINTS - GESTIÓN DE CREDENCIALES (.env)
# =====================================================

class CredentialEntry(BaseModel):
    """Una credencial del sistema."""
    key: str
    value: str
    category: str = "general"
    description: Optional[str] = None
    is_secret: bool = True


class CredentialBulkRequest(BaseModel):
    """Actualización masiva de credenciales."""
    credentials: List[CredentialEntry]


class StripeModeRequest(BaseModel):
    """Cambiar modo Stripe (test/live)."""
    mode: str = Field(..., description="'test' o 'live'")
    test_secret_key: Optional[str] = None
    test_publishable_key: Optional[str] = None
    test_webhook_secret: Optional[str] = None
    live_secret_key: Optional[str] = None
    live_publishable_key: Optional[str] = None
    live_webhook_secret: Optional[str] = None


# Credenciales organizadas por categoría con metadatos
CREDENTIAL_DEFINITIONS = {
    "stripe": {
        "label": "Stripe Payments",
        "items": [
            {"key": "STRIPE_MODE", "description": "Modo activo (test / live)", "is_secret": False, "default": "live"},
            {"key": "STRIPE_SECRET_KEY", "description": "Secret key activa (sk_ o rk_)", "is_secret": True},
            {"key": "STRIPE_PUBLISHABLE_KEY", "description": "Publishable key activa (pk_)", "is_secret": False},
            {"key": "STRIPE_WEBHOOK_SECRET", "description": "Webhook secret activo (whsec_)", "is_secret": True},
            {"key": "STRIPE_TEST_SECRET_KEY", "description": "Secret key de TEST (sk_test_)", "is_secret": True},
            {"key": "STRIPE_TEST_PUBLISHABLE_KEY", "description": "Publishable key de TEST (pk_test_)", "is_secret": False},
            {"key": "STRIPE_TEST_WEBHOOK_SECRET", "description": "Webhook secret de TEST", "is_secret": True},
            {"key": "STRIPE_LIVE_SECRET_KEY", "description": "Secret key de LIVE (rk_live_ / sk_live_)", "is_secret": True},
            {"key": "STRIPE_LIVE_PUBLISHABLE_KEY", "description": "Publishable key de LIVE (pk_live_)", "is_secret": False},
            {"key": "STRIPE_LIVE_WEBHOOK_SECRET", "description": "Webhook secret de LIVE", "is_secret": True},
        ],
    },
    "cloudflare": {
        "label": "Cloudflare",
        "items": [
            {"key": "CLOUDFLARE_API_TOKEN", "description": "API Token de Cloudflare", "is_secret": True},
            {"key": "CLOUDFLARE_ACCOUNT_ID", "description": "Account ID", "is_secret": False},
            {"key": "CLOUDFLARE_ZONE_ID", "description": "Zone ID principal (sajet.us)", "is_secret": False},
            {"key": "CLOUDFLARE_TUNNEL_ID", "description": "Tunnel ID principal", "is_secret": False},
            {"key": "CLOUDFLARE_ZONES", "description": "Zonas: domain=zone_id,domain=zone_id", "is_secret": False},
        ],
    },
    "database": {
        "label": "Base de Datos",
        "items": [
            {"key": "DATABASE_URL", "description": "URL de conexión PostgreSQL", "is_secret": True},
            {"key": "DB_HOST", "description": "Host PostgreSQL", "is_secret": False},
            {"key": "DB_PORT", "description": "Puerto PostgreSQL", "is_secret": False},
            {"key": "DB_NAME", "description": "Nombre de la BD", "is_secret": False},
            {"key": "DB_USER", "description": "Usuario PostgreSQL", "is_secret": False},
            {"key": "DB_PASSWORD", "description": "Password PostgreSQL", "is_secret": True},
        ],
    },
    "auth": {
        "label": "Autenticación / JWT",
        "items": [
            {"key": "JWT_SECRET_KEY", "description": "Clave secreta JWT", "is_secret": True},
            {"key": "JWT_REFRESH_SECRET_KEY", "description": "Clave secreta refresh JWT", "is_secret": True},
            {"key": "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "description": "Minutos de expiración del token", "is_secret": False},
            {"key": "ADMIN_USERNAME", "description": "Email del admin", "is_secret": False},
            {"key": "ADMIN_PASSWORD", "description": "Password del admin", "is_secret": True},
        ],
    },
    "infrastructure": {
        "label": "Infraestructura",
        "items": [
            {"key": "APP_URL", "description": "URL pública de la aplicación", "is_secret": False},
            {"key": "ENVIRONMENT", "description": "Entorno (development / production)", "is_secret": False},
            {"key": "ODOO_PRIMARY_IP", "description": "IP del servidor Odoo primario", "is_secret": False},
            {"key": "CT105_IP", "description": "IP del contenedor CT105", "is_secret": False},
            {"key": "ERP_CORE_IP", "description": "IP de ERP Core", "is_secret": False},
            {"key": "PROVISIONING_API_KEY", "description": "API Key de provisioning", "is_secret": True},
        ],
    },
}



# =====================================================
# HELPERS
# =====================================================

def require_admin(authorization: str = None, cookie_token: str = None):
    """Verifica que el usuario sea admin. Acepta Bearer token o cookie."""
    token = None
    
    # Primero intentar con Authorization header
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    # Si no hay header, intentar con cookie
    elif cookie_token:
        token = cookie_token
    
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_token(token)
        # Aquí podrías verificar roles específicos
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token inválido")


# =====================================================
# ENDPOINTS - CONFIGURACIÓN GENERAL
# =====================================================

@router.get("")
async def list_all_configs(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Lista todas las configuraciones del sistema.
    
    Categorías disponibles:
    - odoo: Configuración de Odoo/tenants
    - stripe: Configuración de pagos
    - security: Configuración de seguridad
    - general: Configuración general
    """
    require_admin(authorization, access_token)
    
    try:
        configs = get_all_configs(category)
        
        # Agrupar por categoría
        by_category = {}
        for config in configs:
            cat = config.get("category", "general")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(config)
        
        return {
            "configs": configs,
            "by_category": by_category,
            "total": len(configs)
        }
    except Exception as e:
        logger.error(f"Error listando configuraciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/credentials")
async def list_credentials(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Lista todas las credenciales del sistema organizadas por categoría.
    Valores secretos se muestran enmascarados. Los valores vienen de:
    1. BD (system_config) si existe
    2. Variables de entorno como fallback
    """
    require_admin(authorization, access_token)

    result = {}
    for cat_key, cat_def in CREDENTIAL_DEFINITIONS.items():
        if category and cat_key != category:
            continue
        items = []
        for item_def in cat_def["items"]:
            key = item_def["key"]
            # Intentar BD primero, luego env
            db_val = get_config(key, None)
            env_val = os.getenv(key, "")
            raw_value = db_val if db_val is not None else env_val
            source = "database" if db_val is not None else ("env" if env_val else "not_set")

            # Enmascarar secretos
            if item_def["is_secret"] and raw_value:
                if len(raw_value) > 8:
                    masked = raw_value[:4] + "•" * (len(raw_value) - 8) + raw_value[-4:]
                else:
                    masked = "••••••••"
            else:
                masked = raw_value or ""

            items.append({
                "key": key,
                "value": masked,
                "raw_length": len(raw_value) if raw_value else 0,
                "description": item_def["description"],
                "is_secret": item_def["is_secret"],
                "is_set": bool(raw_value),
                "source": source,
            })
        result[cat_key] = {
            "label": cat_def["label"],
            "items": items,
        }

    return {"success": True, "credentials": result}


@router.put("/credentials/{key}")
async def update_credential(
    key: str,
    payload: CredentialEntry,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Actualiza una credencial. Se guarda en system_config (BD).
    Para cambios en .env del disco se requiere reinicio del servicio.
    """
    require_admin(authorization, access_token)

    if payload.key != key:
        raise HTTPException(status_code=400, detail="Key mismatch")

    # Validar que la key esté en las definiciones permitidas
    valid_keys = set()
    for cat in CREDENTIAL_DEFINITIONS.values():
        for item in cat["items"]:
            valid_keys.add(item["key"])

    if key not in valid_keys:
        raise HTTPException(status_code=400, detail=f"Credencial '{key}' no está en la lista permitida")

    success = set_config(
        key=key,
        value=payload.value,
        description=payload.description or f"Credential: {key}",
        category=payload.category,
        is_secret=payload.is_secret,
        updated_by="admin",
    )

    if success:
        logger.info(f"Credencial actualizada: {key}")
        return {"success": True, "key": key, "message": f"Credencial '{key}' actualizada"}
    else:
        raise HTTPException(status_code=500, detail="Error guardando credencial")


@router.post("/credentials/bulk")
async def update_credentials_bulk(
    payload: CredentialBulkRequest,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """Actualiza múltiples credenciales a la vez."""
    require_admin(authorization, access_token)

    results = []
    for cred in payload.credentials:
        success = set_config(
            key=cred.key,
            value=cred.value,
            description=cred.description,
            category=cred.category,
            is_secret=cred.is_secret,
            updated_by="admin",
        )
        results.append({"key": cred.key, "success": success})

    return {
        "success": True,
        "results": results,
        "updated": sum(1 for r in results if r["success"]),
    }


# =====================================================
# ENDPOINTS - STRIPE MODE TOGGLE (dev / prod)
# =====================================================

@router.get("/stripe/mode")
async def get_stripe_mode(
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Obtiene el modo actual de Stripe (test/live) y las keys configuradas.
    """
    require_admin(authorization, access_token)

    mode = get_config("STRIPE_MODE", None) or "live"
    current_sk = get_config("STRIPE_SECRET_KEY", None) or os.getenv("STRIPE_SECRET_KEY", "")
    current_pk = get_config("STRIPE_PUBLISHABLE_KEY", None) or os.getenv("STRIPE_PUBLISHABLE_KEY", "")

    # Auto-detectar modo si no está explícito
    if current_sk:
        if current_sk.startswith("sk_test_") or current_sk.startswith("rk_test_"):
            detected = "test"
        else:
            detected = "live"
    else:
        detected = "unknown"

    # Verificar si hay keys guardadas para cada modo
    has_test = bool(get_config("STRIPE_TEST_SECRET_KEY", None))
    has_live = bool(get_config("STRIPE_LIVE_SECRET_KEY", None) or (current_sk and "live" in current_sk))

    return {
        "success": True,
        "mode": mode,
        "detected_mode": detected,
        "active_secret_key_prefix": current_sk[:12] + "..." if current_sk and len(current_sk) > 12 else "",
        "active_publishable_key": current_pk[:20] + "..." if current_pk and len(current_pk) > 20 else "",
        "has_test_keys": has_test,
        "has_live_keys": has_live,
    }


@router.post("/stripe/mode")
async def set_stripe_mode(
    payload: StripeModeRequest,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Cambia el modo Stripe entre test y live.
    
    Flujo:
    1. Si se proporcionan keys nuevas, las guarda en STRIPE_{TEST/LIVE}_*
    2. Copia las keys del modo seleccionado a STRIPE_SECRET_KEY, etc.
    3. Actualiza STRIPE_MODE
    
    Los cambios se guardan en BD (system_config) y aplican en el próximo request.
    Para aplicar globalmente se requiere reiniciar el servicio.
    """
    require_admin(authorization, access_token)

    if payload.mode not in ("test", "live"):
        raise HTTPException(status_code=400, detail="Modo debe ser 'test' o 'live'")

    changes = []

    # Guardar keys nuevas si se proporcionan
    if payload.mode == "test":
        if payload.test_secret_key:
            set_config("STRIPE_TEST_SECRET_KEY", payload.test_secret_key, "Secret key TEST", "stripe", True, "admin")
            changes.append("STRIPE_TEST_SECRET_KEY")
        if payload.test_publishable_key:
            set_config("STRIPE_TEST_PUBLISHABLE_KEY", payload.test_publishable_key, "Publishable key TEST", "stripe", False, "admin")
            changes.append("STRIPE_TEST_PUBLISHABLE_KEY")
        if payload.test_webhook_secret:
            set_config("STRIPE_TEST_WEBHOOK_SECRET", payload.test_webhook_secret, "Webhook secret TEST", "stripe", True, "admin")
            changes.append("STRIPE_TEST_WEBHOOK_SECRET")
    else:
        if payload.live_secret_key:
            set_config("STRIPE_LIVE_SECRET_KEY", payload.live_secret_key, "Secret key LIVE", "stripe", True, "admin")
            changes.append("STRIPE_LIVE_SECRET_KEY")
        if payload.live_publishable_key:
            set_config("STRIPE_LIVE_PUBLISHABLE_KEY", payload.live_publishable_key, "Publishable key LIVE", "stripe", False, "admin")
            changes.append("STRIPE_LIVE_PUBLISHABLE_KEY")
        if payload.live_webhook_secret:
            set_config("STRIPE_LIVE_WEBHOOK_SECRET", payload.live_webhook_secret, "Webhook secret LIVE", "stripe", True, "admin")
            changes.append("STRIPE_LIVE_WEBHOOK_SECRET")

    # Obtener las keys del modo seleccionado
    if payload.mode == "test":
        sk = get_config("STRIPE_TEST_SECRET_KEY", "")
        pk = get_config("STRIPE_TEST_PUBLISHABLE_KEY", "")
        wh = get_config("STRIPE_TEST_WEBHOOK_SECRET", "")
    else:
        sk = get_config("STRIPE_LIVE_SECRET_KEY", None) or os.getenv("STRIPE_SECRET_KEY", "")
        pk = get_config("STRIPE_LIVE_PUBLISHABLE_KEY", None) or os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        wh = get_config("STRIPE_LIVE_WEBHOOK_SECRET", None) or os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if not sk:
        raise HTTPException(
            status_code=400,
            detail=f"No hay Secret Key configurada para modo '{payload.mode}'. Primero guarde las credenciales."
        )

    # Activar las keys del modo seleccionado
    set_config("STRIPE_SECRET_KEY", sk, f"Stripe SK activa ({payload.mode})", "stripe", True, "admin")
    set_config("STRIPE_PUBLISHABLE_KEY", pk, f"Stripe PK activa ({payload.mode})", "stripe", False, "admin")
    if wh:
        set_config("STRIPE_WEBHOOK_SECRET", wh, f"Stripe WH activa ({payload.mode})", "stripe", True, "admin")
    set_config("STRIPE_MODE", payload.mode, "Modo Stripe activo", "stripe", False, "admin")

    logger.info(f"Stripe modo cambiado a '{payload.mode}' — SK prefix: {sk[:12]}...")

    return {
        "success": True,
        "mode": payload.mode,
        "message": f"Stripe cambiado a modo {payload.mode.upper()}. Reinicie el servicio para aplicar globalmente.",
        "active_key_prefix": sk[:12] + "..." if len(sk) > 12 else sk,
        "changes": changes,
        "requires_restart": True,
    }


@router.get("/{key}")
async def get_config_value(
    key: str,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """Obtiene el valor de una configuración específica"""
    require_admin(authorization, access_token)
    
    value = get_config(key, None)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Configuración '{key}' no encontrada")
    
    # Verificar si es secreto
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        is_secret = config.is_secret if config else False
    finally:
        db.close()
    
    return {
        "key": key,
        "value": "********" if is_secret else value,
        "is_secret": is_secret
    }


@router.put("/{key}")
async def update_config_value(
    key: str,
    payload: ConfigUpdateRequest,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """Actualiza el valor de una configuración"""
    require_admin(authorization, access_token)
    
    if payload.key != key:
        raise HTTPException(status_code=400, detail="Key en URL y body no coinciden")
    
    # Verificar si es editable
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if config and not config.is_editable:
            raise HTTPException(status_code=403, detail=f"Configuración '{key}' no es editable")
    finally:
        db.close()
    
    success = set_config(
        key=key,
        value=payload.value,
        description=payload.description,
        updated_by="admin"  # TODO: obtener del token
    )
    
    if success:
        logger.info(f"Configuración actualizada: {key}")
        return {"success": True, "key": key, "message": "Configuración actualizada"}
    else:
        raise HTTPException(status_code=500, detail="Error actualizando configuración")


@router.post("/bulk")
async def update_configs_bulk(
    payload: ConfigBulkUpdateRequest,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """Actualiza múltiples configuraciones a la vez"""
    require_admin(authorization, access_token)
    
    results = []
    for config in payload.configs:
        success = set_config(
            key=config.key,
            value=config.value,
            description=config.description,
            updated_by="admin"
        )
        results.append({
            "key": config.key,
            "success": success
        })
    
    return {
        "results": results,
        "total": len(results),
        "success_count": sum(1 for r in results if r["success"])
    }


# =====================================================
# ENDPOINTS - CONFIGURACIÓN ODOO
# =====================================================

@router.get("/odoo/current")
async def get_odoo_settings(
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Obtiene la configuración actual de Odoo para provisioning de tenants.
    Las contraseñas se muestran enmascaradas.
    """
    require_admin(authorization, access_token)
    
    return {
        "config": get_odoo_config(),
        "source": "Variables de entorno y/o base de datos",
        "editable_via": "/api/settings/odoo"
    }


@router.put("/odoo")
async def update_odoo_settings(
    payload: OdooConfigUpdateRequest,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Actualiza la configuración de Odoo.
    
    Los cambios se guardan en la base de datos y tienen prioridad
    sobre las variables de entorno.
    """
    require_admin(authorization, access_token)
    
    updates = []
    
    # Mapeo de campos a claves de configuración
    field_mapping = {
        "admin_login": ("ODOO_DEFAULT_ADMIN_LOGIN", "odoo", False),
        "admin_password": ("ODOO_DEFAULT_ADMIN_PASSWORD", "odoo", True),
        "master_password": ("ODOO_MASTER_PASSWORD", "odoo", True),
        "db_user": ("ODOO_DB_USER", "odoo", False),
        "db_password": ("ODOO_DB_PASSWORD", "odoo", True),
        "default_lang": ("ODOO_DEFAULT_LANG", "odoo", False),
        "default_country": ("ODOO_DEFAULT_COUNTRY", "odoo", False),
        "base_domain": ("ODOO_BASE_DOMAIN", "odoo", False),
        "template_db": ("ODOO_TEMPLATE_DB", "odoo", False),
    }
    
    for field, (key, category, is_secret) in field_mapping.items():
        value = getattr(payload, field, None)
        if value is not None:
            success = set_config(
                key=key,
                value=value,
                description=f"Configuración Odoo: {field}",
                category=category,
                is_secret=is_secret,
                updated_by="admin"
            )
            updates.append({
                "field": field,
                "key": key,
                "success": success
            })
    
    if not updates:
        return {"message": "No se proporcionaron campos para actualizar"}
    
    logger.info(f"Configuración Odoo actualizada: {[u['field'] for u in updates if u['success']]}")
    
    return {
        "success": True,
        "updates": updates,
        "message": "Configuración de Odoo actualizada. Los cambios aplican inmediatamente."
    }


# =====================================================
# ENDPOINTS - INICIALIZACIÓN
# =====================================================

@router.post("/init-defaults")
async def initialize_default_configs(
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Inicializa las configuraciones por defecto en la base de datos.
    Útil para primera instalación o reset de configuración.
    """
    require_admin(authorization, access_token)
    
    from ..config import (
        ODOO_DEFAULT_ADMIN_LOGIN, ODOO_DEFAULT_ADMIN_PASSWORD,
        ODOO_MASTER_PASSWORD, ODOO_DB_USER, ODOO_DB_PASSWORD,
        ODOO_DEFAULT_LANG, ODOO_DEFAULT_COUNTRY, ODOO_BASE_DOMAIN,
        ODOO_TEMPLATE_DB,
    )

    defaults = [
        # Odoo
        ("ODOO_DEFAULT_ADMIN_LOGIN", ODOO_DEFAULT_ADMIN_LOGIN,
         "Email admin por defecto para nuevos tenants", "odoo", False),
        ("ODOO_DEFAULT_ADMIN_PASSWORD", ODOO_DEFAULT_ADMIN_PASSWORD,
         "Password admin por defecto", "odoo", True),
        ("ODOO_MASTER_PASSWORD", ODOO_MASTER_PASSWORD,
         "Master password de Odoo", "odoo", True),
        ("ODOO_DB_USER", ODOO_DB_USER,
         "Usuario PostgreSQL del servidor Odoo", "odoo", False),
        ("ODOO_DB_PASSWORD", ODOO_DB_PASSWORD,
         "Password PostgreSQL", "odoo", True),
        ("ODOO_DEFAULT_LANG", ODOO_DEFAULT_LANG,
         "Idioma por defecto (es_DO, es_MX, en_US)", "odoo", False),
        ("ODOO_DEFAULT_COUNTRY", ODOO_DEFAULT_COUNTRY, 
         "País por defecto (DO, MX, US)", "odoo", False),
        ("ODOO_BASE_DOMAIN", ODOO_BASE_DOMAIN,
         "Dominio base para URLs de tenants", "odoo", False),
        ("ODOO_TEMPLATE_DB", ODOO_TEMPLATE_DB, 
         "BD template para duplicar al crear tenants", "odoo", False),
        
        # General
        ("APP_NAME", "Sajet ERP SaaS", "Nombre de la aplicación", "general", False),
        ("SUPPORT_EMAIL", "soporte@sajet.us", "Email de soporte", "general", False),
    ]
    
    results = []
    for key, value, description, category, is_secret in defaults:
        # Solo crear si no existe
        existing = get_config(key, None)
        if existing is None:
            success = set_config(key, value, description, category, is_secret, "system")
            results.append({"key": key, "action": "created", "success": success})
        else:
            results.append({"key": key, "action": "skipped", "reason": "already exists"})
    
    return {
        "results": results,
        "created": sum(1 for r in results if r.get("action") == "created" and r.get("success")),
        "skipped": sum(1 for r in results if r.get("action") == "skipped")
    }


@router.get("/env")
async def get_env_vars(
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Muestra las variables de entorno relevantes (para debug).
    Solo disponible en modo desarrollo.
    """
    require_admin(authorization, access_token)
    
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        raise HTTPException(status_code=403, detail="No disponible en producción")
    
    # Variables seguras para mostrar
    safe_vars = [
        "ENVIRONMENT", "APP_PORT", "LOG_LEVEL",
        "ODOO_DEFAULT_ADMIN_LOGIN", "ODOO_DEFAULT_LANG", 
        "ODOO_DEFAULT_COUNTRY", "ODOO_BASE_DOMAIN", "ODOO_TEMPLATE_DB",
        "LXC_CONTAINER_ID", "TENANT_DOMAIN"
    ]
    
    return {
        "environment": env,
        "variables": {
            var: os.getenv(var, "not set")
            for var in safe_vars
        }
    }

