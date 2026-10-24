# Model Card: CANON-021 — Landsat Surface Reflectance

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-021` |
| **name** | Landsat Surface Reflectance (LaSRC) |
| **version** | `1.0.0` (Collection 2, Level-2) |
| **scientific_domain** | Remote Sensing (Optical Imagery) |
| **intended_use** | Provide surface reflectance products for land cover classification, vegetation index computation (NDVI, EVI), change detection, and time-series analysis. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | LaSRC (Landsat Surface Reflectance Code) atmospheric correction (Vermote et al., LANDSAT ET handbook):<br>ρ_surface = (π × L_λ × d²) / (ESUN_λ × cos(θ_s) × T_gases × T_water × T_aerosol)<br>where L_λ = spectral radiance at sensor, d = Earth-Sun distance, ESUN_λ = mean solar exoatmospheric irradiance, θ_s = solar zenith angle, T = transmittance terms for gases, water vapour, and aerosols. |
| **equation_conventions** | Reflectance dimensionless [−0.1, 1.0] (may be slightly negative over bright surfaces). Bands: Coastal, Blue, Green, Red, NIR, SWIR1, SWIR2, TIRS1, TIRS2. Spatial resolution: 30 m (15 m panchromatic, 100 m thermal). |
| **assumptions** | (1) Standard atmospheric conditions. (2) Uniform land cover within 30 m pixel. (3) No adjacency effects. (4) Aerosol model: rural or urban. |
| **applicability_domain** | Global, 90°N–90°S. Valid for cloud-free scenes. Temporal: every 8–16 days per Landsat satellite. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `path` (int, 1–232), `row` (int, 1–248), `date` (datetime), `bands` (list: SR_B2..SR_B7, ST_B1..ST_B7) |
| **output_schema** | `surface_reflectance` (dict band → 2D array, dimensionless), `qa_band` (2D array, bit-packed pixel QA), `brightness_temperature` (dict band → 2D array, K) |
| **units** | Surface reflectance dimensionless. Brightness temperature in Kelvin. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — observational data product. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Atmospheric correction via LaSRC radiative transfer. Not an engine solver. |
| **solver_configuration** | N/A. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Vermote, E., et al. (2016). "Landsat Level-2 Science Product Product Development Plan." USGS. Also: Masek, R.G. et al. (2006). "An empirical approach to Landsat digital surface reflectance." *IEEE GRS Letters* 33(3): 115–118. |
| **reference_cases** | USGS Landsat validation against AERONET and SURFRAD. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s09_remote_sensing.py` — data availability, unit consistency. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | Reflectance in [−0.1, 1.0]; brightness temperature > 0 K. |
| **empirical_validation** | Validated against AERONET. USGS collection 2. ECO-03.1 confirmed. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | USGS pixel-level QA flags. |
| **known_limitations** | (1) Cloud cover requires masking. (2) 30 m resolution for multispectral; 100 m for thermal. (3) Temporal revisit 8–16 days. (4) Aerosol and water vapour assumptions may introduce errors in humid conditions. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Reference data — USGS Landsat product. |
| **verification_status** | Verified by USGS. |
| **validation_status** | Validated against AERONET/SURFRAD. |
| **provenance** | `data_source: "measured"`; `model: "Landsat C2 L2 LaSRC"`; `computed: False` |
