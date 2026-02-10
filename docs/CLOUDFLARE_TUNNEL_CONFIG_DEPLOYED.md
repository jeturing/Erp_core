# Cloudflare Tunnel - Configuración Desplegada

## 📋 RESUMEN

Se ha configurado **cloudflared tunnel** en **Orion (172.16.16.160)** para exponer servicios de los 3 hosts vía Tailscale:

```
┌─ INTERNET (Cloudflare)
│
└─ tcs-sajet-tunnel (Orion: 23.95.79.152)
   │
   ├─ atenea.sajet.us          → 100.103.65.2:8069 (Atenea vía Tailscale)
   ├─ atenea-admin.sajet.us    → 100.103.65.2:8072
   │
   ├─ atlas.sajet.us           → 100.75.41.36:8069 (Atlas vía Tailscale)
   ├─ atlas-admin.sajet.us     → 100.75.41.36:8072
   │
   ├─ orion.sajet.us           → 172.16.16.105:8069 (Local Odoo)
   ├─ local.sajet.us           → 172.16.16.105:8069
   │
   ├─ api.sajet.us             → 127.0.0.1:4443 (FastAPI)
   ├─ admin.sajet.us           → 127.0.0.1:4443
   └─ tunnels.sajet.us         → 127.0.0.1:4443 (Dashboard)
```

## 🔧 CONFIGURACIÓN

### Archivo: `/etc/cloudflared/config.yml`

```yaml
tunnel: tcs-sajet-tunnel
credentials-file: /root/.cloudflared/cert.pem

ingress:
  # === Atenea (10.10.10.1) ===
  - hostname: atenea.sajet.us
    service: http://100.103.65.2:8069
  - hostname: atenea-admin.sajet.us
    service: http://100.103.65.2:8072

  # === Atlas (192.168.1.250) ===
  - hostname: atlas.sajet.us
    service: http://100.75.41.36:8069
  - hostname: atlas-admin.sajet.us
    service: http://100.75.41.36:8072

  # === Orion Local (172.16.16.160) ===
  - hostname: orion.sajet.us
    service: http://172.16.16.105:8069
  - hostname: local.sajet.us
    service: http://172.16.16.105:8069
  
  # === API y Admin ===
  - hostname: api.sajet.us
    service: http://127.0.0.1:4443
  - hostname: admin.sajet.us
    service: http://127.0.0.1:4443

  # === Dashboard de Tunnels ===
  - hostname: tunnels.sajet.us
    service: http://127.0.0.1:4443

  # Default catch-all
  - service: http_status:404
```

### Servicio Systemd: `/etc/systemd/system/cloudflared-tunnel.service`

```ini
[Unit]
Description=Cloudflare Tunnel (tcs-sajet-tunnel)
After=network.target
Wants=network-online.target

[Service]
Type=notify
User=root
WorkingDirectory=/root
ExecStart=/usr/bin/cloudflared tunnel run tcs-sajet-tunnel --config /etc/cloudflared/config.yml
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

## ✅ VERIFICACIÓN

### Estado del servicio:
```bash
systemctl status cloudflared-tunnel.service
```

### Logs:
```bash
journalctl -u cloudflared-tunnel.service -f
```

### Verificar túnel activo:
```bash
cloudflared tunnel list
cloudflared tunnel info tcs-sajet-tunnel
```

### Probar conectividad:
```bash
# Desde cualquier lugar con internet:
curl https://api.sajet.us/health
curl https://atenea.sajet.us  # Redirige a Atenea via Tailscale
curl https://atlas.sajet.us   # Redirige a Atlas via Tailscale
```

## 🌐 DNS RECORDS

Cloudflare ha creado automáticamente CNAME records:

| Subdomain | CNAME | Destino |
|-----------|-------|---------|
| atenea.sajet.us | → | UUID.cfargotunnel.com |
| atlas.sajet.us | → | UUID.cfargotunnel.com |
| orion.sajet.us | → | UUID.cfargotunnel.com |
| api.sajet.us | → | UUID.cfargotunnel.com |
| admin.sajet.us | → | UUID.cfargotunnel.com |

## 🔗 ARQUITECTURA DE RED

```
INTERNET
  ↓ DNS lookup: atenea.sajet.us
CLOUDFLARE
  ↓ CNAME → cfargotunnel.com
CLOUDFLARE EDGE
  ↓ Tunnel connection
Orion (23.95.79.152)
  ↓ Tailscale 100.66.8.90
Atenea (10.10.10.1)
  ↓ Tailscale 100.103.65.2:8069
Odoo Instance
```

## 🚀 PROVISIONING AUTOMÁTICO

Para crear nuevos tenants que apunten a diferentes hosts:

```python
# app/services/odoo_provisioner.py

HOSTS = {
    "local": {
        "ip": "172.16.16.105",
        "port": 8069,
        "tunnel": "tcs-sajet-tunnel"
    },
    "atenea": {
        "ip": "100.103.65.2",  # Tailscale
        "port": 8069,
        "tunnel": "tcs-sajet-tunnel"
    },
    "atlas": {
        "ip": "100.75.41.36",   # Tailscale
        "port": 8069,
        "tunnel": "tcs-sajet-tunnel"
    }
}

async def provision_tenant(
    subdomain: str,
    host: str = "local",
    ...
):
    config = HOSTS.get(host, HOSTS["local"])
    
    # Crear entrada en Cloudflare
    # cloudflared tunnel route dns tcs-sajet-tunnel {subdomain}.sajet.us
```

## 📊 MATRIZ DE ACCESO

| Tenant | Host | URL | Ruta |
|--------|------|-----|------|
| acme-local | Orion | https://acme-local.sajet.us | → 172.16.16.105:8069 |
| acme-atenea | Atenea | https://acme-atenea.sajet.us | → 100.103.65.2:8069 (Tailscale) |
| acme-atlas | Atlas | https://acme-atlas.sajet.us | → 100.75.41.36:8069 (Tailscale) |

## ⚙️ MANTENIMIENTO

### Agregar nuevo subdomain:
```bash
cloudflared tunnel route dns tcs-sajet-tunnel tenant.sajet.us
```

### Actualizar config.yml:
```bash
# Editar /etc/cloudflared/config.yml
# Reiniciar servicio
systemctl restart cloudflared-tunnel.service
```

### Verificar conectividad Tailscale:
```bash
# En Orion:
ping 100.103.65.2  # Atenea
ping 100.75.41.36  # Atlas

# En Atenea:
ping 100.66.8.90   # Orion
ping 100.75.41.36  # Atlas
```

## 🔒 SEGURIDAD

✅ **Tunnel encriptado** - Todo tráfico es encriptado end-to-end  
✅ **Tailscale VPN** - Red privada adicional para inter-host  
✅ **Cloudflare WAF** - DDoS y rate limiting automático  
✅ **SSL/TLS** - HTTPS en todos los subdominios  
⚠️ **Firewall** - Verificar que puertos 8069, 8072 estén abiertos internamente

## 📞 CONTACTO

Para problemas:
```bash
# SSH a Orion
ssh root@172.16.16.160

# Verificar tunnel
systemctl status cloudflared-tunnel

# Ver logs completos
journalctl -u cloudflared-tunnel.service -S "10 minutes ago"
```
