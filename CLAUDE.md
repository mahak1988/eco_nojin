# CLAUDE.md — Eco Nojin Instructions for Claude

## Quick Reference
- **Project**: Eco Nojin — Ecological Intelligence Platform
- **Stack**: Python/FastAPI, Go, Rust, TypeScript/Next.js, C++20
- **Architecture**: Modular, service-oriented, offline-first, event-driven
- **Key Docs**: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/API_REFERENCE.md`

## Current Sprint
**Phase 1: Foundation** — Sprint 1.1 (Week 1-2): Observability & Cache

## Commands
```bash
# Dev
docker-compose up -d
uvicorn services.api_gateway.main:app --reload --port 8000
cd frontend && pnpm dev

# Test
pytest tests/ -v --tb=short
pytest tests/test_contract.py -v
locust -f tests/load/locustfile.py --headless -u 50 -t 60s

# Lint
ruff check . && ruff format --check .
mypy --strict engine/hydroma/config/settings.py services/api_gateway/

# DB
alembic upgrade heads
alembic revision --autogenerate -m "description"

# Pre-commit
pre-commit run --all-files
```

## Code Style
- **Python**: Ruff + MyPy strict + type hints everywhere
- **TypeScript**: Strict mode, Zod for validation, TanStack Query v5
- **Go**: Standard library first, gofmt, golangci-lint
- **Rust**: Clippy, rustfmt, cargo-nextest
- **C++20**: clang-format, CMake, pybind11

## Architecture Rules
1. **Settings only via `get_settings()`** — never `os.getenv()` directly
2. **Feature flags** for all new features: `settings.enable_xxx`
3. **Correlation IDs** in all logs: `request.headers.get("X-Request-ID")`
4. **Structured logging**: `logger.info("event", extra={"key": value})`
5. **Custom exceptions** with error codes for all errors
6. **Contract tests** for new endpoints: `tests/test_contract.py`
4. **ADRs** for architectural decisions: `docs/adr/NNNN-title.md`
5. **Prefer composition** — dependency injection via FastAPI `Depends`

## Testing Requirements
- Unit tests for all new functions (target ≥80% coverage)
- Contract tests for all new endpoints (schemathesis + Pact)
- Mutation testing for critical paths (target ≥70%)
- Load testing for new endpoints (Locust)

## Current Focus
**Sprint 1.1: Observability & Cache**
- [ ] Structured JSON logger with correlation IDs
- [ ] Redis cache layer (L1/L2, tags, invalidation)
- [ ] Cache invalidator via Redis pub/sub
- [ ] Alert rules (latency, error rate, saturation)

## Key Files to Know
| File | Purpose |
|------|---------|
| `engine/hydroma/config/settings.py` | All configuration |
| `services/api_gateway/main.py` | FastAPI app entry |
| `services/api_gateway/routers/` | API endpoints |
| `database/models.py` | SQLAlchemy models |
| `database/hub.py` | Database access layer |
| `frontend/lib/api/apiClient.ts` | Frontend API client |
| `frontend/lib/cache/` | Offline cache logic |

## Don't Do
- ❌ Commit `.env` or secrets
- ❌ Hardcode configuration values
- ❌ Skip tests for new features
- ❌ Use `print()` for logging
- ❌ Bypass feature flags
- ❌ Direct SQL in business logic (use repositories)
- ❌ Blocking I/O in async functions