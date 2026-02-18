"""
Leads Management Routes — Pipeline de prospectos por partner
Cláusula 7 del contrato: Registro previo al cierre comercial.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Request
from pydantic import BaseModel

from ..models.database import (
    Customer, Lead, Partner, SessionLocal,
    LeadStatus, PartnerStatus,
)
from .roles import _require_admin

router = APIRouter(prefix="/api/leads", tags=["Leads"])


# ── DTOs ──

class LeadCreate(BaseModel):
    partner_id: int
    company_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    estimated_monthly_value: float = 0


class LeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    estimated_monthly_value: Optional[float] = None
    lost_reason: Optional[str] = None
    converted_customer_id: Optional[int] = None


def _lead_to_dict(l: Lead) -> dict:
    return {
        "id": l.id,
        "partner_id": l.partner_id,
        "company_name": l.company_name,
        "contact_name": l.contact_name,
        "contact_email": l.contact_email,
        "phone": l.phone,
        "country": l.country,
        "status": l.status.value if l.status else None,
        "notes": l.notes,
        "estimated_monthly_value": l.estimated_monthly_value,
        "converted_customer_id": l.converted_customer_id,
        "converted_at": l.converted_at.isoformat() if l.converted_at else None,
        "lost_reason": l.lost_reason,
        "registered_at": l.registered_at.isoformat() if l.registered_at else None,
        "updated_at": l.updated_at.isoformat() if l.updated_at else None,
    }


# ── Routes ──

@router.get("")
async def list_leads(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    partner_id: Optional[int] = None,
    status_filter: Optional[str] = None,
):
    """Lista leads con filtros opcionales por partner y status."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(Lead)
        if partner_id:
            q = q.filter(Lead.partner_id == partner_id)
        if status_filter:
            try:
                q = q.filter(Lead.status == LeadStatus(status_filter))
            except ValueError:
                pass

        leads = q.order_by(Lead.registered_at.desc()).all()
        items = []
        for l in leads:
            d = _lead_to_dict(l)
            # Añadir nombre del partner
            partner = db.query(Partner).filter(Partner.id == l.partner_id).first()
            d["partner_name"] = partner.company_name if partner else "—"
            items.append(d)

        # Pipeline summary
        pipeline = {}
        for s in LeadStatus:
            pipeline[s.value] = sum(1 for i in items if i["status"] == s.value)

        return {
            "items": items,
            "total": len(items),
            "pipeline": pipeline,
            "total_estimated_value": sum(i["estimated_monthly_value"] or 0 for i in items),
        }
    finally:
        db.close()


@router.get("/{lead_id}")
async def get_lead(
    lead_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        data = _lead_to_dict(lead)
        partner = db.query(Partner).filter(Partner.id == lead.partner_id).first()
        data["partner_name"] = partner.company_name if partner else "—"

        return data
    finally:
        db.close()


@router.post("")
async def create_lead(
    payload: LeadCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Registra un nuevo lead para un partner."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")
        if partner.status != PartnerStatus.active:
            raise HTTPException(status_code=400, detail="El partner no está activo")

        lead = Lead(
            partner_id=payload.partner_id,
            company_name=payload.company_name,
            contact_name=payload.contact_name,
            contact_email=payload.contact_email,
            phone=payload.phone,
            country=payload.country,
            notes=payload.notes,
            estimated_monthly_value=payload.estimated_monthly_value,
            status=LeadStatus.new,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)

        return {"message": "Lead registrado", "lead": _lead_to_dict(lead)}
    finally:
        db.close()


@router.put("/{lead_id}")
async def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Actualiza un lead (cambiar status en el pipeline, etc.)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        changes = []
        for field, value in payload.dict(exclude_unset=True).items():
            if field == "status" and value:
                try:
                    new_status = LeadStatus(value)
                    if new_status == LeadStatus.won and not lead.converted_at:
                        lead.converted_at = datetime.utcnow()
                    value = new_status
                except ValueError:
                    continue

            old = getattr(lead, field, None)
            if old != value:
                setattr(lead, field, value)
                changes.append(field)

        db.commit()
        db.refresh(lead)

        return {"message": "Lead actualizado", "changes": changes, "lead": _lead_to_dict(lead)}
    finally:
        db.close()


@router.delete("/{lead_id}")
async def delete_lead(
    lead_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Elimina un lead."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        db.delete(lead)
        db.commit()

        return {"message": "Lead eliminado"}
    finally:
        db.close()


@router.post("/{lead_id}/convert")
async def convert_lead(
    lead_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    customer_id: Optional[int] = None,
):
    """Convierte un lead a cliente (marca como won y vincula customer)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        lead.status = LeadStatus.won
        lead.converted_at = datetime.utcnow()
        if customer_id:
            cust = db.query(Customer).filter(Customer.id == customer_id).first()
            if cust:
                lead.converted_customer_id = customer_id

        db.commit()
        db.refresh(lead)

        return {"message": "Lead convertido a cliente", "lead": _lead_to_dict(lead)}
    finally:
        db.close()
