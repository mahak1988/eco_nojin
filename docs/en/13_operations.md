# 13. Operations: Backup, Rollback, and Tooling (Phase 0)

**Status:** Approved | **Version:** 1.0.0 | **Date:** 2026-08-16

## 1. Automated Backup

Run anytime (no Docker, no desktop app, stdlib only):

```bash
python scripts/backup.py                # backup into backups/<timestamp>/
python scripts/backup.py --retain 10    # keep the last 10 backups
```

What is captured per backup:

| Item | How |
|---|---|
| SQLite databases (`*.db`) | consistent copy via the SQLite online backup API |
| `.env` (secrets) | copied verbatim — keep the backup folder private |
| `requirements*.txt` | pinned + lockfile |
| `alembic/` | all migrations |
| Git history | single-file `eco_nojin.bundle` (full repo, restorable with `git clone eco_nojin.bundle`) |

## 2. Restore / Rollback

1. Pick a backup: `backups/20260816_033634/`
2. Stop the API process.
3. Restore the DB: copy `econojin.db` from the backup over the live file.
4. Restore `.env` if needed.
5. Restore git state if needed:
   ```bash
   git clone backups/<stamp>/eco_nojin.bundle restore_dir
   ```
6. Start the API again and run `pytest` to confirm health.

## 3. Dependency tooling (uv)

Phase 0 moved the project to `uv` (fast, deterministic):

```bash
uv pip compile requirements.txt -o requirements.lock.txt   # refresh the lock
uv pip install -r requirements.lock.txt                    # install exactly
```

Never edit `requirements.lock.txt` by hand; regenerate it.

## 4. Database migrations (Alembic)

Phase 0 restored the Alembic baseline:

```bash
alembic current          # should print: ed7a1747d8db (head)
alembic upgrade head     # apply pending migrations
alembic revision --autogenerate -m "describe_change"   # new migration
```

- The baseline migration `ed7a1747d8db` recreates the full unified schema
  (12 tables). Existing dev databases are stamped at head (schema is created
  by `create_all` at startup, migrations take over from here).
- `env.py` reads the real database URL from settings and falls back to the
  app engine; a `driver://` placeholder in `alembic.ini` is intentionally
  ignored.

## 5. Supabase scaffolding (Phase 0)

`supabase/migrations/00001_auth_roles_rls.sql` contains:

- `public.current_role()` / `public.is_admin()` helpers (roles from JWT
  `app_metadata.role`: farmer, cooperative, NGO, admin)
- RLS policies on `public.farms` (owner reads/writes, admin override)
- a public `media` storage bucket for the future content panel

To enable Supabase (requires an account):

1. Create a project at <https://supabase.com> (free tier is enough).
2. `npx supabase link --project-ref <ref>` (or paste the SQL in the SQL editor).
3. `npx supabase db push`
4. Put `SUPABASE_URL` / `SUPABASE_ANON_KEY` into `.env`.

Until then, the app keeps running on SQLite — Supabase is additive.

## 6. Frontend build (Next.js 16)

```bash
cd frontend
pnpm install
pnpm build        # Next.js 16.3.1 (Turbopack) — CVE-2025-66478 fixed
pnpm dev
```

Phase 0 notes:

- Tailwind was decoupled from the build: the codebase uses no utility classes
  (only 4 custom classes, all defined in `app/globals.css`). `postcss.config.mjs`
  is intentionally empty. Tailwind deps remain installed but unused; remove in
  Phase 3 when the frontend is rebuilt.
- Pre-existing TypeScript debt is tracked as W-022 (see
  `docs/11_weaknesses_and_fixes.md`) and currently gated with
  `typescript.ignoreBuildErrors` so the CVE-fixed build ships today. The debt
  is scheduled for the Phase 3 frontend rebuild.
