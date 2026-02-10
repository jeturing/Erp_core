# Quick Start - JWT Authentication Testing

## Start the Server

```bash
cd /opt/onboarding-system
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload
```

## Access the Application

### 1. Web Browser Login
Navigate to: **http://localhost:4443/login**

**Credentials**:
- Username: `admin`
- Password: `admin123`

After successful login, you'll be redirected to the admin dashboard at `http://localhost:4443/admin`.

### 2. Command Line Testing

**Get Token**:
```bash
curl -X POST http://localhost:4443/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq .
```

**Use Token to Access Protected Endpoint**:
```bash
# Save token from login response
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Access metrics
curl -X GET http://localhost:4443/api/dashboard/metrics \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# Access tenants
curl -X GET http://localhost:4443/api/tenants \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

## Test Script

Save this as `test_jwt.sh` and run with `bash test_jwt.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:4443"
CREDENTIALS='{"username":"admin","password":"admin123"}'

echo "🔐 Step 1: Login and get token"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/admin/login" \
  -H "Content-Type: application/json" \
  -d "$CREDENTIALS")

TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "❌ Login failed!"
    echo "$RESPONSE" | jq .
    exit 1
fi

echo "✅ Token received: ${TOKEN:0:50}..."
echo ""

echo "📊 Step 2: Fetch dashboard metrics"
curl -s -X GET "$BASE_URL/api/dashboard/metrics" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

echo "🏢 Step 3: Fetch tenants list"
curl -s -X GET "$BASE_URL/api/tenants" \
  -H "Authorization: Bearer $TOKEN" | jq .
echo ""

echo "❌ Step 4: Try accessing without token (should fail)"
curl -s -X GET "$BASE_URL/api/dashboard/metrics" | jq .
echo ""

echo "✅ All tests completed!"
```

## Environment Variables

Create/update `.env` file:

```
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_WEBHOOK_SECRET=whsec_your_secret
DATABASE_URL=postgresql://jeturing:321Abcd@localhost/onboarding_db
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-prod
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## Key Files

- **Login Page**: `templates/admin_login.html`
- **Dashboard**: `templates/admin_dashboard.html`
- **Backend**: `app/main.py` (JWT routes and protection)
- **Docs**: `docs/JWT_AUTHENTICATION.md` (detailed reference)

## Features

✅ JWT token-based authentication
✅ Token stored in localStorage
✅ Auto-include token in API requests
✅ Token expiration (24 hours default)
✅ Logout functionality
✅ Protected routes (`/admin`, `/api/dashboard/metrics`, `/api/tenants`)
✅ Error handling and user feedback
✅ Responsive login UI

## What's Next?

After testing JWT auth, you can:
1. Integrate remaining templates (Billing, Reports, Logs)
2. Add PATCH/DELETE endpoints for tenant management
3. Implement 2FA for additional security
4. Add role-based access control (RBAC)

See `docs/INTEGRATION_SUMMARY.md` for the complete roadmap.
