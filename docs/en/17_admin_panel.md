# 17 — Phase 5: Admin Panel (kickoff)

> Status: **foundation shipped** — real admin API (RBAC + audit) + first two
> live admin pages. Remaining Phase 5 modules: content, bots, carbon/market,
> models, settings, error management.

## 1. What shipped

### Backend — `services/api_gateway/routers/admin.py` (all admin-only)

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/admin/health` | Live channel checks: database, AI backend (Ollama), satellite (CDSE creds), weather (NASA/ERA5), bot tokens (telegram/eitaa/bale/rubika) |
| `GET /api/v1/admin/users` | List users (newest first) |
| `POST /api/v1/admin/users/{id}/block` | Deactivate a user (audited, self-block prevented) |
| `POST /api/v1/admin/users/{id}/unblock` | Reactivate a user (audited) |
| `GET /api/v1/admin/audit` | Recent audit-log entries (W-015) |

- **Audit log (W-015):** new `audit_logs` table (migration `c3d8e0f2a1b4`);
  every admin mutation records actor/action/target/detail.
- **RBAC:** `require_roles("admin")` — non-admin gets 403.

### Frontend — real pages (not previews)

- `/admin/health` — live channel status with honest badges (sane / degraded /
  down / not-configured), refresh button.
- `/admin/users` — user table with block/unblock actions wired to the API.
- Both pages show a clear "admin role required" gate for non-admins.

### Critical pre-existing bug fixed (JWT auth)

`POST /api/v1/auth/login` and `/register` created tokens with
`sub = user.email` (and a hard-coded `role: farmer`). The JWT dependency
(`get_current_user`) looks up `int(sub)` — so **authenticated endpoints
silently failed for every user** and admin roles never reached the token.
Fixed: `sub = str(user.id)`, `role = user.role`. This unblocks the entire
authenticated surface (farms, dashboard, profile, admin).

## 2. Acceptance criterion progress

> "A non-technical operator can block a user, stop a model, see an error."

- ✅ Block a user (real DB write + audit trail + login rejection)
- ✅ See an error (channel health panel)
- ⏳ Stop a model / manage content / bots — next Phase 5 modules

## 3. How to bootstrap the first admin

```sql
UPDATE users SET role='admin' WHERE email='you@example.com';
```

(or register normally, then run the update once from the console.)

## 4. Next Phase 5 modules

1. Content management (list/edit/publish articles + RAG sync trigger)
2. Bot channels management (enable/disable per platform, send test message)
3. Error/incident view (recent 500s from logs + retry)
4. Settings (site-wide: feature flags, model selection, alert thresholds)


## 5. Modules 2-5 shipped (same session)

### Content (`/admin/content`, API: `/admin/content*`)
- `GET/POST /api/v1/admin/content`, `PUT /{id}`, `POST /{id}/publish`,
  `DELETE /{id}` (soft archive) — categories validated, all audited.
- New `content_items` table (migration `d4e9f0a3b2c5`). RAG sync lands in
  Phase 6; publish currently sets the visible flag + audit trail.

### Bots (`/admin/bots`, API: `/admin/bots*`)
- `GET /api/v1/admin/bots` — real registry status: token configured (env)
  + persisted enabled flag (settings table, key `bot_enabled_{platform}`).
- `POST /api/v1/admin/bots/{key}/toggle` — flips the persisted flag (audited).
- No fake state: `configured` comes from env, `enabled` from settings.

### Errors (`/admin/errors`, API: `/admin/errors*`)
- Global exception handler in `main.py` persists every unhandled 500 into
  the new `error_logs` table (path, method, message, traceback, acked).
- `GET /api/v1/admin/errors` + `POST /{id}/ack` — the "see an error" part of
  the Phase 5 acceptance criterion.

### Settings (`/admin/settings`, API: `/admin/settings*`)
- New `settings` table (key/value/description) with `PUT /{key}` guarded by
  a known-keys whitelist (`site_announcement`, `alerts_ndvi_enabled`,
  `rag_available`, `default_language`); every change audited.

### Migration `d4e9f0a3b2c5`
Creates `settings`, `error_logs`, `content_items` (+ indexes).

## 6. Acceptance criterion status (updated)

> "A non-technical operator can block a user, stop a model, see an error."

- ✅ Block a user (real DB write + audit + login rejection)
- ✅ See an error (error_logs + admin errors view)
- ✅ Manage content (create/publish/archive with audit)
- ✅ Manage bots (enable/disable persisted flags)
- ✅ Global settings (feature flags with audit)
- ⏳ Stop a model / model management — Phase 5 remaining (models module)

## 7. Next

- Models module (list/stop AI models, Ollama runtime state)
- Security module (recent logins, role changes)
- Dashboard metrics (requests/sec, latency from error_logs + access logs)

## 8. Module 5 shipped: Models (acceptance criterion "stop a model" ✅)

### Models (`/admin/models`, API: `/admin/models*`)
- `GET /api/v1/admin/models` — live Ollama state: `GET {OLLAMA_BASE_URL}/api/tags`
  + `/api/ps` → models with family/parameter_size/quantization/size + `loaded` flags.
  Never fabricates: Ollama unreachable → `{"configured": false, "error": ...}`.
- `POST /api/v1/admin/models/{name}/stop` — unload from memory (`keep_alive=0`),
  audited (`models.stop`), 503 with honest detail when Ollama is down.
- New tests (`test_admin_models.py`, 3): honest down-state, stop 503, RBAC 403.

### Phase 5 acceptance criterion — FINAL STATE
> "A non-technical operator can block a user, stop a model, see an error."
- ✅ Block a user (users module)
- ✅ Stop a model (models module)
- ✅ See an error (errors module)
- ✅ Manage content (content module, RAG sync in Phase 6)
- ✅ Manage bots (bots module)
- ✅ Global settings (settings module)

## 9. Remaining Phase 5 stretch
- Security module (recent logins, role-change history)
- Dashboard metrics (request/latency from error_logs + access logs)
- Admin nav linking between all real pages (health/users/content/bots/errors/settings/models)

## 10. Usability: AdminNav + bootstrap CLI
- `components/site/AdminNav.tsx` — linked navigation across all 7 real admin
  pages (health/users/content/bots/errors/settings/models); active page
  highlighted.
- `scripts/bootstrap_admin.py` — idempotent admin bootstrap:
  `python scripts/bootstrap_admin.py you@example.com`

## 11. Phase 5 finalization (this session) — panel is complete

### Overview metrics (`/admin/overview`)
- `GET /api/v1/admin/overview` — honest live metrics: uptime (process start),
  counts (users/farms/audit/errors open/content published), last 8 audit
  actions, last 5 errors. No fabricated numbers.
- AdminOverview.tsx: metric cards + recent audit + recent errors.

### Security (`/admin/security`)
- Login endpoint now audits every attempt into `audit_logs`
  (`auth.login` / detail: ok|failed:bad credentials|failed:account disabled).
- `GET /api/v1/admin/security` — last 50 auth events; AdminSecurity.tsx with
  success/failure badges.

### Placeholder hygiene
- The 10 generator-made /admin pages (alerts, analytics, backup, data, docs,
  farms, logs, roles, translations) were misleading — replaced with an honest
  AdminPlaceholder card naming the phase where the module lands.
- AdminNav now links 9 real pages: overview, health, users, content, bots,
  errors, settings, models, security.

### Phase 5 spec coverage (master plan §4)
| Module | Status |
|---|---|
| Health (5 channels) | ✅ /admin/health |
| Users (RBAC, block) | ✅ /admin/users |
| Models/runs (stop model) | ✅ /admin/models |
| Content | ✅ /admin/content |
| Bots | ✅ /admin/bots |
| Audit log (W-015) | ✅ audit_logs + /admin/overview activity |
| Settings | ✅ /admin/settings |
| Errors: see + act | ✅ /admin/errors (+ auto-capture) |
| Metrics dashboard | ✅ /admin/overview (uptime/counts/activity) |
| Carbon/marketplace | ⏳ Phase 8 (honest placeholder /admin/data) |
| Security/login history | ✅ /admin/security |

Acceptance criterion ("block a user, stop a model, see an error") — ✅ all three.

## 12. Phase 6 readiness
- Content model + publish flow already in place (Phase 5 content module);
  Phase 6 adds the Markdown editor, AI translation to 14 languages, RAG sync
  and scheduled bot publishing.

## 13. Bootstrap with account creation
`python scripts/bootstrap_admin.py you@example.com --create --password <pass>`
registers the user (role=admin, active) when the email was never registered
through the site — fixes "no user found with email ...".

## 14. Changing the admin password

Three ways:
1. Web UI: log in → **/profile** → change-password form
   (calls `POST /api/v1/auth/change-password`, validates current password).
2. CLI (fastest, no login needed):
   `python scripts/bootstrap_admin.py you@example.com --set-password NEW`
   (resets the hash for an EXISTING user; min 6 chars).
3. API: `POST /api/v1/auth/change-password` with
   `{current_password, new_password}` + bearer token.

> Note: the integration test suite recreates the dev SQLite DB
> (`drop_all`/`create_all`), so users are wiped after `pytest`.
> Re-run `python scripts/bootstrap_admin.py you@example.com --create --password ***
> whenever that happens.
