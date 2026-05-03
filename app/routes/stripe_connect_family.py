"""
Stripe Connect Family — Tenant Sync (Phase 6).

Endpoints para que cada tenant Odoo **PUSH-eé** su configuración Stripe
Connect a SAJET. SAJET no consulta a los tenants (anti-SPOF): los tenants
son los responsables de mantener su espejo actualizado.

Uso desde un tenant Odoo:

    POST /api/v1/stripe-connect/sync
    Headers: X-API-Key: <tenant_api_key>
    Body: {
        "source": "boletly_tickets",
        "stripe_mode": "live",
        "stripe_account_count": 12,
        "stripe_account_type": "express",
        "connect_country": "DO",
        "terminal_routing": "connect",
        "terminal_max_devices": 0,
        "feature_flags": {"enable_apple_pay": true, "reconcile_cron_minutes": 15},
        "fee_rules_count": 3,
        "last_transaction_at": "2026-04-24T17:30:00Z",
        "transactions_30d": 1450,
        "transfers_30d_cents": 12500000,
        "refunds_30d_cents": 35000
    }

El endpoint hace upsert por (tenant_id, source).
"""
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models.database import (
    TenantStripeConfig, TenantDeployment, get_db,
)
from .api_keys import verify_api_key


router = APIRouter(prefix="/api/v1/stripe-connect", tags=["Stripe Connect Family"])
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────────────────
class StripeSyncPayload(BaseModel):
    source: str = Field(..., description="Conector: boletly_tickets, jeturing_pay_shop, jeturing_event_stripe")
    stripe_mode: Optional[str] = Field(None, description="test | live")
    stripe_account_count: int = 0
    stripe_account_type: Optional[str] = None
    connect_country: Optional[str] = None
    terminal_routing: Optional[str] = "connect"
    terminal_max_devices: int = 0
    feature_flags: Optional[Dict[str, Any]] = None
    fee_rules_count: int = 0
    last_transaction_at: Optional[datetime] = None
    transactions_30d: int = 0
    transfers_30d_cents: int = 0
    refunds_30d_cents: int = 0
    raw_payload: Optional[Dict[str, Any]] = None


class StripeSyncResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


# ──────────────────────────────────────────────────────────────────────────
# Auth helper
# ──────────────────────────────────────────────────────────────────────────
def _resolve_tenant_from_api_key(
    request: Request,
    db: Session,
    x_api_key: Optional[str] = None,
) -> TenantDeployment:
    """Valida API key y devuelve el tenant_deployment asociado."""
    raw_key = x_api_key or request.headers.get("X-API-Key", "")
    if not raw_key:
        raise HTTPException(status_code=401, detail="X-API-Key requerido")

    api_key = verify_api_key(
        raw_key=raw_key,
        db=db,
        endpoint=str(request.url.path),
        ip_address=(request.client.host if request.client else None),
    )
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key inválida o expirada")
    if not api_key.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Esta API Key no está vinculada a ningún tenant",
        )
    tenant = db.query(TenantDeployment).filter(
        TenantDeployment.id == api_key.tenant_id
    ).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return tenant


# ──────────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────────
@router.post("/sync", response_model=StripeSyncResponse)
async def sync_tenant_stripe_config(
    payload: StripeSyncPayload,
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Upsert de la configuración Stripe Connect del tenant en SAJET."""
    tenant = _resolve_tenant_from_api_key(request, db, x_api_key)

    # Validar source contra whitelist
    valid_sources = {
        "boletly_tickets", "jeturing_pay_shop", "jeturing_event_stripe",
    }
    if payload.source not in valid_sources:
        raise HTTPException(
            status_code=422,
            detail=f"source inválida. Valores permitidos: {sorted(valid_sources)}",
        )

    config = (
        db.query(TenantStripeConfig)
        .filter(
            TenantStripeConfig.tenant_id == tenant.id,
            TenantStripeConfig.source == payload.source,
        )
        .first()
    )
    if not config:
        config = TenantStripeConfig(
            tenant_id=tenant.id,
            source=payload.source,
        )
        db.add(config)

    # Actualizar todos los campos
    for field in (
        "stripe_mode", "stripe_account_count", "stripe_account_type",
        "connect_country", "terminal_routing", "terminal_max_devices",
        "feature_flags", "fee_rules_count", "last_transaction_at",
        "transactions_30d", "transfers_30d_cents", "refunds_30d_cents",
        "raw_payload",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(config, field, value)
    config.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()
    db.refresh(config)

    logger.info(
        "TenantStripeConfig sync: tenant=%s (%s) source=%s tx_30d=%s",
        tenant.id, tenant.subdomain or tenant.tenant_name,
        payload.source, payload.transactions_30d,
    )
    return StripeSyncResponse(
        success=True,
        data={
            "config_id": config.id,
            "tenant_id": tenant.id,
            "tenant_subdomain": tenant.subdomain,
            "source": config.source,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None,
        },
    )


@router.get("/configs")
async def list_tenant_configs(
    request: Request,
    db: Session = Depends(get_db),
    source: Optional[str] = None,
    tenant_id: Optional[int] = None,
):
    """Admin: lista configuraciones agregadas (panel central)."""
    # Reutilizamos el verificador de admin del módulo stripe_sync
    from .stripe_sync import _verify_admin
    _verify_admin(request, token=request.cookies.get("access_token"))

    q = db.query(TenantStripeConfig)
    if source:
        q = q.filter(TenantStripeConfig.source == source)
    if tenant_id:
        q = q.filter(TenantStripeConfig.tenant_id == tenant_id)
    configs = q.order_by(TenantStripeConfig.updated_at.desc().nullslast()).all()

    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "tenant_id": c.tenant_id,
                "source": c.source,
                "stripe_mode": c.stripe_mode,
                "stripe_account_count": c.stripe_account_count,
                "stripe_account_type": c.stripe_account_type,
                "connect_country": c.connect_country,
                "terminal_routing": c.terminal_routing,
                "terminal_max_devices": c.terminal_max_devices,
                "feature_flags": c.feature_flags,
                "fee_rules_count": c.fee_rules_count,
                "last_transaction_at": c.last_transaction_at.isoformat() if c.last_transaction_at else None,
                "transactions_30d": c.transactions_30d,
                "transfers_30d_cents": c.transfers_30d_cents,
                "refunds_30d_cents": c.refunds_30d_cents,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in configs
        ],
        "meta": {"total": len(configs)},
    }


@router.get("/configs/{tenant_id}/{source}")
async def get_tenant_config(
    tenant_id: int,
    source: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Admin: detalle de una config (incluye raw_payload completo)."""
    from .stripe_sync import _verify_admin
    _verify_admin(request, token=request.cookies.get("access_token"))

    cfg = (
        db.query(TenantStripeConfig)
        .filter(
            TenantStripeConfig.tenant_id == tenant_id,
            TenantStripeConfig.source == source,
        )
        .first()
    )
    if not cfg:
        raise HTTPException(status_code=404, detail="Config no encontrada")
    return {
        "success": True,
        "data": {
            "id": cfg.id,
            "tenant_id": cfg.tenant_id,
            "source": cfg.source,
            "stripe_mode": cfg.stripe_mode,
            "stripe_account_count": cfg.stripe_account_count,
            "stripe_account_type": cfg.stripe_account_type,
            "connect_country": cfg.connect_country,
            "terminal_routing": cfg.terminal_routing,
            "terminal_max_devices": cfg.terminal_max_devices,
            "feature_flags": cfg.feature_flags,
            "fee_rules_count": cfg.fee_rules_count,
            "last_transaction_at": cfg.last_transaction_at.isoformat() if cfg.last_transaction_at else None,
            "transactions_30d": cfg.transactions_30d,
            "transfers_30d_cents": cfg.transfers_30d_cents,
            "refunds_30d_cents": cfg.refunds_30d_cents,
            "raw_payload": cfg.raw_payload,
            "created_at": cfg.created_at.isoformat() if cfg.created_at else None,
            "updated_at": cfg.updated_at.isoformat() if cfg.updated_at else None,
        },
    }
