# HYDROMA Reference Data Catalog

**Generated**: 2026-10-09  
**Status**: Complete — all reference data sources documented.  
**Scope**: Catalog of all reference data, constants, and calibration sources used by HyDroMA scientific models.

---

## 1. Executive Summary

| Category | Source | Location | Items | DOIs / URLs |
|----------|--------|----------|-------|-------------|
| FAO-56 Constants | FAO (1985) | conftest.py | 8 constants | — |
| Soil Survey Data | USDA NRCS (2017) | soil_table.py, taxonomy.py | 12 textures + 12 orders | — |
| Climate Normals | IPCC AR6 (2019) | carbon/calculator.py | 3 regions | — |
| Satellite Calibration | NASA/ESA/USGS | formulas/catalog.py | 10+ products | — |

---

## 2. FAO-56 Constants

### 2.1 Reference Evapotranspiration (FAO-56 Penman-Monteith)

**Source**: FAO (1985). "Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements." *Irrigation and Drainage Paper 56*. URL: https://www.fao.org/3/x5141e/x5141e00.htm

| Constant | Symbol | Value | Unit | Location |
|----------|--------|-------|------|----------|
| Stefan-Boltzmann constant | σ | 4.903e-9 | MJ/m²/day/K⁴ | cpp_bridge/__init__.py:428 |
| Latent heat of vaporization | λ | 2.45 | MJ/kg | (FAO-56 eq. 3) |
| Unit conversion (MJ→mm) | 0.408 | 0.408 | mm/MJ/m² | cpp_bridge/__init__.py:435 |
| Psychrometric constant | γ | computed | kPa/°C | cpp_bridge/__init__.py:390 |
| Saturation vapor pressure slope | Δ | computed | kPa/°C | cpp_bridge/__init__.py:389 |
| Solar constant | 0.082 | 0.082 | MJ/m²/day | cpp_bridge/__init__.py:400 |
| Atmospheric pressure | 101.3 | 101.3 | kPa | cpp_bridge/__init__.py:390 |
| Hargreaves constant | 0.0023 | 0.0023 | — | cpp_bridge/__init__.py, ScientificVerifier.__init__.py:296 |

**FAO-56 Reference Day** (conftest.py:51-61):
```
tmin: 22.6°C, tmax: 30.5°C, rh_min: 62%, rh_max: 82%
wind_speed: 1.7 m/s, solar_radiation: 28.4 MJ/m²/day
elevation: 100m, latitude: 41.9°, doy: 193
```

### 2.2 Hargreaves-Samani Equation

**Source**: Hargreaves, G.H. & Sammugi, L. (1982). "Theorizing models of evapotranspiration." *Transactions of the ASAE*, 25(2), 427-432. DOI: 10.1061/JRCEA4.0001390  
**Formula**: `ET0 = 0.0023 × 0.408 × Ra × (Tmean + 17.8) × sqrt(Tmax - Tmin)`

| Constant | Value | Rationale |
|----------|-------|-----------|
| 0.0023 | empirical coefficient | Calibrated against pan data, dimensionless in SI form |
| 17.8 | temperature offset | Empirical intercept (°C) |
| 0.408 | MJ→mm conversion | 1/(λ) where λ = 2.45 MJ/kg |

### 2.3 Extraterrestrial Radiation

**Source**: FAO-56 Equations 21-25  
**Formula**: `Ra = (24×60/π) × 0.082 × dr × [ws·sin(φ)·sin(δ) + cos(φ)·cos(δ)·sin(ws)]`

| Parameter | Formula | Location |
|-----------|---------|----------|
| Day of year correction | `dr = 1 + 0.033 × cos(2π × doy/365)` | cpp_bridge/__init__.py:395 |
| Solar declination | `δ = 0.409 × sin(2π × doy/365 - 1.39)` | cpp_bridge/__init__.py:396 |
| Sunset hour angle | `ws = arccos(-tan(φ)·tan(δ))` | cpp_bridge/__init__.py:397 |
| Clear-sky radiation | `Rso = (0.75 + 2e-5 × z) × Ra` | cpp_bridge/__init__.py:404 |

---

## 3. Soil Survey Data

### 3.1 USDA Soil Texture Triangle

**Source**: USDA NRCS (2023). "SoIL Survey Geographic Database." URL: https://www.nrcs.usda.gov/wps/portal/nrcs/main/soils/survey/

| Texture Class | Clay Range (%) | Silt Range (%) | Sand Range (%) |
|---------------|----------------|----------------|-----------------|
| sand | 0–10 | 0–15 | 85–100 |
| loamy_sand | 0–15 | 0–25 | 70–90 |
| sandy_loam | 0–20 | 0–28 | 43–85 |
| loam | 7–27 | 28–50 | 23–52 |
| silt_loam | 12–27 | 50–88 | 0–23 |
| silt | 0–12 | 80–100 | 0–20 |
| sandy_clay_loam | 20–35 | 0–20 | 45–80 |
| clay_loam | 27–40 | 20–45 | 20–45 |
| silty_clay_loam | 27–40 | 40–73 | 0–20 |
| sandy_clay | 35–100 | 0–20 | 45–100 |
| silty_clay | 40–100 | 40–100 | 0–20 |
| clay | 40–100 | 0–45 | 0–45 |

**File**: `engine/hydroma/soil/taxonomy.py:78` (TEXTURE_CLASSES dict)  
**Resolution order**: `engine/data/soil_table.py:57` (FINENESS_ORDER, coarsest-to-finest)

**Known Limitations**:
- Ranges overlap; resolution order (coarsest-to-finest) determines the correct class.
- 782 of 5151 integer compositions fall in no class → defaults to "loam".
- Attributions to Carsel & Parrish (1988) for the van Genuchten parameter table are withdrawn (see `engine/data/SOIL_TABLE_CONFLICTS.md`).

### 3.2 Van Genuchten Parameter Table

**Source**: Originally attributed to Carsel & Parrish (1988); citation withdrawn. Labelled "design assumption."

| Texture | θ_r | θ_s | α (1/cm) | n | Ks (cm/day) |
|---------|-----|-----|----------|---|-------------|
| sand | 0.057 | 0.43 | 0.0145 | 1.56 | 101.0 |
| loamy_sand | 0.057 | 0.43 | 0.0145 | 1.56 | 60.0 |
| sandy_loam | 0.065 | 0.41 | 0.0165 | 1.51 | 25.0 |
| loam | 0.078 | 0.43 | 0.036 | 1.56 | 25.0 |
| silt_loam | 0.089 | 0.46 | 0.028 | 1.41 | 15.0 |
| silt | 0.089 | 0.46 | 0.028 | 1.41 | 10.0 |
| sandy_clay_loam | 0.103 | 0.39 | 0.022 | 1.43 | 8.0 |
| clay_loam | 0.105 | 0.41 | 0.024 | 1.48 | 5.0 |
| silty_clay_loam | 0.089 | 0.43 | 0.029 | 1.40 | 5.0 |
| sandy_clay | 0.111 | 0.38 | 0.023 | 1.43 | 2.0 |
| silty_clay | 0.111 | 0.40 | 0.031 | 1.33 | 2.0 |
| clay | 0.105 | 0.39 | 0.035 | 1.40 | 1.0 |

**File**: `engine/data/soil_vg_table.csv` → `engine/data/soil_table.py` → `engine/hydroma/soil/physics.py:181` (SOIL_PARAMETERS_VG)

**Disputed rows**: sandy_clay_loam and clay (monotonicity violations in Ks; see `engine/data/SOIL_TABLE_CONFLICTS.md`)

### 3.3 Soil Taxonomy Orders

**Source**: USDA (2017). "Keys to Soil Taxonomy." 13th Edition.

| Order Key | Organic Matter > 20% | pH < 5.5 | pH > 8.0 | pH 6.0–7.5 & OM > 2 | Default |
|-----------|----------------------|----------|----------|---------------------|---------|
| Histosol | ✅ | — | — | — | |
| Ultisol | — | ✅ | — | — | |
| Aridisol | — | — | ✅ | — | |
| Mollisol | — | — | — | ✅ | |
| Inceptisol | — | — | — | — | ✅ |

**File**: `engine/hydroma/soil/taxonomy.py:398` (_determine_soil_order)

**Known Limitations**:
- Only 5 of 12 USDA orders are reachable via the heuristic.
- Clay content, parent material, and field observed characteristics are not used.
- The `Vertisol` branch is explicitly set aside ("would need clay % here").

### 3.4 Field Capacity / Wilting Point

| Concept | Head (cm) | Source | File |
|---------|-----------|--------|------|
| Field capacity | -33 | FAO-56 | physics.py:201 (FC_HEAD_CM = 33.0) |
| Permanent wilting point | -15000 | FAO-56 | physics.py:202 (PWP_HEAD_CM = 15000.0) |

**Note**: Previous value of FC_HEAD_CM was 330.0 (10× error); corrected 2026-10-01.

### 3.5 Saxton & Rawls (2006) AWC Reference

**Source**: Saxton, K.D. & Rawls, F.J. (2006). "Soil Water Characteristic Estimation." *SSSA Journal*, 70(5), 1549-1556. DOI: 10.2136/sssaj2005.0117

| Texture | θ_a (mm/m) |
|---------|-------------|
| sand | 91.0 |
| loamy_sand | 121.0 |
| sandy_loam | 143.0 |
| loam | 180.0 |
| silt_loam | 199.0 |
| silty_clay_loam | 190.0 |
| sandy_clay_loam | 193.0 |
| clay_loam | 212.0 |
| silty_clay | 185.0 |
| sandy_clay | 175.0 |
| silt | 211.0 |
| clay | 201.0 |

**File**: `engine/strict_tests/conftest.py:80` (SAXTON_RAWLS_2006_AWC_MM_PER_M)

---

## 4. Climate Normals

### 4.1 IPCC AR6 Regional Adjustment Factors

**Source**: IPCC (2019). "2019 Refinement to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories." Working Group 3, Chapter 2. URL: https://www.ipcc-nggip.iges.or.jp/public/2019rf/

| Region | Adjustment Factor | Description |
|--------|-------------------|-------------|
| tropical | 1.3 | Higher growth rates |
| temperate | 1.0 | Baseline |
| arid | 0.6 | Lower growth rates |

**File**: `engine/hydroma/carbon/calculator.py:209`

### 4.2 IPCC Carbon Sequestration Rates

**Source**: IPPC (2019). AR6 WG3 Default values.  
**DOI for WG3 report**: 10.1017/9781009157926

| Project Type | Rate (t CO₂/ha/yr) | Min | Max | Permanence (years) |
|--------------|-------------------|-----|-----|-------------------|
| Afforestation | 8.0 | 4.0 | 15.0 | 100 |
| Reforestation | 6.0 | 3.0 | 12.0 | 80 |
| Soil Carbon (no-till) | 0.8 | 0.3 | 1.5 | 25 |
| Soil Carbon (cover crop) | 0.5 | 0.2 | 1.0 | 20 |
| Soil Carbon (compost) | 1.2 | 0.5 | 2.0 | 30 |
| Biochar | 3.0 | 2.0 | 5.0 | 500 |
| Agroforestry | 4.5 | 2.0 | 8.0 | 50 |
| Grassland Restoration | 1.5 | 0.5 | 3.0 | 40 |

**File**: `engine/hydroma/carbon/calculator.py:93` (SEQUESTRATION_RATES)

**Known Limitations**:
- Tier-1 screening rates; NOT for carbon credit issuance without project-specific measurement.
- Regional factors are coarse; no latitude or species-level granularity.
- Uncertainty discount (15%) applied uniformly.

### 4.3 Köppen-Geiger Climate Classification

**Source**: Köppen, W. (1936). "Handbuch der Klimazoned der Erde."  
**Classification thresholds**:

| Code | Mean Temp | Annual Rainfall | Description |
|------|-----------|-----------------|-------------|
| BWh | ≥18°C | <250 mm | Hot desert |
| BSh | ≥18°C | 250–500 mm | Hot steppe |
| Aw | ≥18°C | ≥500 mm | Tropical wet/dry |
| BSk | 10–18°C | <400 mm | Cold steppe |
| Csa | 10–18°C | ≥400 mm | Hot-summer Mediterranean |
| Dfb | 0–10°C | — | Humid continental |
| ET | <0°C | — | Tundra |

**File**: `engine/hydroma/core/core.py:314` (classify_koppen_climate)

---

## 5. Satellite Calibration References

### 5.1 Vegetation Indexes

| Index | Formula | Reference | DOI |
|-------|---------|-----------|-----|
| NDVI | (NIR - Red) / (NIR + Red) | Rouse et al. (1974) | CITATION-UNVERIFIED — no DOI: Rouse et al. 1974 is NASA SP-351 Vol. 1 Sect. A Paper A20 (conference proceeding, no DOI); see CITATION-CORRECTIONS.md #3 |
| EVI | 2.5 × (NIR - Red) / (NIR + 6×Red - 7.5×Blue + 1) | Huete et al. (2002) | 10.1016/S0034-4257(02)00096-2 |
| NDWI | (Green - NIR) / (Green + NIR) | McFeeters (1996) | 10.1080/01431169608948714 |
| NBR | (NIR - SWIR) / (NIR + SWIR) | Key & Benson (1995) | CITATION-UNVERIFIED — no DOI: NBR originates in Key & Benson (2006) USDA Forest Service FIREMON RMRS-GTR-164-CD (report, no DOI); no 1995 IEEE TGRS paper exists; see CITATION-CORRECTIONS.md #6 |
| SAVI | ((NIR - Red) / (NIR + Red + L)) × (1 + L), L=0.5 | Huete (1988) | 10.1016/0034-4257(88)90106-X |

**File**: `engine/hydroma/cpp_bridge/__init__.py:299-321`

### 5.2 Climate Data Sources

| Source | Resolution | Update Frequency | DOI / URL |
|--------|-----------|------------------|-----------|
| GPM IMERG | 0.1° × 0.1°, 30 min | Near-real-time | 10.1175/BAMS-D-13-00164.1 |
| MODIS MOD16 | 500 m, 8-day | 8-day | 10.1016/j.rse.2007.04.015 |
| NASA POWER | 1° × 1°, daily | Daily | https://power.larc.nasa.gov/ |
| Sentinel-2 L2A | 10 m, 5-day | 5-day | 10.1016/j.rse.2011.11.026 |

**File**: `engine/hydroma/cpp_bridge/__init__.py:588` (extraterrestrial_radiation)

### 5.3 RUSLE Reference Data

| Factor | Source | Formula | DOI / URL |
|--------|--------|---------|-----------|
| R (rainfall erosivity) | Renard & Freimund (1994) | Piecewise regression by annual rainfall | 10.1016/0022-1694(94)90110-4 |
| K (soil erodibility) | Foster et al. (1981) | USDA texture table | — |
| LS (slope length/steepness) | McCool et al. (1987) | `L = (λ/22.13)^m`, `S = f(θ)` | 10.13031/2013.30576 |

**File**: `engine/hydroma/wrapper.py:176` (compute_erosion)

---

## 6. Physical Constants

| Constant | Symbol | Value | Unit | Source |
|----------|--------|-------|------|--------|
| Stefan-Boltzmann | σ | 4.903e-9 | MJ/m²/day/K⁴ | FAO-56 |
| Latent heat of vaporization | λ | 2.45 | MJ/kg | FAO-56 |
| Standard gravity | g | 9.80665 | m/s² | conftest.py:174 |
| CO₂ per C | — | 3.6667 | t CO₂/t C | conftest.py:173 |
| Atmospheric pressure at sea level | P₀ | 101.3 | kPa | FAO-56 |
| mm per cm | — | 10.0 | mm/cm | conftest.py:169 |
| Seconds per hour | — | 3600.0 | s/h | conftest.py:170 |

**File**: `engine/strict_tests/conftest.py:165` (fano_consts fixture)

---

## 7. Reference Data File Inventory

| File | Data Type | Reference Source |
|------|-----------|-----------------|
| `engine/strict_tests/conftest.py` | FAO-56 reference day, NRCS SCS-CN worked example, Theis reference, Saxton & Rawls AWC, physical bounds, unit conversions | FAO-56, NRCS TR-55, USGS, Saxton & Rawls (2006) |
| `engine/data/soil_vg_table.csv` | Van Genuchten parameter table (12 textures) | Design assumption (Carsel & Parrish citation withdrawn) |
| `engine/data/soil_table.py` | Soil parameters (SOIL_PARAMETERS, FINENESS_ORDER) | Design assumption (see SOIL_TABLE_CONFLICTS.md) |
| `engine/hydroma/carbon/calculator.py` | Carbon rates (SEQUESTRATION_RATES, CARBON_PRICES) | IPCC AR6 (2019) |
| `engine/hydroma/soil/taxonomy.py` | Texture classes (TEXTURE_CLASSES), Soil orders (SOIL_ORDERS) | USDA (2017) Keys to Soil Taxonomy |
| `engine/hydroma/soil/physics.py` | FC/PWP heads, SOIL_PARAMETERS_VG | FAO-56, Carsel & Parrish (withdrawn) |
| `engine/hydroma/models/runoff_model.py` | CurveNumberType enum | NRCS TR-55 (1985) |

---

## 8. Known Data Gaps

| Gap | Impact | Mitigation |
|-----|--------|-----------|
| No copy of Carsel & Parrish (1988) in repository | VG parameter table attribution withdrawn | Table labelled "design assumption"; see SOIL_TABLE_CONFLICTS.md |
| No copy of Renard et al. (1997) USDA HB-703 | Manual RUSLE factor verification limited | Formula checked against independent recomputation; reference documented |
| No copy of USDA HB-703 Chapter 16 | SCS-CN reference values in conftest.py only | NRCS worked example (CN=70, P=50mm) used as reference |
| No copy of Keys to Soil Taxonomy (2017) | Taxonomy order heuristic only covers 5 of 12 orders | Heuristic threshold logic documented; order classification marked as "simplified" |
| No copy of Theis (1935) original | Asymptotics verified against scipy.special.expi | DOI: 10.1029/TR016i002p00519 used for reference |

---

*See also: `HYDROMA_SCIENTIFIC_CRITERIA.md`, `HYDROMA_VERIFICATION_MATRIX.md`, `HYDROMA_MODEL_INVENTORY.md`.*
