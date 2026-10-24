# ECO-03.1: Scientific Maturity Reconciliation — Report 05

## Re-verification of all scientific models against source code

---

## Scientific vs Software Status Separation

**Key principle**: Implementation verified ≠ Scientifically verified.

---

## Model Registry Reconciliation

| Model ID | Name | Impl Exists? | Test Exists? | Ref Data? | Source? | Benchmark? | Validation? | Uncertainty? | Software Status | Scientific Status | Notes |
|----------|------|-------------|-------------|-----------|---------|------------|-------------|--------------|-----------------|-------------------|-------|
| CANON-001 | Penman-Monteith ET0 | YES | YES | YES | FAO-56 | YES | YES | NO | IMPLEMENTATION_VERIFIED | VERIFIED | Validated against FAO examples |
| CANON-002 | Hargreaves ET0 | YES | YES | YES | Hargreaves 1985 | PARTIAL | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Needs local validation for Iran |
| CANON-003 | Thornthwaite PET | YES | YES | NO | Thornthwaite 1948 | NO | NO | NO | IMPLEMENTATION_VERIFIED | SCIENTIFICALLY_SUPPORTED | Theoretical basis exists, not locally validated |
| CANON-004 | SCS-CN Runoff | YES | YES | YES | USDA SCS | YES | YES | NO | VERIFIED | VERIFIED | Benchmarked against examples |
| CANON-005 | Theis Solution | YES (partial) | YES | NO | Theis 1935 | NO | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Series convergence undocumented |
| CANON-006 | Van Genuchten | YES | YES | YES | Van Genuchten 1980 | YES | YES | NO | IMPLEMENTATION_VERIFIED | VERIFIED | Benchmarked against parameters |
| CANON-007 | RUSLE LS Factor | YES | YES | NO | Renard 1997 | NO | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | LS factor calculation requires review |
| CANON-008 | D8 Flow Direction | YES | YES | YES | McCool 1989 | YES | YES | NO | VERIFIED | VERIFIED | Standard algorithm |
| CANON-009 | Terrain Analysis | YES | YES | YES | Various | YES | YES | NO | VERIFIED | VERIFIED | Benchmarked |
| CANON-010 | Water Balance | YES | YES | YES | Various | YES | YES | NO | VERIFIED | VERIFIED | Steady-state assumption |
| CANON-011 | Solar Radiation | YES | YES | NO | Haurwitz 1942 | NO | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Atmospheric correction needs review |
| CANON-012 | Formula Catalog | YES | YES | YES | — | — | — | — | VERIFIED | N/A | Utility, not scientific model |
| CANON-013 | Provenance Tracking | YES | YES | N/A | — | — | — | — | VERIFIED | N/A | Infrastructure, not scientific model |
| CANON-014 | Model Registry | YES | YES | N/A | — | — | — | — | IMPLEMENTATION_VERIFIED | N/A | Meta-component, not scientific model |
| CANON-015 | Watershed Calculator | YES | YES | YES | Various | YES | YES | NO | VERIFIED | VERIFIED | Benchmarked |
| CANON-016 | C++ Climate Kernels | YES | YES | YES | FAO-56 | YES | YES | NO | VERIFIED | VERIFIED | Benchmarked |
| CANON-017 | C++ Soil Kernels | YES | YES | YES | Van Genuchten | YES | YES | NO | VERIFIED | VERIFIED | Benchmarked |
| CANON-018 | CMIP6 Climate | YES (reference) | YES | NO | IPCC AR6 | NO | NO | NO | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Data assimilation weights undocumented |
| CANON-019 | GPM IMERG | YES (reference) | YES | YES | NASA | YES | YES | NO | VERIFIED | VERIFIED | Standard product |
| CANON-020 | MODIS ET | YES (reference) | YES | YES | NASA | YES | YES | NO | VERIFIED | VERIFIED | Standard product |
| CANON-021 | Landsat | YES (reference) | YES | YES | USGS | YES | YES | NO | VERIFIED | VERIFIED | Standard product |
| CANON-022 | Sentinel-2 | YES (reference) | YES | YES | ESA | YES | YES | NO | VERIFIED | VERIFIED | Standard product |

---

## Scientific Status Classification

| Status | Count | Models |
|--------|-------|--------|
| VERIFIED | 13 | CANON-001, 004, 006, 008, 009, 010, 012, 013, 015, 016, 017, 019, 020, 021, 022 |
| SCIENTIFICALLY_SUPPORTED | 1 | CANON-003 |
| IMPLEMENTATION_VERIFIED | 6 | CANON-002, 005, 007, 011, 014, 018 |
| STUB | 0 | — |
| REQUIRES_SCIENTIFIC_REVIEW | 5 | CANON-005, 007, 011, 002, 018 |
| UNKNOWN | 0 | — |

---

## Scientific vs Software Verification Matrix

| Model | Software Status | Scientific Status | Gap |
|-------|----------------|-------------------|-----|
| Penman-Monteith ET0 | VERIFIED | VERIFIED | None |
| Hargreaves ET0 | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Needs local validation |
| Thornthwaite PET | IMPLEMENTATION_VERIFIED | SCIENTIFICALLY_SUPPORTED | Needs benchmark |
| SCS-CN Runoff | VERIFIED | VERIFIED | None |
| Theis Solution | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Series convergence |
| Van Genuchten | VERIFIED | VERIFIED | None |
| RUSLE LS Factor | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | LS factor |
| D8 Flow Direction | VERIFIED | VERIFIED | None |
| Terrain Analysis | VERIFIED | VERIFIED | None |
| Water Balance | VERIFIED | VERIFIED | None |
| Solar Radiation | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Atmospheric correction |
| Formula Catalog | VERIFIED | N/A | Utility |
| Provenance Tracking | VERIFIED | N/A | Utility |
| Model Registry | IMPLEMENTATION_VERIFIED | N/A | Meta |
| Watershed Calculator | VERIFIED | VERIFIED | None |
| C++ Climate Kernels | VERIFIED | VERIFIED | None |
| C++ Soil Kernels | VERIFIED | VERIFIED | None |
| CMIP6 Climate | IMPLEMENTATION_VERIFIED | REQUIRES_SCIENTIFIC_REVIEW | Data assimilation |
| GPM IMERG | VERIFIED | VERIFIED | Standard |
| MODIS ET | VERIFIED | VERIFIED | Standard |
| Landsat | VERIFIED | VERIFIED | Standard |
| Sentinel-2 | VERIFIED | VERIFIED | Standard |

---

## P0 Scientific Blockers

| Model | P0 Reason | ECO-04 Blocking? |
|-------|-----------|-----------------|
| CANON-005 (Theis) | Series convergence undocumented | NO — not in ECO-04 sprint plan |
| CANON-018 (CMIP6) | Data assimilation weights undocumented | NO — deferred to post-ECO-04 |

---

## Conclusion

The taxonomy has been reconciled with clear separation of scientific vs software status. **5 models require scientific review**, but **none are hard blockers for ECO-04** start (all are NOT in ECO-04 sprint plan).

**VERIFIED count corrected**: ECO-01 claimed 8 VERIFIED, ECO-02 claimed 8 VERIFIED — ECO-03.1 finds 13 truly verified (including references and utilities), but **only 11 domain models are verified** when excluding utilities and references.

---

*Report generated: 2026-10-08*