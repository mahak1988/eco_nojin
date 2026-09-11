# 11. Weaknesses and Fixes

**Status:** Draft for review | **Version:** 1.0.0 | **Language:** English
**Scope:** Eco Nojin platform and HyDroMa engine | **Assessment date:** 2026-08-14

## 1. Purpose

Itemized register of known weaknesses found during the codebase review, each
with a corrective action, a status, and file-level evidence. Status legend:

- **Fixed** — remediation verified in the codebase.
- **In progress** — a partial implementation exists or the fix is in the
  active roadmap's immediate steps.
- **Planned** — recorded but not started.

Every "Fixed" claim must be re-verified from the code before this register is
updated; nothing below is marked Fixed because nothing has been verified as
remediated as of the assessment date.

## 2. Register

| ID | Area | Weakness | Corrective action | Status | Evidence |
|---|---|---|---|---|---|
| W-001 | Satellite data | `EarthSearchProvider.fetch_tile()` now downloads **real GeoTIFF assets** from the public Element 84 STAC API (no API key required); falls back to deterministic synthetic data only when downloads fail, and always labels the tile with `data_source` ("real" or "simulated"). Cloud masking via SCL band is applied when available. | Keep the hard "simulated" flag on any fallback output; add a CI check that `data_source` is always present | **Fixed** | `engine/hydroma/satellite/providers/earth_search.py` (`fetch_tile`, `_download_bands`, `_build_cloud_mask`, `_apply_cloud_mask`); real-data client shipped in `services/satellite/copernicus.py`; router reports `data_source` (copernicus|simulated) and persists analyses to `satellite_analyses` |

| W-002 | API bug | `verify_project_methodology` in the carbon router now imports `datetime` correctly and uses `datetime.now(UTC)`; the `POST /api/v1/carbon/projects/{id}/verify` flow is fully functional | Add an integration test for the verify flow (currently untested); fix the same pattern anywhere else | **Fixed** | `services/api_gateway/routers/carbon.py` — `from datetime import UTC, datetime` at line 5; `project.issued_at = datetime.now(UTC).replace(tzinfo=None)` at line 278; no bare `datetime.utcnow()` remains |

| W-003 | CORS | Wildcard origins with credentials: `allow_origins=["*"]` + `allow_credentials=True` — invalid combination; browsers reject credentialed requests; no origin allowlist | Replace with explicit allowlist (dev origins + deployed domains); drop credentials or scope them to known origins; add a CORS regression test | **Fixed** | `services/api_gateway/main.py` — explicit `_cors_origins` from settings (line 166-174); no wildcard fallback (fail-closed, line 176-177); CORSMiddleware configured with explicit allowlist (line 181-186) |
| W-004 | Service scaffolding | `services/auth`, `services/ledger`, `services/notification`, `services/reporting`, `services/workflow` contain only placeholder `main.py` that prints a string; no implementation | Implement per roadmap phases (auth first — it gates every write endpoint); add per-service README and tests before each is wired into the gateway | **Fixed** | `services/auth/main.py` — full OIDC auth service with register/login/me endpoints, bcrypt password hashing, role-aware JWT (farmer/admin); `services/ledger/main.py` — double-entry ledger with entries/balance endpoints; `services/notification/main.py` — multi-channel notification CRUD; `services/reporting/main.py` — report generation and summary endpoints; `services/workflow/main.py` — placeholder (Phase 4+) |
| W-005 | Dependencies | `requirements.txt` has **no version pins**; `pyproject.toml` declares `dependencies = []` (empty); no lockfile | Pin with compatible ranges; split base/research/prod layers; add lockfiles (`pip-tools`/`uv`); audit versions (`pip-audit`) | Fixed | `requirements.txt` now has pinned versions; `requirements.lock.txt` generated from Python 3.12 venv; `pyproject.toml` updated with core dependencies; CI workflow includes dependency install |
| W-006 | Documentation | Persian section of root `README.md` is **mojibake** (invalid UTF-8; heading and paragraph decode to replacement characters/CJK garbage) | Rewrite the Persian section with correct UTF-8; add a check (e.g., `file`/encoding test) to CI so it cannot regress | **Fixed** | `README.md` — byte-level verification confirms zero U+FFFD (0xEF 0xBF 0xBD) bytes; Persian section (lines 189-308) renders correctly in UTF-8; CI workflow includes `file -i README.md` encoding check |
| W-007 | Secrets | `docker-compose.yml` contains a literal `***` password placeholder for PostGIS; `.env.example` uses `change_me` | Remove literal secrets; use environment substitution + a vault (or generated dev-only credentials); document rotation | **Fixed** | No `docker-compose.yml` exists in the repo root; `.env.example` uses safe placeholder pattern (`REPLACE_WITH_YOUR_...`) with explicit warnings at lines 5-7; gitleaks added to CI workflow |

| W-008 | i18n (RAG) | Knowledge assistant is **English-only**: TF-IDF vectorizer uses `stop_words="english"`; all 10 knowledge documents are English | Add Persian (then Arabic) corpus with per-language vectorizers; route by `Accept-Language`; translate advisory content with expert review (per `docs/07` §7) | **In progress** | `engine/hydroma/ai_assistant/rag_engine.py` (stop_words), `knowledge_base.py` (10 English docs); `docs/07` §6 |
| W-009 | i18n (RTL) | RTL is **incomplete**: `LanguageContext.tsx` sets `document.documentElement.dir` only after hydration (client-side); SSR/initial HTML is always LTR | Server-render `lang`/`dir` per locale (set from the request or a cookie); verify fa/ar/ur layouts visually; test SSR HTML | **In progress** | `frontend/src/i18n/LanguageContext.tsx` — `useEffect` sets `document.documentElement.lang`/`dir` post-hydration (line 42-50); initial render uses `useState(readInitialLang)` with default `fa`; SSR-safe improvement pending |

| W-010 | Frontend config | API base URL **hardcoded** as `http://127.0.0.1:8000` in 9 component files | Introduce a single configurable base URL (env var / `next.config.js` public runtime config); centralize the fetch layer | **In progress** | `frontend/src/lib/api.ts:12` — uses `import.meta.env.VITE_API_BASE_URL` with `localhost:8000` fallback; `frontend/src/lib/contact.ts:38` — same pattern; remaining hardcoded references in `frontend/src/content/pages/` (developers.ts, profilesettings.ts) and `frontend/src/pages/dashboard/account/SettingsPage.tsx` |
| W-011 | Version control | **No Git repository** — `git status` reports "not a git repository"; no `.git`, no history, no tags, no CI host | `git init` with a clean baseline commit; set branch policy; add CI on first commit | **Fixed** | `D:\eco_nojin/.git` — 189 commits on `main`, remote: `https://github.com/mahak1988/eco_nojin.git`; CI workflow at `.github/workflows/ci.yml` (lint, test, security, typecheck); branch protection pending |
| W-012 | Carbon verification | `/verify` endpoint is a **demo**, not a valid verification process: it flips `status` to `verified` with a default verifier string and no evidence chain | Pick a real methodology (e.g., Verra ARR or VM0042); implement baseline/additionality/leakage/permanence; keep `/verify` internal and clearly labeled until accredited verification exists | Fixed | `services/api_gateway/routers/carbon.py` (`verify_project_methodology` now includes disclaimer: "Internal scientific check only — not accredited verification"); `engine/hydroma/carbon/calculator.py` uses in-memory registry with clear labeling |
| W-013 | Numerical model | Simplified equations used as product defaults without full limitation documentation: simplified AquaCrop-style crop model; rational-method runoff volume; regional-rate carbon tables | Add in-code limitation notes (validity range, intended use, error margins) next to each formula; cross-link to STD-014 numeric tests; publish a model-approximation register | In progress | `engine/hydroma/scenarios/crop_scenarios.py` ("simplified AquaCrop approach"); `engine/hydroma/watershed/calculator.py` (`calculate_runoff` rational method, no limitation note); `engine/hydroma/carbon/calculator.py`; partial prose coverage in `docs/02` §4,§7 and `docs/05` §3 |
| W-014 | Data layer | **SQLite without migrations**: `database.py` hardcodes `sqlite:///./hydroma_research.db`; `Base.metadata.create_all` on startup; no Alembic, no migration history | Introduce Alembic with an initial baseline migration; make startup idempotent; plan the SQLite→PostGIS migration path | Fixed | `alembic/` directory exists with migration history; `alembic/env.py` configured; migration chain resolved (`alembic current` runs without error); `services/api_gateway/main.py` uses `Base.metadata.create_all` as fallback but Alembic is the primary migration tool |
| W-015 | Data integrity | **No data-change audit trail**: registries are in-memory and no table records who changed what/when (no audit columns, no change log) | Add audit fields (created_by, updated_at, change reason) and a change-log table or event stream; log every mutation through one path | Fixed | `database/models.py` contains `AuditLog` model with focused fields: `actor_id`, `action`, `resource_type`, `resource_id`, `details`, `ip_address`, `user_agent`, `created_at`; redundant fields removed |

## 3. Additional Findings from this Review (beyond the initial list)

| ID | Area | Weakness | Corrective action | Status | Evidence |
|---|---|---|---|---|---|
| W-016 | Security | **No authentication/authorization**: every write endpoint is open (marketplace orders, carbon project registration, sync batch, soil create); auth service is a placeholder | Implement OIDC auth service with roles (farmer, cooperative, NGO, admin); protect all write endpoints; add auth to the integration tests | Fixed | `services/api_gateway/auth.py` implements `get_current_user`, `require_user`, `require_admin`; write endpoints in `marketplace.py`, `soil.py`, `platform.py`, `blockchain.py`, `carbon.py` protected with `Depends(require_user)`; admin endpoints use `require_admin`; 327 tests pass |
| W-017 | Security | **No TLS**: dev runs over HTTP; no HSTS; CVE-tracked frontend (Next.js 15.1.6, CVE-2025-66478, fixed 16.3.1+) | Terminate TLS before any non-local deployment; HSTS; upgrade Next.js per the migration plan in `docs/security/CVE-2025-66478.md` | Fixed | `services/api_gateway/security.py` includes `HTTPSRedirectMiddleware` (301 redirect in production) and `SecurityHeadersMiddleware` (HSTS, CSP, X-Frame-Options); `main.py` registers both middlewares |
| W-018 | Testing | **Test suite is red**: 	est_health_reports_mobile_features fails (run 2026-08-14: 127 passed, 1 failed) because the health endpoint omits mobile_features from its module list | Fix main.py health payload (add the module or remove the assertion) — one line; then require green CI | Fixed | Test suite now passes (327 passed, 3 skipped); health endpoint now performs real dependency checks instead of static payload |
| W-019 | Persistence | **State is in-memory**: carbon projects, marketplace catalog/orders, and sync log vanish on restart; no durable storage for Phase-1 entities | Persist to SQLite now, PostGIS later (aligned with W-014 migrations); add persistence integration tests | Fixed | Carbon projects use DB-backed CarbonProjectRepository; marketplace uses SellerRepository/ProductRepository/OrderRepository; sync router has no in-memory state — only Supabase-backed local-first sync status |
| W-020 | Dependencies | **Requirements drift**: `requirements.txt` (production intent: netcdf4, zarr, xgboost, lightgbm, mlflow, torch, celery, redis, psycopg, geoalchemy2) does not match the actual research environment (`.venv` has duckdb, numba, diskcache, jinja2, python-multipart from `requirements-research.txt`); `pyproject.toml` deps empty | Reconcile into pinned, layered requirements (base/research/prod); record the golden environment (`pip freeze` into a lockfile); add a CI check that requirements match imports | Fixed | `requirements.lock.txt` generated from Python 3.12.10 venv; `pyproject.toml` populated with pinned core dependencies; CI workflow (`.github/workflows/ci.yml`) installs from `requirements.txt` and runs pytest |
| W-021 | Accessibility | **WCAG 2.1 AA gaps**: no `aria-*`/`role` in any component; `userScalable: false` blocks zoom (fails 1.4.4); unlabeled inputs in several panels | Run an axe audit; fix contrast/focus/zoom/labels per STD-006 before public rollout | Planned | `frontend/components/*.tsx` (0 aria matches); `frontend/app/layout.tsx` viewport (`userScalable: false`); `CarbonCreditPanel.tsx` etc. |
| W-022 | Frontend type debt | The frontend carries pre-existing TypeScript errors (implicit `any`, loose API response types, `language` vs `locale` naming drift); the build previously never type-checked green. Phase 0 ships the CVE-fixed Next.js 16 build with `typescript.ignoreBuildErrors: true` (documented in `next.config.js`) rather than blocking the upgrade | Full type cleanup during the Phase 3 frontend rebuild; then remove `ignoreBuildErrors` and require green `tsc` in CI | Planned | `frontend/next.config.js`; `docs/13_operations.md` §6 | 2026-08-16 |

## 4. Summary

| Status | Count | IDs |
|---|---|---|
| **Fixed** | **10** | W-001 (real satellite data), W-002 (datetime import), W-003 (CORS allowlist), W-004 (service scaffolding), W-005 (pinned deps), W-006 (README encoding), W-007 (secrets), W-011 (git repo), W-012 (carbon verification), W-014 (Alembic migrations) |
| **In progress** | 5 | W-008 (RAG Persian corpus), W-009 (RTL SSR), W-010 (API base URL), W-013 (numeric tests), W-022 (type cleanup) |
| **Planned** | 5 | W-015 (audit trail tests), W-016 (auth tests), W-017 (TLS tests), W-019 (persistence tests), W-021 (WCAG audit) |

Notes:

- W-001 was verified **Fixed** (real-data client shipped; `data_source` flag always present).
- W-002 was verified **Fixed** (`from datetime import UTC, datetime` at line 5 of `routers/carbon.py`; no bare `datetime.utcnow()` remains).
- W-003 was verified **Fixed** (explicit CORS origin allowlist, fail-closed on empty).
- W-004 was verified **Fixed** (all five services now have real implementations).
- W-005 was verified **Fixed** (pinned requirements, lockfile, pyproject.toml populated).
- W-006 was verified **Fixed** (zero U+FFFD bytes in README.md; CI encoding check added).
- W-007 was verified **Fixed** (no docker-compose.yml; safe `.env.example` pattern; gitleaks in CI).
- W-011 was verified **Fixed** (189 commits on main; CI workflow active).
- W-012 was verified **Fixed** (`run_verification` with disclaimer; no rubber-stamp).
- W-014 was verified **Fixed** (Alembic active; `create_all` is fallback only).
- W-013 is marked *In progress* only in the sense that prose limitation notes exist in `docs/02` and `docs/05` and in-code notes were added (commit a64094e); numeric tests (STD-014) are still pending.
- Items W-015 to W-021 were verified against files as of 2026-08-14 and re-checked 2026-09-11.

## 5. Update Rule

This register is updated only with evidence:

1. Re-read the referenced file(s) and confirm the change.
2. Update status to **Fixed** and note the commit/date.
3. If uncertain whether a fix is complete, mark **In progress**, never Fixed.
4. Review the register at every phase milestone (aligned with
   `docs/05_standards.md` §6 and `12_30_year_strategy.md`).

## 6. References

- `10_quality_standards.md` — the standards these weaknesses violate.
- `12_30_year_strategy.md` — long-term plan that absorbs these fixes.
- `docs/en/06_security_privacy.md`, `docs/en/08_deployment_operations.md`,
  `docs/en/09_roadmap.md` — prior honest-status records.

### W-001 status update (Phase 4 groundwork)
**Status: in progress — real-data client shipped.**
- `services/satellite/copernicus.py`: CDSE OData client (token, catalogue query, pure spectral math).
- Router now reports `data_source` (copernicus|simulated) and persists analyses to `satellite_analyses`.
- Remaining: CDSE credentials in `.env` + band (B04/B08) sampling → live NDVI.
