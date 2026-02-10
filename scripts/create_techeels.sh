#!/bin/bash
#
# Script para crear tenant "Techeels" en PCT 105
# Ejecutar en el servidor PCH 160 o en cualquier servidor con curl
#

TENANT_SUBDOMAIN="techeels"
ADMIN_PASSWORD="Techeels2026!"
ODOO_NODE_IP="10.10.10.100"
ODOO_NODE_PORT="8070"
API_KEY="prov-key-2026-secure"
DOMAIN="sajet.us"

echo "═════════════════════════════════════════════════════════"
echo "Creando tenant: $TENANT_SUBDOMAIN"
echo "═════════════════════════════════════════════════════════"
echo ""

# Crear tenant en la API local del nodo Odoo
echo "📡 Contactando API en $ODOO_NODE_IP:$ODOO_NODE_PORT..."

RESPONSE=$(curl -s -X POST \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"subdomain\": \"$TENANT_SUBDOMAIN\",
    \"admin_password\": \"$ADMIN_PASSWORD\",
    \"domain\": \"$DOMAIN\",
    \"template_db\": \"tcs\"
  }" \
  "http://$ODOO_NODE_IP:$ODOO_NODE_PORT/api/tenant")

echo ""
echo "Respuesta de la API:"
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
echo ""

# Verificar si fue exitoso
if echo "$RESPONSE" | grep -q '"success": true'; then
    echo "✅ Tenant creado exitosamente"
    echo ""
    echo "Detalles:"
    URL=$(echo "$RESPONSE" | jq -r '.url' 2>/dev/null)
    DB=$(echo "$RESPONSE" | jq -r '.database' 2>/dev/null)
    DNS=$(echo "$RESPONSE" | jq -r '.dns_created' 2>/dev/null)
    
    echo "  • URL: $URL"
    echo "  • Base de datos: $DB"
    echo "  • DNS creado: $DNS"
    echo "  • Usuario: admin"
    echo "  • Contraseña: $ADMIN_PASSWORD"
    echo ""
    echo "⏳ Esperando a que el servidor Odoo se configure..."
    sleep 3
    echo ""
    echo "🌐 Accede a la aplicación en:"
    echo "   https://$TENANT_SUBDOMAIN.$DOMAIN"
    echo ""
else
    echo "❌ Error creando tenant"
    exit 1
fi
