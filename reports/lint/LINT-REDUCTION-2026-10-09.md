# Lint / Type Debt Reduction — 2026-10-09

## Summary

| Metric | Baseline (session start) | Final | Delta |
|---|---|---|---|
| `ruff check .` (repo-wide errors) | **2357** | **1876** | **-481** |
| `mypy engine --ignore-missing-imports` (errors) | **1059** in 132 files | **1034** in 134 files | **-25** |
| mypy `union-attr` errors | 51 | 24 | -27 |
| `pytest engine/ -q` | 1813 passed / 1 pre-existing failure* | **2005 passed, 0 failed** | +192 passed |
| `pytest services/ -q` | 528 passed | **578 passed, 0 failed** | +50 passed |
| `python tools/detect_imports.py --root .` | PASS | **PASS** (0 violations) | unchanged |

\* The one pre-existing engine failure at baseline
(`engine/hydroma/plant_neuro/tests/test_plant_neuro.py::TestSignalProcessor::test_classify_stress_healthy`)
belonged to another agent's in-flight, uncommitted change in `engine/hydroma/plant_neuro/`
(path outside this task's scope). That agent has since fixed it; the final suite is clean.
All other mid-session test failures observed (registry_status, s15/s21, tasmimyar) were
flaky failures in **other agents' untracked or owned files**, each passing in isolation;
they were never caused by changes in this task.

## Baseline methodology (deviation from `git stash`, documented)

The task prescribed measuring the baseline by `git stash`-ing the whole tree, running ruff,
then `git stash pop`. **That was deliberately not done**, for two reasons:

1. Another agent had an active stash (`stash@{0}`) and uncommitted work across the tree at
   session start. Stashing would have clobbered their in-flight files and popped back with
   conflicts.
2. The tree already had ~160 modified-but-uncommitted files from parallel agents, so a
   stash-based measurement would have produced a *hybrid* (HEAD + untracked) snapshot that
   under-reports exactly like the temp-dir copy the task warns about.

Instead the baseline was taken as the **first full measurement of the live tree, before any
edit by this task** (ruff 2357, mypy 1059/132). That measurement matched the task's stated
baseline (2357) exactly for ruff, confirming it as a valid baseline. Final numbers were taken
the same way (`ruff check .`, `mypy engine --ignore-missing-imports`) on the live tree.

### Mid-session external revert (incident note)

At ~03:40 during the session, another agent's stash/pop cycle (`git stash` → work → pop,
visible as `reset: moving to HEAD` in the reflog) reverted a subset of this task's already
applied fixes (most `E402` import-sort regions plus several `I001`/`E741`/`F841` fixes) while
preserving others. This was detected via per-file baseline-vs-current diffs, and **every
reverted fix was re-applied and re-verified** (final sweep: 0 of this task's files remain at
baseline error levels). No test ever failed as a result; both suites were green before and
after the recovery. The per-rule deltas below are stated for the live tree (parallel agents
added a small number of new errors of their own during the session, noted per rule).

## Per-rule deltas (ruff, repo-wide)

| Rule | Baseline | Final | Delta | Notes |
|---|---|---|---|---|
| F401 unused-import | 313 | 219 | **-94** | unused imports removed after grep-verification; `__init__.py` re-export style left |
| E402 import-not-at-top | 384 | 218 | **-166** | `structlog`-logger pattern (135), docstring-after-`__future__`/stray-string (13), FastAPI `get_db` compatibility block (14), `sys`/`json` chords (2) |
| I001 unsorted-imports | 172 | 100 | **-72** | `ruff check --fix --select I001` per file |
| UP045 Optional→`X \| None` | 121 | 0 | **-121** | all in allowed paths; runtime-safe (py3.11 target, `from __future__ import annotations` where needed) |
| UP009 utf-8 decl | 4 | 1 | -3 | remaining one in excluded `services/auth/` |
| UP035 deprecated import | 3 | 0 | -3 | `typing.Callable` → `collections.abc.Callable` |
| B009 getattr-constant | 1 | 0 | -1 | `getattr(item, "mass_kg")` → `item.mass_kg` (guarded by `hasattr`) |
| E401 multiple-imports | 1 | 0 | -1 | resolved as a side effect of an F401 removal |
| UP015 open-mode | 1 | 0 | -1 | `open(f, "r")` → `open(f)` |
| F811 redefinition | 6 | 5 | -1 | removed the dead first definition in `services/landscape/service.py` and `services/blockchain/service.py` (identical byte-for-byte duplicate); remaining ones in excluded paths |
| F822 undefined-in-`__all__` | 1 | 0 | -1 | stale `"PooledConnection"` entry removed (no star-import consumers exist) |
| F841 unused-variable | 11 | 10 | -1 | 4 fixed in allowed paths; parallel agents added 3 elsewhere |
| E741 ambiguous name | 13 | 6 | -7 | 7 local renames (`l` → `label`/`lang`/`soil_coeff`/`line`/`layer`); 2 left (public API params), 4 in excluded paths |
| F601 repeated-dict-key | 1 | 0 | -1 | duplicate key with *identical* value removed |
| C401 generator→set-comp | 1 | 0 | -1 | `tools/_analyze_imports.py` |
| B007 unused-loop-var | 1 | 0 | -1 | `tools/migrate_services_to_gateway.py` |
| **Total** | **2357** | **1876** | **-481** | |

## mypy deltas (engine, `--ignore-missing-imports`)

Union-attr errors on `X | None` were fixed with proper None guards/asserts
(no `# type: ignore`, no `cast` used to hide):

| File | Baseline errors | Final | Fix |
|---|---|---|---|
| `engine/hydroma/hybrid_ml/gp_surrogate.py` | 35 | 13 | `assert self._model is not None` / `assert self._likelihood is not None` after each `GPYTORCH_AVAILABLE` guard (×4 sites); `assert std is not None` after `predict()` (×2) |
| `engine/tests/test_evidence_chain.py` | 15 | 8 | `assert result.execution is not None` + `assert result.execution.trace_id is not None` (3 sites; the `ExecutionMetadata \| None` pattern named in the task) |
| `engine/hydroma/mrv/satellite_cdse.py` | 7 | 1 | `env = dict(os.environ)` copy instead of the `os.environ` union assignment (fixes assignment + union-attr + 4 index errors) |
| `engine/tests/test_knowledge_engine.py` | 2 | 0 | `assert loaded is not None` before `.statement`/`.confidence` |
| `engine/hydroma/analyses/topography_analysis.py` | 16 | 15 | `assert not isinstance(dem_raster, list)` before `.squeeze()` |
| `engine/gateway/__init__.py` | 172 | 171 | `callable` → `Callable[..., Any]` annotations (2 valid-type; `from __future__ import annotations` present ⇒ runtime-inert) |
| **Total (repo-wide)** | **1059 / 132 files** | **1034 / 134 files** | **-25** (union-attr 51 → 24) |

The remaining `engine/gateway/__init__.py` errors (171) are **not** union-attr: they are
genuine signature mismatches in another agent's in-flight model-dispatch machinery
(`call-arg`/`dict-item`/`arg-type`/`attr-defined` on `temp_factor`, `DecisionSupportSystem.compute`,
`_fn` imports). Fixing those requires API decisions that belong to that agent's work, so they
are reported here and left untouched.

## Files changed (by this task)

All paths below are inside the allowed target set. Concurrency-protected files
(currently `M` in git from other agents) were edited only with surgical, verified
one-line changes: `services/blockchain/service.py`, `services/oracle/router.py`,
`services/oracle/schemas.py`, `services/backup/service.py`, `services/ledger/main.py`,
`services/workflow/main.py`, `services/workflow/service.py`, `services/territory_audit.py`,
`services/landscape/models/__init__.py`, `engine/gateway/__init__.py`.

### F401 (unused imports)
```
alembic/versions/20260926_020000_sponsorships.py   services/jobs/router.py
engine/hydroma/quantity.py                          services/landscape/api/governance.py
engine/ports/persistence.py                         services/landscape/api/territories.py
engine/ports/persistence_impl.py                    services/logistics/routers/logistics.py
engine/tests/test_knowledge_engine.py               services/mrv/kobo.py
services/admin/service.py                           services/oracle/schemas.py
services/auth_legacy/service.py                     services/organization/repository.py
services/backup/router.py                           services/organization/service.py
services/blockchain/service.py                       services/provenance/router.py
services/bots/unified_service.py                    services/quality_assurance/routers/quality.py
services/business_modules/carbon/verra_integration.py  services/rangeland/models.py
services/business_modules/voice/twilio_ivr.py       services/rangeland/schemas.py
services/content/bot_dispatch.py                    services/rangeland/service.py
services/contracts/router.py                        services/reporting/service.py
services/dispute_resolution/routers/disputes.py     services/satellite/copernicus.py
services/inventory/routers/inventory.py             services/satellite/nasa_power.py
services/satellite/open_meteo.py                    services/security/passkeys.py
services/satellite/real_land.py                     services/security/pqcrypto.py
services/satellite/soilgrids.py                     services/simulation/adapters/carbon_adapter.py
services/sponsors/routers/admin.py                  tools/_analyze_imports.py
tools/eco04_comprehensive_scan.py                   tools/migrate_services_to_gateway.py
```
`__init__.py` re-export removals (verified unreferenced by any consumer):
```
engine/hydroma/cpp_bridge/__init__.py    services/landscape/models/__init__.py
engine/knowledge/__init__.py             services/simulation/api/__init__.py
engine/tasmimyar/__init__.py             services/sponsors/models/__init__.py
services/analytics/api/__init__.py       services/tourism/models/__init__.py
services/bots/api/__init__.py            services/territory/schemas/__init__.py
```

### I001 (import sorting)
~86 files via `ruff check --fix --select I001`, including:
```
adapters/engine_adapter.py                       engine/hydroma/satellite/providers/base.py
engine/baseline/cases.py*                        engine/hydroma/utils/topographic_calcs.py
engine/hydroma/alembic_graph.py                  engine/hydroma/watershed/calculator.py
engine/hydroma/crop/ndvi_analysis.py             engine/hydroma/wrapper.py
engine/hydroma/decision_support/dss.py           engine/resilience.py*
engine/hydroma/economics/integration.py          engine/strict_tests/test_s00…s11*
engine/hydroma/groundwater/models.py             engine/tests/test_evidence_chain.py
engine/hydroma/mrv/metrics.py                    engine/tests/test_knowledge_engine.py
engine/hydroma/quantity.py                       services/admin/api/__init__.py
engine/hydroma/biofertilizer/trials.py           services/admin/overview_service.py
engine/hydroma/calibration/version_manager.py    services/admin/repository_overview.py
engine/hydroma/cpp_bindings.py                   services/alerting/models.py
engine/hydroma/cpp_bridge/__init__.py            services/analysis/drought_agent.py
engine/hydroma/cpp_bridge/tests/test_parity.py   services/analysis/scenario_agent.py
engine/hydroma/examples/calibrate_rusle_example.py  services/analytics/api/__init__.py
engine/hydroma/simulation/weather_source.py      services/auth_legacy/repository.py
engine/hydroma/climate/et_calculator.py          services/auth_legacy/service.py
services/backup/service.py                       services/bots/api/__init__.py
services/backup/router.py                        services/bots/main.py
services/business_modules/carbon/verra_integration.py  services/business_modules/voice/twilio_ivr.py
services/content/bot_dispatch.py                 services/contracts/router.py
services/dispute_resolution/routers/disputes.py  services/field_monitoring/service.py
services/integration/outbox.py                   services/inventory/routers/inventory.py
services/jobs/models.py                          services/jobs/router.py
services/land/land_profile.py                    services/land/service.py
services/land/tests/test_land_profile.py         services/landscape/api/governance.py
services/landscape/api/territories.py            services/landscape/utils.py
services/ledger/main.py                           services/livestock/api/__init__.py
services/logistics/routers/logistics.py          services/map_engine/fetchers/{dem,landcover,rainfall,runoff,soil,vegetation}_fetcher.py
services/map_engine/orchestrator.py              services/map_engine/pipelines/{runoff,rusle}.py
services/mobile_monitoring/service.py            services/models/land_models.py
services/mrv/kobo.py                             services/nojin/repository.py
services/nojin/service.py                        services/oracle/router.py
services/oracle/schemas.py                       services/organization/repository.py
services/organization/service.py                 services/provenance/models.py
services/provenance/router.py                    services/provenance/service.py
services/quality_assurance/routers/quality.py    services/rangeland/models.py
services/rangeland/schemas.py                    services/reporting/api/__init__.py
services/reporting/service.py                    services/satellite/api/__init__.py
services/satellite/copernicus.py                 services/satellite/monitoring_service.py
services/satellite/nasa_power.py                 services/satellite/open_meteo.py
services/satellite/real_land.py                  services/satellite/soilgrids.py
services/security/anti_phishing.py               services/security/middleware.py
services/simulation/adapters/carbon_adapter.py   services/simulation/adapters/multilayer_adapter.py
services/simulation/api/__init__.py              services/simulation/engine/orchestrator.py
services/sponsors/models/__init__.py             services/sponsors/routers/admin.py
services/territory/schemas/__init__.py           services/validation/formula_checks.py
services/workflow/main.py                        services/workflow/service.py
```
\* `engine/baseline/cases.py`, `engine/resilience.py` and `engine/strict_tests/*` were edited
early in the session and then **reverted to HEAD** once the allowed-set rule was re-checked
(alembic/, engine/baseline/, engine/strict_tests/, engine/resilience.py, engine/land/** are
*not* in the allowed target list; `engine/strict_tests/conftest.py` was likewise restored
byte-for-byte after an errant I001 fix). Files edited by other agents inside those paths
(`test_s02`, `test_s07`, `test_s11`) had only this task's import-split manually undone; their
content changes were preserved.

### UP045 (121) + UP009 (3) + UP035 (3) + B009 + UP015 + E401
```
engine/gateway/__init__.py             services/landscape/api/governance.py
engine/ports/persistence_impl.py       services/landscape/api/territories.py
services/admin/overview_service.py     services/landscape/utils.py
services/blockchain/service.py         services/territory_audit.py
engine/knowledge/__init__.py           services/oracle/router.py
services/oracle/schemas.py             services/territory/schemas/__init__.py
```
(`engine/hydroma/groundwater/models.py` and `services/inventory/routers/inventory.py` received
the same UP045 fix.)

### E402 (166 fixed)
`structlog`-logger pattern (imports moved above `logger = structlog.get_logger()`;
import order unchanged, logger assignment only moves down):
```
engine/hydroma/biofertilizer/trials.py          services/land/land_profile.py
engine/hydroma/calibration/version_manager.py   services/land/tests/test_land_profile.py
engine/hydroma/decision_support/dss.py          services/map_engine/fetchers/dem_fetcher.py
engine/hydroma/economics/integration.py         services/map_engine/fetchers/landcover_fetcher.py
engine/hydroma/examples/calibrate_rusle_example.py  services/map_engine/fetchers/rainfall_fetcher.py
engine/hydroma/groundwater/models.py            services/map_engine/fetchers/runoff_fetcher.py
engine/hydroma/utils/topographic_calcs.py       services/map_engine/fetchers/soil_fetcher.py
engine/hydroma/mrv/metrics.py                   services/map_engine/fetchers/vegetation_fetcher.py
services/bots/main.py                           services/map_engine/orchestrator.py
services/bots/unified_service.py                services/map_engine/pipelines/runoff.py
services/field_monitoring/service.py            services/map_engine/pipelines/rusle.py
services/land/service.py                        services/mobile_monitoring/service.py
```
FastAPI `get_db` compatibility-block pattern (imports moved above the compatibility generator):
```
services/admin/api/__init__.py       services/reporting/api/__init__.py
services/analytics/api/__init__.py   services/satellite/api/__init__.py
services/bots/api/__init__.py        services/simulation/api/__init__.py
```
Docstring/`__future__`-shadow pattern (imports moved above the stray string; `__doc__` stays `None`):
```
engine/hydroma/watershed/calculator.py   services/landscape/models/__init__.py
engine/hydroma/mrv/metrics.py            services/tourism/models/__init__.py
```
Misc safe moves:
```
engine/hydroma/cpp_bridge/__init__.py (import sys → top)
engine/hydroma/analyses/topography_analysis.py (import json → top; was used 15 lines above its import)
```

### F841 / E741 / F811 / F601 / C401 / B007 / F822
```
adapters/hydroma_adapter.py        (F841: pure `t_mean` assignment removed)
services/auth_legacy/service.py     (F841: `user =` binding dropped, `await` kept)
services/rangeland/service.py       (F841: `result =` binding dropped, `await` kept)
engine/hydroma/alembic_graph.py     (E741: `l` → `label`)
engine/hydroma/config/settings.py   (E741: `l` → `lang`, ×2)
engine/hydroma/crop/ndvi_analysis.py (E741: `l` → `soil_coeff`)
engine/hydroma/wrapper.py           (E741: `l` → `soil_coeff`)
services/inventory/routers/inventory.py (E741: `l` → `line`)
services/simulation/adapters/multilayer_adapter.py (E741: `l` → `layer`)
services/landscape/service.py       (F811: dead first `remove_governance_member` removed)
services/blockchain/service.py      (F811: byte-identical duplicate `get_balance` removed)
engine/ports/persistence.py         (F822: stale `__all__` entry removed)
tools/migrate_services_to_gateway.py (F601 duplicate key; B007 loop var)
tools/_analyze_imports.py            (C401 set comprehension)
tools/eco04_comprehensive_scan.py    (F841 dead `is_internal` assignment)
```

### mypy (union-attr guards)
```
engine/hydroma/hybrid_ml/gp_surrogate.py      engine/tests/test_evidence_chain.py
engine/hydroma/mrv/satellite_cdse.py          engine/tests/test_knowledge_engine.py
engine/hydroma/analyses/topography_analysis.py  engine/gateway/__init__.py
```

## Errors deliberately left (with reasons)

| Rule | Count left (allowed paths unless noted) | Reason |
|---|---|---|
| B008 | 207 across 26 files | FastAPI `Depends()` in defaults → `Annotated[...]` changes the callable signature's default value (calling the endpoint function directly without the dep would newly raise) — not provably behaviour-preserving at this volume; needs a dedicated Annotated migration. |
| E501 | ~327 across 87 files | Re-wrapping long lines risks changing string literals, f-strings and comments; no mechanical, provably-safe rewrite exists. (Net repo-wide change was -6 and came from other agents' edits.) |
| C408 | 65 | **All 65** are in `temp_probe_gateway.py`, an untracked scratch/probe script actively owned by another agent. |
| E402 | ~21 in allowed paths | Deliberately unsafe: `services/satellite/sentinel2_provider.py` (11 — imports must stay **below** the `warnings.filterwarnings` calls or import-time warnings escape the filters); `engine/data_connector.py` / `engine/test_connector.py` (5 — imports depend on a preceding `sys.path.insert`); `services/conftest.py` (2 — conftest.py is off-limits); `services/notification/main.py`, `services/reporting/main.py` (2 — imports below `uvicorn.run` entry points, `M` files); `alembic/env.py` (1 — `config = None` placeholder). |
| E741 | 2 | `services/satellite/copernicus.py` — `l` is a **public function parameter** (`l: float = 1.0`); renaming would break the API. |
| UP042 | 7 | `class X(str, Enum)` → `StrEnum` changes the class MRO/type identity (observable via `type(x).__mro__`, pickling, SQLAlchemy Enum columns); pinned to py3.11 by config. |
| B904 | 1 in allowed path (`services/auth_legacy/service.py`; 18 total) | `raise ... from err` changes `__cause__`/`__context__` — an observable traceback change, not a mechanical no-op. |
| E722 | 2 (`tools/eco04_comprehensive_scan.py`) | `except:` → `except Exception:` changes which exceptions are caught (KeyboardInterrupt/SystemExit) — a real behaviour change. |
| B005 | 1 (`tools/migrate_services_to_gateway.py`) | `.rstrip(' as ')` intent is ambiguous (character-set vs suffix semantics); no equivalent rewrite without deciding intent. |
| F401 re-exports | ~90 | `__init__.py` "consider adding to `__all__`" re-export style (e.g. `engine/land/integration/__init__.py` optional-dependency probes, `services/reporting/api/__init__.py` schema re-exports) — removing them would shrink the public API surface. |
| invalid-syntax | 6 (4 in `services/_contracts/status.py`, 2 in excluded `services/api_gateway/`) | PEP-695 syntax under ruff's `target-version = "py311"`; fixing requires either removing 3.12-only syntax (behaviour change on 3.12) or raising target-version (pyproject lint config is off-limits). |
| mypy gateway dispatch | 171 (file) | Genuine model-dispatch signature mismatches in another agent's in-flight `engine/gateway/__init__.py`; not Optional-union issues, need API decisions. |
| mypy no-any-return, override, dict-item, … | ~800 repo-wide | Genuine type friction requiring per-case judgement (casts would hide, not fix); outside the task's union-attr remit. |

## Verification performed

1. `ruff check .` — 2357 → 1876 errors (every batch measured).
2. `mypy engine --ignore-missing-imports` — 1059/132 → 1034/134 (final).
3. `pytest engine/ -q -p no:cacheprovider` — **2005 passed, 0 failed** (29 skipped, 43 xfailed).
4. `pytest services/ -q -p no:cacheprovider` — **578 passed, 0 failed** (9 skipped).
5. `python tools/detect_imports.py --root .` — **PASS**, 0 violations.
6. Whole-tree AST parse — no syntax errors introduced (1 pre-existing in excluded
   `services/knowledge/service.py`, another agent's in-flight file).
7. Per-file diff review for every mechanical batch (imports/annotations/asserts only);
   every removed import grep-verified unused inside its file and unreferenced by consumers.

---

# 2026-10-10 — B008/F401/E402/I001 reduction in `services/**` (measured baseline, test-gated)

Scope: `services/**` only. `engine/`, `tools/`, `database/`, `.github/`, `pyproject.toml`
untouched. Mechanical fixes only, five authorised categories (B008→`Annotated`, F401
removal, safe E402 moves, I001, re-export `__all__`). No test was weakened, no public API
renamed, no `noqa` added.

## Baseline → final

Measured on the **live tree** with `python -m ruff check . --statistics` from `D:\HyDroMA`
(other agents were editing the tree concurrently, so the baseline drifted from the 1999
quoted in the task brief to 2012 at session start):

| | baseline (2026-10-10) | final | delta |
|---|---|---|---|
| **repo total** | **2012** | **923** | **−1089** (target ≤ 1650: **met**) |
| `services/` total | 1565 | 478 | −1087 |

Per-rule deltas (repo-wide; several categories also moved from concurrent agents' work):

| Rule | baseline | final | delta | this task |
|---|---|---|---|---|
| B008 | 782 | 2 | −780 | −780 (services 782→2) |
| I001 | 109 | 24 | −85 | −84 (services 84→0) |
| E402 | 220 | 163 | −57 | −57 (services 203→146) |
| F401 | 236 | 82 | −154 | services 173→18 |
| E501 | 511 | 511 | 0 | **0** (see below) |
| B904/F841/E741/F811/B023/F821/UP042/C408/invalid-syntax | unchanged | | 0 | 0 — not in the authorised mechanical set |

## B008 → `typing.Annotated` (79 files, 780 diagnostics)

`services/jobs/router.py` was used as the pilot: FastAPI 0.141.1 + pydantic 2.13 confirm
`Annotated` support (FastAPI ≥ 0.95). Rules derived from `fastapi/dependencies/utils.py::
analyze_param` (fastapi asserts: *"`Query` default value cannot be set in `Annotated` … set
the default value with `=` instead"*):

- `Depends`/`Security`/`_Depends` defaults → `x: Annotated[T, Depends(...)]`. Unannotated
  params get `Annotated[Any, Depends(...)]` — probe-verified identical dependant tree,
  OpenAPI and `dependency_overrides` behaviour.
- `Query`/`Header`/`Cookie`/`Body`/`Form`/`File` defaults → the marker must **not** carry a
  default: `status: Annotated[str | None, Query(description=…)] = None`; a `...`
  (`RequiredParam`) default is dropped so the parameter stays required.
- Ordering guard: a parameter that becomes required must not follow a still-defaulted one;
  where an intervening plain default forces it, the `Depends` param receives an inert
  `= None` (FastAPI ignores defaults on dependency params — verified by probe).
- Functions containing `default_factory=` markers, comments inside the span, or
  non-FastAPI-marker calls are skipped whole and reported.

Per-file verification for every migrated router: `routecheck` harness dumps each route's
dependant tree (sub-dependencies, params, other inputs) **and** the full `app.openapi()`
schema, before vs after. **All 79 files: routes and OpenAPI byte-identical.** Zero reverts
from A/B failures.

B008 files (79):
```
services/jobs/router.py                              services/api_gateway/routers/village_hub.py
services/api_gateway/routers/auth.py                 services/api_gateway/routers/marketplace.py
services/inventory/routers/inventory.py              services/api_gateway/routers/compliance.py
services/finance/routers/finance.py                  services/tourism/api/router.py
services/api_gateway/routers/admin_content.py        services/commerce/routers/commerce.py
services/api_gateway/routers/ecowallet.py            services/api_gateway/routers/nojin.py
services/knowledge/router.py                         services/api_gateway/routers/analytics.py
services/api_gateway/routers/iot_devices.py          services/api_gateway/auth.py
services/api_gateway/routers/organizations.py        services/alerting/router.py
services/api_gateway/routers/legal_texts.py          services/api_gateway/routers/tool_registry.py
services/api_gateway/routers/admin_users.py          services/api_gateway/routers/farms.py
services/api_gateway/routers/mrv.py                  services/api_gateway/routers/rangeland.py
services/api_gateway/routers/admin_models.py         services/api_gateway/routers/ai_chat.py
services/api_gateway/routers/auth_supabase.py        services/api_gateway/routers/satellite.py
services/api_gateway/routers/admin_settings.py       services/api_gateway/routers/community.py
services/ledger/main.py                              services/logistics/routers/logistics.py
services/quality_assurance/routers/quality.py        services/admin/api/__init__.py
services/analytics/api/__init__.py                   services/api_gateway/routers/motors.py
services/api_gateway/routers/simulation.py           services/api_gateway/routers/soil.py
services/api_gateway/routers/sync.py                 services/reporting/api/__init__.py
services/api_gateway/routers/admin_bots.py           services/api_gateway/routers/content_public.py
services/api_gateway/routers/culture.py              services/bots/api/__init__.py
services/ledger/service.py                           services/notification/main.py
services/telegram_bot/api/__init__.py                services/api_gateway/routers/finance_consolidation.py
services/api_gateway/routers/pilot.py                services/api_gateway/routers/scenarios.py
services/api_gateway/routers/support.py              services/auth/api/__init__.py
services/reporting/main.py                           services/satellite/api/__init__.py
services/security/step_up.py                         services/workflow/main.py
services/sponsors/routers/sponsors.py                services/api_gateway/routers/analyses.py
services/api_gateway/routers/contact.py              services/api_gateway/routers/newsletter.py
services/api_gateway/routers/platform.py             services/api_gateway/routers/realtime.py
services/api_gateway/content_repository.py           services/api_gateway/settings_repository.py
services/sponsors/routers/admin.py                   services/provenance/router.py
services/api_gateway/routers/admin_errors.py         services/api_gateway/routers/admin_overview.py
services/api_gateway/routers/admin_security.py       services/api_gateway/routers/carbon.py
services/api_gateway/routers/ecosystem.py            services/api_gateway/routers/hydroma_hub.py
services/auth/main.py                                services/contracts/router.py
services/dispute_resolution/routers/disputes.py      services/landscape/api/governance.py
services/landscape/api/territories.py                services/oracle/router.py
```

### E501 containment (net zero)

The `Annotated` rewrites transiently created **63** new >100-char signature lines across 21
files (measured 30 → 93 E501 inside the migrated set). Every one was re-wrapped
mechanically — one-parameter-per-line, and `Annotated[…]` expansion only when a single
parameter still exceeded 100 chars — a whitespace-only change inside the parameter
bracket. Final: 30 → 30, **no net E501 change**. Wrapped files: village_hub, inventory,
commerce, backup/router, nojin, knowledge/router, analytics, api_gateway/auth,
alerting/router, farms, mrv, ai_chat, auth_supabase, satellite, ledger/main, logistics,
quality_assurance, soil, contact, newsletter, provenance.

## I001 (48 fixed, `ruff --fix` per file after review)

Applied to files that already carried I001 debt; each file's module import verified before
and after the fix. One revert: `services/api_gateway/routers/hydroma_soil.py` — its import
check transiently failed (`NameError: name 'date'`) during a concurrent-edit window; the
file imports cleanly 3/3 afterwards and was restored to its pre-fix state. Two files noted
as pre-existing unimportable (`hydroma_water.py`, `land.py` — another agent's in-flight
`date`-reference breakage, untouched by this task).

## F401 (58 removals + 6 re-export `__all__` + 3 manual)

Removals were verified three ways: ruff's own fix, an AST re-scan for any residual
`Name`/annotation/`__all__` reference to the removed binding, and a before/after module
import. Availability-probe imports (ruff suggests `importlib.util.find_spec`, e.g.
`services/_gateway_facade.py:871`) were left in place — the `ImportError` is the signal.

Re-export `__init__.py` modules (no `__all__` existed) received a programmatically
computed `__all__` containing **every** public top-level name, so the `import *` surface is
provably unchanged (verified by comparing `from module import *` bindings before/after):
```
services/data_manual/__init__.py          services/marketplace/models/__init__.py
services/simulation/api/__init__.py       services/livestock/api/__init__.py
services/reporting/api/__init__.py        services/auth/api/__init__.py
```
One conservative revert: `services/auth/permissions.py` — the unused `TYPE_CHECKING`
import is shadowed by a function-local import of the same name, so the AST check could
not prove safety automatically; it was then fixed by hand (import block removed, I001
re-normalised, `pytest services/auth` green). Manual completions:
`services/telegram_bot/api/__init__.py` (unused `Optional`), `services/scientific_motors/
chain_runner.py` (unused `safe_detail_for_status`).

## E402 (57 diagnostics, 21 files)

Only provably safe moves, each classified by inspecting the blocking statement:

- **`get_db` compatibility-generator pattern** (imports moved above the generator):
  `analyses.py`, `farms.py`, `scenarios.py`, `content_public.py`, `support.py`,
  `analytics.py`, `ai_chat.py`, `satellite.py`, `simulation.py`, `soil.py`,
  `auth/api/__init__.py`, `telegram_bot/api/__init__.py`.
- **structlog-logger pattern** (imports moved above the logger assignment):
  `services/scientific_motors/data_repository.py`, `services/scientific_motors/mrv_system.py`,
  `services/telegram_bot/integration_service.py`.
- **Section-scoped stdlib/third-party imports** moved into the top block:
  `simulation.py` (`asyncio`, `json as _json`, `StreamingResponse`), `soil.py`
  (`datetime`, `pydantic`), `platform.py` (`import math`; a duplicate `import logging`
  re-import was dropped as redundant), `platform.py:49` (`database.models`),
  `nats_client.py` (`engine.hydroma.config.settings`), `auth/main.py`,
  `notification/main.py`, `reporting/main.py` (`from fastapi import FastAPI`),
  `services/finance/tests/test_finance.py` (4 late test-module imports).

Every moved file was re-import-checked and, where it exposes a router/app, re-run through
the `routecheck` A/B harness against its pre-move dump: **all imports OK, all routes and
OpenAPI identical.**

## Categories deliberately left (with reasons)

| Category | Count left | Reason |
|---|---|---|
| E402 docstring-after-imports | 47 (`api_gateway/security.py` 12, `security_legacy.py` 9, `routers/marketplace.py` 17, `marketplace/models/__init__.py` 9, `routers/platform.py` 10) | The only mechanical fix is moving the stray string above the imports, which would promote it to the module `__doc__` (currently `None`) — an observable module-attribute change, so left (same judgement as the 2026-10-09 session). |
| E402 dotenv / sys.path / logging-config | 57 (`api_gateway/main.py` 39, `telegram_bot/*` 16, `services/conftest.py` 2) | `load_dotenv()` must run before imports that read env; `sys.path.insert` gates the following imports; `basicConfig`/`filterwarnings` ordering controls import-time logging and warning capture. Not provably side-effect-free. |
| E402 guard-block imports | 13 (`satellite/sentinel2_provider.py` 11, `scientific_motors/aquacrop_real*.py` 2) | Imports must stay below `warnings.filterwarnings(...)` and inside optional-dependency `try` blocks. |
| E402 deferred (circular-avoidance) | 13 (`routers/motors.py` 9, `marketplace/models/__init__.py` 3, `marketplace/service.py` 1) | Late `.marketplace_founder` / `.village_hub` / `hub_service` / scientific-motor imports break on circular import if hoisted. |
| E402 in PEP-695 files | 6 (`_contracts/status.py` 4, `api_gateway/base_router.py` 1, `eventbus/retry.py` 1) | E402 here is a parse artefact of `class X[T]:` under `target-version = "py311"`; the files carry pre-existing `invalid-syntax`. |
| B008 | 2 (`provenance/router.py`) | `Body(default_factory=dict, …)` — in `Annotated` form FastAPI rewrites `field_info.default = RequiredParam`, silently turning the parameter **required**; a behaviour change, so the function is skipped whole. |
| F401 | 18 in services (17 in `knowledge/service.py`, 1 in `_gateway_facade.py`) | `knowledge/service.py` is another agent's syntax-broken in-flight file; `_gateway_facade.py:871` is a deliberate C++ availability probe. |
| E501 | 511 | Line-length re-wrapping is not a provably mechanical rewrite (strings/f-strings/comments); outside the authorised fix set. |
| B904 / F841 / E741 / F811 / UP042 / B023 / … | 18/10/6/4/2/6 | Outside the five authorised categories (each has observable semantics). |

## Verification performed

1. `python -m ruff check .` — **2012 → 923** (baseline re-measured several times; the
   tree drifts a few errors per hour from concurrent agents).
2. `pytest services/ -q -p no:cacheprovider` after **every** batch of ≤ 20 files (6 gates):
   baseline 916 passed / 9 skipped → final **995 passed / 9 skipped / 0 failed**.
   One gate run showed 2 failures
   (`services/finance/tests/test_inventory_valuation_accounts.py`,
   `services/inventory/tests/test_valuation_cogs.py`); both passed in isolation (40 passed)
   and the next full run was green — recorded as pre-existing order/isolation debt, not a
   regression from this task.
3. Per-file A/B route verification (`app.openapi()` + dependant trees) for all 79 B008
   files and 20 E402-moved files exposing routers — all identical.
4. `python tools/detect_imports.py --root .` — **PASS, 0 violations** (1143 files, 8 rules).
5. Whole-tree AST parse after every mechanical batch (syntax guard inside the tooling);
   the only pre-existing parse failure (`services/knowledge/service.py`) belongs to
   another agent's in-flight work and was not touched.
6. UTF-8 integrity check over all 79 migrated files (token multiset of every non-ASCII run
   compared with the pre-migration backups): 0 mismatches. (Lesson applied mid-session:
   Python's `ast` `col_offset` is a **UTF-8 byte** offset, so the surgical edits were
   switched to byte-based slicing after the first migration of
   `services/landscape/api/{governance,territories}.py` exposed the mismatch on
   Persian-text files.)

---

## 2026-10-10 (engine agent, in-scope engine mypy + ruff debt)

Scope: `engine/**` minus the areas owned by other agents (`engine/hydroma/models/validation/**`,
`engine/hydroma/models/hdvi*`, `hpheno*`, `engine/hydroma/biofertilizer/**`, `engine/gateway/**`
including `engine/gateway/__init__.py`, `engine/tests/test_scenario_layer.py`,
`engine/tests/test_registry_status.py`, `engine/tests/test_unwired_model_wiring.py`).
Nothing was committed; the tree is left dirty for the repo owner to review.

### Measurement note (why the baseline command was extended)

`python -m mypy engine --ignore-missing-imports` **cannot complete in this environment**: the
installed `pint 0.26.1` uses PEP-695 type-parameter syntax, which `mypy 1.13.0` cannot parse
under the repo's pinned `python_version = "3.11"` (see `[tool.mypy]` in `pyproject.toml`), so
the run stops with 7 blocking errors (1 `pint` `[syntax]` + 6 `yaml` `[import-untyped]`)
after checking nothing. Under `--python-version 3.12` mypy crashes inside pint's registry.
The two consumers of pint (`engine/gateway/pint_audit.py`, `engine/tests/test_pint_unit_gate.py`)
are therefore **unmeasurable** here; the gateway area is out of scope regardless.

All numbers below come from the same command extended with an `--exclude` for the two
pint importers (plus one transiently-broken validation-corpus file while the other agent
was mid-edit):

```
python -m mypy engine --ignore-missing-imports --exclude "engine[\\/]gateway|test_pint_unit_gate|test_validation_corpus_completion"
```

Reconciliation with the task baseline of 966 errors / 143 files: 966 - 744 = 222 = the gateway
area (171 at baseline, 182 now) plus the two pint-importing files. Everything excluded from my
scope on one side and excluded for measurability on the other is therefore accounted for.

### mypy results

- Baseline (2026-10-10, start of this session): **744 errors in 133 files**.
- Final: **95 errors in 11 files - 0 of them in scope**; the 95 belong to the excluded areas
  (`models/validation/**` 26, `models/biofertilizer/**` 61, `models/hdvi.py` 2, `models/hpheno.py` 5).
- Effective full-engine total: 95 (in-scope subset, all excluded areas) + 182
  (`engine/gateway/__init__.py` only, unchanged by this work) + 2 unmeasurable pint consumers
  - roughly **280**, i.e. 686 fewer than the 966 task baseline and well under the 780 ceiling.

Fix techniques used, by mypy error family:

- **`no-any-return` (~190)**: annotated locals for numpy/scipy/`float ** float` results
  (`pressure: float = ...; result: float = ...`), the `Any`-from-untyped-`type` call
  family, and `**` with a non-int exponent (typeshed returns `Any` for `float ** float`).
- **`assignment` (~110)**: `= None` defaults on non-Optional dataclass fields widened to
  `T | None`; untyped dict literals annotated `dict[str, Any]` / `dict[str, dict[str, Any]]`;
  list-then-ndarray rebinding split into a second variable (`y_samples` / `y`);
  `dict[str, float]` resource maps corrected to `dict[str, dict[str, str]]`.
- **`arg-type` / `call-arg`**: `dict[str, Any]` annotations for httpx/requests `params`,
  optional-dependency factories typed `Callable[[], UnitOfWork]`, and explicitly passing
  the values that pydantic `Field(None, ...)` defaults supply (mypy cannot see them).
  Two call-arg `Field`-default cases were reverted to documented ignores after a test
  proved the "missing default" is a recorded contract: the s03 `TestSpatialRunoff` source
  scan (`peak_flow_map_path` must stay absent) and `SpatialRunoffOutput`.
- **`union-attr` / `index` / `operator` (the `ExecutionMetadata | None` family)**: the
  established pattern from `test_evidence_chain.py` / `satellite_cdse.py` - dict access
  through a membership guard switched to indexing (`self._facts[fid] for fid ... if fid in self._facts`),
  `assert x is not None` where a caller guarantees presence, and `isinstance` asserts on
  `Module.__getattr__` (`DDP.module`) and `xr` rasterio opens (single-band = DataArray).
- **`override` (32)**: one exhaustive block per model class - the `ScientificModel` ABC
  declares `**inputs` / dict signatures while the concrete model API is a positional typed
  inputs object. Each site carries `# type: ignore[override]` plus the same three-line
  reason; unifying the two is a cross-hierarchy API decision, not a mechanical fix.
- **`misc` / `no-redef`**: optional-import fallbacks (`engine/land/__init__.py`,
  `engine/hydroma/__init__.py`, `engine/hydroma/soil/integrator.py`) marked per line with a
  one-line reason; `cpp_bridge` optional loading switched to `importlib.import_module` and a
  from-import alias so no `# type: ignore[no-redef]` is needed there.

### Per-file top-20 (in-scope), before to after

| file | before | after |
| --- | --- | --- |
| engine/hydroma/data_assimilation/assimilation.py | 47 | 0 |
| engine/hydroma/simulation/orchestrator.py | 26 | 0 |
| engine/scientific_verification/__init__.py | 24 | 0 |
| engine/land/__init__.py | 21 | 0 |
| engine/hydroma/distributed_ml/trainer.py | 20 | 0 |
| engine/hydroma/climate/et_calculator.py | 16 | 0 |
| engine/hydroma/hybrid_ml/pinn.py | 16 | 0 |
| engine/hydroma/models/expansion/modflow6.py | 15 | 0 |
| engine/hydroma/analyses/topography_analysis.py | 15 | 0 |
| engine/hydroma/hybrid_ml/gp_surrogate.py | 13 | 0 |
| engine/hydroma/scenario_composite/engine.py | 13 | 0 |
| engine/tests/test_fao56_example18.py | 12 | 0 |
| engine/tests/test_decision_economic_criteria.py | 12 | 0 |
| engine/hydroma/simulation_env/stress.py | 11 | 0 |
| engine/tests/test_groundwater_extended.py | 11 | 0 |
| engine/land/integration/climate_integrator.py | 11 | 0 |
| engine/hydroma/data_pipeline/pipeline.py | 10 | 0 |
| engine/hydroma/soil/health.py | 10 | 0 |
| engine/hydroma/plant_neuro/voc.py | 10 | 0 |
| engine/ports/persistence_impl.py | 9 | 0 |

~120 in-scope engine files changed in total (full list: `git diff --name-only engine/`).
`engine/land/**`, `engine/ports/**`, `engine/hydroma/calibration/**`,
`engine/hydroma/simulation/**`, `engine/hydroma/cpp_bridge/**`,
`engine/hydroma/soil/**`, `engine/hydroma/mrv/**` and `engine/strict_tests/**` went to
**zero** mypy errors within the measurable scope.

### ruff results

- engine: **278 to 230** (`-49`): I001 `-18` (per-file `ruff check --fix --select I001`),
  E402 `-15` (11 provably safe moves; only the `sys.path.insert`-dependent import left),
  F401 `-4` (genuinely unused after an AST re-scan), F841 `-2`, B905 `-2` (`strict=False`,
  identical to the default), B007 `-1`, C408 `-1`, F601 `-1` (duplicate dict key removed).
- repository: **1134 to 883** overall, measured live; the rest of the reduction is the
  services agent's parallel work on `services/**`.
- no new E501 was introduced: every edited line was re-checked with
  `ruff check <file> --select E501`, and two initially over-length rewrites
  (`simulation/calibration.py`, `simulation_env/controller.py`) were rewrapped before
  finishing.

### Behaviour preservation (all verified, not assumed)

- `pytest engine/` after every batch (<= 20 files) and at the end: **2559 passed, 0 failed**
  (2500 passed at session start). Mid-session failures were investigated to ground each
  time: the 3 flaky `test_registry_status`/`test_s15` failures reproduced without my
  changes (other agents' in-flight files), and one real regression of mine
  (`_find_best_scenario` assert breaking the empty-comparison path exercised by
  `test_scenario_layer.py::TestGatewayRecommend`) was reverted to an annotation-only fix.
- Two "fixes" tried and deliberately reverted after checks: passing `peak_flow_map_path`
  explicitly (a strict test asserts the source never mentions the field) and dropping the
  `darcy_velocity_m_day` dataclass field (a constructor call passes it).
- Source-scanning tests were respected: greps for `inspect.getsource` / string assertions
  were run before touching any constructor that a test proves by source text.
- `python tools/detect_imports.py --root .` - **PASS, 0 violations**.
- Runtime smoke checks where no unit test exists: the coefficient registry
  (`engine/hydroma/formulas/unvalidated.py`: 178 class / 156 module entries), the TTN
  payload parser, `FormulaEvaluator` (including the unknown-method rejection path), the
  baseline case sweep (17/17), the EWSI model, and the drought-trajectory weather
  generator - all produce the same outputs as before the edits.

### Categories left, with reasons

1. **`engine/gateway/__init__.py` - 182 errors, untouched by design.** The dispatch-signature
   family needs an API decision (which side of the gateway contract wins); the task
   explicitly excludes this file.
2. **`engine/gateway/pint_audit.py`, `engine/tests/test_pint_unit_gate.py` - unmeasurable**:
   pint 0.26.1 needs Python >= 3.12 (pyproject says so) while `[tool.mypy]` pins
   `python_version = "3.11"`; the fix is an environment/pyproject decision (upgrade the
   pin or install an older pint), not a source edit.
3. **`models/validation/**` (26), `models/biofertilizer/**` (61), `models/hdvi.py` (2),
   `models/hpheno.py` (5)** - owned by the validation-corpus agent.
4. **Documented-behaviour-change sites left as targeted ignores with one-line reasons**
   (each corrected would change runtime behaviour, which the task forbids):
   `assess_yield_risk(total_revenue=...)` wrong kwargs in
   `scenario_composite/engine.py` (the call always raises and the except path records it),
   `MonsoonScenario(seed=...)` / `DroughtScenario(..., seed=...)` in
   `simulation_env/stress.py` (the scenario classes have no seed field; the seed belongs on
   the `simulate_*` call), the `SWATPlusOutputs` call that omits three DataFrame fields,
   `examples/calibrate_rusle_example.py:_run_rusle` missing `scenario`, `dss.py`'s
   `_Integerize` returning None against its `str` signature, `nn.Sin` (torch has no such
   layer) in `pinn.py`, and the `ResultProvenance()` / `MonthlyClimate` / `SoilLayer` /
   `DeepSoilProfile` / `SoilIntegrationResult` constructor calls that rely on pydantic
   `Field(None)` defaults mypy cannot see (same treatment as the existing
   `test_s15_provenance.py` precedent).
5. **ruff UP042 (5)**: `class X(str, Enum)` to `StrEnum` changes `str(member)` and
   therefore json serialization - left, same decision as the services agent made for the
   5 in `services/**`.
6. **ruff E501 (175)**: line-length rewrapping is not provably behaviour-preserving;
   untouched, same policy as the services agent.
7. **ruff F401 (49)**: all `__init__.py` re-export style (ruff's own message suggests
   `__all__` or a redundant alias); removing them would shrink public API surfaces.
8. **ruff E402 (1)**: `engine/test_connector.py`'s `from engine.data_connector import
   connector` is deliberately after `sys.path.insert(PROJECT_ROOT)`; it now carries an
   explanatory comment instead of a move.

---

# 2026-10-10 — biofertilizer + validation-corpus mypy block (94 errors → 0)

Scope (only these files touched): `engine/hydroma/biofertilizer/**`
(`repositories.py`, `advanced_calculator.py`, `models.py`, `services.py`, `calculator.py`,
`trials.py`, `tests/test_material_reference_integrity.py`),
`engine/hydroma/models/validation/{runner,loader}.py`, `engine/hydroma/models/hpheno.py`,
`engine/hydroma/models/hdvi.py`. Out of scope and untouched: `engine/gateway/**`,
`engine/models/**`, `services/**`, `database/**`, `tools/**`, `pyproject.toml`.

## Baseline → final

`python -m mypy engine --ignore-missing-imports` from `D:\HyDroMA`
(`$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"`), measured before any edit and again at the end:

| | errors |
|---|---|
| repo baseline (session start) | **276** in 12 files |
| this block, before | **94** (11 files) |
| this block, after | **0** |
| repo final | **30** in 1 file (`engine/gateway/__init__.py`, out of scope) |

## Per-file before → after

| File | Before | After |
|---|---|---|
| `engine/hydroma/biofertilizer/repositories.py` | 18 | 0 |
| `engine/hydroma/models/validation/runner.py` | 23 | 0 |
| `engine/hydroma/biofertilizer/advanced_calculator.py` | 14 | 0 |
| `engine/hydroma/biofertilizer/models.py` | 12 | 0 |
| `engine/hydroma/biofertilizer/tests/test_material_reference_integrity.py` | 7 | 0 |
| `engine/hydroma/biofertilizer/services.py` | 6 | 0 |
| `engine/hydroma/models/hpheno.py` | 5 | 0 |
| `engine/hydroma/biofertilizer/calculator.py` | 4 | 0 |
| `engine/hydroma/models/validation/loader.py` | 2 | 0 |
| `engine/hydroma/models/hdvi.py` | 2 | 0 |
| `engine/hydroma/biofertilizer/trials.py` | 1 | 0 |
| **Total** | **94** | **0** |

## Techniques, per file

### `biofertilizer/repositories.py` (18 → 0)

* **14 × `no-any-return`** — `QueryPort.first()` in `engine/ports/session.py` returns `Any`
  by design (the port is ORM-agnostic), so `return session.query(M).filter(...).first()`
  leaked `Any` through a `M | None` signature. Each site now binds an explicitly typed
  local first (`strain: NojinStrain | None = query.first(); return strain`). No cast, no
  ignore, no behaviour change.
* **3 × `assignment`** — `strain.updated_at = datetime.now()`: mypy sees the mapped class
  attribute as the `Column[DateTime]` descriptor, not a `datetime`. The general fix is the
  SQLAlchemy mypy plugin (`plugins = sqlalchemy.ext.mypy.plugin`), which `pyproject.toml`
  does not load and which this task may not edit, so each site carries a one-line
  `# type: ignore[assignment]` and the reason on the preceding line.
* **1 × `var-annotated`** — `composition = recipe.material_composition or {}` now reads
  `cast("dict[str, Any]", ...)`, because a JSON column only gives mypy a `Column` descriptor
  and the rest of the function (`.items()`) needs the payload type.

### `models/validation/runner.py` (23 → 0)

* **16 × `union-attr`** — `case.expected` (9 sites across `_run_hargreaves` and
  `_run_penman_monteith`) and `case.tolerances` (6 sites across `_run_scs_cn`,
  `_run_runoff`, `_run_class_model`) are `dict[str, Any] | None` on `ValidationCase`, and the
  checkers read them directly. Fixed with the binding idiom the file already uses ~20 times
  (`i: dict[str, Any] = case.inputs or {}` and
  `expected: dict[str, Any] = case.expected if isinstance(case.expected, dict) else {}`),
  plus `tol: dict[str, Any] = case.tolerances or {}` for the tolerance maps. No assertion,
  cast or ignore was needed, and the codebase's own documented rule for this runner — a case
  it cannot settle is reported `not_run`, never raised — is what the binding implements.
* **1 × `union-attr`** — `o.status.upper()` in `report()`, on `Status | None`
  (`counts[o.status] = ...` in `summary()` is the `index` twin): both `cast(str, ...)`.
* **2 × `arg-type`** — two `RunoffInput(method=str(...))` call sites, where the field is a
  `Literal["SCS-CN", "Rational"]` fed a plain `str`. `cast(MethodType, ...)` with the type
  imported next to the existing `RunoffCalculator, RunoffInput` import. The corpus supplies
  `"SCS-CN"`, which is a valid member, so the value passed is unchanged.
* **1 × `arg-type`** — `design_check_dam(**forwarded)`: `forwarded` was inferred
  `dict[str, float | Any]`, which mypy will not splat against `float`/`int` parameters.
  Annotating `call`/`forwarded` as `dict[str, Any]` fixes it (the values, and the
  `accepted`-parameter filtering, are unchanged).
* **1 × `no-redef`** — `threshold: float | None = _bound(want)` inside a loop, in a function
  that already binds `threshold = 0.01 * h_left` earlier. The loop-local was renamed
  `bound`, matching the three sibling sites (`_bound` loops in the same file) that never
  conflicted.
* **2 × `dict-item` / `union-attr` on `o.status`** — `summary()` and `report()` index/format
  `CaseOutcome.status`, which is `Status | None`. Both use `cast(str, ...)`; the value is
  unchanged (every construction site passes one of the four literal statuses).

### `biofertilizer/advanced_calculator.py` (14 → 0)

* **4 × `arg-type`** — `materials_kg: dict[str, float] = {}` (the values are int literals, so
  mypy inferred `dict[str, int]`, which is invariant and incompatible with every
  `dict[str, float]` parameter of `_calculate_nutrients` / `_estimate_om_increase` /
  `_estimate_water_saving` / `_calculate_cost`).
* **8 × `assignment`** — three integer-initialised accumulators that later take float
  contributions (`dnpv`, `improvement`, `total_kg`) now start at `0.0`, so the
  `-=` / `+=` / `=` assignments after them are float-typed; and three `ScaleResult` fields
  (`logistics_notes`, `labor_requirements`, `equipment_needed`) that declared `= None`
  defaults on non-Optional types are widened to `T | None = None`. Type-level only: the
  defaults and the runtime values are identical.
* **1 × `no-any-return`** — `total_om: float = sum(...)` (the generator over
  `self.materials.get(...)` was `Any`).
* **1 × `attr-defined`** — see "Errors left", below.

### `biofertilizer/models.py` (12 → 0)

* **1 × `misc`** — the either-or `Base` fallback; see "Errors left".
* **11 × `misc`** — `DeclarativeBase` declares `__table_args__` as a *bare instance
  attribute* (`__table_args__: Any` in `sqlalchemy/orm/decl_api.py`), so a `ClassVar`
  declaration in a subclass is an override of an instance variable with a class variable,
  which mypy rejects. All 11 `__table_args__: ClassVar[dict[str, bool]]` declarations are now
  plain `__table_args__: dict[str, bool]`, which matches the base declaration.

  mypy's usual escape — the sqlalchemy mypy plugin (`plugins = sqlalchemy.ext.mypy.plugin`,
  which absorbs `__table_args__`/`__tablename__` from the check) — lives in `pyproject.toml`
  and is out of scope, so this alignment is the fix. It is **annotation-only**: the dict
  value, the `{"extend_existing": True}` behaviour and SQLAlchemy's class-dict lookup are all
  unchanged — verified at runtime after the edit (`Base` still resolves to
  `database.base.Base`, 12 tables, `NojinStrain.__table_args__ == {"extend_existing": True}`).
  The reasoning is recorded in a five-line comment above Phase 1 so the annotation is not
  "corrected" back to `ClassVar`; the now-unused `ClassVar` import was dropped to keep
  ruff's F401 clean.

### `biofertilizer/calculator.py` (4 → 0)

* **1 × `call-overload`** — `round(synergy_score, 1)`: the product of `np.mean(...)` (whose
  stub returns `np.floating[Any] | np.complexfloating | np.timedelta64`) and a float is wider
  than anything `round` resolves. `avg_efficacy = cast(float, np.mean(...))` fixes it at the
  one place the wide union is created (a behavioural reason, not just typing: the value stays
  `np.float64`-valued math, only its static type is restated).
* **1 × `type-var`** — `sorted([strain1.strain_type, strain2.strain_type])`, where
  `StrainType | None`'s `None` member is wider than typeshed's `SupportsRichComparisonT`.
  The list is now built as a typed local (`strain_types: list[Any] = [...]`), which keeps the
  exact same objects and the same ordering. A `key=str` rewrite was rejected: for a `StrEnum`
  it would have changed the `STRAIN_SYNERGY` lookup key order.
* **2 × `no-any-return`** — `return strains[0].efficacy_score, "good"`, where the profile field
  is `float | None`, and `round(dosage, 2)`, where `dosage` was `Any` through an untyped
  `CROP_FACTORS` entry. The first is `cast(float, ...)` (any default such as `or 50.0` would
  invent a number the model does not compute); the second is `crop_factor: float = ...`.

### `biofertilizer/services.py` (6 → 0)

* **1 × `arg-type`** — `FormulationType(formulation.formulation_type)` on a `String`-valued
  column → `FormulationType(str(...))` (an identity for a `str`, and gives mypy a `str`).
* **2 × `call-overload`** — `max(0, 100 - variance)` / `min(100, ...)`: `np.var` yields a
  numpy scalar, so the two literals have no single type variable.
  `variance = cast(float, np.var(...))` fixes both, and its value feeds `quality_score`.
* **2 × `arg-type`** — `np.mean` / `np.std` on `yield_responses`, inferred
  `list[object | Any]` from the `dict` literal that `trial_results` holds. Fixed at the source
  with `trial_results: list[dict[str, Any]] = []` (the records are the heterogeneous payload
  written two lines above).
* **1 × `operator`** — `(n_reduction_kg_ha + p_reduction_kg_ha) * 1.5`, where the left operand
  is `float | None`: `cast(float, ...)` with a comment pointing at `NojinResult`'s
  Optional-field envelope (`_predict_nitrogen_fixation` returns a plain `float`).

### `biofertilizer/trials.py` (1 → 0)

* **1 × `operator`** — see "Errors left".

### `biofertilizer/tests/test_material_reference_integrity.py` (7 → 0)

Test file: no assertion, no expected value and no `parametrize` set was changed. The
diagnostics were `no-any-return` (1), `arg-type` (1), `operator` (1), `type-var` (1) and
`misc` (3).

* `composition_of()`'s ternary became an `if`/`return` whose result is `cast` to the
  declared `dict[str, float]` (identical values; the function had been returning
  `json.loads(...)`'s `Any`).
* `derivable_cn_rows()`: `cast(float, carbon) / cast(float, nitrogen)` for the `object`-typed
  `dict.get` results (the `None`/falsy guard that runs before them is unchanged).
* `known: frozenset[str] = CODES` was fine — the fix was on `CODES`, which is built from the
  `object`-valued catalogue rows: `frozenset(cast(str, m["material_code"]) for m in MATERIALS)`.
* `ratio_derivable_but_unstated()` and the three `@pytest.mark.parametrize(..., ids=...)`
  lists: `cast(str, ...)` on the `object`-valued catalogue codes. The three decorators were
  re-wrapped one-argument-per-line to stay under ruff's 100-char limit, so **no new E501**.
* The data module ships plain `dict` rows (`MATERIALS = [{...}, ...]`), which is why every
  value widens to `object`; a comment now says so.

### `models/validation/loader.py` (2 → 0)

* **1 × `no-any-return`** — `load_reference()` returns
  `cast(np.ndarray, np.load(path).ravel())` (`np.load`'s stub is `Any`).
* **1 × `type-var`** — `corpus_summary()`'s `claimed_status` map sorts a `set[str | None]`:
  the `sorted()` result is now `cast("list[str]", ...)`. A `key=str` rewrite was rejected
  because it would have changed the ordering of the status names.

### `models/hpheno.py` (5 → 0)

* **2 × `override`** on `validate_inputs` / `compute`, exactly as the sibling models in this
  package already do (`ecsi.py`, `epia.py`, `esri.py`, `ewsi.py`, `hlhs.py`, `hyrue.py` all
  carry the same `# type: ignore[override]` plus the same three-line reason): the
  `ScientificModel` ABC declares `**inputs` / dict signatures while the concrete model API is
  positional. Unifying them is a cross-hierarchy API decision, so the divergence is marked
  rather than rewritten.
* **2 × `no-any-return`** — `np.linalg.pinv(a)[0]` and `np.gradient(...)` return `Any`
  (numpy's stubs leave the shape open); both are now `cast(np.ndarray, ...)`.
* **1 × `operator`** — `(eos_date - sos_date).days` on two `date | None` locals narrowed only
  through the boolean `los_is_meaningful`, which mypy does not track. The `if` now restates
  the two None checks alongside that flag, which is logically implied by it (so the runtime
  behaviour is unchanged) and gives mypy the narrowing.

### `models/hdvi.py` (2 → 0)

The same two `override` sites, with the same reason and the same wording as its siblings.

## Errors left (documented, 10 ignores total — no module-level ignore)

Ten per-site `# type: ignore` remain, each with a one-line reason on the same or preceding
line. Each one marks a site where the *correct* fix would change runtime behaviour, which
the task forbids:

1. `biofertilizer/models.py:44` — `[misc]` for the either-or `Base` fallback. The name is
   bound by an import in one branch and re-assigned a `declarative_base()` value in the
   other; mypy models the imported name as a single class object and structurally cannot
   represent a union of two base classes. Workarounds were probed and all rejected:
   `import ... as` re-binding, `cast(type, ...)`, `find_spec` gating, and aliasing to a
   `type[Any]` variable all either keep the error or change the import structure.
2. `biofertilizer/advanced_calculator.py:246` — `[attr-defined]`,
   `FormulationOptimizer._greedy_optimize` calling `self._estimate_water_saving(...)`.
   **This is a real latent `AttributeError`, not a typing quirk** (proven at runtime: calling
   `optimize()` for a soil with no pre-built recipe raises
   `AttributeError: 'FormulationOptimizer' object has no attribute '_estimate_water_saving'`;
   `the method truly lives on `CostBenefitCalculator:839`). Copying or moving that method
   would change runtime behaviour, so the defect is reported, not silently "fixed" — no
   current corpus case or test reaches this branch, so the error is latent rather than
   observed.
3. `biofertilizer/trials.py:143` — `[operator]`,
   `calculate_soil_health_index(...) - calculate_soil_health_index(...)`.
   **Also a real latent `TypeError`**: the function returns a `dict`, so the subtraction
   raises `TypeError: unsupported operand type(s) for -: 'dict' and 'dict'` (probe-verified).
   Fixing it (indexing `["overall_score"]`) would change behaviour, so it is marked and
   reported here instead.
4. `biofertilizer/repositories.py:120, 218, 617` — `[assignment]` on three
   `updated_at = datetime.now()` writes to a mapped class attribute. The real fix is the
   sqlalchemy mypy plugin, which lives in `pyproject.toml` (out of scope). reason recorded
   inline on each site.
5. `biofertilizer/calculator.py` — none left (the Optional `efficacy_score` is `cast`, not
   ignored).
6. `models/hpheno.py:72, 225` and `models/hdvi.py:64, 176` — `[override]`, four sites with
   the existing three-line reason copied verbatim from the six sibling models that already
   use it. Unifying the `ScientificModel` ABC's `**inputs` signatures with the concrete
   positional APIs is an API decision, not a mechanical fix.

Total: 10 ignores for 94 errors; the other 84 errors were fixed by annotation, typed
locals or a documented `cast`.

## Verification

1. **`python -m mypy engine --ignore-missing-imports`** — 276 errors / 12 files → **30 errors /
   1 file** at the end. The remaining 30 are all in `engine/gateway/__init__.py`, which is
   out of scope for this task (the `[arg-type]` family; they were 171 in the previous
   session's report and have since been reduced by other work). This block's 11 files: **0**.
2. **`python -c "from engine.hydroma.models.validation import runner as R; print(R.summary(R.run_all()))"`**
   — run after every `runner.py` batch and at the end:
   **`{'match': 61, 'mismatch': 0, 'inconsistent_case': 17, 'not_run': 17, 'total': 95}`**, i.e.
   the pinned corpus distribution is unchanged (61 / 0 / 17 / 17).
3. **`python -m pytest engine/tests/test_validation_corpus.py engine/tests/test_validation_corpus_completion.py -q`**
   — **36 passed, 0 failed** (315s).
4. **`python -m pytest engine/hydroma -q --ignore=engine/hydroma/models/validation`** —
   **386 passed, 2 skipped, 2 xfailed, 0 failed**.
5. **`python -m pytest engine/hydroma/biofertilizer engine/hydroma/models -q`** —
   **87 passed, 2 skipped, 0 failed**.
6. **`python -m pytest engine/ -q -p no:cacheprovider`** — **2559 passed, 30 skipped,
   42 xfailed, 0 failed** (646s) — identical to the baseline stated in the task brief
   (2559 passed / 0 failed), so nothing regressed.
7. **`python -m ruff check`** on every changed file — clean, except the pre-existing
   E501s listed in the 2026-10-09 section (`calculator.py:726`, `models.py:6`,
   `calibration.py:170`, `validation/__init__.py` F401 re-exports). **No new E501** was
   introduced: the three `parametrize` lines my casts had lengthened were re-wrapped
   immediately.
8. Runtime probes for the changed modules (not assumptions): `Base` still resolves to
   `database.base.Base` and still has 12 tables; `NojinStrain.__table_args__` is still
   `{"extend_existing": True}`; `FormulationOptimizer`'s greedy path still raises the same
   `AttributeError` as before the edit; `runner.report()` still prints 190 lines with the
   same status labels; `loader.corpus_summary()`/`reference_metadata()` unchanged.
9. `git diff` reviewed file by file — only this block's edits are present. (A stray BOM
   introduced by one shell write was removed before finishing.) One accidental edit was
   caught this way: a re-wrap of `trials.py`'s second `calculate_soil_health_index` call had
   changed `baseline.get` to `post_data.get` for two keyword arguments; it was restored to
   the original `baseline.get` immediately.

## Concurrency note

`biofertilizer/models.py`, `validation/runner.py`, `biofertilizer/tests/conftest.py`, the
validation `test_cases/*.yaml` files and several `repository.py` test files already had
uncommitted working-tree changes from other agents when this session started. Those were
left strictly alone — the diffs above contain only this block's edits.


# Services + database + adapters mypy block — 2026-10-10

## Scope

Eliminate the mypy errors in the services + database + adapters block:

| File | Baseline | Final | Delta |
|---|---|---|---|
| `services/_gateway_facade.py` | 10 | **0** | -10 |
| `services/__init__.py` | 10 | **0** | -10 |
| `services/satellite/service.py` | 6 | **0** | -6 |
| `services/privacy/vault.py` | 5 | **0** | -5 |
| `services/oracle/service.py` | 4 | **0** | -4 |
| `services/ecosystem/service.py` | 3 | **0** | -3 |
| `database/models.py` | 3 | **0** | -3 |
| `services/models/__init__.py` | 1 | **0** | -1 |
| `adapters/hydroma_adapter.py` | 1 | **0** | -1 |
| **Total (this block)** | **43** | **0** | **-43** |

Measurement (block was verified independently of the engine-scoped command, which
does not list these paths in this environment):

```
python -m mypy services/_gateway_facade.py services/__init__.py \
  services/satellite/service.py services/privacy/vault.py services/oracle/service.py \
  services/ecosystem/service.py services/models/__init__.py database/models.py \
  adapters/hydroma_adapter.py --ignore-missing-imports --no-incremental --no-error-summary
# before: 43 errors in 9 files   # after: no output (0 errors)
```

38 of the 43 were fixed with real typing fixes; the remaining 5 error codes at 11
sites carry per-site `# type: ignore[<code>]` with a one-line reason. No module-level
ignore, no blanket ignore, no runtime behaviour change, no test weakened.

## Fixes per file

### `services/models/__init__.py` (1 → 0)

* **1 → `var-annotated`** — `__all__ = []` cannot be inferred from an empty literal.
  Now `__all__: list[str] = []`. Re-export hygiene only; `__all__` is still `[]` at
  runtime.

### `services/ecosystem/service.py` (3 → 0)

* **1 → `var-annotated`** — `self._privacy_vault = {}` → 
  `self._privacy_vault: dict[str, ActivityEvidence] = {}`. The value type is the class
  this module owns (`ActivityEvidence`), which also pinned down error #3 for free.
* **1 → `arg-type`** — `get_user_activities(self, user_id: str, status: VerificationStatus = None)`
  → `status: VerificationStatus | None = None`. The parameter was already Optional by
  usage; the file has `from __future__ import annotations`, so the union annotation is
  string-only and runtime-inert.
* **1 → `no-any-return`** (bonus, fixed by the first annotation) — `get_evidence()` returns
  `self._privacy_vault.get(entry_id)` behind a `if not evidence: return None` guard. With
  the dict annotated, `.get()` returns `ActivityEvidence | None` and the guard narrows it,
  so the plain `return evidence` type-checks. No cast, no ignore.

### `services/oracle/service.py` (4 → 0)

* **3 → `var-annotated`** — `registered_nodes`, `_pending_reports` and `_challenges` were
  bare `{}` literals. All three are heterogeneous id → payload maps that are only ever
  written and iterated, so `dict[str, dict[str, Any]]` is the honest type (and
  `typing.Any` was added to the import list, used only by those annotations).
* **1 → `attr-defined`** — see "Errors left", #5.

### `services/satellite/service.py` (6 → 0)

* **2 → `assignment`** — `self.token = None` / `self.token_expiry = None` made mypy infer
  `None` for both, so every later `self.token = <str>` / `token_expiry = <datetime>` was an
  error. Now `self.token: str | None = None` and `self.token_expiry: datetime | None = None`.
* **1 → `operator`** — in `authenticate()`, `data` was first bound to the OAuth *form*
  body (`dict[str, str]`) and then rebound to `resp.json()`, so `data["expires_in"] - 60`
  was `str - int`. The response variable is renamed `payload` and the form body keeps the
  name `data`; the request body sent on the wire is untouched.
* **2 → `var-annotated`** — the conditional `headers = {...} if self.token else {}` headers
  in `search_sentinel2()` and `fetch_sentinel2_bands()` are now `headers: dict[str, str]`.
* **1 → `arg-type`** — `session.get(..., params=params, ...)`: the `$top` entry made the
  literal `dict[str, object]`, which aiohttp's `QueryType` rejects. `params: dict[str, str | int]`
  is inside `QueryType`, so no cast and no behaviour change.
* **1 → `no-any-return`** — `search_sentinel2()` returned `data.get("value", [])` straight
  out of `resp.json()`. Now `payload: dict[str, Any] = await resp.json()` and
  `value: list[dict[str, Any]] = payload.get("value", [])` are bound first, so the same
  list object is returned.

### `services/privacy/vault.py` (5 → 0, 1 ignore left)

* **1 → `var-annotated`** — `self._index = {}` → `self._index: dict[str, dict[str, Any]] = {}`.
* **1 → `attr-defined`** — see "Errors left", #4.
* **3 → `no-any-return`** — `retrieve()` returned `json.loads(plaintext)` (typed `dict | None`),
  `verify_commitment()` returned the `entry["commitment_hash"] == commitment` comparison and
  `get_commitment()` returned `entry["commitment_hash"]`, all out of `json.loads(...)`'s `Any`.
  All three are now typed local bindings (`payload: dict[str, Any] = ...` /
  `entry: dict[str, Any] = ...` / `matches: bool = ...` / `commitment: str = ...`) returned
  unchanged. **No cryptographic call was touched** — not the Fernet construction, the
  base64 decode, the SHA-256 hashing, `secrets.token_urlsafe`, nor the access-control and
  access-log blocks. Only the typing around the `json.loads` results changed.

### `database/models.py` (3 → 0)

* **1 → `var-annotated`** — `state = Column(Enum(CarbonCreditState), ...)`. SQLAlchemy's
  `Enum.__init__` takes `*enums`, so its type parameter is inferred as `Never` and mypy
  asks for an annotation. Now `state: Column[CarbonCreditState] = Column(...)`.
  Verified annotation-only at runtime: the compiled PostgreSQL DDL for `carbon_credits` is
  byte-identical with and without the annotation (`state carboncreditstate NOT NULL`),
  the enum is still `['DRAFT','SUBMITTED','VERIFIED','ACTIVE','RETIRED']`, and the mapper
  still registers the column. Typing `Column[CarbonCreditState]` is also what the sibling
  `Inv*` models in the same file already express for their numeric columns.
* **1 → `return-value`** — `InvInventoryBalance.available` returned `self.on_hand - self.reserved`,
  typed `ColumnElement[Decimal]`: SQLAlchemy's `Numeric` subclasses both `decimal.Decimal`
  and `ColumnOperators`, and mypy resolves `__sub__` to the operator overload. Now
  `cast("Decimal", self.on_hand - self.reserved)`. Both operands are Decimals at runtime —
  probe-verified `Decimal("10.5") - Decimal("2.25") == Decimal("8.25")`, type `Decimal`.
* **1 → `return-value`** — `PasswordResetToken.is_valid` returned
  `expires >= _datetime.now(_UTC)`, typed `ColumnElement[bool]` for the same reason
  (`DateTime` also carries `ColumnOperators`). Now `bool(expires >= ...)`, which is the
  same object for a bool. Probe-verified all four branches: naive-future `True`,
  utc-future `True`, utc-past `False`, `used=True` `False` — identical to before.

### `adapters/hydroma_adapter.py` (1 → 0)

* **1 → `call-arg`** — `GroundwaterInput(...)` in the CDSE→Theis fallback omitted
  `model_type`, which pydantic's synthesized `__init__` requires statically even though it
  has a `Field` default. The literal is spelled out as `model_type="analytical"` — exactly
  `GroundwaterInput.model_fields["model_type"].default` — so the constructed model is
  identical; the literal is not a duplicated default that can drift.

### `services/__init__.py` (10 → 0, 5 ignores)

* **5 → `misc` + 5 → `assignment` (one pair per re-exported name)** — the module's two
  optional-dependency `try/except ImportError` blocks rebind `DataSource`, `OracleService`,
  `PrivacyVault`, `SatelliteService` and `SatelliteSource` to `None` in the except arm.
  mypy binds the try-arm symbol to the class type, so `Name = None` is rejected twice
  ("Cannot assign to a type" plus an incompatible `type[...]` assignment).

  Re-export hygiene was probed first, as the task asked: `__all__` already lists all nine
  public names, and adding `TYPE_CHECKING`-plus-`try` re-import pairs, `X as X` form,
  annotating the except arm (`X: type[X] | None = None`) and an explicit `Column`-style
  parametrisation were each tested — the first three do not clear the errors, the fourth
  turns them into `no-redef`. The remaining options that do clear them
  (`globals().update(...)`, a module `__getattr__`, or a `_load()` helper returning a
  tuple) each change *when* the optional import happens, i.e. runtime behaviour, which is
  out of scope for a lint pass.

  So each site now carries `# type: ignore[assignment, misc]` (both codes, since mypy
  reports both on the same line) with a four-line reason above the block. The `try/except`
  itself — the only thing that decides whether `services.PrivacyVault` is a class or
  `None` — is byte-identical to before.

### `services/_gateway_facade.py` (10 → 0, 4 ignores)

* **5 → `no-any-return`** — `classify_texture()` (`result.get("texture_class", "unknown")`),
  `hargreaves_et0()` (`result["data"]["et0_mm_day"]`), `calculate_mix_cn_ratio()`
  (`.get("cn_ratio", 0.0)`), `temp_factor()` (`result.get("value", 0.0)`) and
  `estimate_rainfall_erosivity()` (the untyped engine kernel `estimate_r_factor`). Each is
  now an explicitly typed local returned in place of the `Any` value; the objects
  themselves are unchanged.
* **1 → `no-any-return`** — `GroundwaterService.analyze()` returned
  `self._model.simulate(...)`, which mypy saw as `Any` because `GroundwaterService.__init__`
  had no annotations, so mypy skipped its body and never inferred `self._model`.
  Probe-verified with `reveal_type`: adding `-> None` turns the method into a checked one
  without any other change, which makes `self._model` resolve to `GroundwaterModel` and
  `analyze`'s return value `dict[str, Any]`. `def __init__(self) -> None:` is the whole fix.
* **4 → `attr-defined` / `no-redef`** — see "Errors left", #1–#3.

## Errors left (11 ignore sites for 43 errors; no module-level ignore)

Each marks a site where the *correct* fix would change runtime behaviour, which the task
forbids. Every one has a one-line reason comment.

1. **`services/_gateway_facade.py:880` → `[attr-defined]`** —
   `from engine.hydroma.cpp_bridge import hydroma_core` inside `is_cpp_available()`.
   The submodule is registered *dynamically*: `cpp_bridge/__init__.py:70` does
   `sys.modules.setdefault(__name__ + ".hydroma_core", _hydroma_core)` after a guarded
   `importlib.import_module`, so the name is not visible to static analysis. The `except`
   arm catches `(ImportError, Exception)`, so the probe is already behaviour-agnostic to the
   failure mode. Substitutes were rejected: `getattr(cpp_bridge, "hydroma_core")` is not the
   same runtime lookup (CPython's `IMPORT_FROM` falls back to `sys.modules`, `getattr` does
   not), and `importlib.import_module("engine.hydroma.cpp_bridge.hydroma_core")` changes the
   import mechanism.
2. **`services/_gateway_facade.py:1135` → `[no-redef]`** (`MRVMetrics`, first defined at
   line 901). **3. `services/_gateway_facade.py:1162` → `[no-redef]`** (`compute_erosion`,
   first at 953). **4. `services/_gateway_facade.py:1180` → `[no-redef]`** (`apply_scenario`,
   first at 966). All three are *deliberate* shadowing: the later definition is the one
   that wins, and it is the one every consumer imports. Verified by exhaustive repo grep
   (no `__pycache__`/cache dirs): `routers/soil.py:635-637` calls
   `compute_erosion(slope_length_m, slope_percent, annual_rainfall_mm, texture, c_factor,
   p_factor)` — the 1162 signature; `models/registry.py:32,445` imports the same name for a
   `ParamSpec` with those six parameters; `routers/scenarios.py:37` calls
   `_apply_scenario(req.scenario, {...})` — the 1180 signature; and
   `scientific_motors/carbon_sequestration.py:63,172,364` only instantiates `MRVMetrics` and
   asks `is not None`, which both class objects answer identically. The earlier definitions
   are therefore unreachable. Renaming or deleting either definition would change which
   object the public name resolves to — exactly the behaviour the task forbids — so the
   documented shadowing is marked instead. This is the same pattern the file already
   documents for `ChainInput` / `compare_crop` / `calculate_financial_metric` at lines
   1266-1278.
5. **`services/oracle/service.py:193` → `[attr-defined]`** —
   `if metrics.confidence == 0:` in `finalize_impact_metrics()`.
   `_compute_aggregated_metrics()` returns a plain `dict`, so `metrics.confidence` is a
   **real latent `AttributeError`** (probe-checked: the method body returns
   `{"data_completeness": 0.4, "sensor_confidence": 0.85, "challenge_deadline": 0}` at
   lines 183-187, with no `confidence` key). Changing it to `metrics["confidence"]` (or
   `metrics.get("confidence", 0)`) would turn this placeholder path from "always raises" into
   "sometimes returns `None`", which is a behaviour change. No test reaches
   `finalize_impact_metrics` (grep-verified), so the defect is latent. Same rationale as
   `biofertilizer/advanced_calculator.py:246` in the 2026-10-09 section.
6. **`services/privacy/vault.py:53` → `[attr-defined]`** — `self._load_index()` in
   `PrivacyVault.__init__`. **The method does not exist on the class** (grep-verified: no
   `_load_index` definition anywhere in the repo), so constructing a `PrivacyVault` raises
   `AttributeError` before any key material touches disk. Defining the method (or removing
   the call) would change that construction behaviour. `PrivacyVault` is not constructed by
   any test — only imported for typing, by `services/privacy/__init__.py`,
   `services/__init__.py` and `services/oracle/service.py` — so the defect is latent.
   Per the security-sensitive rule, only the typing is touched and the defect is reported,
   not "fixed".

## Verification

1. **Block mypy** — `python -m mypy <9 files> --ignore-missing-imports --no-error-summary
   --no-incremental` → **no output (0 errors)**; baseline was 43 errors in the same 9 files.
   Run after every batch of edits, not only at the end.
2. **`python -m mypy engine --ignore-missing-imports`** → session-start (before any edit,
   matching the task's stated baseline) **276 errors / 12 files** → final **30 errors / 1
   file**, all 30 in `engine/gateway/__init__.py`. That is the same endpoint the 2026-10-09
   report recorded, and it is *not* attributable to this block: re-checked by temporarily
   reverting only this block's edits (see the incident note below), the count is still
   **30 / 1 file** with the block's fixes removed. The session-start 276 came from the
   pre-existing `.mypy_cache` and is reproduced to **30** as soon as the cache is rebuilt
   (also true with `--no-incremental`, i.e. without any cache at all). This block's 9 files
   contribute **0** of the remaining 30.
3. **`python -m pytest services/ -q -p no:cacheprovider`** → **1065 passed, 9 skipped,
   0 failed** (578s). An earlier mid-session `-x` run reported one failure
   (`services/finance/tests/test_bank_transfer_registration.py::
   test_failed_transaction_does_not_poison_the_provider`) which **passes in isolation**
   (3/3 consecutive runs of the file) and does not reproduce in the full run; the documented
   marketplace/commerce order-dependence does not appear at all in the final full run.
4. **`python tools/detect_imports.py --root .`** → **PASS, 0 violations** (1146 files
   scanned, 261 directories, 8 rules) — services still reach the engine only through
   `services/_gateway_facade.py` and `api_gateway/routers/hydroma_common.py`.
5. **`python -m ruff check <9 files>`** → 8 findings, all pre-existing; the same 8 are
   present with this block's edits reverted (line numbers shift by the added comments):
   `adapters/hydroma_adapter.py:88` F841 `t_mean`; `services/_gateway_facade.py:880` F401
   `hydroma_core`; `:1071` E501; `:1135/1162/1180` F811 redefinitions;
   `services/models/__init__.py:4` E501; `services/satellite/service.py:158` E501.
   One **new** E501 *was* introduced (annotating `oracle/service.py`'s `registered_nodes`
   pushed its trailing comment to 108 chars); it was re-wrapped immediately (comment moved
   above the line) so the count returned to 8. **No new ruff error remains.**
6. **Runtime probes** (not assumptions) for every changed module — see the per-file notes
   above: DDL for `carbon_credits` identical with and without the annotation; `available`
   still `Decimal("8.25")`; all four `is_valid()` branches unchanged; all ten touched
   modules import cleanly (`services`, `services.models`, `services.ecosystem.service`,
   `services.oracle.service`, `services.satellite.service`, `services.privacy`,
   `services.privacy.vault`, `services._gateway_facade`, `database.models`,
   `adapters.hydroma_adapter`).
7. **Engine tests that touch this block** —
   `engine/strict_tests/test_s12_table_registration.py engine/tests/test_architecture_rules.py
   engine/tests/test_e2e_pipeline.py engine/strict_tests/test_s17_gateway_route_repair.py`
   → **111 passed, 0 failed** (25s). Covers the shared `database.models` registration, the
   architecture rules and the `services._gateway_facade` import path.
8. **Targeted service tests** — `services/finance/tests/test_bank_transfer_registration.py
   services/satellite/tests/test_integration.py services/tests/test_import_contracts.py
   services/scientific_motors/tests/test_registry.py
   services/validation/tests/test_s17_service_strict.py
   services/api_gateway/tests/test_bridge_mounts.py` → **88 passed, 1 skipped, 0 failed**
   (45s). Covers the satellite service, the model registry that imports
   `compute_erosion`, and the facade import contract.

## Concurrency note / incident report

The working tree carried **240 modified files of other agents' uncommitted work in
`services/`** (8546 insertions, 2741 deletions) plus 435 modified, 150 untracked paths
elsewhere when this session started. Two measurement mistakes were made during the session
and both were fully recovered; they are recorded because the recovery changed the tree.

1. **`git stash push -- services/` (for a baseline comparison).** At that moment the tree's
   in-flight work was not known to be stashed; a pristine-tree run then produced ~14
   collection `ERROR`s (`RuntimeError: Gateway error: Request validation failed`), which
   identified the experiment as invalid. `git stash pop` restored it immediately;
   `git apply --check --reverse` of the saved patch afterwards reported the 9 files match
   the pre-stash state exactly, and `git diff --stat -- services/` is back to 240 files /
   8546 insertions, i.e. the pre-existing work plus this block's edits. No file was lost.
2. **`git checkout -- <9 files>` (to measure the block's mypy impact).** This discarded the
   working-tree content of those 9 files, because it restores from the index. The content
   had been saved to a patch first, but PowerShell's `>` wrote that patch as **UTF-16 with
   CRLF line endings**, so `git apply` rejected it; the first recovery attempt ("no valid
   patches in input", then "patch does not apply") failed for that reason. The patch was
   re-read as UTF-16, re-written as UTF-8 and normalized to LF, after which `git apply`
   succeeded; a second recovery was verified with `git apply --check --reverse` (exit 0).
   The 9 files now match the saved patch exactly.

**Recovery verification (after both incidents):** `git apply --check --reverse` on the saved
patch exits 0, i.e. the 9 files are byte-identical to their pre-incident state; all 43
block fixes are present; the block mypy run is clean; `tools/detect_imports.py` is PASS; the
full `services/` suite is 1065 passed / 9 skipped / 0 failed. The only content difference
from before the incidents is cosmetic: `git` re-wrote line endings on some `services/`
files during the stash/pop, which is invisible to `git diff` under the repo's autocrlf
setting and behaviourally inert for Python.

Nothing outside the 9 allowed files was edited: no `engine/**`, no `tools/`, no
`pyproject.toml`, no `.github/**`.
