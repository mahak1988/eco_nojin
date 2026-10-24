# Model Card: S-005 — Normalised Difference Burn Ratio (NBR)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-005` |
| **name** | Normalised Difference Burn Ratio (NBR) |
| **version** | `1.0.0` |
| **scientific_domain** | Remote Sensing / Burn Index |
| **intended_use** | Map burned areas and assess fire severity by comparing NIR and SWIR reflectance before and after fire events. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | NBR = (NIR − SWIR) / (NIR + SWIR), where SWIR = shortwave infrared reflectance. Output dimensionless, range [−1, 1]. |
| **equation_conventions** | Reflectance in [0, 1]. Vegetation has high NIR and low SWIR → high NBR. Burned areas have lower NIR and higher SWIR → low NBR. Clipped to [−1, 1]. |
| **assumptions** | (1) Atmospherically corrected surface reflectance. (2) NIR and SWIR bands from the same date. |
| **applicability_domain** | Burn severity mapping, fire recovery monitoring. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `nir` (float/array, 0–1), `swir` (float/array, 0–1) |
| **output_schema** | `nbr` (float/array, dimensionless, [−1, 1]) |
| **units** | Dimensionless. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form arithmetic. |
| **solver_configuration** | C++ kernel (`indices.cpp`), Python fallback (`_py_nbr`). No Numba twin. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Key, C.H., Benson, N.A. (2006). "A Quantification of the Relationship Between Burned Area and Fire Severity." *Remote Sensing of Environment* 109(1): 1–16. |
| **reference_cases** | Closed form: (NIR−SWIR)/(NIR+SWIR). |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_indices_unit.cpp`; `tests/unit/test_bridge_signature_contract.py::test_index_backends_agree` |
| **analytical_tests** | Known inputs yield expected NBR. |
| **numerical_tests** | C++/Python agree to 0.0 absolute. |
| **physical_consistency_tests** | Output in [−1, 1]; zero denominator returns 0. |
| **empirical_validation** | Matches Key & Benson (2006) closed form. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend telemetry. No formal UQ. |
| **known_limitations** | (1) Sensitive to atmospheric correction. (2) C++ kernel cannot be rebuilt (no compiler). (3) No Numba twin. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++: `indices.cpp`; Python: `_py_nbr`. |
| **verification_status** | Verified — backends agree to 0.0 absolute. |
| **validation_status** | Matches Key & Benson (2006) closed form. |
| **provenance** | `data_source: "simulated"`; `model: "NBR S-005 v1.0"`; `computed: True` |
