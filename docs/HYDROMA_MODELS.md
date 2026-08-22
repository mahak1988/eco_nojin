# Hydroma Scientific Models Library

> A peer-reviewed collection of scientific models for precision agriculture, 
> water resource management, and landscape health assessment.

**Version:** 1.0  
**Authors:** EcoNojin Scientific Council  
**License:** Proprietary - EcoNojin Platform

---

## 1. EWSI — EcoNojin Water Stress Index

### Scientific Basis

A multi-source fusion index combining optical remote sensing, atmospheric 
conditions, and pedological factors to quantify crop water stress.

### Mathematical Formulation

$$
\text{EWSI} = w_1 \cdot (1 - \text{NDMI}) + w_2 \cdot \text{VPD}_{norm} + w_3 \cdot (1 - \theta/\theta_{fc})
$$

where:
- **NDMI** = (B8 - B11) / (B8 + B11) — Normalized Difference Moisture Index
- **VPD** = Vapour Pressure Deficit from AgERA5/ERA5 (kPa)
- **θ** = Soil moisture at root zone (m³/m³)
- **θ_fc** = Soil moisture at field capacity (from van Genuchten)
- **w₁, w₂, w₃** = Weights derived from crop type (default: 0.4, 0.3, 0.3)

### Output
- Range: [0, 1] where 0 = no stress, 1 = severe stress
- Classification: < 0.3 (optimal), 0.3–0.6 (mild), 0.6–0.8 (moderate), > 0.8 (severe)

### References
- Monteith, J.L. (1993). "The exchange of water and carbon by crops"
- Gao, B.C. (1996). "NDWI—A normalized difference water index"

---

## 2. HY-RUE — Hydroma Radiation Use Efficiency Model

### Scientific Basis

Monteith's biomass accumulation model enhanced with Sentinel-2 LAI retrieval 
and multi-factor stress functions.

### Mathematical Formulation

$$
B = \sum_{t=1}^{T} \text{PAR}_t \times f_{\text{IPAR},t} \times \varepsilon \times \prod_{i} f_{s,i,t}
$$

$$
Y = B \times \text{HI}
$$

where:
- **B** = Above-ground biomass (g/m²)
- **Y** = Yield (g/m²)
- **PAR** = Photosynthetically Active Radiation (MJ/m²/day)
- **f_IPAR** = 1 - exp(-k × LAI) — fraction of intercepted PAR
- **LAI** = Leaf Area Index from Sentinel-2 (BiOp algorithm)
- **ε** = Radiation use efficiency (g/MJ IPAR) — crop-specific
- **f_s,i** = Stress factors: water, temperature, nitrogen, salinity
- **HI** = Harvest index

### Novelty
Unlike AquaCrop which uses canopy cover, HY-RUE uses **observed LAI from Sentinel-2**
for real-time biomass estimation without calibration.

### References
- Monteith, J.L. (1977). "Climate and the efficiency of crop production"
- Steduto et al. (2009). "AquaCrop—The FAO crop model"

---

## 3. ECSI — EcoNojin Carbon Sequestration Index

### Scientific Basis

RothC-26.3 soil carbon model coupled with Sentinel-2 vegetation dynamics 
for estimating carbon sequestration potential.

### Mathematical Formulation

$$
\frac{dC}{dt} = I - k \cdot C \cdot f(T) \cdot f(M) \cdot f(P)
$$

where:
- **C** = Total organic carbon (t/ha)
- **I** = Carbon input from residues and roots (t/ha/year)
- **k** = Decomposition rate (pool-specific: DPM, RPM, BIO, HUM, IOM)
- **f(T)** = Temperature factor = exp(0.047 × T_mean - 0.86)
- **f(M)** = Moisture factor based on rainfall/evaporation ratio
- **f(P)** = Plant retain factor (land use specific)

### Output
- ΔSOC per year (t CO₂-eq/ha/year)
- Carbon credit potential for landscape fund

### References
- Coleman, K. & Jenkinson, D.S. (1996). "RothC-26.3"
- Stockmann et al. (2013). "The knowns, known unknowns and unknowns of SOC sequestration"

---

## 4. HDVI — Hydroma Drought Vulnerability Index

### Scientific Basis

Multi-scale drought index combining meteorological, agricultural, and 
hydrological drought indicators.

### Mathematical Formulation

$$
\text{HDVI}_{scale} = w_1 \cdot \text{SPI}_{scale} + w_2 \cdot \text{SPEI}_{scale} + w_3 \cdot \text{VHI} + w_4 \cdot \text{SMI}
$$

where:
- **SPI** = Standardized Precipitation Index (gamma distribution)
- **SPEI** = Standardized Precipitation-Evapotranspiration Index
- **VHI** = Vegetation Health Index = α·VCI + (1-α)·TCI
- **SMI** = Soil Moisture Index (from ERA5/AgERA5)
- **scale** ∈ {1, 3, 6, 12, 24} months

### Novelty
Integrates **real-time Sentinel-2 VHI** with **ERA5 SPEI** for comprehensive
early warning system.

### References
- McKee et al. (1993). "The relationship of drought frequency and duration to SPI"
- Vicente-Serrano et al. (2010). "A Multiscalar Drought Index (SPEI)"
- Kogan, F.N. (1995). "Application of vegetation index for drought monitoring"

---

## 5. EPIA — EcoNojin Precision Irrigation Advisor

### Scientific Basis

FAO-56 ETc calculation enhanced with satellite-derived Kc for real-time 
irrigation scheduling.

### Mathematical Formulation

$$
\text{ET}_c = \text{ET}_0 \times K_c \times K_s
$$

$$
I_{net} = \max(0, \text{ET}_c - P_{eff} - \Delta\text{SW})
$$

$$
I_{gross} = \frac{I_{net}}{\eta_{irr}}
$$

where:
- **ET₀** = Reference ET (FAO-56 Penman-Monteith from ERA5)
- **K_c** = Crop coefficient derived from LAI: K_c = 0.1 + 0.9 × LAI/LAI_max
- **K_s** = Soil water stress coefficient (from θ/θ_pwp)
- **P_eff** = Effective rainfall (USDA-SCS method)
- **ΔSW** = Change in soil water storage
- **η_irr** = Irrigation efficiency (method-specific)

### Output
- Irrigation timing (days until next irrigation)
- Irrigation amount (mm or m³/ha)
- Recommended method (drip/sprinkler/surface)

### References
- Allen et al. (1998). "FAO Irrigation and Drainage Paper 56"
- Jensen, M.E. & Allen, R.G. (2016). "Crop Water Requirements"

---

## 6. H-Pheno — Hydroma Phenology Detection

### Scientific Basis

Automatic detection of crop phenological stages from Sentinel-2 NDVI 
time series using derivative analysis.

### Mathematical Formulation

$$
\text{NDVI}(t) = \text{SG-filtered}(\text{NDVI}_{raw}(t))
$$

$$
\text{NDVI}'(t) = \frac{d\text{NDVI}}{dt}
$$

$$
\text{NDVI}''(t) = \frac{d^2\text{NDVI}}{dt^2}
$$

Key points:
- **SOS** (Start of Season): first positive zero-crossing of NDVI'
- **POS** (Peak of Season): maximum of NDVI
- **EOS** (End of Season): first negative zero-crossing of NDVI' after POS

### BBCH Mapping
- BBCH 0-19 (Emergence): Before SOS
- BBCH 20-59 (Vegetative): SOS to POS
- BBCH 60-89 (Reproductive): POS to EOS
- BBCH 90-99 (Senescence): After EOS

### Novelty
Uses **Savitzky-Golay smoothing** and **adaptive thresholds** for noise-robust
detection across different crop types.

### References
- White et al. (2009). "Derivation of phenological metrics from MODIS NDVI"
- Zhang et al. (2003). "Monitoring vegetation phenology using MODIS"

---

## 7. ESRI — EcoNojin Salinity Risk Index

### Scientific Basis

Multi-factor salinity assessment combining spectral indices, soil data,
and irrigation management.

### Mathematical Formulation

$$
\text{ESRI} = \alpha \cdot \text{SI}_{s2} + \beta \cdot \text{EC}_{soil,norm} + \gamma \cdot \text{LR}_{deficit}
$$

where:
- **SI_s2** = Salinity Index from Sentinel-2: SI = √(B02 × B04)
- **EC_soil** = Electrical conductivity (dS/m) from soil map or field measurement
- **LR_deficit** = Leaching requirement deficit: LR_req - LR_actual
- **LR_req** = EC_w / (5·EC_e - EC_w) (FAO-32 formula)
- **α, β, γ** = Weights (default: 0.3, 0.5, 0.2)

### Output
- Risk level: Low (< 0.3), Moderate (0.3–0.6), High (0.6–0.8), Severe (> 0.8)
- Recommendation: leaching fraction, gypsum application, crop rotation

### References
- Richards, L.A. (1954). "Diagnosis and Improvement of Saline and Alkali Soils"
- Ayers, R.S. & Westcot, D.W. (1985). "Water Quality for Agriculture (FAO-29)"

---

## 8. HLHS — Hydroma Landscape Health Score

### Scientific Basis

Composite index for landscape fund management combining vegetation, water,
soil, biodiversity, and carbon metrics.

### Mathematical Formulation

$$
\text{HLHS} = \sum_{i=1}^{n} w_i \cdot \frac{X_i - X_{i,min}}{X_{i,max} - X_{i,min}}
$$

where:
- **X_i** ∈ {NDVI_mean, WSI (Water Stress Index), SOC, SHDI (Shannon Diversity), ECSI, ...}
- **w_i** = Weights derived from local stakeholder priorities
- Normalization: min-max scaling per landscape unit

### Components (default weights)
| Component | Indicator | Weight |
|---|---|---|
| Vegetation | Mean NDVI | 0.20 |
| Water | 1 - EWSI | 0.20 |
| Soil | SOC content | 0.15 |
| Biodiversity | SHDI (from land cover) | 0.15 |
| Carbon | ECSI | 0.15 |
| Topography | Slope stability | 0.10 |
| Connectivity | Corridor integrity | 0.05 |

### Novelty
Provides **single score for landscape fund disbursement** with transparent
decomposition for accountability.

### References
- Shannon, C.E. (1948). "A Mathematical Theory of Communication"
- Nagendra, H. (2002). "Opposite trends in response for the Shannon and Simpson indices"

---

## Implementation Notes

All models are implemented in `engine/hydroma/models/` with:
- **Unit tests** with scientific validation data
- **Type annotations** for IDE support
- **Docstrings** with mathematical formulations
- **Vectorized NumPy operations** for performance
- **C++ bridge** via `hydroma_core` for compute-intensive models

## Validation Strategy

Each model is validated against:
1. Published literature values
2. Field measurements (where available)
3. Cross-validation with independent datasets
4. Sensitivity analysis (Sobol indices)
5. Uncertainty quantification (Monte Carlo)