# ECO-03: Open Questions — Report 23
## Unresolved Questions Requiring External Input

---

## Executive Summary

This report captures all questions that cannot be resolved without external input (scientific review, business decisions, or expert consultation).

---

## 1. Scientific Review Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-SCI-001 | Theis Solution series convergence: what is the valid convergence criterion? | CANON-005 cannot be canonized without verification | Hydrogeology expert |
| Q-SCI-002 | Soil Salinity Model: what is the scientific basis? Previous report marks as NOT_RECOMMENDED | Model needs validation or deprecation | Soil science expert |
| Q-SCI-003 | Climate Data Assimilation: weight assignment methodology undocumented | Affects data quality scoring | Climate scientist |
| Q-SCI-004 | Hargreaves-Samani: should this be VERIFIED or remain SCIENTIFICALLY_SUPPORTED? | Affects model authority | Evapotranspiration expert |
| Q-SCI-005 | Van Genuchten solver: convergence criteria for Newton-Raphson | Affects soil moisture accuracy | Soil physics expert |
| Q-SCI-006 | RUSLE LS factor calculation: method validation against local conditions | Affects erosion estimates | Erosion modeling expert |

---

## 2. Architectural Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-ARCH-001 | What is the canonical path for Hydroma engine? Reports show hydra/, hydorama/, hydroma/ | Affects all imports | Architecture team |
| Q-ARCH-002 | Should `engine/hydroma/` be renamed to `engine/scientific/`? | Canonical structure question | Architecture team |
| Q-ARCH-003 | How to resolve circular import: engine→services.ai→services.scientific_motors→engine? | Blocking ECO-LEGACY-001 fix | Architecture team |
| Q-ARCH-004 | Should `database/` be provisioned as external package or removed from engine? | Blocking all tests | Infrastructure team |
| Q-ARCH-005 | Should `services/scientific_motors/` be in AI layer or services layer? | Affects AI boundary | Architecture team |
| Q-ARCH-006 | Should `engine/hydroma/optimization/` be moved to decision layer? | Boundary clarity | Architecture team |
| Q-ARCH-007 | Should the 8 bounded contexts be reduced or expanded? | Implementation complexity | Architecture team |

---

## 3. Business / Domain Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-BIZ-001 | Which Iranian crop coefficients (KBK-001 series) should be canonical? | Affects AgriWater accuracy | Agricultural expert |
| Q-BIZ-002 | Should `services/livestock/` and `services/tourism/` be in any context? | Service consolidation scope | Product manager |
| Q-BIZ-003 | What is the canonical stakeholder model for decision weighting? | Affects Tasmimyar DE-006 | Domain expert |
| Q-BIZ-004 | Should smart contracts use REFERENCE_ONLY or be re-architected? | Affects blockchain scope | Blockchain architect |
| Q-BIZ-005 | What is the budget allocation for AI research vs. core development? | Affects ADR-014 technology strategy | Project manager |

---

## 4. Technical Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-TECH-001 | Should we use pyproject.toml or requirements.txt? | Blocking reproducible builds | DevOps engineer |
| Q-TECH-002 | What Python versions to support? (3.11, 3.12 detected) | Affects deployment | DevOps engineer |
| Q-TECH-003 | Should C++ build use single build directory? (build/ vs build2/) | Build reliability | Build engineer |
| Q-TECH-004 | What is the minimum supported browser for visualization? | UI planning | Frontend team |
| Q-TECH-005 | Should we deprecate numpy.random in favor of explicit RNG? | Reproducibility | Data scientist |
| Q-TECH-006 | What is the canonical model serving architecture? | Implementation planning | MLOps engineer |

---

## 5. Performance Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-PERF-001 | What are the actual benchmark results for C++ vs Python? | No benchmark data in repository | Performance engineer |
| Q-PERF-002 | What is the 10x-200x speedup claim based on? | No evidence found | Performance engineer |
| Q-PERF-003 | What are the memory usage patterns for large arrays? | Not measured | Performance engineer |
| Q-PERF-004 | Should we use GPU acceleration for indices? | 3 GPU candidates identified, not verified | Performance engineer |

---

## 6. Data Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-DATA-001 | What is the schema for the missing `database/` package? | Blocking all tests | Data architect |
| Q-DATA-002 | How to handle real-time vs batch data processing? | Affects system design | Data engineer |
| Q-DATA-003 | What satellite data licensing is required? | Affects commercial use | Legal/compliance |
| Q-DATA-004 | How to handle missing data in climate stations? | Affects data quality | Data scientist |

---

## 7. Security Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-SEC-001 | What authentication system will be used? (Supabase auth exists) | Out of scope but engine references it | Security architect |
| Q-SEC-002 | How to secure the Engine Gateway API? | Must be defined before implementation | Security architect |
| Q-SEC-003 | What are the compliance requirements for Iranian data? | Data residency | Legal/compliance |

---

## 8. Deployment Questions

| question_id | question | why_blocking | reviewer |
|-------------|----------|--------------|----------|
| Q-DEPLOY-001 | Should the platform be cloud-native or on-premise? | Affects architecture | DevOps engineer |
| Q-DEPLOY-002 | What is the container orchestration strategy? | Affects deployment | DevOps engineer |
| Q-DEPLOY-003 | How to handle C++ extension deployment? | Platform-specific .pyd files | DevOps engineer |

---

## 9. Open Questions Summary

| Category | Count | Blocking |
|----------|-------|----------|
| Scientific | 6 | 4 |
| Architectural | 7 | 5 |
| Business/Domain | 5 | 3 |
| Technical | 6 | 2 |
| Performance | 4 | 1 |
| Data | 4 | 1 |
| Security | 3 | 1 |
| Deployment | 3 | 2 |
| **Total** | **38** | **19** |

---

## 10. Scientific Review Queue

### Priority 0 (Critical)
| Item | Model | Required By | Evidence Needed |
|------|-------|-------------|-----------------|
| 1 | Theis Solution (CANON-005) | ECO-04.4 | Series convergence proof |
| 2 | Climate Data Assimilation | ECO-04.4 | Validation against station data |

### Priority 1 (Important)
| Item | Model | Required By | Evidence Needed |
|------|-------|-------------|-----------------|
| 3 | Soil Salinity Model | ECO-04.4 | Documented scientific basis |
| 4 | CANON-014 (Model Registry) | ECO-04.5 | Remove service coupling |
| 5 | CANON-015 (Watershed Calculator) | ECO-04.5 | Remove service coupling |

### Priority 2 (Quality Gap)
| Item | Model | Required By | Evidence Needed |
|------|-------|-------------|-----------------|
| 6 | Hargreaves-Samani (CANON-002) | ECO-04.5 | Benchmark against field data |
| 7 | RUSLE LS factor | ECO-04.5 | Local validation |
| 8 | EPIA Precision Irrigation | ECO-04.6 | Validation against trials |

---

*Report generated: 2026-10-08*
*Status: 38 open questions, 19 blocking*