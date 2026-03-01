"""
Storage Alerts Routes — Endpoints para gestión de alertas de almacenamiento
"""
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from ..models.database import SessionLocal
from ..services.storage_alert_service import StorageAlertService
from ..config import PROVISIONING_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/storage-alerts", tags=["Storage Alerts"])


class AlertResponse(BaseModel):
    """Respuesta de una alerta de almacenamiento"""
    id: Optional[int] = None
    customer_id: int
    subdomain: str
    status: str  # "ok" | "warning" | "critical" | "exceeded"
    usage_percent: float
    storage_limit_mb: int
    current_usage_mb: float
    created_at: Optional[str] = None
    message: str


# ═══════════════════════════════════════════════════════════════════════════════
# EVALUACIÓN DE ALERTAS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/evaluate", response_model=dict)
async def evaluate_tenant_alert(
    tenant_db: str = Query(..., description="Nombre del tenant"),
    customer_id: int = Query(None, description="ID del cliente (opcional)"),
    x_api_key: str = Header(None)
):
    """
    Evalúa un tenant específico y genera alerta si necesario.
    
    Retorna:
    - status: "ok" | "warning" | "critical" | "exceeded"
    - alert_created: bool indicando si se creó una alerta nueva
    - email_sent: bool indicando si se envió notificación
    """
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    db = SessionLocal()
    try:
        service = StorageAlertService(db)
        result = service.evaluate_and_alert(
            customer_id=customer_id or 0,
            subdomain=tenant_db
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    finally:
        db.close()


@router.get("/evaluate-all", response_model=dict)
async def evaluate_all_alerts(
    x_api_key: str = Header(None)
):
    """
    Evalúa todos los tenants y genera alertas necesarias.
    
    Útil para:
    - Cron job diario de evaluación
    - Generación de alertas batch
    - Reportes de status global
    """
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    db = SessionLocal()
    try:
        service = StorageAlertService(db)
        result = service.evaluate_all_with_alerts()
        
        return {
            "success": True,
            **result
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# CONSULTAR ALERTAS ACTIVAS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/active", response_model=dict)
async def get_active_alerts(
    x_api_key: str = Header(None)
):
    """
    Obtiene todas las alertas activas del sistema.
    
    Retorna:
    - total_alerts: Número de alertas activas
    - alerts: Array de alertas con detalles
    
    Disponible para: Admin
    """
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    db = SessionLocal()
    try:
        service = StorageAlertService(db)
        alerts = service.get_active_alerts()
        
        return {
            "success": True,
            "total_alerts": len(alerts),
            "alerts": alerts
        }
    finally:
        db.close()


@router.get("/customer/{customer_id}", response_model=dict)
async def get_customer_alerts(
    customer_id: int,
    x_api_key: str = Header(None)
):
    """
    Obtiene alertas activas de un cliente específico.
    
    Disponible para: Admin + Tenant
    """
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    db = SessionLocal()
    try:
        service = StorageAlertService(db)
        alerts = service.get_customer_alerts(customer_id)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "total_alerts": len(alerts),
            "alerts": alerts
        }
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# RESUMEN PARA DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/summary", response_model=dict)
async def get_alerts_summary(
    x_api_key: str = Header(None)
):
    """
    Obtiene resumen ejecutivo de alertas para dashboard.
    
    Retorna:
    - total_alerts: Número de alertas activas
    - by_status: Desglose por tipo de alerta
    - critical_count: Número de alertas críticas
    
    Disponible para: Admin
    """
    if x_api_key != PROVISIONING_API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    
    db = SessionLocal()
    try:
        service = StorageAlertService(db)
        alerts = service.get_active_alerts()
        
        # Agrupar por status
        by_status = {
            "warning": [],
            "critical": [],
            "exceeded": []
        }
        
        for alert in alerts:
            if alert["status"] in by_status:
                by_status[alert["status"]].append(alert)
        
        return {
            "success": True,
            "total_alerts": len(alerts),
            "by_status": {
                status: len(items) for status, items in by_status.items()
            },
            "alerts_requiring_attention": by_status["critical"] + by_status["exceeded"],
            "critical_count": len(by_status["critical"]),
            "exceeded_count": len(by_status["exceeded"]),
        }
    finally:
        db.close()
