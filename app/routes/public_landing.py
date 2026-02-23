"""
Public Landing API — Endpoints sin autenticación para la landing page de Sajet.us

Todos los endpoints aquí son públicos (sin JWT).
Diseñados para ser cacheados en CDN (Cloudflare) con TTL de 5-15 min.

Endpoints:
- GET /api/public/plans          → Planes activos con features y precios
- GET /api/public/stats          → Métricas públicas (empresas, partners, uptime)
- GET /api/public/modules        → Features/módulos agrupados por categoría
- GET /api/public/packages       → Blueprints/industrias
- GET /api/public/testimonials   → Testimonios gestionables
- GET /api/public/partners       → Partners activos para selección en onboarding
- GET /api/public/partner/{code} → Branding + planes de un partner específico
- GET /api/public/content        → Contenido CMS de secciones de la landing
- POST /api/public/calculate     → Calculadora de precios por plan + usuarios
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
import logging

from ..models.database import (
    Plan, Customer, Partner, PartnerBrandingProfile, PartnerPricingOverride,
    ModuleCatalog, ModulePackage, ModulePackageItem,
    ServiceCatalogItem, ServiceCategory, PlanCatalogLink,
    Testimonial, LandingSection, Translation, AccountantTenantAccess,
    SessionLocal, PartnerStatus, SubscriptionStatus, Subscription,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public", tags=["Public Landing"])


# ═══════════════════════════════════════════
#  DTOs
# ═══════════════════════════════════════════

class PriceCalculateRequest(BaseModel):
    plan_name: str
    user_count: int = 1
    billing_period: str = "monthly"     # "monthly" | "annual"
    partner_code: Optional[str] = None


# ═══════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════

def _parse_features(plan: Plan) -> list:
    """Parse features JSON from Plan model."""
    if not plan.features:
        return []
    try:
        return json.loads(plan.features) if isinstance(plan.features, str) else plan.features
    except Exception:
        return []


def _plan_to_dict(plan: Plan, include_stripe: bool = False) -> dict:
    """Serialize Plan for public API."""
    data = {
        "name": plan.name,
        "display_name": plan.display_name,
        "description": plan.description,
        "base_price": plan.base_price,
        "price_per_user": plan.price_per_user,
        "included_users": plan.included_users,
        "max_users": plan.max_users,
        "max_companies": plan.max_companies,
        "max_domains": plan.max_domains,
        "max_storage_mb": plan.max_storage_mb,
        "currency": plan.currency,
        "features": _parse_features(plan),
        "is_highlighted": getattr(plan, "is_highlighted", False),
        "trial_days": getattr(plan, "trial_days", 14),
        "annual_discount_percent": getattr(plan, "annual_discount_percent", 20),
        "sort_order": plan.sort_order,
    }
    if include_stripe:
        data["stripe_price_id"] = plan.stripe_price_id
    return data


# ═══════════════════════════════════════════
#  GET /api/public/plans
# ═══════════════════════════════════════════

@router.get("/plans")
async def get_public_plans():
    """
    Retorna planes activos y públicos con features y precios.
    Ordenados por sort_order. Usado por PricingPreview.svelte.
    Cache-Control: public, max-age=300 (5 min).
    """
    db = SessionLocal()
    try:
        plans = db.query(Plan).filter(
            Plan.is_active == True,
        ).order_by(Plan.sort_order).all()

        # Filtrar por is_public si el campo existe
        result = []
        for p in plans:
            is_public = getattr(p, "is_public", True)
            if is_public:
                result.append(_plan_to_dict(p))

        response = JSONResponse(content={"plans": result, "total": len(result)})
        response.headers["Cache-Control"] = "public, max-age=300"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/stats
# ═══════════════════════════════════════════

@router.get("/stats")
async def get_public_stats():
    """
    Métricas públicas para social proof en la landing.
    Calcula counts reales desde BD.
    Cache-Control: public, max-age=900 (15 min).
    """
    db = SessionLocal()
    try:
        total_customers = db.query(Customer).filter(
            Customer.is_admin_account == False,
            Customer.status == "active",
        ).count()

        total_partners = db.query(Partner).filter(
            Partner.status == PartnerStatus.active,
        ).count()

        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.active,
        ).count()

        total_modules = db.query(ModuleCatalog).filter(
            ModuleCatalog.is_active == True,
        ).count()

        stats = [
            {"value": f"{max(total_customers, 500)}+", "label": "Companies", "key": "companies"},
            {"value": "99.9%", "label": "Uptime", "key": "uptime"},
            {"value": "24/7", "label": "Support", "key": "support"},
            {"value": f"{max(total_partners, 10)}+", "label": "Partners", "key": "partners"},
        ]

        response = JSONResponse(content={
            "stats": stats,
            "raw": {
                "total_customers": total_customers,
                "total_partners": total_partners,
                "active_subscriptions": active_subscriptions,
                "total_modules": total_modules,
            }
        })
        response.headers["Cache-Control"] = "public, max-age=900"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/modules
# ═══════════════════════════════════════════

@router.get("/modules")
async def get_public_modules():
    """
    Features/módulos agrupados por categoría.
    Usado por FeaturesGrid.svelte.
    """
    db = SessionLocal()
    try:
        modules = db.query(ModuleCatalog).filter(
            ModuleCatalog.is_active == True,
        ).order_by(ModuleCatalog.sort_order).all()

        # Agrupar por categoría
        categories = {}
        for m in modules:
            cat = m.category or "Other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "name": m.technical_name,
                "display_name": m.display_name,
                "description": m.description,
                "category": cat,
                "is_core": m.is_core,
                "price_monthly": m.price_monthly,
            })

        response = JSONResponse(content={
            "categories": categories,
            "total": len(modules),
        })
        response.headers["Cache-Control"] = "public, max-age=300"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/packages
# ═══════════════════════════════════════════

@router.get("/packages")
async def get_public_packages():
    """
    Blueprints/paquetes de módulos por industria.
    Usado por SocialProof.svelte para logos de industria.
    """
    db = SessionLocal()
    try:
        packages = db.query(ModulePackage).filter(
            ModulePackage.is_active == True,
        ).order_by(ModulePackage.display_name).all()

        result = []
        for pkg in packages:
            # Contar módulos incluidos
            module_count = db.query(ModulePackageItem).filter(
                ModulePackageItem.package_id == pkg.id,
            ).count()

            result.append({
                "id": pkg.id,
                "name": pkg.name,
                "display_name": pkg.display_name,
                "description": pkg.description,
                "plan_type": pkg.plan_type.value if pkg.plan_type else None,
                "base_price_monthly": pkg.base_price_monthly,
                "module_count": module_count,
                "module_list": pkg.module_list or [],
                "is_default": pkg.is_default,
            })

        response = JSONResponse(content={"packages": result, "total": len(result)})
        response.headers["Cache-Control"] = "public, max-age=300"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/testimonials
# ═══════════════════════════════════════════

@router.get("/testimonials")
async def get_public_testimonials(locale: str = Query("en")):
    """
    Testimonios activos para la landing page.
    Filtrados por locale (en/es).
    Retorna: nombre, rol, empresa, texto, avatar_url
    Cache-Control: public, max-age=600 (10 min).
    """
    db = SessionLocal()
    try:
        testimonials = db.query(Testimonial).filter(
            Testimonial.locale == locale,
        ).order_by(Testimonial.sort_order).all()

        result = []
        for t in testimonials:
            result.append({
                "id": t.id,
                "name": t.name,
                "role": t.role,
                "company": t.company,
                "text": t.text,
                "avatar_url": t.avatar_url,
                "featured": t.featured,
                "locale": t.locale,
            })

        response = JSONResponse(content={"testimonials": result, "locale": locale, "total": len(result)})
        response.headers["Cache-Control"] = "public, max-age=600"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/translations
# ═══════════════════════════════════════════

@router.get("/translations")
async def get_public_translations(locale: str = Query("en"), context: Optional[str] = None):
    """
    Traducciones gestionables desde admin (Translation table).
    Filtradas por locale (en/es) y opcionalmente por context.
    Usadas para strings que cambian frecuentemente (SEO, badges, etc).
    
    Query params:
    - locale: "en" | "es" (default: "en")
    - context: "landing" | "seo" | "pricing" | "footer" (optional)
    
    Cache-Control: public, max-age=600 (10 min).
    """
    db = SessionLocal()
    try:
        query = db.query(Translation).filter(
            Translation.locale == locale,
            Translation.is_approved == True,
        )
        
        if context:
            query = query.filter(Translation.context == context)
        
        translations = query.all()
        
        # Retornar como dict key->value para fácil acceso en frontend
        result = {}
        for t in translations:
            result[t.key] = t.value
        
        response = JSONResponse(content={
            "translations": result,
            "locale": locale,
            "context": context,
            "total": len(result),
        })
        response.headers["Cache-Control"] = "public, max-age=600"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/partners — Partners activos para selección
# ═══════════════════════════════════════════

@router.get("/partners")
async def get_public_partners():
    """
    Lista de partners activos para selección en onboarding.
    El cliente puede elegir "Trabaja con un socio implementador".
    Solo muestra datos públicos (nombre, logo, especialidad).
    """
    db = SessionLocal()
    try:
        partners = db.query(Partner).filter(
            Partner.status == PartnerStatus.active,
            Partner.portal_access == True,
        ).order_by(Partner.company_name).all()

        result = []
        for p in partners:
            # Obtener branding si existe
            branding = db.query(PartnerBrandingProfile).filter(
                PartnerBrandingProfile.partner_id == p.id,
                PartnerBrandingProfile.is_active == True,
            ).first()

            result.append({
                "id": p.id,
                "company_name": p.company_name,
                "partner_code": p.partner_code,
                "slug": getattr(p, "slug", None) or p.partner_code,
                "country": p.country,
                "logo_url": branding.logo_url if branding else None,
                "brand_name": branding.brand_name if branding else p.company_name,
                "primary_color": branding.primary_color if branding else "#1B4FD8",
            })

        response = JSONResponse(content={"partners": result, "total": len(result)})
        response.headers["Cache-Control"] = "public, max-age=300"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/partner/{code} — Branding de un partner
# ═══════════════════════════════════════════

@router.get("/partner/{code}")
async def get_partner_landing(code: str):
    """
    Retorna branding + planes de un partner para su URL personalizada.
    Busca primero por slug, luego por partner_code.
    Usado por PartnerLanding.svelte (ruta #/plt/{code}).
    """
    db = SessionLocal()
    try:
        # Buscar por slug primero, luego por partner_code
        partner = db.query(Partner).filter(
            Partner.slug == code,
            Partner.status == PartnerStatus.active,
        ).first()

        if not partner:
            partner = db.query(Partner).filter(
                Partner.partner_code == code,
                Partner.status == PartnerStatus.active,
            ).first()

        if not partner:
            raise HTTPException(404, f"Partner '{code}' not found or inactive")

        # Obtener branding
        branding = db.query(PartnerBrandingProfile).filter(
            PartnerBrandingProfile.partner_id == partner.id,
            PartnerBrandingProfile.is_active == True,
        ).first()

        # Obtener planes con pricing override del partner
        plans = db.query(Plan).filter(
            Plan.is_active == True,
        ).order_by(Plan.sort_order).all()

        plans_data = []
        for plan in plans:
            is_public = getattr(plan, "is_public", True)
            if not is_public:
                continue

            # Buscar pricing override para este partner
            override = db.query(PartnerPricingOverride).filter(
                PartnerPricingOverride.partner_id == partner.id,
                PartnerPricingOverride.plan_name == plan.name,
                PartnerPricingOverride.is_active == True,
            ).first()

            plan_dict = _plan_to_dict(plan)
            if override:
                if override.base_price_override is not None:
                    plan_dict["base_price"] = override.base_price_override
                if override.price_per_user_override is not None:
                    plan_dict["price_per_user"] = override.price_per_user_override
                if override.included_users_override is not None:
                    plan_dict["included_users"] = override.included_users_override
                plan_dict["has_partner_pricing"] = True
            else:
                plan_dict["has_partner_pricing"] = False

            plans_data.append(plan_dict)

        result = {
            "partner": {
                "id": partner.id,
                "company_name": partner.company_name,
                "partner_code": partner.partner_code,
                "slug": getattr(partner, "slug", None) or partner.partner_code,
                "country": partner.country,
            },
            "branding": {
                "brand_name": branding.brand_name if branding else partner.company_name,
                "logo_url": branding.logo_url if branding else None,
                "favicon_url": branding.favicon_url if branding else None,
                "primary_color": branding.primary_color if branding else "#1B4FD8",
                "secondary_color": branding.secondary_color if branding else "#0EA5E9",
                "support_email": branding.support_email if branding else partner.contact_email,
                "support_url": branding.support_url if branding else None,
                "custom_css": branding.custom_css if branding else None,
            } if branding or partner else {},
            "plans": plans_data,
        }

        response = JSONResponse(content=result)
        response.headers["Cache-Control"] = "public, max-age=300"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  POST /api/public/calculate — Calculadora de precios
# ═══════════════════════════════════════════

@router.post("/calculate")
async def calculate_price(payload: PriceCalculateRequest):
    """
    Calcula precio por plan + cantidad de usuarios.
    Soporta billing mensual/anual y pricing override de partner.
    Usado por UserSelector.svelte para mostrar precio en tiempo real.
    """
    db = SessionLocal()
    try:
        plan = db.query(Plan).filter(
            Plan.name == payload.plan_name,
            Plan.is_active == True,
        ).first()

        if not plan:
            raise HTTPException(404, f"Plan '{payload.plan_name}' not found")

        # Resolver partner si viene código
        partner_id = None
        if payload.partner_code:
            partner = db.query(Partner).filter(
                Partner.partner_code == payload.partner_code,
                Partner.status == PartnerStatus.active,
            ).first()
            if not partner:
                partner = db.query(Partner).filter(
                    Partner.slug == payload.partner_code,
                    Partner.status == PartnerStatus.active,
                ).first()
            if partner:
                partner_id = partner.id

        monthly_price = plan.calculate_monthly(payload.user_count, partner_id)

        # Calcular anual con descuento
        discount = getattr(plan, "annual_discount_percent", 20) or 20
        annual_monthly = monthly_price * (1 - discount / 100)
        annual_total = annual_monthly * 12

        extra_users = max(0, payload.user_count - plan.included_users)

        return {
            "plan_name": plan.name,
            "display_name": plan.display_name,
            "user_count": payload.user_count,
            "included_users": plan.included_users,
            "extra_users": extra_users,
            "base_price": plan.base_price,
            "price_per_user": plan.price_per_user,
            "monthly": {
                "total": round(monthly_price, 2),
                "base": round(plan.base_price, 2),
                "users_cost": round(extra_users * plan.price_per_user, 2),
            },
            "annual": {
                "monthly_equivalent": round(annual_monthly, 2),
                "total": round(annual_total, 2),
                "discount_percent": discount,
                "savings": round((monthly_price * 12) - annual_total, 2),
            },
            "currency": plan.currency,
            "has_partner_pricing": partner_id is not None,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/content — CMS de secciones
# ═══════════════════════════════════════════

@router.get("/content")
async def get_landing_content(locale: str = Query("en")):
    """
    Retorna todas las secciones de contenido de la landing page por locale.
    Permite al equipo de marketing cambiar textos sin deploy.
    
    Estructura de respuesta:
    {
        "hero": { "title": "...", "content": "...", "meta_description": "..." },
        "features": { ... },
        "pricing": { ... }
    }
    
    Cache-Control: public, max-age=600 (10 min).
    """
    db = SessionLocal()
    try:
        sections = db.query(LandingSection).filter(
            LandingSection.locale == locale,
        ).all()

        result = {}
        for s in sections:
            result[s.section_key] = {
                "id": s.id,
                "section_key": s.section_key,
                "title": s.title,
                "content": s.content,
                "meta_description": s.meta_description,
                "meta_keywords": s.meta_keywords,
                "og_title": s.og_title,
                "og_description": s.og_description,
                "og_image_url": s.og_image_url,
                "structured_data": s.structured_data,
                "locale": s.locale,
            }

        response = JSONResponse(content={"sections": result, "locale": locale, "total": len(result)})
        response.headers["Cache-Control"] = "public, max-age=600"
        return response
    finally:
        db.close()


# ═══════════════════════════════════════════
#  GET /api/public/catalog — Catálogo de servicios
# ═══════════════════════════════════════════

@router.get("/catalog")
async def get_public_catalog():
    """
    Catálogo de servicios agrupado por categoría.
    Usado para mostrar servicios adicionales.
    """
    db = SessionLocal()
    try:
        items = db.query(ServiceCatalogItem).filter(
            ServiceCatalogItem.is_active == True,
        ).order_by(ServiceCatalogItem.sort_order).all()

        categories = {}
        for item in items:
            cat = item.category.value if item.category else "other"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "id": item.id,
                "name": item.name,
                "description": item.description,
                "unit": item.unit,
                "price_monthly": item.price_monthly,
                "price_max": item.price_max,
                "is_addon": item.is_addon,
            })

        response = JSONResponse(content={"categories": categories, "total": len(items)})
        response.headers["Cache-Control"] = "public, max-age=300"
        return response
    finally:
        db.close()
