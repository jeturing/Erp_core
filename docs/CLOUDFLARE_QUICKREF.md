# Quick Reference - Cloudflare Tunnel Integration

## 🚀 Quick Start

### Setup (One-time)

1. **Copy credentials template:**
   ```bash
   cp ~/.cf_credentials_example ~/.cf_credentials
   ```

2. **Get API token from Cloudflare:**
   - Go: https://dash.cloudflare.com/profile/api-tokens
   - Create token with: Zone:DNS:Edit + Tunnels:Admin
   - Copy to `CF_API_TOKEN` in `~/.cf_credentials`

3. **Add to .env:**
   ```bash
   CF_CREDENTIALS_FILE=/root/.cf_credentials
   CLOUDFLARE_PATH=/usr/bin/cloudflared
   ```

4. **Restart service:**
   ```bash
   systemctl restart onboarding
   ```

## 📋 Common Commands

### Get JWT Token
```bash
JWT=$(curl -s -X POST http://localhost:4443/api/auth/login \
  -d "username=admin&password=admin123" | jq -r .access_token)

echo $JWT  # Save for next commands
```

### List All Tunnels
```bash
curl -H "Authorization: Bearer $JWT" \
     http://localhost:4443/api/tunnels | jq
```

### Get Tunnel Status
```bash
curl -H "Authorization: Bearer $JWT" \
     http://localhost:4443/api/tunnels/acme-tunnel/status
```

### Get Tunnel Logs (Last 50 lines)
```bash
curl -H "Authorization: Bearer $JWT" \
     "http://localhost:4443/api/tunnels/acme-tunnel/logs?lines=50" | jq
```

### Restart Tunnel
```bash
curl -X POST \
     -H "Authorization: Bearer $JWT" \
     http://localhost:4443/api/tunnels/acme-tunnel/restart
```

### Delete Tunnel
```bash
curl -X DELETE \
     -H "Authorization: Bearer $JWT" \
     http://localhost:4443/api/tunnels/acme-tunnel
```

## 🔍 Troubleshooting

### Check Service Status
```bash
systemctl status cloudflared-[tunnel-name]-tunnel
```

### View Service Logs
```bash
journalctl -u cloudflared-acme-tunnel -f
```

### List All Tunnels (CLI)
```bash
cloudflared tunnel list
```

### Check Credentials
```bash
cat ~/.cf_credentials
```

### Restart All Cloudflare Services
```bash
systemctl restart cloudflared*
```

## 🎯 API Endpoints Cheatsheet

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/tunnels` | List all tunnels |
| POST | `/api/tunnels` | Create tunnel |
| GET | `/api/tunnels/{id}/status` | Get status |
| GET | `/api/tunnels/{id}/logs` | Get logs |
| POST | `/api/tunnels/{id}/restart` | Restart tunnel |
| DELETE | `/api/tunnels/{id}` | Delete tunnel |
| GET | `/api/tunnels/subscription/{sub_id}/tunnel` | Get by subscription |

## 📊 Dashboard Access

```
URL: http://localhost:4443/admin/tunnels
Auth: Admin account required
Stats: Total, Active, Provisioning, Errors
```

## 🛠️ File Locations

| File | Location | Purpose |
|------|----------|---------|
| Service | `app/services/cloudflare_manager.py` | Core manager |
| API Routes | `app/routes/tunnels.py` | REST endpoints |
| Dashboard | `templates/admin_tunnels.html` | Admin UI |
| Script | `Cloudflare/create_tenant_enhanced.sh` | Provisioning |
| Credentials | `~/.cf_credentials` | API tokens |
| Docs | `docs/CLOUDFLARE_INTEGRATION.md` | Full guide |

## 🔧 Configuration Variables

```bash
# Cloudflare
CF_CREDENTIALS_FILE=/root/.cf_credentials
CLOUDFLARED_PATH=/usr/bin/cloudflared

# LXC
LXC_CONTAINER_ID=105
DOMAIN=sajet.us
CREATE_TENANT_SCRIPT=/root/Cloudflare/create_tenant.sh
```

## 📱 JSON Response Examples

### List Tunnels
```json
{
  "success": true,
  "total": 2,
  "tunnels": [
    {
      "id": "xyz123",
      "name": "acme-tunnel",
      "status": "active",
      "deployment": {
        "subdomain": "acme",
        "domain": "acme.sajet.us",
        "plan": "pro"
      }
    }
  ]
}
```

### Tunnel Status
```json
{
  "tunnel_name": "acme-tunnel",
  "service": "cloudflared-acme-tunnel",
  "active": true,
  "status": "running"
}
```

## ⚙️ Systemd Services

### List Active Tunnel Services
```bash
systemctl list-units cloudflared-*
```

### Enable Auto-start
```bash
systemctl enable cloudflared-acme-tunnel
```

### Stop Tunnel
```bash
systemctl stop cloudflared-acme-tunnel
```

## 🔐 Security Tips

1. **Protect credentials:**
   ```bash
   chmod 600 ~/.cf_credentials
   ```

2. **Use strong JWT tokens** - Tokens expire after 1 hour

3. **Rate limiting** - API limits to 5 requests per user per minute

4. **Audit logs** - All tunnel changes are logged

## 📚 Documentation Links

- **Full Guide:** `docs/CLOUDFLARE_INTEGRATION.md`
- **Implementation:** `docs/CLOUDFLARE_TUNNEL_IMPLEMENTATION.md`
- **Module README:** `Cloudflare/README.md`

## 🆘 Quick Help

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check JWT token or use correct credentials |
| Tunnel not found | Check tunnel name spelling, list tunnels first |
| DNS not resolving | Run: `cloudflared tunnel route dns acme acme.sajet.us` |
| Service not starting | Check `journalctl -u cloudflared-acme-tunnel -n 20` |
| Credentials invalid | Re-authenticate: `cloudflared tunnel login` |

## 🚨 Emergency Procedures

### Kill All Tunnel Services
```bash
systemctl stop cloudflared*
```

### Clear Stuck Tunnels
```bash
cloudflared tunnel delete --force acme
```

### Reset Credentials
```bash
rm ~/.cloudflared/*
cloudflared tunnel login
```

## 📞 Support Resources

- Cloudflare Docs: https://developers.cloudflare.com/cloudflare-one/
- cloudflared CLI: https://github.com/cloudflare/cloudflared
- Issues: Check `docs/CLOUDFLARE_INTEGRATION.md` troubleshooting section

---

**Last Updated:** 2024  
**Version:** 2.0.0  
**Status:** Production Ready ✅
