#!/bin/bash
# ══════════════════════════════════════════════════════════════════
# Provisioning Dedicated Service: cliente1 on CT105
# ══════════════════════════════════════════════════════════════════
# Ejecutar desde host Proxmox (atenea) como root
# Usa pct exec contra CT105 (no SSH directo)
#
# Pasos:
#   1. Reestructurar nginx de CT105 con maps de upstream dedicado
#   2. Reservar puertos HTTP=9000, Chat=9500
#   3. Crear conf per-tenant
#   4. Instalar template systemd
#   5. Arrancar servicio y validar
#   6. Agregar routing nginx al puerto dedicado
#   7. Verificar acceso
# ══════════════════════════════════════════════════════════════════

set -euo pipefail

PCT=105
SUBDOMAIN="cliente1"
DB_NAME="cliente1"
HTTP_PORT=9000
CHAT_PORT=9500
NODE_IP="10.10.10.100"

# PostgreSQL centralizado en PCT 137
DB_HOST="10.10.10.137"
DB_PORT=5432
DB_USER="odoo17"
DB_PASS="Jtr17Pg2025!"

# Redis en PCT 149
REDIS_URL="redis://:JtrRedis2026!@10.10.10.7:6379/0"

NGINX_CONF="/etc/nginx/sites-enabled/odoo"
TENANT_CONF="/etc/odoo/tenant-${SUBDOMAIN}.conf"
SYSTEMD_TEMPLATE="/etc/systemd/system/odoo-tenant@.service"
OVERLAY_DIR="/opt/odoo/tenant-addons/${SUBDOMAIN}"

echo "═══════════════════════════════════════════════════════════"
echo "  Provisioning Dedicated Service: ${SUBDOMAIN}"
echo "  Nodo: CT${PCT} (${NODE_IP})"
echo "  Puertos: HTTP=${HTTP_PORT}, Chat=${CHAT_PORT}"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Paso 1: Reestructurar nginx con maps de upstream dedicado ──
echo "📌 Paso 1: Configurando maps de upstream dedicado en nginx..."

# Verificar si los maps ya existen
if pct exec ${PCT} -- grep -q 'odoo_http_upstream' ${NGINX_CONF} 2>/dev/null; then
    echo "   ✅ Maps de upstream dedicado ya existen, saltando..."
else
    echo "   📝 Agregando maps \$odoo_http_upstream y \$odoo_chat_upstream..."
    
    # Crear script temporal para editar nginx
    cat > /tmp/nginx_dedicated_setup.py << 'PYEOF'
import re, sys

with open(sys.argv[1], 'r') as f:
    content = f.read()

# 1. Agregar map $odoo_http_upstream antes de 'server {'
http_map = """
# Upstream HTTP por tenant: dedicated=puerto propio, shared=8069
map $host $odoo_http_upstream {
    default http://127.0.0.1:8069;
}

# Upstream Chat/LongPolling por tenant: dedicated=puerto propio, shared=8072
map $host $odoo_chat_upstream {
    default http://127.0.0.1:8072;
}

"""
    server_idx = content.find('\nserver {')
    if server_idx != -1:
        content = content[:server_idx] + http_map + content[server_idx:]

    # 2. Reemplazar proxy_pass estáticos por variables
    # proxy_pass http://odoo; → proxy_pass $odoo_http_upstream;
    # proxy_pass http://odoo-chat; → proxy_pass $odoo_chat_upstream;
    # NO tocar proxy_pass http://erp_core;
    content = content.replace('proxy_pass http://odoo;', 'proxy_pass $odoo_http_upstream;')
    content = content.replace('proxy_pass http://odoo-chat;', 'proxy_pass $odoo_chat_upstream;')

    with open(sys.argv[1], 'w') as f:
        f.write(content)

    print("Maps agregados y proxy_pass actualizados")
PYEOF

    # Copiar script al CT y ejecutar
    pct push ${PCT} /tmp/nginx_dedicated_setup.py /tmp/nginx_dedicated_setup.py
    pct exec ${PCT} -- python3 /tmp/nginx_dedicated_setup.py ${NGINX_CONF}
    
    # Validar nginx
    if pct exec ${PCT} -- nginx -t 2>&1; then
        pct exec ${PCT} -- systemctl reload nginx
        echo "   ✅ Nginx reestructurado y recargado"
    else
        echo "   ❌ nginx -t falló, revirtiendo..."
        pct exec ${PCT} -- cp ${NGINX_CONF}.bak.pre-dedicated ${NGINX_CONF}
        pct exec ${PCT} -- systemctl reload nginx
        exit 1
    fi
fi
echo ""

# ── Paso 2: Crear overlay de addons ──
echo "📁 Paso 2: Creando overlay de addons..."
pct exec ${PCT} -- bash -c "
    mkdir -p ${OVERLAY_DIR}
    # Symlink addons base
    if [ -d /opt/odoo/extra-addons ]; then
        for d in /opt/odoo/extra-addons/*/; do
            name=\$(basename \"\$d\")
            ln -sfn \"\$d\" \"${OVERLAY_DIR}/\${name}\" 2>/dev/null || true
        done
    fi
    echo 'Overlay creado en ${OVERLAY_DIR}'
    ls ${OVERLAY_DIR}/ | head -5
"
echo "   ✅ Overlay creado"
echo ""

# ── Paso 3: Generar conf per-tenant ──
echo "📝 Paso 3: Generando conf Odoo per-tenant..."
cat > /tmp/tenant-${SUBDOMAIN}.conf << CONFEOF
[options]
; === Tenant Dedicated Config: ${SUBDOMAIN} ===
db_host = ${DB_HOST}
db_port = ${DB_PORT}
db_user = ${DB_USER}
db_password = ${DB_PASS}
db_name = ${DB_NAME}
dbfilter = ^${DB_NAME}\$

; Puertos dedicados
http_port = ${HTTP_PORT}
longpolling_port = ${CHAT_PORT}

; Performance
workers = 2
max_cron_threads = 1
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 600
limit_time_real = 1200

; Paths
data_dir = /opt/odoo/.local/share/Odoo-${SUBDOMAIN}
addons_path = /opt/odoo/odoo/addons,/opt/odoo/extra-addons,${OVERLAY_DIR}
logfile = /var/log/odoo/odoo-${SUBDOMAIN}.log

; Session Redis
session_redis = True
session_redis_url = ${REDIS_URL}
session_redis_prefix = session:${SUBDOMAIN}:

; Security
proxy_mode = True
list_db = False
admin_passwd = False
CONFEOF

pct push ${PCT} /tmp/tenant-${SUBDOMAIN}.conf ${TENANT_CONF}
echo "   ✅ Conf desplegada: ${TENANT_CONF}"
echo ""

# ── Paso 4: Instalar template systemd ──
echo "⚙️  Paso 4: Instalando template systemd..."
if pct exec ${PCT} -- test -f ${SYSTEMD_TEMPLATE}; then
    echo "   ✅ Template ya existe, saltando..."
else
    cat > /tmp/odoo-tenant@.service << 'SVCEOF'
[Unit]
Description=Odoo Dedicated Service for tenant %i
After=network.target postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
ExecStart=/opt/odoo/venv/bin/python3 /opt/odoo/odoo-bin -c /etc/odoo/tenant-%i.conf
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/odoo/odoo-%i.log
StandardError=append:/var/log/odoo/odoo-%i-error.log

[Install]
WantedBy=multi-user.target
SVCEOF

    pct push ${PCT} /tmp/odoo-tenant@.service ${SYSTEMD_TEMPLATE}
    pct exec ${PCT} -- systemctl daemon-reload
    echo "   ✅ Template systemd instalado"
fi
echo ""

# ── Paso 5: Habilitar y arrancar servicio ──
echo "🚀 Paso 5: Habilitando y arrancando servicio..."
SERVICE_NAME="odoo-tenant@${SUBDOMAIN}"

# Crear directorio de datos y logs con permisos correctos
pct exec ${PCT} -- bash -c "
    mkdir -p /opt/odoo/.local/share/Odoo-${SUBDOMAIN}
    chown -R odoo:odoo /opt/odoo/.local/share/Odoo-${SUBDOMAIN}
    touch /var/log/odoo/odoo-${SUBDOMAIN}.log
    touch /var/log/odoo/odoo-${SUBDOMAIN}-error.log
    chown odoo:odoo /var/log/odoo/odoo-${SUBDOMAIN}*.log
"

pct exec ${PCT} -- systemctl enable ${SERVICE_NAME}
pct exec ${PCT} -- systemctl start ${SERVICE_NAME}
echo "   Servicio iniciado, esperando arranque..."

# Esperar hasta 60 segundos a que responda
for i in $(seq 1 12); do
    sleep 5
    HTTP_CODE=$(pct exec ${PCT} -- curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${HTTP_PORT}/web/login" 2>/dev/null || echo "000")
    echo "   ⏳ Intento ${i}/12: HTTP ${HTTP_CODE}"
    if [ "${HTTP_CODE}" = "200" ] || [ "${HTTP_CODE}" = "303" ]; then
        echo "   ✅ Servicio dedicado respondiendo en puerto ${HTTP_PORT}"
        break
    fi
    if [ ${i} -eq 12 ]; then
        echo "   ⚠️  Timeout esperando servicio. Verificando status..."
        pct exec ${PCT} -- systemctl status ${SERVICE_NAME} --no-pager | head -15
        pct exec ${PCT} -- tail -20 /var/log/odoo/odoo-${SUBDOMAIN}.log 2>/dev/null || true
        pct exec ${PCT} -- tail -20 /var/log/odoo/odoo-${SUBDOMAIN}-error.log 2>/dev/null || true
    fi
done
echo ""

# ── Paso 6: Configurar routing nginx al puerto dedicado ──
echo "🌐 Paso 6: Configurando routing nginx..."

# Agregar entries al map
cat > /tmp/nginx_add_dedicated_route.py << PYEOF
import re, sys

subdomain = "${SUBDOMAIN}"
http_port = ${HTTP_PORT}
chat_port = ${CHAT_PORT}
full_domain = f"{subdomain}.sajet.us"

with open(sys.argv[1], 'r') as f:
    content = f.read()

# Agregar al map \$odoo_http_upstream
http_entry = f"    {full_domain} http://127.0.0.1:{http_port};"
pattern_http = r'(map \$host \$odoo_http_upstream \{[^}]*)(})'
match_http = re.search(pattern_http, content, re.DOTALL)
if match_http and full_domain not in match_http.group(1):
    content = content[:match_http.start(2)] + f"\n{http_entry}\n" + content[match_http.start(2):]
    print(f"Added HTTP: {full_domain} -> :{http_port}")

# Agregar al map \$odoo_chat_upstream
chat_entry = f"    {full_domain} http://127.0.0.1:{chat_port};"
pattern_chat = r'(map \$host \$odoo_chat_upstream \{[^}]*)(})'
match_chat = re.search(pattern_chat, content, re.DOTALL)
if match_chat and full_domain not in match_chat.group(1):
    content = content[:match_chat.start(2)] + f"\n{chat_entry}\n" + content[match_chat.start(2):]
    print(f"Added Chat: {full_domain} -> :{chat_port}")

with open(sys.argv[1], 'w') as f:
    f.write(content)

print("Routing entries added")
PYEOF

pct push ${PCT} /tmp/nginx_add_dedicated_route.py /tmp/nginx_add_dedicated_route.py
pct exec ${PCT} -- python3 /tmp/nginx_add_dedicated_route.py ${NGINX_CONF}

if pct exec ${PCT} -- nginx -t 2>&1; then
    pct exec ${PCT} -- systemctl reload nginx
    echo "   ✅ Nginx routing actualizado"
else
    echo "   ❌ nginx -t falló!"
    exit 1
fi
echo ""

# ── Paso 7: Verificar ──
echo "🔍 Paso 7: Verificación final..."
echo ""
echo "=== Status del servicio ==="
pct exec ${PCT} -- systemctl is-active ${SERVICE_NAME}

echo ""
echo "=== Test directo HTTP ==="
pct exec ${PCT} -- curl -s -o /dev/null -w 'HTTP %{http_code}\n' "http://127.0.0.1:${HTTP_PORT}/web/login"

echo ""
echo "=== Test via nginx (8443 - como lo ve Cloudflare) ==="
pct exec ${PCT} -- curl -sk -o /dev/null -w 'HTTP %{http_code}\n' -H "Host: ${SUBDOMAIN}.sajet.us" "https://127.0.0.1:8443/web/login"

echo ""
echo "=== Maps de upstream dedicado ==="
pct exec ${PCT} -- grep -A5 'odoo_http_upstream' ${NGINX_CONF} | head -10
echo "..."
pct exec ${PCT} -- grep -A5 'odoo_chat_upstream' ${NGINX_CONF} | head -10

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Provisioning completado: ${SUBDOMAIN}"
echo "  Servicio: ${SERVICE_NAME}"
echo "  HTTP:     ${HTTP_PORT}"
echo "  Chat:     ${CHAT_PORT}"
echo "  URL:      https://${SUBDOMAIN}.sajet.us"
echo ""
echo "  Cloudflare: wildcard *.sajet.us ya apunta al tunnel de CT105"
echo "  Nginx:      ${SUBDOMAIN}.sajet.us → 127.0.0.1:${HTTP_PORT}"
echo "═══════════════════════════════════════════════════════════"
