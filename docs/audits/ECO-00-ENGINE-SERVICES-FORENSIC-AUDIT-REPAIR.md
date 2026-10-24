ECO-00
ENGINE & SERVICES FORENSIC AUDIT, REPAIR AND CANONICALIZATION
Document ID: ECO-00
 Version: 1.0
 Status: EXECUTION AUTHORIZED
 Priority: CRITICAL
 Execution Mode: Autonomous, evidence-driven, non-destructive
 Primary Scope: engine/ and services/ only
 Project Strategy: Clean-Room Rebuild with Verified Asset Preservation
________________________________________

> **Implementation status (verified 2026-10-11)** — وضعیت راستی‌آزمایی‌شدهٔ گزارش ECO-00 روی درخت زندهٔ `D:\HyDroMA`.
> این بخش جایگزین گزارش اجرای ECO-00 **نیست**؛ فقط ادعاهای تازهٔ اجرا را به شواهد امروز گره می‌زند.
>
> ## الف) وضعیت کلی درخت اجرایی (سنجش ۲۰۲۶-۱۰-۱۱)
>
> | ناحیه | واقعیت امروز | شواهد |
> |---|---|---|
> | Import guard | **۱۶ تخلف باز** — همگی `services/_gateway_facade_adapters/{carbon,climate,economics,groundwater,soil}.py` (`SERVICES_NO_ENGINE_INTERNALS`) | `python tools/detect_imports.py --root .` → `Violations found: 16` |
> | Lint | `ruff check .` → **۸۱۵** یافته (خط‌مبنای مستند در `reports/lint/`) | |
> | Typecheck | `mypy engine --ignore-missing-imports` → **۰ خطا در ۴۰۵ فایل** | `Success: no issues found in 405 source files` |
> | Tests — `engine/` | **۷ شکست / ۲۶۹۹ پاس / ۳۱ skip / ۴۲ xfailed**: یکی از همان «مسیر اسپک ریشه» است (اثر انتقال این سند)، بقیه درخت پیش‌رو (drift گراف، راتچهٔ مرز سرویس، biofertilizer) | |
> | Tests — `engine/strict_tests` | **۱۳۲۳ پاس**، ۰ شکست | |
> | Tests — `services/` | **۱ شکست / ۱۴۴۳ پاس / ۹ skip**؛ جمع‌آوری به‌دلیل یک فایل ردیابی‌نشدهٔ همزمان (`test_inline_science_routing.py` + پلاگین schemathesis) متوقف می‌شود؛ با حذف آن **۱۴۵۳ تست جمع می‌شود** | |
>
> ## ب) بازسازی فهرست G-Z (ثبت‌شده در `reports/eco-nojin/GAP-REGISTER.md`)
>
> | شناسه | ادعای ثيت | وضعیت ۲۰۲۶-۱۰-۱۱ | شواهد |
> |---|---|---|---|
> | **G-Z1** | supabase/duckdb در وابستگی‌های اصلی (نقض پشتهٔ ZED) | **بخشاً رفع‌شده** — هستهٔ `pyproject.toml` پاک است (فقط numpy/scipy/pandas/requests/httpx/pydantic/loguru) و duckdb/supabase به extra `legacy-bridge` کوچیده‌اند؛ **اما `requirements.txt:37-38` هنوز هر دو را دارد** | `pyproject.toml:26-34`, `:90-93`; `requirements.txt:37-38` |
> | **G-Z2** | دریافت زندهٔ شبکه در موتور بدون گیت `--allow-download` | **رفع‌شده** — `engine/hydroma/data_pipeline/download_gate.py` با `HYDROMA_ALLOW_DOWNLOAD` (خوانش در زمان فراخوانی)، CLI `--allow-download`/`--strict`/`--deny-download` | `download_gate.py:56`, `:111`, `:207` |
> | **G-Z3** | پایگاه DuckDB به‌جای SQLite | **باز** — `engine/data_connector.py` هنوز روی درخت است و `data/master/eco_nojin_master.duckdb` (۲.۸MB، ردیابی‌نشده) باقی است | `Test-Path engine\data_connector.py` → True |
> | **G-Z4** | نبود قرارداد `*.meta.json` برای داده خام | **باز (بخشی)** — چهار قرارداد `*.meta.json` برای دادهٔ مرجع وجود دارد، اما `data/` همچنان `raw/processed/indices/model_runs/evidence/scenarios/decisions` را ندارد | `git ls-files '*.meta.json'` = 4 (همه در `tests/reference_data/`); `Get-ChildItem data` |
> | **G-Z5** | pint نادیده‌گرفته‌شده؛ `Quantity` یک stub ده‌خطی | **باز** — `engine/hydroma/quantity.py` همچنان `@dataclass Quantity` ده‌خطی است؛ ممیزی pint (`engine/gateway/pint_audit.py`) جدا از تبدیل واقعی باقی است | فایل را بخوانید |
> | **G-Z6** | نبود `LICENSES/` | **رفع‌شده** — `LICENSES/README.md` و `LICENSES/Dependency-LICENSES.md` ردیابی می‌شوند | `git ls-files LICENSES` |
>
> ## ج) Track C2 — کوچک‌سازی allowlist مهاجرت سرویس→Gateway
>
> کار باقی‌ماندهٔ ثبت‌شده در `docs/adr/014-import-guard-policy.md:42,49,85`
> (`engine.hydroma.carbon.calculator` = «POLICY GAP»؛ واردات مستقیم `services/_gateway_facade.py`)
> **هنوز باز است و بدتر شده است**: درخت امروز ۱۶ تخلف همه در
> `services/_gateway_facade_adapters/` دارد. Track C2 بنابراین **OPEN** است — نه بخشی از
> برنامهٔ ۲۸ قلمی، ولی هیچ‌کدام از آن درخت‌ساز جدید اینجا ردیابی نشده بود.
>
> ## د) برنامهٔ اخیر پیاده‌سازی (۲۸ قلم) — چه چیزی در این ممیزی خارج از حوزه بود
> ECO-00 صریحاً §۴ دیتابیس/API/احراز هویت/پرداخت را از دامنه خارج می‌کند؛ موارد زیر
> پیاده شده‌اند و **بر روی فهرست مخارج این ممیزی تأثير ندارند**:
> دفتر کل دوبل‌انتر+ (`services/finance/ledger_service.py`، `FinJournalBatch/FinJournalEntry`)،
> کدینگ حساب (`services/finance/chart_of_accounts.py`)، ارزیابی موجودی/COGS با لات و FEFO
> (`services/inventory/service.py`)، اقلام سفارش و موجودی اتمیک (`services/commerce/`)،
> پرداخت→سفارش (`services/marketplace/payments_service.py`)، هاب روستایی با RBAC و گردشگری
> (`services/marketplace/hub_service.py`، `services/api_gateway/routers/village_hub.py`)،
> ثبت مالکیت زمین (`services/land/registry.py`)، ۵ نسخهٔ مهاجرت Alembic برای همهٔ جداول
> (`alembic/versions/`)، امنیت HTTP (HMAC وب‌هوک، هدرهای امنیتی، محدودیت نرخ احراز هویت —
> `services/api_gateway/middleware/security_headers.py`، `rate_limit.py`، `security.py`)،
> ۹۱ تست رگرسیون HTTP (`services/api_gateway/tests/test_http_*`)، ۷۳ تست ویژگی‌محور پول
> (۴ فایل `test_properties_*`) و شتاب‌دهی Numba موتور (`engine/land/terrain_analysis.py`,
> `engine/land/hydrology.py`).
>
> ________________________________________
1. MISSION
The new Eco Nojin project is intentionally being rebuilt from a clean foundation.
Only two categories of assets have been transferred from the previous project:
engine/
services/

These two directories are considered legacy-derived technical assets, not automatically trusted production code.
Your mission is to:
1.	Discover the actual structure of engine/.
2.	Discover the actual structure of services/.
3.	Identify dependencies, coupling, hidden assumptions, and legacy references.
4.	Determine what is healthy, broken, incomplete, duplicated, obsolete, or unsafe.
5.	Repair code that can be repaired without changing its intended scientific or business meaning.
6.	Verify scientific engines independently from application services.
7.	Verify services independently from the old application platform.
8.	Remove or isolate accidental dependencies on the old project.
9.	Preserve valid scientific algorithms and business rules.
10.	Produce a canonical technical baseline for future development.
11.	Leave the project in a state where subsequent ECO tasks can build the new platform without depending on the old repository.
This task is not a product-development task.
This task is not a frontend task.
This task is not a database migration task.
This task is not an API reconstruction task.
This task is not a smart-contract task.
This task is an Engine + Services Forensic Audit, Repair, Verification and Canonicalization task.
________________________________________
2. ABSOLUTE STRATEGIC RULE
The old project is no longer the architecture to be repaired.
It is only a source of potentially valuable assets.
The governing principle is:
OLD PROJECT
     ↓
FORENSIC ANALYSIS
     ↓
VERIFY
     ↓
EXTRACT VALID ASSETS
     ↓
REPAIR ONLY WHEN JUSTIFIED
     ↓
CANONICALIZE
     ↓
NEW ECO NOJIN PLATFORM

Never reverse this relationship.
Do not attempt to recreate the old project around these directories.
Do not reintroduce the old architecture merely because some imported code expects it.
If imported code depends on something that does not exist in the new project, determine whether that dependency is:
●	genuinely required,
●	accidental,
●	obsolete,
●	replaceable,
●	or requires a future platform task.
Do not silently recreate the old dependency.
________________________________________
3. SCOPE
3.1 Allowed primary directories
You may read and modify:
engine/
services/

You may create task-specific documentation and reports under:
docs/
reports/

only if these directories already exist or if creating them is necessary for this task.
If they do not exist, you may create:
docs/engine-services/
reports/engine-services/

for audit artifacts.
You may create no unrelated product architecture.
________________________________________
4. FORBIDDEN SCOPE
Do NOT implement or redesign:
frontend/
web/
mobile/
admin/
cms/
database/
migrations/
smart contracts/
blockchain/
wallet UI/
marketplace UI/
tourism UI/
authentication UI/
new API architecture/
new OpenAPI architecture/
new product features/
Eco Coin economics/
new scientific models/
new AI models/
new recommendation systems/
new decision algorithms/

Do not create a new database merely to make the services run.
Do not create a new frontend merely to test an endpoint.
Do not create mock production architecture.
Do not create fake integrations.
Do not invent missing business rules.
Do not invent missing scientific formulas.
________________________________________
5. WRITE-SCOPE RULE
Before changing any file, determine whether the file belongs to:
ENGINE
SERVICES
TASK DOCUMENTATION
TASK REPORTING

If a required change falls outside the allowed write scope:
STOP THAT CHANGE
DOCUMENT THE BLOCKER
DO NOT MODIFY THE EXTERNAL FILE
CONTINUE ALL INDEPENDENT WORK

Do not ask the user for routine permission.
Do not stop the entire task because one unrelated dependency is missing.
________________________________________
6. CORE PRINCIPLE: NO UNDOCUMENTED INTELLIGENCE
No production code may introduce undocumented:
●	formula
●	equation
●	coefficient
●	threshold
●	score
●	weight
●	heuristic
●	optimization objective
●	decision rule
●	classification rule
●	scientific assumption
●	transformation
●	model
●	calibration parameter
●	business rule
unless its source is already established in the existing asset or formally documented during this task.
If an implementation contains intelligence that cannot be explained from existing evidence:
STATUS = REQUIRES_REVIEW

Do not silently "improve" it.
________________________________________
7. SCIENTIFIC INTEGRITY RULE
For scientific Engine code, distinguish strictly between:
A. Existing validated scientific implementation
May be preserved and repaired.
B. Existing implementation with unclear provenance
May be inspected and tested but must be marked:
PROVENANCE_STATUS = UNKNOWN

C. Existing implementation with obvious defects
May be repaired only if the intended mathematical behavior can be established from:
●	source code,
●	documentation,
●	tests,
●	equations,
●	references,
●	established domain standards,
●	numerical invariants,
●	known scientific specifications.
D. Missing scientific behavior
Do NOT invent it.
Use:
FORMULA STATUS = RESEARCH-PENDING
IMPLEMENTATION STATUS = NOT AUTHORIZED

________________________________________
8. SERVICE INTEGRITY RULE
For Services, preserve valid business behavior but do not assume that existing architecture is correct.
For every service determine:
Purpose
Domain
Inputs
Outputs
Dependencies
Business Rules
Persistence Assumptions
External Dependencies
Events
Authorization Assumptions
Validation Rules
Error Model
Idempotency Requirements
Tests
Known Defects
Legacy Coupling
Future Replacement

A service that only exists because the old platform had a particular architecture must not automatically be recreated.
________________________________________
9. FIRST PHASE: REPOSITORY DISCOVERY
Before modifying anything, perform a complete read-only inventory.
Inspect:
engine/
services/

and identify:
●	files
●	directories
●	languages
●	packages
●	modules
●	entry points
●	tests
●	configuration
●	build systems
●	dependency manifests
●	generated files
●	native code
●	bindings
●	scripts
●	documentation
●	fixtures
●	sample data
●	schemas
●	adapters
●	clients
●	service registries
●	routers
●	repositories
●	domain models
●	engines
●	calculators
●	optimization modules
●	validation modules
●	serialization layers.
Do not make changes during the initial inventory unless a file must be generated solely to run a harmless inspection command.
________________________________________
10. REQUIRED INVENTORY REPORT
Create:
reports/engine-services/INVENTORY.md

The report must contain at minimum:
Total engine files
Total service files
Languages
Frameworks
Build systems
Dependency manifests
Test files
Scientific modules
Business-domain services
Native modules
Generated code
External dependencies
Internal dependencies
Potentially obsolete modules
Potentially duplicated modules
Missing dependencies
Broken imports
Unclear ownership
Legacy references

Also produce a directory tree.
Do not merely list filenames.
Explain the role of each major subsystem.
________________________________________
11. DEPENDENCY FORENSICS
Build a dependency graph.
At minimum identify:
engine → engine
engine → services
services → engine
services → services
services → external packages
engine → external packages

Also identify forbidden or suspicious dependencies such as:
engine → database
engine → HTTP
engine → UI
engine → authentication
engine → service-specific infrastructure

The preferred scientific Engine architecture is:
Input
  ↓
Validation
  ↓
Scientific Computation
  ↓
Validation
  ↓
Structured Output

with no unnecessary application infrastructure dependency.
________________________________________
12. ENGINE BOUNDARY
The Engine must remain conceptually independent from application services.
Preferred architecture:
Application
    ↓
Decision/Application Layer
    ↓
Engine Gateway
    ↓
Scientific Engine
    ↓
Validated Result

The Engine should not directly depend on:
database sessions
HTTP requests
frontend objects
user sessions
UI state
authentication state
service-specific repositories

If such coupling exists, document it.
Do not perform a large architectural rewrite during this task unless required to restore correctness.
________________________________________
13. HYDROMA FORENSICS
If Hydroma exists under engine/, inspect it as a scientific system.
Identify:
Hydroma root
Scientific domains
Python implementation
C/C++ implementation
Bindings
Numerical kernels
Input models
Output models
Unit handling
Validation
Calibration
Optimization
Simulation
Climate modules
Water modules
Soil modules
Agriculture modules
Carbon/MRV modules
Engineering modules
Tests
Benchmarks
Reference data
Documentation

Do not replace a working scientific implementation merely because another language or framework appears cleaner.
________________________________________
14. C++ / PYTHON RULE
If both C++ and Python implementations exist:
Do NOT automatically choose one.
Determine:
Which implementation is authoritative?
Which implementation is faster?
Which is more numerically stable?
Which is more tested?
Which has broader functionality?
Which is actually used?

Where practical, establish benchmark evidence.
Possible outcomes:
CPP_AUTHORITATIVE
PYTHON_AUTHORITATIVE
HYBRID
DUPLICATE_REQUIRES_CONSOLIDATION
UNKNOWN

If unknown, do not delete either implementation.
________________________________________
15. SCIENTIFIC MODEL INVENTORY
For every significant scientific model/calculator, create an inventory entry containing:
Model ID
Model Name
Domain
Implementation Path
Language
Version if available
Purpose
Inputs
Input Units
Outputs
Output Units
Parameters
Assumptions
Constraints
Equations if documented
Algorithm
Data Requirements
References
Tests
Validation Status
Benchmark Status
Uncertainty
Known Limitations
Provenance
Production Status

If no formal Model ID exists, assign a temporary audit identifier such as:
AUDIT-MODEL-001
AUDIT-MODEL-002
...

These are audit IDs, not final public model IDs.
________________________________________
16. UNIT AND DIMENSION ANALYSIS
For scientific calculations, inspect dimensional consistency.
For every major equation or calculation:
Input quantity
Unit
Expected dimension
Transformation
Output quantity
Output unit

Check for:
●	temperature unit mismatch
●	pressure unit mismatch
●	length unit mismatch
●	area mismatch
●	volume mismatch
●	mass mismatch
●	time-scale mismatch
●	rate versus accumulated quantity
●	daily versus hourly values
●	coordinate reference system mismatch
●	degrees versus radians
●	percentage versus fraction
●	absolute versus relative values.
Do not silently change scientific units without documenting the change.
________________________________________
17. SCIENTIFIC VALIDATION
Where known formulas already exist, test:
Mathematical consistency
f(valid_input)

must produce physically/mathematically meaningful output.
Boundary behavior
Test:
minimum valid input
typical input
maximum valid input
zero where physically valid
near-zero values
missing values
invalid values
extreme values

Determinism
If the model is intended to be deterministic:
same input + same configuration
        ↓
same output

within the defined numerical tolerance.
Numerical stability
Check sensitivity to:
floating-point precision
rounding
small perturbations
large values
near-boundary values

________________________________________
18. SCIENTIFIC FORMULAS
Do not invent formulas.
For existing formulas, document the formula exactly enough to establish:
Equation
Variables
Units
Parameters
Assumptions
Constraints
Reference
Implementation mapping
Test mapping

For example, if a standard FAO-56 Penman-Monteith implementation exists and is already intended by the codebase, document the exact implemented equation and units rather than replacing it with a different formulation.
If an equation cannot be established:
FORMULA_STATUS = UNKNOWN

and do not rewrite its scientific behavior.
________________________________________
19. ALGORITHM DOCUMENTATION
For each major algorithm, document:
Algorithm name
Purpose
Inputs
Preconditions
Steps
Intermediate states
Outputs
Postconditions
Complexity if known
Numerical assumptions
Failure conditions
Validation

Use pseudocode where necessary.
Do not create pseudocode that changes the implementation's behavior.
________________________________________
20. SERVICE FORENSICS
For every service:
Service ID
Service name
Domain
Purpose
Entry points
Public methods
Internal methods
Dependencies
Data dependencies
External dependencies
Events
Business rules
Validation
Authorization assumptions
Error behavior
Idempotency
Concurrency assumptions
Tests
Known defects
Legacy coupling
Status

Assign temporary audit IDs:
AUDIT-SVC-001
AUDIT-SVC-002
...

________________________________________
21. SERVICE CLASSIFICATION
Each service must be classified as one of:
VALID_KEEP
KEEP_WITH_REPAIR
KEEP_WITH_REFACTOR
MERGE_CANDIDATE
DUPLICATE
LEGACY_WRAPPER
OBSOLETE
UNSAFE
UNKNOWN

Do not delete anything merely because it appears unused.
Deletion requires evidence.
________________________________________
22. SERVICE MERGING RULE
Do not merge services during the first discovery pass.
First establish:
ownership
dependencies
business rules
database assumptions
events
security assumptions
tests

Only then may a merge recommendation be created.
The actual merge should be a later task unless required for a clear correctness issue.
________________________________________
23. LEGACY DEPENDENCY DETECTION
Search for references to:
●	old project names
●	old package names
●	old absolute paths
●	old environment variables
●	old database names
●	old API hosts
●	old service URLs
●	old authentication modules
●	old configuration systems
●	old OpenAPI generated clients
●	old frontend packages
●	old deployment assumptions
●	old Docker assumptions
●	old cloud provider assumptions
●	old secrets/config paths.
Classify each reference:
REQUIRED
OPTIONAL
OBSOLETE
REPLACEABLE
UNKNOWN

Do not restore the old platform just because an import fails.
________________________________________
24. ENVIRONMENT AND CONFIGURATION
Identify all required configuration.
Separate:
CODE DEFAULT
DEVELOPMENT CONFIG
TEST CONFIG
PRODUCTION CONFIG
SECRET
NON-SECRET CONFIG

Never create or commit real secrets.
Never copy production credentials from the old project.
If a required secret is missing:
BLOCKED_EXTERNAL_DEPENDENCY

Do not invent a secret.
________________________________________
25. TEST FORENSICS
Find all tests associated with Engine and Services.
Classify:
PASS
FAIL
ERROR
SKIPPED
UNRUNNABLE
STALE
DUPLICATE
INVALID

Do not assume an existing test is correct merely because it passes.
For scientific Engine tests, distinguish:
UNIT
NUMERICAL
REGRESSION
REFERENCE
PROPERTY
BOUNDARY
INTEGRATION
PERFORMANCE

________________________________________
26. TEST REPAIR
You may repair tests when:
●	imports are stale,
●	paths changed during migration,
●	test fixtures are broken,
●	assertions reflect an obsolete wrapper,
●	setup assumes the old project,
●	a clear implementation bug is exposed.
Do not weaken an assertion simply to make a test pass.
Never change:
expected scientific result

just because the implementation currently produces another result.
If expected behavior is unclear:
TEST_STATUS = REQUIRES_REVIEW

________________________________________
27. PERFORMANCE BASELINE
For significant Engine computations, establish a baseline where practical.
Record:
Model
Input size
Execution environment
Language
Implementation
Execution time
Memory if measurable
Output correctness
Numerical tolerance

Do not optimize prematurely.
A faster wrong scientific model is not an improvement.
________________________________________
28. REPAIR PRIORITY
Repair in this order:
P0
Security / data corruption / scientific correctness

P1
Build-breaking defects
Import-breaking defects
Critical runtime failures

P2
Incorrect validation
Incorrect units
Incorrect state handling
Broken tests

P3
Architectural coupling
Duplication
Maintainability problems

P4
Performance optimization

P5
Cosmetic cleanup

Never spend significant time on P5 while P0/P1 defects remain.
________________________________________
29. REPAIR RULE
Every non-trivial repair must answer:
What was wrong?
Why was it wrong?
What evidence proves the intended behavior?
What changed?
How was the change validated?
Could the change alter scientific/business behavior?

Record this in:
reports/engine-services/REPAIR_LOG.md

________________________________________
30. NO BLIND REFACTORING
Do not perform broad refactoring merely because:
●	the code is old,
●	another framework is preferred,
●	naming could be cleaner,
●	architecture could be prettier,
●	a different pattern looks better.
Refactoring must have a measurable reason:
correctness
security
testability
dependency isolation
scientific integrity
maintainability
performance

________________________________________
31. ENGINE/SERVICE CONTRACT
For each Engine exposed to Services, identify:
Input schema
Input validation
Units
Required fields
Optional fields
Output schema
Output units
Error conditions
Determinism
Version
Model identifier
Execution metadata
Uncertainty if applicable
Provenance

If such a contract does not exist, document the current behavior.
Do not invent a final public API.
________________________________________
32. TEMPORARY INTERNAL CONTRACT
Where necessary for testing, you may define an internal temporary contract.
It must be labeled:
TEMPORARY AUDIT CONTRACT
NOT FINAL PRODUCT API

It must not become the permanent public API automatically.
________________________________________
33. DATA RULE
Do not import large external datasets merely to make tests pass.
Do not create a global data warehouse.
Use:
small deterministic fixtures
reference datasets
existing local test data

where legally and technically appropriate.
For every external dataset found in the Engine or Services, document:
Source
License
Attribution
Version/date
Format
Purpose
Size
Required access

Never bypass registration or provider restrictions.
________________________________________
34. DATABASE RULE
This task does not establish the new production database architecture.
If Services require database models to understand their behavior:
READ AND DOCUMENT

but do not reconstruct the old database wholesale.
If a model is essential to understanding service logic, document:
Entity
Fields
Relationships
Constraints
Business meaning

as an audit artifact.
The final database architecture belongs to a later ECO task.
________________________________________
35. API RULE
Do not rebuild the old API.
You may inspect:
●	routers
●	request models
●	response models
●	service calls
●	validation
●	error semantics
to understand service behavior.
But do not recreate the old API architecture merely because the old service expects it.
________________________________________
36. SECURITY
During the audit:
●	never print secrets,
●	never copy credentials,
●	never commit .env values,
●	never expose private keys,
●	never expose tokens,
●	never include credentials in reports,
●	redact secrets in logs,
●	flag suspicious credential files,
●	flag unsafe subprocess usage,
●	flag unsafe path handling,
●	flag SQL injection risks,
●	flag command injection risks,
●	flag deserialization risks,
●	flag SSRF risks,
●	flag unsafe file writes,
●	flag missing authorization boundaries.
For security findings use:
SECURITY-ID
Severity
Location
Finding
Evidence
Impact
Recommended remediation
Status

________________________________________
37. SCIENTIFIC SECURITY
Scientific integrity is also a security concern.
Flag:
●	silent unit conversion
●	hidden constants
●	unexplained coefficients
●	hard-coded thresholds
●	unexplained clipping
●	silent missing-value replacement
●	silent interpolation
●	silent extrapolation
●	undocumented normalization
●	undocumented weighting
●	undocumented randomization
●	unseeded stochastic behavior
●	model fallback without disclosure
●	model selection without documented criteria.
________________________________________
38. NO NEW AI INTELLIGENCE
Do not introduce:
●	LLM calls
●	embeddings
●	RAG
●	classifiers
●	AI scoring
●	AI recommendations
●	AI model selection
during this task unless such behavior already exists inside the transferred Engine/Service asset and is necessary to preserve it.
This task is about stabilizing existing assets.
________________________________________
39. REQUIRED REPORTS
At completion, create:
reports/engine-services/
├── INVENTORY.md
├── DEPENDENCY-MAP.md
├── ENGINE-AUDIT.md
├── SERVICE-AUDIT.md
├── SCIENTIFIC-MODEL-REGISTRY.md
├── SERVICE-REGISTRY.md
├── TEST-REPORT.md
├── REPAIR_LOG.md
├── SECURITY-FINDINGS.md
├── LEGACY-DEPENDENCIES.md
├── PERFORMANCE-BASELINE.md
├── BLOCKERS.md
└── FINAL-VALIDATION.md

If a report category has no findings, explicitly state:
NONE IDENTIFIED

Do not omit the report.
________________________________________
40. ENGINE AUDIT REPORT
ENGINE-AUDIT.md must contain:
Engine subsystem
Purpose
Architecture
Modules
Scientific domains
Model inventory
Dependencies
Language boundaries
C++/Python relationship
Input/output behavior
Units
Validation
Tests
Performance
Known defects
Scientific risks
Legacy coupling
Recommended status

________________________________________
41. SERVICE AUDIT REPORT
SERVICE-AUDIT.md must contain:
Service
Domain
Purpose
Dependencies
Business rules
State
Persistence assumptions
Events
Security assumptions
Tests
Legacy coupling
Defects
Classification
Recommendation

________________________________________
42. SCIENTIFIC MODEL REGISTRY
For each significant model:
Model ID
Name
Domain
Path
Version
Formula status
Algorithm status
Input schema
Units
Output schema
Parameters
Assumptions
Constraints
Reference
Validation
Benchmark
Uncertainty
Known limitations
Production readiness

Possible status:
VERIFIED
VERIFIED_WITH_LIMITATIONS
REQUIRES_VALIDATION
REQUIRES_RESEARCH
UNKNOWN
REJECTED

________________________________________
43. SERVICE REGISTRY
For each Service:
Service ID
Name
Domain
Status
Dependencies
Consumers
Engine dependencies
Data dependencies
Business rules
Security requirements
Tests
Legacy coupling
Repair status
Future destination

________________________________________
44. BLOCKER POLICY
Every blocker must be classified:
BLOCKER-P0
BLOCKER-P1
BLOCKER-P2
BLOCKER-P3

A blocker is something that prevents correct execution.
Examples:
missing required source code
corrupted implementation
unavailable required dependency
ambiguous scientific formula
missing critical reference data
security vulnerability

Do not classify ordinary inconvenience as a blocker.
________________________________________
45. AUTONOMOUS EXECUTION
You are expected to execute the task without asking routine questions.
Do not ask:
●	whether you should inspect another file,
●	whether you should run tests,
●	whether you should document findings,
●	whether you should fix obvious broken imports,
●	whether you should generate the required reports.
Those actions are explicitly authorized.
Ask for human intervention only when:
1.	a legal decision is required,
2.	an irreversible destructive action is required,
3.	two scientifically incompatible interpretations cannot be resolved from evidence,
4.	production credentials or privileged external access are required,
5.	a change outside the defined scope is unavoidable.
Even then:
STOP THE BLOCKED ACTION
CONTINUE ALL OTHER INDEPENDENT WORK
DOCUMENT THE BLOCKER

________________________________________
46. DESTRUCTIVE ACTION POLICY
Do not permanently delete code during ECO-00.
For questionable code:
MARK
DOCUMENT
ISOLATE

rather than immediately deleting it.
Deletion belongs to a later controlled cleanup task after canonical replacements exist.
________________________________________
47. GIT / VERSION CONTROL
Before substantial modifications:
●	inspect git status,
●	inspect current branch,
●	record the baseline state.
Do not rewrite git history.
Do not reset user work.
Do not force-push.
Do not delete branches.
Do not remove unrelated files.
If the project is not under git, document that fact.
________________________________________
48. QUALITY GATE
ECO-00 is complete only when:
Discovery
[ ] Engine fully inventoried
[ ] Services fully inventoried
[ ] Dependencies mapped
[ ] Legacy references identified

Engine
[ ] Scientific modules identified
[ ] Models registered
[ ] C++/Python boundaries documented
[ ] Units reviewed
[ ] Major algorithms documented
[ ] Scientific defects classified
[ ] Tests executed where possible

Services
[ ] All services classified
[ ] Dependencies mapped
[ ] Business rules identified
[ ] Legacy coupling identified
[ ] Critical defects repaired
[ ] Tests executed where possible

Security
[ ] Secrets checked
[ ] Dangerous dependencies checked
[ ] Security findings recorded

Documentation
[ ] Inventory complete
[ ] Engine audit complete
[ ] Service audit complete
[ ] Model registry complete
[ ] Service registry complete
[ ] Repair log complete
[ ] Blockers complete
[ ] Final validation complete

________________________________________
49. FINAL VALIDATION
Run all appropriate checks available for the actual technology found.
Do not assume a particular framework.
Possible checks include:
build
compile
typecheck
lint
unit tests
integration tests
scientific regression tests
numerical tests
static analysis
dependency audit
security scan
benchmark

Use the project's actual tooling.
Do not install unnecessary infrastructure merely to satisfy this task.
Do not require Docker, external databases, cloud services, or third-party accounts unless the existing Engine/Service code genuinely requires them and there is no local alternative.
________________________________________
50. FINAL VALIDATION REPORT
FINAL-VALIDATION.md must contain:
Execution date
Repository baseline
Files changed
Files created
Files intentionally untouched
Tests executed
Tests passed
Tests failed
Tests unavailable
Build result
Lint result
Typecheck result
Scientific validation result
Security result
Performance result
Remaining defects
Remaining blockers
Required future ECO tasks
Overall status

Overall status must be exactly one of:
READY_FOR_NEXT_PHASE
READY_WITH_LIMITATIONS
BLOCKED
REQUIRES_SCIENTIFIC_REVIEW

________________________________________
51. DEFINITION OF DONE
The task is NOT considered complete merely because tests pass.
It is complete when we know:
WHAT WE HAVE
WHAT WORKS
WHAT IS BROKEN
WHAT IS SCIENTIFICALLY TRUSTWORTHY
WHAT IS BUSINESS-LOGICALLY TRUSTWORTHY
WHAT DEPENDS ON THE OLD PROJECT
WHAT CAN BE PRESERVED
WHAT MUST BE REBUILT
WHAT MUST BE RESEARCHED
WHAT MUST BE DEPRECATED
WHAT MUST NOT BE TOUCHED

The result must allow the next development phase to begin without guessing.
________________________________________
52. OUTPUT TO THE NEXT ECO TASK
At the end, produce a concise machine-readable summary:
ENGINE_STATUS=
SERVICES_STATUS=

VERIFIED_ENGINE_ASSETS=
VERIFIED_SERVICE_ASSETS=

ENGINE_REPAIRS=
SERVICE_REPAIRS=

SCIENTIFIC_MODELS_VERIFIED=
SCIENTIFIC_MODELS_REQUIRING_REVIEW=

SERVICES_KEEP=
SERVICES_REPAIR=
SERVICES_MERGE_CANDIDATE=
SERVICES_OBSOLETE=
SERVICES_UNKNOWN=

CRITICAL_SECURITY_FINDINGS=
CRITICAL_BLOCKERS=

LEGACY_DEPENDENCIES_REMAINING=

TESTS_PASS=
TESTS_FAIL=
TESTS_ERROR=

FINAL_STATUS=

________________________________________
53. ABSOLUTE PROHIBITIONS
Never:
invent scientific formulas
invent business rules
invent missing requirements
invent production data
invent secrets
invent external credentials
recreate the old platform
rebuild the old frontend
rebuild the old database
rebuild the old API
create smart contracts
introduce blockchain architecture
introduce unnecessary infrastructure
hide failed tests
delete unexplained code
weaken tests to obtain green status
silently change scientific outputs
silently change business behavior
silently change units
silently change thresholds
silently change model parameters

________________________________________
54. FINAL DIRECTIVE TO THE AGENT
You are not rebuilding the old Eco Nojin platform.
You are not repairing the old Eco Nojin platform as a whole.
You are extracting and stabilizing the valuable technical core that was deliberately carried into the new project.
Your scope is:
ENGINE
+
SERVICES

Everything else is outside this task.
Use evidence before modification.
Use tests before declaring correctness.
Use scientific references before changing scientific behavior.
Use explicit documentation before introducing intelligence.
Preserve valid assets.
Repair justified defects.
Isolate uncertainty.
Do not invent.
Do not expand scope.
Do not recreate the legacy platform.
The desired result is:
OLD ENGINE/SERVICES
        ↓
FORENSICALLY UNDERSTOOD
        ↓
VERIFIED
        ↓
REPAIRED WHERE JUSTIFIED
        ↓
DOCUMENTED
        ↓
DECOUPLED FROM LEGACY ASSUMPTIONS
        ↓
READY TO BECOME THE TECHNICAL CORE
OF THE NEW ECO NOJIN PLATFORM

EXECUTION STATUS: AUTHORIZED
NEXT PHASE MAY NOT BEGIN UNTIL FINAL-VALIDATION.md EXISTS.
