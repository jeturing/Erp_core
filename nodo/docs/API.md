# API Local de Provisioning

Documentación técnica de la API REST para provisioning de tenants.

## Información General

- **Servidor:** Odoo Local (PCT 105)
- **Puerto:** 8070
- **Protocolo:** HTTP (comunicación interna)
- **Autenticación:** API Key vía header `X-API-KEY`

## Endpoints

### 1. Health Check

```http
GET /health
```

**Respuesta:**
```json
{
  "status": "ok",
  "service": "odoo-provisioning"
}
```

---

### 2. Listar Tenants

```http
GET /api/tenants
Headers:
  X-API-KEY: prov-key-2026-secure
```

**Respuesta (200 OK):**
```json
{
  "tenants": [
    {
      "database": "tcs",
      "url": "https://tcs.sajet.us"
    },
    {
      "database": "cliente1",
      "url": "https://cliente1.sajet.us"
    }
  ],
  "total": 2
}
```

**Errores:**
- `401 Unauthorized` - API Key inválida

---

### 3. Crear Tenant

```http
POST /api/tenant
Headers:
  X-API-KEY: prov-key-2026-secure
  Content-Type: application/json

Body:
{
  "subdomain": "nuevo_cliente",
  "admin_password": "secreto123",
  "domain": "sajet.us",
  "template_db": "tcs"
}
```

**Parámetros:**
- `subdomain` (string, required) - Nombre del tenant (min 3, max 30 caracteres)
- `admin_password` (string, default: "admin") - Contraseña para admin
- `domain` (string, default: "sajet.us") - Dominio de la BD
- `template_db` (string, default: "tcs") - BD plantilla para duplicar

**Respuesta (200 OK):**
```json
{
  "success": true,
  "subdomain": "nuevo_cliente",
  "url": "https://nuevo_cliente.sajet.us",
  "database": "nuevo_cliente",
  "dns_created": true
}
```

**Errores:**
- `400 Bad Request` - Parámetros inválidos
- `401 Unauthorized` - API Key inválida
- `409 Conflict` - BD ya existe
- `500 Internal Server Error` - Error creando BD

---

### 4. Eliminar Tenant

```http
DELETE /api/tenant
Headers:
  X-API-KEY: prov-key-2026-secure
  Content-Type: application/json

Body:
{
  "subdomain": "nuevo_cliente",
  "delete_dns": true
}
```

**Parámetros:**
- `subdomain` (string, required) - Nombre del tenant
- `delete_dns` (boolean, default: true) - Eliminar DNS de Cloudflare

**Respuesta (200 OK):**
```json
{
  "success": true,
  "database_deleted": true,
  "dns_deleted": true
}
```

**Errores:**
- `401 Unauthorized` - API Key inválida
- `500 Internal Server Error` - Error eliminando BD

---

### 5. Listar Dominios

```http
GET /api/domains
```

**Respuesta:**
```json
{
  "domains": [
    "sajet.us",
    "jeturing.com",
    "gmfcllc.com",
    "lslogistic.net",
    "aysautorepair.com",
    "esecure.do"
  ]
}
```

---

## Ejemplos de Uso

### Con cURL

```bash
# Crear tenant
curl -X POST \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "cliente_demo",
    "admin_password": "demo123"
  }' \
  http://10.10.10.100:8070/api/tenant

# Listar tenants
curl -H "X-API-KEY: prov-key-2026-secure" \
  http://10.10.10.100:8070/api/tenants

# Eliminar tenant
curl -X DELETE \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{"subdomain": "cliente_demo"}' \
  http://10.10.10.100:8070/api/tenant
```

### Con Python

```python
import httpx
import json

# Headers con API Key
headers = {
    "X-API-KEY": "prov-key-2026-secure",
    "Content-Type": "application/json"
}

# Crear tenant
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://10.10.10.100:8070/api/tenant",
        headers=headers,
        json={
            "subdomain": "cliente_nuevo",
            "admin_password": "secreto123"
        }
    )
    print(response.json())
```

### Con JavaScript/Node.js

```javascript
// Crear tenant
const response = await fetch('http://10.10.10.100:8070/api/tenant', {
  method: 'POST',
  headers: {
    'X-API-KEY': 'prov-key-2026-secure',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    subdomain: 'cliente_nuevo',
    admin_password: 'secreto123'
  })
});

const data = await response.json();
console.log(data);
```

---

## Códigos de Estado HTTP

| Código | Significado |
|--------|-------------|
| 200 | OK - Operación exitosa |
| 400 | Bad Request - Parámetros inválidos |
| 401 | Unauthorized - API Key inválida |
| 409 | Conflict - BD ya existe |
| 500 | Internal Server Error - Error del servidor |

---

## Notas de Seguridad

1. **API Key:** Cambiar `prov-key-2026-secure` en producción
2. **HTTPS:** En producción, usar HTTPS (configurar en Nginx reverse proxy)
3. **Firewall:** Limitar acceso al puerto 8070 solo desde APP Server (IP whitelisting)
4. **Logs:** Revisar regularmente `/var/log/syslog` para actividad sospechosa

---

## Configuración de Nginx (Reverse Proxy - Opcional)

Para exponer API vía HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name api.odoo.sajet.us;

    location / {
        proxy_pass http://localhost:8070;
        proxy_set_header X-API-KEY $http_x_api_key;
        proxy_set_header Host $host;
    }
}
```

---

**Versión:** 1.0  
**Actualizado:** Febrero 2026
