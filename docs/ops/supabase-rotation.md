# Supabase Credential Rotation Guide

## Overview

This document describes the procedure for rotating Supabase credentials in production environments.
All secrets are stored in `.env` (never committed to git) and loaded via pydantic-settings.

## Credentials to Rotate

| Credential | Environment Variable | Rotation Frequency | Impact |
|------------|---------------------|-------------------|--------|
| Supabase URL | `SUPABASE_URL` | Yearly (infrequent) | Low - new URL endpoint |
| Supabase Anon Key | `SUPABASE_ANON_KEY` | Yearly | Low - frontend read access |
| Supabase Service Role Key | `SUPABASE_SERVICE_ROLE_KEY` | **Quarterly** | High - backend admin access |
| Supabase DB Password | `SUPABASE_DB_PASSWORD` | **Quarterly** | High - direct database access |
| Supabase Access Token | `SUPABASE_ACCESS_TOKEN` | Yearly | Medium - CLI/MCP access |

---

## Rotation Procedure: Service Role Key (Most Critical)

### Step 1: Generate New Key

1. Go to your Supabase project dashboard: https://app.supabase.com
2. Navigate to **Project Settings** → **API**
3. Click "Regenerate" next to **service_role key**
4. Copy the new key

### Step 2: Update .env

```bash
# Edit .env on the production server
nano /path/to/econojin/.env

# Update the credential
SUPABASE_SERVICE_ROLE_KEY=new_service_role_key_here

# Save and exit
```

### Step 3: Restart Services

```bash
# Option A: Direct server restart
sudo systemctl restart econojin-api

# Option B: Docker restart
docker-compose down
docker-compose up -d

# Option C: Container orchestration (k8s)
kubectl rollout restart deployment/econojin-api
```

### Step 4: Verify

```bash
# Check health endpoint
curl https://api.econojin.ir/api/v1/sync/status | jq

# Expected response shows supabase_connected: true
{
  "status": "ok",
  "supabase_connected": true,
  ...
}
```

### Step 5: Monitor

```bash
# Check logs for sync errors
journalctl -u econojin-api -f --since "1 minute ago"

# Check metrics
curl https://api.econojin.ir/metrics | grep supabase
```

---

## Rotation Procedure: DB Password

### Step 1: Rotate in Supabase

1. Go to **Project Settings** → **Database**
2. Find **Database Password**
3. Click "Change password"
4. Enter and confirm new password

### Step 2: Update Connection String

Update `SUPABASE_DB_PASSWORD` in `.env`:

```bash
SUPABASE_DB_PASSWORD=new_db_password_here
```

### Step 3: Update DATABASE_URL (if using Supabase)

If using Supabase as primary database:

```bash
DATABASE_URL=postgresql://postgres:NEW_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```

### Step 4: Restart & Verify

Same as service role key rotation.

---

## Rotation Procedure: Anon Key

The anon (public) key is used by the frontend for client-side reads.

### Step 1: Generate New Key

1. Go to Supabase dashboard → **Project Settings** → **API**
2. Click "Regenerate" next to **anon public key**
3. Copy new key

### Step 2: Update and Deploy

```bash
# Update .env
SUPABASE_ANON_KEY=new_anon_key_here

# For frontend-only apps, you may need to rebuild and deploy frontend
cd frontend
sed -i "s/OLD_ANON_KEY/NEW_ANON_KEY/g" .env.local
pnpm run build
# Deploy to your hosting provider
```

### Step 3: Verify

Check that frontend can still read public data after deployment.

---

## Emergency: Compromised Key

If a key is suspected to be compromised (leaked, exposed in logs, etc.):

1. **Immediately** revoke the compromised key via Supabase dashboard
2. **Immediately** generate new keys
3. Update `.env` on production servers
4. Restart all services
5. Check logs for any suspicious activity
6. Rotate ALL related keys (don't just replace the compromised one)

```bash
# 1. Revoke via Supabase CLI (if available)
supabase projects list
supabase api-keys revoke --key-id KEY_ID

# 2. Or via Dashboard: https://app.supabase.com/project/_/settings/api

# 3. Update .env
# 4. Restart services
# 5. Verify
curl https://api.econojin.ir/api/v1/sync/status
```

---

## Verification: Credential Health Check

### Automated Health Check

The `/api/v1/sync/status` endpoint performs a connectivity check:

```bash
# This will show supabase_connected: true/false
curl -H "X-Request-ID: health-check-$(date +%s)" https://api.econojin.ir/api/v1/sync/status
```

### Manual Verification

```bash
# 1. Test Supabase connectivity with new credentials
python -c "
from services.supabase.client import get_supabase_client
client = get_supabase_client()
result = client.table('platform_landscapes').select('id', count='exact').limit(1).execute()
print('Supabase connection OK:', result)
"
```

---

## Security Best Practices

1. **Never commit `.env` to version control** — verified in `.gitignore`
2. **Use separate projects** for dev/staging/production in Supabase
3. **Minimize service_role key usage** — only for backend server-side operations
4. **Enable Row Level Security (RLS)** on all Supabase tables
5. **Use anon key for frontend** — it has limited permissions by design
6. **Monitor access logs** in Supabase dashboard regularly
7. **Set up alerts** for unusual activity (high query volume, unusual IP addresses)

---

## References

- [Supabase Security Docs](https://supabase.com/docs/guides/auth/security)
- [Supabase API Keys Guide](https://supabase.com/docs/guides/api)
- [Supabase RLS Tutorial](https://supabase.com/docs/guides/auth/row-level-security)