# Testing and quality gates

This is the canonical test contract for the frontend, API, and scientific engine. A test result is evidence only for the tested commit; it is not a deployment approval.

## Required gates

The decision gate is green only when all applicable checks pass:

1. Biome check without automatic writes.
2. TypeScript type-check.
3. Unit tests with the agreed coverage threshold of at least 80%.
4. Fourteen-locale catalog parity and i18n compilation.
5. API generation followed by an Orval drift check.
6. Next.js production build.
7. Playwright against the production server, not a development server.
8. Lighthouse/CWV checks and the security scan.
9. Backend unit, integration, contract, and scientific validation checks.
10. C++ build, CTest, module-load verification, and parity tests for the affected core.

Auth, money, and state-machine branches require stronger targeted coverage than the global threshold. Generated or fixture data must be identifiable and must not be presented as an observation.

## Common commands

Run from the repository root unless a command says otherwise:

```bash
python -m pytest tests/unit -q
python -m pytest tests/integration/test_sqlite_migrations.py -q
python -m pytest tests/contract -q
python -m pytest --cov=engine --cov=services --cov-fail-under=80

pnpm -C apps/web quality
pnpm -C apps/web test:e2e
pnpm -C apps/web generate:api
pnpm -C apps/web i18n:compile
```

For the C++ core, configure and test with the project CMake options documented in `engine/cpp_core/README.md`; do not substitute an untracked build directory in CI.

## Test layers

- **Unit:** deterministic domain and policy functions, including authorization and offline state transitions.
- **Integration:** SQLite locally and the supported PostgreSQL/Redis test services where required.
- **Contract:** OpenAPI validation, typed error envelopes, generated-client drift, and BFF-to-API mapping; use Schemathesis and Pact where the service contract is exercised.
- **End-to-end:** production `next start`, authentication/session boundaries, public i18n routes, accessibility, and protected online-only flows.
- **Scientific:** regression, calibration/provenance, and parity checks with explicit source metadata.
- **Performance:** C++ benchmarks and web-vitals gates; INP is a field measurement and is not inferred from a lab-only score. Load tests use Locust with the project P99 target below 200 ms; mutation testing targets at least 70%, and chaos checks remain separate gates.

## Data and security rules

Use synthetic fixtures with clear labels. Never log secrets or tokens, and never commit `.env` files. A failing, skipped, or unavailable required check blocks the decision gate. Test evidence must identify the commit and the environment configuration without exposing credentials.

See [`ARCHITECTURE.md`](ARCHITECTURE.md), [`AUTH_AND_RBAC.md`](AUTH_AND_RBAC.md), and [`DEPLOYMENT.md`](DEPLOYMENT.md) for boundary-specific gates.
