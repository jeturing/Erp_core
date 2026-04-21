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
    """Cambiar modo Stripe (test/sandbox/live)."""
    mode: str = Field(..., description="'test', 'sandbox' o 'live'")
    test_secret_key: Optional[str] = None
    test_publishable_key: Optional[str] = None
    test_webhook_secret: Optional[str] = None
    sandbox_secret_key: Optional[str] = None
    sandbox_publishable_key: Optional[str] = None
    sandbox_webhook_secret: Optional[str] = None
    live_secret_key: Optional[str] = None
    live_publishable_key: Optional[str] = None
    live_webhook_secret: Optional[str] = None


class EnvironmentSwitchRequest(BaseModel):
    """Cambiar ambiente activo (dev / test / production)."""
    environment: str = Field(..., description="development, test o production")


# Credenciales organizadas por categoría con metadatos
CREDENTIAL_DEFINITIONS = {
    "gusto": {
        "label": "Gusto Embedded Payroll",
        "items": [
            {"key": "GUSTO_ENV", "description": "Ambiente activo (demo / production)", "is_secret": False, "default": "demo"},
            {"key": "GUSTO_CLIENT_ID", "description": "Client ID de la app Gusto", "is_secret": False},
            {"key": "GUSTO_CLIENT_SECRET", "description": "Client Secret de la app Gusto", "is_secret": True},
            {"key": "GUSTO_API_VERSION", "description": "Versión API de Gusto", "is_secret": False, "default": "2025-06-15"},
            {"key": "GUSTO_REDIRECT_URI", "description": "Redirect URI OAuth de Gusto", "is_secret": False, "default": "https://sajet.us/redirect"},
            {"key": "GUSTO_WEBHOOK_URL", "description": "Webhook público registrado en Gusto", "is_secret": False, "default": "https://sajet.us/api/v1/gusto/webhook"},
            {"key": "GUSTO_WEBHOOK_SECRET", "description": "Secret para validar X-Gusto-Signature", "is_secret": True},
            {"key": "GUSTO_BACKEND_API_TOKEN", "description": "Token interno para llamadas Odoo ↔ SAJET", "is_secret": True},
            {"key": "GUSTO_SCOPES", "description": "Scopes OAuth separados por espacio", "is_secret": False, "default": "public webhook_subscriptions:read webhook_subscriptions:write"},
            {"key": "GUSTO_STATE_SECRET", "description": "Secret para firmar estado OAuth", "is_secret": True},
        ],
    },
    "meta": {
        "label": "Meta Hub / Webhooks",
        "items": [
            {"key": "META_PROXY_BASE_URL", "description": "Base pública del proxy Meta en SAJET", "is_secret": False, "default": "https://sajet.us/meta"},
            {"key": "META_OAUTH_REDIRECT_URI", "description": "URI de redirección OAuth para Meta App", "is_secret": False, "default": "https://sajet.us/meta/oauth/callback"},
            {"key": "META_WEBHOOK_URL", "description": "Webhook público registrado en Meta", "is_secret": False, "default": "https://sajet.us/meta/webhook"},
            {"key": "META_WEBHOOK_BEARER", "description": "Bearer opcional para proteger el endpoint /meta/webhook", "is_secret": True},
            {"key": "META_WEBHOOK_TARGETS", "description": "Hosts destino para fanout (coma separada)", "is_secret": False},
            {"key": "META_WEBHOOK_TARGET_PATHS", "description": "Paths destino por tenant (coma separada)", "is_secret": False, "default": "/jeturing_whatsapp/webhook,/jeturing_meta/webhook"},
        ],
    },
    "delivery_doordash": {
        "label": "Delivery — DoorDash",
        "items": [
            {"key": "DOORDASH_WEBHOOK_URL", "description": "Webhook público de DoorDash en SAJET", "is_secret": False, "default": "https://sajet.us/kds/webhook/doordash-drive"},
            {"key": "DOORDASH_WEBHOOK_BEARER", "description": "Bearer para validar webhook entrante DoorDash", "is_secret": True},
            {"key": "DOORDASH_WEBHOOK_TARGETS", "description": "Hosts destino para fanout DoorDash (coma separada)", "is_secret": False},
        ],
    },
    "delivery_uber": {
        "label": "Delivery — Uber",
        "items": [
            {"key": "UBER_WEBHOOK_URL", "description": "Webhook público de Uber en SAJET", "is_secret": False, "default": "https://sajet.us/kds/webhook/uber"},
            {"key": "UBER_WEBHOOK_BEARER", "description": "Bearer para validar webhook entrante Uber (si aplica)", "is_secret": True},
            {"key": "UBER_WEBHOOK_TARGETS", "description": "Hosts destino para fanout Uber (coma separada)", "is_secret": False},
            {"key": "UBER_CLIENT_ID", "description": "Client ID OAuth de Uber", "is_secret": False},
            {"key": "UBER_CLIENT_SECRET", "description": "Client Secret OAuth de Uber", "is_secret": True},
        ],
    },
    "delivery_pedidosya": {
        "label": "Delivery — PedidosYa",
        "items": [
            {"key": "PEDIDOSYA_WEBHOOK_URL", "description": "Webhook público de PedidosYa en SAJET", "is_secret": False, "default": "https://sajet.us/kds/webhook/pedidosya"},
            {"key": "PEDIDOSYA_WEBHOOK_BEARER", "description": "Bearer para validar webhook entrante PedidosYa", "is_secret": True},
            {"key": "PEDIDOSYA_WEBHOOK_TARGETS", "description": "Hosts destino para fanout PedidosYa (coma separada)", "is_secret": False},
            {"key": "PEDIDOSYA_CLIENT_ID", "description": "Client ID/API key de PedidosYa", "is_secret": False},
            {"key": "PEDIDOSYA_CLIENT_SECRET", "description": "Client Secret de PedidosYa", "is_secret": True},
        ],
    },
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


_STRIPE_APPS = {
    "sajet": {
        "label": "SAJET",
        "base_prefix": "STRIPE_",
        "host": "sajet.us",
    },
    "med": {
        "label": "MED",
        "base_prefix": "STRIPE_MED_",
        "host": "med.sajet.us",
    },
}

_STRIPE_KEY_SUFFIX = {
    "secret": "SECRET_KEY",
    "publishable": "PUBLISHABLE_KEY",
    "webhook": "WEBHOOK_SECRET",
}

_STRIPE_MODE_LABELS = {
    "test": "Pruebas",
    "sandbox": "Aislado",
    "live": "Producción",
}


def _normalize_stripe_app(app: Optional[str]) -> str:
    value = (app or "sajet").strip().lower()
    if value not in _STRIPE_APPS:
        raise HTTPException(status_code=400, detail="App inválida. Use 'sajet' o 'med'")
    return value


def _stripe_mode_key(app: str) -> str:
    return f"{_STRIPE_APPS[app]['base_prefix']}MODE"


def _stripe_active_key(app: str, kind: str) -> str:
    return f"{_STRIPE_APPS[app]['base_prefix']}{_STRIPE_KEY_SUFFIX[kind]}"


def _stripe_stored_key(app: str, mode: str, kind: str) -> str:
    return f"{_STRIPE_APPS[app]['base_prefix']}{mode.upper()}_{_STRIPE_KEY_SUFFIX[kind]}"


def _get_runtime_env_value(key: str) -> str:
    return os.getenv(key, "") or ""


def _get_config_or_env(key: str, default: str = "") -> str:
    value = get_config(key, None)
    if value is not None and value != "":
        return value
    env_value = _get_runtime_env_value(key)
    return env_value if env_value else default


def _infer_stripe_mode_from_key(secret_key: str) -> str:
    key = (secret_key or "").lower()
    if not key:
        return "unknown"
    if "rk_live" in key or "sk_live" in key:
        return "live"
    if "sandbox" in key:
        return "sandbox"
    if "test" in key:
        return "test"
    return "unknown"


def _mask_key_prefix(value: str, limit: int = 20) -> str:
    if not value:
        return ""
    return value[:limit] + "..." if len(value) > limit else value


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
    app: str = Query("sajet", description="App Stripe: sajet o med"),
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Obtiene el modo actual de Stripe por app (sajet/med) y las keys configuradas.
    """
    require_admin(authorization, access_token)

    normalized_app = _normalize_stripe_app(app)
    current_sk = _get_config_or_env(_stripe_active_key(normalized_app, "secret"))
    current_pk = _get_config_or_env(_stripe_active_key(normalized_app, "publishable"))
    mode = _get_config_or_env(_stripe_mode_key(normalized_app), "") or _infer_stripe_mode_from_key(current_sk)
    if mode not in _STRIPE_MODE_LABELS:
        mode = "test"

    detected = _infer_stripe_mode_from_key(current_sk)
    has_test = bool(_get_config_or_env(_stripe_stored_key(normalized_app, "test", "secret")))
    has_sandbox = bool(_get_config_or_env(_stripe_stored_key(normalized_app, "sandbox", "secret")))
    has_live = bool(_get_config_or_env(_stripe_stored_key(normalized_app, "live", "secret")) or (current_sk and "live" in current_sk.lower()))
    coherence_warning = None
    if detected != "unknown" and mode != detected:
        coherence_warning = f"Modo guardado={mode} pero la key activa parece {detected}"

    return {
        "success": True,
        "app": normalized_app,
        "app_label": _STRIPE_APPS[normalized_app]["label"],
        "app_host": _STRIPE_APPS[normalized_app]["host"],
        "mode": mode,
        "mode_label": _STRIPE_MODE_LABELS.get(mode, mode.upper()),
        "detected_mode": detected,
        "active_secret_key_prefix": _mask_key_prefix(current_sk, 12),
        "active_publishable_key": _mask_key_prefix(current_pk, 20),
        "has_test_keys": has_test,
        "has_sandbox_keys": has_sandbox,
        "has_live_keys": has_live,
        "coherence_warning": coherence_warning,
        "requires_restart": False,
        "cache_ttl_seconds": 5,
    }


@router.post("/stripe/mode")
async def set_stripe_mode(
    payload: StripeModeRequest,
    app: str = Query("sajet", description="App Stripe: sajet o med"),
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Cambia el modo Stripe por app entre test, sandbox y live.
    
    Flujo:
    1. Si se proporcionan keys nuevas, las guarda en STRIPE_{TEST/LIVE}_*
    2. Copia las keys del modo seleccionado a STRIPE_SECRET_KEY, etc.
    3. Actualiza STRIPE_MODE
    
    Los cambios se guardan en BD (system_config) y aplican en el próximo request.
    Para aplicar globalmente se requiere reiniciar el servicio.
    """
    require_admin(authorization, access_token)

    normalized_app = _normalize_stripe_app(app)

    if payload.mode not in ("test", "sandbox", "live"):
        raise HTTPException(status_code=400, detail="Modo debe ser 'test', 'sandbox' o 'live'")

    changes = []

    payload_keys = {
        "test": {
            "secret": payload.test_secret_key,
            "publishable": payload.test_publishable_key,
            "webhook": payload.test_webhook_secret,
        },
        "sandbox": {
            "secret": payload.sandbox_secret_key,
            "publishable": payload.sandbox_publishable_key,
            "webhook": payload.sandbox_webhook_secret,
        },
        "live": {
            "secret": payload.live_secret_key,
            "publishable": payload.live_publishable_key,
            "webhook": payload.live_webhook_secret,
        },
    }

    for mode_name, values in payload_keys.items():
        for kind, value in values.items():
            if not value:
                continue
            key_name = _stripe_stored_key(normalized_app, mode_name, kind)
            is_secret = kind != "publishable"
            desc = f"Stripe {mode_name.upper()} {kind} ({_STRIPE_APPS[normalized_app]['label']})"
            set_config(key_name, value, desc, "stripe", is_secret, "admin")
            changes.append(key_name)

    sk = _get_config_or_env(_stripe_stored_key(normalized_app, payload.mode, "secret"))
    pk = _get_config_or_env(_stripe_stored_key(normalized_app, payload.mode, "publishable"))
    wh = _get_config_or_env(_stripe_stored_key(normalized_app, payload.mode, "webhook"))

    if not sk:
        raise HTTPException(
            status_code=400,
            detail=f"No hay Secret Key configurada para modo '{payload.mode}' en app '{normalized_app}'. Primero guarde las credenciales."
        )

    detected = _infer_stripe_mode_from_key(sk)
    if payload.mode == "live" and detected != "live":
        raise HTTPException(status_code=400, detail="No se puede activar LIVE con una clave que no sea live")
    if payload.mode == "sandbox" and detected not in ("sandbox", "test"):
        logger.warning("Sandbox configurado con una clave sin patrón sandbox/test para app=%s", normalized_app)

    # Activar las keys del modo seleccionado
    set_config(_stripe_active_key(normalized_app, "secret"), sk, f"Stripe SK activa ({payload.mode}) [{normalized_app}]", "stripe", True, "admin")
    set_config(_stripe_active_key(normalized_app, "publishable"), pk, f"Stripe PK activa ({payload.mode}) [{normalized_app}]", "stripe", False, "admin")
    if wh:
        set_config(_stripe_active_key(normalized_app, "webhook"), wh, f"Stripe WH activa ({payload.mode}) [{normalized_app}]", "stripe", True, "admin")
    set_config(_stripe_mode_key(normalized_app), payload.mode, f"Modo Stripe activo ({normalized_app})", "stripe", False, "admin")

    logger.info("Stripe modo cambiado app=%s mode=%s — SK prefix: %s", normalized_app, payload.mode, _mask_key_prefix(sk, 12))

    return {
        "success": True,
        "app": normalized_app,
        "mode": payload.mode,
        "mode_label": _STRIPE_MODE_LABELS.get(payload.mode, payload.mode.upper()),
        "message": f"Stripe {_STRIPE_APPS[normalized_app]['label']} cambiado a modo {payload.mode.upper()}.",
        "active_key_prefix": _mask_key_prefix(sk, 12),
        "changes": changes,
        "requires_restart": False,
        "cache_ttl_seconds": 5,
    }


# =====================================================
# ENDPOINTS - ENVIRONMENT SWITCH
# =====================================================

_ENV_DEFINITIONS = {
    "development": {
        "label": "Desarrollo",
        "env_file": ".env",
        "description": "Ambiente local de desarrollo — BD local, Stripe test",
        "color": "blue",
    },
    "test": {
        "label": "Pruebas",
        "env_file": ".env.test",
        "description": "Ambiente de pruebas — BD local 10.10.10.20, Stripe test",
        "color": "amber",
    },
    "production": {
        "label": "Producción",
        "env_file": ".env.production",
        "description": "Ambiente productivo — BD HA 10.10.10.137, Stripe live",
        "color": "emerald",
    },
}


@router.get("/environment/current")
async def get_current_environment(
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Obtiene el ambiente activo y la info de cada ambiente disponible.
    """
    require_admin(authorization, access_token)

    from ..config import get_env_info, ACTIVE_ENV_FILE

    current = get_env_info()
    erp_env = current["erp_env"]

    # Check which .env files exist on disk
    import pathlib
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    environments = []
    for env_key, env_def in _ENV_DEFINITIONS.items():
        env_path = project_root / env_def["env_file"]
        # Parse DB host from file if it exists
        db_host = ""
        stripe_mode_hint = ""
        if env_path.exists():
            content = env_path.read_text()
            for line in content.splitlines():
                if line.startswith("DATABASE_URL="):
                    # Extract host:port
                    val = line.split("=", 1)[1]
                    if "@" in val:
                        db_host = val.split("@")[1].split("/")[0]
                if line.startswith("STRIPE_SECRET_KEY="):
                    val = line.split("=", 1)[1]
                    stripe_mode_hint = "live" if "live" in val else "test"

        environments.append({
            "key": env_key,
            "label": env_def["label"],
            "description": env_def["description"],
            "env_file": env_def["env_file"],
            "color": env_def["color"],
            "available": env_path.exists(),
            "is_active": env_key == erp_env,
            "db_host": db_host,
            "stripe_mode": stripe_mode_hint,
        })

    return {
        "success": True,
        "current": erp_env,
        "env_file": ACTIVE_ENV_FILE,
        "database_host": current["database_host"],
        "database_name": current["database_name"],
        "stripe_mode": current["stripe_mode"],
        "app_url": current["app_url"],
        "environments": environments,
    }


@router.put("/environment/switch")
async def switch_environment(
    payload: EnvironmentSwitchRequest,
    authorization: str = Header(None),
    access_token: str = Cookie(None)
):
    """
    Cambia el ambiente activo modificando la variable ERP_ENV en el servicio systemd.
    Requiere reinicio del servicio para tomar efecto.
    """
    require_admin(authorization, access_token)

    target = payload.environment.lower().strip()
    if target not in _ENV_DEFINITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Ambiente '{target}' no válido. Opciones: {list(_ENV_DEFINITIONS.keys())}"
        )

    # Verify the target .env file exists
    import pathlib
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    env_file = project_root / _ENV_DEFINITIONS[target]["env_file"]
    if not env_file.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Archivo {_ENV_DEFINITIONS[target]['env_file']} no encontrado en el servidor"
        )

    from ..config import get_env_info
    current = get_env_info()
    if current["erp_env"] == target:
        return {
            "success": True,
            "message": f"Ya estás en el ambiente '{target}'",
            "requires_restart": False,
            "current": target,
        }

    # Update systemd service to use the new ERP_ENV
    import subprocess
    service_path = "/etc/systemd/system/erp-core.service"
    try:
        with open(service_path, "r") as f:
            content = f.read()

        # Replace ERP_ENV line
        import re as _re
        new_content = _re.sub(
            r'Environment="ERP_ENV=\w+"',
            f'Environment="ERP_ENV={target}"',
            content
        )

        if new_content == content:
            # ERP_ENV line might not exist yet, add it after [Service]
            new_content = content.replace(
                'WorkingDirectory=',
                f'Environment="ERP_ENV={target}"\nWorkingDirectory='
            )

        with open(service_path, "w") as f:
            f.write(new_content)

        # Reload systemd and restart
        subprocess.run(["systemctl", "daemon-reload"], check=True, capture_output=True)
        subprocess.Popen(["systemctl", "restart", "erp-core"])

        logger.warning(f"⚠️ ENVIRONMENT SWITCH: {current['erp_env']} → {target} — Service restarting...")

        return {
            "success": True,
            "message": f"Ambiente cambiado a '{_ENV_DEFINITIONS[target]['label']}'. El servicio se está reiniciando...",
            "requires_restart": True,
            "previous": current["erp_env"],
            "current": target,
            "target_db": _ENV_DEFINITIONS[target]["description"],
        }
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Sin permisos para modificar el servicio systemd. El proceso debe correr como root o tener permisos de escritura."
        )
    except Exception as e:
        logger.error(f"Error switching environment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        # Gusto
        ("GUSTO_ENV", "demo", "Ambiente activo de Gusto (demo / production)", "gusto", False),
        ("GUSTO_API_VERSION", "2025-06-15", "Versión API de Gusto", "gusto", False),
        ("GUSTO_REDIRECT_URI", "https://sajet.us/redirect", "Redirect URI OAuth de Gusto", "gusto", False),
        ("GUSTO_WEBHOOK_URL", "https://sajet.us/api/v1/gusto/webhook", "Webhook URL pública para Gusto", "gusto", False),
        ("GUSTO_BACKEND_API_TOKEN", "", "Token interno para llamadas Odoo ↔ SAJET", "gusto", True),
        ("GUSTO_SCOPES", "public webhook_subscriptions:read webhook_subscriptions:write", "Scopes OAuth de Gusto", "gusto", False),

        # Meta
        ("META_PROXY_BASE_URL", "https://sajet.us/meta", "Base pública del proxy Meta en SAJET", "meta", False),
        ("META_OAUTH_REDIRECT_URI", "https://sajet.us/meta/oauth/callback", "Redirect URI OAuth de Meta", "meta", False),
        ("META_WEBHOOK_URL", "https://sajet.us/meta/webhook", "Webhook URL pública para Meta", "meta", False),
        ("META_WEBHOOK_BEARER", "", "Bearer opcional para proteger /meta/webhook", "meta", True),
        ("META_WEBHOOK_TARGET_PATHS", "/jeturing_whatsapp/webhook,/jeturing_meta/webhook", "Paths destino para fanout Meta", "meta", False),

        # DoorDash
        ("DOORDASH_WEBHOOK_URL", "https://sajet.us/kds/webhook/doordash-drive", "Webhook URL pública para DoorDash", "delivery_doordash", False),
        ("DOORDASH_WEBHOOK_BEARER", "", "Bearer para validar webhook DoorDash", "delivery_doordash", True),

        # Uber
        ("UBER_WEBHOOK_URL", "https://sajet.us/kds/webhook/uber", "Webhook URL pública para Uber", "delivery_uber", False),
        ("UBER_WEBHOOK_BEARER", "", "Bearer para validar webhook Uber (si aplica)", "delivery_uber", True),
        ("UBER_CLIENT_ID", "", "Client ID OAuth de Uber", "delivery_uber", False),
        ("UBER_CLIENT_SECRET", "", "Client Secret OAuth de Uber", "delivery_uber", True),

        # PedidosYa
        ("PEDIDOSYA_WEBHOOK_URL", "https://sajet.us/kds/webhook/pedidosya", "Webhook URL pública para PedidosYa", "delivery_pedidosya", False),
        ("PEDIDOSYA_WEBHOOK_BEARER", "", "Bearer para validar webhook PedidosYa", "delivery_pedidosya", True),
        ("PEDIDOSYA_CLIENT_ID", "", "Client ID/API key de PedidosYa", "delivery_pedidosya", False),
        ("PEDIDOSYA_CLIENT_SECRET", "", "Client Secret de PedidosYa", "delivery_pedidosya", True),

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

