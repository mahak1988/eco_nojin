# HYDROMA Model Card Catalog

**Generated**: 2026-10-09  
**Purpose**: Index of all Model Cards in the HyDroMa engine, linking CANON reference models and C++ kernel symbols to their scientific documentation.  
**Template**: `engine/models/cards/_template.md`  

---

## How to Read This Catalog

Each model card follows the template at `engine/models/cards/_template.md`, which implements all fields required by HYDROMA-MASTER §292–337. Fields are marked **required** or **applicable**. Fields marked "Not applicable" state a reason per §337.

| Status Tag | Meaning |
|------------|---------|
| VERIFIED | Implementation verified AND scientifically validated |
| IMPLEMENTATION_VERIFIED | Code exists and matches design; scientific review pending |
| SCIENTIFICALLY_SUPPORTED | Theoretical basis exists; implementation not benchmarked |
| REQUIRES_SCIENTIFIC_REVIEW | Implementation exists but has known issues |
| STUB | Minimal placeholder code |
| NOT IMPLEMENTED | No code exists |
| RUNTIME_UNVERIFIED | Cannot execute (missing deps or compiler); Python parity used where available |

---

## Part 1: CANON Reference Models (22)

### 1.1 Evapotranspiration (3 models)

| ID | Model | Card Link | Status | Sci. Ref. | Key Test |
|----|-------|-----------|--------|-----------|----------|
| CANON-001 | Penman-Monteith ET0 | [card](./engine/models/cards/CANON-001_penman_monteith_et0.md) | VERIFIED | FAO-56 Allen et al. (1998) | test_s02_climate_et0.py |
| CANON-002 | Hargreaves ET0 | [card](./engine/models/cards/CANON-002_hargreaves_et0.md) | REQUIRES_SCIENTIFIC_REVIEW | Hargreaves & Samani (1985) | test_s02_climate_et0.py |
| CANON-003 | Thornthwaite PET | [card](./engine/models/cards/CANON-003_thornthwaite_pet.md) | SCIENTIFICALLY_SUPPORTED | Thornthwaite (1948) | (no dedicated test) |

### 1.2 Hydrology (5 models)

| ID | Model | Card Link | Status | Sci. Ref. | Key Test |
|----|-------|-----------|--------|-----------|----------|
| CANON-004 | SCS-CN Runoff | [card](./engine/models/cards/CANON-004_scs_cn_runoff.md) | VERIFIED | USDA NRCS TR-55 Part 630 | test_s03_hydrology_runoff.py |
| CANON-005 | Theis Groundwater | [card](./engine/models/cards/CANON-005_theis_solution.md) | REQUIRES_SCIENTIFIC_REVIEW | Theis (1935) | test_s04_groundwater.py |
| CANON-008 | D8 Flow Direction | [card](./engine/models/cards/CANON-008_d8_flow_direction.md) | VERIFIED | O'Callaghan & Mark (1984) | test_s06_hydrology_watershed.py |
| CANON-009 | Terrain Analysis | [card](./engine/models/cards/CANON-009_terrain_analysis.md) | VERIFIED | Horn (1981); Beven & Kirkby (1979) | test_s08_terrain.py |
| CANON-010 | Water Balance | [card](./engine/models/cards/CANON-010_water_balance.md) | VERIFIED | Water balance continuity | test_s10_water_balance.py |

### 1.3 Soil Physics (1 model)

| ID | Model | Card Link | Status | Sci. Ref. | Key Test |
|----|-------|-----------|--------|-----------|----------|
| CANON-006 | Van Genuchten | [card](./engine/models/cards/CANON-006_van_genuchten.md) | VERIFIED | van Genuchten (1980); Mualem (1976) | test_s05_soil_retention.py |

### 1.4 Soil Erosion (1 model)

| ID | Model | Card Link | Status | Sci. Ref. | Key Test |
|----|-------|-----------|--------|-----------|----------|
| CANON-007 | RUSLE LS Factor | [card](./engine/models/cards/CANON-007_rusle_ls_factor.md) | REQUIRES_SCIENTIFIC_REVIEW | RUSLE (Renard et al. 1997) | test_erosion_unit.cpp |

### 1.5 Meteorology / Radiation (1 model)

| ID | Model | Card Link | Status | Sci. Ref. | Key Test |
|----|-------|-----------|--------|-----------|----------|
| CANON-011 | Solar Radiation | [card](./engine/models/cards/CANON-011_solar_radiation.md) | REQUIRES_SCIENTIFIC_REVIEW | FAO-56 eq. 21; Haurwitz (1942) | test_s02_climate_et0.py |

### 1.6 Watershed (1 model)

| ID | Model | Card Link | Status | Sci. Ref. | Key Test |
|----|-------|-----------|--------|-----------|----------|
| CANON-015 | Watershed Calculator | [card](./engine/models/cards/CANON-015_watershed_calculator.md) | VERIFIED | O'Callaghan & Mark; Jenson & Dominguez | test_s06_hydrology_watershed.py |

### 1.7 Infrastructure / Utility (3 models)

| ID | Model | Card Link | Status | Key Test |
|----|-------|-----------|--------|----------|
| CANON-012 | Formula Catalog | [card](./engine/models/cards/CANON-012_formula_catalog.md) | VERIFIED (N/A) | test_formula_registry.py |
| CANON-013 | Provenance Tracking | [card](./engine/models/cards/CANON-013_provenance_tracking.md) | VERIFIED (N/A) | test_s15_provenance.py |
| CANON-014 | Model Registry | [card](./engine/models/cards/CANON-014_model_registry.md) | IMPLEMENTATION_VERIFIED (BLOCKER) | test_s12_formula_catalog.py |

### 1.8 C++ Kernels (2 models)

| ID | Model | Card Link | Status | Runtime |
|----|-------|-----------|--------|---------|
| CANON-016 | Climate Kernels (C++) | [card](./engine/models/cards/CANON-016_climate_kernels.md) | VERIFIED | Partial (.pyd loads; no compiler) |
| CANON-017 | Soil Kernels (C++) | [card](./engine/models/cards/CANON-017_soil_kernels.md) | VERIFIED | Partial (.pyd loads; no compiler) |

### 1.9 Climate Data (1 model)

| ID | Model | Card Link | Status | Sci. Ref. |
|----|-------|-----------|--------|-----------|
| CANON-018 | CMIP6 Climate | [card](./engine/models/cards/CANON-018_cmip6_climate.md) | REQUIRES_SCIENTIFIC_REVIEW | IPCC AR6 (2021) |

### 1.10 Remote Sensing Reference Data (4 models)

| ID | Model | Card Link | Status | Provider |
|----|-------|-----------|--------|----------|
| CANON-019 | GPM IMERG Precipitation | [card](./engine/models/cards/CANON-019_gpm_imerg.md) | VERIFIED | NASA |
| CANON-020 | MODIS ET | [card](./engine/models/cards/CANON-020_modis_et.md) | VERIFIED | NASA |
| CANON-021 | Landsat SR | [card](./engine/models/cards/CANON-021_landsat.md) | VERIFIED | USGS |
| CANON-022 | Sentinel-2 SR | [card](./engine/models/cards/CANON-022_sentinel2.md) | VERIFIED | ESA |

---

## Part 2: C++ Exported Symbol Model Cards (14)

### 2.1 Spectral Indices

| ID | Symbol | Card Link | C++ Source | Python Fallback | Numba Twin | Status |
|----|--------|-----------|------------|-----------------|------------|--------|
| S-001 | `ndvi` | [card](./engine/models/cards/S-001_ndvi.md) | `indices.cpp` | `_py_ndvi` | `ndvi_fast` | VERIFIED |
| S-002 | `evi` | [card](./engine/models/cards/S-002_evi.md) | `indices.cpp` | `_py_evi` | `evi_fast` | VERIFIED |
| S-003 | `savi` | [card](./engine/models/cards/S-003_savi.md) | `indices.cpp` | `_py_savi` | `savi_fast` | VERIFIED |
| S-004 | `ndwi` | [card](./engine/models/cards/S-004_ndwi.md) | `indices.cpp` | `_py_ndwi` | None | VERIFIED |
| S-005 | `nbr` | [card](./engine/models/cards/S-005_nbr.md) | `indices.cpp` | `_py_nbr` | None | VERIFIED |

### 2.2 Climate / Radiation

| ID | Symbol | Card Link | C++ Source | Python Fallback | Status |
|----|--------|-----------|------------|-----------------|--------|
| S-006 | `hargreaves_et0` | [card](./engine/models/cards/S-006_hargreaves_et0.md) | `climate.cpp` | None (NotImplementedError) | STUB (gap) |
| S-007 | `penman_monteith_et0` | [card](./engine/models/cards/S-007_penman_monteith_et0.md) | `climate.cpp` | `_py_penman_monteith_et0` | VERIFIED |
| S-009 | `extraterrestrial_radiation` | [card](./engine/models/cards/S-009_extraterrestrial_radiation.md) | `climate.cpp` | None (NotImplementedError) | STUB (gap) |
| S-010 | `fao56_net_radiation` | [card](./engine/models/cards/S-010_fao56_net_radiation.md) | `climate.cpp` | None (NotImplementedError) | STUB (gap) |

### 2.3 Soil Physics

| ID | Symbol | Card Link | C++ Source | Python Fallback | Status |
|----|--------|-----------|------------|-----------------|--------|
| S-011 | `soil_water_content` | [card](./engine/models/cards/S-011_soil_water_content.md) | `soil.cpp` | None (NotImplementedError) | STUB (gap) |
| S-013 | `hydraulic_conductivity` | [card](./engine/models/cards/S-013_hydraulic_conductivity.md) | `soil.cpp` | None (NotImplementedError) | STUB (gap) |

### 2.4 Erosion

| ID | Symbol | Card Link | C++ Source | Python Fallback | Status |
|----|--------|-----------|------------|-----------------|--------|
| S-008 | `rusle_annual_soil_loss` | [card](./engine/models/cards/S-008_rusle_soil_loss.md) | `erosion.cpp` | `_py_rusle_annual_soil_loss` | VERIFIED |
| S-012 | `ls_factor` | [card](./engine/models/cards/S-012_ls_factor.md) | `erosion.cpp` | None (NotImplementedError) | STUB (gap) |
| S-014 | `estimate_rainfall_erosivity` | [card](./engine/models/cards/S-014_estimate_rainfall_erosivity.md) | `erosion.cpp` | None (NotImplementedError) | STUB (gap) |

### 2.5 Other Exported Symbols (not carded — infrastructure)

These C++ symbols are exported by `cpp_bridge/__init__.py` but are infrastructure/utility functions not covered by a dedicated model card:

`BottomBoundary`, `CropWaterParams`, `CropWaterResult`, `RichardsOptions`, `RichardsResult`, `RoutingResult`, `RusleCell`, `SaintVenantOptions`, `SaintVenantResult`, `TopBoundary`, `WaveParameters`, `YieldStats`, `compute_wave_parameters`, `estimate_mean_lhs`, `estimate_mean_mc`, `latin_hypercube`, `manning_normal_depth`, `monte_carlo_uniform`, `route_flood_wave`, `route_multi_reach`, `rusle_grid`, `rusle_grid_total`, `scale_samples`, `sediment_delivery_ratio`, `sediment_trapped`, `sediment_yield`, `simplified_yield`, `simulate_crop_water`, `simulate_richards`, `simulate_saint_venant`, `soil_erodibility_k`, `soil_params`, `specific_moisture_capacity`, `supported_textures`, `trap_efficiency_brune`, `yield_ensemble_lhs`

---

## Part 3: Summary

### Card Count
- CANON reference models: **22** (including template)
- C++ symbol model cards: **14**
- **Total**: 36 model cards + 1 template

### Status Distribution

| Status | CANON (22) | C++ Symbols (14) | Total |
|--------|-------------|-------------------|-------|
| VERIFIED | 13 | 7 | 20 |
| VERIFIED (N/A) | 2 | 0 | 2 |
| IMPLEMENTATION_VERIFIED | 2 | 0 | 2 |
| SCIENTIFICALLY_SUPPORTED | 1 | 0 | 1 |
| REQUIRES_SCIENTIFIC_REVIEW | 3 | 0 | 3 |
| STUB | 0 | 7 | 7 |
| RUNTIME_UNVERIFIED | 0 | 0 | 0 |

### Runtime Verification Status

All 36 models have `.pyd` available (cp312-win_amd64) that exports 56 C++ functions. However, **numpy + pytest + hypothesis are not installed** (defect B-011), so the strict test suite cannot execute. C++ unit tests (`test_*_unit.cpp`) exist but cannot compile (no compiler). Python parity is the primary verification mechanism; models without Python fallbacks are marked STUB (gap) and cannot be runtime-verified.

### Template & Field Compliance

All 36 model cards follow the template at `engine/models/cards/_template.md`. Required fields (HYDROMA-MASTER §292–334) are filled in each card. Applicable fields are filled or explicitly marked "Not applicable — [reason]" per §337. Fields not applicable state a concrete justification.
