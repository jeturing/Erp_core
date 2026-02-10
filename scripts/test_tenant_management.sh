#!/bin/bash
#
# Script de prueba para gestión de tenants
# Cambio de clave y suspensión
#

set -e

API_KEY="prov-key-2026-secure"
APP_SERVER="http://localhost:4443"
TENANT="techeels"

echo "═════════════════════════════════════════════════════════"
echo "Pruebas de Gestión de Tenants"
echo "═════════════════════════════════════════════════════════"
echo ""

# Test 1: Listar tenants
echo "1️⃣  Listando tenants..."
curl -s -X GET \
  -H "X-API-KEY: $API_KEY" \
  "$APP_SERVER/api/tenants" | jq '.'
echo ""
echo ""

# Test 2: Cambiar contraseña
echo "2️⃣  Cambiando contraseña de admin para $TENANT..."
curl -s -X PUT \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"subdomain\": \"$TENANT\",
    \"new_password\": \"NuevaClaveSegura2026!\"
  }" \
  "$APP_SERVER/api/provisioning/tenant/password" | jq '.'
echo ""
echo "✅ Nueva contraseña: NuevaClaveSegura2026!"
echo ""
echo ""

# Test 3: Suspender tenant
echo "3️⃣  Suspendiendo tenant $TENANT..."
curl -s -X PUT \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"subdomain\": \"$TENANT\",
    \"suspend\": true,
    \"reason\": \"Prueba de suspensión automática\"
  }" \
  "$APP_SERVER/api/provisioning/tenant/suspend" | jq '.'
echo ""
echo "✅ Tenant suspendido"
echo ""
echo ""

# Test 4: Reactivar tenant
echo "4️⃣  Reactivando tenant $TENANT..."
curl -s -X PUT \
  -H "X-API-KEY: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"subdomain\": \"$TENANT\",
    \"suspend\": false
  }" \
  "$APP_SERVER/api/provisioning/tenant/suspend" | jq '.'
echo ""
echo "✅ Tenant reactivado"
echo ""
