# 🔧 ADMIN PANEL API — Tests & Ejemplos de Uso

**Estado:** ✅ **OPERACIONAL**  
**Versión:** 1.0  
**Endpoint Base:** `http://localhost:4443/api/admin` (interno)  
**Autenticación:** API Key `x-api-key: prov-key-2026-secure` o Bearer Token  

---

## 📧 SMTP MANAGEMENT ENDPOINTS

### 1️⃣ GET /smtp/config — Obtener configuración SMTP

```bash
curl -X GET "http://localhost:4443/api/admin/smtp/config" \
  -H "x-api-key: prov-key-2026-secure"
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "from_email": "no-reply@sajet.us",
    "from_name": "Sajet ERP Alerts",
    "port": 465,
    "server": "mail5010.site4now.net",
    "user": "no-reply@sajet.us",
    "password_masked": "****bcd."
  }
}
```

### 2️⃣ POST /smtp/config — Actualizar credenciales SMTP

```bash
curl -X POST "http://localhost:4443/api/admin/smtp/config" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "SMTP_SERVER": "mail.example.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "new-user@example.com",
    "SMTP_PASSWORD": "new-password"
  }'
```

### 3️⃣ PUT /smtp/credential/{key} — Actualizar una credencial

```bash
curl -X PUT "http://localhost:4443/api/admin/smtp/credential/SMTP_FROM_NAME" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"value": "New Name"}'
```

### 4️⃣ POST /smtp/test — Probar conexión SMTP

```bash
# Sin enviar email
curl -X POST "http://localhost:4443/api/admin/smtp/test" \
  -H "x-api-key: prov-key-2026-secure"

# Enviando email de prueba
curl -X POST "http://localhost:4443/api/admin/smtp/test?test_email=soc@jeturing.com" \
  -H "x-api-key: prov-key-2026-secure"
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "connected": true,
    "message": "✅ Conexión SMTP exitosa",
    "details": "Server: mail5010.site4now.net:465"
  }
}
```

### 5️⃣ GET /smtp/status — Estado del SMTP

```bash
curl -X GET "http://localhost:4443/api/admin/smtp/status" \
  -H "x-api-key: prov-key-2026-secure"
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "configured": true,
    "config": {
      "server": "mail5010.site4now.net",
      "port": 465,
      "user": "no-reply@sajet.us"
    },
    "tests": {
      "total": 5,
      "successful": 5,
      "failure_rate": 0,
      "last_test": "2026-03-01T12:00:00"
    }
  }
}
```

---

## 📧 EMAIL TEMPLATE MANAGEMENT

### 6️⃣ GET /email-templates — Listar plantillas

```bash
curl -X GET "http://localhost:4443/api/admin/email-templates" \
  -H "x-api-key: prov-key-2026-secure"
```

**Respuesta:**
```json
{
  "success": true,
  "data": [],
  "count": 0
}
```

### 7️⃣ POST /email-templates — Crear nueva plantilla

```bash
curl -X POST "http://localhost:4443/api/admin/email-templates" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "template_type": "storage_warning",
    "name": "Alerta de Almacenamiento - Warning",
    "subject": "🟡 Alerta - {{company_name}} ({{usage_percent}}%)",
    "html_body": "<html><body><h1>Advertencia de Almacenamiento</h1><p>Su almacenamiento está al {{usage_percent}}%</p></body></html>",
    "preview_text": "Alerta de almacenamiento",
    "tags": ["alert", "storage"],
    "variables": {
      "company_name": "string",
      "usage_percent": "float"
    }
  }'
```

### 8️⃣ GET /email-templates/{type} — Obtener plantilla

```bash
curl -X GET "http://localhost:4443/api/admin/email-templates/storage_warning" \
  -H "x-api-key: prov-key-2026-secure"
```

### 9️⃣ PUT /email-templates/{type} — Actualizar plantilla

```bash
curl -X PUT "http://localhost:4443/api/admin/email-templates/storage_warning" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "🟡 Actualización: {{company_name}} ({{usage_percent}}%)",
    "html_body": "<html><body><h1>Actualización</h1></body></html>"
  }'
```

### 🔟 POST /email-templates/{type}/preview — Preview de plantilla

```bash
curl -X POST "http://localhost:4443/api/admin/email-templates/storage_warning/preview" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Sajet Corporation",
    "usage_percent": 87.5
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "data": {
    "subject": "🟡 Alerta - Sajet Corporation (87.5%)",
    "html_preview": "<html><body><h1>Advertencia...</h1></body></html>",
    "variables_used": ["company_name", "usage_percent"],
    "missing_variables": []
  }
}
```

### 1️⃣1️⃣ POST /email-templates/{type}/toggle — Activar/Desactivar

```bash
curl -X POST "http://localhost:4443/api/admin/email-templates/storage_warning/toggle" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### 1️⃣2️⃣ GET /email-templates/stats — Estadísticas de plantillas

```bash
curl -X GET "http://localhost:4443/api/admin/email-templates/stats" \
  -H "x-api-key: prov-key-2026-secure"
```

---

## 💾 STORAGE ALERTS MANAGEMENT

### 1️⃣3️⃣ GET /storage-alerts/config — Obtener configuración

```bash
curl -X GET "http://localhost:4443/api/admin/storage-alerts/config" \
  -H "x-api-key: prov-key-2026-secure"
```

**Respuesta:**
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
    "check_interval_hours": 24,
    "updated_at": "2026-03-01T20:57:03.174322",
    "updated_by": null
  }
}
```

### 1️⃣4️⃣ PUT /storage-alerts/config — Actualizar thresholds

```bash
curl -X PUT "http://localhost:4443/api/admin/storage-alerts/config" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold_warning": 70,
    "threshold_critical": 85,
    "threshold_exceeded": 100,
    "enable_email": true,
    "enable_slack": true
  }'
```

### 1️⃣5️⃣ GET /storage-alerts/active — Alertas activas

```bash
curl -X GET "http://localhost:4443/api/admin/storage-alerts/active" \
  -H "x-api-key: prov-key-2026-secure"

# Con filtros
curl -X GET "http://localhost:4443/api/admin/storage-alerts/active?status=critical&days=7" \
  -H "x-api-key: prov-key-2026-secure"
```

### 1️⃣6️⃣ GET /storage-alerts/stats — Estadísticas

```bash
curl -X GET "http://localhost:4443/api/admin/storage-alerts/stats" \
  -H "x-api-key: prov-key-2026-secure"
```

### 1️⃣7️⃣ POST /storage-alerts/{id}/resolve — Resolver alerta

```bash
curl -X POST "http://localhost:4443/api/admin/storage-alerts/123/resolve" \
  -H "x-api-key: prov-key-2026-secure"
```

### 1️⃣8️⃣ POST /storage-alerts/resolve-batch — Resolver múltiples

```bash
curl -X POST "http://localhost:4443/api/admin/storage-alerts/resolve-batch" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"alert_ids": [1, 2, 3, 4, 5]}'
```

### 1️⃣9️⃣ GET /storage-alerts/customer/{id}/trends — Tendencias de cliente

```bash
curl -X GET "http://localhost:4443/api/admin/storage-alerts/customer/1/trends?days=30" \
  -H "x-api-key: prov-key-2026-secure"
```

### 2️⃣0️⃣ POST /storage-alerts/slack/enable — Habilitar Slack

```bash
curl -X POST "http://localhost:4443/api/admin/storage-alerts/slack/enable" \
  -H "x-api-key: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"}'
```

---

## 🏥 HEALTH CHECK

### 2️⃣1️⃣ GET /health — Estado de servicios

```bash
curl -X GET "http://localhost:4443/api/admin/health" \
  -H "x-api-key: prov-key-2026-secure"
```

**Respuesta:**
```json
{
  "success": true,
  "status": "healthy",
  "services": {
    "smtp": "available",
    "email_templates": "available",
    "storage_alerts": "available"
  }
}
```

---

## 🔐 Autenticación

### Opción 1: API Key (recomendado para herramientas)

```bash
curl ... -H "x-api-key: prov-key-2026-secure"
```

### Opción 2: Bearer Token (para usuarios autenticados)

```bash
curl ... -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Opción 3: Cookie

```bash
curl ... --cookie "access_token=YOUR_TOKEN_HERE"
```

---

## ✅ Test Results Summary

| Endpoint | Método | Status | Respuesta |
|----------|--------|--------|-----------|
| `/health` | GET | ✅ 200 | Healthy |
| `/smtp/config` | GET | ✅ 200 | Config retornado |
| `/email-templates` | GET | ✅ 200 | Lista vacía (normal) |
| `/storage-alerts/config` | GET | ✅ 200 | Thresholds por defecto |

---

## 📝 Notas Importantes

1. **API Key**: `prov-key-2026-secure` es la clave de administrador temporal
2. **SMTP Credentials**: Almacenadas en `system_config` table con contraseña enmascarada
3. **Email Templates**: Base de datos vacía en primer inicio - crear templates según necesario
4. **Storage Alerts**: Configuración de thresholds lista para usar (75%, 90%, 100%)
5. **Autenticación**: Todos los endpoints requieren API key o token Bearer de admin

---

## 🚀 Próximos Pasos

1. ✅ Sistema admin panel operacional
2. ⏳ Crear plantillas de email para diferentes tipos de alertas
3. ⏳ Integrar con portal de clientes para visualización
4. ⏳ Webhook para eventos de actualización de configuración (opcional)
5. ⏳ Dashboard Svelte para gestión visual (opcional)

