# Stage 24: Scientific References & Data Source Priorities

## Date: 2026-10-17
## Status: IMPLEMENTED

---

## 1. NASA POWER Direct PAR

### Finding
NASA POWER provides **direct** Photosynthetically Active Radiation (PAR) via the
parameter `ALLSKY_SFC_PAR_TOT` ("All Sky Surface PAR Total").

### Source
- **API documentation**: https://power.larc.nasa.gov/docs/methodology/energy-fluxes/derived-parameters/
- **Parameter code**: `ALLSKY_SFX_PAR_TOT` is incorrect — the correct parameter name
  returned by the NASA POWER daily API is `ALLSKY_SFC_PAR_TOT` (Surface, not
  Surface-extraterrestrial).
- **Units**: MJ/m²/day (daily total, all-sky conditions)
- **Data source**: CERES SYN1deg Ed. 4.2 (satellite observations)
- **Temporal coverage**: 1984 to within months of Near Real Time (NRT)
- **Scientific reference**: Su et al. (2007), "Derivation of PAR from CERES SYN1deg
  Edition 4.2 data," method is computed from both diffuse and direct horizontal
  irradiance PAR.

### Priority
1. **Direct PAR** from NASA POWER (`ALLSKY_SFC_PAR_TOT`) — provenance: `observed`,
   status: `observed`
2. **Converted PAR** from shortwave radiation (using 0.5 fraction) — provenance:
   `converted_documented`, status: `estimated`

When direct PAR is available, the shortwave-to-PAR conversion is NOT applied.

### Implementation
- `weather_source.py`: `_fetch_nasa_power()` now requests `ALLSKY_SFC_PAR_TOT`
  alongside the existing parameters and stores it with full provenance metadata.
- `weather_source.py`: `_build_dataframe()` accepts `par_values` and provenance
  attributes; when PAR is not directly available (e.g., Open-Meteo), the PAR column
  contains NaN — no silent conversion occurs.
- `par_pipeline.py`: `build_seasonal_climate_inputs()` checks for direct PAR first
  (Priority 1) before falling back to shortwave conversion (Priority 2).

---

## 2. LAI Model Data Source Priority

### Priority Order
The `LAIModel.compute_with_provenance()` method implements:

1. **observed** — User-provided observed LAI array (field measurements, satellite LAI)
2. **empirical** — NDVI converted via `LAI = 3.5 * NDVI` (Monteith 1993)
3. **model_generated** — GDD-accumulated sigmoid growth curve using CropPhenology thresholds
4. **unavailable** — No LAI data of any kind available

### Empirical LAI (NDVI path)
- **Formula**: `LAI = 3.5 * NDVI`
- **Coefficient**: `NDVI_TO_LAI_COEFFICIENT = 3.5`
- **Reference**: Monteith, J.L. (1993), "The interpretation of optical leaf area
  indicators as crop vigour indicators." Journal of Agricultural Science, Cambridge, 121(1): 1-4.
- **Clipping**: LAI clipped to `[LAI_MIN=0.1, LAI_MAX=8.0]`
- **Note**: This is the same formula used in `services/map_engine/pipelines/vegetation.py:_compute_lai`

### GDD Model (fallback)
- **Method**: Sigmoid growth curve using accumulated growing degree days
- **Formula**: `LAI = lai_min + (lai_max - lai_min) * sigmoid(gdd - center)`
- **GDD thresholds**: From `engine/hydroma/phenology.py` (CROP_PHENOLOGY)
- **Reference**: GDD thresholds from FAO literature averages; LAI curve shape is a
  placeholder sigmoid, not a validated crop model.
- **Status**: `model_generated` — explicitly documented as NOT a validated prediction.

---

## 3. EWSI Scientific Components

### Status: NOVEL composite index

EWSI is NOT a published index. The three-component composition, weights, and VPD
anchors are this project's own inventions.

### Component 1: NDMI Stress (weight: 0.4)
- **Formula**: `NDMI = (NIR - SWIR) / (NIR + SWIR)` with exact zero-denominator guard
- **Stress**: `ndmi_stress = clip(1 - NDMI, 0, 1)`
- **Reference**: Gao, B.C. (1996). "NDWI - A normalized difference water index."
  Remote Sensing of Environment, 58(3), 257-266.
- **Note**: Gao's original paper is NDWI (Green-NIR), not NDMI (NIR-SWIR). The algebra
  `(NIR - SWIR) / (NIR + SWIR)` is Gao's, but applied to Sentinel-2 B8A (NIR) and
  B11 (SWIR), which is Gao's *bands*. The citation is retained but corrected.

### Component 2: VPD Stress (weight: 0.3)
- **Formula**: `vpd_stress = clip((VPD - 0.5) / 3.5, 0, 1)`
- **VPD computation**: `vpd_kpa(t_max, t_min, rh)` from `engine/hydroma/climate_adaptation/dynamic_stress_engine.py`
  uses the Tetens equation: `es = 0.6108 * exp(17.27*T / (T+237.3))`
- **Anchors**: 0.5 kPa (0 stress), 4.0 kPa (full stress) — UNSOURCED
- **VPD range**: [0, 10] kPa (declared in model but only 0.5-4.0 is discriminating)
- **Recorded defect**: VPD values from 4.0 to 10 kPa all return 1.0 (60% of declared
  range collapses to one number)

### Component 3: Soil Moisture Stress (weight: 0.3)
- **Formula**: `soil_stress = clip(1 - (SM / FC), 0, 1)`
- **SM range**: [0, 0.6] m³/m³
- **FC (field capacity)**: Must be > 0 (validated)

### Composite
```
EWSI = 0.4 * ndmi_stress + 0.3 * vpd_stress + 0.3 * soil_stress
```
- **Output range**: [0, 1] where 0 = no stress, 1 = severe stress
- **Weights**: Normalized to sum to 1.0 via `__post_init__`

---

## 4. HYRUE Seasonal Mode Formulas

### Core Equations (from `engine/hydroma/models/hyrue.py`)
```
f_IPAR  = 1 - exp(-k * min(LAI, lai_max))     (Beer-Lambert extinction)
f_water = 1 - EWSI                            (water stress complement)
f_temp  = exp(-((T - T_opt) / 8)²)            (Gaussian temperature response)
B_day   = PAR * f_IPAR * epsilon * f_water * f_temp
B_total = sum(B_day)                          (seasonal: sum of daily)
Y_g_m²  = B_total * HI                          (harvest index)
Y_t_ha  = Y_g_m² / 100                         (unit conversion)
```

### Parameters (frozen — NOT modified)
| Parameter | Wheat | Maize | Rice | Potato | Generic |
|-----------|-------|-------|------|--------|---------|
| epsilon (g/MJ IPAR) | 2.2 | 3.3 | 2.2 | 2.8 | 2.5 |
| k (extinction coeff) | 0.65 | 0.65 | 0.65 | 0.65 | 0.65 |
| HI (harvest index) | 0.45 | 0.50 | 0.45 | 0.75 | 0.45 |
| lai_max | 6.0 | 6.0 | 6.0 | 6.0 | 6.0 |
| t_opt (°C) | 20.0 | 25.0 | 28.0 | 18.0 | 25.0 |
| sigma (Gaussian width) | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 |
| t_min (°C) | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| t_max (°C) | 35.0 | 35.0 | 35.0 | 35.0 | 35.0 |

### References
- Monteith, J.L. (1977). "Climate and the efficiency of crop production in Britain."
  Phil Trans R Soc B, 281, 277-294.
- Steduto, P. et al. (2009). "AquaCrop - The FAO crop model." Agronomy Journal, 101(3), 426-437.

---

## 5. PAR Conversion Coefficient

### Status: ESTIMATED (Status B)
The fraction of shortwave radiation that falls in the 400–700 nm PAR band depends
on atmospheric composition, solar zenith angle, and aerosol loading.

- **Fraction used**: `DEFAULT_PAR_FRACTION = 0.5`
- **Reference**: Monteith & Unsworth (2013), *Principles of Environmental Physics*,
  4th ed., ch. 9: PAR is ~50% of total shortwave downward at the surface under
  mid-latitude conditions.
- **FAO-56**: Also uses 0.5 in the absence of spectral data.
- **Status**: `estimated` — calibration-grade assumption, NOT a measured crop parameter.

---

## 6. Evaluation Framework References

The independent evaluation framework (`engine/hydroma/eval/`) implements standard
statistical metrics with no proprietary algorithms:

- **RMSE**: Standard root-mean-square error
- **MAE**: Standard mean absolute error
- **R²**: Standard coefficient of determination
- **MAPE**: Standard mean absolute percentage error (with epsilon guard)
- **Cross-validation**: Standard k-fold CV with equal-width partitioning
- **Sensitivity analysis**: One-at-a-time (OAT) method, normalised sensitivity coefficient
  S = (ΔOutput/Output) / (ΔInput/Input)
- **Consistency checks**: Independent recomputation of documented formulas
