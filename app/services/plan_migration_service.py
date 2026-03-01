"""
Plan Migration Service — Migración automática de planes basada en consumo
===========================================================================

Evalúa el uso de recursos (principalmente tamaño de BD) de cada tenant y:
- Detecta cuándo se acerca o supera el límite del plan actual
- Sugiere planes superiores apropiados
- Ejecuta migraciones automáticas (opcional)
- Envía alertas cuando el consumo supera umbrales (75%, 90%, 100%)

Ejemplo de uso:
    # Evaluar un tenant específico
    result = PlanMigrationService(db).evaluate_tenant("sattra")
    
    # Evaluar todos los tenants
    results = PlanMigrationService(db).evaluate_all_tenants()
    
    # Migrar automáticamente si es necesario
    result = PlanMigrationService(db).auto_migrate_tenant("sattra", dry_run=False)
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.database import (
    Customer, Subscription, SubscriptionStatus,
    Plan, TenantDeployment,
)
from ..config import (
    ODOO_DB_HOST, ODOO_DB_USER, ODOO_DB_PASSWORD, ODOO_DB_PORT,
    ODOO_FILESTORE_PATH, ODOO_FILESTORE_PCT_ID,
)
from .odoo_database_manager import _run_pct_shell, _run_pct_sql

logger = logging.getLogger("plan_migration")


# Umbrales de alerta (% de uso del límite)
ALERT_THRESHOLDS = {
    "warning": 75,   # 75% del límite
    "critical": 90,  # 90% del límite
    "exceeded": 100, # 100% o más
}


class PlanMigrationService:
    """Servicio de evaluación y migración automática de planes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_tenant_database_size(self, tenant_db: str) -> Dict[str, Any]:
        """
        Obtiene el tamaño real de la BD + filestore de un tenant.
        Retorna tamaños en MB.
        """
        # 1. Tamaño de la base de datos PostgreSQL
        sql = f"""
        SELECT 
            pg_database_size('{tenant_db}') / (1024.0 * 1024.0) as db_size_mb;
        """
        
        ok, result = _run_pct_sql(
            105,  # PCT con PostgreSQL (ajustar según tu configuración)
            "postgres",  # DB para ejecutar la consulta
            sql
        )
        
        db_size_mb = 0
        if ok and result:
            try:
                # Parse result
                lines = [l.strip() for l in result.split('\n') if l.strip()]
                for line in lines:
                    if line.replace('.', '').replace('-', '').isdigit():
                        db_size_mb = float(line)
                        break
            except Exception as e:
                logger.warning(f"Error parseando tamaño de BD para {tenant_db}: {e}")
        
        # 2. Tamaño del filestore
        filestore_cmd = (
            f"du -sm {ODOO_FILESTORE_PATH}/{tenant_db} 2>/dev/null | cut -f1 || echo 0"
        )
        fs_ok, fs_result = _run_pct_shell(ODOO_FILESTORE_PCT_ID, filestore_cmd, timeout=30)
        
        filestore_size_mb = 0
        if fs_ok:
            try:
                filestore_size_mb = int(fs_result.strip())
            except Exception as e:
                logger.warning(f"Error parseando tamaño de filestore para {tenant_db}: {e}")
        
        total_size_mb = db_size_mb + filestore_size_mb
        
        return {
            "tenant_db": tenant_db,
            "db_size_mb": round(db_size_mb, 2),
            "filestore_size_mb": filestore_size_mb,
            "total_size_mb": round(total_size_mb, 2),
            "measured_at": datetime.utcnow().isoformat(),
        }
    
    def get_customer_plan_and_usage(self, customer_id: int) -> Dict[str, Any]:
        """
        Obtiene el plan actual del cliente y su uso de almacenamiento.
        """
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"error": "Cliente no encontrado"}
        
        # Obtener suscripción activa
        sub = self.db.query(Subscription).filter(
            Subscription.customer_id == customer_id,
            Subscription.status == SubscriptionStatus.active,
        ).first()
        
        plan_name = "basic"
        if sub:
            plan_name = sub.plan_name
        elif customer.plan:
            plan_name = customer.plan.value
        
        # Obtener plan
        plan = self.db.query(Plan).filter(
            Plan.name == plan_name,
            Plan.is_active == True
        ).first()
        
        if not plan:
            return {"error": f"Plan '{plan_name}' no encontrado"}
        
        # Obtener deployment para saber la BD del tenant
        deployment = self.db.query(TenantDeployment).filter(
            TenantDeployment.customer_id == customer_id
        ).first()
        
        tenant_db = customer.subdomain if customer.subdomain else None
        if deployment and deployment.subdomain:
            tenant_db = deployment.subdomain
        
        if not tenant_db:
            return {"error": "No se pudo determinar la BD del tenant"}
        
        # Obtener tamaño actual
        size_info = self.get_tenant_database_size(tenant_db)
        
        return {
            "customer_id": customer_id,
            "company_name": customer.company_name,
            "subdomain": customer.subdomain,
            "tenant_db": tenant_db,
            "plan_name": plan.name,
            "plan_display": plan.display_name,
            "plan_storage_limit_mb": plan.max_storage_mb,
            "storage_unlimited": plan.max_storage_mb == 0,
            "current_usage": size_info,
        }
    
    def evaluate_tenant(self, tenant_db: str, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Evalúa si un tenant necesita migración de plan por consumo de almacenamiento.
        
        Retorna:
        - status: "ok" | "warning" | "critical" | "exceeded"
        - recommendation: Plan recomendado (si aplica)
        - should_migrate: bool
        - usage_percent: % de uso del límite actual
        """
        if not customer_id:
            # Buscar customer_id desde subdomain
            customer = self.db.query(Customer).filter(
                Customer.subdomain == tenant_db
            ).first()
            if not customer:
                return {"error": f"No se encontró cliente para tenant '{tenant_db}'"}
            customer_id = customer.id
        
        info = self.get_customer_plan_and_usage(customer_id)
        
        if "error" in info:
            return info
        
        current_usage_mb = info["current_usage"]["total_size_mb"]
        plan_limit_mb = info["plan_storage_limit_mb"]
        unlimited = info["storage_unlimited"]
        
        # Si es ilimitado, no hay migración necesaria
        if unlimited:
            return {
                **info,
                "status": "ok",
                "usage_percent": 0,
                "should_migrate": False,
                "recommendation": None,
                "message": "Plan con almacenamiento ilimitado",
            }
        
        # Calcular % de uso
        usage_percent = (current_usage_mb / plan_limit_mb * 100) if plan_limit_mb > 0 else 0
        
        # Determinar estado
        status = "ok"
        if usage_percent >= ALERT_THRESHOLDS["exceeded"]:
            status = "exceeded"
        elif usage_percent >= ALERT_THRESHOLDS["critical"]:
            status = "critical"
        elif usage_percent >= ALERT_THRESHOLDS["warning"]:
            status = "warning"
        
        # Buscar plan recomendado
        recommended_plan = self._find_recommended_plan(current_usage_mb, info["plan_name"])
        
        should_migrate = status in ["critical", "exceeded"] and recommended_plan is not None
        
        message = self._get_status_message(status, usage_percent, current_usage_mb, plan_limit_mb)
        
        return {
            **info,
            "status": status,
            "usage_percent": round(usage_percent, 2),
            "should_migrate": should_migrate,
            "recommendation": recommended_plan,
            "message": message,
        }
    
    def _find_recommended_plan(self, current_usage_mb: float, current_plan_name: str) -> Optional[Dict[str, Any]]:
        """
        Encuentra el plan más apropiado basado en el uso actual.
        Busca el plan inmediatamente superior que pueda acomodar el uso actual + buffer (25%).
        """
        required_capacity = current_usage_mb * 1.25  # +25% de buffer
        
        # Obtener todos los planes activos ordenados por storage
        plans = self.db.query(Plan).filter(
            Plan.is_active == True,
            Plan.max_storage_mb > 0,  # Excluir ilimitados
        ).order_by(Plan.max_storage_mb.asc()).all()
        
        # Buscar el plan más pequeño que satisfaga la capacidad requerida
        for plan in plans:
            if plan.name != current_plan_name and plan.max_storage_mb >= required_capacity:
                return {
                    "plan_name": plan.name,
                    "plan_display": plan.display_name,
                    "storage_limit_mb": plan.max_storage_mb,
                    "base_price": plan.base_price,
                    "description": plan.description,
                }
        
        # Si no hay plan que lo acomode, recomendar ilimitado
        unlimited_plan = self.db.query(Plan).filter(
            Plan.is_active == True,
            Plan.max_storage_mb == 0,
        ).order_by(Plan.base_price.asc()).first()
        
        if unlimited_plan:
            return {
                "plan_name": unlimited_plan.name,
                "plan_display": unlimited_plan.display_name,
                "storage_limit_mb": 0,  # Ilimitado
                "base_price": unlimited_plan.base_price,
                "description": unlimited_plan.description,
            }
        
        return None
    
    def _get_status_message(self, status: str, usage_percent: float, current_mb: float, limit_mb: int) -> str:
        """Genera mensaje descriptivo del estado"""
        if status == "exceeded":
            return (
                f"⚠️ LÍMITE EXCEDIDO: {current_mb:.1f}MB / {limit_mb}MB ({usage_percent:.1f}%). "
                "Migración urgente requerida."
            )
        elif status == "critical":
            return (
                f"🔴 CRÍTICO: {current_mb:.1f}MB / {limit_mb}MB ({usage_percent:.1f}%). "
                "Se recomienda migrar pronto."
            )
        elif status == "warning":
            return (
                f"🟡 ADVERTENCIA: {current_mb:.1f}MB / {limit_mb}MB ({usage_percent:.1f}%). "
                "Considerar migración."
            )
        else:
            return (
                f"✅ OK: {current_mb:.1f}MB / {limit_mb}MB ({usage_percent:.1f}%). "
                "Uso dentro del límite."
            )
    
    def evaluate_all_tenants(self) -> List[Dict[str, Any]]:
        """
        Evalúa todos los tenants activos y retorna un reporte completo.
        """
        customers = self.db.query(Customer).filter(
            Customer.status == "active"
        ).all()
        
        results = []
        for customer in customers:
            try:
                if customer.subdomain:
                    evaluation = self.evaluate_tenant(customer.subdomain, customer.id)
                    results.append(evaluation)
            except Exception as e:
                logger.error(f"Error evaluando tenant {customer.subdomain}: {e}")
                results.append({
                    "customer_id": customer.id,
                    "company_name": customer.company_name,
                    "subdomain": customer.subdomain,
                    "error": str(e),
                })
        
        return results
    
    def auto_migrate_tenant(
        self,
        tenant_db: str,
        customer_id: Optional[int] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Ejecuta migración automática de plan si es necesario.
        
        Args:
            tenant_db: Nombre de la BD del tenant
            customer_id: ID del cliente (opcional)
            dry_run: Si True, solo simula (no ejecuta la migración)
        
        Returns:
            Resultado de la evaluación + acción tomada
        """
        evaluation = self.evaluate_tenant(tenant_db, customer_id)
        
        if "error" in evaluation:
            return evaluation
        
        if not evaluation["should_migrate"]:
            return {
                **evaluation,
                "migration_executed": False,
                "migration_reason": "No se requiere migración",
            }
        
        if dry_run:
            return {
                **evaluation,
                "migration_executed": False,
                "migration_reason": "Dry run - no se ejecutó la migración",
                "would_migrate_to": evaluation["recommendation"],
            }
        
        # Ejecutar migración real
        customer_id = evaluation["customer_id"]
        new_plan_name = evaluation["recommendation"]["plan_name"]
        
        try:
            # Actualizar suscripción
            sub = self.db.query(Subscription).filter(
                Subscription.customer_id == customer_id,
                Subscription.status == SubscriptionStatus.active,
            ).first()
            
            if sub:
                old_plan_name = sub.plan_name
                sub.plan_name = new_plan_name
                
                # Actualizar monthly_amount según el nuevo plan
                new_plan = self.db.query(Plan).filter(Plan.name == new_plan_name).first()
                if new_plan:
                    sub.monthly_amount = new_plan.calculate_monthly(sub.user_count or 1)
                
                self.db.commit()
                
                logger.info(
                    f"✅ Migración ejecutada: {evaluation['company_name']} "
                    f"({old_plan_name} → {new_plan_name})"
                )
                
                return {
                    **evaluation,
                    "migration_executed": True,
                    "old_plan": old_plan_name,
                    "new_plan": new_plan_name,
                    "migration_reason": f"Uso al {evaluation['usage_percent']:.1f}% del límite",
                }
            else:
                return {
                    **evaluation,
                    "migration_executed": False,
                    "error": "No se encontró suscripción activa",
                }
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error migrando tenant {tenant_db}: {e}")
            return {
                **evaluation,
                "migration_executed": False,
                "error": f"Error ejecutando migración: {str(e)}",
            }
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """
        Genera resumen ejecutivo de todos los tenants que requieren atención.
        """
        evaluations = self.evaluate_all_tenants()
        
        summary = {
            "total_tenants": len(evaluations),
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
            },
        }
        
        for eval_result in evaluations:
            if "error" in eval_result:
                continue
            
            status = eval_result.get("status", "ok")
            summary[status] += 1
            
            if eval_result.get("should_migrate"):
                summary["migration_recommended"] += 1
            
            summary["tenants_by_status"][status].append({
                "company_name": eval_result["company_name"],
                "subdomain": eval_result["subdomain"],
                "usage_percent": eval_result.get("usage_percent", 0),
                "current_plan": eval_result["plan_display"],
                "recommendation": eval_result.get("recommendation"),
            })
        
        return summary
