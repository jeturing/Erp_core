# ✅ Refactorización de provision_tenant - Resumen

## 🎯 Cambios Principales

### Antes
```python
async def provision_tenant(
    subdomain: str,
    admin_email: str,
    company_name: str,
    subscription_id: Optional[int] = None,
    container_ip: str = "172.16.16.105",  # ❌ Hardcodeado
    local_port: int = 8069,                # ❌ Hardcodeado
    create_tunnel: bool = True             # ❌ Hardcodeado
):
```

**Problemas:**
- Valores hardcodeados = difícil cambiar sin editar código
- Sin validación de entrada
- Sin manejo de errores específicos

---

### Después
```python
async def provision_tenant(
    subdomain: str,
    admin_email: str,
    company_name: str,
    subscription_id: Optional[int] = None,
    container_ip: Optional[str] = None,    # ✅ None = usar .env
    local_port: Optional[int] = None,       # ✅ None = usar .env
    create_tunnel: Optional[bool] = None    # ✅ None = usar .env
):
```

**Mejoras:**
- ✅ Valores desde `.env` (DEFAULT_CONTAINER_IP, DEFAULT_LOCAL_PORT, ENABLE_CLOUDFLARE)
- ✅ Validación completa de todos los parámetros
- ✅ Errores descriptivos y tipados
- ✅ Logging detallado con emojis
- ✅ Funciones de validación reutilizables

---

## 📋 Nuevas Funciones de Validación

| Función | Valida |
|---------|--------|
| `_validate_subdomain()` | Alfanuméricos, guiones, máx 63 chars, no reservado |
| `_validate_email()` | Formato RFC 5322, máx 254 chars |
| `_validate_company_name()` | 2-255 caracteres |
| `_validate_ip_address()` | IPv4 (0-255 en cada octeto) o IPv6 |
| `_validate_port()` | Entero 1-65535 |
| `_get_config_from_env()` | Lee y valida todas las variables de .env |

---

## 🔧 Variables de Entorno Requeridas

Agregar a `.env`:

```bash
# REQUERIDAS (si faltan, error en provisioning)
LXC_CONTAINER_ID=105
DOMAIN=sajet.us
CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant_enhanced.sh
DEFAULT_CONTAINER_IP=172.16.16.105
DEFAULT_LOCAL_PORT=8069

# OPCIONAL
ENABLE_CLOUDFLARE=true
```

Ver `.env.example` para todos los valores.

---

## 🚨 Tipos de Error

### ValidationError
Errores en datos de entrada:

```json
{
  "success": false,
  "error_type": "validation_error",
  "error": "Email inválido: notanemail"
}
```

**Causas:**
- Subdomain inválido/reservado
- Email malformado
- Company name muy corto
- IP inválida
- Puerto fuera de rango

### ProvisioningError
Errores de configuración o provisioning:

```json
{
  "success": false,
  "error_type": "provisioning_error",
  "error": "Variable LXC_CONTAINER_ID no configurada en .env"
}
```

**Causas:**
- Variable de .env faltante
- Script de provisioning falló
- Base de datos no accesible

### TimeoutError
El provisioning tardó > 5 minutos:

```json
{
  "success": false,
  "error_type": "timeout_error",
  "error": "Provisioning tardó más de 5 minutos"
}
```

### UnknownError
Errores inesperados:

```json
{
  "success": false,
  "error_type": "unknown_error",
  "error": "Unexpected error message"
}
```

---

## 📊 Ejemplo de Flujo

### Solicitud
```python
result = await provision_tenant(
    subdomain="acme",
    admin_email="admin@acme.com",
    company_name="Acme Corp",
    subscription_id=5
    # container_ip, local_port, create_tunnel = None → usar defaults
)
```

### Validaciones
```
✓ Validar config desde .env
  - LXC_CONTAINER_ID=105 ✅
  - DOMAIN=sajet.us ✅
  - CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant_enhanced.sh ✅
  - DEFAULT_CONTAINER_IP=172.16.16.105 ✅
  - DEFAULT_LOCAL_PORT=8069 ✅
  - ENABLE_CLOUDFLARE=true ✅

✓ Aplicar defaults
  - container_ip = None → 172.16.16.105 (de .env)
  - local_port = None → 8069 (de .env)
  - create_tunnel = None → true (de .env)

✓ Validar parámetros
  - subdomain="acme" → ✅ válido
  - admin_email="admin@acme.com" → ✅ válido
  - company_name="Acme Corp" → ✅ válido
  - container_ip="172.16.16.105" → ✅ IP válida
  - local_port=8069 → ✅ puerto válido
```

### Ejecución
```
1. Ejecutar create_tenant_enhanced.sh
2. Crear Cloudflare tunnel
3. Actualizar BD
```

### Respuesta OK
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
    "tunnel_id": "xyz789",
    "tunnel_name": "acme-tunnel",
    "domain": "acme.sajet.us",
    "status": "active"
  }
}
```

---

## 📚 Documentación Relacionada

- **Validación Detallada:** `docs/PARAMETER_VALIDATION.md`
- **Ejemplos Completos:** `docs/PARAMETER_VALIDATION.md`
- **Variables de Entorno:** `.env.example`

---

## 🔄 Backward Compatibility

El código sigue siendo compatible con llamadas anteriores:

```python
# Así sigue funcionando (usa defaults)
result = await provision_tenant(
    subdomain="acme",
    admin_email="admin@acme.com",
    company_name="Acme Corp"
)

# Pero también puedes override específicos
result = await provision_tenant(
    subdomain="acme",
    admin_email="admin@acme.com",
    company_name="Acme Corp",
    container_ip="192.168.1.100",  # Override
    local_port=9000  # Override
)
```

---

## ✅ Checklist

- ✅ Eliminar hardcoded values
- ✅ Agregar validación de subdomain
- ✅ Agregar validación de email
- ✅ Agregar validación de company_name
- ✅ Agregar validación de IP
- ✅ Agregar validación de puerto
- ✅ Leer config desde .env
- ✅ Usar defaults de .env
- ✅ Manejo de excepciones específicas
- ✅ Logging detallado
- ✅ Documentación completa
- ✅ Backward compatible

---

## 🚀 Próximos Pasos

1. Actualizar `.env` en desarrollo con variables requeridas
2. Actualizar `.env` en producción (172.16.16.160)
3. Testear provisioning con parámetros válidos e inválidos
4. Verificar logging en `/var/log/onboarding/app.log`

