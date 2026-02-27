"""
Dispersión Mercury — Pagos directos a proveedores vía Mercury Banking

Flujo:
1. Admin crea payout_request (estado: pending_approval)
2. Otro admin autoriza (estado: authorized)        ← REQUERIDO, no auto
3. Sistema ejecuta pago vía Mercury (estado: processing → completed/failed)

Feature flag: MERCURY_DISPERSION_ENABLED=true/false (config + DB)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..routes.roles import _require_admin

router = APIRouter(prefix="/api/dispersion", tags=["Dispersión"])
logger = logging.getLogger(__name__)

# ─── helpers ────────────────────────────────────────────────────────────────

def _feature_enabled(db: Session) -> bool:
    """Lee el feature flag de DB primero, luego del env."""
    try:
        row = db.execute(
            text("SELECT value FROM system_config WHERE key = 'mercury_dispersion_enabled'")
        ).fetchone()
        if row:
            return str(row[0]).lower() in ("true", "1", "yes")
    except Exception:
        pass
    return os.getenv("MERCURY_DISPERSION_ENABLED", "false").lower() in ("true", "1", "yes")


def _require_dispersion_enabled(db: Session = Depends(get_db)):
    if not _feature_enabled(db):
        raise HTTPException(
            status_code=423,
            detail={
                "code": "DISPERSION_DISABLED",
                "message": "La dispersión Mercury está desactivada. Actívala en Configuración → Dispersión.",
            },
        )
    return db


def _get_mercury_client():
    from ..services.mercury_client import get_mercury_client
    return get_mercury_client()


# ─── Pydantic models ─────────────────────────────────────────────────────────

class DispersionStatusResponse(BaseModel):
    enabled: bool
    feature_flag_source: str          # "database" | "env"
    mercury_connected: bool
    checking_balance: Optional[float]
    savings_balance: Optional[float]
    pending_count: int
    authorized_count: int
    processing_count: int
    completed_today: int
    failed_today: int
    daily_limit_usd: float
    used_today_usd: float
    remaining_today_usd: float
    last_updated: str


class CreatePayoutRequest(BaseModel):
    provider_name: str = Field(..., min_length=2, description="Nombre del proveedor")
    provider_account: str = Field(..., description="Número de cuenta destino")
    provider_routing: str = Field(..., description="Número de ruta (ACH) o SWIFT (Wire)")
    amount_usd: float = Field(..., gt=0, le=50000, description="Monto en USD")
    payment_method: str = Field("ach", description="ach | wire")
    concept: str = Field(..., min_length=5, description="Concepto del pago")
    reference: Optional[str] = Field(None, description="Referencia interna (factura, PO, etc.)")
    notes: Optional[str] = Field(None, description="Notas adicionales para el autorizador")


class AuthorizePayoutRequest(BaseModel):
    payout_id: int
    authorization_note: Optional[str] = Field(None, description="Nota de autorización")


class RejectPayoutRequest(BaseModel):
    payout_id: int
    rejection_reason: str = Field(..., min_length=5, description="Motivo del rechazo")


class FeatureFlagRequest(BaseModel):
    enabled: bool
    reason: Optional[str] = Field(None, description="Motivo del cambio")


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/status", summary="Estado del sistema de dispersión")
async def get_dispersion_status(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Retorna el estado completo del sistema de dispersión:
    - Feature flag (activo/inactivo)
    - Balances Mercury (CHECKING + SAVINGS)
    - Conteo de payouts por estado
    - Límites diarios
    
    Visible para cualquier admin aunque el flag esté apagado.
    """
    admin = await _require_admin(request, db)

    # Feature flag
    flag_from_db = False
    flag_source = "env"
    try:
        row = db.execute(
            text("SELECT value FROM system_config WHERE key = 'mercury_dispersion_enabled'")
        ).fetchone()
        if row:
            flag_from_db = str(row[0]).lower() in ("true", "1", "yes")
            flag_source = "database"
        else:
            flag_from_db = os.getenv("MERCURY_DISPERSION_ENABLED", "false").lower() in ("true", "1", "yes")
    except Exception:
        flag_from_db = os.getenv("MERCURY_DISPERSION_ENABLED", "false").lower() in ("true", "1", "yes")

    # Balances Mercury
    checking_balance = None
    savings_balance = None
    mercury_connected = False
    try:
        client = _get_mercury_client()
        accounts = client.get_accounts()
        mercury_connected = True
        checking_id = os.getenv("MERCURY_CHECKING_ACCOUNT_ID", "")
        savings_id = os.getenv("MERCURY_SAVINGS_ACCOUNT_ID", "")
        for acct in (accounts if isinstance(accounts, list) else []):
            aid = str(acct.get("id", ""))
            bal = float(acct.get("availableBalance", acct.get("currentBalance", 0)) or 0)
            if aid == checking_id:
                checking_balance = bal
            elif aid == savings_id:
                savings_balance = bal
    except Exception as e:
        logger.warning(f"No se pudo conectar a Mercury: {e}")

    # Conteo de payouts
    today = datetime.now(timezone.utc).date().isoformat()
    pending_count = authorized_count = processing_count = 0
    completed_today = failed_today = 0
    used_today_usd = 0.0
    try:
        r = db.execute(text(
            "SELECT status, COUNT(*), COALESCE(SUM(amount_usd),0) "
            "FROM payout_requests GROUP BY status"
        )).fetchall()
        for row in r:
            status, count, total = row
            if status == "pending_approval":
                pending_count = count
            elif status == "authorized":
                authorized_count = count
            elif status == "processing":
                processing_count = count

        r2 = db.execute(text(
            "SELECT status, COUNT(*), COALESCE(SUM(amount_usd),0) "
            "FROM payout_requests WHERE DATE(created_at) = :today GROUP BY status"
        ), {"today": today}).fetchall()
        for row in r2:
            status, count, total = row
            if status == "completed":
                completed_today = count
                used_today_usd += float(total)
            elif status == "failed":
                failed_today = count
    except Exception:
        pass  # tabla puede no existir aún

    daily_limit = float(os.getenv("MERCURY_DAILY_LIMIT", "100000"))

    return {
        "enabled": flag_from_db,
        "feature_flag_source": flag_source,
        "mercury_connected": mercury_connected,
        "checking_balance": checking_balance,
        "savings_balance": savings_balance,
        "pending_count": pending_count,
        "authorized_count": authorized_count,
        "processing_count": processing_count,
        "completed_today": completed_today,
        "failed_today": failed_today,
        "daily_limit_usd": daily_limit,
        "used_today_usd": used_today_usd,
        "remaining_today_usd": max(0.0, daily_limit - used_today_usd),
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/feature-flag", summary="Activar/desactivar dispersión Mercury")
async def set_feature_flag(
    body: FeatureFlagRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Activa o desactiva el sistema de dispersión Mercury.
    Solo administradores. El cambio se persiste en system_config.
    """
    admin = await _require_admin(request, db)

    value = "true" if body.enabled else "false"
    try:
        db.execute(text(
            "INSERT INTO system_config (key, value, updated_at, updated_by) "
            "VALUES ('mercury_dispersion_enabled', :val, NOW(), :user) "
            "ON CONFLICT (key) DO UPDATE SET value=:val, updated_at=NOW(), updated_by=:user"
        ), {"val": value, "user": admin.get("email", "admin")})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error guardando config: {e}")

    action = "activada" if body.enabled else "desactivada"
    logger.info(f"Dispersión Mercury {action} por {admin.get('email')}. Motivo: {body.reason}")

    return {
        "success": True,
        "enabled": body.enabled,
        "message": f"Dispersión Mercury {action} exitosamente.",
        "changed_by": admin.get("email"),
        "reason": body.reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/payouts", summary="Listar payout requests")
async def list_payouts(
    request: Request,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Lista todos los payout requests. Filtrable por status.
    Status: pending_approval | authorized | processing | completed | failed | rejected
    """
    await _require_admin(request, db)

    try:
        where = "WHERE pr.status = :status" if status else ""
        params = {"status": status, "limit": limit} if status else {"limit": limit}
        rows = db.execute(text(f"""
            SELECT
                pr.id, pr.provider_name, pr.provider_account, pr.provider_routing,
                pr.amount_usd, pr.payment_method, pr.concept, pr.reference,
                pr.status, pr.notes,
                pr.created_by, pr.created_at,
                pr.authorized_by, pr.authorized_at, pr.authorization_note,
                pr.rejected_by, pr.rejected_at, pr.rejection_reason,
                pr.mercury_payment_id, pr.executed_at, pr.error_message
            FROM payout_requests pr
            {where}
            ORDER BY pr.created_at DESC
            LIMIT :limit
        """), params).fetchall()

        return {
            "payouts": [dict(zip([
                "id", "provider_name", "provider_account", "provider_routing",
                "amount_usd", "payment_method", "concept", "reference",
                "status", "notes",
                "created_by", "created_at",
                "authorized_by", "authorized_at", "authorization_note",
                "rejected_by", "rejected_at", "rejection_reason",
                "mercury_payment_id", "executed_at", "error_message"
            ], r)) for r in rows],
            "total": len(rows),
        }
    except Exception as e:
        logger.warning(f"Error listando payouts: {e}")
        return {"payouts": [], "total": 0, "warning": "Tabla payout_requests no disponible aún"}


@router.post("/payouts/create", summary="Crear solicitud de pago (requiere autorización)")
async def create_payout_request(
    body: CreatePayoutRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Crea una solicitud de pago. Estado inicial: pending_approval.
    
    ⚠️ NO ejecuta el pago. Requiere que otro admin lo autorice primero.
    El feature flag debe estar activo para crear solicitudes.
    """
    admin = await _require_admin(request, db)

    if not _feature_enabled(db):
        raise HTTPException(
            status_code=423,
            detail={
                "code": "DISPERSION_DISABLED",
                "message": "Activa la dispersión en Configuración antes de crear pagos.",
            },
        )

    # Validar límite diario
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        used_row = db.execute(text(
            "SELECT COALESCE(SUM(amount_usd),0) FROM payout_requests "
            "WHERE DATE(created_at) = :today AND status IN ('authorized','processing','completed')"
        ), {"today": today}).fetchone()
        used_today = float(used_row[0]) if used_row else 0.0
        daily_limit = float(os.getenv("MERCURY_DAILY_LIMIT", "100000"))
        if used_today + body.amount_usd > daily_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Límite diario excedido. Usado: ${used_today:,.2f} / ${daily_limit:,.2f}",
            )
    except HTTPException:
        raise
    except Exception:
        pass

    try:
        result = db.execute(text("""
            INSERT INTO payout_requests (
                provider_name, provider_account, provider_routing,
                amount_usd, payment_method, concept, reference, notes,
                status, created_by, created_at
            ) VALUES (
                :provider_name, :provider_account, :provider_routing,
                :amount_usd, :payment_method, :concept, :reference, :notes,
                'pending_approval', :created_by, NOW()
            ) RETURNING id
        """), {
            "provider_name": body.provider_name,
            "provider_account": body.provider_account,
            "provider_routing": body.provider_routing,
            "amount_usd": body.amount_usd,
            "payment_method": body.payment_method,
            "concept": body.concept,
            "reference": body.reference,
            "notes": body.notes,
            "created_by": admin.get("email", "admin"),
        })
        payout_id = result.fetchone()[0]
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando solicitud: {e}")

    logger.info(
        f"Payout request #{payout_id} creado por {admin.get('email')} "
        f"— ${body.amount_usd} → {body.provider_name} ({body.payment_method})"
    )

    return {
        "success": True,
        "payout_id": payout_id,
        "status": "pending_approval",
        "message": f"Solicitud #{payout_id} creada. Pendiente de autorización por otro administrador.",
        "amount_usd": body.amount_usd,
        "provider_name": body.provider_name,
        "requires_authorization": True,
    }


@router.post("/payouts/authorize", summary="Autorizar pago (admin distinto al creador)")
async def authorize_payout(
    body: AuthorizePayoutRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Autoriza un payout_request pendiente y ejecuta el pago via Mercury.
    
    Reglas:
    - El autorizador debe ser un admin diferente al creador (4-eyes principle)
    - El feature flag debe estar activo
    - El pago se ejecuta inmediatamente tras la autorización
    """
    admin = await _require_admin(request, db)
    authorizer_email = admin.get("email", "admin")

    if not _feature_enabled(db):
        raise HTTPException(status_code=423, detail={"code": "DISPERSION_DISABLED", "message": "Dispersión desactivada."})

    # Cargar el payout
    try:
        row = db.execute(text(
            "SELECT id, provider_name, provider_account, provider_routing, "
            "amount_usd, payment_method, concept, reference, status, created_by "
            "FROM payout_requests WHERE id = :id"
        ), {"id": body.payout_id}).fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando payout: {e}")

    if not row:
        raise HTTPException(status_code=404, detail=f"Payout #{body.payout_id} no encontrado")

    (pid, provider_name, provider_account, provider_routing,
     amount_usd, payment_method, concept, reference, status, created_by) = row

    if status != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Payout #{pid} no está pendiente de autorización (estado: {status})"
        )

    # 4-eyes: el autorizador no puede ser el mismo que creó
    if authorizer_email == created_by:
        raise HTTPException(
            status_code=403,
            detail="El autorizador no puede ser la misma persona que creó la solicitud (principio 4-ojos).",
        )

    # Marcar como authorized
    try:
        db.execute(text(
            "UPDATE payout_requests SET status='authorized', "
            "authorized_by=:auth, authorized_at=NOW(), authorization_note=:note "
            "WHERE id=:id"
        ), {"auth": authorizer_email, "note": body.authorization_note, "id": pid})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error autorizando: {e}")

    logger.info(f"Payout #{pid} autorizado por {authorizer_email} — ${amount_usd} → {provider_name}")

    # Ejecutar pago via Mercury
    mercury_payment_id = None
    execution_error = None
    final_status = "processing"

    try:
        client = _get_mercury_client()
        checking_id = os.getenv("MERCURY_CHECKING_ACCOUNT_ID")

        if payment_method == "ach":
            result = client.create_payment(
                account_id=checking_id,
                recipient_name=provider_name,
                routing_number=provider_routing,
                account_number=provider_account,
                amount_cents=int(float(amount_usd) * 100),
                memo=f"{concept} | Ref: {reference or pid}",
                payment_type="ach",
            )
        else:
            result = client.create_payment(
                account_id=checking_id,
                recipient_name=provider_name,
                routing_number=provider_routing,
                account_number=provider_account,
                amount_cents=int(float(amount_usd) * 100),
                memo=f"{concept} | Ref: {reference or pid}",
                payment_type="domestic_wire",
            )

        mercury_payment_id = result.get("id") or result.get("paymentId")
        final_status = "processing"
        logger.info(f"✅ Pago Mercury iniciado: {mercury_payment_id}")

    except Exception as e:
        execution_error = str(e)
        final_status = "failed"
        logger.error(f"❌ Error ejecutando pago Mercury para #{pid}: {e}")

    # Actualizar estado final
    try:
        if final_status == "processing":
            db.execute(text(
                "UPDATE payout_requests SET status='processing', "
                "mercury_payment_id=:mpid, executed_at=NOW() WHERE id=:id"
            ), {"mpid": mercury_payment_id, "id": pid})
        else:
            db.execute(text(
                "UPDATE payout_requests SET status='failed', "
                "error_message=:err, executed_at=NOW() WHERE id=:id"
            ), {"err": execution_error, "id": pid})
        db.commit()
    except Exception:
        db.rollback()

    if final_status == "failed":
        raise HTTPException(
            status_code=502,
            detail={
                "code": "MERCURY_PAYMENT_FAILED",
                "message": f"Payout autorizado pero falló la ejecución en Mercury: {execution_error}",
                "payout_id": pid,
                "status": "failed",
            }
        )

    return {
        "success": True,
        "payout_id": pid,
        "status": "processing",
        "mercury_payment_id": mercury_payment_id,
        "message": f"Pago #{pid} autorizado y enviado a Mercury. Estado: processing.",
        "authorized_by": authorizer_email,
        "amount_usd": amount_usd,
        "provider_name": provider_name,
    }


@router.post("/payouts/reject", summary="Rechazar solicitud de pago")
async def reject_payout(
    body: RejectPayoutRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Rechaza un payout pending_approval."""
    admin = await _require_admin(request, db)

    try:
        row = db.execute(
            text("SELECT status FROM payout_requests WHERE id=:id"), {"id": body.payout_id}
        ).fetchone()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not row:
        raise HTTPException(status_code=404, detail=f"Payout #{body.payout_id} no encontrado")
    if row[0] != "pending_approval":
        raise HTTPException(status_code=400, detail=f"Solo se pueden rechazar payouts pendientes (estado actual: {row[0]})")

    try:
        db.execute(text(
            "UPDATE payout_requests SET status='rejected', "
            "rejected_by=:by, rejected_at=NOW(), rejection_reason=:reason WHERE id=:id"
        ), {"by": admin.get("email"), "reason": body.rejection_reason, "id": body.payout_id})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "payout_id": body.payout_id,
        "status": "rejected",
        "rejected_by": admin.get("email"),
        "reason": body.rejection_reason,
    }
