# Eco Nojin – Integration/API Security Review

Date: 2026-09-17
Scope: broader API integration, auth, gateway security, and high-risk endpoints

## 1) Validation command and result

Executed:

```powershell
Set-Location "D:\eco_nojin"; .\.venv\Scripts\python.exe -m pytest -q tests/integration tests/unit/test_auth.py tests/unit/test_security.py tests/unit/test_phase1_cors.py tests/unit/test_phase1_seed_demo.py
```

Initial result:

- 50 passed
- 54 failed
- 42 errors

Focused remediation result:

- 61 passed
- 0 failed
- 16 warnings, all dependency deprecations or test-cache permissions

## 2) Main findings

### A. Public endpoints were being blocked by the global CSRF gate

Evidence from the failing tests:

- `/api/v1/ai/chat` returns `403` instead of `200/422` as expected
- `/api/v1/simulation/run` returns `403` instead of `200/422`
- `/api/v1/land/profiles` returns `403` instead of `201/200`
- satellite + MRV + sync endpoints return `403` and `404` unexpectedly

This is consistent with API routes that are expected to be public or semi-public but are configured with strict `Depends(get_current_user)` / `require_user`, or with a global CSRF middleware that blocks non-Bearer unsafe methods.

Relevant files:

- [services/api_gateway/main.py](../services/api_gateway/main.py)
- [services/api_gateway/auth.py](../services/api_gateway/auth.py)
- [services/security/csrf.py](../services/security/csrf.py)
- [services/api_gateway/routers/ai_chat.py](../services/api_gateway/routers/ai_chat.py)

Remediation:

- Narrow stateless endpoint exemptions were added for AI chat, land, simulation, satellite analysis, MRV ingestion, sync, insurance, and dataset capability routes.
- Route-level auth remains explicit for protected endpoints; bearer requests still bypass the cookie-session CSRF check.

Risk:

- This creates a denial-of-service style issue for legitimate public API consumers even when they are not authenticating.
- It also introduces accidental security drift: endpoints that should be public may become accidentally protected, and routes that should be protected may rely on global middleware instead of explicit auth boundaries.

### B. Database initialization mismatch in legacy integration setup

Evidence:

- `sqlite3.OperationalError: no such table: users`
- `index ix_inv_re...` errors in admin and auth flow tests

This indicates a mismatch between:

1. the app’s runtime database engine / session factory
2. the database used by integration tests
3. initialization order of the app, including `Base.metadata.create_all` and test overrides

Relevant files:

- [services/api_gateway/main.py](../services/api_gateway/main.py)
- [database/hub/hub.py](../database/hub/hub.py)
- [database/base.py](../database/base.py)
- [tests/conftest.py](../tests/conftest.py)
- [tests/integration/test_admin_api.py](../tests/integration/test_admin_api.py)

Remediation:

- Application startup now imports all mapped model modules before `Base.metadata.create_all`.
- The focused endpoint suite no longer reports missing MRV or land tables.
- A broader legacy suite still contains repeated setup against a partially migrated file database and can collide on the existing `ix_inv_reservation_reference` index. This needs a separate migration/test-fixture cleanup; it was not bypassed with destructive schema deletion.

Risk:

- Hidden state leaks between tests and app startup
- inconsistent data layer behavior across app and test environment
- admin/auth flows can fail even when the application logic itself is correct

### C. Land API contract and service behavior mismatch

Evidence:

- `KeyError: 'id'` when reading profiles
- `list_profiles` returns `0` instead of expected `>= 2`
- `create_profile` returns `403` despite being a public endpoint in the test contract

Relevant file:

- [services/api_gateway/routers/land.py](../services/api_gateway/routers/land.py)

Remediation:

- The existing durable `LandService` path is now exercised successfully by the focused land integration tests.

### D. Optional/feature-gated modules fail in integration environment

Evidence:

- `PQUnavailableError: ML-DSA not available in this crypto...`
- `NameError: name 'Integerization' is not defined`
- `ModuleNotFoundError: No module named 'scripts.watchdog'`
- `zenodo` token-related endpoints returning unexpected statuses

Relevant files likely involved:

- [services/ledger](../services/ledger)
- [scripts/watchdog.py](../scripts/watchdog.py)
- integration tests under [tests/integration](../tests/integration)

Remediation:

- Added the `scripts.watchdog` compatibility module with bounded sample classification.
- Corrected PQC serialization imports to use `cryptography.hazmat.primitives.serialization`.
- PQC continues to fail closed with `PQUnavailableError` when ML-DSA/ML-KEM are absent; it does not silently downgrade security.
- Registered the existing insurance router in the gateway.

Risk:

- Unstable optional dependencies are being treated as required runtime behavior.
- The app must degrade gracefully when crypto or watchdog capabilities are missing.

## 3) Security hardening assessment

### Current status

The project has improved substantially in the following areas:

- explicit CORS allowlist instead of wildcard fallback
- fail-closed production settings checks
- JWT configuration aligned with secure default behavior
- rate limiting and request ID middleware present
- CSRF middleware with explicit exempt path list

### Remaining high-risk items

1. Legacy integration fixtures still mix database engines and repeatedly initialize a file DB with historical schema artifacts.
2. Route exposure should continue to be maintained through an explicit public/user/admin/webhook contract matrix.
3. Optional dependency coverage should be expanded for environments where PQC primitives are unavailable.

## 4) Priority remediation order

### P0 – Must fix before broader release

1. Complete database fixture/migration normalization.
   - Use one engine/session factory per integration run.
   - Remove or migrate historical duplicate-index state through Alembic.
   - Avoid mixing `database.config.engine`, `hub.get_sqlalchemy_engine()`, and ad hoc test DB instances.

2. Maintain explicit route security classification.
   - Keep public, user-only, admin-only, and webhook-only routes documented and tested.
   - Use route guards for authorization rather than relying on middleware side effects.

3. Continue hard-fail/graceful responses for missing feature dependencies.
   - If PQC/ML-DSA or watchdog modules are unavailable, return graceful 501/503 with clear contract rather than crashing or returning 403.

### P1 – Strongly recommended

1. Review all route decorators and public/private API expectations.
2. Add an explicit contract matrix for each endpoint: public / user-only / admin-only / webhook-only.
3. Add DB health checks and startup validation logs.
4. Add negative-path tests for missing tables, missing auth, and optional dependencies.

### P2 – Long-term quality

1. Unify DB lifecycle across app + tests.
2. Replace brittle `KeyError` assumptions with explicit 404/400 validation.
3. Refactor optional integrations behind a consistent feature-flag guard.

## 5) Immediate next action recommendation

The auth/public-route, MRV persistence, land/simulation, insurance, watchdog, and PQC integration slices are now green. The next isolated work item is database fixture and migration normalization for the broader legacy suite.

This is the shortest path to restore a reliable integration baseline without guessing at unrelated scientific logic.
