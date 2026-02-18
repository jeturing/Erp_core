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
        ReconciliationRun.created_at.desc()
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "runs": [
            {
                "id": r.id,
                "run_date": r.created_at.isoformat() if r.created_at else None,
                "period_start": r.period_start.isoformat() if r.period_start else None,
                "period_end": r.period_end.isoformat() if r.period_end else None,
                "status": r.status,
                "stripe_total": r.stripe_total,
                "local_total": r.local_total,
                "discrepancy": r.discrepancy,
                "run_by": r.run_by,
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
        "run_date": run.created_at.isoformat() if run.created_at else None,
        "period_start": run.period_start.isoformat() if run.period_start else None,
        "period_end": run.period_end.isoformat() if run.period_end else None,
        "status": run.status,
        "stripe_total": run.stripe_total,
        "local_total": run.local_total,
        "discrepancy": run.discrepancy,
        "run_by": run.run_by,
        "details": run.discrepancy_details,
    }
