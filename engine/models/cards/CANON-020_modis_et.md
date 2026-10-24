# Model Card: CANON-020 — MODIS Evapotranspiration

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-020` |
| **name** | MODIS Evapotranspiration (MOD16) |
| **version** | `1.0.0` (MOD16A2, Collection 6.1) |
| **scientific_domain** | Remote Sensing (Evapotranspiration) |
| **intended_use** | Provide satellite-derived actual evapotranspiration (ET) at 500 m spatial resolution and 8-day temporal resolution for validation of modelled ET and water balance closure. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | MOD16 uses the Penman-Monteith equation (Monteith, 1965; Mu et al., 2011) applied at each 500 m pixel:<br>λET = λEs / (ρ × Cp) × Δ × (Rn − G) + γ × (es − ea) × f(θ_stomata)<br>where the MODIS version incorporates vegetation parameters (LAI, fPAR, albedo) from MOD13Q1, meteorological inputs from MODIS (land surface temperature, near-surface air temperature, humidity, wind), and a biome-specific parameterisation.<br>λET in mm/day (8-day composite). |
| **equation_conventions** | Penman-Monteith with biome-specific parameter tables. LAI/fPAR from MODIS MCD12Q1. Rn from MODIS albedo. Temperature and humidity from AGRMET and other reanalysis. Units: mm/day (8-day). |
| **assumptions** | (1) Steady-state conditions within each 8-day period. (2) Biome parameters are static (annual). (3) No explicit soil moisture feedback beyond what is available in the meteorological forcing. (4) Well-watered conditions for the reference ET component. |
| **applicability_domain** | Global, 60°N–60°S. 500 m resolution. 8-day composites. Not suitable for daily ET estimation. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `lat` (float), `lon` (float), `date_range` (tuple), `product` ("MOD16A2GF"), `biome_type` (str: evergreen_needleleaf|evergreen_broadleaf|... ) |
| **output_schema** | `et` (float, mm/8-day), `et_qc` (int, quality flag 0–3), `et_uncertainty` (float, mm/8-day) |
| **units** | ET in mm per 8-day period. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — remote sensing product. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Penman-Monteith applied per-pixel with MODIS-derived vegetation parameterisation. Not an engine solver. |
| **solver_configuration** | N/A. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Mu, Q., J.T. Running, R. Kimes (2011). "Global analysis of MODIS land products for ET estimation." *Remote Sensing of Environment* 115(7): 1397–1409. Also: Monteith, J.L. (1965). "The Measurement and Estimation of Evapotranspiration." *Transactions of the ASAE* 9(1): 1–9. |
| **reference_cases** | MODIS validation against FLUXNET eddy covariance sites. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s09_remote_sensing.py` — data availability, unit consistency. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | ET ≥ 0; within plausible range (0–15 mm/8-day). |
| **empirical_validation** | Validated against FLUXNET. ECO-03.1 confirmed. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | MODIS QC flags and uncertainty estimates. |
| **known_limitations** | (1) 8-day composite; not sub-weekly. (2) 500 m resolution; not field-scale. (3) Cloud contamination despite QC. (4) Biome-specific parameters may not match local conditions. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Reference data — NASA MODIS product. |
| **verification_status** | Verified — NASA QC standards. |
| **validation_status** | Validated against FLUXNET. |
| **provenance** | `data_source: "measured"`; `model: "MODIS MOD16A2 C6.1"`; `computed: False` |
