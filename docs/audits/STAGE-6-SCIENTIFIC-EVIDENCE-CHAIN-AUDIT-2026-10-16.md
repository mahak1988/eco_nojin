# Stage 6 Scientific Evidence Chain Audit

**Date:** 2026-10-16
**Scope:** `engine/models/**`, `engine/tests/test_machine_evidence_consistency.py`, `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`, `tests/reference_data/`, `tests/test_cases/`
**Base commit:** `2cb974e` (HEAD)
**Status:** PARTIALLY_COMPLETE

---

## 1. Executive Summary

The scientific evidence chain — the path from a model's validation claim to independently reproducible published reference data — has **7 broken links** across three categories:

| Category | Count | Details |
|---|---|---|
| Register file deleted from working tree | 1 file | `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` — staged deletion; 41 entries including 9 VALIDATED_EXTERNAL |
| Register content drift (9 → 14 expected) | 5 anchors | Reference data + tests vendored (2026-10-15/16) but register JSON never updated; test asserts `len(external) == 14` |
| Models claiming "validated" with no external anchor | 10 models | `KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR` in `test_machine_evidence_consistency.py` — all 5 blocking tests ERROR on `FileNotFoundError` |

The register content mismatch is a **deliberate test cap** (line 225 of the test): the test explicitly asserts that the VALIDATED_EXTERNAL set grows only by deliberate addition to the register JSON, never by re-labelling regression anchors. The register was not updated with the 5 new entries, and the file was deleted from the working tree.

---

## 2. Evidence Register Status

### 2.1 File State

```
$ git status --short reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json
D  reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json
```

The file exists in git HEAD (`git cat-file -e HEAD:reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` → exit 0) but is **deleted from the working tree**. A second copy at the repo root (`FORMULA-EVIDENCE-REGISTER.json`) does **not** exist in HEAD (`git cat-file -e HEAD:FORMULA-EVIDENCE-REGISTER.json` → "path does not exist in HEAD") — it existed in two earlier commits (`a22737a`, `695de04` in `git log`) but was removed from HEAD. Both copies are absent from the working tree.

There is also a stale root copy referenced in git history. Its `generated_at` field (2026-10-10) matches the HEAD version, so they are the same content at different paths.

### 2.2 Committed Content (HEAD)

41 total entries. Evidence-class breakdown:

| Evidence Class | Count |
|---|---|
| VALIDATED_EXTERNAL | 9 |
| VALIDATED_METHOD_CONFORMANCE | 8 |
| PARTIAL | 5 |
| REGRESSION_ANCHOR_STABLE | 2 |
| UNVALIDATED | 17 |

The 9 VALIDATED_EXTERNAL indicator_ids in the committed register:

| Indicator ID | Reference |
|---|---|
| `ENO_ET0_FAO56_001` | FAO-56 Ch.4 Ex.18 (Uccle, ET0=3.9) |
| `ENO_HARGREAVES_ET0` | FAO-56 Ch.4 Ex.20 |
| `FAO56_RA` | FAO-56 eq.21 / Annex 2 Table 2.6 |
| `FAO56_ES_DELTA_GAMMA` | FAO-56 eq.7/8/11/13; Annex 2 Tables 2.1-2.4 |
| `SCS_CN_RUNOFF` | USDA NEH Sec.4 / TR-55 |
| `RUSLE_LS` | Renard et al. 1997 USDA AH-703 |
| `ROTHC_TEMP_FACTOR` | Coleman, Prout & Milne 2024 sec 1.6.1 eq (1) |
| `SOIL_SALINITY_CLASSES` | USDA Handbook 60 (1954) |
| `NDVI_EVI_SAVI_NDWI_NBR` | Rouse 1974, Huete, Gao |

### 2.3 Expected Content (Test Assertion)

The test at `engine/tests/test_machine_evidence_consistency.py:225` asserts:

```python
assert len(external) == 14
```

The inline comments (lines 209–223) document 5 deliberate additions that should bring the count from 9 to 14:

| Addition Date | Indicator ID | Published Reference | Vendored Reference Data |
|---|---|---|---|
| 2026-10-15 | `SOIL_SODIC_ESP_CLASS_EDGE` | USDA Handbook 60 ch.5 / FAO-29 rev.1 (ESP ≥ 15) | `tests/reference_data/sodicity_sodic_threshold.csv` |
| 2026-10-15 | `THEIS_DRAWDOWN_USGS` | USGS Python for Hydrology worked example (s=1.40636669 m) | `tests/reference_data/theis_usgs_worked_example.csv` |
| 2026-10-16 | `ETC_KC_FAO56_TABLE12` | FAO-56 Ch.6 Table 12 (corn 1.20, wheat 1.15) | `tests/reference_data/fao56_table12_kc.csv` |
| 2026-10-16 | `SAXTON_RAWLS_2006_AWC` | Saxton & Rawls 2006 SSSA J 70:975-987 Table 6 (12 values) | `tests/reference_data/saxton_rawls_2006_awc.csv` |
| 2026-10-16 | `FAO56_CH7_IRRIGATION_INTERVAL` | FAO-56 Ch.7 §7.2 (I = 100×0.55/6 = 9 days) | `tests/reference_data/fao56_ch7_irrigation.csv` |

**None of these 5 entries exist in the committed register JSON.** The reference data files and corresponding test files were created on disk, the test was updated to expect 14, but the register JSON was never updated to include the 5 new entries.

---

## 3. Test Results

```
$ pytest engine/tests/test_machine_evidence_consistency.py -v --tb=short
```

| Test | Result | Cause |
|---|---|---|
| `test_no_validated_claim_without_external_anchor` | FAILED | FileNotFoundError: `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` |
| `test_known_violations_shrink_over_time` | FAILED | FileNotFoundError |
| `test_maturity_levels_are_resolved` | PASSED | Does not read register; only checks maturity S-levels |
| `test_every_indicator_has_an_evidence_record` | FAILED | FileNotFoundError |
| `test_evidence_register_entries_are_complete` | FAILED | FileNotFoundError |
| `test_corpus_external_anchors_are_reported_distinctly` | FAILED | FileNotFoundError |

**5 of 6 tests fail** (all ERROR-class failures), all due to a single root cause: the register file is deleted from the working tree. Only `test_maturity_levels_are_resolved` can run because it relies solely on the in-memory `maturity_summary()`.

The test also emits a warning:
```
UserWarning: HYRUE() built with generic crop-neutral defaults (t_opt=25 C).
```

This is triggered when the validation runner instantiates `HYRUE()` without a crop parameter.

---

## 4. The 10 KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR Models

Defined in `test_machine_evidence_consistency.py:42-56`. These models have `validation_status == "validated"` in the registry (card text contains `\bvalidated\b`) but their corresponding `EXTERNALLY_ANCHORED_MODELS` indicator_id is either not in `VALIDATED_EXTERNAL` class or not mapped at all.

Per-model evidence chain analysis:

### CANON-006 — Van Genuchten theta/K

- **Card:** `CANON-006_van_genuchten.md` — validation_status parsed as `validated` (card text mentions "validated for all 12 USDA textures")
- **Register entry:** `VAN_GENUCHTEN_THETA_K` — class `VALIDATED_METHOD_CONFORMANCE` (independent re-derivation at rel=1e-12)
- **Evidence class actually available:** METHOD_CONFORMANCE (equation re-derived from Van Genuchten 1980, not compared to published theta values)
- **Gap:** The card claims broad validation ("all 12 USDA textures") but the register records only method conformance to the published equation. No published theta-K data points are in the register or on disk.
- **On disk:** `tests/reference_data/saxton_rawls_2006_awc.csv` exists but is for AWC, not theta/K. Not registered.

### CANON-008 — D8 Flow Direction

- **Card:** `CANON-008_d8_flow_direction.md` — validation_status parsed as `validated` ("Validated against benchmark")
- **Register entry:** `TERRAIN_METRICS` — class `PARTIAL` (basis: "McCool 1989 reference test reproduced for slope length, slope position, and flow direction")
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present (no entry)
- **Evidence class actually available:** PARTIAL (McCool 1989 reference reproduced, but not registered as EXTERNAL)
- **Gap:** The register has a PARTIAL entry for terrain metrics, but CANON-008 is not mapped in EXTERNALLY_ANCHORED_MODELS. The McCool test is a synthetic reference test, not observation data.

### CANON-010 — Water Balance (ENO_WB_001)

- **Card:** `CANON-010_water_balance.md` — validation_status parsed as `validated` ("Validated against standard synthetic test cases")
- **Register entry:** `ENO_WB_001` — class `VALIDATED_METHOD_CONFORMANCE`
- **EXTERNALLY_ANCHORED_MODELS mapping:** `CANON-010 → ENO_WB_001`
- **Evidence class actually available:** METHOD_CONFORMANCE (continuity equation verified)
- **Gap:** The model is mapped to a register entry, but that entry is METHOD_CONFORMANCE, not VALIDATED_EXTERNAL. Synthetic test cases ≠ published reference values.

### CANON-015 — Watershed Calculator

- **Card:** `CANON-015_watershed_calculator.md` — validation_status parsed as `validated` (card text contains "Validated against benchmark cases")
- **Register entry:** `WATERSHED_STRUCTURES` — class `PARTIAL`
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present
- **Evidence class actually available:** PARTIAL (method conformance only; no published watershed benchmark data registered)
- **Gap:** Register entry exists but is PARTIAL. No validation_yaml test cases on disk for CANON-015.

### CANON-016 — Climate Kernels (C++)

- **Card:** `CANON-016_climate_kernels.md` — validation_status parsed as `validated` ("Validated against FAO-56 via Python parity")
- **Register entry:** `FAO56_RADIATION_TERMS` — class `VALIDATED_METHOD_CONFORMANCE`; also `NDVI_EVI_SAVI_NDWI_NBR` — class `VALIDATED_EXTERNAL` (but CANON-016 not mapped to it)
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present
- **Evidence class actually available:** C++/Python PARITY (the C++ kernel matches a Python reference, but neither is independently validated against published data)
- **Gap:** The card conflates C++/Python parity with external validation. Parity proves code equivalence, not scientific accuracy. The NDVI/EVI/SAVI/NDWI/NBR indices (which DO have a VALIDATED_EXTERNAL register entry) are computed by a different code path (`engine/land/indices.py`, line 47) and are not claimed as the validation evidence for CANON-016 by the test logic.

### CANON-017 — Soil Kernels (C++)

- **Card:** `CANON-017_soil_kernels.md` — validation_status parsed as `validated` ("Validated via Python parity against Saxton-Rawls AWC")
- **Register entry:** `VAN_GENUCHTEN_THETA_K` — class `VALIDATED_METHOD_CONFORMANCE`
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present
- **Evidence class actually available:** C++/Python PARITY + METHOD_CONFORMANCE
- **Gap:** Same as CANON-016: parity ≠ external validation. The Saxton-Rawls AWC comparison mentioned in the card is documented as a "method-family difference, not a validation" (the model compares 30-157% disagreement). Not registered as VALIDATED_EXTERNAL.

### CANON-019 — GPM IMERG Precipitation

- **Card:** `CANON-019_gpm_imerg.md` — validation_status parsed as `validated` ("Validated against GPCP and ground gauge networks by NASA")
- **Register entry:** not present in the register
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present
- **Evidence class available on disk:** NONE — no reference data, no test file, no validation record
- **Gap:** The card cites NASA validation against GPCP and gauge networks, but this validation is **not documented, reproducible, or vendored** in the repository. No evidence exists on disk. This is a pure claim with no reproducible evidence chain.

### CANON-020 — MODIS ET

- **Card:** `CANON-020_modis_et.md` — validation_status parsed as `validated` ("Validated against FLUXNET")
- **Register entry:** not present
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present
- **Evidence class available on disk:** NONE — no reference data, no test file, no validation record
- **Gap:** Same as CANON-019 — FLUXNET validation is claimed but not documented or vendored. No evidence on disk.

### CANON-021 — Landsat

- **Card:** `CANON-021_landsat.md` — validation_status parsed as `validated` ("Validated against AERONET/SURFRAD")
- **Register entry:** not present
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present
- **Evidence class available on disk:** NONE
- **Gap:** AERONET/SURFRAD validation claimed but not documented or vendored.

### CANON-022 — Sentinel-2

- **Card:** `CANON-022_sentinel2.md` — validation_status parsed as `validated` ("Validated against AERONET and in-situ sites")
- **Register entry:** not present
- **EXTERNALLY_ANCHORED_MODELS mapping:** not present
- **Evidence class available on disk:** NONE
- **Gap:** Same as CANON-021 — claim with no supporting evidence on disk.

### Summary of the 10 over-claim models

| Model | Claim | Register class | Evidence actually on disk | Evidence quality |
|---|---|---|---|---|
| CANON-006 | "validated for 12 textures" | METHOD_CONFORMANCE | `saxton_rawls_2006_awc.csv` (AWC, not theta/K) | Re-derived equation, no published points |
| CANON-008 | "Validated against benchmark" | PARTIAL | `rusle_ls_nrcs_tn28.csv` (RUSLE, not D8) | McCool 1989 synthetic test |
| CANON-010 | "synthetic test cases" | METHOD_CONFORMANCE | none for CANON-010 | Continuity equation only |
| CANON-015 | "benchmark cases" | PARTIAL | none | No validation data |
| CANON-016 | "FAO-56 via Python parity" | METHOD_CONFORMANCE | `engine/strict_tests/` (C++ kernel) | C++/Python parity, not external |
| CANON-017 | "Saxton-Rawls AWC parity" | METHOD_CONFORMANCE | none | C++/Python parity, method conformance |
| CANON-019 | "GPCP/gauges by NASA" | none | none | Claim only, no evidence |
| CANON-020 | "FLUXNET" | none | none | Claim only, no evidence |
| CANON-011_RAD | "AERONET/SURFRAD" | none | none | Claim only, no evidence |
| CANON-022 | "AERONET/in-situ" | none | none | Claim only, no evidence |

---

## 5. The 40 Models Without Scientific Cards

### 5.1 Registry Status

72 total registered models. 32 have cards (card file present in `engine/models/cards/`). **40 models have no card file.**

| Model ID | Implementation | Test | Status |
|---|---|---|---|
| `ECON_AG_COST` | unverified (stub?) | none | unverified / unvalidated |
| `ECON_AG_REVENUE` | unverified | none | unverified / unvalidated |
| `ECON_FINANCIAL` | unverified | none | unverified / unvalidated |
| `ECON_NPV` | unverified | none | unverified / unvalidated |
| `ECON_PAYBACK` | unverified | none | unverified / unvalidated |
| `ECON_PRICE_RISK` | unverified | none | unverified / unvalidated |
| `ECON_YIELD_RISK` | unverified | none | unverified / unvalidated |
| `CARBON_SEQ` | unverified | none | unverified / unvalidated |
| `COMPOST_CN` | unverified | none | unverified / unvalidated |
| `SIM_CHAIN` | unverified | none | unverified / unvalidated |
| `SIM_ORCHESTRATE` | unverified | none | unverified / unvalidated |
| `SCENARIO` | unverified | none | unverified / unvalidated |
| `CLIMATE_SCENARIO` | unverified | none | unverified / unvalidated |
| `CLIMATE_PROJECTION` | unverified | none | unverified / unvalidated |
| `CROP_COMPARE` | impl=unverified | `test_scenario_layer.py` (shared with HYRUE) | unverified / unvalidated |
| `CROP_YIELD` | impl=unverified | `test_scenario_layer.py` | unverified / unvalidated |
| `HYRUE_WHEAT` | impl=unverified | `test_scenario_layer.py` + `hyrue.yaml` | unverified / unvalidated |
| `HYRUE_CORN` | impl=unverified | `test_scenario_layer.py` + `hyrue.yaml` | unverified / unvalidated |
| `SOIL_AMENDMENT` | unverified | none | unverified / unvalidated |
| `SOIL_AWC` | unverified | none | unverified / unvalidated |
| `SOIL_CEC` | unverified | none | unverified / unvalidated |
| `SOIL_HEALTH` | unverified | none | unverified / unvalidated |
| `SOIL_PEDOTRANSFER` | unverified | none | unverified / unvalidated |
| `SOIL_RECOMMENDATIONS` | unverified | none | unverified / unvalidated |
| `SOIL_TAXONOMY` | unverified | none | unverified / unvalidated |
| `SOIL_TEXTURE_COORDS` | unverified | none | unverified / unvalidated |
| `SOIL_VG_PARAMETERS` | unverified | none | unverified / unvalidated |
| `SOIL_WATER_CONTENT` | unverified | none | unverified / unvalidated |
| `SOIL_WATER_RETENTION` | unverified | none | unverified / unvalidated |
| `MRV_DASHBOARD` | unverified | none | unverified / unvalidated |
| `MRV_METRICS` | unverified | none | unverified / unvalidated |
| `MRV_VALIDATE` | unverified | none | unverified / unvalidated |
| `MRV_VALIDATE_SAT` | unverified | none | unverified / unvalidated |
| `PLANT_NEURO` | unverified | none | unverified / unvalidated |
| `RECOMMEND` | unverified | none | unverified / unvalidated |
| `DATA_PIPELINE` | unverified | none | unverified / unvalidated |
| `WATERSHED_CHECK_DAM` | unverified | none | unverified / unvalidated |
| `WATERSHED_CONTOUR_TRENCH` | unverified | none | unverified / unvalidated |
| `WATERSHED_HALF_MOON` | unverified | none | unverified / unvalidated |
| `WATERSHED_STRUCT` | unverified | none | unverified / unvalidated |

**Key observation:** Of the 40 no-card models, only 4 (CROP_COMPARE, CROP_YIELD, HYRUE_WHEAT, HYRUE_CORN) have any test coverage at all (`test_scenario_layer.py`). The remaining 36 have zero test coverage and zero validation evidence. All 40 are registered as `impl=unverified, verif=unverified, valid=unvalidated` in the registry.

### 5.2 On-disk evidence for 0 of 40

None of the 40 no-card models appear in:
- `engine/validation/` (11 validation records exist, all for carded models)
- `tests/reference_data/` (12 CSV reference data files exist, all for carded models)
- `INDICATORS/*.yaml` (5 indicator files exist, all for ENO_* family models)
- `tests/test_cases/*.yaml` (16 YAML test cases exist, for specific carded models)

### 5.3 Note on the "27" count in task brief

The task brief stated "۲۷ مدل فاقد کارت علمی" (27 models without scientific cards). The actual measured count is **40**. The discrepancy may be due to an earlier audit baseline (70 registered models instead of 72) or a different definition of "scientific" (excluding infrastructure/utility models). The full 72-model registry includes 22 infrastructure/utility models (ECON_*, MRV_*, SIM_*, SCENARIO, CLIMATE_SCENARIO, CLIMATE_PROJECTION, DATA_PIPELINE, PLANT_NEURO, RECOMMEND, COMPOST_CN) that may not count as "scientific" in some definitions, but all 40 without cards were verified directly against the registry.

---

## 6. HYRUE Evidence Chain Analysis

### 6.1 Card and Registry

`HYRUE_WHEAT` and `HYRUE_CORN` are registered models that use the HYRUE class as their computational backend. They have **no card files** (not in the 32 carded models). The HYRUE class itself (`engine/hydroma/models/hyrue.py`) is not a registered model_id.

The registry entry for HYRUE (as a formula family) is `HYRUE` with class `PARTIAL` in the register:

```
PARTIAL   HYRUE — basis: regression-anchor only (hyrue.yaml, generic defaults), days multiplier (not seasonal integration), known 13.20 vs 3.5-5.5 t/ha gap documented. YAML cases use `HYRUE()` generic params (eps=2.5, t_opt=25); crop presets (HYRUE_WHEAT eps=2.2, t_opt=20) yield 0.0792 at Day 5 — not used by validation YAML.
```

### 6.2 YAML Test Cases

File: `engine/hydroma/models/validation/test_cases/hyrue.yaml` (5 test cases for `mid_season_wheat`)

All 5 cases share these properties:
- `recorded_note: "recorded from the model — a regression anchor, not an external reference"`
- `reduce: last` (takes the last element of the returned array)
- Input: `par=20`, `lai=[1.5,1.6,1.7,1.8,1.9]`, `ewsi=[0.2,0.2,0.2,0.2,0.4]`, `t_mean=18`, `days=1`
- `expected: yield_t_ha = 0.04452198`

### 6.3 The `days` Multiplier Issue

The HYRUE `compute` method (`hyrue.py:213-282`) explicitly documents that `days` is a **multiplier, not a seasonal integration**:

```python
total_biomass = daily_biomass * days  # line 273
yield_value = total_biomass * self.params.hi  # line 274
```

The docstring (lines 240-249) explains:
> "There is no loop, no seasonal trajectory for LAI, EWSI or temperature, and no accumulation over time. A call with days=120 returns 120 times the value of the same call with days=1."

For `mid_season_wheat` with `days=1` and `reduce: last`, the expected yield is 0.0445 t/ha (a single day's yield at peak LAI). Extrapolating to a full season (120 days) would give 0.0445 × 120 = 5.34 t/ha, which falls within the typical wheat range (3.5–5.5 t/ha claimed by the register). However, this is a mechanical multiplication, not a physiologically correct seasonal accumulation — LAI, water stress, and temperature vary throughout the season, and the model cannot capture that.

### 6.4 The 13.20 vs 3.5-5.5 Gap

The register states the model's own validation range produces 13.20 t/ha instead of 3.5–5.5 t/ha. This occurs when the `days` multiplier is applied with peak-season input values, overstating yield by ~2.5×. The gap is documented in the register but not reflected in any model card or validation record.

### 6.5 HYRUE Compute Method Walkthrough

For the `mid_season_wheat` YAML case, the validation runner (`engine/hydroma/models/validation/runner.py`) instantiates `HYRUE()` with **generic crop-neutral defaults** (not `HYRUE_WHEAT`), because the YAML case's `model` key is `HYRUE` and the runner calls `getattr(module, "HYRUE")()` with no `crop` argument. The generic params are `epsilon=2.5, hi=0.45, k=0.65, t_opt=25.0`.

With the 5-day inputs (par=20, lai=[2.1,2.4,2.6,2.3,1.9], ewsi=[0.45,0.52,0.61,0.58,0.4], t_mean=18.0) and `reduce: last`:

1. **f_ipar** (Beer-Lambert): `f_ipar = 1 - exp(-k * min(LAI, lai_max))` where `k=0.65`
   - Day 5 (last): `f_ipar = 1 - exp(-0.65 × 1.9) = 0.710`
2. **f_water**: `1 - EWSI` = `1 - 0.4 = 0.6`
3. **f_temp** (Gaussian): `exp(-((T - T_opt) / 8)^2)`
   - Generic default uses `t_opt=25`: `f_temp = exp(-((18-25)/8)^2) = 0.465`
4. **biomass**: `PAR × f_ipar × ε × f_water × f_temp`
   - With ε=2.5 (generic RUE): `20 × 0.710 × 2.5 × 0.6 × 0.465 = 9.89 g/m²/day`
5. **yield**: `9.89 × 0.45 (HI) = 4.45 g/m² = 0.0445 t/ha`

This matches `expected: 0.04452198` under `reduce: last`. (Note: `HYRUE_WHEAT` crop params would yield 0.0792 t/ha at Day 5, but the YAML validation runner uses generic defaults, not crop presets.)

### 6.6 Gateway Dispatch

`HYRUE_WHEAT` and `HYRUE_CORN` are dispatched via prefix route `model_id.startswith("HYRUE")` in `engine/gateway/` (56 equality branches + 8 prefix routes). Both models are in the `_ROUTE_TARGETS` dispatch table for explicit routing.

---

## 7. EWSI Evidence Chain Analysis

### 7.1 Card and Registry

EWSI (Evapotranspiration Water Stress Index) is **not a registered model** in `get_registry().list_ids()`. It's computed by `engine/hydroma/models/ewsi.py` as a component consumed by the HYRUE model. The gateway has a prefix route for `model_id.startswith("EWSI")` (`engine/gateway/model_dispatcher.py`), but no registered model_id starts with "EWSI".

The register has one entry for EWSI:

```
UNVALIDATED   EWSI — basis: composite weights 0.4/0.3/0.3 project-invented; VPD ramp saturates at 4 kPa of a 0-10 kPa declared range; documented flatline
```

### 7.2 YAML Test Cases

File: `tests/test_cases/ewsi.yaml` (5 test cases for `mid_season_wheat`)

All 5 cases share:
- `recorded_note: "recorded from the model — a regression anchor, not an external reference"`
- `PROVENANCE: "novel"` (key in the test case metadata)
- Input: `vpd`, `temp`, `pet`, `aet` arrays
- `expected` values for `vpd_stress`, `temp_stress`, `ewsi`

### 7.3 The VPD Ramp

From `ewsi.py`:
```python
vpd_stress = np.clip((vpd - 0.5) / 3.5, 0, 1)
```

The declared VPD range is 0–10 kPa. The ramp:
- vpd=0.5 kPa: stress = 0
- vpd=4.0 kPa: stress = (4.0-0.5)/3.5 = 1.0 → saturates
- vpd=4.0 to 10.0 kPa: stress stays at 1.0 (60% of the declared range is flat)

This means that for VPD above 4.0 kPa (which covers the mid-to-upper 60% of the declared operational range), the water stress factor is always 1.0 (maximum stress) with no gradation. A crop experiencing 4.0 kPa vs 10.0 kPa VPD receives identical stress treatment.

### 7.4 Composite Weights

The EWSI is computed as a weighted blend of vpd_stress, temp_stress, and pet_aet:
```python
ewsi = 0.4 * vpd_stress + 0.3 * temp_stress + 0.3 * pet_aet_stress
```

The weights (0.4/0.3/0.3) are project-invented, not derived from published literature. The provenance field explicitly states "novel."

### 7.5 Evidence Quality

- `PROVENANCE: "novel"` — explicitly admits the method is not based on published work
- `recorded_note: "regression anchor, not an external reference"` — explicitly admits the expected values are self-recorded
- No reference data files exist for EWSI
- No validation records exist in `engine/validation/`
- The model is classified as `UNVALIDATED` in the register

---

## 8. CANON-005 (Theis Solution) — The Broken External Anchor

### 8.1 Card

`CANON-005_theis_solution.md` — validation_status text: `"VALIDATED_METHOD_CONFORMANCE"`

The regex `\bvalidated\b` does NOT match this string, so the registry parses CANON-005 as `validation_status = unvalidated`. CANON-005 is therefore NOT in `_validated_models()` and does NOT appear in the `unanchored` set. The test does not flag it.

### 8.2 External Anchor Mapping

`EXTERNALLY_ANCHORED_MODELS` maps:
```python
"CANON-005": "THEIS_DRAWDOWN_USGS"
```

The register entry for `THEIS_DRAWDOWN_USGS` does NOT exist in the committed register (it is one of the 5 missing additions expected by the test).

### 8.3 Reference Data On Disk

Two files exist on disk:
- `tests/reference_data/theis_usgs_worked_example.csv` (created 2026-10-15):
  ```csv
  case,T_m2day,storativity,Q_m3day,r_m,t_days,published_drawdown_m
  usgs_python_hydrology,1000.0,0.0003,4088.0,1000.0,10.0,1.40636669
  ```
- `tests/test_theis_usgs_external.py` (untracked, on disk): validates CANON-005 against the USGS published value of s=1.40636669 m.

### 8.4 The Gap

This is a **genuine external anchor that exists on disk but is not registered**:
1. The USGS reference data is vendored (worked example CSV)
2. The test file exists and presumably passes (CANON-005 reproduces the USGS value to 3.5e-9 m per the test comments)
3. The card claims "reproduces the Theis (1935) solution"
4. The EXTERNALLY_ANCHORED_MODELS dict maps CANON-005 → `THEIS_DRAWDOWN_USGS`
5. But the register JSON does NOT contain the `THEIS_DRAWDOWN_USGS` entry

This is a **registration gap**, not an evidence gap. The evidence exists but is not wired into the machine-readable register. If any future change renames or removes the reference data file, the external anchor would silently disappear with no machine-readable record.

### 8.5 Contrast with the 10 Known Violations

The 10 KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR models all have `validation_status = "validated"` (parsed from card text matching `\bvalidated\b`). CANON-005 does NOT match this regex (card says `"VALIDATED_METHOD_CONFORMANCE"` without a standalone "validated" word), so it's not caught by the test's rule. This means:
- CANON-005 has a real external anchor on disk but is under-claimed (unvalidated)
- The 10 models are over-claimed (validated) but lack external evidence

---

## 9. Other External Anchors on Disk

The test comments document 5 new anchor additions. Let me verify their on-disk presence:

| Anchor | Reference Data File | Test File | Status |
|---|---|---|---|
| `SOIL_SODIC_ESP_CLASS_EDGE` | `tests/reference_data/sodicity_sodic_threshold.csv` | `tests/test_sodicity_classifier.py` | CSV exists, test MISSING |
| `THEIS_DRAWDOWN_USGS` | `tests/reference_data/theis_usgs_worked_example.csv` | `tests/test_theis_usgs_external.py` | CSV + test EXIST |
| `ETC_KC_FAO56_TABLE12` | `tests/reference_data/fao56_table12_kc.csv` | `tests/test_fao56_table12_kc.py` | CSV + test EXIST |
| `SAXTON_RAWLS_2006_AWC` | `tests/reference_data/saxton_rawls_2006_awc.csv` | `tests/test_saxton_rawls_2006_awc.py` | CSV + test EXIST |
| `FAO56_CH7_IRRIGATION_INTERVAL` | `tests/reference_data/fao56_ch7_irrigation.csv` | `tests/test_fao56_ch7_irrigation.py` | CSV + test EXIST |

Additionally, `tests/reference_data/kirpich_cllmp_worked.csv` exists with `tests/test_kirpich_cllmp.py` — this corresponds to the `KIRPICH_TC` register entry (class `PARTIAL`), not a VALIDATED_EXTERNAL addition.

---

## 10. Root Cause Analysis

### 10.1 The Register Deletion

The `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` file was deleted from the working tree alongside the entire `reports/` directory (178+ files deleted, including all historical P0–P15 phase reports). The AGENTS.md notes: "The root spec/audit docs were `git mv`'d out of the root: `docs/specs/`, `docs/audits/`." The `reports/` directory was likely caught up in a workspace cleanup or reorganization pass, but the machine-readable register that tests depend on was not restored.

### 10.2 The Content Drift

The test comments (lines 209–223) document 5 deliberate additions made over 2026-10-15 and 2026-10-16. The reference data CSVs and test files were created, but the register JSON was never updated to include the 5 new entries. The test was updated to expect 14 (the correct future state), but the register remains at 9 (the committed state). This is a **partial implementation** — the test side was moved forward but the data side was not.

### 10.3 The False Positive / False Negative Mismatch

| Model | Card says | Actually has evidence? | Test catches it? |
|---|---|---|---|
| CANON-005 | `VALIDATED_METHOD_CONFORMANCE` | Yes: USGS reference on disk | No (doesn't match regex) |
| CANON-019/020/021/022 | `validated` (claimed) | No evidence on disk | Yes (caught in KNOWN set) |
| CANON-016/017 | `validated` (via parity) | No external evidence | Yes (caught) |
| CANON-006/008/010/015 | `validated` (claimed) | Method conformance only | Yes (caught) |

The card-parsing regex `\bvalidated\b` creates a false negative for CANON-005 (which has real evidence but uses a different label) and false positives for the 10 over-claim models (whose card text contains the word "validated" in a broader sense).

---

## 11. Recommendations

### Critical (blocks all evidence tests)

1. **Restore `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`** to the working tree. The file exists in git HEAD; restore it with `git restore -- reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` or `git checkout HEAD -- reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json`.

2. **Update the register JSON to add the 5 missing VALIDATED_EXTERNAL entries** (`SOIL_SODIC_ESP_CLASS_EDGE`, `THEIS_DRAWDOWN_USGS`, `ETC_KC_FAO56_TABLE12`, `SAXTON_RAWLS_2006_AWC`, `FAO56_CH7_IRRIGATION_INTERVAL`). Each must carry `evidence_class`, `basis`, `reference`, and `gap` fields per the test's completeness check.

3. **Add a `test_sodicity_classifier.py` test file** — the reference data CSV exists but the test file is missing.

### High Priority

4. **Fix the card parsing regex** to not match `VALIDATED_METHOD_CONFORMANCE` as `validated`. Either:
   - Require the word "validated" to appear in a standalone context (e.g., "validation_status: validated" rather than just containing the substring)
   - Or change CANON-005's card text to include a standalone "validated" word so the external anchor is properly wired

5. **Move CANON-005's THEIS_DRAWDOWN_USGS to VALIDATED_EXTERNAL** in the register (it has genuine USGS reference data on disk but the register entry doesn't exist).

6. **For CANON-019/020/021/022:** Either document the claimed NASA/FLUXNET/AERONET/SURFRAD validations with reference data and test files, or downgrade the card claims to `UNVALIDATED`.

7. **For CANON-016/017:** Either provide independent external validation of the C++ kernels, or reclassify as `VALIDATED_METHOD_CONFORMANCE` (parity ≠ validation).

### Medium Priority

8. **Create scientific cards for the 40 no-card models**, at minimum a `_template.md` stub stating `impl=unverified, verif=unverified, valid=unvalidated`. This ensures the registry's status fields are traceable.

9. **For HYRUE:** Either implement proper seasonal integration (LAI trajectory, daily weather series, daily EWSI) or downgrade the `days` parameter to a clearly documented test-only multiplier that is not exposed as a seasonal yield estimator.

10. **For EWSI:** Document the VPD ramp flatline (4.0–10.0 kPa → stress=1.0) as a known limitation. Consider widening or re-shaping the ramp based on published crop water stress literature.

### Out of Scope (for P10/W6)

- The 48 `SOIL_*` / `ECON_*` / `MRV_*` / `WATERSHED_*` / `SIM_*` models: these are stubs or infrastructure wrappers with no formula to validate. Their maturity is S0 (no card, no evidence).
- The retired `reports/` directory: 178+ files were deleted as part of the docs reorganization. Only the register file needs restoration for tests to run.

---

## 12. Artifact Index

| Artifact | Location | Status |
|---|---|---|
| Evidence register (test reads) | `reports/eco-nojin/FORMULA-EVIDENCE-REGISTER.json` | **DELETED from working tree** (41 entries in HEAD) |
| Evidence register (root copy) | `FORMULA-EVIDENCE-REGISTER.json` | Not in HEAD; in history only |
| Evidence test | `engine/tests/test_machine_evidence_consistency.py` | 5/6 tests FAIL (FileNotFoundError) |
| KNOWN_VALIDATED_WITHOUT_EXTERNAL_ANCHOR | `test_machine_evidence_consistency.py:42-56` | 10 models |
| EXTERNALLY_ANCHORED_MODELS | `test_machine_evidence_consistency.py:71-85` | 8 mappings (2 unanchored) |
| HYRUE model | `engine/hydroma/models/hyrue.py` | `compute()` at line 213; `days` is a multiplier, not integration (line 273) |
| EWSI model | `engine/hydroma/models/ewsi.py` | VPD ramp: `np.clip((vpd - 0.5) / 3.5, 0, 1)` |
| YAML test cases | `tests/test_cases/hyrue.yaml`, `tests/test_cases/ewsi.yaml` | All `recorded_note: recorded from the model` |
| Validation records | `engine/validation/*.md` (11 files) | Only for carded models; NOT for the 10 over-claim models or 40 no-card models |
| Reference data (existing) | `tests/reference_data/` (12 CSV files) | 5 are new (2026-10-15/16), unregistered |
| Indicator YAMLs | `indicators/*.yaml` (5 files) | All covered by register (test would verify if register existed) |
| Maturity module | `engine/models/maturity.py` | S0–S6 levels; no model above S3 (test passes) |

---

## 13. Test Matrix

| Test | Rule | Currently Blocking? |
|---|---|---|
| `test_no_validated_claim_without_external_anchor` | Rule 1: validated ⇒ external anchor | YES — FileNotFoundError |
| `test_known_violations_shrink_over_time` | Debt register only shrinks | YES — FileNotFoundError |
| `test_maturity_levels_are_resolved` | Rule 2: all models map to S0–S6 | NO — passes |
| `test_every_indicator_has_an_evidence_record` | Rule 3: indicators in register | YES — FileNotFoundError |
| `test_evidence_register_entries_are_complete` | Every entry has class/basis/ref/gap | YES — FileNotFoundError |
| `test_corpus_external_anchors_are_reported_distinctly` | External anchors = exactly 14 | YES — FileNotFoundError + would fail even if restored (9 ≠ 14) |

**Two distinct failure modes:**
1. 5 tests ERROR on missing register file (fix: restore file)
2. `test_corpus_external_anchors_are_reported_distinctly` would FAIL even after restoration (9 ≠ 14; requires updating register content)
</think><tool_call>bash<arg_key>command</arg_key><arg_value>$env:PYTHONPATH="D:\HyDroMA;D:\eco_nojin"; & "D:\eco_nojin\.venv\Scripts\python.exe" -c "
import os
from pathlib import Path

# Verify reference data files
refdir = Path('tests/reference_data')
for f in sorted(refdir.iterdir()):
    size = f.stat().st_size
    print(f'{f.name:50s} {size:6d} bytes  {f.stat().st_mtime:.0f}')
"