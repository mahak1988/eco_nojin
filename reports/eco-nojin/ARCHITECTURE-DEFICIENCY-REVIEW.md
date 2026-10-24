# ARCHITECTURE & STRUCTURE DEFICIENCY REVIEW

Document id: `ECO-ARCH-REVIEW` · Date: 2026-10-11 · Method: live measurement of the tree (not inspection of the documents), cross-checked against `GAP-REGISTER.md`, `EQUATION-DIVERGENCE-REGISTER.md`, `SPEC-V3-CONFORMANCE-REPORT.md` and the four formula audits.

## 0. Measured baseline (today)

| Area | Files | LOC | Note |
|---|---|---|---|
| `engine/` | 354 | 100,993 | 250 modules under `engine/hydroma/` alone |
| `services/` | 715 | 141,677 | the business layer is **1.4× the engine** |
| `tools/` | 16 | 7,146 | includes the honesty/enforcement tooling built in this programme |
| `runtime/`, `scenario/`, `decision/`, `adapters/`, `tests/` | 14 | 2,714 | the spec-shaped paths that exist so far |
| `database/` | 6 py | ~1.6k | SQLAlchemy models + JSONB→SQLite shim + 6 alembic migrations |
| Uncommitted changes | **622** entries in `git status` | — | the tree is majority-uncommitted; a concurrent worker edits it live |

Largest modules: `engine/gateway/__init__.py` **3,117** · `services/inventory/service.py` 2,639 · `engine/hydroma/data_pipeline/pipeline.py` 2,393 · `models/validation/runner.py` 2,155 · `models/registry.py` 1,723 · 44 modules over 800 lines, 7 over 1,500.

---

## A. Structural deficiencies (the shape of the system)

**A-1 · The Gateway is a 3,117-line monolith.** One `__init__.py` holds `UnitSpec`, `InputSpec`, `GatewayRequest/Result`, `ModelSpec`, the route table (~75 handlers), `_route_float/_int/_str`, `_normalize_inputs`, the dispatch and the engine facade. The spec asked for `model_dispatcher.py`, `input_validator.py`, `unit_converter.py` (§6.5). Consequence: every gateway fix is a 3,000-line-file edit (the two G-H20 repairs were exactly that), review is impractical, and the file is now the single highest-blast-radius module in the repo. **Severity: P1.**

**A-2 · Two services/facade choke points that are themselves large.** `services/_gateway_facade.py` (1,335 lines) is the *sanctioned* bridge and the reason services can stay guard-green — but it is a God-object whose 6 allowlisted engine imports (`tools/import_guard_policy.json`) include a self-declared **POLICY GAP** (`engine.hydroma.carbon.calculator`, a computation module). `services/inventory/service.py` (2,639) and `hub_service.py` (1,717) are un-partitioned business blobs. **Severity: P1.**

**A-3 · The business layer outgrew the engine without a boundary contract in code.** 715 files / 141k LOC against 354 / 101k. DP-1/DP-2 say ZED binds only layer 1 and Docker is out, but nothing *in code* prevents layer 3 from drifting (no package-level `__all__` boundaries, no dependency-cruiser rule for services→services, no size/complexity gate in CI). **Severity: P1.**

**A-4 · `engine/hydroma/` is a 250-module grab-bag.** Scientific kernels, scenario composites, satellite processors, data ingestion (`data_pipeline/` 2,393 lines with live network calls), biofertilizer (1,339 + 1,241), validation corpus, and business-adjacent helpers all sit under one prefix. The spec's chain (§3.1) has no directory mirror: no `indicators/`, no `knowledge/`, no `decision/`, no `scenario/engine/`, no `numerical/` kernel boundary. **Severity: P1.**

**A-5 · Test layout is four-way split and partially invisible.** `engine/tests/` (473+ tests), `engine/strict_tests/` (1,300+), `services/*/tests/` (1,150+), one file at repo-root `tests/`. `testpaths` in `pyproject.toml` lists `engine/tests`, `engine/strict_tests`, `services/*/tests` — so anything added at repo-root `tests/` is collected only by the *best-effort* CI step. The spec's `tests/{unit,scientific,integration,architecture,e2e}` does not exist. **Severity: P2.**

**A-6 · Configuration is spread over five homes.** `engine/hydroma/config/settings.py` + `rules.py` (production rules + the new storage tier), `database/settings.py` + `config.py`, `.env.example`, and `runtime/services.yaml`. There is no single documented precedence, and the two settings objects do not know about each other. **Severity: P2.**

---

## B. Coupling & dependency deficiencies

**B-1 · The guard is green because 8 carve-outs exist, not because the boundaries hold.** `allowed_imports` = 6 engine modules + 2 `facade_files`; the engine's own `ENGINE_NO_DATABASE` rule carries the sanctioned `database.config`/`database.base` exception (the persistence bridge). Every one is documented, but the *trend* is that a new integration becomes a new exception. There is no expiry/ratchet on exceptions. **Severity: P1.**

**B-2 · Engine ↔ database coupling is real and one-way-sanctioned.** `engine/hydroma/biofertilizer/calibration.py` imports `SessionLocal` for DB-backed calibration — scientific code reaching into a persistence implementation. ZED's rule is satisfied by a policy line, not by structure (the port exists but is not used there). **Severity: P1.**

**B-3 · Duplicated scientific implementations (10 families).** `EQUATION-DIVERGENCE-REGISTER.md`: 3 LS forms, K differing 6.8×, R 2 forms, 5 SCS-CN copies, 2 Theis, 3 RothC, 6+ copies of es/Δ/γ/Ra, 5 of eq. 52, 2 of PM, 4 of NDVI. Cross-module parity tests exist for some families; none for others. **Severity: P1 (scientific integrity), P2 (maintenance).**

**B-4 · Services still recompute science at the edges.** The three wrong eq.-52 copies were routed (PHASES), but the *pattern* remains: business code holds copies of formulas because the facade is the only bridge and it is a 1,335-line God-object. **Severity: P2.**

**B-5 · Three storage technologies coexist.** SQLite (engine, spec), DuckDB (legacy `data/master/`, now an optional extra), PostgreSQL (services; DP-1), plus the JSONB→SQLite compile shim and 6 alembic migrations. The spec's single SQLite/GeoPackage schema (§4.4/§5.1) is implemented but not the production path. **Severity: P2.**

**B-6 · No dependency graph artefact and no layering test for services→services.** `tools/detect_imports.py` covers engine/services/AI rules; nothing forbids `services.marketplace` from importing `services.finance` internals, and no `dependency_graph.md` exists (ECO-02 output). **Severity: P2.**

---

## C. Operational & process deficiencies

**C-1 · 622 uncommitted changes; a concurrent worker edits the tree live.** Every gate in this session had to be re-measured because files changed under it (three transient-failure episodes: finance isolation, marketplace mid-run rewrite, the soil-kernel API break). The project has no locking, no branch discipline, and no "gate before edit" protocol — the v3.1 constitution's Rule 5 (Quick Scan before any task) exists but is not enforced. **Severity: P0 (process).**

**C-2 · CI exists but is uncommitted, so no gate actually runs.** `.github/workflows/ci.yml` (6 jobs incl. the new `parity` job and the citation/phantom checks) is untracked. **Severity: P1.**

**C-3 · Coverage is unmeasured** (SB-08 requires ≥80 %). `pytest-cov` is in the dev extra but no coverage job exists. **Severity: P2.**

**C-4 · No architecture tests for the new structure.** We have 48 rules tests for the old INV rules; nothing asserts "the gateway stays a package with ≤N lines", "no module exceeds M lines", "engine/hydroma has no direct network import", or "every exception has an expiry". Brakes without tests are decoration (AR-10). **Severity: P1.**

**C-5 · Error taxonomy is duplicated.** The engine has its own `GatewayError`, `HydromaError` (added here), plus per-module `ValueError`s and services-level exceptions; no single mapping to the spec's 13 codes. **Severity: P2.**

---

## D. What is structurally sound (credit where due)
- **One gateway entry point** with real dispatch for ~75 models, unit audit at the boundary, and provenance in results (AR-13 holds in the engine).
- **A machine-enforced boundary** (0 violations today) with data-driven policy, plus the honesty machinery (vocabulary, phantom-path, citation, index gate) built in this programme.
- **A persistence port + spec-conformant SQLite adapter** that is ready to become the production path.
- **Docker-free internal runtime** (supervisor + state file + backup) and an explicit storage tier.
- **A validation corpus with honest verdict taxonomy** (`match / mismatch / inconsistent_case / not_run`) and external anchors where they exist.
- **Reference-data culture**: published values are transcribed with sidecars instead of invented.

---

## E. Remediation plan (with mandate classification)

| # | Action | Class | Brake |
|---|---|---|---|
| E-1 | **Split the gateway** into `gateway/{model_dispatcher,input_validator,unit_converter,contracts}.py` behind the existing public names (a façade that re-exports) | mandate (public API surface) | SB-03 (API), SB-01 (≤5 files: exactly 5) |
| E-2 | **Shrink `_gateway_facade`** by moving its 6 engine exceptions behind one typed adapter per domain (soil, climate, economics) | mandate | SB-03 |
| E-3 | **Exception ratchet**: every policy exception gets an `expires`/`revisit` field and a CI job that fails when an exception outlives it | additive (tooling) | none |
| E-4 | **Structure tests**: line-count ceilings per module (start: gateway ≤1,200 after the split, no new module >800), no direct network import under `engine/hydroma/` (already true), services→services dependency map generated in CI | additive | none |
| E-5 | **Commit the tree** (622 entries) with a branch protocol and the Rule-5 Quick Scan as a pre-edit hook | decision (owner) | none |
| E-6 | **Consolidate the 10 duplicated equation families** one at a time, each with a parity test before deleting the duplicates | mandate per family | SB-07 |
| E-7 | **Collapse storage** to the spec path: engine SQLite/GeoPackage as production, DuckDB legacy behind a documented reader, PostgreSQL for services only (already the DP-1 shape) | decision | SB-03 |
| E-8 | **Coverage job** in CI + a floor that ratchets up (start 60 %, +5 %/month to 80 %) | additive | SB-08 |
| E-9 | **Directory mirror for the spec chain**: create `engine/indicators/`, `engine/knowledge/`, `engine/decision/`, `engine/scenario/`, `engine/numerical/` as re-export shims over today's modules (behaviour-preserving), then migrate module by module | additive first, mandate for the moves | SB-01/SB-03 |
| E-10 | **Single settings object**: one `Settings` with the storage tier, the runtime config and the DB URLs, others deprecated | mandate | SB-03 |

**Bottom line.** The architecture has the right *skeleton* (one gateway, one guard, one port, one runtime) and the wrong *musculature*: two God-objects on the critical path, 250 grab-bag modules, ten duplicated science families, eight carve-outs instead of structure, and 622 uncommitted changes being edited live. The highest-value first moves are **C-1/C-2 (commit + CI)** — they cost nothing and make every other measurable improvement verifiable — then **E-1/E-2** (the two God-objects), then **E-3/E-4** (exception ratchet + structure tests) so the fixes cannot rot.
