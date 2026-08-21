# گزارش مطالعه مستندات پروژه اکو نوژین (Eco Nojin / HyDroMa)

**تهیهشده توسط:** زیرعامل تحلیلگر فنی-راهبردی
**تاریخ:** 2026-08-17
**مسیر مطالعهشده:** `D:\eco_nojin`
**محدوده:** `docs/en/` (۲۶ فایل)، `docs/fa/` (۱۶ فایل + ۴ گزارش تحقیقاتی)، `docs/security/` (۱ فایل CVE)، و ۷ فایل مارکداون ریشهای.

---

## روششناسی

تمام فایلهای فهرستشده با PowerShell (`Get-ChildItem`، `Get-Content -Raw -Encoding UTF8`) خوانده شدند. هیچ فایلی از `docs/en/` (شامل 00 تا 99 و فایلهای 22/23) از قلم نیفتاده است. اعداد و وضعیتها مستقیم از متن مستندات نقل شدهاند؛ جایی که بین دو سند تناقض وجود داشت، ثبت شده است (به بخش «شکافهای مستندسازی» مراجعه کنید).

---

## بخش ۱: `D:\eco_nojin\docs\en\` — خلاصه تمام فایلها

### 00_master_plan.md — طرح جامع و فازها
سند راهبردی مصوب (v1.0.0) که چشم‌انداز را «زیرساخت دیجیتال استاندارد بین‌المللی برای پل زدن بین علوم محاسباتی پیشرفته و معیشت روستایی» تعریف می‌کند. چهار هدف محوری: (۱) احیای اکولوژیک (بیابان‌زدایی، احیای آبخیز، کربن آلی خاک)، (۲) شمول اقتصادی (هویت دیجیتال، اعتبارسنجی جایگزین، بیمه شاخص‌محور، دسترسی به بازار کربن/ارگانیک)، (۳) دقت علمی (موتور شبیه‌سازی چندفیزیکی HyDroMa + ML فیزیک‌آگاه)، (۴) انطباق جهانی (FAO، UN SDGs، ISO 14064، OGC). **فازهای پنج‌گانه:** Phase 1 (تحقیق و MVP: ماژول‌های خاک/آب/گیاه، SQLite/DuckDB) ← Phase 2 (اکوسیستم و مواد: بیوچار، کمپوست، سازه‌های آبخیز) ← Phase 3 (ریسک و بحران: هشدار زودهنگام خشکسالی/سیلاب، بیمه شاخص‌محور) ← Phase 4 (شمول و اقتصاد: مسیریابی عشایر، مارکت‌پلیس، اعتبار خرد، توکن پاداش) ← Phase 5 (مقیاس جهانی: تأیید اعتبار کربن، دفترکل بلاک‌چین، امنیت پساکوانتوم، یکپارچگی API بین‌المللی). گروه‌های هدف: کشاورزان خردهمالک، دامداران/عشایر، جوانان و زنان روستایی، دولت‌ها و NGOها.

### 01_architecture.md — معماری
الگوی «Modular Monolith در حال تکامل به Microservices» با معماری API-first و لایه جداشده‌ی موتور محاسباتی. چهار لایه: (۱) رابط‌های کاربر (Next.js با i18n ۱۴ زبانه، USSD/SMS برای دسترسی آفلاین، Voice/IVR)، (۲) API Gateway و سرویس‌ها (FastAPI: Auth، Workflow، Ledger، Notification)، (۳) موتور HyDroMa (ارکستراسیون پایتون + هسته C++ برای Richards، Saint-Venant، RUSLE با اتصال pybind11)، (۴) لایه داده (DuckDB، SQLite/GeoPackage، فایل‌های GeoTIFF/NetCDF محلی). لایه Trust/Ledger برای هش رمزنگاری داده‌های MRV و آمادگی امضای پساکوانتوم (ML-KEM/ML-DSA). مثال جریان داده: دریافت آب‌وهوا ← محاسبه ET0 با هسته FAO-56 Penman-Monteith ← تصحیح با ML ← خروجی استاندارد OGC/WaterML 2.0 ← تحویل بومی‌سازی‌شده از طریق SMS یا داشبورد. اصل «حاکمیت داده»: کشاورز مالک داده است و داده‌های تجمیعی قبل از استفاده خارجی ناشناس‌سازی می‌شوند.

### 02_hydroma_engine.md — موتور علمی HyDroMa
موتور هیبرید: لایه ارکستراسیون پایتون، مسیر عددی شتاب‌یافته Numba-JIT، و هسته C++20 با ماژول pybind11 (هر کرنل نسخه پایتونی عدداً یکسان دارد). موجودی ماژول: هیدرولوژی (Muskingum-Cunge)، فیزیک خاک (van Genuchten)، شاخص‌های پوشش گیاهی، فرسایش RUSLE، اقلیم FAO-56/Hargreaves، ماشین‌حساب کربن (حالت تخمین)، سناریوها (SSP، محصول، مونت‌کارلو)، تحلیل ماهواره‌ای، مارکت‌پلیس (in-memory)، دستیار دانش RAG (TF-IDF با ۱۰ سند FAO)، سازه‌های آبخیز، USSD/SMS، بنچمارک. «صداقت علمی» در بخش ۷: باندهای ماهواره‌ای فعلاً **سنتتیک (شبیه‌سازی‌شده)** هستند؛ ارقام کربن تخمین پیش‌از-تأیید هستند. مراجع علمی کامل (FAO-56، Carsel & Parrish 1988، Cunge 1969 و…).

### 03_eco_nojin_platform.md — پلتفرم
تعریف پلتفرم بین‌المللی برای احیای اکوسیستم، کشاورزی هوشمند، مدیریت آب/خاک، رفاه روستایی، حمایت از دامداران، مشوق‌های کربن، مارکت‌پلیس و اکوتوریسم. رابط‌های کاربر: وب/PWA (Next.js، ۱۴ زبان، PWA آفلاین-اول با IndexedDB و Capacitor)، دروازه USSD `*384*73#` و دستورات SMS (SOIL، CROP، PRICE، WEATHER، ASK)، و Voice/IVR (برنامه‌ریزی‌شده). جدول صادقانه وضعیت سرویس‌ها: api_gateway پیاده‌سازی‌شده؛ auth/ledger/workflow/notification/reporting **Placeholder** (stub چاپی)؛ blockchain/ml/deploy اسکلت خالی. محدودیت‌های فعلی: URL هاردکد `http://127.0.0.1:8000` در فرانت، نبود لایه احراز هویت، داده ماهواره‌ای شبیه‌سازی‌شده.

### 04_data_model.md — مدل داده
راهبرد ذخیره‌سازی: حالت تحقیق SQLite (`hydroma_research.db`) با SQLAlchemy؛ تولید هدف PostgreSQL/PostGIS (کامپوز `postgis/postgis:16-3.4`). موجودیت‌های هسته: `soil_profiles` (بافت، pH، EC، ماده آلی)، `plants` (نام علمی، نیاز آبی، تحمل خشکی/شوری)، `materials` (نسبت C/N). موجودیت‌های مارکت‌پلیس (in-memory): Product/Producer/Order با چرخه‌ی pending→confirmed→shipped→delivered. پروژه‌های کربن (in-memory): ۷ نوع با وضعیت draft→submitted→verified. داده‌های ماهواره‌ای/اقلیم: NASA POWER (زنده و واقعی)، Sentinel-2 L2A از STAC عمومی Element 84 (متادیتا واقعی، **ارزش باند شبیه‌سازی‌شده**). نکته مهم: هنوز از `create_all` در استارت‌آپ استفاده می‌شود و Alembic در آن زمان «کار برنامه‌ریزی‌شده» بوده است (بعداً در Phase 0 انجام شد — به سند 13 مراجعه کنید).

### 05_standards.md — استانداردهای بیرونی
چارچوب‌های راهنما: FAO، IFAD، World Bank، WMO، ISO، OGC، UN SDGs، GODAN، چارچوب‌های گزارش‌دهی کربن. جدول استانداردهای علمی: FAO-56 (پیاده‌سازی‌شده)، AquaCrop (تقریب ساده‌شده)، RUSLE (پیاده‌سازی‌شده در C++)، van Genuchten/Mualem (پیاده‌سازی‌شده)، OGC API Features و WaterML 2.0 (برنامه‌ریزی‌شده)، IPCC AR6/SSP (جداول منطقه‌ای ساده‌شده). **وضعیت صادقانه کربن:** ISO 14064 فقط hook معماری دارد؛ Verra VCS/Gold Standard صرفاً به روش‌شناسی‌ها ارجاع می‌دهند ولی خروجی فعلی «تخمین پیش‌از-تأیید» با تخفیف عدم‌قطعیت ۱۵٪ است؛ اندپوینت `/verify` یک دموی داخلی است نه گواهینامه. نگاشت SDG: اهداف ۱، ۲، ۵، ۶، ۸، ۱۳، ۱۵. مرور انطباق در هر milestone فاز.

### 06_security_privacy.md — امنیت و حریم خصوصی
اصول: حاکمیت داده کشاورز، ناشناس‌سازی، حداقلی‌سازی جمع‌آوری، آمادگی پساکوانتوم. **وضعیت فعلی (صادقانه):** ترنسپورت TLS پیکربندی نشده (HTTP در dev)؛ احراز هویت پیاده‌سازی نشده؛ CORS با `allow_origins=["*"]` + `allow_credentials=True` (ترکیب نامعتبر)؛ سکرت‌ها با `change_me` و `***` در docker-compose؛ وابستگی‌ها پین‌نشده؛ دیتابیس SQLite رمزنگاری‌نشده. تهدیدهای کلیدی: قرارگیری در معرض API بدون احراز هویت، داده ماهواره‌ای شبیه‌سازی‌شده که نباید به‌عنوان واقعی ارائه شود، و ریسک قانونی/تقلبی ارائه خروجی `/verify` به‌عنوان اعتبار گواهی‌شده. کنترل‌های هدف: OAuth2/OIDC با نقش‌ها، CORS allowlist، HTTPS/HSTS، vault سکرت، پین و ممیزی وابستگی، جداسازی داده tenant، لاگ ممیزی MRV با هش رمزنگاری.

### 07_i18n_localization.md — بین‌المللی‌سازی
i18n از روز اول الزام بوده است. فرانت: ۱۴ فایل locale (en, fa, ar, de, es, fr, hi, it, ms, pt, ru, ur, zh, bn) + `backend_translations.json`؛ سوئیچر زبان با ذخیره در localStorage. **شکاف:** RTL برای fa/ar/ur ناقص است (layout هاردکد `dir="ltr"`، سوییچ سمت کلاینت بعد از hydration — ارجاع به W-009). بک‌اند فعلاً انگلیسی است؛ ترجمه سمت فرانت انجام می‌شود؛ `Accept-Language` برنامه‌ریزی‌شده. USSD/SMS: en/fa/ar با محدودیت ۱۶۰ کاراکتر SMS و ۱۸۲ کاراکتر USSD. دانش‌نامه RAG فقط انگلیسی. فرایند کیفیت ترجمه: بازبینی انسانی جامعه/آژانس برای اصطلاحات کشاورزی، بدون ترجمه ماشینی خام برای محتوای مشاوره‌ای.

### 08_deployment_operations.md — استقرار و عملیات
محیط توسعه: بک‌اند Python 3.11 + FastAPI/Uvicorn؛ فرانت Next.js با pnpm؛ تست‌ها `pytest` (در آن زمان ۱۲۶ تست). IaC فعلی: `docker-compose.yml` با postgis و redis (شامل پلیسهولدر رمز `***`). پیکربندی از `.env.example` (کلیدهای PROJECT_NAME، ENGINE_NAME، ENVIRONMENT، DATABASE_URL، REDIS_URL). CI/CD برنامه‌ریزی‌شده (deploy/ci و deploy/k8s خالی). **الزام فوری در آن زمان: راه‌اندازی Git** (پروژه تحت version control نبود). سه محیط: Local research / Staging pilot / Production. چک‌لیست پیش-پایلوت: git init، جایگزینی سکرت‌ها، دانلود واقعی Sentinel-2، TLS + CORS، پیاده‌سازی auth، پین وابستگی‌ها، تعریف زمان‌بندی بکاپ.

### 09_roadmap.md — نقشه راه در برابر واقعیت
جدول تطبیق فاز ۰۰ با واقعیت: فاز ۱ «بیشتر انجام‌شده»، فاز ۲ «کمپوست و آبخیز انجام؛ بیوچار فقط در KB»، فاز ۳ «رودینگ سیلاب و SSP انجام؛ EWS/بیمه pending»، فاز ۴ «مارکت‌پلیس و USSD انجام؛ مسیریابی/اعتبار/توکن pending»، فاز ۵ «فقط اسکلت». کارهای تکمیل‌شده: موتور HyDroMa (۳۵ تست سبز C++)، API gateway با ۱۱ ناحیه روتر، مارکت‌پلیس، ماشین‌حساب کربن، موتور سناریو، خط لوله ماهواره (STAC + باند شبیه‌سازی‌شده)، RAG، فرانت Next.js PWA با ۱۴ زبان، USSD/SMS، ۱۲۵/۱۲۶ تست سبز. **قدم‌های بعدی فوری:** Git+CI، داده ماهواره‌ای واقعی، رفع باگ datetime در اندپوینت verify کربن و تست stale، AuthN/AuthZ، مسیر کربن (Verra ARR یا VM0042)، ارتقای لایه داده به PostGIS + Alembic. معیار موفقیت پایان فاز ۲: پایلوت ۳ روستا با NDVI واقعی راستی‌آزمایی‌شده، پذیرش کمپوست/آبخیز، استفاده ≥۵۰٪ خانوارها از USSD.

### 10_quality_standards.md — استانداردهای کیفیت داخلی (STD-001..015) ⭐
سند مرکزی کیفیت مهندسی (تاریخ ارزیابی 2026-08-14). هر استاندارد شامل Requirement / Audit method / Current status است. **ثبت کامل استانداردها:**

| ID | حوزه | خلاصه الزام | وضعیت |
|---|---|---|---|
| STD-001 | ساختار کد و نام‌گذاری | چیدمان ماژولار منسجم، PEP8/TS، بدون scaffolding مرده | Partial |
| STD-002 | مدیریت خطا | اعتبارسنجی ورودی در مرزهای API، پاسخ خطای ساختاریافته، بدون `except` خاموش | Partial |
| STD-003 | لاگ‌نگاری | لاگ ساختاریافته JSON با request ID، بدون سکرت در لاگ | Not implemented |
| STD-004 | تست | Unit+Integration+E2E؛ پوشش هسته ≥۸۰٪؛ سوئیت سبز در CI | Partial |
| STD-005 | امنیت | TLS، CORS allowlist، سکرت در vault، authN/authZ | Partial |
| STD-006 | دسترس‌پذیری | WCAG 2.1 AA: کیبورد، فوکوس، کنتراست ≥4.5:1 | Not implemented |
| STD-007 | i18n/RTL | تمام رشته‌ها محلی‌سازی‌شده؛ RTL صحیح؛ اعداد/تاریخ محلی | Partial |
| STD-008 | مدل داده و مهاجرت | مهاجرت نسخه‌بندی‌شده (Alembic)؛ ممنوعیت `create_all` در تولید | Not implemented |
| STD-009 | مستندسازی | README برای هر ماژول؛ مستندات دوزبانه en/fa | Partial |
| STD-010 | بکاپ و بازیابی | بکاپ خودکار، RPO/RTO تعریف‌شده، دریل سالانه، قانون 3-2-1 | Not implemented |
| STD-011 | نسخه‌بندی | SemVer برای پکیج‌ها و API؛ CHANGELOG؛ git tag | Partial |
| STD-012 | CI/CD | خط لوله lint→test→build→deploy با گیت‌های انتشار | Not implemented |
| STD-013 | بازبینی کد | بازبینی هر تغییر؛ قانون دو بازبین برای هسته عددی | Not implemented |
| STD-014 | معادلات | ارجاع علمی + تست عددی با تلورانس برای هر فرمول | Partial |
| STD-015 | API (OpenAPI) | اسکیمای OpenAPI کامل؛ سازگاری افزودنی‌محور؛ سیاست deprecation | Partial |

**جمع‌بندی انطباق:** هیچ استانداری کاملاً «Implemented» نیست؛ ۹ مورد Partial (001, 002, 004, 005, 007, 009, 011, 014, 015)؛ ۶ مورد Not implemented (003, 006, 008, 010, 012, 013). اولویت اصلاح: STD-008 و STD-012 (مسدودشده توسط نبود Git و وابستگی‌های پین‌نشده) ← STD-005 (بلوکر پیش-پایلوت) ← STD-004 ← STD-003/010/013 ← STD-006.

### 11_weaknesses_and_fixes.md — نقاط ضعف و راه‌حل‌ها (W-001..021 + W-022) ⭐
ثبت جزئی نقاط ضعف با شواهد فایل‌به‌فایل و وضعیت (Fixed / In progress / Planned):

- **W-001** — داده ماهواره‌ای: `EarthSearchProvider.fetch_tile()` باندهای **سنتتیک** با `np.random.uniform` برمی‌گرداند؛ راه‌حل: دانلود GeoTIFF واقعی از STAC + cloud masking + فیلد provenance + پرچم hard «simulated». وضعیت: **In progress** (در Phase 4 مشتری واقعی CDSE ساخته شد؛ فقط نیاز به اعتبارنامه `.env`).
- **W-002** — باگ API: `verify_carbon_project` از `datetime.utcnow()` بدون import استفاده می‌کند (NameError قطعی در `POST /api/v1/carbon/projects/{id}/verify`)؛ راه‌حل: افزودن import + تست یکپارچگی. وضعیت: In progress.
- **W-003** — CORS: wildcard + credentials (ترکیب نامعتبر)؛ راه‌حل: allowlist صریح + تست رگرسیون. وضعیت: در انتهای جدول **Fixed در 2026-08-16** (allowlist در main.py)؛ اما در جدول اصلی همچنان Planned ثبت شده (تناقض داخلی).
- **W-004** — سرویس‌های placeholder: auth/ledger/notification/reporting/workflow فقط چاپ رشته؛ راه‌حل: پیاده‌سازی بر اساس فازها (auth اولویت دارد).
- **W-005** — وابستگی‌ها: `requirements.txt` بدون پین؛ `pyproject.toml` با `dependencies=[]`؛ راه‌حل: پین + لایه‌بندی + lockfile + ممیزی.
- **W-006** — مستندات: بخش فارسی README ریشه **mojibake** (UTF-8 خراب)؛ راه‌حل: بازنویسی + تست CI.
- **W-007** — سکرت‌ها: `POSTGRES_PASSWORD: ***` در docker-compose و `change_me` در .env.example؛ راه‌حل: vault + گردش rotation.
- **W-008** — i18n RAG: دانش‌نامه فقط انگلیسی (`stop_words="english"`)؛ راه‌حل: کرپوس فارسی/عربی با vectorizer هر زبان + مسیریابی Accept-Language.
- **W-009** — i18n RTL: `layout.tsx` هاردکد `lang="en" dir="ltr"`؛ RTL فقط بعد از hydration؛ راه‌حل: رندر سمت سرور lang/dir. وضعیت: In progress.
- **W-010** — کانفیگ فرانت: URL هاردکد `127.0.0.1:8000` در ۹ فایل کامپوننت؛ راه‌حل: base URL پیکربندی‌پذیر متمرکز.
- **W-011** — کنترل نسخه: **هیچ ریپازیتوری Git وجود ندارد**؛ راه‌حل: `git init` + CI در اولین commit.
- **W-012** — تأیید کربن: `/verify` دموست نه فرایند واقعی (بدون زنجیره شواهد)؛ راه‌حل: انتخاب متدولوژی واقعی (Verra ARR/VM0042) + baseline/additionality/leakage/permanence.
- **W-013** — مدل‌های عددی ساده‌شده بدون محدودیت‌نامه کامل (AquaCrop ساده، روش Rational، نرخ‌های منطقه‌ای کربن)؛ راه‌حل: یادداشت محدودیت درون‌کد + ثبت تقریب‌ها. وضعیت: In progress (پوشش prose در docs/02 و docs/05).
- **W-014** — لایه داده: SQLite بدون مهاجرت، `create_all` در استارت‌آپ، `sqlite:///./hydroma_research.db` هاردکد؛ راه‌حل: Alembic baseline.
- **W-015** — یکپارچگی داده: **هیچ audit trail برای تغییرات داده** (رجیستری‌ها in-memory)؛ راه‌حل: فیلدهای audit + جدول change-log.
- **W-016** — امنیت: **بدون احراز هویت/مجوز**؛ همه اندپوینت‌های write باز؛ راه‌حل: سرویس OIDC با نقش‌ها.
- **W-017** — امنیت: **بدون TLS**؛ فرانت با CVE (Next.js 15.1.6)؛ راه‌حل: TLS/HSTS + ارتقای Next.js (به سند CVE مراجعه کنید).
- **W-018** — تست: سوئیت قرمز است (127 passed / 1 failed؛ `test_health_reports_mobile_features`)؛ راه‌حل: اصلاح health payload. وضعیت: In progress.
- **W-019** — ماندگاری: وضعیت in-memory (پروژه‌های کربن، مارکت‌پلیس، sync log) با restart از بین می‌رود؛ راه‌حل: persistence به SQLite سپس PostGIS.
- **W-020** — وابستگی‌ها: انحراف `requirements.txt` از محیط واقعی (.venv) و `pyproject.toml` خالی؛ راه‌حل: لایه‌بندی پین‌شده + lockfile طلایی.
- **W-021** — دسترس‌پذیری: صفر `aria-*`/`role` در ۱۶ کامپوننت؛ `userScalable:false` (نقض WCAG 1.4.4)؛ inputهای بدون label؛ راه‌حل: ممیزی axe.
- **W-022** (افزوده‌شده، خارج از بازه 01-21) — بدهی تایپ فرانت: خطاهای TypeScript موجود، بیلد با `typescript.ignoreBuildErrors:true`؛ راه‌حل: پاکسازی تایپ در بازسازی Phase 3 فرانت.

**جمع‌بندی:** ۱ مورد Fixed (W-003)، ۳ مورد In progress (W-002, W-009, W-018 + W-013 و W-001 تا حدی)، ۱۹ مورد Planned. قانون به‌روزرسانی: هر ادعای «Fixed» باید از کد بازتأیید شود و تاریخ/کامیت ثبت شود.

### 12_30_year_strategy.md — استراتژی ۳۰ ساله تا ۲۰۵۵ ⭐
افق 2026 تا 2055؛ هدف «تداوم به‌عنوان پیش‌فرض» با حداقل وابستگی‌ها، رابط‌های پایدار، داده باز و تصمیم‌های مستند. **اصول پنج‌گانه:** (۱) وابستگی‌های حداقلی و پایدار با مرور سالانه (فقط ۱۴ پکیج runtime در کل ۳۰ سال پیش‌بینی شده)، (۲) رابط API پایدار (فریز `/api/v1/` تا پایان عمر v1)، (۳) فرمت‌های داده باز (PostGIS/GeoPackage، netCDF/CF، JSON/CSV)، (۴) قابلیت مهاجرت هر کامپوننت بدون بازنویسی کل، (۵) تداوم بر نوآوری. **برنامه ارتقا:** پنجره ارتقای سه‌ماهه (Q1 زبان‌ها، Q2 فریم‌ورک‌ها، Q3 دیتابیس، Q4 مابقی)؛ سیاست Python سه‌نسخه، Node فقط LTS، Postgres حداکثر یک major عقب. **سازگاری:** SemVer برای سه مؤلفه (که فعلاً ناهماهنگ‌اند: 0.1.0 در pyproject/package.json در برابر 1.2.0 در gateway)؛ سیاست deprecation دوسره؛ feature flag به‌عنوان کانفیگ؛ v1 و v2 به مدت ≥۲ سال هم‌زمان. **بکاپ:** RPO ≤۲۴h، RTO ≤۴۸h، قانون 3-2-1، دریل بازیابی سالانه به‌عنوان release gate («یک سال بدون دریل موفق = بدون بکاپ»). **گزارش‌دهی:** سند وضعیت سالانه `docs/status/YYYY.md` (جدول STD-001..015، ثبات ضعف‌ها، دفترچه وابستگی، نتیجه دریل، یادداشت علمی)؛ ثبت ADR برای هر تصمیم مهم (ADR-0001 = پذیرش این استراتژی)؛ runbook حوادث با تمرین سالانه. **سناریوی 2055 مشخص:** `/api/v1/` هنوز زنده، v3 از 2041، ۴۰۰+ ADR، ۲۹ سال OpenAPI diff در CI، ۲۸ دریل بازیابی موفق، و جدول 2026-era `SEQUESTRATION_RATES` به‌عنوان مصنوع تاریخی با برچسب «legacy estimate, not for issuance» حفظ شده. **ماتریس ریسک بلندمدت:** تغییر روش‌شناسی‌های کربن (Certain/High)، بازنشستگی ماهواره Sentinel-2 (Certain/Medium)، خروج افراد کلیدی (High/Medium)، تغییرات نظارتی (High/High). **اقدامات سال اول (2026-2027):** git init + CI، پین و لایه‌بندی وابستگی‌ها، Alembic baseline + persistence، CORS/سکرت/auth، جایگزینی باندهای شبیه‌سازی‌شده، رفع W-018/W-002، انتشار ADR-0001 و سند وضعیت 2027.

### 13_operations.md — عملیات، بکاپ، ابزار (Phase 0)
سند اجرایی (2026-08-16) که بسیاری از نقاط ضعف قبلی را می‌بندد: اسکریپت `scripts/backup.py` (کپی SQLite با API بکاپ آنلاین + `.env` + requirements + alembic + git bundle؛ `--retain 10`)؛ دستورالعمل بازیابی/رول‌بک گام‌به‌گام؛ مهاجرت به **uv** (`uv pip compile` → `requirements.lock.txt` که هرگز دستی ویرایش نمی‌شود)؛ **بازسازی Alembic baseline** با migration `ed7a1747d8db` (۱۲ جدول unified schema؛ `env.py` آدرس واقعی DB را از settings می‌خواند)؛ اسکلت Supabase (`supabase/migrations/00001_auth_roles_rls.sql` با helperهای `current_role()`/`is_admin()` و RLS روی `farms` + باکت media)؛ و **ارتقای فرانت به Next.js 16.3.1** (Turbopack، CVE-2025-66478 رفع‌شده — یعنی ارتقای امنیتی اتفاق افتاده است). یادداشت: Tailwind از بیلد جدا شده (فقط ۴ کلاس سفارشی)؛ بدهی تایپ TypeScript به W-022 ارجاع و با `ignoreBuildErrors` گیت‌شده است.

### 14_telegram_bot.md — ربات تلگرام (Phase 1)
ربات پیاده‌سازی‌شده و تست‌شده (۱۳ تست آفلاین). معماری `services/bots/`: یک هسته + آداپتورها؛ i18n با **۱۴ زبان** و تشخیص خودکار (BCP-47، سپس heuristics اسکریپت، پیش‌فرض fa). جریان مشاوره: سؤال کاربر ← RAG با بازیابی top-3 از دانش‌نامه FAO ← مدل محلی **Ollama** پاسخ با استنادهای درون‌خطی `[1],[2]` می‌سازد (فقط از context بازیابی‌شده؛ چیزی اختراع نمی‌شود) ← اگر Ollama آفلاین باشد، شواهد خام انگلیسی با یادداشت صادقانه برمی‌گردد. مدل‌های پیشنهادی: `glm4:9b` (توصیه‌شده)، `qwen2.5:7b`، `dolphin-mistral`. ویزارد ثبت مزرعه (FSM) به اسکیمای unified SQLite ذخیره می‌شود. بدون `BOT_TOKEN` ربات از شروع امتناع می‌کند.

### 15_multiplatform_bots.md — ربات‌های چندپلتفرمی (Phase 2)
معماری «یک هسته، چند آداپتور» برای Telegram/Eitaa/Bale/Rubika. ماتریس صادقانه: **Telegram** (aiogram، تأییدشده)؛ **Eitaa** (API سازگار با Telegram با base `https://eitaayar.ir/api` — همان dispatcher، نیاز به تست زنده getMe)؛ **Bale** (کتابخانه `python-bale-bot` با تعارض aiohttp/`asyncio` سایه روی ویندوز — باید در venv جدا روی لینوکس اجرا شود)؛ **Rubika** (پروتکل اختصاصی غیرسازگار — نیاز به مطالعه یکپارچگی؛ آداپتور با پیام واضح از شروع امتناع می‌کند؛ «هیچ glue تأییدنشده‌ای ارسال نمی‌شود»). موتور هوشمند هشدار `core/alerts.py`: قواعد روی ردیف‌های داده مزرعه (metric، عملگر، آستانه، شدت، برچسب فارسی)؛ **metricهای غایب هرگز هشدار نمی‌سازند**؛ اتصال به داده واقعی ماهواره در Phase 4. تست‌ها: ۱۴ تست آفلاین.

### 16_phase4_copernicus.md — داده واقعی Copernicus ⭐
جایگزینی W-001 با داده واقعی **Copernicus Data Space Ecosystem (CDSE)**. تحویل‌شده: `services/satellite/copernicus.py` (کلاینت OData با OAuth2 client-credentials، کوئری کاتالوگ Sentinel-2 L2A با bbox/date/cloud-cover، توابع خالص `ndvi_from_bands/evi_from_bands/savi_from_bands` + `health_from_ndvi` با برچسب‌های FAO)؛ **قرارداد صداقت:** بدون اعتبارنامه هر متد شبکه `CopernicusNotConfigured` پرتاب می‌کند و روتر با پرچم صریح `data_source="copernicus"|"simulated"` fallback می‌شود — «هیچ داده جعلی خاموشی هرگز به‌عنوان واقعی ارائه نمی‌شود». روتر `/api/v1/satellite/analyze` اکنون `data_source` و `farm_id` برمی‌گرداند و ردیف‌ها در جدول واقعی `satellite_analyses` ذخیره می‌شوند؛ `history/{farm_id}` و `health` هم اضافه شده‌اند. **Cloud masking (SCL):** باند SCL با پنجره ۵×۵، `scl_clear_ratio`، وضعیت `cloudy` وقتی نسبت <0.5 — قرائت ابری هرگز به‌عنوان شاخص واقعی ارائه نمی‌شود. **NASA POWER + Open-Meteo ERA5** بدون اعتبارنامه (واقعی). **Sample_bands با rasterio** (B04/B08/B02) کد و تست شده؛ فعال‌سازی زنده فقط منتظر `CDSE_CLIENT_ID/SECRET` در `.env` است. DVC pipeline (`dvc.yaml`: stac_fetch→band_sample→load_db)، DuckDB analytics (`/api/v1/satellite/stats/{farm_id}`)، قواعد هشدار NDVI که **فقط روی `data_source=="copernicus"`** فعال می‌شوند، و `alert_runner` به‌عنوان task پس‌زمینه (interval پیش‌فرض ۹۰۰ ثانیه). تست‌ها: ۱۷+۷+۴ تست؛ کل سوئیت بک‌اند ۲۵۳ پاس.

### 17_admin_panel.md — پنل مدیریت (Phase 5) ⭐
پنل کامل با معیار پذیرش «یک اپراتور غیرفنی می‌تواند کاربر را بلاک کند، مدل را متوقف کند و خطا را ببیند». بک‌اند: `routers/admin.py` با RBAC (`require_roles("admin")`، 403 برای غیرادمین) — اندپوینت‌های health/users/block/unblock/audit. **باگ حیاتی JWT رفع شد:** توکن‌ها `sub = user.email` داشتند در حالی که `get_current_user` از `int(sub)` استفاده می‌کرد (یعنی همه اندپوینت‌های احرازشده برای همه کاربران بی‌صدا شکست می‌خوردند و نقش admin هرگز به توکن نمی‌رسید)؛ فیکس: `sub = str(user.id)` و `role = user.role`. ماژول‌های تحویل‌شده: **Content** (CRUD + publish + soft-archive با ممیزی، جدول `content_items`)، **Bots** (وضعیت واقعی: configured از env، enabled از settings — «هیچ وضعیت جعلی»)، **Errors** (exception handler سراسری که 500ها را در `error_logs` ذخیره می‌کند + ack)، **Settings** (key/value با whitelist کلیدهای شناخته‌شده)، **Models** (وضعیت زنده Ollama از `/api/tags` و `/api/ps`، توقف مدل با `keep_alive=0`، هرگز fabrication)، **Overview** (متریک‌های صادقانه: uptime، شمارنده‌ها، آخرین ۸ اقدام ممیزی، ۵ خطای آخر)، **Security** (لاگ تلاش‌های ورود در audit_logs، ۵۰ رویداد آخر). **Hygiene:** ۱۰ صفحه placeholder تولیدشده با AdminPlaceholder صادقانه جایگزین شدند؛ AdminNav به ۹ صفحه واقعی لینک می‌دهد. Bootstrap CLI: `python scripts/bootstrap_admin.py you@example.com --create --password ***`. مهاجرت‌ها: `c3d8e0f2a1b4` (audit_logs)، `d4e9f0a3b2c5` (settings/error_logs/content_items).

### 18_phase6_content_production.md — تولید محتوا (Phase 6) ⭐
هدف «یک انتشار، سه کانال» (سایت + RAG + پیام‌رسان‌ها). مدل داده (migration `e5f1a2b3c4d5`): `content_versions` (اسنپ‌شات هر به‌روزرسانی)، `content_translations` (عنوان/بدن per-language با منبع ai|manual)، ستون‌های `generated_by_ai/rag_synced/published_at`. بک‌اند: ترجمه AI با Ollama برای ۱۴ زبان (503 صادقانه وقتی آفلاین — بدون ترجمه جعلی)، `sync_content_to_rag` (شاخص کلمات کلیدی صادقانه تا Phase 9)، جستجوی عمومی `/api/v1/content/search`. فرانت: ویرایشگر Markdown با پیش‌نمایش زنده (رندر امن، HTML-escaped)، دراور per-item با انتخابگر ۱۴ زبانه، نسخه‌ها، بج‌های AI/RAG. **مکمل‌های جلسه:** تولید پیش‌نویس AI (`generate-draft` با `generated_by_ai=True`)، dispatch به تلگرام با گیت سه‌شرطی (setting + BOT_TOKEN + channel — اگر هر جزء نبود `dispatched=0` با دلیل صریح)، انتشار زمان‌بندی‌شده (`scheduled_at`، migration `f6a2b3c4d5e6`، `run_due_publishes` در حلقه دوره‌ای). ۳۰۷ تست بک‌اند سبز. باقی‌مانده: رسانه (Supabase Storage — مسدود به اعتبارنامه).

### 19_phase7_models.md — هسته مدل‌های علمی (Phase 7) ⭐
۲۲ مدل واقعی قابل‌فراخوانی از API با **بج وفاداری** (official ۹ / simplified ۱۱ / experimental ۲) — بدون stub. پوشش: ET0 Hargreaves، رواناب، طراحی check-dam/ترانشه/نیم‌ماه، عملکرد محصول + مقایسه (AquaCrop-style)، پروژکتورهای اقلیمی، زیست‌توده IPCC، **RothC پنج‌حوضچه‌ای**، **فتوسنتز Farquhar**، بازده کوانتومی (experimental)، ترسیب کربن پروژه (هم‌راستا با VM0042)، شاخص سلامت خاک، pedotransfer (Saxton & Rawls)، کلاس شوری + نیاز آبشویی (FAO)، **van Genuchten**، AWC بر اساس بافت، **RUSLE**. `run_model(slug, params)` با اعتبارسنجی تایپ/الزامی، خروجی `{slug, fidelity, result, executed_ms}`، خطاهای صریح (ValueError→400). API عمومی `/api/v1/models*` (علم باز است) + کاتالوگ فرانت با ۲۲ کارت، فرم پارامتر با پیش‌فرض، بج C++20. **Model cards:** هر ۲۲ مدل دارای دامنه اعتبار و محدودیت صادقانه (مثلاً ET0 «روزانه، نیمه‌خشک؛ خطای بزرگ در شرایط بادی/مرطوب»). **PINN surrogate** (PyTorch 2.13.0 نصب و فعال؛ MLP + حلقه fit؛ تست همگرایی روی sin(x)) برای پاسخ‌های میلی‌ثانیه‌ای در مسیر bot/USSD. **C++20 parity:** `c_api.cpp` با MSVC 2019 /O2 به `hydroma_core.dll` کامپایل شده؛ `cpp_bridge.py` با ctypes؛ پارتی عددی rel 1e-9 برای `et0_hargreaves` و `van_genuchten_theta` (۵ تست؛ skip بدون DLL). **ERA5 real-data pipeline** (`era5_fetch.py` با h5netcdf، متغیرهای t2m/tp، 401 صادقانه برای عدم مجوز، حالت Bearer جدید + `CDS_AUTH=basic` قدیمی). فیکس‌های استارت: `import os` گم‌شده، `load_dotenv()` در زمان import، `prefers-reduced-motion`. ۳۳۰ تست بک‌اند.

### 20_phase8_token_carbon.md — اقتصاد توکن و کربن (Phase 8) ⭐
هدف: لایه اقتصادی قانونی و معتبر — ثبت پروژه کربن ← تأیید (متدولوژی هم‌راستا با VM0042) ← صدور اعتبار ← نمایش در کیف پول. تحویل‌شده: `services/carbon/verification.py` با **چک‌های صادقانه** baseline/additionality/leakage/permanence (پروژه فقط وقتی پاس می‌شود که همه چک‌ها پاس باشند؛ شکست‌ها verbatim برمی‌گردند — «هرگز rubber-stamp نمی‌کند»)؛ `POST /carbon/projects/{id}/verify`؛ `POST /carbon/projects/{id}/issue` فقط برای پروژه‌های VERIFIED با اعتبار به **ECO wallet ماندگار** (نرخ: `carbon_credit = 100 ECO/unit`)؛ `GET /carbon/wallet` با پشتوانه DB (بقای ری‌استارت)؛ مهاجرت `f7a3b4c5d6e7` (ستون‌های verification_status/verification_detail/issued_at)؛ مالکیت اجباری (403) و 404. **قدم‌های بعدی (باقی‌مانده Phase 8):** موتور توزیع **EcoCoin با نسبت 70/15/10/5** + UI کیف پول (فرانت + بات)؛ مارکت‌پلیس (سفارش + ردیابی)؛ هوک‌های دفترکل بلاک‌چین (گیت‌های صادقانه؛ مشاوره حقوقی قبل از هر راه‌اندازی)؛ مهاجرت VerificationOracle از econojin.com. ۳۶۰ تست بک‌اند سبز.

> **توجه تحلیلی:** سند 20 صرفاً «70/15/10/5» را به‌عنوان توزیع آینده EcoCoin ذکر می‌کند بدون تفکیک. وایت‌پیپر (فایل ریشه) توزیع متفاوت **40/25/15/10/10** را می‌دهد. این دو عدد با هم سازگار نیستند — رجوع به «شکاف‌های مستندسازی».

### 21_frontend_component_spec.md — اسپک کامپوننت‌های فرانت (Phase 9) ⭐
نقشه راه UI با ۲۶ دسته کامپوننت (Foundation/Typography/Buttons/Inputs/Forms/Selection/Data Display/Cards/Feedback/Modal/Navigation/Loading/Charts/GIS/Simulation/Hydrology/Agriculture/Monitoring/Dashboard/File/Auth/Reports/Animation/Icon/Accessibility/Responsive). استک: radix-ui primitives، recharts، leaflet/react-leaflet، framer-motion، sonner، lucide-react، react-hook-form + zod، tanstack/react-query. قوانین: `components/ui/*` = ابتدایی‌های قابل‌استفاده مجدد؛ `components/charts|gis|simulation|...` = حوزه‌ای؛ Server Components با حداقل `"use client"`؛ **قانون zero orphan** — هر فایل باید از entry (main.tsx→App.tsx) قابل ردیابی باشد. یادداشت: فایل 21 (برخلاف بقیه) عمدتاً فارسی/چندزبانه است و از نظر فنی وضعیت‌ها را با نمادهای ؟/؟؟/؟؟؟ نشان می‌دهد (پیاده‌سازی‌شده/در حال انجام/برنامه‌ریزی‌شده). تحویل‌های انجام‌شده تا 22_implementation_report: DataTable (sort/filter/pagination/export CSV)، Sheet/Drawer، CommandPalette، SkeletonTable/LoadingOverlay، FormField/FormWizard، نمودارهای علمی (WaterBalance، FlowDurationCurve، SoilMoisture، ET0، VegetationIndex)، تست‌های vitest و چک‌های a11y.

### 22_implementation_report.md — گزارش پیاده‌سازی و ممیزی فاز (اضافه بر بازه 00-21)
گزارش 2026-08-17 روی branch `feature/phase-b-alembic` (کامیت f7ef644). تأیید تحلیل‌های analyzer: 3 مورد «hardcoded secrets» نادرست بودند (false positive)، 34 «API key» عمدتاً false positive (مثلاً `password: 'Min 6 chars'` در zod)؛ CORS با `CORS_ORIGINS` از env درست شد؛ 3 خطای تست رفع شد؛ 52 دارایی unoptimized در public (PNG/SVG/woff2) بهینه شد؛ alt-text اضافه شد؛ `node_modules`/`.next` خارج از git ماندند. تحویل‌های این فاز: **JWT Refresh Token** (`POST /api/v1/auth/refresh` با `type=refresh`، بازگرداندن 401 برای توکن access)، **ESLint** (ESLint 9 + eslint-config-next؛ `pnpm lint` با 0 error / 279 warning legacy)، **i18n اصلاح‌شده** (SiteNav/SiteFooter با `useI18n()`، `dir` در context، رجیستری `locales/registry.en.json`)، **RTL** (`dir="ltr"` + بارگذاری Vazirmatn + fix recharts)، **UI kit** (sheet، data-table، command، form، skeleton-table، loading-overlay + تست‌های vitest)، `.env.example` کامل. فازها: 0-8 تکمیل‌شده، فاز 9 (ساینس/فرانت) در حال انجام (science router با citations + datasets، صفحه `/science`، i18n، ESLint، refresh token؛ باقی: DataTable با داده واقعی، تست‌های vitest بیشتر).

### 22_research_ag_science.md — تحقیق علوم کشاورزی (Master Research)
سند دانش/معماری 2026-08-17؛ **نسخه کامل فارسی، معتبر (authoritative) است** (`docs/fa/22_research_ag_science.md`؛ گزارش‌های خام در `docs/fa/22_research_reports/`). بخش‌ها: (۱) شبیه‌سازهای محصول و هیدرولوژی — DSSAT/CERES، APSIM، AquaCrop (فرمول B = WP×ΣTr؛ Y = B×HI)، SWAT، HEC-HMS، MIKE SHE؛ معادلات کلیدی FAO-56 PM، Hargreaves-Samani، Richards، SCS-CN، Saint-Venant، RUSLE؛ روش‌های عددی (FD/FV، RK4، Newton-Raphson، CFL)؛ کالیبراسیون (NSE، RMSE، KGE، PBIAS؛ GLUE/PEST؛ Morris/Sobol؛ EnKF). (۲) کودهای زیستی و اصلاح‌کننده‌های خاک — Rhizobium/Azotobacter/PGPR/AMF، شیمی NPK، بازدارنده‌های نیتریفیکاسیون، بیوچار (پیرولیز 350-700°C)، نسبت C/N ایده‌آل 25-30:1، فرمول N rate = (نیاز − عرضه)/NUE، 4R stewardship؛ بازار جهانی کود زیستی ~2.7-3.3 میلیارد دلار 2025 (پیش‌بینی 11.08B تا 2035). (۳) مهندسی آبخیز و محصولات مقاوم — check dam/تراس/ترانشه/نیم‌ماه/گابیون، روش Rational و SCS-CN، هالوفیت‌ها (کینوا)، برنج SUB1، CRISPR/Cas9 در نخود، orphan crops. (۴) پایش — NDVI/EVI/SAVI/NDWI/NBR، Sentinel-1 SAR، SPI/SPEI/VCI/VHI، IoT (TDR/FDR، MQTT/LoRaWAN)، UAV، نقشه‌برداری دیجیتال خاک. (۵) نقشه راه پیاده‌سازی HyDroMa (HP-WH-01..05، HP-BT-01، HP-VG-01/02).

### 23_research_frontend_assets.md — تحقیق دارایی‌های طراحی و داده
پژوهش چهار منبع برای فرانت: **Dribbble** (الهام داشبورد؛ 177K+ طرح dashboard؛ فقط الهام، بدون دانلود)، **NASA GISS** (داده رایگان GISTEMP v4 از 1880 تاکنون — مکمل CMIP6/Copernicus برای داشبورد اقلیمی)، **Vercel** (استقرار serverless برای Next.js؛ Preview Deployments؛ قالب شادکن/UI admin — هم‌راستا با Radix kit پروژه)، **LottieFiles** (۱.۳M+ انیمیشن؛ Lottie JSON سبک برای پهنای‌باند کم و آفلاین-اول؛ ایموجی‌های متحرک برای RAG assistant). توصیه‌ها: داشبورد از Dribbble + قالب Vercel؛ انیمیشن Lottie + react-lottie-player با احترام به `prefers-reduced-motion`؛ استقرار پیش‌نمایش Vercel و تولید Docker/Nginx (تصمیم نهایی با مالک پروژه).

### 99_conversation_summary.md — خلاصه توافق‌ها ⭐
سند «حافظه توافقی» پروژه. اسامی: موتور **HyDroMa**، پلتفرم **Eco Nojin**. توافق‌های هسته: پلتفرم ماژولار استاندارد-محور بین‌المللی؛ پایتون برای ارکستراسیون/AI/داده/API؛ C++ برای هسته محاسباتی؛ TypeScript برای فرانت؛ شروع با مستندات و پیشروی ماژول‌به‌ماژول؛ کد و کامنت‌ها انگلیسی؛ **مستندات دوزبانه انگلیسی/فارسی**؛ i18n از قدم اول. محدوده عملکردی: کشاورزی/مرتع/دام/معیشت روستایی، هیدرولوژی/آب زیرزمینی/سیلاب/آبخیز، خاک/فرسایش/کود زیستی/کمپوست/بیوچار، اقلیم/خشکسالی/پوشش گیاهی، رشد محصول/آبیاری/سناریو، مدیریت ریسک/بحران، احیای اکوسیستم/جنگل‌کاری/کنترل بیابان‌زایی، ترسیب کربن/MRV/پاداش/مشوق توکنی، مالی/انبار/مارکت‌پلیس/اکوتوریسم، دستیار دانش/جستجو/ML/مشاوره AI. استانداردهای بین‌المللی: FAO، IFAD، World Bank، WMO، ISO، OGC، UN SDGs، GODAN و چارچوب‌های کربن. **قانون حافظه:** توسعه آینده باید با این سند هم‌راستا بماند؛ هر تغییر بزرگ باید به‌عنوان تصمیم جدید ثبت شود.

---

## بخش ۲: `D:\eco_nojin\docs\fa\` — فهرست و تفاوت با en

**فایل‌های موجود (۱۶ فایل + ۴ گزارش):**

| فایل | حجم |
|---|---|
| `docs\fa\00_master_plan.md` | 3.5 KB |
| `docs\fa\01_architecture.md` | 3.5 KB |
| `docs\fa\02_hydroma_engine.md` | 6.7 KB |
| `docs\fa\03_eco_nojin_platform.md` | 4.8 KB |
| `docs\fa\04_data_model.md` | 4.3 KB |
| `docs\fa\05_standards.md` | 3.5 KB |
| `docs\fa\06_security_privacy.md` | 4.5 KB |
| `docs\fa\07_i18n_localization.md` | 2.7 KB |
| `docs\fa\08_deployment_operations.md` | 3.7 KB |
| `docs\fa\09_roadmap.md` | 5.5 KB |
| `docs\fa\10_quality_standards.md` | 28.3 KB |
| `docs\fa\11_weaknesses_and_fixes.md` | 17.9 KB |
| `docs\fa\12_30_year_strategy.md` | 19.4 KB |
| `docs\fa\22_research_ag_science.md` | 17.1 KB |
| `docs\fa\23_research_frontend_assets.md` | 7.8 KB |
| `docs\fa\99_conversation_summary.md` | 2.7 KB |
| `docs\fa\22_research_reports\research-a-simulators.md` | 49.1 KB |
| `docs\fa\22_research_reports\research-b-fertilizers.md` | 57.0 KB |
| `docs\fa\22_research_reports\research-c-watershed-crops.md` | 44.3 KB |
| `docs\fa\22_research_reports\research-d-hydroma-steps.md` | 38.0 KB |

**تفاوت‌ها با `docs/en/`:**

1. **۱۰ فایل en بدون نسخه فارسی:** `13_operations.md`، `14_telegram_bot.md`، `15_multiplatform_bots.md`، `16_phase4_copernicus.md`، `17_admin_panel.md`، `18_phase6_content_production.md`، `19_phase7_models.md`، `20_phase8_token_carbon.md`، `21_frontend_component_spec.md`، `22_implementation_report.md` — یعنی کل بازه فازهای اجرایی جدید (Phase 0 و 4 تا 8) و گزارش پیاده‌سازی فقط انگلیسی‌اند؛ این با تعهد «مستندات دوزبانه» در `99_conversation_summary.md` و STD-009 در تناقض است.
2. **نسخه‌های فارسی 10/11/12 حجیم‌تر از انگلیسی هستند** (مثلاً fa/12 با 19.4KB در برابر en/12 با 13.1KB؛ fa/10 با 28.3KB در برابر 20.1KB) — ترجمه گسترش‌یافته/تفسیری‌اند، نه یک‌به‌یک.
3. **فقط fa دارای `22_research_reports/` است** (۴ گزارش خام تحقیقاتی فارسی) — این فایل‌ها در en وجود ندارند.
4. **`docs/fa/22_research_ag_science.md` نسخه معتبر (authoritative) است** و نسخه en (4.8KB) چکیده آن است — برخلاف الگوی معمول که en مرجع است.
5. محتوای فارسی در ترمینال ویندوز با codepage پیش‌فرض به‌صورت mojibake نمایش داده شد (مشکل نمایش PowerShell، نه الزاماً فایل) — اما همین موضوع خطر W-006 (فاسدشدن UTF-8) را یادآوری می‌کند.

---

## بخش ۳: `D:\eco_nojin\docs\security\CVE-2025-66478.md` — جزئیات و وضعیت فیکس

- **آسیب‌پذیری:** CVE-2025-66478 در **Next.js**؛ شدت **Medium**؛ کامپوننت آسیب‌پذیر: **Middleware و Server Actions**؛ نسخه‌های اصلاح‌شده: **16.3.1+** و پچ‌های آینده 15.x.
- **وضعیت هنگام نوشتن سند:** نسخه در حال استفاده 15.1.6 (downgrade عمدی از 16.3.0 به دلیل فساد پایدار Turbopack cache در ویندوز). ارزیابی ریسک: در محیط توسعه (localhost، بدون endpoint در معرض، بدون auth middleware) = **Negligible**؛ در پیش‌تولید/تولید = **Moderate** با اقدام الزامی قبل از دیپلوی: ارتقا به 16.3.1+ (با Webpack یا غیرفعال‌کردن صریح Turbopack در صورت ناپایداری)، تست کامل سوئیت.
- **مسیر مهاجرت:** Option A: `pnpm add next@16.3.1`؛ Option B: انتظار برای 15.x پچ‌شده. پایش: خبرنامه امنیتی Next.js، `pnpm audit` قبل از هر دیپلوی.
- **وضعیت فعلی (تطبیق با اسناد جدیدتر):** سند CVE منسوخ شده است — `docs/13_operations.md` (2026-08-16) و `docs/22_implementation_report.md` (2026-08-17) و ساختار `frontend/` (نسخه `next@16.3.1` در node_modules) نشان می‌دهند ارتقا به **Next.js 16.3.1 (Turbopack) انجام شده** و CVE رفع شده است. باقی‌مانده: بدهی TypeScript (W-022) که با `ignoreBuildErrors` گیت شده و باید در بازسازی Phase 3 فرانت پاک شود؛ ورودی W-017 در سند 11 نیز هنوز وضعیت «Planned» را نشان می‌دهد (به‌روزرسانی نشده).

---

## بخش ۴: فایل‌های ریشه‌ای — خلاصه با اعداد کلیدی

### `D:\eco_nojin\ECONOMIC_MODEL.md` — مدل اقتصادی (v1.0، آگوست 2026)
موقعیت‌یابی: **پلتفرم تسهیل سرمایه‌گذاری، نه دریافت‌کننده سرمایه** — سرمایه‌گذاران پروژه‌های کشاورزی واقعی متعلق به کشاورزان را تأمین مالی می‌کنند و پلتفرم کمیسیون می‌گیرد. **۶ جریان درآمد:** (۱) کمیسیون تسهیل ۱۰٪ مبلغ سرمایه‌گذاری، (۲) کمیسیون مدیریت ۵٪ سود پروژه، (۳) کمیسیون مارکت‌پلیس 2-5٪، (۴) اشتراک حرفه‌ای $10/ماه، (۵) لایسنس API سازمانی $500-2,000/ماه، (۶) فروش داده ناشناس $10K-50K در هر دیتاست. اعداد کلیدی: ROI انتظاری سرمایه‌گذار 15-40٪ سالانه؛ افزایش درآمد کشاورز 50-100٪؛ پوشش ریسک 70-90٪ با بیمه+وثیقه؛ **سر به سر در ماه 8-10** (۲۶۷ پروژه/ماه یا $267K سرمایه در ماه با هزینه ثابت $40K/ماه). مثال توزیع سود: سرمایه‌گذار 60٪، کشاورز 40٪، پلتفرم 5٪ سود. سناریوهای رشد: محافظه‌کارانه سال 5 = $1.2M درآمد پلتفرم؛ پایه = $3M؛ خوش‌بینانه = $7.5M. **پروژکشن ۵ ساله (جدول پایه):** سرمایه تسهیل‌شده $1M→$30M؛ درآمد $150K→$4.5M؛ سود خالص -$330K→+$3M؛ 15,000 کشاورز؛ 80,000 تن CO2. LTV/CAC = 153.75x (LTV $1,230 در برابر CAC $8). اثر اجتماعی سال 5: 25,000 کشاورز، مشارکت 40٪ زنان، 100,000 تن CO2، 5,000 هکتار، $50M سرمایه‌ mobilized. **تناقض داخلی:** خلاصه اجرایی «هدف درآمد ۵ ساله $7.5M سالانه» را می‌گوید اما جدول پروژکشن سال 5 را $4.5M نشان می‌دهد ($7.5M فقط در سناریوی خوش‌بینانه است).

### `D:\eco_nojin\ECO_COIN_WHITEPAPER.md` — وایت‌پیپر Eco Coin (v1.0، Draft، ممنوع از توزیع تا بازبینی حقوقی)
ECO به‌عنوان **توکن utility** (نه security — عدم عبور از Howey Test)، نه ابزار سرمایه‌گذاری، نه ICO/IEO/IDO، نه ارز. **توکنومیکس:** عرضه کل **۱۰۰,۰۰۰,۰۰۰ ECO ثابت**؛ تقسیم‌پذیری 0.001 ECO (1 گرم CO2)؛ پشتوانه **1 ECO = 1 تن CO2 تأییدشده**؛ بلاک‌چین Polygon (پیشنهادی، ERC-20) یا L2 سفارشی یا بدون بلاک‌چین در ابتدا. **توزیع وایت‌پیپر (40/25/15/10/10):** پاداش کربن ۴۰٪ (40M)، خدمات پلتفرم ۲۵٪ (25M)، آموزش ۱۵٪ (15M)، صندوق اکوسیستم ۱۰٪ (10M)، تیم و عملیات ۱۰٪ (10M). کسب ECO: کاشت ۱۰۰ درخت = 50 ECO (تأیید ماهواره‌ای)، no-till 1 هکتار = 20، دوره آموزشی = 10، فروش مارکت‌پلیس = 1 ECO به ازای هر $100، معرفی = 5، احیای 1 هکتار = 30. مصرف: 100 ECO = $10 تخفیف نهاده، 30 ECO = 10٪ تخفیف بیمه. خریداران کربن: 1,000 ECO به قیمت $10 = $10,000 با retire دائمی. مکانیسم ارزش: قیمت بازار داوطلبانه $10-50/تن، **کف قیمت پلتفرم $5**، سقف $50+؛ مثال: ۱۰ تن = 10 ECO × $20 = $200، کارمزد ۱۰٪، خالص کشاورز $180. درآمد سال 3: $830K (کارمزد فروش کربن ۱۰٪ = $500K و...). قرارداد هوشمند سادهشده: `mintCarbonReward` (فقط verifier)، `redeemForService`، `retireForOffset` (burn). تحلیل حقوقی Howey: هر ۴ معیار «خیر» (کسب از طریق اقدام، نه خرید؛ فعالیت فردی؛ خدمات نه سود؛ تلاش خود). جدول حوزه‌های قضایی: USA/EU/UK/Iran بدون لایسنس؛ UAE (VARA اگر معامله شود)؛ Singapore (MAS اگر مبادله شود). نقشه راه ۴ فاز: 100 کشاورز پایلوت ← 1,000 ← مهاجرت Polygon و 10,000 ← چندکشوری و رجیستری‌های ملی کربن. **ناسازگاری با سند 20:** توزیع 40/25/15/10/10 وایت‌پیپر در برابر «70/15/10/5» ذکرشده در `20_phase8_token_carbon.md` — نیاز به یکسان‌سازی.

### `D:\eco_nojin\INVESTOR_PITCH.md` — پچ سرمایه‌گذار (آگوست 2026)
Elevator pitch: دموکراتیک‌سازی علوم کشاورزی برای ۲.۵ میلیارد کشاورز خردهمالک با ۵ کانال دسترسی و ۱۴ زبان؛ **درخواست: $500K Seed** (پایلوت 40٪ /$200K، مهندسی 30٪/$150K، مشارکت‌ها 20٪/$100K، مارکتینگ 10٪/$50K). **TAM:** AgTech جهانی **$43B تا 2030** + بازار اعتبار کربن **$50B تا 2030** + خدمات ترویج کشاورزی **$10B+ سالانه**. **SAM:** ۲۵۰ میلیون کشاورز خردهمالک MENA+جنوب آسیا (۱۰۰ میلیون متمرکز بر تاب‌آوری اقلیمی). **SOM:** ابتدا ۱ میلیون (ایران، پاکستان، افغانستان)؛ ۵ ساله ۱۰ میلیون در MENA. مدل درآمد: Freemium (رایگان USSD/SMS/Voice؛ حرفه‌ای $10/ماه؛ سازمانی $500+/ماه) + ۵ جریان (کمیسیون تأیید کربن 5-10٪، کمیسیون مارکت‌پلیس 2-5٪، لایسنس API، قراردادهای دولتی/NGO، دیتا اینسایت). Traction (باید با وضعیت واقعی سنجیده شود): ۱۴ ماژول، ۱۶۹ تست، ۶۰+ اندپوینت، ۸x عملکرد Numba، رجیستری کربن بلاک‌چینی. Milestones: ماه 3 = 1,000 کشاورز فعال؛ ماه 6 = اولین درآمد $10K MRR؛ ماه 12 = 10,000 کشاورز و $100K MRR؛ سال 2 = آماده Series A. چشم‌انداز: ۱۰ میلیون کشاورز، ۱۰۰ میلیون تن CO2، $1B ارزش اعتبار کربن. **هشدار انطباق:** اعداد traction (۱۶۹ تست، «blockchain-verified»، «real-time satellite») با وضعیت صادقانه docs/11 (مثلاً داده ماهواره شبیه‌سازی‌شده تا Phase 4) فاصله دارند.

### `D:\eco_nojin\LEGAL_COMPLIANCE.md` — تحلیل انطباق حقوقی (Draft، نیازمند بازبینی حقوقی)
دو مدل مالی: (۱) **تسهیل سرمایه‌گذاری** — طبقه‌بندی نظارتی per-country: USA (SEC Reg CF یا لایسنس ایالتی)، EU (لایسنس ECSP)، UK (مجوز FCA)، ایران (لایسنس SEO/Fintech)، UAE (DFSA یا SCA). الزامات: KYC/AML، حفاظت سرمایه‌گذار (افشای ریسک، سقف $10K، دوره خنک‌شدن)، شفافیت و گزارش‌دهی، ثبت پلتفرم. **ساختار پیشنهادی SPV:** سرمایه‌گذار ← SPV ← پروژه ← کشاورز (SPV ریسک را ایزوله می‌کند؛ پلتفرم وجوه را نگه نمی‌دارد؛ بار نظارتی کم). (۲) **Eco Coin utility token** — تحلیل Howey با ۴ معیار «NO»؛ جدول بین‌المللی (USA: SEC guidance؛ EU: MiCA اگر معامله شود؛ UK: FCA؛ Canada: CSA 21-329؛ Australia: ASIC؛ Singapore: MAS PSA؛ UAE: VARA؛ ایران: راهنمای بانک مرکزی). **۶ تضمین کلیدی:** بدون ICO/IEO/IDO، بدون وعده سود، utility روشن، بدون بازار ثانویه (ابتدائاً)، شرایط شفاف، اجتناب از واژگان securities. ریسک‌ها: نظارتی (Low/High)، AML/KYC (Medium/High)، حریم داده (Medium/High)، فرامرزی (Medium/High). اقدامات قبل از راه‌اندازی: وکیل securities، مشاوره رگولاتور (no-action letter در صورت امکان)، چارچوب KYC/ToS/Privacy، تضمین‌های فنی (تراکنش‌مانیتورینگ، audit log، رمزنگاری). نکات حوزه‌ای: ایران (کروفاندینگ طبق SEO مجاز؛ کریپتو ماینینگ قانونی/معامله محدود؛ توکن utility در صورت عدم معامله عموماً مجاز)؛ UAE (VARA)؛ EU (ECSP + MiCA)؛ USA (Reg CF/Reg A+).

### `D:\eco_nojin\PRESENTATION.md` — ارائه ۱۲ اسلایدی سرمایه‌گذار
اسلایدها: عنوان ← مشکل (۲.۵B کشاورز؛ ۷۰٪ بدون AgTech؛ ۸۰٪ پلتفرم‌ها اسمارت‌فون می‌خواهند؛ ۹۰٪ پژوهش به کشاورز نمی‌رسد؛ افت ۲۵٪ بهره‌وری تا 2050) ← راه‌حل (HyDroMa + RAG + ماهواره + سناریو + کربن + ۵ کانال) ← ۵ کانال دسترسی ← پایه علمی (Rouse 1974، Cunge 1969، AquaCrop، IPCC AR6، Verra VCS) ← معماری ← مزیت رقابتی ← مدل کسب‌وکار ← **بازار (TAM $43B/$50B/$10B+؛ SAM 250M/100M؛ SOM 1M→10M)** ← ترکشن و milestones ← تیم و درخواست $500K ← چشم‌انداز. اپندیکس: معماری ۱۴ ماژول، استک تکنولوژی (Next.js 15.1.6 — قدیمی‌تر از وضعیت فعلی 16.3.1)، جدول متریک (۱۶۹ تست، ۶۰+ اندپوینت، ۸x)، ۳ سناریوی کاربری (USSD، توسعه‌دهنده پروژه کربن، Voice IVR). همین اعداد traction در اینجا هم بدون حاشیه «صداقت» ارائه شده‌اند.

### `D:\eco_nojin\DEMO_SCRIPT.md` — اسکریپت دمو (۱۴ آگوست 2026)
سه سطح دمو (۵/۱۵/۳۰ دقیقه) با زمان‌بندی دقیق و دیالوگ آماده. سناریوی ۱۵ دقیقه: تور ۹ پنل (خاک، ماهواره، Crop Planner، سناریو، کربن، آبخیز، مارکت‌پلیس، بنچمارک، AI) ← دموی USSD/SMS/Voice ← **دموی بلاک‌چین** (ثبت پروژه کربن ← verify با verifier "Verra" ← صدور ۸۰۰ اعتبار ← انتقال ← retire با اندپوینت‌های `/api/v1/blockchain/carbon/*`) ← deep-dive فنی ← کسب‌وکار. بخش Q&A آماده (چرا USSD؟ رقابت؟ دقت علمی؟ CAC پایین؟). عیب‌یابی (ویدیوی ضبط‌شده به‌عنوان fallback). اعداد کلیدی برای حفظ: 2.5B/70%/25%/14/169/60+/8x/$43B. **نکته تحلیلی:** دموی بلاک‌چین با verifier "Verra" در واقع «دموی داخلی» است و سند 05/11 صریحاً هشدار می‌دهند که نباید به‌عنوان گواهینامه واقعی ارائه شود — اسکریپت دمو این تمایز را به‌وضوح به مجری گوشزد نمی‌کند.

### `D:\eco_nojin\PROJECT_SUMMARY.md` — خلاصه پروژه (v1.4.0، «MVP Complete»)
وضعیت: «Production-Ready Research Prototype». متریک‌ها: ۱۴ ماژول، ۱۶۹ تست (100٪)، ۶۰+ اندپوینت، ۱۴ زبان، ۵ کانال، ۸x Numba، FastAPI/Python 3.11، Next.js 15.1.6 (به‌روزرسانی نشده با 16.3.1). همان TAM/SAM/SOM و مدل Freemium. بخش وضعیت فعلی: MVP کامل، آماده پایلوت، به‌دنبال seed/پایلوت‌پارتنر/مشارکت telco. **قدم‌های بعدی:** 0-3 ماه (پایلوت ۱,۰۰۰ کشاورز ایران، تخصیص کد USSD، **فیکس CVE-2025-66478 + دیپلوی تولید** — که در Phase 0 انجام شد)، 3-12 ماه (ماژول ۱۵ مالی/اعتبار خرد، ماژول ۱۶ بیمه شاخص‌محور، توسعه به پاکستان/افغانستان)، 1-3 سال (۱۰ میلیون کشاورز، رجیستری‌های ملی کربن، وایت‌لیبل دولتی).

---

## تصمیم‌های کلیدی پروژه

1. **معماری دوزبانه علم/محاسبه:** پایتون برای ارکستراسیون و API + هسته C++20 (و Numba) برای کرنل‌های عددی با توابع جایگزین یکسان — با pybind11/ctypes اتصال داده شده.
2. **شمول دیجیتال به‌عنوان دیفرانسیاتور اصلی:** ۵ کانال دسترسی (Web/PWA/USSD/SMS/Voice) و ۱۴ زبان از روز اول؛ USSD `*384*73#` برای feature phoneها.
3. **استانداردهای بیرونی به‌عنوان قرارداد:** هم‌راستایی با FAO-56، RUSLE، van Genuchten، IPCC AR6/CMIP6، OGC، ISO 14064، UN SDGs.
4. **اصل «صداقت علمی» (Honesty Contract):** داده ماهواره‌ای شبیه‌سازی‌شده هرگز به‌عنوان واقعی ارائه نمی‌شود (`data_source` پرچم‌دار)؛ خروجی `/verify` کربن تا تأیید آکرشده «دموی داخلی» می‌ماند؛ قرائت ابری (SCL<0.5) هرگز شاخص واقعی نیست؛ بدون اعتبارنامه، خطای صریح به‌جای داده جعلی.
5. **توکنومیکس اکوکوین به‌عنوان utility token:** 1 ECO = 1 تن CO2؛ عرضه ثابت 100M؛ کف قیمت $5؛ بدون ICO و بدون بازار ثانویه ابتدائاً؛ Polygon به‌عنوان بلاک‌چین هدف.
6. **مدل درآمد تسهیل‌گری (نه دریافت سرمایه):** ۱۰٪ کمیسیون تسهیل + ۵٪ سود + مارکت‌پلیس 2-5٪ + اشتراک/API/داده؛ سر به سر ماه 8-10.
7. **تکامل از Monolith به Microservices** با آمادگی پساکوانتوم (ML-KEM/ML-DSA) در لایه Ledger از ابتدا.
8. **استراتژی ۳۰ ساله (تا 2055):** فریز `/api/v1/`، حداقل وابستگی (هدف ۱۴ پکیج در ۳۰ سال)، ADR برای هر تصمیم، دریل بکاپ سالانه به‌عنوان release gate، سند وضعیت سالانه.
9. **توالی فاز اجرایی:** Phase 0 (عملیات/بکاپ/Alembic/ارتقای امنیتی) ← فازهای 4-8 با ترتیب Copernicus ← Admin ← Content ← Models ← Token/Carbon؛ مدل‌ها با fidelity badge و پارتی عددی 1e-9 با C++.

## شکاف‌های مستندسازی

1. **تناقض توزیع توکن:** «70/15/10/5» در `20_phase8_token_carbon.md` در برابر «40/25/15/10/10» در `ECO_COIN_WHITEPAPER.md` — بدون هیچ سندی که این دو را reconcile کند؛ همچنین نرخ «100 ECO/unit» سند 20 با «1 ECO = 1 تن» وایت‌پیپر ناسازگار به نظر می‌رسد.
2. **تناقض شماره‌گذاری فازها:** `00_master_plan.md` فقط ۵ فاز دارد، اما اسناد اجرایی از Phase 0 (عملیات)، 4 (Copernicus)، 5 (Admin)، 6 (Content)، 7 (Models)، 8 (Token/Carbon)، 9 (Frontend) استفاده می‌کنند — نگاشت فاز به فاز (مثلاً Phase 4 کارشناسی در master plan = شمول اقتصادی، ولی در سند 16 = داده ماهواره) روشن نیست.
3. **دوزبانه‌بودن نقض‌شده:** ۱۰ سند جدید en (13-21 و 22_implementation_report) ترجمه فارسی ندارند، در حالی که STD-009 و 99_conversation_summary دوزبانه‌بودن را الزام می‌کنند.
4. **منسوخ‌شدن سند CVE و W-017:** سند امنیتی هنوز Next.js 15.1.6 را «در حال استفاده» می‌گوید در حالی که فاز 0 به 16.3.1 ارتقا داده؛ ثبت W-017 و بخش‌هایی از W-003 در سند 11 با واقعیت کد هم‌زمان نیستند (خود سند 11 به قانون «بازتأیید از کد» اشاره دارد ولی رعایت نشده).
5. **اعداد Traction قدیمی/ناهماهنگ در فایل‌های ریشه:** INVESTOR_PITCH/PRESENTATION/PROJECT_SUMMARY همگی «۱۶۹ تست، ۶۰+ اندپوینت، Next.js 15.1.6، real-time satellite، blockchain-verified» را بدون حاشیه صداقت تکرار می‌کنند، در حالی که docs/en جدیدتر ۳۶۰ تست، ۲۵۳+ تست فاز 4، 330 تست فاز 7 و داده شبیه‌سازی‌شده (تا Phase 4) را ثبت کرده‌اند؛ ناهماهنگی بین «خلاصه اجرایی $7.5M» و «پروژکشن $4.5M» در ECONOMIC_MODEL.md.
6. **نقص ساختاری در اسناد:** سند 16 دو بخش «## 5» و دو بخش «## 6» تکراری دارد (نشانه ادغام بد در طول جلسات)؛ سند 21 عمدتاً به‌صورت نیمه‌فارسی/چندزبانه و با نمادهای نامشخص (؟/؟؟/؟؟؟) نوشته شده؛ سند 11 شامل دو ورودی W-003 با وضعیت‌های متفاوت است؛ سند 22_implementation_report تقریباً تمام‌فارسی ولی با نام en است (قرارداد نام‌گذاری شکسته).
7. **نبود مستندات حوزه‌ای که اسناد فاز به آن‌ها ارجاع می‌دهند:** «VerificationOracle migration from econojin.com»، «docs/ops/runbook.md»، «docs/adr/» (فقط ADR-0001 وعده داده شده)، «docs/status/YYYY.md» — هیچ‌کدام هنوز وجود ندارند.
8. **اعداد تست در اسناد 09/10/11 با هم اختلاف دارند** (125/126 ← 127/1fail ← 128 تست در سند 10؛ سپس 253، 307، 330، 360 در فازهای بعدی) — هیچ جدول واحدی از تکامل شمار تست‌ها وجود ندارد.

## پیشنهادها

1. **ایجاد «دیتابیس تصمیم» (Decision Log) یکپارچه:** یک فایل `docs/DECISIONS.md` یا ADR-0001 واقعی بسازید که نگاشت فازها (master plan 5 فازی در برابر فازهای اجرایی 0-9)، توزیع توکن نهایی (70/15/10/5 در برابر 40/25/15/10/10) و نرخ تبدیل ECO (1 ECO = 1 تن در برابر 100 ECO/unit) را به‌صورت قطعی ثبت کند؛ سپس اسناد متعارض را به آن ارجاع دهید. این بالاترین اولویت است چون توکنومیکس پایه‌ی جذب سرمایه و انطباق حقوقی است.
2. **بازنگری فایل‌های ریشه با «حاشیه صداقت»:** INVESTOR_PITCH/PRESENTATION/PROJECT_SUMMARY/DEMO_SCRIPT باید اعداد traction را از ۱۶۹ تست به آخرین وضعیت (۳۶۰+ تست) و نسخه Next.js را به 16.3.1 به‌روزرسانی کنند؛ و در DEMO_SCRIPT برای بخش بلاک‌چین یک یادداشت صریح «این دموی داخلی است، نه گواهینامه Verra» اضافه شود تا با ریسک W-012 تداخل نکند.
3. **بستن شکاف ترجمه:** ترجمه فارسی ۱۰ سند فاز اجرایی (13-21 و 22_implementation_report) را برنامه‌ریزی کنید — یا حداقل خلاصه فارسی هر فاز؛ این الزام صریح STD-009 و 99_conversation_summary است.
4. **به‌روزرسانی سند 11 بر اساس قانون خودش:** ورودی‌های W-001 (در progress با کلاینت CDSE)، W-002، W-017 (Next.js ارتقا یافته)، W-018 (سوئیت سبز شده)، W-003 (تکراری/منسوخ) و STD-ها را با شواهد کد بازبینی و ثبت تاریخ/کامیت کنید؛ ورودی تکراری W-003 حذف شود.
5. **سازمان‌دهی سند 16:** بخش‌های تکراری (## 5 و ## 6 دو بار) ادغام شوند و تاریخ هر دستاورد به‌صورت خط زمانی ثبت شود؛ همین کار برای هر سند فازی که در چند جلسه رشد کرده (17، 18، 19) انجام شود تا تاریخچه قابل ردیابی باشد.
6. **ثبت «شمارش تست‌ها» به‌عنوان متریک رسمی:** یک جدول در `docs/status/` یا README که تکامل شمار تست (126 → 253 → 307 → 330 → 360) را با تاریخ و شواهد ثبت کند تا از تناقض اسناد جلوگیری شود.
7. **تکمیل مصنوعات وعده‌داده‌شده:** قبل از پایلوت، `docs/ops/runbook.md` (الزام docs/06 §6)، `docs/adr/README.md` + ADR-0001، و `docs/status/2027.md` ساخته شوند؛ چک‌لیست پیش-پایلوت سند 08 به‌عنوان منبع حقیقت عملیاتی به‌روز نگه داشته شود.
8. **اعتبارسنجی عددی توکنومیکس:** یک شبیه‌سازی مالی (سناریوهای بالا/پایه/پایین) برای نسبت‌های توزیع ECO و نرخ 100 ECO/unit انجام و به وایت‌پیپر پیوست شود تا اعداد با هم قابل راستی‌آزمایی باشند — پیش از هرگونه تماس با سرمایه‌گذار یا مشاور حقوقی.

---

*گزارش پایان. تمام مسیرها دقیق و تمام ادعاها مستند به متن فایل‌های خوانده‌شده در 2026-08-17 است.*
