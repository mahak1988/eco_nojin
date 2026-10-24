# Model Card: S-007 — Penman-Monteith ET0 (C++ Symbol)

## 1. Identification

| Field | Value |
| **model_id** | `S-007` |
| **name** | Penman-Monteith ET0 (C++ Symbol) |
| **version** | `1.0.0` |
| **scientific_domain** | Evapotranspiration |
| **intended_use** | C++ kernel exposing the FAO-56 Penman-Monteith reference ET0 calculation (see CANON-001 for full scientific description). |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | See CANON-001. FAO-56 eqs. 6–14, full Penman-Monteith equation with es = (e0(Tmax)+e0(Tmin))/2, Δ = 4098·e0(Tmean)/(Tmean+237.3)², temperature conversion using 273. |
| **equation_conventions** | Same as CANON-001. C++ binding parameter order: (t_min, t_max, rh_mean_pct, u2, rs_mj, elevation_m, lat_deg, doy). |
| **assumptions** | Same as CANON-001. |
| **applicability_domain** | Same as CANON-001. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `t_min` (float, °C), `t_max` (float, °C), `rh_mean_pct` (float, %), `u2` (float, m/s), `rs_mj` (float, MJ/m²/day), `elevation_m` (float, m), `lat_deg` (float, degrees), `doy` (int) |
| **output_schema** | `et0` (float, mm/day, ≥0) |
| **units** | SI throughout. See CANON-001. |

---

## 4. Initial & Boundary Conditions

Not applicable — daily diagnostic.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of closed-form FAO-56 equations. |
| **solver_configuration** | C++ kernel (`climate.cpp`) with Python fallback (`_py_penman_monteith_et0`). Backend dispatch: scalar → C++, array → Numba if available else C++. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | See CANON-001. Allen, R.G. et al. (1998), FAO Irrigation and Drainage Paper 56. |
| **reference_cases** | See CANON-001 / `FAO56_REFERENCE_DAY`. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_climate_unit.cpp`; `strict_tests/test_s02_climate_et0.py`; `tests/unit/test_bridge_signature_contract.py::test_penman_monteith_backends_agree` |
| **analytical_tests** | FAO-56 reference day: expected ≈ 5.8 mm/day. |
| **numerical_tests** | 5 conditions including overcast winter days; C++/Python agree to 0.0 relative (after defects fixed). |
| **physical_consistency_tests** | ET0 ≥ 0; es ≥ ea; Rs/Rso ratio limited to [0.3, 1.0]. |
| **empirical_validation** | Validated against FAO-56 (Python parity). See CANON-001. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend telemetry. |
| **known_limitations** | (1) Three defects reconciled: es formula (eq. 11), Δ formula (eq. 13), temperature constant 273 (not 273.16). (2) Parameter order swap between C++ and Python (positions 4 and 5) was corrected. (3) Cloudiness factor clipping corrected to [0.3, 1.0] on the Rs/Rso ratio. (4) C++ kernel cannot be rebuilt (no compiler). See CANON-001 and CANON-016 for details. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++: `engine/cpp_core/src/climate.cpp`; Python fallback: `_py_penman_monteith_et0` in `engine/hydroma/cpp_bridge/__init__.py`. |
| **verification_status** | Verified — C++/Python parity confirmed to 0.0 relative across 5 conditions. |
| **validation_status** | Validated against FAO-56 worked examples (Python parity). |
| **provenance** | `data_source: "simulated"`; `model: "Penman-Monteith ET0 C++ v1.0"`; `computed: True` |

