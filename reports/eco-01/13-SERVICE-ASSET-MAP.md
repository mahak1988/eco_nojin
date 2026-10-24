# ECO-01 Service Asset Map

**Document ID:** ECO-01-13-SERVICE-ASSET-MAP  
**Scope:** services/ directory - all microservices  
**Purpose:** Map every service to reusable knowledge/assets and classify reuse value

---

## 1. Service Registry Overview

**Total Services:** 73 directories in services/

Services identified as having scientific/reusable domain logic:

| Service | Domain | Scientific Dependencies | Reuse Value | Classification |
|---------|--------|------------------------|-------------|----------------|
| models | Scientific | engine/hydroma | HIGH | REUSABLE_SCIENTIFIC_LOGIC |
| science | Scientific | engine/hydroma | HIGH | REUSABLE_SCIENTIFIC_LOGIC |
| carbon | Carbon Cycle | engine/hydoma/carbon | HIGH | REUSABLE_DOMAIN_LOGIC |
| ecosystem | Ecosystem | engine/hydoma/ecosystem | MEDIUM | REUSABLE_DOMAIN_LOGIC |
| land | Land/GIS | engine/land | HIGH | REUSABLE_DOMAIN_LOGIC |
| satellite | Remote Sensing | engine/hydoma/remote_sensing | MEDIUM | DUPLICATE (with science) |
| map_engine | GIS | engine/land | MEDIUM | DUPLICATE |
| design_engine | Engineering | engine/hydoma/watershed | MEDIUM | REUSABLE_DOMAIN_LOGIC |
| simulation | Modeling | engine/hydroama/simulation | HIGH | REUSABLE_SCIENTIFIC_LOGIC |
| irrigation | Agriculture | engine/hydoma/irrigation | HIGH | REUSABLE_DOMAIN_LOGIC |
| climate | Climate | engine/hydoma/climate | HIGH | REUSABLE_DOMAIN_LOGIC |
| soil | Soil | engine/hydoma/soil | HIGH | REUSABLE_DOMAIN_LOGIC |
| territory | Watershed | engine/hydoma/watershed | MEDIUM | REUSABLE_DOMAIN_LOGIC |
| monitoring | Observations | engine/hydoma/observations | MEDIUM | REUSABLE_DATA_CONCEPT |
| knowledge | Knowledge Base | Various | HIGH | REUSABLE_DATA_CONCEPT |
| provenance | Tracking | engine/hydoma/provenance | HIGH | REUSABLE_PROVENANCE_LOGIC |
| daneshyar | Local Knowledge | services/daneshyar | HIGH | REUSABLE_DOMAIN_LOGIC |
| tasmimyar | Decision Support | services/tasmimyar | HIGH | REUSABLE_DECISION_LOGIC |
| reporting | Reports | engine/hydoma/generative_ai | LOW | LEGACY_ONLY |
| bots | Telegram Bot | External API | LOW | LEGACY_ONLY |
| mobile_monitoring | Mobile | External | LOW | DUPLICATE |
| marketplace | Commerce | External | LOW | LEGACY_ONLY |
| finance | Accounting | External | LOW | LEGACY_ONLY |
| commerce | Business | External | LOW | LEGACY_ONLY |
| tourism | Tourism | External | LOW | LEGACY_ONLY |
| livestock | Livestock | engine/hydoma/livestock | LOW | LEGACY_ONLY |
| rangeland | Rangeland | engine/hydoma/rangeland | LOW | REUSABLE_DOMAIN_LOGIC |
| restoration | Restoration | engine/hydoma/restoration | MEDIUM | REUSABLE_DOMAIN_LOGIC |
| mrv | MRV (Measurement) | services/monitoring | MEDIUM | REUSABLE_DATA_CONCEPT |
| blockchain | Blockchain | External | LOW | LEGACY_ONLY |
| wallet | Crypto Wallet | External | LOW | LEGACY_ONLY |
| ecowallet | Eco Wallet | External | LOW | LEGACY_ONLY |
| ledger | Ledger | External | LOW | DUPLICATE |
| ogc | OGC Standards | External | MEDIUM | REUSABLE_INTEGRATION |
| oracle | Oracle/Bridge | External | LOW | DUPLICATE |
| jobs | Background Jobs | celery | LOW | LEGACY_ONLY |
| workers | Workers | celery | LOW | LEGACY_ONLY |
| alerting | Alerting | External | LOW | LEGACY_ONLY |
| analytics | Analytics | services/analytics | MEDIUM | REUSABLE_DATA_CONCEPT |
| notification | Notifications | External | LOW | LEGACY_ONLY |
| content | Content Mgmt | External | LOW | LEGACY_ONLY |
| admin | Admin Panel | External | LOW | LEGACY_ONLY |
| auth | Authentication | External | LOW | LEGACY_ONLY |
| auth_legacy | Legacy Auth | External | LOW | OBSOLETE |
| backup | Backup | External | LOW | LEGACY_ONLY |
| bots | Bot Management | External | LOW | LEGACY_ONLY |
| business_modules | Business Logic | External | LOW | LEGACY_ONLY |
| dispute_resolution | Dispute | External | LOW | LEGACY_ONLY |
| field_monitoring | Field Data | External | LOW | REUSABLE_DOMAIN_LOGIC |
| governance | Governance | External | LOW | LEGACY_ONLY |
| hydroma | Hydroma Service | engine/hydoma | HIGH | REUSABLE_SCIENTIFIC_LOGIC |
| integration | Integration | External | LOW | LEGACY_ONLY |
| inventory | Inventory | External | LOW | LEGACY_ONLY |
| legal | Legal | External | LOW | LEGACY_ONLY |
| logistics | Logistics | External | LOW | LEGACY_ONLY |
| nojin | Nojin Core | services/nojin | HIGH | REUSABLE_GOVERNANCE_LOGIC |
| ogc | OGC Standards | External | MEDIUM | REUSABLE_INTEGRATION |
| privacy | Privacy | External | LOW | LEGACY_ONLY |
| quality | Quality Control | External | LOW | LEGACY_ONLY |
| quality_assurance | QA | External | LOW | LEGACY_ONLY |
| reliability | Reliability | External | LOW | LEGACY_ONLY |
| reporting | Reporting | engine/hydoma/generative_ai | LOW | LEGACY_ONLY |
| security | Security | External | LOW | LEGACY_ONLY |
| sponsors | Sponsors | External | LOW | LEGACY_ONLY |
| supabase | Supabase | External | LOW | LEGACY_ONLY |
| telecom_bot | Telegram Bot | External | LOW | LEGACY_ONLY |
| validation | Validation | services/validation | MEDIUM | REUSABLE_VALIDATION_LOGIC |
| audit | Audit Trail | services/audit | HIGH | REUSABLE_SECURITY_PRIMITIVE |
| data | Data Pipeline | services/data | HIGH | REUSABLE_DATA_CONCEPT |
| data_manual | Manual Data | Manual entry | LOW | LEGACY_ONLY |
| data_sources | Data Sources | External APIs | MEDIUM | REUSABLE_INTEGRATION |
| _contracts | Contracts | services/_contracts | HIGH | REUSABLE_DOMAIN_LOGIC |

---

## 2. Service Classification

### REUSABLE_SCIENTIFIC_LOGIC
Services that encapsulate scientific computation that can be directly used in Eco Nojin:

| Service | Key Assets | Confidence |
|---------|-----------|------------|
| `models` | Model registry, 22 scientific models | HIGH |
| `science` | Scientific analysis pipelines | HIGH |
| `simulation` | Water balance, scenario simulation | HIGH |
| `hydroma` | Engine wrapper for scientific computation | HIGH |

### REUSABLE_DOMAIN_LOGIC
Services with domain-specific business rules:

| Service | Key Assets | Confidence |
|---------|-----------|------------|
| `carbon` | Carbon sequestration, flux | HIGH |
| `ecosystem` | Biodiversity, ecosystem metrics | MEDIUM |
| `land` | Land analysis, GIS operations | HIGH |
| `soil` | Soil analysis, salinity, carbon | HIGH |
| `water` | Hydrology, groundwater | HIGH |
| `climate` | ET0, radiation, climate data | HIGH |
| `watershed` | Watershed design, flow | HIGH |
| `irrigation` | Scheduling, water demand | HIGH |
| `agriculture` | Crop modeling, yield | HIGH |
| `knowledge` | Knowledge base management | HIGH |
| `provenance` | Provenance tracking | HIGH |
| `daneshyar` | Local knowledge management | HIGH |
| `tasmimyar` | Decision support | HIGH |
| `restoration` | Restoration planning | MEDIUM |
| `rangeland` | Rangeland analysis | MEDIUM |

### REUSABLE_DATA_CONCEPTS
Services defining reusable data structures:

| Service | Key Assets | Confidence |
|---------|-----------|------------|
| `monitoring` | Observation data models | MEDIUM |
| `analytics` | Analysis result schemas | MEDIUM |
| `data` | Data pipeline patterns | HIGH |
| `mrv` | MRV (Measurement-Reporting-Verification) models | MEDIUM |
| `validation` | Validation schemas | MEDIUM |

### REUSABLE_SECURITY_PRIMITIVES
| Service | Key Assets | Confidence |
|---------|-----------|------------|
| `audit` | Audit logging, event tracking | HIGH |
| `provenance` | Provenance tracking (overlaps with domain) | HIGH |

### REUSABLE_INTEGRATION
| Service | Key Assets | Confidence |
|---------|-----------|------------|
| `ogc` | OGC standard compliance | MEDIUM |
| `data_sources` | External data source adapters | MEDIUM |
| `_contracts` | Shared service contracts | HIGH |

### LEGACY_ONLY
Services that should not be part of the new architecture:

| Service | Reason |
|---------|--------|
| `admin` | Frontend admin panel |
| `auth` / `auth_legacy` | Authentication is separate concern |
| `backup` | Infrastructure |
| `bots` / `telegram_bot` | Bot interface, not business logic |
| `blockchain` / `wallet` / `ecowallet` | Blockchain not in ECO-01 scope |
| `content` | Content management |
| `legal` | Legal services |
| `marketplace` / `commerce` / `finance` | Commercial features |
| `tourism` | Off-domain |

### OBSOLETE
| Service | Reason |
|---------|--------|
| `auth_legacy` | Superseded by newer auth |

### DUPLICATE
Services that duplicate others:

| Primary | Duplicate | Overlap |
|---------|-----------|---------|
| `satellite` | `science` | Both handle remote sensing |
| `map_engine` | `land` | Both handle GIS |
| `ledger` | `wallet` | Both handle financial ledger |
| `oracle` | `data_sources` | Both handle external data |
| `mobile_monitoring` | `monitoring` | Duplicate field monitoring |

---

## 3. Scientific Model-to-Service Mapping

| Model (from Registry) | Service | Confidence |
|----------------------|---------|------------|
| et0_hargreaves | climate, science, models | HIGH |
| runoff_volume | simulation, design_engine | HIGH |
| check_dam_design | design_engine, water | HIGH |
| contour_trench_design | design_engine | HIGH |
| half_moon_design | design_engine | HIGH |
| crop_yield | agriculture, simulation | HIGH |
| compare_crops | agriculture | HIGH |
| climate_projection | climate, science | HIGH |
| apply_climate_change | climate | HIGH |
| biomass_aboveground | carbon | HIGH |
| biomass_belowground | carbon | HIGH |
| rothc_pools | carbon | HIGH |
| farquhar_photosynthesis | carbon, science | HIGH |
| quantum_efficiency | science, carbon | HIGH |
| carbon_sequestration | carbon | HIGH |
| soil_health_index | soil | HIGH |
| soil_pedotransfer | soil | HIGH |
| salinity_class | soil, water | HIGH |
| leaching_requirement | soil, water | HIGH |
| van_genuchten_theta | soil | HIGH |
| soil_water_retention | soil | HIGH |
| erosion_usle | soil, land | HIGH |

---

## 4. Service Asset Reusability Matrix

| Service | Scientific Logic | Domain Logic | Data Concepts | Integration | Security | Future Role |
|---------|------------------|-------------|---------------|-------------|----------|-------------|
| models | HIGH | HIGH | HIGH | HIGH | LOW | Model registry (canonical) |
| science | HIGH | MEDIUM | MEDIUM | MEDIUM | LOW | Scientific analysis platform |
| simulation | HIGH | MEDIUM | MEDIUM | MEDIUM | LOW | Scenario simulation engine |
| carbon | HIGH | HIGH | MEDIUM | LOW | LOW | Carbon accounting domain |
| soil | HIGH | HIGH | HIGH | MEDIUM | LOW | Soil science domain |
| climate | HIGH | HIGH | HIGH | MEDIUM | LOW | Climate science domain |
| water | HIGH | HIGH | HIGH | MEDIUM | LOW | Hydrology domain |
| land | HIGH | HIGH | HIGH | MEDIUM | LOW | Land intelligence domain |
| irrigation | HIGH | HIGH | MEDIUM | LOW | LOW | Irrigation scheduling domain |
| watershed | HIGH | HIGH | MEDIUM | LOW | LOW | Watershed analysis domain |
| agriculture | HIGH | HIGH | MEDIUM | LOW | LOW | Crop modeling domain |
| knowledge | LOW | HIGH | HIGH | MEDIUM | LOW | Knowledge base management |
| provenance | HIGH | HIGH | HIGH | LOW | HIGH | Traceability system |
| daneshyar | LOW | HIGH | HIGH | LOW | LOW | Local knowledge domain |
| tasmimyar | LOW | HIGH | HIGH | LOW | LOW | Decision support domain |
| audit | LOW | LOW | LOW | LOW | HIGH | Audit/primitives |

---

## 5. Merge Candidates

| Service 1 | Service 2 | Reason | Recommendation |
|-----------|-----------|--------|----------------|
| satellite | science | Both handle remote sensing/indices | MERGE into `science` |
| map_engine | land | Both handle GIS operations | MERGE into `land` |
| ledger | wallet | Both financial tracking | MERGE into `finance` |
| oracle | data_sources | Both external data | MERGE into `data_sources` |
| mobile_monitoring | monitoring | Duplicate field monitoring | MERGE into `monitoring` |
| reporting | generative_ai | Report generation via AI | CONSIDER merge |
| telecom_bot | bots | Both Telegram | MERGE into `bots` |
| climate | weather | Overlapping climate data | CONSIDER merge |
| ecosystem | biodiversity | Overlapping ecological | CONSIDER merge |

---

## 6. High-Value Domain Concepts to Preserve

| Concept | Service | Confidence | Canonical Candidate |
|---------|---------|------------|---------------------|
| Model Registry | models | HIGH | ECO-NOJN-MODEL-REGISTRY |
| Provenance | provenance | HIGH | ECO-NOJN-PROVENANCE |
| Formula Catalog | models | HIGH | ECO-NOJN-FORMULA-CATALOG |
| Watershed Calculator | design_engine / watershed | HIGH | HYDROMA-WATERSHED-CALC |
| ET0 Calculation | climate | HIGH | HYDROMA-CLIMATE-ET0 |
| Water Balance | simulation | HIGH | HYDROMA-SIMULATION-BALANCE |
| Carbon Sequestration | carbon | HIGH | HYDROMA-CARBON-SEQ |
| Soil Health Index | soil | HIGH | HYDROMA-SOIL-HEALTH |
| Salinity Classification | soil | HIGH | HYDROMA-SOIL-SALINITY |
| Van Genuchten | soil | HIGH | HYDROMA-SOIL-VG |
| RUSLE Erosion | soil | HIGH | HYDROMA-SOIL-EROSION |
| Crop Yield | agriculture | HIGH | HYDROMA-AG-CROP-YIELD |
| Irrigation Scheduling | irrigation | HIGH | HYDROMA-IRRIGATION |
| D8 Flow Direction | land | HIGH | HYDROMA-LAND-D8 |
| Terrain Analysis | land | HIGH | HYDROMA-LAND-TERRAIN |

---

*See also: 14-SERVICE-CONSOLIDATION-ANALYSIS.md, 20-CANONICAL-ASSETS.md, 02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md*