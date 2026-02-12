# Configuración de Cloudflare Tunnels

## ✅ Estado Actual

### Completado
- ✅ **cloudflared instalado** (versión 2026.1.2)
- ✅ **API Token válido** configurado: `QRo16IDzpln0CRW5OhN214I4HBFwhoDJq1mHd0tL`
- ✅ **Credenciales básicas** en `/root/.cf_credentials`
- ✅ **Script de setup** creado: `/root/setup_cloudflare_tunnel.sh`
- ✅ **Sistema preparado** para tunnels

### Información de la Cuenta
- **Dominio**: sajet.us
- **Zone ID**: 4a83b88793ac3688486ace69b6ae80f9
- **API Token**: Permisos de "Editar zona de DNS"

## 🚀 Configuración Final (Requiere Acceso al Servidor)

### Opción 1: Setup Interactivo (Recomendado)

Conéctate al servidor y ejecuta:

```bash
ssh root@172.16.16.160

# Ejecutar script de configuración
/root/setup_cloudflare_tunnel.sh
```

Esto ejecutará `cloudflared tunnel login` y abrirá un navegador donde debes:
1. Iniciar sesión en Cloudflare
2. Autorizar cloudflared
3. Seleccionar el dominio "sajet.us"

### Opción 2: Setup Manual

```bash
ssh root@172.16.16.160

# Login a Cloudflare
cloudflared tunnel login

# Verificar credenciales
ls -la ~/.cloudflared/

# Reiniciar servicio
systemctl restart onboarding
```

### Opción 3: Setup Remoto (Sin Navegador)

Si no tienes acceso a un navegador en el servidor:

```bash
ssh root@172.16.16.160

# Generar URL de autorización
cloudflared tunnel login --url

# Copiar la URL y abrirla en tu navegador local
# Después de autorizar, las credenciales se guardarán automáticamente
```

## 📋 Verificación Post-Setup

Después de configurar cloudflared:

```bash
# 1. Verificar que las credenciales existan
ls -la ~/.cloudflared/

# 2. Listar tunnels (debería estar vacío inicialmente)
cloudflared tunnel list

# 3. Reiniciar servicio onboarding
systemctl restart onboarding

# 4. Verificar logs
journalctl -u onboarding -f

# 5. Acceder al dashboard
# http://172.16.16.160:4443/admin/tunnels
```

## 🧪 Crear Primer Tunnel de Prueba

Una vez configurado, puedes crear un tunnel manualmente:

```bash
# Crear tunnel
cloudflared tunnel create test-tenant

# Configurar DNS
cloudflared tunnel route dns test-tenant test-tenant.sajet.us

# Crear archivo de configuración
cat > /root/.cloudflared/test-tenant.yml << EOF
tunnel: test-tenant
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: test-tenant.sajet.us
    service: http://172.16.16.105:8069
  - service: http_status:404
EOF

# Ejecutar tunnel
cloudflared tunnel run test-tenant
```

## 🔧 Troubleshooting

### Error: "No se pudo obtener lista de tunnels"

**Causa**: cloudflared no ha hecho login  
**Solución**: Ejecutar `cloudflared tunnel login`

### Error: "Invalid API Token"

**Causa**: Token en .cf_credentials está desactualizado  
**Solución**: Ya actualizado con el nuevo token

### Error: "Unauthorized to access requested resource"

**Causa**: Token no tiene permisos de Tunnel  
**Solución**: Usar `cloudflared tunnel login` en lugar del API token

### Tunnel no aparece en el dashboard

**Causa**: Túnel no está registrado en la base de datos  
**Solución**: Usar el endpoint POST /api/tunnels para crear tunnels desde el sistema

## 📚 Referencias

- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [cloudflared GitHub](https://github.com/cloudflare/cloudflared)
- Token de API válido hasta que sea revocado
- ZONE_ID y DOMAIN configurados correctamente

## 🎯 Siguiente Paso

**Ejecuta en el servidor:**
```bash
/root/setup_cloudflare_tunnel.sh
```

O conéctate manualmente y ejecuta:
```bash
cloudflared tunnel login
```

Después de esto, el dashboard de tunnels en `/admin/tunnels` mostrará los tunnels activos en lugar del mensaje de "no configurado".
