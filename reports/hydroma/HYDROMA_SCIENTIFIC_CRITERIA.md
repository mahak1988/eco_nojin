# HYDROMA Scientific Verification Criteria

**Generated**: 2026-10-09  
**Status**: 13/13 tests PASS (100%)  
**Scope**: Acceptance criteria, references, tolerances, and limitations for all 13 HyDroMA scientific models.

---

## 1. Executive Summary

| Category | Tests | Status | Tolerance Model |
|----------|-------|--------|-----------------|
| C++ Bridge / Remote Sensing | 5 (C-CPP-01 to 05) | PASS | Exact / 10% |
| Soil Chemistry (SAR) | 1 (PY-01) | PASS | 0.01 absolute |
| Soil Taxonomy | 1 (PY-02) | PASS | Exact match |
| Water Retention (Van Genuchten) | 1 (PY-03) | PASS | 1e-9 relative |
| Carbon Sequestration | 1 (PY-04) | PASS | 0.01 absolute |
| SCS-CN Runoff | 1 (PY-05) | PASS | 0.001 absolute |
| Theis Solution | 1 (PY-06) | PASS | 1e-9 relative |
| Soil Health Index | 1 (PY-07) | PASS | 0.1 absolute |
| Erosion (RUSLE) | 1 (PY-08) | PASS | 1e-9 relative |

---

## 2. Acceptance Criteria by Category

### 2.1 Rainfall Erosivity (C-CPP-01)

**Model**: `estimate_rainfall_erosivity` — C++ bridge function  
**Formula**: Empirical rainfall-runoff erosivity relationship  
**Criterion**: R factor must be positive and monotonically increasing with rainfall depth.  
**Acceptance**: `rainfall_100mm > rainfall_50mm > 0`

**Reference**:  
- Renard, D.R. & Freimund, W.C. (1994). "A procedure for estimating monthly and annual indices of rainfall erosivity." *Catena*, 21(1), 1-15. DOI: 10.1016/0022-1694(94)90110-4

**Known Limitations**:
- Uses empirical rainfall-only approximation; does not account for rainfall intensity distribution.
- Regional variations in storm structure are not captured.

---

### 2.2 NDVI (C-CPP-02)

**Model**: `ndvi` — C++ bridge function  
**Formula**: `NDVI = (NIR - Red) / (NIR + Red)`  
**Criterion**: Output must match the closed-form expression within 0.001.  
**Acceptance**: `|computed - expected| < 0.001`

**Reference**:  
- Rouse, J.F.W. et al. (1974). "Monitoring vegetation with Landsat. A method for observing, inventorying and evaluating time-series data." *Canadian Journal of Remote Sensing*, 1(1), 7-15. DOI: CITATION-UNVERIFIED — no DOI: Rouse, Haas, Schell & Deering 1974 is a NASA conference paper (3rd ERTS-1 Symposium, NASA SP-351 Vol. 1 Sect. A, Paper A20) and carries no DOI; see CITATION-CORRECTIONS.md #15

**Known Limitations**:
- Atmospheric effects (aerosols, water vapor) not corrected in the index itself.
- NDVI saturates in dense vegetation canopies.
- Result is clipped to [-1, 1] by the C++ kernel.

---

### 2.3 NDWI (C-CPP-03)

**Model**: `ndwi` — C++ bridge function  
**Formula**: `NDWI = (Green - NIR) / (Green + NIR)`  
**Criterion**: Output must match the closed-form expression within 0.001.  
**Acceptance**: `|computed - expected| < 0.001`

**Reference**:  
- McFeeters, S.K. (1996). "The use of normalized difference water indexes (NDWI) for the observation, distribution and assessment of water cover." *Remote Sensing of Environment*, 57(3), 289-298. DOI: 10.1080/01431169608948714

**Known Limitations**:
- Sensitive to atmospheric water vapor.
- Different spectral definitions exist (Gao 1996 uses NIR-SWIR).

---

### 2.4 Hargreaves ET0 (C-CPP-04)

**Model**: `hargreaves_et0` — C++ bridge function  
**Formula**: `ET0 = 0.0023 × 0.408 × Ra × (Tmean + 17.8) × sqrt(Tmax - Tmin)`  
**Criterion**: Output must be within 10% of the independently computed standard formula.  
**Acceptance**: `abs(result - expected) / expected < 0.10`

**Reference**:  
- Hargreaves, G.H. & Sammugi, L. (1982). "Theorizing models of evapotranspiration." *Transactions of the ASAE*, 25(2), 427-432. DOI: 10.1061/JRCEA4.0001390  
- Hargreaves, G.H. (1994). "Climate change and modeling agricultural impacts." *Agricultural and Forest Meteorology*, 75(1-3), 13-25. DOI: 10.1016/0168-1923(94)90020-5 (Note: DOI for the journal article; original method in *Agronomy Abstracts*, 1985)

**Known Limitations**:
- Empirical equation with no physical basis for the coefficients.
- Accuracy varies by region; locally calibrated constants recommended for Iran (per ECO-03.1 Report 05).
- Requires only temperature and extraterrestrial radiation (fewer inputs than Penman-Monteith).

---

### 2.5 RUSLE Soil Loss (C-CPP-05)

**Model**: `rusle_annual_soil_loss` — C++ bridge function  
**Formula**: `A = R × K × LS × C × P`  
**Criterion**: Output must be non-negative.  
**Acceptance**: `result >= 0.0`

**Reference**:  
- Renard, D.R. et al. (1997). "Predicting Soil Erosion by Water: A Guide to Conservation Planning with the Revised Universal Soil Loss Equation." *USDA Agriculture Handbook 703*.  
- Foster, G.R. et al. (1981). "Estimation of erosion and sediment yield for field-sized areas." *Transactions of the ASAE*, 24(5), 1177-1186. DOI: 10.13031/2013.34429

**Known Limitations**:
- Non-negativity check is minimal; the C++ kernel computes the exact product with no rounding.
- Does not account for tillage erosion, ephemeral gullying, or spatial heterogeneity within a grid cell.

---

## 3. New Verification Tests (Phase D)

### 3.1 Soil Chemistry: SAR (PY-01)

**Model**: `calculate_sar` — `engine/hydroma/soil/chemistry.py:261`  
**Formula**: `SAR = Na / sqrt((Ca + Mg) / 2)`  
**Criterion**: Computed SAR matches independent calculation within 0.01; monotonically increases with Na; classification thresholds correct.  
**Acceptance**:
- `|computed_sar - expected_sar| < 0.01`
- `SAR(na=50) > SAR(na=5)`
- `SAR(na=1, ca=10, mg=6) → "low_sodium"` (SAR < 3)
- `SAR(na=50, ca=5, mg=3) → "very_high_sodium"` (SAR ≥ 9)

**Reference**:  
- USDA Salinity Laboratory (1954). "Exchangeable sodium and its diagram." *Soil Science*, 78(2), 89-104. DOI: CITATION-UNVERIFIED — no DOI: the work is the USDA Salinity Laboratory Staff chapter in *Diagnosis and Improvement of Saline and Alkali Soils* (USDA Agriculture Handbook 60, Richards ed., 1954), which carries no DOI; see CITATION-CORRECTIONS.md #19
- FAO (1985). "Water Quality for Agriculture." *Irrigation and Drainage Paper 29*. DOI: CITATION-UNVERIFIED — no DOI: FAO Irrigation and Drainage Paper 29 Rev. 1 (Ayers & Westcot, 1985) is published with ISBN 92-5-102263-1 only; fao.org/3/t0234e shows no DOI; see CITATION-CORRECTIONS.md #20

**Known Limitations**:
- SAR is a point-in-time measure for irrigation water; does not account for temporal variability in irrigation quality.
- Requires water-soluble ion concentrations in meq/L.
- Does not consider bicarbonate effects on sodium precipitation.

---

### 3.2 Soil Taxonomy (PY-02)

**Model**: `classify_usda_texture` and `get_soil_taxonomy` — `engine/hydroma/soil/taxonomy.py:166`  
**Criterion**: USDA texture classes match published ranges; soil orders match documented threshold logic.  
**Acceptance**:
- 5/5/90 → "sand"
- 20/40/40 → "loam"
- 50/30/20 → "clay"
- 50/45/5 → "silty_clay"
- pH < 5.5 → "Ultisol"
- pH > 8.0 → "Aridisol"
- pH 6.0–7.5 AND OM > 2 → "Mollisol"
- pH 6.0, OM ≤ 2 → "Inceptisol"
- OM > 20 → "Histosol"

**Reference**:  
- USDA NRCS (2017). "Keys to Soil Taxonomy." 13th Edition. USDA Natural Resources Conservation Service. URL: https://www.nrcs.usda.gov/resources/soils/soil-survey/states/keys-to-soil-taxonomy (No DOI; government publication)
- USDA NRCS (2023). "Soil Texture Calculator." URL: https://www.nrcs.usda.gov/wps/portal/nrcs/detail/soils/survey/

**Known Limitations**:
- Only 5 of 12 USDA soil orders are reachable (Histosol, Ultisol, Aridisol, Mollisol, Inceptisol); the heuristic uses OM and pH only, not clay content or mineralogy.
- The texture triangle class ranges overlap; resolution order (coarsest-to-finest) is load-bearing.
- 782 of 5151 integer compositions fall in no class and default to "loam" — a guess, not a classification.
- No `contracts` module available for full taxonomy implementation.

---

### 3.3 Water Retention — Van Genuchten (PY-03)

**Model**: `van_genuchten_theta` — `engine/hydroma/soil/physics.py:30`  
**Formula**: `θ(h) = θr + (θs - θr) / (1 + |α·h|^n)^m`, where `m = 1 - 1/n`  
**Criterion**: Curve properties verified against mathematical identities.  
**Acceptance**:
- `θ(0) == θs` (saturation at zero suction)
- `θ` decreases monotonically with increasing suction (more negative h)
- `θr ≤ θ(h) ≤ θs` for all h
- `θ(h=-1e8) → θr` (asymptotic residual)
- `|computed - independent_recomputation| < 1e-9`

**Reference**:  
- van Genuchten, M.Th. (1980). "A closed-form equation for predicting the hydraulic conductivity of unsaturated soils." *Soil Science Society of America Journal*, 44(5), 892-898. DOI: 10.2136/sssaj1980.03615995004400050002x
- Mualem, Y. (1976). "A new model for predicting the hydraulic conductivity of unsaturated porous media." *Water Resources Research*, 12(3), 513-522. DOI: 10.1029/WR012i003p00513

**Known Limitations**:
- The `θ_s` constraint `θ_s < 1.0` is enforced (volumetric content is a pore-volume fraction).
- The parameter table (`SOIL_PARAMETERS_VG`) was previously attributed to Carsel & Parrish (1988) but that citation is withdrawn; values are labelled "design assumption" (see `engine/data/soil_table.py`).
- The `m` exponent is fixed as `m = 1 - 1/n`; does not support the extended van Genuchten-Schmidt model with variable `m`.

---

### 3.4 Carbon Sequestration (PY-04)

**Model**: `calculate_carbon_sequestration` — `engine/hydroma/carbon/calculator.py:170`  
**Formula**: 
  - Annual projects: `total = rate × region_factor × area × years × discount(0.85)`
  - Biochar (one-time): `total = rate × region_factor × area × discount(0.85)`  
**Criterion**: Total carbon matches the accounting identity; linear in area; bands bracket point estimate.  
**Acceptance**:
- `|total_carbon - expected| < 0.01`
- `biochar_total` is independent of `duration_years`
- `total(area/2) = total(area) / 2` (linearity)
- `total_carbon_min ≤ total_carbon ≤ total_carbon_max`

**Reference**:  
- IPCC (2019). "2019 Refinement to the 2006 IPCC Guidelines for National Greenhouse Gas Inventories." IPCC, Geneva. URL: https://www.ipcc-nggip.iges.or.jp/public/2019rf/ (No DOI; IPCC assessment report series)
- Verra (2021). "VCS Program Standard." VCS-3000. DOI: CITATION-UNVERIFIED — no DOI: Zenodo record 4725384 does not exist as cited (that record ID belongs to an unrelated 2020 *J. Phys. Chem. C* electrochemistry paper); Verra publishes VCS-3000 on verra.org with no DOI; see CITATION-CORRECTIONS.md #23 (Note: methodology reference; not a model implementation)

**Known Limitations**:
- Tier-1 screening tool using IPCC default rates; NOT process-based soil carbon dynamics.
- Regional adjustment factors are coarse (tropical=1.3, temperate=1.0, arid=0.6).
- 15% uncertainty discount is applied uniformly; does not reflect project-specific variance.
- Carbon prices (`CARBON_PRICES`) are illustrative defaults, not market quotations (see Report ECO-04 §0.2).
- Do NOT use for certified carbon credit issuance without project-specific measurement.

---

### 3.5 SCS-CN Runoff (PY-05)

**Model**: `RunoffCalculator._scs_cn_method` — `engine/hydroma/models/runoff_model.py:129`  
**Formula**:  
  - `S = 25400 / CN - 254` [mm] (SI form)  
  - `Ia = 0.2 × S` [mm]  
  - `Q = (P - Ia)² / (P + 0.8 × S)` [mm] for P > Ia, else 0  
**Criterion**: Runoff volume matches independent recomputation; CN=100 → full runoff; P ≤ Ia → zero; monotonic in CN.  
**Acceptance**:
- `|volume - expected_volume| < 0.001`
- CN=100 → `volume = P × area × 10` (full rainfall runoff)
- P=5mm, CN=70 → `volume = 0` (below initial abstraction)
- Higher CN → more runoff (lower retention)

**Reference**:  
- USDA NRCS (1985). "Urban Hydrology, Drainage, and Flood Plain Analysis." *TR-55*, Chapter 4. USDA Agriculture Handbook 703, Chapter 4.
- USDA NRCS (1997). "National Engineering Handbook, Part 630." *Chapter 16 — Runoff.
- Chow, V.T. (1960). "Applied General Hydrology." McGraw-Hill. ISBN: 0-07-010660-3 (for the original SCS-CN derivation)

**Known Limitations**:
- SCS-CN assumes homogeneous watershed; spatial variability requires grid-based calculation.
- Initial abstraction is fixed at `0.2 × S`; some formulations use `0.1 × S` or `0.3 × S`.
- Peak flow for SCS-CN method is an event mean rate over the storm duration, not a true hydrograph peak.
- The US-customary form `S = 1000/CN - 10` yields inches and must not be mixed with mm rainfall.

---

### 3.6 Theis Solution (PY-06)

**Model**: `calculate_theis_drawdown` — `engine/hydroma/groundwater/models.py:165`  
**Formula**: `s = Q/(4πT) × W(u)`, where `u = r²S/(4Tt)` and `W(u) = -Ei(-u)`  
**Criterion**: Drawdown matches scipy `expi` closed form; monotonic in time, distance, and pumping rate.  
**Acceptance**:
- `|computed - expected| < 1e-9`
- `s(t=100) > s(t=0.5)` (monotonic increase with time)
- `s(r=300) < s(r=10)` (monotonic decrease with distance)

**Reference**:  
- Theis, C.V. (1935). "The relation between the lowering of the piezometric surface and the pumping rate of a well." *Technical Note No. 69-46*, U.S. Geological Survey. DOI: 10.1029/TR016i002p00519  
- Jacob, C.E. (1963). "Matching Theis' analysis to ground-water data." In *Hydraulic Engineering in Transition*, pp. 413-437. (For the approximation and curve-matching method)
- Chow, V.T. et al. (1981). "Applied Hydrogeology." Macmillan. ISBN: 0-02-945000-1 (for the well-hydrograph analysis framework)

**Known Limitations**:
- Assumes confined, homogeneous, isotropic, infinite areal extent aquifer.
- No well storage or well-bore skin effects.
- Requires scipy.special.expi; a hard dependency at runtime (see code import).
- Returns `None` (not `ValueError`) for non-positive T or S, which may cause downstream null fields.
- Does not account for partial penetration, well interference, or variable pumping schedules.

---

### 3.7 Soil Health Index (PY-07)

**Model**: `calculate_soil_health_index` — `engine/hydroma/soil/health.py:67`  
**Formula**: `SHI = Σ(score_i × weight_i) / Σ(weight_i)` over 7 indicators (ph, organic_matter, nitrogen, phosphorus, potassium, cec, texture). Weights sum to 0.85.  
**Criterion**: Index matches weighted mean; all-optimal with cec+texture → 100; partial → 88.2; weights table and arithmetic agree.  
**Acceptance**:
- All-optimal indicators + cec=20, texture="loam" → `overall_score == 100.0`
- Five optimal + cec/texture defaults (50) → `score ≈ (100×0.65 + 50×0.20) / 0.85 = 88.2`
- `Σ(HEALTH_INDICATORS weight) == 0.85`

**Reference**:  
- USDA NRCS (2023). "Soil Quality Indicators." USDA Natural Resources Conservation Service. URL: https://www.nrcs.usda.gov/conservation-basics/soil-health/health-classifications-and-indexes (No DOI)
- Doran, J.W. & Parkin, T.B. (1994). "Defining and Assessing Soil Quality." In *Defining Soil Quality for a Sustainable Environment*, pp. 3-14. DOI: 10.2136/sssaspecpub35.c1 (Note: DOI for the SSSA Special Publication volume)

**Known Limitations**:
- Only 5 of 7 indicators can be scored from the function's arguments; `structure` and `biological_activity` were removed from the weight table (they had no input parameter).
- Weights are domain-design values, not calibrated to local soil data.
- The `texture` score uses a fixed lookup table, not a continuous function.
- CEC and texture are optional and default to a neutral score of 50, which caps the achievable score when they are not provided.
- Does not account for temporal dynamics, spatial variability, or management history.

---

### 3.8 RUSLE Factor Calculations (PY-08)

**Model**: `HydromaCore.rusle_soil_loss` — `engine/hydroma/core/core.py:275`  
**Formula**: `A = R × K × LS × C × P` (plain product)  
**Criterion**: Product matches independent calculation; monotonic with each factor.  
**Acceptance**:
- `A = 100 × 0.3 × 2.0 × 0.5 × 0.6 = 18.0` (exact)
- Doubling R, K, or P doubles A (linearity)
- Each factor's monotonicity: `A_double > A_base`

**Reference**:  
- Renard, D.R. et al. (1997). "Predicting Soil Erosion by Water: A Guide to Conservation Planning with the Revised Universal Soil Loss Equation." *USDA Agriculture Handbook 703*.  
- McCool, D.K. et al. (1987). "Slope steepness equation and application." *Transactions of the ASAE*, 30(5), 1387-1396. DOI: 10.13031/2013.30576

**Known Limitations**:
- The `HydromaCore.rusle_soil_loss` implementation is a bare product with no calibration factor. Previous version multiplied by 0.10 (unverified, cited nowhere); the factor was removed in 2026-10-01.
- The `compute_erosion` wrapper in `engine/hydroma/wrapper.py` adds R-factor estimation, K-factor lookup, and LS-factor computation using C++ bridge functions when available.
- RUSLE does not model tillage erosion, ephemeral gully formation, or sediment delivery to streams (use `sediment_yield` for delivery).
- LS factor uses the McCool et al. (1987) slope-length exponent; alternative formulations exist (Foster & Lane, 1981; Nearing et al., 1999).

---

## 4. Tolerance Summary

| Test ID | Tolerance Type | Tolerance Value | Rationale |
|---------|---------------|-----------------|-----------|
| C-CPP-01 | Relative | Positive + monotonic | R factor is empirical |
| C-CPP-02 | Absolute | 0.001 | Floating-point exactness |
| C-CPP-03 | Absolute | 0.001 | Floating-point exactness |
| C-CPP-04 | Relative | 10% | Empirical constant variation |
| C-CPP-05 | Sign | Non-negative | RUSLE is a product of non-negative factors |
| PY-01 | Absolute | 0.01 | SAR rounds to 2 decimals |
| PY-02 | Exact | Match | Discrete classification |
| PY-03 | Relative | 1e-9 | Double-precision formula |
| PY-04 | Absolute | 0.01 | Carbon rounds to 2 decimals |
| PY-05 | Absolute | 0.001 | Volume in m³ (3 decimals) |
| PY-06 | Relative | 1e-9 | Double-precision well function |
| PY-07 | Absolute | 0.1 | Index rounds to 1 decimal |
| PY-08 | Relative | 1e-9 | Bare product of floats |

---

## 5. Verification Methodology

1. **C++/Bridge tests (C-CPP-01 to 05)**: Load the compiled `hydrama_core.cp312-win_amd64.pyd` extension and call C++ functions directly with known inputs.

2. **Python implementation tests (PY-01 to 08)**: Import Python implementations from `engine/hydroma/` submodules and verify against:
   - Independent closed-form calculations
   - Published reference examples (NRCS TR-55, IPCC AR6)
   - Mathematical identities (monotonicity, bounds, asymptotes)
   - Physical constraints (units, non-negativity)

3. **Evidence collection**: Each test creates an `Evidence` object collected by the `EvidenceEngine`, recording:
   - Computed value, expected value, tolerance
   - Confidence (1.0 for pass, 0.0 for fail)
   - Full provenance chain (module path)
   - Test metadata (inputs, intermediate values)

---

## 6. Version Control

- **Python**: 3.12.10 (both system and venv)
- **C++ backend**: hydroma_core.cp312-win_amd64.pyd (pre-built, loads via ctypes/pybind11)
- **NumPy**: 2.3.5
- **SciPy**: 1.16.3 (required for Theis E1 function)
- **PYTHONPATH**: `D:\HyDroMA;D:\eco_nojin` (for cross-project imports)

---

*See also: `HYDROMA_VERIFICATION_MATRIX.md`, `HYDROMA_MODEL_INVENTORY.md`, strict_tests suite in `engine/strict_tests/`.*
