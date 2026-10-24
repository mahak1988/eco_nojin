# Model Card: CANON-002 — Hargreaves Reference Evapotranspiration (ET0)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-002` |
| **name** | Hargreaves Reference Evapotranspiration |
| **version** | `1.0.0` |
| **scientific_domain** | Evapotranspiration |
| **intended_use** | Estimate reference ET0 with minimal meteorological inputs (temperature and extraterrestrial radiation only). Used as a simplified alternative when wind and humidity data are unavailable. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | FAO-56 equation 52 (Allen et al. 1998, ch. 4):<br>ET0 = 0.0023 * (Tmean + 17.8) * (Tmax − Tmin)^0.5 * Ra<br>where: Tmean = (Tmax+Tmin)/2, Ra = extraterrestrial radiation (MJ/m²/day) from FAO-56 eq. 21, converted to mm/day by eq. 40 (Ra[mm/day] = 0.408 * Ra[MJ/m²/day]).<br>Units: ET0 in mm/day, temperatures in °C, Ra in MJ/m²/day. |
| **equation_conventions** | The 0.0023 coefficient converts the product to mm/day; the 0.408 factor performs the MJ/m²/day to mm/day conversion and the engine owns it. T range is (°C), Ra range is (MJ/m²/day). The equation assumes the same reference surface as FAO-56 Penman-Monteith (well-watered grass). |
| **assumptions** | (1) Reference grass crop (same as FAO-56 PM). (2) Wind and humidity effects are implicitly captured through temperature range (diurnal temperature difference as a proxy). (3) Adequate water supply at the reference surface. (4) Solar radiation approximated by extraterrestrial radiation (no cloud correction). |
| **applicability_domain** | Originally calibrated for California and Mediterranean climates. Requires at least a thermometer and latitude/DOY for Ra. Not recommended where solar radiation data is available (use PM instead). Best validated for temperate regions; local calibration may be needed in arid or tropical regions. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `tmin` (float, °C, −30..50), `tmax` (float, °C, −30..50), `lat_deg` (float, degrees, −90..90), `doy` (int, 1..365) |
| **output_schema** | `et0` (float, mm/day, ≥0) |
| **units** | Temperature in °C, latitude in degrees, DOY dimensionless. Ra computed internally. Output ET0 in mm/day. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — steady-state (daily) diagnostic model. No state variables carried between timesteps. |
| **boundary_conditions** | Not applicable — latitude and DOY prescribed as meteorological/geometric inputs. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form analytical equation; no numerical integration. |
| **solver_configuration** | Not applicable — direct evaluation. |
| **convergence_criteria** | Not applicable — no iterative solver. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Hargreaves, G.H., Samani, Z.A. (1985). "An Empirical Method of Estimating Evapotranspiration." *Applied Engineering in Agriculture* 1(2): 93–96. Also: Hargreaves, G.H., Allen, R.G., (2003). "Analysis of potential and actual evapotranspiration in a semi-arid environment." *Journal of Irrigation and Drainage Engineering*. |
| **reference_cases** | FAO-56 Appendix 2 worked example, using the same meteorological conditions as CANON-001. See `strict_tests/conftest.py:FAO56_REFERENCE_DAY`. Also Hargreaves (1985) original paper examples for California conditions. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s02_climate_et0.py` (alt path) — checks Hargreaves ET0 against the FAO-56 reference day. `engine/cpp_core/tests/test_climate_unit.cpp` — C++ unit test (exists but NOT run; no compiler available). |
| **analytical_tests** | FAO-56 Appendix 2 comparison with CANON-001; expected to differ by <30% for temperate conditions. |
| **numerical_tests** | Property-based bounds check: ET0 should be positive and below the equilibrium evaporation estimate. |
| **physical_consistency_tests** | ET0 ≥ 0; diurnal temperature range (Tmax − Tmin) > 0; Ra computed via independent FAO-56 eq. 21 integration. |
| **empirical_validation** | Not locally calibrated. Requires local validation for Iran and other non-temperate regions (per HYDROMA_MODEL_INVENTORY.md). |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity via property-based testing. No formal Monte Carlo UQ. |
| **known_limitations** | (1) Scientific status: REQUIRES_SCIENTIFIC_REVIEW — needs local validation outside temperate climates. (2) No Python fallback in the C++ bridge (fallback raises NotImplementedError). (3) C++ unit test not run (no compiler). (4) Uses extraterrestrial radiation instead of actual solar radiation, so overcast/cloudy days produce higher ET0 than PM would. (3) The 0.0023 coefficient and 17.8 offset are empirical; the model may overestimate ET0 in humid regions and underestimate in windy climates. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — implemented in `engine/hydroma/climate/et_calculator.py` (hargreaves_et0 method). C++ kernel in `engine/cpp_core/src/climate.cpp`. |
| **verification_status** | Implementation matches design. The C++ unit test is not executed here — the "(no compiler)" reason recorded for this line is stale for this host, where `engine.hydroma.cpp_bridge.backend_status()` reports `{'backend': 'cpp', 'cpp_available': True, 'import_error': None}` (the prebuilt extension loads; the build toolchain is simply never invoked, so the `.pyd` is not rebuilt). The FAO-56 reference-day check in `strict_tests/test_s02_climate_et0.py` covers the Python path. |
| **validation_status** | **VALIDATED_METHOD** — validated against the published FAO-56 equations 52, 40 and 21, evaluated from first principles with the evidence record `engine/validation/CANON-002.md`, whose reference values are re-derived independently of the engine in `engine/validation/test_validation_records.py`. The record establishes method conformance over 10.44 - 41.09 MJ/m2/day of extraterrestrial radiation; it does not compare any measured ET0, so the estimator's climate-dependent bias against Penman-Monteith is untouched by it and the local-calibration limitation above stands. |
| **provenance** | `data_source: "simulated"`; `model: "Hargreaves ET0 v1.0"`; `computed: True` |
| **validation_record** | `engine/validation/CANON-002.md` |
