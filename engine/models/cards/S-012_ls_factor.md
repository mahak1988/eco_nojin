# Model Card: S-012 — LS Factor (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-012` |
| **name** | LS Factor (Slope Length × Steepness) |
| **version** | `1.0.0` |
| **scientific_domain** | Soil Erosion |
| **intended_use** | C++ kernel exposing the RUSLE LS factor calculation (see CANON-007 for full description). |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | See CANON-007. L = (λ/22.13)^m, S = slope steepness function, LS = L × S. |
| **equation_conventions** | Same as CANON-007. |
| **assumptions** | Same as CANON-007. |
| **applicability_domain** | Same as CANON-007. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `slope` (float, degrees or percent), `slope_length_m` (float, m, >0) |
| **output_schema** | `LS` (float, dimensionless, ≥0) |
| **units** | Slope in degrees or percent, length in metres. LS dimensionless. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of RUSLE LS equations. |
| **solver_configuration** | C++ kernel (`erosion.cpp`). No Python fallback (`_py_not_implemented`). |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | See CANON-007. Renard et al. (1997), USDA AH-703. |
| **reference_cases** | See CANON-007. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_erosion_unit.cpp` (NOT run; no compiler). |
| **analytical_tests** | Not executable (no Python fallback). |
| **numerical_tests** | Not executable. |
| **physical_consistency_tests** | Not executable. |
| **empirical_validation** | Not executable. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not measurable — no Python comparison path. |
| **known_limitations** | (1) No Python fallback. (2) C++ unit test not run. (3) See CANON-007 for scientific limitations. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled) — `engine/cpp_core/src/erosion.cpp`. Bridge: no Python fallback. |
| **verification_status** | Cannot verify at runtime. |
| **validation_status** | Cannot validate at runtime. |
| **provenance** | `data_source: "simulated"`; `model: "LS Factor C++ v1.0"`; `computed: True` |

