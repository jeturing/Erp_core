"""
Stripe Connect Routes — Onboarding y gestión de cuentas Connect para partners.
"""
from fastapi import APIRouter, HTTPException, Request, Cookie
from pydantic import BaseModel
from typing import Optional
from ..models.database import Partner, Customer, SessionLocal
from ..services.stripe_connect import (
    create_connect_account,
    create_onboarding_link,
    create_login_link,
    get_account_status,
    create_transfer,
    get_partner_balance,
)
from .roles import _require_admin, _extract_token, verify_token_with_role
import logging

router = APIRouter(prefix="/api/stripe-connect", tags=["Stripe Connect"])
logger = logging.getLogger(__name__)


class ConnectAccountRequest(BaseModel):
    partner_id: int
    country: Optional[str] = "US"


class TransferRequest(BaseModel):
    partner_id: int
    amount: float  # USD (ej: 500.00)
    description: Optional[str] = ""
    commission_id: Optional[int] = None


# ── Endpoints Admin ──

@router.post("/create-account")
async def create_partner_connect_account(
    payload: ConnectAccountRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """Crea cuenta Stripe Connect Express para un partner"""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")

        if partner.stripe_account_id:
            raise HTTPException(
                status_code=409,
                detail=f"Partner ya tiene cuenta Connect: {partner.stripe_account_id}",
            )

        result = await create_connect_account(
            partner_email=partner.contact_email,
            partner_company=partner.company_name,
            partner_country=payload.country or "US",
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Guardar account_id en el partner
        partner.stripe_account_id = result["account_id"]
        db.commit()

        # Generar link de onboarding
        link_result = await create_onboarding_link(result["account_id"])

        return {
            "success": True,
            "account_id": result["account_id"],
            "onboarding_url": link_result.get("url") if link_result["success"] else None,
            "message": f"Cuenta Connect creada para {partner.company_name}",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creando Connect account: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{partner_id}/onboarding-link")
async def get_onboarding_link(
    partner_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Genera o regenera link de onboarding de Stripe"""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")
        if not partner.stripe_account_id:
            raise HTTPException(status_code=400, detail="Partner no tiene cuenta Connect")

        result = await create_onboarding_link(partner.stripe_account_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    finally:
        db.close()


@router.get("/{partner_id}/dashboard-link")
async def get_partner_dashboard_link(
    partner_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Genera link para que el partner acceda a su Stripe Express Dashboard"""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")
        if not partner.stripe_account_id:
            raise HTTPException(status_code=400, detail="Partner no tiene cuenta Connect")

        result = await create_login_link(partner.stripe_account_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        return result
    finally:
        db.close()


@router.get("/{partner_id}/status")
async def get_partner_connect_status(
    partner_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtiene estado de la cuenta Connect de un partner"""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner no encontrado")
        if not partner.stripe_account_id:
            return {
                "success": True,
                "has_account": False,
                "partner_id": partner_id,
            }

        result = await get_account_status(partner.stripe_account_id)

        # Actualizar flags en BD si cambiaron
        if result["success"]:
            changed = False
            if partner.stripe_charges_enabled != result.get("charges_enabled", False):
                partner.stripe_charges_enabled = bool(result["charges_enabled"])
                changed = True
            if partner.stripe_onboarding_complete != result.get("onboarding_ready", False):
                partner.stripe_onboarding_complete = bool(result["onboarding_ready"])
                changed = True
            if changed:
                db.commit()

        result["has_account"] = True
        result["partner_id"] = partner_id
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error consultando status Connect: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/{partner_id}/balance")
async def get_partner_connect_balance(
    partner_id: int,
    request: Request,
    access_token: str = Cookie(None),
):
    """Obtiene balance actual del partner en Stripe"""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner or not partner.stripe_account_id:
            raise HTTPException(status_code=404, detail="Partner sin cuenta Connect")

        return await get_partner_balance(partner.stripe_account_id)
    finally:
        db.close()


@router.post("/transfer")
async def execute_transfer(
    payload: TransferRequest,
    request: Request,
    access_token: str = Cookie(None),
):
    """Ejecuta una transferencia manual al partner"""
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        partner = db.query(Partner).filter(Partner.id == payload.partner_id).first()
        if not partner or not partner.stripe_account_id:
            raise HTTPException(status_code=404, detail="Partner sin cuenta Connect")

        if not partner.stripe_charges_enabled:
            raise HTTPException(
                status_code=400,
                detail="La cuenta del partner no está habilitada para recibir pagos. Complete el onboarding primero.",
            )

        amount_cents = int(payload.amount * 100)
        if amount_cents <= 0:
            raise HTTPException(status_code=400, detail="Monto debe ser mayor a 0")

        result = await create_transfer(
            destination_account_id=partner.stripe_account_id,
            amount_cents=amount_cents,
            description=payload.description or f"Comisión partner #{partner.id}",
            metadata={
                "partner_id": str(partner.id),
                "commission_id": str(payload.commission_id) if payload.commission_id else "",
            },
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])

        # Si hay commission_id, actualizar estado
        if payload.commission_id:
            from ..models.database import Commission, CommissionStatus
            from datetime import datetime

            commission = db.query(Commission).filter(Commission.id == payload.commission_id).first()
            if commission:
                commission.status = CommissionStatus.paid
                commission.paid_at = datetime.utcnow()
                commission.payment_reference = result["transfer_id"]
                db.commit()

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error en transfer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
