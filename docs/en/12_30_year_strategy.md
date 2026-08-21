# 12. Thirty-Year Maintenance Strategy

**Status:** Draft for review | **Version:** 1.0.0 | **Language:** English
**Scope:** Eco Nojin platform and HyDroMa engine | **Horizon:** 2026 – 2055

## 1. Purpose

Ecosystem-restoration and carbon-incentive infrastructure must outlive
individual frameworks, funding cycles, and technology generations. A 30-year
horizon (to 2055) is not a forecast; it is a set of policies that make
continuity the default: minimal dependencies, stable interfaces, open data,
and documented decisions. This document defines those policies and the
cadence that keeps them alive.

It assumes the baseline in `docs/00`–`docs/09` and the defect register in
`11_weaknesses_and_fixes.md`; in particular it assumes the immediate fixes
(Git, pinned dependencies, real satellite data, auth, migrations) land first.

## 2. Principles

| Principle | Policy |
|---|---|
| Minimal, stable dependencies | Every runtime dependency must justify itself against the 30-year cost of keeping it patched. Prefer stdlib, then small stable libraries, then frameworks. A dependency review runs annually: drop, replace, or pin-and-budget each one. |
| Stable API interfaces | The public API is a contract, not an implementation detail. `/api/v1/` paths and response shapes are frozen for the life of v1; new capabilities are additive. |
| Open data formats | All durable data uses open, documented formats: SQL schemas owned by the project, GeoPackage/PostGIS for spatial data, netCDF/CF for climate time series, JSON/CSV for exchange. No proprietary binary formats for stored truth. |
| Migratability | Every component must be replaceable without rewriting the whole: the engine is a Python orchestration layer over swappable numerical kernels (NumPy/Numba/C++20), data access goes through one model layer, and providers are behind interfaces (`satellite/providers/base.py`). |
| Continuity over novelty | Adopt a new technology only when it reduces the 30-year risk (maintainability, security, hiring) — never for its own sake. |

## 3. Version Upgrade Program

### 3.1 Language and runtime support policy

| Runtime | Baseline (2026) | Policy |
|---|---|---|
| Python | 3.11 (per `pyproject.toml`) | Support the current minor plus the two previous (3-version window). Adopt each new minor within 18 months of release; drop the oldest only after the ecosystem (FastAPI, SQLAlchemy, scientific stack) supports the next. |
| Node.js | ≥ 18.18 (per `frontend/package.json`), currently on 22 LTS line | Track Node LTS only. Upgrade the frontend runtime inside the LTS window; never run on EOL Node in any environment. |
| C++ | C++20 (per `engine/cpp_core/CMakeLists.txt`) | Stay on a compiler-generation level that is available in the pinned CI image; move to C++23 only when all three major toolchains support it for a full year. |
| PostgreSQL/PostGIS | 16-3.4 (per `docker-compose.yml`) | Upgrade within 12 months of each major release's first point release; keep one major behind is allowed, two behind is not. |

### 3.2 Upgrade window

- One **scheduled upgrade window per quarter** (Q1: language runtimes, Q2:
  frameworks, Q3: database, Q4: everything else). No unplanned major upgrades
  within 60 days of a pilot or reporting deadline.
- Every upgrade is a branch with: changelog review → full test suite →
  benchmark comparison (Numba vs NumPy vs C++ paths,
  `tests/benchmarks/`) → signed-off rollback plan.
- Dependency refresh: `pip-audit` + `pnpm audit` run monthly; critical
  security patches are exempt from the window and applied immediately with
  the same rollback discipline.

## 4. Compatibility

### 4.1 Semantic versioning

- The gateway API, engine packages, and frontend each follow SemVer 2.0.0.
  The three currently disagree (`0.1.0` in `pyproject.toml` and
  `package.json` vs `1.2.0` in the gateway) — they are reconciled at the first
  release, then kept in sync by CI.
- **Major:** breaking changes (removed endpoints, changed response shapes,
  changed numerical semantics). **Minor:** additive features. **Patch:**
  fixes that do not change contracts.

### 4.2 Deprecation policy

1. A change that breaks compatibility is announced in the CHANGELOG and an
   ADR at least **two minor releases** before it ships.
2. The deprecated surface keeps working for the whole current major version
   and is marked `Deprecated` in the OpenAPI schema and docs.
3. Removal happens only in the next major version, with a migration guide
   written and tested.

### 4.3 Feature flags

- New behavior that changes user-visible outcomes ships behind a flag with a
  default that preserves current behavior; flags are removed (or flipped)
  deliberately at the quarterly window, never silently.
- Flags are configuration, not code: defined in one settings module
  (`engine/hydroma/config/settings.py` grows into the single config source).

### 4.4 API versioning

- The `/api/v1/` prefix is frozen for v1. A v2 exists only when a breaking
  change is unavoidable; v1 and v2 run side by side for at least 2 years, and
  v1 read endpoints may be kept indefinitely at trivial cost.
- OpenAPI schema diff runs in CI for every change (STD-015).

## 5. Backup and Recovery

### 5.1 Targets

- **RPO** ≤ 24 h for operational state; **RTO** ≤ 48 h for a full restore of
  the platform.
- 3-2-1 rule: 3 copies, 2 media types, 1 off-site (different region than
  primary).

### 5.2 Schedule (post-persistence; see W-019)

| Asset | Frequency | Method |
|---|---|---|
| PostgreSQL/PostGIS | Continuous WAL + daily full `pg_dump` | `pg_dump` to object storage + WAL archiving |
| SQLite research DB (until retired) | Daily snapshot | File copy with integrity hash |
| Raw satellite / climate cache | Re-fetchable | No backup; documented cache-invalidation policy (per `docs/08` §6) |
| Configuration, docs, code | Every commit | Git repository + off-site mirror |

### 5.3 Restore drill

- One **restore drill per year** (Q4), from off-site media into a clean
  environment, with a written result (restored-at timestamp, data checksum
  comparison, report filed in `docs/ops/`).
- The drill is a release gate: a year without a successful drill is treated as
  "no backup".

## 6. Accountability Reporting

### 6.1 Annual status document

Each year (Q1) the project publishes `docs/status/YYYY.md` containing:

1. Compliance against these standards (STD-001…015 table, from
   `10_quality_standards.md`).
2. Updated weakness register (`11_weaknesses_and_fixes.md`) with evidence for
   every status change.
3. Dependency ledger: what was added/removed/pinned and why.
4. Backup drill result and incident log.
5. Science note: any change to equations, rates, or models with the
   underlying reference (STD-014).

### 6.2 Decision log (ADR)

- Every consequential decision (schema change, dependency swap, methodology
  change, deprecation) is recorded as an ADR in `docs/adr/ADR-####-title.md`
  with: context, decision, alternatives considered, consequences, date.
- The ADR index is maintained in `docs/adr/README.md` and reviewed at each
  quarterly window. ADR-0001 records the adoption of this strategy.

### 6.3 Incident response

- A runbook (`docs/ops/runbook.md`, drafted before the first pilot per
  `docs/06` §6) defines severity levels, contacts, and breach-notification
  obligations; it is exercised once a year with the restore drill.

## 7. Knowledge Continuity

- **Living docs:** `docs/` (bilingual en/fa) is maintained in the same commit
  as the code it describes; a docs check runs in CI (READMEs per module,
  STD-009; correct UTF-8, W-006 regression guard).
- **Bus factor:** no module may be understood by only one person. Each
  `engine/hydroma/*` module gets a README and a named owner, reviewed
  annually. Numerical kernels require two reviewers (STD-013).
- **Training:** a short onboarding guide (`docs/en/99_conversation_summary.md`
  already captures project direction) grows into `docs/ops/onboarding.md` —
  how to run, test, extend, and deploy each layer. One "engine deep-dive"
  session per year, recorded, keeps the scientific basis (FAO-56, RUSLE,
  van Genuchten, Muskingum-Cunge, AquaCrop approximations) transferable.
- **Tooling continuity:** all dev tooling is captured in `pyproject.toml`,
  lockfiles, and CI images, so a 2055 engineer reproduces the 2026 environment
  deterministically.

## 8. Scenario: 2055

Concrete, deliberately boring picture of a working system in 2055 — the
strategy's job is to make this unremarkable:

- **API:** `/api/v1/` still serves the 2026-era read endpoints (soil
  profiles, marketplace listings, health). A `/api/v3/` exists for newer
  clients; the v2→v3 migration was completed in 2041 under the deprecation
  policy. OpenAPI diffing has run in CI for 29 years.
- **Engine:** `engine/hydroma/` still imports the same package layout. The
  carbon module runs Verra v6-era methodology with real field MRV data
  streams; the 2026-era `SEQUESTRATION_RATES` table survives as a documented
  historical artifact, flagged "legacy estimate, not for issuance". The RAG
  assistant retrieves from a 12-language corpus; the 2026 English TF-IDF
  corpus is archived as a baseline dataset.
- **Data:** the schema migrated SQLite → PostGIS (2027) → PostGIS 20 (2043)
  through Alembic; 29 years of MRV measurements, sync logs, and market orders
  are intact and queryable. The annual restore drill restored this dataset
  from off-site media 28 times without failure.
- **Satellite:** the `SatelliteProvider` interface (`providers/base.py`)
  originally written for Sentinel-2 L2A now wraps the successor missions;
  `fetch_tile` returns real pixels with provenance — the synthetic fallback
  (W-001) was removed in 2027 and exists only in git history.
- **Runtimes:** the code runs on Python 3.x (2026-era 3.11 code still
  executes after mechanical migrations in 2031, 2037, 2043, 2049); the
  frontend is on the 2055-era Next.js LTS; Node has been upgraded 12 times
  inside LTS windows.
- **People:** the ADR log (400+ entries) and the bilingual docs let a new
  maintainer answer "why does this exist?" in an afternoon. The 2026 decision
  to keep dependencies minimal means only 14 runtime packages had to be
  carried across the full 30 years.

## 9. Long-Term Risk Matrix

| Risk (to 2055) | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A core dependency goes unmaintained or hostile | High | Medium | Minimal-dependency policy; annual review; fork-and-own fallback plan for the top 5 packages |
| Climate/carbon methodologies change (Verra, ISO 14064 revisions) | Certain | High | Methodology-parameter tables kept separate from code; ADR per methodology change; never hardcode standards into kernel code |
| Satellite program retirement (Sentinel-2 EOL) | Certain | Medium | Provider interface + provenance fields from day 1; mock/test fixtures make provider swaps testable |
| Key person leaves (bus factor) | High | Medium | Module READMEs, named owners, onboarding docs, two-reviewer rule |
| Storage/format rot (SQLite→PostGIS→…) | Certain | Medium | Alembic from 2027; open formats only; annual restore drill as the canary |
| Regulatory change (carbon credit issuance rules) | High | High | Internal `/verify` stays a demo until accredited verification; compliance review at each milestone (`docs/05` §6) |
| Hardware/compiler landscape shifts | Medium | Low | C++ core behind a thin bridge (`cpp_bridge/`); kernels have NumPy fallbacks; benchmark suite guards regressions |
| Frontend framework churn | High | Medium | Thin UI over the API contract; PWA shell (service worker, offline hooks) is stable regardless of framework |
| Data-sovereignty/legal change across target countries | High | Medium | Consent records, anonymization, per-tenant separation (`docs/06`); legal review at each phase milestone |
| Security incident (CVE in a runtime or the API) | Certain | High | Monthly audits, quarterly upgrade window, runbook, restore drill doubles as incident rehearsal |

## 10. First-Year Actions (2026–2027)

1. `git init`, baseline commit, CI with lint + tests + OpenAPI diff
   (resolves W-011, W-012-adjacent, STD-012).
2. Pin and layer dependencies; lockfiles; reconcile `requirements*.txt`
   (W-005, W-020).
3. Alembic baseline migration; persist marketplace/carbon/sync state
   (W-014, W-019, STD-008).
4. CORS allowlist, secrets out of compose, auth service v1 (W-003, W-007,
   W-016).
5. Replace simulated satellite bands; flag any remaining synthetic output
   (W-001).
6. Fix the red test (W-018) and the carbon `datetime` bug (W-002); add the
   verify-flow integration test.
7. Publish ADR-0001 (this strategy) and the first annual status document
   (`docs/status/2027.md`).

## 11. References

- `10_quality_standards.md` — standards this strategy sustains.
- `11_weaknesses_and_fixes.md` — defect register with first-year actions.
- `docs/en/00_master_plan.md` — vision and phase map.
- `docs/en/05_standards.md` — external standards compliance cadence.
- `docs/en/08_deployment_operations.md` — ops baseline and environments.
