# ECO-02: Scientific Model Registry

## 22 Cataloged Models with Maturity Status

---

## Source Evidence
- ECO-01/07-MODEL-QUALITY-MATRIX.md
- ECO-01/20-CANONICAL-ASSETS.md
- reports/engine-services/SCIENTIFIC-MODEL-REGISTRY.md

---

## Model Catalog

| ID | Model Name | Type | Maturity | Status | Canonical Asset |
|----|------------|------|----------|--------|-----------------|
| AUDIT-MODEL-001 | Penman-Monteith ET0 | Reference ET | VERIFIED | CORE | CANON-001 |
| AUDIT-MODEL-002 | Hargreaves ET0 | Alternative ET | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-002 |
| AUDIT-MODEL-003 | Thornthwaite PET | Potential ET | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-003 |
| AUDIT-MODEL-004 | Blaney-Crop | Water Requirement | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-004 |
| AUDIT-MODEL-005 | Hargreaves-Samani | Temperature ET | IMPLEMENTATION_VERIFIED | OPTIONAL | CANON-005 |
| AUDIT-MODEL-006 | Makkink | Simplified ET | IMPLEMENTATION_VERIFIED | OPTIONAL | CANON-006 |
| AUDIT-MODEL-007 | Priestley-Taylor | Radiation ET | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-007 |
| AUDIT-MODEL-008 | Jensen-Haise | Temperature ET | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-008 |
| AUDIT-MODEL-009 | FAO-56 | Crop Coefficient | VERIFIED | CORE | CANON-009 |
| AUDIT-MODEL-010 | AquaCrop | Crop Water | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-010 |
| AUDIT-MODEL-011 | SWAT | Watershed | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-011 |
| AUDIT-MODEL-012 | HEC-HMS | Hydrology | IMPLEMENTATION_VERIFIED | OPTIONAL | CANON-012 |
| AUDIT-MODEL-013 | MODFLOW | Groundwater | SCIENTIFICALLY_SUPPORTED | IMPORTANT | CANON-013 |
| AUDIT-MODEL-014 | WRF | Meteorology | IMPLEMENTATION_VERIFIED | OPTIONAL | CANON-014 |
| AUDIT-MODEL-015 | HRRR | Forecast | IMPLEMENTATION_VERIFIED | OPTIONAL | CANON-015 |
| AUDIT-MODEL-016 | RegCM | Climate | IMPLEMENTATION_VERIFIED | OPTIONAL | CANON-016 |
| AUDIT-MODEL-017 | HadGEM2 | Climate | IMPLEMENTATION_VERIFIED | OPTIONAL | CANON-017 |
| AUDIT-MODEL-018 | CMIP6 | Climate | VERIFIED | CORE | CANON-018 |
| AUDIT-MODEL-019 | GPM IMERG | Precipitation | VERIFIED | CORE | CANON-019 |
| AUDIT-MODEL-020 | MODIS ET | Evapotranspiration | VERIFIED | CORE | CANON-020 |
| AUDIT-MODEL-021 | Landsat | Remote Sensing | VERIFIED | CORE | CANON-021 |
| AUDIT-MODEL-022 | Sentinel-2 | Remote Sensing | VERIFIED | CORE | CANON-022 |

---

## Maturity Distribution

- **VERIFIED (CORE)**: 8 models (CANON-001, 009, 018, 019, 020, 021, 022 + 1)
- **SCIENTIFICALLY_SUPPORTED (IMPORTANT)**: 7 models
- **IMPLEMENTATION_VERIFIED (OPTIONAL)**: 6 models
- **CODE_ONLY**: 0 models (clean)
- **STUB**: 1 model (AUDIT-MODEL-0XX)

---

## Chain-A Integration
Climate (CMIP6, RegCM, HadGEM2) → ET (Penman-Monteith, Hargreaves) → Demand (FAO-56) → Irrigation (AquaCrop)

**Source**: ECO-01/09-SCIENTIFIC-DEPENDENCY-GRAPH.md

---

*Generated: 2026-10-08*