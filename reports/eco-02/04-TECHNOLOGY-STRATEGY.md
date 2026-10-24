# ECO-02: Technology Strategy

## CORE / IMPORTANT / OPTIONAL / RESEARCH / LEGACY / REMOVE Classification

---

## Source Evidence
- ECO-01/19-TECHNOLOGY-STRATEGY.md
- ECO-01/07-MODEL-QUALITY-MATRIX.md
- ECO-01/12-AI-FORENSICS.md
- ECO-01/22-LEGACY-DEPENDENCY-STRATEGY.md

---

## Technology Categories

### CORE (Mission-critical, must maintain)

| Technology | Justification |
|------------|---------------|
| Hydroma Scientific Engine (Python) | Central scientific computation orchestration |
| C++ Numerical Kernels | High-performance computation core |
| C++/Python boundary (ctypes/pybind11/buffer) | Zero-copy data transfer, performance-critical |
| Penman-Monteith ET0 (CANON-001) | FAO-56 reference standard |
| FAO-56 Crop Coefficient (CANON-009) | Irrigation scheduling standard |
| CMIP6 Climate Projections (CANON-018) | Climate data foundation |
| GPM IMERG Precipitation (CANON-019) | Observational meteorology |
| MODIS ET (CANON-020) | Satellite ET validation |
| Landsat (CANON-021) | Land surface monitoring |
| Sentinel-2 (CANON-022) | High-resolution remote sensing |

### IMPORTANT (Necessary, optimize but maintain)

| Technology | Justification |
|------------|---------------|
| Hargreaves ET0 (CANON-002) | Alternative ET method |
| Thornthwaite PET (CANON-003) | Temperature-based ET |
| Makkink (CANON-006) | Simplified radiation method |
| Priestley-Taylor (CANON-007) | Radiation-based ET |
| AquaCrop (CANON-010) | Crop water modeling |
| SWAT (CANON-011) | Watershed simulation |
| MODFLOW (CANON-013) | Groundwater flow |
| Hargreaves-Samani (CANON-005) | Temperature ET variant |
| Blaney-Crop (CANON-004) | Water requirement estimation |
| Jensen-Haise (CANON-008) | Energy-based ET |

### OPTIONAL (Useful but not essential)

| Technology | Justification |
|------------|---------------|
| HEC-HMS (CANON-012) | Flood simulation (supplementary) |
| WRF (CANON-014) | Weather research (external) |
| HRRR (CANON-015) | Rapid refresh forecast (external) |
| RegCM (CANON-016) | Regional climate (external) |
| HadGEM2 (CANON-017) | Climate model (external) |
| Python standard library | Core language support |

### RESEARCH (Experimental, isolate)

| Technology | Justification |
|------------|---------------|
| AI augmentation modules | Experimental per ECO-01/12, must not touch scientific core |
| ML-based downscaling | Research prototype |
| Neural ET estimation | Experimental alternative |
| AI policy recommendation | Experimental decision support |

### LEGACY (Deprecated, plan removal)

| Technology | Justification | Requirement ID |
|------------|---------------|----------------|
| Services importing from engine/ | Violates ECO-LEGACY-001 | ECO-LEGACY-001 |
| C++ code without Python tests | Coverage gap | - |
| Models marked STUB | Not functional | AUDIT-MODEL-0XX |

### REMOVE (Critical violation)

| Technology | Violation | Requirement ID |
|------------|-----------|----------------|
| All engine/→services/ imports | Breaks isolation | ECO-LEGACY-001 |
| Any AI component touching scientific core | Chain violation | ECO-AI-001 |
| Direct database access from scientific engine | Boundary violation | ECO-ARCH-001 |

---

## Classification Framework

### CORE Criteria
- Directly involved in scientific computation accuracy
- Peer-reviewed, validated models
- FAO/IEEE/ISO standards compliance

### RESEARCH Criteria
- Experimental, unvalidated
- No scientific peer review
- Must be isolated from CORE through Evidence Engine

### LEGACY/Removal Triggers
- Any import from engine/ to services/
- AI accessing scientific models directly
- Models without scientific documentation

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture*