ECO-03.1
BLOCKER RECONCILIATION & MINIMAL ARCHITECTURE HARDENING
Project: Eco Nojin / اکو نوژین
 Phase: ECO-03.1
 Parent Phase: ECO-03
 Priority: CRITICAL
 Mode: FORENSIC + RECONCILIATION + MINIMAL HARDENING
 Production Implementation: FORBIDDEN
 Feature Development: FORBIDDEN
 Scientific Model Development: FORBIDDEN
 Database Development: FORBIDDEN
 Frontend/API Development: FORBIDDEN
 Smart Contract Development: FORBIDDEN
________________________________________
> **Implementation status (verified 2026-10-11)** — وضعیت هر بلاکرِ بازتاییدشده در این مرحله.
> وضعیت‌های «STUB» بدنهٔ سند منابع بلاکر بودند و دست‌نخورده می‌مانند.
>
> | بلاکر اصلی ECO-03.1 | وضعیت ۲۰۲۶-۱۰-۱۱ | شواهد |
> |---|---|---|
> | B-005: import guard ساخته شود ولی در CI نباشد | **رفع‌شده** — ابزار وجود دارد و در CI به‌عنوان گیت مسدودکننده اجرا می‌شود | `.github/workflows/ci.yml:197` |
> | B-006: `engine/gateway/` وجود نداشت | **رفع‌شده (رابط)** — فاز Gateway ساخته شد؛ مهاجرت کامل سرویس‌ها هنوز باز است | `git ls-files engine/gateway` |
> | B-002-arch: موتور ← `database/` | **رفع‌شده** — `engine/ports/persistence_port.py` + آداپتر SQLite؛ دو import مجاز مستند | `engine/ports/persistence_port.py`؛ `docs/adr/014-import-guard-policy.md` |
> | stub موقت `database/` | **منسوخ (superseded)** — `database/` اکنون پیاده‌سازی واقعی است (`database/models.py` مدل‌های SQLAlchemy + ۵ نسخهٔ Alembic در `alembic/versions/`) | `git ls-files database alembic/versions` |
> | نتیجهٔ اجرای import guard | **باز** — ۱۶ تخلف `SERVICES_NO_ENGINE_INTERNALS` | `python tools/detect_imports.py --root .` |
> | محدودیت نسخهٔ `cmake` در extra `cpp` | **رفع‌شده** — `cmake>=3.22` | `pyproject.toml:47-51` |
>
> **دکترین مزروع:** «stub را production implementation تلقی نکن» امروز هم معتبر است و رعایت شده:
> `database/` دیگر stub نیست.
________________________________________
 0. مأموریت
گزارش ECO-03 اعلام کرده است:
STATUS: BLOCKED
15 hard blockers initially identified
3 blockers fixed
12 blockers remaining

اما خود گزارش دارای چند تناقض مهم است.
بنابراین قبل از ورود به ECO-04 باید یک مرحله مستقل برای بازبینی و اثبات blockerها اجرا شود.
نام این مرحله:
ECO-03.1
BLOCKER RECONCILIATION & MINIMAL ARCHITECTURE HARDENING

مأموریت تو:
ECO-03
   ↓
re-audit
   ↓
reconcile contradictions
   ↓
verify every blocker
   ↓
minimal safe hardening
   ↓
re-run tests
   ↓
re-classify blockers
   ↓
FINAL GATE

این مرحله برای «حل همه مشکلات پروژه» نیست.
هدف فقط این است:
دقیقاً مشخص کن چه چیزی واقعاً blocker است، چه چیزی false positive است، چه چیزی فقط طراحی نشده، چه چیزی architectural violation است، و چه چیزی باید در ECO-04 باقی بماند.
________________________________________
1. اصل بنیادین
هیچ ادعایی را صرفاً به دلیل وجود در:
ECO-00
ECO-01
ECO-02
ECO-03

قبول نکن.
Source Code مرجع نهایی برای وضعیت فعلی implementation است.
برای هر finding باید ترجیحاً این زنجیره وجود داشته باشد:
Report Claim
    ↓
Source Evidence
    ↓
Reproduction
    ↓
Test / Static Analysis
    ↓
Disposition

________________________________________
2. قوانین مطلق
در ECO-03.1 ممنوع است:
●	ساخت Frontend
●	ساخت UI
●	ساخت API نهایی
●	ساخت Database واقعی
●	ساخت Migration
●	ساخت Authentication
●	ساخت Payment
●	ساخت Wallet
●	ساخت Blockchain
●	ساخت Smart Contract
●	ساخت Admin/CMS
●	ساخت Feature جدید
●	ساخت مدل علمی جدید
●	تغییر معادلات علمی
●	تغییر پارامترهای علمی بدون review
●	ساخت ML/AI جدید
●	refactor گسترده
●	mass rename
●	حذف گسترده legacy
●	انتقال کور فایل‌ها
●	redesign کل architecture
مجاز است فقط:
minimal blocker fix
test infrastructure
dependency installation
static architecture checks
import guards
safe package metadata
report correction
documentation correction
minimal adapter/interface required to prove boundary

هر تغییر source باید:
JUSTIFIED
MINIMAL
REVERSIBLE
TRACEABLE

باشد.
________________________________________
3. اولویت اصلی: گزارش ECO-03 را Audit کن
ابتدا تمام ادعاهای زیر را دوباره بررسی کن.
3.1 ادعای 15 blocker
از:
reports/eco-03/25-IMPLEMENTATION-BLOCKERS.md

تمام blockerها را استخراج کن.
برای هر blocker جدول زیر را بساز:
ID	Claim	Source Evidence	Reproduction	Current Status	Severity	Action
هیچ blocker بدون evidence معتبر باقی نماند.
________________________________________
4. وضعیت‌های مجاز Blocker
هر finding فقط می‌تواند یکی از وضعیت‌های زیر را داشته باشد:
CONFIRMED_BLOCKER
FIXED_AND_VERIFIED
FIXED_BUT_UNVERIFIED
FALSE_POSITIVE
DUPLICATE
NON_BLOCKING
DEFERRED_TO_ECO_04
REQUIRES_SCIENTIFIC_REVIEW
REQUIRES_ARCHITECTURAL_DECISION

این statusها را با هم قاطی نکن.
مثلاً:
FIXED_BUT_UNVERIFIED

هرگز معادل:
FIXED_AND_VERIFIED

نیست.
________________________________________
5. تناقض شماره 1: B-001
ECO-03 ادعا کرده:
B-001 fixed

و گفته:
engine/hydroma/generative_ai/

به:
services/ai/generative_ai/

منتقل شده است.
اکنون بررسی کن:
A
آیا فایل‌های اصلی واقعاً منتقل شده‌اند؟
B
آیا هیچ import باقی‌مانده‌ای از:
engine.hydroma.generative_ai

وجود دارد؟
C
آیا import معکوس ایجاد شده؟
D
آیا service AI اکنون به internal engine modules دسترسی مستقیم دارد؟
E
آیا import cycle دیگری ساخته شده؟
F
آیا packageهای قدیمی هنوز به‌صورت ghost package وجود دارند؟
G
آیا git/source references هنوز path قدیمی را استفاده می‌کنند؟
اجرای static search الزامی است.
نتیجه:
B-001:
FIXED_AND_VERIFIED

فقط در صورت اثبات کامل.
________________________________________
6. تناقض شماره 2: B-002 Database
ECO-03 گفته:
database/ stub created

اما این به‌تنهایی blocker را حل نمی‌کند.
باید دو سؤال کاملاً جدا بررسی شوند:
سؤال اول
آیا:
import engine

اکنون بدون ModuleNotFoundError اجرا می‌شود؟
سؤال دوم
آیا معماری canonical اجازه می‌دهد:
engine → database

؟
اگر پاسخ سؤال اول YES و سؤال دوم NO باشد:
B-002 import failure

ممکن است حل شده باشد، اما:
ENGINE_DATABASE_ARCHITECTURAL_VIOLATION

هنوز باقی است.
این دو را هرگز یکی نکن.
________________________________________
7. بررسی کامل Engine → Database
این فایل‌ها حداقل بررسی شوند:
engine/data_connector.py
engine/resource_manager.py
engine/ports/session.py

و کل repository را برای:
from database
import database
database.

جست‌وجو کن.
برای هر occurrence مشخص کن:
direct dependency
optional dependency
test-only dependency
legacy dependency
adapter dependency
architecture violation

هدف نهایی:
Hydroma / Scientific Engine
        X
Database

Engine باید برای persistence از abstraction/port استفاده کند، نه implementation database.
اما در ECO-03.1 فقط boundary correction انجام بده، نه ساخت persistence architecture کامل.
اگر حذف مستقیم dependency بدون طراحی بیشتر ممکن نیست:
DEFERRED_TO_ECO_04

ثبت کن.
________________________________________
8. تناقض شماره 3: B-003 pyproject.toml
ECO-03 می‌گوید:
pyproject.toml created

اما همان گزارش در بخش readiness نوشته:
pyproject.toml: NOT VERIFIED

این تناقض را resolve کن.
بررسی:
pyproject.toml exists?
valid TOML?
project metadata?
python version?
dependencies?
optional dependencies?
test dependencies?
build backend?
package discovery?

آن را با source code تطبیق بده.
اما:
dependency manifest را فقط برای آنچه source واقعاً استفاده می‌کند canonicalize کن.
Dependency حدسی اضافه نکن.
________________________________________
9. نصب Dependencies
یکی از مهم‌ترین blockerهای ECO-03 این بوده:
0 / 47 tests executable

به دلیل:
ModuleNotFoundError
numpy
scipy
...

اکنون dependency environment را بررسی کن.
9.1 ابتدا محیط فعلی را تشخیص بده
ثبت کن:
Python version
OS
architecture
compiler
pip version
virtual environment
package manager

سپس dependency resolution را انجام بده.
اولویت:
pyproject.toml

و نه:
pip install random packages until tests pass

________________________________________
10. Dependency Integrity
پس از نصب dependencyها:
pip check

یا معادل مناسب اجرا کن.
ثبت کن:
missing packages
version conflicts
binary conflicts
compiler failures
ABI failures

هیچ dependency را فقط برای سبز کردن تست‌ها اضافه نکن.
اگر dependency واقعاً در architecture لازم نیست:
REMOVE / DEFER

________________________________________
11. اجرای واقعی Test Suite
پس از dependency resolution دوباره تمام testها را اجرا کن.
گزارش قبلی:
47 identified
0 executable

اکنون باید به وضعیت واقعی تبدیل شود.
جدول:
Suite	Total	Collected	Executed	Passed	Failed	Error	Skipped
هیچ عددی را حدس نزن.
________________________________________
12. تفاوت Test Failure و Environment Failure
هر failure را طبقه‌بندی کن:
ENVIRONMENT_FAILURE
IMPORT_FAILURE
DEPENDENCY_FAILURE
COLLECTION_FAILURE
TEST_FAILURE
SCIENTIFIC_VALIDATION_FAILURE
ARCHITECTURE_FAILURE
NUMERICAL_FAILURE
C++_BUILD_FAILURE
ABI_FAILURE

مثلاً:
ModuleNotFoundError

را test failure علمی محسوب نکن.
________________________________________
13. B-005 Import Guard
اگر:
tools/detect_imports.py

وجود ندارد، یک ابزار کوچک و مستقل برای architecture checking ایجاد کن.
هدف:
تشخیص dependencyهای ممنوع.
حداقل قوانین:
engine → services      FORBIDDEN
engine → database      FORBIDDEN
engine → frontend      FORBIDDEN
engine → auth          FORBIDDEN
engine → payment       FORBIDDEN
engine → blockchain    FORBIDDEN
AI → engine internals  FORBIDDEN

اما:
ابزار باید ابتدا architecture contract را بخواند یا rules را در یک محل canonical و قابل نگهداری تعریف کند.
Hard-code کردن ده‌ها rule پراکنده در چند script ممنوع.
________________________________________
14. Boundary Checker
در صورت نیاز:
tools/check_boundary.py

بساز.
خروجی باید machine-readable باشد.
مثلاً:
{
  "status": "FAIL",
  "violations": [
    {
      "rule": "ENGINE_NO_DATABASE",
      "source": "...",
      "line": 86,
      "import": "database.hub"
    }
  ]
}

JSON نمونه صرفاً illustrative است.
فرمت نهایی را با architecture reports هماهنگ کن.
________________________________________
15. Architecture Guard نباید False Positive تولید کند
قبل از فعال کردن guard روی کل repository:
آن را با:
known-good import
known-bad import
test-only import
optional import
TYPE_CHECKING import

آزمایش کن.
باید بتواند موارد واقعی را از موارد غیرواقعی تفکیک کند.
________________________________________
16. Service Inventory Reconciliation
ECO-03 گفته:
73 → 75

اما توضیح خودش شامل:
services/ai/
services/observability/
services/landscape/

است.
این محاسبه را دوباره انجام بده.
دستورالعمل:
find every top-level services directory

و برای هر directory مشخص کن:
actual service?
package?
shared library?
infrastructure?
test?
registry?
placeholder?

یک count واحد تولید کن.
مثلاً:
TOTAL_TOP_LEVEL_DIRECTORIES
ACTUAL_SERVICES
INFRASTRUCTURE_MODULES
SHARED_LIBRARIES
TEST_SUPPORT
PLACEHOLDERS

عدد «service count» باید تعریف داشته باشد.
________________________________________
17. Service Registry Canonicalization
هر مورد را در:
reports/eco-03.1/

ثبت کن.
برای هر service:
service_id
path
category
bounded_context
owner
status
dependencies
dependents

اگر services/models/ service نیست، دلیل ثبت کن.
اگر services/validation/ service نیست، دلیل ثبت کن.
اگر services/ai/ یک bounded context است یا فقط infrastructure، مشخص کن.
________________________________________
18. Bounded Context Validation
فعلاً هیچ service را physically move نکن.
فقط مشخص کن:
current context
canonical context
reason
dependency violations
migration complexity

عدد 8 را فرض نکن.
نتیجه می‌تواند:
8 valid contexts

یا:
9 valid contexts

یا:
7 valid contexts

باشد.
Architecture باید از evidence پیروی کند.
________________________________________
19. Scientific Maturity Reconciliation
تمام مدل‌های علمی را دوباره شمارش کن.
برای هر مدل:
model_id
implementation_exists
test_exists
reference_data_exists
scientific_source_exists
benchmark_exists
validation_exists
uncertainty_exists
status

سپس taxonomy نهایی را اعمال کن:
VERIFIED
SCIENTIFICALLY_SUPPORTED
IMPLEMENTATION_VERIFIED
STUB
REQUIRES_SCIENTIFIC_REVIEW
UNKNOWN

نکته بسیار مهم:
VERIFIED

فقط زمانی مجاز است که evidence معتبر وجود داشته باشد.
اگر هیچ test قابل اجرا نبوده، نمی‌توان صرفاً بر اساس code inspection گفت:
VERIFIED

________________________________________
20. Scientific vs Software Verification
این دو ستون را حتماً جدا کن:
Model	Software Status	Scientific Status
PM ET0	...	...
Theis	...	...
SCS-CN	...	...
Darcy	...	...
مثلاً:
Implementation verified

نباید به‌صورت خودکار:
Scientifically verified

تفسیر شود.
________________________________________
21. P0 Scientific Blockers
دو مورد اعلام‌شده:
CANON-005 Theis
Climate Data Assimilation

را دوباره بررسی کن.
برای هرکدام مشخص کن:
equation
algorithm
parameter assumptions
convergence
boundary conditions
reference source
validation data
implementation
test
uncertainty

اگر بررسی علمی واقعی خارج از scope است:
REQUIRES_SCIENTIFIC_REVIEW

ثبت کن.
اما صرفاً به دلیل review requirement، کل ECO-04 را متوقف نکن مگر اینکه آن مدل برای implementation مرحله بعدی ضروری باشد.
________________________________________
22. AI Isolation
پس از اصلاح B-001:
جست‌وجوی کامل انجام بده:
engine.*ai
ai.*engine
services.ai.*engine
engine.*services

بررسی کن:
AI → engine internals
engine → AI
AI → scientific computation
AI → parameter mutation
AI → provenance mutation
AI → epistemic mutation

هر violation را ثبت کن.
________________________________________
23. Uncertainty
در این مرحله uncertainty را کامل پیاده‌سازی نکن.
فقط مشخص کن:
Does current output contract contain uncertainty?
Does current model registry contain uncertainty?
Does Engine Gateway contract specify it?
Are current outputs point estimates only?

اگر implementation وجود ندارد:
DEFERRED_TO_ECO_04

اما اگر architecture invariant آن را برای current implementation الزام کرده، مشخص کن که آیا blocker واقعی است یا future implementation requirement.
این تمایز مهم است.
________________________________________
24. Evidence / Knowledge / Decision
در ECO-03.1 آنها را از صفر پیاده‌سازی نکن.
فقط بررسی کن:
contract exists?
schema exists?
implementation exists?
test exists?
boundary exists?

و نتیجه:
DESIGNED
PARTIAL
IMPLEMENTED
TESTED
NOT_IMPLEMENTED

ثبت شود.
اگر چیزی صرفاً طراحی است، آن را blocker implementation infrastructure ندان مگر اینکه ECO-04 بدون آن واقعاً امکان شروع نداشته باشد.
________________________________________
25. C++ / Python
بررسی کن:
compiler available?
C++ build possible?
pybind11 available?
extension source?
Python version compatibility?
ABI?
fallback?

تست کن.
اگر build ممکن نیست:
ENVIRONMENT_BLOCKER

ثبت کن، نه:
SCIENTIFIC_FAILURE

________________________________________
26. Performance Claims
ECO-01 ادعا کرده:
10x–200x

این ادعا را بررسی کن.
اگر benchmark source وجود ندارد:
UNVERIFIED PERFORMANCE CLAIM

ثبت کن.
این موضوع به‌تنهایی blocker ECO-04 نیست مگر performance requirement برای اولین implementation phase باشد.
________________________________________
27. Minimal Hardening
فقط blockerهایی را اصلاح کن که:
small
safe
architecture-preserving
reversible
objectively verifiable

هستند.
نمونه‌های مجاز:
import cleanup
package metadata
architecture checker
test configuration
safe module relocation
dead import removal
minimal adapter interface

نمونه‌های ممنوع:
complete database architecture
complete service rewrite
new domain implementation
new scientific model
new AI system
large-scale refactor

________________________________________
28. Database Stub Rule
اگر database/ stub ایجاد شده است، بررسی کن آیا باید باقی بماند.
سه حالت:
حالت A
Engine واقعاً باید database-independent شود.
در این صورت:
stub is temporary workaround

و dependency باید در ECO-04 حذف/معکوس شود.
حالت B
Database abstraction در architecture لازم است.
در این صورت باید interface/port تعریف شود، نه database implementation.
حالت C
Database dependency legacy-only است.
در این صورت:
remove/defer

کن.
ساخت stub برای پنهان کردن architectural violation ممنوع است.
________________________________________
29. No Silent Fixes
هر source change باید در:
reports/eco-03.1/CHANGELOG.md

ثبت شود:
change_id
file
before
after
reason
blocker_id
risk
verification
rollback

هیچ تغییر بدون ثبت مجاز نیست.
________________________________________
30. Git / Diff Audit
قبل و بعد از اصلاحات:
git status
git diff
git diff --stat

بررسی کن.
اگر repository git نیست، معادل مناسب تهیه کن.
هدف:
NO UNEXPLAINED CHANGES

________________________________________
31. Required Reports
تمام خروجی‌ها در:
reports/eco-03.1/

قرار بگیرند.
حداقل:
00-FINAL-GATE.md
01-BLOCKER-RECONCILIATION.md
02-EVIDENCE-MATRIX.md
03-SERVICE-COUNT-RECONCILIATION.md
04-BOUNDED-CONTEXT-REVALIDATION.md
05-SCIENTIFIC-MATURITY-RECONCILIATION.md
06-ENGINE-DATABASE-DEPENDENCY.md
07-ENGINE-SERVICE-DEPENDENCY.md
08-AI-ISOLATION-REVALIDATION.md
09-CPP-PYTHON-REVALIDATION.md
10-DEPENDENCY-ENVIRONMENT.md
11-TEST-EXECUTION-REPORT.md
12-ARCHITECTURE-GUARD-REPORT.md
13-MINIMAL-HARDENING-CHANGELOG.md
14-SCIENTIFIC-BLOCKERS.md
15-ECO-04-BLOCKERS.md
16-OPEN-QUESTIONS.md
17-MACHINE-READABLE-SUMMARY.json

در صورت نیاز فایل‌های بیشتر اضافه کن.
________________________________________
32. Evidence Matrix
مهم‌ترین خروجی ECO-03.1:
02-EVIDENCE-MATRIX.md

برای هر blocker:
Blocker	Original Claim	Source	Reproduced?	Fixed?	Verified?	Current Severity	ECO-04 Blocking?
این جدول باید مرجع نهایی باشد.
________________________________________
33. Final Blocker Accounting
در پایان اعداد باید دقیقاً reconcile شوند.
مثلاً:
Initial blockers: X

Confirmed:
Y

Fixed and verified:
Z

False positives:
A

Duplicates:
B

Deferred to ECO-04:
C

Scientific review:
D

Remaining hard blockers:
E

باید برقرار باشد:
X = Y + Z + A + B + C + D

هر عدد باید قابل trace باشد.
________________________________________
34. Definition of Hard Blocker
هر finding فقط زمانی:
HARD BLOCKER

است که:
1.	با source evidence اثبات شده باشد.
2.	reproducible باشد.
3.	مانع مستقیم اجرای مرحله مشخص ECO-04 باشد.
4.	با یک documentation change ساده حل نشود.
5.	صرفاً future feature requirement نباشد.
6.	صرفاً scientific improvement غیرضروری نباشد.
مثال:
missing import dependency

ممکن است blocker باشد.
اما:
uncertainty propagation هنوز کامل نشده

الزاماً blocker کل ECO-04 نیست، اگر مرحله ECO-04 موردنظر بدون آن قابل پیاده‌سازی باشد.
________________________________________
35. ECO-04 Blocking Policy
ECO-04 را فقط موارد زیر می‌توانند متوقف کنند:
critical architecture violation
unresolvable dependency cycle
unrunnable required build environment
missing mandatory contract
unsafe scientific implementation required for immediate build
security-critical violation
data-integrity-critical violation

مواردی مانند:
future UI
future API
future CMS
future AI enhancement
performance optimization
non-critical scientific review
optional service consolidation

نباید به‌تنهایی ECO-04 را متوقف کنند.
________________________________________
36. ECO-04 Readiness Levels
در پایان یکی از این statusها را انتخاب کن:
READY_FOR_ECO_04
اگر blocker واقعی برای شروع controlled implementation وجود ندارد.
READY_WITH_LIMITATIONS
اگر ECO-04 می‌تواند شروع شود ولی برخی workstreamها باید deferred شوند.
BLOCKED
اگر حداقل یک hard blocker مستقیم باقی مانده است.
REQUIRES_SCIENTIFIC_REVIEW
اگر implementation مرحله بعدی مستقیماً به یک scientific decision unresolved وابسته است.
________________________________________
37. بسیار مهم: ECO-04 را بیش از حد متوقف نکن
هدف این مرحله این نیست که:
100% architecture
100% science
100% evidence
100% uncertainty
100% decision
100% AI

را قبل از شروع implementation کامل کنیم.
این کار باعث endless planning می‌شود.
هدف:
minimum safe implementation boundary

است.
اگر Engine Gateway را می‌توان مستقل ساخت، آن را فقط به دلیل اینکه Tasmimyar هنوز کامل نیست متوقف نکن.
اگر Scientific Model Registry را می‌توان ساخت، آن را فقط به دلیل اینکه UI وجود ندارد متوقف نکن.
________________________________________
38. Final Gate Questions
در 00-FINAL-GATE.md دقیقاً به این سؤالات پاسخ بده:
Q1.
چند blocker واقعی باقی مانده؟

Q2.
چند blocker گزارش قبلی false positive بود؟

Q3.
چند blocker واقعاً fixed و verified شد؟

Q4.
آیا engine → database هنوز وجود دارد؟

Q5.
آیا engine → services هنوز وجود دارد؟

Q6.
آیا circular dependency وجود دارد؟

Q7.
آیا import guards واقعاً اجرا شده‌اند؟

Q8.
چند test اکنون واقعاً اجرا می‌شود؟

Q9.
چند test pass/fail/error/skip شده؟

Q10.
آیا pyproject.toml معتبر و کافی است؟

Q11.
تعداد واقعی serviceها چند است؟

Q12.
تعداد واقعی bounded contextها چند است؟

Q13.
کدام scientific models واقعاً verified هستند؟

Q14.
کدام scientific models فقط implementation verified هستند؟

Q15.
کدام مدل‌ها scientific review می‌خواهند؟

Q16.
آیا AI boundary در source enforce شده؟

Q17.
آیا ECO-04 می‌تواند بدون تغییر architecture وارد implementation شود؟

Q18.
اولین task امن ECO-04 دقیقاً چیست؟

Q19.
کدام کارها باید به بعد از ECO-04 منتقل شوند؟

Q20.
FINAL STATUS چیست؟

________________________________________
39. گزارش نهایی باید صادقانه باشد
از عبارت‌های زیر بدون evidence استفاده نکن:
fully fixed
fully validated
production ready
scientifically proven
secure
complete
architecture enforced

به‌جای آن از:
verified
partially verified
designed
implemented
tested
not tested
not verified
blocked
deferred
requires review

استفاده کن.
________________________________________
40. شرط عبور از ECO-03.1
ECO-03.1 موفق است اگر:
[ ] تمام blockerهای ECO-03 دوباره بررسی شده‌اند
[ ] تناقض‌های گزارش قبلی resolve شده‌اند
[ ] تعداد واقعی serviceها مشخص شده
[ ] bounded contexts دوباره validate شده‌اند
[ ] scientific maturity reconcile شده
[ ] engine → services بررسی شده
[ ] engine → database بررسی شده
[ ] AI isolation بررسی شده
[ ] dependency environment بررسی شده
[ ] test suite واقعاً اجرا شده یا failure دقیق ثبت شده
[ ] architecture guard اجرا شده
[ ] تمام source changes ثبت شده‌اند
[ ] blocker accounting mathematically reconciled است
[ ] ECO-04 blockers واقعی مشخص شده‌اند
[ ] ECO-04 build entry point مشخص شده

________________________________________
41. مهم‌ترین قانون این مرحله
اگر در حین اجرای ECO-03.1 متوجه شدی که گزارش ECO-03 اشتباه بوده است، گزارش قبلی را حفظ کن اما حقیقت جدید را ثبت کن.
نباید برای هماهنگ کردن source با report، source را دستکاری کنی.
قاعده:
SOURCE TRUTH
    >
TEST EVIDENCE
    >
STATIC ANALYSIS
    >
ARCHITECTURE CONTRACT
    >
REPORT CLAIM

________________________________________
42. پایان مأموریت
پس از اتمام:
1.	source را دوباره scan کن.
2.	تمام blockerها را reproduce کن.
3.	minimal fixes را اعمال کن.
4.	tests را دوباره اجرا کن.
5.	architecture guards را اجرا کن.
6.	git diff را بررسی کن.
7.	تمام تغییرات را ثبت کن.
8.	blocker accounting را reconcile کن.
9.	00-FINAL-GATE.md را آخر از همه تولید کن.
10.	ECO-04 را فقط در صورت عبور از gate توصیه کن.
هیچ production feature در ECO-03.1 ساخته نشود.
این مرحله باید حقیقت وضعیت repository را مشخص کند، نه اینکه repository را برای سبز شدن گزارش‌ها دستکاری کند.
بعد از اجرای این مرحله، کل 00-FINAL-GATE.md و جدول 02-EVIDENCE-MATRIX.md را برای من بیاور. این دو فایل برای تصمیم ورود به ECO-04 کافی‌ترین شواهد خواهند بود.

