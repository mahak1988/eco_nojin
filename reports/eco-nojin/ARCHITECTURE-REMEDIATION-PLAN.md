# ARCHITECTURE REMEDIATION PLAN — per-category deficiency closures

Document id: `ECO-ARCH-REMEDIATION` · Date: 2026-10-11 · Companion to `ARCHITECTURE-DEFICIENCY-REVIEW.md`
Rule set: every item is (a) additive-first, (b) behaviour-preserving unless a mandate is recorded, (c) verified by a named command, (d) sequenced so no step depends on an uncommitted state.
Legends — **Class**: `ADD` (no mandate) · `DEC` (owner decision) · `MAN` (brake-taking, needs a recorded mandate). **Brake**: which SB/AR it touches.

---

# CATEGORY A — STRUCTURAL (shape of the code)

## A-1 · The 3,117-line gateway monolith · P1 · Class: MAN · Brake: SB-01, SB-03
**End state:** `engine/gateway/` is a package whose public surface is byte-identical, split into four modules with no module above ~1,200 lines.

| Step | Action | Why it is safe |
|---|---|---|
| 1 | Create `engine/gateway/contracts.py` and move `UnitSpec`, `InputSpec`, `ModelSpec`, `GatewayRequest`, `GatewayResult`, `ValidationResult`, `UncertaintySpec`, `ProvenanceSpec`, `GatewayError` and the export list | pure moves; `engine/gateway/__init__.py` re-exports every name it exported today (asserted by a test that diffs `__all__` before/after) |
| 2 | Create `engine/gateway/input_validator.py` for `_normalize_inputs`, `_route_float/_int/_str`, `REQUIRED_INPUTS` | same re-export; the two G-H20 repairs are already inside `_normalize_inputs`/`_route_float` |
| 3 | Create `engine/gateway/model_dispatcher.py` for the ~75-entry route table and `_dispatch_by_type` | the dispatch table is data; moving it changes no behaviour |
| 4 | Create `engine/gateway/unit_converter.py` wrapping `pint_audit` + `UnitSpec.si_equivalent` | the audit already exists and is not wired; wiring is a later mandate |
| 5 | `engine/gateway/__init__.py` becomes the façade: imports the four modules, keeps `EngineGateway` and every re-export | existing importers (`engine.hydroma.*`, `services/_gateway_facade.py`, tests) are untouched |
| 6 | Add `engine/tests/test_gateway_package_split.py`: (a) `__all__` equality with the recorded pre-split list, (b) each of the four modules' line count, (c) a smoke dispatch of CANON-001/004 and SOIL_AMENDMENT through the public path | the split is proven behaviour-preserving, not assumed |

**Done when:** steps 1–6 done, `pytest engine/ engine/strict_tests` green, no module in `engine/gateway/` over 1,200 lines, `git diff --stat` shows the file count within SB-01.

## A-2 · The two service God-objects · P1 · Class: MAN · Brake: SB-03
**End state:** `_gateway_facade.py` ≤ 600 lines; `inventory/service.py` and `hub_service.py` ≤ 800 each, split by cohesive concern, public functions re-exported.

| Step | Action | Verification |
|---|---|---|
| 1 | Extract the six engine-import exception sites into `services/_gateway_facade/adapters/{soil,climate,carbon,economics,groundwater,cpp}.py`, each a thin typed wrapper; the facade imports the adapters | the facade's public names unchanged (sampled by the existing service tests); guard still PASS (the policy keys move, the count does not) |
| 2 | Split `inventory/service.py` by read/write/segregation concerns into `inventory/{queries,commands,stock}.py` | `pytest services/inventory -q` green |
| 3 | Split `hub_service.py` into `marketplace/hub/{listings,matching,schedules}.py` | `pytest services/marketplace -q` green |
| 4 | Structure test: no module in `services/` newly exceeds 900 lines; the facade's own line count is asserted | `engine/tests/test_structure_ceilings.py` (ADD) |

## A-3 · No in-code boundary for the business layer · P1 · Class: DEC (policy) + ADD (test)
1. Add `services/__init__.py` package boundaries: each subpackage declares its public surface in `__all__`; a CI job (`tools/check_service_boundaries.py`, ADD) lists any cross-subpackage import that is not declared in an explicit allowlist.
2. Publish the allowlist as data (`tools/service_boundary_policy.json`) with the same expiry mechanism as B-1.
3. **Done:** CI job green, allowlist ≤ 20 edges, every edge has a rationale.

## A-4 · `engine/hydroma/` as a 250-module grab-bag · P1 · Class: ADD (shims) → MAN (moves)
1. Create the spec's directory mirror as **re-export shims**: `engine/indicators/`, `engine/knowledge/`, `engine/decision/`, `engine/scenario/`, `engine/numerical/` (each `__init__.py` re-exports today's modules). Zero behaviour change; the chain of §3.1 becomes navigable.
2. Migrate one family at a time behind a parity test: `spi_calculator`/`water_balance`/`water_productivity` → `engine/indicators/`; `models/{hdvi,epia,ewsi,esri,ecsi,hyrue,hlhs,hpheno}.py` → `engine/indicators/`; `evidence/`, `knowledge/` → the shim dirs.
3. **Done:** each migrated family has `pytest` parity before the old path is deprecated (keep a re-export for two releases).

## A-5 · Four-way test layout · P2 · Class: DEC
1. Decide: keep `engine/tests` + `engine/strict_tests` and declare them the canonical `unit`/`scientific`/`integration` homes in the constitution (cheapest), **or** create the spec's tree and move (MAN, SB-01).
2. Whichever is chosen: add `conftest.py` at the repo root `tests/` so the root tree is collected by the same config (currently only a best-effort CI step sees it).
3. **Done:** one `pytest` invocation collects every test file in the repo (`pytest --collect-only -q | tail -1` equals the sum of the four areas).

## A-6 · Five configuration homes · P2 · Class: MAN · Brake: SB-03
1. `engine/hydroma/config/settings.py` becomes the single `Settings`; `database/settings.py` and `runtime/services.yaml` become views over it (adapters, not owners).
2. Document precedence in one README block: env > runtime YAML > database settings > defaults.
3. **Done:** two objects instead of five, a test asserting both storage tiers read the same source.

---

# CATEGORY B — COUPLING & DEPENDENCIES

## B-1 · Guard green via 8 carve-outs, no ratchet · P1 · Class: ADD
1. Add `expires` (ISO date) + `ratchet` (max count) to `tools/import_guard_policy.json`, plus a re-check date on each `allowed_imports` entry.
2. `tools/check_policy_expiry.py` (ADD): fails when an exception is past `expires` or the count exceeds `ratchet`; add it as a CI step (non-blocking first, blocking after 2 clean weeks).
3. **Done:** policy carries dates; CI job exists; the 8 current exceptions all have `expires` ≤ 2027-01-31 and a named owner.

## B-2 · Engine → database coupling · P1 · Class: MAN · Brake: SB-07 (behaviour), SB-03
1. Move `engine/hydroma/biofertilizer/calibration.py`'s `SessionLocal` use behind the existing `PersistencePort`: inject a port at construction; the production wiring supplies the SQLite adapter (`adapters/persistence/sqlite_persistence.py`, spec-conformant, already tested).
2. Delete the `ENGINE_NO_DATABASE` exception for `database.config`/`database.base` only after the port injection is green.
3. **Done:** `pytest engine/hydroma/biofertilizer` green; the guard's engine rule reports the *unchanged* count with the two entries now `pending-removal`.

## B-3 · Ten duplicated scientific families · P1 · Class: MAN per family · Brake: SB-07
Sequence (each: parity test first, then delete-or-delegate, then update the divergence register):

| Order | Family | Canonical | Note |
|---|---|---|---|
| 1 | `es`/`Δ`/`γ`/`Ra` (6 copies) | `engine/hydroma/climate/et_calculator.py` | the 6th copy is in `scenario_composite/models_additions.py` |
| 2 | PM (2 copies, different equations) | `et_calculator.calc_et0_penman_monteith` | the `cpp_bridge` copy uses eq. 19 (`ea=es·rh`) — publish *which* equation is intended before converging |
| 3 | SCS-CN (5 copies) | `engine/hydroma/models/runoff_model.py` | the 4 services copies are algebraically equivalent; parity test pins them |
| 4 | LS (3 forms) | `erosion.cpp`/`wrapper.py` (AH-703) | `erosion_risk.py` needs a decision, not a merge |
| 5 | Theis (2) | `groundwater/models.py` | trivial |
| 6 | RothC (3) | `rothc_runner.py` | the two services ports differ structurally |
| 7 | eq. 52 (5, 3 wrong) | `et_calculator` | 3 already routed; 2 inline copies remain |
| 8 | NDVI (4) | `engine/hydroma/satellite/processors/indices.py` | — |
| 9 | K (6.8×) and R (2 forms) | decide the published source per family | a *decision*, then a merge |

**Done per family:** `EQUATION-DIVERGENCE-REGISTER.md` row reads `resolved: <canonical>` with the parity test named.

## B-4 · Services recomputing science · P2 · Class: ADD + MAN
1. `tools/find_inline_science.py` (ADD): regex/AST scan of `services/**` for the published formula skeletons (0.0023, 0.408, 25400/CN, 0.77·Rs, …) and report offenders.
2. Route each offender through the facade adapter (A-2 step 1).
3. **Done:** scan reports zero inline copies.

## B-5 · Three storage technologies · P2 · Class: DEC
1. Decision points: (a) is DuckDB retired or kept as the analytics reader? (b) is PostgreSQL the services tier only? (c) is GeoPackage required for spatial data?
2. Then: `engine/hydroma/data_connector.py` keeps a *documented reader* behind `HYDROMA_STORAGE_TIER` (already implemented); the alembic migrations get a note that they serve the services tier.
3. **Done:** one architecture diagram in the constitution; `DATABASE_URL` precedence documented; no reader outside its tier.

## B-6 · No dependency graph, no services→services rule · P2 · Class: ADD
1. `tools/dependency_graph.py` (ADD): emits `architecture/dependency-graph.md` (module → imports, per area) from AST, with a diff mode for CI.
2. `tools/check_service_boundaries.py` (A-3) uses the same graph.
3. **Done:** the graph exists as a CI artefact; the ECO-02 output `dependency_graph.md` is satisfied.

---

# CATEGORY C — PROCESS & OPERATIONS

## C-1 · 622 uncommitted changes edited live · P0 · Class: DEC
1. **Decision required**: branch strategy + who merges. Recommended: one `main`, the concurrent worker and this programme both land features on short-lived branches, `main` stays green.
2. Land in this order (each independently revertable): (a) the honesty machinery (`engine/honesty`, `tools/phantom_path_check.py`, `tools/check_citations.py`, `tools/novel_index_gate.py`), (b) the runtime (`runtime/`), (c) the storage tier + DP-2 edits, (d) the reference data + new tests, (e) the registers/reports, (f) the concurrent worker's own areas (their branch).
3. **Pre-edit hook**: `.githooks/pre-edit` running the v3.1 Rule-5 Quick Scan (`pytest engine/tests -q`, `pytest services/ -q`, `detect_imports.py`, `ruff check . --statistics`) and refusing when red.
4. **Done:** `git status` clean on `main`; the hook installed; the transient-failure classes G-H19/H-H22 impossible by construction.

## C-2 · CI uncommitted → no gate runs · P1 · Class: DEC (commit) + ADD (jobs)
1. Commit `.github/workflows/ci.yml` (6 jobs) as part of C-1(a)–(f).
2. Add three jobs: `structure` (A-2 step 4 ceilings + B-1 expiry), `coverage` (C-3), `dependency-graph` (B-6) — all non-blocking for the first two weeks, then blocking.
3. **Done:** every push runs guard + both suites + phantom + citations + parity + the three new jobs.

## C-3 · Coverage unmeasured (SB-08) · P2 · Class: ADD
1. CI job: `pytest engine/ services/ --cov=engine --cov=services --cov-report=term-missing -q -p no:cacheprovider`, publish the total.
2. Floor ratchet: block at 55 % now, +5 % per month to 80 % (SB-08), with the engine's *scientific* paths measured separately from the services'.
3. **Done:** a coverage number exists in CI and the ratchet is recorded in the constitution's KPI table.

## C-4 · No architecture tests for the new structure (AR-10) · P1 · Class: ADD
`engine/tests/test_structure_ceilings.py`:
1. no Python module under `engine/gateway/` exceeds 1,200 lines; no *new* module anywhere exceeds 800 (allowlist the 7 existing ones with a shrink-by date);
2. no `import requests|httpx|urlopen` under `engine/hydroma/` except the whitelisted ingestion modules, which must carry `note_download`;
3. every entry in `import_guard_policy.json` has `expires` and a `rationale`;
4. `engine/honesty/statuses.py` still exports 10 brakes and 13 AR rules (the vocabulary cannot silently shrink);
5. `architecture/dependency-graph.md` is regenerable and matches (B-6).

## C-5 · Duplicated error taxonomy · P2 · Class: MAN · Brake: SB-03
1. Map `GatewayError`, `HydromaError` and the services' exceptions onto the spec's 13 codes in one table (`docs/error-map.md`, ADD).
2. Make `HydromaError` the engine's base with `error_code` from the vocabulary; `GatewayError` becomes a subclass (behaviour-preserving because every existing code path keeps its current code).
3. **Done:** the map exists; a test asserts every raised engine error carries a code from the vocabulary.

---

# Sequencing (what runs when)

| Wave | Items | Depends on | Exit gate |
|---|---|---|---|
| **R5** | C-1 (commit + hook), C-2 (CI commit) | owner decision only | `main` green with CI running; `git status` clean |
| **R6** | B-1 (exception ratchet), C-4 (structure tests), A-3 (boundaries) | R5 | three new CI jobs green |
| **R7** | A-1 (gateway split), A-2 (facade/service slimming) | R5 (mandate recorded) | public-surface tests green; ceilings met |
| **R8** | B-3 (equation families, one per release), B-4, B-5 | R5 + per-family mandates | divergence register rows `resolved`; inline-science scan zero |
| **R9** | A-4 (directory shims + migration), A-5, A-6, B-2, B-6, C-3, C-5 | R5–R8 | spec §3.1 chain navigable; one settings object; coverage floor active |

**Total: 25 items — 10 ADD, 8 DEC, 7 MAN.** Everything in R5 costs nothing but a decision and removes the largest single risk (live-edited uncommitted tree); R6 is tooling; R7–R9 are the structural repairs.
