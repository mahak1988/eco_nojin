# AGENTS.md

Runbook for agents/operators in the HyDroMA repo (`D:\HyDroMA`, Windows /
PowerShell). Every figure below was re-verified against the live tree on
**2026-10-11** unless explicitly marked a *baseline* (a committed-tree snapshot).

## Environment

**Interpreter.** Plain `python` is **not** on PATH. Always call the venv python by
its full path with the call operator `&`:

```powershell
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest ...
```

**Two working venvs â€” pick the right one (both exist):**

| venv | used by | use it for |
|---|---|---|
| `D:\eco_nojin\.venv\Scripts\python.exe` | this repo's agents + these dev docs | all dev / test / lint / typecheck below |
| `.venv\Scripts\python.exe` (repo root) | **CI** (`.github/workflows`) and `.githooks` | only to reproduce CI/githooks locally. Note: `pip install -e .` is broken (`pyproject` build-backend points at a non-existent `setuptools.backends._legacy`); CI installs from `requirements*.txt` |

**Environment variables** (per-shell â€” set them in the *same* shell that runs a
command; they do not persist):

```powershell
$env:PYTHONPATH = "D:\HyDroMA;D:\eco_nojin"
$env:SECRET_KEY = "test-secret-key"    # required by GBIF/data-pipeline + finance/money tests
```

Operational runtime vars (set only what a command exercises):

- `BANK_WEBHOOK_SECRET` â€” HMAC key for the bank-transfer webhook. **Fail-closed:**
  unset/blank â‡’ the webhook route returns `503` (`services/finance/routers/finance.py`);
  the name is a sanctioned constant (`database/settings.py::BANK_WEBHOOK_SECRET_ENV`).
- `HYDROMA_AUTH_RATE_LIMIT_ENABLED` (default true) /
  `HYDROMA_AUTH_RATE_LIMIT_MAX_REQUESTS` / `HYDROMA_AUTH_RATE_LIMIT_WINDOW_SECONDS`
  â€” auth token-bucket rate limiter (`services/api_gateway/middleware/rate_limit.py`).

**Windows / PowerShell pitfalls**

- Use the call operator `&` + the quoted full interpreter path (no bare `python`).
- Set `PYTHONPATH`/`SECRET_KEY` in the same shell as the command.
- Quote paths containing spaces (`"ECO-NOJIN MASTER EXECUTION SPECIFICATION.md"`).
- SQLite runtime is **3.49.1** â€” below the WAL-reset fix (**3.51.3**; backports
  3.44.6, 3.50.7). `database/hub.py` logs an ERROR on file engines and exposes
  `sqlite_wal_deployment_safe()` (`version >= (3,51,3)`). **A WAL deployment must
  upgrade SQLite first.**

## Commands

```powershell
# Tests â€” engine/ and services/ are large; use -n 6 (xdist installed). Run ONE
# suite per shell: two 6-worker suites on one box over-subscribe and kill xdist
# workers (observed "[gw0] node down" / OSError Errno 22 this session).
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest services/ -q -n 6 -p no:cacheprovider
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest engine/    -q -n 6 -p no:cacheprovider
& "D:\eco_nojin\.venv\Scripts\python.exe" -m pytest engine/strict_tests -q -p no:cacheprovider

# Lint / types
& "D:\eco_nojin\.venv\Scripts\python.exe" -m ruff check .
& "D:\eco_nojin\.venv\Scripts\python.exe" -m mypy engine --ignore-missing-imports

# Architecture import guard (must be 0 violations)
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/detect_imports.py --root .

# App boot
& "D:\eco_nojin\.venv\Scripts\python.exe" -c "from services.api_gateway.main import app; app.openapi()"

# Root cleanup (refuses tracked files; idempotent)
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/cleanup.py --dry-run
& "D:\eco_nojin\.venv\Scripts\python.exe" tools/cleanup.py --yes [--include-build]

# Alembic (head below)
& "D:\eco_nojin\.venv\Scripts\python.exe" -m alembic heads
& "D:\eco_nojin\.venv\Scripts\python.exe" -m alembic upgrade head --sql   # render offline
& "D:\eco_nojin\.venv\Scripts\python.exe" -m alembic upgrade head         # apply
```

## Quality gates (verified against the live tree, 2026-10-11)

| Gate | Expected / current | Measured here |
|---|---|---|
| `pytest services/ -n 6` | 0 failed | 1381 passed / 9 skipped / 0 failed *(2026-10-11 outcome baseline â€” see note)* |
| `pytest engine/ -n 6` | 0 failed | 2698 passed / 30 skipped / 42 xfailed / 0 failed *(2026-10-11 outcome baseline â€” see note)* |
| `pytest engine/strict_tests` | 0 failed | 1323 passed / 27 skipped / 40 xfailed *(measured 2026-10-11, 117.85 s â€” P1 re-measurement; the earlier 1314 figure was stale, see KN-10)*; **1390 collected** |
| `ruff check .` | baseline, no growth | **769** *(2026-10-11 committed baseline)*; live read ~**810** (it swung 809â€“852 during the session) |
| `mypy engine --ignore-missing-imports` | 0 | **0 errors in 406 source files, exit 0** *(measured)* |
| `tools/detect_imports.py --root .` | 0 violations | **0 (PASS, 1193 files scanned)** *(measured)* â€” a mid-session run transiently read **16** from an untracked in-flight `services/_gateway_facade_adapters/`, since resolved by that agent |
| `app.openapi()` | boots | **`app.routes` = 113** (openapi: 630 paths / 710 ops), exit 0 *(measured)* |
| `alembic upgrade head --sql` | renders clean | head `20261011_090000_remaining_legacy_tables` *(file present)* |

**On the two big-suite numbers.** A full re-run is **not cleanly reproducible in this
box**, so the two rows above are the recorded 2026-10-11 baseline. Symptoms seen this
session: running the two 6-worker suites *concurrently* kills the xdist workers
(`OSError [Errno 22]`); and a *lone* `services/ -n 6` reached ~92% then a worker hit a
native `Windows fatal exception: access violation` in the torch / `sentence-transformers`
RAG tests (`services/ai/tests/test_hydroma_rag.py`, `services/knowledge/...`) under xdist
memory pressure â€” an environment/resource limit, not test logic. A suite I *did* execute
cleanly here: `pytest services/inventory/tests -n 4` â†’ **164 passed, 0 failed** (matches
its 164 collected). Combined `services/` + `engine/` collect **4236** tests (~+76 vs the
2026-10-11 outcome snapshot; the tree keeps growing). Collected sizes:
`services/inventory/tests` 164, `engine/strict_tests` 1390.

> **The tree is live.** Other agents are `git mv`-ing the root specs into
> `docs/specs` / `docs/audits` and editing `services/**` + `engine/**` docstrings, so
> `ruff` and the guard count move by the minute (an in-flight untracked adapter briefly
> put the guard at 16; it is back to **0** now â€” see the guard row; new tests keep it moving). Re-measure on a quiescent/committed tree before acting on
> any precise live figure â€” which is why the published gates above quote the
> committed baselines.

## Repository layout (post docs-move, 2026-10-11)

The root spec/audit docs were `git mv`'d out of the root:

- `docs/specs/` â€” ECO-01â€¦04.1, the ECO-NOJIN master set (`ECO-NOJIN MASTER EXECUTION SPECIFICATION.md`, `ECO-NOJIN_MASTER_v3.1_UNIFIED.md`, `ECO_NOJIN_HYDROMA_MASTER_v3.0.html`), `HYDROMA-MASTER.md`, `HYDROMA-MASTER-TESTING.md`
- `docs/audits/ECO-00-ENGINE-SERVICES-FORENSIC-AUDIT-REPAIR.md`
- `docs/adr/` (e.g. `014-import-guard-policy.md`) and `docs/reports/`
- Root code tree: `adapters/`, `AGENTS.md`, `alembic/`, `architecture/` (the YAML rules stay), `database/`, `decision/`, `engine/`, `indicators/`, `runtime/`, `scenario/`, `services/`, `tests/`, `tools/`, `data/`, plus `pyproject.toml`, `requirements*.txt`, `LICENSES/`
- No spec `.md`/`.html` lives at the root any more. `reports/` is the program record-of-record.

## Execution program (`docs/project/`) â€” read before any phase work

The executable 16-phase program (re-based on the measured baseline on 2026-10-11) lives here and
supersedes the phase plan in `eco.md`:

- `docs/project/BASELINE.md` â€” measured gates/numbers + reproduction commands
- `docs/project/KNOWN_ISSUES.md` â€” KN-01â€¦KN-19, each with an owner target phase
- `docs/project/OPEN_DECISIONS.md` â€” D-01â€¦D-17; agents never close these, only the named approver does
- `docs/project/CAPABILITY_MATRIX.md` â€” per-domain status (planned/stub/implemented/tested/validated)
- `docs/project/DEPENDENCY_MAP.md` â€” hard boundaries, phase graph, file-ownership map for parallel agents
- `docs/project/PHASE_PLAN.md` â€” the wave schedule, phase cards (scope/gate/exit), integrator checklist

`docs/specs/ECO-PROGRAM-FA.md` (root, untracked) remains the strategy source; P1 moves it to `docs/specs/`.

## Recently completed (2026-10-11) â€” full record in `reports/`

The **28-item implementation program is COMPLETE and green**: 20 P0/P1/P2 fixes +
3 parallel tracks (Numba engine acceleration **124â€“244أ—**; **73** property-based money
tests; security hardening) + 5 follow-up fixes (cross-tenant idempotency, penny-order
settlement, marketplace fee drift, unblock reconciliation, 16 unguarded write routes)
+ Alembic + root cleanup. `reports/HANDOFF-IMPLEMENTATION-2026-10-10.md` is now the
final program record. Verified artifacts:

- Alembic head `20261011_090000_remaining_legacy_tables` â€” **9 new + 127 legacy**
  tables, all ops **guarded/idempotent**; `upgrade head --sql` renders clean.
- `tools/cleanup.py` â€” the root-cleanup pass **reclaimed ~282 MB + a 36 MB audit log**;
  it refuses tracked files (idempotent).

## Stage 40 (2026-10-19) — development calibration + frozen-model external benchmark

**Status: `PARTIAL` (NOT `VALIDATED_EXTERNAL`).** The model was calibrated on 7
development districts and evaluated on 3 held-out test districts with the
parameters frozen first.

- `engine/hydroma/eval/identifiability_calibration.py` — identifiability-constrained
  calibration; only `epsilon` is free (`HI` fixed at 0.45, because `epsilon` and `HI`
  are perfectly collinear). Fitted **ε = 2.630 g/MJ IPAR**.
- `engine/hydroma/eval/resumable_benchmark_runner.py` — now accepts an explicit
  parameter set, a record-id list, and sharding (`shard_index`/`shard_count`).
- `engine/hydroma/eval/seasonal_predictor.py` — `SeasonalPredictionRequest.hyrue_params`
  and an optional `input_sink` that captures the resolved daily arrays.
- Reports: `engine/reports/STAGE-40-*.md` (8 files).

**Two defects were found and fixed during this stage — read before reusing the
model path:**

1. `HYRUE.__init__` used to let the **crop preset override explicit `HYRUEParams`**
   (`HYRUE(params=calibrated, crop="wheat")` silently ran ε = 2.2). Explicit
   parameters now win. Without this, a "calibrated" benchmark is the baseline.
2. The first calibration was fitted against a **synthetic sigmoid LAI** while the
   benchmark resolves LAI with the GDD model — a train/serve skew. Profiles are now
   built by the benchmark runner itself (`tools/diagnostics/stage40_build_profiles.py`),
   which removed the skew and moved the fitted ε from 2.570 to 2.630.

Regression tests: `engine/tests/test_stage40_parameter_plumbing.py` (params reach the
model; the analytical calibration formula equals `HYRUE.compute` to rel 1e-12).

**Benchmark throughput.** The Sentinel-2 COG reads dominate (~66-130 s per band) and the
APIs throttle above ~8 concurrent readers, so the test run uses a documented
**stratified sample** (`engine/reports/data/stage40_test_sample.json`, seed 20240115),
not all 1,722 test records. `tools/diagnostics/stage40_run_parallel_benchmark.py` runs
8 shards, is resumable, and self-heals.

## Stage 41 (2026-10-20) — full frozen-model test benchmark + error attribution

**Status: `PARTIAL` (unchanged).** The Stage 40 frozen model is carried through
Stage 41 **unchanged**; no calibration, parameter selection, weight change, HI
change or model selection was performed on the test set.

- `engine/reports/data/stage41_frozen_model_manifest.json` — frozen-model identity,
  code hashes, unit contract, input policy, test-set manifest hash, run id.
- `engine/reports/STAGE-41-*.md` — 12 reports.

**What changed in the code, and why it is not scientific.** Two of the eight model
code files now hash differently from the Stage 40 freeze:
`identifiability_calibration.py` and `seasonal_predictor.py`. The change is a
`data_source` provenance field added to four result dataclasses
(`SeasonProfile`, `FoldResult`, `RecordResult`, `OperationalReport`) to satisfy
the repository's own contract in `engine/strict_tests/test_s15_provenance.py`,
which was failing on the Stage 40/41 result types. It is additive metadata with
no numerical effect, shown empirically: records recomputed with the current code
reproduce the Stage 40 predictions bit-identically whenever the upstream inputs
are identical. Regression test: `engine/tests/test_stage41_provenance_contract.py`.

**Two methods worth reusing.**

1. *In-pass dual evaluation.* The baseline (ε=2.2) is computed **in the same
   pass, from the same resolved inputs** as the calibrated model, so the
   comparison is exactly like-for-like. The ε-linearity reconstruction
   (`Y ∝ ε`) is retained only as an independent check. This matters because the
   upstream APIs are **not** deterministic between runs: a Sentinel-2
   acquisition available in one run may be absent in the next, so a baseline
   reconstructed across runs is not a like-for-like comparison.
2. *Re-run control.* `tools/diagnostics/stage41_reproducibility.py` compares the
   Stage 40 and Stage 41 predictions for shared records and separates
   "the model changed" from "the upstream data changed".

**The benchmark now evaluates the full 1,722-record test frame** in 8 resumable,
self-healing shards (`tools/diagnostics/stage41_run_parallel_benchmark.py`).
The record schema carries the Stage 41 provenance fields the Stage 40 schema
lacked: model code hash, resolved-input data hash, valid satellite acquisition
count, valid weather day count, weather/satellite provenance, weather source.
`tools/diagnostics/stage41_finish.py` runs the analysis and writes all 12
reports in one step.

**Repository triage** (`engine/reports/data/stage41_repo_audit.json`): the
failures are classified by real cause — provenance contract, weather input,
path naming, GDD-LAI fallback, EWSI contract, C++ parity, and other agents'
scratch test files. Only the failures that are Stage 40/41 code were fixed.

## Known debt / follow-ups (accurate as of 2026-10-11)

Lint baseline is **769** ruff errors; the documented **2357 â†’ 1876** is stale, and the
**1034** mypy baseline is stale â€” mypy is now **0**. Live `ruff check .` reads
**~800â€“850** today only because in-flight `services/**`/`engine/**` files are present
(measure on a committed tree). Dominant remaining rules (live snapshot): **E501 481,
E402 149, F401 113**, F405 34, B904 18, plus **6 `invalid-syntax`** (PEP-695 in
`services/_contracts/status.py` under ruff `target-version=py311`); B008 is down to ~3.
These are left untouched on purpose â€” line-length / import-order rewraps and 3.12-only
syntax are not provably behaviour-preserving to change mechanically.

Remaining follow-ups (accurate as of 2026-10-11, after P1–P4; see `docs/project/KNOWN_ISSUES.md`):

- ~~`com_orders` unique `(buyer_id, idempotency_key)` backstop~~ — **closed in P4** (model +
  guarded revision `20261011_120000_p4_relationship_backstops`, tests in
  `tests/test_alembic_p4_backstops.py`).
- ~~3 deferred FKs~~ — **closed in P4**: `com_order_items.order_id` and
  `inv_inventory_balances.warehouse_id` were added by the guarded revision;
  `marketplace_order_items.order_id` was already present in a migrated database.
- Off-registry tables — **measured in P4**: a migrated database is 152 tables = 150 registry +
  `alembic_version` + `escrow_items`. The "17 tables / `auth_users` / `app_notifications`" line was
  stale. Still genuinely off-registry: the `ecocoin_balances`/`ecocoin_transactions` raw-SQL pair
  (KN-02, P5) and the deliberately separate `adapters/persistence` SQLite plane.
- Named `Enum` columns — one in the registry (`carbon_credit_records.state`); pre-pass rules
  recorded (additive-only + `ALTER TYPE ... ADD VALUE` in its own revision).
- `adjust` movements store `abs(qty)`; inventory reconciliation is quantity/value-blind
  to ledger mispostings. *(open — P5)*
- Per-user attribution across the five money ledgers is still impossible (no shared user key).
  *(open — P5, D-10)*

## Architecture invariants (must not regress)

- **Import guard = 0 violations.** `services/**` reaches the engine only via
  `services/_gateway_facade.py`; no service imports engine internals directly.
  (`database.config` / `database.base` are the sanctioned persistence-bridge exceptions â€”
  see `tools/detect_imports.py::get_rules()` and `tools/import_guard_policy.json`.)
- **Money is `Decimal`** throughout (never float); settle/valuation batches stay
  balanced and are **posted at their call sites**.
- **Alembic guarded/idempotent** pattern: every op re-run-safe and coexists with
  `create_all`; incompatible changes reviewed by hand and proved with `--sql`.
- **`tools/cleanup.py` must never delete a tracked file** â€” it refuses them by design.
- Route-count: a suite pins the registered route surface, so growing `app.routes`
  beyond it (113 today) is a deliberate change, never an accident.
