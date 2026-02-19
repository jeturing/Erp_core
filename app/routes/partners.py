"""
Partners Management Routes — Gestión de socios comerciales
Basado en el Acuerdo Global de Partnership (No Exclusivo)
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Cookie, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from ..models.database import (
    Customer, Partner, Lead, Commission, SessionLocal,
    PartnerStatus, BillingScenario, PartnerPricingOverride, Plan, SupportLevel,
)
from .roles import _require_admin

router = APIRouter(prefix="/api/partners", tags=["Partners"])


# ── DTOs ──

class PartnerCreate(BaseModel):
    customer_id: Optional[int] = None
    company_name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: str
    phone: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    billing_scenario: str = "jeturing_collects"
    commission_rate: float = 50.0
    margin_cap: float = 30.0
    contract_reference: Optional[str] = None
    notes: Optional[str] = None


class PartnerUpdate(BaseModel):
    company_name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None
    billing_scenario: Optional[str] = None
    commission_rate: Optional[float] = None
    margin_cap: Optional[float] = None
    status: Optional[str] = None
    portal_access: Optional[bool] = None
    contract_reference: Optional[str] = None
    notes: Optional[str] = None


def _partner_to_dict(p: Partner) -> dict:
    return {
        "id": p.id,
        "customer_id": p.customer_id,
        "company_name": p.company_name,
        "legal_name": p.legal_name,
        "tax_id": p.tax_id,
        "contact_name": p.contact_name,
        "contact_email": p.contact_email,
        "phone": p.phone,
        "country": p.country,
        "address": p.address,
        "billing_scenario": p.billing_scenario.value if p.billing_scenario else None,
        "commission_rate": p.commission_rate,
        "margin_cap": p.margin_cap,
        "status": p.status.value if p.status else None,
        "portal_access": p.portal_access,
        "contract_signed_at": p.contract_signed_at.isoformat() if p.contract_signed_at else None,
        "contract_reference": p.contract_reference,
        "notes": p.notes,
        "leads_count": len(p.leads) if p.leads else 0,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


# ── Routes ──

@router.get("")
async def list_partners(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    status_filter: Optional[str] = None,
):
    """Lista todos los partners (admin only)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        q = db.query(Partner)
        if status_filter:
            try:
                q = q.filter(Partner.status == PartnerStatus(status_filter))
            except ValueError:
                pass
        partners = q.order_by(Partner.created_at.desc()).all()
        items = [_partner_to_dict(p) for p in partners]

        # Estadísticas rápidas
        total_active = sum(1 for i in items if i["status"] == "active")
        total_leads = sum(i["leads_count"] for i in items)

        return {
            "items": items,
            "total": len(items),
            "summary": {
                "active": total_active,
                "pending": sum(1 for i in items if i["status"] == "pending"),
                "total_leads": total_leads,
            },
        }
    finally:
        db.close()


@router.get("/{partner_id}")
async def get_partner(
    partner_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Detalle de un partner con resumen de leads y comisiones."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        data = _partner_to_dict(partner)

        # Resumen de leads
        leads = db.query(Lead).filter(Lead.partner_id == partner_id).all()
        data["leads_summary"] = {
            "total": len(leads),
            "won": sum(1 for l in leads if l.status.value == "won"),
            "active": sum(1 for l in leads if l.status.value in ("new", "contacted", "qualified", "proposal")),
            "estimated_value": sum(l.estimated_monthly_value or 0 for l in leads),
        }

        # Resumen de comisiones
        comms = db.query(Commission).filter(Commission.partner_id == partner_id).all()
        data["commissions_summary"] = {
            "total": len(comms),
            "total_partner_amount": sum(c.partner_amount or 0 for c in comms),
            "pending": sum(1 for c in comms if c.status.value == "pending"),
            "paid": sum(1 for c in comms if c.status.value == "paid"),
        }

        return data
    finally:
        db.close()


@router.post("")
async def create_partner(
    payload: PartnerCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Registra un nuevo partner (socio comercial)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        # Verificar email único
        existing = db.query(Partner).filter(Partner.contact_email == payload.contact_email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Ya existe un partner con ese email")

        # Verificar customer_id si se provee
        if payload.customer_id:
            cust = db.query(Customer).filter(Customer.id == payload.customer_id).first()
            if not cust:
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            dup = db.query(Partner).filter(Partner.customer_id == payload.customer_id).first()
            if dup:
                raise HTTPException(status_code=409, detail="Ese cliente ya está vinculado a un partner")

        try:
            scenario = BillingScenario(payload.billing_scenario)
        except ValueError:
            scenario = BillingScenario.jeturing_collects

        partner = Partner(
            customer_id=payload.customer_id,
            company_name=payload.company_name,
            legal_name=payload.legal_name,
            tax_id=payload.tax_id,
            contact_name=payload.contact_name,
            contact_email=payload.contact_email,
            phone=payload.phone,
            country=payload.country,
            address=payload.address,
            billing_scenario=scenario,
            commission_rate=payload.commission_rate,
            margin_cap=payload.margin_cap,
            status=PartnerStatus.pending,
            portal_access=True,
            contract_reference=payload.contract_reference,
            notes=payload.notes,
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)

        return {"message": "Partner creado exitosamente", "partner": _partner_to_dict(partner)}
    finally:
        db.close()


@router.put("/{partner_id}")
async def update_partner(
    partner_id: int,
    payload: PartnerUpdate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Actualiza datos de un partner."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        changes = []
        for field, value in payload.dict(exclude_unset=True).items():
            if field == "billing_scenario" and value:
                try:
                    value = BillingScenario(value)
                except ValueError:
                    continue
            elif field == "status" and value:
                try:
                    value = PartnerStatus(value)
                    if value == PartnerStatus.active and not partner.contract_signed_at:
                        partner.contract_signed_at = datetime.utcnow()
                except ValueError:
                    continue

            old = getattr(partner, field, None)
            if old != value:
                setattr(partner, field, value)
                changes.append(field)

        db.commit()
        db.refresh(partner)

        return {"message": "Partner actualizado", "changes": changes, "partner": _partner_to_dict(partner)}
    finally:
        db.close()


@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Elimina un partner (soft: cambia status a terminated)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        partner.status = PartnerStatus.terminated
        partner.portal_access = False
        db.commit()

        return {"message": f"Partner '{partner.company_name}' desactivado"}
    finally:
        db.close()


@router.post("/{partner_id}/activate")
async def activate_partner(
    partner_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Activa un partner y marca fecha de firma del contrato."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        partner.status = PartnerStatus.active
        if not partner.contract_signed_at:
            partner.contract_signed_at = datetime.utcnow()
        partner.portal_access = True
        db.commit()
        db.refresh(partner)

        return {"message": f"Partner '{partner.company_name}' activado", "partner": _partner_to_dict(partner)}
    finally:
        db.close()


# ══════════════════════════════════════════════════════
# PARTNER PRICING OVERRIDES
# ══════════════════════════════════════════════════════

class PricingOverrideCreate(BaseModel):
    plan_name: str                                       # basic, pro, enterprise
    base_price_override: Optional[float] = None
    price_per_user_override: Optional[float] = None
    included_users_override: Optional[int] = None
    setup_fee: float = 0
    customization_hourly_rate: Optional[float] = None
    support_level: str = "helpdesk_only"
    ecf_passthrough: bool = False
    ecf_monthly_cost: Optional[float] = None
    label: Optional[str] = None
    notes: Optional[str] = None


class PricingOverrideUpdate(BaseModel):
    base_price_override: Optional[float] = None
    price_per_user_override: Optional[float] = None
    included_users_override: Optional[int] = None
    setup_fee: Optional[float] = None
    customization_hourly_rate: Optional[float] = None
    support_level: Optional[str] = None
    ecf_passthrough: Optional[bool] = None
    ecf_monthly_cost: Optional[float] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


def _pricing_override_to_dict(po: PartnerPricingOverride) -> dict:
    return {
        "id": po.id,
        "partner_id": po.partner_id,
        "plan_name": po.plan_name,
        "base_price_override": po.base_price_override,
        "price_per_user_override": po.price_per_user_override,
        "included_users_override": po.included_users_override,
        "setup_fee": po.setup_fee,
        "customization_hourly_rate": po.customization_hourly_rate,
        "support_level": po.support_level.value if po.support_level else None,
        "ecf_passthrough": po.ecf_passthrough,
        "ecf_monthly_cost": po.ecf_monthly_cost,
        "label": po.label,
        "notes": po.notes,
        "is_active": po.is_active,
        "valid_from": po.valid_from.isoformat() if po.valid_from else None,
        "valid_until": po.valid_until.isoformat() if po.valid_until else None,
        "created_at": po.created_at.isoformat() if po.created_at else None,
        "updated_at": po.updated_at.isoformat() if po.updated_at else None,
    }


@router.get("/{partner_id}/pricing")
async def list_pricing_overrides(
    partner_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Lista los pricing overrides de un partner."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        overrides = db.query(PartnerPricingOverride).filter(
            PartnerPricingOverride.partner_id == partner_id
        ).order_by(PartnerPricingOverride.plan_name).all()

        items = [_pricing_override_to_dict(po) for po in overrides]

        # Enriquecer con precios globales del plan para comparación
        for item in items:
            plan = db.query(Plan).filter(Plan.name == item["plan_name"]).first()
            if plan:
                item["global_base_price"] = plan.base_price
                item["global_price_per_user"] = plan.price_per_user
                item["global_included_users"] = plan.included_users

        return {"items": items, "total": len(items), "partner_id": partner_id}
    finally:
        db.close()


@router.post("/{partner_id}/pricing")
async def create_pricing_override(
    partner_id: int,
    payload: PricingOverrideCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Crea un pricing override para un partner en un plan específico."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        # Verificar que no existe override para este plan
        existing = db.query(PartnerPricingOverride).filter(
            PartnerPricingOverride.partner_id == partner_id,
            PartnerPricingOverride.plan_name == payload.plan_name,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Ya existe un override para el plan '{payload.plan_name}'")

        # Verificar plan válido
        valid_plans = ['basic', 'pro', 'enterprise']
        if payload.plan_name not in valid_plans:
            raise HTTPException(status_code=400, detail=f"Plan inválido. Opciones: {valid_plans}")

        try:
            sl = SupportLevel(payload.support_level)
        except ValueError:
            sl = SupportLevel.helpdesk_only

        override = PartnerPricingOverride(
            partner_id=partner_id,
            plan_name=payload.plan_name,
            base_price_override=payload.base_price_override,
            price_per_user_override=payload.price_per_user_override,
            included_users_override=payload.included_users_override,
            setup_fee=payload.setup_fee,
            customization_hourly_rate=payload.customization_hourly_rate,
            support_level=sl,
            ecf_passthrough=payload.ecf_passthrough,
            ecf_monthly_cost=payload.ecf_monthly_cost,
            label=payload.label,
            notes=payload.notes,
        )
        db.add(override)
        db.commit()
        db.refresh(override)

        return {"message": "Pricing override creado", "override": _pricing_override_to_dict(override)}
    finally:
        db.close()


@router.put("/{partner_id}/pricing/{override_id}")
async def update_pricing_override(
    partner_id: int,
    override_id: int,
    payload: PricingOverrideUpdate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Actualiza un pricing override existente."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        override = db.query(PartnerPricingOverride).filter(
            PartnerPricingOverride.id == override_id,
            PartnerPricingOverride.partner_id == partner_id,
        ).first()
        if not override:
            raise HTTPException(status_code=404, detail="Pricing override no encontrado")

        changes = []
        for field, value in payload.dict(exclude_unset=True).items():
            if field == "support_level" and value:
                try:
                    value = SupportLevel(value)
                except ValueError:
                    continue
            old = getattr(override, field, None)
            if old != value:
                setattr(override, field, value)
                changes.append(field)

        db.commit()
        db.refresh(override)

        return {"message": "Pricing override actualizado", "changes": changes, "override": _pricing_override_to_dict(override)}
    finally:
        db.close()


@router.delete("/{partner_id}/pricing/{override_id}")
async def delete_pricing_override(
    partner_id: int,
    override_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Elimina un pricing override."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        override = db.query(PartnerPricingOverride).filter(
            PartnerPricingOverride.id == override_id,
            PartnerPricingOverride.partner_id == partner_id,
        ).first()
        if not override:
            raise HTTPException(status_code=404, detail="Pricing override no encontrado")

        db.delete(override)
        db.commit()

        return {"message": "Pricing override eliminado"}
    finally:
        db.close()


@router.get("/{partner_id}/simulate-pricing")
async def simulate_pricing(
    partner_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    plan_name: str = "basic",
    user_count: int = 1,
):
    """
    Simula el precio mensual para un partner con sus overrides aplicados.
    Compara precio público vs precio partner.
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        plan = db.query(Plan).filter(Plan.name == plan_name).first()
        if not plan:
            # Fallback a precios hardcodeados si no hay planes en BD
            plan_defaults = {"basic": (29, 10, 1), "pro": (79, 15, 3), "enterprise": (199, 20, 10)}
            defaults = plan_defaults.get(plan_name, (29, 10, 1))
            public_price = defaults[0] + max(0, user_count - defaults[2]) * defaults[1]
            partner_price = public_price  # Sin override

            override = db.query(PartnerPricingOverride).filter(
                PartnerPricingOverride.partner_id == partner_id,
                PartnerPricingOverride.plan_name == plan_name,
                PartnerPricingOverride.is_active == True,
            ).first()

            if override:
                base = override.base_price_override if override.base_price_override is not None else defaults[0]
                ppu = override.price_per_user_override if override.price_per_user_override is not None else defaults[1]
                incl = override.included_users_override if override.included_users_override is not None else defaults[2]
                partner_price = base + max(0, user_count - incl) * ppu

            return {
                "plan": plan_name,
                "user_count": user_count,
                "public_price": public_price,
                "partner_price": partner_price,
                "discount_pct": round((1 - partner_price / public_price) * 100, 1) if public_price > 0 else 0,
                "setup_fee": override.setup_fee if override else 0,
                "customization_rate": override.customization_hourly_rate if override else None,
                "partner": partner.company_name,
            }

        public_price = plan.calculate_monthly(user_count)
        partner_price = plan.calculate_monthly(user_count, partner_id=partner_id)

        override = db.query(PartnerPricingOverride).filter(
            PartnerPricingOverride.partner_id == partner_id,
            PartnerPricingOverride.plan_name == plan_name,
            PartnerPricingOverride.is_active == True,
        ).first()

        return {
            "plan": plan_name,
            "user_count": user_count,
            "public_price": public_price,
            "partner_price": partner_price,
            "discount_pct": round((1 - partner_price / public_price) * 100, 1) if public_price > 0 else 0,
            "setup_fee": override.setup_fee if override else 0,
            "customization_rate": override.customization_hourly_rate if override else None,
            "support_level": override.support_level.value if override and override.support_level else "standard",
            "ecf_passthrough": override.ecf_passthrough if override else False,
            "ecf_monthly_cost": override.ecf_monthly_cost if override else None,
            "partner": partner.company_name,
        }
    finally:
        db.close()
