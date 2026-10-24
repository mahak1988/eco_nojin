# Model Card: CANON-006 — van Genuchten Soil Water Retention

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-006` |
| **name** | van Genuchten Soil Water Retention Curve |
| **version** | `1.0.0` |
| **scientific_domain** | Soil Physics |
| **intended_use** | Compute volumetric water content θ as a function of soil water suction (pressure head), and derive plant-available water capacity (AWC) for a given soil texture. Used in crop water balance, irrigation scheduling, and hydrological modelling. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | van Genuchten (1980), retention:<br>θ(h) = θ_r + (θ_s − θ_r) / (1 + |α·h|^n)^m<br>where m = 1 − 1/n<br><br>Mualem (1976), unsaturated hydraulic conductivity:<br>K(θ) = K_s · S_e^0.5 · [1 − (1 − S_e^(1/m))^m]²<br>where S_e = (θ − θ_r) / (θ_s − θ_r) (effective saturation)<br><br>FAO-56 convention for field capacity and permanent wilting point:<br>θ_fc at h = −33 cm (0.33 bar), θ_pwp at h = −15000 cm (15 bar)<br>AWC = θ_fc − θ_pwp [cm³/cm³] → [mm/m] = (θ_fc − θ_pwp) × 1000 |
| **equation_conventions** | Pressure head h in cm (negative for suction). α in cm⁻¹, n dimensionless > 1, m = 1−1/n. θ in cm³/cm³. K_s in cm/day. |
| **assumptions** | (1) Soil is homogeneous and isotropic. (2) No hysteresis between wetting and drying. (3) Temperature effects on water retention neglected. (4) Root zone is uniform in soil properties. (5) Field capacity defined at −33 cm per FAO-56 (not −30 or −50 cm). |
| **applicability_domain** | Unsaturated zone, pressure heads from −10⁴ to 0 cm. For 12 USDA soil textures (sand through clay). Not applicable to saturated conditions (h ≥ 0 → θ = θ_s). Outside the fitted texture range, parameters should be derived from pedotransfer functions. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `pressure_head_cm` (float, cm, −1e6..0), `soil_texture` (str, one of 12 USDA textures: sand, loamy_sand, sandy_loam, loam, silt_loam, silt, sandy_clay_loam, clay_loam, silty_clay_loam, sandy_clay, silty_clay, clay), `theta_r` (float, cm³/cm³, 0–0.3, optional override), `theta_s` (float, cm³/cm³, 0.3–1.0, optional override), `alpha` (float, cm⁻¹, 1e-4–1.0, optional override), `n` (float, dimensionless, 1.0–3.0, optional override), `k_sat` (float, cm/day, optional override) |
| **output_schema** | `theta` (float, cm³/cm³), `k_unsat` (float, cm/day), `saturated` (bool) |
| **units** | Pressure head in cm, water content in cm³/cm³ (volumetric), conductivity in cm/day. AWC conversion to mm/m: multiply cm³/cm³ by 1000. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — diagnostic model. The initial water content is an input (via pressure head or θ value), not computed. |
| **boundary_conditions** | Not applicable — boundary variable is the prescribed pressure head (suction). |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Evaluated form of van Genuchten retention equation. No discretization in the retention model itself; numerical root-finding (bisection) used to invert θ to h when needed for field capacity. |
| **solver_configuration** | Not applicable for retention. For Richards equation coupling, backward Euler is used (see CANON-016 C++ and richards.cpp). |
| **convergence_criteria** | Not applicable for retention. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | van Genuchten, M.T. (1980). "A Closed-Form Equation for Predicting the Relative Appearance of Liquids in Saturated and Partially Saturated Porous Media." *Soil Science Society of America Journal* 44(5): 892–898. Mualem, Y. (1976). "A New Model for Predicting the Hydraulic Conductivity of Unsaturated Porous Media." *Water Resources Research* 12(3): 513–522. Carsel, R.F., Parrish, R.S. (1988). "Developing Soil-Specific Water Retention Functions: A Method." *Water Resources Research* 24(5): 755–769. |
| **reference_cases** | SAXTON_RAWLS_2006_AWC in conftest.py — published AWC (mm/m) for 12 soil textures per Saxton & Rawls (2006), used as an *independent check* of this model's own AWC. See §7 for the measured agreement. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s05_soil_retention.py` — van Genuchten equation, Mualem conductivity, the parameter table, FC/PWP heads, and the AWC check against Saxton-Rawls. |
| **analytical_tests** | Saturation branch: θ = θ_s at h = 0 (verified by closed form). Monotonic approach to θ_r as h → −∞. |
| **numerical_tests** | Property-based: θ bounded [θ_r, θ_s]; θ monotonic decreasing in |h|; FC head = 33 cm (not 330 cm); K(θ) bounded [0, K_s]. |
| **physical_consistency_tests** | θ_r ≤ θ ≤ θ_s; K ≥ 0; field capacity at −33 cm, PWP at −15000 cm; AWC = FC − PWP at those heads. |
| **empirical_validation** | **PARTIAL, measured 2026-10-10.** Against the Saxton & Rawls (2006) AWC values in conftest.py, the engine's own VG AWC spans **30.2 % to 157.2 %** of the published value and **5 of 12 textures fall inside 30 %** (sandy_loam 99.1 %, sandy_clay_loam 92.7 %, clay_loam 108.3 %, silty_clay_loam 115.3 %, sandy_clay 102.1 %). `strict_tests/test_s05_soil_retention.py` passes only because its thresholds are deliberately loose (a 5× floor and a 33 cm-vs-330 cm band). **Retired claims:** "verified against Saxton & Rawls (2006) AWC for 12 textures"; neither was measured. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | The texture parameter table carries **no provenance it can prove**: `engine/data/soil_vg_table.csv` marks every row `unverified; formerly attributed to Carsel & Parrish 1988` with `status: design_assumption` (or `design_assumption_disputed`), and `engine/data/SOIL_TABLE_CONFLICTS.md` records that the Ks column is not monotone in texture fineness in two places, which hydraulic conductivity cannot be. The Carsel & Parrish attribution is **withdrawn**. No uncertainty bounds on the texture-specific parameters. Input sensitivity on α, n, θ_s, θ_r via property-based testing. |
| **known_limitations** | (1) The physics.py module defines FC_HEAD_CM = 330.0 — this is a 10× outlier; the water_retention module correctly uses 33 cm. The two modules share a parameter table but disagree on FC head. (2) The van Genuchten θ equation is correct (power m on bracket); two claims of being wrong were retracted. (3) The embedded texture table is a **design assumption**, not a transcription of Carsel & Parrish (1988); the paper's values are not in the repository, and its Ks column is provably not a faithful copy (see §8 uncertainty_method and `engine/data/SOIL_TABLE_CONFLICTS.md`). (4) C++ kernel cannot be rebuilt (no compiler). |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Production — `engine/hydroma/soil/physics.py` (SOIL_PARAMETERS_VG table, van Genuchten theta/K functions), `engine/hydroma/soil/water_retention.py` (field capacity search). C++ kernel in `engine/cpp_core/src/soil.cpp`. |
| **verification_status** | The θ(h) form and the Mualem K(θ) form are reproduced to machine precision by an independent closed-form re-derivation (`test_s05`, `test_s18`). C++/Python parity confirmed. **No claim is made that the embedded texture table matches Saxton & Rawls (2006) AWC** — the measured agreement spans 30.2 %–157.2 % of the published values, 5 of 12 textures inside 30 %. |
| **validation_status** | **PARTIAL**. Equation form: VALIDATED_METHOD (independent re-derivation at rel=1e-12). Texture parameters: **UNVALIDATED — design assumption** (`engine/data/soil_vg_table.csv`, provenance `unverified`). AWC against Saxton & Rawls (2006): measured 30–157 % agreement, 5/12 within 30 % — a documented model-family difference, not a validation. **Retired claims:** "<1 % agreement" and "validated for all 12 USDA textures"; neither was measured. |
| **provenance** | `data_source: "simulated"`; `model: "Van Genuchten (1980) + Mualem (1976) v1.0"`; `computed: True` |
