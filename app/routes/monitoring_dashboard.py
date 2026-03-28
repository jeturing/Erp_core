"""
Full Monitoring Dashboard — Evaluación completa con alertas y migraciones
Combina plan_migration + storage_alerts en un solo endpoint
"""
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field
from typing import Optional
import logging

from ..models.database import SessionLocal
from ..services.plan_migration_service import PlanMigrationService
from ..services.storage_alert_service import StorageAlertService
from ..config import PROVISIONING_API_KEY, get_runtime_setting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring Dashboard"])


def _require_api_key(x_api_key: Optional[str]) -> None:
    if x_api_key != get_runtime_setting("PROVISIONING_API_KEY", PROVISIONING_API_KEY):
        raise HTTPException(status_code=401, detail="API key inválida")


@router.get("/dashboard", response_model=dict)
async def get_monitoring_dashboard(
    x_api_key: str = Header(None)
):
    """
    Dashboard completo de monitoreo con:
    - Evaluación de consumo de todos los tenants
    - Alertas activas
    - Recomendaciones de migración
    - Resumen ejecutivo
    
    Disponible para: Admin
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        # Evaluar consumo y alertas
        alert_service = StorageAlertService(db)
        evaluation_result = alert_service.evaluate_all_with_alerts()
        
        # Obtener alertas activas
        active_alerts = alert_service.get_active_alerts()
        
        # Intentar obtener resumen de migraciones (si falla, usar defaults)
        migration_summary = {
            "ok": 0,
            "warning": 0,
            "critical": 0,
            "exceeded": 0,
            "migration_recommended": 0,
            "tenants_by_status": {
                "ok": [],
                "warning": [],
                "critical": [],
                "exceeded": [],
            }
        }
        
        try:
            migration_service = PlanMigrationService(db)
            migration_summary = migration_service.get_migration_summary()
        except Exception as e:
            logger.error(f"Error getting migration summary: {str(e)}")
        
        return {
            "success": True,
            "timestamp": "",
            "overview": {
                "total_tenants": evaluation_result.get("total_evaluated", 0),
                "total_alerts": len(active_alerts),
                "alerts_by_status": {
                    "warning": len([a for a in active_alerts if a.get("status") == "warning"]),
                    "critical": len([a for a in active_alerts if a.get("status") == "critical"]),
                    "exceeded": len([a for a in active_alerts if a.get("status") == "exceeded"]),
                },
                "migration_recommended": migration_summary.get("migration_recommended", 0),
            },
            "health": {
                "total_ok": migration_summary.get("ok", 0),
                "total_warning": migration_summary.get("warning", 0),
                "total_critical": migration_summary.get("critical", 0),
                "total_exceeded": migration_summary.get("exceeded", 0),
            },
            "alerts": active_alerts,
            "tenants_requiring_attention": [
                t for t in migration_summary.get("tenants_by_status", {}).get("critical", []) +
                migration_summary.get("tenants_by_status", {}).get("exceeded", [])
            ],
            "recommendations": {
                "migrations": migration_summary.get("tenants_by_status", {}).get("exceeded", []),
                "upgrades": migration_summary.get("tenants_by_status", {}).get("critical", []),
            }
        }
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en dashboard: {str(e)}")
    finally:
        db.close()


@router.post("/evaluate-and-alert", response_model=dict)
async def evaluate_tenant_with_alert(
    subdomain: str = Query(...),
    customer_id: Optional[int] = Query(None),
    x_api_key: str = Header(None)
):
    """
    Evalúa un tenant y genera alertas automáticamente.
    
    Returns:
    - Evaluación de consumo
    - Alerta generada (si aplica)
    - Recomendación de migración
    - Email enviado (bool)
    """
    _require_api_key(x_api_key)
    
    db = SessionLocal()
    try:
        # Generar alerta (que incluye evaluación)
        alert_service = StorageAlertService(db)
        alert_result = alert_service.evaluate_and_alert(customer_id or 0, subdomain)
        
        # Evaluación adicional para recomendación de plan
        migration_service = PlanMigrationService(db)
        evaluation = migration_service.evaluate_tenant(subdomain, customer_id)
        
        return {
            "success": True,
            "evaluation": {
                "subdomain": subdomain,
                "status": alert_result.get("status"),
                "usage_percent": alert_result.get("usage_percent"),
                "message": alert_result.get("message"),
            },
            "alert": {
                "created": alert_result.get("alert_created"),
                "email_sent": alert_result.get("email_sent"),
            },
            "recommendation": evaluation.get("recommendation"),
            "should_migrate": evaluation.get("should_migrate"),
        }
    finally:
        db.close()
