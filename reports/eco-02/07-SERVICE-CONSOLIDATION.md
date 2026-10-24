# ECO-02: Service Consolidation Analysis

## From 73 Services to Bounded-Context Modules

---

## Source Evidence
- ECO-01/13-SERVICE-ASSET-MAP.md (73 services catalogued)
- ECO-01/14-SERVICE-CONSOLIDATION-ANALYSIS.md
- ECO-01 §3.2 (consolidation requirement)

---

## Current State: 73 Services

### Breakdown
| Category | Count | Percentage |
|----------|-------|------------|
| Infrastructure | 45 | 63% |
| Domain (scientific) | 28 | 37% |
| **Total** | **73** | **100%** |

### Infrastructure Overrepresentation
45/73 services (63%) are infrastructure - far too many microservices for a water resources project.

---

## Target Architecture: Bounded Contexts

### Consolidated Modules

| Bounded Context | Services Consolidated | Purpose |
|-----------------|----------------------|---------|
| **Platform Core** | ~25 infra services | Auth, config, logging, monitoring |
| **Meteorology** | ~8 services | Weather data acquisition, processing |
| **Hydrology** | ~6 services | Streamflow, watershed, groundwater |
| **AgriWater** | ~5 services | ET, crop water, irrigation scheduling |
| **Evidence Provenance** | ~4 services | Audit trail, data validation |
| **Decision Engine** | ~3 services | Policy evaluation, recommendation |
| **Remote Sensing** | ~5 services | Satellite data, image processing |
| **Reporting** | ~2 services | Output generation, visualization |

---

## Consolidation Rules

### Rule 1: Infrastructure → Platform Core
All infrastructure services (auth, database, config, monitoring) consolidate into single Platform Core module.

### Rule 2: Scientific services → Domain contexts
- Meteorology services → Meteorology context
- Hydrology services → Hydrology context
- AgriWater services → AgriWater context

### Rule 3: Evidence services → Evidence context
All provenance, validation, and audit services → Evidence Provenance context.

---

## Violation Detection

### ECO-SVC-001: engine/→services/ import
**Condition**: Any service imports from engine/ package
**Action**: BLOCK, redirect through Engine Gateway

### ECO-SVC-002: Cross-context dependency
**Condition**: Service in one bounded context imports from another (non-adjacent)
**Action**: Introduce anti-corruption layer at Evidence Engine

---

## Migration Path

### Phase 1: Platform Core
- Consolidate auth, database, config services
- Establish common interface patterns

### Phase 2: Domain Consolidation
- Group meteorology, hydrology, agri-water services
- Establish evidence engine as integration layer

### Phase 3: AI Isolation
- Move AI augmentation to separate context
- Enforce evidence-chain integration only

---

## Service-to-Layer Mapping

| Service Group | Architecture Layer |
|---------------|-------------------|
| Platform Core | Layer 2 (Application Orchestration) |
| Meteorology | Layer 6 (Domain Services) |
| Hydrology | Layer 6 (Domain Services) |
| AgriWater | Layer 6 (Domain Services) |
| Evidence Provenance | Layer 5 (Evidence Engine) |
| Decision Engine | Layer 3 (Decision/Tasmimyar) |
| Remote Sensing | Layer 6 (Domain Services) |
| Reporting | Layer 1 (Product Experience) |

---

*Generated: 2026-10-08*
*Source: ECO-02.md canonical architecture, ECO-01/13-SERVICE-ASSET-MAP.md*