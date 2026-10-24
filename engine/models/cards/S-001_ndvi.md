# Model Card: S-001 — Normalised Difference Vegetation Index (NDVI)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-001` |
| **name** | Normalised Difference Vegetation Index (NDVI) |
| **version** | `1.0.0` |
| **scientific_domain** | Remote Sensing / Vegetation Index |
| **intended_use** | Quantify vegetation greenness and health from multispectral imagery. Used as input to drought indices, phenology detection, and crop water models. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | NDVI = (NIR − Red) / (NIR + Red), where NIR = near-infrared reflectance, Red = red-band reflectance. Output dimensionless, range [−1, 1]. |
| **equation_conventions** | Reflectance values in [0, 1]. NDVI clipped to [−1, 1]. Zero-denominator (NIR+Red = 0) returns 0. |
| **assumptions** | (1) Reflectance values are atmospherically corrected (surface reflectance). (2) Band alignment is correct. |
| **applicability_domain** | Vegetation monitoring. Valid for cloud-free, sun-lit surfaces. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `red` (float or array, reflectance, 0–1), `nir` (float or array, reflectance, 0–1) |
| **output_schema** | `ndvi` (float or array, dimensionless, [−1, 1]) |
| **units** | Dimensionless input and output. |

---

## 4. Initial & Boundary Conditions

Not applicable — diagnostic index.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form arithmetic mean ratio. |
| **solver_configuration** | C++ kernel (`indices.cpp`), Python fallback (`_py_ndvi`), Numba twin (`ndvi_fast`). Dispatch: Numba for <1M elements, C++ for ≥1M. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Rouse, J.W. et al. (1974). "Monitoring Vegetation Success — Red and Reflected Illumination." NASA CR-144397. |
| **reference_cases** | Closed form: NDVI = (NIR−Red)/(NIR+Red). |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_indices_unit.cpp`; `tests/unit/test_bridge_signature_contract.py::test_index_backends_agree` |
| **analytical_tests** | Known inputs: Red=0.1, NIR=0.5 → NDVI=0.667 |
| **numerical_tests** | C++/Python/Numba agree to 0.0 absolute. |
| **physical_consistency_tests** | Output in [−1, 1]; zero denominator returns 0. |
| **empirical_validation** | Standard index, verified against closed-form arithmetic. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend dispatch telemetry. No formal UQ on reflectance inputs. |
| **known_limitations** | (1) Sensitive to atmospheric effects if surface reflectance is not used. (2) Saturation in dense vegetation. (3) C++ kernel cannot be rebuilt (no compiler). (4) Python fallback previously added 1e-10 epsilon (biased results); fixed to match native exactly. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++: `engine/cpp_core/src/indices.cpp`; Python: `engine/hydroma/cpp_bridge/__init__.py` (`_py_ndvi`); Numba: `indices_fast.py`. |
| **verification_status** | Verified — all backends agree to 0.0 absolute. |
| **validation_status** | Matches closed-form definition. |
| **provenance** | `data_source: "simulated"`; `model: "NDVI S-001 v1.0"`; `computed: True` |
