# اکو نوژین + هیدروما — سند مادر یکپارچه نسخه ۳.۱

Document id: `ECO-NOJIN_MASTER_v3.1_UNIFIED` · تاریخ: ۲۰۲۶-۱۰-۱۰ · وضعیت: **پیشنهادی برای تصویب** · ارجاع کد: `d6fac05+`
جایگزین: `ECO_NOJIN_HYDROMA_MASTER_v3.0.html` (سند موقت، با ۱۳ وصلهٔ ثبت‌شده در `reports/eco-nojin/SPEC-V3.1-PATCH.md` ادغام شده است)

> **قاعدهٔ بنیادین این نسخه:** هیچ عددی در این سند «ادعا» نیست. هر عدد یا **سنجش‌شده در تاریخ سند** است یا **هدف**. هر ادعای علمی بدون لنگر بیرونی، به‌صراحت `UNVALIDATED` است.

---

## ۰. بیانیه یکپارچگی
**اکو نوژین** = هستهٔ علمی و موتور حکمرانی شواهد. **هیدروما** = پلتفرم کسب‌وکار. مرزها با یک قرارداد مرزی (Boundary Contract) تعریف می‌شوند؛ تمام عبور داده و تصمیم از `EngineGateway` + `Tasmimyar` با provenance.

**اصل طلایی:** لایهٔ کسب‌وکار هرگز مستقیماً یک معادله یا پارامتر علمی را تغییر نمی‌دهد (AR-03/SB-07).

## ۱. پیمان ZED و قواعد غیرقابل‌مذاکره (الزامی برای **لایهٔ ۱** — تصمیم DP-1)

1. هیچ `pip install` خارج از Approved FOSS Stack.
2. هیچ API ابری (AWS/Azure/GCP/GEE) در هستهٔ علمی.
3. هیچ دادهٔ مصنوعی بدون برچسب `# FIXTURE` (قرارداد پروژه؛ تست‌های E2E از `synthetic_test_data: true` استفاده می‌کنند و هر دو باید هم‌خوان شوند).
4. هیچ تغییر واحد بدون `pint`/`UnitRegistry`.
5. هیچ تغییر وزن تصمیم‌یار بدون آزمون حساسیت.

**پشتهٔ مجاز (لایهٔ ۱):** Python ≥ ۳.۱۱، numpy، scipy، pandas، pydantic، **pint**، pyyaml، sqlalchemy (SQLite)، geopandas/rasterio/shapely/pyproj (دادهٔ مکانی)، pybind11 (کرنل)، CPython ART • لایهٔ ۳: FastAPI + **Hydroma Runtime** (بدون Docker؛ تصمیم DP-2).

**بسته‌های مرجع dev/test (هرگز در runtime موتور):** `pyet` (MIT)، `climate_indices` (BSD-3)، `rosetta-soil` (CC0) — هر سه در extraهای `[ref]`/`[units]` ثبت‌اند و تست‌ها با `importorskip` در نبودشان skip می‌شوند.

## ۲. ده ترمز ایمنی (SB-01..SB-10)

| ردیف | شرط توقف |
|---|---|
| SB-01 | تغییر بیش از ۵ فایل اصلی |
| SB-02 | حذف بیش از ۱۰۰ خط کد |
| SB-03 | تغییر API عمومی (نام/ورودی/خروجی/استثنا) |
| SB-04 | افزودن `pip install` خارج پشتهٔ مجاز |
| SB-05 | تغییر واحدها یا وزن‌های تصمیم |
| SB-06 | استفاده از دادهٔ مصنوعی به‌جای مرجع علمی |
| SB-07 | تغییر معادلهٔ علمی (FAO/USDA/WMO) بدون مرجع چپشده |
| SB-08 | کاهش coverage تست زیر ۸۰٪ |
| SB-09 | عدم تطابق `tools/detect_imports.py` |
| SB-10 | عدم ارائه Fix Log یا Evidence برای تغییر > ۵۰ خط |

پیاده‌سازی: `engine/honesty/statuses.py::BRAKES` (باید از ۷ به ۱۰ ارتقا یابد — کار تکمیلی W6).

## ۳. قواعد معماری (AR-01..AR-13)

| شناسه | قاعده | وضعیت اجرا در درخت |
|---|---|---|
| AR-01 | Separation of Concerns — هستهٔcientific به اینترنت متصل نمی‌شود | ✅ `detect_imports.py` PASS · گیت دانلود با `--allow-download` |
| AR-02 | Dependency Inversion — هسته به Port وابسته است نه implementation | ✅ `engine/ports/persistence_port.py` + `adapters/persistence/` |
| AR-03 | Model Immutability — معادلات ثبت‌شده در Model Card تغییرناپذیرند | ✅ سرتاسر برنامه رعایت شد |
| AR-04 | API Stability — تغییر API عمومی = STOP | ✅ |
| AR-05 | Evidence-Based Decision — هر تصمیم Tasmimyar شاهد دارد | ✅ `engine/evidence` + `engine/knowledge` |
| AR-06 | Unit Safety — تمام محاسبات با pint | ⚠️ ممیزی پیاده (`engine/gateway/pint_audit.py`)؛ تبدیل در Gateway در انتظار تصمیم |
| AR-07 | AI Guardrails — AI حق تغییر معادله/پارامتر علمی ندارد | ✅ |
| AR-08 | Fail Closed | ✅ (`hydroma_dashboard` باید اجراشده را گزارش کند — G-H2) |
| AR-09 | Provenance Traceability | ✅ مسیر E2E؛ لایهٔ تولید در انتظار سیم‌کشی |
| AR-10 | Testable Architecture — آزمون مثبت/منفی برای هر قاعده | ✅ ۴۸ تست (۲۴ منفی + ۱۲ کنترل + درخت واقعی) |
| **AR-11** | هیچ frontend/auth/payment/blockchain در هستهٔ علمی (حفظ‌شده از سند قبلی) | ✅ `ENGINE_NO_AUTH/PAYMENT/BLOCKCHAIN` |
| **AR-12** | سرویس‌ها حق فراخوانی مستقیم درون موتور را ندارند | ⚠️ `_gateway_facade` ۶ bypass؛ allowlist ثبت و در حال کوچک‌شدن |
| **AR-13** | تمام فراخوانی مدل از Gateway | ⚠️ سه کپی eq.52 واگذار شدند (PHASES)؛ بقییه در نوبت |

## ۴. ساختار سه‌لایه و قرارداد مرز

| لایه | نام | فناوری | نقش |
|---|---|---|---|
| ۳ | هیدروما کسب‌وکار | FastAPI + **Hydroma Runtime** (بدون Docker) | بازار، رهگیری، خدمات، اشتغال |
| ۲ | Gateway + Tasmimyar + Daneshyar | Python، REST Adapter، SQLite (cache) | ترجمهٔ درخواست تجاری به زبان علمی، تصمیم مبتنی بر شواهد |
| ۱ | اکو نوژین (ZED) | Python FOSS، SQLite/GeoPackage، **pint** | محاسبات علمی آفلاین، مدل‌های لنگردار |

| موضوع | لایهٔ ۳ | لایهٔ ۲ | لایهٔ ۱ |
|---|---|---|---|
| دیتابیس | SQLite (پیش‌فرض `local`) / PostgreSQL (ردیف اختیاری `scaled`) | SQLite (cache) | SQLite/GeoPackage |
| شبکه | FastAPI REST | Adapter | آفلاین |
| واحد | رشتهٔ آزاد | اعتبارسنجی pint | UnitRegistry اجباری |
| مدل علمی | درخواست تجاری | ترجمه به CANON-ID | اجرا + S18 |
| تصمیم | سفارش/رزرو | Tasmimyar scoring | Evidence-based |
| دادهٔ خارجی | Webhook/API | Ingestion flag | Local Mirror + checksum |

## ۵. وضعیت سنجش‌شدهٔ قابلیت‌ها (جایگزین «نقشهٔ ادعا»)

| دامنه | اندازه‌گیری ۲۰۲۶-۱۰-۱۰ |
|---|---|
| مدل‌های ثبت‌شده | **۷۰**؛ بلوغ: S0 ۱۴ · S1 ۴۷ · S2 ۲ · **S3 ۷** (۹.۹٪) |
| لنگر بیرونی مستقل | **CANON-001** (FAO-56 Ex.18 = ۳.۹؛ PyETo Δ=۰) · **CANON-002** (Ex.20 = ۵.۰) · **CANON-004** (NEH/TR-55 ۵.۸۱۲۸، rel 1e-9) · RUSLE-LS (AH-703, rel 1e-12) · RothC `temp_factor` (۵ نقطهٔ چپشده) · salinity classes (USDA HB60) · NDVI/EVI/SAVI (فرم بسته + تست C++) |
| شاخص‌های اولویت‌ ۱ | ET0 **E** · Hargreaves **E** · SPI/WB/WP **method-conformance** |
| آزمون | `engine/` **۲۵۵۹ پاس / ۰ failed** · `services/` **۱۰۵۲ پاس / ۰ failed** · strict ۱۳۰۹ · guard **۰ تخلف** |
| کیفیت | ruff ۸۸۳ · DOI مرده **۰** · مسیر تست فانتوم ۵۷ (ردیابی‌شده) |
| ممیزی ادعا | `test_machine_evidence_consistency.py`: ۱۰ مدل `validated` بدون لنگر بیرونی، به‌عنوان **مجموعهٔ بدهی کوچک‌شونده** pin شده‌اند |

## ۶. کاتالوگ مدل‌ها و شاخص‌ها — با وضعیت صادقانه

### ۶.۱ مدل‌های با لنگر و بدون لنگر
| CANON | مدل | مرجع | وضعیت |
|---|---|---|---|
| 001 | ET₀ PM | FAO-56 eq. 6/21/37-40 | **VALIDATED_EXTERNAL** (Ex.18/20 + PyETo) — با انحراف مستند DEV-01 (کلمپ Rs/Rso) و DEV-02 (dtr_floor) |
| 002 | ET₀ Hargreaves | FAO-56 eq. 52 (توان ۰.۵) | **VALIDATED_EXTERNAL** (Ex.20 = ۵.۰) — باینری `.pyd` هنوز ۰.۴۸ (SB-09/G-V3-07) |
| 004 | SCS-CN | NEH/TR-55 | **VALIDATED_EXTERNAL** (rel 1e-9) |
| 005 | Theis | Theis 1935 | **VALIDATED_METHOD** — مقدار مرجع چپشده در درخت نیست؛ کارت اصلاح‌شده (۰.۳۰۶ m) |
| 006 | van Genuchten | van Genuchten 1980 + Mualem 1976 (WRR 12:513) | **PARTIAL** — جدول پارامتر `design_assumption`؛ مقایسه با Rosetta 3 ثبت (α تا ۳.۸×) |

### ۶.۲ ده شاخص نوین — **پیش‌شرط، نه ادعا**
FDII · CDHE · CMSI · WSNI · RRI · IWEq · WAI · WVI · PSI · CW — **هیچ‌کدام پیاده نیستند**. قاعده: هر شاخص پیش از کدنویسی باید **تعریف چپشده + لنگر مرجع مستقل** داشته باشد (الگوی FAO-56 Example 18). تا آن زمان پیاده‌سازی، نقض SB-06 است.

### ۶.۳ کاتالوگ دادهٔ باز (ZED-Compliant)
CHIRPS v3 (Public Domain) · ERA5-Land (Copernicus) · SoilGrids 2.0 (CC BY 4.0) · WaPOR (FAO Open Access) · SRTM/FABDEM (Public Domain) · WorldClim 2.1 (CC BY 4.0).
**وضعیت آینه:** `data/mirror/` **وجود ندارد**؛ E2E در `BLOCKED_ENVIRONMENT`؛ هیچ دانلودی در هسته (ZED §۲.۲ج)/ ingestion فقط با فلگ و sidecar §۴.۲.

## ۷. اسکیماهای داده
- **SQLite (لایهٔ ۱):** `datasets` · `model_runs` · `models` · `evidence` · `claims` · `claim_evidence` · `scenarios` · `decisions` — پیاده‌شده در `adapters/persistence/sqlite_persistence.py` (۱۱ تست)؛ سیم‌کشی به مسیر تولید باز (G-V3-09).
**تصمیم DP-2 — حذف Docker و ارکستراتور (۲۰۲۶-۱۰-۱۰):** اجرا با **`runtime/`** (ناظر فرایند خالص‌پایتون: `python -m runtime.supervise up|down|status`) انجام می‌شود؛ نه Docker، نه Kubernetes/Helm، نه رجیستری ایمیج.
**ردیف‌های ذخیره‌سازی:** `local` (پیش‌فرض) = SQLite با WAL — صفر نصب، صفر سرور، پشتیبان فایلی با `runtime/backup.py`. `scaled` (اختیاری) = PostgreSQL وقتی مقیاس خواست؛ در هر دو ردیف، لایهٔ ۱ به SQLite خود وفادار است و هیچ دسترسی مستقیمی بین PostgreSQL لایهٔ ۳ و جداول لایهٔ ۱ وجود ندارد (DP-1).

## ۸. KPIها با خط‌مبنای واقعی

| شاخص | خط‌مبنای امروز | هدف ۹۰ روزه | هدف بلندمدت |
|---|---|---|---|
| Scientific Validation Coverage (S3/کل) | **۹.۹٪** | ≥ ۲۵٪ | ≥ ۸۰٪ |
| Reference Data (CANON-001..006) | **۳/۶** | ۵/۶ | ۶/۶ |
| Test Coverage (خط/قرارداد/علم) | سنجش‌نشده | ≥ ۸۰٪ مسیرهای اصلی Gateway | ≥ ۸۰٪ |
| Import Guard | **۰ تخلف** | ۰ | ۰ |
| Provenance Completeness | مسیر E2E | تولید + تصمیم | ۱۰۰٪ |
| ادعاهای بی‌لنگر | **۱۰ مدل** | ۰ | ۰ |

## ۹. حکمرانی AI — چهار سطح اختیار
۱) اطلاعی → Daneshyar (Epistemic + Evidence) · ۲) عملیاتی کم‌ریسک → Tasmimyar CAUTION ≥ ۰.۴ · ۳) اجرایی محدود → RECOMMEND ≥ ۰.۷ + SB-05 · ۴) حساس → STOP + تأیید انسانی + Audit Log.
**Quick Scan پیش از هر تسک (۵ دستور):** `pytest engine/ -q` (≥۲۵۵۹، ۰ failed) · `pytest services/ -q` (≥۱۰۵۲، ۰ failed) · `tools/detect_imports.py --root .` (PASS) · `ruff check .` (F۸۲۱ = ۰) · `mypy engine` (بدون خطای جدید). خط‌مبناها فقط **بالا** می‌روند.

## ۱۰. نقشهٔ راه ۹۰ روزه — بازپایه‌گذاری‌شده روی وضعیت سنجش‌شده

| فاز | وضعیت امروز | کار باقی‌مانده |
|---|---|---|
| **ECO-00/01/02/03/04** (Gateway، ۱۷ مسیر، exponent، اعتبارسنجی ورودی) | ✅ انجام‌شده در تاریخچهٔ پروژه (commit `6e7b8b4` ~۷۵ مسیر dispatch واقعی؛ منبع exponent ۰.۵) | ✷ باینری ۰.۴۸ (بازسازی C++ در CI — نیازمند تصمیم کامیت `.github/`) · ✷ سیم‌کشی SQLite spec · ✷ گزارش «اجراشده» داشبورد |
| **ECO-05..08** (Tasmimyar/Daneshyar/Provenance/Mirror) | ⚠️ موتورها درون‌حافظه‌اند؛ Provenance در مسیر E2E | تفکیک `evidence_engine/provenance_tracker`، `claim_registry/epistemic_manager/conflict_resolver`، `problem_formulator/mca_engine/sensitivity_analyzer` · Mirror + ingestion (نیازمند تصمیم منبع داده) |
| **ECO-09..11** (شاخص‌ها در H2/H5 + Canary Dispatch) | ❌ ده شاخص نوین پیاده نیستند؛ Canary Dispatch نیست | تعریف چپشدهٔ هر شاخص، سپس پیاده‌سازی یک‌یک · زیرساخت A/B مدل |
| **ECO-12..14** (اقتصاد، خدمات، اشتغال) | ⚠️ NPV/Payback در موتور (دو قرارداد ناهمخوان در بسته) · finance در لایهٔ ۳ | یکسان‌سازی قرارداد NPV/payback · اتصال Tasmimyar به H1 |
| **ECO-15..17** (رهگیری، اقتصاد محلی، پایلوت) | ❌ | provenance_chain هر محموله · RRI/WSNI · پایلوت ۱۰ سفارش |

## ۱۱. چک‌لیست PR و Definition of Done
چک‌لیست همان سند موقت، با دو افزوده: **(الف)** `tools/check_citations.py` سبز (dead=۰) **(ب)** `tools/phantom_path_check.py` بدون مسیر فانتوم جدید **(ج)** هر ادعای عددی شواهد ممیزی دارد (Decision Log در `GAP-REGISTER.md`).

## ۱۲. پیوست — مسیرهای واقعی (فقط آنچه وجود دارد)
`engine/gateway/__init__.py` · `engine/models/registry.py` و `engine/models/maturity.py` · `engine/tasmimyar/__init__.py` · `engine/evidence/__init__.py` · `engine/knowledge/__init__.py` · **`engine/honesty/statuses.py`** (قراردادهای صداقت) · `engine/strict_tests/test_s16_gateway_strict_contracts.py` · `engine/strict_tests/test_s18_scientific_validation.py` · `engine/ports/persistence_port.py` · `adapters/persistence/sqlite_persistence.py` · `tests/reference_data/` (FAO-56 Ex.18/20، جدول McKee، قرارداد meta.json) · `tools/detect_imports.py` · `tools/phantom_path_check.py` · `tools/check_citations.py` · `tools/run_e2e_demo.py` · `tools/regenerate_ptf_reference.py` · `tools/characterize_texture_classifier.py` · `reports/eco-nojin/` (GAP-REGISTER · FORMULA-VALIDATION-REGISTER · FORMULA-EVIDENCE-REGISTER · DEVIATION-REGISTER · EQUATION-DIVERGENCE-REGISTER · EXTERNAL-ALIGNMENT-PLAN · SPEC-V3.1-PATCH · RESUME-STATE).

---

### والانت‌های ثبت‌شده برای بازبینی بعدی
`engine/hydroma/soil/ptf_reference.json` (artifact Rosetta/CC0، ۸.۳۵KB) · `engine/hydroma/spi_calculator.py` · `engine/gateway/pint_audit.py` · `engine/hydroma/data_pipeline/download_gate.py`.
