# 🔧 MÓDULO DE ADMINISTRACIÓN - SAJET ERP

## 📋 Índice
1. [Descripción General](#descripción-general)
2. [Servicios de Administración](#servicios-de-administración)
3. [API REST Endpoints](#api-rest-endpoints)
4. [Casos de Uso](#casos-de-uso)
5. [Seguridad](#seguridad)
6. [Instalación](#instalación)

---

## Descripción General

El módulo de administración proporciona a los admins de Sajet ERP herramientas completas para:

✅ **Gestión de SMTP** - Configurar credenciales de email sin redeploy  
✅ **Plantillas de Email** - Crear y editar templates HTML para todas las notificaciones  
✅ **Sistema de Alertas** - Monitorear almacenamiento y configurar thresholds  
✅ **Testing** - Validar credenciales y enviar emails de prueba  
✅ **Estadísticas** - Ver métricas de uso y efectividad  

**Ubicación:** `/opt/Erp_core/app/admin/`

**Componentes:**
- `AdminSmtpService` - Gestión SMTP
- `AdminEmailTemplateService` - Gestión de templates
- `AdminStorageAlertsService` - Configuración y monitoreo de alertas
- `admin_control_panel.py` - API REST endpoints

---

## Servicios de Administración

### 1. AdminSmtpService

**Archivo:** `app/services/admin_smtp_service.py` (400 líneas)

#### Responsabilidades:
- Leer/actualizar credenciales SMTP desde BD
- Probar conexión SMTP
- Enviar emails de prueba
- Obtener estado y histórico

#### Métodos principales:

```python
# Obtener configuración
config = service.get_smtp_config()
# Returns: {server, port, user, password, from_email, from_name}

# Obtener config sin exponer contraseña
config = service.get_smtp_config_display()
# Returns: config con password_masked

# Actualizar credencial individual
success, msg = service.update_smtp_credential(
    key="SMTP_SERVER",
    value="mail.example.com",
    updated_by="admin@example.com"
)

# Actualizar múltiples credenciales
all_success, results = service.update_smtp_config_batch(
    config={
        "SMTP_SERVER": "mail.example.com",
        "SMTP_PORT": "465",
        "SMTP_USER": "user@example.com",
        "SMTP_PASSWORD": "password"
    },
    updated_by="admin@example.com"
)

# Probar conexión SMTP
result = service.test_smtp_connection(test_email="admin@example.com")
# Returns: {success, server, port, connection_test, email_test, errors}

# Obtener estado
status = service.get_smtp_status()
# Returns: {configured, config, tests: {total, successful, failure_rate, last_test}}
```

---

### 2. AdminEmailTemplateService

**Archivo:** `app/services/admin_email_template_service.py` (600 líneas)

#### Responsabilidades:
- CRUD de plantillas HTML
- Versionado de templates
- Preview con variables reemplazadas
- Estadísticas de uso

#### Tipos de Template soportados:

```python
TEMPLATE_TYPES = {
    "storage_warning": "Alerta 75%",
    "storage_critical": "Alerta 90%",
    "storage_exceeded": "Alerta 100%+",
    "welcome": "Bienvenida cliente",
    "plan_upgrade": "Upgrade de plan",
    "invoice": "Factura",
    "password_reset": "Reset contraseña",
    "account_suspended": "Suspensión",
    "billing_alert": "Alerta facturación",
    "custom": "Personalizado"
}
```

#### Métodos principales:

```python
# Listar templates activos
templates = service.get_all_templates(only_active=True)

# Obtener template completo
template = service.get_template("storage_warning")
# Returns: {id, type, name, subject, html_body, tags, variables, version, ...}

# Crear template
success, msg, template_id = service.create_template(
    template_type="custom_alert",
    name="Alerta Personalizada",
    subject="Notificación: {{alert_type}}",
    html_body="<html>...</html>",
    updated_by="admin@example.com",
    tags=["alert"],
    variables={"alert_type": "string"}
)

# Actualizar template (incrementa versión)
success, msg = service.update_template(
    template_type="storage_warning",
    subject="Nuevo asunto",
    html_body="<html>...</html>",
    updated_by="admin@example.com"
)

# Preview con variables
preview = service.preview_template(
    "storage_warning",
    variables={
        "company_name": "ACME Corp",
        "usage_percent": "75.5",
        "limit_mb": "2048"
    }
)
# Returns: {html_rendered, subject_rendered, is_ready_to_send, missing_variables}

# Obtener estadísticas
stats = service.get_templates_stats()
# Returns: {total, active, usage_stats}
```

#### Estructura de Template:

```json
{
  "template_type": "storage_warning",
  "name": "Alerta de Almacenamiento - Warning",
  "subject": "🟡 Alerta de Almacenamiento - {{company_name}} ({{usage_percent}}%)",
  "html_body": "<html>...</html>",
  "preview_text": "Su almacenamiento alcanzó el 75% del límite",
  "variables": {
    "company_name": "string",
    "usage_percent": "float",
    "storage_limit_mb": "integer",
    "current_usage_mb": "float",
    "plan_type": "string"
  },
  "tags": ["alert", "storage", "warning"]
}
```

---

### 3. AdminStorageAlertsService

**Archivo:** `app/services/admin_storage_alerts_service.py` (550 líneas)

#### Responsabilidades:
- Configurar thresholds de alertas
- Ver y gestionar alertas activas
- Análisis de tendencias
- Estadísticas de alertas

#### Configuración de Thresholds:

```python
DEFAULT_THRESHOLDS = {
    "warning": 75,      # % de límite
    "critical": 90,     # % de límite
    "exceeded": 100     # % de límite
}
```

#### Métodos principales:

```python
# Obtener configuración actual
config = service.get_threshold_config()
# Returns: {threshold_warning, threshold_critical, threshold_exceeded, 
#           enable_email, enable_slack, check_interval_hours, ...}

# Actualizar thresholds
success, msg = service.update_threshold_config(
    warning=75,
    critical=90,
    exceeded=100,
    enable_email=True,
    enable_slack=False,
    check_interval_hours=24,
    updated_by="admin@example.com"
)

# Obtener alertas activas (sin resolver)
alerts = service.get_active_alerts(
    status="critical",  # Opcional: filtrar por status
    days=30  # Últimos N días
)
# Returns: List[{id, customer_id, company_name, status, usage_percent, ...}]

# Obtener estadísticas
stats = service.get_alert_stats()
# Returns: {
#   active_alerts: {total, by_status},
#   resolved_7days: int,
#   email_metrics: {total_alerts_30d, sent_30d, sent_rate_percent}
# }

# Resolver una alerta
success, msg = service.resolve_alert(
    alert_id=123,
    resolved_by="admin@example.com"
)

# Resolver múltiples alertas
resolved, errors = service.resolve_alerts_batch(
    alert_ids=[123, 124, 125],
    resolved_by="admin@example.com"
)

# Obtener tendencias de cliente
trends = service.get_customer_storage_trends(
    customer_id=10,
    days=30
)
# Returns: {customer_id, alerts_count, trend_growth_percent, data, recommendation}

# Habilitar notificaciones Slack
success, msg = service.enable_slack_notifications(
    slack_webhook="https://hooks.slack.com/services/...",
    updated_by="admin@example.com"
)
```

---

## API REST Endpoints

**Base URL:** `http://localhost:4443/api/admin/`  
**Autenticación:** `x-api-key: prov-key-2026-secure`  
**Rol requerido:** `admin`

### SMTP Management

#### GET `/smtp/config`
Obtiene configuración SMTP actual (sin contraseña)

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/smtp/config
```

**Response:**
```json
{
  "success": true,
  "data": {
    "server": "mail5010.site4now.net",
    "port": 465,
    "user": "no-reply@sajet.us",
    "password_masked": "****ajet.us",
    "from_email": "no-reply@sajet.us",
    "from_name": "Sajet ERP Alerts"
  }
}
```

#### POST `/smtp/config`
Actualiza múltiples credenciales SMTP

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{
       "SMTP_SERVER": "mail.example.com",
       "SMTP_PORT": "465",
       "SMTP_USER": "user@example.com",
       "SMTP_PASSWORD": "password"
     }' \
     http://localhost:4443/api/admin/smtp/config
```

#### PUT `/smtp/credential/{key}`
Actualiza una credencial individual

```bash
curl -X PUT -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{"value": "new-server.com"}' \
     http://localhost:4443/api/admin/smtp/credential/SMTP_SERVER
```

#### POST `/smtp/test`
Prueba conexión SMTP y opcionalmente envía email de prueba

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     "http://localhost:4443/api/admin/smtp/test?test_email=admin@example.com"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "server": "mail5010.site4now.net",
    "port": 465,
    "connection_test": "✓ Conexión SMTP exitosa",
    "email_test": "✓ Email de prueba enviado a admin@example.com",
    "has_credentials": true
  }
}
```

#### GET `/smtp/status`
Obtiene estado completo del SMTP

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/smtp/status
```

---

### Email Template Management

#### GET `/email-templates`
Lista todas las plantillas

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     "http://localhost:4443/api/admin/email-templates?only_active=true"
```

#### GET `/email-templates/{template_type}`
Obtiene una plantilla específica

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/email-templates/storage_warning
```

#### POST `/email-templates`
Crea nueva plantilla

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{
       "template_type": "custom_alert",
       "name": "Alerta Personalizada",
       "subject": "Notificación: {{alert_type}}",
       "html_body": "<html>...</html>",
       "tags": ["alert", "custom"]
     }' \
     http://localhost:4443/api/admin/email-templates
```

#### PUT `/email-templates/{template_type}`
Actualiza plantilla existente (incrementa versión)

```bash
curl -X PUT -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{
       "subject": "Nuevo asunto",
       "html_body": "<html>...</html>"
     }' \
     http://localhost:4443/api/admin/email-templates/storage_warning
```

#### POST `/email-templates/{template_type}/preview`
Vista previa con variables reemplazadas

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{
       "company_name": "ACME Corp",
       "usage_percent": "75.5",
       "storage_limit_mb": "2048"
     }' \
     http://localhost:4443/api/admin/email-templates/storage_warning/preview
```

#### POST `/email-templates/{template_type}/toggle`
Activa/desactiva una plantilla

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{"is_active": false}' \
     http://localhost:4443/api/admin/email-templates/storage_warning/toggle
```

#### GET `/email-templates/stats`
Estadísticas de uso de templates

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/email-templates/stats
```

---

### Storage Alerts Management

#### GET `/storage-alerts/config`
Obtiene configuración de thresholds

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/storage-alerts/config
```

**Response:**
```json
{
  "success": true,
  "data": {
    "threshold_warning": 75,
    "threshold_critical": 90,
    "threshold_exceeded": 100,
    "enable_email": true,
    "enable_slack": false,
    "email_on_resolution": true,
    "check_interval_hours": 24
  }
}
```

#### PUT `/storage-alerts/config`
Actualiza configuración de thresholds

```bash
curl -X PUT -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{
       "threshold_warning": 70,
       "threshold_critical": 85,
       "enable_slack": true,
       "check_interval_hours": 12
     }' \
     http://localhost:4443/api/admin/storage-alerts/config
```

#### GET `/storage-alerts/active`
Lista alertas activas (sin resolver)

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     "http://localhost:4443/api/admin/storage-alerts/active?status=critical&days=30"
```

#### GET `/storage-alerts/stats`
Estadísticas de alertas

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/storage-alerts/stats
```

#### POST `/storage-alerts/{alert_id}/resolve`
Marca una alerta como resuelta

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/storage-alerts/123/resolve
```

#### POST `/storage-alerts/resolve-batch`
Resuelve múltiples alertas

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '[123, 124, 125]' \
     http://localhost:4443/api/admin/storage-alerts/resolve-batch
```

#### GET `/storage-alerts/customer/{customer_id}/trends`
Historial y tendencias de almacenamiento de un cliente

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     "http://localhost:4443/api/admin/storage-alerts/customer/10/trends?days=30"
```

#### POST `/storage-alerts/slack/enable`
Habilita notificaciones Slack

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -H "Content-Type: application/json" \
     -d '{"slack_webhook": "https://hooks.slack.com/services/..."}' \
     http://localhost:4443/api/admin/storage-alerts/slack/enable
```

---

## Casos de Uso

### Caso 1: Admin cambiar servidor SMTP

```bash
# 1. Actualizar credenciales
curl -X PUT -H "x-api-key: prov-key-2026-secure" \
     -d '{"value": "new-mail-server.com"}' \
     http://localhost:4443/api/admin/smtp/credential/SMTP_SERVER

# 2. Probar conexión
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     "http://localhost:4443/api/admin/smtp/test?test_email=admin@example.com"

# 3. Verificar status
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/smtp/status
```

### Caso 2: Admin crear plantilla de email personalizada

```bash
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -d '{
       "template_type": "welcome_customer",
       "name": "Bienvenida Personalizada",
       "subject": "¡Bienvenido {{company_name}}!",
       "html_body": "<html>Contenido HTML...</html>",
       "tags": ["welcome", "onboarding"]
     }' \
     http://localhost:4443/api/admin/email-templates

# Preview antes de usar en producción
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -d '{"company_name": "ACME Corp"}' \
     http://localhost:4443/api/admin/email-templates/welcome_customer/preview
```

### Caso 3: Admin ajustar thresholds de alertas

```bash
# 1. Ver configuración actual
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/storage-alerts/config

# 2. Ajustar thresholds (ej: alertar más temprano)
curl -X PUT -H "x-api-key: prov-key-2026-secure" \
     -d '{
       "threshold_warning": 70,
       "threshold_critical": 85,
       "check_interval_hours": 12
     }' \
     http://localhost:4443/api/admin/storage-alerts/config

# 3. Ver alertas activas ahora
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/storage-alerts/active
```

### Caso 4: Admin resolver alertas en lote

```bash
# 1. Ver alertas activas
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/storage-alerts/active

# 2. Resolver múltiples alertas
curl -X POST -H "x-api-key: prov-key-2026-secure" \
     -d '[1, 2, 3, 4, 5]' \
     http://localhost:4443/api/admin/storage-alerts/resolve-batch
```

---

## Seguridad

### Autenticación y Autorización

- **Requiere:** HTTP Header `x-api-key: prov-key-2026-secure`
- **Rol:** Solo usuarios con rol `admin`
- **Auditoría:** Todos los cambios se registran con usuario y timestamp

### Manejo de Credenciales

- **Contraseñas** marcadas como `is_secret=true` en BD
- **Enmascaramiento:** API retorna contraseña enmascarada (últimos 4 caracteres)
- **Logs:** Credenciales nunca se logguean

### Validaciones

- **SMTP Port:** Solo números (0-65535)
- **SMTP Webhook:** Validación de formato Slack
- **Thresholds:** Solo valores 0-100
- **Emails:** Validación de formato

---

## Instalación

### 1. Copiar archivos de servicio

```bash
cp /opt/Erp_core/app/services/admin_smtp_service.py /var/www/html/app/services/
cp /opt/Erp_core/app/services/admin_email_template_service.py /var/www/html/app/services/
cp /opt/Erp_core/app/services/admin_storage_alerts_service.py /var/www/html/app/services/
```

### 2. Copiar rutas API

```bash
cp /opt/Erp_core/app/routes/admin_control_panel.py /var/www/html/app/routes/
```

### 3. Actualizar main.py

```python
# En app/main.py, agregar:
from .routes import admin_control_panel
app.include_router(admin_control_panel.router)
```

### 4. Reiniciar servicio

```bash
pkill -f "uvicorn app.main:app"
cd /var/www/html && nohup venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 4443 --workers 2 &
```

### 5. Verificar salud

```bash
curl -H "x-api-key: prov-key-2026-secure" \
     http://localhost:4443/api/admin/health
```

---

## 📊 Tablas de BD utilizadas

```sql
-- Configuración SMTP centralizada
system_config (category = 'email')
  - SMTP_SERVER, SMTP_PORT
  - SMTP_USER, SMTP_PASSWORD (is_secret=true)
  - SMTP_FROM_EMAIL, SMTP_FROM_NAME

-- Templates de email con versionado
email_templates
  - template_type (PK)
  - subject, html_body, text_body
  - version (auto-incrementa)
  - tags (JSON), variables (JSON)

-- Configuración de alertas
storage_alert_config
  - threshold_warning, threshold_critical, threshold_exceeded
  - enable_email_notifications, enable_slack_notifications
  - check_interval_hours

-- Alertas generadas y historial
storage_alerts
  - customer_id, status, usage_percent
  - email_sent, email_sent_at
  - resolved_at (NULL = no resuelta)

-- Logs de envío de emails
email_logs
  - template_type, recipient
  - success (bool)
  - error_message
```

---

**Status:** ✅ Completo y lista para deployment  
**Última actualización:** Marzo 1, 2026  
**Mantenedor:** Sajet ERP
