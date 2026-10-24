# Model Card: CANON-019 — GPM IMERG Precipitation

## 1. Identification

| Field | Value |
|-------|-------|
| **model_id** | `CANON-019` |
| **name** | GPM IMERG Precipitation |
| **version** | `07` (current IMERG version as of 2026) |
| **scientific_domain** | Remote Sensing (Precipitation) |
| **intended_use** | Provide near-real-time and research-grade global precipitation estimates at 0.1° spatial resolution and 30-minute temporal resolution for hydrological modelling and validation. |

---

## 2. Governing Equations and Conventions

| Field | Value |
|-------|-------|
| **governing_equations** | Not a computed model. IMERG (Integrated Multi-satellite Retrieval for GPM) combines microwave, infrared, and ground-based precipitation gauge estimates via the Goddard Profiling Algorithm (GPROF) and a Kalman-filter-like optimal interpolation. Precipitation rate: Pr = Σ(wi × Pi) where wi are satellite-gain weights and Pi are individual sensor retrievals, bias-corrected against GPCP. |
| **equation_conventions** | Precipitation in mm/hour. Spatial grid: 0.1° × 111 km. Temporal: half-hourly. Coordinates: latitude/longitude (WGS84). |
| **assumptions** | (1) Microwave retrievals are the primary source (accuracy ~1 mm/h). (2) IR interpolation fills temporal gaps between microwave overpasses. (3) Gauge correction applied via GPCP monthlies. (4) Uncertainties estimated via triple-correlation method across satellites. |
| **applicability_domain** | Global (60°N–60°S latitude; extends to 90° with reduced accuracy). Valid for event-scale (30 min) to climatological (monthly) precipitation. Not suitable for snowfall without correction. |

---

## 3. Input / Output Schema

| Field | Value |
|-------|-------|
| **input_schema** | `lat` (float, degrees, −60..60), `lon` (float, degrees, −180..180), `date` (datetime), `version` ("GPM_07"|"GPM_06"), `product_type` ("near_real_time"|"random_rust") |
| **output_schema** | `precipitation_rate` (float, mm/hour), `precipitation_flag` (int: 0=no data, 1=interp, 2=mw-gauged, 3=IR-only), `uncertainty_mmh` (float, mm/hour) |
| **units** | Precipitation rate in mm/hour. Uncertainty in mm/hour. |

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
| **numerical_method** | Data integration via IMERG algorithm (GPM IMERG L3). Not a modelling solver. |
| **solver_configuration** | N/A. |
| **convergence_criteria** | Not applicable. |

---

## 6. Scientific References

| Field | Value |
|-------|-------|
| **scientific_references** | Huffman, G.J. et al. (2020). "GPM IMERG Version 6 Final Precipitation Data." *NASA Technical Report*. Also: Huffman, G.J. et al. (2003). "Bridging Critical Gaps in Precipitation Gauge Measurements." *Bulletin of the American Meteorological Society* 84(9): 1247–1258. |
| **reference_cases** | NASA IMERG documentation and validation reports. |

---

## 7. Tests

| Field | Value |
|-------|-------|
| **unit_tests** | `strict_tests/test_s09_remote_sensing.py` — data availability, unit consistency. |
| **analytical_tests** | Not applicable. |
| **numerical_tests** | Not applicable. |
| **physical_consistency_tests** | Precipitation rate ≥ 0; flag values valid. |
| **empirical_validation** | Validated against GPCP and ground gauge networks by NASA. ECO-03.1 confirmed. |

---

## 8. Uncertainty & Limitations

| Field | Value |
|-------|-------|
| **uncertainty_method** | IMERG internal uncertainty estimate (mm/hour). |
| **known_limitations** | (1) Spatial resolution (0.1°) may be too coarse for local hydrology. (2) IR interpolation under heavy convective conditions. (3) Snowfall underestimated. (4) Latency: near-real-time ~30 min, final ~10 days. |

---

## 9. Implementation & Traceability

| Field | Value |
|-------|-------|
| **implementation_status** | Reference data — NASA GPM mission product. |
| **verification_status** | Verified by NASA against GPCP. |
| **validation_status** | Validated. |
| **provenance** | `data_source: "measured"`; `model: "GPM IMERG v07"`; `computed: False` |
