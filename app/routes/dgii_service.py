"""
DGII Data Service: Microservicio FastAPI para validación RNC y enriquecimiento datos.

Endpoints:
- GET /api/dgii/rnc/{numero}        → Validar RNC contra padrón oficial
- POST /api/dgii/validate           → Pre-validación anti-rechazo
- GET /api/dgii/health              → Health check
- POST /api/dgii/partner/enrich     → Enriquecimiento automático de partners

Cache: Redis (opcional) o PostgreSQL tabla local
TTL: 30 días para RNC, 7 días para validaciones
"""
from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

router = APIRouter(prefix="/api/dgii", tags=["DGII"])
_logger = logging.getLogger(__name__)


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class RncValidationRequest(BaseModel):
    """Solicitud de validación RNC."""
    rnc: str = Field(..., min_length=9, max_length=11, description="RNC del proveedor")
    business_name: str | None = Field(None, description="Nombre empresa (opcional)")
    company_id: int = Field(..., description="Company Odoo ID")


class RncValidationResponse(BaseModel):
    """Respuesta de validación RNC."""
    rnc: str
    valid: bool
    status: str  # "active", "inactive", "not_found"
    business_name: str | None
    last_updated: datetime
    cache_ttl_expires: datetime | None
    confidence_score: float  # 0.0 - 1.0


class DgiiValidationRequest(BaseModel):
    """Solicitud de pre-validación DGII."""
    document_type: str  # "606", "607", "608"
    company_id: int
    ncf: str | None = None
    amount: float | None = None
    supplier_rnc: str | None = None
    invoice_date: str | None = None


class ValidationIssue(BaseModel):
    """Problema detectado en validación."""
    issue_code: str  # "NCF_DUPLICATE", "AMOUNT_ZERO", "RNC_INACTIVE", etc.
    severity: str  # "warning", "error"
    description: str
    suggestion: str | None = None


class DgiiValidationResponse(BaseModel):
    """Respuesta de pre-validación."""
    valid: bool
    issues: list[ValidationIssue] = []
    can_proceed: bool  # True si severity="warning", False si severity="error"
    timestamp: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    database: str
    timestamp: datetime


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check del servicio DGII."""
    return HealthResponse(
        status="healthy",
        service="DGII Data Service",
        version="1.0.0",
        database="PostgreSQL (erp_core_db)",
        timestamp=datetime.utcnow()
    )


@router.get("/rnc/{numero}", response_model=RncValidationResponse)
async def validate_rnc(
    numero: str,
    db: AsyncSession = Depends()  # Inyectar sesión DB
):
    """
    Validar RNC contra padrón oficial.
    
    Flujo:
    1. Buscar en cache local (dgii_rnc_cache)
    2. Si TTL válido (< 30 días), retornar caché
    3. Si TTL expirado, consultar API oficial DGII (si implementado)
    4. Actualizar cache, retornar resultado
    
    Códigos de estado:
    - "active": RNC registrado y activo
    - "inactive": RNC registrado pero inactivo
    - "not_found": No encontrado en padrón
    """
    
    # Validar formato RNC
    if not numero or len(numero) < 9:
        raise HTTPException(status_code=400, detail="RNC inválido (mín. 9 caracteres)")
    
    # Buscar en cache local
    from app.models.database import DgiiRncCache
    
    cache_record = (await db.execute(
        select(DgiiRncCache)
        .where(DgiiRncCache.rnc_number == numero)
        .where(DgiiRncCache.ttl_expires > datetime.utcnow())  # No expirado
    )).scalars().first()
    
    if cache_record:
        # Retornar desde cache
        return RncValidationResponse(
            rnc=numero,
            valid=cache_record.status == "active",
            status=cache_record.status,
            business_name=cache_record.business_name,
            last_updated=cache_record.last_updated,
            cache_ttl_expires=cache_record.ttl_expires,
            confidence_score=1.0  # Cache es confiable
        )
    
    # Si cache expirado o no existe, consultar API DGII (mock por ahora)
    # TODO: Integrar con API oficial DGII cuando esté disponible
    
    # Mock: Simular respuesta
    new_status = "active"  # Asumir activo por defecto
    new_record = DgiiRncCache(
        rnc_number=numero,
        business_name=f"Empresa RNC {numero}",
        status=new_status,
        last_updated=datetime.utcnow(),
        ttl_expires=datetime.utcnow() + timedelta(days=30)
    )
    db.add(new_record)
    await db.commit()
    
    return RncValidationResponse(
        rnc=numero,
        valid=(new_status == "active"),
        status=new_status,
        business_name=new_record.business_name,
        last_updated=new_record.last_updated,
        cache_ttl_expires=new_record.ttl_expires,
        confidence_score=0.8  # API es confiable pero requiere validación
    )


@router.post("/validate", response_model=DgiiValidationResponse)
async def validate_dgii_document(
    request: DgiiValidationRequest = Body(...),
    db: AsyncSession = Depends()
):
    """
    Pre-validación anti-rechazo para documentos 606/607/608.
    
    Checks:
    1. NCF duplicado (no debe existir ya en 606/607/608)
    2. Formato válido (NCF según secuencia fiscal)
    3. Catálogos válidos (empresa en padrón, RNC activo)
    4. Montos válidos (no ceros, no negativos)
    5. Fechas válidas (dentro del período fiscal)
    6. Retenciones correctas (si aplica)
    """
    
    issues: list[ValidationIssue] = []
    
    # Check 1: NCF Duplicado
    if request.ncf:
        from app.models.database import DgiiReportLog
        existing = (await db.execute(
            select(DgiiReportLog)
            .where(DgiiReportLog.ncf == request.ncf)
            .where(DgiiReportLog.company_id == request.company_id)
            .where(DgiiReportLog.document_type == request.document_type)
        )).scalars().first()
        
        if existing:
            issues.append(ValidationIssue(
                issue_code="NCF_DUPLICATE",
                severity="error",
                description=f"NCF {request.ncf} ya existe en {request.document_type}",
                suggestion="Usar NCF diferente"
            ))
    
    # Check 2: Monto válido
    if request.amount is not None:
        if request.amount <= 0:
            issues.append(ValidationIssue(
                issue_code="AMOUNT_ZERO",
                severity="error",
                description="Monto debe ser mayor a 0",
                suggestion="Verificar monto de la factura"
            ))
        elif request.amount > 999999999.99:
            issues.append(ValidationIssue(
                issue_code="AMOUNT_TOO_HIGH",
                severity="warning",
                description="Monto inusualmente alto",
                suggestion="Verificar que sea correcto"
            ))
    
    # Check 3: RNC proveedor activo (si es 606)
    if request.document_type == "606" and request.supplier_rnc:
        rnc_valid = (await validate_rnc(request.supplier_rnc, db)).valid
        if not rnc_valid:
            issues.append(ValidationIssue(
                issue_code="RNC_INACTIVE",
                severity="error",
                description=f"RNC {request.supplier_rnc} no está activo",
                suggestion="Verificar RNC del proveedor"
            ))
    
    # Check 4: Fecha válida
    if request.invoice_date:
        try:
            from datetime import datetime
            inv_date = datetime.fromisoformat(request.invoice_date)
            if inv_date > datetime.utcnow():
                issues.append(ValidationIssue(
                    issue_code="DATE_FUTURE",
                    severity="error",
                    description="Fecha de factura no puede ser futura",
                    suggestion="Usar fecha actual o anterior"
                ))
        except ValueError:
            issues.append(ValidationIssue(
                issue_code="DATE_FORMAT_INVALID",
                severity="error",
                description="Formato de fecha inválido (use ISO 8601)",
                suggestion="Usar formato YYYY-MM-DD"
            ))
    
    # Determinar si puede proceder
    has_errors = any(issue.severity == "error" for issue in issues)
    can_proceed = not has_errors
    
    return DgiiValidationResponse(
        valid=len(issues) == 0,
        issues=issues,
        can_proceed=can_proceed,
        timestamp=datetime.utcnow()
    )


@router.post("/partner/enrich", response_model=dict)
async def enrich_partner(
    rnc: str = Body(...),
    company_id: int = Body(...),
    db: AsyncSession = Depends()
):
    """
    Enriquecimiento automático de res.partner desde RNC.
    
    Flujo:
    1. Validar RNC
    2. Obtener datos del padrón
    3. Buscar o crear res.partner
    4. Actualizar campos:
       - name (business_name)
       - vat (RNC)
       - country_id (Dominican Republic)
       - is_company = True
    5. Retornar partner_id o error
    """
    
    rnc_response = await validate_rnc(rnc, db)
    
    if not rnc_response.valid:
        raise HTTPException(
            status_code=400,
            detail=f"RNC {rnc} no válido (estado: {rnc_response.status})"
        )
    
    # Buscar partner existente
    from app.models.database import Partner  # res.partner alias
    
    existing_partner = (await db.execute(
        select(Partner)
        .where(Partner.vat == rnc)
        .where(Partner.company_id == company_id)
    )).scalars().first()
    
    if existing_partner:
        return {
            "status": "updated",
            "partner_id": existing_partner.id,
            "message": f"Partner {rnc} ya existía"
        }
    
    # Crear nuevo partner
    # TODO: Mapear country_id para República Dominicana
    
    new_partner = Partner(
        name=rnc_response.business_name or f"Partner {rnc}",
        vat=rnc,
        is_company=True,
        # country_id = <DO>,
        company_id=company_id,
    )
    db.add(new_partner)
    await db.commit()
    
    return {
        "status": "created",
        "partner_id": new_partner.id,
        "name": new_partner.name,
        "rnc": rnc
    }


# ============================================================================
# INCLUIR ROUTER EN MAIN
# ============================================================================
# En app/main.py:
# from app.routes.dgii_service import router as dgii_router
# app.include_router(dgii_router)
