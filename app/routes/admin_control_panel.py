"""
🔧 ADMIN ROUTES — API REST para administración de sistema
═════════════════════════════════════════════════════════════════
Endpoints para gestionar SMTP, templates de email y alertas de almacenamiento.
Requiere API Key o autenticación admin.
═════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, HTTPException, Query, Body, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Optional
import hmac
import logging

from ..models.database import get_db
from ..services.admin_smtp_service import AdminSmtpService
from ..services.admin_email_template_service import AdminEmailTemplateService
from ..services.admin_storage_alerts_service import AdminStorageAlertsService
from ..security.tokens import TokenManager
from ..config import PROVISIONING_API_KEY, get_runtime_setting

logger = logging.getLogger("admin_routes")
SMTP_ENV_ONLY_MESSAGE = "SMTP se administra solo desde .env.production y requiere reinicio de erp-core"

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ═══════════════════════════════════════════════════════════════════
# 🔐 AUTHENTICATION HELPER
# ═══════════════════════════════════════════════════════════════════

def _get_admin_user(request: Request) -> Dict:
    """
    Verifica que el usuario sea admin.
    Acepta: token Bearer en Authorization header, cookie, o x-api-key.
    """
    # Intentar token Bearer o cookie
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        try:
            payload = TokenManager.verify_access_token(token)
            if payload.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Solo administradores")
            return payload
        except:
            pass
    
    # Fallback a API key
    api_key = (request.headers.get("x-api-key") or "").strip()
    expected_api_key = str(get_runtime_setting("PROVISIONING_API_KEY", PROVISIONING_API_KEY) or "").strip()
    if expected_api_key and api_key and hmac.compare_digest(api_key, expected_api_key):
        return {"username": "api-admin", "role": "admin"}
    
    raise HTTPException(status_code=401, detail="No autenticado. Requiere token Bearer o x-api-key")


# ═══════════════════════════════════════════════════════════════════
# 📧 SMTP ADMINISTRATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/smtp/config")
async def get_smtp_config(request: Request, db: Session = Depends(get_db)):
    """GET /api/admin/smtp/config - Obtiene configuración SMTP sin contraseña"""
    _get_admin_user(request)
    service = AdminSmtpService(db)
    return {"success": True, "data": service.get_smtp_config_display()}


@router.post("/smtp/config")
async def update_smtp_config(request: Request, updates: Dict = Body(...), db: Session = Depends(get_db)):
    """POST /api/admin/smtp/config - Actualiza credenciales SMTP"""
    _get_admin_user(request)
    raise HTTPException(status_code=403, detail=SMTP_ENV_ONLY_MESSAGE)


@router.put("/smtp/credential/{key}")
async def update_smtp_credential(key: str, value: str = Body(..., embed=True), request: Request = None, db: Session = Depends(get_db)):
    """PUT /api/admin/smtp/credential/{key} - Actualiza una credencial"""
    _get_admin_user(request)
    raise HTTPException(status_code=403, detail=SMTP_ENV_ONLY_MESSAGE)


@router.post("/smtp/test")
async def test_smtp(test_email: Optional[str] = Query(None), request: Request = None, db: Session = Depends(get_db)):
    """POST /api/admin/smtp/test - Prueba conexión SMTP"""
    _get_admin_user(request)
    service = AdminSmtpService(db)
    result = service.test_smtp_connection(test_email)
    return {"success": result.get("success", False), "data": result}


@router.get("/smtp/status")
async def get_smtp_status(request: Request, db: Session = Depends(get_db)):
    """GET /api/admin/smtp/status - Estado del SMTP"""
    _get_admin_user(request)
    service = AdminSmtpService(db)
    return {"success": True, "data": service.get_smtp_status()}


# ═══════════════════════════════════════════════════════════════════
# 📧 EMAIL TEMPLATE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/email-templates")
async def list_email_templates(request: Request, only_active: bool = Query(True), db: Session = Depends(get_db)):
    """GET /api/admin/email-templates - Lista plantillas"""
    _get_admin_user(request)
    service = AdminEmailTemplateService(db)
    templates = service.get_all_templates(only_active)
    return {"success": True, "data": templates, "count": len(templates)}


@router.get("/email-templates/{template_type}")
async def get_email_template(template_type: str, request: Request, db: Session = Depends(get_db)):
    """GET /api/admin/email-templates/{type} - Obtiene plantilla"""
    _get_admin_user(request)
    service = AdminEmailTemplateService(db)
    template = service.get_template(template_type)
    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    return {"success": True, "data": template}


@router.post("/email-templates")
async def create_email_template(template_data: Dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    """POST /api/admin/email-templates - Crea plantilla"""
    admin = _get_admin_user(request)
    service = AdminEmailTemplateService(db)
    success, message, template_id = service.create_template(
        template_type=template_data.get("template_type"),
        name=template_data.get("name"),
        subject=template_data.get("subject"),
        html_body=template_data.get("html_body"),
        updated_by=admin.get("username", "api"),
        **{k: v for k, v in template_data.items() if k in ["text_body", "preview_text", "tags", "variables"]}
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "data": {"template_id": template_id}, "message": message}


@router.put("/email-templates/{template_type}")
async def update_email_template(template_type: str, updates: Dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    """PUT /api/admin/email-templates/{type} - Actualiza plantilla"""
    admin = _get_admin_user(request)
    service = AdminEmailTemplateService(db)
    updates["updated_by"] = admin.get("username", "api")
    success, message = service.update_template(template_type, **updates)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post("/email-templates/{template_type}/preview")
async def preview_email_template(template_type: str, variables: Dict = Body(default={}), request: Request = None, db: Session = Depends(get_db)):
    """POST /api/admin/email-templates/{type}/preview - Preview con variables"""
    _get_admin_user(request)
    service = AdminEmailTemplateService(db)
    preview = service.preview_template(template_type, variables)
    if not preview.get("success"):
        raise HTTPException(status_code=404, detail=preview.get("error"))
    return {"success": True, "data": preview}


@router.post("/email-templates/{template_type}/toggle")
async def toggle_email_template(template_type: str, is_active: bool = Body(..., embed=True), request: Request = None, db: Session = Depends(get_db)):
    """POST /api/admin/email-templates/{type}/toggle - Activa/desactiva"""
    admin = _get_admin_user(request)
    service = AdminEmailTemplateService(db)
    success, message = service.toggle_template_active(template_type, is_active, admin.get("username", "api"))
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.get("/email-templates/stats")
async def get_email_templates_stats(request: Request, db: Session = Depends(get_db)):
    """GET /api/admin/email-templates/stats - Estadísticas"""
    _get_admin_user(request)
    service = AdminEmailTemplateService(db)
    stats = service.get_templates_stats()
    return {"success": True, "data": stats}


# ═══════════════════════════════════════════════════════════════════
# 💾 STORAGE ALERTS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/storage-alerts/config")
async def get_storage_alert_config(request: Request, db: Session = Depends(get_db)):
    """GET /api/admin/storage-alerts/config - Obtiene configuración"""
    _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    return {"success": True, "data": service.get_threshold_config()}


@router.put("/storage-alerts/config")
async def update_storage_alert_config(config_updates: Dict = Body(...), request: Request = None, db: Session = Depends(get_db)):
    """PUT /api/admin/storage-alerts/config - Actualiza thresholds"""
    admin = _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    config_updates["updated_by"] = admin.get("username", "api")
    success, message = service.update_threshold_config(**config_updates)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.get("/storage-alerts/active")
async def get_active_storage_alerts(status: Optional[str] = Query(None), days: int = Query(30), request: Request = None, db: Session = Depends(get_db)):
    """GET /api/admin/storage-alerts/active - Alertas activas"""
    _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    alerts = service.get_active_alerts(status, days)
    return {"success": True, "data": alerts, "count": len(alerts)}


@router.get("/storage-alerts/stats")
async def get_storage_alert_stats(request: Request, db: Session = Depends(get_db)):
    """GET /api/admin/storage-alerts/stats - Estadísticas"""
    _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    stats = service.get_alert_stats()
    return {"success": True, "data": stats}


@router.post("/storage-alerts/{alert_id}/resolve")
async def resolve_storage_alert(alert_id: int, request: Request = None, db: Session = Depends(get_db)):
    """POST /api/admin/storage-alerts/{id}/resolve - Resuelve alerta"""
    admin = _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    success, message = service.resolve_alert(alert_id, admin.get("username", "api"))
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.post("/storage-alerts/resolve-batch")
async def resolve_storage_alerts_batch(alert_ids: List[int] = Body(...), request: Request = None, db: Session = Depends(get_db)):
    """POST /api/admin/storage-alerts/resolve-batch - Resuelve múltiples"""
    admin = _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    resolved, errors = service.resolve_alerts_batch(alert_ids, admin.get("username", "api"))
    return {"success": len(errors) == 0, "data": {"resolved": resolved, "failed": len(errors), "errors": errors}}


@router.get("/storage-alerts/customer/{customer_id}/trends")
async def get_customer_storage_trends(customer_id: int, days: int = Query(30), request: Request = None, db: Session = Depends(get_db)):
    """GET /api/admin/storage-alerts/customer/{id}/trends - Tendencias"""
    _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    trends = service.get_customer_storage_trends(customer_id, days)
    if not trends:
        raise HTTPException(status_code=404, detail="No se encontraron datos")
    return {"success": True, "data": trends}


@router.post("/storage-alerts/slack/enable")
async def enable_slack_notifications(slack_webhook: str = Body(..., embed=True), request: Request = None, db: Session = Depends(get_db)):
    """POST /api/admin/storage-alerts/slack/enable - Habilita Slack"""
    admin = _get_admin_user(request)
    service = AdminStorageAlertsService(db)
    success, message = service.enable_slack_notifications(slack_webhook, admin.get("username", "api"))
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


# ═══════════════════════════════════════════════════════════════════
# 🏥 HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════

@router.get("/health")
async def admin_health(request: Request, db: Session = Depends(get_db)):
    """GET /api/admin/health - Verificar salud de servicios"""
    _get_admin_user(request)
    return {
        "success": True,
        "status": "healthy",
        "services": {
            "smtp": "available",
            "email_templates": "available",
            "storage_alerts": "available"
        }
    }
