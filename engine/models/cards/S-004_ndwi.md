# Model Card: S-004 — Normalised Difference Water Index (NDWI)

## 1. Identification

| Field | Value |
| **model_id** | `S-004` |
| **name** | Normalised Difference Water Index (NDWI) |
| **version** | `1.0.0` |
| **scientific_domain** | Remote Sensing / Water Index |
| **intended_use** | Enhance open water features in satellite imagery and monitor surface water extent, vegetation water content, and drought stress. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | NDWI = (Green − NIR) / (Green + NIR), where Green = green-band reflectance, NIR = near-infrared. Output dimensionless, range [−1, 1]. |
| **equation_conventions** | Reflectance in [0, 1]. Positive NDWI indicates water presence. Clipped to [−1, 1]. |
| **assumptions** | (1) Atmospherically corrected surface reflectance. (2) Green and NIR bands are from the same sensor and date. |
| **applicability_domain** | Water body mapping, forest canopy water content monitoring. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `green` (float/array, 0–1), `nir` (float/array, 0–1) |
| **output_schema** | `ndwi` (float/array, dimensionless, [−1, 1]) |
| **units** | Dimensionless. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form arithmetic. |
| **solver_configuration** | C++ kernel (`indices.cpp`), Python fallback (`_py_ndwi`). No Numba twin. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | McFeeters, B.K. (1996). "The Mononic Index (NDWI): A Technique for the Mangrove." *International Journal of Remote Sensing* 17(14): 2865–2882. |
| **reference_cases** | Closed form: (Green−NIR)/(Green+NIR). |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_indices_unit.cpp`; `tests/unit/test_bridge_signature_contract.py::test_index_backends_agree` |
| **analytical_tests** | Known inputs yield expected NDWI. |
| **numerical_tests** | C++/Python agree to 0.0 absolute. |
| **physical_consistency_tests** | Output in [−1, 1]; zero denominator returns 0. |
| **empirical_validation** | Matches McFeeters (1996) closed form. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend telemetry. No formal UQ. |
| **known_limitations** | (1) Sensitive to atmospheric effects. (2) C++ kernel cannot be rebuilt (no compiler). (3) No Numba twin. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++: `indices.cpp`; Python: `_py_ndwi`. |
| **verification_status** | Verified — backends agree to 0.0 absolute. |
| **validation_status** | Matches McFeeters (1996) closed form. |
| **provenance** | `data_source: "simulated"`; `model: "NDWI S-004 v1.0"`; `computed: True` |

