# Model Card: CANON-022 — Sentinel-2 MSI Surface Reflectance

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-022` |
| **name** | Sentinel-2 MSI Surface Reflectance (Sen2Cor) |
| **version** | `1.0.0` (Processing Baseline 4.0) |
| **scientific_domain** | Remote Sensing (Optical Imagery) |
| **intended_use** | Provide high-resolution surface reflectance for vegetation monitoring, land cover mapping, precision agriculture, and index computation (NDVI, EVI, NDWI). |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Sen2Cor atmospheric correction (Louis et al., 2016):<br>ρ_surface = [L_λ − L_path] × (d²) / (ESUN_λ × cos(θ_s) × T_dir(θ_s) × T_dif) × t_oz + t_oz<br>where L_λ = TOA radiance, L_path = path radiance, d = Earth-Sun distance, ESUN_λ = solar irradiance, θ_s = solar zenith, T_dir/dif = direct/diffuse transmittance, t_oz = ozone transmission. |
| **equation_conventions** | Reflectance dimensionless [0, 1]. Bands: 13 spectral bands from 443 nm (Coastal) to 2190 nm (SWIR). Spatial resolution: 10 m (Blue, Green, Red, NIR, Red Edge), 20 m (SWIR, Red Edge), 60 m (Coastal, Cirrus, NIR atmospheric band). |
| **assumptions** | (1) Standard atmospheric profile. (2) Uniform surface within pixel. (3) Aerosol optical thickness computed via the scene. |
| **applicability_domain** | Global, 80°N–80°S. Cloud-free scenes required. Temporal: 5-day revisit (10-day at single satellite, 5-day with Sentinel-2A+B). |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `tile_id` (str: T33UUN..), `date` (datetime), `bands` (list: B02..B8A, B11, B12) |
| **output_schema** | `surface_reflectance` (dict band → 2D array, dimensionless [0,1]), `cloud_mask` (2D array, uint8), `aerosol_optical_thickness` (float) |
| **units** | Surface reflectance dimensionless. AOT dimensionless. |

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
| **numerical_method** | Sen2Cor radiative transfer model (6S-based). Not an engine solver. |
| **solver_configuration** | N/A. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Louis, I.-C., et al. (2016). "Sen2Cor: L2A Processor for Sentinel-2." ESA Sentinel-2 Support Laboratory. Also: ESA (2021). "Sentinel-2 User Guide." ESA Copernicus. |
| **reference_cases** | ESA Sen2Cor validation against AERONET and in-situ sites. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s09_remote_sensing.py` — data availability, unit consistency. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | Reflectance in [0, 1]; cloud mask valid values. |
| **empirical_validation** | Validated against AERONET and in-situ sites. ECO-03.1 confirmed. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | ESA scene-level QA. Sen2Cor reports uncertainty in AOT, water vapour, and surface temperature. |
| **known_limitations** | (1) Cloud cover. (2) Aerosol model assumptions. (3) Spatial resolution varies by band. (4) Temporal revisit 5 days. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Reference data — ESA Sentinel-2 (Sen2Cor). |
| **verification_status** | Verified by ESA. |
| **validation_status** | Validated against AERONET. |
| **provenance** | `data_source: "measured"`; `model: "Sentinel-2 L2A Sen2Cor v4.0"`; `computed: False` |
