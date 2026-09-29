# AGENTS.md — Eco Nojin Agent Instructions

## Project Overview
Eco Nojin is a modular, service-oriented platform for ecological intelligence, combining:
- **Scientific Engine** (HyDroMa): Soil, hydrology, climate, erosion, carbon modeling
- **API Gateway** (FastAPI): REST, GraphQL, gRPC, SSE, Webhooks
- **Frontend** (Next.js 15 + React 19 + TypeScript): PWA, offline-first, 14 languages
- **Event Bus** (NATS JetStream): Event-driven architecture
- **AI/ML**: RAG, embeddings, multi-agent orchestration

## Architecture Principles
1. **Offline-first** — All mobile features work without internet
2. **Inclusive access** — Feature phones via USSD/SMS/Voice
3. **Scientific rigor** — Peer-reviewed methodologies (FAO, IPCC, OGC)
4. **Performance** — Numba JIT, C++20 kernels, Rust for hot paths
5. **Multi-language** — 14 languages with RTL/LTR support
6. **Modularity** — Each module independently testable
7. **Open standards** — FAO, IPCC, OGC compliance

## Language Strategy (ADR 0001)
| Language | Domain | Rationale |
|----------|--------|-----------|
| **Python** | Business logic, AI/ML, scientific computing, orchestration | Ecosystem, team expertise |
| **Go** | Gateway, event bus, webhooks, gRPC gateway | Concurrency, fast startup, single binary |
| **Rust** | Offline sync, geospatial, high-perf kernels | Memory safety, WASM, zero-cost abstractions |
| **TypeScript** | Frontend, shared types, edge functions | Type safety, shared schemas |
| **C++20** | Numerical kernels (existing via pybind11) | Performance-critical numerics |

## Current Phase
**Phase 1: Foundation** — Week 1-4
- Sprint 1.1: Observability & Cache (Week 1-2)
- Sprint 1.2: Load Testing & CI/CD (Week 3-4)

## Key Files & Patterns

### Settings & Configuration
- Single source of truth: `engine/hydroma/config/settings.py` (pydantic-settings v2)
- All config via `.env` (never committed, in `.gitignore`)
- Feature flags: `ENABLE_*` in settings

### API Gateway Structure
```
services/api_gateway/
├── main.py                 # FastAPI app entry
├── routers/                # API endpoints per module
├── middleware/             # Auth, rate limit, cache, logging
├── security/               # HTTPS, rate limit, headers, CSRF
├── observability/          # Logging, metrics, tracing
├── cache/                  # Redis cache layer
└── resilience/             # Circuit breaker, retry
```

### Database
- SQLAlchemy 2.0 + async (SQLite dev, PostgreSQL prod)
- Alembic migrations in `alembic/versions/`
- Models in `database/models.py`

### Frontend
- Next.js 15 App Router + React 19 + TypeScript in `apps/web`
- TanStack Query v5 + Zustand + React Hook Form + Zod
- PWA with Workbox, offline-first with IndexedDB (Dexie.js)
- 14 locales (i18n) with RTL support
- Tests: `apps/web/src/**/*.test.ts` (vitest + jsdom)

### Testing Strategy
- **Contract**: schemathesis (OpenAPI) + Pact (consumer-driven)
- **Unit**: pytest + pytest-asyncio (target ≥80% coverage)
- **Integration**: pytest with testcontainers (Redis, PostgreSQL)
- **Load**: Locust (target P99 < 200ms)
- **Mutation**: mutmut (target ≥70% score)
- **Chaos**: Chaos Mesh (latency, error, partition injection)

## Development Workflow
1. **Branch**: `feature/{ticket-id}-{short-desc}` from `main`
2. **Commit**: Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`)
3. **PR**: Target `main`, require CI green + 1 review
4. **Merge**: Squash merge, delete branch
5. **Release**: Immutable `vX.Y.Z` tag → GitHub Release; no branch publish

## Code Quality Gates
- **Lint**: Ruff (replaces flake8, isort, black) — `ruff check . && ruff format --check .`
- **Type**: MyPy strict — `mypy --strict engine/hydroma/config/settings.py services/api_gateway/`
- **Format**: Ruff format — `ruff format .`
- **Test**: pytest with coverage ≥80% — `pytest --cov=engine --cov=services --cov-fail-under=80`
- **Mutation**: mutmut — `mutmut run --paths-to-mutate=engine,services --tests-dir=tests --runner="pytest -x"`

## Environment Variables
All secrets in `.env` (never committed):
- **Required**: `SECRET_KEY`, `JWT_SECRET`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- **Feature Flags**: `ENABLE_SUPABASE_SYNC`, `ENABLE_REALTIME_SSE`, `ENABLE_BLOCKCHAIN`, etc.
- **External**: `SUPABASE_*`, `TELEGRAM_BOT_TOKEN`, `CDSE_*`, `CDS_*`, `ALCHEMY_API_KEY`, etc.

## Deployment
- **Staging**: Disabled until required checks and deployment contract are green
- **Production**: Disabled until immutable artifact promotion and reviewer gates are configured
- **Containers**: Multi-stage Dockerfile, GHCR registry
- **Orchestration**: Kubernetes (staging/prod namespaces)
- **Secrets**: External Secrets Operator → AWS Secrets Manager / Vault

## Key Commands
```bash
# Local development (no container runtime required)
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-local-api.txt
.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000
pnpm -C apps/web dev

# Optional full local dependency stack (Podman; not required for SQLite-only dev)
podman compose -f deploy/docker-compose.yml up -d

# Testing (no-container lane)
.venv\Scripts\python.exe -m pytest tests/unit -q
.venv\Scripts\python.exe -m pytest tests/integration/test_sqlite_migrations.py -q
.venv\Scripts\python.exe -m pytest tests/contract -q
pnpm -C apps/web test
pnpm -C apps/web type-check
locust -f tests/load/locustfile.py --headless -u 50 -t 60s

# Linting
ruff check . && ruff format --check .
mypy --strict engine/hydroma/config/settings.py services/api_gateway/

# Database
.venv\Scripts\python.exe -m alembic upgrade heads
.venv\Scripts\python.exe -m alembic revision --autogenerate -m "description"

# Pre-commit
pre-commit run --all-files

# Innovation backlog (see INNOVATION_BACKLOG_FA.md and docs/adr/0007-innovation-programme.md)
.venv\Scripts\python.exe scripts\innovation_backlog.py validate
.venv\Scripts\python.exe scripts\innovation_backlog.py summary
.venv\Scripts\python.exe scripts\innovation_backlog.py status --wave W0
.venv\Scripts\python.exe scripts\innovation_backlog.py ready
.venv\Scripts\python.exe scripts\innovation_backlog.py blocked

# Cost control (see COST_OPTIMIZATION_RESEARCH_FA.md)
.venv\Scripts\python.exe scripts\cost_estimate.py
.venv\Scripts\python.exe scripts\cost_guard.py check
.venv\Scripts\python.exe scripts\cost_collect.py
.venv\Scripts\python.exe scripts\cost_guard.py budget

# Document/code consistency (after editing any analysis, ADR or standards doc)
.venv\Scripts\python.exe -m pytest tests/contract/test_claims_gate.py -q
```

## Important Notes for Agents
- **Never commit `.env`** — verified in `.gitignore`
- **Never hardcode secrets** — always use `get_settings()`
- **Use feature flags** for new functionality — `settings.enable_xxx`
- **Add correlation IDs** to logs — `request.headers.get("X-Request-ID")`
- **Write contract tests** for new endpoints — `tests/test_contract.py`
- **Update OpenAPI schema** after API changes — `.venv\Scripts\python.exe scripts/generate_openapi_schema.py`
- **Write ADRs** for architectural decisions — `docs/adr/NNNN-title.md`
- **Prefer composition over inheritance** — dependency injection via FastAPI `Depends`
- **Use structured logging** — `logger.info("event", extra={"key": value})`
- **Handle errors explicitly** — custom exceptions with error codes
- **Check the innovation backlog before adding a feature** — `docs/innovation_backlog.csv` is the single source of truth for status; a new capability must either map to an existing item or get an ADR in `docs/adr/0007-innovation-programme.md`. Run `.venv\Scripts\python.exe scripts/innovation_backlog.py validate` after editing it
- **Respect wave ordering** — an item in a later wave must not be started before its dependencies are done (`scripts/innovation_backlog.py blocked`)
- **Do not add cost-bearing infrastructure without a driver** — `helm/eco-nojin/values.yaml` is a *target* manifest, not current state. Before enabling istio, multiRegion, tempo, pgpool or velero, run `scripts/cost_guard.py check` and be able to state the cost in USD/month. Run `.venv\Scripts\python.exe scripts\cost_guard.py check` after any deployment change
- **Every number in an analysis document needs a reproduction path** — a figure you cannot regenerate is an assertion, not a finding. Three rules:
  1. **Derive, don't transcribe.** Copying a number from another document or a comment block is forbidden. Extract it from the source of truth, or mark it `NOT VERIFIED` and say why. (On 2026-09-29 an analysis asserted six functions returned constants; all six were wrong — one file was deleted, five were fully implemented. The source was a stale comment in `tolerated-degradations.yaml`.)
  2. **Ship the derivation.** If a document states a figure, an equivalent runnable command must exist and produce that figure. `scripts/cost_estimate.py` → `COST_OPTIMIZATION_RESEARCH_FA.md` is the reference pattern.
  3. **Guard it in CI.** `tests/contract/test_claims_gate.py` cross-checks documents against the code they describe. Run it after editing any analysis, ADR, or standards document. Green means the documents still match reality; red means someone changed the code without updating the text, or wrote a number that cannot be reproduced.
  - When research fails or cannot be verified, **record the negative result** in the document. A documented "could not verify" is required output, not a gap to be quietly removed.

## Analysis Document Standards
- **Label every figure** — `measured` (taken from a primary source) or `estimated` (assumption). Never present an estimate as a measurement.
- **Cite primary sources with a retrieval date** — a vendor pricing page, a LICENSE file, an official doc. A citation without a date is a citation without a guarantee.
- **Distinguish "the manifest as written" from "what is running"** — `docs/ENGINEERING_INDEX_FA.md §۴٫۱` forbids describing intent as status. A cost or capability figure must say which one it measures.
- **Name the thing you could not verify** — unverified claims are part of the deliverable. Do not smooth over a failed lookup.

## Current Sprint Focus (Week 1-2)
**Sprint 1.1: Observability & Cache**
- [ ] Structured JSON logger with correlation IDs
- [ ] Redis cache layer (L1/L2, tags, invalidation) — innovation item 19 (W0)
- [ ] Cache invalidator via Redis pub/sub
- [ ] Alert rules (latency, error rate, saturation)

**Next**: Sprint 1.2 (Load Testing & CI/CD) — Week 3-4