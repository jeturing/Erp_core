"""
Reconciliation Routes — Épica 7: Stripe ↔ DB Reconciliation
- POST /api/reconciliation/run     → Ejecutar run de reconciliación
- GET  /api/reconciliation/runs    → Historial de runs
- GET  /api/reconciliation/runs/{id} → Detalle de un run
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import os
import logging

from ..models.database import ReconciliationRun, get_db
from ..services.stripe_reconciliation import StripeReconciliationService

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])
logger = logging.getLogger(__name__)


class RunReconciliationRequest(BaseModel):
    scope: str = "all"   # all | direct | partner | legacy
    dry_run: bool = False


@router.post("/run")
def run_reconciliation(
    payload: RunReconciliationRequest,
    db: Session = Depends(get_db),
):
    """
    Ejecuta reconciliación Stripe vs DB.
    - scope=legacy → Solo lee, no corrige (DB READONLY para legacy)
    - dry_run=True → Reporta sin modificar
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        raise HTTPException(500, "STRIPE_SECRET_KEY not configured")

    # Legacy siempre es dry_run (readonly)
    if payload.scope == "legacy":
        payload.dry_run = True

    svc = StripeReconciliationService(db, stripe_key)
    result = svc.run_reconciliation(scope=payload.scope, dry_run=payload.dry_run)

    return result


@router.get("/runs")
def list_reconciliation_runs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    total = db.query(ReconciliationRun).count()
    runs = db.query(ReconciliationRun).order_by(
        ReconciliationRun.run_date.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "runs": [
            {
                "id": r.id,
                "run_date": r.run_date.isoformat() if r.run_date else None,
                "scope": r.scope,
                "status": r.status,
                "total_checked": r.total_checked,
                "mismatches_found": r.mismatches_found,
                "auto_fixed": r.auto_fixed,
            }
            for r in runs
        ],
    }


@router.get("/runs/{run_id}")
def get_reconciliation_detail(run_id: int, db: Session = Depends(get_db)):
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise HTTPException(404, "Reconciliation run not found")
    return {
        "id": run.id,
        "run_date": run.run_date.isoformat() if run.run_date else None,
        "scope": run.scope,
        "status": run.status,
        "total_checked": run.total_checked,
        "mismatches_found": run.mismatches_found,
        "auto_fixed": run.auto_fixed,
        "details": run.details_json,
    }
