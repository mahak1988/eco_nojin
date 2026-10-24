# ECO-01 Legacy Dependency Strategy

**Document ID:** ECO-01-22-LEGACY-DEPENDENCY-STRATEGY  
**Scope:** engine/ + services/ legacy dependencies  
**Purpose:** Classify all legacy dependencies and define isolation strategy

---

## 1. Legacy Dependency Classification

| Classification | Meaning |
|----------------|---------|
| REMOVE | Eliminate entirely; no replacement needed |
| ISOLATE | Separate into adapter layer; remove direct coupling |
| REPLACE | Replace with modern alternative |
| RETAIN_TEMPORARILY | Keep until alternative developed |
| UNKNOWN | Cannot determine impact |

---

## 2. Engine → Services Dependencies (Critical)

### ECO-LEGACY-001: Engine importing from services

**Severity:** CRITICAL  
**Locations found:**

| File | Import | Type | Recommendation |
|------|--------|------|----------------|
| engine/hydroma/models/groundwater_model.py | services.utils.units | UNIT CONVERSION | ISOLATE |
| engine/hydrama/watershed/flow.py | services.territory.models | SCHEMA | ISOLATE |
| engine/hydrama/irrigation/scheduler.py | services.crops.models | DATA | ISOLATE |
| engine/hydra/climate/assimilation.py | services.config.settings | CONFIG | ISOLATE |
| engine/hydrama/soil/physics.py | services.soil.lookup | LOOKUP TABLE | ISOLATE |

**Impact:** Scientific engine is coupled to service layer, violating architectural separation.

**Action:** Remove all `services.*` imports from engine code. Create configuration injection or local lookup tables.

### ECO-LEGACY-002: Service layer importing engine

**Severity:** ACCEPTABLE but monitor  
**Locations found:**

| File | Import | Type | Notes |
|------|--------|------|-------|
| services/models/registry.py | engine.hydroma.* | SCIENTIFIC LOGIC | REVERSE dependency |
| services/simulation/ | engine.hydroma.simulation | COMPUTATION | REVERSE dependency |
| services/analysis/ | engine.land.* | GIS ANALYSIS | REVERSE dependency |

**Assessment:** Reverse dependency (services → engine) is acceptable. Engine should remain the computation core, services orchestrate.

---

## 3. Services → Database Dependencies

### ECO-LEGACY-003: Database ORM coupling

**Severity:** HIGH  
**Locations found:**

| Service | Import | Type | Recommendation |
|---------|--------|------|----------------|
| services/data | sqlalchemy, psycopg2 | DATABASE | RETAIN_TEMPORARILY |
| services/knowledge | sqlalchemy | DATABASE | RETAIN_TEMPORARILY |
| services/monitoring | sqlalchemy | DATABASE | RETAIN_TEMPORARILY |
| services/validation | sqlalchemy | DATABASE | ISOLATE |
| services/audit | sqlalchemy | DATABASE | ISOLATE |
| services/project | sqlalchemy | DATABASE | RETAIN_TEMPORARILY |
| services/tasmimyar | sqlalchemy | DATABASE | RETAIN_TEMPORARILY |
| services/daneshyar | sqlalchemy | DATABASE | RETAIN_TEMPORARILY |

**Assessment:** Database coupling is pervasive in services layer. Database is out of ECO-01 scope. These should be isolated but retained.

### ECO-LEGACY-004: ORM-specific queries

| Service | Pattern | Risk | Recommendation |
|---------|---------|------|----------------|
| services/carbon | SQLAlchemy ORM | HIGH | Abstract with repository pattern |
| services/soil | ORM queries in logic | HIGH | Extract data access layer |
| services/climate | Mixed SQL + ORM | MEDIUM | Standardize |
| services/water | ORM in computation | MEDIUM | Extract domain layer |

---

## 4. Services → Frontend Dependencies

### ECO-LEGACY-005: Direct HTML/template rendering

| Service | Pattern | Recommendation |
|---------|---------|----------------|
| services/reporting | Jinja2 templates | ISOLATE |
| services/admin | Admin templates | LEGACY |
| services/bots | Telegram bot rendering | LEGACY |
| services/content | Content management | LEGACY |

---

## 5. AI → Application Services Dependencies

### ECO-LEGACY-006: AI components calling application services

| File | Import | Risk | Recommendation |
|------|--------|------|----------------|
| engine/hydroma/generative_ai/ | services.ai.* | HIGH | ISOLATE |
| engine/hydorama/remote_sensing/ | services.satellite.* | MEDIUM | ISOLATE |

**Assessment:** AI components should not depend on application services. Must be isolated.

---

## 6. Scientific Code → Legacy APIs

### ECO-LEGACY-007: Scientific models calling external APIs

| Model | API Call | Type | Risk | Recommendation |
|-------|----------|------|------|----------------|
| Climate Assimilation | Weather API | External | HIGH | ISOLATE to adapter |
| Radiation Model | No | Local | Low | OK |
| ET0 | No | Local | Low | OK |
| All soil models | No | Local | Low | OK |
| All hydrology | No | Local | Low | OK |

---

## 7. Legacy Wrappers

### ECO-LEGACY-008: Deprecated library wrappers

| Wrapper | Legacy Library | Modern Alternative | Recommendation |
|---------|----------------|-------------------|----------------|
| services/data/processors/csv_parser.py | pandas.read_csv | pd.read_csv | RETAIN |
| services/utils/geo.py | geopy | shapely | REPLACE |
| services/data/formats/old_json.py | custom JSON | json module | REMOVE |
| services/validation/legacy.py | old validation | pydantic | REPLACE |

---

## 8. Environment Assumptions

### ECO-LEGACY-009: Hard-coded paths and environment assumptions

| File | Assumption | Risk | Recommendation |
|------|------------|------|----------------|
| engine/hydroma/paths.py | /data directory exists | HIGH | CONFIGURE via env |
| engine/hydra/config.py | HOME env var set | LOW | ACCEPTABLE |
| services/config.py | DATABASE_URL set | HIGH | ISOLATE |
| engine/hydoma/logs/config.py | LOG_DIR writable | LOW | Accept with fallback |

---

## 9. Implicit Imports

### ECO-LEGACY-010: Circular / implicit dependencies

| From | To | Type | Risk | Recommendation |
|------|----|------|------|----------------|
| engine.hydroma.climate | engine.hydromoa.soil | Implicit | LOW | Document |
| services.carbon | engine.hydroma.soil | Explicit | LOW | Acceptable |
| services.agriculture | engine.hydroma.agriculture + engine.hydra.soil | Mixed | MEDIUM | Consolidate |
| services.land | engine.hydra + services.map_engine | Mixed | HIGH | ISOLATE |

---

## 10. Full Legacy Dependency List

### Engine → Service Dependencies (Must Fix)

| Dependency | Location | Severity | Classification |
|-----------|----------|----------|----------------|
| services.config → engine.hydroma | engine/climate/assimilation.py | CRITICAL | ISOLATE |
| services.territory → engine.hydroma.watershed | engine/watershed/flow.py | HIGH | ISOLATE |
| services.crops → engine.hydra.irrigation | engine/irrigation/scheduler.py | HIGH | ISOLATE |
| services.utils → engine.hydoma | engine/models/groundwater_model.py | HIGH | ISOLATE |
| services.soil.lookup → engine.hydoma.soil | engine/soil/physics.py | MEDIUM | ISOLATE |

### Service → Database Dependencies

| Dependency | Services Affected | Severity | Classification |
|-----------|-------------------|----------|----------------|
| SQLAlchemy ORM | 15+ services | HIGH | RETAIN_TEMPORARILY |
| psycopg2 | 4 services | HIGH | RETAIN_TEMPORARILY |
| Session/Transaction | 15+ services | HIGH | RETAIN_TEMPORARILY |

### Service → External Dependencies

| Dependency | Services Affected | Severity | Classification |
|-----------|-------------------|----------|----------------|
| Weather APIs | climate, satellite | MEDIUM | ISOLATE |
| Satellite APIs | satellite, remote_sensing | MEDIUM | ISOLATE |
| Payment APIs | commerce, wallet | LOW | REMOVE |
| Blockchain | blockchain, wallet | LOW | REMOVE |
| Messaging | bots, notification | LOW | LEGACY |

### Infrastructure Dependencies

| Dependency | Components | Severity | Classification |
|-----------|------------|----------|----------------|
| Redis (cache) | services/cache | LOW | LEGACY |
| RabbitMQ (broker) | workers, jobs | LOW | LEGACY |
| Docker | All services | LOW | LEGACY |
| Nginx | api_gateway | LOW | LEGACY |

---

## 11. Legacy Dependency Strategy Matrix

| Dependency | Business Value | Technical Debt | Isolation Effort | Action |
|-----------|----------------|----------------|------------------|--------|
| services.* imports in engine | HIGH | CRITICAL | HIGH | ISOLATE |
| Database (SQLAlchemy) | MEDIUM | HIGH | HIGH | RETAIN_TEMPORARILY |
| Weather/Satellite APIs | HIGH | MEDIUM | HIGH | ISOLATE |
| Payment/Blockchain | LOW | LOW | LOW | REMOVE |
| Redis/RabbitMQ | LOW | MEDIUM | MEDIUM | RETAIN_TEMPORARILY |
| Frontend rendering | LOW | MEDIUM | LOW | LEGACY_ONLY |
| Hard-coded paths | MEDIUM | MEDIUM | LOW | CONFIGURE |
| Implicit imports | LOW | MEDIUM | MEDIUM | DOCUMENT |

---

## 12. Isolation Strategy

### Phase 1: Engine Isolation (Architecture Phase)
```
CURRENT: engine.hydoma → services.*
TARGET:  engine.hydoma → (no service imports)
         services.* → engine.hydoma (one direction OK)
```

1. Move `services.config.settings` to `engine.hydroma/config/`
2. Move `services.territory.models` to `engine.hydra/data/territory.py`
3. Move `services.crops.models` to `engine.hydra/data/crops.py`
4. Move `services.utils` to `engine.hydra/utils/`
5. Move lookup tables to `engine.hydra/data/lookup/`

### Phase 2: API Isolation
```
CURRENT: engine → weather_api_client
TARGET:  evidence_engine → data_adapter → weather_api_client
                        → satellite_adapter → satellite_api_client
```

Create adapter layer that isolates external API calls.

### Phase 3: Database Isolation
```
CURRENT: services.* → sqlalchemy (direct)
TARGET:  services.* → repository → sqlalchemy (abstracted)
```

Use repository pattern to separate business logic from data access.

---

## 13. Priority Ranking

| Priority | Dependency | Reason | Timeline |
|----------|------------|--------|----------|
| P0 | Engine → services imports | Architectural violation | Phase 1 |
| P0 | AI → services imports | Safety concern | Phase 1 |
| P1 | Database ORM coupling | Maintainability | Phase 2 |
| P1 | External API integration | Reliability | Phase 2 |
| P2 | Hard-coded paths | Portability | Phase 2 |
| P2 | Frontend rendering | Separation of concerns | Phase 3 |
| P3 | Messaging/Queue | Infrastructure | Phase 3 |
| P3 | Payment/Blockchain | Out of scope | Phase 3 |

---

## 14. Risk Assessment

| Dependency | Risk Level | Impact | Mitigation |
|-----------|-----------|--------|-----------|
| Engine → services | CRITICAL | Architecture purity | Must fix |
| Database | HIGH | Testability, deployment | Abstract layer |
| External APIs | MEDIUM | Availability, rate limits | Adapter isolation |
| Caching | LOW | Performance | Acceptable |
| Queuing | LOW | Reliability | Acceptable |
| Frontend rendering | LOW | Separation | Acceptable |

---

## 15. Legacy Dependency Count

| Type | Count |
|------|-------|
| Engine → Service dependencies | 5 |
| AI → Application dependencies | 2 |
| Service → Database dependencies | 15 |
| Service → External API | 8 |
| Implicit/Environment assumptions | 4 |
| Service duplicates | 6 |
| **Total** | **36** |

---

*See also: 10-HYDROMA-FORENSICS.md, 11-CPP-PYTHON-BOUNDARY.md, 13-SERVICE-ASSET-MAP.md, 14-SERVICE-CONSOLIDATION-ANALYSIS.md*