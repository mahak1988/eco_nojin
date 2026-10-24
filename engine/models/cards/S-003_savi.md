# Model Card: S-003 — Soil-Adjusted Vegetation Index (SAVI)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-003` |
| **name** | Soil-Adjusted Vegetation Index (SAVI) |
| **version** | `1.0.0` |
| **scientific_domain** | Remote Sensing / Vegetation Index |
| **intended_use** | Minimise soil brightness influence on vegetation indices in areas with sparse vegetation. Used with Landsat and similar sensors. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | SAVI = ((NIR − Red) / (NIR + Red + L)) × (1 + L), where L = soil-brightness correction factor (default 0.5). Output dimensionless, range [−1, 1]. |
| **equation_conventions** | L = 0.5 (standard). Reflectance in [0, 1]. SAVI clipped to [−1, 1]. Zero denominator returns 0. |
| **assumptions** | (1) Atmospherically corrected surface reflectance. (2) L = 0.5 is the standard value for intermediate vegetation. |
| **applicability_domain** | Sparse to moderate vegetation. Best in arid and semi-arid regions. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `red` (float/array, 0–1), `nir` (float/array, 0–1), `L` (float, default 0.5) |
| **output_schema** | `savi` (float/array, dimensionless, [−1, 1]) |
| **units** | Dimensionless. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form arithmetic. |
| **solver_configuration** | C++ kernel (`indices.cpp`), Python fallback (`_py_savi`), Numba twin (`savi_fast`). Dispatch: Numba for <1M elements, C++ for ≥1M. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Huete, A.R. (1988). "A Soil-Adjusted Vegetation Index (SAVI)." *Remote Sensing of Environment* 25(3): 229–246. |
| **reference_cases** | Closed form: ((NIR−Red)/(NIR+Red+L)) × (1+L). |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_indices_unit.cpp`; `tests/unit/test_bridge_signature_contract.py::test_index_backends_agree` |
| **analytical_tests** | Known inputs with L=0.5 yield expected SAVI. |
| **numerical_tests** | C++/Python/Numba agree to 0.0 absolute after clip fix. |
| **physical_consistency_tests** | Output in [−1, 1]; zero denominator returns 0. |
| **empirical_validation** | Matches Huete (1988) closed form. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend telemetry. Choice of L introduces uncertainty; default 0.5 may not be optimal for all soil/surface types. |
| **known_limitations** | (1) L is a single scalar; not adaptive to soil type. (2) C++ kernel cannot be rebuilt (no compiler). |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++: `indices.cpp`; Python: `_py_savi`; Numba: `indices_fast.py` (`savi_fast`). |
| **verification_status** | Verified — backends agree to 0.0 absolute. |
| **validation_status** | Matches Huete (1988) closed form. |
| **provenance** | `data_source: "simulated"`; `model: "SAVI S-003 v1.0"`; `computed: True` |
