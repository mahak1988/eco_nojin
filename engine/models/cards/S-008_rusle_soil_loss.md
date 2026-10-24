# Model Card: S-008 — RUSLE Annual Soil Loss (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-008` |
| **name** | RUSLE Annual Soil Loss (C++ Symbol) |
| **version** | `1.0.0` |
| **scientific_domain** | Soil Erosion |
| **intended_use** | C++ kernel exposing the RUSLE soil loss calculation (see CANON-007 for full scientific description). |

---

## 2. Governing Equations and Conventions

| Field | Value |
>|-------|-------|
| **governing_equations** | See CANON-007. A = R × K × LS × C × P [t/ha/yr]. |
| **equation_conventions** | Same as CANON-007. |
| **assumptions** | Same as CANON-007. |
| **applicability_domain** | Same as CANON-007. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `R` (float, kJ·mm/ha/h, rainfall erosivity), `K` (float, t·ha·h/kJ·mm, soil erodibility), `LS` (float, dimensionless), `C` (float, 0–1, cover), `P` (float, 0–1, support practices) |
| **output_schema** | `A` (float, t/ha/yr, ≥0) |
| **units** | R in kJ·mm/ha/h, K in t·ha·h/kJ·mm, A in t/ha/yr. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form multiplication of five factors. |
| **solver_configuration** | C++ kernel (`erosion.cpp`) with Python fallback (`_py_rusle_annual_soil_loss`). Dispatch: C++ primary, Python fallback. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | See CANON-007. Renard et al. (1997), USDA Agriculture Handbook 703. |
| **reference_cases** | Worked R-factor example from Renard et al. (1997) AH-703. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_erosion_unit.cpp`; `tests/unit/test_rusle_uncorrelated.py` |
| **analytical_tests** | Worked example: known R, K, LS, C, P values → known A. |
| **numerical_tests** | C++/Python parity. Uncorrelated test checks each factor independently. |
| **physical_consistency_tests** | A ≥ 0; all factors within valid ranges. |
| **empirical_validation** | See CANON-007. Calibration factor of 0.10 removed (was uncited, 10× understatement). |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend telemetry. |
| **known_limitations** | (1) Previous uncited 0.10 calibration factor removed — was causing 10× reduction. (2) C++ kernel cannot be rebuilt (no compiler). (3) No Numba twin. See CANON-007 for full details. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++: `engine/cpp_core/src/erosion.cpp`; Python fallback: `_py_rusle_annual_soil_loss`. |
| **verification_status** | Verified — C++/Python parity confirmed after calibration factor removal. |
| **validation_status** | Framework validated (RUSLE). See CANON-007. |
| **provenance** | `data_source: "simulated"`; `model: "RUSLE C++ v1.0"`; `computed: True` |
