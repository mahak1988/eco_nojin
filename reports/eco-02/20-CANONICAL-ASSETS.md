# ECO-02: Canonical Assets Registry

## CANON-XXX Asset Definitions and Metadata

---

## Source Evidence
- ECO-01/20-CANONICAL-ASSETS.md
- ECO-01/07-MODEL-QUALITY-MATRIX.md
- ECO-01/02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md

---

## Canonical Asset List (22 Models)

### VERIFIED Models (CORE)

#### CANON-001: FAO-56 Penman-Monteith Reference ET
- **Type**: Reference ET
- **Equation**: FAO-56 Eq 6.7
- **Inputs**: Temperature, humidity, wind, radiation
- **Output**: Reference crop ET (mm/day)
- **FAO Standard**: Yes (FAO Irrigation and Drainage Paper 56)
- **C++ Kernel**: `et_calculations.cpp`
- **Python Path**: `engine/hydroma/scientific/et/penman_monteith.py`

#### CANON-009: FAO-56 Crop Coefficient Method
- **Type**: Crop water requirement
- **Equation**: ETc = Kc × ET0
- **Inputs**: Crop coefficient, reference ET
- **Output**: Crop-specific ET (mm/day)
- **C++ Kernel**: `crop_water.cpp`

#### CANON-018: CMIP6 Climate Projections
- **Type**: Global climate model ensemble
- **Source**: World Climate Research Programme
- **Variables**: Temperature, precipitation, pressure, wind
- **Resolution**: ~100km
- **Python Path**: `engine/hydroma/scientific/climate/cmip6.py`

#### CANON-019: GPM IMERG Precipitation
- **Type**: Satellite precipitation product
- **Source**: NASA Global Precipitation Measurement
- **Resolution**: 0.1° (~10km)
- **Frequency**: Half-hourly
- **Units**: mm/hour
- **Trust Level**: HIGH

#### CANON-020: MODIS Evapotranspiration
- **Type**: Satellite ET product
- **Source**: NASA MODIS (MOD16A2)
- **Resolution**: 500m
- **Frequency**: 8-day
- **Units**: mm/day
- **Trust Level**: HIGH

#### CANON-021: Landsat 8/9 Surface Reflectance
- **Type**: Optical satellite imagery
- **Source**: USGS Landsat program
- **Resolution**: 30m
- **Bands**: Visible, NIR, SWIR
- **Trust Level**: HIGH

#### CANON-022: Sentinel-2 MSI
- **Type**: High-resolution optical imagery
- **Source**: ESA Copernicus program
- **Resolution**: 10m (vis/NIR), 20m (SWIR)
- **Trust Level**: HIGH

### SCIENTIFICALLY_SUPPORTED Models (IMPORTANT)

#### CANON-002: Hargreaves-Samani ET
- **Type**: Temperature-based ET
- **Equation**: Hargreaves & Samani (1985)
- **Inputs**: Temperature min/max, extraterrestrial radiation
- **Output**: ET (mm/day)
- **C++ Kernel**: `et_calculations.cpp`

#### CANON-003: Thornthwaite PET
- **Type**: Temperature-based PET
- **Equation**: Thornthwaite (1948)
- **Inputs**: Temperature, latitude
- **Output**: PET (mm/month)

#### CANON-004: Blaney-Crop Method
- **Type**: Water requirement estimation
- **Equation**: Blaney & Musgrave (1934)
- **Inputs**: Temperature, daylight hours, crop data

#### CANON-007: Priestley-Taylor ET
- **Type**: Radiation-based ET
- **Equation**: Priestley & Taylor (1972)
- **Inputs**: Net radiation, temperature
- **Output**: ET (mm/day)

#### CANON-008: Jensen-Haise ET
- **Type**: Energy-based ET
- **Equation**: Jensen & Haise (1963)
- **Inputs**: Temperature, elevation, radiation
- **Output**: ET (mm/day)

#### CANON-010: FAO AquaCrop
- **Type**: Crop water productivity model
- **Source**: FAO AquaCrop documentation
- **Purpose**: Yield gap analysis under water stress

#### CANON-011: SWAT (Soil and Water Assessment Tool)
- **Type**: Watershed simulation
- **Source**: USDA-ARS
- **Purpose**: Hydrology, sediment, nutrient cycling

#### CANON-013: MODFLOW
- **Type**: Groundwater flow model
- **Source**: USGS
- **Purpose**: Saturated groundwater flow
- **C++ Kernel**: `groundwater.cpp`

---

## Asset Metadata Schema

```json
{
  "canon_id": "CANON-001",
  "name": "FAO-56 Penman-Monteith Reference ET",
  "type": "reference_et",
  "equation": "FAO-56 Eq 6.7",
  "inputs": ["temperature", "humidity", "wind", "radiation"],
  "outputs": ["et0_mm_per_day"],
  "units": "SI",
  "maturity": "VERIFIED",
  "status": "CORE",
  "cpp_kernel": "et_calculations.cpp",
  "python_path": "engine/hydroma/scientific/et/penman_monteith.py",
  "validation_sources": ["MODIS ET", "FLUXNET"],
  "last_validated": "2026-10-08"
}
```

---

## Canonical Asset Validation

### Validation Matrix
| CANON ID | Validated Against | Status | Next Validation |
|----------|-------------------|--------|-----------------|
| CANON-001 | MODIS ET, FLUXNET | ✅ PASS | 2027-01-08 |
| CANON-009 | Field measurements | ✅ PASS | 2027-01-08 |
| CANON-018 | CMIP6 ensemble | ✅ PASS | 2027-01-08 |
| CANON-019 | Rain gauge data | ✅ PASS | 2026-11-08 |
| CANON-020 | FLUXNET stations | ✅ PASS | 2026-11-08 |

---

## Asset Dependency Graph

```
CANON-018 (CMIP6) ──→ CANON-001 (Penman-Monteith) ──→ CANON-009 (FAO-56) ──→ CANON-010 (AquaCrop)
        │                       │                           │
        └──→ CANON-014 (WRF) ───┘                           ├──→ CANON-011 (SWAT)
        └──→ CANON-016 (RegCM)                              │
        └──→ CANON-017 (HadGEM2)                             └──→ CANON-013 (MODFLOW)
        
CANON-019 (GPM) ──→ CANON-001
CANON-020 (MODIS) ──→ Validate ──→ CANON-001
CANON-021 (Landsat) ──→ Land use → CANON-009, CANON-010
CANON-022 (Sentinel-2) ──→ Crop params → CANON-010
```

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/20*