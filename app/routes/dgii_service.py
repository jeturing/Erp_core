"""DGII Data Service: validación RNC y prevalidación anti-rechazo."""
from datetime import datetime, timedelta
import logging
import re
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models.database import Partner, get_db
from ..models.dgii_cache_models import DgiiRncCache, DgiiValidationLog, DgiiDataServiceConfig, RncStatus

router = APIRouter(prefix="/api/dgii", tags=["DGII"])
logger = logging.getLogger(__name__)


class RncValidationResponse(BaseModel):
    rnc: str
    valid: bool
    status: str
    business_name: str | None
    last_updated: datetime
    cache_ttl_expires: datetime | None
    confidence_score: float


class DgiiValidationRequest(BaseModel):
    document_type: str = Field(..., description="606 | 607 | 608")
    company_id: int
    ncf: str | None = None
    amount: float | None = None
    supplier_rnc: str | None = None
    invoice_date: str | None = None
    user_id: int | None = None


class ValidationIssue(BaseModel):
    issue_code: str
    severity: str
    description: str
    suggestion: str | None = None


class DgiiValidationResponse(BaseModel):
    valid: bool
    issues: list[ValidationIssue]
    can_proceed: bool
    timestamp: datetime


class EnrichPartnerRequest(BaseModel):
    rnc: str = Field(..., min_length=9, max_length=11)
    company_name: str | None = None
    contact_email: str | None = None


def _clean_rnc(value: str) -> str:
    return re.sub(r"\D", "", (value or "").strip())


def _valid_ncf(value: str) -> bool:
    if not value:
        return False
    ncf = value.strip().upper()
    return bool(re.match(r"^(E\d{11}|[ABP]\d{10})$", ncf))


def _get_or_create_config(db: Session, company_id: int) -> DgiiDataServiceConfig:
    config = db.query(DgiiDataServiceConfig).filter(DgiiDataServiceConfig.company_id == company_id).first()
    if config:
        return config
    config = DgiiDataServiceConfig(company_id=company_id)
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _resolve_rnc(db: Session, rnc: str, ttl_days: int = 30) -> DgiiRncCache:
    clean = _clean_rnc(rnc)
    if len(clean) < 9:
        raise HTTPException(status_code=400, detail="RNC inválido (mínimo 9 dígitos)")

    now = datetime.utcnow()
    cache = db.query(DgiiRncCache).filter(DgiiRncCache.rnc_number == clean).first()
    cache_obj = cast(Any, cache)
    if cache_obj is not None and cache_obj.ttl_expires and cache_obj.ttl_expires > now:
        return cache

    # Placeholder hasta integrar padrón oficial DGII
    inferred_status = RncStatus.ACTIVE if len(clean) in (9, 11) else RncStatus.NOT_FOUND
    business_name = cache_obj.business_name if cache_obj is not None and cache_obj.business_name else f"RNC {clean}"

    if cache_obj is not None:
        cache_obj.status = inferred_status
        cache_obj.business_name = business_name
        cache_obj.last_updated = now
        cache_obj.ttl_expires = now + timedelta(days=ttl_days)
        cache_obj.update_count = (cache_obj.update_count or 0) + 1
    else:
        cache = DgiiRncCache(
            rnc_number=clean,
            status=inferred_status,
            business_name=business_name,
            last_updated=now,
            ttl_expires=now + timedelta(days=ttl_days),
            update_count=1,
        )
        db.add(cache)

    db.commit()
    db.refresh(cache)
    return cache


@router.get("/health")
async def health_check() -> dict:
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "service": "DGII Data Service",
            "version": "1.0.1",
            "timestamp": datetime.utcnow().isoformat(),
        },
        "meta": {},
    }


@router.get("/rnc/{numero}", response_model=RncValidationResponse)
async def validate_rnc(numero: str, db: Session = Depends(get_db)):
    cache = _resolve_rnc(db, numero)
    status_value = cache.status.value if hasattr(cache.status, "value") else str(cache.status)
    return RncValidationResponse(
        rnc=cast(Any, cache).rnc_number,
        valid=status_value == RncStatus.ACTIVE.value,
        status=status_value,
        business_name=cast(Any, cache).business_name,
        last_updated=cast(Any, cache).last_updated,
        cache_ttl_expires=cast(Any, cache).ttl_expires,
        confidence_score=1.0,
    )


@router.post("/validate", response_model=DgiiValidationResponse)
async def validate_dgii_document(request: DgiiValidationRequest, db: Session = Depends(get_db)):
    issues: list[ValidationIssue] = []
    doc_type = (request.document_type or "").strip()
    if doc_type not in {"606", "607", "608"}:
        issues.append(
            ValidationIssue(
                issue_code="DOC_TYPE_INVALID",
                severity="error",
                description="Tipo de documento inválido. Use 606, 607 o 608.",
                suggestion="Corregir document_type",
            )
        )

    if request.ncf and not _valid_ncf(request.ncf):
        issues.append(
            ValidationIssue(
                issue_code="NCF_FORMAT_INVALID",
                severity="error",
                description=f"NCF {request.ncf} no cumple formato fiscal.",
                suggestion="Revisar secuencia NCF",
            )
        )

    if request.amount is not None and request.amount <= 0:
        issues.append(
            ValidationIssue(
                issue_code="AMOUNT_ZERO",
                severity="error",
                description="Monto debe ser mayor a 0.",
                suggestion="Corregir monto del documento",
            )
        )

    if request.invoice_date:
        try:
            inv_date = datetime.fromisoformat(request.invoice_date)
            if inv_date > datetime.utcnow():
                issues.append(
                    ValidationIssue(
                        issue_code="DATE_FUTURE",
                        severity="error",
                        description="La fecha no puede ser futura.",
                        suggestion="Usar fecha válida",
                    )
                )
        except ValueError:
            issues.append(
                ValidationIssue(
                    issue_code="DATE_FORMAT_INVALID",
                    severity="error",
                    description="Formato de fecha inválido.",
                    suggestion="Usar formato ISO YYYY-MM-DD",
                )
            )

    if doc_type == "606" and request.supplier_rnc:
        config = _get_or_create_config(db, request.company_id)
        ttl_days = int(cast(Any, config).cache_ttl_days or 30)
        cache = _resolve_rnc(db, request.supplier_rnc, ttl_days=ttl_days)
        status_value = cache.status.value if hasattr(cache.status, "value") else str(cache.status)
        if status_value != RncStatus.ACTIVE.value:
            issues.append(
                ValidationIssue(
                    issue_code="RNC_INACTIVE",
                    severity="error",
                    description=f"RNC {cache.rnc_number} no está activo.",
                    suggestion="Verificar RNC del proveedor",
                )
            )

    has_errors = any(i.severity == "error" for i in issues)
    result = DgiiValidationResponse(
        valid=not issues,
        issues=issues,
        can_proceed=not has_errors,
        timestamp=datetime.utcnow(),
    )

    log = DgiiValidationLog(
        company_id=request.company_id,
        document_type=doc_type or "",
        ncf=request.ncf,
        amount=request.amount,
        is_valid=result.valid,
        issues_found=len(issues),
        error_codes=[i.issue_code for i in issues] if issues else [],
        validated_by=request.user_id,
    )
    db.add(log)
    db.commit()

    return result


@router.post("/partner/enrich")
async def enrich_partner(payload: EnrichPartnerRequest, db: Session = Depends(get_db)) -> dict:
    cache = _resolve_rnc(db, payload.rnc)
    status_value = cache.status.value if hasattr(cache.status, "value") else str(cache.status)
    if status_value != RncStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail=f"RNC {cache.rnc_number} no activo")

    existing = db.query(Partner).filter(Partner.tax_id == cache.rnc_number).first()
    existing_obj = cast(Any, existing)
    if existing_obj:
        if payload.company_name and existing_obj.company_name != payload.company_name:
            existing_obj.company_name = payload.company_name
            db.commit()
        return {
            "success": True,
            "data": {
                "status": "updated",
                "partner_id": existing_obj.id,
                "tax_id": existing_obj.tax_id,
            },
            "meta": {},
        }

    partner = Partner(
        company_name=payload.company_name or cache.business_name or f"RNC {cache.rnc_number}",
        tax_id=cache.rnc_number,
        contact_email=payload.contact_email or f"rnc-{cache.rnc_number}@placeholder.local",
        status="pending",
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)

    return {
        "success": True,
        "data": {
            "status": "created",
            "partner_id": partner.id,
            "tax_id": partner.tax_id,
        },
        "meta": {},
    }
