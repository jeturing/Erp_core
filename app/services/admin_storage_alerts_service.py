"""
💾 ADMIN STORAGE ALERTS SERVICE
═════════════════════════════════════════════════════════════════
Gestión administrativa del sistema de alertas de almacenamiento.
Permite configurar thresholds, ver historial y gestionar alertas activas.
═════════════════════════════════════════════════════════════════
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("admin_storage_service")


class AdminStorageAlertsService:
    """
    Servicio para administración de alertas de almacenamiento.
    Gestiona configuración de thresholds, histórico y estado de alertas.
    """
    
    DEFAULT_THRESHOLDS = {
        "warning": 75,      # % de límite antes de enviar alerta warning
        "critical": 90,     # % de límite antes de enviar alerta critical
        "exceeded": 100     # % de límite antes de enviar alerta exceeded
    }
    
    def __init__(self, db: Session):
        """Inicializa el servicio con conexión a BD."""
        self.db = db
        self._ensure_config_table()
    
    def _ensure_config_table(self):
        """Asegura que exista la tabla de configuración de alertas."""
        try:
            create_table = """
            CREATE TABLE IF NOT EXISTS storage_alert_config (
                id SERIAL PRIMARY KEY,
                config_key VARCHAR(100) NOT NULL UNIQUE,
                threshold_warning INT DEFAULT 75,
                threshold_critical INT DEFAULT 90,
                threshold_exceeded INT DEFAULT 100,
                enable_email_notifications BOOLEAN DEFAULT true,
                enable_slack_notifications BOOLEAN DEFAULT false,
                email_on_resolution BOOLEAN DEFAULT true,
                check_interval_hours INT DEFAULT 24,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(150)
            );
            
            CREATE INDEX IF NOT EXISTS idx_alert_config_key ON storage_alert_config(config_key);
            """
            self.db.execute(text(create_table))
            self.db.commit()
        except Exception as e:
            logger.warning(f"⚠️ Tabla storage_alert_config ya existe: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # ⚙️ CONFIGURATION — Gestionar configuración de thresholds
    # ═══════════════════════════════════════════════════════════════════
    
    def get_threshold_config(self) -> Dict[str, any]:
        """
        Obtiene la configuración actual de thresholds de alertas.
        
        Returns:
            Dict con configuración de warning, critical, exceeded
        """
        try:
            query = "SELECT * FROM storage_alert_config WHERE config_key = 'default' LIMIT 1"
            result = self.db.execute(text(query)).first()
            
            if not result:
                # Crear configuración por defecto si no existe
                self._create_default_config()
                result = self.db.execute(text(query)).first()
            
            return {
                "threshold_warning": result[2],
                "threshold_critical": result[3],
                "threshold_exceeded": result[4],
                "enable_email": result[5],
                "enable_slack": result[6],
                "email_on_resolution": result[7],
                "check_interval_hours": result[8],
                "updated_at": result[11].isoformat() if result[11] else None,
                "updated_by": result[12]
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo config: {e}")
            return self.DEFAULT_THRESHOLDS
    
    def _create_default_config(self):
        """Crea la configuración por defecto de thresholds."""
        try:
            insert_query = """
                INSERT INTO storage_alert_config 
                (config_key, threshold_warning, threshold_critical, threshold_exceeded, 
                 enable_email_notifications, check_interval_hours)
                VALUES ('default', 75, 90, 100, true, 24)
                ON CONFLICT (config_key) DO NOTHING
            """
            self.db.execute(text(insert_query))
            self.db.commit()
        except Exception as e:
            logger.error(f"❌ Error creando default config: {e}")
    
    def update_threshold_config(
        self,
        warning: int = None,
        critical: int = None,
        exceeded: int = None,
        enable_email: bool = None,
        enable_slack: bool = None,
        email_on_resolution: bool = None,
        check_interval_hours: int = None,
        updated_by: str = None
    ) -> Tuple[bool, str]:
        """
        Actualiza la configuración de thresholds de alertas.
        
        Args:
            warning: Porcentaje para alerta warning (0-100)
            critical: Porcentaje para alerta critical (0-100)
            exceeded: Porcentaje para alerta exceeded (0-100)
            enable_email: Habilitar emails
            enable_slack: Habilitar Slack
            email_on_resolution: Enviar email cuando se resuelve
            check_interval_hours: Intervalo de chequeo en horas
            updated_by: Usuario que actualiza
        
        Returns:
            (success: bool, message: str)
        """
        # Validaciones
        if warning is not None and not (0 <= warning <= 100):
            return False, "❌ threshold_warning debe estar entre 0 y 100"
        
        if critical is not None and not (0 <= critical <= 100):
            return False, "❌ threshold_critical debe estar entre 0 y 100"
        
        if exceeded is not None and not (0 <= exceeded <= 100):
            return False, "❌ threshold_exceeded debe estar entre 0 y 100"
        
        try:
            # Construir updates dinámicamente
            updates = {}
            if warning is not None:
                updates["threshold_warning"] = warning
            if critical is not None:
                updates["threshold_critical"] = critical
            if exceeded is not None:
                updates["threshold_exceeded"] = exceeded
            if enable_email is not None:
                updates["enable_email_notifications"] = enable_email
            if enable_slack is not None:
                updates["enable_slack_notifications"] = enable_slack
            if email_on_resolution is not None:
                updates["email_on_resolution"] = email_on_resolution
            if check_interval_hours is not None:
                updates["check_interval_hours"] = check_interval_hours
            if updated_by is not None:
                updates["updated_by"] = updated_by
            
            updates["updated_at"] = datetime.utcnow()
            
            if not updates:
                return False, "❌ No hay cambios para realizar"
            
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            update_query = f"""
                UPDATE storage_alert_config 
                SET {set_clause}
                WHERE config_key = 'default'
            """
            
            self.db.execute(text(update_query), updates)
            self.db.commit()
            
            logger.info(f"✅ Configuración de alertas actualizada por {updated_by}")
            return True, "✅ Configuración actualizada exitosamente"
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error actualizando config: {e}")
            return False, f"❌ Error: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════════════
    # 📊 ALERTS — Ver y gestionar alertas activas
    # ═══════════════════════════════════════════════════════════════════
    
    def get_active_alerts(self, status: str = None, days: int = 30) -> List[Dict]:
        """
        Obtiene todas las alertas activas sin resolver.
        
        Args:
            status: Filtrar por status (warning, critical, exceeded)
            days: Mostrar alertas creadas en los últimos N días
        
        Returns:
            Lista de alertas activas
        """
        try:
            query = """
                SELECT 
                    a.id, a.customer_id, c.company_name, a.status, 
                    a.usage_percent, a.storage_limit_mb, a.current_usage_mb,
                    a.email_sent, a.email_sent_at, a.created_at
                FROM storage_alerts a
                JOIN customers c ON a.customer_id = c.id
                WHERE a.resolved_at IS NULL
                    AND a.created_at >= NOW() - INTERVAL '{{}} days'
            """.format(days)
            
            if status:
                query += " AND a.status = :status"
            
            query += " ORDER BY a.created_at DESC"
            
            params = {"status": status} if status else {}
            result = self.db.execute(text(query), params).fetchall()
            
            alerts = []
            for row in result:
                alerts.append({
                    "id": row[0],
                    "customer_id": row[1],
                    "company_name": row[2],
                    "status": row[3],
                    "usage_percent": round(row[4], 2),
                    "storage_limit_mb": row[5],
                    "current_usage_mb": round(row[6], 2),
                    "email_sent": row[7],
                    "email_sent_at": row[8].isoformat() if row[8] else None,
                    "created_at": row[9].isoformat() if row[9] else None
                })
            
            return alerts
        except Exception as e:
            logger.error(f"❌ Error obteniendo alertas: {e}")
            return []
    
    def get_alert_stats(self) -> Dict[str, any]:
        """
        Obtiene estadísticas de alertas (resumen ejecutivo).
        """
        try:
            # Total alertas activas
            active_query = "SELECT COUNT(*) FROM storage_alerts WHERE resolved_at IS NULL"
            active_total = self.db.execute(text(active_query)).scalar() or 0
            
            # Por status
            status_query = """
                SELECT status, COUNT(*) 
                FROM storage_alerts 
                WHERE resolved_at IS NULL
                GROUP BY status
            """
            status_counts = {}
            for row in self.db.execute(text(status_query)).fetchall():
                status_counts[row[0]] = row[1]
            
            # Alertas resueltas en los últimos 7 días
            resolved_query = """
                SELECT COUNT(*) 
                FROM storage_alerts 
                WHERE resolved_at IS NOT NULL 
                  AND resolved_at >= NOW() - INTERVAL '7 days'
            """
            resolved_7d = self.db.execute(text(resolved_query)).scalar() or 0
            
            # Email sent rate (últimas 30 días)
            email_query = """
                SELECT COUNT(*), SUM(CASE WHEN email_sent = true THEN 1 ELSE 0 END)
                FROM storage_alerts
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """
            email_result = self.db.execute(text(email_query)).first()
            total_30d = email_result[0] or 0
            sent_30d = email_result[1] or 0
            email_sent_rate = 0 if total_30d == 0 else round((sent_30d / total_30d) * 100, 2)
            
            return {
                "active_alerts": {
                    "total": active_total,
                    "by_status": {
                        "warning": status_counts.get("warning", 0),
                        "critical": status_counts.get("critical", 0),
                        "exceeded": status_counts.get("exceeded", 0)
                    }
                },
                "resolved_7days": resolved_7d,
                "email_metrics": {
                    "total_alerts_30d": total_30d,
                    "sent_30d": sent_30d,
                    "sent_rate_percent": email_sent_rate
                }
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo stats: {e}")
            return {}
    
    def resolve_alert(self, alert_id: int, resolved_by: str = None) -> Tuple[bool, str]:
        """
        Marca una alerta como resuelta.
        
        Args:
            alert_id: ID de la alerta a resolver
            resolved_by: Usuario que resuelve
        
        Returns:
            (success: bool, message: str)
        """
        try:
            query = """
                UPDATE storage_alerts 
                SET resolved_at = :now, 
                    updated_by = :user
                WHERE id = :id
            """
            self.db.execute(text(query), {
                "now": datetime.utcnow(),
                "user": resolved_by or "system",
                "id": alert_id
            })
            self.db.commit()
            
            logger.info(f"✅ Alerta {alert_id} resuelta por {resolved_by}")
            return True, f"✅ Alerta {alert_id} marcada como resuelta"
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error resolviendo alerta: {e}")
            return False, f"❌ Error: {str(e)}"
    
    def resolve_alerts_batch(self, alert_ids: List[int], resolved_by: str = None) -> Tuple[int, List[str]]:
        """
        Resuelve múltiples alertas en lote.
        
        Returns:
            (count_resolved: int, errors: List[str])
        """
        resolved = 0
        errors = []
        
        for alert_id in alert_ids:
            success, msg = self.resolve_alert(alert_id, resolved_by)
            if success:
                resolved += 1
            else:
                errors.append(msg)
        
        return resolved, errors
    
    # ═══════════════════════════════════════════════════════════════════
    # 📈 TRENDS — Análisis de tendencias de almacenamiento
    # ═══════════════════════════════════════════════════════════════════
    
    def get_customer_storage_trends(self, customer_id: int, days: int = 30) -> Dict:
        """
        Obtiene historial de almacenamiento y tendencias de un cliente.
        """
        try:
            query = """
                SELECT created_at, current_usage_mb, storage_limit_mb, status
                FROM storage_alerts
                WHERE customer_id = :cid
                  AND created_at >= NOW() - INTERVAL '{{}} days'
                ORDER BY created_at ASC
            """.format(days)
            
            result = self.db.execute(text(query), {"cid": customer_id}).fetchall()
            
            alerts_data = []
            for row in result:
                alerts_data.append({
                    "date": row[0].isoformat() if row[0] else None,
                    "usage_mb": round(row[1], 2),
                    "limit_mb": row[2],
                    "status": row[3]
                })
            
            # Calcular tendencia (% crecimiento)
            if len(alerts_data) >= 2:
                first_usage = alerts_data[0]["usage_mb"]
                last_usage = alerts_data[-1]["usage_mb"]
                growth_percent = round(((last_usage - first_usage) / first_usage) * 100, 2) if first_usage > 0 else 0
            else:
                growth_percent = 0
            
            return {
                "customer_id": customer_id,
                "alerts_count": len(alerts_data),
                "trend_growth_percent": growth_percent,
                "data": alerts_data,
                "recommendation": self._get_storage_recommendation(growth_percent, 
                    alerts_data[-1]["usage_mb"] if alerts_data else 0,
                    alerts_data[-1]["limit_mb"] if alerts_data else 0)
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo trends: {e}")
            return {}
    
    def _get_storage_recommendation(self, growth_percent: float, current_usage: float, limit: float) -> str:
        """Genera recomendación de upgrade basada en uso y crecimiento."""
        if growth_percent > 50:
            return "🔴 URGENTE: Crecimiento de >50%. Upgrade inmediato recomendado."
        elif growth_percent > 20:
            return "🟠 Crecimiento significativo. Considere upgrade en próximas semanas."
        elif current_usage >= limit * 0.9:
            return "🟡 Aproximándose a límite. Evalúe necesidades de almacenamiento."
        else:
            return "✅ Almacenamiento adecuado. Sin recomendaciones de cambio."
    
    # ═══════════════════════════════════════════════════════════════════
    # 🔔 NOTIFICATIONS — Configurar notificaciones
    # ═══════════════════════════════════════════════════════════════════
    
    def enable_slack_notifications(self, slack_webhook: str, updated_by: str) -> Tuple[bool, str]:
        """
        Habilita notificaciones por Slack para alertas.
        
        Args:
            slack_webhook: URL del webhook de Slack
            updated_by: Usuario que configura
        
        Returns:
            (success: bool, message: str)
        """
        if not slack_webhook or "hooks.slack.com" not in slack_webhook:
            return False, "❌ webhook de Slack inválido"
        
        try:
            # Guardar webhook en system_config
            insert_query = """
                INSERT INTO system_config (key, value, category, is_secret, description, updated_by)
                VALUES ('SLACK_WEBHOOK_STORAGE_ALERTS', :webhook, 'notifications', true, 
                        'Webhook para alertas de almacenamiento', :user)
                ON CONFLICT (key) DO UPDATE SET value = :webhook, updated_by = :user, updated_at = NOW()
            """
            self.db.execute(text(insert_query), {
                "webhook": slack_webhook,
                "user": updated_by
            })
            
            # Habilitar en config
            config_query = """
                UPDATE storage_alert_config 
                SET enable_slack_notifications = true, updated_by = :user
                WHERE config_key = 'default'
            """
            self.db.execute(text(config_query), {"user": updated_by})
            
            self.db.commit()
            logger.info(f"✅ Slack notifications habilitadas por {updated_by}")
            return True, "✅ Notificaciones por Slack habilitadas"
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error habilitando Slack: {e}")
            return False, f"❌ Error: {str(e)}"
