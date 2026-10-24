# ECO-01 Service Consolidation Analysis

**Document ID:** ECO-01-14-SERVICE-CONSOLIDATION-ANALYSIS  
**Scope:** services/ directory  
**Purpose:** Analyze consolidation opportunities and future service architecture

---

## 1. Current State

The services/ directory contains 73 service directories. This number is **not** the target architecture. The number reflects a microservices decomposition that may be excessive for the scientific computation domain.

### Service Count by Domain

| Domain | Services | Percentage |
|--------|----------|------------|
| Scientific Core | 4 | 5.5% |
| Climate/Hydrology | 4 | 5.5% |
| Soil/Carbon | 4 | 5.5% |
| Land/GIS | 5 | 6.8% |
| Agriculture/Irrigation | 4 | 5.5% |
| Engineering Design | 3 | 4.1% |
| Data/Monitoring | 6 | 8.2% |
| Knowledge Management | 4 | 5.5% |
| Decision Support | 3 | 4.1% |
| Infrastructure/Utility | 38 | 52.1% |
| External/Integration | 6 | 8.2% |

**Assessment:** 63% of services are infrastructure/utility, not domain logic. Significant consolidation opportunity.

---

## 2. Consolidation Recommendations

### 2.1 Module-Level Consolidation

Services that should become **modules** (not separate services) in the Eco Nojin architecture:

| Current Service | Should Become | Rationale |
|-----------------|---------------|-----------|
| `models` | Module: ScientificModelRegistry | Single source of truth for 22 models |
| `science` | Module: ScienceAnalysis | Shared scientific computation utilities |
| `carbon` | Module: CarbonAccounting | Specific domain (carbon sequestration) |
| `soil` | Module: SoilAnalysis | Specific domain (soil science) |
| `climate` | Module: ClimateAnalysis | Specific domain (climate data) |
| `water` | Module: Hydrology | Specific domain (hydrology) |
| `land` | Module: LandIntelligence | Specific domain (terrain/GIS) |
| `watershed` | Module: WatershedAnalysis | Specific domain (watershed) |
| `irrigation` | Module: IrrigationScheduling | Specific domain (agriculture irrigation) |
| `agriculture` | Module: CropModeling | Specific domain (crop modeling) |
| `simulation` | Module: ScenarioSimulation | Cross-domain scenarios |

### 2.2 Bounded Context Consolidation

Services that should become **bounded contexts**:

| Bounded Context | Services Included | Rationale |
|-----------------|-------------------|-----------|
| **Hydroma Engine** | models, science, simulation, hydroma | Core scientific computation engine |
| **Ecosystem Science** | carbon, soil, climate, water, land | Environmental domain services |
| **Decision Support** | tasmimyar, daneshyar, knowledge | Knowledge and decision management |
| **Field Operations** | monitoring, field_monitoring, mrv | Data collection and monitoring |
| **Infrastructure** | data, data_sources, ogc, _contracts | Technical integration layer |

### 2.3 Individual Service Disposition

| Service | Recommendation | Future Role |
|---------|----------------|-------------|
| `models` | **Become Module** | Scientific model registry with provenance |
| `science` | **Become Module** | Shared scientific computation |
| `simulation` | **Become Module** | Scenario modeling engine |
| `hydroma` | **Merge with models** | Scientific computation facade |
| `carbon` | **Become Module** | Carbon accounting domain |
| `soil` | **Become Module** | Soil analysis domain |
| `climate` | **Become Module** | Climate science domain |
| `water` | **Become Domain Service** | Hydrology service |
| `land` | **Become Module** | Land intelligence domain |
| `watershed` | **Become Module** | Watershed analysis domain |
| `irrigation` | **Become Module** | Irrigation scheduling domain |
| `agriculture` | **Become Module** | Crop modeling domain |
| `ecosystem` | **Become Module** | Ecosystem analysis domain |
| `satellite` | **Merge into science** | Remote sensing capabilities |
| `map_engine` | **Merge into land** | GIS operations consolidation |
| `design_engine` | **Become Module** | Engineering design calculations |
| `monitoring` | **Become Domain Service** | Observation and data collection |
| `field_monitoring` | **Merge into monitoring** | Unify monitoring data |
| `mrv` | **Become Module** | MRV (measurement-reporting-verification) |
| `knowledge` | **Become Domain Service** | Knowledge base management |
| `daneshyar` | **Become Domain Service** | Local knowledge management |
| `tasmimyar` | **Become Domain Service** | Decision support engine |
| `provenance` | **Become Domain Service** | Provenance and traceability |
| `reporting` | **Merge with generative_ai** | Report generation |
| `analytics` | **Become Module** | Analysis and metrics |
| `validation` | **Become Module** | Data validation services |
| `audit` | **Become Domain Service** | Security audit primitives |
| `ogc` | **Become Module** | OGC standards compliance |
| `data` | **Become Domain Service** | Data pipeline management |
| `data_sources` | **Merge with data** | External data source integration |
| `_contracts` | **Become Module** | Shared domain contracts |
| `nojin` | **Become Core Domain Service** | Eco Nojin platform core |
| `bots` | **External Integration** | Bot interface only |
| `telegram_bot` | **Merge into bots** | Single bot service |
| `notification` | **Infrastructure Service** | Notification dispatch |
| `jobs` | **Infrastructure Service** | Background job processing |
| `workers` | **Infrastructure Service** | Worker management |
| `alerting` | **Infrastructure Service** | Monitoring alerts |
| `restoration` | **Become Module** | Restoration planning |
| `rangeland` | **Merge into ecosystem** | Part of ecosystem analysis |
| `livestock` | **LEGACY_ONLY** | Separate domain, not core |
| `blockchain` | **REMOVE** | Not in scope per ECO-01 |
| `wallet` | **REMOVE** | Not in scope |
| `ecowallet` | **REMOVE** | Not in scope |
| `ledger` | **Merge with finance** | Financial ledger |
| `finance` | **LEGACY_ONLY** | Business finance |
| `commerce` | **LEGACY_ONLY** | E-commerce features |
| `marketplace` | **LEGACY_ONLY** | Marketplace features |
| `tourism` | **LEGACY_ONLY** | Off-domain |
| `admin` | **External** | Admin UI only |
| `auth` | **Infrastructure** | Authentication service |
| `auth_legacy` | **REMOVE** | Obsolete |
| `backup` | **Infrastructure** | Backup service |
| `content` | **LEGACY_ONLY** | Content management |
| `legal` | **LEGACY_ONLY** | Legal services |
| `logistics` | **LEGACY_ONLY** | Logistics domain |
| `oracle` | **Merge into data_sources** | External oracle |
| `privacy` | **Infrastructure** | Privacy compliance |
| `quality` | **Become Module** | Quality control |
| `quality_assurance` | **Merge into quality** | Quality standards |
| `reliability` | **Infrastructure** | System reliability |
| `security` | **Infrastructure** | Security service |
| `sponsors` | **LEGACY_ONLY** | Sponsor features |
| `supabase` | **Infrastructure** | Supabase integration |
| `dispute_resolution` | **LEGACY_ONLY** | Business feature |
| `business_modules` | **LEGACY_ONLY** | Generic business logic |
| `integration` | **Infrastructure** | Integration platform |
| `inventory` | **LEGACY_ONLY** | Inventory management |
| `data_manual` | **Merge into data** | Manual data entry |

---

## 3. Future Architecture (Eco Nojin)

### Recommended Service Structure

```
Eco Nojin Platform Services
├── hydroma-engine (Core Scientific Module)
│   ├── Climate Analysis
│   ├── Soil Physics
│   ├── Hydrology
│   ├── Terrain Analysis
│   └── Carbon Accounting
├── ecosystem-science (Domain Module)
│   ├── Carbon Cycle
│   ├── Ecosystem Metrics
│   ├── Soil Health
│   └── Biodiversity
├── land-intelligence (Domain Module)
│   ├── Terrain Analysis
│   ├── Hydrology
│   ├── Land Cover
│   └── Watershed
├── agriculture-intelligence (Domain Module)
│   ├── Crop Modeling
│   ├── Irrigation Scheduling
│   ├── Soil Management
│   └── Growth Monitoring
├── knowledge-base (Domain Service)
│   ├── daneshyar (Local Knowledge)
│   ├── tasmimyar (Decision Support)
│   └── provenance (Traceability)
├── evidence-engine (Domain Service)
│   ├── monitoring
│   ├── satellite data integration
│   └── quality control
├── model-registry (Domain Service)
│   ├── 22 scientific models
│   ├── Fidelity classification
│   └── Validation metadata
├── infrastructure (Technical Services)
│   ├── ogc-standards
│   ├── data-pipeline
│   ├── validation
│   └── audit
├── nojin-core (Platform Core)
│   ├── governance
│   ├── workflow orchestration
│   └── policy management
└── External (Out of Scope)
    ├── auth
    ├── blockchain/wallet
    ├── marketplace/commerce
    └── admin/bots
```

### Module Count Rationale

| Type | Count | Purpose |
|------|-------|---------|
| Domain Modules | 4 | Core scientific domains (hydroma, ecosystem, land, agriculture) |
| Domain Services | 4 | Cross-cutting concerns (knowledge, evidence, models, nojin) |
| Infrastructure Services | 4 | Technical services (ogc, data, validation, audit) |
| External | Variable | Auth, external integrations |

**Total recommended:** ~12 services vs. current 73 (83% reduction)

---

## 4. Consolidation Benefits

| Benefit | Impact | Notes |
|--------|--------|-------|
| Reduced operational complexity | HIGH | Fewer services to deploy/monitor |
| Clearer boundaries | HIGH | Domain vs infrastructure separation |
| Easier development | HIGH | Fewer cross-service calls |
| Better performance | HIGH | In-process calls for domain logic |
| Reduced data consistency issues | HIGH | No distributed transactions |
| Simplified testing | HIGH | Fewer service integration tests |
| Faster CI/CD | MEDIUM | Fewer pipelines |
| Lower cloud costs | MEDIUM | Fewer deployments |

---

## 5. Risks of Consolidation

| Risk | Mitigation |
|------|-----------|
| Monolith if over-consolidated | Use bounded contexts with clear module boundaries |
| Domain coupling | Maintain module-level separation |
| Loss of independent scaling | Keep infrastructure scalable; domain modules scale together |
| Large codebase | Use modular code organization within services |

---

## 6. Migration Path

```
Phase 1: Identify canonical assets (current ECO-01)
    ↓
Phase 2: Isolate scientific computation from services
    ↓
Phase 3: Consolidate modules within bounded contexts
    ↓
Phase 4: Deploy consolidated services gradually
    ↓
Phase 5: Decommission legacy services
```

---

## 7. Merge Priority Matrix

| Priority | Merge Pair | Value | Complexity |
|----------|-----------|-------|------------|
| P0 | satellite → science | HIGH | LOW |
| P0 | map_engine → land | HIGH | LOW |
| P0 | field_monitoring → monitoring | HIGH | LOW |
| P1 | oracle → data_sources | MEDIUM | LOW |
| P1 | ledger → finance | MEDIUM | LOW |
| P1 | mobile_monitoring → monitoring | MEDIUM | LOW |
| P1 | telecom_bot → bots | LOW | LOW |
| P2 | reporting → generative_ai | LOW | MEDIUM |
| P2 | quality_assurance → quality | MEDIUM | LOW |
| P2 | data_manual → data | LOW | MEDIUM |

---

*See also: 13-SERVICE-ASSET-MAP.md, 20-CANONICAL-ASSETS.md, 22-LEGACY-DEPENDENCY-STRATEGY.md*