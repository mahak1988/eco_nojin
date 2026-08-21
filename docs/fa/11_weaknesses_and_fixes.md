# ۱۱. نقاط ضعف و اقدامات اصلاحی

**وضعیت:** پیش‌نویس برای بازبینی | **نسخه:** 1.0.0 | **زبان:** فارسی
**دامنه:** پلتفرم Eco Nojin و موتور HyDroMa | **تاریخ ارزیابی:** ۱۴۰۵-۰۵-۲۳ (2026-08-14)

## 1. هدف

فهرست موردی نقاط ضعف شناخته‌شده حاصل از بازبینی کدبیس، هرکدام با اقدام اصلاحی،
وضعیت و شواهد در سطح فایل. معنی وضعیت‌ها:

- **رفع‌شده** — اصلاح در کدبیس راستی‌آزمایی شده است.
- **در حال رفع** — پیاده‌سازی جزئی وجود دارد یا رفع در گام‌های فوری نقشه راه
  فعال است.
- **برنامه‌ریزی** — ثبت شده اما شروع نشده.

هر ادعای «رفع‌شده» باید پیش از به‌روزرسانی این فهرست از روی کد دوباره
راستی‌آزمایی شود؛ در تاریخ ارزیابی هیچ موردی «رفع‌شده» ثبت نشده است، چون هیچ
اصلاحی در کد راستی‌آزمایی نشده است.

## 2. فهرست نقاط ضعف

| شناسه | ناحیه | شرح ضعف | اقدام اصلاحی | وضعیت | شواهد |
|---|---|---|---|---|---|
| W-001 | داده ماهواره | `EarthSearchProvider.fetch_tile()` به‌جای پیکسل‌های واقعی Sentinel-2، **باندهای تصادفی مصنوعی** (`np.random.uniform`) با seed از هش شناسه آیتم برمی‌گرداند | جایگزینی با دانلود GeoTIFF واقعی از پیوندهای دارایی STAC؛ افزودن ابرزدایی، پرچم کیفیت و فیلد منشأ داده؛ نگه‌داشتن پرچم سخت «شبیه‌سازی‌شده» روی هر خروجی نمایشی | برنامه‌ریزی | `engine/hydroma/satellite/providers/earth_search.py` (`fetch_tile`، با عبارت «simplified mock … synthetic data for demo»)؛ هشدار در `docs/02` بند ۷ و `docs/06` بند ۳ |
| W-002 | باگ API | `verify_carbon_project` در روتر کربن از `datetime.utcnow()` استفاده می‌کند اما `datetime` **هرگز import نشده** در `routers/carbon.py` → `NameError` قطعی در `POST /api/v1/carbon/projects/{id}/verify` | افزودن import مربوطه؛ افزودن تست یکپارچه برای جریان verify (اکنون بی‌تست است)؛ اصلاح همین الگو در جاهای دیگر | در حال رفع | `services/api_gateway/routers/carbon.py` (~خط ۲۰۰، `project.verification_date = datetime.utcnow()`)؛ در importهای ابتدای فایل `datetime` نیست؛ در `docs/09_roadmap.md` بند ۳ مورد ۳ («datetime import bug in carbon verify endpoint») |
| W-003 | CORS | اوریجین وحشی با اعتبارنامه: `allow_origins=["*"]` + `allow_credentials=True` — ترکیب نامعتبر؛ مرورگرها درخواست‌های دارای اعتبارنامه را رد می‌کنند؛ لیست سفید اوریجین نیست | جایگزینی با لیست سفید صریح (اوریجین‌های توسعه + دامنه‌های مستقر)؛ حذف credentials یا محدودکردن به اوریجین‌های شناخته‌شده؛ افزودن تست بازگشتی CORS | برنامه‌ریزی | `services/api_gateway/main.py` (بلاک CORSMiddleware)؛ اشاره در `docs/06` بند ۲ و `docs/09` بند ۳ مورد ۳ |
| W-004 | داربست سرویس‌ها | `services/auth`، `services/ledger`، `services/notification`، `services/reporting`، `services/workflow` فقط `main.py` placeholder دارند که یک رشته چاپ می‌کند؛ پیاده‌سازی نیست | پیاده‌سازی طبق فازهای نقشه راه (اول auth چون دروازه همه نقطه‌های نوشتن است)؛ افزودن README و تست هر سرویس پیش از اتصال به گیت‌وی | برنامه‌ریزی | `services/*/main.py` (هرکدام «Eco Nojin service placeholder: …» چاپ می‌کند)؛ طرح فازها در `docs/00` |
| W-005 | وابستگی‌ها | `requirements.txt` **هیچ پین نسخه‌ای ندارد**؛ `pyproject.toml` مقدار `dependencies = []` (خالی) اعلام می‌کند؛ فایل قفل نیست | پین با بازه‌های سازگار؛ تفکیک لایه‌های base/research/prod؛ افزودن فایل‌های قفل (`pip-tools`/`uv`)؛ ممیزی نسخه‌ها (`pip-audit`) | برنامه‌ریزی | `requirements.txt` (فهرست بدون پین شامل fastapi، sqlalchemy، torch، celery…)؛ `pyproject.toml` بخش `[project] dependencies = []`؛ نقشه راه بند ۳ مورد ۱ |
| W-006 | مستندات | بخش فارسی `README.md` ریشه **mojibake** است (UTF-8 نامعتبر؛ سرفصل و پاراگراف به کاراکترهای جایگزین/نویسه‌های CJK خراب تبدیل شده) | بازنویسی بخش فارسی با UTF-8 درست؛ افزودن بررسی (مثلاً آزمون encoding) به CI تا بازنگردد | برنامه‌ریزی | `README.md` — خواندن بایت‌محور کاراکترهای جایگزین U+FFFD را در بلاک فارسی نشان می‌دهد؛ نقشه راه بند ۳ مورد ۳ («README Persian encoding») |
| W-007 | رازها | `docker-compose.yml` رمز لفظی `***` برای PostGIS دارد؛ `.env.example` از `change_me` استفاده می‌کند | حذف رازهای لفظی؛ استفاده از جایگزینی محیطی + vault (یا اعتبارنامه صرفاً توسعه‌ای تولیدشده)؛ مستندسازی چرخش | برنامه‌ریزی | `docker-compose.yml` (`POSTGRES_PASSWORD: ***`)؛ `.env.example` (`change_me`)؛ هشدار `docs/08` بند ۲ |
| W-008 | i18n (RAG) | دستیار دانش **فقط انگلیسی** است: برداری‌ساز TF-IDF از `stop_words="english"` استفاده می‌کند؛ هر ۱۰ سند دانش انگلیسی‌اند | افزودن پیکره فارسی (سپس عربی) با برداری‌ساز هر زبان؛ مسیریابی با `Accept-Language`؛ ترجمه محتوای مشاوره‌ای با بازبینی متخصص (طبق `docs/07` بند ۷) | برنامه‌ریزی | `engine/hydroma/ai_assistant/rag_engine.py` (stop_words)، `knowledge_base.py` (۱۰ سند انگلیسی)؛ `docs/07` بند ۶ |
| W-009 | i18n (RTL) | RTL **ناقص** است: `app/layout.tsx` مقدار `<html lang="en" dir="ltr">` را ثابت گذاشته؛ جهت فقط پس از hydration در سمت کلاینت تغییر می‌کند، پس SSR/HTML اولیه همیشه LTR است | رندر سمت سرور `lang`/`dir` بر اساس زبان (از درخواست یا کوکی)؛ بررسی دیداری چیدمان fa/ar/ur؛ تست HTML سمت سرور | در حال رفع | `frontend/app/layout.tsx` (ltr ثابت)؛ `frontend/lib/i18n-context.tsx` پس از hydration مقدار `document.documentElement.dir` را تنظیم می‌کند (رفع جزئی موجود)؛ `docs/07` بند ۲ |
| W-010 | پیکربندی فرانت | آدرس پایه API به‌صورت **هاردکد** `http://127.0.0.1:8000` در ۹ فایل کامپوننت | معرفی یک آدرس پایه قابل‌پیکربندی واحد (متغیر محیط / پیکربندی عمومی `next.config.js`)؛ متمرکزکردن لایه fetch | برنامه‌ریزی | `frontend/components/`: `BenchmarkPanel.tsx:19`، `CarbonCreditPanel.tsx:33`، `ChatAssistant.tsx:32`، `CropPlannerPanel.tsx:30`، `MarketplacePanel.tsx:37`، `SatellitePanel.tsx:67`، `ScenarioPanel.tsx:33,59`، `SoilDashboard.tsx:21`، `WatershedPanel.tsx:21` |
| W-011 | کنترل نسخه | **مخزن Git وجود ندارد** — `git status` گزارش «not a git repository» می‌دهد؛ `.git`، تاریخچه، برچسب و میزبان CI نیست | `git init` با commit پایه تمیز؛ سیاست شاخه؛ افزودن CI روی اولین commit | برنامه‌ریزی | `D:\eco_nojin` — بدون `.git`؛ نقشه راه بند ۳ مورد ۱؛ چک‌لیست `docs/08` بند ۸ |
| W-012 | راستی‌آزمایی کربن | نقطه پایانی `/verify` **نمایشی** است نه فرایند معتبر: فقط `status` را به `verified` با رشته verifier پیش‌فرض و بدون زنجیره شواهد تغییر می‌دهد | انتخاب روش‌شناسی واقعی (مثلاً Verra ARR یا VM0042)؛ پیاده‌سازی baseline/additionality/leakage/permanence؛ داخلی و برچسب‌خورده نگه‌داشتن `/verify` تا زمانی که راستی‌آزمایی معتبر ممکن شود | برنامه‌ریزی | `services/api_gateway/routers/carbon.py` (`verify_carbon_project`)؛ `engine/hydroma/carbon/calculator.py` (دفتر ثبت در حافظه، تخفیف ۱۵٪ سراسری)؛ `docs/05` بند ۳ (وضعیت صادقانه) |
| W-013 | مدل عددی | معادلات ساده‌شده به‌عنوان پیش‌فرض محصول بدون مستندسازی کامل محدودیت: مدل محصول سبک AquaCrop؛ حجم رواناب با روش منطقی؛ جدول‌های نرخ منطقه‌ای کربن | افزودن یادداشت محدودیت درون‌کدی (بازه اعتبار، کاربرد موردنظر، حاشیه خطا) کنار هر فرمول؛ پیوند به تست‌های عددی STD-014؛ انتشار فهرست تقریب‌های مدل | در حال رفع | `engine/hydroma/scenarios/crop_scenarios.py` («simplified AquaCrop approach»)؛ `engine/hydroma/watershed/calculator.py` (`calculate_runoff` روش منطقی، بدون یادداشت محدودیت)؛ `engine/hydroma/carbon/calculator.py`؛ پوشش نثری جزئی در `docs/02` بند ۴،۷ و `docs/05` بند ۳ |
| W-014 | لایه داده | **SQLite بدون مهاجرت**: `database.py` مقدار `sqlite:///./hydroma_research.db` را ثابت دارد؛ `Base.metadata.create_all` در راه‌اندازی؛ نه Alembic نه تاریخچه مهاجرت | معرفی Alembic با مهاجرت پایه اولیه؛ یکتا کردن راه‌اندازی؛ برنامه‌ریزی مسیر مهاجرت SQLite→PostGIS | برنامه‌ریزی | `engine/hydroma/core/database.py`؛ `services/api_gateway/main.py` (create_all)؛ هیچ `alembic*` در کل درخت؛ `docs/04` بند ۷ |
| W-015 | یکپارچگی داده | **اثر ردیابی تغییرات داده نیست**: دفترهای ثبت در حافظه‌اند و هیچ جدولی ثبت نمی‌کند چه کسی چه چیزی را کی تغییر داده (ستون‌های ممیزی/لاگ تغییر نیست) | افزودن فیلدهای ممیزی (created_by، updated_at، دلیل تغییر) و جدول/جریان رویداد تغییر؛ ثبت همه تغییرات از یک مسیر واحد | برنامه‌ریزی | `engine/hydroma/carbon/calculator.py` (`_projects` در حافظه)، `engine/hydroma/marketplace/` (مدل‌های در حافظه)، `services/api_gateway/routers/sync.py` (`_sync_log` در حافظه)؛ نبود جدول ممیزی در `engine/hydroma/core/models.py` |

## 3. یافته‌های تکمیلی این بازبینی (فراتر از فهرست اولیه)

| شناسه | ناحیه | شرح ضعف | اقدام اصلاحی | وضعیت | شواهد |
|---|---|---|---|---|---|
| W-016 | امنیت | **احراز هویت/مجوز نیست**: هر نقطه پایانی نوشتن باز است (سفارش بازار، ثبت پروژه کربن، sync batch، ایجاد خاک)؛ سرویس auth placeholder است | پیاده‌سازی سرویس OIDC با نقش‌ها (کشاورز، تعاونی، NGO، مدیر)؛ محافظت همه نقطه‌های نوشتن؛ افزودن auth به تست‌های یکپارچه | برنامه‌ریزی | `services/auth/main.py` (placeholder)؛ هیچ `Depends`/وابستگی auth در هیچ روتری؛ مدل تهدید در `docs/06` بند ۳ |
| W-017 | امنیت | **TLS نیست**: توسعه روی HTTP است؛ HSTS نیست؛ فرانت دارای CVE ردیابی‌شده (Next.js 15.1.6، CVE-2025-66478، اصلاح 16.3.1+) | پایان TLS پیش از هر استقرار غیرمحلی؛ HSTS؛ ارتقای Next.js طبق برنامه مهاجرت در `docs/security/CVE-2025-66478.md` | برنامه‌ریزی | `docs/06` بند ۲ («Transport security: Not configured yet»)؛ `docs/security/CVE-2025-66478.md` |
| W-018 | تست | **مجموعه تست قرمز است**: `test_health_reports_mobile_features` ناموفق است (اجرا ۱۴۰۵-۰۵-۲۳: ۱۲۷ موفق، ۱ ناموفق) چون نقطه پایانی سلامت `mobile_features` را در فهرست مدول‌ها ندارد | اصلاح پاسخ سلامت در `main.py` (افزودن مدول یا حذف assert) — یک خط؛ سپس الزام CI سبز | در حال رفع | `tests/integration/test_sync.py`؛ `services/api_gateway/main.py` (فهرست مدول‌های سلامت)؛ نتیجه اجرای pytest در ۱۴۰۵-۰۵-۲۳؛ نقشه راه بند ۳ مورد ۳ («stale mobile_features test») |
| W-019 | ماندگاری | **وضعیت در حافظه است**: پروژه‌های کربن، کاتالوگ/سفارش‌های بازار و لاگ sync با ری‌استارت از بین می‌روند؛ ذخیره ماندگار برای موجودیت‌های فاز ۱ نیست | ماندگاری در SQLite اکنون و PostGIS بعداً (هم‌راستا با مهاجرت W-014)؛ افزودن تست یکپارچه ماندگاری | برنامه‌ریزی | `engine/hydroma/carbon/calculator.py` (`_projects`)؛ `engine/hydroma/marketplace/*` (طبق `docs/04` بند ۳)؛ `routers/sync.py` (`_sync_log`) |
| W-020 | وابستگی‌ها | **انحراف requirements**: `requirements.txt` (نیّت تولید: netcdf4، zarr، xgboost، lightgbm، mlflow، torch، celery، redis، psycopg، geoalchemy2) با محیط تحقیقاتی واقعی نمی‌خواند (`.venv` از `requirements-research.txt` شامل duckdb، numba، diskcache، jinja2، python-multipart است)؛ وابستگی‌های `pyproject.toml` خالی است | هم‌راستاسازی در requirements پین‌شده و لایه‌ای (base/research/prod)؛ ثبت محیط طلایی (`pip freeze` در فایل قفل)؛ افزودن بررسی CI که requirements با importها می‌خواند | برنامه‌ریزی | `requirements.txt` در برابر `requirements-research.txt` در برابر فهرست `.venv/Lib/site-packages` (۱۴۰۵-۰۵-۲۳)؛ `pyproject.toml` |
| W-021 | دسترس‌پذیری | **شکاف‌های WCAG 2.1 AA**: هیچ `aria-*`/`role` در هیچ کامپوننتی نیست؛ `userScalable: false` بزرگ‌نمایی را مسدود می‌کند (شکست ۱.4.4)؛ ورودی‌های بدون برچسب در چند پنل | اجرای ممیزی axe؛ اصلاح کنتراست/فوکوس/بزرگ‌نمایی/برچسب‌ها طبق STD-006 پیش از عرضه عمومی | برنامه‌ریزی | `frontend/components/*.tsx` (۰ مورد aria)؛ `frontend/app/layout.tsx` viewport (`userScalable: false`)؛ `CarbonCreditPanel.tsx` و… |

## 4. خلاصه

| وضعیت | تعداد | شناسه‌ها |
|---|---|---|
| رفع‌شده | ۰ | — |
| در حال رفع | ۳ | W-002، W-009، W-018 (و W-013 به‌صورت جزئی) |
| برنامه‌ریزی | ۱۸ | W-001، W-003، W-004، W-005، W-006، W-007، W-008، W-010، W-011، W-012، W-014، W-015، W-016، W-017، W-019، W-020، W-021 |

نکات:

- هیچ موردی **رفع‌شده** ثبت نشده: بازبینی هیچ تغییر کدی که ضعفی را اصلاح کرده
  باشد نیافت. W-013 تنها به این معنا *در حال رفع* است که یادداشت‌های محدودیت
  نثری در `docs/02` و `docs/05` وجود دارد؛ یادداشت‌های درون‌کدی و تست‌های عددی
  (STD-014) همچنان غایب‌اند.
- هر سه مورد *در حال رفع* (W-002، W-009، W-018) در فهرست نقص‌های «گام‌های
  بعدی فوری» نقشه راه هستند (`docs/09_roadmap.md` بند ۳).
- موارد W-016 تا W-021 افزوده‌های این بازبینی مستقل‌اند و در برابر فایل‌ها در
  تاریخ ۱۴۰۵-۰۵-۲۳ راستی‌آزمایی شده‌اند.

## 5. قاعده به‌روزرسانی

این فهرست فقط با شواهد به‌روز می‌شود:

1. فایل(های) مرجع را دوباره بخوانید و تغییر را تأیید کنید.
2. وضعیت را به **رفع‌شده** تغییر دهید و commit/تاریخ را یادداشت کنید.
3. اگر از کامل بودن رفع مطمئن نیستید، **در حال رفع** ثبت کنید، هرگز رفع‌شده.
4. فهرست را در هر نقطه عطف فاز بازبینی کنید (هم‌راستا با `docs/05_standards.md`
   بند ۶ و `12_30_year_strategy.md`).

## 6. مراجع

- `10_quality_standards.md` — استانداردهایی که این ضعف‌ها نقض می‌کنند.
- `12_30_year_strategy.md` — برنامه بلندمدت که این اصلاحات را جذب می‌کند.
- `docs/en/06_security_privacy.md`، `docs/en/08_deployment_operations.md`،
  `docs/en/09_roadmap.md` — سوابق صادقانه پیشین.
