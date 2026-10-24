# FORMULA VALIDATION & HONESTY REGISTER — Eco Nojin / HyDroMA

Document id: `ECO-10-REGISTER` · Verified: 2026-10-10 · Source spec: ECO-MASTER-v2.0-ZED-UNIFIED (§6.10, §8.3)
Method: code reading + live execution (venv `D:\eco_nojin\.venv`, `$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"`) by four parallel auditors (climate / hydrology / soil-carbon / agronomy-economics) plus machine-measured state from `engine/hydroma/models/validation/runner.py`, `engine/models/maturity.py` and the strict suite.

---

## 0. Headline numbers (all measured, none claimed)

| Measure | Value | What it means |
|---|---|---|
| Registered models | **70** | maturity S0=14, S1=47, S2=2, **S3=7** (S4–S6 = 0) |
| Validation corpus | 95 cases → **match 25 / mismatch 0 / inconsistent_case 12 / not_run 58** | only **4** matches rest on a *published* value (SCS-CN NEH worked example family); the other 21 are `recorded: 2026-09-29` **regression anchors** — the model's own recorded outputs |
| Independently validated indicators | **1 of 4 Priority-1** | `ENO_ET0_FAO56_001` (FAO-56 Example 18, primary source). SPI/WB/WP = method/definition conformance only |
| Cards whose `validation_status: validated` outruns the evidence | **≥ 6** | CANON-005, CANON-006, CANON-007, CANON-015, CANON-017 + registry entries CANON-008..011, 019..022 (`validated` while `blocked`/S0) |
| Phantom test paths cited as evidence | **56 paths from 96 sites** | incl. catalog `parity_tests`, card `unit_tests`, `hdvi.yaml`, `hpheno.py` |
| Live defects reaching API consumers | **3** | SOIL_AMENDMENT 100× unit, pedotransfer `ks_cm_per_day` (4.1e38 cm/day), withdrawn Carsel & Parrish attribution still served |

### The match≠validation rule (the single most important line in this register)
`runner.py` reports `match` when the implementation reproduces a **stored value**. A stored value is only a scientific reference when it is *published independently of this repo*. The six families whose YAML declares `status: validated` **and** `recorded: 2026-09-29` (ecsi, epia, esri, ewsi, hlhs, hyrue) therefore fail the test that matters: their "matches" are stability checks. The register below classifies every formula into **E** (external anchor verified), **R** (regression anchor only), **I** (internal consistency), **N** (nothing).

---

## 1. Externally validated (E) — evidence that would survive an external audit

| Formula | Anchor (published, independently of this repo) | Evidence | Verdict |
|---|---|---|---|
| ET0 Penman–Monteith (`climate/et_calculator.py:256`) | FAO-56 Ch.4 Example 18, Uccle 6 Jul, ET0=3.9 | engine **3.8801 mm/day**, Δ−0.0199 ±0.05; independent eq.-6 re-implementation; NCAR/pyet/hydpy reproduce 3.87–3.9 | **VALIDATED_EXTERNAL** |
| SCS-CN runoff (`models/runoff_model.py:152-172`) | USDA NEH Sec.4 / TR-55 worked example P=50, CN=70 → 5.8128 mm | `test_s03:58` `rel=1e-9`; inch→mm trap pinned `test_s03:69`; engine strict suite green | **VALIDATED_EXTERNAL** |
| RUSLE LS — AH-703 form (`cpp_core/src/erosion.cpp:22-46`, `wrapper.py:212-226`) | USDA AH-703 (Renard et al. 1997) McCool constants | two independent hand re-derivations `rel=1e-12`; live C++/Python parity 1.0422484 | **VALIDATED_EXTERNAL** |
| RothC temperature factor (`rothc_runner.py:107-138`) | Coleman–Prout–Milne 2024 §1.6.1 eq.(1) tabulated points | `test_s20:390-400` 5 points to 2e-3 + 9.291 °C normalisation | **VALIDATED_EXTERNAL** |
| Salinity classes (`soil/salinity.py:32-84`) | USDA Handbook 60 (1954) class edges 2/4/8/16 dS/m | `test_s18:91-100`, `test_soil.py:449-493` | **VALIDATED_EXTERNAL** |
| NDVI/EVI/SAVI/NDWI/NBR (`land/indices.py:47-89`) | Rouse 1974, Huete, Gao — closed forms | C++/Numba/Python parity + `cpp_core/tests/test_indices_unit.cpp` | **VALIDATED_EXTERNAL** (closed form) |
| Texture classification (4 known points) | USDA texture triangle | `formula_checks:174-198` (only 4 points; see §5) | **PARTIAL→E** |

---

## 2. Method-conformance only (I/R)

| Family | Verdict | Basis | Gap |
|---|---|---|---|
| SPI (`hydroma/spi_calculator.py`) | **VALIDATED_METHOD_CONFORMANCE** | from-scratch McKee/WMO-1090 re-implementation (Newton MLE, series/CF incomplete gamma vs exact Erlang, AS241), published classification bands pinned | no offline published *value* table (Guttman 1999) |
| Water balance | **VALIDATED_MASS_CONSERVATION** | identity `P=ET+Q+ΔS`; closure 7.1e-15 mm | no catchment benchmark |
| Water productivity | **VALIDATED_UNIT_DEFINITION** | FAO WaPOR definition; 5000 kg/ha & 500 mm → exactly 1.0 kg/m³ | no published WP values |
| Hargreaves ET0 (`climate/et_calculator.py:112-125`) | **PARTIAL** | 1 corpus `match` — but the runner re-derives ET0 inline from eq.52/21 and compares to the stored number; it **never calls the engine**. 3 further cases are internally inconsistent (stored Ra contradicts eq. 21) | engine path not anchored to a published Hargreaves value |
| Priestley–Taylor (CANON-003) | **UNVALIDATED** | property tests only | — |
| van Genuchten θ/K (`soil/physics.py:30-109`) | **VALIDATED_METHOD** | independent `_ref_vg_theta` `rel=1e-12` (s05:159, s18:132) | no published θ/K table values |
| SAR / ESP (`soil/chemistry.py`) | **VALIDATED_METHOD** | exact re-derivations (s18:64-89) | hazard class edges uncited |
| Leaching requirement (`soil/salinity.py:163-226`) | **VALIDATED_METHOD** | FAO-29/Rhoades `LR=ECw/(5·ECe−ECw)` exact (s18:102) | `ec_soil` never enters; 0.95 ceiling untraceable |
| FC/PWP heads 33/15000 cm | **VALIDATED_METHOD** | s05:409-423 pins 33.0 (a former 330.0 = 10× error, fixed) | — |
| NDL/Theis (`groundwater/models.py:214-218`) | **VALIDATED_METHOD** | independent `expi` re-derivation + limit tests; day-based units correct | **no published drawdown value stored** (and the card prints a wrong one, §6) |
| Hantush–Jacob / Cooper–Jacob / Neuman blend | **PARTIAL / VALIDATED_METHOD** | two published mathematical limits each; Neuman blend self-labelled "not the Neuman type curve" (the most honest limitation in the package) | — |
| Muskingum–Cunge (`calculator.py:897-937`) | **VALIDATED_METHOD** | coefficient identity, volume conservation, stability-window proof | no published routed-hydrograph benchmark |
| SCS-CN AMC adjustment | **VALIDATED_METHOD** | correct NEH-4 forms (`map_engine/runoff.py:162`) | only implementation in tree |
| Rational method, spillway, Horn slope, Strahler, reservoir storage | **VALIDATED_METHOD** | closed-form re-derivations, unit algebra | — |
| Bransby-Williams / California Tc / Snyder / unit hydrograph | — | **do not exist in the tree** | — |

---

## 3. Regression-anchor only (R) — the honesty problem in one table

These are the 21 "matches" that are **not** validation. Each stores `recorded: 2026-09-29` (the model's own output) while the YAML header says `status: validated`.

| Family (cases matching) | What the match proves | What it does **not** prove |
|---|---|---|
| ECSI (7) | the RothC port still reproduces its 2026-09-29 output | no published RothC run exists in the repo; and the anchor set that *would* test it fails if wired (see §5) |
| EPIA (5) | stability of `ETc=ET0·Kc·Ks` | Kc(LAI), Ks, effective-rain are property-tested only; `Kc(LAI)` is the project's own form (max 1.2 > FAO max 1.15) |
| ESRI (1) | a 4-pixel band-ratio scene reproduces | the composite weights α/β/γ and /10, /16 rescalings are project-invented; own docstring says "NO PUBLISHED SOURCE" |
| EWSI (1) | reproduces a 4-pixel scene | composite weights 0.4/0.3/0.3 project-invented; VPD ramp saturates at 4 kPa of a declared 10 kPa range; Gao 1996 is the NDWI paper, not NDMI |
| HLHS (5) | reproduces the landscape score | HLHS is a composite of composites (EWSI+ECSI, both project contributions); `shdi` is caller-supplied and never computed; the cited Shannon/Nagendra entropy is **not** computed |
| HY-RUE (1) | reproduces mid-season wheat | `days` is a multiplier, not an integration; the module's own `HYRUE_VALIDATION` would fail (13.20 vs 3.5–5.5 t/ha) |

---

## 4. Unvalidated with honest labels (N, correctly labelled)

`hdvi.py` composite (project-invented; `hdvi.yaml:38` self-declares) · `hdvi.spi` z-score (self-declared "THIS IS NOT SPI"; zero-variance guard produces z=−9 999 000 then clipped to −3) · `soil/chemistry.py` CEC (pH term labelled "not defensible" in its own docstring) · ph-buffer (buffer capacity accepted and unused) · dual-pore & Richards accumulators (no test reads them) · Saxton–Rawls θ1500/θ33 regression coefficients (never re-derived by any test) · lst `_calculate_texture_properties` whc/K tables · soil-order ladder (5 of 12 orders unreachable) · soil-health index (7 weights sum 0.85, not 1.0; no test) · amendment cost bands (no citation for any figure) · `SEQUESTRATION_RATES` + `CARBON_PRICES` (10–18 USD/t shipped while the module's own note cites World Bank ~6.34 and MSCI ~3.5) · irrigation `application_rate=20` mm/h default · Kc lookup (1.15/1.20/1.25, no provenance) · integration economics' 1.05/0.95/1.10 magic constants · biofertilizer's 178 constants (AST guard: 178/178 unsourced, 105 load-bearing — honestly labelled `unvalidated` on every result) · `FormulationOptimizer` (docstring claims LP/simplex; executes a greedy heuristic with unused CN constraint).

---

## 5. Systemic honesty failures (independently of per-formula verdicts)

1. **Phantom test tree.** 56 paths under `tests/unit`, `tests/models`, `tests/contract` are cited from 96 sites (catalog `parity_tests`, card `unit_tests`, `unvalidated_verdicts.py:31`, `hpheno.py:48` "the best-validated code in this package"). None exists; the repo root `tests/` contains only `reference_data/`. The catalog validates only that `parity_tests` is non-empty, not that the files exist.
2. **Dead literature anchor set that would fail if activated.** `models/validation/reference_data.py` (EWSI/HYRUE/ECSI/HLHS ranges with Rothamsted/ICARDA/AquaCrop/USDA-NASS provenance) has **zero import sites**. Measured if wired: EWSI healthy 0.357 vs 0.0–0.3 **FAIL**; HY-RUE wheat 13.20 vs 3.5–5.5 **FAIL**; HY-RUE maize 29.20 vs 9.0–12.0 **FAIL**; HLHS healthy 74.71 vs 80–95 **FAIL**; ECSI −0.578 vs ±0.5 **FAIL**.
3. **The dashboard publishes passes that never ran.** `services/api_gateway/routers/hydroma_dashboard.py:675-725` returns `overall_status="passed"` + `test_cases_passed=N` for epia/ewsi/esri/ecsi/hyrue/hlhs/hdvi while the engine runner records `not_run` for their cases; the same router mis-names and de-cites models (HLHS published as "Hybrid Latin Hypercube Sampling"; every citation replaced by `"<ACRONYM> methodology"`).
4. **Divergent duplicates of the same named equation.** Three LS forms (`65.41 sin²θ+4.56 sinθ+0.065` with no length factor; AH-703; a third "McCool 1999" set with `−0.045cos²θ` that is neither), K differing 6.8× (Williams vs Renard), R differing (Renard vs Fournier), five SCS-CN copies, two Theis, three RothC (incl. `services/api_gateway/routers/carbon_engine.py` with annual step, different initial split and a second temp-factor zeroing at T≤0), three more NDVI copies. Kirpich exists twice with **unit errors in one copy** (`land/drainage.py:153`: slope in percent, output labelled hours → 3.98 "hours" vs 23.44 min canonical).
5. **Cards document equations the code does not implement.** CANON-007 (β and S forms), CANON-009 (`φ=arctan2(q,−p)` argument order; TWI `flow_accumulation × cell_area` vs code's length form; curvature "1/m" while profile+plan are added in quadrature across dimensions), CANON-015 (advertises `Tc=L/(v·S^0.5)`; cites "McCool 1989 reference data"; points at a module containing no delineation code), CANON-006 (fabricated Mualem/Carsel&Parrish citations; "<1% AWC agreement" vs measured 30–157%).
6. **YAML `status: validated` without any run** (the six families in §3), and a corpus runner whose `match` verdict cannot distinguish regression from reference.

---

## 6. Live defects that reach users today

1. **`SOIL_AMENDMENT` 100× under-report.** Router declares `soil_depth` in **m** (default 0.3) and passes it to a kernel expecting cm → **100 kg/ha gypsum instead of 10 000 kg/ha**. The module's claim "fixed in the router" is false. (`hydroma_soil.py:229-234` ← `soil/salinity.py:229-293`)
2. **Unattributed pedotransfer `ks_cm_per_day`.** `pedotransfer.py:161-174` returns **4.5e9 cm/day (sandy loam)** and **4.1e38 cm/day (clay)**; no test reads it; the 2.278/2.778 prefactor and five coefficients appear nowhere else; served live by `SOIL_PEDOTRANSFER`.
3. **Withdrawn attribution still served.** `SOIL_VG_PARAMETERS` answers "Carsel & Parrish, 1988" on every request while `engine/data/soil_vg_table.csv` and `SOIL_TABLE_CONFLICTS.md` mark those rows `design_assumption`/`design_assumption_disputed` and the CSV's own provenance says "unverified".
4. **`SOIL_AWC` unit label.** Returns a volumetric fraction labelled `mm/m`; published Saxton & Rawls loam AWC is 180 mm/m vs 142.6 measured (79%), with texture agreement spanning 30–157%.
5. **CANON-005 card prints a wrong reference value**: "Drawdown should be approximately 0.018 m" — engine and hand calculation both give **0.3062 m** (17×); no test asserts the card's number, yet the card reads "matches reference case" and the registry seeds it `validated`.

---

## 7. What the strict suite *does* pin (the honest credit side)

202+ engine strict tests green; s18 pins SAR/ESP/the five salinity classes/leaching to exact published re-derivations; s05 pins the VG table, FC/PWP heads and Saxton-Rawls **bands** (20 % floor and 5× window — bands, not values); s04/s06 pin Muskingum stability and Theis singularity behaviour; s07 pins carbon ordering/bracketing only; s13/s14 pin table provenance conflicts. The suite's self-description is honest; the *cards* and *YAML headers* are what over-claim.

---

## 8. Recommended closure order (spec §9.3 priorities)

- **P0 (validity of published claims).** Correct or retract: CANON-005's 0.018 m value; CANON-006's "<1%" and its two fabricated citations; the six `status: validated` YAML headers whose anchors are `recorded`; the dashboard's `passed` for never-run cases. Fix the `SOIL_AMENDMENT` m/cm unit at the router. These are documentation/validation-label corrections — no equations change.
- **P1 (evidence wiring).** Either wire `reference_data.py` as a real test target and label its measured failures as scientific findings, or delete it. Make the corpus runner distinguish `match-external` from `match-regression`. Create a catalog test that asserts every cited `parity_tests`/`unit_tests` path exists (this single test retires 56 phantom paths).
- **P2 (divergence).** One canonical implementation per named equation; reconcile K (6.8×), R, LS (3 forms), Tc units, and the three RothC ports; document routing in `tools/import_guard_policy.json`.
- **P3.** Published benchmarks: Kirpich Tc, Theis drawdown, FAO structure volumes/spacings, Hargreaves value for the engine path, texture full-triangle table.

---

## 9. Machine-measured state at audit close

```
corpus   : {'match': 25, 'mismatch': 0, 'inconsistent_case': 12, 'not_run': 58, 'total': 95}
maturity : {'S0': 14, 'S1': 47, 'S2': 2, 'S3': 7}  (70 models; S4–S6 = 0)
engine   : engine/tests 473 passed / 0 failed (2026-10-10)
```
12 `inconsistent_case` verdicts are case-side defects (stored expectations that no correct implementation can produce): penman_monteith 6, hargreaves 3, check_dam 2, scs_cn 1 — the runner's own verdict taxonomy exonerates the code for these.

**Note on a moving tree.** The audit observed a concurrent worker wiring corpus handlers mid-audit (corpus moved 1/85 → 25/28 within the session). All numbers above were re-measured at close. Sections 1–6 classify each *formula*, and that classification is unaffected by which anchors are wired.

---

## 10. Climate/evapotranspiration audit (F-CLIMATE, appended after its completion — with a self-correction)

### 10.1 Externally validated (E) — the strongest evidence in this register

| Formula | Published anchor (verified against fao.org primary source by the auditor) | Evidence | Verdict |
|---|---|---|---|
| `es` (eq. 11) | FAO Annex 2 Table 2.3 (es(0)=0.611, es(25)=3.17, es(30)=4.24); Ex. 3, Ex. 18 | `test_s02:175` pins the table ±2e-3 | **E** |
| `Δ` (eq. 13) | Table 2.4 (Δ(25)=0.189, Δ(20)=0.145); Ex. 17 Δ(30.2)=0.246 | `test_s02:198,206` | **E** |
| `P`, `γ` (eq. 7/8) | Ex. 2 (P(1800)=81.8, γ=0.054); Ex. 18 γ(100)=0.0666 | `test_s02:215,224` — exponent **5.26** confirmed against FAO text and PyETo | **E** |
| `Ra` (eq. 21) | Ex. 8 (32.2), Ex. 10 (25.1), Ex. 17 (38.06), **Ex. 18 (41.09)**, Ex. 20 (40.55) | `test_s02:238` vs an explicit day-length cosine-integration oracle across 6 lats × 7 doys | **E** |
| **ET0 PM (eq. 6)** | **FAO-56 Ex. 17 (5.72) and Ex. 20 (4.56) reproduce in-engine; Ex. 18 = 3.9 pinned** | `engine/tests/test_fao56_example18.py` (Uccle 3.8801/3.9) + `test_s02:433` | **E** |
| ET0 Hargreaves (eq. 52) | **Ex. 20: "Hargreaves eq. 52 predicts ETo = 5.0 mm/day"; engine gives 5.033** | **pinned 2026-10-10 in `engine/tests/test_fao56_example20_missing_data.py`** (Ra 40.55 and the eq.-50 estimate 22.29 also pinned) | **E** |

### 10.2 Method-conformance only

`Rns/Rso/Rnl/Rn` (external only through the composite ET0; **no test pins Rnl or Rn individually**) · `Priestley-Taylor`/`Blaney-Criddle`/`Turc`/`Makkink` static/passivity forms with published constants but no external values · C++ twins and the three delegate paths (parity at 1e-12/0.02) · monthly ET0 and mid-month Ra (property tests only) · grid.

### 10.3 Unvalidated / uncorrectly attributed

1. **Two engine-invented deviations are attributed to FAO in docstrings and cards.** `Rs/Rso` is clamped to **[0.3, 1.0]** (`et_calculator.py:222`) — FAO-56 text (verified 2026-10-10) limits only the upper bound (≤ 1.0); measured effect at Rs/Rso=0.14: Rn −1.44 MJ/m²/day (≈ −0.35 mm/day ET0). The `dtr_floor=0.1 °C` injected by delegates is uncited and inflates ET0 by **124 %** at ΔT=0.02. The "overcast ⇒ Rnl=0" branch described by the same docstring is unreachable dead code (the clamp already forces the cloud factor ≥ 0.055).
2. **The live compiled kernel still carries the rejected exponent.** Measured today: `hydroma_core.hargreaves_et0` returns the **0.48** value (−4.5 % vs the 0.5 source). `climate.cpp:47-59` and S11 `:161` record it as an honest strict xfail, but `scientific_verification/__init__.py:298` passes it under a **10 % tolerance** with the comment "the C++ implementation uses a slightly tuned constant" — the cards `CANON-002`/`S-006` never mention it.
3. **Cards document equations the code does not run.** `CANON-002_hargreaves_et0.md:19` and `S-006:19` publish `(Tmax−Tmin)^0.6 · Ra^0.5`; code uses `^0.5` and linear Ra — and no FAO source publishes the card's exponents. `CANON-011:60` states "Ra ≈ 24.5 MJ/m²/day" at 41.9 °N/DOY 193 where FAO Annex 2 and the engine give **41.0**.
4. **Three inline eq. 52 copies are actively wrong.** `simulation/adapters/crop_adapter.py:147`, `analysis/drought_agent.py:203`, `analysis/scenario_agent.py:67` omit the **0.408** conversion (2.45× overstatement), substitute Rs or W/m² for Ra, and clamp at 0.5 — none is tested. `platform.py:602` implements eq. 50 without FAO's `≤ Rso` cap.
5. **A public validation endpoint fails and mis-cites.** `services/validation/formula_checks.py:211` computes exponent **0.48** with the comment "FAO publishes 0.48" — FAO does not; the engine and `test_s17_service_strict.py:159` both pin 5.279098340839128. Live today: expected 5.00078 vs actual 5.27910, `passed: false`, exposed at `GET /api/v1/hydroma/validation`, covered by no test.
6. **A second published PM equation lives beside the engine's.** `cpp_bridge/__init__.py:361` computes `ea = es_mean·rh_mean/100` (eq. 19 route) rather than eq. 17; it is a legitimate different equation, but it is the direct cause of the six `inconsistent_case` corpus verdicts.
7. **Invented defaults presented as FAO's.** `hydroma_climate.py:166-170` fills missing `rh_max=80, rh_min=30, wind_speed=2.0, solar_radiation=20.0`; only u2=2 m/s is FAO's "global value".
8. **Self-correction of record:** the "independent" FAO-56 oracle inside `engine/tests/test_fao56_example18.py` originally used exponent **5.54** (eq. 7) where FAO publishes **5.26**. Corrected 2026-10-10 (0.03 % effect, inside tolerance) and documented in the file; the test still passes. This is exactly the class of defect §10.3.1 describes — an oracle must match the cited standard, not merely agree with the engine.

### 10.4 Climate verdict summary
E: es, Δ, P/γ, Ra, ET0-PM, **ET0-Hargreaves**. Method: radiation terms, C++ twins, delegates, other ET0 families. Unvalidated: ~~Hargreaves engine-path anchor~~ (now pinned via Ex. 20), eq. 35/47 (not implemented), eq. 50 (uncapped), three wrong inline copies, invented defaults, the two FAO-attributed engine clamps.

### 10.5 Standing validation programme — machinery landed 2026-10-10
- **Second external anchor (Example 20, Lyon 15 July).** `tests/reference_data/fao56_examples.csv` now carries two published rows; the sidecar meta.json is at v3 (sha256 843d1ff0…). `engine/tests/test_fao56_example20_missing_data.py` pins PM ET0 = 4.56 ± 0.05, Hargreaves = 5.0 ± 0.10, Ra = 40.55 and the eq.-50 estimate 22.29.
- **Mutation sensitivity (programme item 6).** `engine/tests/test_mutation_sensitivity.py` proves each anchor accepts the published value and rejects a 2–10 % constant mutation for six monitored constants (eq. 6 terms, eq. 21 Ra, Rns albedo, eq. 52, SCS-CN S, RothC temperature factor), so a vacuous anchor test cannot pass silently.
- **Machine evidence (programme item 7).** `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` classifies every formula family E/R/I/N with citations; `engine/tests/test_machine_evidence_consistency.py` asserts registry claims agree with it — currently pinning 10 models that claim `validated` without an external anchor as a shrinking debt set (two were retired by the concurrent work during this audit: CANON-009, CANON-011, and CANON-015 mid-run).
- **Independent oracle self-correction.** The Example-18 oracle's eq.-7 exponent is 5.26 (FAO), not 5.54; recorded in-file (G-H13).

---

## 11. Bottom line for the spec's ECO-10/ECO-17 status

The engine's **Priority-1 chain is implemented and its core equations are externally anchored where it matters most** (PM ET0 against the primary FAO-56 source; SCS-CN against NEH; RUSLE-LS against AH-703). What is **not** true, and this register now records, is the claim of broad validation: 5 of the 7 S3 models and 20 of the 25 corpus "matches" rest on regression anchors or internal consistency, six families carry `status: validated` without any run, 56 test paths cited as evidence do not exist, a dashboard reports green for never-run cases, and several documented/carded equations differ from the code they document. The correctness of the arithmetic is in far better shape than the truthfulness of the labels: closing the labels (P0), wiring or retiring the dead anchors and phantom paths (P1), and consolidating divergent duplicates (P2) is the remaining work before a `PASS_INTEGRATION_READY` verdict would be honest.
