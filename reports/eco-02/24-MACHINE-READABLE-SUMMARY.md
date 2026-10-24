# ECO-02: Machine Readable Summary

## JSON/YAML Architecture Definition

---

## Source Evidence
- reports/engine-services/MACHINE_READABLE_SUMMARY.md
- ECO-01/20-CANONICAL-ASSETS.md
- ECO-01/07-MODEL-QUALITY-MATRIX.md

---

## Architecture Summary (JSON)

```json
{
  "ecosystem": "ECO-02 Canonical Architecture",
  "version": "1.0.0",
  "generated": "2026-10-08",
  "layers": {
    "product_experience": {
      "purpose": "User interfaces and presentation",
      "status": "out_of_scope_per_eco01"
    },
    "application_orchestration": {
      "purpose": "Workflow coordination and API",
      "status": "in_scope"
    },
    "decision": {
      "name": "Tasmimyar",
      "purpose": "Policy evaluation and decision engine",
      "elements": 11
    },
    "knowledge": {
      "name": "Daneshyar",
      "purpose": "Knowledge graph and canonical assets",
      "types": 9
    },
    "evidence": {
      "name": "Evidence Engine",
      "purpose": "Evidence collection and provenance",
      "status": "in_scope"
    },
    "domain_services": {
      "name": "Hydroma",
      "purpose": "Domain-bounded microservices",
      "services_consolidated": 73
    },
    "engine_gateway": {
      "purpose": "Python/C++ boundary",
      "mechanisms": ["ctypes", "pybind11", "buffer_protocol"]
    },
    "scientific_engine": {
      "name": "Hydroma Scientific Engine",
      "purpose": "Scientific computation orchestration",
      "models": 22
    },
    "numerical_computation": {
      "name": "C++ Numerical Kernels",
      "purpose": "High-performance computation",
      "cpp_files": 10,
      "headers": 10,
      "tests": 21
    }
  }
}
```

---

## Model Registry (JSON)

```json
{
  "models": [
    {
      "id": "AUDIT-MODEL-001",
      "canon_id": "CANON-001",
      "name": "Penman-Monteith ET0",
      "maturity": "VERIFIED",
      "status": "CORE",
      "layer": "numerical_computation",
      "cpp_kernel": "et_calculations.cpp"
    },
    {
      "id": "AUDIT-MODEL-009",
      "canon_id": "CANON-009",
      "name": "FAO-56 Crop Coefficient",
      "maturity": "VERIFIED",
      "status": "CORE",
      "layer": "numerical_computation",
      "cpp_kernel": "crop_water.cpp"
    },
    {
      "id": "AUDIT-MODEL-011",
      "canon_id": "CANON-011",
      "name": "SWAT",
      "maturity": "SCIENTIFICALLY_SUPPORTED",
      "status": "IMPORTANT",
      "layer": "domain_services"
    },
    {
      "id": "AUDIT-MODEL-013",
      "canon_id": "CANON-013",
      "name": "MODFLOW",
      "maturity": "SCIENTIFICALLY_SUPPORTED",
      "status": "IMPORTANT",
      "layer": "numerical_computation",
      "cpp_kernel": "groundwater.cpp"
    }
  ],
  "maturity_counts": {
    "VERIFIED": 8,
    "SCIENTIFICALLY_SUPPORTED": 7,
    "IMPLEMENTATION_VERIFIED": 6,
    "CODE_ONLY": 0,
    "STUB": 1
  }
}
```

---

## Service Consolidation Map (JSON)

```json
{
  "current_services": 73,
  "consolidation_target": {
    "Platform Core": {"count": 25, "purpose": "infrastructure"},
    "Meteorology": {"count": 8, "purpose": "weather data"},
    "Hydrology": {"count": 6, "purpose": "streamflow, watershed"},
    "AgriWater": {"count": 5, "purpose": "ET, crops, irrigation"},
    "Evidence Provenance": {"count": 4, "purpose": "audit, validation"},
    "Decision Engine": {"count": 3, "purpose": "policy, decisions"},
    "Remote Sensing": {"count": 5, "purpose": "satellite processing"},
    "Reporting": {"count": 2, "purpose": "output, visualization"}
  }
}
```

---

## Technology Strategy (YAML)

```yaml
technology_classification:
  CORE:
    - hydroma_scientific_engine
    - cxx_numerical_kernels
    - cpp_python_boundary
    - penman_monteith_et0
    - fao56_crop_coefficient
    - cmip6_climate_projections
    - gpm_imerg_precipitation
    - modis_et
    - landsat
    - sentinel2
    
  IMPORTANT:
    - hargreaves_et0
    - thornthwaite_pet
    - makkink_et
    - priestley_taylor_et
    - aquacrop
    - swat_model
    - modflow
    - hargreaves_samani
    - blaney_crop
    - jensen_haise
    
  OPTIONAL:
    - hec_hms
    - wrf_model
    - hrrr_forecast
    - regcm_model
    - hadgem2_model
    
  RESEARCH:
    - ai_recommendation
    - ml_downscaling
    - neural_et
    - ai_augmentation
    
  LEGACY:
    - duplicate_model_implementations
    - engine_to_services_imports
    - stub_models
    
  REMOVE:
    - engine_services_imports
    - ai_direct_scientific_core_access
    - direct_database_from_engine
```

---

## Boundary Violations (JSON)

```json
{
  "violations": [
    {
      "type": "ECO-LEGACY-001",
      "description": "Services importing from engine/",
      "severity": "CRITICAL",
      "status": "requires_immediate_fix"
    },
    {
      "type": "ECO-AI-001",
      "description": "AI accessing scientific models",
      "severity": "CRITICAL",
      "status": "must_be_blocked"
    },
    {
      "type": "ECO-SVC-001",
      "description": "Cross-context service imports",
      "severity": "HIGH",
      "status": "consolidation_required"
    }
  ]
}
```

---

## File Inventory Summary

| Category | Files | Tests |
|----------|-------|-------|
| C++ source files | 10 | - |
| C++ header files | 10 | - |
| C++ test files | - | 21 |
| Python engine files | 290 | - |
| Python service files | 644 | - |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, reports/engine-services/MACHINE_READABLE_SUMMARY.md*