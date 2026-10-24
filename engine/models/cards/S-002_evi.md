# Model Card: S-002 — Enhanced Vegetation Index (EVI)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `S-002` |
| **name** | Enhanced Vegetation Index (EVI) |
| **version** | `1.0.0` |
| **scientific_domain** | Remote Sensing / Vegetation Index |
| **intended_use** | Improve vegetation signal in areas with dense canopy and high atmospheric scattering. Used with MODIS and Landsat for global vegetation monitoring. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | EVI = 2.5 × (NIR − Red) / (NIR + 6×Red − 7.5×Blue + 1), where Blue = blue-band reflectance. Output dimensionless, range [−1, 1]. |
| **equation_conventions** | Reflectance in [0, 1]. The coefficient 2.5 scales the index to a similar range as NDVI. The +1 in the denominator prevents division by zero. The aerosol resistance term is built into the 6×Red − 7.5×Blue adjustment. |
| **assumptions** | (1) Atmospherically corrected surface reflectance. (2) Requires Blue, Red, and NIR bands simultaneously. |
| **applicability_domain** | Dense vegetation, high biomass. MODIS/Terra/Aqua and Landsat. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `red` (float/array, 0–1), `nir` (float/array, 0–1), `blue` (float/array, 0–1) |
| **output_schema** | `evi` (float/array, dimensionless, [−1, 1]) |
| **units** | Dimensionless. |

---

## 4. Initial & Boundary Conditions

Not applicable.

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form arithmetic. |
| **solver_configuration** | C++ kernel (`indices.cpp`), Python fallback (`_py_evi`), Numba twin (`evi_fast`). Dispatch: Numba for <1M elements, C++ for ≥1M. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Huete, A.R. et al. (2002). "Overview of the Radiometric and Biophysical Performance of Landsat Data." *Remote Sensing of Environment* 83(1): 19–33. |
| **reference_cases** | Closed form: 2.5(NIR−Red)/(NIR+6Red−7.5Blue+1). |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_indices_unit.cpp`; `tests/unit/test_bridge_signature_contract.py::test_index_backends_agree` |
| **analytical_tests** | Known inputs yield expected EVI. |
| **numerical_tests** | C++/Python/Numba agree to 2.2e-16 (double epsilon). |
| **physical_consistency_tests** | Output in [−1, 1]; zero-denominator returns 0. |
| **empirical_validation** | Matches Huete et al. (2002) formula exactly. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Backend telemetry. No formal UQ. |
| **known_limitations** | (1) Was the worst divergence found: Python fallback previously omitted the [−1,1] clip, causing EVI to exceed 1 — fixed. (2) Sensitive to atmospheric correction quality. (3) C++ kernel cannot be rebuilt (no compiler). |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++: `indices.cpp`; Python: `_py_evi`; Numba: `indices_fast.py` (`evi_fast`). |
| **verification_status** | Verified — backends agree to 2.2e-16. |
| **validation_status** | Matches Huete et al. (2002) closed form. |
| **provenance** | `data_source: "simulated"`; `model: "EVI S-002 v1.0"`; `computed: True` |
