# ⏳ Autorización de Cloudflare Pendiente

## 🔗 URL de Autorización Activa

**Abre esta URL en tu navegador AHORA:**

```
https://dash.cloudflare.com/argotunnel?aud=&callback=https%3A%2F%2Flogin.cloudflareaccess.org%2Fz-lIfbkumLnHlAFxAATSCQXdVWWLwS_2QCAIrP3viCo%3D
```

## 📋 Pasos a Seguir

1. **Abre la URL arriba** en tu navegador
2. **Inicia sesión** con tu cuenta de Cloudflare
3. **Autoriza cloudflared** cuando te lo pida
4. **Selecciona el dominio** `sajet.us` de la lista
5. **Espera 10-20 segundos** después de autorizar

## ✅ Verificación

Después de completar la autorización, ejecuta en el servidor:

```bash
ssh root@172.16.16.160
/root/check_cloudflare_auth.sh
```

O verifica manualmente:

```bash
# Verificar que el certificado existe
ls -la ~/.cloudflared/cert.pem

# Listar tunnels disponibles
cloudflared tunnel list

# Crear tunnel de prueba
cloudflared tunnel create test-tunnel
```

## 🚀 Después de la Autorización

Una vez completada la autorización:

1. **El certificado** `cert.pem` se descargará automáticamente a `~/.cloudflared/`
2. **El sistema** podrá crear y gestionar tunnels
3. **El dashboard** `/admin/tunnels` mostrará los tunnels activos
4. **El servicio** onboarding se reiniciará automáticamente

## ⚡ Estado Actual del Sistema

- ✅ cloudflared instalado (v2026.1.2)
- ✅ API Token configurado
- ✅ Proceso de login en background
- ⏳ **Esperando autorización en navegador**
- ⏳ Certificado pendiente de descarga

## 🔄 Si la Autorización Falla

Si después de 5 minutos no funciona:

```bash
# Detener proceso de login
pkill cloudflared

# Reiniciar proceso
nohup cloudflared tunnel login > /tmp/cloudflared_login.log 2>&1 &

# Ver la nueva URL
tail -f /tmp/cloudflared_login.log
```

## 📞 Soporte

Si encuentras problemas:
- Verifica los logs: `tail -f /tmp/cloudflared_login.log`
- Verifica el proceso: `ps aux | grep cloudflared`
- Consulta [CLOUDFLARE_SETUP.md](CLOUDFLARE_SETUP.md) para más opciones

---

**⏰ Tiempo estimado:** 2-3 minutos después de autorizar en el navegador

**🎯 Próximo paso:** Abre la URL en tu navegador y autoriza cloudflared
