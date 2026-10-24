# Model Card: S-011 — Soil Water Content (C++ Symbol)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-011` |
| **name** | Soil Water Content |
| **version** | `1.0.0` |
| **scientific_domain** | Soil Physics |
| **intended_use** | C++ kernel exposing van Genuchten-based soil water content calculation (θ) for a given pressure head and soil texture. Used in crop water and hydrology models. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | See CANON-006. θ(h) = θ_r + (θ_s−θ_r)/(1+|α·h|^n)^m, m = 1−1/n. For h ≥ 0 (positive pressure): θ = θ_s (saturated). |
| **equation_conventions** | Pressure head in cm. θ in cm³/cm³. Parameters from Carsel & Parrish (1988). |
| **assumptions** | Same as CANON-006. |
| **applicability_domain** | 12 USDA soil textures. Same as CANON-006. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `pressure_head_cm` (float, cm, −1e6..0), `texture` (str) or individual params (theta_r, theta_s, alpha, n) |
| **output_schema** | `theta` (float, cm³/cm³, θ_r ≤ θ ≤ θ_s) |
| **units** | Pressure in cm, water content in cm³/cm³. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of van Genuchten retention. |
| **solver_configuration** | C++ kernel (`soil.cpp`). No Python fallback (`_py_not_implemented`). |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | See CANON-006. van Genuchten (1980); Carsel & Parrish (1988). |
| **reference_cases** | SAXTON_RAWLS_2006_AWC in conftest.py. |

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
| **known_limitations** | (1) No Python fallback. (2) C++ unit test not run. (3) See CANON-006 and CANON-017 for scientific limitations. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled) — `engine/cpp_core/src/soil.cpp`. Bridge: no Python fallback. |
| **verification_status** | Cannot verify at runtime. |
| **validation_status** | Cannot validate at runtime. |
| **provenance** | `data_source: "simulated"`; `model: "Soil Water Content C++ v1.0"`; `computed: True` |

