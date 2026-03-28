"""
Plan Migration Routes — Endpoints para evaluación y migración automática de planes
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from ..models.database import SessionLocal
from ..services.plan_migration_service import PlanMigrationService
from ..config import PROVISIONING_API_KEY, get_runtime_setting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plan-migration", tags=["Plan Migration"])


def _require_api_key(x_api_key: Optional[str]) -> None:
    if x_api_key != get_runtime_setting("PROVISIONING_API_KEY", PROVISIONING_API_KEY):
        raise HTTPException(status_code=401, detail="API key inválida")


class TenantEvaluationRequest(BaseModel):
    """Request para evaluar un tenant específico"""
    tenant_db: str = Field(..., description="Nombre de la BD del tenant (subdomain)")
    customer_id: Optional[int] = Field(None, description="ID del cliente (opcional)")


class AutoMigrateRequest(BaseModel):
    """Request para ejecutar migración automática"""
    tenant_db: str = Field(..., description="Nombre de la BD del tenant")
    customer_id: Optional[int] = Field(None, description="ID del cliente (opcional)")
    dry_run: bool = Field(True, description="Si True, solo simula (no ejecuta)")


# ═══════════════════════════════════════════════════════════════════════════════
# EVALUACIÓN DE TENANTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/evaluate", response_model=dict)
async def evaluate_tenant(
    request: TenantEvaluationRequest,
    x_api_key: str = Header(None)
):
    """
    Evalúa un tenant específico y determina si necesita migración de plan.
    
    Retorna:
    - status: "ok" | "warning" | "critical" | "exceeded"
    - usage_percent: % de uso del límite actual
    - should_migrate: bool indicando si se recomienda migración
    - recommendation: Plan recomendado (si aplica)
    
    Ejemplos:
    ```json
    {
        "tenant_db": "sattra",
        "customer_id": 5
    }
    ```
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        result = service.evaluate_tenant(
            tenant_db=request.tenant_db,
            customer_id=request.customer_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    finally:
        db.close()


@router.get("/evaluate-all", response_model=dict)
async def evaluate_all_tenants(
    x_api_key: str = Header(None)
):
    """
    Evalúa todos los tenants activos y retorna un reporte completo.
    
    Útil para:
    - Dashboard de monitoreo
    - Reportes ejecutivos
    - Identificar tenants que requieren atención
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        results = service.evaluate_all_tenants()
        
        return {
            "success": True,
            "total_tenants": len(results),
            "evaluations": results,
        }
    finally:
        db.close()


@router.get("/summary", response_model=dict)
async def get_migration_summary(
    x_api_key: str = Header(None)
):
    """
    Genera resumen ejecutivo de todos los tenants.
    
    Retorna contadores por estado:
    - ok: Dentro del límite
    - warning: 75-90% del límite
    - critical: 90-100% del límite
    - exceeded: Supera el límite
    - migration_recommended: Requieren migración
    
    Incluye listas detalladas por cada estado.
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        summary = service.get_migration_summary()
        
        return {
            "success": True,
            "summary": summary,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# MIGRACIÓN AUTOMÁTICA
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/auto-migrate", response_model=dict)
async def auto_migrate_tenant(
    request: AutoMigrateRequest,
    x_api_key: str = Header(None)
):
    """
    Ejecuta migración automática de plan si es necesario.
    
    Args:
    - tenant_db: Nombre de la BD del tenant
    - customer_id: ID del cliente (opcional)
    - dry_run: Si True, solo simula (default: True)
    
    Proceso:
    1. Evalúa el tenant
    2. Si requiere migración y dry_run=False:
       - Actualiza la suscripción al plan recomendado
       - Recalcula monthly_amount
       - Registra en logs
    
    Ejemplos:
    ```json
    // Simular migración
    {
        "tenant_db": "sattra",
        "dry_run": true
    }
    
    // Ejecutar migración real
    {
        "tenant_db": "sattra",
        "dry_run": false
    }
    ```
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        result = service.auto_migrate_tenant(
            tenant_db=request.tenant_db,
            customer_id=request.customer_id,
            dry_run=request.dry_run
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    finally:
        db.close()


@router.post("/batch-migrate", response_model=dict)
async def batch_migrate_tenants(
    dry_run: bool = True,
    x_api_key: str = Header(None)
):
    """
    Ejecuta migración automática para TODOS los tenants que lo requieran.
    
    Proceso:
    1. Evalúa todos los tenants
    2. Filtra los que requieren migración (status critical o exceeded)
    3. Ejecuta migración para cada uno (si dry_run=False)
    
    Query params:
    - dry_run: Si True, solo simula (default: True)
    
    ADVERTENCIA: Usar con precaución en producción.
    Se recomienda ejecutar primero con dry_run=true.
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        evaluations = service.evaluate_all_tenants()
        
        # Filtrar tenants que requieren migración
        to_migrate = [
            e for e in evaluations 
            if e.get("should_migrate") and "error" not in e
        ]
        
        results = []
        migrated_count = 0
        
        for eval_result in to_migrate:
            tenant_db = eval_result["tenant_db"]
            customer_id = eval_result["customer_id"]
            
            migration_result = service.auto_migrate_tenant(
                tenant_db=tenant_db,
                customer_id=customer_id,
                dry_run=dry_run
            )
            
            results.append(migration_result)
            
            if migration_result.get("migration_executed"):
                migrated_count += 1
        
        return {
            "success": True,
            "dry_run": dry_run,
            "total_evaluated": len(evaluations),
            "requires_migration": len(to_migrate),
            "migrated": migrated_count,
            "results": results,
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# INFORMACIÓN DE PLANES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/plans", response_model=dict)
async def list_available_plans(
    x_api_key: str = Header(None)
):
    """
    Lista todos los planes disponibles con sus límites de almacenamiento.
    
    Útil para:
    - Mostrar opciones de upgrade en UI
    - Comparar planes
    - Planificación de capacidad
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        from ..models.database import Plan
        
        plans = db.query(Plan).filter(
            Plan.is_active == True
        ).order_by(Plan.max_storage_mb.asc()).all()
        
        plans_info = []
        for plan in plans:
            plans_info.append({
                "name": plan.name,
                "display_name": plan.display_name,
                "description": plan.description,
                "base_price": plan.base_price,
                "price_per_user": plan.price_per_user,
                "max_storage_mb": plan.max_storage_mb,
                "storage_unlimited": plan.max_storage_mb == 0,
                "max_users": plan.max_users,
                "max_domains": plan.max_domains,
            })
        
        return {
            "success": True,
            "plans": plans_info,
        }
    finally:
        db.close()


@router.get("/tenant/{tenant_db}/size", response_model=dict)
async def get_tenant_size(
    tenant_db: str,
    x_api_key: str = Header(None)
):
    """
    Obtiene el tamaño actual de un tenant (BD + filestore).
    
    Retorna:
    - db_size_mb: Tamaño de la base de datos PostgreSQL
    - filestore_size_mb: Tamaño del filestore
    - total_size_mb: Suma total
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        size_info = service.get_tenant_database_size(tenant_db)
        
        return {
            "success": True,
            **size_info,
        }
    finally:
        db.close()
