"""
Public Funnel Leads — Captura orgánica desde landing pages de nichos.
No requiere autenticación. Guarda en BDA + intenta sync con Jeturing CRM.
"""
import logging
import httpx
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr, field_validator

from ..models.database import FunnelLead, FunnelNiche, SessionLocal
from ..utils.ip import get_real_ip

import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/public/funnel", tags=["Funnel Leads"])

JETURING_CRM_URL = "https://jeturing.com/api/v1/crm/leads"
JETURING_API_KEY = os.getenv("JETURING_API_KEY")


# ── DTOs ──────────────────────────────────────────────────────────────────────

class FunnelLeadIn(BaseModel):
    niche:          str               # mpos | build | partners | cpa | smb | general
    full_name:      str
    email:          EmailStr
    phone:          Optional[str]     = None
    company_name:   Optional[str]     = None
    country:        Optional[str]     = None
    language:       Optional[str]     = "es"

    # Calificación
    has_entity:     Optional[bool]    = None
    monthly_volume: Optional[str]     = None
    budget_range:   Optional[str]     = None
    timeline:       Optional[str]     = None
    client_count:   Optional[int]     = None
    has_sales_team: Optional[bool]    = None
    industry:       Optional[str]     = None
    main_goal:      Optional[str]     = None

    # Tracking (enviados por el frontend)
    utm_source:     Optional[str]     = None
    utm_medium:     Optional[str]     = None
    utm_campaign:   Optional[str]     = None
    referrer:       Optional[str]     = None

    @field_validator("niche")
    @classmethod
    def validate_niche(cls, v: str) -> str:
        valid = {n.value for n in FunnelNiche}
        return v if v in valid else "general"


class FunnelLeadOut(BaseModel):
    id:        int
    qualified: bool
    redirect:  str   # URL a donde llevar al usuario


# ── Helpers ───────────────────────────────────────────────────────────────────



def _qualify(lead: FunnelLeadIn) -> tuple[bool, Optional[str]]:
    """
    Aplica reglas de calificación por nicho.
    Retorna (qualified, disqualify_reason).
    """
    if lead.has_entity is False:
        return False, "no_entity"

    niche = lead.niche

    if niche == "mpos":
        # Necesita empresa formada (ya chequeado arriba)
        return True, None

    if niche == "build":
        if lead.budget_range and lead.budget_range in ("under_1k", "1k_5k"):
            return False, "budget_too_low"
        if lead.timeline and lead.timeline == "under_4w":
            return False, "timeline_too_short"
        return True, None

    if niche == "partners":
        if lead.client_count is not None and lead.client_count < 2:
            return False, "not_enough_clients"
        if lead.has_sales_team is False:
            return False, "no_sales_team"
        return True, None

    if niche == "cpa":
        if lead.client_count is not None and lead.client_count < 2:
            return False, "not_enough_clients"
        if lead.has_entity is False:
            return False, "no_entity"
        return True, None

    return True, None


def _redirect_for(qualified: bool, reason: Optional[str], niche: str) -> str:
    if not qualified:
        if reason == "no_entity":
            return "https://jeturing.com/atlas"
        return "/smb"
    return f"/team-onboarding?niche={niche}"


async def _sync_jeturing(lead_id: int, data: FunnelLeadIn, qualified: bool):
    """Intenta registrar el lead en Jeturing CRM (best-effort, no bloquea)."""
    import os
    api_key = os.getenv("JETURING_API_KEY")
    if not api_key:
        return

    payload = {
        "name":         data.full_name,
        "email":        data.email,
        "phone":        data.phone,
        "company":      data.company_name,
        "country":      data.country,
        "source":       f"sajet_funnel_{data.niche}",
        "utm_source":   data.utm_source,
        "utm_medium":   data.utm_medium,
        "utm_campaign": data.utm_campaign,
        "qualified":    qualified,
        "metadata": {
            "niche":          data.niche,
            "has_entity":     data.has_entity,
            "monthly_volume": data.monthly_volume,
            "budget_range":   data.budget_range,
            "timeline":       data.timeline,
            "client_count":   data.client_count,
            "main_goal":      data.main_goal,
            "sajet_lead_id":  lead_id,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(
                JETURING_CRM_URL,
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if resp.status_code == 200:
                crm_id = resp.json().get("id")
                # Actualizar crm_id en BDA
                db = SessionLocal()
                try:
                    row = db.query(FunnelLead).filter(FunnelLead.id == lead_id).first()
                    if row:
                        row.jeturing_crm_id = str(crm_id)
                        db.commit()
                finally:
                    db.close()
    except Exception as exc:
        logger.warning("Jeturing CRM sync failed for lead %s: %s", lead_id, exc)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/lead", response_model=FunnelLeadOut)
async def capture_funnel_lead(
    data: FunnelLeadIn,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Captura un lead orgánico desde las landing pages de nichos.
    Público — sin autenticación.
    Califica el lead y retorna la URL de redirección correcta.
    """
    qualified, reason = _qualify(data)
    redirect  = _redirect_for(qualified, reason, data.niche)
    ip        = _get_real_ip(request)

    db = SessionLocal()
    try:
        niche_enum = FunnelNiche(data.niche) if data.niche in {n.value for n in FunnelNiche} else FunnelNiche.general

        row = FunnelLead(
            niche             = niche_enum,
            full_name         = data.full_name,
            email             = data.email,
            phone             = data.phone,
            company_name      = data.company_name,
            country           = data.country,
            language          = data.language,
            has_entity        = data.has_entity,
            monthly_volume    = data.monthly_volume,
            budget_range      = data.budget_range,
            timeline          = data.timeline,
            client_count      = data.client_count,
            has_sales_team    = data.has_sales_team,
            industry          = data.industry,
            main_goal         = data.main_goal,
            utm_source        = data.utm_source,
            utm_medium        = data.utm_medium,
            utm_campaign      = data.utm_campaign,
            referrer          = data.referrer or request.headers.get("referer"),
            ip_address        = ip,
            user_agent        = request.headers.get("user-agent", "")[:500],
            qualified         = qualified,
            disqualify_reason = reason,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        lead_id = row.id
    finally:
        db.close()

    # Sync a Jeturing CRM en background (no bloquea la respuesta)
    background_tasks.add_task(_sync_jeturing, lead_id, data, qualified)

    return FunnelLeadOut(id=lead_id, qualified=qualified, redirect=redirect)


@router.get("/stats")
async def funnel_stats():
    """Stats públicas básicas (sin datos PII) para social proof."""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        total = db.query(func.count(FunnelLead.id)).scalar() or 0
        by_niche = (
            db.query(FunnelLead.niche, func.count(FunnelLead.id))
            .group_by(FunnelLead.niche)
            .all()
        )
        return {
            "total_leads": total,
            "by_niche": {row[0].value: row[1] for row in by_niche},
        }
    finally:
        db.close()
