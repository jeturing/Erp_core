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
from ..config import PROVISIONING_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring Dashboard"])


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
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    db = SessionLocal()
    try:
        # Evaluar consumo y alertas
        alert_service = StorageAlertService(db)
        evaluation_result = alert_service.evaluate_all_with_alerts()
        
        # Obtener alertas activas
        active_alerts = alert_service.get_active_alerts()
        
        # Evaluación de planes
        migration_service = PlanMigrationService(db)
        migration_summary = migration_service.get_migration_summary()
        
        return {
            "success": True,
            "timestamp": "",
            "overview": {
                "total_tenants": evaluation_result["total_evaluated"],
                "total_alerts": len(active_alerts),
                "alerts_by_status": {
                    "warning": len([a for a in active_alerts if a["status"] == "warning"]),
                    "critical": len([a for a in active_alerts if a["status"] == "critical"]),
                    "exceeded": len([a for a in active_alerts if a["status"] == "exceeded"]),
                },
                "migration_recommended": migration_summary["summary"]["migration_recommended"],
            },
            "health": {
                "total_ok": migration_summary["summary"]["ok"],
                "total_warning": len([a for a in active_alerts if a["status"] == "warning"]),
                "total_critical": len([a for a in active_alerts if a["status"] == "critical"]),
                "total_exceeded": len([a for a in active_alerts if a["status"] == "exceeded"]),
            },
            "alerts": active_alerts,
            "tenants_requiring_attention": [
                t for t in migration_summary["summary"]["tenants_by_status"].get("critical", []) +
                migration_summary["summary"]["tenants_by_status"].get("exceeded", [])
            ],
            "recommendations": {
                "migrations": migration_summary["summary"]["tenants_by_status"].get("exceeded", []),
                "upgrades": [
                    t for t in migration_summary["summary"]["tenants_by_status"].get("critical", [])
                ],
            }
        }
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
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
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
