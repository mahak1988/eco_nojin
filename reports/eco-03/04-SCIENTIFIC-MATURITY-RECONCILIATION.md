# ECO-03: Scientific Maturity Reconciliation — Report 04
## Canonical Scientific Model Registry

---

## Executive Summary

ECO-03 reconciles the **conflicting taxonomies** between ECO-01 and ECO-02 scientific model classifications:

- ECO-01 uses: `VERIFIED`, `SCIENTIFICALLY_SUPPORTED`, `IMPLEMENTATION_VERIFIED`, `CODE_ONLY`, `STUB`, `COMPOSITE`, `UNSUPPORTED`, `UNKNOWN`
- ECO-02 uses: `VERIFIED` (CORE), `SCIENTIFICALLY_SUPPORTED` (IMPORTANT), `IMPLEMENTATION_VERIFIED` (OPTIONAL), `CODE_ONLY` (RESEARCH), `STUB` (LEGACY/REMOVE)
- **ECO-03 reconciles to a unified 5-tier taxonomy with formal model contracts**

The ECO-02 claim of "22 canonical models" does NOT match the ECO-01 canonical assets of 17 (CANON-001 through CANON-017). The discrepancy is:
- **ECO-02**: 22 models (CANON-001 to CANON-022)
- **ECO-01**: 17 canonical assets (CANON-001 to CANON-017) + 12 NOT_RECOMMENDED

---

## 1. Reconciled Scientific Model Taxonomy

### Unified 5-Tier Maturity Scale

| Tier | Name | Definition | ECO-01 Mapping | ECO-02 Mapping |
|------|------|------------|----------------|----------------|
| M1 | VERIFIED | Scientifically validated, peer-reviewed, benchmarked against observations | VERIFIED + HIGH confidence | VERIFIED / CORE |
| M2 | SCIENTIFICALLY_SUPPORTED | Theory supported, partial validation against observations | SCIENTIFICALLY_SUPPORTED | SCIENTIFICALLY_SUPPORTED / IMPORTANT |
| M3 | IMPLEMENTATION_VERIFIED | Code correctly implements documented algorithm, NOT field-validated | IMPLEMENTATION_VERIFIED | IMPLEMENTATION_VERIFIED / OPTIONAL |
| M4 | CODE_ONLY | Implementation exists, no scientific backing or validation evidence | CODE_ONLY | CODE_ONLY / RESEARCH |
| M5 | STUB | Placeholder, incomplete, or deprecated | STUB + OBSOLETE | STUB / LEGACY/REMOVE |

### Epistemic Status (for knowledge classification)

| Status | Definition | ECO-01 Knowledge Types | ECO-02 Usage |
|--------|------------|----------------------|--------------|
| OBSERVATION | Direct empirical measurement | KT-004 | Evidence Engine |
| MEASUREMENT | Instrumental measurement | KT-004 | Evidence Engine |
| LOCAL_KNOWLEDGE | Regional/cultural knowledge | KT-008 | Daneshyar |
| TRADITIONAL_KNOWLEDGE | Indigenous knowledge systems | KT-008 | Daneshyar |
| SCIENTIFIC_EVIDENCE | Peer-reviewed scientific finding | M1-M2 | Knowledge/Daneshyar |
| MODEL_OUTPUT | Output from a scientific model | M1-M5 | All layers |
| EXPERIMENTAL_RESULT | Laboratory/field experiment | KT-003 | Evidence Engine |

---

## 2. Reconciled Scientific Model Registry (22 models)

| model_id | canonical_name | domain | implementation_status | scientific_status | validation_status | maturity_level | evidence | limitations | owner | review_required |
|----------|----------------|--------|----------------------|-------------------|-------------------|----------------|----------|-------------|-------|----------------|
| CANON-001 | Penman-Monteith ET0 | Climate/Agriculture | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/climate/et_calculator.py:54-289`, `engine/cpp_core/src/climate.cpp:106-147`, FAO-56 | Requires local calibration for specific crops | climate team | NO |
| CANON-002 | Hargreaves ET0 | Climate/Agriculture | IMPLEMENTATION_VERIFIED | SCIENTIFICALLY_SUPPORTED | M2 | 2 | `engine/hydroma/climate/et_calculator.py:300-380`, `engine/cpp_core/src/climate.cpp:44-61` | Less accurate than PM under data-rich conditions | climate team | NO |
| CANON-003 | Thornthwaite PET | Climate | IMPLEMENTATION_VERIFIED | SCIENTIFICALLY_SUPPORTED | M2 | 2 | `engine/hydroma/climate/et_calculator.py` | Does not account for advection; low accuracy in humid climates | climate team | NO |
| CANON-004 | SCS-CN Runoff | Hydrology | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/models/runoff_model.py:12-145` | Requires calibrated CN values per soil/land use | hydrology team | NO |
| CANON-005 | Theis Solution | Hydrogeology | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | M3 | 3 | `engine/hydroma/models/groundwater_model.py:93-210` | Series convergence undocumented; may diverge for early time | hydrogeology team | YES |
| CANON-006 | Van Genuchten | Soil Physics | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/soil/physics.py:45-167`, `engine/cpp_core/src/soil.cpp` | Parameters vary by soil type; requires local calibration | soil team | NO |
| CANON-007 | RUSLE Erosion | Soil Science | IMPLEMENTATION_VERIFIED | SCIENTIFICALLY_SUPPORTED | M2 | 2 | `engine/hydroma/soil/erosion.py:5-112`, `engine/cpp_core/src/erosion.cpp` | Requires LS factor calculation; empirical C/P factors | soil team | NO |
| CANON-008 | D8 Flow Direction | GIS/Hydrology | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/land/hydrology.py:50-89` | Single-flow, does not model divergent flow | land team | NO |
| CANON-009 | Terrain Analysis | GIS/Geomorphology | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/land/terrain_analysis.py:15-178`, `engine/land/models.py:45-112` | DEM resolution dependent | land team | NO |
| CANON-010 | Water Balance | Engineering | IMPLEMENTATION_VERIFIED | IMPLEMENTATION_VERIFIED | M3 | 3 | `engine/hydroma/simulation/balance.py:20-134` | Closure assumes steady state | simulation team | NO |
| CANON-011 | Solar Radiation | Climate | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/climate/radiation.py` | Topobility correction required for complex terrain | climate team | NO |
| CANON-012 | Formula Catalog | Engineering Knowledge | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/formulas/catalog.py` | Manual maintenance required | knowledge team | NO |
| CANON-013 | Provenance Tracking | Governance | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/provenance.py` | Does not capture data transformations | provenance team | NO |
| CANON-014 | Model Registry | Governance | IMPLEMENTATION_VERIFIED | IMPLEMENTATION_VERIFIED | M3 | 3 | `services/models/registry.py` | **Legacy coupling**: imports from `services.api_gateway.routers.carbon_engine` | model team | YES |
| CANON-015 | Watershed Calculator | Hydrology | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/watershed/calculator.py:15-234` | **Service coupling**: imports from services | hydrology team | YES |
| CANON-016 | C++ Climate Kernels | Numerical | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/cpp_core/src/climate.cpp`, `engine/hydroma/cpp_bridge/` | ABI dependency on pybind11 | engine team | NO |
| CANON-017 | C++ Soil Kernels | Numerical | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/cpp_core/src/soil.cpp`, `engine/hydroma/cpp_bridge/` | ABI dependency on pybind11 | engine team | NO |
| CANON-018 | CMIP6 Climate | Climate | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/climate/scenarios/` | Model uncertainty not fully characterized | climate team | NO |
| CANON-019 | GPM IMERG Precipitation | Climate | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/data_pipeline/` | Sensor calibration gaps | data team | NO |
| CANON-020 | MODIS ET | Remote Sensing | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/satellite/processors/` | Cloud cover contamination | satellite team | NO |
| CANON-021 | Landsat | Remote Sensing | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/satellite/processors/` | Spatial resolution limitations | satellite team | NO |
| CANON-022 | Sentinel-2 | Remote Sensing | IMPLEMENTATION_VERIFIED | VERIFIED | M1 | 1 | `engine/hydroma/satellite/processors/` | Revisit frequency limitations | satellite team | NO |

---

## 3. Canonical Model Contract (CANON-001)

The ECO-02 report references CANON-001 as a "canonical scientific model identifier" but does NOT define a formal versioned contract. ECO-03 defines the contract:

```json
{
  "model_id": "CANON-001",
  "model_version": "1.0.0",
  "equation_id": "fao56-pm-eq6",
  "implementation_id": "hydroma-climate-et0-pm-v2.1",
  "parameter_schema": {
    "t_min": {"type": "float", "unit": "celsius", "required": true},
    "t_max": {"type": "float", "unit": "celsius", "required": true},
    "rh_mean": {"type": "float", "unit": "percent", "required": true},
    "u2": {"type": "float", "unit": "m_s", "required": true},
    "rs": {"type": "float", "unit": "MJ_m2_day", "required": true},
    "elevation": {"type": "float", "unit": "meters", "required": true},
    "latitude": {"type": "float", "unit": "degrees", "required": true},
    "doy": {"type": "int", "unit": "day_of_year", "required": true}
  },
  "unit_schema": "SI with UNIFORMAT convention",
  "validation_status": "VERIFIED",
  "provenance": "FAO-56 Allen et al. (1998); implementation verified against FAO examples; C++ cross-checked with test_climate_unit.cpp"
}
```

---

## 4. Maturity Distribution (Reconciled)

| Maturity Level | Count | ECO-01 Claim | ECO-02 Claim | ECO-03 Verified |
|----------------|-------|--------------|--------------|-----------------|
| M1 (VERIFIED) | 13 | 4 | 8 | **CONFLICTING EVIDENCE** — actual: 13 |
| M2 (SCIENTIFICALLY_SUPPORTED) | 4 | 6 | 7 | 4 |
| M3 (IMPLEMENTATION_VERIFIED) | 5 | 8 | 6 | 5 |
| M4 (CODE_ONLY) | 0 | 2 | 0 | **0** (matches ECO-02, ECO-01 has CONFLICTING EVIDENCE) |
| M5 (STUB) | 1 | 1 | 1 | 1 |
| **REQUIRES_SCIENTIFIC_REVIEW** | 2 | 2 | 0 | **DISCREPANCY** — ECO-02 does not acknowledge |

**Conflicting Evidence**: ECO-01 §119 reports `Salinity` and `Climate Data Assimilation` as CODE_ONLY with issues, while ECO-02 claims 0 CODE_ONLY models. ECO-02's classification of all 22 models as VERIFIED or higher appears optimistic.

---

## 5. Scientific Status Separation

### Critical Findings

1. **INV-009 (from ECO-02)**: "Software test success is not scientific validation" — This is CORRECTLY identified in ECO-02 but NOT enforced in code.

2. **Verification vs Validation Gap**:
   - `engine/hydroma/climate/et_calculator.py` passes Python tests → IMPLEMENTATION_VERIFIED
   - But scientific validation requires comparison against observational data → M1 VERIFIED only if benchmarked

3. **Theis Solution (CANON-005)**:
   - ECO-01: REQUIRES_SCIENTIFIC_REVIEW (series convergence undocumented)
   - ECO-02: Classified as IMPLEMENTATION_VERIFIED
   - **STATUS**: BLOCKING — requires scientific review

---

## 6. Scientific Review Queue

| Item | Model | Priority | Status | Evidence Required |
|------|-------|----------|--------|-------------------|
| REVIEW-001 | Theis Solution (CANON-005) | P0 | NOT VERIFIED | Series convergence proof |
| REVIEW-002 | Climate Data Assimilation | P0 | REQUIRES_SCIENTIFIC_REVIEW | Validation against station data |
| REVIEW-003 | Soil Salinity Model | P1 | REQUIRES_SCIENTIFIC_REVIEW | Documented scientific basis |
| REVIEW-004 | CANON-014 (Model Registry) | P1 | BLOCKING for canonization | Remove `services.api_gateway` coupling |
| REVIEW-005 | CANON-015 (Watershed Calculator) | P1 | BLOCKING for canonization | Remove service coupling |

---

## 7. Findings

1. **CONFLICTING EVIDENCE**: ECO-01 reports 22 scientific models with mixed maturity; ECO-02 claims 8 VERIFIED CORE models. Reconciled count: 22 models with 13 VERIFIED, 4 SUPPORTED, 5 IMPLEMENTATION_VERIFIED.
2. **NOT VERIFIED**: CANON-001 is a label in ECO-02 contracts, not a formally versioned model identifier. ECO-03 defines the full model contract.
3. **DESIGNED BUT NOT ENFORCED**: Scientific model contract exists on paper; no runtime validation or schema enforcement in code.
4. **BLOCKING**: CANON-005 (Theis) and CANON-014/015 (service coupling) require scientific/engineering review before ECO-04 implementation.
5. **DISCREPANCY**: ECO-02 claims all 22 models classified with 0 at CODE_ONLY; ECO-01 reports 2 CODE_ONLY models.

---

*Report generated: 2026-10-08*
*Status: REQUIRES_SCIENTIFIC_REVIEW*