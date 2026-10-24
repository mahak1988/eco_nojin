# ECO-04: Model Registry Report — Report 04

## Scientific model registry status

---

## 1. Registry Status

The Engine Gateway (`engine/gateway/`) has been created with a `ModelSpec` dataclass and `register_model()` method. However, **no models are registered yet** — the model registry implementation is deferred to ECO-04.4.

---

## 2. Models Identified (from ECO-03.1)

| Model ID | Name | Implementation | Test | Ref Data | Source | Benchmark | Validation | Software Status | Scientific Status |
|----------|------|---------------|------|----------|--------|-----------|------------|-----------------|-------------------|
| CANON-001 | Penman-Monteith ET0 | YES | YES | YES | FAO-56 | YES | YES | VERIFIED | VERIFIED |
| CANON-002 | Hargreaves ET0 | YES | YES | YES | Hargreaves 1985 | PARTIAL | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW |
| CANON-003 | Thornthwaite PET | YES | YES | NO | Thornthwaite 1948 | NO | NO | IMPLEMENTATION_VERIFIED | SCIENTIFICALLY_SUPPORTED |
| CANON-004 | SCS-CN Runoff | YES | YES | YES | USDA SCS | YES | YES | VERIFIED | VERIFIED |
| CANON-005 | Theis Solution | YES (partial) | YES | NO | Theis 1935 | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW |
| CANON-006 | Van Genuchten | YES | YES | YES | Van Genuchten 1980 | YES | YES | VERIFIED | VERIFIED |
| CANON-007 | RUSLE LS Factor | YES | YES | NO | Renard 1997 | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW |
| CANON-008 | D8 Flow Direction | YES | YES | YES | McCool 1989 | YES | YES | VERIFIED | VERIFIED |
| CANON-009 | Terrain Analysis | YES | YES | YES | Various | YES | YES | VERIFIED | VERIFIED |
| CANON-010 | Water Balance | YES | YES | YES | Various | YES | YES | VERIFIED | VERIFIED |
| CANON-011 | Solar Radiation | YES | YES | NO | Haurwitz 1942 | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW |
| CANON-012 | Formula Catalog | YES | YES | YES | — | — | — | VERIFIED | N/A |
| CANON-013 | Provenance Tracking | YES | YES | N/A | — | — | — | VERIFIED | N/A |
| CANON-014 | Model Registry | YES* | YES | N/A | — | — | — | IMPLEMENTATION_VERIFIED | N/A |
| CANON-015 | Watershed Calculator | YES | YES | YES | Various | YES | YES | VERIFIED | VERIFIED |
| CANON-016 | C++ Climate Kernels | YES | YES | YES | FAO-56 | YES | YES | VERIFIED | VERIFIED |
| CANON-017 | C++ Soil Kernels | YES | YES | YES | Van Genuchten | YES | YES | VERIFIED | VERIFIED |
| CANON-018 | CMIP6 Climate | YES (reference) | YES | NO | IPCC AR6 | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW |
| CANON-019 | GPM IMERG | YES (reference) | YES | YES | NASA | YES | YES | VERIFIED | VERIFIED |
| CANON-020 | MODIS ET | YES (reference) | YES | YES | NASA | YES | YES | VERIFIED | VERIFIED |
| CANON-021 | Landsat | YES (reference) | YES | YES | USGS | YES | YES | VERIFIED | VERIFIED |
| CANON-022 | Sentinel-2 | YES (reference) | YES | YES | ESA | YES | YES | VERIFIED | VERIFIED |

*CANON-014 (Model Registry) — Implementation partially exists in `engine/hydroma/models/registry.py`, pending full gateway integration.

---

## 3. Model Metadata Requirements

Per ECO-04.md §15, each model registered with the gateway MUST have:

- model_id
- model_version
- model_name
- model_type
- domain
- purpose
- inputs
- input_units
- input_constraints
- parameters
- parameter_units
- parameter_constraints
- assumptions
- equations
- algorithms
- numerical_methods
- outputs
- output_units
- uncertainty
- uncertainty_method
- provenance
- validation
- validation_evidence
- applicability_domain
- limitations
- execution_metadata

Current status: Only `model_id`, `model_version`, `model_name`, `model_type`, `domain`, `purpose`, `assumptions`, and `limitations` are captured in `ModelSpec`. The remaining metadata fields will be added in ECO-04.4.

---

## 4. Registry Status

| Criterion | Status |
|-----------|--------|
| Model registry module exists | ✅ YES (in Engine Gateway) |
| ModelSpec class defined | ✅ YES |
| register_model() method | ✅ YES |
| Models registered | ❌ NO (deferred to ECO-04.4) |
| Model metadata complete | ❌ PARTIAL (8 of 24 fields) |
| Scientific validation status tracked | ❌ NO (deferred to ECO-04.4) |

---

## 5. Next Steps

| Sprint | Task |
|--------|------|
| ECO-04.4 | Implement full model registry with metadata |
| ECO-04.4 | Register all 22 CANON models with metadata |
| ECO-04.4 | Integrate with scientific validation status |

---

*Report generated: 2026-10-08*
*Status: Model registry structure exists, implementations deferred to ECO-04.4*