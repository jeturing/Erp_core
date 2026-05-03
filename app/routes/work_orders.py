"""
Work Orders Routes — Épica 9: Órdenes de trabajo con blueprint de aplicaciones.

POST /api/work-orders                        — Crear work order
GET  /api/work-orders                        — Lista con filtros
GET  /api/work-orders/{id}                   — Detalle enriquecido
PUT  /api/work-orders/{id}/status            — Transición de estado (envía email al completar)
POST /api/work-orders/{id}/approve-modules   — Aprobar/rechazar módulos seleccionados
GET  /api/work-orders/catalog/packages       — Blueprints disponibles
GET  /api/work-orders/catalog/modules        — Catálogo de módulos con categorías
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Cookie
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import secrets
import logging
import os

from ..models.database import (
    WorkOrder, WorkOrderStatus, Customer, Partner,
    ModulePackage, ModuleCatalog, get_db,
)
from .roles import verify_token_with_role, _extract_token

router = APIRouter(prefix="/api/work-orders", tags=["WorkOrders"])
logger = logging.getLogger(__name__)

ADMIN_TENANT_LOGIN = os.getenv("ODOO_DEFAULT_ADMIN_LOGIN", "admin@sajet.us")
ADMIN_TENANT_PASSWORD = os.getenv("ODOO_DEFAULT_ADMIN_PASSWORD", "")

# ─── Cifrado Fernet para credenciales sensibles ───────────────────────────────

def _get_fernet():
    """Devuelve instancia Fernet si FIELD_ENCRYPT_KEY está configurada."""
    key = os.getenv("FIELD_ENCRYPT_KEY", "")
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode())
    except Exception as e:
        logger.warning(f"Fernet init failed: {e}")
        return None

def _encrypt(value: str) -> str:
    """Cifra un string con Fernet. Devuelve el valor original si no hay clave."""
    if not value:
        return value
    f = _get_fernet()
    if f is None:
        return value
    return f.encrypt(value.encode()).decode()

def _decrypt(value: str) -> str:
    """Descifra un string con Fernet. Devuelve el valor original si no hay clave."""
    if not value:
        return value
    f = _get_fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value  # Devuelve crudo si no puede descifrar (ej: valores legacy)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_admin(request: Request, access_token=None):
    token = _extract_token(request, access_token)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    payload = verify_token_with_role(token)
    if payload.get("role") not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="Acceso solo para administradores")
    return payload


def _next_order_number(db) -> str:
    year = datetime.now(timezone.utc).replace(tzinfo=None).year
    count = db.query(WorkOrder).count() + 1
    return f"WO-{year}-{count:04d}"


def _serialize(wo: WorkOrder) -> dict:
    return {
        "id": wo.id,
        "order_number": wo.order_number,
        "subscription_id": wo.subscription_id,
        "customer_id": wo.customer_id,
        "partner_id": wo.partner_id,
        "work_type": wo.work_type,
        "description": wo.description,
        "blueprint_package_id": wo.blueprint_package_id,
        "selected_modules": wo.selected_modules,
        "approved_modules": wo.approved_modules,
        "rejected_modules": wo.rejected_modules,
        "status": wo.status.value if wo.status else None,
        "requested_by": wo.requested_by,
        "approved_by": wo.approved_by,
        "completed_by": wo.completed_by,
        "tenant_admin_email": wo.tenant_admin_email,
        "tenant_user_email": wo.tenant_user_email,
        "notes": wo.notes,
        "requested_at": wo.requested_at.isoformat() if wo.requested_at else None,
        "approved_at": wo.approved_at.isoformat() if wo.approved_at else None,
        "completed_at": wo.completed_at.isoformat() if wo.completed_at else None,
        "created_at": wo.created_at.isoformat() if wo.created_at else None,
    }


def _send_completion_email(wo: WorkOrder, db):
    try:
        customer = db.query(Customer).filter(Customer.id == wo.customer_id).first()
        if not customer:
            return
        from ..services.email_service import send_work_order_completion
        send_work_order_completion(
            to_email=customer.email,
            company_name=customer.company_name or customer.subdomain or str(customer.id),
            subdomain=customer.subdomain or "",
            admin_login=wo.tenant_admin_email or ADMIN_TENANT_LOGIN,
            admin_password=_decrypt(wo.tenant_admin_password or ADMIN_TENANT_PASSWORD),
            user_login=wo.tenant_user_email or f"usuario@{customer.subdomain}.sajet.us",
            user_password=_decrypt(wo.tenant_user_password or ""),
            approved_modules=wo.approved_modules or [],
            order_number=wo.order_number,
        )
        logger.info(f"✅ Email enviado a {customer.email} — WO {wo.order_number}")
    except Exception as e:
        logger.error(f"❌ Error email WO {wo.id}: {e}")


# ─── Schemas ──────────────────────────────────────────────────────────────────

class CreateWorkOrder(BaseModel):
    customer_id: int
    partner_id: Optional[int] = None
    subscription_id: Optional[int] = None
    work_type: str = "provision"
    description: str
    blueprint_package_id: Optional[int] = None
    selected_modules: Optional[List[str]] = None
    requested_by: Optional[str] = None


class UpdateWorkOrderStatus(BaseModel):
    status: str
    notes: Optional[str] = None
    completed_by: Optional[str] = None


class ApproveModulesPayload(BaseModel):
    approved_modules: List[str]
    rejected_modules: List[str] = []
    notes: Optional[str] = None
    approved_by: Optional[str] = None


# ─── Rutas estáticas ANTES que /{wo_id} ───────────────────────────────────────

@router.get("/catalog/packages")
async def get_blueprint_packages(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """Lista paquetes de blueprint. Oculta pkg_saas_ops a no-admin."""
    auth = _require_admin(request, access_token)
    is_admin = auth.get("role") == "admin"
    q = db.query(ModulePackage).filter(ModulePackage.is_active == True)
    if not is_admin:
        q = q.filter(ModulePackage.name != "pkg_saas_ops")
    packages = q.order_by(ModulePackage.display_name).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "display_name": p.display_name,
            "description": p.description,
            "module_list": p.module_list or [],
            "module_count": len(p.module_list or []),
            "partner_allowed": p.name != "pkg_saas_ops",
        }
        for p in packages
    ]


@router.get("/catalog/modules")
async def get_catalog_modules(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    auth = _require_admin(request, access_token)
    is_admin = auth.get("role") == "admin"
    q = db.query(ModuleCatalog).filter(ModuleCatalog.is_active == True)
    if not is_admin:
        q = q.filter(ModuleCatalog.partner_allowed == True)
    if category:
        q = q.filter(ModuleCatalog.category == category)
    modules = q.order_by(ModuleCatalog.category, ModuleCatalog.display_name).all()
    return {
        "items": [
            {
                "id": m.id,
                "technical_name": m.technical_name,
                "display_name": m.display_name,
                "category": m.category,
                "is_core": m.is_core,
                "partner_allowed": m.partner_allowed,
            }
            for m in modules
        ],
        "categories": sorted({m.category for m in modules if m.category}),
    }


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@router.post("")
async def create_work_order(
    payload: CreateWorkOrder,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    auth = _require_admin(request, access_token)
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(404, "Cliente no encontrado")

    selected_modules = payload.selected_modules or []
    if payload.blueprint_package_id and not selected_modules:
        pkg = db.query(ModulePackage).filter(ModulePackage.id == payload.blueprint_package_id).first()
        if pkg and pkg.module_list:
            selected_modules = pkg.module_list

    user_password = secrets.token_urlsafe(9)
    tenant_user_email = (
        f"admin@{customer.subdomain}.sajet.us" if customer.subdomain else None
    )

    wo = WorkOrder(
        order_number=_next_order_number(db),
        customer_id=payload.customer_id,
        partner_id=payload.partner_id,
        subscription_id=payload.subscription_id,
        work_type=payload.work_type,
        description=payload.description,
        blueprint_package_id=payload.blueprint_package_id,
        selected_modules=selected_modules if selected_modules else None,
        status=WorkOrderStatus.requested,
        requested_by=payload.requested_by or auth.get("sub", "system"),
        tenant_admin_email=ADMIN_TENANT_LOGIN,
        tenant_admin_password=_encrypt(ADMIN_TENANT_PASSWORD),
        tenant_user_email=tenant_user_email,
        tenant_user_password=_encrypt(user_password),
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return {"message": "Work order creada", "work_order": _serialize(wo)}


@router.get("")
async def list_work_orders(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    customer_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    subscription_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    _require_admin(request, access_token)
    q = db.query(WorkOrder)
    if customer_id:
        q = q.filter(WorkOrder.customer_id == customer_id)
    if partner_id:
        q = q.filter(WorkOrder.partner_id == partner_id)
    if subscription_id:
        q = q.filter(WorkOrder.subscription_id == subscription_id)
    if status:
        try:
            q = q.filter(WorkOrder.status == WorkOrderStatus(status))
        except ValueError:
            pass
    total = q.count()
    orders = q.order_by(WorkOrder.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [_serialize(wo) for wo in orders]}


@router.get("/{wo_id}")
async def get_work_order(
    wo_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    _require_admin(request, access_token)
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(404, "Work order no encontrada")

    data = _serialize(wo)
    if wo.customer_id:
        c = db.query(Customer).filter(Customer.id == wo.customer_id).first()
        if c:
            data["customer_name"] = c.company_name or c.full_name
            data["customer_subdomain"] = c.subdomain
    if wo.partner_id:
        p = db.query(Partner).filter(Partner.id == wo.partner_id).first()
        if p:
            data["partner_name"] = p.company_name

    if wo.selected_modules:
        catalog = {m.technical_name: m for m in db.query(ModuleCatalog).filter(
            ModuleCatalog.technical_name.in_(wo.selected_modules)
        ).all()}
        data["selected_modules_detail"] = [
            {
                "technical_name": tn,
                "display_name": catalog[tn].display_name if tn in catalog else tn,
                "category": catalog[tn].category if tn in catalog else None,
                "approved": tn in (wo.approved_modules or []),
                "rejected": tn in (wo.rejected_modules or []),
            }
            for tn in wo.selected_modules
        ]
    if wo.blueprint_package_id:
        pkg = db.query(ModulePackage).filter(ModulePackage.id == wo.blueprint_package_id).first()
        if pkg:
            data["blueprint_name"] = pkg.display_name

    return data


@router.put("/{wo_id}/status")
async def update_work_order_status(
    wo_id: int,
    payload: UpdateWorkOrderStatus,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Transiciones: requested→approved|rejected | approved→in_progress|cancelled | in_progress→completed|cancelled
    Al completar: envía email con credenciales al cliente.
    """
    auth = _require_admin(request, access_token)
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(404, "Work order no encontrada")

    new = payload.status
    current = wo.status.value if wo.status else "unknown"
    valid_transitions = {
        "requested":   ["approved", "rejected"],
        "approved":    ["in_progress", "cancelled"],
        "in_progress": ["completed", "cancelled"],
    }
    if new not in valid_transitions.get(current, []):
        raise HTTPException(400, f"Transición inválida: {current} → {new}")

    try:
        wo.status = WorkOrderStatus(new)
    except ValueError:
        raise HTTPException(400, f"Estado inválido: {new}")

    actor = payload.completed_by or auth.get("sub", "admin")
    ts = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")

    if new == "approved":
        wo.approved_by = actor
        wo.approved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    elif new == "completed":
        wo.completed_by = actor
        wo.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        _send_completion_email(wo, db)
    elif new == "rejected":
        wo.approved_by = None

    if payload.notes:
        wo.notes = (wo.notes or "") + f"\n[{ts}] [{new}] {payload.notes}"

    db.commit()
    return {"message": f"Work order → {new}", "work_order": _serialize(wo)}


@router.post("/{wo_id}/approve-modules")
async def approve_modules(
    wo_id: int,
    payload: ApproveModulesPayload,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """Registra módulos aprobados/rechazados por equipo Jeturing."""
    auth = _require_admin(request, access_token)
    wo = db.query(WorkOrder).filter(WorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(404, "Work order no encontrada")
    if wo.status not in (WorkOrderStatus.requested, WorkOrderStatus.approved):
        raise HTTPException(400, "Solo se puede revisar módulos en estado requested o approved")

    wo.approved_modules = payload.approved_modules
    wo.rejected_modules = payload.rejected_modules
    actor = payload.approved_by or auth.get("sub", "admin")
    ts = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")
    note = (f"\n[{ts}] Módulos aprobados: {len(payload.approved_modules)}, "
            f"rechazados: {len(payload.rejected_modules)} — {actor}")
    if payload.notes:
        note += f" | {payload.notes}"
    wo.notes = (wo.notes or "") + note

    db.commit()
    return {
        "message": "Módulos actualizados",
        "approved": payload.approved_modules,
        "rejected": payload.rejected_modules,
    }
