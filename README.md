# HyDroMA — Eco Nojin

Eco Nojin (`اکو نوژین`) is a scientific water–energy–agriculture modelling engine paired
with **HyDroMA**, a business/services platform built on top of it. The engine side
(`engine/`) is an offline, FOSS-only scientific core: hydrology, land-surface,
soil, climate, agronomy, carbon/MRV and economic models registered behind a single
`EngineGateway`, every model carrying an honest status (`stub` → `implemented` →
`tested` → `validated`) and an external anchor where one exists. The platform side
(`services/`) is a FastAPI application exposing the market, village hub, tourism,
commerce, inventory, finance (double-entry ledger), land registry and auth
domains. The two halves are separated by a hard architecture boundary that is
enforced in CI by `tools/detect_imports.py` — no service may import engine
internals directly; it must reach scientific computation through the gateway
facade. The project's governing honesty contract is simple and enforced: *the
existence of a file is not evidence of a completed capability.*

## Repository layout

```
D:\HyDroMA
├─ engine/            # scientific core — isolated by the import guard
│  ├─ hydroma/        # domain models (hydrology, land, soil, climate, mrv, …)
│  ├─ cpp_bridge/     # C++/Python boundary (parity + benchmark suites)
│  ├─ models/         # registry, maturity, model cards (CANON-xxx)
│  ├─ gateway/        # EngineGateway — the sanctioned entry point for services
│  ├─ ports/          # abstract ports (PersistencePort, Evidence adapter)
│  ├─ evidence/  knowledge/  tasmimyar/  honesty/   decision-adjacent modules
│  └─ tests/  strict_tests/                                (scientific test stack)
├─ services/          # FastAPI platform — the HTTP + domain layer
│  ├─ api_gateway/    # app assembly, middleware, 100+ routers, tests/
│  ├─ finance/        # chart of accounts, double-entry LedgerService, wallet
│  ├─ inventory/      # moving-average valuation, COGS, lots + FEFO
│  ├─ commerce/       # order items + atomic stock, settlement posting
│  ├─ marketplace/    # order management, payments→orders, village hub
│  ├─ land/           # land-ownership registry
│  └─ tourism/  wallet/  auth/  mrv/  validation/  …  (~70 public subpackages)
├─ database/          # SQLAlchemy base/config/hub/settings + all models
├─ alembic/           # migration chain — 15 revisions in versions/
│  └─ versions/       # …20261013_120000_p8_departure_cancel_reason.py (head)
├─ adapters/          # persistence adapters (SQLite) implementing engine ports
├─ architecture/      # rules.yaml, the YAML dependency rules, generated graph
├─ runtime/           # pure-Python process supervisor (DP-2: no Docker)
├─ scenario/  decision/  indicators/                    shared engine contracts
├─ tools/             # detect_imports.py, cleanup.py, phantom_path_check.py,
│                     # check_citations.py, check_service_boundaries.py, …
├─ tests/reference_data/   # FAO-56 Ex.18/20, McKee SPI, Theis, USDA texture
│                          # each with a *.meta.json provenance contract
├─ docs/
│  ├─ specs/          # ECO-01..04.1, master directives, testing directive
│  ├─ audits/         # ECO-00 engine & services forensic audit
│  └─ adr/            # ADR-014 import-guard policy
├─ reports/           # the program record-of-resolution (owned by the
│                     # implementation agents; the specs above do NOT live here)
├─ data/              # reference (tracked) vs runtime (gitignored, regenerated)
├─ .githooks/  .github/workflows/
├─ pyproject.toml  requirements.txt  requirements-dev.txt  alembic.ini
└─ README.md  AGENTS.md
```

`data/` splits two ways. **Reference data is tracked** (`data/model_registry.json`,
`data/links/external_links.json`, `tests/reference_data/**`) and carries provenance
sidecars. **Runtime data is gitignored and regenerated** (`data/cache/`,
`data/copernicus_cache/`, `data/master/`, `data/motors/`, `data/maps/`, `data/rag/`,
`data/reports/`, `data/security/`, `*.duckdb`).

## Quickstart

### Which interpreter

Use the **repo-root `.venv`** only to reproduce what CI and the git hooks do.
Use **`D:\eco_nojin\.venv`** for everything else — it is the long-lived working
environment these docs and the dev test runs are measured against. Note that
plain `python` is not on `PATH`; always call the interpreter by its full path
with the `&` call operator.

```powershell
# The one you want for development, tests, lint, typecheck:
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest services/ -q -n 6

# Only to reproduce CI / .githooks exactly:
& ".venv\Scripts\python.exe" -m pytest engine/ -q
```

### Environment variables

Set these **in the same shell** that runs the command — they do not persist
between shells.

```powershell
$env:PYTHONPATH  = "D:\HyDroMA;D:\eco_nojin"   # repo root + the venv's site root
$env:SECRET_KEY  = "test-secret-key"           # required by GBIF/data-pipeline + money tests
$env:BANK_WEBHOOK_SECRET = "<shared secret>"   # HMAC key for the bank-transfer webhook
```

`BANK_WEBHOOK_SECRET` is **fail-closed**: if it is unset or blank, the bank
transfer webhook route returns `503` (`services/finance/routers/finance.py`).
Optional operational knobs live in `database/settings.py` — e.g.
`HYDROMA_AUTH_RATE_LIMIT_ENABLED`,
`HYDROMA_AUTH_RATE_LIMIT_MAX_REQUESTS`,
`HYDROMA_AUTH_RATE_LIMIT_WINDOW_SECONDS`.

### Install

`pip install -e .` does **not** work on this tree (`pyproject.toml`'s build
backend is not a resolved setuptools backend, and the project now declares a
README). Install from the requirements files, which is what CI does:

```powershell
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pip install -r requirements.txt -r requirements-dev.txt
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pip install -e ".[dev,cpp,ref,units,fast]"
```

Optional extras and what they are for: `cpp` (pybind11/ninja/cmake for C++
parity), `fast` (Numba acceleration of the engine's land hot loops — every
kernel degrades to a bit-identical pure-Python path when Numba is absent),
`ref` (dev/test-only reference implementations — `pyet`, `climate_indices`,
`rosetta-soil` — never imported by `engine/` at runtime),
`units` (`pint`), `legacy-bridge` (duckdb/supabase, only for legacy migration).

### Core commands

```powershell
# Tests. engine/ and services/ are large — run ONE suite per shell and use -n 6
# (xdist). Two 6-worker suites on one box over-subscribe and kill workers.
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest services/ -q -n 6 -p no:cacheprovider
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest engine/    -q -n 6 -p no:cacheprovider
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest engine/strict_tests -q -p no:cacheprovider

# Lint / types
& "D:\eco_nojin\.venv\Scripts\python.exe" -m ruff check .
& "D:\eco_nojin\.venv\Scripts\python.exe" -m mypy engine --ignore-missing-imports

# Architecture import guard — must report 0 violations
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/detect_imports.py --root .

# Root cleanup (refuses tracked files; idempotent)
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/cleanup.py

# Database migrations
& "D:\eco_nojin\.venv\Scripts\python.exe" -m alembic heads
& "D:\eco_nojin\.venv\Scripts\python.exe" -m alembic upgrade head         # apply
& "D:\eco_nojin\.venv\Scripts\python.exe" -m alembic upgrade head --sql    # render offline

# App boot
& "D:\eco_nojin\.venv\Scripts\python.exe" -c "from services.api_gateway.main import app; app.openapi()"
```

## Quality gates

The table below is the **2026-10-11 baseline snapshot**. The live tree keeps
moving (agents land revisions, routers and tests by the hour), so the numbers
quoted in it are a record, not a live reading.

| Gate | Expected | Measured 2026-10-11 |
|---|---|---|
| `pytest engine/` | 0 failed | **7 failed, 2699 passed, 31 skipped, 42 xfailed** — see the honest breakdown below |
| `pytest engine/strict_tests` | 0 failed | **1323 passed, 27 skipped, 40 xfailed — PASS** |
| `pytest services/` | 0 failed | **1 failed, 1443 passed, 9 skipped** — collection is additionally blocked by one in-flight untracked file; excluding it, 1453 tests collect |
| `ruff check .` | baseline, no growth | **815 findings** (documented baseline on a committed tree: **769**) |
| `mypy engine --ignore-missing-imports` | 0 | **0 errors in 405 source files** |
| `tools/detect_imports.py --root .` | **0 violations** | **16 violations — currently FAILING** (see below) |
| `tools/check_service_boundaries.py` | 0 violations | **2 violations** (see below) |
| `app.openapi()` | boots | **113 routes / 630 paths / 710 operations**, exit 0 |
| `alembic heads` / `upgrade head --sql` | single head, renders clean | head **`20261011_090000_remaining_legacy_tables`**, `--sql` exit **0** |

### Re-measured on the live tree, 2026-10-13/14

| Gate | Result |
|---|---|
| `mypy engine --ignore-missing-imports` | **0 errors in 416 source files**, exit 0 |
| `tools/detect_imports.py --root .` | **0 violations — PASS** (1193 files scanned; the facade adapters migrated, incl. the vectorised `services/_gateway_facade_adapters/runoff.py` entry) |
| `app.openapi()` | **117 routes / 658 paths / 744 operations**, exit 0 — the surface grew by the village-governance, jobs, compliance-registry and tourism-safety mounts plus the tasmimyar advice route |
| `alembic upgrade head --sql` | renders clean from base to head **`20261013_120000_p8_departure_cancel_reason`** (single head, linear chain, no duplicated constraints in the render) |
| `alembic upgrade head` (online, scratch DB) | idempotent across three consecutive runs plus a `downgrade -1` / `upgrade head` cycle; exactly one FK per repaired edge |
| targeted service suites | tourism 49 · village 14 · jobs 30 · compliance 44 · finance 157 · api_gateway 321 · scientific_motors+marketplace 544 — all green |

Everything above is measured live, so treat the exact counts as a snapshot.
The root-cause split of the engine failures matters more than the total:

- **1 failure is a direct consequence of this repository's documentation
  restructure.** `engine/tests/test_architecture_rules.py:34` still reads
  `PROJECT_ROOT / "ECO-NOJIN MASTER EXECUTION SPECIFICATION.md"`; the
  specification now lives at
  `docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`, so
  `test_spec_architecture_enforcement_not_connected_to_ci_yet` raises
  `FileNotFoundError`. The fix is a one-line path update inside `engine/**`
  (off-limits to this pass) — see *Risks & follow-ups*.
- **6 failures are pre-existing on the live tree** and unrelated to the move:
  four architecture-policy assertions (stale
  `architecture/dependency-graph.md` drift, the 140-edge service ratchet
  exceeding the 139 policy maximum, and the unsanctioned `database.config`
  persistence-bridge edge) plus two `biofertilizer` calibration-session tests
  in the area of untracked in-flight work
  (`engine/hydroma/biofertilizer/persistence_bridge.py`).
- **`services/scientific_motors/tests/test_inline_science_routing.py` is
  untracked in-flight work** and fails to *collect* under the installed
  `schemathesis` plugin (`function uses no argument 'texture'`), which
  interrupts the whole `services/` run. That is the blocker for the
  `~1381` services baseline quoted in the docs; excluding the file, 1453
  tests collect, and the run finishes **1 failed / 1443 passed / 9 skipped**.
  Nothing in the documentation restructure touches Python, so both the
  collection error and that failure come from the concurrent edits in
  `services/**` (`services/_gateway_facade*.py`, `ledger/`, `marketplace/`,
  `scientific_motors/`, `api_gateway/routers/`).

Two guard gates were also red at that snapshot, from the same in-flight
package (both are green on the re-measured tree above):

- **`tools/detect_imports.py` → 16 `SERVICES_NO_ENGINE_INTERNALS` violations**,
  all inside the then-untracked `services/_gateway_facade_adapters/`
  (`carbon.py`, `climate.py`, `economics.py`, `groundwater.py`, `soil.py`
  importing `engine.hydroma.*` directly instead of through the gateway
  facade). The committed baseline is 0 violations.
- **`tools/check_service_boundaries.py` → 2 violations** (one undeclared
  `services._contracts → services._gateway_facade` edge plus the 140-vs-139
  ratchet).

Re-measure on a quiescent/committed tree before quoting a precise number: the
authoritative quality-gate record is [`AGENTS.md`](AGENTS.md) and
[`reports/`](reports/).

## Documentation

- [`AGENTS.md`](AGENTS.md) — the agent runbook: environment, commands, quality
  gates, known debt and remaining follow-ups.
- [`docs/specs/`](docs/specs/) — the specification set (these are the source of
  truth for requirements):
  - [`ECO-NOJIN_MASTER_v3.1_UNIFIED.md`](docs/specs/ECO-NOJIN_MASTER_v3.1_UNIFIED.md)
    — the live constitution (v3.0 HTML is superseded)
  - [`ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`](docs/specs/ECO-NOJIN%20MASTER%20EXECUTION%20SPECIFICATION.md)
    — the master execution spec (ECO-MASTER-v2.0-ZED-UNIFIED)
  - `ECO-01.md`, `ECO-02.md`, `ECO-03.md`, `ECO-03.1.md`, `ECO-04.md`,
    `ECO-04.1.md` — the phase directives
  - [`HYDROMA-MASTER.md`](docs/specs/HYDROMA-MASTER.md) and
    [`HYDROMA-MASTER-TESTING.md`](docs/specs/HYDROMA-MASTER-TESTING.md) —
    the master and the testing/validation directives
- [`docs/audits/ECO-00-ENGINE-SERVICES-FORENSIC-AUDIT-REPAIR.md`](docs/audits/ECO-00-ENGINE-SERVICES-FORENSIC-AUDIT-REPAIR.md)
  — the engine & services forensic audit, with an implementation-status
  reconciliation of its G-Z gap register.
- [`docs/adr/014-import-guard-policy.md`](docs/adr/014-import-guard-policy.md)
  — ADR-014: the externalised import-guard exception policy
  (`tools/import_guard_policy.json`).
- [`docs/project/`](docs/project/) — the executable program: `BASELINE.md`,
  `KNOWN_ISSUES.md`, `OPEN_DECISIONS.md`, `CAPABILITY_MATRIX.md`,
  `DEPENDENCY_MAP.md`, `PHASE_PLAN.md` — read before any phase work.
- [`reports/`](reports/) — the program record-of-resolution (handoffs, gap
  registers, lint/quality measurements, release plans).

## Architecture invariants (must not regress)
- **Import guard = 0 violations.** `services/**` reaches the engine only via
  `services/_gateway_facade.py` (plus the sanctioned facade adapters under
  `services/_gateway_facade_adapters/` — each edge registered in
  `tools/import_guard_policy.json`); no service imports engine internals
  directly. `database.config` / `database.base` are the sanctioned
  `ENGINE_NO_DATABASE` exceptions (see `tools/detect_imports.py::get_rules()`).
- **Money is `Decimal`** throughout (never float); settle/valuation batches stay
  balanced and are **posted at their call sites**.
- **Alembic guarded/idempotent** pattern: every op re-run-safe and coexisting
  with `create_all`; incompatible changes reviewed by hand and proved with
  `--sql` (both online replay and offline render are verified).
- **`tools/cleanup.py` must never delete a tracked file** — it refuses them by
  design.
- **Route-count**: a suite pins the registered route surface, so growing
  `app.routes` beyond 117 is a deliberate change, never an accident.

## Risks & follow-ups (as of 2026-10-11)

1. **Fix the one hard-coded spec path.** `engine/tests/test_architecture_rules.py:34`
   reads `PROJECT_ROOT / "ECO-NOJIN MASTER EXECUTION SPECIFICATION.md"`; that
   file now lives at
   `docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`, so
   `test_spec_architecture_enforcement_not_connected_to_ci_yet` raises
   `FileNotFoundError`. A one-line `SPEC_PATH` update (or a `docs/specs/`-aware
   lookup) inside `engine/**` restores it.
2. **Stale prose path references outside this pass's write scope.** These files
   still name the documents without their new `docs/specs/` prefix and were left
   untouched because they are outside `docs/**`, `README.md` and the moved
   specs: `adapters/persistence/__init__.py:5`,
   `adapters/persistence/sqlite_persistence.py:5`,
   `architecture/eco-nojin-architecture.yaml:3`, `decision/weights.yaml:4,21`,
   `engine/ports/persistence.py:7`, `engine/ports/persistence_port.py:4`,
   `engine/tests/test_novel_index_gate.py:3`,
   `engine/tests/test_persistence_port_contract.py:4`,
   `tests/reference_data/fao56_examples.md:25`,
   `tools/novel_index_gate.py:4,490`, `LICENSES/README.md:9`,
   `LICENSES/Dependency-LICENSES.md:4`, plus the historical record in
   `AGENTS.md` and `reports/**`.
3. **16 import-guard violations** in the untracked
   `services/_gateway_facade_adapters/` package (AR-12 / G-S10 / Track C2) —
   migrate them through `EngineGateway`, then `git add` the package.
4. **`architecture/dependency-graph.md` has drifted** — regenerate it with
   `python tools/dependency_graph.py --out architecture/dependency-graph.md`
   and ratchet the service-boundary policy from 139 to 140 (or declare the
   `services._contracts → services._gateway_facade` edge).
5. **The import-guard policy does not sanction `database.config`** for the
   persistence bridge — either add it to
   `tools/import_guard_policy.json` or drop the `engine.data_connector` /
   legacy DuckDB path (G-Z3).
6. **`requirements.txt:37-38` still installs `duckdb` and `supabase` outside any
   extra**, which is the residual half of G-Z1 — move them into the
   `legacy-bridge` extra so the core install stays ZED-clean.
7. **`data/` still lacks the raw/indices/model_runs/evidence layout** (G-Z4) and
   `engine/hydroma/quantity.py` is still a 10-line stub behind `pint` (G-Z5).

## Licence

MIT — see [`LICENSES/`](LICENSES/).
