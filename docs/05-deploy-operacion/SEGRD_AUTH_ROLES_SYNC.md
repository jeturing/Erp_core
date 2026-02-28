# SEGRD Auth Roles Sync (ERP Core)

## Summary
ERP Core now supports two additional admin-user roles for SEGRD integration:
- `segrd-admin`
- `segrd-user`

These roles are synchronized to downstream SEGRD auth flows and kept backward-compatible with existing auth payloads.

## Backend Changes
- `AdminUserRole` enum now includes:
  - `admin`, `operator`, `viewer`, `segrd-admin`, `segrd-user`
- Admin users API accepts the new roles.
- `/api/auth/login` response remains compatible and now includes:
  - `email`
  - `email_domain`

## DB Migration (PostgreSQL enum)
Migration file:
- `alembic/versions/o7l5n1p2q234_016_add_segrd_roles_to_adminuserrole.py`

Idempotent SQL executed by migration:
```sql
ALTER TYPE adminuserrole ADD VALUE IF NOT EXISTS 'segrd-admin';
ALTER TYPE adminuserrole ADD VALUE IF NOT EXISTS 'segrd-user';
```

## Deploy Steps (CT160)
1. Deploy code into `/var/www/html` runtime source.
2. Run DB migration:
```bash
cd /var/www/html
alembic upgrade head
```
3. Execute official push script:
```bash
/opt/Erp_core/scripts/pct_push_160.sh
```
4. Restart/verify service:
```bash
systemctl restart erp-core
systemctl is-active erp-core
systemctl show erp-core -p WorkingDirectory --value
```

## Post-Deploy Validation
### Validate enum values
```sql
SELECT e.enumlabel
FROM pg_enum e
JOIN pg_type t ON t.oid = e.enumtypid
WHERE t.typname = 'adminuserrole'
ORDER BY e.enumsortorder;
```

### Validate admin users API accepts new roles
- Create user with `role='segrd-admin'`.
- Create user with `role='segrd-user'`.

### Validate login payload compatibility
`POST /api/auth/login` should include existing fields plus:
- `email`
- `email_domain`

## Troubleshooting
### `Rol inválido` for segrd roles
- Confirm backend deployed from updated build.
- Confirm enum migration applied in production DB.

### Login does not expose `email_domain`
- Confirm updated `secure_auth.py` is loaded in `/var/www/html` runtime.
- Restart `erp-core` after deployment.
