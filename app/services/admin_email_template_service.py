"""
📧 ADMIN EMAIL TEMPLATE SERVICE
═════════════════════════════════════════════════════════════════
Gestión de plantillas HTML para emails del sistema.
Permite a admins crear, editar y previsualizar templates sin código.
═════════════════════════════════════════════════════════════════
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger("admin_email_service")


class AdminEmailTemplateService:
    """
    Servicio para gestión de plantillas de email.
    Soporta templates para alertas, bienvenida, notificaciones, etc.
    """
    
    TEMPLATE_TYPES = {
        "storage_warning": "Alerta de almacenamiento - Warning (75%)",
        "storage_critical": "Alerta de almacenamiento - Critical (90%)",
        "storage_exceeded": "Alerta de almacenamiento - Exceeded (100%+)",
        "welcome": "Email de bienvenida a nuevo cliente",
        "plan_upgrade": "Notificación de upgrade de plan",
        "invoice": "Factura / Recibo de pago",
        "password_reset": "Recuperación de contraseña",
        "account_suspended": "Notificación de suspensión",
        "billing_alert": "Alerta de facturación",
        "custom": "Plantilla personalizada del cliente"
    }
    
    def __init__(self, db: Session):
        """Inicializa el servicio con conexión a BD."""
        self.db = db
        self._ensure_templates_table()
    
    def _ensure_templates_table(self):
        """Crea la tabla de templates si no existe."""
        try:
            create_table = """
            CREATE TABLE IF NOT EXISTS email_templates (
                id SERIAL PRIMARY KEY,
                template_type VARCHAR(100) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                subject VARCHAR(500) NOT NULL,
                html_body TEXT NOT NULL,
                text_body TEXT,
                preview_text VARCHAR(500),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(150),
                version INT DEFAULT 1,
                tags JSON DEFAULT '[]',
                variables JSON DEFAULT '{}',
                CONSTRAINT chk_template_type CHECK (template_type != '')
            );
            
            CREATE INDEX IF NOT EXISTS idx_templates_type ON email_templates(template_type);
            CREATE INDEX IF NOT EXISTS idx_templates_active ON email_templates(is_active);
            """
            self.db.execute(text(create_table))
            self.db.commit()
        except Exception as e:
            logger.warning(f"⚠️ Tabla email_templates ya existe: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 📋 GET — Leer templates
    # ═══════════════════════════════════════════════════════════════════
    
    def get_all_templates(self, only_active: bool = True) -> List[Dict]:
        """
        Obtiene todas las plantillas de email.
        
        Args:
            only_active: Si True, solo plantillas activas
        
        Returns:
            Lista de templates con metadata
        """
        try:
            query = "SELECT * FROM email_templates"
            if only_active:
                query += " WHERE is_active = true"
            query += " ORDER BY template_type"
            
            result = self.db.execute(text(query)).fetchall()
            
            templates = []
            for row in result:
                templates.append({
                    "id": row[0],
                    "template_type": row[1],
                    "name": row[2],
                    "subject": row[3],
                    "preview_text": row[8],
                    "is_active": row[7],
                    "updated_at": row[11].isoformat() if row[11] else None,
                    "version": row[13]
                })
            
            return templates
        except Exception as e:
            logger.error(f"❌ Error listando templates: {e}")
            return []
    
    def get_template(self, template_type: str) -> Optional[Dict]:
        """
        Obtiene una plantilla específica con todo su contenido.
        
        Args:
            template_type: Tipo de plantilla (storage_warning, welcome, etc)
        
        Returns:
            Dict con template completo o None si no existe
        """
        try:
            query = "SELECT * FROM email_templates WHERE template_type = :type AND is_active = true LIMIT 1"
            result = self.db.execute(text(query), {"type": template_type}).first()
            
            if not result:
                return None
            
            return {
                "id": result[0],
                "template_type": result[1],
                "name": result[2],
                "subject": result[3],
                "html_body": result[4],
                "text_body": result[5],
                "preview_text": result[8],
                "is_active": result[7],
                "created_at": result[9].isoformat() if result[9] else None,
                "updated_at": result[10].isoformat() if result[10] else None,
                "updated_by": result[11],
                "version": result[12],
                "tags": result[13] or [],
                "variables": result[14] or {}
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo template {template_type}: {e}")
            return None
    
    def get_template_with_variables(self, template_type: str, variables: Dict) -> Optional[Dict]:
        """
        Obtiene un template y retorna información sobre variables requeridas.
        Útil para preview antes de enviar.
        
        Args:
            template_type: Tipo de plantilla
            variables: Dict con variables para reemplazar
        
        Returns:
            Dict con template renderizado y metadata
        """
        template = self.get_template(template_type)
        if not template:
            return None
        
        # Extraer variables requeridas del template ({{variable}})
        import re
        pattern = r'\{\{(\w+)\}\}'
        required_vars = set(re.findall(pattern, template["html_body"]))
        missing_vars = required_vars - set(variables.keys())
        
        # Renderizar template
        html_rendered = template["html_body"]
        subject_rendered = template["subject"]
        
        for var, value in variables.items():
            html_rendered = html_rendered.replace(f"{{{{{var}}}}}", str(value))
            subject_rendered = subject_rendered.replace(f"{{{{{var}}}}}", str(value))
        
        return {
            **template,
            "html_rendered": html_rendered,
            "subject_rendered": subject_rendered,
            "required_variables": list(required_vars),
            "missing_variables": list(missing_vars),
            "is_ready_to_send": len(missing_vars) == 0
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # ✏️ CREATE/UPDATE — Crear o actualizar templates
    # ═══════════════════════════════════════════════════════════════════
    
    def create_template(
        self, 
        template_type: str,
        name: str,
        subject: str,
        html_body: str,
        updated_by: str,
        text_body: str = None,
        preview_text: str = None,
        tags: List[str] = None,
        variables: Dict = None
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Crea una nueva plantilla de email.
        
        Returns:
            (success: bool, message: str, template_id: Optional[int])
        """
        # Validaciones
        if not template_type or template_type.strip() == "":
            return False, "❌ template_type no puede estar vacío", None
        
        if not name or name.strip() == "":
            return False, "❌ name no puede estar vacío", None
        
        if not subject or subject.strip() == "":
            return False, "❌ subject no puede estar vacío", None
        
        if not html_body or html_body.strip() == "":
            return False, "❌ html_body no puede estar vacío", None
        
        try:
            # Verificar que no exista
            check = self.db.execute(
                text("SELECT id FROM email_templates WHERE template_type = :type"),
                {"type": template_type}
            ).first()
            
            if check:
                return False, f"❌ Ya existe template con type '{template_type}'", None
            
            # Insertar
            insert_query = """
                INSERT INTO email_templates 
                (template_type, name, subject, html_body, text_body, preview_text, 
                 updated_by, tags, variables)
                VALUES 
                (:type, :name, :subject, :html, :text, :preview, :user, :tags, :vars)
                RETURNING id
            """
            
            result = self.db.execute(text(insert_query), {
                "type": template_type,
                "name": name,
                "subject": subject,
                "html": html_body,
                "text": text_body or "",
                "preview": preview_text or name[:100],
                "user": updated_by,
                "tags": json.dumps(tags or []),
                "vars": json.dumps(variables or {})
            })
            
            template_id = result.scalar()
            self.db.commit()
            
            logger.info(f"✅ Template '{template_type}' creado por {updated_by}")
            return True, f"✅ Template creado exitosamente", template_id
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creando template: {e}")
            return False, f"❌ Error: {str(e)}", None
    
    def update_template(
        self,
        template_type: str,
        name: str = None,
        subject: str = None,
        html_body: str = None,
        text_body: str = None,
        preview_text: str = None,
        updated_by: str = None,
        tags: List[str] = None,
        variables: Dict = None
    ) -> Tuple[bool, str]:
        """
        Actualiza una plantilla existente (incrementa versión).
        
        Args:
            template_type: Identificador del template
            **kwargs: Campos a actualizar
            updated_by: Usuario que actualiza
        
        Returns:
            (success: bool, message: str)
        """
        try:
            # Verificar que existe
            template = self.get_template(template_type)
            if not template:
                return False, f"❌ Template '{template_type}' no existe"
            
            # Preparar updates
            updates = {}
            if name is not None:
                updates["name"] = name
            if subject is not None:
                updates["subject"] = subject
            if html_body is not None:
                updates["html_body"] = html_body
            if text_body is not None:
                updates["text_body"] = text_body
            if preview_text is not None:
                updates["preview_text"] = preview_text
            if updated_by is not None:
                updates["updated_by"] = updated_by
            if tags is not None:
                updates["tags"] = json.dumps(tags)
            if variables is not None:
                updates["variables"] = json.dumps(variables)
            
            if not updates:
                return False, "❌ No hay cambios para realizar"
            
            # Incrementar versión y actualizar
            updates["version"] = template["version"] + 1
            updates["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
            
            # Construir query dinámicamente
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            update_query = f"""
                UPDATE email_templates 
                SET {set_clause}
                WHERE template_type = :type
            """
            
            updates["type"] = template_type
            self.db.execute(text(update_query), updates)
            self.db.commit()
            
            logger.info(f"✅ Template '{template_type}' actualizado a v{updates['version']} por {updated_by}")
            return True, f"✅ Template actualizado a versión {updates['version']}"
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error actualizando template: {e}")
            return False, f"❌ Error: {str(e)}"
    
    def toggle_template_active(self, template_type: str, is_active: bool, updated_by: str) -> Tuple[bool, str]:
        """
        Activa o desactiva una plantilla.
        """
        try:
            query = """
                UPDATE email_templates 
                SET is_active = :active, updated_by = :user, updated_at = :now
                WHERE template_type = :type
            """
            self.db.execute(text(query), {
                "active": is_active,
                "user": updated_by,
                "now": datetime.now(timezone.utc).replace(tzinfo=None),
                "type": template_type
            })
            self.db.commit()
            
            status = "activada" if is_active else "desactivada"
            logger.info(f"✅ Template '{template_type}' {status} por {updated_by}")
            return True, f"✅ Template {status}"
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error toggling template: {e}")
            return False, f"❌ Error: {str(e)}"
    
    # ═══════════════════════════════════════════════════════════════════
    # 🧪 PREVIEW — Previsualizar antes de usar
    # ═══════════════════════════════════════════════════════════════════
    
    def preview_template(self, template_type: str, variables: Dict = None) -> Dict:
        """
        Genera una vista previa del template con variables reemplazadas.
        
        Returns:
            Dict con html_rendered, subject_rendered y variables info
        """
        result = self.get_template_with_variables(template_type, variables or {})
        
        if not result:
            return {
                "error": f"Template '{template_type}' no encontrado",
                "success": False
            }
        
        return {
            "success": True,
            "template_type": template_type,
            "name": result["name"],
            "subject": result["subject_rendered"],
            "html": result["html_rendered"],
            "preview_text": result["preview_text"],
            "is_ready_to_send": result["is_ready_to_send"],
            "required_variables": result["required_variables"],
            "missing_variables": result["missing_variables"]
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # 📊 STATS — Estadísticas de templates
    # ═══════════════════════════════════════════════════════════════════
    
    def get_templates_stats(self) -> Dict:
        """
        Obtiene estadísticas de uso de templates.
        """
        try:
            # Contar templates
            count_query = "SELECT COUNT(*) FROM email_templates"
            total = self.db.execute(text(count_query)).scalar() or 0
            
            # Activos vs inactivos
            active_query = "SELECT COUNT(*) FROM email_templates WHERE is_active = true"
            active = self.db.execute(text(active_query)).scalar() or 0
            
            # Logs de envío
            logs_query = """
                SELECT template_type, COUNT(*), 
                       SUM(CASE WHEN success = true THEN 1 ELSE 0 END)
                FROM email_logs
                GROUP BY template_type
                ORDER BY COUNT(*) DESC
            """
            logs = self.db.execute(text(logs_query)).fetchall()
            
            usage_stats = []
            for row in logs:
                template_type, total_sent, successful = row
                failure_rate = 0 if total_sent == 0 else round(
                    ((total_sent - successful) / total_sent) * 100, 2
                )
                usage_stats.append({
                    "template_type": template_type,
                    "total_sent": total_sent,
                    "successful": successful,
                    "failure_rate": failure_rate
                })
            
            return {
                "total_templates": total,
                "active_templates": active,
                "inactive_templates": total - active,
                "usage_stats": usage_stats
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo stats: {e}")
            return {"error": str(e)}
