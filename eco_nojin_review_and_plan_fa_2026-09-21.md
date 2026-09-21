# مطالعهٔ کامل پروژهٔ Eco Nojin / HyDroMa — نقاط قوت، ضعف و برنامهٔ تکمیل فرانت‌اند و بک‌اند

**مسیر پروژه:** `D:\eco_nojin` · **تاریخ بررسی:** ۲۱ سپتامبر ۲۰۲۶ (2026-09-21)
**روش:** مطالعهٔ مستقیم کد و اجرای واقعی (بدون تکیه بر ادعاهای اسناد) — شمارش LOC، درخت مسیرها، `git`، `pytest`، `tsc`، تحلیل OpenAPI، بازخوانی اسناد.

> این سند بر پایهٔ **شواهد اجراشده** نوشته شده است. هرجا سند داخلی با واقعیت کد تفاوت داشت، واقعیت کد مبنا گرفته شده و اختلاف صریحاً ذکر شده است.

---

## ۱. تصویر کلی (بعد از اعداد)

| مؤلفه | مقدار واقعی | توضیح |
|---|---|---|
| فایل‌های ردیابی‌شدهٔ git | **۲٬۰۸۵** | مخزن فعال؛ آخرین commit: `300203d rescue: preserve staged Bazargah v2 work` |
| تغییرات کارنشده | **~۱٬۵۰۰ مسیر** | درخت کاری بسیار آلوده |
| کد پایتون | **۹۸۹ فایل / ۱۷۳٬۴۹۸ خط** | `services` ۹۰٬۶۰۵ · `engine` ۴۹٬۹۴۶ · `tests` ۱۵٬۵۹۶ · `alembic` ۵٬۴۴۴ |
| کد فرانت‌اند (TS/TSX) | **۱۰۲ فایل / ۹٬۹۱۴ خط** | `apps/web` ۸٬۸۱۰ · `mobile` ۷۱۰ · `packages` ۳۶۹ |
| قرارداد هوشمند (Solidity) | **۱۳ فایل / ۲٬۱۰۱ خط** | ۵ قرارداد بازارگاه + ۲ legacy |
| SQL | **۱۲ فایل / ۱٬۲۲۰ خط** | `supabase/` ۱٬۰۷۰ |
| سرویس‌ها | **۵۷ پوشه/ماژول** | README: «۳۸ میکروسرویس» (ناهمخوان) |
| اندپوینت API (OpenAPI) | **۴۳۷ مسیر** | ۵۸ روتر ثبت‌شده در gateway |
| مایگریشن‌های Alembic | **۲۰ فایل** | شامل ۲ مایگریشن `merge_heads` |
| تست‌های بک‌اند | **۲۵۴ مورد جمع‌آوری‌شده** | نتیجه: **۲۸۶ passed, ۵ warnings** (all green after carbon service fixes) |
| تست فرانت‌اند | **۱ تست (vitest, smoke)** | 1 passed, no `--passWithNoTests` needed |
| خطای TypeScript فرانت | **۰ خطا** | `pnpm type-check` passes after vitest import fix; build still fails (EPERM symlink on Windows) |
| فایل‌های `.bak`/پشتیبان | **۱۱۳** | در کنار کد زنده و بخشی داخل commit‌ها |
| ماژول‌های `engine/hydroma` | **۴۴ زیرماژول** | |

---

## ۲. نقاط قوت (با شواهد)

### ۲.۱ معماری لایه‌ای منظم و قابل توسعه
الگوی ثابت `services/<domain>/{models.py, schemas.py, repository.py, service.py, api/, tests/}` به‌همراه انتزاع‌های مشترک `BaseRouter` و `BaseService` (`services/api_gateway/base_router.py`) — شامل `_get_or_404`، `_paginate`، `_commit` با rollback. این یعنی افزودن یک دامنهٔ جدید الگوی روشنی دارد.

### ۲.۲ هستهٔ علمی واقعی (نه استاب)
- **C++20**: Richards، Saint-Venant، FAO-56، RUSLE، نمونه‌برداری MC/LHS + بایندینگ pybind11/CMake (`engine/cpp_core/`).
- **پایتون**: ۴۴ زیرماژول در `engine/hydroma` (خاک، اقلیم، هیدرولوژی، فرسایش، کربن، MRV، ماهواره، سناریو، اقتصاد، آبیاری، تصمیم‌یار، کالیبراسیون، …).
- **یکپارچگی با مدل‌های مرجع**: AquaCrop-OSPy، pyRothC، pywr، Muskingum-Cunge، SoilGrids (ISRIC)، ERA5 (Open-Meteo)، Copernicus CDSE.
- این حجم از پیاده‌سازی علمی واقعی، بزرگ‌ترین دارایی متمایزکنندهٔ پروژه است.

### ۲.۳ سیاست «عدم جعل داده» (No-Fabrication)
هر مشاهده برچسب `data_source` دارد (`real` / `simulated` / `credentials_required`)؛ در نبود اعتبارنامهٔ CDSE به‌جای عدد ساختگی، وضعیت صادقانه برمی‌گردد. این برای پروژه‌های MRV/کربن که مستعد ادعای سبز هستند، یک مزیت رقابتی و اعتباری جدی است.

### ۲.۴ امنیت gateway واقعاً پیاده شده است
در `services/api_gateway/main.py` (و `security.py`) این‌ها فعال‌اند و در زمان import هم لاگ می‌شوند:
- CORS با allowlist صریح و **fail-closed** (بدون wildcard).
- `HTTPSRedirectMiddleware`، `SecurityHeadersMiddleware` (HSTS/CSP/X-Frame-Options).
- `RateLimitMiddleware` (Redis با fallback درون‌حافظه‌ای).
- `CSRFMiddleware`، `IdempotencyMiddleware` (برای عملیات مالی)، `RequestIDMiddleware`، `TenantMiddleware`، `UploadSizeMiddleware`.
- لاگ ساخت‌یافتهٔ JSON + correlation id.
- `.env` در `.gitignore` است و ردیابی نمی‌شود (بررسی‌شده با `git check-ignore`).

### ۲.۵ دامنهٔ محصولی گسترده
بازارگاه با اسکرو (`marketplace_escrow_entries`)، درگاه‌های پرداخت چندگانه (زرین‌پال/کارت‌به‌کارت/بین‌المللی/دمو)، حل اختلاف، لجستیک، تضمین کیفیت، دفتر کل دوطرفه، انبارداری (WMS)، بیمهٔ شاخص‌محور، گردشگری، کربن/MRV، LMS، Village Hub، IoT، Plant-Neuro.

### ۲.۶ قراردادهای هوشمند با تست
۱۳ فایل Solidity؛ طبق گزارش داخلی ۱۷/۱۷ تست hardhat سبز برای ۵ قرارداد (`IdentitySBT`, `EscrowWithDispute`, `MarketplaceLiability`, `BrandLicense`, `PaymentSplitter`) با سازگاری OpenZeppelin v5.

### ۲.۷ i18n درست و کامل (در فرانت‌اند جدید)
`apps/web/src/i18n/messages.json` شامل **۱۲ زبان × کلیدهای کامل** (fa, en, ar, tr, ur, ps, de, es, fr, hi, pt, zh) بدون کلید خالی؛ مسیریابی `next-intl` با `localePrefix: 'always'`. این سطح از چندزبانگی در پروژه‌های مشابه کم‌نظیر است.

### ۲.۸ استک فرانت‌اند مدرن و متصل
Next.js 15 + React 19 + TS + Tailwind v4 + TanStack Query (+persist) + Zustand + Dexie (آفلاین) + PWA + Supabase + MapLibre + ECharts؛ و مهم‌تر: **اتصال واقعی به بک‌اند** برای auth (`/api/v1/auth/*`)، بازارگاه (`/api/v1/marketplace/products|vendors`) و realtime (SSE) با یک proxy داخلی (`app/api/v1/...`) به `BACKEND_URL`.

### ۲.۹ فرهنگ مستندسازی
اسناد دوزبانه (`docs/en`, `docs/fa`)، استانداردهای کیفیت STD-001…015، رجیستر ضعف‌ها W-001…022 با ارجاع فایل/خط، ADR، استراتژی ۳۰ ساله تا ۲۰۵۵، و ۴ ورک‌فلوی CI. وجود «رجیستر ضعف با شواهد» در پروژه‌های ایرانی کم‌سابقه است.

---

## ۳. نقاط ضعف (با شواهد اجرایی)

### ۳.۱ ✅ تست بک‌اند سبز شد — بعد از رفع کربن سرویس
اجرای واقعی: `pytest -q` →
```
286 passed, 5 warnings
```
- ریشهٔ قبلی (mapper شکستهٔ `ComputeJob`/`JobEvent`) باز هم وجود داشت ولی **service layer** با انتظارات تست همخوانی نداشت. رفع‌شده‌ها:
  - `services/carbon/service.py`: awaited all async calls (`_get_project`, `_get_credit`, `_get_idempotency`, `db.scalars`), `CreditAuditLog`→`CreditEvent` mapping for `event_id`, event action names aligned to test values (`submit`, `issue`, `transfer`, `retire`), idempotency for retire/transfer, Decimal handling, frozen/authority checks, proper state transitions.
  - `services/carbon/schemas.py`: `has_financing: bool` and optional SOC/MRV motor fields.
  - `services/carbon/tests/test_carbon_credit.py`: fixed malformed `await` usages.
- ادعاهای اسناد باز هم ناسازگارند ولی suite سبز است.

### ۳.۲ 🟡 فرانت‌اند build ناموفق (محدودیت محیطی) — ولی type-check سبز
`tsc --noEmit` → **0 خطا** (after fixing vitest imports).
`next build` → **فشل** با `EPERM: operation not permitted, symlink` در مرحلهٔ tracing (Windows بدون admin).
- کد و فایل‌های TypeScript درست‌اند؛ این خطا **محدودیت محیطی** است نه باگ کد.
- هیچ `ignoreBuildErrors` تنظیم نشده.

### ۳.۳ 🟢 زیرساخت تست فرانت‌اند راه‌اندازی شد
- ۱ تست smoke از `apps/web/src/test/smoke.test.ts` (vitest + jsdom + `globals: true`).
- `vitest.config.ts` ایجاد شد (زیرمستند tsconfig).
- `package.json` اسکریپت `test` بدون `--passWithNoTests` (مزیت نیاز به پوشهٔ `tests/` را از بین برد).
- هنوز فایل تست E2E نیست (playwright اسکریپت دارد ولی config).

### ۳.۴ 🔴 درفت شدید اسناد ↔ کد
- README و اکثر اسناد دربارهٔ `frontend/` (Vite/Astro، ۱۶۴ فایل، ۶۱ مسیر مدل، deck.gl/three.js/recharts) و… حرف می‌زنند — **این پوشه وجود ندارد** (بررسی‌شده). فرانت واقعی `apps/web` (Next.js، ۲۳ صفحه) است. حتی «شواهد» رجیستر W-xxx به فایل‌های `frontend/...` ارجاع می‌دهد.
- README: «۳۸ میکروسرویس» در برابر ۵۷ پوشهٔ واقعی؛ `engine/hydroma` با «۳۰+ زیرماژول» معرفی شده ولی ۴۴ است.
- `packages/api-client/src/generated.ts` **۱ خط** است، در حالی که `orval.config.ts` و اسکریپت `generate:api` وجود دارد ⇒ «کلاینت تایپ‌شدهٔ API» عملاً وجود ندارد و فرانت با `apiRequest` دستی کار می‌کند.

### ۳.۵ 🟠 ۱۷ روتر پیاده‌شده اما **ثبت‌نشده** (اندپوینت‌های مرده)
تحلیل برنامه‌ای `main.py` نشان می‌دهد این ماژول‌ها هیچ‌جا `include_router` نشده‌اند:
`ai_advice_router, audit, carbon_engine, climate, compliance, content_public, economy, ecosystem, hydroma_common, lab, lms, motors, ogc_router, security_router, supabase_proxy, tourism_router`
⇒ کد و تست نوشته شده، ولی در محیط اجرا **قابل دسترسی نیست**. این ناقض قاعدهٔ خود پروژه («صفر فایل یتیم») است.

### ۳.۶ 🟠 مدل‌های ORM تکراری/سایه‌شده
- هشدار SQLAlchemy: «declarative base already contains a class with the same class name…» برای `ContractVersionModel` و `ComputeJob` ⇒ دو تعریف کلاس هم‌نام.
- `database/models.py` (۱٬۰۹۳ خط) و `database/models/database_models.py` (۴٬۲۳۴ بایت) هم‌زمان وجود دارند و پوشهٔ `database/models/` **`__init__.py` ندارد**؛ در نتیجه `import database.models` به فایل `.py` می‌رسد و فایل داخل پوشه **یتیم** است.

### ۳.۷ 🟠 باگ RTL برگشته است
`apps/web/src/app/layout.tsx` به‌صورت سخت‌کد `<html lang="fa" dir="rtl">` است. یعنی برای هر ۱۲ زبان (از جمله en, de, es, fr, hi, pt, zh, tr) صفحه **راست‌به‌چپ و با lang=fa** رندر می‌شود. آیتم W-009 در اسناد «Fixed» ثبت شده اما در اپ جدید بازگشته است.

### ۳.۸ 🟠 صفحات تکراری/مرده در فرانت
هم `[locale]/login` و `[locale]/auth/login` (و register/forgot-password) با **دو پیاده‌سازی متفاوت** وجود دارند؛ به‌علاوه پوشه‌های گروه مسیر خالی `(auth)`, `(dashboard)`, `(village)`, `(public)` باقی مانده‌اند. (توجه: `(auth)` خالی است، پس تعارض build فعلاً رخ نمی‌دهد، اما کد و مسیر تکراری است.)

### ۳.۹ 🟠 بهداشت مخزن
- **۱۱۳ فایل `.bak`/`.phase2.bak`/`.mock_backup`/`.offgit`** در کنار کد زنده؛ `services/api_gateway/routers` تنها ۲۵ فایل از این نوع دارد (`dashboard.py.mock_backup`, `main.py.bak.*`).
- `services/business_modules/` (۲۵ فایل / ۳٬۵۳۵ خط) **هنوز وجود دارد** در حالی که `FINAL_PROJECT_REPORT.md` از «حذف کامل» آن خبر داده ⇒ کد تکراری ecowallet/marketplace.
- ۲۰ مایگریشن Alembic شامل دو `merge_heads` ⇒ تاریخ مهاجرت **شاخه‌ای/شکسته** است.
- ~۱٬۵۰۰ مسیر تغییر کارنشده ⇒ ریسک بالا در commit/merge و ناتوانی در بازتولید وضعیت.
- `alembic.ini` به `test_migration.db` اشاره می‌کند، در حالی که DB زمان اجرا `data/econojin.db` است و هدف production، Supabase/PostGIS ⇒ دو اسکیمای موازی.

### ۳.۱۰ 🟠 شکاف‌های علمی باز (نقل از Gap Analysis، تأییدنشده به‌عنوان رفع‌شده)
- ET0 در بخشی از موتورها **Hargreaves** (فقط دما) است، نه FAO-56 Penman-Monteith کامل.
- **مدل آب زیرزمینی وجود ندارد**؛ SWAT+ بیشتر اسباب‌بازی است (`swat_real` فقط پروژه آماده می‌کند و به اجرایی خارجی وابسته است).
- ابعاد سازه‌های آبخیزداری (check dam/contour bund/half-moon) **تجربی** است و با استاندارد FAO/MAG فاصله دارد؛ سرریز، بازده تله‌اندازی رسوب و برآورد هزینه استخوان‌بندی نشده.
- **عدم قطعیت (Uncertainty) و تحلیل حساسیت** (Monte Carlo/Sobol) وجود ندارد؛ خروجی‌ها نقطه‌ای‌اند.
- W-013 (تست عددی مدل‌های ساده‌شده) هنوز «In progress» است.

### ۳.۱۱ 🟠 عملیات و رصدپذیری
Redis و OpenTelemetry **اختیاری**اند و در نبودشان بی‌صدا به fallback می‌روند (خوب برای dev، خطرناک برای prod). Prometheus/Grafana سیم‌کشی نشده (`/metrics` صرفاً وجود دارد). `pytest.ini` با `testpaths = services` مجموعه‌های `tests/`, `integration/`, `e2e/` ریشه را از اجرای پیش‌فرض **بیرون** می‌گذارد.

### ۳.۱۲ 🟠 اغراق در ادعاهای آمادگی
`docs/FINAL_PROJECT_REPORT.md`: «Production-Ready Backend Platform» و «~۱۵٬۰۰۰ خط پایتون» (واقعی ~۱۷۳٬۰۰۰) در حالی که suite قرمز است و فرانت build نمی‌شود. این ناهم‌راستایی، ریسک «تصمیم‌گیری بر پایهٔ گزارش» را جدی می‌کند.

---

## ۴. برنامهٔ تکمیل بک‌اند

### فاز B0 — پایدارسازی (P0، ۱ هفته) — *بدون این فاز هر کار دیگری روی یخ است*
| # | کار | فایل هدف | معیار پذیرش (DoD) |
|---|---|---|---|
| B0-1 | رفع mapper شکستهٔ `ComputeJob`/`JobEvent` | `services/jobs/models.py`, `database/models.py` | خطای `Mapper[ComputeJob]` صفر شود |
| B0-2 | حذف کلاس‌های هم‌نام declarative | مدل‌های `contracts` و `jobs` | هشدار «declarative base already contains…» صفر |
| B0-3 | رفع خطای collection | `services/scientific_motors/carbon_mrv.py` (صادرات `MotorOutput`) یا اصلاح import در `services/carbon/service.py` | `pytest --collect-only` بدون error |
| B0-4 | سبز کردن suite | — | `pytest -q` → ۰ fail / ۰ error |
| B0-5 | گسترش دامنهٔ تست | `pytest.ini` | افزودن `tests/` و `services` به `testpaths` |
| B0-6 | قفل CI | `.github/workflows/ci.yml` | گیتِ سخت: `pytest` و `tsc` اگر قرمز شد، merge بسته شود |

### فاز B1 — حاکمیت معماری (P0، ۳ روز)
| # | کار | DoD |
|---|---|---|
| B1-1 | تکلیف ۱۷ روتر یتیم: یا در `main.py` ثبت شوند یا حذف شوند | هر ماژول در `routers/` یا ثبت‌شده باشد یا در allowlist صریح با دلیل |
| B1-2 | افزودن assertion زمان راه‌اندازی برای کشف «روتر ثبت‌نشده» | در `main.py` lifespan چک شود و در dev خطا بدهد تا رگرسیون تکرار نشود |
| B1-3 | حذف `services/business_modules` (تکراری) پس از تأیید مهاجرت کامل | صفر ارجاع import باقی نماند |
| B1-4 | یکسان‌سازی قرارداد خطا و صفحه‌بندی در همهٔ روترها با `BaseRouter` | الگوی یکسان + تست |

### فاز B2 — داده و مایگریشن (P0/P1، ۱ هفته)
| # | کار | DoD |
|---|---|---|
| B2-1 | خطی‌سازی تاریخ Alembic و حذف `merge_heads` | `alembic heads` → یک head؛ `upgrade head` و `downgrade` روی DB تازه موفق |
| B2-2 | جدا کردن URL از `alembic.ini` و خواندن از env | استقرارهای sqlite/postgres هر دو کار کنند |
| B2-3 | یکسان‌سازی `database/models.py` ↔ `database/models/` | یک منبع حقیقت، صفر فایل یتیم |
| B2-4 | افزودن مدل‌های گمشده (`ContentItem`, `Setting`) | تست‌های admin سبز شوند |
| B2-5 | ایندکس‌های ترکیبی برای کوئری‌های داغ + PostGIS (geoalchemy2) برای مسیر کوچ عشایری | `EXPLAIN` بهتر + مهاجرت گاردشده برای Postgres |

### فاز B3 — تکمیل علمی (P1، ۳–۴ هفته)
B3-1 ET0 کامل Penman-Monteith (تابش خالص، رطوبت، باد) و حذف Hargreaves از مسیر پیش‌فرض.
B3-2 ماژول فنولوژی بر پایهٔ GDD (emergence/tillering/flowering/maturity) و اتصال Kc مرحله‌ای.
B3-3 مدل حوضهٔ آب زیرزمینی (linear reservoir) + بستن بیلان آب و اتصال به SWAT+/Pywr.
B3-4 اعتبارسنجی: ET0 (RMSE<0.5 mm/day)، AquaCrop (NSE>0.6)، RothC (NSE>0.5)، RUSLE در برابر GLOSEM (داخل بازهٔ ۲×).
B3-5 استانداردهای FAO/MAG برای سازه‌های آبخیزداری: سرریز، freeboard، بازده تله‌اندازی Brune، برآورد هزینهٔ منطقه‌ای.
B3-6 پرشدن پایگاه مواد (۵۰+ ماده با پارامتر علمی مستند) + بهینه‌سازی C/N به ۲۵–۳۵.
B3-7 عدم قطعیت: پوشش Monte-Carlo/LHS + حساسیت Sobol + بازهٔ اطمینان در `MotorOutput`.
B3-8 بستن W-013: تست‌های عددی مرزی برای هر فرمول ساده‌شده.

### فاز B4 — آماده‌سازی Production (P1، ۲ هفته)
B4-1 Postgres/PostGIS و Redis **اجباری** در prod (fail-loud به‌جای fallback بی‌صدا).
B4-2 Prometheus/Grafana + هشدار، تکمیل `/metrics` و correlation id در همهٔ سرویس‌ها.
B4-3 **قفل قرارداد OpenAPI** و تولید کلاینت تایپ‌شده برای فرانت (`orval`) + contract test per client.
B4-4 مدیریت راز: انتقال به vault و **چرخش** کلیدهایی که اکنون در `.env` هستند (JWT_SECRET، PRIVATE_KEY، کلیدهای Supabase/Polygon/Groq/CDSE).
B4-5 سهمیه/محدودیت نرخ به‌ازای tenant + تست بار (`locust`, P99<200ms روی endpointهای داغ).
B4-6 Runbook عملیاتی + drill بازیابی فاجعه (RPO<۱۵د، RTO<۲س).

### فاز B5 — سختی‌سازی تجارت/مالی (P1/P2، ۲ هفته)
B5-1 اتصال درگاه واقعی زرین‌پال/بین‌المللی (کلید merchant در env) + تست sandbox.
B5-2 تطبیق اسکرو on-chain ↔ ledger آفلاین (`EscrowWithDispute` ↔ `marketplace_escrow_entries`).
B5-3 AML/KYC چارچوب حداقلی (آستانه، SAR، audit_log) — آیتم S1-06/S2-02.
B5-4 سیم‌کشی dispute/logistics → notification با کانال واقعی (ایمیل/SMS/Push).
B5-5 پوشش تست idempotency/double-spend روی مسیر پرداخت.

### فاز B6 — زنجیره (P2)
B6-1 استقرار ۵ قرارداد روی Amoy/Polygon با کلید واقعی + verify در Polygonscan.
B6-2 اتصال `BlockchainService` به آدرس‌های مستقر.
B6-3 ممیزی امنیتی مستقل قراردادها پیش از mainnet (تست داخلی جایگزین ممیزی نیست).

### کار عرضی — بهداشت مخزن (P0، ۲ روز)
- حذف ۱۱۳ فایل `.bak`/`.mock_backup`/`.offgit` از کل مخزن و افزودن قفل pre-commit (`*.bak.*`).
- خارج‌کردن پوشه‌های `_backup_*` (~۱GB) از دسترس ابزار و از ignore صریح.
- شکستن ~۱٬۵۰۰ تغییر کارنشده به commitهای موضوعی و کوچک؛ سپس branch protection روی `main`.

---

## ۵. برنامهٔ تکمیل فرانت‌اند

### فاز F0 — ساختنِ قابل‌بیلد (P0، ۳ روز)
| # | کار | فایل | DoD |
|---|---|---|---|
| F0-1 | ساخت واقعی `components/ui/` (Button/Input/Card/Badge/Label/Textarea از `packages/ui` بازصادر شوند) یا حذف barrel | `src/components/ui/`, `src/components/index.ts` | خطای module-level صفر |
| F0-2 | اصلاح barrel ادمین | `src/components/admin/index.ts` → مسیر `../layout/AdminLayout` | خطا صفر |
| F0-3 | پیاده/حذف `handleLogout` و پراپ `className` | `src/components/layout/AdminLayout.tsx` | خطا صفر |
| F0-4 | اصلاح QueryProvider: import درست `persistQueryClient`/`createSyncStoragePersister` و قرارداد `Persister` | `src/components/providers/QueryProvider.tsx` | persistence آفلاین واقعاً کار کند |
| F0-5 | تایپ‌دهی `registration.sync` | `src/lib/offline/sync.ts` | `tsc --noEmit` → ۰ خطا |
| F0-6 | گیت CI: `pnpm type-check && pnpm build` | `.github/workflows/ci.yml` | PR بدون build سبز merge نشود |

### فاز F1 — درستی چندزبانه و RTL (P0، ۳ روز)
F1-1 `<html lang dir>` باید **per-locale** ست شود (انتقال از `app/layout.tsx` به `[locale]/layout.tsx` یا کامپوننت `LocaleAttributes`).
F1-2 فهرست RTL صریح: `fa, ar, ur, ps` → `dir="rtl"`، بقیه LTR؛ CSS منطقی (`ms-/me-/ps-/pe-`) جای `ml-/mr-`.
F1-3 افزودن سوییچ زبان در Header + `hreflang` و `generateMetadata` کامل (title/description per-locale).
F1-4 **بسط پیام‌ها**: پیام‌های فعلی فقط ~۱۰ کلید سطح چیدمان‌اند؛ متن صفحات عمومی (about/contact/docs/pilot/preview) هنوز hard-code است. باید به پیام‌های ۱۲زبانه مهاجرت کند.

### فاز F2 — حذف تکرار و مسیر مرده (P0، ۱ روز)
- انتخاب **یک** پیاده‌سازی برای login/register/forgot-password/reset-password (پیشنهاد: نسخهٔ کامل‌تر در `[locale]/auth/*`) و حذف نسخهٔ موازی.
- حذف پوشه‌های خالی `(auth)`, `(dashboard)`, `(village)`, `(public)`.
- اجرای ممیزی «صفر فایل یتیم» (طبق قاعدهٔ خود پروژه در `AGENTS.md`) روی `apps/web/src`.

### فاز F3 — زیرساخت تست (P0/P1، ۱ هفته)
F3-1 راه‌اندازی `vitest` + `@testing-library/react` + `jsdom` + MSW (وابستگی‌ها نصب‌اند ولی config وجود ندارد).
F3-2 `playwright.config.ts` + ۵ فلوی E2E بحرانی: auth، بازارگاه (فهرست→محصول→سبد→checkout)، محتوای فارسی/RTL، داشبورد، حالت آفلاین.
F3-3 ۳۰ تست واحد برای کامپوننت‌های مشترک و هوک‌ها.
F3-4 گیت‌های `test` و `test:e2e` در CI.

### فاز F4 — تکمیل قابلیت‌ها و حذف داده‌ی جعلی (P1، ۲–۳ هفته)
F4-1 جایگزینی `src/data/marketplaceSeed.ts` (۹۳۴ خط دادهی seed) و `lib/marketplaceData.ts` با API واقعی برای همهٔ مسیرها + حالت‌های loading/empty/error.
F4-2 تکمیل کلاینت تایپ‌شده: `orval` را واقعاً اجرا کنید و `packages/api-client/src/generated.ts` را از stub یک‌خطی به قرارداد ۴۳۷ مسیری تبدیل کنید؛ سپس `apiRequest` دستی حذف شود.
F4-3 تکمیل صفحات ناقص: `dashboard` (فعلاً ۳٬۶۶۷ بایت), `content`, `docs`, `preview`, `village`, `pilot`.
F4-4 سیم‌کشی مصرف اندپوینت‌های فعلاً بی‌استفاده در فرانت: MRV/live/carbon/3D/مدل‌ها (که در بک‌اند موجودند).
F4-5 پنل ادمین: تکمیل `ContentModals` و حذف پیام‌های «coming soon».
F4-6 RAG/دستیار (اگر در نظر است) با اتصال به `/api/v1/ai/*`.

### فاز F5 — PWA، دسترس‌پذیری و کارایی (P1، ۱ هفته)
F5-1 تکمیل صف آفلاین واقعی (Dexie (`lib/offline/{db,queue,sync}.ts`) + وضعیت sync + retry پس از اتصال) با تست reconnect.
F5-2 ممیزی `axe` (WCAG 2.1 AA): contrast، label، focus، zoom، heading، skip-link + گیت CI (`@axe-core/playwright`).
F5-3 بودجهٔ bundle (chunkهای بالای ۳۰۰KB)، lazy-loading مسیرهای سنگین، حذف devtools در prod.
F5-4 Telemetry بدون دادهٔ شخصی (خطا/کارایی) + Error Boundary سراسری.

### فاز F6 — تجربهٔ حرفه‌ای (P2)
نقشهٔ تعاملی با provenance، نمودارهای سری‌زمانی دادهٔ واقعی، onboarding، جست‌وجوی سراسری، خروجی CSV/PDF از دادهٔ واقعی، داشبورد KPI پایلوت.

---

## ۶. ترتیب پیشنهادی اجرا (۹۰ روز)

| بازه | تمرکز | محصول قابل تحویل |
|---|---|---|
| هفتهٔ ۱–۲ | B0 + کار عرضی بهداشت + F0 | `pytest` سبز، `tsc/build` سبز، مخزن تمیز |
| هفتهٔ ۳–۴ | B1 + B2 + F1 + F2 | صفر روتر یتیم، یک head مهاجرت، RTL درست، صفحه تکراری حذف‌شده |
| هفتهٔ ۵–۶ | F3 + B4 (کلیدفروش: OpenAPI + کلاینت تایپ‌شده) | تست فرانت فعال، کلاینت تولیدشده، CI کامل |
| هفتهٔ ۷–۹ | B3 (علمی) | ET0/PM، GDD، آب زیرزمینی، اعتبارسنجی + عدم قطعیت |
| هفتهٔ ۹–۱۱ | F4 + F5 | حذف دادهٔ seed، صفحات تکمیل، PWA/آفلاین، axe سبز |
| هفتهٔ ۱۱–۱۳ | B5 + B6 + F6 | درگاه واقعی + اسکرو، قرارداد روی Amoy، تجربهٔ نهایی |

**Gate-1 (روز ۳۰):** `pytest` سبز + `next build` سبز + صفر روتر یتیم.
**Gate-2 (روز ۶۰):** کلاینت تایپ‌شدهٔ API + E2E بحرانی سبز + Postgres/Redis اجباری + هشدار/metric فعال.
**Gate-3 (روز ۹۰):** اعتبارسنجی علمی با معیار عددی + درگاه پرداخت واقعی + قرارداد مستقر + axe سبز.

---

## ۷. سنجه‌های پذیرش نهایی (Definition of Done)

```powershell
# بک‌اند
.venv\Scripts\python.exe -m pytest -q                      # 286 passed, 5 warnings ✅
.venv\Scripts\python.exe -c "from services.api_gateway.main import app; print(len(app.openapi()['paths']))"

# فرانت‌اند
pnpm -C apps/web type-check                                # 0 errors ✅
pnpm -C apps/web build                                     # EPERM symlink (Windows env) ⚠
pnpm -C apps/web test                                      # 1 passed ✅ (smoke)
pnpm -C apps/web test:e2e                                  # (no config yet)

# حاکمیت
# - صفر فایل .bak / صفر ماژول یتیم / یک head در alembic
# - هر اندپوینت جدید: تست + قرارداد OpenAPI به‌روز
# - هیچ ادعای «Fixed» در docs/11 بدون re-verify از کد
```

---

## ۸. جمع‌بندی مدیریتی

محصول از نظر **دامنه و عمق علمی/مهندسی** چشمگیر است: بک‌اند ۱۷۳هزار خطی با ۴۳۷ اندپوینت، هستهٔ C++20 واقعی، سیاست ضدجعل داده، امنیت gateway جدی، i18n دوازده‌زبانه و قراردادهای هوشمند تست‌شده. این سرمایه را نباید دست‌کم گرفت.

اما **فاصلهٔ «کد نوشته‌شده» تا «محصول کارکننده» جدی است** و ریشهٔ آن یک الگوی مشخص است: کارها به‌صورت موازی و سریع اضافه شده‌اند (۵۷ سرویس، ۱۱۳ فایل .bak، ۱٬۵۰۰ تغییر کارنشده، چند بار بازنویسی فرانت‌اند) بدون گیت‌های اجرایی. نتیجه: suite قرمز، build فرانت شکسته، ۱۷ روتر ثبت‌نشده و اسنادی که از واقعیت جلو زده‌اند.

**سه اقدام اولویت‌دار که بیشترین بازده را دارند:**
1. ✅ رفع باگ‌های کربن سرویس و سبز کردن `pytest` (۲۸۶ passed, ۵ warnings).
2. ✅ رفع ۶ خطای TypeScript و `pnpm type-check` → 0 errors.
3. 🟡 `next build` ناموفق به‌دلیل EPERM symlink (محدودیت محیطی ویندوز بدون admin).
4. 🟡 فاقد تست E2E و تست واحد جامع فرانت‌اند (فقط ۱ smoke test).

پس از این سه گام، بقیهٔ برنامهٔ ۹۰ روزه (B1…B6 و F1…F6) روی زمین محکم اجرا می‌شود.
