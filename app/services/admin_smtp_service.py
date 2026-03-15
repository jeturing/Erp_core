"""
🔧 ADMIN SMTP SERVICE
═════════════════════════════════════════════════════════════════
Gestión administrativa de credenciales SMTP, testing y configuración centralizada.
Permite a los admins cambiar servidores sin redeploy de código.
═════════════════════════════════════════════════════════════════
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Tuple, Optional

from ..config import get_smtp_config, smtp_is_configured

logger = logging.getLogger("admin_smtp_service")
ENV_ONLY_MESSAGE = "SMTP se administra solo desde .env.production y requiere reinicio de erp-core"


class AdminSmtpService:
    """
    Servicio para inspección y testing de SMTP.
    La configuración es de solo lectura y se consume desde .env.production.
    """
    
    SMTP_CONFIG_KEYS = {
        "SMTP_SERVER": "Servidor SMTP",
        "SMTP_PORT": "Puerto SMTP",
        "SMTP_USER": "Usuario para autenticación",
        "SMTP_PASSWORD": "Contraseña (secreto)",
        "SMTP_FROM_EMAIL": "Email del remitente",
        "SMTP_FROM_NAME": "Nombre del remitente"
    }
    
    def __init__(self, db: Session):
        """Inicializa el servicio con conexión a BD."""
        self.db = db
    
    # ═══════════════════════════════════════════════════════════════════
    # 📋 GET — Leer configuración SMTP desde BD
    # ═══════════════════════════════════════════════════════════════════
    
    def get_smtp_config(self) -> Dict[str, any]:
        """
        Obtiene la configuración SMTP completa desde el .env activo.
        
        Returns:
            Dict con keys: server, port, user, password, from_email, from_name
        """
        return get_smtp_config()
    
    def get_smtp_config_display(self) -> Dict[str, any]:
        """
        Retorna config SMTP pero con PASSWORD enmascarada para UI.
        """
        return get_smtp_config(mask_secret=True)
    
    # ═══════════════════════════════════════════════════════════════════
    # ✏️ UPDATE — Actualizar credenciales SMTP
    # ═══════════════════════════════════════════════════════════════════
    
    def update_smtp_credential(self, key: str, value: str, updated_by: str) -> Tuple[bool, str]:
        """
        Actualiza una credencial SMTP individual en system_config.
        
        Args:
            key: Una de las claves SMTP_* permitidas
            value: Nuevo valor
            updated_by: Usuario que realiza la actualización
        
        Returns:
            (success: bool, message: str)
        """
        return False, f"❌ {ENV_ONLY_MESSAGE}"
    
    def update_smtp_config_batch(self, config: Dict[str, str], updated_by: str) -> Tuple[bool, Dict]:
        """
        Actualiza múltiples credenciales SMTP en una transacción.
        
        Args:
            config: Dict con keys SMTP_* y valores
            updated_by: Usuario que realiza la actualización
        
        Returns:
            (all_success: bool, results: Dict[key] -> (success, message))
        """
        results = {}
        all_success = True
        
        for key, value in config.items():
            success, message = self.update_smtp_credential(key, value, updated_by)
            results[key] = {"success": success, "message": message}
            if not success:
                all_success = False
        
        return all_success, results
    
    # ═══════════════════════════════════════════════════════════════════
    # 🧪 TEST — Probar conexión y credenciales
    # ═══════════════════════════════════════════════════════════════════
    
    def test_smtp_connection(self, test_email: str = None) -> Dict[str, any]:
        """
        Prueba la conexión SMTP actual y envía email de prueba.
        
        Args:
            test_email: Email destino para prueba. Si no se da, solo prueba conexión.
        
        Returns:
            Dict con resultados detallados
        """
        config = self.get_smtp_config()
        result = {
            "success": False,
            "server": config.get("server"),
            "port": config.get("port"),
            "user": config.get("user"),
            "has_credentials": bool(config.get("user") and config.get("password")),
            "connection_test": None,
            "email_test": None,
            "errors": []
        }
        
        # Validar config básica
        if not config.get("server"):
            result["errors"].append("❌ SMTP_SERVER no configurado")
            return result
        
        if not config.get("user") or not config.get("password"):
            result["errors"].append("❌ Credenciales (user/password) no configuradas")
            return result
        
        # Test 1: Conexión SMTP
        try:
            with smtplib.SMTP_SSL(config["server"], config["port"], timeout=10) as server:
                server.login(config["user"], config["password"])
                result["connection_test"] = "✓ Conexión SMTP exitosa"
        except smtplib.SMTPAuthenticationError as e:
            result["errors"].append(f"❌ Error de autenticación: {str(e)}")
            result["connection_test"] = "❌ Autenticación fallida"
            return result
        except smtplib.SMTPException as e:
            result["errors"].append(f"❌ Error SMTP: {str(e)}")
            result["connection_test"] = f"❌ {str(e)}"
            return result
        except Exception as e:
            result["errors"].append(f"❌ Error de conexión: {str(e)}")
            result["connection_test"] = f"❌ {str(e)}"
            return result
        
        result["success"] = True
        
        # Test 2: Enviar email de prueba (si se proporciona email)
        if test_email:
            result["email_test"] = self._send_test_email(
                test_email, config
            )
        
        return result
    
    def _send_test_email(self, to_email: str, config: Dict) -> str:
        """
        Envía un email de prueba.
        """
        try:
            subject = "✅ TEST - Configuración SMTP Sajet ERP"
            body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background: #4F46E5; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                        .content {{ background: #f5f5f5; padding: 20px; border-radius: 0 0 8px 8px; }}
                        .success {{ color: #22c55e; font-weight: bold; }}
                        .details {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #22c55e; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>✅ SMTP Configurado Correctamente</h1>
                        </div>
                        <div class="content">
                            <p class="success">¡La configuración SMTP de Sajet ERP está funcionando correctamente!</p>
                            
                            <div class="details">
                                <p><strong>Servidor:</strong> {config.get('server')}</p>
                                <p><strong>Puerto:</strong> {config.get('port')}</p>
                                <p><strong>Usuario:</strong> {config.get('user')}</p>
                                <p><strong>De (From):</strong> {config.get('from_name')} &lt;{config.get('from_email')}&gt;</p>
                            </div>
                            
                            <p>Este email fue enviado exitosamente para confirmar que el sistema de notificaciones está listo para enviar alertas a tus clientes.</p>
                            
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                            
                            <p style="color: #666; font-size: 12px;">
                                Email generado automáticamente por Sajet ERP.
                                No responder a este email.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{config['from_name']} <{config['from_email']}>"
            msg["To"] = to_email
            msg.attach(MIMEText(body, "html"))
            
            with smtplib.SMTP_SSL(config["server"], config["port"]) as server:
                server.login(config["user"], config["password"])
                server.send_message(msg)
            
            return f"✓ Email de prueba enviado exitosamente a {to_email}"
        except Exception as e:
            return f"❌ Error enviando email: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════════════
    # 📊 STATUS — Estado de SMTP y historial
    # ═══════════════════════════════════════════════════════════════════
    
    def get_smtp_status(self) -> Dict[str, any]:
        """
        Obtiene el estado actual del SMTP y últimos tests.
        """
        config = self.get_smtp_config_display()
        
        try:
            # Obtener últimos tests de email_logs
            query = """
                SELECT COUNT(*), 
                       SUM(CASE WHEN success = true THEN 1 ELSE 0 END),
                       MAX(created_at)
                FROM email_logs 
                WHERE category = 'test'
                LIMIT 1
            """
            result = self.db.execute(text(query)).first()
            
            total_tests = result[0] or 0
            successful_tests = result[1] or 0
            last_test = result[2]
            
            return {
                "configured": smtp_is_configured(),
                "config": config,
                "tests": {
                    "total": total_tests,
                    "successful": successful_tests,
                    "failure_rate": 0 if total_tests == 0 else round(
                        ((total_tests - successful_tests) / total_tests) * 100, 2
                    ),
                    "last_test": last_test.isoformat() if last_test else None
                }
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo SMTP status: {e}")
            return {
                "configured": smtp_is_configured(),
                "config": config,
                "tests": {"error": str(e)}
            }
