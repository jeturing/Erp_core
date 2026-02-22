"""
Blueprints Routes — Module Catalog & Packages (Épica 2)
CRUD para catálogo de módulos Odoo y paquetes/blueprints.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Cookie
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import os, ast, logging

from ..models.database import (
    ModuleCatalog, ModulePackage, ModulePackageItem,
    get_db, PlanType
)

router = APIRouter(prefix="/api/blueprints", tags=["Blueprints"])
logger = logging.getLogger(__name__)

V17_PATH = os.getenv("V17_ADDONS_PATH", "/opt/extra-addons/V17")


# ── DTOs ──

class ModuleCatalogCreate(BaseModel):
    technical_name: str
    display_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    version: str = "17.0.1.0"
    is_core: bool = False
    partner_allowed: bool = True
    price_monthly: float = 0
    requires_module_id: Optional[int] = None

class ModuleCatalogUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    is_core: Optional[bool] = None
    partner_allowed: Optional[bool] = None
    price_monthly: Optional[float] = None
    is_active: Optional[bool] = None

class PackageCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    plan_type: Optional[str] = None
    base_price_monthly: float = 0
    is_default: bool = False
    module_list: List[str] = []       # technical_names

class PackageUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    base_price_monthly: Optional[float] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    module_list: Optional[List[str]] = None


# ── MODULE CATALOG ──

@router.get("/modules")
def list_modules(
    active_only: bool = True,
    partner_only: bool = False,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista módulos del catálogo."""
    q = db.query(ModuleCatalog)
    if active_only:
        q = q.filter(ModuleCatalog.is_active == True)
    if partner_only:
        q = q.filter(ModuleCatalog.partner_allowed == True)
    if category:
        q = q.filter(ModuleCatalog.category == category)
    modules = q.order_by(ModuleCatalog.sort_order, ModuleCatalog.display_name).all()
    return {
        "total": len(modules),
        "items": [
            {
                "id": m.id,
                "technical_name": m.technical_name,
                "display_name": m.display_name,
                "description": m.description,
                "category": m.category,
                "version": m.version,
                "is_core": m.is_core,
                "partner_allowed": m.partner_allowed,
                "price_monthly": m.price_monthly,
                "requires_module_id": m.requires_module_id,
                "is_active": m.is_active,
                "sort_order": m.sort_order or 0,
            }
            for m in modules
        ]
    }


@router.get("/modules/categories")
def list_categories(db: Session = Depends(get_db)):
    """Lista categorías únicas de módulos."""
    rows = db.query(ModuleCatalog.category).filter(
        ModuleCatalog.is_active == True,
        ModuleCatalog.category != None
    ).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


@router.post("/modules/import-fs")
def import_modules_from_fs(db: Session = Depends(get_db)):
    """Importa módulos desde el filesystem V17 al catálogo (upsert)."""
    if not os.path.isdir(V17_PATH):
        raise HTTPException(404, f"V17 path not found: {V17_PATH}")

    JETURING_ONLY = {
        "jeturing_branding", "jeturing_iframe_app_manager", "odoo_saas_kit",
        "cetmix_tower", "odoo_rest", "odoo_database_restore_manager",
    }
    CORE_MODULES = {"web", "portal", "dynamic_odoo", "queue_job", "document_management_system"}

    created = 0
    updated = 0
    skipped = 0

    dirs = sorted([d for d in os.listdir(V17_PATH) if os.path.isdir(os.path.join(V17_PATH, d))])
    for d in dirs:
        technical_name = d.split("-")[0]
        manifest_path = os.path.join(V17_PATH, d, "__manifest__.py")
        manifest = {}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                manifest = ast.literal_eval(content)
            except Exception:
                pass

        display_name = str(manifest.get("name", technical_name.replace("_", " ").title()))[:100]
        category = str(manifest.get("category", "General"))[:50]
        version = str(manifest.get("version", "17.0.1.0"))[:20]
        desc_raw = manifest.get("summary", manifest.get("description", ""))
        description = str(desc_raw or "")[:500] if desc_raw else None
        partner_allowed = technical_name not in JETURING_ONLY
        is_core = technical_name in CORE_MODULES

        try:
            existing = db.query(ModuleCatalog).filter(
                ModuleCatalog.technical_name == technical_name
            ).first()
            if existing:
                existing.display_name = display_name
                existing.category = category
                existing.version = version
                existing.partner_allowed = partner_allowed
                existing.is_core = is_core
                if description:
                    existing.description = description
                updated += 1
            else:
                db.add(ModuleCatalog(
                    technical_name=technical_name,
                    display_name=display_name,
                    category=category,
                    version=version,
                    description=description,
                    partner_allowed=partner_allowed,
                    is_core=is_core,
                    price_monthly=0,
                    is_active=True,
                ))
                created += 1
        except Exception as e:
            logger.warning(f"Skipping {technical_name}: {e}")
            db.rollback()
            skipped += 1
            continue

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Commit error: {e}")

    total = db.query(ModuleCatalog).count()
    return {
        "status": "ok",
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total_in_catalog": total,
    }


@router.post("/modules")
def create_module(payload: ModuleCatalogCreate, db: Session = Depends(get_db)):
    """Crea un módulo en el catálogo."""
    existing = db.query(ModuleCatalog).filter(
        ModuleCatalog.technical_name == payload.technical_name
    ).first()
    if existing:
        raise HTTPException(400, f"Module '{payload.technical_name}' already exists")
    module = ModuleCatalog(**payload.model_dump())
    db.add(module)
    db.commit()
    db.refresh(module)
    return {"id": module.id, "technical_name": module.technical_name, "status": "created"}


@router.put("/modules/{module_id}")
def update_module(module_id: int, payload: ModuleCatalogUpdate, db: Session = Depends(get_db)):
    """Actualiza un módulo del catálogo."""
    module = db.query(ModuleCatalog).filter(ModuleCatalog.id == module_id).first()
    if not module:
        raise HTTPException(404, "Module not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(module, k, v)
    db.commit()
    return {"id": module.id, "status": "updated"}


# ── PACKAGES / BLUEPRINTS ──

@router.get("/packages")
def list_packages(
    active_only: bool = True,
    plan_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista paquetes/blueprints disponibles."""
    q = db.query(ModulePackage)
    if active_only:
        q = q.filter(ModulePackage.is_active == True)
    if plan_type:
        q = q.filter(ModulePackage.plan_type == plan_type)
    packages = q.order_by(ModulePackage.display_name).all()
    items = [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "description": p.description,
            "plan_type": p.plan_type.value if p.plan_type else None,
            "base_price_monthly": p.base_price_monthly,
            "is_default": p.is_default,
            "is_active": p.is_active,
            "module_list": p.module_list or [],
            "module_count": len(p.module_list) if p.module_list else 0,
            "partner_allowed": getattr(p, "partner_allowed", True),
        }
        for p in packages
    ]
    return {"total": len(items), "items": items}


@router.post("/packages")
def create_package(payload: PackageCreate, db: Session = Depends(get_db)):
    """Crea un paquete/blueprint con lista de módulos."""
    existing = db.query(ModulePackage).filter(ModulePackage.name == payload.name).first()
    if existing:
        raise HTTPException(400, f"Package '{payload.name}' already exists")

    plan_type_enum = None
    if payload.plan_type:
        try:
            plan_type_enum = PlanType(payload.plan_type)
        except ValueError:
            raise HTTPException(400, f"Invalid plan_type: {payload.plan_type}")

    package = ModulePackage(
        name=payload.name,
        display_name=payload.display_name,
        description=payload.description,
        plan_type=plan_type_enum,
        base_price_monthly=payload.base_price_monthly,
        is_default=payload.is_default,
        module_list=payload.module_list,
    )
    db.add(package)
    db.flush()

    # Link modules by technical_name
    for tech_name in payload.module_list:
        module = db.query(ModuleCatalog).filter(
            ModuleCatalog.technical_name == tech_name
        ).first()
        if module:
            item = ModulePackageItem(
                package_id=package.id,
                module_id=module.id,
            )
            db.add(item)

    db.commit()
    db.refresh(package)
    return {"id": package.id, "name": package.name, "status": "created"}


@router.put("/packages/{package_id}")
def update_package(package_id: int, payload: PackageUpdate, db: Session = Depends(get_db)):
    """Actualiza un paquete/blueprint."""
    package = db.query(ModulePackage).filter(ModulePackage.id == package_id).first()
    if not package:
        raise HTTPException(404, "Package not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "module_list" and v is not None:
            # Rebuild items
            db.query(ModulePackageItem).filter(
                ModulePackageItem.package_id == package.id
            ).delete()
            package.module_list = v
            for tech_name in v:
                module = db.query(ModuleCatalog).filter(
                    ModuleCatalog.technical_name == tech_name
                ).first()
                if module:
                    db.add(ModulePackageItem(
                        package_id=package.id,
                        module_id=module.id,
                    ))
        else:
            setattr(package, k, v)

    db.commit()
    return {"id": package.id, "status": "updated"}


@router.get("/packages/{package_id}")
def get_package(package_id: int, db: Session = Depends(get_db)):
    """Obtiene detalle de un paquete."""
    package = db.query(ModulePackage).filter(ModulePackage.id == package_id).first()
    if not package:
        raise HTTPException(404, "Package not found")
    return {
        "id": package.id,
        "name": package.name,
        "display_name": package.display_name,
        "description": package.description,
        "plan_type": package.plan_type.value if package.plan_type else None,
        "base_price_monthly": package.base_price_monthly,
        "is_default": package.is_default,
        "module_list": package.module_list or [],
        "items": [
            {
                "module_id": item.module_id,
                "technical_name": item.module.technical_name if item.module else None,
                "display_name": item.module.display_name if item.module else None,
                "is_optional": item.is_optional,
            }
            for item in (package.items or [])
        ],
    }
