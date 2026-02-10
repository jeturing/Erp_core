#!/bin/bash

set -e

# Usage: create_tenant.sh <subdomain> [--with-demo]
# Creates PostgreSQL DB named <subdomain>, initializes Odoo without demo by default,
# and routes Cloudflare DNS to the existing tunnel.

SUBDOMAIN="$1"
WITH_DEMO_FLAG="$2"

if [[ -z "$SUBDOMAIN" ]]; then
  echo "Usage: $0 <subdomain> [--with-demo]"
  exit 1
fi

DB_NAME="$SUBDOMAIN"
HOSTNAME="$SUBDOMAIN.sajet.us"
ODOO_CONF="/etc/odoo/odoo.conf"
TUNNEL_NAME="tcs-sajet-tunnel"

echo "🔧 Creating PostgreSQL database '$DB_NAME' owned by Jeturing..."
if command -v sudo >/dev/null; then
  sudo -u postgres psql -qc "CREATE DATABASE \"$DB_NAME\" OWNER \"Jeturing\"" || true
else
  su - postgres -c "psql -qc \"CREATE DATABASE \\\"$DB_NAME\\\" OWNER \\\"Jeturing\\\"\"" || true
fi

echo "🧹 Cleaning filestore for '$DB_NAME' (if exists)..."
FILEROOT="/var/lib/odoo/.local/share/Odoo/filestore"
rm -rf "$FILEROOT/$DB_NAME" || true

echo "📦 Initializing Odoo database '$DB_NAME' (base module)..."
DEMO_ARGS="--without-demo all"
if [[ "$WITH_DEMO_FLAG" == "--with-demo" ]]; then
  DEMO_ARGS=""
fi
if command -v sudo >/dev/null; then
  sudo -u odoo /opt/odoo/odoo-bin -c "$ODOO_CONF" -d "$DB_NAME" -i base $DEMO_ARGS --no-http --stop-after-init
else
  su -s /bin/bash -c "/opt/odoo/odoo-bin -c \"$ODOO_CONF\" -d \"$DB_NAME\" -i base $DEMO_ARGS --no-http --stop-after-init" odoo
fi

echo "🌐 Routing Cloudflare DNS for $HOSTNAME -> tunnel $TUNNEL_NAME..."
cloudflared tunnel route dns "$TUNNEL_NAME" "$HOSTNAME"

echo "🔗 Setting web.base.url to https://$HOSTNAME ..."
if command -v sudo >/dev/null; then
  sudo -u postgres psql -d "$DB_NAME" -qc "INSERT INTO ir_config_parameter(key, value) VALUES ('web.base.url', 'https://$HOSTNAME') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;" || true
else
  su - postgres -c "psql -d \"$DB_NAME\" -qc \"INSERT INTO ir_config_parameter(key, value) VALUES ('web.base.url', 'https://$HOSTNAME') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;\"" || true
fi

echo "✅ Tenant '$SUBDOMAIN' ready at https://$HOSTNAME"
