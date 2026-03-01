"""
Storage Alert Service — Gestión de alertas de almacenamiento
Envía notificaciones a clientes cuando se acercan a los límites
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..models.database import StorageAlert, Customer, Plan, StorageAlertStatus
from ..config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL
from .plan_migration_service import PlanMigrationService

logger = logging.getLogger(__name__)


class StorageAlertService:
    """Servicio para generar alertas de almacenamiento y enviar notificaciones"""
    
    def __init__(self, db: Session):
        self.db = db
        self.migration_service = PlanMigrationService(db)
        
        # Cargar configuración SMTP desde BD o usar fallbacks
        self.smtp_config = self._load_smtp_config()
    
    def _load_smtp_config(self) -> Dict[str, Any]:
        """
        Carga configuración SMTP desde la tabla system_config.
        Si no existe en BD, usa variables de entorno como fallback.
        """
        config = {
            "server": SMTP_SERVER,
            "port": SMTP_PORT,
            "user": SMTP_USER,
            "password": SMTP_PASSWORD,
            "from_email": SMTP_FROM_EMAIL,
            "from_name": "Sajet ERP Alerts"
        }
        
        try:
            # Buscar configuración en la BD
            result = self.db.execute(text("""
                SELECT key, value FROM system_config 
                WHERE category = 'email' AND key IN ('SMTP_SERVER', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'SMTP_FROM_EMAIL', 'SMTP_FROM_NAME')
            """))
            
            db_config = {}
            for row in result.fetchall():
                key, value = row
                db_config[key] = value
            
            # Mapear configuración BD a variables del servicio
            if 'SMTP_SERVER' in db_config:
                config['server'] = db_config['SMTP_SERVER']
            if 'SMTP_PORT' in db_config:
                try:
                    config['port'] = int(db_config['SMTP_PORT'])
                except ValueError:
                    logger.warning(f"SMTP_PORT inválido en BD: {db_config['SMTP_PORT']}, usando {SMTP_PORT}")
            if 'SMTP_USER' in db_config:
                config['user'] = db_config['SMTP_USER']
            if 'SMTP_PASSWORD' in db_config:
                config['password'] = db_config['SMTP_PASSWORD']
            if 'SMTP_FROM_EMAIL' in db_config:
                config['from_email'] = db_config['SMTP_FROM_EMAIL']
            if 'SMTP_FROM_NAME' in db_config:
                config['from_name'] = db_config['SMTP_FROM_NAME']
            
            logger.info(f"✓ Configuración SMTP cargada desde BD: {config['server']}:{config['port']}")
            
        except Exception as e:
            logger.warning(f"No se pudo cargar SMTP desde BD: {e}. Usando fallbacks de config.py")
        
        return config
    
    def evaluate_and_alert(self, customer_id: int, subdomain: str) -> Dict[str, Any]:
        """
        Evalúa el consumo de un tenant y genera alerta si necesario.
        
        Returns:
            {
                "customer_id": int,
                "subdomain": str,
                "status": "ok" | "warning" | "critical" | "exceeded",
                "usage_percent": float,
                "alert_created": bool,
                "email_sent": bool,
                "message": str
            }
        """
        # Evaluación de consumo
        evaluation = self.migration_service.evaluate_tenant(subdomain, customer_id)
        
        if "error" in evaluation:
            return {
                "customer_id": customer_id,
                "subdomain": subdomain,
                "error": evaluation["error"],
                "alert_created": False,
            }
        
        # Obtener customer y plan actual
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {
                "customer_id": customer_id,
                "subdomain": subdomain,
                "error": "Customer not found",
                "alert_created": False,
            }
        
        status = evaluation["status"]
        usage_percent = evaluation["usage_percent"]
        current_usage_mb = evaluation["current_usage"]["total_size_mb"]
        storage_limit_mb = evaluation["plan_storage_limit_mb"]
        
        # Convertir status a enum solo si NO es "ok"
        # "ok" significa que el uso está dentro de los límites - no es un estado de alerta
        status_enum = None
        if status in ["warning", "critical", "exceeded"]:
            try:
                status_enum = StorageAlertStatus[status]
            except KeyError:
                logger.error(f"Invalid status value: {status}")
                status_enum = None
        
        # Verificar si hay alerta previa para este nivel
        if status_enum:
            existing_alert = self.db.query(StorageAlert).filter(
                StorageAlert.customer_id == customer_id,
                StorageAlert.status == status_enum,
                StorageAlert.resolved_at.is_(None)
            ).first()
        else:
            existing_alert = None
        
        if existing_alert:
            # Actualizar alerta existente
            existing_alert.usage_percent = usage_percent
            existing_alert.current_usage_mb = current_usage_mb
            self.db.commit()
            return {
                "customer_id": customer_id,
                "subdomain": subdomain,
                "status": status,
                "usage_percent": usage_percent,
                "alert_created": False,
                "email_sent": existing_alert.email_sent,
                "message": f"Alerta existente de {status} actualizada"
            }
        
        # Crear nueva alerta si status lo requiere
        if status in ["warning", "critical", "exceeded"] and status_enum:
            alert = StorageAlert(
                customer_id=customer_id,
                status=status_enum,
                usage_percent=usage_percent,
                storage_limit_mb=storage_limit_mb,
                current_usage_mb=current_usage_mb,
                email_recipient=customer.contact_email or customer.email
            )
            self.db.add(alert)
            self.db.commit()
            
            # Enviar email
            email_sent = self._send_alert_email(
                customer=customer,
                alert=alert,
                subdomain=subdomain,
                evaluation=evaluation
            )
            
            alert.email_sent = email_sent
            if email_sent:
                alert.email_sent_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "customer_id": customer_id,
                "subdomain": subdomain,
                "status": status,
                "usage_percent": usage_percent,
                "alert_created": True,
                "email_sent": email_sent,
                "message": self._get_alert_message(status, usage_percent)
            }
        else:
            # Status OK - resolver alertas previas si existen
            self.db.query(StorageAlert).filter(
                StorageAlert.customer_id == customer_id,
                StorageAlert.resolved_at.is_(None)
            ).update({"resolved_at": datetime.utcnow()})
            self.db.commit()
            
            return {
                "customer_id": customer_id,
                "subdomain": subdomain,
                "status": status,
                "usage_percent": usage_percent,
                "alert_created": False,
                "email_sent": False,
                "message": "✅ Uso dentro del límite"
            }
    
    def evaluate_all_with_alerts(self) -> Dict[str, Any]:
        """
        Evalúa todos los tenants activos y genera alertas.
        
        Returns:
            {
                "total_evaluated": int,
                "total_alerts": int,
                "by_status": {
                    "ok": int,
                    "warning": int,
                    "critical": int,
                    "exceeded": int
                },
                "results": [...]
            }
        """
        customers = self.db.query(Customer).filter(
            Customer.status == "active"
        ).all()
        
        results = []
        counts = {
            "ok": 0,
            "warning": 0,
            "critical": 0,
            "exceeded": 0
        }
        
        for customer in customers:
            result = self.evaluate_and_alert(customer.id, customer.subdomain)
            results.append(result)
            
            if "error" not in result:
                status = result["status"]
                counts[status] += 1
        
        return {
            "total_evaluated": len(customers),
            "total_alerts": sum(1 for r in results if r.get("alert_created")),
            "emails_sent": sum(1 for r in results if r.get("email_sent")),
            "by_status": counts,
            "results": results
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Obtiene todas las alertas activas"""
        alerts = self.db.query(StorageAlert).filter(
            StorageAlert.resolved_at.is_(None)
        ).all()
        
        return [
            {
                "id": alert.id,
                "customer_id": alert.customer_id,
                "customer_name": alert.customer.company_name,
                "subdomain": alert.customer.subdomain,
                "status": alert.status.value if hasattr(alert.status, 'value') else alert.status,
                "usage_percent": alert.usage_percent,
                "storage_limit_mb": alert.storage_limit_mb,
                "current_usage_mb": alert.current_usage_mb,
                "email_sent": alert.email_sent,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in alerts
        ]
    
    def get_customer_alerts(self, customer_id: int) -> List[Dict[str, Any]]:
        """Obtiene alertas activas de un cliente específico"""
        alerts = self.db.query(StorageAlert).filter(
            StorageAlert.customer_id == customer_id,
            StorageAlert.resolved_at.is_(None)
        ).all()
        
        return [
            {
                "id": alert.id,
                "status": alert.status.value if hasattr(alert.status, 'value') else alert.status,
                "usage_percent": alert.usage_percent,
                "storage_limit_mb": alert.storage_limit_mb,
                "current_usage_mb": alert.current_usage_mb,
                "created_at": alert.created_at.isoformat(),
                "message": self._get_alert_message(alert.status.value if hasattr(alert.status, 'value') else alert.status, alert.usage_percent)
            }
            for alert in alerts
        ]
    
    def _get_alert_message(self, status: str, usage_percent: float) -> str:
        """Genera mensaje de alerta basado en status"""
        messages = {
            "warning": f"🟡 WARNING: {usage_percent:.1f}% del límite de almacenamiento. Se recomienda upgrade pronto.",
            "critical": f"🔴 CRITICAL: {usage_percent:.1f}% del límite. Se recomienda upgrade inmediato.",
            "exceeded": f"⚠️  EXCEDIDO: {usage_percent:.1f}% del límite. Se requiere upgrade urgente.",
        }
        return messages.get(status, "")
    
    def _send_alert_email(
        self,
        customer: Customer,
        alert: StorageAlert,
        subdomain: str,
        evaluation: Dict[str, Any]
    ) -> bool:
        """
        Envía email de alerta al cliente.
        
        Returns:
            True si fue enviado exitosamente
        """
        try:
            recipient = alert.email_recipient
            if not recipient:
                logger.warning(f"No email configured for customer {customer.id}")
                return False
            
            # Obtener plan actual
            plan = self.db.query(Plan).filter(Plan.name == evaluation["plan_name"]).first()
            plan_display = evaluation["plan_display"]
            
            # Asunto
            subject = self._get_email_subject(alert.status, subdomain)
            
            # Cuerpo del email
            body = self._generate_email_body(
                customer=customer,
                alert=alert,
                subdomain=subdomain,
                evaluation=evaluation,
                plan_display=plan_display
            )
            
            # Enviar email
            self._send_smtp_email(
                to=recipient,
                subject=subject,
                body=body
            )
            
            logger.info(f"Alert email sent to {recipient} for customer {customer.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
            return False
    
    def _get_email_subject(self, status: str, subdomain: str) -> str:
        """Genera asunto del email basado en status"""
        subjects = {
            "warning": f"⚠️  Alerta de Almacenamiento: {subdomain} - 75% del límite",
            "critical": f"🔴 Alerta Crítica: {subdomain} - 90% del límite",
            "exceeded": f"⚠️  URGENTE: {subdomain} ha superado el límite de almacenamiento",
        }
        return subjects.get(status, "Alerta de Almacenamiento")
    
    def _generate_email_body(
        self,
        customer: Customer,
        alert: StorageAlert,
        subdomain: str,
        evaluation: Dict[str, Any],
        plan_display: str
    ) -> str:
        """Genera cuerpo del email HTML"""
        current_usage = evaluation["current_usage"]["total_size_mb"]
        storage_limit = alert.storage_limit_mb
        usage_percent = alert.usage_percent
        
        # Recomendación
        recommendation = evaluation.get("recommendation", {})
        recommended_plan = recommendation.get("plan_display", "Enterprise")
        recommended_price = recommendation.get("base_price", "N/A")
        
        # Convertir enum a string si es necesario
        status_value = alert.status.value if hasattr(alert.status, 'value') else alert.status
        
        # Determinar mensaje según status
        if status_value == "warning":
            alert_title = "⚠️  Alerta de Almacenamiento - Advértencia (75%)"
            alert_text = "Su almacenamiento se está acercando al límite. Se recomienda actualizar el plan pronto para evitar interrupciones."
            color = "#FFA500"
        elif status_value == "critical":
            alert_title = "🔴 Alerta Crítica de Almacenamiento (90%)"
            alert_text = "Su almacenamiento está muy cerca del límite. Se recomienda actualizar el plan inmediatamente."
            color = "#FF6B6B"
        else:  # exceeded
            alert_title = "⚠️  URGENTE - Límite de Almacenamiento Superado"
            alert_text = "Ha superado el límite de almacenamiento de su plan actual. Debe actualizar inmediatamente para continuar operando."
            color = "#CC0000"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .section {{ margin: 15px 0; }}
        .stats {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .stat-item {{ margin: 10px 0; }}
        .stat-label {{ font-weight: bold; }}
        .progress-bar {{ width: 100%; height: 20px; background-color: #ddd; border-radius: 5px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background-color: {color}; width: {usage_percent:.0f}%; }}
        .recommendation {{ background-color: #E8F4F8; padding: 15px; border-left: 4px solid #0088CC; margin: 15px 0; }}
        .button {{ background-color: #0088CC; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 0; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>{alert_title}</h2>
        </div>
        
        <div class="section">
            <p>Hola <strong>{customer.company_name}</strong>,</p>
            <p>{alert_text}</p>
        </div>
        
        <div class="stats">
            <h3>📊 Detalles de su Almacenamiento</h3>
            
            <div class="stat-item">
                <span class="stat-label">Tenant:</span> {subdomain}.sajet.us
            </div>
            
            <div class="stat-item">
                <span class="stat-label">Plan Actual:</span> {plan_display}
            </div>
            
            <div class="stat-item">
                <span class="stat-label">Uso:</span> {current_usage:.1f} MB / {storage_limit} MB
            </div>
            
            <div class="stat-item">
                <span class="stat-label">Porcentaje de Uso:</span> {usage_percent:.1f}%
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        </div>
        
        <div class="recommendation">
            <h3>💡 Plan Recomendado</h3>
            <p>
                Para asegurar operaciones continuas sin interrupciones, recomendamos 
                actualizar su plan a <strong>{recommended_plan}</strong> 
                que ofrece más almacenamiento y mejor rendimiento.
            </p>
            <p><strong>Precio base:</strong> ${recommended_price}/mes</p>
            <a href="https://sajet.us/dashboard/plans" class="button">Actualizar Plan</a>
        </div>
        
        <div class="section">
            <h3>❓ ¿Qué puedo hacer?</h3>
            <ul>
                <li><strong>Opción 1 (Recomendada):</strong> Actualizar a un plan superior con más almacenamiento</li>
                <li><strong>Opción 2:</strong> Limpiar archivos innecesarios de su sistema</li>
                <li><strong>Opción 3:</strong> Contactar al equipo de soporte para asesoramiento personalizado</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Este es un email automático. Por favor no responda a este mensaje.</p>
            <p>Si tiene preguntas, contáctenos en support@sajet.us</p>
            <p>© 2026 Sajet Inc. Todos los derechos reservados.</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_body
    
    def _send_smtp_email(self, to: str, subject: str, body: str) -> bool:
        """Envía email mediante SMTP usando configuración desde BD"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_config['from_email']
            msg["To"] = to
            
            # Adjuntar cuerpo HTML
            msg.attach(MIMEText(body, "html"))
            
            # Enviar usando configuración desde BD
            with smtplib.SMTP_SSL(self.smtp_config['server'], self.smtp_config['port']) as server:
                if self.smtp_config['user'] and self.smtp_config['password']:
                    server.login(self.smtp_config['user'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"✓ Email enviado a {to} via {self.smtp_config['server']}:{self.smtp_config['port']}")
            return True
        except Exception as e:
            logger.error(f"❌ Error SMTP: {e}")
            return False
