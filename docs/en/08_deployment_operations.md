# 08. Deployment and Operations

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. Development Environment

- **Backend:** Python 3.11 venv (`.venv`), FastAPI + Uvicorn.
  Run: `uvicorn services.api_gateway.main:app --reload` (from repo root).
- **Frontend:** Next.js (pnpm). Run: `pnpm install && pnpm dev`.
  Dev origins for LAN access configured in `next.config.js`
  (`allowedDevOrigins`).
- **Tests:** `pytest` from repo root (126 tests: unit + integration +
  benchmarks). C++ core tests: `ctest` or the self-contained
  `tests/test_hydroma.cpp` executable.

## 2. Infrastructure as Code (current)

`docker-compose.yml` provides:

| Service | Image | Purpose |
|---|---|---|
| postgis | `postgis/postgis:16-3.4` | spatial database (production target) |
| redis | `redis:7-alpine` | cache / Celery broker |

⚠ The compose file contains a literal `***` password placeholder — replace
with a real secret before any shared environment.

## 3. Configuration

- `.env.example` → copy to `.env`; keys: `PROJECT_NAME`, `ENGINE_NAME`,
  `ENVIRONMENT`, `DATABASE_URL`, `REDIS_URL`.
- Research mode defaults to SQLite; production switches `DATABASE_URL` to
  PostGIS (`postgresql+psycopg://…`).

## 4. CI/CD (planned)

- `deploy/ci/` and `deploy/k8s/` are empty scaffolding.
- Target pipeline: lint → unit/integration tests → C++ build + ctest →
  build frontend → container image → deploy (k8s manifests or managed
  platform).
- **Immediate prerequisite:** initialize a Git repository (the project is
  not under version control yet) and add CI on the first commit.

## 5. Observability (planned)

- Structured logging (JSON), request IDs.
- Health endpoint already exposes module status (`/api/v1/health`).
- Metrics (Prometheus) and tracing (OpenTelemetry) for gateway + engine.

## 6. Backup & Recovery

- PostGIS: scheduled `pg_dump`/WAL archiving; SQLite research DB: file-level
  snapshots.
- Satellite/meteorological data are re-fetchable from upstream APIs; cache
  invalidation policy needed (diskcache).

## 7. Environments

1. **Local research** — SQLite, in-memory modules, simulated satellite data.
2. **Staging pilot** — PostGIS + Redis, real satellite tiles, auth enabled.
3. **Production** — k8s, TLS, secrets vault, accredited carbon workflow,
   real MRV + ledger.

## 8. Operations Checklist (pre-pilot)

- [ ] `git init` + baseline commit
- [ ] Replace placeholder secrets; add vault
- [ ] Wire real Sentinel-2 downloads (remove simulated bands)
- [ ] Enable TLS + explicit CORS allowlist
- [ ] Implement auth (or gate pilot behind a simple access token)
- [ ] Pin dependencies; add dependency audit
- [ ] Define backup schedule
