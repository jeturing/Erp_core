# Arquitectura Tailscale + Cloudflare Tunnels

## 🔴 PROBLEMA ENCONTRADO

**Proxmox no soporta TUN natively** en el kernel 6.8.12-15-pve.

Esto significa que Tailscale no puede funcionar como cliente completo en el host Proxmox.

## ✅ SOLUCIÓN RECOMENDADA

En lugar de instalar Tailscale en **Proxmox (172.16.16.160)**, instalarlo en:

### **OPCIÓN 1: En cada LXC Container (RECOMENDADO)**

```
┌─ Proxmox 172.16.16.160
│  └─ Cloudflare Tunnel (NO Tailscale)
│     ├─ LXC 105 (con Tailscale) → 100.x.x.x
│     ├─ LXC 106 (con Tailscale) → 100.x.x.y
│     └─ LXC 107 (con Tailscale) → 100.x.x.z
│
├─ Oficina DF (con Tailscale) → 100.x.x.a
├─ Oficina MTY (con Tailscale) → 100.x.x.b
└─ Clientes (con Tailscale) → 100.x.x.c
```

Ventajas:
- ✅ Cada contenedor tiene su IP Tailscale
- ✅ VPN encriptada entre todos
- ✅ Proxy reverso en Proxmox apunta a IPs Tailscale
- ✅ Sin dependencias de kernel

### **OPCIÓN 2: En Máquina Virtual (Alternativa)**

```
┌─ VM Linux (Ubuntu/Debian) en Proxmox
│  └─ Tailscale + Gateway
│     └─ Acceso a toda la red 172.16.16.X
│
└─ Proxy desde 172.16.16.160 → VM → Tailscale
```

## 📋 CONFIGURACIÓN POR OPCIÓN

### **OPCIÓN 1: Tailscale en LXC 105**

```bash
# Dentro del LXC 105
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --auth-key=tskey-auth-kRmHCpYC8Z11CNTRL-wc5kuMC31rJocF6i7y24rJv3WQdeXo4mE

# Obtendrá IP como 100.64.x.x
tailscale ip -4
```

Luego en `cloudflared config.yml`:
```yaml
ingress:
  - hostname: tenant1.sajet.us
    service: http://100.64.x.x:8069  # IP Tailscale de LXC 105
```

### **OPCIÓN 2: Tailscale en VM Gateway**

```bash
# En VM Linux
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --auth-key=tskey-auth-... --advertise-routes=172.16.16.0/24 --exit-node

# En Proxmox host, acepta rutas:
# Habilitar en Tailscale dashboard
```

## 🎯 RECOMENDACIÓN

**Usa OPCIÓN 1 (Tailscale en LXC)** porque:
1. ✅ Simple: instala en cada contenedor
2. ✅ Seguro: VPN end-to-end
3. ✅ Sin kernel issues
4. ✅ Escalable: agrega contenedores fácilmente
5. ✅ Funciona con Cloudflare Tunnel

## 🚀 PASOS SIGUIENTES

1. Verificar que los LXCs tienen soporte TUN (probablemente sí)
2. Instalar Tailscale en LXC 105
3. Configurar cloudflared para usar IPs Tailscale
4. Conectar otros segmentos de la red

---

**Nota:** Sin Tailscale en Proxmox no hay problema - CloudFlare Tunnel ya expone todo públicamente. Tailscale es extra para conectar segmentos privados.
