"""
Onboarding Configuration API — Admin-configurable onboarding flow.

Permite al admin:
- Definir qué pasos aparecen (contraseña, perfil, e-CF, confirmación)
- Qué planes son visibles en el onboarding y portal
- El menú del portal de tenant (qué secciones se muestran)
- Textos de bienvenida y branding del onboarding
- Gestión de cuenta: cambio de plan, cancelación, e-mail, facturas, uso
- Qué países activan el cuestionario e-CF

Public endpoint: GET /api/onboarding-config/active  ← usado por CustomerOnboarding.svelte
Admin endpoints: CRUD completo bajo /api/onboarding-config/admin/
"""

from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
import logging

from ..models.database import (
    OnboardingConfig, Plan, SessionLocal,
)
from ..routes.secure_auth import TokenManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding-config", tags=["Onboarding Config"])


# ═══════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════

def _extract_token(request: Request, access_token: Optional[str] = None) -> str:
    token = access_token or request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "No autenticado")
    return token


def _require_admin(request: Request, access_token: str = Cookie(None)) -> dict:
    token = _extract_token(request, access_token)
    try:
        payload = TokenManager.verify_access_token(token)
    except Exception:
        raise HTTPException(401, "Token inválido")
    if payload.get("role") != "admin":
        raise HTTPException(403, "Solo administradores")
    return {"username": payload.get("sub")}


# ═══════════════════════════════════════════
#  DTOs
# ═══════════════════════════════════════════

class OnboardingConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    steps_config: Optional[List[Any]] = None
    visible_plans: Optional[List[str]] = None
    portal_menu: Optional[List[Any]] = None
    welcome_title: Optional[str] = None
    welcome_subtitle: Optional[str] = None
    allow_plan_change: Optional[bool] = None
    allow_cancel: Optional[bool] = None
    allow_email_change: Optional[bool] = None
    show_invoices: Optional[bool] = None
    show_usage: Optional[bool] = None
    ecf_countries: Optional[List[str]] = None
    is_active: Optional[bool] = None


class OnboardingConfigCreate(OnboardingConfigUpdate):
    config_key: str
    display_name: str = "Nueva Configuración"


# ═══════════════════════════════════════════
#  SERIALIZER HELPER
# ═══════════════════════════════════════════

def _serialize(cfg: OnboardingConfig) -> dict:
    return {
        "id": cfg.id,
        "config_key": cfg.config_key,
        "display_name": cfg.display_name,
        "steps_config": cfg.steps_config or [],
        "visible_plans": cfg.visible_plans or [],
        "portal_menu": cfg.portal_menu or [],
        "welcome_title": cfg.welcome_title,
        "welcome_subtitle": cfg.welcome_subtitle,
        "allow_plan_change": cfg.allow_plan_change,
        "allow_cancel": cfg.allow_cancel,
        "allow_email_change": cfg.allow_email_change,
        "show_invoices": cfg.show_invoices,
        "show_usage": cfg.show_usage,
        "ecf_countries": cfg.ecf_countries or ["DO"],
        "is_active": cfg.is_active,
        "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
        "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
    }


def _get_plans_detail(visible_plans: list, db) -> list:
    """Fetches plan data for the plans listed in visible_plans config."""
    plans = db.query(Plan).filter(
        Plan.name.in_(visible_plans),
        Plan.is_active == True,
    ).all()
    plan_map = {p.name: p for p in plans}
    result = []
    for pname in visible_plans:
        p = plan_map.get(pname)
        if p:
            import json
            features = []
            if p.features:
                try:
                    features = json.loads(p.features) if isinstance(p.features, str) else p.features
                except Exception:
                    features = []
            result.append({
                "name": p.name,
                "display_name": p.display_name,
                "description": p.description,
                "base_price": p.base_price,
                "price_per_user": p.price_per_user,
                "included_users": p.included_users,
                "max_users": p.max_users,
                "features": features,
                "stripe_price_id": p.stripe_price_id,
            })
    return result


# ═══════════════════════════════════════════
#  PUBLIC ENDPOINT — no auth required (used by onboarding SPA)
# ═══════════════════════════════════════════

@router.get("/active")
async def get_active_config(request: Request):
    """
    Retorna la configuración activa de onboarding junto con datos de planes.
    Usado por CustomerOnboarding.svelte y TenantPortal.svelte sin autenticación.
    """
    db = SessionLocal()
    try:
        cfg = db.query(OnboardingConfig).filter(
            OnboardingConfig.config_key == "default",
            OnboardingConfig.is_active == True,
        ).first()

        if not cfg:
            # Fallback defaults if no config exists in DB
            return {
                "config_key": "default",
                "display_name": "Configuración Principal",
                "steps_config": [
                    {"step": 0, "key": "password", "label": "Contraseña", "required": True, "visible": True, "condition": None},
                    {"step": 1, "key": "profile", "label": "Perfil", "required": True, "visible": True, "condition": None},
                    {"step": 2, "key": "ecf", "label": "Fiscal (RD)", "required": False, "visible": True, "condition": {"country_in": ["DO"]}},
                    {"step": 3, "key": "confirm", "label": "Confirmación", "required": True, "visible": True, "condition": None},
                ],
                "visible_plans": ["basic", "pro", "enterprise"],
                "plans_detail": [],
                "portal_menu": [],
                "welcome_title": "¡Bienvenido a Sajet ERP!",
                "welcome_subtitle": "Configure su cuenta para comenzar.",
                "allow_plan_change": True,
                "allow_cancel": True,
                "allow_email_change": False,
                "show_invoices": True,
                "show_usage": True,
                "ecf_countries": ["DO"],
            }

        data = _serialize(cfg)
        data["plans_detail"] = _get_plans_detail(cfg.visible_plans or [], db)
        return data
    finally:
        db.close()


# ═══════════════════════════════════════════
#  ADMIN ENDPOINTS
# ═══════════════════════════════════════════

@router.get("/admin")
async def list_configs(request: Request, access_token: str = Cookie(None)):
    """Lista todas las configuraciones de onboarding (admin)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        configs = db.query(OnboardingConfig).order_by(OnboardingConfig.id).all()
        result = []
        for cfg in configs:
            data = _serialize(cfg)
            data["plans_detail"] = _get_plans_detail(cfg.visible_plans or [], db)
            result.append(data)
        return {"items": result, "total": len(result)}
    finally:
        db.close()


@router.get("/admin/{config_key}")
async def get_config(config_key: str, request: Request, access_token: str = Cookie(None)):
    """Obtiene una configuración específica por key (admin)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        cfg = db.query(OnboardingConfig).filter(OnboardingConfig.config_key == config_key).first()
        if not cfg:
            raise HTTPException(404, f"Configuración '{config_key}' no encontrada")
        data = _serialize(cfg)
        data["plans_detail"] = _get_plans_detail(cfg.visible_plans or [], db)

        # Include available plans for the admin editor
        all_plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.sort_order).all()
        data["available_plans"] = [
            {"name": p.name, "display_name": p.display_name, "base_price": p.base_price}
            for p in all_plans
        ]
        return data
    finally:
        db.close()


@router.post("/admin")
async def create_config(data: OnboardingConfigCreate, request: Request, access_token: str = Cookie(None)):
    """Crea una nueva configuración de onboarding (admin)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        existing = db.query(OnboardingConfig).filter(
            OnboardingConfig.config_key == data.config_key
        ).first()
        if existing:
            raise HTTPException(400, f"Ya existe una configuración con key '{data.config_key}'")

        cfg = OnboardingConfig(
            config_key=data.config_key,
            display_name=data.display_name or "Nueva Configuración",
            steps_config=data.steps_config or [],
            visible_plans=data.visible_plans or ["basic", "pro", "enterprise"],
            portal_menu=data.portal_menu or [],
            welcome_title=data.welcome_title,
            welcome_subtitle=data.welcome_subtitle,
            allow_plan_change=data.allow_plan_change if data.allow_plan_change is not None else True,
            allow_cancel=data.allow_cancel if data.allow_cancel is not None else True,
            allow_email_change=data.allow_email_change if data.allow_email_change is not None else False,
            show_invoices=data.show_invoices if data.show_invoices is not None else True,
            show_usage=data.show_usage if data.show_usage is not None else True,
            ecf_countries=data.ecf_countries or ["DO"],
            is_active=data.is_active if data.is_active is not None else True,
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
        logger.info(f"Onboarding config created: {data.config_key}")
        return {"message": "Configuración creada", "config": _serialize(cfg)}
    finally:
        db.close()


@router.put("/admin/{config_key}")
async def update_config(
    config_key: str,
    data: OnboardingConfigUpdate,
    request: Request,
    access_token: str = Cookie(None),
):
    """Actualiza una configuración de onboarding (admin)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        cfg = db.query(OnboardingConfig).filter(OnboardingConfig.config_key == config_key).first()
        if not cfg:
            raise HTTPException(404, f"Configuración '{config_key}' no encontrada")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(cfg, field, value)

        cfg.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cfg)
        logger.info(f"Onboarding config updated: {config_key}")
        return {"message": "Configuración actualizada", "config": _serialize(cfg)}
    finally:
        db.close()


@router.delete("/admin/{config_key}")
async def delete_config(config_key: str, request: Request, access_token: str = Cookie(None)):
    """Elimina una configuración (no se puede eliminar 'default')."""
    _require_admin(request, access_token)
    if config_key == "default":
        raise HTTPException(400, "No se puede eliminar la configuración por defecto")
    db = SessionLocal()
    try:
        cfg = db.query(OnboardingConfig).filter(OnboardingConfig.config_key == config_key).first()
        if not cfg:
            raise HTTPException(404, f"Configuración '{config_key}' no encontrada")
        db.delete(cfg)
        db.commit()
        return {"message": f"Configuración '{config_key}' eliminada"}
    finally:
        db.close()


@router.post("/admin/{config_key}/activate")
async def activate_config(config_key: str, request: Request, access_token: str = Cookie(None)):
    """Activa/desactiva una configuración."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        cfg = db.query(OnboardingConfig).filter(OnboardingConfig.config_key == config_key).first()
        if not cfg:
            raise HTTPException(404, f"Configuración '{config_key}' no encontrada")
        cfg.is_active = not cfg.is_active
        cfg.updated_at = datetime.utcnow()
        db.commit()
        return {"message": f"Configuración {'activada' if cfg.is_active else 'desactivada'}", "is_active": cfg.is_active}
    finally:
        db.close()


@router.get("/admin/{config_key}/preview")
async def preview_config(config_key: str, request: Request, access_token: str = Cookie(None)):
    """Vista previa de la configuración con todos los datos expandidos (admin)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        cfg = db.query(OnboardingConfig).filter(OnboardingConfig.config_key == config_key).first()
        if not cfg:
            raise HTTPException(404, f"Configuración '{config_key}' no encontrada")
        data = _serialize(cfg)
        data["plans_detail"] = _get_plans_detail(cfg.visible_plans or [], db)
        all_plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.sort_order).all()
        data["available_plans"] = [
            {"name": p.name, "display_name": p.display_name, "base_price": p.base_price}
            for p in all_plans
        ]
        return data
    finally:
        db.close()
