# Gap Analysis Report: Eco Nojin Phase 1 & 2
**Audit Date:** 2026-09-08  
**Working Directory:** D:\eco_nojin  
**Auditor:** Kilo  

---

## Executive Summary

The Eco Nojin platform has a **solid scientific foundation** with genuine model implementations (AquaCrop-OSPy, pyRothC, Muskingum-Cunge, RUSLE, pySWATPlus, pywr) and real data integrations (Open-Meteo ERA5, SoilGrids ISRIC). However, several **critical gaps** exist against global standards (FAO, ISO, IPCC, USDA) that must be addressed before production deployment.

| Phase | Component | Status | Critical Gaps |
|-------|-----------|--------|---------------|
| 1 | Soil Simulation | 70% | Missing SOC modeling (RothC in Phase 2), no groundwater, limited validation |
| 1 | Water Simulation | 65% | Simplified ET0, no full SWAT+, missing groundwater, limited Muskingum-Cunge |
| 1 | Crop Simulation | 75% | AquaCrop-OSPy integrated, but missing phenology, stress factors, validation |
| 1 | Database Layer | 80% | SQLite+DuckDB unified, but migrations incomplete, no query optimization |
| 2 | Biochar/Compost | 60% | Calculator exists, but material DB sparse, no formulation validation |
| 2 | Water Harvesting | 50% | Basic structures only, missing detailed FAO/MAG design standards |

---

## Phase 1: Research & MVP

### 1.1 Soil Simulation

**Current Implementation:**
- `engine/hydroma/soil/physics.py` — van Genuchten (1980) / Mualem (1976) water retention and hydraulic conductivity
- `engine/hydroma/soil/pedotransfer.py` — Saxton & Rawls (2006) pedotransfer functions
- `engine/hydroma/soil/texture.py` — USDA 12-class texture triangle
- `engine/hydroma/soil/taxonomy.py` — USDA soil taxonomy (order-level only)
- `engine/hydroma/soil/chemistry.py` — CEC, ESP, SAR, pH buffering
- `engine/hydroma/soil/health.py` — weighted soil health index
- `engine/hydroma/soil/salinity.py` — EC classification, leaching requirement
- `engine/hydroma/cpp_bridge/soil_physics_fast.py` — Numba-accelerated VG models

**Strengths:**
- Correct implementation of van Genuchten-Mualem with Carsel & Parrish (1988) parameters for 12 textures
- Pedotransfer functions properly implemented
- C++ bridge with Numba JIT for performance

**Gaps Against Standards:**
1. **Missing RothC in Phase 1** — Soil organic carbon dynamics (RothC-26.3) is in Phase 2 (`services/scientific_motors/rothc.py`, `rothc_real.py`), not Phase 1. Phase 1 should have a standalone SOC model.
2. **No erosion modeling in Phase 1** — RUSLE is in Phase 2 (`services/scientific_motors/erosion_rusle.py`). Phase 1 should include basic erosion risk.
3. **No groundwater modeling** — Missing vadose zone / groundwater interaction (Richards equation is only in carbon_sequestration.py as a C++ bridge import that may not be functional).
4. **No validation dataset** — No reference to independent soil dataset validation (e.g., USGS, FAO soil maps).
5. **Limited soil taxonomy** — Only order-level classification; missing suborder, great group, family, series.
6. **No bulk density / pedotransfer consistency** — Saxton-Rawls gives theta_33/theta_1500 but not bulk density; conversion to t/ha SOC inconsistent.

### 1.2 Water Simulation

**Current Implementation:**
- `engine/hydroma/cpp_bridge/hydrology_fast.py` — Muskingum-Cunge flood routing (Cunge 1969, Chow 1988)
- `engine/hydroma/watershed/calculator.py` — Rational method runoff, Kirpich Tc, Strahler ordering, Horton ratios
- `services/scientific_motors/irrigation_scheduler.py` — FAO-56 ETc = ET0 × Kc with crop coefficient tables
- `services/scientific_motors/swat_plus.py` — Simplified SWAT+ water balance (SCS-CN, Hargreaves ET)
- `services/scientific_motors/pywr_real.py` — Pywr water allocation network

**Strengths:**
- Industry-standard Muskingum-Cunge with Numba acceleration
- FAO-56 Kc tables for 15+ crops
- Real Pywr network simulation
- HEC-RAS automation hook with honest Manning fallback

**Gaps Against Standards:**
1. **Simplified ET0** — Uses Hargreaves (temp-only) instead of full FAO-56 Penman-Monteith (`services/scientific_motors/aquacrop_real.py:_calculate_et0`). Missing solar radiation, humidity, wind speed.
2. **No groundwater module** — Missing MODFLOW-style or simplified groundwater bucket model.
3. **SWAT+ is simplified** — `swat_plus.py` is a toy model; `swat_real.py` only prepares projects but requires external SWAT+ executable.
4. **No vadose zone / infiltration** — Missing Green-Ampt, Philip, or Richards equation infiltration models (only referenced in carbon_sequestration.py).
5. **Runoff coefficient is empirical** — Rational method in `watershed/calculator.py` uses fixed coefficient (0.5) without land-use/soil-specific calibration.
6. **Missing dam/reservoir operations** — No reservoir release rules, no operational optimization.

### 1.3 Crop Simulation

**Current Implementation:**
- `services/scientific_motors/aquacrop.py` — Simplified daily water balance with Kc curve, biomass = WP × T, HI conversion
- `services/scientific_motors/aquacrop_real.py` — Full AquaCrop-OSPy 3.x wrapper with real weather data
- `services/scientific_motors/aquacrop_real_motor.py` — Async worker-thread execution
- `services/scientific_motors/aquacrop_adapter.py` — SQLAlchemy integration adapter
- `services/scientific_motors/crop_database.py` — 30 curated CropProfiles + DuckDB 5000 species
- `services/scientific_motors/crop_advisor.py` — Köppen-climate crop matching with rotation plans

**Strengths:**
- Real AquaCrop-OSPy integration (not a stub)
- Extensive crop database with Köppen climate, water, soil, temperature requirements
- Rotation planning with biofertilizer suggestions
- Worker-thread execution for CPU-heavy models

**Gaps Against Standards:**
1. **Missing phenology modules** — No GDD-based growth stage transitions (emergence, tillering, flowering, maturity) beyond simple day-proportions.
2. **No stress factors** — Missing temperature stress (high/low), salinity stress, nutrient stress (N/P/K). Only water stress is modeled.
3. **No pest/disease module** — IPM database exists in DuckDB but not integrated into crop simulation.
4. **Limited validation** — No KGE/NSE calibration against observed yield datasets (FAO, national stats).
5. **AquaCrop-OSPy version lock** — Only supports AquaCrop 3.x; no fallback if package missing (honest failure is good, but no simplified alternative path).
6. **CO2 fertilization missing** — AquaCrop-OSPy has CO2 response but not exposed in Eco Nojin wrapper.

### 1.4 Database Layer

**Current Implementation:**
- `database/hub/hub.py` — Unified DataHub (Singleton) for SQLAlchemy, DuckDB, SQLite, Redis
- `database/models.py` — SQLAlchemy models (User, LandProfile, SimulationRun, etc.)
- `services/scientific_motors/data_repository.py` — DuckDB repository with 25 methods
- `alembic/` — Migration system configured

**Strengths:**
- Multi-backend unified access (SQLite + DuckDB)
- LRU caching on repository methods
- Proper session management with async support

**Gaps Against Standards:**
1. **Migrations not tracked** — `alembic/versions/` not inspected; no evidence of active migration version control.
2. **DuckDB connection pooling missing** — Each `get_duckdb()` call creates a new connection; no persistent connection pool.
3. **No query performance monitoring** — Missing EXPLAIN plans, index usage stats, slow query logs.
4. **Database schema fragmentation** — Biofertilizer models in `engine/hydroma/biofertilizer/models.py` are separate from `database/models.py`; no unified metadata.
5. **Missing indexes** — No evidence of composite indexes for common query patterns (e.g., site_id + date ranges).
6. **No backup/restore automation** — DuckDB file-based but no automated backup strategy.

---

## Phase 2: Ecosystem & Materials

### 2.1 Biochar / Compost

**Current Implementation:**
- `engine/hydroma/biofertilizer/calculator.py` — NojinCalculator (multi-strain synergy, dosage, timing)
- `engine/hydroma/biofertilizer/advanced_calculator.py` — FormulationOptimizer, CostBenefitCalculator, WaterSavingsCalculator, ScaleCalculator
- `engine/hydroma/biofertilizer/models.py` — 12 SQLAlchemy models (strains, formulations, recipes, materials, cost-benefit)
- `engine/hydroma/biofertilizer/services.py` — NojinService with cross-phase integration
- `services/scientific_motors/biofertilizer.py` — BiofertilizerMotor (NPK deficit, recommendations)
- `engine/hydroma/materials/compost_formulator.py` — C/N ratio calculator
- `services/api_gateway/routers/materials.py` — API endpoint for compost calculation

**Strengths:**
- Comprehensive NojinCalculator with strain synergy, seasonal dynamics, persistence modeling
- Advanced economic analysis (NPV, IRR, BCR, payback)
- Water savings and scale calculators
- 12-table database schema for full lifecycle management

**Gaps Against Standards:**
1. **Material database is skeletal** — `NojinMaterial` has 30+ columns but `seed_data.py` / `materials_data.py` not audited for actual populated values.
2. **No C/N ratio optimization** — `compost_formulator.py` only calculates C/N ratio; no optimization to reach target 25-35:1.
3. **Missing nutrient content standards** — No alignment with global compost standards (e.g., EN 13432, ISO 14040 LCA).
4. **No formulation stability testing** — Missing shelf-life, temperature, moisture stability models.
5. **No regulatory compliance** — Missing organic certification standards (IFOAM, USDA NOP, EU Organic).
6. **Biochar not modeled separately** — No distinction between biochar types (pyrolysis temperature, feedstock, pH, surface area).

### 2.2 Water Harvesting Structures

**Current Implementation:**
- `engine/hydroma/watershed/calculator.py` — Check dams, contour trenches, half-moons; Strahler ordering, Horton ratios, Kirpich Tc, Muskingum routing
- `engine/hydroma/watershed/watershed_calculator.py` — Alternative check dam design (duplicate?)
- `services/api_gateway/routers/watershed.py` — REST API for structure design

**Strengths:**
- Multiple structure types (check dam, contour trench, half-moon, terrace, gully plug)
- Standard hydrological calculations (Kirpich, Muskingum, Strahler)
- API exposure

**Gaps Against Standards:**
1. **Simplistic sizing** — Check dam height = `min(3.0, max(0.5, slope_pct / 10))` is empirical guess, not FAO/MAG engineering standard.
2. **No spillway design** — Missing crest length, freeboard, spillway capacity per FAO Watershed Management Field Manual.
3. **No sediment retention calculation** — Check dams should compute trap efficiency based on inflow, sediment concentration, settling velocity (Brune/Marengo methods).
4. **Missing cost estimation standards** — Cost = `dam_volume * 150` is a rough constant; no labor, equipment, or regional cost factors.
5. **No contour bund sizing** — Contour trenches use fixed 0.5m depth/width; FAO standards use catchment area, rainfall intensity, and soil infiltration.
6. **Missing GIS/Topography integration** — No DEM-based structure placement optimization.

---

## Cross-Cutting Gaps

### Test Coverage
- **Missing validation tests** — No tests compare model outputs against published FAO/AquaCrop/SWAT benchmarks.
- **Missing edge-case tests** — No tests for extreme inputs (zero rainfall, 100% slope, etc.).
- **Integration tests exist but are thin** — `tests/integration/test_simulation_api.py` exists but depth unknown.

### Documentation
- **No scientific reference documentation** — Models cite papers but no user-facing methodology docs.
- **Missing API docs** — FastAPI routers lack docstrings and schema descriptions.
- **No data dictionary** — DuckDB tables have no documented schema.

### Performance / Accuracy
- **No benchmark suite** — `testing_lab/benchmarks/test_perf.py` exists but not audited for scientific accuracy.
- **No uncertainty quantification** — Models return point estimates; no confidence intervals or Monte Carlo error propagation.
- **No sensitivity analysis** — No Sobol, Morris, or local sensitivity analysis for key parameters.

---

## Prioritized Action Items

### P0 (Blocking Production)
1. **Implement full FAO-56 Penman-Monteith ET0** — Replace Hargreaves with net radiation, humidity, wind speed inputs.
2. **Add groundwater module** — Simple bucket model with recharge/discharge for water balance closure.
3. **Validate AquaCrop outputs** — Run against FAO test datasets; publish KGE/NSE metrics.
4. **Unify database schema** — Merge biofertilizer models into `database/models.py` or document separation.
5. **Add migration version control** — Verify alembic versions are committed and deployable.

### P1 (High Value)
6. **Add phenology/GDD module** — Integrate with crop database for stage-specific Kc and stress.
7. **Implement RUSLE validation** — Compare against Global Soil Erosion Map (GLOSEM) benchmark.
8. **Add reservoir operations** — Rule curves, release rules, evaporation losses.
9. **Material DB population** — Populate `ref_fertilizers` and `nojin_materials` with 50+ real materials.
10. **FAO/MAG water harvesting standards** — Redesign check dam sizing with spillway, sediment trap efficiency.

### P2 (Medium Value)
11. **Quantum ML for soil carbon** — Research quantum kernel methods for RothC parameter calibration.
12. **NSGA-II full model-in-the-loop** — Replace surrogate with real AquaCrop/RothC calls (expensive but accurate).
13. **Uncertainty quantification** — Add Monte Carlo wrappers to all motors.
14. **LCA integration** — Align biofertilizer with ISO 14040/14044 life cycle assessment.
15. **Post-quantum cryptography** — Audit `services/security/pqcrypto.py` for data-at-rest security.

---

## Appendix: File Inventory by Component

### Phase 1 Files
- Soil: `engine/hydroma/soil/*.py` (8 modules), `engine/hydroma/cpp_bridge/soil_physics_*.py`
- Water: `engine/hydroma/cpp_bridge/hydrology_*.py`, `engine/hydroma/watershed/*.py`, `services/scientific_motors/irrigation_scheduler.py`, `swat_plus.py`, `pywr_real.py`
- Crop: `services/scientific_motors/aquacrop*.py` (4 files), `crop_database.py`, `crop_advisor.py`
- DB: `database/hub/hub.py`, `database/models.py`, `services/scientific_motors/data_repository.py`, `alembic/`

### Phase 2 Files
- Biofertilizer: `engine/hydroma/biofertilizer/*.py` (6 modules), `services/scientific_motors/biofertilizer.py`, `carbon_sequestration.py`
- Water Harvesting: `engine/hydroma/watershed/calculator.py`, `services/api_gateway/routers/watershed.py`
- Materials: `engine/hydroma/materials/compost_formulator.py`, `services/api_gateway/routers/materials.py`
