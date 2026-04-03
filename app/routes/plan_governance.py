"""
Plan Governance Routes — Fair use, límites y uso real por tenant.

Fase 1:
- Monitoreo y recomendación
- Sin enforcement duro
- Aplicable principalmente a clientes nuevos (fair_use_enabled=True)
"""
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Cookie, Request

from ..models.database import SessionLocal, Plan
from ..services.quota_service import QuotaService
from .roles import _require_admin

router = APIRouter(prefix="/api/plan-governance", tags=["Plan Governance"])

_RESOURCE_LABELS = {
    "users": "Usuarios",
    "domains": "Dominios",
    "websites": "Sitios web",
    "companies": "Empresas",
    "storage_mb": "Almacenamiento",
    "stock_sku": "SKU con stock",
    "backups": "Backups",
    "api_calls": "API calls",
}


def _percentage(resource: Dict[str, Any]) -> float:
    if resource.get("unlimited") or not resource.get("limit"):
        return 0.0
    limit = float(resource.get("limit") or 0)
    used = float(resource.get("used") or 0)
    return round((used / limit) * 100, 1) if limit > 0 else 0.0


def _recommend_plan(db, current_plan_key: str, top_resource: str, required_used: float) -> Optional[Dict[str, Any]]:
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.sort_order, Plan.id).all()
    current_index = next((idx for idx, plan in enumerate(plans) if plan.name == current_plan_key), None)
    if current_index is None:
        return None

    resource_to_field = {
        "users": "max_users",
        "domains": "max_domains",
        "websites": "max_websites",
        "companies": "max_companies",
        "storage_mb": "max_storage_mb",
        "stock_sku": "max_stock_sku",
        "backups": "max_backups",
        "api_calls": "max_api_calls_day",
    }
    field = resource_to_field.get(top_resource)
    if not field:
        return None

    for plan in plans[current_index + 1:]:
        limit = getattr(plan, field, 0) or 0
        if limit == 0 or limit >= required_used:
            return {
                "plan_name": plan.name,
                "display_name": plan.display_name,
                "resource": top_resource,
                "resource_label": _RESOURCE_LABELS.get(top_resource, top_resource),
                "new_limit": limit,
            }
    return None


@router.get("/summary")
async def get_plan_governance_summary(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    new_only: bool = True,
) -> Dict[str, Any]:
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        items = svc.get_all_customers_quotas()
        if new_only:
            items = [item for item in items if item.get("fair_use_enabled")]

        customers: List[Dict[str, Any]] = []
        for item in items:
            ranked = []
            for resource_key, resource in item.get("resources", {}).items():
                ranked.append((resource_key, _percentage(resource), resource))
            ranked.sort(key=lambda row: row[1], reverse=True)
            top_key, top_pct, top_resource = ranked[0] if ranked else (None, 0, {})
            recommendation = _recommend_plan(
                db,
                item.get("plan_key"),
                top_key,
                float(top_resource.get("used") or 0),
            ) if top_key else None

            customers.append({
                **item,
                "top_resource": top_key,
                "top_resource_label": _RESOURCE_LABELS.get(top_key, top_key) if top_key else None,
                "top_usage_percent": top_pct,
                "top_status": top_resource.get("status", "ok") if top_key else "ok",
                "recommendation": recommendation,
            })

        customers.sort(key=lambda row: (row.get("top_usage_percent", 0), row.get("company_name") or ""), reverse=True)

        plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.sort_order, Plan.id).all()
        return {
            "success": True,
            "new_only": new_only,
            "total": len(customers),
            "plans": [
                {
                    "id": plan.id,
                    "name": plan.name,
                    "display_name": plan.display_name,
                    "max_users": plan.max_users,
                    "max_storage_mb": plan.max_storage_mb,
                    "max_stock_sku": getattr(plan, "max_stock_sku", 0),
                    "quota_warning_percent": getattr(plan, "quota_warning_percent", 80),
                    "quota_recommend_percent": getattr(plan, "quota_recommend_percent", 95),
                    "quota_block_percent": getattr(plan, "quota_block_percent", 100),
                    "fair_use_new_customers_only": getattr(plan, "fair_use_new_customers_only", True),
                }
                for plan in plans
            ],
            "customers": customers,
        }
    finally:
        db.close()


@router.get("/customer/{customer_id}")
async def get_plan_governance_customer(
    customer_id: int,
    request: Request,
    access_token: Optional[str] = Cookie(None),
) -> Dict[str, Any]:
    _require_admin(request, access_token)
    db = SessionLocal()
    try:
        svc = QuotaService(db)
        result = svc.get_customer_quotas(customer_id)
        if not result.get("success"):
            return result

        ranked = []
        for resource_key, resource in result.get("quotas", {}).items():
            ranked.append((resource_key, _percentage(resource), resource))
        ranked.sort(key=lambda row: row[1], reverse=True)
        top_key, top_pct, top_resource = ranked[0] if ranked else (None, 0, {})
        result["top_resource"] = top_key
        result["top_resource_label"] = _RESOURCE_LABELS.get(top_key, top_key) if top_key else None
        result["top_usage_percent"] = top_pct
        result["top_status"] = top_resource.get("status", "ok") if top_key else "ok"
        result["recommendation"] = _recommend_plan(
            db,
            result.get("plan_key"),
            top_key,
            float(top_resource.get("used") or 0),
        ) if top_key else None
        return result
    finally:
        db.close()
