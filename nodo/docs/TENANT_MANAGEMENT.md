# API de Gestión de Tenants - Guía Completa

## Descripción

El sistema de gestión de tenants permite:
- ✅ Crear nuevos tenants (instancias de Odoo)
- ✅ Cambiar la contraseña del administrador
- ✅ Suspender/reactivar tenants (para falta de pago)
- ✅ Listar y consultar tenants
- ✅ Gestión automática de DNS en Cloudflare

## Endpoints

### 1. Listar Tenants

**GET** `/api/tenants`

Obtiene la lista de todos los tenants en el sistema.

```bash
curl -X GET http://localhost:4443/api/tenants
```

**Respuesta:**
```json
{
  "items": [
    {
      "id": 1,
      "company_name": "Acme Corp",
      "email": "admin@acme.com",
      "subdomain": "acme",
      "plan": "pro",
      "status": "active",
      "tunnel_active": true,
      "created_at": "2026-01-28T10:00:00Z",
      "node": "Node 1 (LXC 105)"
    }
  ],
  "total": 1
}
```

### 2. Crear Tenant (Provisioning)

**POST** `/api/provisioning/tenant`

Crea una nueva instancia de Odoo.

```bash
curl -X POST http://localhost:4443/api/provisioning/tenant \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "admin_password": "Techeels2026!",
    "domain": "sajet.us",
    "server": "primary",
    "template_db": "tcs"
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "subdomain": "techeels",
  "url": "https://techeels.sajet.us",
  "database": "techeels",
  "dns_created": true
}
```

**Parámetros:**
- `subdomain` (required): Nombre del subdominio (3-30 caracteres)
- `admin_password` (optional): Contraseña del admin (default: "admin")
- `domain` (optional): Dominio base (default: "sajet.us")
- `server` (optional): Servidor Odoo (default: "primary")
- `template_db` (optional): BD plantilla (default: "tcs")

### 3. Cambiar Contraseña Admin

**PUT** `/api/provisioning/tenant/password`

Cambia la contraseña del usuario administrador de un tenant.

```bash
curl -X PUT http://localhost:4443/api/provisioning/tenant/password \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "new_password": "MuevaClaveSegura2026!"
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "subdomain": "techeels",
  "message": "Contraseña actualizada exitosamente"
}
```

**Parámetros:**
- `subdomain` (required): Subdominio del tenant
- `new_password` (required): Nueva contraseña (mínimo 6 caracteres)
- `server` (optional): Servidor destino (default: "primary")

### 4. Suspender Tenant

**PUT** `/api/provisioning/tenant/suspend`

Suspende un tenant bloqueando el acceso de todos los usuarios (excepto admin).
Se utiliza cuando hay falta de pago.

```bash
curl -X PUT http://localhost:4443/api/provisioning/tenant/suspend \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "suspend": true,
    "reason": "Suspensión por falta de pago"
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "subdomain": "techeels",
  "suspended": true,
  "reason": "Suspensión por falta de pago",
  "message": "Tenant suspendido exitosamente"
}
```

**Parámetros:**
- `subdomain` (required): Subdominio del tenant
- `suspend` (required): true para suspender, false para reactivar
- `reason` (optional): Razón de la suspensión
- `server` (optional): Servidor destino (default: "primary")

### 5. Reactivar Tenant

**PUT** `/api/provisioning/tenant/suspend`

Reactiva un tenant suspendido permitiendo nuevamente el acceso.

```bash
curl -X PUT http://localhost:4443/api/provisioning/tenant/suspend \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "suspend": false
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "subdomain": "techeels",
  "suspended": false,
  "message": "Tenant reactivado exitosamente"
}
```

### 6. Eliminar Tenant

**DELETE** `/api/provisioning/tenant`

Elimina completamente un tenant y su base de datos.

```bash
curl -X DELETE http://localhost:4443/api/provisioning/tenant \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels"
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "database_deleted": true,
  "dns_deleted": true
}
```

## Flujo de Suspensión por Falta de Pago

Cuando un cliente no paga su suscripción:

```
1. Sistema detecta falta de pago
2. API suspende el tenant (PUT /tenant/suspend)
3. BD: res_users.active = false (usuarios no pueden acceder)
4. Admin puede reactivar cuando se pague
5. Sistema registra razón en ir_config_parameter
```

## Autorización

Todos los endpoints (excepto GET /api/tenants) requieren:

```
Header: X-API-KEY: prov-key-2026-secure
```

## Estado de Tenants

- **active**: Operativo, usuarios pueden acceder
- **pending/provisioning**: En creación, esperar 1-2 minutos
- **suspended**: Bloqueado por falta de pago
- **cancelled**: Eliminado

## Panel Admin

Acceso en: `https://sajet.us/admin/tenants`

Características:
- ✅ Ver todos los tenants en tiempo real
- ✅ Filtrar por estado, plan, nodo
- ✅ Buscar por nombre, email, subdominio
- ✅ Crear nuevos tenants
- ✅ Cambiar contraseña admin
- ✅ Suspender/reactivar tenants
- ✅ Estadísticas en tiempo real

## Ejemplos Prácticos

### Crear tenant con script

```bash
#!/bin/bash
SUBDOMAIN="cliente1"
PASSWORD="MiClaveSegura123!"

curl -X POST http://localhost:4443/api/provisioning/tenant \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d "{
    \"subdomain\": \"$SUBDOMAIN\",
    \"admin_password\": \"$PASSWORD\"
  }" | jq '.url'
```

### Suspender por falta de pago

```bash
curl -X PUT http://localhost:4443/api/provisioning/tenant/suspend \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "cliente1",
    "suspend": true,
    "reason": "Pago vencido hace 30 días"
  }'
```

### Cambiar contraseña

```bash
curl -X PUT http://localhost:4443/api/provisioning/tenant/password \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "cliente1",
    "new_password": "NuevaClaveSegura2026!"
  }'
```

## Notas Importantes

1. **Seguridad**: El API Key debe ser secreto y cambiar en producción
2. **Backups**: Los tenants suspendidos conservan sus datos
3. **Recuperación**: Un tenant suspendido se puede reactivar sin perder datos
4. **DNS**: Se crea automáticamente en Cloudflare al crear tenant
5. **Tenants**: Cada tenant es una BD separada en PostgreSQL

## Troubleshooting

### Timeout contactando servidor
- Verificar conectividad a 10.10.10.100:8070
- Revisar firewall entre PCT 160 y PCT 105

### Contraseña no cambió
- Verificar que la contraseña tenga mínimo 6 caracteres
- Comprobar que el tenant existe

### Suspensión no funciona
- Verificar que API Key sea correcta
- Revisar logs en PCT 105

## Referencias

- [Creación de Tenants](/nodo/docs/API.md)
- [Panel Admin](/admin/tenants)
- [Instalación](/nodo/QUICKSTART.md)
