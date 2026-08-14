# 10. Internal Quality Standards

**Status:** Draft for review | **Version:** 1.0.0 | **Language:** English
**Scope:** Eco Nojin platform and HyDroMa engine | **Assessment date:** 2026-08-14

## 1. Purpose

This document defines the internal engineering quality standards (STD-001 to
STD-015) for the Eco Nojin / HyDroMa codebase. It complements `05_standards.md`,
which covers external/scientific frameworks (FAO, ISO, OGC, UN SDGs); this
document covers how we build, verify, and maintain the software itself.

Each standard records three things:

1. **Requirement** — the normative statement of what must hold.
2. **Audit method** — how compliance is checked (tool, procedure, or review).
3. **Current status** — an honest assessment against the code as of 2026-08-14,
   with file-level evidence.

Status legend: **Implemented** = fully in place and verified; **Partial** = some
elements exist, gaps remain; **Not implemented** = no evidence in the codebase.

## 2. Standards Register

| ID | Domain | Requirement (summary) | Audit method | Current status |
|---|---|---|---|---|
| STD-001 | Code structure & naming | Consistent module layout; PEP 8 / TypeScript conventions; meaningful names; no dead scaffolding | Lint (ruff/ESLint), directory review | Partial |
| STD-002 | Error handling | Validated input at API boundaries; structured error responses; no silent `except`; graceful degradation | Code review, error-path tests | Partial |
| STD-003 | Logging | Structured, leveled logging with request IDs; no secrets in logs | Grep for `logging` usage; log review | Not implemented |
| STD-004 | Testing | Unit + integration + E2E; core-engine coverage ≥ 80 %; tests green in CI | `pytest --cov`, CI gate | Partial |
| STD-005 | Security | TLS everywhere outside dev; explicit CORS allowlist; secrets only via env/vault; input validation; authN/authZ | CORS/TLS config review, secret scan, dependency audit | Partial |
| STD-006 | Accessibility | WCAG 2.1 AA: keyboard, focus, contrast ≥ 4.5:1, resizable text, semantic HTML, labeled inputs, correct lang/dir | axe scan, manual keyboard pass | Not implemented |
| STD-007 | i18n / RTL | All UI strings localized; correct RTL for fa/ar/ur; locale persistence; localized numbers/dates | String-extraction check, RTL visual test | Partial |
| STD-008 | Data model & migrations | Versioned schema migrations (Alembic); no `create_all` in production; idempotent seeds | Alembic presence, migration review | Not implemented |
| STD-009 | Documentation | Every module has a README (purpose, usage, status); project docs bilingual (en/fa) | README inventory per module | Partial |
| STD-010 | Backup & restore | Automated backups; defined RPO/RTO; annual restore drill; 3-2-1 rule | Backup-job inspection, drill records | Not implemented |
| STD-011 | Versioning | SemVer for packages and API; CHANGELOG; git tags | Tag/CHANGELOG inspection | Partial |
| STD-012 | CI/CD | Pipeline: lint → test → build → deploy; gated releases; automated versioning | CI config inspection | Not implemented |
| STD-013 | Code review | Every change reviewed; two-person rule for numerical core; PR checklist | PR history, review records | Not implemented |
| STD-014 | Equations | Every numerical equation carries a scientific reference and a numeric test with tolerance | Docstring + test inspection | Partial |
| STD-015 | API (OpenAPI + compatibility) | Published OpenAPI schema; versioned paths; additive-only changes within a major version; deprecation policy | `/docs` inspection, schema diff | Partial |

## 3. Detail per Standard

### STD-001 — Code structure & naming

- **Requirement:** The repository follows one layout convention (`engine/`,
  `services/`, `frontend/`, `tests/`, `docs/`); Python follows PEP 8 naming
  (snake_case functions, PascalCase classes); TypeScript follows project
  conventions (PascalCase components); no dead or placeholder code survives a
  release; lint and format checks are enforced.
- **Audit method:** Run `ruff check` / `eslint`; review directory tree;
  search for placeholder files.
- **Current status: Partial.**
  - Good: the layout is consistent and modular — `engine/hydroma/` contains
    20+ domain modules (`carbon/`, `satellite/`, `scenarios/`, `watershed/`,
    `ussd/`, `ai_assistant/`, `cpp_bridge/`, …); `services/api_gateway/routers/`
    holds 13 routers; `tests/` is split into `unit/`, `integration/`,
    `benchmarks/`, `e2e/`; naming in Python and TypeScript is consistent and
    descriptive (e.g., `calculate_carbon_sequestration`,
    `SatelliteAnalyzer`, `CarbonCreditPanel`).
  - Gaps: `pyproject.toml` defines no lint/format tooling (no `[tool.ruff]`,
    no black/isort config); no ESLint config in `frontend/`; placeholder code
    exists (`services/auth|ledger|notification|reporting|workflow/main.py`);
    `tests/e2e/` is empty; `ml/`, `blockchain/`, `deploy/` contain only
    `.gitkeep` scaffolding.

### STD-002 — Error handling

- **Requirement:** All API boundaries validate input before processing and
  return structured errors (HTTP status + machine-readable detail); no bare
  `except:` that swallows failures; subsystems degrade gracefully with an
  explicit fallback path.
- **Audit method:** Code review of routers; tests that exercise invalid-input
  and failure paths; grep for bare `except`.
- **Current status: Partial.**
  - Good: Pydantic models validate every API boundary
    (`engine/hydroma/core/schemas.py`, request models in routers with `Field`
    constraints such as `gt=0, le=100000`); routers raise `HTTPException` with
    specific status codes (400/404 in `routers/carbon.py`); the satellite
    provider returns `[]` on `requests.RequestException`
    (`satellite/providers/earth_search.py`) and the analyzer has an explicit
    `_fallback_analysis` path (`satellite/analyzer.py`).
  - Gaps: `routers/carbon.py` `verify_carbon_project` calls `datetime.utcnow()`
    without importing `datetime` — a guaranteed `NameError` on that endpoint
    (see W-002); `compare_project_types` in `engine/hydroma/carbon/calculator.py`
    uses a bare `except Exception: continue`, hiding per-type failures;
    no central error handler; error bodies are ad hoc, not a documented schema.

### STD-003 — Logging

- **Requirement:** Application events are logged with a structured format
  (JSON), leveled severity, and a request correlation ID; secrets and personal
  data never appear in logs; the log pipeline is defined before pilot.
- **Audit method:** `grep -r "import logging"`; sample logs from a request;
  configuration review.
- **Current status: Not implemented.**
  - No `logging` import or logger usage exists in `services/api_gateway/`
    (including all 13 routers) or in `engine/hydroma/` modules
    (verified 2026-08-14). The API relies on Uvicorn's default access log.
    `docs/08_deployment_operations.md` §5 lists structured logging as planned.

### STD-004 — Testing

- **Requirement:** Unit tests for all engine modules; integration tests for
  every router; E2E tests for the critical user journeys; core-engine
  statement coverage ≥ 80 %; the full suite is green and runs in CI on every
  commit.
- **Audit method:** `pytest` with coverage; CI gate inspection.
- **Current status: Partial.**
  - As of 2026-08-14 a full run gives **127 passed, 1 failed** (~11 s):
    `tests/integration/test_sync.py::test_health_reports_mobile_features`
    fails because the health endpoint does not report a `mobile_features`
    module (see W-018). This contradicts the "125/126 passing" figure recorded
    in `docs/09_roadmap.md` §2 — the suite has grown to 128 tests.
  - Coverage: 12 unit-test files (`test_carbon`, `test_scenarios`,
    `test_marketplace`, `test_ussd`, `test_satellite`, `test_watershed`,
    `test_numba_correctness`, `test_models`, `test_climate`, `test_compost`,
    `test_ai`, `test_placeholder`), 4 integration files (`test_api`,
    `test_api_ai`, `test_api_satellite`, `test_sync`), 1 benchmark file
    (`test_numba_performance`); `tests/e2e/` is empty.
  - C++ core has its own tests (`engine/cpp_core/tests/test_hydroma.cpp`).
  - No coverage measurement configured; `pytest-cov` is absent from both
    requirements files; no CI gate exists.

### STD-005 — Security

- **Requirement:** TLS (HTTPS + HSTS) in every non-local environment; CORS
  restricted to an explicit origin allowlist; secrets injected via environment
  or vault, never committed; all inputs validated at boundaries; authentication
  and authorization enforced on write endpoints; dependencies pinned and
  audited.
- **Audit method:** Review of `main.py` CORS config, deployment config,
  `.env.example`, secret scan of the tree, dependency audit (`pip-audit`,
  `pnpm audit`).
- **Current status: Partial** (secure input validation exists; transport,
  CORS, secrets, and auth do not).
  - Input validation: good — Pydantic schemas at every boundary.
  - CORS: `allow_origins=["*"]` with `allow_credentials=True` in
    `services/api_gateway/main.py` — an invalid combination that browsers
    reject; must become an explicit allowlist.
  - Secrets: `.env.example` uses `change_me`; `docker-compose.yml` contains a
    literal `***` password for PostGIS.
  - TLS: not configured; dev runs over HTTP (`docs/06_security_privacy.md` §2).
  - AuthN/AuthZ: none — the auth service is a placeholder and every write
    endpoint is open (see W-016).
  - Dependencies: unpinned in `requirements.txt` (see W-005); known CVE
    tracking exists for the frontend (`docs/security/CVE-2025-66478.md`,
    Next.js 15.1.6, medium severity, patched versions 16.3.1+).

### STD-006 — Accessibility (WCAG 2.1 AA)

- **Requirement:** Full keyboard operability with visible focus; text
  contrast ≥ 4.5:1; text resizable to 200 % without loss of function; semantic
  HTML landmarks; every input labeled; `lang`/`dir` correct per locale.
- **Audit method:** Automated axe scan; manual keyboard-only pass; contrast
  check on the palette.
- **Current status: Not implemented.**
  - No `aria-*` attributes or `role=` in any of the 16 frontend components
    (grep count: 0).
  - `app/layout.tsx` sets `userScalable: false` in the viewport meta — blocks
    pinch-zoom, a WCAG 2.1 AA failure (1.4.4 Resize Text).
  - Panels use inline styles and hardcoded colors (e.g., `#16a34a` text on
    `#dcfce7` backgrounds in `SatellitePanel.tsx`) without a contrast or focus
    audit; some inputs have `<label>` elements, others are unlabeled.
  - No accessibility test tooling or CI check exists.

### STD-007 — i18n / RTL

- **Requirement:** Every user-visible string comes from a locale catalog;
  RTL layouts are correct for fa/ar/ur (including the server-rendered HTML);
  the chosen locale persists; numbers, dates, and units are localized; backend
  messages are localized or mapped.
- **Audit method:** String-extraction scan of components; RTL visual test in
  fa/ar/ur; locale-switch test.
- **Current status: Partial.**
  - 14 locale files exist in `frontend/locales/` (en, fa, ar, ur, de, es, fr,
    hi, it, ms, pt, ru, zh, bn) plus `backend_translations.json`; a language
    switcher and context provider persist the locale in `localStorage`
    (`lib/i18n-context.tsx`); the USSD/SMS engine supports en/fa/ar
    (`engine/hydroma/ussd/engine.py`).
  - Gaps: `app/layout.tsx` hardcodes `<html lang="en" dir="ltr">`; direction is
    switched client-side after hydration only, so SSR HTML is always LTR (see
    W-009); hardcoded English strings remain in components (e.g.,
    `CarbonCreditPanel.tsx`: "Region", "Calculating...", "Estimated Revenue",
    "Permanence (years)", "Methodology:"); the RAG knowledge base is
    English-only (see W-008); API responses are English-only.

### STD-008 — Data model & migrations

- **Requirement:** Schema changes are managed as versioned migrations
  (Alembic); no `create_all`/`drop_all` outside tests; seed data is
  idempotent; the research SQLite schema is a strict subset of the production
  PostGIS schema.
- **Audit method:** Presence of `alembic/` and migration history; review of
  startup code; schema diff between environments.
- **Current status: Not implemented.**
  - `services/api_gateway/main.py` runs `Base.metadata.create_all(bind=engine)`
    on startup; `engine/hydroma/core/database.py` hardcodes
    `sqlite:///./hydroma_research.db`.
  - No `alembic` package, no `alembic.ini`, no migrations directory anywhere in
    the tree (verified). `docs/04_data_model.md` §7 records Alembic as a
    planned task.

### STD-009 — Documentation

- **Requirement:** Every module ships a README stating purpose, usage, status,
  and key references; project-level documentation is maintained bilingually
  (English + Persian); docs carry status/version headers and stay honest about
  implementation state.
- **Audit method:** README inventory per directory; freshness review of
  `docs/`.
- **Current status: Partial.**
  - `docs/en/` and `docs/fa/` each contain 00–09 (master plan, architecture,
    engine, platform, data model, standards, security, i18n, deployment,
    roadmap) plus `99_conversation_summary.md`; a security advisory exists
    under `docs/security/`.
  - Only `engine/cpp_core/README.md` exists at module level; none of the
    `engine/hydroma/*` modules, services, or frontend have READMEs.
  - `README.md` (repository root) has a corrupted Persian section (mojibake —
    see W-006).

### STD-010 — Backup & restore

- **Requirement:** Automated backups of all durable state; documented RPO/RTO
  targets; an annual restore drill with a written result; 3-2-1 rule
  (3 copies, 2 media, 1 off-site).
- **Audit method:** Inspection of scheduled jobs and scripts; drill records.
- **Current status: Not implemented.**
  - No backup scripts exist (`scripts/` is empty); `docs/08_deployment_
    operations.md` §6 plans `pg_dump`/WAL for PostGIS and file snapshots for
    the SQLite research DB. Most current state is in-memory anyway
    (marketplace, carbon registry, sync log — see W-019), which makes backups
    moot until persistence lands.

### STD-011 — Versioning (SemVer)

- **Requirement:** All packages and the public API follow SemVer 2.0.0;
  releases are tagged; a CHANGELOG records user-visible changes.
- **Audit method:** `git tag`, CHANGELOG presence, version string review.
- **Current status: Partial.**
  - The API version is declared in code (`version="1.2.0"` in
    `services/api_gateway/main.py` and in the health payload) and the path
    prefix `/api/v1/` is used consistently across routers.
  - There is no Git repository (see W-011), no tags, no CHANGELOG;
    `pyproject.toml` declares `version = "0.1.0"` while the frontend
    `package.json` says `0.1.0` and the gateway says `1.2.0` — the three
    version numbers are already out of sync.

### STD-012 — CI/CD

- **Requirement:** A pipeline runs lint, unit/integration/E2E tests, C++
    build + `ctest`, frontend build, dependency audit, and then builds and
    deploys artifacts; releases are gated and versioned automatically.
- **Audit method:** CI configuration inspection; pipeline run logs.
- **Current status: Not implemented.**
  - `deploy/ci/`, `deploy/docker/`, and `deploy/k8s/` contain only `.gitkeep`;
    there is no Git repository to host CI; `docs/08` §4 describes the target
    pipeline as planned and names Git initialization as the immediate
    prerequisite.

### STD-013 — Code review

- **Requirement:** Every change to the main branch is reviewed by at least one
  person other than the author; changes to the numerical core
  (`engine/cpp_core/`, `engine/hydroma/cpp_bridge/`) require a second reviewer
  and a passing numeric test; review checklist covers security, error paths,
  and docs.
- **Audit method:** Pull-request history; review records.
- **Current status: Not implemented.**
  - No Git history or PR process exists; the codebase is single-authored so
    far. This standard takes effect at the first commit (see
    `12_30_year_strategy.md` for the governance timeline).

### STD-014 — Equations (scientific references + numeric tests)

- **Requirement:** Every numerical formula in the engine cites its primary
  scientific source in the docstring and has at least one numeric test that
  checks output against a known value or bound (with tolerance); simplified
  approximations are labeled as such with their validity limits.
- **Audit method:** Docstring inspection for citations; test inspection for
  asserted values (not just `> 0`); diff against reference implementations.
- **Current status: Partial.**
  - Strongly covered: FAO-56 Penman-Monteith / Hargreaves-Samani
    (`climate/et_calculator.py`, `cpp_core/src/climate.cpp` — Allen et al.
    1998, Hargreaves & Samani 1985); van Genuchten/Mualem (`soil.cpp` —
    van Genuchten 1980, Carsel & Parrish 1988); RUSLE (`erosion.cpp` — Renard
    et al. 1997); Muskingum-Cunge (`hydrology.cpp`, `hydrology_fast.py` —
    Cunge 1969, Chow et al. 1988); vegetation indices with range tests
    (`tests/unit/test_satellite.py`); Numba-vs-NumPy numeric identity tests
    (`tests/unit/test_numba_correctness.py`).
  - Gaps: carbon sequestration tests only assert `> 0`
    (`tests/unit/test_carbon.py`) — no check against the cited IPCC AR6 /
    Verra/Gold Standard rate tables; watershed structure design formulas
    (`watershed/calculator.py`) cite the FAO field manual but have no numeric
    reference values and no in-code limitation note for the rational-method
    runoff estimate; the simplified AquaCrop crop model is cited
    (Steduto et al. 2009) and labeled "simplified" in its docstring, but its
    limitation is documented in prose only (see W-013).

### STD-015 — API (OpenAPI + backward compatibility)

- **Requirement:** The gateway publishes a complete OpenAPI schema; the schema
  is part of the review process; changes within a major version are
  additive-only; breaking changes require a new major version and a published
  deprecation period; clients pin the API major version.
- **Audit method:** `/docs` and `/redoc` inspection; OpenAPI schema diff in
  CI; deprecation notice review.
- **Current status: Partial.**
  - FastAPI auto-generates OpenAPI; the app declares `title`, `description`,
    `version="1.2.0"` and the health endpoint reports modules and access
    channels (`services/api_gateway/main.py`); `response_model` is used in
    some routers (e.g., `routers/sync.py`) but not consistently; all routers
    share the `/api/v1/` prefix.
  - Gaps: no schema-versioning or deprecation policy exists; no contract tests
    pin response shapes; the health payload's module list is already out of
    sync with the test suite (W-018).

## 4. Compliance Summary

| Status | Standards |
|---|---|
| Implemented | — (none fully) |
| Partial | STD-001, STD-002, STD-004, STD-005, STD-007, STD-009, STD-011, STD-014, STD-015 |
| Not implemented | STD-003, STD-006, STD-008, STD-010, STD-012, STD-013 |

Remediation priority (see `11_weaknesses_and_fixes.md` for the itemized
defects):

1. STD-008 (migrations) and STD-012 (CI/CD) — blocked by the missing Git
   repository (W-011) and unpinned dependencies (W-005).
2. STD-005 (security) — CORS allowlist, secrets, and auth are pre-pilot
   blockers (W-003, W-007, W-016, W-017).
3. STD-004 (testing) — restore a green suite (W-018) and add coverage
   thresholds.
4. STD-003 (logging), STD-010 (backup), STD-013 (code review) — required
   before the first pilot deployment.
5. STD-006 (accessibility) — required before public rollout; schedule an axe
   audit alongside the i18n/RTL work (STD-007).

## 5. References

- `docs/en/05_standards.md` — external scientific/standards alignment.
- `docs/en/06_security_privacy.md` — security posture and threat model.
- `docs/en/08_deployment_operations.md` — deployment and ops baseline.
- `docs/en/09_roadmap.md` — phase plan and known-defect list.
- `11_weaknesses_and_fixes.md` — itemized defects with evidence.
- `12_30_year_strategy.md` — how these standards are sustained over decades.
