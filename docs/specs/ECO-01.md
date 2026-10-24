ECO-01 — KNOWLEDGE, SCIENTIFIC & TECHNOLOGY FORENSICS
Document ID: ECO-01-KNOWLEDGE-SCIENCE-TECH-FORENSICS
 Phase: Post-ECO-00 Forensic Analysis
 Status: EXECUTABLE
 Scope: engine/ + services/ + relevant existing reports
 Primary Goal: Understand, verify, classify, and canonicalize the scientific knowledge, engineering knowledge, algorithms, technologies, domain logic, and reusable assets discovered in ECO-00 before designing the new Eco Nojin architecture.
________________________________________
> **Implementation status (verified 2026-10-11)** — reconciliation of this forensic inventory against the live tree.
> These are *inventory counts*, not requirements; the discovery mission's intent is unchanged.
>
> | ادعای ممیزى (ECO-01 و گزارش‌های پیوسته) | واقعیت کد در ۲۰۲۶-۱۰-۱۱ | شواهد |
> |---|---|---|
> | شمار سرویس‌ها ۷۳ / ۷۵ / ۷۷ (سه گزارش متناقض) | زیربسته‌های عمومی `services/` = **۷۰**؛ مرز بین آن‌ها اکنون با سیاست داده‌محور اعتبارسنجی می‌شود | `List-ChildItem services`؛ `tools/check_service_boundaries.py` |
> | ۲۲ مدلٔ CANON | رجیستری **۷۰** مدل دارد، از این میان **۲۲** مدل کارت دارند (۴۸ بدون کارت؛ ۱۴ کارت `S-0xx` بدون مدل ثبت‌شده) | `engine/models/registry.py::status_summary()` → `models: 70, with_card: 22, cards_without_a_registered_model: 14` |
> | موتورها به‌صورت قرارداد بودند، پیاده‌سازی نه | Engine Gateway (`engine/gateway/`)، Evidence (`engine/evidence/`)، Knowledge (`engine/knowledge/`)، Tasmimyar (`engine/tasmimyar/`) و Decision Adjacent modules اکنون ماژول واقعی هستند | `git ls-files engine/gateway` |
> | مرز سرویس↔سرویس اعتبارسنجی نمی‌شود | اعتبارسنجی می‌شود اما روی درخت زنده **FAIL** است (۲ تخلف) | `tools/check_service_boundaries.py` → `Summary: 140 measured …, 2 violation(s)` |
>
> **خارج از دامنهٔ ECO-01 ولی پیاده‌شده (فقط برای آگاهی):** دفتر کل دوبل‌انتر، کدینگ حساب،
> ارزیابی موجودی/COGS + لات/FEFO، اقلام سفارش + موجودی اتمیک، پرداخت→سفارش، هاب روستایی (RBAC +
> گردشگری)، ثبت مالکیت زمین، مهاجرت‌های Alembic، امنیت HTTP، ۹۱ تست رگرسیون HTTP، ۷۳ تست
> ویژگی‌محور پول و شتاب‌دهی Numba.
________________________________________
 1. MISSION
ECO-00 established the initial technical and forensic state of the transferred engine/ and services/.
ECO-01 must now answer a deeper question:
What knowledge, science, technology, algorithms, models, domain logic, research assets, and reusable capabilities actually exist inside the transferred codebase, what can be trusted, what requires verification, what should be discarded, and what should become part of the new Eco Nojin platform?
This is a knowledge-discovery and canonicalization task.
This is NOT a general implementation task.
The agent must understand the existing assets before recommending how they should be rebuilt into Eco Nojin.
________________________________________
2. ABSOLUTE ARCHITECTURAL PRINCIPLE
The old project is NOT the target architecture.
The old project is an:
Asset Source + Knowledge Source + Forensic Reference
Do not reconstruct the old platform.
Do not preserve architecture merely because it already exists.
Do not assume that an existing class, service, algorithm, database model, API, or module deserves to survive.
The required transformation is:
OLD CODE
   ↓
Understand
   ↓
Extract Knowledge
   ↓
Verify
   ↓
Classify
   ↓
Canonicalize
   ↓
Map to Eco Nojin
   ↓
Build later

Never:
OLD CODE
   ↓
Copy
   ↓
Patch
   ↓
Rebuild old architecture

________________________________________
3. SCOPE
3.1 Primary Scope
Inspect:
engine/
services/

and all ECO-00 reports relevant to understanding these assets.
Read at minimum:
reports/engine-services/INVENTORY.md
reports/engine-services/DEPENDENCY-MAP.md
reports/engine-services/DEPENDENCY_FORENSICS.md
reports/engine-services/ENGINE-AUDIT.md
reports/engine-services/SERVICE-AUDIT.md
reports/engine-services/SCIENTIFIC-MODEL-REGISTRY.md
reports/engine-services/SERVICE-REGISTRY.md
reports/engine-services/LEGACY-DEPENDENCIES.md
reports/engine-services/REPAIR_LOG.md
reports/engine-services/BLOCKERS.md
reports/engine-services/SECURITY-FINDINGS.md
reports/engine-services/TEST-REPORT.md
reports/engine-services/FINAL-VALIDATION.md
reports/engine-services/MACHINE_READABLE_SUMMARY.md

Inspect source code as necessary to verify report claims.
________________________________________
4. FORBIDDEN SCOPE
Do NOT implement or redesign:
frontend/
web/
mobile/
database/
migrations/
smart_contracts/
blockchain/
final API architecture
final OpenAPI
admin UI
CMS
authentication architecture
payment infrastructure
production cloud infrastructure
new external services
new scientific models
new AI models

Do not create a database merely to make legacy services executable.
Do not create APIs merely to expose legacy code.
Do not create UI.
Do not introduce new infrastructure.
________________________________________
5. NO BLIND REFACTORING
During this task:
DISCOVERY > REFACTORING

Do not perform broad refactoring.
Do not reorganize directories merely for aesthetics.
Do not rename large numbers of files.
Do not delete apparently unused scientific code.
Do not simplify formulas.
Do not change thresholds.
Do not change coefficients.
Do not change equations.
Do not change scientific assumptions.
Do not change model behavior.
Do not replace algorithms with "better" algorithms.
If a defect is discovered:
Document
→ classify
→ explain
→ do not silently redesign

Only minimal safe changes required to prevent accidental execution or corruption are permitted.
________________________________________
6. PRIMARY QUESTIONS
ECO-01 must answer all of the following.
Scientific
1.	What scientific models exist?
2.	Which equations are implemented?
3.	Which algorithms are implemented?
4.	Which parameters exist?
5.	Which coefficients exist?
6.	Which thresholds exist?
7.	Which assumptions exist?
8.	Which constraints exist?
9.	Which models depend on which other models?
10.	Which models are deterministic?
11.	Which models are empirical?
12.	Which models are mechanistic?
13.	Which models are statistical?
14.	Which models are hybrid?
15.	Which models are merely heuristics?
16.	Which models have validation evidence?
17.	Which models only have unit tests?
18.	Which models lack scientific validation?
19.	Which models contain undocumented assumptions?
20.	Which models require external scientific review?
Engineering
21.	What engineering calculations exist?
22.	What physical systems are represented?
23.	What numerical methods are used?
24.	What optimization methods exist?
25.	What simulation methods exist?
26.	What calibration mechanisms exist?
27.	What uncertainty mechanisms exist?
28.	What numerical stability risks exist?
29.	What boundary-condition assumptions exist?
30.	What engineering capabilities are reusable?
Domain Knowledge
31.	What domain concepts exist?
32.	What business rules exist?
33.	What terminology exists?
34.	What entities are represented?
35.	What workflows exist?
36.	What roles exist?
37.	What decision logic exists?
38.	What provenance mechanisms exist?
39.	What verification mechanisms exist?
40.	What domain logic is genuinely reusable?
Technology
41.	What technologies are used?
42.	Which technologies are core?
43.	Which are incidental?
44.	Which are obsolete?
45.	Which are duplicated?
46.	Which are tightly coupled to legacy architecture?
47.	Which can be isolated?
48.	Which should be replaced later?
49.	Which technologies create strategic opportunities for Eco Nojin?
________________________________________
7. KNOWLEDGE TAXONOMY
Every meaningful knowledge asset must be classified.
Use one or more of:
SCIENTIFIC_MODEL
ENGINEERING_MODEL
MATHEMATICAL_METHOD
NUMERICAL_METHOD
OPTIMIZATION_METHOD
SIMULATION_METHOD
STATISTICAL_METHOD
MACHINE_LEARNING
AI_METHOD
GIS_METHOD
REMOTE_SENSING_METHOD
DATA_PROCESSING_METHOD
DOMAIN_KNOWLEDGE
AGRICULTURAL_KNOWLEDGE
SOIL_KNOWLEDGE
WATER_KNOWLEDGE
CLIMATE_KNOWLEDGE
LAND_KNOWLEDGE
ECOLOGICAL_KNOWLEDGE
RESTORATION_KNOWLEDGE
CARBON_KNOWLEDGE
MONITORING_KNOWLEDGE
LOCAL_KNOWLEDGE
EXPERIMENTAL_KNOWLEDGE
RESEARCH_HYPOTHESIS
BUSINESS_RULE
WORKFLOW
PROVENANCE_RULE
GOVERNANCE_RULE
SECURITY_KNOWLEDGE
INFRASTRUCTURE_TECHNOLOGY
INTEGRATION_TECHNOLOGY
UNKNOWN

________________________________________
8. SCIENTIFIC STATUS TAXONOMY
Every scientific model must receive a scientific status.
Use exactly one primary status:
CODE_ONLY
IMPLEMENTATION_VERIFIED
MATHEMATICALLY_VERIFIED
SCIENTIFICALLY_SUPPORTED
SCIENTIFICALLY_VALIDATED
PRODUCTION_VALIDATED
EXPERIMENTAL
REQUIRES_SCIENTIFIC_REVIEW
UNSUPPORTED
UNKNOWN

Do NOT call a model SCIENTIFICALLY_VALIDATED merely because a unit test passed.
________________________________________
9. NOVELTY TAXONOMY
Do not claim that anything is novel merely because it appears unusual.
Use:
KNOWN
KNOWN_APPLICATION
MODEL_ADAPTATION
NOVEL_INTEGRATION_CANDIDATE
NOVEL_METHOD_CANDIDATE
RESEARCH_HYPOTHESIS
UNKNOWN_NOVELTY

Novelty requires prior-art research later.
Do not use:
INVENTION
PATENTABLE
ORIGINAL
NOVEL
BREAKTHROUGH

unless supported by actual evidence.
________________________________________
10. SCIENTIFIC MODEL FORENSICS
For every significant model, extract:
model_id
model_name
domain
purpose
scientific_basis
equations
variables
parameters
coefficients
thresholds
units
assumptions
constraints
boundary_conditions
initial_conditions
algorithm
numerical_method
input_data
output_data
uncertainty
calibration
validation
known_limitations
failure_modes
dependencies
source_code
tests
scientific_references
provenance
current_status
recommended_future_status

If any item is unknown:
UNKNOWN

Do not invent missing information.
________________________________________
11. EQUATION FORENSICS
For every non-trivial equation found:
1.	Extract the equation.
2.	Identify every variable.
3.	Identify every parameter.
4.	Identify every coefficient.
5.	Identify units.
6.	Identify dimensional relationships.
7.	Identify assumptions.
8.	Identify implementation location.
9.	Compare implementation with the documented equation.
10.	Record discrepancies.
Required distinction:
Equation Exists
≠
Equation Correctly Implemented
≠
Equation Scientifically Appropriate

If the equation cannot be reconstructed confidently:
EQUATION_STATUS = INCOMPLETE

Do not reverse-engineer a scientific formula by guessing.
________________________________________
12. UNIT AND DIMENSIONAL ANALYSIS
Perform deeper unit analysis than ECO-00.
For every significant scientific calculation verify:
input units
→ conversion
→ internal units
→ calculation
→ output units

Check:
temperature
rainfall
evapotranspiration
soil moisture
salinity
pressure
flow
area
volume
distance
slope
elevation
time
radiation
energy
carbon
concentration

Record:
UNIT_STATUS =
CONSISTENT
CONVERSION_REQUIRED
INCONSISTENT
UNKNOWN

Do not silently modify units.
________________________________________
13. MODEL DEPENDENCY GRAPH
Build a scientific dependency graph.
Example:
Climate Data
    ↓
Radiation
    ↓
ET0
    ↓
Water Demand
    ↓
Irrigation Requirement
    ↓
Agricultural Decision

Another:
DEM
 ↓
Terrain Analysis
 ↓
Slope / Aspect
 ↓
Runoff
 ↓
Watershed Analysis
 ↓
Water Structure Decision

Another:
Soil Properties
 ↓
Salinity
 ↓
Crop Constraints
 ↓
Soil Management
 ↓
Agricultural Decision

Identify:
direct dependencies
indirect dependencies
circular dependencies
hidden dependencies
legacy dependencies
external dependencies
scientific assumptions

________________________________________
14. SCIENTIFIC MODEL QUALITY MATRIX
Create a matrix:
Model	Code	Math	Units	Scientific Basis	Validation	Uncertainty	Production Status
Use:
PASS
PARTIAL
FAIL
UNKNOWN

Do not convert UNKNOWN into PASS.
________________________________________
15. SCIENTIFIC MODEL DEEP REVIEW
At minimum deeply review the models already identified by ECO-00:
AUDIT-MODEL-001 Penman-Monteith ET0
AUDIT-MODEL-002 Climate Data Assimilation
AUDIT-MODEL-003 Hargreaves ET0
AUDIT-MODEL-004 Radiation
AUDIT-MODEL-005 SCS-CN runoff
AUDIT-MODEL-006 Darcy groundwater
AUDIT-MODEL-007 Soil salinity
AUDIT-MODEL-009 Slope-aspect
AUDIT-MODEL-010 Terrain analysis
AUDIT-MODEL-011 Surface water

For models marked "verified" by ECO-00, independently verify the evidence supporting that status.
For models marked "requiring review", identify precisely why.
________________________________________
16. HYDROMA FORENSICS
Hydroma receives special treatment.
Inspect:
engine/hydroma/
engine/hydroma/cpp_bridge/
engine/hydroma/generative_ai/

and all relevant dependencies.
Determine:
Hydroma scientific core
Hydroma numerical core
Hydroma data layer
Hydroma AI layer
Hydroma integration layer
Hydroma legacy coupling

The target conceptual boundary is:
Hydroma
    ↓
Scientific Computation

not:
Hydroma
    ↓
Application Services

Any dependency from scientific engine code into application/service architecture must be identified.
________________________________________
17. CPP / PYTHON FORENSICS
Inspect the C++/Python boundary.
Determine:
C++ responsibilities
Python responsibilities
data crossing boundary
serialization
memory ownership
error handling
type conversion
unit conversion
performance-critical paths
fallback behavior
ABI assumptions
version assumptions

Do not rewrite the C++ layer during ECO-01.
Produce a recommendation:
KEEP
KEEP_WITH_REFACTOR
REIMPLEMENT_LATER
DEPRECATE
UNKNOWN

________________________________________
18. AI FORENSICS
Inspect existing AI/ML/generative components.
Determine:
what AI actually does
what inputs it receives
what outputs it produces
whether outputs affect scientific calculations
whether it introduces hidden assumptions
whether it generates formulas
whether it generates parameters
whether it generates thresholds
whether it makes decisions
whether it depends on external providers

Classify each AI capability:
INTERPRETATION
CLASSIFICATION
PREDICTION
RECOMMENDATION
GENERATION
SCIENTIFIC_ANALYSIS
ORCHESTRATION
LEGACY_SUPPORT
UNKNOWN

Critical rule:
AI must not silently become the scientific authority.
If AI influences scientific output, document the exact control boundary.
________________________________________
19. SERVICE FORENSICS
Use the ECO-00 service registry as the starting point.
For every service determine:
purpose
domain
real business value
domain entities
business rules
workflows
inputs
outputs
scientific dependencies
data dependencies
external dependencies
legacy dependencies
security dependencies
test coverage
reuse value
architectural value
duplication
merge candidates
obsolescence

Do NOT rebuild services.
The goal is to identify:
REUSABLE_DOMAIN_LOGIC
REUSABLE_SCIENTIFIC_LOGIC
REUSABLE_WORKFLOW
REUSABLE_SECURITY_PRIMITIVE
REUSABLE_DATA_CONCEPT
REUSABLE_GOVERNANCE_LOGIC
REUSABLE_INTEGRATION
LEGACY_ONLY
DUPLICATE
OBSOLETE
UNKNOWN

________________________________________
20. SERVICE CONSOLIDATION ANALYSIS
The existing number of services must NOT be treated as the target architecture.
Analyze possible consolidation.
For each service answer:
Should this become a module?
Should this become a bounded context?
Should this become a domain service?
Should this become part of another service?
Should this remain independent?
Should this disappear?

Do not make final architecture implementation changes.
Produce recommendations only.
________________________________________
21. KNOWLEDGE GRAPH EXTRACTION
Identify important concepts and relationships.
At minimum inspect:
Territory
Land
Soil
Water
Climate
Agriculture
Ecosystem
Carbon
Monitoring
Knowledge
Observation
Measurement
Model
Evidence
Research
Project
Decision
Workflow
User
Organization
Service

Find existing representations of these concepts.
Identify:
duplicate concepts
conflicting definitions
missing concepts
implicit concepts
legacy-only concepts
high-value canonical concepts

________________________________________
22. DANESHYAR COMPATIBILITY ANALYSIS
Do not implement Daneshyar.
Analyze whether existing knowledge structures can support:
Knowledge
Observation
Measurement
Local Knowledge
Expert Opinion
Scientific Evidence
Research Project
Hypothesis
Experiment
Monitoring
Result
Provenance
Confidence
Validation

Determine which existing assets can be reused later.
Important:
Local Knowledge
≠
Scientific Fact

Every knowledge type must preserve provenance and epistemic status.
________________________________________
23. TASIMYAR COMPATIBILITY ANALYSIS
Do not implement Tasmimyar.
Determine whether existing services/engine outputs can eventually support:
Current State
Problem
Options
Scenario
Consequence
Risk
Recommendation
Rationale
Confidence
Uncertainty
Evidence

Identify what is missing.
Do not invent decision rules.
________________________________________
24. EVIDENCE ENGINE COMPATIBILITY
Analyze whether current assets can support automatic evidence extraction from:
satellite
climate
weather
soil
water
land cover
vegetation
remote sensing
historical observations
field monitoring
scientific literature
local knowledge

Do not integrate external providers during ECO-01.
Instead identify:
required evidence types
required metadata
required spatial resolution
required temporal resolution
processing requirements
quality-control requirements
provenance requirements
license requirements

________________________________________
25. RESEARCH GAP DISCOVERY
Identify research gaps revealed by the codebase.
A research gap may be:
missing model
missing coupling
missing data
missing validation
missing uncertainty
missing local adaptation
missing temporal dynamics
missing spatial dynamics
missing feedback loop
missing decision layer
missing monitoring loop
missing scientific integration

Potential ideas may be recorded, but MUST be classified as hypotheses.
Use:
KNOWN
EXTENSION
NOVEL_INTEGRATION_CANDIDATE
NOVEL_METHOD_CANDIDATE
RESEARCH_HYPOTHESIS
UNKNOWN

No novelty claims.
________________________________________
26. TECHNOLOGY LANDSCAPE
Inventory technology categories.
At minimum:
C++
Python
NumPy
SciPy
Pydantic
GIS
Raster Processing
Vector Processing
Remote Sensing
Numerical Computing
Optimization
Machine Learning
AI
Databases
Caching
Messaging
Authentication
Security
Blockchain
Cryptography
Monitoring
Data Formats

For each:
current_usage
importance
quality
technical_debt
legacy_coupling
replacement_risk
strategic_value

________________________________________
27. STRATEGIC TECHNOLOGY CLASSIFICATION
Every technology should be placed into:
CORE
IMPORTANT
OPTIONAL
RESEARCH
LEGACY
REMOVE
UNKNOWN

Do not select replacement technologies merely because they are fashionable.
Technology choices must follow product and scientific requirements.
________________________________________
28. SCIENTIFIC KNOWLEDGE SOURCES
For important scientific claims, identify authoritative references where possible.
Prioritize:
peer-reviewed literature
recognized scientific institutions
official standards
official scientific datasets
recognized engineering references
government scientific agencies
international scientific organizations

Do not rely on random blogs for scientific validation.
Do not copy copyrighted material.
Record citation/provenance information, not large copied passages.
________________________________________
29. EXTERNAL RESEARCH RULE
External research is allowed during this task for:
scientific verification
algorithm verification
technology verification
standards
model definitions
known limitations
prior art
dataset identification
scientific terminology

External research must NOT be used to justify arbitrary architecture decisions without evidence.
Record important sources.
________________________________________
30. PROVENANCE REQUIREMENT
Every significant extracted knowledge asset must have:
source
source_type
source_location
code_location
evidence
confidence
status
review_required

If the source is unknown:
source = UNKNOWN

Never invent provenance.
________________________________________
31. CONFIDENCE MODEL
Use qualitative confidence:
HIGH
MEDIUM
LOW
UNKNOWN

Confidence must refer to evidence quality, not personal intuition.
Example:
MODEL_IMPLEMENTATION_CONFIDENCE = HIGH
SCIENTIFIC_VALIDATION_CONFIDENCE = LOW

These are different dimensions.
________________________________________
32. REUSABILITY SCORE
For each major asset evaluate:
Scientific Value
Domain Value
Technical Quality
Independence
Testability
Documentation Quality
Strategic Value
Migration Complexity
Legacy Coupling

Do not collapse all dimensions into one arbitrary numerical score unless justified.
Prefer qualitative classification:
HIGH_VALUE
MEDIUM_VALUE
LOW_VALUE
REFERENCE_ONLY
LEGACY_ONLY

________________________________________
33. CANONICAL ASSET DEFINITION
For every high-value asset define a future canonical identity.
Example:
Asset:
ET0 Calculation

Current:
multiple implementations

Canonical candidate:
HYDROMA-CLIMATE-ET0

Status:
CANDIDATE

Scientific basis:
...
Implementation:
...

Future role:
Hydroma Engine

Legacy implementations:
...

Do not implement the canonical architecture yet.
________________________________________
34. DUPLICATE DETECTION
Look for duplicate:
models
calculators
entities
services
algorithms
schemas
rules
utilities
AI wrappers
data processors

For each duplicate determine:
same meaning
same mathematics
same domain
different assumptions
different units
different precision
different purpose

Do not merge automatically.
________________________________________
35. LEGACY DEPENDENCY ANALYSIS
Pay special attention to:
engine → services
services → database
services → frontend
AI → application services
scientific code → legacy APIs
legacy wrappers
implicit imports
environment assumptions

Every legacy dependency must be classified:
REMOVE
ISOLATE
REPLACE
RETAIN_TEMPORARILY
UNKNOWN

________________________________________
36. SCIENTIFIC INTEGRITY RULES
The agent MUST NOT:
invent formulas
invent coefficients
invent thresholds
invent weights
invent datasets
invent validation results
invent scientific references
invent calibration
invent uncertainty
invent experimental outcomes

If information is unavailable:
UNKNOWN

If scientific conflict exists:
SCIENTIFIC_CONFLICT

and document it.
Never silently choose one interpretation.
________________________________________
37. NO SCIENTIFIC DRIFT
Do not modify scientific behavior merely to make tests pass.
If:
test expectation
≠
scientific specification

record the conflict.
Required path:
Conflict
→ Documentation
→ Scientific Review Candidate
→ Future Decision

________________________________________
38. OUTPUT FILES
Create:
reports/eco-01/

with the following files:
00-FINAL-VALIDATION.md
01-KNOWLEDGE-INVENTORY.md
02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md
03-ENGINEERING-KNOWLEDGE-REGISTRY.md
04-ALGORITHM-REGISTRY.md
05-DOMAIN-KNOWLEDGE-REGISTRY.md
06-TECHNOLOGY-REGISTRY.md
07-MODEL-QUALITY-MATRIX.md
08-EQUATION-AND-UNIT-FORENSICS.md
09-SCIENTIFIC-DEPENDENCY-GRAPH.md
10-HYDROMA-FORENSICS.md
11-CPP-PYTHON-BOUNDARY.md
12-AI-FORENSICS.md
13-SERVICE-ASSET-MAP.md
14-SERVICE-CONSOLIDATION-ANALYSIS.md
15-DANESHYAR-COMPATIBILITY.md
16-TASMIMYAR-COMPATIBILITY.md
17-EVIDENCE-ENGINE-COMPATIBILITY.md
18-RESEARCH-GAPS.md
19-TECHNOLOGY-STRATEGY.md
20-CANONICAL-ASSETS.md
21-DUPLICATION-ANALYSIS.md
22-LEGACY-DEPENDENCY-STRATEGY.md
23-SCIENTIFIC-REVIEW-QUEUE.md
24-UNKNOWN-AND-CONFLICTS.md
25-RECOMMENDED-NEXT-PHASE.md

________________________________________
39. CANONICAL ASSET REGISTRY
Create a structured registry containing at minimum:
asset_id
asset_name
asset_type
domain
current_location
knowledge_status
scientific_status
technical_status
provenance
confidence
reuse_value
legacy_coupling
future_role
recommended_action
review_required

Possible recommended actions:
CANONICALIZE
PORT
REIMPLEMENT
ISOLATE
MERGE
DEPRECATE
RESEARCH
VALIDATE
REFERENCE_ONLY
REJECT
UNKNOWN

________________________________________
40. SCIENTIFIC REVIEW QUEUE
Create a prioritized scientific review queue.
Priority:
P0 = could invalidate important downstream results
P1 = important scientific uncertainty
P2 = important quality/validation gap
P3 = improvement

At minimum evaluate:
Climate Data Assimilation
Radiation
Surface Water
Penman-Monteith
Hargreaves
SCS-CN
Darcy
Soil Salinity
Terrain Analysis
Slope/Aspect

________________________________________
41. RESEARCH GAP FORMAT
For each research candidate:
Research ID:
Problem:
Existing Knowledge:
Current Implementation:
Known Limitation:
Gap:
Hypothesis:
Potential Variables:
Potential Data:
Potential Experiment:
Potential Validation:
Novelty Status:
Confidence:
Risk:
Next Research Action:

Do not turn research hypotheses into production code.
________________________________________
42. DANESHYAR KNOWLEDGE TYPES
Explicitly evaluate support for:
OBSERVATION
MEASUREMENT
LOCAL_KNOWLEDGE
TRADITIONAL_KNOWLEDGE
EXPERT_OPINION
SCIENTIFIC_EVIDENCE
MODEL_OUTPUT
INFERENCE
HYPOTHESIS
EXPERIMENTAL_RESULT

The system must eventually distinguish:
Observation ≠ Evidence
Evidence ≠ Causality
Model Output ≠ Fact
Prediction ≠ Measurement
Inference ≠ Observation

________________________________________
43. FUTURE LEARNING LOOP
Document whether current assets can support the future cycle:
User
 ↓
Local Knowledge
 ↓
Observation
 ↓
Evidence
 ↓
Hydroma
 ↓
Analysis
 ↓
Tasmimyar
 ↓
Decision
 ↓
Real-world Action
 ↓
Monitoring
 ↓
Observed Outcome
 ↓
Research
 ↓
Validation
 ↓
Model Version

Important:
Automatic model modification is forbidden.
Future model evolution must follow:
Observation
→ Research
→ Validation
→ Versioning
→ Approval
→ Production

________________________________________
44. SOIL RESTORATION RESEARCH ASSET CHECK
Because soil-specific biological/material formulation is potentially a high-value research domain, inspect existing assets for:
soil diagnosis
soil classification
salinity
pH
organic matter
nutrients
CEC
moisture
bulk density
carbon
material properties
biological inputs
organic amendments
natural materials
formulation logic
application rate
application timing
crop response
water response
monitoring
experimental results

If proprietary formulations or potentially patentable methods are discovered:
DO NOT PUBLICLY DISCLOSE FORMULAS

Record only:
PROPRIETARY_ASSET_DETECTED

and identify the file/location privately in the report.
Do not reproduce sensitive formulas in broad reports.
________________________________________
45. SATELLITE AND MONITORING RESEARCH ASSET CHECK
Identify existing capabilities related to:
vegetation
surface water
land cover
temperature
rainfall
soil moisture
drought
agricultural activity
historical change
remote sensing
GIS
field monitoring

Do not implement provider integrations.
Determine what an eventual Evidence Engine would need.
________________________________________
46. PERFORMANCE KNOWLEDGE
Identify performance-sensitive assets:
C++ kernels
raster operations
large arrays
simulation loops
optimization loops
GIS processing
remote sensing processing
ML inference
large historical datasets

Classify:
CPU_BOUND
MEMORY_BOUND
IO_BOUND
GPU_CANDIDATE
DISTRIBUTION_CANDIDATE
UNKNOWN

Do not optimize prematurely.
________________________________________
47. SECURITY KNOWLEDGE
Identify reusable security primitives separately from legacy application architecture.
Look for:
authentication primitives
authorization concepts
data classification
provenance
audit logging
validation
input sanitization
privacy controls
cryptographic utilities

Do not build final identity/security architecture.
Only extract reusable knowledge.
________________________________________
48. ACCEPTANCE CRITERIA
ECO-01 is complete only when:
Knowledge
●	[ ] Major knowledge assets identified
●	[ ] Scientific knowledge classified
●	[ ] Engineering knowledge classified
●	[ ] Domain knowledge classified
●	[ ] Technology knowledge classified
●	[ ] Unknowns recorded
Science
●	[ ] All ECO-00 models reviewed
●	[ ] Scientific status independently assessed
●	[ ] Equations extracted where possible
●	[ ] Units reviewed
●	[ ] Assumptions documented
●	[ ] Validation evidence classified
●	[ ] Scientific conflicts recorded
●	[ ] Scientific review queue created
Hydroma
●	[ ] Core boundaries identified
●	[ ] C++/Python responsibilities mapped
●	[ ] AI coupling analyzed
●	[ ] Legacy coupling analyzed
●	[ ] Canonical Hydroma assets identified
Services
●	[ ] Every service mapped to reusable knowledge/assets
●	[ ] Duplicates identified
●	[ ] Merge candidates identified
●	[ ] Legacy-only services identified
●	[ ] Future domain candidates identified
Daneshyar
●	[ ] Knowledge compatibility analyzed
●	[ ] Local knowledge model compatibility analyzed
●	[ ] Research project compatibility analyzed
●	[ ] Provenance compatibility analyzed
Tasmimyar
●	[ ] Decision-support inputs identified
●	[ ] Scientific outputs mapped
●	[ ] Uncertainty requirements identified
●	[ ] Missing decision capabilities identified
Evidence
●	[ ] Evidence requirements identified
●	[ ] Satellite/monitoring capabilities mapped
●	[ ] Provenance requirements identified
●	[ ] Data quality requirements identified
●	[ ] Licensing concerns identified
Research
●	[ ] Research gaps identified
●	[ ] Hypotheses separated from facts
●	[ ] Novelty claims avoided without prior art
●	[ ] High-value research candidates prioritized
Architecture preparation
●	[ ] Canonical assets identified
●	[ ] Legacy assets isolated conceptually
●	[ ] No legacy architecture reconstructed
●	[ ] Next phase defined from evidence
________________________________________
49. STOP CONDITIONS
Stop only the affected analysis and document the issue if:
critical file is unreadable
scientific meaning cannot be determined
code is corrupted
provenance cannot be established
multiple interpretations materially change conclusions

Do not stop the entire task unless execution itself is impossible.
Use:
BLOCKED

only when the missing information prevents meaningful completion.
________________________________________
50. REQUIRED FINAL REPORT
reports/eco-01/00-FINAL-VALIDATION.md
must contain:
Execution Metadata
Scope
Files Inspected
Knowledge Assets Found
Scientific Models
Engineering Models
Algorithms
Domain Knowledge
Technology Inventory
Hydroma Findings
C++/Python Findings
AI Findings
Service Asset Findings
Daneshyar Compatibility
Tasmimyar Compatibility
Evidence Engine Compatibility
Research Gaps
Canonical Assets
Scientific Review Queue
Unknowns
Conflicts
Legacy Dependencies
Security Findings
Performance Findings
Recommended Next Phase
Final Status
Machine-Readable Summary

________________________________________
51. FINAL STATUS
Use exactly one:
READY_FOR_ARCHITECTURE
READY_WITH_LIMITATIONS
REQUIRES_SCIENTIFIC_REVIEW
BLOCKED

Meaning:
READY_FOR_ARCHITECTURE
The knowledge landscape is sufficiently understood to begin architecture design.
READY_WITH_LIMITATIONS
Architecture can begin, but specified knowledge gaps remain.
REQUIRES_SCIENTIFIC_REVIEW
Scientific uncertainty is too important to proceed without specialist review.
BLOCKED
Required information cannot be obtained from the available repository.
________________________________________
52. MACHINE-READABLE SUMMARY
At the end of the final report include:
ECO01_STATUS=
KNOWLEDGE_STATUS=
SCIENTIFIC_STATUS=
ENGINEERING_STATUS=
HYDROMA_STATUS=
CPP_PYTHON_STATUS=
AI_STATUS=
SERVICES_STATUS=
DANESHYAR_COMPATIBILITY=
TASMIMYAR_COMPATIBILITY=
EVIDENCE_ENGINE_COMPATIBILITY=
CANONICAL_ASSETS_COUNT=
SCIENTIFIC_MODELS_COUNT=
RESEARCH_GAPS_COUNT=
SCIENTIFIC_REVIEW_ITEMS=
CRITICAL_UNKNOWN_COUNT=
CRITICAL_CONFLICT_COUNT=
LEGACY_DEPENDENCIES_COUNT=
SECURITY_CRITICAL_FINDINGS=
FINAL_STATUS=

________________________________________
53. FINAL PRINCIPLE
The agent must remember:
We are not trying to save the old platform. We are trying to discover what is valuable inside it.
And:
Code is not automatically knowledge.
And:
A passing test is not automatically scientific validation.
And:
An existing algorithm is not automatically a good algorithm.
And:
A combination of existing models is not automatically a novel invention.
And:
Unknown must remain UNKNOWN until evidence resolves it.
And:
Scientific intelligence must remain traceable from source to decision.
The desired future chain is:
Knowledge
   ↓
Evidence
   ↓
Science
   ↓
Model
   ↓
Simulation
   ↓
AI Analysis
   ↓
Decision
   ↓
Action
   ↓
Monitoring
   ↓
Research
   ↓
Validation
   ↓
Improved Knowledge

ECO-01 must prepare the evidence required to build that chain correctly.
________________________________________
54. DO NOT BUILD THE FUTURE YET
This task ends with knowledge.
Not with:
frontend
database
API
smart contracts
UI
new models
new AI

Those come later.
First:
Understand.
Verify.
Classify.
Canonicalize.
Then Build.

END OF ECO-01

