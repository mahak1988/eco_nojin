# Model Card: CANON-007 — RUSLE LS Factor (Slope Length/Steepness)

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-007` |
| **name** | RUSLE LS Factor |
| **version** | `1.0.0` |
| **scientific_domain** | Soil Erosion |
| **intended_use** | Compute the slope-length (L) and steepness (S) factor for the Revised Universal Soil Loss Equation (RUSLE). Used within RUSLE to estimate sheet and rill erosion potential on slopes. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | RUSLE (Renard et al. 1997, USDA Agriculture Handbook 703):<br>A = R × K × LS × C × P  [t/ha/yr]<br><br>Slope angle: θ = arctan(slope_percent / 100), sin θ = sin θ.<br><br>**Slope-length exponent (AH-703 form, as implemented):**<br>β = (sin θ / 0.0896) / (3 · sin θ^0.8 + 0.56)<br>m = β / (1 + β)<br>L = (λ / 22.13)^m<br>where λ = slope length (m) and 22.13 m is the standard rill-interrill spacing length used in the exponent.<br><br>**Slope-steepness factor (McCool et al. 1987, as implemented):**<br>For slope_fraction < 0.09 (≈ 5.1 %): S = 10.8 · sin θ + 0.03<br>For slope_fraction ≥ 0.09: S = 16.8 · sin θ − 0.50, floored at 0.<br><br>Combined LS = L × S |
| **equation_conventions** | Slope is supplied as a **percent** (0–100) and converted to θ = arctan(percent/100) inside the kernel. λ in metres. L, S and LS are dimensionless. The 22.13 m standard length is the L exponent's reference. m varies with slope angle through the AH-703 β form above.<br><br>**Divergence of record:** this card used to print β = (sin θ / 0.0896) / (0.513 · ln(sin θ / 0.0896) + 0.0896) and S = (sin θ / 0.0896)^(β/2). Neither form is what the engine runs: `engine/cpp_core/src/erosion.cpp:40-41` and its twin `engine/hydroma/wrapper.py:222` implement the AH-703 β above, with the McCool S above. The equation in this card now matches the code; no engine equation was changed. |
| **assumptions** | (1) Steady-state, uniform plane flow. (2) Top-of-slope water source (no concentrated flow). (3) Homogeneous slope and soil. (4) No terracing or buffer effects. (5) No deposition (transport capacity dominates). (6) Rill spacing = 22.13 m (standard rill spacing). |
| **applicability_domain** | Agricultural and rangeland slopes. Valid for 0° to ~60° slopes. Not applicable to highly concentrated flow channels (use channel erosion models). |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `slope_percent` (float, %, 0–100), `slope_length_m` (float, m, >0), `slope_class` ("annual_tillage" or "contour_cultivation") |
| **output_schema** | `L` (float, dimensionless, ≥0), `S` (float, dimensionless, ≥0), `LS` (float, dimensionless, ≥0) |
| **units** | Slope in percent, slope length in metres. L, S, and LS are dimensionless factors. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — diagnostic factor calculation. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Closed-form analytical equations. No iterative solver. |
| **solver_configuration** | Not applicable. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Renard, K.G., G.R. Foster, G.A. Weesies, D.K. McCool, D.C. Yoder (coordinators) (1997). *Predicting Soil Erosion by Water: A Guide to Conservation Planning with the Revised Universal Soil Loss Equation (RUSLE)*. USDA Agriculture Handbook 703. McCool, D.K., L.D. Meyer, G.R. Foster, C.B. Onstad (1987). "Revised Slope Length and Steepness Factors for the Universal Soil Loss Equation." *Transactions of the ASAE* 30(5): 1387–1396. |
| **reference_cases** | No LS-specific published reference case is stored in this repository. The AH-703 β form and the McCool S constants are taken from those standards; no independent AH-703 worked example for LS is pinned by any test in the tree. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `engine/cpp_core/tests/test_erosion_unit.cpp` — C++ unit tests. `engine/land/tests/test_hydrology.py::TestDownstreamConsumersUseTheOneImplementation` — the Python D8 accumulation feeding the LS length term. No dedicated `strict_tests` file for LS exists. |
| **analytical_tests** | Closed-form check of L and S against RUSLE equations for known slope/length. |
| **numerical_tests** | Property-based: LS ≥ 0; L increases with slope length; S increases with slope steepness. |
| **physical_consistency_tests** | LS ≥ 0; monotonic increase of L with λ; monotonic increase of S with slope angle. |
| **empirical_validation** | Not directly validated against field erosion data; relies on RUSLE framework validation. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | Parameters from RUSLE default. No formal UQ on m exponent. |
| **known_limitations** | (1) Scientific status: REQUIRES_SCIENTIFIC_REVIEW. LS factor calculation has not been locally benchmarked against a published value. (2) The previous Python implementation silently multiplied RUSLE output by an uncited calibration factor of 0.10 — this was removed; the equation is now the plain RUSLE product A = R × K × LS × C × P. (3) C++ kernel cannot be rebuilt (no compiler). (4) **Divergence of record (P1-5, unresolved):** a third LS form exists at `engine/land/erosion_risk.py::calculate_ls_factor`, documenting itself as "McCool et al. (1999)": β = (sin θ / cos²θ) · (λ/300)^0.5, m = β/(1+β), and S = 16.8·sin θ − 0.045·cos² θ above 9 %. Neither the β form nor the −0.045·cos²θ term is the AH-703/McCool-1987 form the C++ kernel and this card use, and it is not reconciled. The canonical implementation is `engine/cpp_core/src/erosion.cpp` (`engine/hydroma/formulas/catalog.py` names it for `rusle_soil_loss`). |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — C++ kernel in `engine/cpp_core/src/erosion.cpp` (`ls_factor`, `ls_factor_array`; β at lines 40-41, m at 42, L at 44). Python fallback with the identical β/m/L/S algebra in `engine/hydroma/wrapper.py::compute_erosion` (lines 212-226), used when the compiled kernel is unavailable. `engine/hydroma/models/runoff_model.py` contains **no** RUSLE code. |
| **verification_status** | The Python fallback reproduces the C++ kernel's β, m, L and S algebra (same constants, same branch at slope_fraction = 0.09). The 0.10 calibration factor was removed; the equation is now the plain RUSLE product A = R × K × LS × C × P. |
| **validation_status** | **VALIDATED_METHOD_CONFORMANCE** for the equation form: the AH-703 β and McCool S constants match `erosion.cpp`. The RUSLE *framework* is externally validated; this LS factor is not independently benchmarked, and the AH-703 "worked reference case" this card used to cite does not exist in the tree. |
| **provenance** | `data_source: "simulated"`; `model: "RUSLE LS Factor v1.0"`; `computed: True` |
