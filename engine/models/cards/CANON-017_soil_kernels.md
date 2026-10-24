# Model Card: CANON-017 — Soil Kernels (C++)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-017` |
| **name** | Soil Kernels (C++) |
| **version** | `1.0.0` |
>  | **scientific_domain** | Numerical (Soil Physics) |
| **intended_use** | High-performance C++ kernels for soil physics: van Genuchten water retention, Mualem unsaturated conductivity, soil parameter table lookup, hydraulic conductivity, soil erodibility K, specific moisture capacity. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | (1) van Genuchten retention: θ(h) = θ_r + (θ_s−θ_r) / (1+|αh|^n)^m, m = 1−1/n. (2) Mualem conductivity: K(h) = K_s·S_e^0.5·[1−(1−S_e^(1/m))^m]². (3) Specific moisture capacity: C(h) = dθ/dh. (4) Soil erodibility K from EPIC. (5) Hydraulic conductivity from Kozeny-Carman or Campbell. Source: `engine/cpp_core/src/soil.cpp`. |
| **equation_conventions** | Pressure head in cm. θ in cm³/cm³. K in cm/day. Parameters from Carsel & Parrish (1988) table embedded in C++ (`soil.cpp:24-32`). |
| **assumptions** | Same as CANON-006 Van Genuchten. |
| **applicability_domain** | 12 USDA soil textures. Same as CANON-006. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `pressure_head_cm` (float, cm, −1e6..0), `texture` (str), `theta_r`, `theta_s`, `alpha`, `n`, `ks` (optional overrides) |
| **output_schema** | `theta` (cm³/cm³), `k_unsat` (cm/day), `c` (specific moisture capacity, dimensionall) |
| **units** | Pressure in cm, water content in cm³/cm³, conductivity in cm/day. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable. |
| **boundary_conditions** | Pressure head prescribed. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Direct evaluation of closed-form equations. Vectorized via `_array` bindings. |
| **solver_configuration** | C++ with pybind11. Backend dispatch: C++ primary, Python fallback (where exists). |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | van Genuchten (1980); Mualem (1976); Carsel & Parrish (1988). See CANON-006. |
| **reference_cases** | SAXON_RAWLS_2006_AWC in conftest.py. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_soil_unit.cpp` — C++ unit tests (NOT run; no compiler). `strict_tests/test_s05_soil_retention.py` — Python parity. `tests/unit/test_bridge_signature_contract.py` — backend agreement. |
| **analytical_tests** | Saturation at h=0; bounded θ ∈ [θ_r, θ_s]; monotone approach to θ_r. |
| **numerical_tests** | Property-based checks on texture parameter ordering (K_s non-increasing coarse-to-fine). |
| **physical_consistency_tests** | θ_r ≤ θ ≤ θ_s; K ∈ [0, K_s]; AWC = θ_fc − θ_pwp matches Saxton-Rawls. |
| **empirical_validation** | Validated via Python parity against Saxton-Rawls AWC. C++ unit test not run. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend dispatch telemetry. No formal UQ on texture parameters. |
| **known_limitations** | (1) `.pyd` loads 61 symbols but cannot be rebuilt (no compiler). (2) Some functions (soil_water_content, hydraulic_conductivity, etc.) have `_py_not_implemented` as fallback — no Python path at all. (3) The FC_HEAD_CM discrepancy: physics.py uses 330.0 (10× outlier), water_retention.py uses 33 cm correctly. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production (C++ compiled). Source: `engine/cpp_core/src/soil.cpp`. Bridge: `engine/hydroma/cpp_bridge/__init__.py`. |
| **verification_status** | Verified via Python parity. C++ unit test not run. |
| **validation_status** | Validated against Saxton-Rawls via Python parity. |
| **provenance** | `data_source: "simulated"`; `model: "Soil Kernels C++ v1.0"`; `computed: True` |

