#!/bin/bash

# Simple test script for JWT authentication

BASE_URL="http://localhost:4443"

echo "Testing JWT Authentication"
echo "=========================="
echo ""

# Test 1: Login
echo "Test 1: POST /api/admin/login"
echo "-----------------------------"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

echo "Response: $RESPONSE"
echo ""

# Extract token
TOKEN=$(echo "$RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed - no token received"
    exit 1
fi

echo "✅ Token received: ${TOKEN:0:50}..."
echo ""

# Test 2: Access protected endpoint with token
echo "Test 2: GET /api/dashboard/metrics (with token)"
echo "-----------------------------------------------"
curl -s -X GET "$BASE_URL/api/dashboard/metrics" \
  -H "Authorization: Bearer $TOKEN"
echo ""
echo ""

# Test 3: Access protected endpoint without token (should fail)
echo "Test 3: GET /api/dashboard/metrics (without token - should fail)"
echo "--------------------------------------------------------------"
curl -s -X GET "$BASE_URL/api/dashboard/metrics"
echo ""
echo ""

# Test 4: Check login page
echo "Test 4: GET /login"
echo "------------------"
echo "HTTP Status:"
curl -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/login"
echo ""
echo ""

# Test 5: Check admin dashboard (without authentication - should redirect or show login)
echo "Test 5: GET /admin (checking authentication)"
echo "-------------------------------------------"
echo "HTTP Status:"
curl -s -o /dev/null -w "%{http_code}" -X GET "$BASE_URL/admin"
echo ""

echo ""
echo "✅ All tests completed!"
