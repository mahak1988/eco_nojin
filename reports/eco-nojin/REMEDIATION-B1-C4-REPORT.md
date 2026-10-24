# Remediation B-1 (policy ratchet) + C-4 (structure ceilings) — implementation report

Date: 2026-10-11 · Wave R6 · Owner of this change: agent REME-1
Source items: `reports/eco-nojin/ARCHITECTURE-REMEDIATION-PLAN.md` §B-1, §C-4, §C-2

## 1. Scope and file ownership

Only these files were created or edited:

| File | Change |
|---|---|
| `tools/import_guard_policy.json` | edited (new top-level `ratchet`; per-entry dates; new `ENGINE_NO_DATABASE` rule) |
| `tools/check_policy_expiry.py` | new (stdlib only) |
| `engine/tests/test_structure_ceilings.py` | new (pytest, 6 tests, ~6 s) |
| `.github/workflows/ci.yml` | edited (new `structure` job) |
| `reports/eco-nojin/REMEDIATION-B1-C4-REPORT.md` | new (this file) |

No `engine/**` or `services/**` production or test-logic file was touched, and
`tools/detect_imports.py` was **not** modified: the engine's
`ENGINE_NO_DATABASE` rule stays where the enforcement tool defines it
(`get_rules()`), and the two allowed modules are additionally published as
*data* in the policy file so they carry the same expiry/ratchet treatment.
`tools/detect_imports.py` reads only
`rules.SERVICES_NO_ENGINE_INTERNALS.allowed_imports` and `.facade_files`, so
the extra rule is inert to the guard (verified: `detect_imports.py --root .`
still reports PASS).

## 2. What changed in `tools/import_guard_policy.json` (B-1)

Before (top-level keys): `version`, `updated`, `description`, `rules`.

After: the three unchanged keys plus

```json
"ratchet": {
  "max_allowed_imports": 8,
  "hard_cap": 12,
  "next_review": "2026-11-10"
}
```

Before (per entry of `rules.SERVICES_NO_ENGINE_INTERNALS.allowed_imports`):
`module`, `rationale`.

After (each of the 6 entries): `module`,
`rationale` (text byte-identical to before), plus

```json
"expires": "2027-01-31",
"revisit": "2026-11-10",
"owner": "<team>"
```

`owner` was added because §B-1's Done criterion ("the 8 current exceptions
all have `expires` ≤ 2027-01-31 and a named owner") names one; owners are
team ids, not individuals: `services-team` for
`engine.hydroma.config.settings`, `engine.hydroma.config.rules` and
`engine.hydroma.carbon.calculator` (the POLICY-GAP entry), `engine-team` for
`engine.hydroma.biofertilizer.models`, `engine.hydroma.core.models`,
`engine.hydroma.cpp_bridge`, `database.config`, `database.base`.

New rule `ENGINE_NO_DATABASE` (the "where they live" part of the brief — the
rule object itself is enforced from `tools/detect_imports.py`, so the policy
carries the data copy) with two dated entries:

| module | rationale (summary) | expires | revisit | owner |
|---|---|---|---|---|
| `database.config` | sanctioned persistence bridge: session factory / engine binding, same one the PersistencePort adapter imports | 2027-01-31 | 2026-11-10 | engine-team |
| `database.base` | sanctioned persistence bridge: shared declarative Base registry | 2027-01-31 | 2026-11-10 | engine-team |

Untouched: `version`, `updated`, `description`, both `facade_files` entries
and their rationales, and the 6 existing `rationale` strings — the diff is
purely additive except for the trailing comma each of those strings now
carries. The dated-entry total is 8 = `ratchet.max_allowed_imports`.

## 3. `tools/check_policy_expiry.py` semantics (B-1)

* Loads `tools/import_guard_policy.json` (resolved next to the tool, the same
  way `detect_imports.py` resolves it). Stdlib only: `argparse`, `json`,
  `sys`, `datetime`, `pathlib`. **Never** imports `engine` or `services`
  code — it reads a JSON document, so it can run anywhere the policy is
  present.
* A "dated entry" is any object with a `module` key inside a rule's
  `allowed_imports` list (`facade_files` carries `path`, so it is not a
  carve-out). Total across all rules = **8** today.
* Text output — one line per entry:

  ```
  OK|EXPIRED|OVER-RATCHET <rule> <module> <expires>
  ```

  preceded by a header (`policy`, `today`, `entries: 8 (max_allowed_imports 8,
  hard_cap 12)`) and followed by `status: PASS|FAIL — N expired, M current,
  ratchet 8/12`. Warnings (non-failing) are printed when the count is above
  `max_allowed_imports` but within `hard_cap`, and when `next_review` has
  passed.
* Per-entry status precedence: `EXPIRED` (that entry's `expires` is in the
  past, or missing/unparsable — fail closed, an exception without a date is a
  leak, not a decision), else `OVER-RATCHET` (the total exceeds
  `ratchet.hard_cap`), else `OK`.
* `--json` emits the same report as a machine payload: `entries_total`,
  `max_allowed_imports`, `hard_cap`, `over_max_allowed`, `over_hard_cap`,
  `next_review`, `review_overdue`, `expired_count`, per-entry records
  (`rule`, `section`, `module`, `expires`, `revisit`, `owner`,
  `days_to_expiry`, `status`), `failures`, `status`, `exit_code`.
* Exit code: **1** when any entry is `EXPIRED` or `OVER-RATCHET`, else **0**.
  `next_review` being passed never fails the build on its own, so a late
  review cannot silently become an expired exception.

## 4. Measured numbers (2026-10-11)

From `engine/tests/test_structure_ceilings.py` (`-s` output):

```
engine/gateway line counts: engine/gateway/__init__.py=3117, engine/gateway/pint_audit.py=110
modules over 800 lines: 44 (recorded 44)
network importers under engine/: 24 (16 sanctioned ingestion, 8 pinned offenders)
policy carve-outs: 8/8 (hard cap 12)
check_policy_expiry.py: 8 entries, exit 0
```

**Modules over 800 lines — 44** (23 under `engine/`, 21 under `services/`).
Head of the list (lines):

| lines | module |
|---|---|
| 3117 | `engine/gateway/__init__.py` |
| 2393 | `engine/hydroma/data_pipeline/pipeline.py` |
| 2155 | `engine/hydroma/models/validation/runner.py` |
| 1723 | `engine/models/registry.py` |
| 1347 | `engine/hydroma/scenario_composite/models_additions.py` |
| 1339 | `engine/hydroma/biofertilizer/advanced_calculator.py` |
| 1241 | `engine/hydroma/biofertilizer/data/materials_data.py` |
| 1236 | `engine/scientific_verification/__init__.py` |
| 1217 | `engine/hydroma/formulas/catalog.py` |
| 2639 | `services/inventory/service.py` |
| 1717 | `services/marketplace/hub_service.py` |
| 1549 | `services/api_gateway/routers/marketplace.py` |
| 1471 | `services/finance/tests/test_properties_money.py` |
| 1335 | `services/_gateway_facade.py` |

**Network-import whitelist under `engine/` — 16 files**, all under
`engine/hydroma/data_pipeline/`: the 7 connectors
(`cds`, `era5`, `grdc`, `igrac`, `market_price`, `usgs_nwis`, `wapor`),
`pipeline.py` (the only file carrying `note_download(` calls), and the 8
pipeline tests (`test_{cds,cgls,era5,grdc,igrac,market_price,usgs_nwis,wapor}_connector.py`).

**Pinned network offenders — 8 files** (AST scan for
`requests` / `httpx` / `urllib.request` outside the ingestion area):
`engine/hydroma/biofertilizer/tests/test_nojin_comprehensive.py`,
`engine/hydroma/models/global_watchdog/climate_fetcher.py`,
`engine/hydroma/mrv/satellite_cdse.py`,
`engine/hydroma/satellite/providers/earth_search.py`,
`engine/hydroma/satellite/providers/nasa_power.py`,
`engine/hydroma/simulation/weather_source.py`,
`engine/land/integration/climate_integrator.py`,
`engine/tests/test_unwired_model_wiring.py`.

**Gateway: 2 modules** — `engine/gateway/__init__.py` 3117 lines (allowlisted,
`shrink_by` 2027-01-31, the A-1 split) and `engine/gateway/pint_audit.py`
110 lines.

**Policy**: 8 dated carve-outs (6 `SERVICES_NO_ENGINE_INTERNALS` + 2
`ENGINE_NO_DATABASE`) = `max_allowed_imports` 8, `hard_cap` 12.
**Honesty vocabulary**: 10 brakes, 13 AR rules (unchanged).

## 5. CI diff (`.github/workflows/ci.yml`, new `structure` job)

The job declares no `needs`, so it runs on every push/PR in parallel with the
existing gates. Added between the `architecture` and `security` jobs:

```yaml
  structure:
    name: Structure ceilings + policy expiry (B-1 / C-4)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      # B-1: stdlib-only, no install needed. BLOCKING: an expired or
      # over-ratchet exception is an undocumented architecture violation.
      - name: "Import-guard policy expiry + ratchet (B-1)"
        env:
          PYTHONPATH: ${{ github.workspace }}
          SECRET_KEY: test-secret-key
        run: python tools/check_policy_expiry.py
      # C-4: engine/tests/test_structure_ceilings.py (module-size ceilings,
      # network-import ingestion whitelist, honesty vocabulary size).
      # Non-blocking for now because the legacy measurements it pins are
      # expected to move while the large modules are split; flip
      # continue-on-error to false (or drop the line) once the gateway split
      # (A-1) lands — that is the change that makes the gateway ceiling
      # unconditional rather than allowlisted.
      # blocking once the gateway split (A-1) lands
      - name: "Structure ceilings (C-4)"
        continue-on-error: true
        env:
          PYTHONPATH: ${{ github.workspace }}
          SECRET_KEY: test-secret-key
        run: python -m pip install -q pytest && python -m pytest engine/tests/test_structure_ceilings.py -q -p no:cacheprovider
```

The B-1 step is **blocking** (it is stdlib-only, so it needs no dependency
install and cannot be red for environmental reasons). The C-4 step is
`continue-on-error: true` because it currently pins 44 legacy modules and 8
network offenders that are still in the tree. Both steps set `PYTHONPATH` and
`SECRET_KEY` exactly as the existing `test`/`parity`/`mypy` jobs do.

## 6. Conditions that make each gate blocking later

**B-1 — blocking now, and stays blocking.** `python
tools/check_policy_expiry.py` has no `continue-on-error`. It fails the job
when any exception passes its `expires` (2027-01-31 for all 8 today) or when
the carve-out count exceeds `hard_cap` 12. Re-approving an exception is a
one-line policy edit that must move `expires`/`revisit` — the CI step then
stays green without anyone editing the tool.

**C-4 — blocked until all four of these hold:**

1. **A-1 (gateway split) lands.** `engine/gateway/__init__.py` must be split
   so no gateway module exceeds 1200 lines. This requires editing
   `test_structure_ceilings.py` itself: `GATEWAY_SPLIT_ALLOWLIST` must become
   empty (the test asserts it is non-empty *and* future-dated precisely so it
   cannot be quietly dropped), after which the 1200-line gateway ceiling is
   unconditional. Only then is it honest to make the CI step blocking.
2. **The >800-line set is re-measured.** `LEGACY_LARGE_MODULES` (44 entries,
   counted by `LEGACY_LARGE_MODULES_RECORDED_COUNT`) must be updated to the
   new measured set; the test already reports stale entries (a shrunk module
   leaves its pin behind) without failing on them.
3. **The 8 network offenders are gone.** Routing them through the ingestion
   pipeline / `note_download` (or proving they are offline-safe) empties
   `NETWORK_IMPORT_OFFENDERS`; the test prints the resolved entries so the
   update is a deliberate edit.
4. **Two clean weeks after the policy's own `next_review` (2026-11-10).**
   §B-1 and §C-2 both specify non-blocking first, blocking after a clean
   fortnight; the review date is the anchor for flipping the C-4 step.

Failing to meet 1–3 while making the step blocking would fail the job on
*measured pre-existing debt*, which is exactly the dishonesty this
programme is removing.

## 7. Verification (run 2026-10-11, `D:\eco_nojin\.venv` Python 3.12.10)

```
& $PY -m pytest engine/tests/test_structure_ceilings.py -q -p no:cacheprovider
......                                                                  [100%]
6 passed in 6.29s

& $PY tools/check_policy_expiry.py ; "EXIT=$LASTEXITCODE"
... 8 OK lines ...
status: PASS — 0 expired, 8 current, ratchet 8/12
EXIT=0

& $PY -m pytest engine/tests/test_architecture_rules.py engine/tests/test_no_phantom_test_paths.py -q -p no:cacheprovider
50 passed in 12.31s

& $PY -c "import yaml,json; yaml.safe_load(...ci.yml); json.load(...import_guard_policy.json); print('YAML_JSON_OK')"
YAML_JSON_OK

& $PY tools/detect_imports.py --root . 2>&1 | Select-Object -Last 2
Status: PASS — No violations found

& $PY -m ruff check tools/check_policy_expiry.py engine/tests/test_structure_ceilings.py
All checks passed!
```

`mypy engine --ignore-missing-imports`: Success, no issues found in 396
source files (no new errors). The full engine suite
(`pytest engine/ -q -p no:cacheprovider`) was run as a regression check
after this change; see the run log line quoted in the hand-off message.
