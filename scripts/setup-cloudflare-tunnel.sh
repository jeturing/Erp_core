#!/bin/bash
# =============================================================================
# Configurar Cloudflare Tunnel para sajet.us en PCT 202
# =============================================================================

set -euo pipefail

PCT_ID="202"
CF_TOKEN="fNeyaWEVQ0iOgTiO-Kjom8pSIH0UUQQUUw5l6J-o"
CF_ZONE_ID="4a83b88793ac3688486ace69b6ae80f9"
DOMAIN="sajet.us"
TUNNEL_NAME="sajet-tunnel-pct202"

# Crear directorio de credenciales en PCT
echo "[*] Creando directorio .cloudflared en PCT 202..."
pct exec ${PCT_ID} -- mkdir -p /root/.cloudflared

# 1. Crear/obtener tunnel ID desde Cloudflare
echo "[*] Verificando tunnel en Cloudflare..."
TUNNEL_LIST=$(curl -s -H "Authorization: Bearer ${CF_TOKEN}" \
  https://api.cloudflare.com/client/v4/accounts/b5f8a23e7d06c2de5ef515ae93e16016/cfd_tunnel \
  2>/dev/null || echo '{"result":[]}')

TUNNEL_ID=$(echo "$TUNNEL_LIST" | grep -o '"id":"[^"]*"' | grep -o '"[^"]*"$' | tr -d '"' | head -1)

if [ -z "$TUNNEL_ID" ]; then
  echo "[!] No hay tunnel existente. Crear manualmente en:"
  echo "    https://dash.cloudflare.com/profile/tunnels"
  echo "[!] Después, obtener el Tunnel ID y credenciales JSON"
  echo "[!] Reintenta con: CF_TUNNEL_ID=<id> $0"
  exit 1
fi

echo "[+] Tunnel ID encontrado: $TUNNEL_ID"

# 2. Obtener credentials token (este paso requiere el Tunnel ID del dashboard)
# Para simplificar, vamos a asumir que el usuario proporciona o ya existe

# 3. Crear config.yml para el tunnel
echo "[*] Creando configuración del tunnel..."
cat > /tmp/sajet-tunnel-config.yml <<'EOF'
tunnel: sajet-tunnel-pct202
credentials-file: /root/.cloudflared/TUNNEL_ID.json
logfile: /var/log/cloudflared/sajet-tunnel.log
loglevel: info

ingress:
  - hostname: sajet.us
    service: https://localhost:443
    originRequest:
      noTLSVerify: true
  - hostname: "*.sajet.us"
    service: https://localhost:443
    originRequest:
      noTLSVerify: true
  - service: http_status:404
EOF

echo "[+] Config template creado en /tmp/sajet-tunnel-config.yml"
echo "[!] Necesitas obtener el archivo de credenciales JSON desde Cloudflare dashboard"
echo "[!] Paso siguiente:"
echo "    1. Ve a: https://dash.cloudflare.com/profile/tunnels"
echo "    2. Selecciona el tunnel 'sajet-tunnel-pct202'"
echo "    3. Descarga el credentials file"
echo "    4. Cópialo a PCT 202: pct push 202 /path/to/credentials.json /root/.cloudflared/"
echo "    5. Luego ejecuta este script de nuevo"
