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
| W-001 | Satellite data | `EarthSearchProvider.fetch_tile()` returns **synthetic random bands** (`np.random.uniform`) seeded by item hash, not real Sentinel-2 pixels | Replace with real GeoTIFF downloads from the STAC asset links; add cloud masking, quality flags, and a data-provenance field; keep a hard "simulated" flag on any demo output | Planned | `engine/hydroma/satellite/providers/earth_search.py` (`fetch_tile`, lines marked "simplified mock … synthetic data for demo"); `docs/02` §7 and `docs/06` §3 warn about it |
| W-002 | API bug | `verify_carbon_project` in the carbon router calls `datetime.utcnow()` but `datetime` is **never imported** in `routers/carbon.py` → guaranteed `NameError` on `POST /api/v1/carbon/projects/{id}/verify` | Add the `datetime` import; add an integration test for the verify flow (currently untested); fix the same pattern anywhere else | In progress | `services/api_gateway/routers/carbon.py` (~line 200, `project.verification_date = datetime.utcnow()`); imports at top of file lack `datetime`; listed in `docs/09_roadmap.md` §3 item 3 ("datetime import bug in carbon verify endpoint") |
| W-003 | CORS | Wildcard origins with credentials: `allow_origins=["*"]` + `allow_credentials=True` — invalid combination; browsers reject credentialed requests; no origin allowlist | Replace with explicit allowlist (dev origins + deployed domains); drop credentials or scope them to known origins; add a CORS regression test | Planned | `services/api_gateway/main.py` (CORSMiddleware block); flagged in `docs/06` §2 and `docs/09` §3 item 3 |
| W-004 | Service scaffolding | `services/auth`, `services/ledger`, `services/notification`, `services/reporting`, `services/workflow` contain only placeholder `main.py` that prints a string; no implementation | Implement per roadmap phases (auth first — it gates every write endpoint); add per-service README and tests before each is wired into the gateway | Planned | `services/*/main.py` (each prints "Eco Nojin service placeholder: …"); `docs/00` phase plan |
| W-005 | Dependencies | `requirements.txt` has **no version pins**; `pyproject.toml` declares `dependencies = []` (empty); no lockfile | Pin with compatible ranges; split base/research/prod layers; add lockfiles (`pip-tools`/`uv`); audit versions (`pip-audit`) | Planned | `requirements.txt` (unpinned list incl. fastapi, sqlalchemy, torch, celery…); `pyproject.toml` `[project] dependencies = []`; roadmap §3 item 1 |
| W-006 | Documentation | Persian section of root `README.md` is **mojibake** (invalid UTF-8; heading and paragraph decode to replacement characters/CJK garbage) | Rewrite the Persian section with correct UTF-8; add a check (e.g., `file`/encoding test) to CI so it cannot regress | Planned | `README.md` — byte-level read shows U+FFFD replacement chars in the Persian block; roadmap §3 item 3 ("README Persian encoding") |
| W-007 | Secrets | `docker-compose.yml` contains a literal `***` password placeholder for PostGIS; `.env.example` uses `change_me` | Remove literal secrets; use environment substitution + a vault (or generated dev-only credentials); document rotation | Planned | `docker-compose.yml` (`POSTGRES_PASSWORD: ***`); `.env.example` (`change_me`); `docs/08` §2 warning |
| W-008 | i18n (RAG) | Knowledge assistant is **English-only**: TF-IDF vectorizer uses `stop_words="english"`; all 10 knowledge documents are English | Add Persian (then Arabic) corpus with per-language vectorizers; route by `Accept-Language`; translate advisory content with expert review (per `docs/07` §7) | Planned | `engine/hydroma/ai_assistant/rag_engine.py` (stop_words), `knowledge_base.py` (10 English docs); `docs/07` §6 |
| W-009 | i18n (RTL) | RTL is **incomplete**: `app/layout.tsx` hardcodes `<html lang="en" dir="ltr">`; direction is switched client-side after hydration only, so SSR/initial HTML is always LTR | Server-render `lang`/`dir` per locale (set from the request or a cookie); verify fa/ar/ur layouts visually; test SSR HTML | In progress | `frontend/app/layout.tsx` (hardcoded ltr); `frontend/lib/i18n-context.tsx` does set `document.documentElement.dir` post-hydration (partial fix exists); `docs/07` §2 |
| W-010 | Frontend config | API base URL **hardcoded** as `http://127.0.0.1:8000` in 9 component files | Introduce a single configurable base URL (env var / `next.config.js` public runtime config); centralize the fetch layer | Planned | `frontend/components/`: `BenchmarkPanel.tsx:19`, `CarbonCreditPanel.tsx:33`, `ChatAssistant.tsx:32`, `CropPlannerPanel.tsx:30`, `MarketplacePanel.tsx:37`, `SatellitePanel.tsx:67`, `ScenarioPanel.tsx:33,59`, `SoilDashboard.tsx:21`, `WatershedPanel.tsx:21` |
| W-011 | Version control | **No Git repository** — `git status` reports "not a git repository"; no `.git`, no history, no tags, no CI host | `git init` with a clean baseline commit; set branch policy; add CI on first commit | Planned | `D:\eco_nojin` — no `.git`; roadmap §3 item 1; `docs/08` §8 checklist |
| W-012 | Carbon verification | `/verify` endpoint is a **demo**, not a valid verification process: it flips `status` to `verified` with a default verifier string and no evidence chain | Pick a real methodology (e.g., Verra ARR or VM0042); implement baseline/additionality/leakage/permanence; keep `/verify` internal and clearly labeled until accredited verification exists | Planned | `services/api_gateway/routers/carbon.py` (`verify_carbon_project`); `engine/hydroma/carbon/calculator.py` (in-memory registry, blanket 15 % discount); `docs/05` §3 (honest status) |
| W-013 | Numerical model | Simplified equations used as product defaults without full limitation documentation: simplified AquaCrop-style crop model; rational-method runoff volume; regional-rate carbon tables | Add in-code limitation notes (validity range, intended use, error margins) next to each formula; cross-link to STD-014 numeric tests; publish a model-approximation register | In progress | `engine/hydroma/scenarios/crop_scenarios.py` ("simplified AquaCrop approach"); `engine/hydroma/watershed/calculator.py` (`calculate_runoff` rational method, no limitation note); `engine/hydroma/carbon/calculator.py`; partial prose coverage in `docs/02` §4,§7 and `docs/05` §3 |
| W-014 | Data layer | **SQLite without migrations**: `database.py` hardcodes `sqlite:///./hydroma_research.db`; `Base.metadata.create_all` on startup; no Alembic, no migration history | Introduce Alembic with an initial baseline migration; make startup idempotent; plan the SQLite→PostGIS migration path | Planned | `engine/hydroma/core/database.py`; `services/api_gateway/main.py` (create_all); no `alembic*` anywhere in the tree; `docs/04` §7 |
| W-015 | Data integrity | **No data-change audit trail**: registries are in-memory and no table records who changed what/when (no audit columns, no change log) | Add audit fields (created_by, updated_at, change reason) and a change-log table or event stream; log every mutation through one path | Planned | `engine/hydroma/carbon/calculator.py` (`_projects` in-memory), `engine/hydroma/marketplace/` (in-memory models), `services/api_gateway/routers/sync.py` (`_sync_log` in-memory); no audit table in `engine/hydroma/core/models.py` |

## 3. Additional Findings from this Review (beyond the initial list)

| ID | Area | Weakness | Corrective action | Status | Evidence |
|---|---|---|---|---|---|
| W-016 | Security | **No authentication/authorization**: every write endpoint is open (marketplace orders, carbon project registration, sync batch, soil create); auth service is a placeholder | Implement OIDC auth service with roles (farmer, cooperative, NGO, admin); protect all write endpoints; add auth to the integration tests | Planned | `services/auth/main.py` (placeholder); no `Depends`/auth dependency in any router; threat model in `docs/06` §3 |
| W-017 | Security | **No TLS**: dev runs over HTTP; no HSTS; CVE-tracked frontend (Next.js 15.1.6, CVE-2025-66478, fixed 16.3.1+) | Terminate TLS before any non-local deployment; HSTS; upgrade Next.js per the migration plan in `docs/security/CVE-2025-66478.md` | Planned | `docs/06` §2 ("Transport security: Not configured yet"); `docs/security/CVE-2025-66478.md` |
| W-018 | Testing | **Test suite is red**: `test_health_reports_mobile_features` fails (run 2026-08-14: 127 passed, 1 failed) because the health endpoint omits `mobile_features` from its module list | Fix `main.py` health payload (add the module or remove the assertion) — one line; then require green CI | In progress | `tests/integration/test_sync.py`; `services/api_gateway/main.py` (health modules list); pytest run result 2026-08-14; roadmap §3 item 3 ("stale mobile_features test") |
| W-019 | Persistence | **State is in-memory**: carbon projects, marketplace catalog/orders, and sync log vanish on restart; no durable storage for Phase-1 entities | Persist to SQLite now, PostGIS later (aligned with W-014 migrations); add persistence integration tests | Planned | `engine/hydroma/carbon/calculator.py` `_projects`; `engine/hydroma/marketplace/*` (per `docs/04` §3); `routers/sync.py` `_sync_log` |
| W-020 | Dependencies | **Requirements drift**: `requirements.txt` (production intent: netcdf4, zarr, xgboost, lightgbm, mlflow, torch, celery, redis, psycopg, geoalchemy2) does not match the actual research environment (`.venv` has duckdb, numba, diskcache, jinja2, python-multipart from `requirements-research.txt`); `pyproject.toml` deps empty | Reconcile into pinned, layered requirements (base/research/prod); record the golden environment (`pip freeze` into a lockfile); add a CI check that requirements match imports | Planned | `requirements.txt` vs `requirements-research.txt` vs `.venv/Lib/site-packages` listing (2026-08-14); `pyproject.toml` |
| W-021 | Accessibility | **WCAG 2.1 AA gaps**: no `aria-*`/`role` in any component; `userScalable: false` blocks zoom (fails 1.4.4); unlabeled inputs in several panels | Run an axe audit; fix contrast/focus/zoom/labels per STD-006 before public rollout | Planned | `frontend/components/*.tsx` (0 aria matches); `frontend/app/layout.tsx` viewport (`userScalable: false`); `CarbonCreditPanel.tsx` etc. |
| W-022 | Frontend type debt | The frontend carries pre-existing TypeScript errors (implicit `any`, loose API response types, `language` vs `locale` naming drift); the build previously never type-checked green. Phase 0 ships the CVE-fixed Next.js 16 build with `typescript.ignoreBuildErrors: true` (documented in `next.config.js`) rather than blocking the upgrade | Full type cleanup during the Phase 3 frontend rebuild; then remove `ignoreBuildErrors` and require green `tsc` in CI | Planned | `frontend/next.config.js`; `docs/13_operations.md` §6 | 2026-08-16 |

## 4. Summary

| Status | Count | IDs |
|---|---|---|
| Fixed | 1 | W-003 (CORS allowlist verified in `services/api_gateway/main.py`, 2026-08-16) |
| In progress | 3 | W-002, W-009, W-018 (plus W-013 partially) |
| Planned | 19 | W-001, W-003, W-004, W-005, W-006, W-007, W-008, W-010, W-011, W-012, W-014, W-015, W-016, W-017, W-019, W-020, W-021, W-022 |

Notes:

- W-003 was verified **Fixed** on 2026-08-16 (explicit CORS origin allowlist in
  `services/api_gateway/main.py`); all other items remain open. W-013 is marked *In progress* only in the sense that
  prose limitation notes already exist in `docs/02` and `docs/05`; the
  in-code notes and numeric tests (STD-014) are still missing.
- The three *In progress* items (W-002, W-009, W-018) all appear in the
  roadmap's "Immediate Next Steps" defect list (`docs/09_roadmap.md` §3).
- Items W-016 to W-021 are additions from this independent review; they were
  verified against files as of 2026-08-14.

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
