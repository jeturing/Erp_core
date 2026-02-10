# Validación de Parámetros - Guía Completa

## Overview

El servicio `odoo_provisioner.py` ahora incluye validación exhaustiva de todos los parámetros, eliminando datos hardcodeados y usando variables de entorno configurables.

## Validaciones Implementadas

### 1. **Subdomain** (requerido)

**Reglas:**
- Solo alfanuméricos y guiones
- Máximo 63 caracteres
- No puede empezar o terminar con guión
- No puede ser palabras reservadas (admin, api, www, mail, ftp, ns, root)

**Ejemplos válidos:**
```
✅ acme
✅ client-123
✅ my-company
✅ project-a
```

**Ejemplos inválidos:**
```
❌ -invalid (empieza con guión)
❌ invalid- (termina con guión)
❌ ADMIN (reservado)
❌ very-long-subdomain-name-that-exceeds-sixty-three-characters-maximum
❌ client@123 (caracteres especiales)
```

**Error:**
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Subdomain solo permite alfanuméricos y guiones..."
}
```

### 2. **Email** (requerido)

**Reglas:**
- Formato de email válido RFC 5322
- Máximo 254 caracteres
- Debe contener @ y dominio válido

**Ejemplos válidos:**
```
✅ admin@acme.com
✅ user.name+tag@example.co.uk
✅ john_doe@company.org
```

**Ejemplos inválidos:**
```
❌ notanemail
❌ @example.com
❌ user@
❌ user..name@example.com
```

**Error:**
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Email inválido: invalid@"
}
```

### 3. **Company Name** (requerido)

**Reglas:**
- String no vacío
- Mínimo 2 caracteres
- Máximo 255 caracteres
- Permite caracteres especiales (espacios, números, etc.)

**Ejemplos válidos:**
```
✅ Acme Corporation
✅ Tech Company Ltd.
✅ My Business 123
```

**Ejemplos inválidos:**
```
❌ A (muy corto)
❌ "" (vacío)
❌ (256 caracteres o más)
```

**Error:**
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Company name mínimo 2 caracteres"
}
```

### 4. **Container IP** (opcional, usa DEFAULT_CONTAINER_IP)

**Reglas:**
- IPv4 válida (formato x.x.x.x)
- Cada octeto entre 0-255
- O IPv6 válida
- Requerida si se omite DEFAULT_CONTAINER_IP

**Ejemplos válidos:**
```
✅ 172.16.16.105
✅ 192.168.1.100
✅ 10.0.0.1
✅ ::1 (IPv6)
```

**Ejemplos inválidos:**
```
❌ 256.1.1.1 (octeto > 255)
❌ 192.168.1 (incompleta)
❌ 192.168.1.256 (último octeto > 255)
❌ invalid-ip
```

**Error:**
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "IP address inválida: 256.1.1.1"
}
```

### 5. **Local Port** (opcional, usa DEFAULT_LOCAL_PORT)

**Reglas:**
- Entero entre 1 y 65535
- Puerto estándar Odoo: 8069
- Requerido si se omite DEFAULT_LOCAL_PORT

**Ejemplos válidos:**
```
✅ 8069 (Odoo default)
✅ 8070
✅ 9000
```

**Ejemplos inválidos:**
```
❌ 0 (menor que 1)
❌ 65536 (mayor que 65535)
❌ "8069" (string, debe ser int)
❌ -1
```

**Error:**
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Port debe estar entre 1 y 65535, recibido: 65536"
}
```

## Validaciones de Configuración

### Variables Requeridas en .env

El servicio valida que TODAS estas variables estén configuradas:

```bash
# REQUERIDAS
LXC_CONTAINER_ID=105
DOMAIN=sajet.us
CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant_enhanced.sh
DEFAULT_CONTAINER_IP=172.16.16.105
DEFAULT_LOCAL_PORT=8069

# OPCIONALES
ENABLE_CLOUDFLARE=true
```

**Si falta alguna variable, error:**
```json
{
  "success": false,
  "error_type": "provisioning_error",
  "error": "Variable LXC_CONTAINER_ID no configurada en .env"
}
```

## Flujo de Validación Completo

```
1. Obtener config desde .env
   ├─ LXC_CONTAINER_ID
   ├─ DOMAIN
   ├─ CREATE_TENANT_SCRIPT
   ├─ DEFAULT_CONTAINER_IP
   ├─ DEFAULT_LOCAL_PORT
   └─ ENABLE_CLOUDFLARE
   
2. Validar variables de config
   ├─ Si falta algo → Error ProvisioningError
   └─ Si válido → Continuar

3. Aplicar defaults (si no se proporcionan valores)
   ├─ container_ip = None → usar DEFAULT_CONTAINER_IP
   ├─ local_port = None → usar DEFAULT_LOCAL_PORT
   └─ create_tunnel = None → usar ENABLE_CLOUDFLARE

4. Validar parámetros de entrada
   ├─ _validate_subdomain(subdomain)
   ├─ _validate_email(admin_email)
   ├─ _validate_company_name(company_name)
   ├─ _validate_ip_address(container_ip)
   ├─ _validate_port(local_port)
   └─ Validar tipos de subscription_id y create_tunnel

5. Si validación falla → Retornar error
   
6. Si validación OK → Provisionar
```

## Ejemplo de Uso Completo

### Request Válido
```python
result = await provision_tenant(
    subdomain="acme",
    admin_email="admin@acme.com",
    company_name="Acme Corporation",
    subscription_id=5,
    # container_ip, local_port, create_tunnel usan defaults
)
```

Response:
```json
{
  "success": true,
  "database": "acme",
  "hostname": "acme.sajet.us",
  "url": "https://acme.sajet.us",
  "container_ip": "172.16.16.105",
  "local_port": 8069,
  "subscription_id": 5,
  "created_at": "2026-01-31T10:30:45.123456",
  "tunnel": {
    "tunnel_id": "abc123",
    "tunnel_name": "acme-tunnel",
    "domain": "acme.sajet.us",
    "status": "active"
  }
}
```

### Request Inválido #1 - Email mal formado
```python
result = await provision_tenant(
    subdomain="acme",
    admin_email="invalid-email",  # ❌ Sin @
    company_name="Acme Corp"
)
```

Response:
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Email inválido: invalid-email"
}
```

### Request Inválido #2 - Subdomain reservado
```python
result = await provision_tenant(
    subdomain="admin",  # ❌ Reservado
    admin_email="admin@acme.com",
    company_name="Acme Corp"
)
```

Response:
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Subdomain 'admin' está reservado"
}
```

### Request Inválido #3 - Puerto fuera de rango
```python
result = await provision_tenant(
    subdomain="acme",
    admin_email="admin@acme.com",
    company_name="Acme Corp",
    local_port=99999  # ❌ > 65535
)
```

Response:
```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Port debe estar entre 1 y 65535, recibido: 99999"
}
```

## Logging

Cada paso se loguea con niveles INFO/WARNING/ERROR:

```
INFO: Validando parámetros para tenant: acme
INFO: ✅ Validación completada para acme
INFO: 📦 Aprovisionando tenant: acme on 172.16.16.105:8069
INFO: 🌐 Creando Cloudflare tunnel para acme.sajet.us
INFO: ✅ Suscripción 5 actualizada a active
INFO: ✅ Tenant aprovisionado exitosamente: https://acme.sajet.us

O en caso de error:
ERROR: ❌ Error de validación: Email inválido: invalid@
```

## Archivos Relacionados

- **Servicio:** `app/services/odoo_provisioner.py`
- **Configuración:** `.env.example`
- **Modelos:** `app/models/database.py`

## Variables de Entorno Requeridas

Ver `.env.example` sección "TENANT PROVISIONING":

```bash
# Requeridas
LXC_CONTAINER_ID=105
DOMAIN=sajet.us
CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant_enhanced.sh
DEFAULT_CONTAINER_IP=172.16.16.105
DEFAULT_LOCAL_PORT=8069

# Opcional
ENABLE_CLOUDFLARE=true
```

