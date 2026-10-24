ECO-02 — CANONICAL ARCHITECTURE & CORE CONTRACTS
Document ID: ECO-02-CANONICAL-ARCHITECTURE-AND-CORE-CONTRACTS
 Phase: Post-ECO-01 Architecture Definition
 Project: Eco Nojin / اکو نوژین
 Status: EXECUTION INSTRUCTION
 Execution Mode: Autonomous, Evidence-Driven, Architecture-Only
 Primary Repository: New Eco Nojin project
 Source Assets: engine/, services/, and ECO-00/ECO-01 reports
 Previous Phase: ECO-01 — Knowledge, Science & Technology Forensics
 Next Phase: ECO-03 — Detailed Implementation Specifications
________________________________________
1. MISSION
این مرحله وظیفه دارد یافته‌های قطعی و محدودیت‌های ECO-00 و ECO-01 را به یک معماری Canonical، قابل کنترل، قابل آزمون و الزام‌آور برای Eco Nojin تبدیل کند.
هدف این مرحله ساخت محصول نیست.
هدف این مرحله پاسخ قطعی به این سؤال‌هاست:
Eco Nojin دقیقاً از چه لایه‌هایی تشکیل می‌شود؟
مسئولیت هر لایه چیست؟
چه چیزی اجازه دارد با چه چیزی ارتباط داشته باشد؟
کدام دارایی‌های پروژه قدیمی وارد معماری جدید می‌شوند؟
کدام دارایی‌ها فقط Reference هستند؟
قرارداد بین Engine، Knowledge، Evidence، Decision و AI چیست؟
چگونه می‌توان بعداً Database، API، Frontend، Blockchain و سایر اجزا را بدون شکستن هسته علمی اضافه کرد؟
________________________________________
2. ABSOLUTE PRINCIPLE
اصل حاکم این مرحله:
DO NOT BUILD THE PLATFORM. DEFINE THE PLATFORM.
در ECO-02 هیچ implementation محصولی انجام نشود.
این مرحله باید معماری را مشخص کند تا implementation مراحل بعدی مجبور باشد از آن تبعیت کند.
________________________________________
3. AUTHORITATIVE INPUTS
قبل از هر تصمیم معماری، Agent MUST مطالعه کند:
reports/engine-services/*
reports/eco-01/*
engine/*
services/*

به‌خصوص:
reports/eco-01/00-FINAL-VALIDATION.md
reports/eco-01/02-SCIENTIFIC-KNOWLEDGE-REGISTRY.md
reports/eco-01/03-ENGINEERING-KNOWLEDGE-REGISTRY.md
reports/eco-01/04-ALGORITHM-REGISTRY.md
reports/eco-01/07-MODEL-QUALITY-MATRIX.md
reports/eco-01/08-EQUATION-AND-UNIT-FORENSICS.md
reports/eco-01/10-HYDROMA-FORENSICS.md
reports/eco-01/11-CPP-PYTHON-BOUNDARY.md
reports/eco-01/12-AI-FORENSICS.md
reports/eco-01/13-SERVICE-ASSET-MAP.md
reports/eco-01/14-SERVICE-CONSOLIDATION-ANALYSIS.md
reports/eco-01/15-DANESHYAR-COMPATIBILITY.md
reports/eco-01/16-TASMIMYAR-COMPATIBILITY.md
reports/eco-01/17-EVIDENCE-ENGINE-COMPATIBILITY.md
reports/eco-01/18-RESEARCH-GAPS.md
reports/eco-01/19-TECHNOLOGY-STRATEGY.md
reports/eco-01/20-CANONICAL-ASSETS.md
reports/eco-01/21-DUPLICATION-ANALYSIS.md
reports/eco-01/22-LEGACY-DEPENDENCY-STRATEGY.md
reports/eco-01/23-SCIENTIFIC-REVIEW-QUEUE.md
reports/eco-01/24-UNKNOWN-AND-CONFLICTS.md

اگر بین گزارش‌ها تناقض وجود داشت، Agent MUST آن را ثبت کند و حق حل خودسرانه ندارد.
________________________________________
4. CURRENT BASELINE
ECO-01 نتیجه زیر را تثبیت کرده است:
KNOWLEDGE_STATUS=UNDERSTOOD_WITH_LIMITATIONS
SCIENTIFIC_STATUS=MOSTLY_VERIFIED_2_P0_REVIEW_REQUIRED
ENGINEERING_STATUS=PARTIALLY_IMPLEMENTED
HYDROMA_STATUS=CLEAR_BOUNDARIES_SOME_COUPLING
CPP_PYTHON_STATUS=KEEP_WITH_REFACTOR_BUILD_CLEANUP
AI_STATUS=ISOLATED_SAFE_FOR_INTERPRETATION
SERVICES_STATUS=OVERFRAGMENTED_CONSOLIDATION_OPPORTUNITY
DANESHYAR_COMPATIBILITY=PARTIAL
TASMIMYAR_COMPATIBILITY=PARTIAL
EVIDENCE_ENGINE_COMPATIBILITY=PARTIAL
CANONICAL_ASSETS_COUNT=17
SCIENTIFIC_MODELS_COUNT=22
RESEARCH_GAPS_COUNT=11
LEGACY_DEPENDENCIES_COUNT=36
FINAL_STATUS=READY_WITH_LIMITATIONS

این baseline الزام‌آور است مگر اینکه Agent با evidence جدید یک تناقض واقعی کشف کند.
________________________________________
5. FORBIDDEN SCOPE
در ECO-02 موارد زیر ممنوع هستند:
frontend implementation
web application implementation
mobile implementation
database implementation
database migrations
API implementation
OpenAPI implementation
authentication implementation
payment implementation
wallet implementation
smart contract implementation
blockchain implementation
cloud deployment
production infrastructure
production CI/CD
admin UI
CMS implementation
new scientific model implementation
new ML model implementation
new AI model implementation
large dataset acquisition
production deployment
service implementation
service migration
mass refactoring
mass file movement
mass deletion

همچنین Agent نباید:
●	پروژه قدیمی را بازسازی کند
●	architecture قدیمی را به‌عنوان architecture جدید بپذیرد
●	صرفاً به دلیل وجود یک service آن را canonical اعلام کند
●	صرفاً به دلیل وجود یک model آن را scientifically approved اعلام کند
●	عدد 12 را به‌عنوان تعداد قطعی سرویس‌های آینده فرض کند
________________________________________
6. ALLOWED ACTIONS
Agent می‌تواند:
●	source code را مطالعه کند
●	dependency graph را اصلاح کند
●	architecture diagrams ایجاد کند
●	contractها را تعریف کند
●	domain boundaries را مشخص کند
●	interfaceهای مفهومی تعریف کند
●	data semantics را تعریف کند
●	model contracts را مشخص کند
●	knowledge ontology طراحی کند
●	evidence contract طراحی کند
●	uncertainty contract طراحی کند
●	decision contract طراحی کند
●	AI boundary را تعریف کند
●	service bounded contexts را پیشنهاد دهد
●	legacy migration strategy تعریف کند
●	ADR ایجاد کند
●	گزارش و specification تولید کند
هرگونه code change فقط در صورتی مجاز است که:
1.	برای اثبات یک architectural fact ضروری باشد؛
2.	کوچک و قابل بازگشت باشد؛
3.	در ECO-02-REPAIR-LOG.md ثبت شود؛
4.	architecture را به‌صورت مخفیانه تغییر ندهد.
________________________________________
7. CORE ARCHITECTURAL PRINCIPLE
معماری پیشنهادی باید حول این تفکیک شکل بگیرد:
┌──────────────────────────────────────────┐
│              Eco Nojin Platform          │
├──────────────────────────────────────────┤
│ Product / Experience Layer               │
│ Future Frontend / Web / Mobile           │
├──────────────────────────────────────────┤
│ Application & Orchestration Layer        │
├──────────────────────────────────────────┤
│ Decision / Tasmimyar                     │
├──────────────────────────────────────────┤
│ Knowledge / Daneshyar                    │
├──────────────────────────────────────────┤
│ Evidence / Provenance                    │
├──────────────────────────────────────────┤
│ Domain Services                          │
├──────────────────────────────────────────┤
│ Engine Gateway                           │
├──────────────────────────────────────────┤
│ Hydroma Scientific Engine                │
├──────────────────────────────────────────┤
│ C++ Numerical Kernels                    │
└──────────────────────────────────────────┘

این نمودار فقط نقطه شروع است.
Agent MUST آن را بر اساس evidence کامل کند و در صورت نیاز اصلاح کند.
________________________________________
8. CANONICAL LAYER MODEL
برای هر layer موارد زیر باید مشخص شود:
Purpose
Responsibilities
Owns
Reads
Writes
Allowed Dependencies
Forbidden Dependencies
Input Contracts
Output Contracts
Error Model
Uncertainty Model
Provenance Requirements
Security Boundary
Testing Boundary

________________________________________
9. HYDROMA ARCHITECTURE
Hydroma باید به‌عنوان Scientific Computation System تعریف شود، نه یک application service.
معماری پیشنهادی:
Hydroma
├── Scientific Models
├── Numerical Methods
├── Climate
├── Soil
├── Water / Hydrology
├── Agriculture
├── Terrain / Land
├── Carbon / MRV
├── Simulation
├── Optimization
├── Validation
├── Provenance
├── Formula Catalog
└── Numerical Kernels

Hydroma MUST NOT:
depend on database
depend on frontend
depend on HTTP
depend on authentication
depend on payment
depend on wallet
depend on blockchain
depend on application workflow
depend on UI

هر dependency مخالف باید در:
ECO-02-ARCHITECTURE-CONFLICTS.md

ثبت شود.
________________________________________
10. ENGINE GATEWAY
یک مرز مفهومی به نام:
ENGINE GATEWAY

تعریف شود.
وظیفه Gateway:
●	validation قبل از execution
●	model selection
●	model version resolution
●	unit normalization
●	input contract validation
●	execution context
●	provenance propagation
●	uncertainty propagation
●	result normalization
●	error normalization
Gateway نباید منطق علمی را دوباره پیاده‌سازی کند.
اصل:
Gateway ≠ Scientific Engine

________________________________________
11. SCIENTIFIC MODEL CONTRACT
برای تمام مدل‌های علمی و مهندسی، قرارداد Canonical زیر تعریف شود:
model_id
model_version
model_name
model_type
domain
purpose

inputs
input_units
input_constraints

parameters
parameter_units
parameter_constraints

assumptions

equations
algorithms
numerical_methods

outputs
output_units

uncertainty
uncertainty_method

provenance

validation
validation_evidence

applicability_domain
limitations

execution_metadata

هیچ Model نباید بدون مشخص بودن این موارد وارد لایه Decision شود.
________________________________________
12. SCIENTIFIC MATURITY
معماری MUST یک maturity classification مستقل از business status داشته باشد:
S0_UNDERSTOOD_ONLY
S1_CODE_VERIFIED
S2_UNIT_VERIFIED
S3_REFERENCE_CASE_VALIDATED
S4_BENCHMARK_VALIDATED
S5_FIELD_VALIDATED
S6_PRODUCTION_APPROVED

این وضعیت نباید با:
CANONICAL
ACTIVE
ENABLED
AVAILABLE

اشتباه شود.
یک مدل می‌تواند:
CANONICAL + S2

باشد ولی:
NOT_APPROVED_FOR_HIGH_STAKES_DECISION

باشد.
________________________________________
13. SCIENTIFIC REVIEW GATE
مدل‌های زیر باید صراحتاً در architecture دارای review gate باشند:
Climate Data Assimilation
Soil Salinity
Theis
Surface Water

هر مدل دارای:
REQUIRES_SCIENTIFIC_REVIEW

نباید بدون review مناسب به‌عنوان حقیقت قطعی یا recommendation قطعی مصرف شود.
________________________________________
14. UNCERTAINTY AS FIRST-CLASS CONCEPT
Uncertainty نباید metadata تزئینی باشد.
معماری باید مفهوم زیر را تعریف کند:
Uncertainty
├── Input Uncertainty
├── Parameter Uncertainty
├── Model Uncertainty
├── Numerical Uncertainty
├── Measurement Uncertainty
├── Observation Uncertainty
├── Propagated Uncertainty
└── Decision Uncertainty

Agent MUST مشخص کند:
●	uncertainty چگونه وارد مدل می‌شود
●	چگونه propagate می‌شود
●	چگونه گزارش می‌شود
●	چه زمانی قابل محاسبه نیست
●	چگونه confidence از uncertainty جدا می‌شود
اصل:
UNKNOWN ≠ ZERO UNCERTAINTY

عدم وجود uncertainty calculation نباید به‌عنوان certainty تفسیر شود.
________________________________________
15. DANESHYAR ARCHITECTURE
Daneshyar باید یک Knowledge System باشد، نه صرفاً collection از records.
حداقل epistemic classes:
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

هر Knowledge Asset باید قابلیت ثبت موارد زیر را داشته باشد:
knowledge_id
type
content
source
provenance
creator
timestamp
location
domain
epistemic_status
confidence
uncertainty
evidence_links
method
validation_status
version
supersedes

اصل غیرقابل مذاکره:
Local Knowledge is valuable knowledge, but it is not automatically Scientific Fact.
همچنین:
Model Output is not automatically Observation.
و:
AI-generated content is not automatically Evidence.
________________________________________
16. EPISTEMIC STATUS
حداقل وضعیت‌های زیر بررسی و در صورت تأیید canonical شوند:
UNVERIFIED
OBSERVED
MEASURED
REPORTED
EXPERT_ASSERTED
SUPPORTED
VALIDATED
INFERRED
HYPOTHESIS
DISPUTED
REJECTED
SUPERSEDED

Agent MUST مشخص کند:
●	چه کسی status را تعیین می‌کند
●	evidence لازم چیست
●	status چگونه تغییر می‌کند
●	آیا status قابل بازگشت است
●	audit trail چگونه حفظ می‌شود
________________________________________
17. EVIDENCE ARCHITECTURE
Evidence Engine باید از Knowledge Engine متمایز باشد.
مدل مفهومی:
Source
   ↓
Observation / Dataset
   ↓
Evidence Record
   ↓
Quality Assessment
   ↓
Provenance
   ↓
Scientific / Decision Consumption

Evidence باید metadata زیر را پشتیبانی کند:
source_id
source_type
provider
sensor
instrument
location
time
resolution
accuracy
method
processing_history
quality_score
license
access_rights
provenance
version

Satellite evidence باید بتواند مواردی مانند:
sensor
spatial_resolution
temporal_resolution
spectral_information
cloud_cover
processing_level
acquisition_time
license

را نگهداری کند.
________________________________________
18. PROVENANCE
Provenance باید cross-cutting architectural concern باشد.
برای هر خروجی علمی یا تصمیمی باید بتوان مشخص کرد:
Where did the input come from?
Which model was used?
Which version?
Which parameters?
Which assumptions?
Which transformations?
Which evidence?
Which uncertainty?
Which execution?

حداقل زنجیره:
SOURCE
→ OBSERVATION
→ PROCESSING
→ MODEL INPUT
→ MODEL EXECUTION
→ MODEL OUTPUT
→ DECISION INPUT
→ DECISION

هیچ مرحله‌ای نباید بدون provenance ناپدید شود.
________________________________________
19. TASMIMYAR ARCHITECTURE
Tasmimyar نباید صرفاً یک recommendation engine باشد.
Canonical decision structure:
CURRENT_STATE
      ↓
PROBLEM
      ↓
OBJECTIVES
      ↓
CONSTRAINTS
      ↓
OPTIONS
      ↓
SCENARIOS
      ↓
EVIDENCE
      ↓
MODEL_OUTPUTS
      ↓
RISKS
      ↓
UNCERTAINTIES
      ↓
TRADE-OFFS
      ↓
RATIONALE
      ↓
RECOMMENDATION
      ↓
CONFIDENCE / LIMITATIONS

Decision Contract باید حداقل شامل:
decision_id
context
problem
objectives
constraints
options
scenarios
evidence
model_outputs
risks
uncertainties
tradeoffs
recommendation
rationale
confidence
limitations
provenance

اصل:
Tasmimyar MAY recommend. It MUST NOT manufacture scientific evidence.
________________________________________
20. ALTERNATIVES
Decision support نباید به‌طور پیش‌فرض تنها یک گزینه تولید کند.
Architecture باید امکان:
Option A
Option B
Option C
No Action

را داشته باشد.
برای هر option:
expected_benefit
expected_cost
risk
uncertainty
constraints
evidence
model_dependencies

در صورت insufficient evidence، سیستم باید بتواند:
INSUFFICIENT_EVIDENCE

اعلام کند.
________________________________________
21. AI ARCHITECTURE
AI باید در معماری یک capability جدا باشد:
AI
├── Interpretation
├── Explanation
├── Summarization
├── Conversational Assistance
├── Classification
├── Prediction
└── Generation

AI نباید مستقیماً:
modify scientific equations
modify scientific parameters
override model outputs
change provenance
change evidence status
promote hypothesis to fact
declare scientific validity

کند.
مرز:
Scientific Engine
      ↓
Authoritative Scientific Output
      ↓
AI Interpretation
      ↓
Human/User

نه:
AI
 ↓
Scientific Engine

مگر در مواردی که architecture به‌صراحت و با contract مشخص اجازه دهد و AI صرفاً parameter proposal غیرقطعی ارائه کند.
________________________________________
22. AI CONFIDENCE
AI confidence با scientific uncertainty یکی نیست.
Architecture MUST این دو را جدا نگه دارد:
AI Confidence
Scientific Uncertainty
Evidence Quality
Decision Confidence

این چهار مفهوم نباید در یک فیلد عمومی confidence ادغام شوند.
________________________________________
23. SERVICE ARCHITECTURE
73 service موجود نباید به‌صورت مستقیم architecture جدید شوند.
Agent MUST ابتدا bounded contexts را استخراج کند.
برای هر service مشخص شود:
Business Capability
Domain Ownership
Data Ownership
Scientific Responsibility
Dependencies
Reusable Logic
API/Contract
Security Responsibility
State
External Dependencies
Duplicate Candidates
Legacy Status

سپس grouping پیشنهادی ایجاد شود.
نمونه حوزه‌ها برای بررسی:
Water
Land
Agriculture
Climate
Ecosystem
Carbon / MRV
Restoration
Knowledge
Decision
Monitoring
Data / Evidence
Commerce
Projects
Workflow
Notifications

این‌ها مثال هستند و نه تصمیم قطعی.
________________________________________
24. SERVICE COUNT RULE
عدد:
12 services

نباید به‌عنوان requirement پذیرفته شود.
هدف:
Minimum coherent domain architecture
نه:
Minimum number of services.
اگر یک bounded context به modular monolith مناسب‌تر از microservice باشد، باید همین موضوع ثبت شود.
معماری باید ابتدا:
Domain Boundary

را تعیین کند و بعد درباره:
Process Boundary
Deployment Boundary
Service Boundary

تصمیم بگیرد.
________________________________________
25. DOMAIN OWNERSHIP
برای هر domain مشخص شود:
Who owns the concept?
Who owns the data?
Who validates it?
Who may mutate it?
Who may consume it?

هیچ دو domain نباید بدون دلیل مشخص مالک یک مفهوم باشند.
________________________________________
26. ENGINE ↔ SERVICE RULE
اصل بنیادی:
Services may call Engine.
Engine must not depend on Services.

اگر reverse dependency موجود باشد:
ENGINE → SERVICES

باید به:
SERVICE / GATEWAY → ENGINE

تبدیل مفهومی شود.
هر exception باید documented و temporary باشد.
________________________________________
27. ADAPTER POLICY
Adapters ایجادشده در ECO-00:
adapters/

نباید خودکار canonical architecture محسوب شوند.
آنها باید بررسی و یکی از وضعیت‌های زیر را بگیرند:
TRANSITIONAL
CANONICAL
REPLACE
REMOVE_LATER
REFERENCE_ONLY

اگر Adapter فقط برای جدا کردن legacy dependency ایجاد شده، باید به‌عنوان:
TRANSITIONAL EXTRACTION ADAPTER

شناخته شود تا Engine Gateway نهایی آن را بلعیده و پنهان نکند.
________________________________________
28. C++ / PYTHON ARCHITECTURE
مرز C++ و Python باید صریح شود:
Python
├── model orchestration
├── validation
├── units
├── provenance
├── scientific workflow
└── public scientific semantics

C++
├── numerical kernels
├── vectorized computation
├── raster kernels
├── performance-critical operations
└── deterministic low-level computation

Agent MUST تعیین کند:
●	ABI contract
●	supported Python versions
●	supported C++ standard
●	ownership
●	memory model
●	error mapping
●	numerical precision
●	fallback policy
●	build separation
اصل:
C++ optimization must never silently change scientific semantics.
________________________________________
29. NUMERICAL DETERMINISM
برای مدل‌هایی که deterministic هستند باید مشخص شود:
same input
+
same model version
+
same parameters
+
same execution contract
=
same scientific result

در مواردی که deterministic نیستند، علت باید ثبت شود.
________________________________________
30. MODEL REGISTRY
Model Registry باید از Service Registry جدا باشد.
دو مفهوم:
MODEL_ID
SERVICE_ID

نباید یکی شوند.
Model ممکن است توسط چند application/domain مصرف شود.
________________________________________
31. FORMULA REGISTRY
Formula Catalog باید authoritative scientific metadata باشد.
برای هر formula:
formula_id
name
equation
variables
units
assumptions
domain
reference
implementation
validation_status
version

هیچ formula جدیدی در ECO-02 اختراع یا اصلاح نشود.
________________________________________
32. UNIT SYSTEM
Architecture باید یک Unit Policy تعریف کند.
حداقل:
SI canonical units
explicit conversion
unit metadata
dimensional validation

اصل:
A numeric value without a unit is not automatically a valid scientific input.
________________________________________
33. RESEARCH ARCHITECTURE
Research باید از production science جدا باشد.
حداقل lifecycle:
RESEARCH_QUESTION
      ↓
HYPOTHESIS
      ↓
METHOD
      ↓
EXPERIMENT
      ↓
RESULT
      ↓
VALIDATION
      ↓
REVIEW
      ↓
CANDIDATE_MODEL
      ↓
CANONICAL_MODEL

هیچ Research Candidate نباید خودکار وارد production engine شود.
________________________________________
34. SCIENTIFIC REVIEW BOARDARY
Architecture باید محل اتصال آینده به scientific review را مشخص کند.
این review ممکن است شامل:
domain scientist
hydrologist
soil scientist
agronomist
climate scientist
GIS specialist
statistician
numerical methods specialist

باشد، ولی در ECO-02 هیچ فرد یا سازمانی به‌عنوان reviewer واقعی جعل نشود.
________________________________________
35. EVIDENCE QUALITY
Evidence Quality باید از Scientific Validity جدا باشد.
مثلاً:
High-quality observation

لزومـاً به معنی:
validated scientific model

نیست.
Architecture MUST این distinction را حفظ کند.
________________________________________
36. SECURITY BOUNDARY
Security باید با domain boundaries سازگار باشد.
حداقل طبقه‌بندی:
PUBLIC
INTERNAL
SENSITIVE
RESTRICTED
SCIENTIFIC_CONFIDENTIAL
PERSONAL

اما Agent حق ندارد بدون evidence این taxonomy را نهایی کند.
این بخش باید با findings قبلی security هماهنگ شود.
________________________________________
37. DATA OWNERSHIP
برای هر domain مشخص شود:
Entity
Owner
Source of Truth
Read Consumers
Write Authority
Audit Requirement
Retention
Provenance

هیچ database schema در ECO-02 ساخته نشود.
فقط conceptual data ownership مجاز است.
________________________________________
38. EVENT POLICY
Agent باید مشخص کند کدام domain interactions ذاتاً:
command
query
event
workflow
calculation request
decision request

هستند.
Event-driven architecture نباید صرفاً به دلیل محبوب بودن فناوری انتخاب شود.
________________________________________
39. SYNCHRONOUS VS ASYNCHRONOUS
برای هر عملیات مهم مشخص شود:
synchronous
asynchronous
batch
stream
simulation
long-running job

معیار باید:
latency
computation time
reliability
state
reproducibility
resource usage

باشد.
________________________________________
40. ERROR MODEL
Architecture باید error classes را تعریف کند:
VALIDATION_ERROR
UNIT_ERROR
MODEL_NOT_FOUND
MODEL_NOT_APPROVED
INSUFFICIENT_EVIDENCE
OUT_OF_DOMAIN
NUMERICAL_FAILURE
UNCERTAINTY_UNAVAILABLE
PROVENANCE_FAILURE
DEPENDENCY_FAILURE
LEGACY_DEPENDENCY
SECURITY_FAILURE

Scientific errors نباید با HTTP errors یا infrastructure errors مخلوط شوند.
________________________________________
41. FAILURE SAFETY
در صورت failure:
Scientific failure ≠ successful recommendation

اگر model execution ناقص باشد، سیستم نباید خروجی ناقص را به‌عنوان معتبر معرفی کند.
________________________________________
42. HIGH-STAKES DECISION BOUNDARY
Architecture باید امکان تعیین decision class را داشته باشد:
INFORMATIONAL
LOW_RISK
MEDIUM_RISK
HIGH_RISK
CRITICAL

هرچه risk بالاتر باشد، requirements مربوط به:
evidence
validation
uncertainty
human review
auditability

باید افزایش یابد.
________________________________________
43. HUMAN OVERSIGHT
برای تصمیم‌های حساس باید امکان:
human review
human override
review rationale
reviewer identity
review timestamp

در معماری آینده پیش‌بینی شود.
این بخش در ECO-02 فقط specification است.
________________________________________
44. CANONICAL ASSET DECISION
تمام 17 canonical assets گزارش ECO-01 باید دوباره در یک ماتریس معماری قرار گیرند:
Asset
Current Location
Canonical Role
Target Layer
Reusable Logic
Required Refactor
Scientific Status
Dependencies
Risk
Disposition

Disposition یکی از:
CANONICAL
CANONICAL_AFTER_REFACTOR
DOMAIN_LOGIC_ONLY
REFERENCE_ONLY
RESEARCH_ONLY
LEGACY
REJECT
PENDING_REVIEW

باشد.
________________________________________
45. LEGACY ASSET POLICY
هیچ legacy asset فقط به دلیل هزینه تولید قبلی حفظ نشود.
معیار حفظ:
scientific value
domain value
validated behavior
provenance
maintainability
security
architectural compatibility

________________________________________
46. OLD SMART CONTRACTS
Smart contracts پروژه قدیمی:
REFERENCE_ONLY

هستند.
نباید وارد canonical architecture شوند.
هیچ contract blockchain در ECO-02 طراحی یا implementation نشود.
________________________________________
47. DATABASE
Database در ECO-02 فقط به‌صورت:
conceptual ownership
logical data responsibilities
persistence requirements

بررسی شود.
ممنوع:
schema implementation
migration
ORM implementation
database deployment

________________________________________
48. API
API در ECO-02 فقط contract-level بررسی شود.
برای domainهای اصلی مشخص شود:
capability
input contract
output contract
error semantics
authorization concept
idempotency requirement

اما API implementation ممنوع است.
________________________________________
49. ARCHITECTURAL DECISION RECORDS
برای تصمیم‌های مهم ADR ایجاد شود.
حداقل ADRها:
ADR-001-CANONICAL-LAYERING
ADR-002-HYDROMA-BOUNDARY
ADR-003-ENGINE-GATEWAY
ADR-004-SCIENTIFIC-MODEL-CONTRACT
ADR-005-KNOWLEDGE-EPISTEMIC-MODEL
ADR-006-EVIDENCE-PROVENANCE
ADR-007-UNCERTAINTY
ADR-008-TASMIMYAR
ADR-009-AI-BOUNDARY
ADR-010-SERVICE-DOMAIN-BOUNDARIES
ADR-011-CPP-PYTHON
ADR-012-LEGACY-ASSET-POLICY
ADR-013-RESEARCH-VS-PRODUCTION
ADR-014-HIGH-STAKES-DECISION

در صورت نیاز ADRهای بیشتری اضافه شود.
________________________________________
50. ARCHITECTURE INVARIANTS
حداقل invariants زیر باید تعریف و ثبت شوند:
I-001
Engine never depends on UI.

I-002
Engine never depends on database.

I-003
Engine never depends on service implementation.

I-004
AI cannot silently modify scientific outputs.

I-005
Knowledge type cannot be inferred solely from content.

I-006
Model output cannot automatically become observation.

I-007
Local knowledge cannot automatically become scientific fact.

I-008
Scientific validity cannot be inferred from software test success.

I-009
Decision recommendation requires traceable evidence.

I-010
Scientific output must preserve model version and provenance.

I-011
Unitless scientific values are invalid unless explicitly defined.

I-012
Research candidates cannot automatically become production models.

I-013
Legacy service existence does not imply canonical service status.

I-014
Old smart contracts are reference assets only.

I-015
Uncertainty absence must not be interpreted as certainty.

Agent MUST expand this list.
________________________________________
51. ARCHITECTURE DIAGRAMS
حداقل diagrams زیر تولید شوند:
01-SYSTEM-CONTEXT
02-CANONICAL-LAYERS
03-HYDROMA-ARCHITECTURE
04-ENGINE-GATEWAY
05-SCIENTIFIC-MODEL-LIFECYCLE
06-KNOWLEDGE-ONTOLOGY
07-EVIDENCE-PROVENANCE
08-UNCERTAINTY-FLOW
09-TASMIMYAR-DECISION-FLOW
10-AI-BOUNDARY
11-SERVICE-BOUNDED-CONTEXTS
12-CPP-PYTHON-BOUNDARY
13-RESEARCH-LIFECYCLE
14-LEGACY-ASSET-FLOW
15-FUTURE-PLATFORM-EXPANSION

Mermaid یا فرمت text-based ترجیح داده شود تا diagrams قابل version control باشند.
________________________________________
52. REQUIRED DOCUMENTS
Agent MUST create:
reports/eco-02/

و حداقل فایل‌های زیر:
00-FINAL-VALIDATION.md
01-CANONICAL-ARCHITECTURE.md
02-LAYER-CONTRACTS.md
03-HYDROMA-CANONICAL-ARCHITECTURE.md
04-ENGINE-GATEWAY-CONTRACT.md
05-SCIENTIFIC-MODEL-CONTRACT.md
06-SCIENTIFIC-MATURITY-FRAMEWORK.md
07-KNOWLEDGE-ARCHITECTURE.md
08-EPISTEMIC-STATUS-MODEL.md
09-EVIDENCE-ARCHITECTURE.md
10-PROVENANCE-ARCHITECTURE.md
11-UNCERTAINTY-ARCHITECTURE.md
12-TASMIMYAR-ARCHITECTURE.md
13-AI-BOUNDARY.md
14-SERVICE-BOUNDED-CONTEXTS.md
15-DOMAIN-OWNERSHIP.md
16-CPP-PYTHON-ARCHITECTURE.md
17-MODEL-REGISTRY-ARCHITECTURE.md
18-RESEARCH-ARCHITECTURE.md
19-LEGACY-ASSET-POLICY.md
20-CANONICAL-ASSET-MATRIX.md
21-ARCHITECTURE-INVARIANTS.md
22-ARCHITECTURAL-RISKS.md
23-ARCHITECTURE-DECISIONS.md
24-IMPLEMENTATION-DEPENDENCIES.md
25-OPEN-QUESTIONS.md
26-ECO-02-REPAIR-LOG.md
27-ECO-02-BLOCKERS.md

________________________________________
53. ADR DIRECTORY
ایجاد شود:
reports/eco-02/adr/

و تمام ADRهای ایجادشده در آن قرار گیرند.
________________________________________
54. CONTRACT DIRECTORY
برای جلوگیری از مخلوط شدن implementation و architecture:
reports/eco-02/contracts/

ایجاد شود.
در آن contractهای مفهومی ذخیره شوند:
scientific-model
knowledge
evidence
provenance
uncertainty
decision
ai
engine-gateway
domain

این contractها در ECO-02 فقط specification هستند.
________________________________________
55. NO IMPLEMENTATION RULE
Agent MUST NOT convert contracts directly into production code.
مثلاً:
Scientific Model Contract

نباید به:
Pydantic implementation

تبدیل شود مگر اینکه صرفاً prototype بسیار کوچک برای اثبات یک ambiguity ضروری باشد.
ترجیح:
Specification first
Implementation later

________________________________________
56. ARCHITECTURAL QUALITY TEST
برای هر architectural decision حداقل این پرسش‌ها پاسخ داده شوند:
Why?
Evidence?
Alternative?
Trade-off?
Risk?
Reversibility?
Affected domains?
Scientific impact?
Security impact?
Performance impact?
Migration impact?

________________________________________
57. TECHNOLOGY SELECTION
فناوری‌ها در این مرحله فقط از نظر architectural suitability بررسی شوند.
برای هر technology:
Purpose
Need
Alternatives
Maturity
License
Operational Cost
Scientific Suitability
Security
Lock-in
Recommendation

وجود فناوری در پروژه قدیمی به معنی انتخاب آن برای پروژه جدید نیست.
________________________________________
58. NO TECHNOLOGY FASHION
انتخاب فناوری صرفاً به دلیل:
microservices
Kubernetes
Kafka
GraphQL
LLM
Blockchain
GPU
Quantum

ممنوع است.
هر technology باید یک مسئله واقعی را حل کند.
________________________________________
59. SCIENTIFIC PRIORITY
معماری باید برای این موارد explicit review path داشته باشد:
Climate Data Assimilation
Soil Salinity
Theis
Surface Water
Radiation
Van Genuchten
RUSLE LS

اما implementation یا scientific correction آنها در ECO-02 ممنوع است.
________________________________________
60. RESEARCH VS ARCHITECTURE
Research gaps گزارش ECO-01 باید به:
Research Track
Validation Track
Engineering Track
Architecture Requirement

تفکیک شوند.
هیچ research gap نباید خودکار تبدیل به feature شود.
________________________________________
61. FUTURE EVIDENCE ENGINE
معماری باید امکان اضافه شدن منابع آینده را بدون coupling شدید فراهم کند:
Satellite
Climate Stations
IoT
Soil Sensors
Field Measurements
GIS
Public Datasets
Scientific Publications
Local Knowledge
Expert Input

اما هیچ integration واقعی در ECO-02 انجام نشود.
________________________________________
62. FUTURE AI
معماری باید امکان آینده برای:
LLM
ML
Remote Sensing AI
Anomaly Detection
Forecasting
Computer Vision
Knowledge Retrieval
Scientific Assistants

را پیش‌بینی کند، اما هیچ‌کدام نباید scientific authority مستقل شوند.
________________________________________
63. FUTURE ECOSYSTEM
Architecture باید قابلیت توسعه آینده به موارد زیر را در سطح conceptual در نظر بگیرد:
Eco Nojin
Nojin Marketplace
Hydroma
Daneshyar
Tasmimyar
Eco Coin
Ecotourism
Rural Economy
Agriculture
Rangelands
Restoration
Carbon / MRV
Research
Projects
Community Knowledge

اما هیچ‌یک در ECO-02 implementation نشوند.
________________________________________
64. CANONICAL BOUNDARY TEST
Agent MUST سناریوهای زیر را با architecture آزمایش مفهومی کند:
Scenario A
یک observation وارد سیستم می‌شود.
باید مشخص شود:
where stored conceptually
how provenance attached
how quality assessed
how model consumes it

Scenario B
Hydroma ET0 محاسبه می‌کند.
باید مشخص شود:
input
model
version
units
output
uncertainty
provenance
consumer

Scenario C
Tasmimyar recommendation تولید می‌کند.
باید مشخص شود:
evidence
models
options
risk
uncertainty
rationale
recommendation

Scenario D
AI گزارش را توضیح می‌دهد.
باید مشخص شود:
what AI sees
what AI may transform
what AI cannot change

Scenario E
Local knowledge ثبت می‌شود.
باید مشخص شود:
epistemic status
source
provenance
validation
relationship to scientific evidence

Scenario F
Scientific model fails.
باید مشخص شود:
error
provenance
decision impact
fallback
user-visible status

________________________________________
65. ARCHITECTURE FAILURE CONDITIONS
اگر هر یک از موارد زیر رخ دهد، status باید:
BLOCKED

شود:
●	Engine هنوز وابسته به Service architecture باشد و boundary قابل تعریف نباشد.
●	Scientific model contract قابل تعریف نباشد.
●	Knowledge و Evidence نتوانند از هم تفکیک شوند.
●	AI boundary قابل enforcement نباشد.
●	provenance قابل trace نباشد.
●	service ownership قابل تعیین نباشد.
●	legacy dependencies architecture را کنترل کنند.
●	تصمیم معماری بدون evidence و صرفاً بر اساس حدس اتخاذ شود.
________________________________________
66. SCIENTIFIC REVIEW CONDITIONS
اگر تناقض علمی جدی پیدا شد:
REQUIRES_SCIENTIFIC_REVIEW

ثبت شود.
Agent حق ندارد:
formula را حدسی اصلاح کند
reference را جعل کند
نتیجه را برای رفع conflict تغییر دهد
scientific status را بدون evidence ارتقا دهد

________________________________________
67. FINAL ARCHITECTURE OUTPUT
در پایان باید یک architecture canonical به دست آید که حداقل این chain را روشن کند:
Knowledge / Evidence
        ↓
Domain Context
        ↓
Scientific Engine
        ↓
Engine Gateway
        ↓
Decision / Application
        ↓
AI Interpretation
        ↓
Product Experience

اما Agent باید بر اساس شواهد تعیین کند آیا این ترتیب دقیقاً مناسب است یا نیاز به اصلاح دارد.
________________________________________
68. IMPLEMENTATION READINESS MATRIX
برای هر layer مشخص شود:
Architecture Ready?
Contract Ready?
Scientific Review Ready?
Implementation Ready?
Dependencies Known?
Risks Known?

Implementation readiness به معنی اجازه implementation در ECO-02 نیست.
________________________________________
69. ECO-03 HANDOFF
ECO-02 باید مشخص کند ECO-03 دقیقاً چه چیزهایی را باید تبدیل به implementation specification کند.
حداقل:
Module boundaries
Repository boundaries
Package boundaries
Interface definitions
Data contracts
API contracts
Testing contracts
Security contracts
Deployment-independent runtime contracts
Migration strategy

اما ECO-03 نیز باید فقط در محدوده‌ای که معماری تأیید کرده حرکت کند.
________________________________________
70. FINAL VALIDATION
در پایان Agent باید اثبات کند:
[ ] Canonical architecture defined
[ ] Layer responsibilities defined
[ ] Hydroma boundary defined
[ ] Engine Gateway defined
[ ] Scientific Model Contract defined
[ ] Scientific maturity defined
[ ] Knowledge architecture defined
[ ] Epistemic status defined
[ ] Evidence architecture defined
[ ] Provenance architecture defined
[ ] Uncertainty architecture defined
[ ] Tasmimyar architecture defined
[ ] AI boundary defined
[ ] Service bounded contexts defined
[ ] Domain ownership defined
[ ] C++/Python boundary defined
[ ] Research boundary defined
[ ] Legacy asset policy defined
[ ] Canonical asset matrix completed
[ ] Architecture invariants defined
[ ] ADRs created
[ ] Conceptual scenarios tested
[ ] No forbidden implementation performed
[ ] No legacy architecture reconstructed
[ ] No scientific formula invented
[ ] No unsupported technology commitment made

________________________________________
71. FINAL STATUS
یکی از statusهای زیر مجاز است:
READY_FOR_ECO_03
READY_WITH_LIMITATIONS
BLOCKED
REQUIRES_SCIENTIFIC_REVIEW

READY_FOR_ECO_03
فقط زمانی مجاز است که architecture، boundaries و contracts به‌اندازه کافی مشخص باشند.
READY_WITH_LIMITATIONS
وقتی architecture قابل استفاده است ولی unresolved decisions وجود دارند.
BLOCKED
وقتی یک architectural dependency اساسی هنوز ناشناخته است.
REQUIRES_SCIENTIFIC_REVIEW
وقتی تصمیم معماری وابسته به یک unresolved scientific conflict اساسی است.
________________________________________
72. MACHINE-READABLE FINAL SUMMARY
Agent MUST provide:
ECO02_STATUS=
ARCHITECTURE_STATUS=
HYDROMA_STATUS=
ENGINE_GATEWAY_STATUS=
SCIENTIFIC_CONTRACT_STATUS=
KNOWLEDGE_ARCHITECTURE_STATUS=
EVIDENCE_ARCHITECTURE_STATUS=
PROVENANCE_STATUS=
UNCERTAINTY_STATUS=
TASMIMYAR_STATUS=
AI_BOUNDARY_STATUS=
SERVICE_ARCHITECTURE_STATUS=
CPP_PYTHON_STATUS=
RESEARCH_ARCHITECTURE_STATUS=
LEGACY_POLICY_STATUS=
CANONICAL_ASSET_STATUS=
ADR_STATUS=
BLOCKER_COUNT=
SCIENTIFIC_REVIEW_COUNT=
OPEN_QUESTION_COUNT=
FORBIDDEN_SCOPE_VIOLATIONS=
FINAL_STATUS=

________________________________________
73. ABSOLUTE CLOSING RULE
Agent باید این اصل را در تمام تصمیم‌ها رعایت کند:
ECO-02 does not build Eco Nojin. ECO-02 defines the architecture that future agents are allowed to build.
و:
The old repository is an evidence and asset source, not the blueprint of the new platform.
و:
Scientific computation remains authoritative for scientific calculation. AI remains interpretive unless an explicitly governed future architecture says otherwise.
و:
Knowledge, Evidence, Model Output, Inference, Hypothesis, Recommendation and Fact must never silently collapse into one another.
و:
Do not optimize the architecture for the legacy repository. Optimize it for the future canonical Eco Nojin platform.
________________________________________
END OF ECO-02

