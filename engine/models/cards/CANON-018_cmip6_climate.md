# Model Card: CANON-018 — CMIP6 Climate Data

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-018` |
| **name** | CMIP6 Climate Data |
| **version** | `1.0.0` |
| **scientific_domain** | Climate |
| **intended_use** | Provide downscaled CMIP6 (Coupled Model Intercomparison Project Phase 6) climate projections as forcing data for hydrological and ecological models under future climate scenarios. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Not a scientific model. Provides access to CMIP6 climate variables: temperature (tas, tasmin, tasmax), precipitation (pr), shortwave radiation (rsds), wind (uas, vas), specific humidity (hurs). Downscaling method: bias correction / spatial disaggregation. |
| **equation_conventions** | CMIP6 standard variables follow CF conventions. Temperature in Kelvin. Precipitation in kg/m²/s. Radiation in W/m². Time in days since reference date. |
| **assumptions** | (1) Bias correction transfers the observed climatological distribution from a reference period to the modelled anomaly. (2) Spatial resolution limited by the host model grid. (3) Scenario dependence: SSP pathways (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5). |
| **applicability_domain** | Global land surfaces at CMIP6 model resolution (typically 50–300 km). Not suitable for local-scale (<10 km) projection without downscaling. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `scenario` (str: SSP1-2.6|SSP2-4.5|SSP3-7.0|SSP5-8.5), `model` (str: CMIP6 model identifier), `period` (str: "historical"|"2020-2040"|"2040-2060"|"2060-2080"|"2080-2100") |
| **output_schema** | `tas` (K), `pr` (kg/m²/s), `rsds` (W/m²), `uas` (m/s), `hurs` (%) — as NetCDF or xarray Dataset |
| **units** | CMIP6 standard units. Conversions to hydrology units (mm/day, °C) performed by consumer. |

---

## 4. Initial & Boundary Conditions

| Field | Value |
|-------|-------|
| **initial_conditions** | Not applicable — reference data service. |
| **boundary_conditions** | Not applicable. |

---

## 5. Numerical Method

| Field | Value |
|-------|-------|
| **numerical_method** | Data retrieval and bias correction. Not a numerical solver. |
| **solver_configuration** | N/A. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | IPCC AR6 (2021). CMIP6 ensemble: Eyring, M.J. et al. (2016). "Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) and simulation protocol." *Geoscientific Model Development* 9(9): 1937–1976. |
| **reference_cases** | IPCC AR6 WG1 assessment. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s07_cmip6.py` — variable availability, unit consistency. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | Temperature > 0 K; precipitation ≥ 0; radiation ≥ 0. |
| **empirical_validation** | Not validated against independent downscaled data. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | CMIP6 ensemble spread. No formal propagated UQ. |
| **known_limitations** | (1) Scientific status: REQUIRES_SCIENTIFIC_REVIEW. (2) Data assimilation weights undocumented. (3) Downscaling method not validated against regional climate models. (4) Not a blocker for ECO-04; deferred to post-ECO-04. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Reference only — not a computational model. |
| **verification_status** | Not applicable — data service. |
| **validation_status** | Not validated. Scientific review pending. |
| **provenance** | `data_source: "measured"`; `model: "CMIP6 (IPCC AR6)"`; `computed: False` |
