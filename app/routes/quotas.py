"""
Quotas API — Phase 2: Resource Quotas
Endpoints para consultar y verificar cuotas de recursos por cliente.
"""
from fastapi import APIRouter, HTTPException, Request, Cookie, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from ..models.database import SessionLocal
from ..services.quota_service import QuotaService
from .roles import verify_token_with_role
import logging

router = APIRouter(prefix="/api/quotas", tags=["Quotas"])
logger = logging.getLogger(__name__)


def _verify_admin(request: Request, token: str = None):
    """Extrae y verifica token de admin."""
    if not token:
        token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    verify_token_with_role(token, required_role="admin")


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.get("/{customer_id}")
async def get_customer_quotas(
    customer_id: int,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Retorna el estado consolidado de todas las cuotas de un cliente.
    Incluye: límite del plan, uso actual, porcentaje, si puede agregar más.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        result = svc.get_customer_quotas(customer_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Error"))
        return result
    finally:
        db.close()


@router.get("/{customer_id}/{resource}")
async def get_resource_quota(
    customer_id: int,
    resource: str,
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Retorna la cuota de un recurso específico para un cliente.
    Recursos: users, domains, websites, companies, storage_mb, backups, api_calls.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        result = svc.get_resource_quota(customer_id, resource)
        if not result.get("success"):
            raise HTTPException(
                status_code=400 if "desconocido" in result.get("error", "") else 404,
                detail=result.get("error", "Error"),
            )
        return result
    finally:
        db.close()


@router.get("/{customer_id}/check/{resource}")
async def check_quota(
    customer_id: int,
    resource: str,
    request: Request,
    access_token: str = Cookie(None),
    increment: int = Query(1, ge=1, description="Unidades a agregar"),
) -> Dict[str, Any]:
    """
    Verifica si el cliente puede agregar N unidades de un recurso.
    Retorna allowed=True si puede, 403 si no.
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        result = svc.check_quota(customer_id, resource, increment)
        if not result.get("success"):
            if result.get("allowed") is False:
                raise HTTPException(status_code=403, detail=result.get("message", "Cuota excedida"))
            raise HTTPException(status_code=400, detail=result.get("error", "Error"))
        return result
    finally:
        db.close()


@router.get("")
async def get_all_quotas(
    request: Request,
    access_token: str = Cookie(None),
) -> Dict[str, Any]:
    """
    Retorna resumen de cuotas de todos los clientes (admin dashboard).
    """
    _verify_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        customers = svc.get_all_customers_quotas()
        return {
            "success": True,
            "total": len(customers),
            "customers": customers,
        }
    finally:
        db.close()
