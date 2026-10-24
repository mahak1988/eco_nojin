# BASELINE — ECO Nojin / HyDroMA (Phase-0 record)

* **Status:** Active · **Recorded:** 2026-10-11 (live tree, UTC) · **Owner:** A00 (repository analysis)
* **Strategy source:** `eco.md` (root, untracked — moved to `docs/specs/ECO-PROGRAM-FA.md` in P1, task 5)
* **Runbook:** `AGENTS.md` (venv paths, env vars, suite discipline) · **Report cross-check:** `reports/PROJECT-REPORT-2026-10-11.md`

> **Live-tree caveat (inherited from AGENTS.md):** other agents are moving root specs into
> `docs/specs/` and editing `services/**` + `engine/**`. Re-measure any number below on a
> quiescent/committed tree before acting on it. A number marked **(live)** was executed
> during this Phase-0 session; **(recorded)** comes from the same-day report and was not
> re-executed here.

## 1. Quality gates

| Gate | Command (from `AGENTS.md`) | Result | Kind |
|---|---|---|---|
| services tests | `pytest services/ -q -n 6 -p no:cacheprovider` | 1381 passed / 9 skipped / **0 failed** | (recorded) |
| engine tests | `pytest engine/ -q -n 6 -p no:cacheprovider` | 2698 passed / 30 skipped / 42 xfailed / **0 failed** | (recorded) |
| engine strict tests | `pytest engine/strict_tests -q -p no:cacheprovider` | **1323 passed / 27 skipped / 40 xfailed / 0 failed** (1390 collected; 117.85 s) — measured during P1 (2026-10-11); resolves KN-10: the earlier "1314 passed" figure in AGENTS.md was the stale one | **(live, P1)** |
| inventory suite (sanity) | `pytest services/inventory/tests -n 4` | 164 passed / 0 failed | (recorded) |
| ruff | `ruff check .` | **762 errors** (committed baseline 769 → below baseline; live tree had swung 809–852 during the session) | **(live)** |
| mypy engine | `mypy engine --ignore-missing-imports` | **0 errors in 406 source files** (this session's run hit the 300 s shell cap; cite the two same-day measurements) | (recorded) |
| import guard | `tools/detect_imports.py --root .` | **0 violations — PASS** | **(live)** |
| service boundaries | `tools/check_service_boundaries.py` | **140 measured edges / 140 policy entries / 0 violations / 0 stale — PASS** | **(live)** |
| app boot | `from services.api_gateway.main import app; app.openapi()` | **113 routes / 630 OpenAPI paths / 710 operations**, exit 0 | **(live)** |
| alembic | `alembic heads` / `alembic upgrade head --sql` | single head `20261011_090000_remaining_legacy_tables`; 5 revision files; renders clean | (recorded) |

**Snapshot rule:** every number above is a snapshot, not a live value. Each phase gate
**re-measures and pastes its own fresh output**; a mismatch against this table is recorded as
debt (see KN-10/KN-14), never silently edited. Canonical sources: `AGENTS.md` (committed
baseline) and `reports/PROJECT-REPORT-2026-10-11.md` (same-day outcome); this file adds no
independent authority.

**Collected sizes (tree keeps growing):** `services/` + `engine/` = 4236 tests;
`engine/strict_tests` = 1390 collected.

**Reproduce (one suite per shell — two 6-worker suites on one box kill xdist):**

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
$env:SECRET_KEY = "test-secret-key"
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest engine/ -q -n 6 -p no:cacheprovider
& "D:\eco_nojin\.venv\Scripts\python.exe" -m ruff check .
```

## 2. Platform shape (measured)

| Item | Value | How measured |
|---|---|---|
| ORM tables / columns | **150 / 1847** | `database.models.Base.metadata` |
| Tables outside the ORM registry | 17 (`auth_users`, `app_notifications`, `nojin_*`, …) | AGENTS.md debt list |
| API surface | 113 registered routes · 630 documented paths · 710 ops | `app.openapi()` |
| Alembic head | `20261011_090000_remaining_legacy_tables` (9 new + 127 legacy tables, guarded/idempotent) | `alembic/versions` |
| Engine model registry | **70 models — 13 `validated` / 57 `unvalidated`** | `engine/models/registry.py` (`list_models()`) |
| Service domains | ~70 packages in `services/` (excluding `__pycache__`, `_contracts`, `_gateway_facade_adapters`); `docs/ARCHITECTURE-REFERENCE-2026-10-11.md` quotes ~79 | live directory listing + reference doc |
| Engine sub-domains | 47 scientific areas in `engine/hydroma` | docs/ARCHITECTURE-REFERENCE |
| Architecture rules | 8 (`architecture/rules.yaml`, `eco-nojin-architecture.yaml`, `dependency-graph.md`) | directory listing |
| Frontend code | **none** — no `package.json`, `vite.config.*`, or any `*.tsx` anywhere; only `docs/FRONTEND-DESIGN-2026-10-11.md` (status: proposed) | filesystem scan |

## 3. Money & storage (multi-ledger reality — see KN-08)

Five parallel money stores exist in `database/models.py`:

1. `fin_accounts`, `fin_journal_batches`, `fin_journal_entries`, `fin_idempotency_keys` (finance)
2. `eco_wallets`, `daily_earnings` (wallet)
3. `com_payment_intents`, `com_orders`, `com_order_items`, `com_settlements` (commerce)
4. `eco_transactions`, `ledger_entries`, `escrow_records` (ecosystem/ledger)
5. `eco_balance_accounts`, `eco_balance_entries` + **`ecocoin_balances` via raw SQL in `services/blockchain/service.py`** (not in the ORM registry, not in any Alembic migration)

## 4. Dependency posture

| Dependency | State | Note |
|---|---|---|
| `nats` | **code present, dependency NOT declared** | `services/api_gateway/eventbus/nats_client.py` imports `nats` in a try/except (`NATS_AVAILABLE`); not in `requirements*.txt`. Eventbus is meant to be an optional extra (D-06). |
| `duckdb`, `supabase` | commented out of `requirements.txt`, marked OPTIONAL / ZED-reclassified | kept for legacy connectors; do not delete without proof (eco.md Phase-1 rule) |
| `torch`, `sentence-transformers` | installed, used by RAG/knowledge tests | heavy under xdist memory pressure — documented crash risk |

## 5. Environment facts that gate deployment

* **SQLite runtime is 3.49.1 — below the WAL-reset fix (3.51.3).** `database/hub.py` logs an ERROR
  on file engines and exposes `sqlite_wal_deployment_safe()` (`version >= (3,51,3)`).
  **A WAL deployment must upgrade SQLite first.** (P4/P15 gate)
* Bank webhook is fail-closed on `BANK_WEBHOOK_SECRET` (unset ⇒ 503).
* Auth rate limiter: `HYDROMA_AUTH_RATE_LIMIT_*` (default on).

## 6. Strategy-document status

`eco.md` (root, **untracked**, 1425 lines) is the strategy source. Its Section-2 baseline table is a
**mid-conversation snapshot**: the seven engine failures and one services failure it reports are
already **fixed** (0 failed in both suites today), ruff 815 → **762**, import-guard 16/0
contradiction → **0 violations**, service-boundary 2 → **0 violations**. The parts it flags that
are still open are real and are tracked in `KNOWN_ISSUES.md`.

## 7. Live-tree refresh (2026-10-15/16) — Phase-0 addendum

 **Interpreter used.** CI/root venv `D:\HyDroMA\.venv\Scripts\python.exe` (the agent venv
 `D:\eco_nojin\.venv` is **not** used for measurement here). Env in-shell:
 `$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"`; `$env:SECRET_KEY = "test-secret-key"`.
 **Harness caveat:** probes are launched from a *clean* temp dir (`C:\Users\hilo\AppData\Local\Temp\kiloclean`) — the shared scratch dir `C:\Users\hilo\AppData\Local\Temp\kilo` contains a stray `rasterio.py` (a parallel agent's geo-import survey) that shadows the `rasterio` package when a script is launched from there (it prepends itself as `sys.path[0]`); that was the source of the `rasterio.warp` `ModuleNotFoundError` seen earlier and is **not** a repo/boot defect.

### Fresh measurements (2026-10-16T09:09Z — clean run, CI venv)

| Item | Live value (2026-10-15/16) | How |
|---|---|---|
| `alembic heads` | single head `20261013_120000_p8_departure_cancel_reason` | `alembic heads` |
| alembic revisions on disk | **13** (filenames `2026*.py`) | `Get-ChildItem alembic/versions` |
| `git status` | 1 changed entry since HEAD `2cb974e` (`chore: pre-edit hook`); `frontend/` remains **untracked** | `git status --porcelain` |
| pytest collect | **4936 collected / 2 errors / 0 failed during collection** | `pytest services/ engine/ --collect-only -q` |
| collection errors | both `services/knowledge/tests/test_public_api_access.py` and `test_service_rag_provenance.py` → `ModuleNotFoundError: No module named 'tests.test_*'` | pytest collect summary |
| app routes (`len(app.routes)`) | **117** (was 113 on 2026-10-11) | `from services.api_gateway.main import app` |
| OpenAPI surface | **667 paths / 753 ops** (GET/POST/PUT/PATCH/DELETE) | `app.openapi()["paths"]` |
| app boot gate | **GREEN (reproducible):** `app.routes=117`, full middleware stack applied (CORS/rate-limit/CSRF/idempotency/WAF/Prometheus) | `TestClient(app)` + `python -c "from services.api_gateway.main import app"` |
| P0 endpoint probes (KN-43 — **RESOLVED this session**) | `/api/v1/rules`→**503**, `/api/v1/units`→**503**, `/dashboard/public/weather`→**200** with `data.status:"no_data"` and `data.avg_temperature_c:0.0` (the fabricated `22.5`/`status:"fallback"` is **removed**) | `TestClient(app).get(...)` (clean CI-venv run, launched from a clean temp dir); pinned by `services/api_gateway/tests/test_http_api_v1_reference_store.py` (3/3 green) |

### Effect on the §1 gates

- **app boot** (row 25): **green and reproducible** at 117 routes / 667 paths / 753 ops. KN-43 is **not** a boot-instability defect — the `rasterio.warp` crash was the harness-contamination in §(Harness caveat) above; a clean run boots deterministically. KN-43 is instead a **live HTTP P0** (the `hub.internal_duckdb` 500s + the dashboard fabrication), now reproducible this session.
- **services tests / engine tests** (rows 17–19): not re-run as full suites (xdist + heavy
  torch/sentence-transformers RAG tests are documented crash-prone under this box's memory
  pressure — KN-15). Collected count rose 4236 → 4936 (+700 from the 10-12/13 security +
  tourism/engineering waves). KN-44 (2 collection errors in `services/knowledge/`) blocks a
  green full-suite run until fixed. Reproduction: run each suite **alone in its own shell**
  (`-n 6 -p no:cacheprovider`); see KN-44.
- **ruff** (row 21): committed baseline 769 unchanged; the 2026-10-11 "(live)" entry (762)
  already noted the live-tree swing. No re-measurement run here (ruff is stable to run; skipped
  to avoid overwriting KN-38/KN-42 edit-revert hazards on concurrently-edited files).

**Action for the next agent:** no boot repair needed (boot is green). The P1/P3 owner should
take KN-43: implement **or honestly disable** the reference-table duckdb path
(`services/api_gateway/api/v1/router.py:149 _query_reference_table` → `/api/v1/rules` @197 and
`/api/v1/units` @219) and remove the dashboard fabrication at `services/api_gateway/routers/dashboard.py:295-303`
(`/dashboard/public/weather` must return `status:"unavailable"`, never a fabricated `22.5`);
the P13 owner should fix KN-44 collection errors; the integrator should reconcile the 113→117
route pin (KN-45) before W6.

### Verified evidence (this session — 2026-10-16T09:45Z)

- KN-43 **fixed + pinned**: `services/api_gateway/api/v1/router.py:146-182` moved
  `hub.internal_duckdb` into `_query_reference_table`'s `try` → `/api/v1/rules` &
  `/api/v1/units` now return the documented **503** (was 500 `AttributeError`);
  `services/api_gateway/routers/dashboard.py:298-306` replaced the fabricated
  `avg_temperature_c: 22.5` / `status: "fallback"` with zeroed metrics +
  `status: "no_data"` (matches the sibling fallbacks at :389/:439/:489/:536/:565).
  `pin test`: `services/api_gateway/tests/test_http_api_v1_reference_store.py` →
  **3 passed**; collection **4945 / 0 errors**.
- KN-44 **fixed**: added `services/knowledge/__init__.py` and `services/blockchain/__init__.py`
  (the only two `services/<domain>` packages missing one — confirms the
  "moved rather than resolved" observation). `pytest services/ engine/ --collect-only -q`
  → 4945 collected, 0 errors.
- KN-45: `len(app.routes)==117` (green-boot). No test hard-pins 113 (the
  `len(_routes())==53` pin in `test_village_hub_route_order.py:108` is the
  village-hub router, unrelated). 667 OpenAPI paths / 753 ops reproduced.

### Structural gates this session

| Gate | Result | Command |
|---|---|---|
| import guard | **0 violations — PASS** (1280 files) | `python tools/detect_imports.py --root .` |
| collection | **4945 collected / 0 errors** | `pytest services/ engine/ --collect-only -q` |
| inventory suite | **164 passed** | `pytest services/inventory/tests -q` |
| KN-43 pin tests | **3 passed** | `pytest services/api_gateway/tests/test_http_api_v1_reference_store.py -q` |
| `ruff check .` | **880** live (~+111 vs 769 baseline from concurrent in-flight files; the 5 touched files are 0) | `python -m ruff check .`
