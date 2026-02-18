#!/usr/bin/env bash
#═══════════════════════════════════════════════════════════════════
# deploy-suspension-nginx.sh
# Despliega la configuración de suspensión de tenants en PCT105
#
# Qué hace:
#   1. Copia suspended_map.conf → /etc/nginx/conf.d/
#   2. Agrega las directivas de intercepción al bloque server de Odoo
#   3. Valida y recarga Nginx
#═══════════════════════════════════════════════════════════════════
set -euo pipefail

PCT105="10.10.10.100"
NGINX_CONF="/etc/nginx/sites-enabled/odoo"
SUSPENDED_MAP="/etc/nginx/conf.d/suspended_map.conf"
BACKUP_DIR="/etc/nginx/backups"

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}━━━ Desplegando sistema de suspensión de tenants ━━━${NC}"

# 1. Crear directorio de backups
echo "[1/4] Creando backup de Nginx actual..."
ssh root@${PCT105} "mkdir -p ${BACKUP_DIR} && cp ${NGINX_CONF} ${BACKUP_DIR}/odoo.bak.\$(date +%Y%m%d_%H%M%S)"

# 2. Copiar mapa de suspensión inicial
echo "[2/4] Copiando mapa de suspensión..."
scp /opt/Erp_core/scripts/nginx/suspended_map.conf root@${PCT105}:${SUSPENDED_MAP}

# 3. Verificar si ya se incluyó el mapa en nginx.conf
echo "[3/4] Verificando include en nginx.conf..."
ssh root@${PCT105} bash -s << 'REMOTE_SCRIPT'
    # Verificar si el include ya existe
    if grep -q "suspended_map.conf" /etc/nginx/nginx.conf 2>/dev/null; then
        echo "  → Include ya existe en nginx.conf"
    elif grep -q "include /etc/nginx/conf.d/" /etc/nginx/nginx.conf 2>/dev/null; then
        echo "  → conf.d/ ya incluido globalmente"
    else
        # Agregar include antes del cierre del bloque http
        echo "  → Agregando include..."
        sed -i '/http {/a\    include /etc/nginx/conf.d/*.conf;' /etc/nginx/nginx.conf
    fi
REMOTE_SCRIPT

# 4. Inyectar las directivas de suspensión en el bloque server SSL
echo "[4/4] Inyectando lógica de suspensión en Nginx..."
ssh root@${PCT105} bash -s << 'REMOTE_INJECT'
NGINX_CONF="/etc/nginx/sites-enabled/odoo"

# Verificar si ya tiene la lógica de suspensión
if grep -q "tenant_suspended" "$NGINX_CONF"; then
    echo "  → Lógica de suspensión ya existe en Nginx config"
    nginx -t && echo "  ✅ Configuración válida" || echo "  ❌ Error en configuración"
    exit 0
fi

# Inyectar DESPUÉS de la línea "proxy_redirect http://joficreditosrd.sajet.us/ https://$host/;"
# en AMBOS bloques server (8080 y 8443)

# Bloque a inyectar
SUSPENSION_BLOCK='
    # ═══ TENANT SUSPENSION SYSTEM ═══
    # Si el tenant está suspendido, redirigir a página de suspensión
    # La cookie "tenant_owner" identifica al propietario del sitio
    
    # Servir archivos estáticos de suspensión directamente
    location /static/suspended/ {
        alias /opt/Erp_core/static/suspended/;
        expires 1h;
    }
    
    # Página de suspensión para propietarios
    location = /suspended/owner {
        proxy_pass http://erp_core;
        proxy_redirect off;
    }
    
    # Página de suspensión para clientes/visitantes  
    location = /suspended/client {
        proxy_pass http://erp_core;
        proxy_redirect off;
    }
    
    # API de estado del tenant (usada internamente)
    location ~ ^/api/tenant-status/ {
        proxy_pass http://erp_core;
        proxy_redirect off;
    }
    location ~ ^/api/tenant-suspension {
        proxy_pass http://erp_core;
        proxy_redirect off;
    }'

# Función para inyectar en ambos bloques server
inject_after_pattern() {
    local file="$1"
    local pattern="proxy_redirect http://joficreditosrd.sajet.us/ https://\$host/;"
    
    # Usar Python para inyección precisa (sed es problemático con multilinea)
    python3 << PYEOF
import re

with open("$file", "r") as f:
    content = f.read()

block = '''$SUSPENSION_BLOCK'''

# Encontrar la ÚLTIMA ocurrencia del patrón de proxy_redirect joficreditosrd
# (hay 2: una en server :8080 y otra en :8443)
pattern = "proxy_redirect http://joficreditosrd.sajet.us/ https://\$host/;"

# Insertar el bloque después de CADA ocurrencia
parts = content.split(pattern)
if len(parts) >= 2:
    new_content = (pattern + block).join(parts)
    with open("$file", "w") as f:
        f.write(new_content)
    print(f"  ✅ Bloque de suspensión inyectado ({len(parts)-1} bloques server)")
else:
    print("  ⚠️ Patrón no encontrado, inyectando antes de 'location /api/'")
    # Fallback: inyectar antes del primer location /api/
    new_content = content.replace(
        "    # === ERP_CORE (FastAPI) ===",
        block + "\n\n    # === ERP_CORE (FastAPI) ===",
        2  # Ambos server blocks
    )
    with open("$file", "w") as f:
        f.write(new_content)
    print("  ✅ Bloque inyectado (fallback)")
PYEOF
}

inject_after_pattern "$NGINX_CONF"

# Ahora inyectar la lógica de intercepción en location = / y location = /web
# Esto es lo que realmente redirige
python3 << 'PYEOF2'
with open("/etc/nginx/sites-enabled/odoo", "r") as f:
    content = f.read()

# Reemplazar los locations de Odoo root para agregar check de suspensión
# Original:  location = / { proxy_pass http://odoo; }
# Nuevo:     location = / { if ($tenant_suspended) { return 302 /suspended/client?reason=$suspension_reason; } proxy_pass http://odoo; }

old_root = 'location = / { proxy_pass http://odoo; }'
new_root = '''location = / {
        # Check tenant suspension
        if ($tenant_suspended) {
            return 302 /suspended/client?reason=$suspension_reason;
        }
        proxy_pass http://odoo;
    }'''

old_web = 'location = /web { proxy_pass http://odoo; }'
new_web = '''location = /web {
        # Check tenant suspension
        if ($tenant_suspended) {
            return 302 /suspended/client?reason=$suspension_reason;
        }
        proxy_pass http://odoo;
    }'''

content = content.replace(old_root, new_root)
content = content.replace(old_web, new_web)

# También interceptar el location / catch-all
old_catchall = '    location / { proxy_pass http://odoo; }'
new_catchall = '''    location / {
        # Check tenant suspension — catch-all
        if ($tenant_suspended) {
            return 302 /suspended/client?reason=$suspension_reason;
        }
        proxy_pass http://odoo;
    }'''

content = content.replace(old_catchall, new_catchall)

with open("/etc/nginx/sites-enabled/odoo", "w") as f:
    f.write(content)

print("  ✅ Intercepción de suspensión agregada a location /, /web y catch-all")
PYEOF2

# Validar
if nginx -t 2>&1; then
    nginx -s reload
    echo ""
    echo "  ✅ Nginx validado y recargado"
else
    echo ""
    echo "  ❌ Error en configuración de Nginx!"
    echo "  Restaurando backup..."
    LATEST_BACKUP=$(ls -t /etc/nginx/backups/odoo.bak.* | head -1)
    cp "$LATEST_BACKUP" /etc/nginx/sites-enabled/odoo
    nginx -s reload
    echo "  ⚠️ Backup restaurado"
    exit 1
fi
REMOTE_INJECT

echo ""
echo -e "${GREEN}━━━ Sistema de suspensión desplegado ━━━${NC}"
echo ""
echo "Uso:"
echo "  Suspender:   curl -X POST 'https://sajet.us/api/tenant-suspension/TENANT?reason=payment_failed&x_api_key=KEY'"
echo "  Reactivar:   curl -X DELETE 'https://sajet.us/api/tenant-suspension/TENANT?x_api_key=KEY'"
echo "  O usar:      /opt/Erp_core/scripts/tenant-suspend.sh suspend TENANT"
