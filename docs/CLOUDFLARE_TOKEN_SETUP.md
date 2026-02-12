# 🔐 Crear Token de API para Cloudflare Tunnels

## ⚠️ Problema Actual

El token actual solo tiene permisos de **"Editar zona de DNS"**, pero para Cloudflare Tunnels necesitas permisos adicionales.

## 🔧 Solución: Crear Nuevo Token de API

### Paso 1: Accede a Cloudflare Dashboard

Ve a: https://dash.cloudflare.com/profile/api-tokens

### Paso 2: Crear Nuevo Token

1. Click en **"Create Token"**
2. Busca la plantilla **"Create Additional Tokens"** o crea uno personalizado

### Paso 3: Configurar Permisos

**Permisos requeridos:**

```
Account:
  - Cloudflare Tunnel: Edit

Zone:
  - DNS: Edit
  - Zone: Read
```

**Recursos de zona:**
- Incluir: Zona específica → `sajet.us`

### Paso 4: Resumen de Configuración

```
Token name: Onboarding System - Tunnels
Permissions:
  ├─ Account → Cloudflare Tunnel → Edit
  ├─ Zone → DNS → Edit
  └─ Zone → Zone → Read

Zone Resources:
  └─ Include → Specific zone → sajet.us

IP Address Filtering: (Opcional)
  └─ Is in → 172.16.16.160
```

### Paso 5: Generar y Copiar Token

1. Click en **"Continue to summary"**
2. Click en **"Create Token"**
3. **COPIA EL TOKEN** (solo se muestra una vez)

### Paso 6: Actualizar en el Servidor

```bash
ssh root@172.16.16.160

# Actualizar token
cat > /root/.cf_credentials << 'EOF'
CF_API_TOKEN=TU_NUEVO_TOKEN_AQUI
ZONE_ID=4a83b88793ac3688486ace69b6ae80f9
DOMAIN=sajet.us
EOF

chmod 600 /root/.cf_credentials

# Intentar login nuevamente
cloudflared tunnel login
```

## 🎯 Alternativa Rápida: Usar Origin CA Key

Si solo necesitas tunnels para desarrollo, puedes usar el Origin CA Key que ya tienes:

```
Origin_CA_Key=v1.0-70add71fa08e7a5e13306448-59ea0d823b4c3119cee40e6b50975813d7d123708a38548db75003f8c42c25790f32cfdbb5c2c093ff9f3965b9b7f9da4e05c07173b2a98708ffa0a2292f9cc073f3e43281a11ab6
```

Pero este no funciona para la API de Tunnels, solo para certificados SSL.

## ✅ Verificar Token Nuevo

Después de crear el token, verifica que tenga los permisos correctos:

```bash
curl -s "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer TU_NUEVO_TOKEN" | python3 -m json.tool
```

Debe mostrar algo como:
```json
{
  "result": {
    "id": "...",
    "status": "active"
  },
  "success": true
}
```

## 🔄 Siguiente Paso Después de Actualizar Token

Una vez actualizado el token:

```bash
# 1. Intentar login
cloudflared tunnel login

# 2. O verificar directamente
/root/check_cloudflare_auth.sh
```

---

**📝 Nota:** El token actual (`QRo16IDzpln0CRW5OhN214I4HBFwhoDJq1mHd0tL`) solo tiene permisos de DNS, por eso no aparecen opciones en la página de autorización de tunnels.
