# DEVELOPMENT, GAP-CLOSURE, VALIDATION & HONESTY PLAN v2

Document id: `ECO-DEVPLAN-v2` · Date: 2026-10-10 · Supersedes: `EXECUTION-PLAN-v1.md` (Waves 1–4, complete)
Inputs: `GAP-REGISTER.md` (G-Z…G-R, G-H1..G-H13), `FORMULA-VALIDATION-REGISTER.md`, `reports/eco-nojin/FINAL-IMPLEMENTATION-AND-SCIENTIFIC-VERIFICATION-REPORT.md` (skeleton).
Basis for every number below: measured on this host 2026-10-10 (`engine/tests` 473 passed / 0 failed; `services/` 627 passed; import-guard PASS; ruff 1967; corpus `{match 25, mismatch 0, inconsistent_case 12, not_run 58}`; maturity `{S0 14, S1 47, S2 2, S3 7}` of 70 models).

---

## 1. The honesty contract (non-negotiable, applies to every action below)

1. **No claim stronger than evidence.** A model/formula is called `validated` only when an *externally published* value passes; everything weaker gets an explicit label from one vocabulary: `VALIDATED_EXTERNAL` / `VALIDATED_METHOD_CONFORMANCE` / `REGRESSION_ANCHOR_STABLE` / `PARTIAL` / `UNVALIDATED` / `BLOCKED`.
2. **`recorded` ≠ `validated`.** Every stored corpus expectation carries a `provenance` field: `published:<citation>` or `recorded:<date — own output>`. The runner reports the two separately.
3. **No cited test that does not exist.** A CI job asserts every path referenced by `formulas/catalog.py` `parity_tests`, model-card `unit_tests`, and YAML `test_file` fields exists (retires the 56 phantom paths).
4. **Nothing green without a run.** Public endpoints (`/models/{id}/validation`) may report only what the runner executed in-process; unreached cases report `not_run`, never `passed`.
5. **Deviations are documented, not attributed.** Any place where the code departs from a cited standard (e.g. the `Rs/Rso ≥ 0.3` clamp, the `dtr_floor` floor) is labelled "engine assumption — deviation from <standard>".
6. **Brakes hold.** No equation, public API, unit, or schema change without explicit mandate; when the tree or its numbers move, the plan re-measures and timestamps.
7. **One canonical implementation per named equation**, or an explicit reconciliation note with measured divergence.

---

## 2. Phase structure and gates

| Phase | Goal | Exit gate (all must pass) | Status |
|---|---|---|---|
| **W5 — Label & unit integrity (P0)** | Every published claim matches the evidence; live defects fixed at the contract level | honesty test suite green; dashboard reflects the runner; `SOIL_AMENDMENT` unit test pins the fixed contract; public check endpoint passes or is removed | **NEXT** |
| **W6 — Evidence wiring (P1)** | Corpus distinguishes external vs regression anchors; dead anchors wired-and-reported or retired; phantom-path test in CI | runner emits `match_external`/`match_regression`; every `reference_data.py` range either passes as a test or is retired; CI includes the path-existence job | pending W5 |
| **W7 — Consolidation & depth (P2)** | One canonical implementation per named equation; indicators → YAML model cards + maturity S4 for externally anchored ones | divergence register shows ≤1 implementation per equation or a documented reconciliation; ≥1 model reaches S4 with external anchors | pending W6 |
| **W8 — Coverage & reproducibility (P3/P2)** | ≥80 % coverage of gateway main paths (§6.5), independent reference tables for Kirpich/Theis/Hargreaves/texture; reproducibility bundle | coverage report in `reports/eco-nojin/`; `pytest.ini` decision recorded; licenses/rebuild notes updated | pending W7 |

---

## 3. Ordered backlog (each row: action · verification · honesty record)

### P0 — blocks scientific/architectural integrity (do first, all label/contract-level)

| # | Action | Verification | Honesty record | Refs |
|---|---|---|---|---|
| P0-1 | Retire the `validated` claim where evidence is a regression anchor: six YAML families (ecsi, epia, esri, ewsi, hlhs, hyrue) → `regression_anchor_stable` + probe provenance | runner summary shows 0 `validated` headers without `published:` anchors | the re-label itself, with before/after | G-H1 |
| P0-2 | Correct `CANON-005` (Theis 0.018 m → 0.3062 m) and `CANON-006` ("<1%", two fabricated citations) | card text matches a measured value printed by a test | card correction + measured number | G-H1, G-H12 |
| P0-3 | Registry fold: models `blocked` may not be `validated` (CANON-008..011, 019..022) | `test_registry_status`-style assertion | fold rule documented | G-H1 |
| P0-4 | `SOIL_AMENDMENT` contract: accept depth in m at the router, convert once at the boundary; pin 0.3 m → 10 000 kg/ha | unit test at `hydroma_soil` router boundary | G-H3 closeout note | G-H3 |
| P0-5 | `ks_cm_per_day`: gate behind an explicit `UNTESTED_UNCONFIRMED` flag or remove from the response until attributed | response schema test | G-H4 closeout | G-H4 |
| P0-6 | Correct the public checker (`formula_checks.py:211`) to eq. 52 exponent 0.5 and remove the false "FAO publishes 0.48" comment | endpoint returns `passed: true` and a test pins it | G-H10 closeout | G-H10 |
| P0-7 | Re-attribute the two engine clamps (`Rs/Rso` floor, `dtr_floor`) to "engine assumption" in docstring + cards (`CANON-001:20`, `S-010:20`) | card/docstring text scan in CI | G-H8 note | G-H8 |
| P0-8 | Tolerance policy: `scientific_verification:298` may not pass the 0.48 `.pyd` under a 10 % "tuned constant"; record as BLOCKED_ARCHITECTURE with the measured −4.5 % and the no-compiler reason | strict-xfail remains the only place it passes | G-H9 note | G-H9 |
| P0-9 | Card↔code audit for the five documented-but-unimplemented equations (CANON-007/009/011/015) | new test `test_cards_match_implemented_equations` | G-H12 closeout | G-H12 |
| P0-10 | ZED/architecture P0s deferred from Waves 1–4 **require mandate** (supabase/duckdb removal, `_gateway_facade` completion, AR-02 exception) | — | mandate request, not attempted | G-Z1, G-A2, G-A3, G-A4 |

### P1 — blocks integration / necessary capability

| # | Action | Verification | Refs |
|---|---|---|---|
| P1-1 | Corpus runner: add `anchor_provenance` to every case; verdicts `match_external` vs `match_regression`; `validated` headers forbidden without `published:` | runner unit test + back-filled 95 cases | G-H1, §3 |
| P1-2 | Phantom-path CI job: assert every cited `parity_tests`/`unit_tests`/`test_file` exists | job green; failure names the path | G-H5 |
| P1-3 | `reference_data.py`: wire as explicit tests; **report measured failures as scientific findings** (EWSI healthy, HY-RUE ×2, HLHS healthy, ECSI) or retire the file | either 7/7 pass or a findings report + retired anchors | G-H7 |
| P1-4 | Dashboard: report only executed verdicts; fix model names/citations (HLHS is the Landscape Health Score, not Latin Hypercube Sampling) | endpoint test asserts `not_run` propagates | G-H2 |
| P1-5 | Consolidate equation duplicates: 3 LS forms, K (6.8×), R (2 forms), 5 SCS-CN, 2 Theis, 3 RothC, Kirpich unit error in `land/drainage.py:153`, three eq.-52 copies missing 0.408 | divergence register; each canonical path parity-tested | G-H6, G-H11 |
| P1-6 | Evidence/Knowledge/Decision maturation to the spec's split (`evidence_engine`/`provenance_tracker`, `claim_registry`/`epistemic_manager`/`conflict_resolver`, `problem_formulator`/`mca_engine`/`sensitivity_analyzer`) **behind the existing in-memory engines** | contract tests like `test_persistence_port_contract` | G-S3, G-S4, G-S9 |
| P1-7 | Uncertainty propagation engine (ECO-11) producing real `UncertaintyEstimate` values from model inputs | a propagation test with a known closed-form case | G-S7 |
| P1-8 | Persistence registrations: dataset/model_run/claim/decision rows written through `adapters/persistence/sqlite_persistence.py` (already spec-conformant) | E2E writes evidence/claim/decision ids into a temp DB | G-D3 |
| P1-9 | Hargreaves external anchor: pin FAO-56 Ex. 20 (engine 5.033 vs published 5.0) as a second reference test | new test, like Example 18 | §10.1 |
| P1-10 | Test layout convergence to `tests/{unit,scientific,integration,architecture,e2e}` (only additive; do **not** add `pytest.ini` — record the decision) | CI collects both trees | G-T1, G-T2 |

### P2 — important, non-blocking

| # | Action | Refs |
|---|---|---|
| P2-1 | Indicators → `models/scientific/*.yaml` cards (5 exist in `indicators/`); raise S3→S4 only on external anchors | G-S2 |
| P2-2 | Independent reference tables: Kirpich Tc, Theis drawdown, full USDA texture triangle, FAO structure volumes (all currently untested) | §8 |
| P2-3 | Unit discipline: `pint` declared and used at gateway boundaries; `Quantity` stub retired | G-Z5 |
| P2-4 | `LICENSES/` extended to the new deps (pint/sqlalchemy/numba) and the `legacy-bridge` extra | G-Z6 |
| P2-5 | Reports renamed/aliased to the `ECO-01..17` scheme with `reports/eco-nojin/` canonical copies | G-R1 |
| P2-6 | Lint/type debt burn-down in CI (non-blocking → blocking at ≤50 new findings) | G-R2 |
| P2-7 | C++ rebuild path (no compiler): document, or vendor a build container; until then keep the xfail+tolerance policy from P0-8 | G-S11, G-H9 |

### P3 — optional polish
`README-ZED.md` at repo root; `BLOCKED-{timestamp}.md` pattern; `data/{raw,processed,indices,model_runs}` promotion guide with `meta.json` contract (module exists); coverage dashboard page.

---

## 4. Validation & verification programme (standing, not a phase)

Every formula carries an evidence class and a test that would fail if the equation changed:

1. **Classification on entry.** New/changed formula lands with E/R/I/N assigned at review; N is allowed only with an explicit `UNVALIDATED` label in code, card, and indicator record.
2. **External anchors first.** Where a published value exists (FAO-56 examples 8/10/17/18/20, NEH/TR-55, AH-703, RothC tabulates, USDA tables), it is transcribed to `tests/reference_data/*.csv` + `.meta.json` and pinned with the standard's own tolerance. Example 18 (ET0) is the template.
3. **Independent re-implementation as second line.** Closed-form/from-scratch oracles written in the test (never sharing code with the module), verified against exact mathematics (Erlang closed form, score equations, published limits).
4. **Property layer last.** Conservation, monotonicity, symmetry, sign/zero behaviour, parity between languages.
5. **Regression anchors labelled.** `recorded` cases keep their role (change detection) but never a `validated` claim.
6. **Mutation spot-checks.** Periodically flip one constant in five formulas; at least one test must fail per flip (guards against vacuous tests).
7. **Machine-readable evidence.** `runner.machine_summary()` + `maturity_summary()` run in CI; the dashboard and cards are generated from these, not hand-written.

## 5. Honesty programme (mechanics)

- Single status vocabulary (§1.1) used by `indicators/*.yaml`, `models/scientific/*.yaml`, `registry.py`, and the corpus; one test asserts they agree.
- `anchor_provenance` mandatory in the corpus (§3 P1-1); `validated` requires `published:`.
- Phantom-path job (§3 P1-2) in the same workflow as the import guard.
- Endpoints report executed verdicts only (§3 P1-4).
- Deviation register: every engine-vs-standard departure listed with measured effect (currently: Rs/Rso clamp −1.44 MJ/m²/day at ratio 0.14; dtr_floor +124 % at ΔT=0.02; `.pyd` 0.48 −4.5 %).
- All reports carry a measurement timestamp, and any moving-tree number is re-measured before a gate.

## 6. Metrics (track per wave)

| Metric | Now (2026-10-10) | W5 target | W6 target |
|---|---|---|---|
| Formulas with E anchors | ~8 | ≥10 (+ Hargreaves Ex. 20) | ≥12 |
| `validated` claims without evidence | ≥8 | **0** | 0 |
| Phantom test paths cited | 56 | 56 (test added) | **0** |
| Dashboard `passed` for never-run cases | 38 cases | 0 | 0 |
| Live unit/attribution defects | 3 | 0 | 0 |
| Models at S3+ / S4+ | 7 / 0 | 7 / 0 | 8 / ≥1 |

## 7. Blocked / mandate-required (not started)

supabase–duckdb removal and SQLite master migration · `_gateway_facade` completion (`AR-06`) · AR-02 sanctioned exception · Gateway API migration to the spec contract · C++ rebuild · real-data E2E (needs local CHIRPS/ERA5/SoilGrids mirrors with meta.json) · Guttman-1999 SPI table (offline unavailable).

## 8. Working method

Subagent-per-item as in Waves 1–4 (bounded scope, additive-first, exact verification commands, report-only on failure), with three standing changes: (a) re-measure mutable numbers immediately before any gate because a concurrent worker is editing this tree; (b) every agent's report separates *measured* from *claimed*; (c) no agent may promote a status — promotions happen only in W6 via the runner, with evidence attached.
