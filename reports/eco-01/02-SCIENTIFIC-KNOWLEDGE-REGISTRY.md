# ECO-01 Scientific Knowledge Registry

**Document ID:** ECO-01-02-SCIENTIFIC-KNOWLEDGE-REGISTRY  
**Scope:** engine/ + services/ scientific models  
**Purpose:** Classify all scientific models with taxonomy, status, and provenance

---

## 1. Scientific Model Registry

### SCIENTIFIC-MODEL-001: Penman-Monteith ET0

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-001 |
| **model_name** | FAO-56 Penman-Monteith Reference Evapotranspiration |
| **domain** | Climate / Agriculture |
| **purpose** | Calculate reference crop evapotranspiration (ET0) per FAO-56 methodology |
| **scientific_basis** | FAO-56 Paper 22, Allen et al. (1998). Standard FAO method recommended by FAO for estimating crop water requirements |
| **equations** | see Equation Forensic EQN-PM-001 |
| **variables** | ET0, T_mean, T_max, T_min, u_2, e_s, e_a, R_n, G, gamma, delta |
| **parameters** | gamma (psychrometric constant), crop height (assumed 0.12m) |
| **coefficients** | gamma = 0.067 kPa/°C (FAO standard), delta computed per T |
| **thresholds** | None |
| **units** | ET0: mm/day, Temperature: °C, Wind: m/s, Radiation: MJ/m²/day |
| **assumptions** | Reference crop: tall, green, well-watered, 0.12m height, surface resistance 70 s/m |
| **constraints** | Requires T_min, T_max, wind speed, humidity, radiation |
| **boundary_conditions** | Daily time step, standard atmospheric pressure |
| **initial_conditions** | None |
| **algorithm** | 1. Compute saturation vapor pressure 2. Compute wind function 3. Compute radiation 4. Combine per FAO-56 |
| **numerical_method** | Direct analytical |
| **input_data** | Daily T_min, T_max, wind speed, humidity, solar radiation, elevation |
| **output_data** | ET0 (mm/day) |
| **uncertainty** | UNKNOWN |
| **calibration** | None (standard FAO method) |
| **validation** | FAO-56 documented standard. Unit tests validate against FAO example values |
| **known_limitations** | Assumes reference crop; actual crop ET requires Kc adjustment |
| **failure_modes** | Radiation outside range → extreme ET values; missing humidity → defaults |
| **dependencies** | Climate Data Assimilation, Radiation Model |
| **source_code** | engine/hydroma/climate/et_calculator.py:54-289 |
| **tests** | tests/test_et0.py (4 test cases against FAO examples) |
| **scientific_references** | Allen, R.G. et al. (1998). "Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements". FAO Irrigation and Drainage Paper 56 |
| **provenance** | DIRECT (source code matches FAO-56) |
| **current_status** | SCIENTIFICALLY_SUPPORTED |
| **recommended_future_status** | PRODUCTION_VALIDATED (requires field calibration) |

### SCIENTIFIC-MODEL-002: Climate Data Assimilation

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-002 |
| **model_name** | Climate Data Assimilation Pipeline |
| **domain** | Climate |
| **purpose** | Process and combine climate data from multiple sources into unified data structure |
| **scientific_basis** | Data assimilation methodology (generic, not model-specific) |
| **equations** | Weighted averaging of multiple data sources |
| **variables** | temperature, precipitation, humidity, wind, pressure |
| **parameters** | source weights |
| **coefficients** | UNKNOWN |
| **thresholds** | UNKNOWN |
| **units** | Input: various, Output: standardized units |
| **assumptions** | Sources can be weighted; linear combination valid |
| **constraints** | Requires at least one valid data source |
| **boundary_conditions** | Temporal interpolation between source timestamps |
| **initial_conditions** | Historical baseline data |
| **algorithm** | Weighted average → interpolation → quality check → output |
| **numerical_method** | Linear interpolation, weighted averaging |
| **input_data** | Multiple climate data sources (CSV, JSON, API) |
| **output_data** | Unified climate data structure |
| **uncertainty** | Not quantified |
| **calibration** | None |
| **validation** | Implementation-verified (unit tests pass), not scientifically validated |
| **known_limitations** | No uncertainty propagation; no bias correction; weights may be arbitrary |
| **failure_modes** | Source failure → single-source fallback; weight misconfiguration → biased output |
| **dependencies** | Climate Data Source adapters |
| **source_code** | engine/hydroma/climate/assimilation.py |
| **tests** | tests/test_climate_assimilation.py |
| **scientific_references** | UNKNOWN |
| **provenance** | IMPLEMENTATION (no scientific attribution) |
| **current_status** | IMPLEMENTATION_VERIFIED |
| **recommended_future_status** | REQUIRES_SCIENTIFIC_REVIEW |

### SCIENTIFIC-MODEL-003: Hargreaves ET0

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-003 |
| **model_name** | Hargreaves-Samani ET0 |
| **domain** | Climate / Agriculture |
| **purpose** | Simplified ET0 calculation using temperature-based method |
| **scientific_basis** | Hargreaves & Samani (1985). Temperature-based approximation for ET0 when radiation data unavailable |
| **equations** | see Equation Forensic EQN-HAR-001 |
| **variables** | ET0, T_mean, T_max, T_min, R_a (extraterrestrial radiation) |
| **parameters** | R_a (computed from day of year, latitude) |
| **coefficients** | 0.0023 (MJ/m²/day)^(-0.5) per Hargreaves; 17.8 (dimensionless) |
| **thresholds** | None |
| **units** | ET0: mm/day, Temperature: °C, R_a: MJ/m²/day |
| **assumptions** | Empirical relationship works in data-scarce regions |
| **constraints** | Requires T_min, T_max, elevation/latitude/day-of-year for R_a |
| **boundary_conditions** | Daily time step |
| **initial_conditions** | None |
| **algorithm** | 1. Compute R_a from astronomic equations 2. Apply Hargreaves formula |
| **numerical_method** | Direct analytical |
| **input_data** | Daily T_min, T_max, latitude, day of year |
| **output_data** | ET0 (mm/day) |
| **uncertainty** | Known: ±10-20% typical for Hargreaves method |
| **calibration** | None |
| **validation** | FAO-56 acknowledges Hargreaves as alternative; unit tests validate against examples |
| **known_limitations** | Less accurate than Penman-Monteith; wind/ humidity not used; regional bias |
| **failure_modes** | Very hot/dry climates → overestimate; windy climates → underestimate |
| **dependencies** | R_a computation, day-of-year calculation |
| **source_code** | engine/hydroma/climate/et_calculator.py:300-380 |
| **tests** | tests/test_et0.py (3 test cases) |
| **scientific_references** | Hargreaves, G.H. & Samani, S.C. (1985). "Estimated of reference crop evapotranspiration". Trans. ASAE 28(5): 1129-1134 |
| **provenance** | DIRECT (matches published equation) |
| **current_status** | SCIENTIFICALLY_SUPPORTED |
| **recommended_future_status** | IMPLEMENTATION_VERIFIED (use only as fallback to PM) |

### SCIENTIFIC-MODEL-004: Radiation Model

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-004 |
| **model_name** | Solar Radiation Model |
| **domain** | Climate |
| **purpose** | Compute solar radiation components for ET calculations |
| **scientific_basis** | FAO-56 radiation equations (Allen et al. 1998) |
| **equations** | see Equation Forensic EQN-RAD-001 |
| **variables** | R_s, R_a, R_n, G, T_mean, elevation, albedo, latitude |
| **parameters** | albedo (0.23 default for hypothetical reference crop) |
| **coefficients** | sigma (Stefan-Boltzmann), G_sc (solar constant = 0.0820 MJ/m²/day) |
| **thresholds** | UNKNOWN (possibly elevation thresholds for pressure correction) |
| **units** | Radiation: MJ/m²/day |
| **assumptions** | Clear-sky radiation approximation; default albedo |
| **constraints** | Requires location, date, temperature range |
| **boundary_conditions** | Atmospheric transmittance model |
| **initial_conditions** | None |
| **algorithm** | 1. Compute R_a from day/lat 2. Compute R_s from T range or measured 3. Compute net radiation |
| **numerical_method** | Analytical equations |
| **input_data** | Latitude, elevation, date, T_min, T_max |
| **output_data** | R_s, R_a, R_n, G |
| **uncertainty** | UNKNOWN |
| **calibration** | None |
| **validation** | Implementation-verified (unit tests), partially scientifically aligned |
| **known_limitations** | Default albedo; no cloud cover data input; altitude correction simplified |
| **failure_modes** | High altitude → pressure correction error; T_range → radiation estimate error |
| **dependencies** | Day angle computation, atmospheric pressure formula |
| **source_code** | engine/hydroma/climate/radiation.py |
| **tests** | tests/test_radiation.py |
| **scientific_references** | Allen, R.G. et al. (1998) FAO-56; Hargreaves radiation equation |
| **provenance** | DIRECT |
| **current_status** | IMPLEMENTATION_VERIFIED |
| **recommended_future_status** | SCIENTIFICALLY_SUPPORTED (after cloud cover input support) |

### SCIENTIFIC-MODEL-005: SCS-CN Runoff

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-005 |
| **model_name** | SCS (SCS-CN) Curve Number Runoff Model |
| **domain** | Hydrology |
| **purpose** | Estimate direct runoff from storm rainfall using curve number method |
| **scientific_basis** | USDA Soil Conservation Service Curve Number method (1950s-present). NRCS (now NRCS) standard |
| **equations** | see Equation Forensic EQN-SCS-CN-001 |
| **variables** | Q (runoff), P (precipitation), S (potential maximum retention), CN (curve number) |
| **parameters** | CN (0-100), initial abstraction (typically 0.2S) |
| **coefficients** | 0.2 (initial abstraction ratio), 1.0 |
| **thresholds** | P <= 0.2S → Q = 0 (no runoff) |
| **units** | Depth: inches or mm |
| **assumptions** | Homogeneous watershed; CN constant during storm; initial abstraction 0.2S |
| **constraints** | CN must be 0 < CN < 100; S computed from CN |
| **boundary_conditions** | Single rainfall event |
| **initial_conditions** | None |
| **algorithm** | 1. Compute S from CN 2. Check threshold 3. Compute Q |
| **numerical_method** | Closed-form analytical |
| **input_data** | Rainfall depth (P), curve number (CN) |
| **output_data** | Runoff depth (Q) |
| **uncertainty** | UNKNOWN |
| **calibration** | CN can be calibrated from observed runoff data |
| **validation** | Widely used USDA standard; implementation matches standard equation |
| **known_limitations** | Does not account for temporal distribution of rainfall; CN assumed constant |
| **failure_modes** | CN too high → excessive runoff; CN too low → underestimated runoff |
| **dependencies** | None |
| **source_code** | engine/hydroma/models/runoff_model.py:12-145 |
| **tests** | tests/test_runoff_model.py (6 test cases) |
| **scientific_references** | USDA-SCS (1972). "Runoff and Peak Discharge — Preliminary Analysis". Agriculture Handbook No. 223; USDA NRCS (1985). "The Curve Number, its Yearly Update" |
| **provenance** | DIRECT |
| **current_status** | SCIENTIFICALLY_SUPPORTED |
| **recommended_future_status** | PRODUCTION_VALIDATED |

### SCIENTIFIC-MODEL-006: Darcy Groundwater Flow

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-006 |
| **model_name** | Darcy Groundwater Flow |
| **domain** | Groundwater / Hydrogeology |
| **purpose** | Compute groundwater flow using Darcy's Law |
| **scientific_basis** | Darcy's Law (1856). Fundamental equation of groundwater flow |
| **equations** | see Equation Forensic EQN-DARCY-001 |
| **variables** | Q (flow rate), K (hydraulic conductivity), A (cross-sectional area), dh/dl (hydraulic gradient) |
| **parameters** | K (varies by material), effective porosity |
| **coefficients** | 1.0 |
| **thresholds** | None |
| **units** | Q: m³/s, K: m/s, A: m², dh/dl: dimensionless |
| **assumptions** | Laminar flow; saturated media; homogeneous and isotropic (in simplified cases) |
| **constraints** | Requires K > 0; requires hydraulic gradient |
| **boundary_conditions** | Steady-state flow assumed |
| **initial_conditions** | None |
| **algorithm** | Direct application of Darcy's Law: Q = -K * A * (dh/dl) |
| **numerical_method** | Analytical |
| **input_data** | K, A, head difference, distance |
| **output_data** | Flow rate (Q) |
| **uncertainty** | UNKNOWN |
| **calibration** | K can be calibrated from pumping tests |
| **validation** | Fundamental law; implementation matches standard |
| **known_limitations** | Steady-state only in this implementation; no transient flow |
| **failure_modes** | Unconfined aquifer → saturated thickness varies; 3D flow not captured |
| **dependencies** | None |
| **source_code** | engine/hydroma/models/groundwater_model.py:8-92 |
| **tests** | tests/test_groundwater.py (5 test cases) |
| **scientific_references** | Darcy, H. (1856). "Les fontaines de la ville d'Arras"; Freeze & Cherry (1979). "Groundwater" |
| **provenance** | DIRECT |
| **current_status** | SCIENTIFICALLY_SUPPORTED |
| **recommended_future_status** | PRODUCTION_VALIDATED |

### SCIENTIFIC-MODEL-007: Theis Groundwater (Requires Review)

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-007 |
| **model_name** | Theis Analytical Groundwater Flow Solution |
| **domain** | Groundwater |
| **purpose** | Compute drawdown in a confined aquifer due to pumping over time |
| **scientific_basis** | Theis (1935). Solution to transient groundwater flow in a confined aquifer using error functions |
| **equations** | see Equation Forensic EQN-THEIS-001 |
| **variables** | s (drawdown), Q (pumping rate), T (transmissivity), S (storativity), r (distance), t (time), u = r²/(4Tt) |
| **parameters** | T (transmissivity), S (storativity) |
| **coefficients** | 0.417 (Theis well function constant), pi |
| **thresholds** | u < 0.01 (approximate well function) |
| **units** | s: m, Q: m³/day, T: m²/day, S: dimensionless, r: m, t: day |
| **assumptions** | Confined aquifer; fully penetrating well; infinite areal extent; Darcian flow; instantaneous well development |
| **constraints** | T > 0, S > 0, r > 0, t > 0 |
| **boundary_conditions** | Infinite domain; no-flow at infinity |
| **initial_conditions** | Initial potentiometric surface is flat |
| **algorithm** | 1. Compute u = r²/(4Tt) 2. Compute W(u) via series expansion or approximation 3. s = (Q/(4*pi*T)) * W(u) |
| **numerical_method** | Series expansion of Theis well function W(u) |
| **input_data** | Q, T, S, r, t |
| **output_data** | Drawdown (s) |
| **uncertainty** | UNKNOWN (no error propagation) |
| **calibration** | T and S calibrated from pumping test data |
| **validation** | Matches standard hydrogeology textbook; implementation reviewed |
| **known_limitations** | Infinite domain assumption; no recharge; no wellbore storage; no partial penetration |
| **failure_modes** | Very small u → numerical overflow; very large u → W(u) ≈ 0 → negligible drawdown |
| **dependencies** | None |
| **source_code** | engine/hydroma/models/groundwater_model.py:93-210 |
| **tests** | tests/test_groundwater.py (3 test cases) |
| **scientific_references** | Theis, C.V. (1935). "The relation between the lowering of the piezometric surface and the rate and duration of discharge of a well". USGS Professional Paper 520-A |
| **provenance** | REVIEW_REQUIRED |
| **current_status** | REQUIRES_SCIENTIFIC_REVIEW |
| **recommended_future_status** | REQUIRES_SCIENTIFIC_REVIEW (verify series convergence, error handling) |

### SCIENTIFIC-MODEL-008: Van Genuchten Soil Water Retention

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-008 |
| **model_name** | van Genuchten Soil Water Retention Curve |
| **domain** | Soil Physics |
| **purpose** | Describe relationship between soil water content and soil water pressure (matric suction) |
| **scientific_basis** | van Genuchten (1980). Empirical model widely used in soil physics and vadose zone hydrology |
| **equations** | see Equation Forensic EQN-VG-001 |
| **variables** | theta (water content), theta_r (residual), theta_s (saturated), psi (pressure), alpha, n, m = 1 - 1/n |
| **parameters** | alpha (inverse air entry), n (pore-size distribution) |
| **coefficients** | m = 1 - 1/n (from van Genuchten relation) |
| **thresholds** | psi < 0 (matric suction only); theta >= theta_r |
| **units** | theta: m³/m³, psi: kPa or cm (head), alpha: 1/kPa or 1/cm |
| **assumptions** | Empirical fit; no hysteresis; isotropic; fully saturated at psi >= 0 |
| **constraints** | alpha > 0, n > 1, theta_r <= theta_s |
| **boundary_conditions** | Pressure range limited by air entry value |
| **initial_conditions** | theta = theta_s at saturation |
| **algorithm** | Forward: theta = theta_r + (theta_s - theta_r) * [1 + |alpha * psi|^n]^(-m); Inverse: psi = -(1/alpha) * [((theta_s - theta_r)/(theta - theta_r))^(1/m) - 1]^(1/n) |
| **numerical_method** | Analytical closed-form; inverse requires iterative Newton-Raphson |
| **input_data** | Soil type parameters (alpha, n, theta_r, theta_s), water pressure |
| **output_data** | Water content (theta) or pressure (inverse) |
| **uncertainty** | UNKNOWN |
| **calibration** | Parameters from literature or lab measurement |
| **validation** | Unit tests against known soil parameter sets; matches published equations |
| **known_limitations** | No hysteresis; no temperature effects; assumes smooth curve |
| **failure_modes** | psi = 0 → division issues; n = 1 → m = 0 → singularity |
| **dependencies** | Newton-Raphson root finder |
| **source_code** | engine/hydroma/soil/physics.py:45-167 |
| **tests** | tests/test_soil_physics.py (8 test cases) |
| **scientific_references** | van Genuchten, M.T. (1980). "A closed-form equation for predicting the hydraulic conductivity of unsaturated soils". Soil Sci. Soc. Am. J. 44(5): 892-898 |
| **provenance** | DIRECT |
| **current_status** | IMPLEMENTATION_VERIFIED |
| **recommended_future_status** | SCIENTIFICALLY_SUPPORTED |

### SCIENTIFIC-MODEL-009: Soil Salinity

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-009 |
| **model_name** | Soil Salinity Model |
| **domain** | Soil Science / Agriculture |
| **purpose** | Estimate soil salinity effects on crop yield and plant growth |
| **scientific_basis** | UNSPECIFIED - possibly empirical relationships |
| **equations** | UNKNOWN |
| **variables** | EC (electrical conductivity), SAR (sodium adsorption ratio), pH |
| **parameters** | UNKNOWN |
| **coefficients** | UNKNOWN |
| **thresholds** | UNKNOWN |
| **units** | EC: dS/m, SAR: (mmol/L)^0.5 |
| **assumptions** | UNKNOWN |
| **constraints** | UNKNOWN |
| **boundary_conditions** | UNKNOWN |
| **initial_conditions** | UNKNOWN |
| **algorithm** | UNKNOWN - implementation does not clearly specify scientific basis |
| **numerical_method** | UNKNOWN |
| **input_data** | Soil salinity measurements |
| **output_data** | Salinity impact assessment |
| **uncertainty** | UNKNOWN |
| **calibration** | None documented |
| **validation** | No validation references found |
| **known_limitations** | Equations not documented; scientific basis unclear |
| **failure_modes** | UNKNOWN |
| **dependencies** | UNKNOWN |
| **source_code** | engine/hydroma/soil/salinity.py:12-98 |
| **tests** | tests/test_soil_salinity.py (2 test cases) |
| **scientific_references** | UNKNOWN |
| **provenance** | UNKNOWN |
| **current_status** | CODE_ONLY |
| **recommended_future_status** | REQUIRES_SCIENTIFIC_REVIEW |

### SCIENTIFIC-MODEL-010: Slope/Aspect (Verified)

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-010 |
| **model_name** | Slope and Aspect Calculation |
| **domain** | GIS / Terrain Analysis |
| **purpose** | Compute slope gradient and aspect from DEM data |
| **scientific_basis** | Standard GIS terrain analysis using Horn's algorithm (1981) |
| **equations** | see Equation Forensic EQN-SLOPE-001 |
| **variables** | slope (degrees or %), aspect (degrees from N), elevation (z) |
| **parameters** | Cell size (spatial resolution) |
| **coefficients** | 180 / pi (radians to degrees) |
| **thresholds** | None |
| **units** | Elevation: meters, Slope: degrees or %, Aspect: degrees 0-360 |
| **assumptions** | Planar approximation within each grid cell; 3x3 moving window |
| **constraints** | DEM must be regular grid |
| **boundary_conditions** | Edge cells require padding or boundary handling |
| **initial_conditions** | None |
| **algorithm** | Horn's finite difference method: compute dz/dx, dz/dy → slope = arctan(sqrt((dz/dx)² + (dz/dy)²)), aspect = arctan2(dz/dy, dz/dx) |
| **numerical_method** | Finite difference |
| **input_data** | DEM (2D elevation array), cell size |
| **output_data** | Slope raster, aspect raster |
| **uncertainty** | UNKNOWN |
| **calibration** | None |
| **validation** | Implementation-verified against known datasets; matches Horn's method |
| **known_limitations** | Planar approximation; no curvature; edge effects |
| **failure_modes** | Flat areas → aspect undefined; noise in DEM → noisy slope |
| **dependencies** | DEM processing |
| **source_code** | engine/land/models.py:45-112; engine/land/terrain_analysis.py:15-178 |
| **tests** | tests/test_terrain_analysis.py (7 test cases) |
| **scientific_references** | Horn, J.E. (1981). "Hill Shading and the Viewshed Problem". Tech. Rep. USGS |
| **provenure** | DIRECT |
| **current_status** | IMPLEMENTATION_VERIFIED |
| **recommended_future_status** | SCIENTIFICALLY_SUPPORTED |

### SCIENTIFIC-MODEL-011: Terrain Analysis (Verified)

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-011 |
| **model_name** | Terrain Analysis Suite |
| **domain** | GIS / Geomorphology |
| **purpose** | Extract terrain attributes from DEM: slope, aspect, hillshade, curvature, wetness index |
| **scientific_basis** | Standard geomorphometric methods |
| **equations** | see Equation Forensic EQN-TERRAIN-* |
| **variables** | slope, aspect, hillshade, plan_curvature, profile_curvature, TWI |
| **parameters** | z_factor, output units |
| **coefficients** | Various (pi factors, trigonometric) |
| **thresholds** | None |
| **units** | Slope: degrees; Aspect: degrees 0-360; Hillshade: 0-255 |
| **assumptions** | Regular grid DEM; local operators |
| **constraints** | DEM quality affects all outputs |
| **boundary_conditions** | Edge cell handling via padding |
| **initial_conditions** | None |
| **algorithm** | 1. Compute gradient (Horn's method) 2. Derive terrain attributes 3. Apply to full DEM |
| **numerical_method** | Finite difference, convolution |
| **input_data** | DEM raster |
| **output_data** | Terrain attribute rasters |
| **uncertainty** | UNKNOWN |
| **calibration** | None |
| **validation** | Unit tests validate against known terrain features; matches standard GIS behavior |
| **known_limitations** | Local operators only; no multi-scale analysis; DEM quality dependent |
| **failure_modes** | Noisy DEM → artifacts; boundary effects |
| **dependencies** | DEM processing, slope/aspect calculation |
| **source_code** | engine/land/terrain_analysis.py:15-178, engine/land/models.py:45-112 |
| **tests** | tests/test_terrain_analysis.py (12 test cases) |
| **scientific_references** | Wilson (2011). "Environmental Analysis and Geomorphology"; Hengl (2009) |
| **provenance** | DIRECT |
| **current_status** | IMPLEMENTATION_VERIFIED |
| **recommended_future_status** | SCIENTIFICALLY_SUPPORTED |

### SCIENTIFIC-MODEL-012: Soil Carbon

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-012 |
| **model_name** | Soil Carbon Storage Estimation |
| **domain** | Soil Science / Carbon Cycle |
| **purpose** | Estimate soil organic carbon storage |
| **scientific_basis** | UNKNOWN - empirical or simplified |
| **equations** | UNKNOWN |
| **variables** | Carbon stock, bulk density, soil depth, SOC concentration |
| **parameters** | Bulk density, SOC%, depth |
| **coefficients** | 10 (depth conversion), 0.587 (C to SOC conversion) |
| **thresholds** | None documented |
| **units** | Carbon stock: Mg C/ha; bulk density: g/cm³; SOC%: percent |
| **assumptions** | Layered soil with constant bulk density per layer |
| **constraints** | Requires SOC data |
| **boundary_conditions** | Fixed soil depth assumption |
| **initial_conditions** | None |
| **algorithm** | Carbon stock = SOC% * bulk_density * depth * conversion_factor |
| **numerical_method** | Simple multiplication |
| **input_data** | SOC%, bulk density, depth |
| **output_data** | Carbon stock (Mg C/ha) |
| **uncertainty** | UNKNOWN |
| **calibration** | None |
| **validation** | Unit tests verify numerical computation, not scientific accuracy |
| **known_limitations** | Linear approximation; no temporal dynamics; no C transformations |
| **failure_modes** | Incorrect bulk density → wrong stock; missing layers → undercount |
| **dependencies** | Soil data, depth profiles |
| **source_code** | engine/hydroma/soil/carbon.py:56-134 |
| **tests** | tests/test_soil_carbon.py (4 test cases) |
| **scientific_references** | UNKNOWN |
| **provenance** | IMPLEMENTATION |
| **current_status** | IMPLEMENTATION_VERIFIED |
| **recommended_future_status** | REQUIRES_SCIENTIFIC_REVIEW |

### SCIENTIFIC-MODEL-013: RUSLE Soil Erosion

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-013 |
| **model_name** | Revised Universal Soil Loss Equation (RUSLE) |
| **domain** | Soil Science / Hydrology |
| **purpose** | Estimate long-term average annual soil loss from sheet and rill erosion |
| **scientific_basis** | RUSLE (Renard et al. 1997). USDA standard model |
| **equations** | see Equation Forensic EQN-RUSLE-001 |
| **variables** | A (soil loss), R (rainfall erosivity), K (soil erodibility), LS (topographic), C (cover), P (support practices) |
| **parameters** | R, K, LS, C, P factors |
| **coefficients** | 1.0 (combined multiplicatively) |
| **thresholds** | None |
| **units** | A: tons/ha/year or t/ha/yr |
| **assumptions** | Steady-state conditions; annual average; uniform conditions over watershed |
| **constraints** | All factors must be non-negative |
| **boundary_conditions** | Annual time step |
| **initial_conditions** | None |
| **algorithm** | A = R * K * LS * C * P |
| **numerical_method** | Multiplication |
| **input_data** | R factor, K factor, LS factor, C factor, P factor |
| **output_data** | Annual soil loss (tons/ha/year) |
| **uncertainty** | Well-documented in RUSLE literature (±20-40% typical) |
| **calibration** | C and P factors calibrated for local conditions |
| **validation** | Unit tests validate multiplication; model is USDA standard |
| **known_limitations** | Does not predict timing/depth; no gully/transition forms; annual average only |
| **failure_modes** | High R + low K → unrealistic; LS factor errors → large errors |
| **dependencies** | LS calculation (slope/length) |
| **source_code** | engine/hydroma/soil/erosion.py:5-112 |
| **tests** | tests/test_soil_erosion.py (5 test cases) |
| **scientific_references** | Renard, K.G. et al. (1997). "Predicting Soil Erosion by Water". USDA Agriculture Handbook No. 703 |
| **provenance** | DIRECT |
| **current_status** | SCIENTIFICALLY_SUPPORTED |
| **recommended_future_status** | SCIENTIFICALLY_SUPPORTED |

### SCIENTIFIC-MODEL-014: Water Demand

| Field | Value |
|-------|-------|
| **model_id** | SCIENTIFIC-MODEL-014 |
| **model_name** | Water Demand Estimation |
| **domain** | Irrigation / Agriculture |
| **purpose** | Estimate crop water requirement and irrigation demand |
| **scientific_basis** | FAO-56 methodology; combines ET0 with crop coefficients |
| **equations** | see Equation Forensic EQN-WD-001 |
| **variables** | ETc (crop ET), ET0, Kc (crop coefficient), crop coefficient curve |
| **parameters** | Kc values by growth stage, crop type |
| **coefficients** | None (factors per FAO-56) |
| **thresholds** | Kc >= 0 |
| **units** | ETc: mm/day, ET0: mm/day |
| **assumptions** | Standard crop coefficient approach; uniform crop |
| **constraints** | Requires ET0 and crop coefficient curves |
| **boundary_conditions** | Growth stage lookup |
| **initial_conditions** | None |
| **algorithm** | ETc = Kc * ET0; demand = ETc - precipitation - existing moisture |
| **numerical_method** | Multiplication |
| **input_data** | ET0, crop type, growth stage, precipitation |
| **output_data** | Crop water requirement (ETc), irrigation requirement |
| **uncertainty** | UNKNOWN |
| **calibration** | Kc curves from FAO-56 or local calibration |
| **validation** | Implementation-verified; matches FAO-56 approach |
| **known_limitations** | Does not account for water stress effects on Kc; simplified |
| **failure_modes** | Wrong Kc → wrong demand; missing ET0 → failure |
| **dependencies** | ET0 model, crop coefficient lookup |
| **source_code** | engine/hydroma/models/water_demand.py:10-156 |
| **tests** | tests/test_water_demand.py (6 test cases) |
| **scientific_references** | Allen, R.G. et al. (1998) FAO-56; FAO Irrigation and Drainage Paper 56 |
| **provenance** | DIRECT |
| **current_status** | IMPLEMENTATION_VERIFIED |
| **recommended_future_status** | SCIENTIFICALLY_SUPPORTED |

---

## 2. Remaining Models (Compact Format)

### SCIENTIFIC-MODEL-015: EPIA (Precision Irrigation Advisor)
- **Status:** COMPOSITE - aggregates ET0, water demand, crop coefficients
- **Location:** engine/hydroma/models/epia.py
- **Scientific Basis:** FAO-56 based irrigation scheduling

### SCIENTIFIC-MODEL-016: Phenology Detection (hpheno)
- **Status:** COMPOSITE - uses temperature accumulation models
- **Location:** engine/hydroma/models/hpheno.py
- **Scientific Basis:** Growing Degree Days / thermal time

### SCIENTIFIC-MODEL-017: Carbon Flux
- **Status:** UNKNOWN - insufficient documentation
- **Location:** engine/hydroma/carbon/flux.py

### SCIENTIFIC-MODEL-018: Crop Coefficient
- **Status:** IMPLEMENTATION_VERIFIED
- **Location:** engine/hydroma/agriculture/crop_coefficient.py

### SCIENTIFIC-MODEL-019: Growth Stage Classification
- **Status:** SCIENTIFICALLY_SUPPORTED
- **Location:** engine/hydroma/agriculture/growth_stage.py

### SCIENTIFIC-MODEL-020: Sorption Isotherm
- **Status:** CODE_ONLY
- **Location:** engine/hydroma/soil/sorption.py

### SCIENTIFIC-MODEL-021: Surface Water Routing
- **Status:** CODE_ONLY - needs review
- **Location:** engine/hydroma/models/surface_water_model.py

### SCIENTIFIC-MODEL-022: Watershed Structure Calculator
- **Status:** IMPLEMENTATION_VERIFIED
- **Location:** engine/hydroma/watershed/calculator.py

---

## 3. Scientific Status Summary

| Status | Count | Models |
|--------|-------|--------|
| SCIENTIFICALLY_VALIDATED | 0 | None - no field/calibration data found |
| SCIENTIFICALLY_SUPPORTED | 6 | PM-ET0, Hargreaves, SCS-CN, Darcy, RUSLE, Growth Stage |
| IMPLEMENTATION_VERIFIED | 8 | Radiation, Van Genuchten, Watershed, Water Demand, Slope/Aspect, Terrain, Carbon, Crop Coefficient |
| CODE_ONLY | 4 | Climate Assimilation, Soil Salinity, Surface Water, Sorption Isotherm |
| REQUIRES_SCIENTIFIC_REVIEW | 2 | Theis (series convergence), Climate Data Assimilation |
| UNKNOWN | 2 | Carbon Flux, Soil Fractionation |

---

*See also: 07-MODEL-QUALITY-MATRIX.md, 08-EQUATION-AND-UNIT-FORENSICS.md, 23-SCIENTIFIC-REVIEW-QUEUE.md*