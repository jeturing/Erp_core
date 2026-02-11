"""
Settings Routes - Configuración del sistema administrable desde /admin
"""
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from ..models.database import (
    SystemConfig, SessionLocal, get_config, set_config, get_all_configs
)
from ..services.odoo_database_manager import get_odoo_config
from .auth import verify_token
import logging
import os

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
# HELPERS
# =====================================================

def require_admin(authorization: str = None):
    """Verifica que el usuario sea admin"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        token = authorization[7:]
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
    authorization: str = Header(None)
):
    """
    Lista todas las configuraciones del sistema.
    
    Categorías disponibles:
    - odoo: Configuración de Odoo/tenants
    - stripe: Configuración de pagos
    - security: Configuración de seguridad
    - general: Configuración general
    """
    require_admin(authorization)
    
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


@router.get("/{key}")
async def get_config_value(
    key: str,
    authorization: str = Header(None)
):
    """Obtiene el valor de una configuración específica"""
    require_admin(authorization)
    
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
    authorization: str = Header(None)
):
    """Actualiza el valor de una configuración"""
    require_admin(authorization)
    
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
    authorization: str = Header(None)
):
    """Actualiza múltiples configuraciones a la vez"""
    require_admin(authorization)
    
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
async def get_odoo_settings(authorization: str = Header(None)):
    """
    Obtiene la configuración actual de Odoo para provisioning de tenants.
    Las contraseñas se muestran enmascaradas.
    """
    require_admin(authorization)
    
    return {
        "config": get_odoo_config(),
        "source": "Variables de entorno y/o base de datos",
        "editable_via": "/api/settings/odoo"
    }


@router.put("/odoo")
async def update_odoo_settings(
    payload: OdooConfigUpdateRequest,
    authorization: str = Header(None)
):
    """
    Actualiza la configuración de Odoo.
    
    Los cambios se guardan en la base de datos y tienen prioridad
    sobre las variables de entorno.
    """
    require_admin(authorization)
    
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
async def initialize_default_configs(authorization: str = Header(None)):
    """
    Inicializa las configuraciones por defecto en la base de datos.
    Útil para primera instalación o reset de configuración.
    """
    require_admin(authorization)
    
    defaults = [
        # Odoo
        ("ODOO_DEFAULT_ADMIN_LOGIN", os.getenv("ODOO_DEFAULT_ADMIN_LOGIN", "admin@sajet.us"), 
         "Email admin por defecto para nuevos tenants", "odoo", False),
        ("ODOO_DEFAULT_ADMIN_PASSWORD", os.getenv("ODOO_DEFAULT_ADMIN_PASSWORD", "321Abcd."), 
         "Password admin por defecto", "odoo", True),
        ("ODOO_MASTER_PASSWORD", os.getenv("ODOO_MASTER_PASSWORD", "admin"), 
         "Master password de Odoo", "odoo", True),
        ("ODOO_DB_USER", os.getenv("ODOO_DB_USER", "Jeturing"), 
         "Usuario PostgreSQL del servidor Odoo", "odoo", False),
        ("ODOO_DB_PASSWORD", os.getenv("ODOO_DB_PASSWORD", "123Abcd."), 
         "Password PostgreSQL", "odoo", True),
        ("ODOO_DEFAULT_LANG", os.getenv("ODOO_DEFAULT_LANG", "es_DO"), 
         "Idioma por defecto (es_DO, es_MX, en_US)", "odoo", False),
        ("ODOO_DEFAULT_COUNTRY", os.getenv("ODOO_DEFAULT_COUNTRY", "DO"), 
         "País por defecto (DO, MX, US)", "odoo", False),
        ("ODOO_BASE_DOMAIN", os.getenv("ODOO_BASE_DOMAIN", "sajet.us"), 
         "Dominio base para URLs de tenants", "odoo", False),
        ("ODOO_TEMPLATE_DB", os.getenv("ODOO_TEMPLATE_DB", "template_tenant"), 
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
async def get_env_vars(authorization: str = Header(None)):
    """
    Muestra las variables de entorno relevantes (para debug).
    Solo disponible en modo desarrollo.
    """
    require_admin(authorization)
    
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
