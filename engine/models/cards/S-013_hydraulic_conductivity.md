# Model Card: S-013 — Hydraulic Conductivity (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-013` |
| **name** | Hydraulic Conductivity |
| **version** | `1.0.0` |
| **scientific_domain** | Soil Physics / Hydrogeology |
| **intended_use** | C++ kernel exposing hydraulic conductivity calculation from soil properties. Used in Richards equation solver and groundwater models. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | For saturated conditions: K = K_sat (saturated hydraulic conductivity). For unsaturated conditions via Mualem-van Genuchten:<br>K(θ) = K_s · S_e^0.5 · [1 − (1 − S_e^{1/m})^m]²<br>where S_e = (θ − θ_r)/(θ_s − θ_r), m = 1 − 1/n. |
| **equation_conventions** | K in cm/day. θ in cm³/cm³. Pressure head in cm. Parameters from Carsel & Parrish (1988). |
| **assumptions** | Same as CANON-006 (Van Genuchten). |
| **applicability_domain** | 12 USDA soil textures. Unsaturated zone. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `pressure_head_cm` (float, cm), `texture` (str) or (theta_r, theta_s, alpha, n, k_sat) |
| **output_schema** | `k` (float, cm/day, 0 ≤ k ≤ k_sat) |
| **units** | Pressure in cm, conductivity in cm/day. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of Mualem-van Genuchten conductivity function. |
| **solver_configuration** | C++ kernel (`soil.cpp`). No Python fallback (`_py_not_implemented`). |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Mualem, Y. (1976). WRR 12:513–522. van Genuchten, M.T. (1980). SSSAJ 44(5):892–898. Carsel, R.F., Parrish, R.S. (1988). |
| **reference_cases** | Canberra clay soil parameters. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_soil_unit.cpp` (NOT run; no compiler). |
| **analytical_tests** | Not executable (no Python fallback). |
| **numerical_tests** | Not executable. |
| **physical_consistency_tests** | Not executable. |
| **empirical_validation** | Not executable. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Not measurable — no Python comparison path. |
| **known_limitations** | (1) No Python fallback. (2) C++ unit test not run. (3) See CANON-006 and CANON-017. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled) — `engine/cpp_core/src/soil.cpp`. Bridge: no Python fallback. |
| **verification_status** | Cannot verify at runtime. |
| **validation_status** | Cannot validate at runtime. |
| **provenance** | `data_source: "simulated"`; `model: "Hydraulic Conductivity C++ v1.0"`; `computed: True` |

