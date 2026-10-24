دقیقاً. اینجا باید Agent را از حالت «فایل‌ساز» خارج کنیم و صریحاً به او بگوییم معماری را واقعاً تا سطح قابل‌اعتماد اصلاح کند، نه اینکه با ساختن کلاس و گزارش، وضعیت را سبز اعلام کند.
فایل زیر را به‌عنوان دستور رسمی مرحله بعدی ECO-04 پیشنهاد می‌کنم. این فایل عمداً Agent را از پرسیدن سؤال‌های غیرضروری منع می‌کند و او را موظف می‌کند inspect → implement → test → verify → reconcile → report → gate را خودش تا انتها انجام دهد.
ECO-04 — ARCHITECTURE COMPLETION, ENFORCEMENT, VERIFICATION & FINAL GATE
نوع سند
Execution Directive / Autonomous Engineering Instruction
این فایل یک گزارش نیست.
 این فایل دستور اجرایی الزام‌آور برای Agent است.
Agent موظف است ECO-04 را تا رسیدن به یک وضعیت واقعاً قابل راستی‌آزمایی ادامه دهد.
هدف ساختن فایل، کلاس، اسکلت، stub یا گزارش سبز نیست.
هدف:
اصلاح واقعی معماری Eco Nojin در کد، enforce کردن مرزها، تکمیل implementationهای لازم، اجرای تست و راستی‌آزمایی، و سپس تولید یک Final Validation Report که دقیقاً وضعیت واقعی سیستم را نشان دهد.
________________________________________
> **Implementation status (verified 2026-10-11)** — پاسخ‌انداختن §32/§37 این دستور به شواهد امروز.
> «NOT IMPLEMENTED»های بدنهٔ سند واژه‌گزین دستور ``` و ادعای وضعیت نیستند.
>
> | سؤال §37 (Definition of Done) | پاسخ ۲۰۲۶-۱۰-۱۱ | شواهد |
> |---|---|---|
> | آیا معماری واقعاً enforce شده؟ | **PARTIAL** — دکترین و ابزار بله؛ نتیجهٔ import guard **FAIL (۱۶ تخلف)** | `python tools/detect_imports.py --root .` |
> | آیا Engine از Database جداست؟ | **YES** — `engine/ports/persistence_port.py` + آداپتر SQLite؛ دو import مستثنا مستند | `engine/ports/persistence_port.py`؛ `docs/adr/014-import-guard-policy.md` |
> | آیا Engine از Services جداست؟ | **YES** — ۰ تخلف Engine→Services | خروجی guard |
> | آیا Services از Gateway استفاده می‌ند؟ | **NO — هنوز ۱۶ واردات مستقیم** | `services/_gateway_facade_adapters/*.py` |
> | آیا AI scientific authority نیست؟ | **YES** — قواعد AI-isolation در guard اجرا می‌شوند | `architecture/rules.yaml`؛ `tools/detect_imports.py` |
> | آیا Evidence و Knowledge از هم تفکیک شده؟ | **PARTIAL** — هر دو واقعی‌اند، تفکیک درخواستی (`evidence_engine`/`provenance_tracker` …) انجام نشده | `engine/evidence/__init__.py`؛ `engine/knowledge/__init__.py` |
> | آیا provenance قابل ردیابی است؟ | مسیر E2E بله؛ لایهٔ تولید هنوز سیم‌کشی نشده | — |
> | آیا Model Registry canonical است؟ | **YES** — رجیستری با ۷۰ مدل و ۲۲ کارت | `engine/models/registry.py::status_summary()` |
> | آیا tests واقعاً اجرا شده؟ | **YES (با تحمل)** — `engine/strict_tests/` ۱۳۲۳ پاس/۰ شکست؛ `engine/` **۷ شکست/۲۶۹۹ پاس** (یکی اثر انتقال اسناد، بقیه drift درخت)؛ `services/` **۱ شکست/۱۴۴۳ پاس** (جمع‌آوری به‌دایل فایل همزمان متوقف) | |
> | آیا scientific validation انجام شده؟ | **PARTIAL** — ۱۳/۷۰ مدل S3+ (۱۸.۶٪)، ۱۰ مدل `validated` بدون لنگر بیرونی pin شده‌اند | `engine/models/maturity.py`؛ `test_machine_evidence_consistency.py` |
> | چه چیزهایی وجود ندارد؟ | `data/mirror/`، ۱۰ شاخص نوین، فراخوانی Aβ/Aار مدل، مهاجرت کامل سرویس→Gateway | — |
>
> **پیاده‌شدهٔ خارج از دامنهٔ ECO-04.1 (ثبت برای شفافیت):** دفتر کل دوبل‌انتر و کدینگ حساب
> (`services/finance/`)، ارزیابی موجودی/COGS + لات/FEFO (`services/inventory/`)، اقلام سفارش و
> موجودی اتمیک (`services/commerce/`)، پرداخت→سفارش (`services/marketplace/payments_service.py`)،
> هاب روستایی با RBAC + گردشگری (`services/marketplace/hub_service.py`,
> `services/api_gateway/routers/village_hub.py`, `services/api_gateway/tests/test_http_tourism.py`)،
> ثبت مالکیت زمین (`services/land/registry.py`)، مهاجرت‌های Alembic برای همهٔ جداول
> (`alembic/versions/`), امنیت HTTP (HMAC وب‌هوک، هدرهای امنیتی، محدودیت نرخ احراز هویت)، ۹۱ تست
> رگرسیون HTTP، ۷۳ تست ویژگی‌محور پول و شتاب‌دهی Numba موتور.
________________________________________
1. فرمان اصلی
Agent باید این اصل را به‌عنوان بالاترین دستور ECO-04 اجرا کند:
ARCHITECTURE FIRST
IMPLEMENTATION SECOND
VERIFICATION THIRD
REPORT LAST

ساختن فایل جدید به‌تنهایی موفقیت محسوب نمی‌شود.
ساختن class یا dataclass به‌تنهایی implementation محسوب نمی‌شود.
وجود import guard به‌تنهایی به معنی enforce شدن معماری نیست.
عبارت‌هایی مانند:
Implemented
Complete
Verified
Production Ready
Ready for Integration
PASS

فقط زمانی مجاز هستند که برای آنها evidence قابل بازتولید وجود داشته باشد.
________________________________________
2. مهم‌ترین دستور به Agent
Agent نباید فقط فایل ایجاد کند.
Agent باید بررسی کند:
1.	چه چیزی واقعاً وجود دارد؟
2.	چه چیزی واقعاً importable است؟
3.	چه چیزی واقعاً executable است؟
4.	چه چیزی واقعاً توسط test اثبات شده؟
5.	چه چیزی فقط skeleton است؟
6.	چه چیزی فقط interface است؟
7.	چه چیزی فقط report شده؟
8.	چه چیزی در معماری نقض شده؟
9.	چه dependencyهایی هنوز وجود دارند؟
10.	چه ادعاهایی در گزارش‌های قبلی با واقعیت کد سازگار نیستند؟
11.	چه invariantهایی واقعاً enforce می‌شوند؟
12.	چه invariantهایی فقط در documentation نوشته شده‌اند؟
13.	چه scientific claims واقعاً validation شده‌اند؟
14.	چه چیزهایی هنوز unknown هستند؟
Agent باید هر اختلاف بین:
DOCUMENTATION
CODE
TEST
RUNTIME
ARCHITECTURE
SCIENTIFIC VALIDATION

را پیدا و گزارش کند.
________________________________________
3. ممنوعیت مطلق گزارش‌سازی
Agent نباید برای سبز کردن Gate:
●	test جعلی بسازد
●	test را skip کند
●	dependency جعلی بسازد
●	stub را جای implementation واقعی معرفی کند
●	exception را swallow کند
●	import را مخفی کند
●	dynamic import را برای دور زدن guard استفاده کند
●	assertion ضعیف ایجاد کند
●	test result را دستی PASS اعلام کند
●	binary موجود را به‌عنوان build موفق معرفی کند
●	manual verification را automated verification معرفی کند
●	software test را scientific validation معرفی کند
●	confidence را به‌جای uncertainty معرفی کند
●	provenance ناقص را provenance کامل معرفی کند
●	وجود یک dataclass را implementation کامل تلقی کند
●	وجود یک API را integration تلقی کند.
اگر محیط اجازه اجرای تست نمی‌دهد:
TEST NOT EXECUTED

باید ثبت شود.
نه:
TEST PASS

________________________________________
4. عدم نیاز به سؤال پرسیدن
Agent باید بدون پرسیدن سؤال از کارفرما پیشروی کند.
اگر با ابهام مواجه شد:
اولویت تصمیم‌گیری
1. ECO-04
2. ECO-03
3. ECO-02
4. ECO-01
5. ECO-00
6. Canonical architecture
7. Existing code evidence
8. Existing tests
9. Scientific evidence
10. Conservative engineering judgment

Agent باید خودش تصمیم محافظه‌کارانه بگیرد.
اگر چیزی قابل اثبات نیست:
UNKNOWN

اگر ناقص است:
PARTIAL

اگر فقط skeleton است:
SCAFFOLDING

اگر وجود ندارد:
NOT IMPLEMENTED

اگر اجرا نشده:
NOT EXECUTED

اگر شکست خورده:
FAILED

نباید برای هیچ‌کدام از این موارد از کارفرما سؤال بپرسد.
________________________________________
5. مأموریت اصلی ECO-04
Agent باید سیستم را از وضعیت فعلی به این وضعیت برساند:
Product / Application
        ↓
Decision / Tasmimyar
        ↓
Knowledge / Daneshyar
        ↓
Evidence / Provenance
        ↓
Domain Services
        ↓
Engine Gateway
        ↓
Hydroma
        ↓
Scientific Engine
        ↓
C++ Numerical Kernels

و این dependency boundaryها باید واقعی باشند.
________________________________________
6. Architecture Invariants
Agent موظف است این invariantها را بررسی، enforce و verify کند.
INV-001
Engine → Services

ممنوع.
باید:
0 violations

باشد.
________________________________________
INV-002
Engine → Database

ممنوع.
Persistence فقط از طریق abstraction/port مجاز است.
باید:
0 violations

باشد.
________________________________________
INV-003
Services → Engine

باید از طریق:
EngineGateway

باشد.
هر direct import به implementation داخلی Hydroma یا scientific kernel باید بررسی و در صورت violation اصلاح شود.
هدف:
0 unauthorized direct service → engine implementation dependencies

________________________________________
INV-004
Circular dependencies ممنوع.
Agent باید dependency graph واقعی تولید کند.
هدف:
0 unexpected cycles

________________________________________
INV-005
Frontend نباید مستقیماً به scientific kernel دسترسی داشته باشد.
________________________________________
INV-006
هر scientific output باید provenance قابل ردیابی داشته باشد.
حداقل زنجیره:
Source
→ Observation
→ Processing
→ Model Input
→ Execution
→ Model Output
→ Decision Input
→ Decision

یک:
list[str]

به‌تنهایی الزاماً provenance کامل محسوب نمی‌شود.
Agent باید بررسی کند implementation واقعاً chain را نگه می‌دارد یا فقط metadata ساده دارد.
________________________________________
INV-007
این موارد نباید با هم اشتباه شوند:
Observation
Measurement
Local Knowledge
Expert Opinion
Scientific Evidence
Model Output
Inference
Hypothesis

________________________________________
INV-008
Epistemic status باید صریح باشد.
نباید:
model output = fact

یا:
AI statement = scientific evidence

شود.
________________________________________
INV-009
AI نباید scientific authority داشته باشد.
AI می‌تواند:
interpret
summarize
retrieve
explain
rank
assist

کند.
اما نباید:
change equations
change model parameters silently
change provenance
change evidence status
declare scientific validity
override scientific constraints

کند.
________________________________________
INV-010
AI نباید مستقیماً scientific kernel را کنترل کند.
________________________________________
INV-011
Uncertainty نباید با confidence یا certainty یکی گرفته شود.
Agent باید بررسی کند:
uncertainty type
uncertainty value
uncertainty method
confidence
confidence interval
prediction interval
measurement error
model error
parameter uncertainty
propagation

کدام‌یک واقعاً وجود دارند و کدام‌یک ندارند.
________________________________________
INV-012
هر Decision باید traceable باشد.
زنجیره:
Decision
→ Recommendation
→ Options
→ Evidence
→ Model Outputs
→ Uncertainty
→ Constraints
→ Rationale

باید قابل بازسازی باشد.
________________________________________
INV-013
Software test ≠ scientific validation.
________________________________________
INV-014
Scientific validation باید evidence مستقل داشته باشد.
________________________________________
INV-015
Research code ≠ Production code.
________________________________________
7. Engine Gateway
Agent باید EngineGateway موجود را inspect کند.
نباید فقط وجود فایل را بررسی کند.
باید بررسی کند:
وجود
engine/gateway/

importability
from engine.gateway import EngineGateway

execution
Gateway باید واقعاً بتواند:
request
→ validation
→ model resolution
→ input validation
→ unit validation
→ provenance validation
→ execution
→ uncertainty/result handling
→ metadata
→ result

را انجام دهد.
اگر dispatch یا execution واقعی وجود ندارد، نباید Gateway را کامل اعلام کند.
________________________________________
8. Scientific Model Contract
Agent باید بررسی کند هر model حداقل دارای موارد زیر باشد:
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

هر موردی که missing است باید در registry گزارش شود.
________________________________________
9. Model Registry
Agent باید:
1.	تمام modelها را inventory کند.
2.	duplicateها را پیدا کند.
3.	model ID canonical ایجاد/تأیید کند.
4.	versioning را بررسی کند.
5.	maturity را بررسی کند.
6.	applicability domain را بررسی کند.
7.	validation evidence را بررسی کند.
8.	scientific review status را بررسی کند.
برای هر model یک وضعیت دقیق ثبت شود:
S0 UNKNOWN
S1 IDENTIFIED
S2 SPECIFIED
S3 IMPLEMENTED
S4 IMPLEMENTATION VERIFIED
S5 SCIENTIFICALLY VALIDATED
S6 PRODUCTION APPROVED

نباید S4 یا S5 صرفاً به دلیل وجود کد یا test ادعا شود.
________________________________________
10. Evidence Engine
Agent باید Evidence Engine را از نظر واقعی بودن implementation بررسی کند.
حداقل:
Evidence ID
Source
Source Type
Epistemic Type
Trust
Confidence
Timestamp
Location
Measurement
Unit
Quality
Provenance
Processing History
Model Reference
Uncertainty
License

اما صرفاً وجود این fields کافی نیست.
Agent باید بررسی کند:
validation logic
persistence behavior
provenance behavior
relationship handling
model reference integrity
uncertainty integrity
epistemic integrity

واقعاً کار می‌کنند یا خیر.
________________________________________
11. Knowledge Engine
Agent باید بررسی کند:
Fact
Claim
ClaimStatus
Evidence relation
Supporting evidence
Contradicting evidence
Confidence aggregation
Epistemic status
Provenance

وجود داشته باشند و رفتار آنها واقعاً تست شود.
________________________________________
12. Evidence ≠ Knowledge
Agent نباید این تبدیل را ساده فرض کند:
Evidence → Fact

باید مشخص باشد:
Evidence
→ interpretation
→ epistemic classification
→ Fact/Claim

و معلوم باشد چه چیزی observation است و چه چیزی inference.
________________________________________
13. Uncertainty
Agent باید uncertainty را تا جایی که scientifically justified است پیاده‌سازی کند.
حداقل باید معماری این موارد را پشتیبانی کند:
measurement uncertainty
parameter uncertainty
model uncertainty
input uncertainty
output uncertainty
propagation
confidence interval
prediction interval
uncertainty method

اگر implementation علمی معتبر برای یک model هنوز وجود ندارد:
آن را جعل نکند.
و وضعیت:
NOT IMPLEMENTED

یا:
REQUIRES SCIENTIFIC IMPLEMENTATION

ثبت شود.
________________________________________
14. Decision Engine / Tasmimyar
Agent باید Decision Engine را ایجاد یا تکمیل کند.
Decision باید حداقل شامل:
decision_id
problem
objectives
constraints
options
scenarios
evidence
model_outputs
uncertainties
risks
tradeoffs
rationale
recommendation
confidence
limitations
provenance

باشد.
هر recommendation باید قابل trace باشد.
مثلاً:
Recommendation
↓
Option
↓
Scenario
↓
Evidence
↓
Model
↓
Input
↓
Source

اگر این chain قابل بازسازی نیست، Decision Engine ناقص است.
________________________________________
15. Service Gateway
این قسمت باید واقعاً اصلاح شود.
وجود:
EngineGateway

به‌تنهایی کافی نیست.
Agent باید تمام service code را search کند.
پیدا کند:
direct imports
direct kernel calls
direct Hydroma calls
direct scientific model calls

و آنها را بررسی کند.
هدف:
Service
→ EngineGateway
→ Model
→ Hydroma

نه:
Service
→ Hydroma internal module
→ C++ kernel

عدد فعلی:
100+ direct imports

باید دوباره محاسبه شود و پس از اصلاح:
before
after
remaining
justified exceptions

گزارش شود.
________________________________________
16. AI Boundary
Agent باید تمام AI modules را inventory کند.
بررسی:
AI → Engine
AI → Scientific Kernel
AI → Model Registry
AI → Evidence
AI → Knowledge
AI → Decision

باید dependencyهای مجاز و غیرمجاز مشخص شوند.
AI نباید scientific authority باشد.
________________________________________
17. Database Boundary
Agent باید دوباره کل repository را scan کند.
نه فقط فایل‌هایی که در ECO-04.3 تغییر کرده‌اند.
جستجو برای:
database
sqlalchemy
duckdb
sqlite
session
engine
hub
Base

و dependency graph.
هدف:
Engine → Database = 0

است.
همچنین باید بررسی کند آیا:
PersistencePort

واقعاً abstraction است یا فقط database import را به جای دیگری منتقل کرده است.
________________________________________
18. C++ / Python Boundary
Agent باید:
1.	source files را inventory کند.
2.	Python bridge را inspect کند.
3.	binding technology را مشخص کند.
4.	ABI/build configuration را بررسی کند.
5.	موجود بودن binary را ثبت کند.
6.	source/binary version compatibility را بررسی کند.
7.	compiler availability را بررسی کند.
8.	build را اگر ممکن بود اجرا کند.
9.	اگر ممکن نبود دقیقاً NOT EXECUTED بنویسد.
10.	performance claims قبلی را بدون benchmark معتبر تکرار نکند.
________________________________________
19. Environment
Agent باید environment را دوباره بررسی کند.
ثبت:
OS
Python
pip
compiler
CMake
numpy
scipy
pandas
pytest
pydantic
pybind11
duckdb
other required dependencies
network
virtual environment

اگر dependency نصب نیست:
ابتدا تلاش استاندارد برای نصب طبق project manifest انجام شود.
اگر network unavailable است:
BLOCKED BY ENVIRONMENT

ثبت شود.
Fake package ممنوع.
________________________________________
20. Test Strategy
Agent باید سه سطح test را از هم جدا کند.
Level 1 — Static
imports
dependency rules
architecture
cycles
API contracts

Level 2 — Software Runtime
unit tests
integration tests
gateway tests
evidence tests
knowledge tests
decision tests
service tests

Level 3 — Scientific Validation
reference values
published benchmarks
analytical solutions
known datasets
domain expert evidence
sensitivity analysis
boundary tests
unit consistency
numerical stability
applicability domain

هیچ سطحی نباید جای سطح دیگر معرفی شود.
________________________________________
21. Scientific Validation
Agent باید برای تمام modelهای مهم بررسی کند:
Formula
Source
Assumptions
Units
Inputs
Outputs
Applicability
Boundary conditions
Numerical method
Reference
Validation evidence
Known limitations

خصوصاً مدل‌های قبلی identified شده:
Theis
Climate Data Assimilation
Hargreaves ET0
SCS-CN
Darcy
Soil Salinity
Surface Water
Radiation
Terrain
Slope / Aspect
Groundwater

اگر validation واقعی انجام نشده:
REQUIRES SCIENTIFIC REVIEW

و نباید VERIFIED نوشته شود.
________________________________________
22. Contradiction Detection
Agent باید تمام گزارش‌های قبلی ECO-00 تا ECO-04 را با repository فعلی تطبیق دهد.
هر contradiction باید ثبت شود.
مثلاً:
Report says COMPLETE
Code says PARTIAL

یا:
Report says 0 violations
Current scan says 7

یا:
Report says implemented
Runtime import fails

یا:
Report says verified
No executable test exists

این موارد باید در:
REPORT-RECONCILIATION.md

ثبت شوند.
________________________________________
23. Canonical Inventory
Agent باید یک inventory نهایی ایجاد کند.
حداقل:
all engines
all services
all models
all gateways
all ports
all evidence types
all epistemic types
all AI modules
all database dependencies
all C++ modules
all tests
all reports
all architectural rules

هیچ موردی نباید صرفاً با حدس inventory شود.
________________________________________
24. Required New Reports
Agent باید در پایان این فایل‌ها را تولید یا به‌روزرسانی کند:
reports/eco-04/

الزامی:
21-FINAL-ARCHITECTURE-AUDIT.md
22-FINAL-DEPENDENCY-AUDIT.md
23-FINAL-MODEL-VALIDATION-MATRIX.md
24-FINAL-EVIDENCE-KNOWLEDGE-AUDIT.md
25-FINAL-UNCERTAINTY-AUDIT.md
26-FINAL-DECISION-AUDIT.md
27-FINAL-AI-BOUNDARY-AUDIT.md
28-FINAL-SERVICE-GATEWAY-AUDIT.md
29-FINAL-CPP-PYTHON-AUDIT.md
30-FINAL-TEST-EXECUTION.md
31-FINAL-SCIENTIFIC-VALIDATION.md
32-REPORT-RECONCILIATION.md
33-FINAL-BLOCKER-REGISTER.md
34-FINAL-FILE-INVENTORY.md
35-FINAL-VALIDATION.md
36-FINAL-MACHINE-SUMMARY.json

________________________________________
25. FINAL-VALIDATION.md
این فایل مهم‌ترین خروجی ECO-04 است.
باید تمام واقعیت ECO-04 در یک فایل نهایی قابل خواندن باشد.
حداقل ساختار:
1. Executive Summary

2. Actual Final Status

3. Environment

4. Architecture Status

5. Architecture Invariants

6. Engine Gateway

7. Persistence Boundary

8. Scientific Model Registry

9. Evidence Engine

10. Knowledge Engine

11. Epistemic Model

12. Provenance

13. Uncertainty

14. Decision Engine

15. Service Gateway

16. AI Boundary

17. C++ / Python Boundary

18. Test Execution

19. Scientific Validation

20. Security

21. Performance

22. Dependency Graph

23. Missing Components

24. Partial Components

25. Failed Components

26. Deferred Components

27. Blockers

28. Contradictions with Previous Reports

29. Files Created

30. Files Modified

31. Files Deleted

32. Verification Commands

33. Verification Results

34. Evidence Index

35. Final Gate Decision

36. Next Allowed Phase

________________________________________
26. برای هر component یک جدول اجباری
برای هر بخش:
Component	Exists	Implemented	Executable	Tested	Verified	Scientific Validated	Production Ready	Evidence
Engine Gateway						N/A/YES/NO		
Evidence Engine								
Knowledge Engine								
Model Registry								
Uncertainty								
Decision Engine								
Service Gateway								
AI Boundary								
Provenance								
C++ Boundary								
هیچ خانه‌ای نباید بدون evidence پر شود.
________________________________________
27. Verification Commands
Agent باید commandهای واقعی مورد استفاده را ثبت کند.
مثلاً:
python -c "import engine"
python -c "from engine.gateway import EngineGateway"
python -m pytest
python tools/detect_imports.py

و هر command باید result واقعی داشته باشد:
PASS
FAIL
BLOCKED
NOT EXECUTED

________________________________________
28. Evidence Index
برای هر claim مهم:
CLAIM
EVIDENCE
COMMAND / FILE
RESULT
DATE
STATUS

مثلاً:
Claim:
Engine → Database = 0

Evidence:
tools/detect_imports.py

Result:
946 files scanned
0 violations

Status:
VERIFIED

________________________________________
29. Missing vs Deferred
این دو نباید یکی شوند.
NOT IMPLEMENTED
یعنی وجود ندارد.
PARTIAL
بخشی وجود دارد.
SCAFFOLDING
ساختار اولیه وجود دارد ولی implementation کامل نیست.
DEFERRED
عمداً به phase بعد منتقل شده.
BLOCKED
به دلیل مانع خارجی قابل اجرا نیست.
FAILED
اجرا شد ولی شکست خورد.
VERIFIED
با evidence قابل بازتولید اثبات شده.
________________________________________
30. Final Status Rules
Agent فقط یکی از این statusها را انتخاب کند:
BLOCKED

اگر blocker بحرانی مانع ادامه واقعی است.
یا:
IMPLEMENTED_WITH_LIMITATIONS

اگر implementation واقعی وجود دارد ولی validation/integration کامل نیست.
یا:
READY_FOR_INTEGRATION

فقط اگر:
architecture invariants pass
required implementation complete
tests executable
critical tests pass
scientific validation requirements satisfied
no critical boundary violations
no unresolved P0/P1 blockers

یا:
READY_FOR_ECO_05

فقط زمانی که ECO-04 واقعاً Gate شده باشد.
________________________________________
31. معیار مهم
وجود این موارد به‌تنهایی هرگز کافی نیست:
file exists
class exists
function exists
import succeeds
manual test succeeds
report says PASS

برای production readiness باید:
architecture
+
implementation
+
runtime
+
automated tests
+
scientific validation where applicable
+
security
+
dependency verification
+
traceability

وجود داشته باشد.
________________________________________
32. اصلاح Report 19
Agent باید Report 19 فعلی را کورکورانه حفظ نکند.
باید آن را با شواهد جدید reconcile کند.
اگر Report 19 نوشته:
IMPLEMENTED — READY FOR INTEGRATION

ولی evidence نشان می‌دهد:
Decision = NOT IMPLEMENTED
Service Gateway = VIOLATED
Tests = 0 executed
Scientific validation = deferred

Final Report باید status واقعی را اصلاح کند.
Report نباید واقعیت را override کند.
________________________________________
33. هیچ کار نیمه‌تمامی مخفی نشود
هر مورد زیر باید در Final Report ظاهر شود:
missing
partial
stub
placeholder
deprecated
legacy
duplicate
unknown
blocked
failed
deferred
not tested
not scientifically validated
not build verified

________________________________________
34. عدم حذف بدون evidence
Agent حق ندارد برای تمیز کردن repository فایل یا کدی را صرفاً به دلیل قدیمی بودن حذف کند.
برای حذف باید:
reason
dependency analysis
replacement
test evidence
rollback consideration

ثبت شود.
________________________________________
35. تغییرات باید قابل ردیابی باشند
برای هر تغییر:
file
change
reason
architectural purpose
risk
verification

ثبت شود.
________________________________________
36. اجرای خودکار مراحل
Agent باید بدون توقف غیرضروری این چرخه را تکرار کند:
SCAN
 ↓
CLASSIFY
 ↓
FIX
 ↓
TEST
 ↓
VERIFY
 ↓
RESCAN
 ↓
RECONCILE
 ↓
FIX AGAIN IF NEEDED
 ↓
FINAL VALIDATION

اگر بعد از fix دوباره violation پیدا شد، کار تمام نشده است.
________________________________________
37. Definition of Done
ECO-04 فقط زمانی Done است که Agent بتواند پاسخ مستند و قابل بازتولید برای این سؤال‌ها بدهد:
آیا معماری واقعاً enforce شده؟
آیا Engine از Database جداست؟
آیا Engine از Services جداست؟
آیا Services از Gateway استفاده می‌کنند؟
آیا AI scientific authority نیست؟
آیا Evidence و Knowledge از هم تفکیک شده‌اند؟
آیا provenance واقعاً قابل ردیابی است؟
آیا epistemic status مشخص است؟
آیا uncertainty واقعی است یا فقط field؟
آیا Decision قابل trace است؟
آیا Model Registry canonical است؟
آیا C++/Python boundary واقعاً verified است؟
آیا tests واقعاً اجرا شده‌اند؟
آیا scientific validation واقعاً انجام شده؟
چه چیزهایی وجود ندارد؟
چه چیزهایی ناقص است؟
چه چیزهایی blocked است؟
چه چیزهایی deferred است؟
چه چیزهایی واقعاً verified است؟

اگر پاسخ هرکدام:
UNKNOWN

باشد، باید همان‌طور در Final Report ثبت شود.
________________________________________
38. مهم‌ترین قانون Final Report
Final Report باید بتواند بدون مراجعه به 20 گزارش قبلی وضعیت واقعی ECO-04 را توضیح دهد.
خواننده باید از همان یک فایل بفهمد:
WHAT EXISTS
WHAT DOES NOT EXIST
WHAT WORKS
WHAT DOES NOT WORK
WHAT IS TESTED
WHAT IS NOT TESTED
WHAT IS SCIENTIFICALLY VALIDATED
WHAT IS NOT
WHAT IS BLOCKED
WHAT IS DEFERRED
WHAT VIOLATIONS REMAIN
WHAT WAS FIXED
WHAT EVIDENCE PROVES EACH CLAIM
WHAT MUST HAPPEN NEXT

________________________________________
39. Machine Readable Summary
فایل:
reports/eco-04/36-FINAL-MACHINE-SUMMARY.json

باید شامل حداقل:
{
  "phase": "ECO-04",
  "status": "...",
  "environment": {},
  "architecture": {},
  "invariants": {},
  "gateway": {},
  "database_boundary": {},
  "model_registry": {},
  "evidence_engine": {},
  "knowledge_engine": {},
  "epistemic": {},
  "provenance": {},
  "uncertainty": {},
  "decision_engine": {},
  "service_gateway": {},
  "ai_boundary": {},
  "cpp_python": {},
  "tests": {},
  "scientific_validation": {},
  "security": {},
  "blockers": [],
  "deferred": [],
  "missing": [],
  "partial": [],
  "verified": [],
  "unknown": [],
  "next_phase": "..."
}

________________________________________
40. Final Gate
در پایان Agent باید یک جدول Gate ارائه کند:
Gate	Requirement	Result	Evidence
G-01	Environment		
G-02	Engine Import		
G-03	Architecture		
G-04	Dependency Boundary		
G-05	Gateway		
G-06	Model Registry		
G-07	Evidence		
G-08	Knowledge		
G-09	Epistemic		
G-10	Provenance		
G-11	Uncertainty		
G-12	Decision		
G-13	Service Gateway		
G-14	AI Isolation		
G-15	C++ Boundary		
G-16	Automated Tests		
G-17	Scientific Validation		
G-18	Security		
G-19	Reconciliation		
G-20	Final Readiness		
________________________________________
41. دستور نهایی به Agent
از همین لحظه:
DO NOT ASK FOR PERMISSION TO INSPECT.
DO NOT ASK FOR PERMISSION TO FIX.
DO NOT ASK FOR PERMISSION TO TEST.
DO NOT ASK FOR PERMISSION TO RECONCILE.
DO NOT ASK FOR PERMISSION TO UPDATE REPORTS.

Agent باید مستقلانه کار را ادامه دهد.
اما:
DO NOT INVENT.
DO NOT FAKE.
DO NOT HIDE.
DO NOT DOWNGRADE.
DO NOT MISLABEL.
DO NOT CALL SCAFFOLDING IMPLEMENTATION.
DO NOT CALL MANUAL VERIFICATION AUTOMATED TESTING.
DO NOT CALL SOFTWARE TEST SCIENTIFIC VALIDATION.
DO NOT CALL CONFIDENCE UNCERTAINTY.
DO NOT CALL EXISTENCE COMPLETENESS.

هرجا evidence کافی نیست:
UNKNOWN

هرجا implementation ناقص است:
PARTIAL

هرجا محیط مانع است:
BLOCKED

هرجا واقعاً ثابت شده:
VERIFIED

________________________________________
42. دستور اجرایی نهایی
Agent باید اکنون:
1. Repository را کامل scan کند.
2. ECO-00 تا ECO-04 را با code تطبیق دهد.
3. تمام contradictions را پیدا کند.
4. معماری فعلی را reconstruct کند.
5. dependency graph واقعی بسازد.
6. تمام invariants را verify کند.
7. violations را اصلاح کند.
8. Gateway را واقعاً executable کند.
9. Evidence را واقعاً قابل ردیابی کند.
10. Knowledge را با epistemic semantics تکمیل کند.
11. Provenance را واقعی کند.
12. Uncertainty را فقط در صورت scientific validity پیاده کند.
13. Decision Engine را طبق contract پیاده کند.
14. Services را به Gateway منتقل کند.
15. AI boundary را enforce کند.
16. C++/Python boundary را verify کند.
17. environment را دوباره validate کند.
18. تمام تست‌های قابل اجرا را اجرا کند.
19. scientific validation را هرجا ممکن است اجرا کند.
20. موارد غیرقابل اجرا را صریحاً ثبت کند.
21. دوباره repository را scan کند.
22. دوباره invariantها را اجرا کند.
23. تمام گزارش‌های قبلی را reconcile کند.
24. Final Architecture Audit را تولید کند.
25. Final Validation را تولید کند.
26. Machine Summary را تولید کند.
27. Final Gate را صادر کند.
28. فقط سپس ECO-04 را ببندد.

________________________________________
43. آخرین و مهم‌ترین اصل
هدف:
NOT:
"Create the files required by ECO-04."

هدف:
"Make the repository actually conform to ECO-04."

و سپس:
"Create the files that prove it."

ترتیب غیرقابل تغییر:
REAL ARCHITECTURE
        ↓
REAL IMPLEMENTATION
        ↓
REAL ENFORCEMENT
        ↓
REAL TESTING
        ↓
REAL SCIENTIFIC VALIDATION
        ↓
REAL VERIFICATION
        ↓
REAL REPORT
        ↓
FINAL GATE

ECO-04 زمانی تمام شده است که repository بتواند ادعاهای Final Report را با evidence قابل بازتولید ثابت کند، نه زمانی که تعداد مشخصی فایل ایجاد شده باشد.
________________________________________
END OF ECO-04 EXECUTION DIRECTIVE

