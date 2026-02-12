# 🌐 Guía de Configuración DNS para Dominios Personalizados

## Para Clientes de TecHeels / Jeturing

Esta guía explica cómo configurar tu dominio personalizado para que apunte a tu aplicación.

---

## 📋 Resumen Rápido

Para que tu dominio funcione (ej: `www.tudominio.com`), necesitas:

1. Ir al panel de tu registrador DNS (GoDaddy, Namecheap, Cloudflare, etc.)
2. Agregar un registro **CNAME**
3. Esperar propagación (5 min - 24 horas)

---

## 🔧 Configuración Paso a Paso

### Paso 1: Obtén tu subdominio de Sajet

Cuando registras tu dominio personalizado en el panel de Jeturing, recibirás un subdominio como:

```
Tu subdominio: tuempresa.sajet.us
```

Este es el valor que usarás en el CNAME.

### Paso 2: Accede a tu panel DNS

Entra al panel de tu registrador de dominio:

| Registrador | URL del Panel DNS |
|-------------|-------------------|
| GoDaddy | https://dcc.godaddy.com/manage/dns |
| Namecheap | https://ap.www.namecheap.com/domains/dns |
| Cloudflare | https://dash.cloudflare.com |
| Google Domains | https://domains.google.com/registrar |
| HostGator | https://portal.hostgator.com |

### Paso 3: Agrega el registro CNAME

Crea un nuevo registro con estos valores:

| Campo | Valor |
|-------|-------|
| **Tipo** | CNAME |
| **Nombre/Host** | `www` (o `@` para dominio raíz*) |
| **Valor/Apunta a** | `tuempresa.sajet.us` |
| **TTL** | 3600 (o "Auto") |

#### Ejemplos específicos:

**Para ImpulseMax:**
```
Tipo:   CNAME
Host:   www
Valor:  impulse-max.sajet.us
TTL:    3600
```

**Para EvolucionaMujer:**
```
Tipo:   CNAME
Host:   www
Valor:  evolucionamujer.sajet.us
TTL:    3600
```

**Para TecHeels:**
```
Tipo:   CNAME
Host:   www
Valor:  techeels.sajet.us
TTL:    3600
```

### Paso 4: Configura redirección del dominio raíz (opcional)

Si quieres que `tudominio.com` (sin www) también funcione:

**Opción A - Redirect (Recomendado):**
Configura una redirección 301 de `tudominio.com` → `www.tudominio.com`

**Opción B - CNAME Flattening (si tu DNS lo soporta):**
Cloudflare y algunos otros permiten CNAME en el apex:
```
Tipo:   CNAME
Host:   @
Valor:  tuempresa.sajet.us
```

---

## ✅ Verificación

### Cómo saber si está funcionando

1. **Espera 5-30 minutos** después de guardar los cambios
2. **Abre una terminal** y ejecuta:
   ```bash
   nslookup www.tudominio.com
   ```
3. **Deberías ver** algo como:
   ```
   www.tudominio.com canonical name = tuempresa.sajet.us
   tuempresa.sajet.us canonical name = tcs-sajet-tunnel.cfargotunnel.com
   ```

### Verificación online

Puedes usar estas herramientas:
- https://dnschecker.org
- https://mxtoolbox.com/DNSLookup.aspx
- https://toolbox.googleapps.com/apps/dig/

---

## ❓ Problemas Comunes

### "Mi dominio no funciona"

1. **Espera más tiempo** - La propagación DNS puede tardar hasta 48 horas
2. **Limpia caché del navegador** - Ctrl+Shift+R o abre en incógnito
3. **Verifica el CNAME** - Asegúrate que el valor sea exactamente `tuempresa.sajet.us`

### "Tengo un registro A existente"

Si ya tienes un registro A para `www`:
1. **Elimina** el registro A existente
2. **Crea** el nuevo registro CNAME
3. No pueden coexistir A y CNAME para el mismo host

### "Mi registrador no permite CNAME en @"

Esto es normal. El dominio raíz (apex) técnicamente no puede tener CNAME según RFC.

**Soluciones:**
- Usa `www` con CNAME y redirecciona `@` a `www`
- Cambia a Cloudflare que soporta CNAME flattening
- Contacta soporte para configurar un registro ALIAS

### "SSL no funciona / Certificado inválido"

El SSL es manejado automáticamente por Cloudflare. Si ves errores:
1. Espera 15 minutos después de configurar el CNAME
2. Asegúrate de acceder por HTTPS (`https://`)
3. El certificado es emitido para `*.sajet.us`, que cubre tu subdominio

---

## 📊 Arquitectura Técnica

```
┌──────────────────┐
│ www.tudominio.com│ ← Tu cliente escribe esto
└────────┬─────────┘
         │ CNAME
         ▼
┌──────────────────┐
│tuempresa.sajet.us│ ← Resuelve a Cloudflare
└────────┬─────────┘
         │ Cloudflare Edge
         ▼
┌──────────────────┐
│ Cloudflare Tunnel│ ← Conexión segura
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Tu Aplicación    │ ← Odoo/Web en contenedor
│ (Servidor)       │
└──────────────────┘
```

---

## 🔒 Seguridad

- **SSL/TLS:** Incluido automáticamente (Cloudflare)
- **DDoS Protection:** Incluido (Cloudflare)
- **WAF:** Incluido en planes Pro/Enterprise

---

## 📞 Soporte

Si necesitas ayuda:

- **Email:** soporte@jeturing.net
- **WhatsApp:** +1 (XXX) XXX-XXXX
- **Panel:** https://admin.sajet.us → Soporte

---

## 📝 Registro de Cambios DNS

Guarda un registro de los cambios que hagas:

| Fecha | Dominio | Tipo | Host | Valor | Estado |
|-------|---------|------|------|-------|--------|
| DD/MM/AAAA | tudominio.com | CNAME | www | tuempresa.sajet.us | ✅ Activo |

---

*Última actualización: Febrero 2026*
*Versión: 1.0*
