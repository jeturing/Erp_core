"""
Partner Portal Routes — Endpoints accesibles por partners autenticados.
Incluye: onboarding, dashboard, leads, clientes, Stripe Connect self-service.
"""
import logging
import hashlib
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Cookie, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from ..models.database import (
    Partner, Lead, Commission, Customer, Subscription, Quotation,
    PartnerPricingOverride, Plan, PartnerBrandingProfile,
    SessionLocal, PartnerStatus, LeadStatus, QuotationStatus,
    BillingScenario, CommissionStatus,
    Invoice, InvoiceStatus,
)
from ..services.stripe_connect import (
    create_connect_account,
    create_onboarding_link,
    create_login_link,
    get_account_status,
    get_partner_balance,
)
from ..services.stripe_billing import (
    push_invoice_to_stripe,
    create_checkout_for_invoice,
)
from ..services.addon_billing_service import (
    list_available_addon_services,
    list_customer_addon_subscriptions,
    purchase_customer_addon,
)
from .roles import _extract_token, verify_token_with_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/partner-portal", tags=["Partner Portal"])


# ── Auth Helper ──

def _require_partner(request: Request, access_token: Optional[str] = None) -> dict:
    """Verifica que el usuario es un partner autenticado. Retorna payload JWT."""
    token = _extract_token(request, access_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    payload = verify_token_with_role(token)
    if payload.get("role") not in ("partner", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso solo para partners")
    return payload


def _get_partner(db, payload: dict) -> Partner:
    """Obtiene el partner desde el JWT payload."""
    partner_id = payload.get("user_id")
    if not partner_id:
        raise HTTPException(status_code=400, detail="Partner ID no encontrado en token")
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner no encontrado")
    return partner


def _apply_partner_stripe_status(partner: Partner, status_result: Dict[str, Any]) -> bool:
    ready = bool(status_result.get("onboarding_ready"))
    partner.stripe_charges_enabled = bool(status_result.get("charges_enabled", False))
    partner.stripe_onboarding_complete = ready

    if ready and partner.onboarding_step < 4:
        partner.onboarding_step = 4
        partner.onboarding_completed_at = datetime.utcnow()

    return ready


# ═══════════════════════════════════════════════
# ONBOARDING
# ═══════════════════════════════════════════════

class SetPasswordRequest(BaseModel):
    password: str
    password_confirm: str


class UpdateProfileRequest(BaseModel):
    company_name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    address: Optional[str] = None


class PartnerInviteRequest(BaseModel):
    """Admin crea partner + envía credenciales iniciales."""
    partner_id: int
    temp_password: str
    portal_email: Optional[str] = None  # Si difiere de contact_email


@router.post("/admin/invite")
async def admin_invite_partner(
    payload: PartnerInviteRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Admin asigna credenciales a un partner para que pueda entrar al portal.
    Genera password_hash y marca invited_at.
    """
    from .roles import _require_admin
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        if partner.password_hash and partner.onboarding_step > 0:
            raise HTTPException(status_code=409, detail="Partner ya tiene credenciales. Use reset-password.")

        # Generar hash de password
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((payload.temp_password + salt).encode()).hexdigest()
        partner.password_hash = f"{salt}:{password_hash}"

        # Configurar email de portal
        partner.portal_email = payload.portal_email or partner.contact_email
        partner.onboarding_step = 1  # Credenciales asignadas, pendiente completar perfil
        partner.portal_access = True
        partner.invited_at = datetime.utcnow()

        # Extraer admin username del token
        token = _extract_token(request, access_token)
        if token:
            try:
                admin_payload = verify_token_with_role(token)
                partner.invited_by = admin_payload.get("sub", "admin")
            except Exception:
                partner.invited_by = "admin"

        db.commit()
        db.refresh(partner)

        return {
            "message": f"Credenciales asignadas a {partner.company_name}",
            "portal_email": partner.portal_email,
            "onboarding_step": partner.onboarding_step,
            "login_url": f"https://sajet.us/#/login",
        }
    finally:
        db.close()


@router.post("/admin/reset-password")
async def admin_reset_partner_password(
    payload: PartnerInviteRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Admin resetea la contraseña de un partner."""
    from .roles import _require_admin
    _require_admin(request, access_token)

    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((payload.temp_password + salt).encode()).hexdigest()
        partner.password_hash = f"{salt}:{password_hash}"
        if payload.portal_email:
            partner.portal_email = payload.portal_email
        db.commit()

        return {"message": f"Password reseteada para {partner.company_name}"}
    finally:
        db.close()


@router.get("/onboarding/status")
async def get_onboarding_status(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Retorna el paso actual del onboarding y qué falta completar."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        stripe_requirements: List[str] = []
        stripe_disabled_reason: Optional[str] = None
        stripe_payouts_enabled = False
        settlement_mode = "domestic"

        if partner.stripe_account_id:
            status_result = await get_account_status(partner.stripe_account_id)
            if status_result.get("success"):
                stripe_requirements = status_result.get("requirements_currently_due", []) or []
                stripe_disabled_reason = status_result.get("requirements_disabled_reason")
                stripe_payouts_enabled = bool(status_result.get("payouts_enabled", False))
                settlement_mode = status_result.get("settlement_mode", settlement_mode)
                _apply_partner_stripe_status(partner, status_result)
                db.commit()

        steps = [
            {"step": 1, "name": "credentials", "label": "Acceso al Portal", "completed": partner.onboarding_step >= 1},
            {"step": 2, "name": "profile", "label": "Completar Perfil", "completed": partner.onboarding_step >= 2},
            {"step": 3, "name": "stripe_kyc", "label": "Stripe Connect (KYC)", "completed": partner.onboarding_step >= 3},
            {"step": 4, "name": "complete", "label": "Onboarding Completo", "completed": partner.onboarding_step >= 4},
        ]

        return {
            "current_step": partner.onboarding_step,
            "steps": steps,
            "completed": partner.onboarding_step >= 4,
            "completed_at": partner.onboarding_completed_at.isoformat() if partner.onboarding_completed_at else None,
            "stripe_account_id": partner.stripe_account_id,
            "stripe_onboarding_complete": partner.stripe_onboarding_complete,
            "stripe_charges_enabled": partner.stripe_charges_enabled,
            "stripe_payouts_enabled": stripe_payouts_enabled,
            "stripe_requirements": stripe_requirements,
            "stripe_disabled_reason": stripe_disabled_reason,
            "billing_scenario": partner.billing_scenario.value if partner.billing_scenario else None,
            "contract_signed_at": partner.contract_signed_at.isoformat() if partner.contract_signed_at else None,
            "can_skip_stripe": bool(partner.onboarding_bypass),
            "settlement_mode": settlement_mode,
        }
    finally:
        db.close()


@router.post("/onboarding/set-password")
async def onboarding_set_password(
    payload: SetPasswordRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Partner establece su propia contraseña (paso 1→2)."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        if payload.password != payload.password_confirm:
            raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
        if len(payload.password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((payload.password + salt).encode()).hexdigest()
        partner.password_hash = f"{salt}:{password_hash}"

        if partner.onboarding_step < 2:
            partner.onboarding_step = 2

        db.commit()
        return {"message": "Contraseña actualizada", "onboarding_step": partner.onboarding_step}
    finally:
        db.close()


@router.post("/onboarding/update-profile")
async def onboarding_update_profile(
    payload: UpdateProfileRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Partner completa su perfil comercial (paso 2→3)."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        for field, value in payload.dict(exclude_unset=True).items():
            if value is not None:
                setattr(partner, field, value)

        if partner.onboarding_step < 3:
            partner.onboarding_step = 3

        db.commit()
        return {"message": "Perfil actualizado", "onboarding_step": partner.onboarding_step}
    finally:
        db.close()


@router.post("/onboarding/start-stripe")
async def onboarding_start_stripe(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Crea cuenta Stripe Connect Express y genera link de onboarding KYC.
    El partner completa el KYC en Stripe y regresa.
    """
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        if not partner.contract_signed_at:
            raise HTTPException(
                status_code=400,
                detail="Debe firmar el acuerdo comercial antes de iniciar Stripe Connect.",
            )
        if not partner.country:
            raise HTTPException(
                status_code=400,
                detail="Complete el país del partner antes de iniciar Stripe Connect.",
            )

        # Si ya tiene cuenta, solo generar nuevo link
        if partner.stripe_account_id:
            link_result = await create_onboarding_link(
                partner.stripe_account_id,
                return_path="/#/partner/portal?stripe_return=true"
            )
            if not link_result["success"]:
                raise HTTPException(status_code=400, detail=link_result["error"])
            return {"onboarding_url": link_result["url"], "account_id": partner.stripe_account_id}

        # Crear cuenta nueva
        result = await create_connect_account(
            partner_email=partner.portal_email or partner.contact_email,
            partner_company=partner.company_name,
            partner_country=partner.country or "US",
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        partner.stripe_account_id = result["account_id"]
        db.commit()

        # Generar link de onboarding
        link_result = await create_onboarding_link(
            result["account_id"],
            return_path="/#/partner/portal?stripe_return=true"
        )

        return {
            "account_id": result["account_id"],
            "onboarding_url": link_result.get("url") if link_result["success"] else None,
            "message": "Cuenta Stripe Connect creada. Complete el KYC.",
        }
    finally:
        db.close()


@router.post("/onboarding/verify-stripe")
async def onboarding_verify_stripe(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Verifica que el KYC de Stripe esté completo y avanza el onboarding."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        if not partner.stripe_account_id:
            raise HTTPException(status_code=400, detail="No tiene cuenta Stripe Connect")

        status_result = await get_account_status(partner.stripe_account_id)
        if not status_result["success"]:
            raise HTTPException(status_code=400, detail=status_result["error"])

        _apply_partner_stripe_status(partner, status_result)

        db.commit()

        return {
            "charges_enabled": partner.stripe_charges_enabled,
            "details_submitted": status_result.get("details_submitted", False),
            "payouts_enabled": status_result.get("payouts_enabled", False),
            "requirements_currently_due": status_result.get("requirements_currently_due", []),
            "requirements_disabled_reason": status_result.get("requirements_disabled_reason"),
            "onboarding_step": partner.onboarding_step,
            "onboarding_complete": partner.onboarding_step >= 4,
        }
    finally:
        db.close()


@router.post("/onboarding/skip-stripe")
async def onboarding_skip_stripe(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Partner puede saltar Stripe (lo completa después) y entrar al portal."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        if not partner.onboarding_bypass:
            raise HTTPException(
                status_code=403,
                detail="Stripe Connect es obligatorio para habilitar pagos del partner.",
            )
        if partner.onboarding_step < 4:
            partner.onboarding_step = 4
            partner.onboarding_completed_at = datetime.utcnow()
        db.commit()
        return {"message": "Onboarding completado (Stripe pendiente)", "onboarding_step": 4}
    finally:
        db.close()


# ═══════════════════════════════════════════════
# DASHBOARD PARTNER
# ═══════════════════════════════════════════════

@router.get("/dashboard")
async def partner_dashboard(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Dashboard del partner con KPIs principales."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        # Leads
        leads = db.query(Lead).filter(Lead.partner_id == partner.id).all()
        active_leads = [l for l in leads if l.status.value in ("new", "contacted", "qualified", "in_qualification", "proposal")]
        won_leads = [l for l in leads if l.status.value == "won"]

        # Comisiones
        commissions = db.query(Commission).filter(Commission.partner_id == partner.id).all()
        total_earned = sum(c.partner_amount or 0 for c in commissions)
        pending_commissions = sum(c.partner_amount or 0 for c in commissions if c.status == CommissionStatus.pending)
        paid_commissions = sum(c.partner_amount or 0 for c in commissions if c.status == CommissionStatus.paid)

        # Clientes activos (suscripciones con este partner)
        active_subs = db.query(Subscription).filter(
            Subscription.owner_partner_id == partner.id,
        ).all()

        # Stripe balance
        stripe_balance = None
        if partner.stripe_account_id and partner.stripe_onboarding_complete:
            try:
                stripe_balance = await get_partner_balance(partner.stripe_account_id)
            except Exception:
                pass

        return {
            "partner": {
                "id": partner.id,
                "company_name": partner.company_name,
                "status": partner.status.value,
                "commission_rate": partner.commission_rate,
                "onboarding_step": partner.onboarding_step,
                "stripe_onboarding_complete": partner.stripe_onboarding_complete,
                "stripe_charges_enabled": partner.stripe_charges_enabled,
            },
            "kpis": {
                "total_leads": len(leads),
                "active_leads": len(active_leads),
                "won_leads": len(won_leads),
                "conversion_rate": round(len(won_leads) / len(leads) * 100, 1) if leads else 0,
                "active_clients": len(active_subs),
                "total_earned": total_earned,
                "pending_commissions": pending_commissions,
                "paid_commissions": paid_commissions,
                "estimated_pipeline": sum(l.estimated_monthly_value or 0 for l in active_leads),
            },
            "stripe_balance": stripe_balance if stripe_balance and stripe_balance.get("success") else None,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════
# LEADS — Self-service CRUD
# ═══════════════════════════════════════════════

class PartnerLeadCreate(BaseModel):
    company_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    estimated_monthly_value: float = 0


class PartnerLeadUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    notes: Optional[str] = None
    estimated_monthly_value: Optional[float] = None
    status: Optional[str] = None


@router.get("/leads")
async def list_partner_leads(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    status_filter: Optional[str] = None,
):
    """Lista los leads del partner autenticado."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        q = db.query(Lead).filter(Lead.partner_id == partner.id)
        if status_filter:
            try:
                q = q.filter(Lead.status == LeadStatus(status_filter))
            except ValueError:
                pass

        leads = q.order_by(Lead.registered_at.desc()).all()
        items = []
        for l in leads:
            items.append({
                "id": l.id,
                "company_name": l.company_name,
                "contact_name": l.contact_name,
                "contact_email": l.contact_email,
                "phone": l.phone,
                "country": l.country,
                "status": l.status.value if l.status else None,
                "estimated_monthly_value": l.estimated_monthly_value,
                "notes": l.notes,
                "registered_at": l.registered_at.isoformat() if l.registered_at else None,
                "updated_at": l.updated_at.isoformat() if l.updated_at else None,
            })

        pipeline = {}
        for s in LeadStatus:
            pipeline[s.value] = sum(1 for i in items if i["status"] == s.value)

        return {
            "items": items,
            "total": len(items),
            "pipeline": pipeline,
        }
    finally:
        db.close()


@router.post("/leads")
async def create_partner_lead(
    payload: PartnerLeadCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """El partner registra un nuevo lead."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        if partner.status != PartnerStatus.active:
            raise HTTPException(status_code=403, detail="Tu cuenta de partner no está activa")

        lead = Lead(
            partner_id=partner.id,
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

        return {"message": "Lead registrado exitosamente", "lead_id": lead.id}
    finally:
        db.close()


@router.put("/leads/{lead_id}")
async def update_partner_lead(
    lead_id: int,
    payload: PartnerLeadUpdate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """El partner actualiza uno de sus leads."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        lead = db.query(Lead).filter(Lead.id == lead_id, Lead.partner_id == partner.id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead no encontrado")

        # Partners solo pueden cambiar status a ciertos valores
        allowed_statuses = {"new", "contacted", "qualified", "in_qualification", "proposal", "lost"}
        for field, value in payload.dict(exclude_unset=True).items():
            if field == "status" and value:
                if value not in allowed_statuses:
                    raise HTTPException(status_code=403, detail=f"No puedes cambiar a status '{value}'")
                try:
                    value = LeadStatus(value)
                except ValueError:
                    continue
            setattr(lead, field, value)

        db.commit()
        return {"message": "Lead actualizado"}
    finally:
        db.close()


# ═══════════════════════════════════════════════
# CLIENTES — Vista de clientes del partner
# ═══════════════════════════════════════════════

@router.get("/clients")
async def list_partner_clients(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Lista clientes activos del partner (suscripciones asignadas)."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        subs = db.query(Subscription).filter(
            Subscription.owner_partner_id == partner.id,
        ).all()

        clients = []
        for sub in subs:
            customer = db.query(Customer).filter(Customer.id == sub.customer_id).first()
            if customer:
                clients.append({
                    "subscription_id": sub.id,
                    "customer_id": customer.id,
                    "company_name": customer.company_name,
                    "email": customer.email,
                    "subdomain": customer.subdomain,
                    "plan": sub.plan_name,
                    "status": sub.status.value if sub.status else None,
                    "billing_mode": sub.billing_mode.value if sub.billing_mode else None,
                    "monthly_amount": sub.monthly_amount,
                    "user_count": sub.user_count,
                    "url": f"https://{customer.subdomain}.sajet.us" if customer.subdomain else None,
                    "created_at": sub.created_at.isoformat() if sub.created_at else None,
                })

        return {"items": clients, "total": len(clients)}
    finally:
        db.close()


# ── Crear Cliente desde Portal Partner ──

class PartnerClientCreate(BaseModel):
    company_name: str
    contact_email: str
    subdomain: str
    plan_name: str = "basic"
    user_count: int = 1
    contact_name: Optional[str] = None
    notes: Optional[str] = None


class PartnerClientAddonPurchase(BaseModel):
    catalog_item_id: int
    quantity: int = 1


@router.post("/clients")
async def create_partner_client(
    payload: PartnerClientCreate,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    El partner crea un nuevo cliente con auto-provisioning del tenant Odoo.

    Flujo completo:
    1. Valida que el partner está activo
    2. Crea Customer + Subscription en BD local (vinculado al partner)
    3. Provisiona la BD Odoo automáticamente (clona template_tenant)
    4. Provisiona subdominio en nginx
    5. Retorna credenciales del tenant

    Esto cierra el gap: el partner puede crear clientes completos
    sin necesitar intervención del admin.
    """
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        if partner.status != PartnerStatus.active:
            raise HTTPException(
                status_code=403,
                detail="Tu cuenta de partner no está activa. Contacta a soporte."
            )

        # Validar subdominio
        import re
        subdomain = payload.subdomain.strip().lower().replace("-", "_")
        if not re.match(r'^[a-z0-9][a-z0-9_]{1,28}[a-z0-9]$', subdomain):
            raise HTTPException(
                status_code=400,
                detail="Subdominio inválido. Solo letras minúsculas, números y guiones bajos (3-30 chars)."
            )

        # Verificar que no exista
        existing = db.query(Customer).filter(Customer.subdomain == subdomain).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"El subdominio '{subdomain}' ya está en uso")

        # Validar plan
        plan = db.query(Plan).filter(Plan.name == payload.plan_name, Plan.is_active == True).first()
        if not plan:
            raise HTTPException(status_code=400, detail=f"Plan '{payload.plan_name}' no existe o no está activo")

        from ..models.database import BillingMode, PayerType, CollectorType, InvoiceIssuer

        # Crear cliente vinculado al partner
        customer = Customer(
            email=payload.contact_email,
            full_name=payload.contact_name or "",
            company_name=payload.company_name,
            subdomain=subdomain,
            user_count=payload.user_count,
            partner_id=partner.id,
        )
        db.add(customer)
        db.flush()

        # Crear suscripción con pricing override del partner
        calculated_amount = plan.calculate_monthly(payload.user_count, partner.id)
        sub = Subscription(
            customer_id=customer.id,
            plan_name=payload.plan_name,
            status=SubscriptionStatus.active,
            user_count=payload.user_count,
            monthly_amount=calculated_amount,
            owner_partner_id=partner.id,
            billing_mode=BillingMode.PARTNER_DIRECT,
            payer_type=PayerType.PARTNER,
            collector=CollectorType.STRIPE_CONNECT,
            invoice_issuer=InvoiceIssuer.JETURING,
        )
        db.add(sub)
        db.commit()
        db.refresh(customer)
        db.refresh(sub)

        response = {
            "success": True,
            "customer_id": customer.id,
            "subscription_id": sub.id,
            "monthly_amount": calculated_amount,
            "message": f"Cliente '{payload.company_name}' creado exitosamente",
        }

        # Auto-provision tenant Odoo
        try:
            from .customers import _auto_provision_tenant
            tenant_result = await _auto_provision_tenant(
                subdomain=subdomain,
                company_name=payload.company_name,
                partner_id=partner.id,
                plan_name=payload.plan_name,
                subscription_id=sub.id,
                customer_id=customer.id,
            )
            if tenant_result.get("success"):
                response["tenant"] = {
                    "subdomain": subdomain,
                    "url": tenant_result.get("url", f"https://{subdomain}.sajet.us"),
                    "admin_login": tenant_result.get("admin_login"),
                    "admin_password": tenant_result.get("admin_password"),
                    "status": "active",
                }
                response["message"] += " + Tenant provisionado"
                logger.info(
                    f"✅ Partner {partner.company_name} creó cliente+tenant '{subdomain}'"
                )
            else:
                response["tenant_error"] = tenant_result.get("error")
                response["message"] += " (tenant pendiente — contacta soporte)"
                logger.warning(
                    f"⚠️ Partner {partner.company_name}: cliente creado pero tenant falló: "
                    f"{tenant_result.get('error')}"
                )
        except Exception as prov_err:
            response["tenant_error"] = str(prov_err)
            response["message"] += " (error en provisioning)"
            logger.error(f"Error en auto-provision para partner: {prov_err}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error partner creando cliente: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/clients/{customer_id}/services/catalog")
async def list_partner_client_service_catalog(
    customer_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Catálogo de add-ons disponibles para un cliente del partner."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.partner_id == partner.id,
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        items = list_available_addon_services(db, customer.id)
        return {"items": items, "total": len(items)}
    finally:
        db.close()


@router.get("/clients/{customer_id}/services/subscriptions")
async def list_partner_client_service_subscriptions(
    customer_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Servicios adicionales activos de un cliente del partner."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.partner_id == partner.id,
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        items = list_customer_addon_subscriptions(db, customer.id)
        return {"items": items, "total": len(items)}
    finally:
        db.close()


@router.post("/clients/{customer_id}/services/purchase")
async def purchase_partner_client_service(
    customer_id: int,
    payload: PartnerClientAddonPurchase,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Compra un add-on para un cliente gestionado por el partner."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        customer = db.query(Customer).filter(
            Customer.id == customer_id,
            Customer.partner_id == partner.id,
        ).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        result = purchase_customer_addon(
            db=db,
            customer_id=customer.id,
            catalog_item_id=payload.catalog_item_id,
            quantity=payload.quantity,
            acquired_via="partner_portal",
            notes=f"Compra gestionada por partner {partner.company_name}",
        )
        return {
            "message": f"Servicio adicional adquirido para {customer.company_name}",
            **result,
        }
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        db.close()


# ═══════════════════════════════════════════════
# COMISIONES — Vista de comisiones del partner
# ═══════════════════════════════════════════════

@router.get("/commissions")
async def list_partner_commissions(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Lista comisiones del partner."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        commissions = db.query(Commission).filter(
            Commission.partner_id == partner.id
        ).order_by(Commission.created_at.desc()).all()

        items = []
        for c in commissions:
            items.append({
                "id": c.id,
                "period_start": c.period_start.isoformat() if c.period_start else None,
                "period_end": c.period_end.isoformat() if c.period_end else None,
                "gross_revenue": c.gross_revenue,
                "net_revenue": c.net_revenue,
                "partner_amount": c.partner_amount,
                "jeturing_amount": c.jeturing_amount,
                "status": c.status.value if c.status else None,
                "paid_at": c.paid_at.isoformat() if c.paid_at else None,
                "payment_reference": c.payment_reference,
            })

        return {
            "items": items,
            "total": len(items),
            "summary": {
                "total_earned": sum(c["partner_amount"] or 0 for c in items),
                "pending": sum(c["partner_amount"] or 0 for c in items if c["status"] == "pending"),
                "paid": sum(c["partner_amount"] or 0 for c in items if c["status"] == "paid"),
            },
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════
# STRIPE CONNECT — Self-service
# ═══════════════════════════════════════════════

@router.get("/stripe/status")
async def partner_stripe_status(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Estado de Stripe Connect del partner."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        if not partner.stripe_account_id:
            return {"has_account": False, "message": "No tiene cuenta Stripe Connect"}

        result = await get_account_status(partner.stripe_account_id)

        # Actualizar flags en BD
        if result.get("success"):
            _apply_partner_stripe_status(partner, result)
            db.commit()

        result["has_account"] = True
        return result
    finally:
        db.close()


@router.get("/stripe/dashboard-link")
async def partner_stripe_dashboard(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Genera link para que el partner acceda a su Stripe Express Dashboard."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        if not partner.stripe_account_id:
            raise HTTPException(status_code=400, detail="No tiene cuenta Stripe Connect")

        result = await create_login_link(partner.stripe_account_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    finally:
        db.close()


@router.get("/stripe/balance")
async def partner_stripe_balance(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Balance actual del partner en Stripe."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        if not partner.stripe_account_id:
            raise HTTPException(status_code=400, detail="No tiene cuenta Stripe Connect")
        return await get_partner_balance(partner.stripe_account_id)
    finally:
        db.close()


# ═══════════════════════════════════════════════
# PERFIL — Self-service
# ═══════════════════════════════════════════════

@router.get("/profile")
async def get_partner_profile(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Perfil del partner autenticado."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        return {
            "id": partner.id,
            "company_name": partner.company_name,
            "legal_name": partner.legal_name,
            "tax_id": partner.tax_id,
            "contact_name": partner.contact_name,
            "contact_email": partner.contact_email,
            "portal_email": partner.portal_email,
            "phone": partner.phone,
            "country": partner.country,
            "address": partner.address,
            "billing_scenario": partner.billing_scenario.value if partner.billing_scenario else None,
            "commission_rate": partner.commission_rate,
            "status": partner.status.value if partner.status else None,
            "stripe_account_id": partner.stripe_account_id,
            "stripe_onboarding_complete": partner.stripe_onboarding_complete,
            "stripe_charges_enabled": partner.stripe_charges_enabled,
            "onboarding_step": partner.onboarding_step,
            "contract_signed_at": partner.contract_signed_at.isoformat() if partner.contract_signed_at else None,
            "contract_reference": partner.contract_reference,
            "created_at": partner.created_at.isoformat() if partner.created_at else None,
        }
    finally:
        db.close()


@router.put("/profile")
async def update_partner_profile(
    payload: UpdateProfileRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """El partner actualiza su propio perfil."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        for field, value in payload.dict(exclude_unset=True).items():
            if value is not None:
                setattr(partner, field, value)
        db.commit()
        return {"message": "Perfil actualizado"}
    finally:
        db.close()


@router.post("/change-password")
async def change_partner_password(
    payload: SetPasswordRequest,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Partner cambia su propia contraseña."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        if payload.password != payload.password_confirm:
            raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
        if len(payload.password) < 8:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((payload.password + salt).encode()).hexdigest()
        partner.password_hash = f"{salt}:{password_hash}"
        db.commit()

        return {"message": "Contraseña actualizada exitosamente"}
    finally:
        db.close()


# ═══════════════════════════════════════════════
# COTIZACIONES — Self-service
# ═══════════════════════════════════════════════

@router.get("/pricing")
async def get_partner_pricing(
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """Retorna los precios disponibles para el partner (con overrides aplicados)."""
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)
        plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.sort_order).all()

        result = []
        for plan in plans:
            override = db.query(PartnerPricingOverride).filter(
                PartnerPricingOverride.partner_id == partner.id,
                PartnerPricingOverride.plan_name == plan.name,
                PartnerPricingOverride.is_active == True,
            ).first()

            base = override.base_price_override if override and override.base_price_override is not None else plan.base_price
            ppu = override.price_per_user_override if override and override.price_per_user_override is not None else plan.price_per_user
            included = override.included_users_override if override and override.included_users_override is not None else plan.included_users

            result.append({
                "plan_name": plan.name,
                "display_name": plan.display_name,
                "base_price": base,
                "price_per_user": ppu,
                "included_users": included,
                "setup_fee": override.setup_fee if override else 0,
                "support_level": override.support_level.value if override and override.support_level else "helpdesk_only",
                "has_custom_pricing": override is not None,
            })

        return {"items": result}
    finally:
        db.close()


# ═══════════════════════════════════════════════
# FACTURAS — Facturas de clientes del partner
# ═══════════════════════════════════════════════

@router.get("/invoices")
async def list_partner_invoices(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    status_filter: Optional[str] = None,
):
    """
    Lista facturas de clientes asignados al partner.
    Según billing_scenario:
    - jeturing_collects: Partner ve facturas de sus clientes (referencia)
    - partner_collects: Partner ve facturas que debe cobrar
    """
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        q = db.query(Invoice).filter(Invoice.partner_id == partner.id)
        if status_filter:
            try:
                q = q.filter(Invoice.status == InvoiceStatus(status_filter))
            except ValueError:
                pass

        invoices = q.order_by(Invoice.created_at.desc()).limit(100).all()

        items = []
        for inv in invoices:
            customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
            item = {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_name": customer.company_name if customer else None,
                "customer_email": customer.email if customer else None,
                "total": inv.total,
                "currency": inv.currency,
                "status": inv.status.value if inv.status else None,
                "billing_mode": inv.billing_mode.value if inv.billing_mode else None,
                "issuer": inv.issuer.value if inv.issuer else None,
                "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                "stripe_invoice_id": inv.stripe_invoice_id,
                "payment_url": None,
            }

            # Si tiene stripe_invoice_id y no está pagada, obtener payment URL
            if inv.stripe_invoice_id and inv.status != InvoiceStatus.paid:
                try:
                    import stripe as _stripe
                    s_inv = _stripe.Invoice.retrieve(inv.stripe_invoice_id)
                    item["payment_url"] = s_inv.get("hosted_invoice_url")
                except Exception:
                    pass

            items.append(item)

        return {
            "items": items,
            "total": len(items),
            "summary": {
                "total_billed": sum(i["total"] or 0 for i in items),
                "total_paid": sum(i["total"] or 0 for i in items if i["status"] == "paid"),
                "total_pending": sum(i["total"] or 0 for i in items if i["status"] in ("issued", "draft")),
            },
        }
    finally:
        db.close()


@router.post("/invoices/{invoice_id}/pay")
async def partner_pay_invoice(
    invoice_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
):
    """
    Genera un link de pago para una factura del partner (partner_collects).
    """
    auth = _require_partner(request, access_token)
    db = SessionLocal()
    try:
        partner = _get_partner(db, auth)

        inv = db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.partner_id == partner.id,
        ).first()

        if not inv:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        if inv.status == InvoiceStatus.paid:
            raise HTTPException(status_code=400, detail="La factura ya está pagada")

        # Push a Stripe y obtener link
        try:
            result = push_invoice_to_stripe(db, inv)
            if result.get("hosted_invoice_url"):
                return {
                    "payment_url": result["hosted_invoice_url"],
                    "method": "stripe_invoice",
                    "invoice_number": inv.invoice_number,
                }
        except Exception as e:
            logger.warning(f"Push to Stripe failed for partner invoice: {e}")

        # Fallback: Checkout Session
        result = create_checkout_for_invoice(
            db, inv,
            success_url=f"https://sajet.us/#/partner/portal?payment_success=true&invoice={inv.invoice_number}",
            cancel_url=f"https://sajet.us/#/partner/portal",
        )
        return {
            "payment_url": result["checkout_url"],
            "method": result.get("method", "checkout_session"),
            "invoice_number": inv.invoice_number,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando pago: {str(e)}")
    finally:
        db.close()
