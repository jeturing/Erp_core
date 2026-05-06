"""
Branding Routes — Épica 10: Partner White-Label Branding Profiles
- POST /api/branding/profiles       → Crear perfil de branding
- GET  /api/branding/profiles       → Lista perfiles
- GET  /api/branding/profiles/{id}  → Detalle
- PUT  /api/branding/profiles/{id}  → Actualizar
- GET  /api/branding/resolve/{domain} → Resolver branding por dominio
- GET  /api/branding/tenant/{subdomain} → Resolver branding por subdomain del tenant
- POST /api/branding/admin/enable-whitelabel → Admin habilita WL para partner
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request, Cookie
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import logging
from pathlib import Path
from uuid import uuid4

from ..models.database import PartnerBrandingProfile, Partner, Customer, get_db
from .roles import _require_admin

router = APIRouter(prefix="/api/branding", tags=["Branding"])
logger = logging.getLogger(__name__)

# ── Defaults de Jeturing (fallback cuando no hay branding de partner) ──
JETURING_DEFAULTS = {
    "brand_name": "Jeturing",
    "product_name": "Sajet",
    "logo_url": "/jeturing_branding/static/img/JEturing.png",
    "favicon_url": None,
    "primary_color": "#4F46E5",
    "secondary_color": "#7C3AED",
    "support_email": "help@jeturing.com",
    "support_url": "https://jeturing.com/help",
    "custom_css": None,
    "is_partner_branded": False,
}


class CreateBrandingProfile(BaseModel):
    partner_id: int
    brand_name: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#1a73e8"
    secondary_color: str = "#ffffff"
    custom_css: Optional[str] = None
    custom_domain: Optional[str] = None
    support_email: Optional[str] = None
    support_url: Optional[str] = None
    terms_url: Optional[str] = None
    privacy_url: Optional[str] = None


class UpdateBrandingProfile(BaseModel):
    brand_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_css: Optional[str] = None
    custom_domain: Optional[str] = None
    support_email: Optional[str] = None
    support_url: Optional[str] = None
    terms_url: Optional[str] = None
    privacy_url: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/profiles")
def create_branding_profile(
    payload: CreateBrandingProfile,
    db: Session = Depends(get_db),
):
    """Crear perfil de branding para un partner."""
    partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    existing = db.query(PartnerBrandingProfile).filter(
        PartnerBrandingProfile.partner_id == payload.partner_id
    ).first()
    if existing:
        raise HTTPException(409, f"Partner already has branding profile: id={existing.id}")

    profile = PartnerBrandingProfile(
        partner_id=payload.partner_id,
        brand_name=payload.brand_name,
        logo_url=payload.logo_url,
        favicon_url=payload.favicon_url,
        primary_color=payload.primary_color,
        secondary_color=payload.secondary_color,
        custom_css=payload.custom_css,
        custom_domain=payload.custom_domain,
        support_email=payload.support_email,
        support_url=payload.support_url,
        terms_url=payload.terms_url,
        privacy_url=payload.privacy_url,
        is_active=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "id": profile.id,
        "partner_id": profile.partner_id,
        "brand_name": profile.brand_name,
        "is_active": profile.is_active,
    }


@router.get("/profiles")
def list_branding_profiles(
    partner_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    q = db.query(PartnerBrandingProfile)
    if partner_id:
        q = q.filter(PartnerBrandingProfile.partner_id == partner_id)
    if active_only:
        q = q.filter(PartnerBrandingProfile.is_active == True)

    profiles = q.all()
    return {
        "total": len(profiles),
        "profiles": [
            {
                "id": p.id,
                "partner_id": p.partner_id,
                "brand_name": p.brand_name,
                "logo_url": p.logo_url,
                "primary_color": p.primary_color,
                "custom_domain": p.custom_domain,
                "is_active": p.is_active,
            }
            for p in profiles
        ],
    }


@router.get("/profiles/{profile_id}")
def get_branding_profile(profile_id: int, db: Session = Depends(get_db)):
    p = db.query(PartnerBrandingProfile).filter(PartnerBrandingProfile.id == profile_id).first()
    if not p:
        raise HTTPException(404, "Branding profile not found")
    return {
        "id": p.id,
        "partner_id": p.partner_id,
        "brand_name": p.brand_name,
        "logo_url": p.logo_url,
        "favicon_url": p.favicon_url,
        "primary_color": p.primary_color,
        "secondary_color": p.secondary_color,
        "custom_css": p.custom_css,
        "custom_domain": p.custom_domain,
        "support_email": p.support_email,
        "support_url": p.support_url,
        "terms_url": p.terms_url,
        "privacy_url": p.privacy_url,
        "is_active": p.is_active,
    }


@router.put("/profiles/{profile_id}")
def update_branding_profile(
    profile_id: int,
    payload: UpdateBrandingProfile,
    db: Session = Depends(get_db),
):
    p = db.query(PartnerBrandingProfile).filter(PartnerBrandingProfile.id == profile_id).first()
    if not p:
        raise HTTPException(404, "Branding profile not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(p, key, value)

    db.commit()
    db.refresh(p)

    return {
        "id": p.id,
        "brand_name": p.brand_name,
        "is_active": p.is_active,
        "updated": list(update_data.keys()),
    }


@router.get("/tenant/{subdomain}")
def resolve_branding_by_subdomain(subdomain: str, db: Session = Depends(get_db)):
    """
    Resuelve branding de partner por subdomain del tenant.
    Público — no requiere autenticación. Usado por Odoo para branding dinámico.
    
    Flow: subdomain → Customer → partner_id → Partner → PartnerBrandingProfile
    Si no hay partner o no tiene branding configurado → defaults Jeturing.
    """
    try:
        customer = db.query(Customer).filter(Customer.subdomain == subdomain).first()
        if not customer or not customer.partner_id:
            logger.debug(f"[branding] No partner for subdomain '{subdomain}', returning defaults")
            return JETURING_DEFAULTS

        profile = db.query(PartnerBrandingProfile).filter(
            PartnerBrandingProfile.partner_id == customer.partner_id,
            PartnerBrandingProfile.is_active == True,
        ).first()

        if not profile:
            # Partner existe pero no tiene branding profile → check campos Partner
            partner = db.query(Partner).filter(Partner.id == customer.partner_id).first()
            if partner and partner.brand_name:
                return {
                    "brand_name": partner.brand_name or JETURING_DEFAULTS["brand_name"],
                    "product_name": partner.brand_name or JETURING_DEFAULTS["product_name"],
                    "logo_url": partner.logo_url or JETURING_DEFAULTS["logo_url"],
                    "favicon_url": JETURING_DEFAULTS["favicon_url"],
                    "primary_color": partner.brand_color_primary or JETURING_DEFAULTS["primary_color"],
                    "secondary_color": partner.brand_color_accent or JETURING_DEFAULTS["secondary_color"],
                    "support_email": partner.smtp_from_email or JETURING_DEFAULTS["support_email"],
                    "support_url": JETURING_DEFAULTS["support_url"],
                    "custom_css": None,
                    "is_partner_branded": True,
                }
            logger.debug(f"[branding] Partner {customer.partner_id} has no branding profile, returning defaults")
            return JETURING_DEFAULTS

        return {
            "brand_name": profile.brand_name or JETURING_DEFAULTS["brand_name"],
            "product_name": profile.brand_name or JETURING_DEFAULTS["product_name"],
            "logo_url": profile.logo_url or JETURING_DEFAULTS["logo_url"],
            "favicon_url": profile.favicon_url or JETURING_DEFAULTS["favicon_url"],
            "primary_color": profile.primary_color or JETURING_DEFAULTS["primary_color"],
            "secondary_color": profile.secondary_color or JETURING_DEFAULTS["secondary_color"],
            "support_email": profile.support_email or JETURING_DEFAULTS["support_email"],
            "support_url": profile.support_url or JETURING_DEFAULTS["support_url"],
            "portal_url": profile.portal_url,
            "terms_url": profile.terms_url,
            "privacy_url": profile.privacy_url,
            "custom_css": profile.custom_css,
            "is_partner_branded": True,
        }
    except Exception as e:
        logger.error(f"[branding] Error resolving branding for '{subdomain}': {e}")
        return JETURING_DEFAULTS


@router.get("/resolve/{domain}")
def resolve_branding_by_domain(domain: str, db: Session = Depends(get_db)):
    """
    Resuelve el perfil de branding por dominio personalizado.
    El frontend usa esto para renderizar white-label.
    """
    profile = db.query(PartnerBrandingProfile).filter(
        PartnerBrandingProfile.custom_domain == domain,
        PartnerBrandingProfile.is_active == True,
    ).first()

    if not profile:
        # Retornar defaults de Jeturing
        return {
            "brand_name": "Sajet",
            "logo_url": "/static/logo.svg",
            "favicon_url": "/static/favicon.ico",
            "primary_color": "#1a73e8",
            "secondary_color": "#ffffff",
            "custom_css": None,
            "support_email": "support@sajet.us",
            "is_white_label": False,
        }

    return {
        "brand_name": profile.brand_name,
        "logo_url": profile.logo_url,
        "favicon_url": profile.favicon_url,
        "primary_color": profile.primary_color,
        "secondary_color": profile.secondary_color,
        "custom_css": profile.custom_css,
        "support_email": profile.support_email,
        "support_url": profile.support_url,
        "terms_url": profile.terms_url,
        "privacy_url": profile.privacy_url,
        "is_white_label": True,
        "partner_id": profile.partner_id,
    }


# ═══════════════════════════════════════════════
# ADMIN — Habilitar/deshabilitar White-Label
# ═══════════════════════════════════════════════

class EnableWhiteLabelRequest(BaseModel):
    partner_id: int
    enabled: bool = True


@router.post("/admin/enable-whitelabel")
def admin_enable_whitelabel(
    payload: EnableWhiteLabelRequest,
    db: Session = Depends(get_db),
):
    """
    Admin habilita o deshabilita la marca blanca para un partner.
    Esto es un gating: el partner no puede usar /branding PUT sin este flag.
    """
    partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
    if not partner:
        raise HTTPException(404, "Partner not found")

    partner.white_label_enabled = payload.enabled
    db.commit()

    return {
        "success": True,
        "partner_id": partner.id,
        "company_name": partner.company_name,
        "white_label_enabled": partner.white_label_enabled,
        "message": f"Marca Blanca {'habilitada' if payload.enabled else 'deshabilitada'} para {partner.company_name}",
    }


@router.post("/profiles/{profile_id}/assets/{asset_type}")
async def upload_branding_asset(
    profile_id: int,
    asset_type: str,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Sube assets de branding: logo, favicon y og image."""
    _require_admin(request, access_token)

    profile = db.query(PartnerBrandingProfile).filter(PartnerBrandingProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(404, "Branding profile not found")

    normalized_type = (asset_type or "").strip().lower()
    if normalized_type not in {"logo", "favicon", "og"}:
        raise HTTPException(400, "asset_type inválido. Usa: logo | favicon | og")

    allowed_mime_by_asset = {
        "logo": {"image/png", "image/jpeg", "image/webp", "image/svg+xml"},
        "favicon": {"image/png", "image/x-icon", "image/vnd.microsoft.icon", "image/svg+xml"},
        "og": {"image/png", "image/jpeg", "image/webp"},
    }
    max_size_by_asset = {
        "logo": 3 * 1024 * 1024,
        "favicon": 1 * 1024 * 1024,
        "og": 5 * 1024 * 1024,
    }

    ext = Path(file.filename or "").suffix.lower() if file.filename else ""
    if not ext:
        ext = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
            "image/x-icon": ".ico",
            "image/vnd.microsoft.icon": ".ico",
        }.get(file.content_type or "", "")

    allowed_ext_by_asset = {
        "logo": {".png", ".jpg", ".jpeg", ".webp", ".svg"},
        "favicon": {".png", ".ico", ".svg"},
        "og": {".png", ".jpg", ".jpeg", ".webp"},
    }
    if ext not in allowed_ext_by_asset[normalized_type]:
        raise HTTPException(400, f"Formato no soportado para {normalized_type}: {sorted(allowed_ext_by_asset[normalized_type])}")

    if file.content_type and file.content_type not in allowed_mime_by_asset[normalized_type]:
        raise HTTPException(400, f"MIME no soportado para {normalized_type}: {file.content_type}")

    base_dir = Path("/opt/Erp_core/static/branding/partners") / str(profile.partner_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{normalized_type}-{uuid4().hex}{ext}"
    target = base_dir / filename

    content = await file.read()
    if not content:
        raise HTTPException(400, "Archivo vacío")

    max_size = max_size_by_asset[normalized_type]
    if len(content) > max_size:
        raise HTTPException(400, f"Archivo excede {max_size // (1024 * 1024)}MB para {normalized_type}")

    target.write_bytes(content)
    asset_url = f"/static/branding/partners/{profile.partner_id}/{filename}"

    updated_field = None
    if normalized_type == "logo":
        profile.logo_url = asset_url
        updated_field = "logo_url"
    elif normalized_type == "favicon":
        profile.favicon_url = asset_url
        updated_field = "favicon_url"

    db.commit()

    return {
        "success": True,
        "data": {
            "profile_id": profile.id,
            "asset_type": normalized_type,
            "asset_url": asset_url,
            "updated_field": updated_field,
        },
        "meta": {
            "content_type": file.content_type,
            "size": len(content),
        },
    }
