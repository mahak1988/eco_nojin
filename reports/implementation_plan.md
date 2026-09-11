# Implementation Plan: Phase 1 & 2 Completion
**Date:** 2026-09-08  
**Working Directory:** D:\eco_nojin  

---

## Overview

This plan translates the Gap Analysis into concrete, actionable steps. Work is organized into **4 sprints** (2 weeks each), prioritized by scientific correctness and production readiness.

---

## Sprint 1: Foundation & Standards Compliance (Weeks 1-2)

### S1.1: Complete FAO-56 Penman-Monteith ET0
**Priority:** P0  
**Files to modify:**
- `services/scientific_motors/irrigation_scheduler.py` — Replace Hargreaves with full PM
- `services/scientific_motors/aquacrop_real.py` — Add PM ET0 calculation
- `services/satellite/open_meteo.py` — Fetch solar radiation, humidity, wind speed

**Steps:**
1. Add `net_radiation_mjm2`, `rh_mean_pct`, `wind_speed_10m_ms` to ERA5 fetch
2. Implement FAO-56 PM equation:
   ```
   ET0 = (0.408 * Δ * (Rn - G) + γ * (900 / (T + 273)) * u2 * (es - ea)) / (Δ + γ * (1 + 0.34 * u2))
   ```
3. Add psychrometric constant (γ) and slope of vapor pressure curve (Δ) calculations
4. Validate against FAO-56 test datasets (Penman-Monteith reference values)
5. Update all motors that use ET0 to accept the new inputs

### S1.2: Unify Database Schema
**Priority:** P0  
**Files to modify:**
- `database/models.py` — Merge biofertilizer models or document separation
- `engine/hydroma/biofertilizer/models.py` — Add `__table_args__` consistency
- `alembic/versions/` — Create initial migration if missing

**Steps:**
1. Audit all SQLAlchemy models across the project
2. Create unified `database/models/` package with submodules
3. Generate alembic migration: `alembic revision --autogenerate -m "unify_schema"`
4. Add composite indexes for common queries:
   - `simulationrun(site_id, executed_at)`
   - `ref_species(id, category)`
   - `nojin_application_plans(land_profile_id, application_date)`

### S1.3: Post-Quantum Cryptography Audit & Migration
**Priority:** P0  
**Files to modify:**
- `services/security/pqcrypto.py` — Audit and upgrade
- `services/api_gateway/main.py` — Add hybrid TLS configuration
- `services/business_modules/blockchain/carbon_registry.py` — Add Dilithium signatures

**Steps:**
1. Read current `pqcrypto.py` implementation
2. Replace any custom PQC with liboqs or cryptography.io NIST-approved algorithms
3. Implement CRYSTALS-Kyber for key encapsulation
4. Implement CRYSTALS-Dilithium for digital signatures
5. Add hybrid mode (classical + PQC) for backward compatibility
6. Test key generation, encapsulation, and signing/verification

---

## Sprint 2: Scientific Model Improvements (Weeks 3-4)

### S2.1: Groundwater Module
**Priority:** P1  
**Files to create:**
- `engine/hydroma/groundwater.py` — Simple groundwater bucket model

**Model:**
```
GW_storage(t+1) = GW_storage(t) + Recharge(t) - Baseflow(t) - Pumping(t)
Baseflow(t) = GW_storage(t) * alpha  (alpha = 0.02-0.05 per month)
Recharge(t) = SoilWater(t) * Rcoeff
```

**Steps:**
1. Implement groundwater balance with linear reservoir approximation
2. Connect to SWAT+ water balance (`swat_plus.py`)
3. Connect to Pywr (`pywr_real.py`) as groundwater node
4. Validate against simple test case (steady-state recharge = baseflow)

### S2.2: Phenology / GDD Module
**Priority:** P1  
**Files to create:**
- `engine/hromma/crop/phenology.py` — GDD-based growth stage model

**Model:**
```
GDD = max(0, (Tmax + Tmin)/2 - Tbase)
Stage transitions:
  Emergence: GDD > GDD_emergence
  Tillering: GDD > GDD_tillering
  Flowering: GDD > GDD_flowering
  Maturity: GDD > GDD_maturity
```

**Steps:**
1. Add GDD accumulation to `crop_database.py` (per crop)
2. Update `aquacrop_real.py` to use GDD stages instead of fixed day proportions
3. Update `irrigation_scheduler.py` Kc tables to be stage-specific
4. Validate against FAO crop calendar data

### S2.3: RUSLE Validation Against Global Benchmark
**Priority:** P1  
**Files to modify:**
- `services/scientific_motors/erosion_rusle.py` — Add validation mode

**Steps:**
1. Fetch GLOSEM (Global Soil Erosion Map) benchmark data for test sites
2. Implement `validate_rusle()` function comparing model output vs GLOSEM
3. Calibrate the 0.10 global calibration factor by climate zone
4. Add R, K, LS, C, P factor uncertainty ranges
5. Document validation results in `reports/rusle_validation.md`

---

## Sprint 3: Phase 2 Materialization (Weeks 5-6)

### S3.1: Populate Material Database
**Priority:** P1  
**Files to modify:**
- `engine/hydroma/biofertilizer/data/materials_data.py` — Populate 50+ materials
- `engine/hydroma/biofertilizer/data/seed_data.py` — Add seed data

**Materials to add:**
- Biochars (woodchip, rice husk, manure) — pH, C%, surface area, persistence
- Composts (FYM, vermicompost, green waste) — C/N, NPK, OM%
- Minerals (zeolite, gypsum, bentonite, vermiculite) — CEC, density, cost
- Cover crop seeds (legume, grass mixes) — N fixation, biomass

**Steps:**
1. Research and document 50 materials with real scientific parameters
2. Add to `seed_data.py` with units, sources, and references
3. Validate C/N ratios, nutrient contents against literature
4. Add application rates and cost data from regional suppliers

### S3.2: FAO/MAG Water Harvesting Standards
**Priority:** P1  
**Files to modify:**
- `engine/hydroma/watershed/calculator.py` — Redesign with standards

**FAO Standards to implement:**
1. **Check Dam Sizing:**
   - Height: `H = 0.5 * Qp^0.4 * (S^0.3)` (empirical from FAO)
   - Spillway width: `W = Qp / (Cd * H^1.5)`
   - Freeboard: 0.3-0.5m
   - Sediment trap efficiency: Brune method

2. **Contour Bund:**
   - Spacing: `S = (H / slope%) * 100` where H = height (0.3-0.5m)
   - Cross-section: trapezoidal with 1.5:1 side slopes

3. **Half-Moon:**
   - Radius: 3-5m (FAO standard for tree planting)
   - Depth: 0.3-0.5m
   - Spacing: 4m between centers

**Steps:**
1. Replace empirical sizing with FAO formulas
2. Add sediment retention calculation
3. Add cost estimation with labor, equipment, regional factors
4. Validate against FAO case study data

---

## Sprint 4: Validation, Testing & Documentation (Weeks 7-8)

### S4.1: Scientific Validation Suite
**Priority:** P1  
**Files to create:**
- `testing_lab/scientific_tests/test_fao_validation.py`
- `testing_lab/scientific_tests/test_benchmark_datasets.py`

**Validation Tasks:**
1. **ET0 Validation:** Compare PM output against FAO-56 test reference (R-value, grass)
2. **AquaCrop Validation:** Run against FAO AquaCrop test datasets (wheat, maize)
3. **RothC Validation:** Compare against Rothamsted long-term experiment data
4. **RUSLE Validation:** Compare against GLOSEM and national erosion datasets
5. **Irrigation Scheduler Validation:** Compare against FAO-56 crop water requirement tables

**Steps:**
1. Download reference datasets (FAO, USDA, ISRIC)
2. Implement validation tests with tolerance thresholds:
   - ET0: RMSE < 0.5 mm/day
   - AquaCrop yield: NSE > 0.6
   - RothC SOC: NSE > 0.5
   - RUSLE: within 2x observed
3. Generate calibration reports

### S4.2: Uncertainty Quantification
**Priority:** P2  
**Files to create:**
- `services/scientific_motors/uncertainty.py` — Monte Carlo wrapper

**Steps:**
1. Implement Monte Carlo sampling for key parameters (Kc, RothC rates, RUSLE C-factor)
2. Add confidence intervals to all MotorOutput results
3. Implement Latin Hypercube Sampling for efficient uncertainty propagation
4. Add sensitivity analysis (Sobol indices) for top parameters

### S4.3: Documentation
**Priority:** P2  
**Files to create:**
- `docs/models/et0.md` — FAO-56 Penman-Monteith methodology
- `docs/models/rothc.md` — RothC-26.3 implementation notes
- `docs/models/aquacrop.md` — AquaCrop-OSPy integration guide
- `docs/models/rusle.md` — RUSLE factor computation
- `docs/database/schema.md` — Unified schema documentation

---

## Code Changes Summary

### New Files to Create
| File | Purpose |
|------|---------|
| `engine/hydroma/groundwater.py` | Groundwater balance module |
| `engine/hydroma/crop/phenology.py` | GDD-based phenology |
| `testing_lab/scientific_tests/test_fao_validation.py` | FAO benchmark tests |
| `services/scientific_motors/uncertainty.py` | Monte Carlo wrapper |
| `docs/models/*.md` | Scientific documentation |

### Files to Modify
| File | Changes |
|------|---------|
| `services/scientific_motors/irrigation_scheduler.py` | PM ET0, GDD stages |
| `services/scientific_motors/aquacrop_real.py` | PM ET0, phenology |
| `services/scientific_motors/swat_plus.py` | Connect groundwater |
| `database/models.py` | Unify schema |
| `engine/hydroma/watershed/calculator.py` | FAO/MAG standards |
| `engine/hydroma/biofertilizer/data/seed_data.py` | Populate materials |
| `services/security/pqcrypto.py` | NIST PQC migration |

### Test Files to Create
| File | Purpose |
|------|---------|
| `tests/unit/test_penman_monteith.py` | ET0 unit tests |
| `tests/unit/test_groundwater.py` | Groundwater module tests |
| `tests/unit/test_phenology.py` | GDD phenology tests |
| `tests/benchmarks/test_scientific_accuracy.py` | Accuracy benchmarks |

---

## Verification Criteria

### Phase 1 Complete When:
- [ ] ET0 RMSE < 0.5 mm/day against FAO-56 reference
- [ ] AquaCrop NSE > 0.6 on FAO benchmark dataset
- [ ] RothC validated against Rothamsted data
- [ ] Database migrations run cleanly on fresh SQLite + DuckDB
- [ ] All motors return results within 2x expected values on test cases

### Phase 2 Complete When:
- [ ] 50+ materials in database with validated nutrient content
- [ ] Check dam sizing matches FAO design examples (±10%)
- [ ] C/N ratio optimization produces 25-35:1 target
- [ ] Cost-benefit calculator NPV matches Excel benchmark within 5%
- [ ] Water savings calculator validated against FAO-56 soil water balance

### Security Complete When:
- [ ] PQC key generation < 100ms
- [ ] Kyber encapsulation/decapsulation < 50ms
- [ ] Dilithium sign/verify < 20ms
- [ ] All new code passes `ruff check` and `mypy --strict`

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| External model packages unavailable (pyRothC, aquacrop) | Maintain simplified fallback implementations (already done for most) |
| ERA5/SoilGrids API downtime | Cache recent fetches, add retry logic, local fallback datasets |
| Quantum hardware access costs | Use classical benchmarks first; quantum only for pilot studies |
| PQC standardization changes | Implement hybrid mode (classical + PQC) during transition |
| Scientific accuracy disputes | Document all assumptions, provide calibration knobs, publish validation reports |

---

## Timeline

```
Week 1-2:  Sprint 1 (Foundation)
Week 3-4:  Sprint 2 (Scientific Models)
Week 5-6:  Sprint 3 (Phase 2 Materialization)
Week 7-8:  Sprint 4 (Validation & Docs)
Week 9:    Buffer / rework
Week 10:   Final integration test & deployment prep
```

**Target Completion:** 10 weeks from kickoff.
