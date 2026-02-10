#!/bin/bash
# Crear nuevos tenants manualmente (para testing)
# Uso: ./create_tenant.sh subdomain admin_password [domain] [template_db]

set -e

SUBDOMAIN="${1:-}"
ADMIN_PASSWORD="${2:-}"
DOMAIN="${3:-sajet.us}"
TEMPLATE_DB="${4:-tcs}"

if [ -z "$SUBDOMAIN" ] || [ -z "$ADMIN_PASSWORD" ]; then
    echo "Uso: $0 subdomain admin_password [domain] [template_db]"
    echo "Ejemplo: $0 cliente_nuevo secreto123 sajet.us tcs"
    exit 1
fi

SUBDOMAIN=$(echo "$SUBDOMAIN" | tr '[:upper:]' '[:lower:]' | tr '-' '_')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Creando tenant: $SUBDOMAIN"
echo "Dominio: $DOMAIN"
echo "Plantilla: $TEMPLATE_DB"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Detectar usuario PostgreSQL
PG_USER=$(sudo -u postgres psql -t -c "SELECT usename FROM pg_user WHERE usename NOT IN ('postgres') LIMIT 1;" | tr -d ' ')
PG_USER=${PG_USER:-odoo}
echo "[*] Usuario PostgreSQL: $PG_USER"

# Verificar si ya existe
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$SUBDOMAIN"; then
    echo "[!] Error: Base de datos '$SUBDOMAIN' ya existe"
    exit 1
fi

echo "[*] Terminando conexiones a plantilla..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$TEMPLATE_DB' AND pid <> pg_backend_pid();" >/dev/null 2>&1

echo "[*] Creando BD desde plantilla..."
sudo -u postgres createdb -O "$PG_USER" -T "$TEMPLATE_DB" "$SUBDOMAIN"

echo "[*] Configurando BD..."
sudo -u postgres psql -d "$SUBDOMAIN" << SQL
UPDATE res_users SET password = '$ADMIN_PASSWORD' WHERE login = 'admin';
UPDATE res_company SET name = '$SUBDOMAIN' WHERE id = 1;
UPDATE res_partner SET name = '$SUBDOMAIN' WHERE id = 1;
UPDATE ir_config_parameter SET value = gen_random_uuid()::text WHERE key = 'database.uuid';
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
VALUES ('web.base.url', 'https://$SUBDOMAIN.$DOMAIN', NOW(), NOW(), 1, 1)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
SQL

echo "[✓] Tenant '$SUBDOMAIN' creado exitosamente"
echo "[✓] URL: https://$SUBDOMAIN.$DOMAIN"
