# Provisioning API - Public Tenant Management

> **Última actualización:** 2026-04-28  
> **Estado:** ✅ Production Ready  
> **Authentication:** Managed API keys (X-API-Key: sk_live_*)

---

## Overview

La API pública de provisioning permite crear, eliminar y gestionar tenants Odoo desde cualquier aplicación cliente externa a través de HTTPS. El flujo es **orquestado en 3 etapas**:

1. **Tenant Agent** (PCT 201:8070) — Clone DB, create systemd service, manage filestore
2. **Cloudflare DNS** (sajet.us zone) — Create CNAME pointing to tunnel
3. **Tunnel Configurations API** — Add ingress rules routing to new tenant ports

---

## Authentication

### Managed API Keys (Recommended)

**Format:** `sk_live_{prefix}_{secret_part}` (managed keys with full access)

```bash
# Create key via utility script
python3 /opt/Erp_core/scripts/create_provisioning_apikey.py
```

**Output:**
```
✅ API KEY CREADA
key_id   : sk_live_XXXXXXXXXXXXXXXX
FULL_KEY : sk_live_XXXXXXXXXXXXXXXX_XXXXXXXXXXXXXXXXXXXXXXXX

Header usage: X-API-Key: sk_live_XXXXXXXXXXXXXXXX_XXXXXXXXXXXXXXXXXXXXXXXX
```

**Characteristics:**
- Scope: `admin` (covers all provisioning operations)
- Tier: `enterprise` (no quota limits)
- Permissions: `["*"]` (wildcard = all operations)
- Access Level: `SENSITIVE` (enforced by gateway)
- Rate Limits: 60 RPM, 10000 RPD

### Legacy Keys (Deprecated, PARTNER level)

```bash
# Old format (pre-managed keys)
X-API-Key: prov-key-2026-secure
```

⚠️ **Deprecation Notice:** Legacy keys (`prov-key-*`) are PARTNER level (cannot access SENSITIVE endpoints). **Migrate to managed keys immediately.**

---

## Endpoints

### Base URL

```
https://sajet.us/api/provisioning
```

All requests require header:
```
X-API-Key: sk_live_<full_key>
Content-Type: application/json
```

---

## 1. Create Tenant

**Endpoint:** `POST /api/provisioning/tenant`

**Request:**
```json
{
  "subdomain": "cliente2",
  "admin_password": "SecurePassword123!",
  "domain": "sajet.us",
  "template_db": "template_tenant",
  "language": "es_DO"
}
```

**Parameters:**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `subdomain` | string | ✅ | Alphanumeric + hyphens, 3-30 chars, unique |
| `admin_password` | string | ✅ | Min 12 chars, enforced in Odoo login |
| `domain` | string | ✅ | Base domain (e.g., `sajet.us`) |
| `template_db` | string | ⚠️ | Defaults to `template_tenant` if omitted |
| `language` | string | ⚠️ | Defaults to `es_DO` (Spanish, Dominican Republic) |

**Success Response (HTTP 201):**
```json
{
  "success": true,
  "subdomain": "cliente2",
  "url": "https://cliente2.sajet.us",
  "message": "Tenant cliente2 provisionado | agent=True dns=True tunnel=True",
  "database": "cliente2",
  "dns_created": true,
  "server": "primary",
  "agent_status": "ok",
  "tunnel_status": "rules_added"
}
```

**Error Responses:**

| Status | Scenario | Detail |
|--------|----------|--------|
| 400 | Subdomain already exists | `{"success": false, "reason": "already_exists"}` |
| 400 | Invalid subdomain format | `{"success": false, "reason": "invalid_subdomain"}` |
| 401 | Missing or invalid API key | `{"detail": "API key requerida"}` |
| 403 | Insufficient scope (legacy key) | `{"detail": "scope_denied"}` |
| 500 | Agent/DNS/Tunnel failure | `{"success": false, "error": "...details..."}` |

**Example (curl):**
```bash
curl -X POST https://sajet.us/api/provisioning/tenant \
  -H "X-API-Key: sk_live_XXXXXXX_XXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "cliente2",
    "admin_password": "AdminPass@2026",
    "domain": "sajet.us",
    "template_db": "template_tenant",
    "language": "es_DO"
  }'
```

---

## 2. Delete Tenant

**Endpoint:** `DELETE /api/provisioning/tenant`

**Request:**
```json
{
  "subdomain": "cliente2",
  "domain": "sajet.us",
  "delete_dns": true
}
```

**Parameters:**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `subdomain` | string | ✅ | Tenant subdomain to delete |
| `domain` | string | ✅ | Base domain |
| `delete_dns` | bool | ⚠️ | Defaults to `true`; remove CNAME record |

**Success Response (HTTP 200):**
```json
{
  "success": true,
  "subdomain": "cliente2",
  "tunnel_rules_removed": 3,
  "dns_deleted": true,
  "database_deleted": true,
  "conf_deleted": true,
  "filestore_deleted": true
}
```

⚠️ **Note:** If DELETE runs against tenant provisioned via old config.yml method, `tunnel_rules_removed=0` (no rules found in API; agent still cleans DB/conf/filestore).

**Error Responses:**

| Status | Scenario |
|--------|----------|
| 404 | Tenant not found or already deleted |
| 401 | Missing/invalid API key |
| 403 | Insufficient scope |
| 500 | Partial failure (see `database_deleted`, `dns_deleted` fields) |

**Example (curl):**
```bash
curl -X DELETE https://sajet.us/api/provisioning/tenant \
  -H "X-API-Key: sk_live_XXXXXXX_XXXXXXX" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "cliente2",
    "domain": "sajet.us",
    "delete_dns": true
  }'
```

---

## 3. List Tenants

**Endpoint:** `GET /api/provisioning/tenants`

**Query Parameters:** (none)

**Success Response (HTTP 200):**
```json
{
  "tenants": [
    {
      "name": "agroliferd",
      "url": "https://agroliferd.sajet.us",
      "database": "agroliferd",
      "port": 9001,
      "status": "active"
    },
    {
      "name": "cliente2",
      "url": "https://cliente2.sajet.us",
      "database": "cliente2",
      "port": 9003,
      "status": "active"
    },
    ...
  ],
  "total": 20,
  "server": "Servidor Principal"
}
```

**Example (curl):**
```bash
curl https://sajet.us/api/provisioning/tenants \
  -H "X-API-Key: sk_live_XXXXXXX_XXXXXXX" | jq '.total'
# Output: 20
```

---

## 4. Change Admin Password (Optional)

**Endpoint:** `PUT /api/provisioning/tenant/password`

**Request:**
```json
{
  "subdomain": "cliente2",
  "new_password": "NewPassword@2026"
}
```

**Success Response (HTTP 200):**
```json
{
  "success": true,
  "subdomain": "cliente2",
  "message": "Password actualizado"
}
```

---

## 5. Get Tenant Accounts (Optional)

**Endpoint:** `GET /api/provisioning/tenant/accounts/{subdomain}`

**Success Response (HTTP 200):**
```json
{
  "subdomain": "cliente2",
  "accounts": [
    {
      "id": 1,
      "name": "Administrator",
      "email": "admin@cliente2.sajet.us",
      "login": "admin",
      "active": true
    }
  ]
}
```

---

## Authentication Deep Dive

### Gateway Architecture

SAJET uses **dual-layer authentication**:

1. **Entry Layer** (`_require_api_key()` in provisioning.py)
   - Accepts legacy keys (`prov-key-*`) OR managed keys (`sk_live_*`)
   - Quick format validation

2. **Enforcement Layer** (`gateway_api_key_dependency(SENSITIVE)` at router level)
   - **Managed keys:** Validates against `api_keys` table, checks `permissions` field
   - **Legacy keys:** Checks against `PROVISIONING_API_KEY` env var, limited to PARTNER level
   - Enforces `ApiAccessLevel.SENSITIVE` (required for provisioning)

### Permission Hierarchy

```
INTERNAL (level 1)
  ├── Can call any INTERNAL endpoint
  └── ↓

PARTNER (level 2)
  ├── Can call INTERNAL + PARTNER endpoints
  ├── Cannot call SENSITIVE
  └── ↓

SENSITIVE (level 3)
  ├── Can call INTERNAL + PARTNER + SENSITIVE
  ├── Provisioning endpoints require this
  └── Examples: /api/provisioning/*, /api/admin/*
```

**Managed Key Permissions:**
- `["*"]` = wildcard (pass all levels)
- `["gateway:level:sensitive"]` = explicit SENSITIVE level
- Legacy keys capped at PARTNER level automatically

### Rate Limiting

| Key Type | RPM (Request/Min) | RPD (Request/Day) |
|----------|-------------------|-------------------|
| Managed (enterprise tier) | 60 | 10000 |
| Legacy provisioning key | 120 | 50000 |

Exceeded → HTTP 429 with `retry-after` header.

---

## Provisioning Orchestration Flow

```
┌─ User calls POST /api/provisioning/tenant
│
├─ Stage 1: Tenant-Agent (PCT 201:8070)
│  ├─ Clone template_tenant → client2 DB
│  ├─ Create /etc/odoo/tenant-client2.conf
│  ├─ systemctl start odoo-tenant@client2
│  ├─ Copy filestore + addons
│  └─ Return: http_port=9003, longpolling_port=9503, agent_status="ok"
│
├─ Stage 2: Cloudflare DNS (sajet.us zone)
│  ├─ Create CNAME: client2.sajet.us → 1b41dd54-...cfargotunnel.com
│  └─ Return: dns_created=true
│
└─ Stage 3: Tunnel Configurations API
   ├─ Fetch current tunnel config from Cloudflare Zero Trust
   ├─ Insert 3 ingress rules before fallback:
   │  ├─ WebSocket: /websocket* → http://10.10.20.201:9503
   │  ├─ Longpolling: /longpolling* → http://10.10.20.201:9503
   │  └─ Catch-all: * → http://10.10.20.201:9003
   ├─ PUT updated config back
   └─ Return: tunnel_status="rules_added"

Final Result:
  ✅ client2.sajet.us → CF tunnel → Agent:9003/9503 → Odoo login page
```

---

## Troubleshooting

### Tenant Provisioned but No Public Access

**Symptom:** `curl https://client2.sajet.us` → timeout (15s TLS handshake)

**Cause:** CNAME created (✅) but tunnel ingress rules not added (❌)

**Fix:**
```bash
# Check tunnel rules
curl https://sajet.us/api/provisioning/tunnel-debug \
  -H "X-API-Key: sk_live_..." | jq '.rules[]'

# If missing client2 rules → re-run provision with idempotent create
# (detects existing DB, skips agent, re-adds tunnel rules)
```

### Database Already Exists

**Symptom:** POST returns `{"success": false, "reason": "already_exists"}`

**Fix:**
```bash
# Delete first (full cleanup)
curl -X DELETE https://sajet.us/api/provisioning/tenant \
  -H "X-API-Key: sk_live_..." \
  -d '{"subdomain":"client2","domain":"sajet.us","delete_dns":true}'

# Then create
curl -X POST https://sajet.us/api/provisioning/tenant \
  -H "X-API-Key: sk_live_..." \
  -d '{"subdomain":"client2",...}'
```

### Invalid API Key

**Symptom:** `{"detail": "API key inválida"}`

**Checklist:**
- [ ] Key starts with `sk_live_` (managed) or `prov-key-` (legacy)?
- [ ] Full key includes secret_part? (e.g., `sk_live_XXXX_YYYY`, not just `sk_live_XXXX`)
- [ ] Header is `X-API-Key` (exact case)?
- [ ] No extra whitespace in key?
- [ ] Key not expired? (check `api_keys.status = 'active'`)

---

## API Key Lifecycle

### Create

```bash
# Run once to generate key
python3 /opt/Erp_core/scripts/create_provisioning_apikey.py

# Output: copy FULL_KEY and store securely (e.g., in password manager)
```

### Rotate (Quarterly)

1. Create new key (same script)
2. Update all clients to use new key
3. Mark old key as inactive: `UPDATE api_keys SET status='inactive' WHERE key_id='...'`
4. Decommission after 30-day grace period

### Revoke

```bash
UPDATE api_keys SET status='inactive' WHERE key_id='sk_live_XXXX_YYYY';
```

---

## Migration from Legacy Keys

If currently using `prov-key-2026-secure` (legacy):

### Step 1: Create Managed Key
```bash
python3 /opt/Erp_core/scripts/create_provisioning_apikey.py
```

### Step 2: Update All Clients
Replace header:
```bash
# Old
X-API-Key: prov-key-2026-secure

# New
X-API-Key: sk_live_XXXX_YYYY
```

### Step 3: Decommission Legacy (Optional)
```bash
# Mark as inactive (not required, but recommended for security)
UPDATE system_config SET value='false' WHERE key='PROVISIONING_LEGACY_ENABLED';
```

---

## Example: Complete Workflow

```bash
#!/bin/bash
# Provision + verify + delete cycle

API_KEY="sk_live_XXXXXXXX_XXXXXXXX"
BASE_URL="https://sajet.us/api/provisioning"
SUBDOMAIN="test-tenant-$(date +%s)"

echo "📦 Creating tenant: $SUBDOMAIN"
curl -s -X POST "$BASE_URL/tenant" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"subdomain\": \"$SUBDOMAIN\",
    \"admin_password\": \"TestPass@2026\",
    \"domain\": \"sajet.us\"
  }" | jq '.message'

# Wait for propagation
sleep 5

echo "✅ Verifying access"
curl -s "https://$SUBDOMAIN.sajet.us/web/login" | grep -q "DOCTYPE" && echo "✓ Login page loaded" || echo "✗ Failed"

echo "🗑️ Deleting tenant"
curl -s -X DELETE "$BASE_URL/tenant" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"subdomain\": \"$SUBDOMAIN\", \"domain\": \"sajet.us\", \"delete_dns\": true}" | jq '.success'
```

---

## Architecture Diagrams

### Request Flow

```
Client
  │
  ├─ POST /api/provisioning/tenant + X-API-Key header
  │
  └─→ SAJET Gateway (nginx 443)
      │
      ├─ TLS: Verify certificate ✅
      │
      └─→ FastAPI Router (127.0.0.1:4443)
          │
          ├─ gateway_api_key_dependency(SENSITIVE)
          │  ├─ Extract X-API-Key header
          │  ├─ If sk_live_*: Query api_keys table → verify_api_key_detailed()
          │  ├─ Enforce permission level (SENSITIVE)
          │  └─ Return auth_info or HTTP 401/403
          │
          ├─ _require_api_key() [internal gate]
          │  └─ Double-check key exists (redundant but explicit)
          │
          └─→ provision_tenant() handler
              │
              ├─ Stage 1: call_odoo_local_api(POST /api/tenant)
              │  └─→ Tenant-Agent (10.10.20.201:8070, HTTP, private)
              │      ├─ Clone DB template_tenant → subdomain
              │      ├─ Create systemd service
              │      ├─ Start service
              │      └─ Return: http_port, longpolling_port, status
              │
              ├─ Stage 2: create_cloudflare_dns()
              │  └─→ Cloudflare API (REST)
              │      ├─ Create CNAME record (subdomain.sajet.us)
              │      └─ Return: dns_created=true
              │
              ├─ Stage 3: add_tenant_routes() [cloudflare_tunnel_api.py]
              │  └─→ Tunnel Configurations API (urllib)
              │      ├─ GET current config from Cloudflare Zero Trust
              │      ├─ Insert 3 rules (ws, longpolling, catch-all)
              │      ├─ PUT updated config back
              │      └─ Return: tunnel_status="rules_added"
              │
              └─ HTTP 201 + response JSON
                 ├─ success=true
                 ├─ url=https://subdomain.sajet.us
                 └─ message="... | agent=True dns=True tunnel=True"

Final Client State:
  ✅ HTTPS://subdomain.sajet.us/web/login → Odoo login page
```

### Tunnel Routing (Zero Trust)

```
Cloudflare Edge (anycast)
  │
  └─→ Tunnel Configurations API Rules (ordered)
      │
      ├─ Rule 0: hostname=subdomain.sajet.us, path=/websocket*
      │  └─→ http://10.10.20.201:9503 (Odoo longpolling WebSocket)
      │
      ├─ Rule 1: hostname=subdomain.sajet.us, path=/longpolling*
      │  └─→ http://10.10.20.201:9503 (Odoo COMET long-polling)
      │
      ├─ Rule 2: hostname=subdomain.sajet.us
      │  └─→ http://10.10.20.201:9003 (Odoo HTTP catch-all)
      │
      ├─ Rule N-2: (other tenants, same pattern)
      │
      ├─ Rule N-1: hostname=sajet.us, path=/api/*
      │  └─→ http://10.10.20.202:443 (SAJET FastAPI through nginx)
      │
      └─ Rule N: (fallback, no hostname)
         └─→ http://10.10.20.202:443 (default)
```

---

## Security Considerations

### 1. Key Storage
- **Never commit keys** to git
- Store in secrets manager (Vault, 1Password, etc.)
- Rotate quarterly
- Use environment variables or secure .env files

### 2. Network Isolation
- Tenant-Agent (10.10.20.201:8070) is **HTTP-only** on private network (not exposed publicly)
- SAJET FastAPI (127.0.0.1:4443) is localhost-only; nginx reverse proxy handles TLS/routing
- Cloudflare tunnel encrypts all traffic to edge

### 3. Rate Limiting
- Managed keys: 60 RPM, 10000 RPD per key
- Use circuit breaker patterns on client side for retries
- Respect 429 responses with `retry-after` header

### 4. Audit Trail
- All API key usages logged to `api_key_events` table
- Fields: key_id, auth_mode, endpoint, method, ip_address, status_code, reject_reason, timestamp
- Query: `SELECT * FROM api_key_events WHERE key_id='sk_live_...' ORDER BY created_at DESC LIMIT 100`

### 5. Input Validation
- Subdomain: alphanumeric + hyphens, 3-30 chars, validated server-side
- Passwords: minimum 12 chars, enforced at Odoo login
- Domain: must match configured base domain (sajet.us)

---

## FAQ

**Q: Can I use legacy key for provisioning?**  
A: No. Legacy keys are PARTNER level; provisioning requires SENSITIVE. Migrate to managed keys.

**Q: What if Cloudflare tunnel is down?**  
A: Tenant DB + service still exist (PCT 201:900X). Manual recovery via pct exec until tunnel recovers.

**Q: Can I provision to other Odoo servers (not PCT 201)?**  
A: Currently hardcoded to PCT 201 (10.10.20.201:8070). Future: configurable via environment.

**Q: How long until subdomain.sajet.us responds after creation?**  
A: Usually <1 min. CNAME creation is instant; tunnel propagation can take 1-3 min. Query with `curl -sI https://subdomain.sajet.us/ -m 20`.

**Q: Can I delete a tenant and recreate with same subdomain?**  
A: Yes. DELETE full cleans (DB, DNS, tunnel rules); subsequent POST recreates from scratch.

---

## References

- [Cloudflare Tunnel Configurations API](https://developers.cloudflare.com/api/operations/cfd_tunnel_management_put_tunnel_configurations)
- [Odoo Multi-Tenant Architecture](../05-deploy-operacion/TENANTS_401_FIX_SUMMARY.md)
- [SAJET API Gateway Authentication](../02-security-auth/gateway-auth-design.md)
- [API Key Management](../02-security-auth/api-keys-lifecycle.md)

---

**Questions?** Contact: ops@jeturing.com  
**Report Issues:** GitHub: [jeturing/Erp_core/issues](https://github.com/jeturing/Erp_core/issues)
