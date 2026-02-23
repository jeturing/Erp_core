"""
Admin Landing I18n Routes - CRUD endpoints for Testimonials, LandingSections, and Translations
"""
from fastapi import APIRouter, Cookie, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy import desc

from ..models.database import (
    Testimonial, LandingSection, Translation, SessionLocal
)
from .roles import _require_admin as _require_admin_base

router = APIRouter(prefix="/api/admin", tags=["Admin Landing I18n"])


# ========== DTOs ==========

class TestimonialCreate(BaseModel):
    name: str
    role: str
    company: str
    text: str
    avatar_url: Optional[str] = None
    locale: str
    featured: bool = False
    sort_order: int = 0


class TestimonialUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None
    text: Optional[str] = None
    avatar_url: Optional[str] = None
    locale: Optional[str] = None
    featured: Optional[bool] = None
    sort_order: Optional[int] = None


class LandingSectionCreate(BaseModel):
    section_key: str
    locale: str
    title: str
    content: str
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_url: Optional[str] = None
    structured_data: Optional[dict] = None


class LandingSectionUpdate(BaseModel):
    section_key: Optional[str] = None
    locale: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_url: Optional[str] = None
    structured_data: Optional[dict] = None


class TranslationCreate(BaseModel):
    key: str
    locale: str
    value: str
    context: Optional[str] = None
    is_approved: bool = True


class TranslationUpdate(BaseModel):
    key: Optional[str] = None
    locale: Optional[str] = None
    value: Optional[str] = None
    context: Optional[str] = None
    is_approved: Optional[bool] = None


# ========== TESTIMONIALS ENDPOINTS ==========

@router.get("/testimonials")
async def list_testimonials(
    request: Request,
    access_token: str = Cookie(None),
    locale: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Lista testimonios con filtros opcionales"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        q = db.query(Testimonial)
        
        if locale:
            q = q.filter(Testimonial.locale == locale)
        if featured is not None:
            q = q.filter(Testimonial.featured == featured)
        
        total = q.count()
        items = q.order_by(Testimonial.sort_order, desc(Testimonial.created_at)).offset(offset).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close()


@router.post("/testimonials", status_code=status.HTTP_201_CREATED)
async def create_testimonial(
    payload: TestimonialCreate,
    request: Request,
    access_token: str = Cookie(None),
):
    """Crear un nuevo testimonio"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        testimonial = Testimonial(
            name=payload.name,
            role=payload.role,
            company=payload.company,
            text=payload.text,
            avatar_url=payload.avatar_url,
            locale=payload.locale,
            featured=payload.featured,
            sort_order=payload.sort_order,
        )
        db.add(testimonial)
        db.commit()
        db.refresh(testimonial)
        return testimonial
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/testimonials/{testimonial_id}")
async def get_testimonial(
    testimonial_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtener un testimonio específico"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
        if not testimonial:
            raise HTTPException(status_code=404, detail="Testimonio no encontrado")
        return testimonial
    finally:
        db.close()


@router.put("/testimonials/{testimonial_id}")
async def update_testimonial(
    testimonial_id: int,
    payload: TestimonialUpdate,
    request: Request,
    access_token: str = Cookie(None),
):
    """Actualizar un testimonio"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
        if not testimonial:
            raise HTTPException(status_code=404, detail="Testimonio no encontrado")
        
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(testimonial, field, value)
        
        db.commit()
        db.refresh(testimonial)
        return testimonial
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.patch("/testimonials/{testimonial_id}")
async def patch_testimonial(
    testimonial_id: int,
    payload: dict,
    request: Request,
    access_token: str = Cookie(None),
):
    """Actualizar parcialmente un testimonio"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
        if not testimonial:
            raise HTTPException(status_code=404, detail="Testimonio no encontrado")
        
        for field, value in payload.items():
            if hasattr(testimonial, field):
                setattr(testimonial, field, value)
        
        db.commit()
        db.refresh(testimonial)
        return testimonial
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.delete("/testimonials/{testimonial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_testimonial(
    testimonial_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Eliminar un testimonio"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        testimonial = db.query(Testimonial).filter(Testimonial.id == testimonial_id).first()
        if not testimonial:
            raise HTTPException(status_code=404, detail="Testimonio no encontrado")
        
        db.delete(testimonial)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# ========== LANDING SECTIONS ENDPOINTS ==========

@router.get("/landing-sections")
async def list_landing_sections(
    request: Request,
    access_token: str = Cookie(None),
    locale: Optional[str] = Query(None),
    section_key: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Lista secciones landing con filtros opcionales"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        q = db.query(LandingSection)
        
        if locale:
            q = q.filter(LandingSection.locale == locale)
        if section_key:
            q = q.filter(LandingSection.section_key == section_key)
        
        total = q.count()
        items = q.order_by(LandingSection.section_key, desc(LandingSection.updated_at)).offset(offset).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close()


@router.post("/landing-sections", status_code=status.HTTP_201_CREATED)
async def create_landing_section(
    payload: LandingSectionCreate,
    request: Request,
    access_token: str = Cookie(None),
):
    """Crear una nueva sección landing"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        section = LandingSection(
            section_key=payload.section_key,
            locale=payload.locale,
            title=payload.title,
            content=payload.content,
            meta_description=payload.meta_description,
            meta_keywords=payload.meta_keywords,
            og_title=payload.og_title,
            og_description=payload.og_description,
            og_image_url=payload.og_image_url,
            structured_data=payload.structured_data or {},
        )
        db.add(section)
        db.commit()
        db.refresh(section)
        return section
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/landing-sections/{section_id}")
async def get_landing_section(
    section_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtener una sección landing específica"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        section = db.query(LandingSection).filter(LandingSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Sección no encontrada")
        return section
    finally:
        db.close()


@router.put("/landing-sections/{section_id}")
async def update_landing_section(
    section_id: int,
    payload: LandingSectionUpdate,
    request: Request,
    access_token: str = Cookie(None),
):
    """Actualizar una sección landing"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        section = db.query(LandingSection).filter(LandingSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Sección no encontrada")
        
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(section, field, value)
        
        db.commit()
        db.refresh(section)
        return section
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.delete("/landing-sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_landing_section(
    section_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Eliminar una sección landing"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        section = db.query(LandingSection).filter(LandingSection.id == section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Sección no encontrada")
        
        db.delete(section)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


# ========== TRANSLATIONS ENDPOINTS ==========

@router.get("/translations")
async def list_translations(
    request: Request,
    access_token: str = Cookie(None),
    locale: Optional[str] = Query(None),
    context: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
    approved_only: bool = Query(False),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Lista traducciones con filtros opcionales"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        q = db.query(Translation)
        
        if locale:
            q = q.filter(Translation.locale == locale)
        if context:
            q = q.filter(Translation.context == context)
        if key:
            q = q.filter(Translation.key.ilike(f"%{key}%"))
        if approved_only:
            q = q.filter(Translation.is_approved == True)
        
        total = q.count()
        items = q.order_by(Translation.key, desc(Translation.updated_at)).offset(offset).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close()


@router.post("/translations", status_code=status.HTTP_201_CREATED)
async def create_translation(
    payload: TranslationCreate,
    request: Request,
    access_token: str = Cookie(None),
):
    """Crear una nueva traducción"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        # Verificar duplicado
        existing = db.query(Translation).filter(
            Translation.key == payload.key,
            Translation.locale == payload.locale
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Traducción ya existe para este key+locale")
        
        translation = Translation(
            key=payload.key,
            locale=payload.locale,
            value=payload.value,
            context=payload.context,
            is_approved=payload.is_approved,
        )
        db.add(translation)
        db.commit()
        db.refresh(translation)
        return translation
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/translations/{translation_id}")
async def get_translation(
    translation_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtener una traducción específica"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            raise HTTPException(status_code=404, detail="Traducción no encontrada")
        return translation
    finally:
        db.close()


@router.put("/translations/{translation_id}")
async def update_translation(
    translation_id: int,
    payload: TranslationUpdate,
    request: Request,
    access_token: str = Cookie(None),
):
    """Actualizar una traducción"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            raise HTTPException(status_code=404, detail="Traducción no encontrada")
        
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(translation, field, value)
        
        db.commit()
        db.refresh(translation)
        return translation
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.patch("/translations/{translation_id}")
async def patch_translation(
    translation_id: int,
    payload: dict,
    request: Request,
    access_token: str = Cookie(None),
):
    """Actualizar parcialmente una traducción"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            raise HTTPException(status_code=404, detail="Traducción no encontrada")
        
        for field, value in payload.items():
            if hasattr(translation, field):
                setattr(translation, field, value)
        
        db.commit()
        db.refresh(translation)
        return translation
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.delete("/translations/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_translation(
    translation_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Eliminar una traducción"""
    _require_admin_base(request, access_token)
    
    db = SessionLocal()
    try:
        translation = db.query(Translation).filter(Translation.id == translation_id).first()
        if not translation:
            raise HTTPException(status_code=404, detail="Traducción no encontrada")
        
        db.delete(translation)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
