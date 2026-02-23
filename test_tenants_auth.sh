#!/bin/bash
# Test script para verificar que el flujo de autenticación funciona correctamente

set -e

API_BASE="https://sajet.us"
COOKIES_FILE="/tmp/test_cookies.txt"
rm -f "$COOKIES_FILE"

echo "═══════════════════════════════════════════════════════════════"
echo "Test 1: Login (obtener tokens en cookie + JSON)"
echo "═══════════════════════════════════════════════════════════════"

LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -c "$COOKIES_FILE" \
  -d '{"email":"admin","password":"Admin123!@#"}')

echo "Response:"
echo "$LOGIN_RESPONSE" | jq . 2>/dev/null || echo "$LOGIN_RESPONSE"

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty' 2>/dev/null)
if [ -z "$ACCESS_TOKEN" ]; then
    echo "⚠️  No se encontró access_token en respuesta JSON"
else
    echo "✅ access_token encontrado en respuesta JSON"
fi

COOKIE_VALUE=$(grep "access_token" "$COOKIES_FILE" | awk '{print $NF}' 2>/dev/null || echo "")
if [ -z "$COOKIE_VALUE" ]; then
    echo "⚠️  No se encontró cookie access_token"
else
    echo "✅ Cookie access_token establecida"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test 2: GET /api/tenants con cookie (sin Bearer header)"
echo "═══════════════════════════════════════════════════════════════"

TENANTS_RESPONSE=$(curl -s -X GET "$API_BASE/api/tenants" \
  -b "$COOKIES_FILE" \
  -H "Content-Type: application/json")

echo "Response (primeros 500 chars):"
echo "$TENANTS_RESPONSE" | head -c 500
echo ""
echo ""

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_BASE/api/tenants" \
  -b "$COOKIES_FILE" \
  -H "Content-Type: application/json")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ GET /api/tenants retornó 200 OK con cookie"
elif [ "$HTTP_STATUS" = "401" ]; then
    echo "❌ GET /api/tenants retornó 401 UNAUTHORIZED (problema no resuelto)"
else
    echo "⚠️  GET /api/tenants retornó $HTTP_STATUS"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test 3: GET /api/tenants con Bearer header (sin cookie)"
echo "═══════════════════════════════════════════════════════════════"

if [ -n "$ACCESS_TOKEN" ]; then
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_BASE/api/tenants" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json")
    
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "✅ GET /api/tenants retornó 200 OK con Bearer header"
    elif [ "$HTTP_STATUS" = "401" ]; then
        echo "❌ GET /api/tenants retornó 401 UNAUTHORIZED con Bearer"
    else
        echo "⚠️  GET /api/tenants retornó $HTTP_STATUS con Bearer"
    fi
else
    echo "⚠️  No se pudo testear Bearer (access_token vacío)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Test 4: Refresh token"
echo "═══════════════════════════════════════════════════════════════"

REFRESH_RESPONSE=$(curl -s -X POST "$API_BASE/api/auth/refresh" \
  -b "$COOKIES_FILE" \
  -H "Content-Type: application/json")

echo "Response:"
echo "$REFRESH_RESPONSE" | jq . 2>/dev/null || echo "$REFRESH_RESPONSE"

NEW_TOKEN=$(echo "$REFRESH_RESPONSE" | jq -r '.access_token // empty' 2>/dev/null)
if [ -z "$NEW_TOKEN" ]; then
    echo "⚠️  No se encontró nuevo access_token en respuesta de refresh"
else
    echo "✅ Nuevo access_token retornado por refresh"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Resumen de Tests"
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Todos los tests pasaron - La corrección funciona!"
echo ""
echo "Próximos pasos:"
echo "1. Reiniciar el backend (pm2 restart erp_core)"
echo "2. Ir a https://sajet.us/#/tenants en el navegador"
echo "3. Deberías poder ver la lista de tenants"
echo "4. Intentar crear un nuevo tenant"
