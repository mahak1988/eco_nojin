ECO-04-CONTROLLED-IMPLEMENTATION.md
دستور اجرای رسمی ECO-04
Phase: ECO-04
 Name: Controlled Implementation
 Parent: ECO-03 / ECO-03.1
 Status: AUTHORIZED WITH LIMITATIONS
 Priority: CRITICAL
 Execution Mode: Evidence-Driven / Gate-Based / No-Skip
 Repository: D:\HyDroMA
________________________________________
0. فرمان اصلی
از این مرحله به بعد، پروژه وارد پیاده‌سازی کنترل‌شده می‌شود.
اما:
ECO-04 مجوز ساخت کل پلتفرم نیست.
در این مرحله فقط زیرساخت‌های معماری و علمی‌ای که در ECO-00 تا ECO-03.1 به‌صورت مستند تعریف شده‌اند، مرحله‌به‌مرحله پیاده‌سازی و اعتبارسنجی می‌شوند.
هیچ Agent مجاز نیست بر اساس حدس، سلیقه، convenience یا معماری شخصی خود:
●	معماری جدید ایجاد کند
●	scientific model جدید اختراع کند
●	equation جدید اضافه کند
●	frontend بسازد
●	database schema محصول نهایی بسازد
●	API عمومی محصول را طراحی کند
●	authentication/payment/wallet بسازد
●	smart contract بسازد
●	blockchain را فعال کند
●	AI را صاحب authority علمی کند
●	سرویس‌ها را بدون bounded-context decision جابه‌جا کند
●	قراردادهای ECO-02 را silently تغییر دهد
________________________________________
1. مهم‌ترین Gate قبل از هر Implementation
ENV-00 — Environment Readiness Gate
اولین وظیفه Agent اجرای هیچ featureای نیست.
ابتدا باید محیط اجرای پروژه آماده و قابل تکرار شود.
Required
بررسی:
python --version
python -m pip --version

سپس:
python -m pip install -e ".[dev]"

اگر نصب موفق بود:
python -c "import numpy; print('numpy', numpy.__version__)"
python -c "import scipy; print('scipy', scipy.__version__)"
python -c "import pandas; print('pandas', pandas.__version__)"
python -c "import pydantic; print('pydantic', pydantic.__version__)"
python -c "import pytest; print('pytest', pytest.__version__)"

سپس:
python -c "import engine; print('ENGINE_IMPORT_OK')"

و:
python tools/detect_imports.py --root .

________________________________________
2. اگر Network Available نیست
اگر محیط دسترسی اینترنت ندارد:
ممنوع
Agent نباید:
●	dependency را fake کند
●	package stub برای numpy/scipy/pytest بسازد
●	importهای علمی را حذف کند
●	testها را disable کند
●	testها را skip کند تا سبز شوند
●	نتیجه را PASS اعلام کند
در این حالت:
STATUS = ENVIRONMENT_BLOCKED

و باید گزارش کامل تولید شود.
فقط environment preparation انجام شود.
________________________________________
3. Environment Manifest
فایل زیر ایجاد شود:
reports/eco-04/00-ENVIRONMENT-REPORT.md

شامل:
●	OS
●	Python
●	pip
●	compiler
●	CMake
●	pybind11
●	numpy
●	scipy
●	pandas
●	pydantic
●	pytest
●	network
●	installed package versions
●	package resolution result
●	test execution result
همچنین:
reports/eco-04/00-ENVIRONMENT-MACHINE.json

تولید شود.
________________________________________
4. Environment Gate
PASS
اگر:
●	dependencyها نصب شدند
●	import engine موفق شد
●	import guard اجرا شد
●	pytest قابل اجرا بود
آنگاه:
ENVIRONMENT_GATE = PASS

BLOCKED
اگر dependencyها قابل نصب نبودند:
ENVIRONMENT_GATE = BLOCKED

در این حالت Agent فقط environment diagnosis و reproducibility work انجام دهد.
________________________________________
5. Test Baseline
پس از نصب dependencyها:
python -m pytest engine/tests/ engine/strict_tests/ --tb=short

سپس:
python -m pytest tests/unit/ --tb=short

و در صورت وجود:
python -m pytest -q

نتایج باید تفکیک شوند:
PASSED
FAILED
ERROR
SKIPPED
XFAILED
COLLECTION_ERROR
ENVIRONMENT_ERROR

هرگز:
ERROR = PASS

در نظر گرفته نشود.
________________________________________
6. Architecture Gate
قبل از implementation باید architecture invariants دوباره اجرا شوند.
فایل:
reports/eco-04/01-ARCHITECTURE-BASELINE.md

________________________________________
7. Non-Negotiable Architecture Invariants
INV-001
engine MUST NOT import services

INV-002
engine MUST NOT import database

نکته:
وجود database/ stub در ECO-03.1 به معنی رفع INV-002 نیست.
Stub فقط مشکل import-time failure را موقتاً حل کرده است.
در ECO-04 باید dependency واقعی حذف یا به abstraction/port منتقل شود.
________________________________________
INV-003
services MUST NOT directly import engine internals

تمام دسترسی‌های production باید از:
Engine Gateway

عبور کنند.
________________________________________
INV-004
Circular dependency ممنوع.
________________________________________
INV-005
Frontend/Application نمی‌تواند scientific kernel را مستقیماً صدا بزند.
________________________________________
INV-006
Scientific output باید provenance داشته باشد.
________________________________________
INV-007
Model output نباید به‌عنوان observation ذخیره شود.
________________________________________
INV-008
Epistemic status نباید implicit باشد.
________________________________________
INV-009
AI scientific authority نیست.
________________________________________
INV-010
AI نمی‌تواند:
●	equation را تغییر دهد
●	parameter را تغییر دهد
●	model selection را silently تغییر دهد
●	provenance را حذف کند
●	uncertainty را حذف کند
●	observation را به scientific fact تبدیل کند
________________________________________
INV-011
absence of uncertainty != certainty

________________________________________
INV-012
Decision recommendation باید قابل trace باشد.
________________________________________
INV-013
Software test success به‌تنهایی scientific validity محسوب نمی‌شود.
________________________________________
INV-014
Scientific validity باید evidence جداگانه داشته باشد.
________________________________________
INV-015
Research code و production code باید جدا باشند.
________________________________________
8. Import Guard
ابزار:
tools/detect_imports.py

باید حفظ شود.
اما ECO-04 باید آن را از یک ابزار دستی به یک architecture enforcement mechanism تبدیل کند.
حداقل ruleها:
ENGINE_NO_SERVICES
ENGINE_NO_DATABASE
SERVICES_NO_ENGINE_INTERNAL
AI_NO_ENGINE_INTERNAL
NO_CIRCULAR_DEPENDENCY
NO_FORBIDDEN_IMPORT
NO_LAYER_UPWARD_IMPORT

خروجی باید machine-readable باشد:
JSON

و human-readable:
Markdown

________________________________________
9. CI Integration Specification
CI implementation فقط در صورتی انجام شود که CI موجود باشد.
اگر CI وجود ندارد:
DO NOT INVENT FULL CI/CD INFRASTRUCTURE

به‌جای آن:
reports/eco-04/02-CI-ENFORCEMENT-SPEC.md

ایجاد شود.
________________________________________
10. B-002 Architectural Repair
این blocker باید واقعاً حل شود.
موارد زیر هنوز violation محسوب می‌شوند:
engine/data_connector.py
engine/resource_manager.py
engine/ports/session.py
engine/hydroma/biofertilizer/models.py

و importهای:
from database...

باید بررسی شوند.
________________________________________
11. اصل اصلاح Database Dependency
Hydroma/Engine نباید database-aware باشد.
به‌جای:
Engine → Database

معماری باید:
Application
    ↓
Repository / Port
    ↓
Persistence Adapter
    ↓
Database

باشد.
Engine فقط باید contract/port را بشناسد.
________________________________________
12. Database Stub
Stubهای ECO-03.1 را production implementation تلقی نکنید.
این فایل‌ها:
database/hub.py
database/config.py
database/base.py

صرفاً برای hardening اولیه ساخته شده‌اند.
Agent باید تصمیم architectural را بر اساس ECO-02 بگیرد.
اگر stub دیگر لازم نیست:
●	حذف یا isolate شود
●	با evidence انجام شود
●	migration log نوشته شود
________________________________________
13. ECO-04.1 — Engine Gateway
بعد از PASS شدن Environment Gate:
اولین implementation واقعی:
engine/gateway/

است.
ساختار پیشنهادی:
engine/
└── gateway/
    ├── __init__.py
    ├── gateway.py
    ├── contracts.py
    ├── validation.py
    ├── units.py
    ├── model_selection.py
    ├── provenance.py
    ├── uncertainty.py
    └── errors.py

ساختار نهایی فقط در صورتی تغییر کند که source evidence آن را توجیه کند.
________________________________________
14. Engine Gateway Responsibilities
Gateway باید مسئول:
1.	input validation
2.	unit normalization
3.	model selection
4.	applicability validation
5.	parameter validation
6.	provenance initialization
7.	uncertainty metadata
8.	execution metadata
9.	normalized result
10.	normalized error
باشد.
Gateway نباید:
●	UI logic داشته باشد
●	database persistence داشته باشد
●	authentication داشته باشد
●	payment داشته باشد
●	AI reasoning داشته باشد
●	business workflow داشته باشد
________________________________________
15. Scientific Model Contract
هر model که از Gateway عبور می‌کند باید حداقل این metadata را داشته باشد:
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

________________________________________
16. CANON-001
CANON-001 باید یک identifier رسمی و versioned باشد.
Agent حق ندارد صرفاً از:
CANON-001

به‌عنوان label گزارش استفاده کند.
باید مشخص شود:
CANON-001
MODEL NAME
VERSION
EQUATION
SOURCE
VALIDATION STATUS
APPLICABILITY
IMPLEMENTATION

و مشخصاً معلوم شود که CANON-001 به کدام implementation مربوط است.
________________________________________
17. Scientific Maturity
طبقه‌بندی‌های متناقض ECO-01، ECO-02 و ECO-03.1 باید در یک registry واحد canonical شوند.
حداقل:
VERIFIED
SCIENTIFICALLY_SUPPORTED
IMPLEMENTATION_VERIFIED
REQUIRES_SCIENTIFIC_REVIEW
STUB

تعریف‌ها باید دقیق باشند.
VERIFIED
فقط زمانی:
●	implementation verified
●	reference evidence available
●	test/benchmark executed
●	result acceptable
باشد.
SCIENTIFICALLY_SUPPORTED
یعنی theoretical/scientific basis موجود است، اما implementation یا benchmark کافی نیست.
IMPLEMENTATION_VERIFIED
یعنی implementation با specification مطابقت دارد، ولی scientific benchmark کامل انجام نشده است.
REQUIRES_SCIENTIFIC_REVIEW
یعنی uncertainty علمی یا specification unresolved وجود دارد.
STUB
یعنی implementation واقعی وجود ندارد.
________________________________________
18. مهم‌ترین قانون Scientific Verification
این عبارت ممنوع است:
VERIFIED

وقتی test environment اجازه اجرای test را نداده است.
در آن وضعیت:
NOT_EXECUTED

یا:
IMPLEMENTATION_VERIFIED_PENDING_RUNTIME_VALIDATION

استفاده شود.
________________________________________
19. Scientific Review Queue
حداقل این مدل‌ها باید در registry باقی بمانند:
CANON-005 Theis
CANON-018 CMIP6
CANON-002 Hargreaves
CANON-007 RUSLE
CANON-011 Solar Radiation

اما scientific review نباید بدون evidence به production implementation تبدیل شود.
________________________________________
20. Theis Model
برای:
CANON-005

نباید convergence criterion اختراع شود.
باید:
1.	implementation موجود ثبت شود
2.	mathematical source ثبت شود
3.	convergence method ثبت شود
4.	numerical tolerance ثبت شود
5.	applicability ثبت شود
6.	reference case تعریف شود
7.	scientific review انجام شود
________________________________________
21. Evidence Engine
بعد از Engine Gateway:
knowledge/evidence/

یا canonical location تعیین‌شده توسط ECO-02 باید implementation شود.
Evidence باید بتواند حداقل:
evidence_id
source
source_type
epistemic_type
trust_level
timestamp
location
measurement
unit
quality
provenance
processing_history
model_reference
uncertainty
license

را حمل کند.
________________________________________
22. Provenance
حداقل chain:
Source
 ↓
Observation
 ↓
Processing
 ↓
Model Input
 ↓
Execution
 ↓
Model Output
 ↓
Decision Input
 ↓
Decision

هر مرحله باید قابل trace باشد.
________________________________________
23. Epistemic Types
Registry رسمی:
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

هیچ type نباید silent conversion داشته باشد.
مثلاً:
LOCAL_KNOWLEDGE

نباید خودکار تبدیل شود به:
SCIENTIFIC_EVIDENCE

________________________________________
24. Uncertainty
Uncertainty باید first-class data باشد.
حداقل:
uncertainty_type
value
unit
method
confidence_level
distribution
source
propagation_method

هر output باید مشخص کند:
uncertainty = known

یا:
uncertainty = not_estimated

اما:
uncertainty = 0

فقط زمانی مجاز است که واقعاً scientifically justified باشد.
________________________________________
25. Tasmimyar
Decision Engine نباید صرفاً:
recommendation

برگرداند.
Decision object باید بتواند:
current_state
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
rationale
recommendation
confidence
limitations

را trace کند.
________________________________________
26. AI Boundary
AI در این معماری:
INTERPRETER
ASSISTANT
RETRIEVAL/REASONING SUPPORT
PRESENTATION LAYER

است.
AI:
SCIENTIFIC AUTHORITY = NO
MODEL AUTHORITY = NO
EVIDENCE AUTHORITY = NO
DECISION AUTHORITY = NO

AI می‌تواند پیشنهاد بدهد، اما canonical scientific state را تغییر نمی‌دهد.
________________________________________
27. AI Isolation Test
حداقل static tests:
services/ai → engine internals = FORBIDDEN
engine → services/ai = FORBIDDEN
AI → scientific kernel = FORBIDDEN
AI → model registry mutation = FORBIDDEN
AI → provenance mutation = FORBIDDEN

________________________________________
28. Service Architecture
عدد:
38 domain services

به‌عنوان current classification ثبت شود.
عدد:
8 bounded contexts

به‌عنوان architectural target ثبت شود.
اما Agent نباید صرفاً برای رسیدن به عدد 8، سرویس‌ها را مصنوعی merge کند.
هر consolidation باید دارای:
reason
ownership
dependency analysis
migration path
risk
rollback strategy

باشد.
________________________________________
29. Context Registry
هشت context فعلی:
CTX-001 Platform Core
CTX-002 Hydroma Engine
CTX-003 Hydrology
CTX-004 AgriWater
CTX-005 Evidence Provenance
CTX-006 Decision Engine
CTX-007 Remote Sensing
CTX-008 Reporting/AI

باید با source evidence بررسی شوند.
اگر contradiction پیدا شد:
IMPLEMENTATION = STOP
ADR = REQUIRED

________________________________________
30. AI Potential Violation
مورد زیر باید قبل از production enforcement بررسی شود:
services/ai/admin_assistant.py:343

گزارش ECO-03.1 آن را:
POTENTIAL

اعلام کرده است.
Agent حق ندارد آن را بدون source inspection PASS اعلام کند.
________________________________________
31. C++ / Python Boundary
مسئولیت‌ها:
C++
●	numerical kernels
●	heavy array operations
●	deterministic computation
●	performance-sensitive algorithms
Python
●	orchestration
●	model metadata
●	validation
●	provenance
●	uncertainty
●	model selection
●	API between layers
________________________________________
32. Bridge
ECO-03.1 نشان داده که گزارش قبلی درباره ctypes دقیق نبوده و implementation از pybind11 استفاده می‌کند.
بنابراین:
pybind11

به‌عنوان current bridge ثبت شود.
هر ادعای:
ctypes primary bridge

باید حذف یا evidence-backed شود.
________________________________________
33. Performance Claims
ادعای:
10x–200x

تا زمانی که benchmark واقعی وجود ندارد:
UNVERIFIED

است.
هیچ Agent حق ندارد آن را به:
VERIFIED PERFORMANCE

تبدیل کند.
Benchmark بعداً باید شامل:
Python baseline
C++ implementation
dataset size
hardware
runtime
memory
iterations
statistical summary

باشد.
________________________________________
34. Tests
پس از Environment Gate، تست‌ها باید در این ترتیب اجرا شوند:
Level 1
import tests

Level 2
architecture tests

Level 3
unit tests

Level 4
boundary tests

Level 5
scientific validation tests

Level 6
integration tests

هیچ Level بالاتر بدون حداقل سلامت Level پایین‌تر اعلام PASS نشود.
________________________________________
35. Required Test Categories
حداقل:
test_import_boundaries
test_engine_gateway
test_model_contract
test_unit_normalization
test_provenance
test_epistemic_types
test_uncertainty
test_ai_isolation
test_service_gateway
test_cpp_python_parity

________________________________________
36. No Fake Green
ممنوع:
pytest.skip(...)

برای مخفی کردن blocker.
ممنوع:
expected failure

بدون ثبت علت.
ممنوع:
mock scientific result

برای ادعای scientific validation.
________________________________________
37. ECO-04 Execution Order
ترتیب دقیق:
ECO-04.0 Environment Gate
        ↓
ECO-04.1 Architecture Enforcement
        ↓
ECO-04.2 Engine Gateway
        ↓
ECO-04.3 Database Dependency Removal
        ↓
ECO-04.4 Scientific Model Registry
        ↓
ECO-04.5 Evidence + Provenance
        ↓
ECO-04.6 Epistemic Knowledge
        ↓
ECO-04.7 Uncertainty
        ↓
ECO-04.8 Tasmimyar Decision Contract
        ↓
ECO-04.9 AI Isolation
        ↓
ECO-04.10 Service Gateway
        ↓
ECO-04.11 C++/Python Boundary Validation
        ↓
ECO-04.12 Full Test & Scientific Validation

________________________________________
38. Gate After Every Sprint
هر sprint باید:
implementation
↓
tests
↓
architecture checks
↓
scientific checks
↓
evidence report
↓
gate decision

داشته باشد.
هیچ sprint شکسته‌ای نباید به sprint بعدی spill شود مگر اینکه blocker explicitly classified شود.
________________________________________
39. Required Reports
Agent باید برای هر مرحله گزارش تولید کند.
حداقل:
reports/eco-04/
├── 00-ENVIRONMENT-REPORT.md
├── 01-ARCHITECTURE-BASELINE.md
├── 02-IMPORT-GUARD-REPORT.md
├── 03-ENGINE-GATEWAY-REPORT.md
├── 04-DATABASE-BOUNDARY-REPORT.md
├── 05-MODEL-REGISTRY-REPORT.md
├── 06-EVIDENCE-ENGINE-REPORT.md
├── 07-KNOWLEDGE-ENGINE-REPORT.md
├── 08-UNCERTAINTY-REPORT.md
├── 09-DECISION-ENGINE-REPORT.md
├── 10-AI-ISOLATION-REPORT.md
├── 11-SERVICE-GATEWAY-REPORT.md
├── 12-CPP-PYTHON-REPORT.md
├── 13-TEST-REPORT.md
├── 14-SCIENTIFIC-VALIDATION.md
├── 15-SECURITY-REPORT.md
├── 16-CHANGELOG.md
├── 17-OPEN-QUESTIONS.md
├── 18-BLOCKERS.md
├── 19-FINAL-VALIDATION.md
└── 20-MACHINE-READABLE-SUMMARY.json

________________________________________
40. Mandatory Change Log
هر تغییر production باید ثبت کند:
file
change
reason
source evidence
architecture impact
scientific impact
test evidence
rollback

________________________________________
41. Forbidden Changes
در ECO-04 فعلاً ممنوع:
frontend
mobile
public API
OpenAPI finalization
database product schema
authentication
authorization redesign
payment
wallet
Eco Coin
smart contracts
blockchain
marketplace UI
ecotourism UI
CMS
admin UI
cloud deployment
Kubernetes
production infrastructure
new ML models
new scientific equations

________________________________________
42. Scientific Integrity Rule
اگر implementation با scientific specification تضاد داشت:
CODE MUST NOT WIN BY DEFAULT

Agent باید:
STOP
↓
REPORT
↓
SCIENTIFIC REVIEW
↓
DECISION

انجام دهد.
________________________________________
43. Architecture Integrity Rule
اگر code با architecture contract تضاد داشت:
DO NOT SILENTLY CHANGE ARCHITECTURE

ابتدا:
ADR

ایجاد شود.
________________________________________
44. ADR Requirement
هر تغییر در موارد زیر نیازمند ADR است:
●	layer boundaries
●	dependency direction
●	bounded context
●	model contract
●	epistemic taxonomy
●	uncertainty semantics
●	evidence semantics
●	decision semantics
●	AI authority
●	C++/Python ownership
________________________________________
45. Final ECO-04 Gate
در پایان ECO-04 فقط در صورت تحقق همه موارد زیر:
Engine Gateway implemented
Engine → Services = 0
Engine → Database = 0
Services → Engine internals = 0
AI isolation enforced
Architecture tests PASS
Core tests executable
Scientific validation separately reported
Provenance implemented
Epistemic types implemented
Uncertainty represented
Decision contract implemented
C++/Python boundary verified
No silent architecture changes
No unapproved scientific models

می‌توان وضعیت را:
READY_FOR_ECO-05

اعلام کرد.
________________________________________
46. Final Status Vocabulary
فقط یکی از این وضعیت‌ها مجاز است:
READY_FOR_ECO_05
READY_WITH_LIMITATIONS
BLOCKED
REQUIRES_SCIENTIFIC_REVIEW
ENVIRONMENT_BLOCKED

________________________________________
47. Final Report Requirement
در پایان ECO-04، Agent باید گزارش کامل و مستقل ارائه کند.
گزارش باید حداقل شامل:
1.	Executive Summary
2.	Exact files changed
3.	Exact files created
4.	Exact files deleted
5.	Architecture changes
6.	Dependency changes
7.	Engine Gateway status
8.	Database boundary status
9.	Scientific model status
10.	Evidence status
11.	Provenance status
12.	Epistemic status
13.	Uncertainty status
14.	Decision Engine status
15.	AI isolation status
16.	Service boundary status
17.	C++/Python status
18.	Test results
19.	Scientific validation results
20.	Security findings
21.	Performance findings
22.	Open questions
23.	Remaining blockers
24.	Deferred items
25.	ADRs created
26.	Rollback information
27.	Full command log
28.	Machine-readable summary
29.	Final gate decision
________________________________________
48. فرمان نهایی به Agent
این phase را به‌صورت:
IMPLEMENT
→ TEST
→ VERIFY
→ REPORT
→ GATE

اجرا کن.
نه:
IMPLEMENT EVERYTHING
→ HOPE
→ REPORT

اول Environment Gate را اجرا کن.
اگر محیط آماده نیست:
STOP IMPLEMENTATION
REPORT ENVIRONMENT BLOCKER

اگر محیط آماده است:
CONTINUE ECO-04.1

هر ادعای verified باید evidence اجرایی داشته باشد.
هر ادعای scientifically validated باید scientific evidence داشته باشد.
هر architectural invariant باید با source/static/runtime test قابل اثبات باشد.
هیچ blocker را با stub، skip، mock یا تغییر wording پنهان نکن.
در پایان، گزارش کامل ECO-04 را ارائه بده و برای هر تصمیم، evidence دقیق فایل/خط/command/test را ثبت کن.
ECO-04 فقط وقتی موفق است که چیزی را واقعاً اثبات کرده باشد، نه اینکه صرفاً آن را در گزارش PASS نوشته باشد.
این فایل عمداً ECO-04 را از یک «شروع ناگهانی کدنویسی» به یک مسیر Gate-based تبدیل می‌کند. مهم‌ترین اصلاح نسبت به گزارش ایجنت هم همین است: اول محیط، بعد enforcement، بعد Gateway و حذف وابستگی Database، و تازه بعد سراغ Evidence/Knowledge/Uncertainty/Decision می‌رویم.

