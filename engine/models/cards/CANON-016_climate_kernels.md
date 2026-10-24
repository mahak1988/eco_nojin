# Model Card: CANON-016 — Climate Kernels (C++)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-016` |
| **name** | Climate Kernels (C++) |
| **version** | `1.0.0` |
| **scientific_domain** | Numerical (Climate Science) |
| **intended_use** | High-performance C++ kernels for atmospheric and climate-related calculations: reference ET (Penman-Monteith, Hargreaves), extraterrestrial radiation, net radiation, and related meteorological computations. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | C++ implementations of: (1) FAO-56 Penman-Monteith ET0 (CANON-001), (2) Hargreaves ET0 (CANON-002), (3) Extraterrestrial radiation Ra (FAO-56 eq. 21), (4) FAO-56 net shortwave and longwave radiation (Rn). Full equations identical to CANON-001–CANON-011. Source: `engine/cpp_core/src/climate.cpp`. |
| **equation_conventions** | Same as CANON-001–CANON-011. C++ uses double precision (64-bit float). Parameter order in native bindings: `penman_monteith_et0(t_min, t_max, rh_mean_pct, u2, rs_mj, elevation_m, lat_deg, doy)`. |
| **assumptions** | Same as CANON-001–CANON-011. |
| **applicability_domain** | Same as CANON-001–CANON-011. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | Scalar or array inputs (via `_array` variants): temperature (tmin, tmax, °C), humidity (rh_mean_pct, %), wind (u2, m/s), radiation (rs_mj, MJ/m²/day), elevation (m), latitude (degrees), day of year (int). |
| **output_schema** | `et0` (mm/day), `ra` (MJ/m²/day), `rn` (MJ/m²/day), `rnl` (MJ/m²/day) |
| **units** | Same as parent CANON models. SI throughout. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable. |
| **boundary_conditions** | Meteorological inputs prescribed. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of closed-form equations. No discretization. Vectorized via `_array` bindings using `py::array_t<double>`. |
| **solver_configuration** | C++ with pybind11 bindings. Backend selection via `_with_telemetry` dispatcher: Numba for small arrays (<1M elements), C++ for large arrays. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Allen, R.G. et al. (1998). FAO Irrigation and Drainage Paper 56. §§ 6–14. |
| **reference_cases** | FAO-56 Chapter 3 worked example. See conftest.py `FAO56_REFERENCE_DAY`. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_climate_unit.cpp` — C++ unit tests (exist but NOT run; no compiler). `strict_tests/test_s02_climate_et0.py` — Python parity. `tests/unit/test_bridge_signature_contract.py::test_penman_monteith_backends_agree` — C++/Python parity. |
| **analytical_tests** | FAO-56 reference day. |
| **numerical_tests** | 5 conditions including overcast winter days; C++/Python agree to 0.0 relative. |
| **physical_consistency_tests** | ET0 ≥ 0; Ra bounded by extraterrestrial limits. |
| **empirical_validation** | Validated against FAO-56 worked examples (Python parity). C++ unit test not run. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend dispatch telemetry. No formal UQ. |
| **known_limitations** | (1) Scientific status: VERIFIED but **partial runtime** — `.pyd` loads 61 symbols but cannot be rebuilt (no compiler). (2) Three defects reconciled in C++ kernel: es formula, delta formula, temperature constant (273 vs 273.16). (3) Parameter order swap between C++ and Python was corrected. (4) Cloudiness factor clipping fixed. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled). `engine/cpp_core/src/climate.cpp` (source), `engine/hydroma/cpp_bridge/__init__.py` (bridge). |
| **verification_status** | Verified — C++/Python parity confirmed. C++ unit test exists but cannot execute. |
| **validation_status** | Validated against FAO-56 (via Python parity). |
| **provenance** | `data_source: "simulated"`; `model: "Climate Kernels C++ v1.0"`; `computed: True` |
