ECO-03
ARCHITECTURE HARDENING, RECONCILIATION & IMPLEMENTATION SPECIFICATION
Project: Eco Nojin / اکو نوژین
 Phase: ECO-03
 Status: EXECUTION INSTRUCTION
 Priority: CRITICAL
 Type: Architecture Hardening + Reconciliation + Implementation Specification
 Implementation Scope: NONE
 Production Feature Development: FORBIDDEN
 Required Output: COMPLETE FORENSIC + ARCHITECTURAL + IMPLEMENTATION-READINESS REPORT
________________________________________
> **Implementation status (verified 2026-10-11)**
> ECO-03 یک گیت آمادگی بود؛ وضعیت آنچه امروز واقعاً آماده است، در ادامه ثبت شده است.
> وضعیت‌های «STUB» موجود در بدنهٔ سند بخشی از وظایف ECO-03 هستند (باید موجودی را طبقه‌بندی کند)،
> ادعای وضعیت نیستند و دست‌نخورده می‌مانند.
>
> | گیت آمادگی که ECO-03 خواسته بود | واقعیت ۲۰۲۶-۱۰-۱۱ | شواهد |
> |---|---|---|
> | شدو (hardened) بودن مرزها با ابزار | `tools/detect_imports.py` + `tools/import_guard_policy.json` + ADR-014 اجرا می‌شوند و در CI گیت‌اند | `.github/workflows/ci.yml:197` |
> | import guard PASS | **FAIL — ۱۶ تخلف** در `services/_gateway_facade_adapters/` | `python tools/detect_imports.py --root .` |
> | داشبورد واقعیِ داشبورد | هنوز OPEN (AR-08/G-H2) | — |
>
> **نکتهٔ مستندسازی:** جدول «Service count» در بدنه (۷۳ → ۸ bounded context) با شمارش امروز
> (۷۰ زیربستهٔ عمومی) سازگار نیست؛ اما این سند وظیفه داشت «اختلاف را ثبت» کند و این کار را
> کرده. یادداشت قطعی شمار در `README.md` نگه داشته شده است.
________________________________________
 0. مأموریت اصلی
تو در این مرحله نباید پلتفرم را پیاده‌سازی کنی.
مأموریت تو این است که معماری ECO-02 را از حالت «تعریف‌شده روی کاغذ» به یک معماری:
●	قابل اثبات
●	قابل تست
●	قابل اجرا
●	قابل پیاده‌سازی
●	قابل نگهداری
●	قابل توسعه
●	و بدون تناقض
تبدیل کنی.
ECO-03 باید مشخص کند که آیا معماری فعلی واقعاً آماده ورود به فاز implementation است یا خیر.
اصل بنیادین:
ECO-00
Forensic Audit
        ↓
ECO-01
Scientific / Knowledge Forensics
        ↓
ECO-02
Canonical Architecture
        ↓
ECO-03
Architecture Reconciliation + Hardening
        ↓
ECO-04
Controlled Implementation

تو در ECO-03 فقط تا مرز آمادگی برای ECO-04 پیش می‌روی.
________________________________________
1. قوانین غیرقابل مذاکره
در این مرحله موارد زیر ممنوع هستند:
●	ساخت Frontend
●	ساخت UI
●	ساخت Database
●	ساخت Migration
●	ساخت API نهایی
●	ساخت OpenAPI نهایی
●	ساخت Authentication
●	ساخت Payment
●	ساخت Wallet
●	ساخت Blockchain
●	ساخت Smart Contract
●	ساخت Admin/CMS
●	ساخت محصول نهایی
●	پیاده‌سازی کامل سرویس‌ها
●	بازنویسی گسترده engine
●	بازنویسی گسترده services
●	ساخت مدل علمی جدید
●	تغییر معادلات علمی
●	تغییر پارامترهای علمی بدون Scientific Review
●	ساخت مدل ML/AI جدید
●	افزودن منطق علمی حدسی
●	حذف فایل‌های legacy به‌صورت کور
●	انتقال مستقیم Smart Contractهای پروژه قدیمی
________________________________________
2. قانون «گزارش کامل»
ECO-03 بدون گزارش کامل موفق محسوب نمی‌شود.
هر ادعا باید تا حد امکان با یکی از موارد زیر پشتیبانی شود:
file path
line / symbol
dependency
import
test result
static analysis result
source evidence
ECO-00 report
ECO-01 report
ECO-02 report
ADR
contract

عباراتی مانند:
verified
resolved
safe
production-ready
canonical
isolated
independent
complete

را بدون evidence استفاده نکن.
اگر چیزی فقط از نظر معماری طراحی شده ولی در source code اثبات نشده، صریحاً بنویس:
DESIGNED BUT NOT ENFORCED

اگر بررسی نشده:
NOT VERIFIED

اگر شواهد متناقض است:
CONFLICTING EVIDENCE

اگر نیاز به بررسی علمی دارد:
REQUIRES SCIENTIFIC REVIEW

________________________________________
3. مرحله اول: Architecture Reconciliation Gate
ابتدا تمام خروجی‌های ECO-00، ECO-01 و ECO-02 را دوباره بررسی کن.
هیچ implementation planning را قبل از حل تناقضات انجام نده.
3.1 تناقض تعداد Bounded Contextها
ECO-02 عدد 8 را به‌عنوان target مطرح کرده است.
اما در ECO-01 مشخص شد که تعداد زیاد services شامل:
●	duplicate
●	legacy
●	obsolete
●	unknown
●	reusable domain logic
●	infrastructure
●	scientific logic
است.
بنابراین بررسی کن:
73 services
        ↓
candidate bounded contexts
        ↓
validated bounded contexts
        ↓
actual canonical contexts

نباید صرفاً بگویی:
73 → 8

باید ثابت کنی:
●	چرا هر service در context خاص قرار می‌گیرد
●	چرا دو service باید merge شوند
●	چرا service خاص باید حذف یا obsolete شود
●	چرا context جدید لازم است
●	dependency direction چیست
●	ownership هر domain چیست
اگر عدد 8 اشتباه است، آن را اصلاح کن.
معماری را به عدد قبلی مجبور نکن.
________________________________________
4. Scientific Maturity Reconciliation
طبقه‌بندی علمی ECO-01 و ECO-02 را تطبیق بده.
به‌خصوص اختلاف‌های احتمالی درباره:
CODE_ONLY
IMPLEMENTATION_VERIFIED
SCIENTIFICALLY_SUPPORTED
VERIFIED
STUB
REQUIRES_SCIENTIFIC_REVIEW

باید به یک taxonomy واحد تبدیل شود.
برای هر scientific model مشخص کن:
model_id
canonical_name
domain
implementation_status
scientific_status
validation_status
maturity_level
evidence
limitations
owner
review_required

نباید:
software test passed

را معادل:
scientifically validated

بدانی.
________________________________________
5. CANON-001 Reconciliation
اگر CANON-001 برای Penman-Monteith تعریف شده، مشخص کن که آیا:
CANON-001

واقعاً یک canonical scientific model identifier است یا صرفاً یک label در گزارش.
در صورت نیاز آن را به قرارداد رسمی تبدیل کن:
model_id
model_version
equation_id
implementation_id
parameter_schema
unit_schema
validation_status
provenance

هیچ مدل علمی نباید فقط با نام مبهم شناخته شود.
________________________________________
6. AI Boundary Reconciliation
عبارت:
Evidence → Decision → AI → User

را از نظر معماری بررسی کن.
مشخص کن:
●	AI چه چیزی را می‌تواند بخواند؟
●	AI چه چیزی را نمی‌تواند تغییر دهد؟
●	آیا conversational AI می‌تواند Knowledge context را دریافت کند؟
●	آیا AI می‌تواند Evidence را خلاصه کند؟
●	آیا AI می‌تواند Model Output را تفسیر کند؟
●	آیا AI می‌تواند recommendation تولید کند؟
●	آیا recommendation AI باید از Tasmimyar عبور کند؟
●	چه چیزی scientific authority محسوب می‌شود؟
●	آیا AI قادر به تغییر equation است؟
●	آیا AI قادر به تغییر parameter است؟
●	آیا AI قادر به تغییر provenance است؟
●	آیا AI قادر به تغییر epistemic status است؟
اصل غیرقابل مذاکره:
AI MAY INTERPRET.
AI MAY NOT SILENTLY AUTHORIZE SCIENCE.

________________________________________
7. بررسی واقعی Dependency Direction
معماری ECO-02 ادعا می‌کند:
Product
  ↓
Application
  ↓
Decision
  ↓
Knowledge
  ↓
Evidence
  ↓
Domain Services
  ↓
Engine Gateway
  ↓
Hydroma
  ↓
C++ Kernels

این را از روی source code بررسی کن.
به‌خصوص:
engine → services
engine → database
engine → frontend
engine → application
engine → auth
engine → payment
engine → blockchain
AI → engine internals
service → engine internals

را جست‌وجو کن.
نتیجه را در matrix زیر ثبت کن:
Boundary	Expected	Actual	Status	Evidence
هیچ boundary را صرفاً با ادعای report معتبر ندان.
________________________________________
8. Engine Gateway Contract
Engine Gateway باید به یک contract دقیق تبدیل شود.
مشخص کن:
request
validation
model selection
unit normalization
parameter validation
execution
uncertainty propagation
provenance capture
result normalization
error normalization

برای هر مرحله مشخص کن:
●	input
●	output
●	owner
●	dependencies
●	failure modes
●	test requirements
Engine Gateway نباید محل business logic محصول شود.
________________________________________
9. Scientific Model Contract
قرارداد canonical مدل علمی را نهایی کن.
حداقل:
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

مشخص کن کدام بخش:
required
optional
runtime
registry-only
scientific-review-only

است.
________________________________________
10. Units & Dimensional Analysis Contract
تمام scientific input/output ها را بررسی کن.
حداقل:
SI canonical units
conversion boundary
dimensional validation
temperature conventions
pressure conventions
time conventions
area/volume conventions
water-depth conventions
soil EC conventions
coordinate conventions

هیچ unit conversion نباید در چند نقطه به‌صورت پراکنده انجام شود.
________________________________________
11. Uncertainty Contract
Uncertainty باید first-class باشد.
مشخص کن:
uncertainty type
uncertainty value
confidence
confidence interval
error bounds
source of uncertainty
propagation method
unknown uncertainty

و تفاوت این موارد را ثبت کن:
unknown
not measured
not modeled
low confidence
high uncertainty
high confidence
validated

قانون:
absence of uncertainty data ≠ certainty

________________________________________
12. Daneshyar Contract
Knowledge Engine را از Evidence Engine جدا نگه دار.
Epistemic types:
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

برای هر type مشخص کن:
definition
required metadata
source
confidence
provenance
validation
review
allowed transformations

به‌خصوص بررسی کن که:
LOCAL_KNOWLEDGE ≠ SCIENTIFIC_FACT

MODEL_OUTPUT ≠ OBSERVATION

INFERENCE ≠ MEASUREMENT

________________________________________
13. Evidence Engine Contract
Evidence Engine باید مشخص کند:
source
observation
processing
model input
execution
model output
decision input
decision

برای هر evidence:
evidence_id
source_id
source_type
epistemic_type
timestamp
location
unit
quality
confidence
provenance
license
processing_history
validation_status

را بررسی کن.
اگر metadata فعلاً وجود ندارد، آن را به‌عنوان implementation requirement ثبت کن، نه اینکه missing را «verified» اعلام کنی.
________________________________________
14. Tasmimyar Contract
Decision chain را دقیق کن:
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

برای هر component:
required?
source?
owner?
validation?
can AI generate it?
can AI modify it?

را مشخص کن.
________________________________________
15. Service Consolidation Specification
تمام 73 service را به یک registry canonical تبدیل کن.
برای هر service:
service_id
path
current_role
domain
dependencies
dependents
classification
bounded_context
canonical_owner
duplicate_of
replacement
migration_strategy
disposition
risk

Dispositionها حداقل:
KEEP
REPAIR
MERGE
MOVE
DEPRECATE
OBSOLETE
RESEARCH_ONLY
UNKNOWN

هیچ service را فقط به دلیل نام آن حذف یا merge نکن.
________________________________________
16. Hydroma Extraction Plan
Hydroma را از legacy application infrastructure جدا کن.
Target:
Hydroma
├── scientific models
├── numerical methods
├── domain scientific logic
├── validation
├── provenance
├── uncertainty
└── engine gateway boundary

و نباید مستقیماً وابسته باشد به:
database
frontend
HTTP framework
auth
payment
wallet
blockchain
application workflow
UI

مشخص کن برای هر dependency:
keep
replace
invert
adapter
remove
defer

________________________________________
17. C++ / Python Boundary
مشخص کن:
C++ owns numerical kernels
Python owns orchestration

و contract دقیق برای:
ABI
memory ownership
array layout
dtype
endianness
exceptions
error propagation
threading
parallelism
build system
compiler
Python version
pybind11 / ctypes
buffer protocol

ارائه کن.
هیچ ادعای performance بدون benchmark معتبر نکن.
اگر ECO-01 گفته:
10x
50x
100x
200x

بررسی کن که evidence واقعی وجود دارد یا نه.
________________________________________
18. Architecture Test Specification
مشخص کن چه تست‌هایی باید در ECO-04 ساخته شوند.
حداقل:
import boundary tests
dependency direction tests
engine purity tests
AI isolation tests
model registry integrity tests
unit consistency tests
provenance tests
uncertainty propagation tests
epistemic type tests
service ownership tests
C++/Python boundary tests
legacy dependency detection

برای هر test:
test_id
purpose
input
expected result
failure condition
automation method
priority

________________________________________
19. Canonical Repository / Package Map
ساختار پیشنهادی implementation را مشخص کن.
اما هنوز آن را پیاده‌سازی نکن.
مثلاً در سطح مفهومی:
engine/
  gateway/
  scientific/
  numerical/
  provenance/
  uncertainty/
  validation/

knowledge/
  daneshyar/

evidence/

decision/
  tasmimyar/

services/
  canonical-contexts/

ai/
  interpretation/
  research/

cpp/
  kernels/

اگر ساختار بهتری پیدا کردی، همان را پیشنهاد بده.
مهم:
architecture must follow responsibility,
not historical directory structure.

________________________________________
20. Legacy Extraction Map
مشخص کن از پروژه قدیمی:
KEEP
EXTRACT
REWRITE
ADAPT
REFERENCE ONLY
DO NOT TRANSFER

برای:
engine/
services/
smart_contracts/
database/
frontend/
AI

Smart Contracts باید:
REFERENCE ONLY

باشند مگر اینکه در فاز مستقل blockchain architecture دوباره از صفر طراحی شوند.
________________________________________
21. Implementation Dependency DAG
یک dependency graph دقیق برای ECO-04 بساز.
مثال:
Scientific Contracts
        ↓
Units / Validation
        ↓
Engine Gateway
        ↓
Hydroma Canonicalization
        ↓
Evidence
        ↓
Knowledge
        ↓
Decision
        ↓
Domain Services
        ↓
Application
        ↓
Product

اگر dependency واقعی متفاوت است، آن را اصلاح کن.
________________________________________
22. ECO-04 Build Order
ترتیب implementation را مشخص کن.
هر مرحله باید dependency و acceptance criteria داشته باشد.
مثلاً:
ECO-04.1
Canonical repository skeleton

ECO-04.2
Scientific contracts

ECO-04.3
Engine Gateway

ECO-04.4
Hydroma extraction

ECO-04.5
Evidence infrastructure

ECO-04.6
Daneshyar core

ECO-04.7
Tasmimyar core

ECO-04.8
Canonical services

ECO-04.9
Application layer

ECO-04.10
Product/API/UI phases

این فقط نمونه است.
ترتیب واقعی را بر اساس dependency analysis تعیین کن.
________________________________________
23. Risk Register
حداقل این دسته‌ها را بررسی کن:
scientific risk
architectural risk
dependency risk
legacy risk
security risk
data integrity risk
unit risk
uncertainty risk
AI risk
performance risk
C++ ABI risk
service consolidation risk
migration risk
provenance risk
knowledge integrity risk
decision integrity risk

برای هر risk:
risk_id
description
probability
impact
severity
evidence
mitigation
owner
blocking?

________________________________________
24. Architecture Invariants
این invariants باید به‌صورت رسمی ثبت شوند.
حداقل:
INV-001
Engine never depends on UI.

INV-002
Engine never depends directly on database.

INV-003
Scientific models cannot be silently modified by AI.

INV-004
AI cannot change scientific equations.

INV-005
AI cannot change provenance.

INV-006
AI cannot change epistemic status.

INV-007
Model output is not observation.

INV-008
Local knowledge is not automatically scientific fact.

INV-009
Software test success is not scientific validation.

INV-010
Recommendation requires traceable evidence.

INV-011
Uncertainty absence is not certainty.

INV-012
Units must be explicit.

INV-013
Scientific model identity must be versioned.

INV-014
Legacy directory structure is not canonical architecture.

INV-015
Smart contracts from the old project are not production contracts.

اگر invariant دیگری لازم است، اضافه کن.
________________________________________
25. Required Reports
تمام خروجی‌ها را در:
reports/eco-03/

قرار بده.
حداقل فایل‌های زیر را ایجاد کن:
00-FINAL-VALIDATION.md

01-ARCHITECTURE-RECONCILIATION.md
02-ARCHITECTURE-VIOLATIONS.md
03-BOUNDED-CONTEXT-REGISTRY.md
04-SCIENTIFIC-MATURITY-RECONCILIATION.md
05-CANONICAL-SCIENTIFIC-CONTRACT.md
06-ENGINE-GATEWAY-SPEC.md
07-HYDROMA-EXTRACTION-SPEC.md
08-UNITS-AND-DIMENSIONAL-CONTRACT.md
09-UNCERTAINTY-CONTRACT.md
10-EVIDENCE-CONTRACT.md
11-DANESHYAR-CONTRACT.md
12-TASMIMYAR-CONTRACT.md
13-AI-BOUNDARY-CONTRACT.md
14-SERVICE-CONSOLIDATION-REGISTRY.md
15-CPP-PYTHON-BOUNDARY-SPEC.md
16-ARCHITECTURE-TEST-SPEC.md
17-LEGACY-EXTRACTION-MAP.md
18-REPOSITORY-STRUCTURE-SPEC.md
19-IMPLEMENTATION-DEPENDENCY-DAG.md
20-ECO-04-BUILD-PLAN.md
21-RISK-REGISTER.md
22-ARCHITECTURE-INVARIANTS.md
23-OPEN-QUESTIONS.md
24-SCIENTIFIC-REVIEW-QUEUE.md
25-IMPLEMENTATION-BLOCKERS.md
26-MACHINE-READABLE-SUMMARY.md

در صورت نیاز فایل بیشتری اضافه کن.
________________________________________
26. Final Validation
در پایان، یک validation کامل اجرا کن.
بررسی کن:
Architecture
●	[ ] dependency direction verified
●	[ ] bounded contexts evidence-based
●	[ ] service ownership defined
●	[ ] no unexplained architectural contradiction
Science
●	[ ] model taxonomy reconciled
●	[ ] scientific status separated from software status
●	[ ] canonical model IDs defined
●	[ ] scientific review queue preserved
Hydroma
●	[ ] engine boundaries explicit
●	[ ] legacy dependencies identified
●	[ ] Engine Gateway contract defined
●	[ ] C++/Python boundary defined
Knowledge
●	[ ] epistemic types defined
●	[ ] provenance defined
●	[ ] evidence separated from knowledge
●	[ ] uncertainty defined
Decision
●	[ ] alternatives defined
●	[ ] risks defined
●	[ ] rationale defined
●	[ ] confidence defined
●	[ ] evidence traceability defined
AI
●	[ ] AI authority boundaries defined
●	[ ] scientific bypass impossible by design
●	[ ] provenance mutation prohibited
●	[ ] epistemic mutation prohibited
Services
●	[ ] all 73 services accounted for
●	[ ] no unexplained service omitted
●	[ ] duplicates identified
●	[ ] obsolete services identified
●	[ ] migration/extraction strategy defined
Implementation readiness
●	[ ] repository structure specified
●	[ ] contracts specified
●	[ ] tests specified
●	[ ] dependency DAG specified
●	[ ] ECO-04 build sequence specified
●	[ ] blockers identified
________________________________________
27. مهم‌ترین قانون گزارش نهایی
اگر چیزی را نتوانستی بررسی کنی، ننویس:
PASS

بنویس:
NOT VERIFIED

اگر معماری آن را تعریف کرده ولی enforcement وجود ندارد:
DESIGNED BUT NOT ENFORCED

اگر evidence متناقض است:
CONFLICTING EVIDENCE

اگر نیاز به دانش علمی بیرونی یا expert review دارد:
REQUIRES SCIENTIFIC REVIEW

اگر مانع ECO-04 است:
BLOCKING

________________________________________
28. Final Status
در پایان فقط یکی از این وضعیت‌ها را انتخاب کن:
READY_FOR_ECO_04

یا:
READY_WITH_LIMITATIONS

یا:
BLOCKED

یا:
REQUIRES_SCIENTIFIC_REVIEW

انتخاب status باید بر اساس evidence باشد.
________________________________________
29. خروجی نهایی برای کارفرما
فایل:
reports/eco-03/00-FINAL-VALIDATION.md

باید شامل این بخش‌ها باشد:
1. Executive Summary

2. What Was Verified

3. What Was Not Verified

4. Architecture Contradictions Found

5. Contradictions Resolved

6. Contradictions Remaining

7. Scientific Validation Status

8. Hydroma Status

9. Evidence Engine Status

10. Daneshyar Status

11. Tasmimyar Status

12. AI Boundary Status

13. Service Consolidation Status

14. C++ / Python Status

15. Legacy Extraction Status

16. Security Findings

17. Performance Findings

18. Open Questions

19. Scientific Review Requirements

20. ECO-04 Blockers

21. ECO-04 Build Sequence

22. Final Architecture Readiness

23. Final Status

در Executive Summary به‌صورت شفاف جواب بده:
آیا معماری ECO-02 واقعاً قابل پیاده‌سازی است؟
کدام قسمت‌ها اثبات شده‌اند؟
کدام قسمت‌ها فقط طراحی هستند؟
کدام قسمت‌ها هنوز متناقض‌اند؟
چه چیزهایی باید قبل از ECO-04 حل شوند؟
چه چیزهایی می‌توانند در ECO-04 حل شوند؟

________________________________________
30. ممنوعیت «گزارش تزئینی»
این مرحله نباید تبدیل شود به تولید تعداد زیادی Markdown بدون بررسی واقعی.
کیفیت ECO-03 بر اساس این سنجیده می‌شود:
Evidence
>
Traceability
>
Consistency
>
Enforceability
>
Implementation Readiness
>
Document Count

تعداد فایل گزارش معیار موفقیت نیست.
________________________________________
31. معیار موفقیت نهایی
ECO-03 فقط زمانی موفق است که یک agent دیگر بتواند فقط با خواندن:
ECO-00
ECO-01
ECO-02
ECO-03

بداند:
چه چیزی باید ساخته شود
چرا باید ساخته شود
کجا باید ساخته شود
چه چیزی نباید ساخته شود
چه چیزی از پروژه قدیمی منتقل شود
چه چیزی منتقل نشود
چه چیزی باید rewrite شود
چه چیزی باید adapter شود
چه dependencyهایی مجازند
چه dependencyهایی ممنوعند
scientific model چگونه شناخته می‌شود
evidence چگونه ثبت می‌شود
knowledge چگونه طبقه‌بندی می‌شود
uncertainty چگونه منتقل می‌شود
decision چگونه ساخته می‌شود
AI چه اختیاری دارد
AI چه اختیاری ندارد
serviceها چگونه consolidate می‌شوند
C++ و Python چگونه با هم ارتباط دارند
چه تست‌هایی لازم است
و ECO-04 دقیقاً از کجا باید شروع کند

اگر این شرط برقرار نیست، ECO-03 را READY_FOR_ECO_04 اعلام نکن.
________________________________________
32. پایان مأموریت
پس از تکمیل:
1.	تمام گزارش‌ها را ذخیره کن.
2.	گزارش‌ها را cross-check کن.
3.	تناقض بین گزارش‌ها را پیدا کن.
4.	ادعاهای بدون evidence را علامت‌گذاری کن.
5.	blockers را استخراج کن.
6.	scientific review items را جدا کن.
7.	ECO-04 build order را نهایی کن.
8.	00-FINAL-VALIDATION.md را آخر از همه تولید کن.
9.	هیچ production implementation انجام نده.
10.	در پایان status نهایی را اعلام کن.
ECO-03 باید یک نقشه اجرایی قابل تحویل به تیم implementation تولید کند، نه یک prototype.
این فایل عمداً یک گیت قبل از پیاده‌سازی است. مهم‌ترین بخشش هم این است که ایجنت مجبور شود ادعاهای ECO-02 را دوباره با source و evidence تطبیق دهد، مخصوصاً اختلاف 73 سرویس → 8 bounded context و اختلاف taxonomy مدل‌های علمی.
بعد از اجرای ECO-03، گزارش 00-FINAL-VALIDATION.md را برایم بیاور؛ از روی آن مشخص می‌کنیم آیا واقعاً وارد ECO-04 Implementation شویم یا یک گیت علمی/معماری دیگر لازم است.

