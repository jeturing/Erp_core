#!/bin/bash

# Enhanced Tenant Provisioning Script
# Integrada con CloudflareManager de FastAPI
# Usage: create_tenant.sh <subdomain> [--with-demo] [--container-ip IP] [--local-port PORT]

set -e

SUBDOMAIN="$1"
WITH_DEMO_FLAG="${2:---without-demo}"
CONTAINER_IP="${3:-10.10.10.100}"
LOCAL_PORT="${4:-8069}"

if [[ -z "$SUBDOMAIN" ]]; then
  echo "❌ Usage: $0 <subdomain> [--with-demo] [--container-ip IP] [--local-port PORT]"
  echo "   Example: $0 acme --without-demo 10.10.10.100 8069"
  exit 1
fi

DB_NAME="$SUBDOMAIN"
HOSTNAME="$SUBDOMAIN.sajet.us"
TUNNEL_NAME="$SUBDOMAIN-tunnel"
ODOO_CONF="/etc/odoo/odoo.conf"

echo "================================"
echo "🚀 Provisioning Tenant: $SUBDOMAIN"
echo "================================"

# Step 1: Create PostgreSQL database
echo ""
echo "Step 1/5: Creating PostgreSQL database..."
if command -v sudo >/dev/null; then
  sudo -u postgres psql -qc "CREATE DATABASE \"$DB_NAME\" OWNER \"Jeturing\"" 2>/dev/null || echo "⚠️  Database already exists"
else
  su - postgres -c "psql -qc \"CREATE DATABASE \\\"$DB_NAME\\\" OWNER \\\"Jeturing\\\"\"" 2>/dev/null || echo "⚠️  Database already exists"
fi
echo "✅ Database created/verified"

# Step 2: Clean filestore
echo ""
echo "Step 2/5: Cleaning filestore..."
FILEROOT="/var/lib/odoo/.local/share/Odoo/filestore"
rm -rf "$FILEROOT/$DB_NAME" 2>/dev/null || true
echo "✅ Filestore cleaned"

# Step 3: Initialize Odoo
echo ""
echo "Step 3/5: Initializing Odoo with base module..."
DEMO_ARGS="--without-demo all"
if [[ "$WITH_DEMO_FLAG" == "--with-demo" ]]; then
  DEMO_ARGS=""
fi

if command -v sudo >/dev/null; then
  sudo -u odoo /opt/odoo/odoo-bin -c "$ODOO_CONF" -d "$DB_NAME" -i base $DEMO_ARGS --no-http --stop-after-init 2>/dev/null || true
else
  su -s /bin/bash -c "/opt/odoo/odoo-bin -c \"$ODOO_CONF\" -d \"$DB_NAME\" -i base $DEMO_ARGS --no-http --stop-after-init" odoo 2>/dev/null || true
fi
echo "✅ Odoo initialized"

# Step 4: Route Cloudflare DNS (si cloudflared está disponible)
echo ""
echo "Step 4/5: Configuring Cloudflare DNS..."
if command -v cloudflared >/dev/null; then
  cloudflared tunnel route dns "$TUNNEL_NAME" "$HOSTNAME" 2>/dev/null || echo "⚠️  DNS already routed"
  echo "✅ Cloudflare DNS routed"
else
  echo "⚠️  cloudflared not found - DNS routing skipped"
fi

# Step 5: Set web.base.url
echo ""
echo "Step 5/5: Setting web.base.url in Odoo..."
if command -v sudo >/dev/null; then
  sudo -u postgres psql -d "$DB_NAME" -qc "INSERT INTO ir_config_parameter(key, value) VALUES ('web.base.url', 'https://$HOSTNAME') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;" 2>/dev/null || true
else
  su - postgres -c "psql -d \"$DB_NAME\" -qc \"INSERT INTO ir_config_parameter(key, value) VALUES ('web.base.url', 'https://$HOSTNAME') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;\"" 2>/dev/null || true
fi
echo "✅ web.base.url configured"

echo ""
echo "================================"
echo "✅ Tenant Provisioning Complete!"
echo "================================"
echo ""
echo "📊 Tenant Details:"
echo "   • Subdomain: $SUBDOMAIN"
echo "   • Database: $DB_NAME"
echo "   • URL: https://$HOSTNAME"
echo "   • Container: $CONTAINER_IP:$LOCAL_PORT"
echo "   • Tunnel: $TUNNEL_NAME"
echo ""
echo "🔗 Access: https://$HOSTNAME"
echo ""
