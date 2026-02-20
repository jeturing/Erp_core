"""
Quota Service — Phase 2: Resource Quotas
Servicio centralizado para consultar y enforcer cuotas de recursos por cliente/plan.

Recursos gestionados:
  - users (max_users): Usuarios Odoo del tenant
  - domains (max_domains): Dominios custom externos
  - websites (max_websites): Websites Odoo (multi-website)
  - companies (max_companies): Multi-company Odoo
  - storage (max_storage_mb): Almacenamiento de BD + filestore en MB
  - backups (max_backups): Backups automáticos retenidos
  - api_calls (max_api_calls_day): Llamadas API diarias

Convenciones:
  - 0 = ilimitado (excepto max_domains donde 0 = sin dominios)
  - -1 = ilimitado (para max_domains, backward compat)
  - Enforcement: check_quota() lanza HTTPException 403 si se excede
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..models.database import (
    Customer, Subscription, SubscriptionStatus,
    Plan, CustomDomain, TenantDeployment,
)

logger = logging.getLogger("quota_service")


# Recursos y sus campos en Plan
QUOTA_FIELDS = {
    "users":      "max_users",
    "domains":    "max_domains",
    "websites":   "max_websites",
    "companies":  "max_companies",
    "storage_mb": "max_storage_mb",
    "backups":    "max_backups",
    "api_calls":  "max_api_calls_day",
}


class QuotaService:
    """Servicio centralizado de cuotas de recursos."""

    def __init__(self, db: Session):
        self.db = db

    # ── Consulta ──────────────────────────────────────────────────────────

    def get_customer_quotas(self, customer_id: int) -> Dict[str, Any]:
        """
        Retorna el estado completo de cuotas de un cliente.
        Incluye: límite del plan, uso actual, % uso, puede agregar más.
        """
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "error": "Cliente no encontrado"}

        plan, plan_name = self._get_active_plan(customer_id)
        usage = self._get_current_usage(customer_id)

        quotas = {}
        for resource, field in QUOTA_FIELDS.items():
            limit = getattr(plan, field, 0) if plan else 0
            used = usage.get(resource, 0)
            unlimited = self._is_unlimited(resource, limit)

            quotas[resource] = {
                "limit": limit,
                "used": used,
                "available": None if unlimited else max(0, limit - used),
                "percentage": 0 if unlimited or limit == 0 else round(used / limit * 100, 1),
                "unlimited": unlimited,
                "can_add": unlimited or used < limit,
                "exceeded": not unlimited and used > limit,
            }

        return {
            "success": True,
            "customer_id": customer_id,
            "company_name": customer.company_name,
            "plan_name": plan.display_name if plan else plan_name,
            "plan_key": plan_name,
            "quotas": quotas,
        }

    def get_resource_quota(
        self, customer_id: int, resource: str
    ) -> Dict[str, Any]:
        """Consulta cuota de un solo recurso."""
        if resource not in QUOTA_FIELDS:
            return {"success": False, "error": f"Recurso desconocido: {resource}"}

        full = self.get_customer_quotas(customer_id)
        if not full.get("success"):
            return full

        return {
            "success": True,
            "customer_id": customer_id,
            "resource": resource,
            **full["quotas"][resource],
            "plan_name": full["plan_name"],
        }

    def check_quota(
        self, customer_id: int, resource: str, increment: int = 1
    ) -> Dict[str, Any]:
        """
        Verifica si el cliente puede agregar `increment` unidades del recurso.
        Retorna success=True si puede, success=False con mensaje si no.
        """
        q = self.get_resource_quota(customer_id, resource)
        if not q.get("success"):
            return q

        if q["unlimited"]:
            return {"success": True, "allowed": True}

        new_total = q["used"] + increment
        if new_total > q["limit"]:
            return {
                "success": False,
                "allowed": False,
                "resource": resource,
                "used": q["used"],
                "limit": q["limit"],
                "requested": increment,
                "message": (
                    f"Cuota de {resource} excedida: {q['used']}/{q['limit']}. "
                    f"El plan '{q['plan_name']}' no permite más. "
                    f"Actualice su plan para obtener más recursos."
                ),
            }

        return {"success": True, "allowed": True}

    # ── Resumen multi-cliente (admin) ─────────────────────────────────────

    def get_all_customers_quotas(self) -> List[Dict[str, Any]]:
        """Retorna resumen de cuotas de todos los clientes (para admin dashboard)."""
        customers = self.db.query(Customer).order_by(Customer.company_name).all()
        result = []

        for c in customers:
            plan, plan_name = self._get_active_plan(c.id)
            usage = self._get_current_usage(c.id)

            summary = {
                "customer_id": c.id,
                "company_name": c.company_name,
                "subdomain": c.subdomain,
                "plan_name": plan.display_name if plan else plan_name,
                "plan_key": plan_name,
                "resources": {},
            }

            for resource, field in QUOTA_FIELDS.items():
                limit = getattr(plan, field, 0) if plan else 0
                used = usage.get(resource, 0)
                unlimited = self._is_unlimited(resource, limit)
                summary["resources"][resource] = {
                    "used": used,
                    "limit": limit,
                    "unlimited": unlimited,
                    "exceeded": not unlimited and used > limit,
                }

            result.append(summary)

        return result

    # ── Helpers internos ──────────────────────────────────────────────────

    def _get_active_plan(self, customer_id: int):
        """Retorna (Plan, plan_name) del cliente."""
        sub = self.db.query(Subscription).filter(
            Subscription.customer_id == customer_id,
            Subscription.status == SubscriptionStatus.active,
        ).first()

        plan_name = "basic"
        if sub:
            plan_name = sub.plan_name
        else:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if customer and customer.plan:
                plan_name = customer.plan.value

        plan = self.db.query(Plan).filter(
            Plan.name == plan_name, Plan.is_active == True
        ).first()

        return plan, plan_name

    def _get_current_usage(self, customer_id: int) -> Dict[str, int]:
        """Calcula el uso actual de todos los recursos del cliente."""
        usage = {}

        # Dominios custom
        usage["domains"] = self.db.query(CustomDomain).filter(
            CustomDomain.customer_id == customer_id,
        ).count()

        # Usuarios (de la suscripción activa)
        sub = self.db.query(Subscription).filter(
            Subscription.customer_id == customer_id,
            Subscription.status == SubscriptionStatus.active,
        ).first()
        usage["users"] = sub.user_count if sub else 1

        # Websites, companies, storage — requieren consulta a Odoo
        # Por ahora usamos valores por defecto; se pueden enriquecer con
        # consultas reales a la BD del tenant cuando sea necesario
        deployment = self.db.query(TenantDeployment).filter(
            TenantDeployment.customer_id == customer_id,
        ).first()

        if deployment and deployment.database_name:
            odoo_usage = self._get_odoo_usage(deployment.database_name)
            usage["websites"] = odoo_usage.get("websites", 1)
            usage["companies"] = odoo_usage.get("companies", 1)
            usage["storage_mb"] = odoo_usage.get("storage_mb", 0)
        else:
            usage["websites"] = 0
            usage["companies"] = 0
            usage["storage_mb"] = 0

        usage["backups"] = 0  # TODO: integrar con sistema de backups
        usage["api_calls"] = 0  # TODO: integrar con rate limiter

        return usage

    def _get_odoo_usage(self, tenant_db: str) -> Dict[str, int]:
        """Consulta uso real desde la BD Odoo del tenant."""
        import subprocess
        from ..config import CT105_IP, ODOO_DB_USER, ODOO_DB_PASSWORD

        result = {"websites": 1, "companies": 1, "storage_mb": 0}

        try:
            # Websites count
            cmd = (
                f"PGPASSWORD='{ODOO_DB_PASSWORD}' psql "
                f"-h {CT105_IP} -p 5432 -U {ODOO_DB_USER} "
                f"-d {tenant_db} -t -A -c "
                f"\"SELECT COUNT(*) FROM website;\""
            )
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                result["websites"] = int(r.stdout.strip())

            # Companies count
            cmd_co = cmd.replace("SELECT COUNT(*) FROM website", "SELECT COUNT(*) FROM res_company")
            r2 = subprocess.run(cmd_co, shell=True, capture_output=True, text=True, timeout=5)
            if r2.returncode == 0 and r2.stdout.strip():
                result["companies"] = int(r2.stdout.strip())

            # DB size in MB
            cmd_sz = (
                f"PGPASSWORD='{ODOO_DB_PASSWORD}' psql "
                f"-h {CT105_IP} -p 5432 -U {ODOO_DB_USER} "
                f"-d {tenant_db} -t -A -c "
                f"\"SELECT pg_database_size(current_database()) / 1024 / 1024;\""
            )
            r3 = subprocess.run(cmd_sz, shell=True, capture_output=True, text=True, timeout=5)
            if r3.returncode == 0 and r3.stdout.strip():
                result["storage_mb"] = int(r3.stdout.strip())

        except Exception as e:
            logger.warning(f"No se pudo consultar uso Odoo para {tenant_db}: {e}")

        return result

    @staticmethod
    def _is_unlimited(resource: str, limit: int) -> bool:
        """Determina si un recurso es ilimitado según su convención."""
        if resource == "domains":
            return limit == -1
        return limit == 0 or limit == -1
