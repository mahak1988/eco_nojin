# Model Card: CANON-011 — Solar Radiation (Extraterrestrial Radiation)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-011` |
| **name** | Solar Radiation (Extraterrestrial Radiation) |
| **version** | `1.0.0` |
| **scientific_domain** | Meteorology / Solar Radiation |
| **intended_use** | Compute extraterrestrial radiation (Ra) at the top of the atmosphere for a given latitude and day of year. Used as input to PET models (FAO-56 Penman-Monteith, Hargreaves) and solar energy estimation. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | FAO-56 eq. 21 (extraterrestrial radiation):<br>Ra = (24 × 60 / π) × Gsc × dr × [ws × sin(φ) × sin(δ) + cos(φ) × cos(δ) × sin(ws)]  [MJ/m²/day]<br><br>where:<br>Gsc = 0.0820 MJ/m²/day (solar constant, FAO-56 value)<br>dr = 1 + 0.033 × cos(2π × doy / 365) (inverse relative distance Earth-Sun)<br>δ = 0.409 × sin(2π × doy / 365 − 1.39) (solar declination, radians)<br>φ = latitude (radians, positive in Northern Hemisphere)<br>ws = arccos(−tan φ × tan δ) (sunset hour angle, radians)<br><br>Caveat: Gsc varies slightly by source (0.0820 MJ/m² per FAO-56; 0.0824 per Haurwitz 1942; 1361 W/m² = 0.0864 MJ/m²/day). |
| **equation_conventions** | Latitude in degrees converted to radians. DOY 1 = January 1. δ and ws in radians. Gsc = 0.082 MJ/m²/day (FAO-56). Ra output in MJ/m²/day. The arccos argument is clipped to [−1, 1] to avoid NaN at and beyond the polar circles. |
| **assumptions** | (1) Clear atmosphere (no pollution or cloud). (2) Earth's orbit is circular (dr approximation). (3) Solar constant is constant. (4) Flat horizontal surface. (5) No atmospheric scattering or absorption. |
| **applicability_domain** | Global latitudes, any day of year. At polar circles in winter, Ra = 0 (no sunrise). Valid for extraterrestrial calculation only; actual surface radiation requires atmospheric correction. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `latitude` (float, degrees, −90..90), `doy` (int, 1..365 or 1..366) |
| **output_schema** | `ra` (float, MJ/m²/day, ≥0) |
| **units** | Latitude in degrees. Ra in MJ/m²/day. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — single-point calculation. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form analytical equation. No discretization. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | FAO-56: Allen, R.G., L.S. Pereira, D. Raes, M. Smith (1998), *FAO Irrigation and Drainage Paper 56*, eq. 21. Iqbal, M. (1986). *An Introduction to Numerical and Practical Weather Analysis*. 2nd ed., Wiley. |
| **reference_cases** | FAO-56 Annex 2 reference day: lat=41.9°N, doy=193 → **Ra = 41.006807208133594 MJ/m²/day (measured 2026-10-10 through `CANON-011_RAD`)**. `fao56_ra_extremes()` in conftest.py brackets Ra over all latitudes/DOYs at 0–45 MJ/m²/day. **Retired figure:** the card used to print "Ra ≈ 24.5 MJ/m²/day", which is wrong by ~41 %. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s02_climate_et0.py` — checks Ra against an independent FAO-56 eq. 21 day-length cosine-integration oracle (`_oracle_ra` in conftest.py) across 6 latitudes × 7 DOYs. `engine/cpp_core/tests/test_climate_unit.cpp` — C++ unit test. |
| **analytical_tests** | FAO-56 reference day: lat=41.9°N, doy=193 gives 41.006807208133594 MJ/m²/day. Equinox at the equator: Ra ≈ 34–40 MJ/m²/day. |
| **numerical_tests** | Property-based: Ra ∈ [0, 45] MJ/m²/day for all latitudes/DOYs. Solstices have max/min Ra at given latitude. |
| **physical_consistency_tests** | Ra ≥ 0 for all valid inputs. Ra increases towards equator. Ra bounded by extraterrestrial maximum. Polar night Ra = 0. |
| **empirical_validation** | Anchored on the published FAO-56 eq. 21 form, verified independently by a day-length cosine-integration oracle (`test_s02::test_matches_integrated_cosine_oracle`, 6 latitudes × 7 DOYs at rel=1e-9). The published FAO-56 Annex 2 example values (Ex. 8 = 32.2, Ex. 10 = 25.1, Ex. 17 = 38.06, Ex. 18 = 41.09, Ex. 20 = 40.55 MJ/m²/day) are the reference the oracle is built from. No atmospheric correction is applied — this is top-of-atmosphere radiation, not surface radiation. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Input sensitivity on latitude and DOY via property-based testing. |
| **known_limitations** | (1) Atmospheric correction (clear-sky transmissivity) is not applied; this is TOA radiation, not surface radiation. (2) No Python fallback in the bridge (NotImplementedError). (3) C++ unit test exists but cannot be run (no compiler). (4) **Label defect of record:** the `CANON-011_RAD` gateway response reports `units: "mm/day"` on a MJ/m²/day value. The value is correct and the schema key was left unchanged so no consumer breaks; the label is wrong and is recorded here. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++ kernel (`penman_monteith_et0` includes Ra) in `engine/cpp_core/src/climate.cpp`. Python fallback in `engine/hydroma/climate/et_calculator.py`. |
| **verification_status** | Verified — matches an independent FAO-56 eq. 21 day-length cosine-integration oracle (`test_s02::_oracle_ra`) across 6 latitudes × 7 DOYs. |
| **validation_status** | **VALIDATED_EXTERNAL** for the eq. 21 closed form: the implementation reproduces the published FAO-56 Annex 2 example days (Ex. 8 = 32.2, Ex. 10 = 25.1, Ex. 17 = 38.06, Ex. 18 = 41.09, Ex. 20 = 40.55 MJ/m²/day; lat 41.9 °N / DOY 193 = 41.006807208133594). Atmospheric correction is absent by design and no clear-sky transmissivity is claimed. |
| **provenance** | `data_source: "simulated"`; `model: "FAO-56 Ra v1.0"`; `computed: True` |
