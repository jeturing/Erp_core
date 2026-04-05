"""
Partners Management Routes — Gestión de socios comerciales
Basado en el Acuerdo Global de Partnership (No Exclusivo)
"""
from datetime import datetime
from typing import List, Optional
import secrets
import string
import logging

from fastapi import APIRouter, Cookie, HTTPException, Request, status
from pydantic import BaseModel, EmailStr

from ..models.database import (
    Customer, Partner, Lead, Commission, Subscription, SubscriptionStatus, SessionLocal,
    PartnerStatus, BillingScenario, PartnerPricingOverride, Plan, SupportLevel,
)
from .roles import _require_admin

router = APIRouter(prefix="/api/partners", tags=["Partners"])
logger = logging.getLogger(__name__)


def _generate_partner_code(db) -> str:
    """Genera un código único de partner: P-XXXX (4 alfanuméricos uppercase)."""
    chars = string.ascii_uppercase + string.digits
    for _ in range(100):
        code = "P-" + "".join(secrets.choice(chars) for _ in range(4))
        existing = db.query(Partner).filter(Partner.partner_code == code).first()
        if not existing:
            return code
    raise ValueError("No se pudo generar un código de partner único")


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
        "partner_code": p.partner_code,
        "stripe_account_id": p.stripe_account_id,
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
            partner_code=_generate_partner_code(db),
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


@router.delete("/{partner_id}/permanent")
async def hard_delete_partner(
    partner_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Elimina permanentemente un partner. Solo permitido si status=terminated y sin clientes/leads activos."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        if partner.status != PartnerStatus.terminated:
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden eliminar permanentemente partners con status 'terminated'. Desactívalo primero."
            )

        # Verificar que no tenga clientes vinculados
        linked_customers = db.query(Customer).filter(Customer.partner_id == partner_id).count()
        if linked_customers > 0:
            raise HTTPException(
                status_code=400,
                detail=f"El partner tiene {linked_customers} cliente(s) vinculado(s). Desvincúlalos antes de eliminar."
            )

        # Verificar que no tenga leads activos
        from ..models.database import Lead
        active_leads = db.query(Lead).filter(Lead.partner_id == partner_id).count()
        if active_leads > 0:
            raise HTTPException(
                status_code=400,
                detail=f"El partner tiene {active_leads} lead(s). Elimínalos antes de eliminar el partner."
            )

        # Eliminar pricing overrides primero (FK)
        db.query(PartnerPricingOverride).filter(PartnerPricingOverride.partner_id == partner_id).delete()

        company_name = partner.company_name
        partner_code = partner.partner_code
        db.delete(partner)
        db.commit()

        logger.info(f"Partner eliminado permanentemente: {company_name} ({partner_code})")
        return {"success": True, "message": f"Partner '{company_name}' ({partner_code}) eliminado permanentemente", "data": {}, "meta": {}}
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
    max_users_override: Optional[int] = None
    max_storage_mb_override: Optional[int] = None
    max_stock_sku_override: Optional[int] = None
    setup_fee: float = 0
    customization_hourly_rate: Optional[float] = None
    support_level: str = "helpdesk_only"
    ecf_passthrough: bool = False
    ecf_monthly_cost: Optional[float] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class PricingOverrideUpdate(BaseModel):
    base_price_override: Optional[float] = None
    price_per_user_override: Optional[float] = None
    included_users_override: Optional[int] = None
    max_users_override: Optional[int] = None
    max_storage_mb_override: Optional[int] = None
    max_stock_sku_override: Optional[int] = None
    setup_fee: Optional[float] = None
    customization_hourly_rate: Optional[float] = None
    support_level: Optional[str] = None
    ecf_passthrough: Optional[bool] = None
    ecf_monthly_cost: Optional[float] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: Optional[bool] = None


def _pricing_override_to_dict(po: PartnerPricingOverride) -> dict:
    return {
        "id": po.id,
        "partner_id": po.partner_id,
        "plan_name": po.plan_name,
        "base_price_override": po.base_price_override,
        "price_per_user_override": po.price_per_user_override,
        "included_users_override": po.included_users_override,
        "max_users_override": po.max_users_override,
        "max_storage_mb_override": po.max_storage_mb_override,
        "max_stock_sku_override": po.max_stock_sku_override,
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


def _validate_partner_override_quotas(db, plan_name: str, payload) -> None:
    plan = db.query(Plan).filter(Plan.name == plan_name).first()
    if not plan:
        raise HTTPException(status_code=400, detail=f"Plan '{plan_name}' no existe")

    storage_override = getattr(payload, "max_storage_mb_override", None)
    if storage_override is not None and plan.max_storage_mb not in (None, 0):
        storage_limit = int(plan.max_storage_mb) * 2
        if storage_override > storage_limit:
            raise HTTPException(
                status_code=400,
                detail=f"max_storage_mb_override excede el techo permitido ({storage_limit} MB)",
            )

    stock_override = getattr(payload, "max_stock_sku_override", None)
    if stock_override is not None and plan.max_stock_sku not in (None, 0):
        stock_limit = int(plan.max_stock_sku) * 2
        if stock_override > stock_limit:
            raise HTTPException(
                status_code=400,
                detail=f"max_stock_sku_override excede el techo permitido ({stock_limit} SKU)",
            )


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
                item["global_max_users"] = plan.max_users
                item["global_max_storage_mb"] = plan.max_storage_mb
                item["global_max_stock_sku"] = plan.max_stock_sku

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

        _validate_partner_override_quotas(db, payload.plan_name, payload)

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
            max_users_override=payload.max_users_override,
            max_storage_mb_override=payload.max_storage_mb_override,
            max_stock_sku_override=payload.max_stock_sku_override,
            setup_fee=payload.setup_fee,
            customization_hourly_rate=payload.customization_hourly_rate,
            support_level=sl,
            ecf_passthrough=payload.ecf_passthrough,
            ecf_monthly_cost=payload.ecf_monthly_cost,
            label=payload.label,
            notes=payload.notes,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
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

        _validate_partner_override_quotas(db, override.plan_name, payload)

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


# ══════════════════════════════════════════════════════
# CUSTOMER ↔ PARTNER LINKING / TRANSFER
# ══════════════════════════════════════════════════════

class LinkCustomerRequest(BaseModel):
    customer_id: int


class TransferCustomerRequest(BaseModel):
    customer_id: int
    send_email: bool = True


class PartnerChangeRequest(BaseModel):
    """Cliente solicita cambio de partner usando un código."""
    partner_code: str


@router.get("/{partner_id}/available-customers")
async def list_available_customers(
    partner_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
    search: Optional[str] = None,
):
    """Lista clientes sin partner asignado (disponibles para vincular)."""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        q = db.query(Customer).filter(Customer.partner_id == None)
        if search:
            s = f"%{search}%"
            q = q.filter(
                (Customer.company_name.ilike(s)) |
                (Customer.email.ilike(s)) |
                (Customer.subdomain.ilike(s))
            )

        customers = q.order_by(Customer.company_name).limit(50).all()
        items = []
        for c in customers:
            sub = db.query(Subscription).filter(
                Subscription.customer_id == c.id,
                Subscription.status == SubscriptionStatus.active,
            ).first()
            items.append({
                "id": c.id,
                "company_name": c.company_name,
                "email": c.email,
                "subdomain": c.subdomain,
                "plan_name": sub.plan_name if sub else None,
                "user_count": c.user_count or 1,
                "is_admin_account": c.is_admin_account or False,
            })

        return {"items": items, "total": len(items)}
    finally:
        db.close()


@router.post("/{partner_id}/link-customer")
async def link_customer_to_partner(
    partner_id: int,
    payload: LinkCustomerRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Vincula un cliente sin partner al partner indicado.
    Si el cliente ya tiene partner → error (debe usar transfer).
    Actualiza customer.partner_id y subscription.partner_id.
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if customer.partner_id is not None:
            existing_partner = db.query(Partner).filter(Partner.id == customer.partner_id).first()
            raise HTTPException(
                status_code=409,
                detail=f"El cliente ya está vinculado al partner '{existing_partner.company_name if existing_partner else customer.partner_id}'. "
                       f"Use el proceso de transferencia para cambiar de partner."
            )

        # Vincular
        customer.partner_id = partner_id

        # Actualizar suscripciones activas
        subs = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).all()
        for sub in subs:
            sub.owner_partner_id = partner_id

        db.commit()

        logger.info(f"✅ Cliente '{customer.company_name}' vinculado a partner '{partner.company_name}'")

        return {
            "message": f"Cliente '{customer.company_name}' vinculado exitosamente a '{partner.company_name}'",
            "customer_id": customer.id,
            "partner_id": partner_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error vinculando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{partner_id}/unlink-customer/{customer_id}")
async def unlink_customer_from_partner(
    partner_id: int,
    customer_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Desvincula un cliente de su partner (baja).
    Limpia customer.partner_id y subscription.partner_id.
    Envía notificación al cliente.
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        if customer.partner_id != partner_id:
            raise HTTPException(
                status_code=400,
                detail="Este cliente no está vinculado a este partner"
            )

        # Desvincular
        old_partner_name = partner.company_name
        customer.partner_id = None

        # Limpiar suscripciones
        subs = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).all()
        for sub in subs:
            sub.owner_partner_id = None

        db.commit()

        # Enviar email de notificación
        try:
            from ..services.email_service import send_partner_change_notification
            send_partner_change_notification(
                to_email=customer.email,
                company_name=customer.company_name or customer.subdomain,
                old_partner_name=old_partner_name,
                new_partner_name=None,
                action="unlink",
            )
        except Exception as email_err:
            logger.warning(f"No se pudo enviar email de desvinculación: {email_err}")

        logger.info(f"✅ Cliente '{customer.company_name}' desvinculado de partner '{old_partner_name}'")

        return {
            "message": f"Cliente '{customer.company_name}' desvinculado de '{old_partner_name}'",
            "customer_id": customer_id,
            "partner_id": partner_id,
            "email_sent": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error desvinculando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/{partner_id}/transfer-customer")
async def transfer_customer_to_partner(
    partner_id: int,
    payload: TransferCustomerRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Transfiere un cliente de un partner a otro.
    1. Desvincula del partner anterior
    2. Vincula al nuevo partner
    3. Actualiza suscripciones
    4. Envía email al cliente notificando el cambio
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        new_partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not new_partner:
            raise HTTPException(status_code=404, detail="Partner destino no encontrado")

        customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        old_partner_name = None
        old_partner_id = customer.partner_id
        if old_partner_id:
            old_partner = db.query(Partner).filter(Partner.id == old_partner_id).first()
            old_partner_name = old_partner.company_name if old_partner else f"Partner #{old_partner_id}"

        if old_partner_id == partner_id:
            raise HTTPException(status_code=400, detail="El cliente ya pertenece a este partner")

        # Transferir
        customer.partner_id = partner_id

        # Actualizar suscripciones
        subs = db.query(Subscription).filter(
            Subscription.customer_id == customer.id,
            Subscription.status == SubscriptionStatus.active,
        ).all()
        for sub in subs:
            sub.owner_partner_id = partner_id

        db.commit()

        # Enviar email
        if payload.send_email:
            try:
                from ..services.email_service import send_partner_change_notification
                send_partner_change_notification(
                    to_email=customer.email,
                    company_name=customer.company_name or customer.subdomain,
                    old_partner_name=old_partner_name,
                    new_partner_name=new_partner.company_name,
                    action="transfer",
                )
            except Exception as email_err:
                logger.warning(f"No se pudo enviar email de transferencia: {email_err}")

        action_desc = f"transferido de '{old_partner_name}'" if old_partner_name else "vinculado"
        logger.info(f"✅ Cliente '{customer.company_name}' {action_desc} a '{new_partner.company_name}'")

        return {
            "message": f"Cliente '{customer.company_name}' {action_desc} a '{new_partner.company_name}'",
            "customer_id": customer.id,
            "old_partner_id": old_partner_id,
            "new_partner_id": partner_id,
            "email_sent": payload.send_email,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error transfiriendo cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ── Endpoint para que el CLIENTE solicite cambio de partner usando código ──

@router.post("/request-partner-change")
async def request_partner_change_by_code(
    payload: PartnerChangeRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Un cliente o admin ingresa un partner_code para vincular/transferir.
    Si el cliente no tiene partner → vincula directo.
    Si ya tiene partner → transfiere (con email).
    """
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        # Buscar partner por código
        target_partner = db.query(Partner).filter(
            Partner.partner_code == payload.partner_code.strip().upper()
        ).first()
        if not target_partner:
            raise HTTPException(status_code=404, detail="Código de partner no válido")

        if target_partner.status != PartnerStatus.active:
            raise HTTPException(status_code=400, detail="El partner no está activo")

        return {
            "partner_id": target_partner.id,
            "company_name": target_partner.company_name,
            "partner_code": target_partner.partner_code,
            "status": target_partner.status.value,
            "message": f"Partner '{target_partner.company_name}' encontrado. Confirme la vinculación.",
        }
    finally:
        db.close()
