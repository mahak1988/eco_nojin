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
1. **Branch**: `feature/{ticket-id}-{short-desc}` from `develop`
2. **Commit**: Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`)
3. **PR**: Target `develop`, require CI green + 1 review
4. **Merge**: Squash merge, delete branch
5. **Release**: `main` → `release/vX.Y.Z` tag → GitHub Release

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
- **Staging**: Auto-deploy on push to `develop`
- **Production**: Manual approval on push to `main`
- **Containers**: Multi-stage Dockerfile, GHCR registry
- **Orchestration**: Kubernetes (staging/prod namespaces)
- **Secrets**: External Secrets Operator → AWS Secrets Manager / Vault

## Key Commands
```bash
# Local development
docker-compose up -d          # Redis, PostgreSQL
uvicorn services.api_gateway.main:app --reload --port 8000
pnpm -C apps/web dev

# Testing
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m pytest tests/ -v --tb=short
pytest tests/test_contract.py -v
pnpm -C apps/web test
pnpm -C apps/web type-check
locust -f tests/load/locustfile.py --headless -u 50 -t 60s

# Linting
ruff check . && ruff format --check .
mypy --strict engine/hydroma/config/settings.py services/api_gateway/

# Database
alembic upgrade heads
alembic revision --autogenerate -m "description"

# Pre-commit
pre-commit run --all-files
```

## Important Notes for Agents
- **Never commit `.env`** — verified in `.gitignore`
- **Never hardcode secrets** — always use `get_settings()`
- **Use feature flags** for new functionality — `settings.enable_xxx`
- **Add correlation IDs** to logs — `request.headers.get("X-Request-ID")`
- **Write contract tests** for new endpoints — `tests/test_contract.py`
- **Update OpenAPI schema** after API changes — `python regen_schema.py`
- **Write ADRs** for architectural decisions — `docs/adr/NNNN-title.md`
- **Prefer composition over inheritance** — dependency injection via FastAPI `Depends`
- **Use structured logging** — `logger.info("event", extra={"key": value})`
- **Handle errors explicitly** — custom exceptions with error codes

## Current Sprint Focus (Week 1-2)
**Sprint 1.1: Observability & Cache**
- [ ] Structured JSON logger with correlation IDs
- [ ] Redis cache layer (L1/L2, tags, invalidation)
- [ ] Cache invalidator via Redis pub/sub
- [ ] Alert rules (latency, error rate, saturation)

**Next**: Sprint 1.2 (Load Testing & CI/CD) — Week 3-4