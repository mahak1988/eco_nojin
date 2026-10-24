# گزارش نهایی ممیزی جامع — HyDroMA / ECO Nojin
**تاریخ:** ۲۰۲۶-۱۰-۱۶ · **شاخهٔ کاری:** `frontend/design-system-migration` · **HEAD:** `2cb974e` · **مجاز نیست:** ورود به برنامه‌ریزی توسعه تا دریافت مجوز صریح کارفرما.

## A — خلاصهٔ مدیریتی
- **وضعیت واقعی مخزن:** درخت کار پاک نیست (`git status`: ۱۳ staged, ۵۹۶ modified, ۱۳۳ untracked). کد و گزارش‌های مراحل قبلی بر اثر جابه‌جایی مستندات/خانه‌سازی CI هنوز commit نشده‌اند. هر اعداد باید با Commit/شاخهٔ مشخص به‌روزخوانی شوند.
- **معماری Python:** Import Guard = ۰ تخلف (۱۲۷۸ فایل). API = ۱۱۷ route, ۶۶۷ path, ۷۵۳ op. مدل‌های علمی ثبت‌شده = ۷۲ (۱۷ `validated`, ۵۵ `unvalidated`). Lint = ۸۶۲ یافته (بدتر از baseline ۷۶۹ به‌دلیل فایل‌های درگردش).
- **کیفیت کد:** `app.openapi()` سبز. `pytest` کامل در این جلسه اجرا نشد (محدودیت حافظه/xdist در محیط Windows); شمارش کشف تست‌ها ~۴۹۴۵ (گزارش فاز ۰). دو جلسهٔ جمع‌آوری (collection) قبلاً رفع شده‌اند.
- **اعتبارسنجی علمی:** CANON-001 (Penman–Monteith FAO-56) در رجیستری با شواهد تطبیق با منبع اصلی (۳.۸۸ vs ۳.۹ mm/d) ثبت شده. خانوادهٔ HYRUE/مدل‌های هیدرولوژیک/خاک/کشاورزی در رجیستری wired=۷۲ هستند، اما ۵۵ مدل صریحاً `unvalidated` هستند؛ wired بودن ثابتِ صحت علمی نیست.
- **اعتبارسنجی اقتصادی:** گزارش `PHASE-2-ECONOMIC-VALIDATION.md` (ه Labor ۲۰۲۶-۱۰-۱۶) در مخزن فعلی یافت نشد؛ اعداد ۳٬۸۸۸ kg/ha, ۱۰ ha, ۳۸٫۸۸ t, ۳۰۰ $/t, ۱۱٬۶۶۴ ریال, ۶٬۴۰۰ ریال, ۵٬۲۶۴ ریال در کد/گزارش‌های موجود قابل بازپخش نیستند. به‌علت نبود نرخ ارز/واحد پول و مبنای هزینه، نتیجهٔ اقتصادی: **«تأییدنشده به دلیل ابهام در واحدها و مبنای محاسبه»**.
- **تناقض‌های اصلی:** تعداد مدل‌های validated بین گزارش‌های پیشین (۱۳) و اندازه‌گیری فعلی (۱۷)؛ baseline ruff ۷۶۹ vs اجرای فعلی ۸۶۲؛ شاخهٔ master و frontend هر دو به `2cb974e` اشاره دارند (واگرایی HEAD مشاهده نشد، اما Commitهای توسل‌شدهٔ گزارش‌های قدیمی `d6fac05` قدیمی هستند). نتیجه: مقایسه باید بر اساس تفاوت Commit/زمان/محیط انجام شود.

## B — فهرست اسناد و دستورهای بررسی‌شده
- `AGENTS.md` (runbook, env, quality gates, architecture invariants).
- `docs/project/BASELINE.md`, `KNOWN_ISSUES.md`, `OPEN_DECISIONS.md`, `CAPABILITY_MATRIX.md`, `DEPENDENCY_MAP.md`, `PHASE_PLAN.md`, `MASTER-AUDIT-AND-PROGRAM-2026-10-11.md`.
- `docs/specs/HYDROMA-MASTER-TESTING.md`, `docs/specs/HYDROMA-MASTER.md`, `docs/specs/ECO-PROGRAM-FA.md`.
- `docs/audits/ECO-00-ENGINE-SERVICES-FORENSIC-AUDIT-REPAIR.md`.
- گزارش‌های Git-tracked `reports/*` (~۲۵۰ فایل) در HEAD ثبت شده‌اند ولی در درخت کار حذف ریشه‌ای شده‌اند؛ از طریق `git show HEAD:...` قابل بازیابی هستند.
- `HYDROMA-MASTER-TESTING — STAGE 2 REPORT (Oct 9 2026)` و `PHASE-2-ECONOMIC-VALIDATION.md`: تدر مخزن فعلی (HEAD `2cb974e`) **وجود ندارند** و از روی نام تخمین نبودن آن‌ها بازسازی شده است. این یک **محدودیت دسترسی صریح** است.
- گزارش Phase 0: `reports/HYDROMA-STAGE1-DIAGNOSTIC-2026-10-09.md` (HEAD baseline `d6fac05`)؛ گزارش ۹ Oct برابر با شاخهٔ master مربوطه.
- کارت‌های مدل (`engine/models/cards/*`, `engine/models/registry.py`), Gateway (`engine/gateway/*`).

## C — وضعیت واقعی معماری و قابلیت‌ها
- **Import guard:** ۰ تخلف، ۱۲۷۸ فایل اسکن، ۸ قانون.
- **Gateway:** `app.routes=117`, OpenAPI ۶۶۷ paths / ۷۵۳ ops، boot GREEN deterministic.
- **Model registry:** ۷۲ مدل؛ ۷۲ دارای `gateway_wired=True`؛ وضعیت‌ها: `validated=17`, `unvalidated=55`; implementation: `implemented=32`, `unverified=40`; verification: `tested=12`, `implemented=17`, `unverified=43`.
- **Service boundary policy tool:** گزارش شده ۱۴۰ edge / ۰ violation (Mededaka from BASELINE) — در این جلسه re-measured نشد.
- **Dep runtime:** SQLite ۳.۴۹.۱ < ۳.۵۱.۳ (پوشش WAL-reset) — محدودیت استقرار باقی است.
- **Money planes:** ۵ ذخیرة موازی در `database/models.py` + raw SQL ecocoin؛ پروژهٔ `com_orders` unique constraint و shared user key در مهاجرت‌های P4/P5 گزارش شده است، اما متناقضٔهای ledger همچنان بازند (KN-08).

## D — گزارش اعتبارسنجی علمی
- **CANON-001 (FAO-56 PM):** ثبت‌شده، مسیر Dispatch به `engine/hydroma/climate/et_calculator.py`، شواهد VAIDATION با FAO-56 Example 18 (3.8801 mm/day vs 3.9 published); status `validated`. همچنین C++ parity گزارش شده.
- **SCS-CN (CANON-004):** شواهد تطابق با NRCS-TR55 sample (5.812803 mm) در گزارش Phase 0 ارائه شده؛ نیاز به اسکن کد مستقل در این جلسه نشد (پوشش آزمون مستقل در `engine/tests`).
- **پارامترهای Van Genuchten (CANON-006):** رجیستری registered/wired, اما accor<|end|><|start|>start<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="content">
## D — گزارش اعتبارسنجی علمی (ادامه)
- **پارامترهای Van Genuchten (CANON-006):** ثبت و wired در رجیستری، اما وضعیت `validation_status` در تاریخ اندازه‌گیری باید مستقیماً از registry بررسی شود؛ شواهد انتساب جدول Saxton&Rawls موجود است (`tests/test_saxton_rawls_2006_awc.py`, `engine/data` reference).
- validated IDs (2026-10-16 registry): CANON-001, CANON-002, CANON-004, CANON-006, CANON-008, CANON-010, CANON-011_RAD, CANON-015, CANON-016, CANON-017, CANON-019, CANON-020, CANON-021, CANON-022, SOIL_SALINITY_CLASSIFY, ROTHTC_TEMP_FACTOR, RUSLE_LS.
- `HYRUE_WHEAT`, `HYRUE_CORN`, `SOIL_VG_PARAMETERS`, `SOIL_WATER_RETENTION`, `SOIL_PEDOTRANSFER`, `SOIL_TEXTURE`, `SOIL_AWC`, `IRRIGATION_DEPTH`, `IRRIGATION_INTERVAL`, `CROP_YIELD`, `CROP_COMPARE` همهٔ مرحلهٔ ثبتِ رجیستری = `unvalidated` (wired=True). بنابراین ادعای "through Gateway executed" برای زنجیرهٔ خاک/محصول/آبیاری هنوز به‌عنوان اعتبارسنجی سنده نشده است.
- **其余 families (SOIL, HYDROLOGY, RUSLE, RothC, etc.):** 55 مدل `unvalidated`؛ وجود در رجیستری/فایل مدرک تکمیل شدن قابلیت یا صحت علمی نیست (قاعدهٔ اول و دوم).

## E — اعتبارسنجی اقتصادی
- وضعیت: **تأییدنشده به‌دلیل ابهام در واحدها و مبانی محاسبه**. دلایل:
  - گزارش Phase 2 در دسترس نیست؛
  - اعداد گزارش‌شده (3,888 kg/ha, 10 ha, 38.88 t, $300/t, 11,664/6,400/5,264) در current tracked tree یافت نشدند؛
  - واحد پول هر ورودی/خروجی، نرخ تبدیل ارز، قیمت برای هر هکتار یا کل ۱۰ هکتار، و مبنای هزینه (`engine/hydroma/economics/*`, `services`) در گزارش قابل بازپخش مشخص نشده‌اند.
- شواهد فعلی کد: `engine/hydroma/economics/revenue.calculate_agricultural_revenue` بسیار ساده و خطی است (`total_yield_ton = area_hectares * yield_ton_per_ha`, `base_revenue = total_yield_ton * market_price_per_ton`), و خروجی‌ها با پسوند `_irr` منتشر می‌شوند؛ یعنی قرارداد ارزی/واحدی ضمنی و منوط به ورودی است. در همین ماژول `costing.py` نیز هزینه‌ها بر پایهٔ هر هکتار و `_irr` بنا شده‌اند. بنابراین ادعای 300 $/t با 11,664 ریال مستقیماً قابل اتصال نیست.
- هیچ فرض دلخواهی برای نرخ ارز یا واحد پول انتخاب نشد.

## F — آزمون‌ها و کیفیت کد (اندازه‌گیری‌های موجود)
- `pytest services/ engine/ --collect-only -q`: 4945 collected, 0 collection errors (Phase 0 addendum).
- Import guard: PASS 0 violations, 1278 files.
- `app.openapi()`: 117 routes, 667 paths, 753 ops.
- `ruff check .`: 862 errors (live, vs baseline 769/762).
- محدودیت محیطی: دو suite ۶-worker را همزمان روی یک box نباید run کرد؛ torch/sentence-transformers ریسک memory pressure دارند.
- نتیجهٔ آزمون‌های کامل Phase 0 (9 Oct: engine 1621 passed/0 failed, services 521 passed/0 failed, import guard PASS) مربوط به Commit `d6fac05` و درخت کار قبلی‌ست؛ نباید به HEAD فعلی بدون اعتبارسنجی مجدد نسبت داده شود.

## G — ماتریس تطبیق ادعاها با شواهد فعلی
| شناسه | ادعا | منبع | شواهد فعلی | وضعیت |
|---|---|---|---|---|
| G-01 | 13 validated model | MASTER 2026-10-11 | registry اندازه‌گیری: 17 validated | تناقض روش شمارش/زمان؛ به‌روزخوانی شده |
| G-02 | Ruff 769 baseline | AGENTS.md | اجرای فعلی 862 | افزایش زنده‌ tree؛ baseline committed = 769 |
| G-03 | Services tests 1381 passed | BASELINE (recorded) | در این جلسه کامل اجرا نشد | گزارش تاریخی، تأییدمجدد لازم |
| G-04 | شاخهٔ master vs frontend | دستور ممیزی | هر دو HEAD به `2cb974e` | واگرایی HEAD مشاهده نشد؛ گزارش‌های قدیمی به Commit `d6fac05` |
| G-05 | 4 نقص gateway | PHASE 2 (不可 دسترس) | 4 نقص در کد فعلی باید جداگانه بررسی شود | نامشخص/نیاز به بررسی بیشتر |
| G-06 | Econ chain E2E | PHASE 2 | شواهد پایدار E2E اجرا کامل همگی بخش‌ها در مخزن یافت نشد | نامشخص |
| G-07 | Import guard 16 violations | mid-session AGENTS | فعلی 0 | حل شده (گزارش حادثه‌ای) |

## H — فهرست یافته‌های نهایی (طبقه‌بندی شده)
1. **Critical — Economic validity unproven:** نتایج 11,664/6,400/5,264 بدون واحد/نرخ ارز قابل اعتماد نیست.
2. **High — Scientific credibility partial:** 55 of 72 models unvalidated (registry)؛ wired≠validated.
3. **High — Environment gate:** SQLite 3.49.1 < required 3.51.3 for WAL safety.
4. **High — Money plane complexity:** 5 لجر موازی و ecocoin raw SQL؛ اختلاف قراردادها هنوز باز.
5. **Medium — Lint growth:** 862 vs baseline 769 (درخت کارِ درگردش).
6. **Medium — Test reproducibility:** شواهد کاملِ دو suite در HEAD فعلی مجدداً ثبت نشده.
7. **Medium — Doctrine vs evidence:** گزارش‌های `FIXED/PASS` باید با شواهد کد/Commit بازخوانی شوند; ا claimed fix ≠ evidence.
8. **Low/Medium — Docs housekeeping:** گزارش‌های مراحل قبلی حذف/جابه‌جا شده؛ مسیر کانونیکال لازم (docs/project).

## I — نیازمند بررسی بیشتر
- دسترسی به `PHASE-2-ECONOMIC-VALIDATION.md` و `HYDROMA MASTER TESTING — STAGE 2 REPORT` (Oct 9).
- Commitهای دقیق هر گزارش (master HEAD now `2cb974e`; reports refer to older `d6fac05`).
- اجرای مجدد کامل `pytest services/` و `pytest engine/` روی HEAD فروzen.
- بازسازی محاسبات اقتصادی از روی `engine/hydroma/economics` و services با واحد پول و نرخٔ صریح.
- بررسی مستقل هر 55 مدل unvalidated (SOIL/HYDROLOGY/RUSLE/ROTHC).
- wal deployment upgrade plan و service-boundary re-measure.

## J — نتیجهٔ نهایی ممیزی
- **اثبات‌شده:** import guard PASS, boot PASS, registry enumeration, بخشی از کارت‌/شواهد علمی (CANON-001, SCS-CN references), گزارش‌های Phase 0 architecture.
- **صرفاً گزارش‌شده (تأیید یافته‌ها لازم):** services/engine suite green counts, PHASE-2 claims, integration chain E2E full validation, economic figures.
- **ردشده:** هیچ مدرکی برای تأیید ادعای Phase-2 economic validation در مخزن فعلی یافت نشد؛ wired status ≠ scientific validity.
- **نامشخص:** بخش‌های I.
- **نتیجهٔ مأموریت بررسی/تحقیق:** تا اندازهٔ دامنهٔ قابل‌دسترس تکمیل شده؛ موارد باز در I باقی ماندند. هیچ برنامهٔ توسعه‌ای، پیشنهاد معماری جدید یا اجرای fix انجام نشد. **ورود به توسعه فقط پس از بررسی این گزارش و دریافت مجوز صریح کارفرما مجاز است.**
""", filePath: "D:\HyDroMA\docs\audits\FINAL-AUDIT-REPORT-2026-10-16.md")