# Eco Nojin — گزارش اجرای مستقیم تغییرات (Wave 1) — ۲۰۲۶-۰۹-۲۱

**مسیر پروژه:** `D:\eco_nojin` · **روش:** تغییر مستقیم کد + راستی‌آزمایی اجرایی در هر گام.

---

## ۱. نتیجهٔ کلی (قبل → بعد)

| سنجه | قبل | بعد | فرمان راستی‌آزمایی |
|---|---|---|---|
| خطاهای collection تست | ۱ error (متوقف‌کننده) | **۰** | `pytest --collect-only -q` |
| خطاهای اجرای تست (mapper cascade) | **۷۹ error** | **۰** | `pytest -q` |
| تست‌های پاس | ۱۱۸ | **۲۵۵** | `pytest -q` |
| تست‌های رد | ۵۷ | **۳۱** (همه در یک ماژول) | `pytest -q` |
| TypeScript فرانت‌اند | ۶ خطا | **۰ خطا** | `tsc --noEmit` |
| بیلد فرانت‌اند | **شکست** | **موفق (exit 0)** | `next build` |
| کلیدهای i18n مفقود | ۵۶ کلید × ۱۲ زبان | **۰** | build بدون MISSING_MESSAGE |
| فایل‌های پشتیبان در درخت زنده | ۱۱۳ | **۰** (قرنطینه‌شده) | `_quarantine_bak_2026-09-21/MANIFEST.md` |
| API زنده | ۴۳۷ مسیر | ۴۳۷ مسیر (بدون تغییر) | `app.openapi()['paths']` |

---

## ۲. رفع‌های انجام‌شده (با فایل و دلیل)

### ۲.۱ ریشهٔ اصلی قرمز بودن تست‌ها — نام رزروشدهٔ `metadata`
- **فایل:** `services/jobs/models.py`
- **مشکل:** ستون `metadata` در کلاس `JobEvent`؛ SQLAlchemy این نام را رزرو کرده است:
  `InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API`
  این خطا کل رجیستری mapper را می‌شکست و به‌صورت آبشاری ۷۹ error + بخشی از ۵۷ fail ایجاد می‌کرد.
- **اصلاح:** `event_metadata = Column("metadata", JSON, ...)` → نام attribute پایتون تغییر کرد، **نام ستون دیتابیس `metadata` حفظ شد** (سازگاری با دادهٔ موجود و قرارداد API).

### ۲.۲ مصرف‌کنندگان + باگ‌های همان ماژول
- **فایل:** `services/jobs/service.py`
  - رویداد وضعیت **دو بار** ساخته و add می‌شد → یک‌بار شد.
  - `select(ComputeJobEvent)` با نام تعریف‌نشده → `select(JobEvent)`.
  - آرگومان‌های `metadata=` → `event_metadata=`.
- **فایل:** `services/jobs/schemas.py`
  - `JobEventResponse` با `serialization_alias="metadata"` → **کلید عمومی API همچنان `metadata`** است.
  - دو باگ نحوی از پیش‌موجود: `Field(1024, ge=64, max(16384))` → `le=16384` و `max=16` → `le=16`.

### ۲.۳ خطای collection تست
- **فایل:** `services/carbon/service.py`
  - `from services.scientific_motors.carbon_mrv import CarbonMrvMotor, MotorOutput` →
    `MotorOutput` از `services.scientific_motors.base` (محل واقعی تعریف).
  - نتیجه: `pytest --collect-only` از ۲۵۴+۱error به **۲۸۶ تست جمع‌آوری بدون خطا** رسید.

### ۲.۴ اصلاح محصولی در کیف پول مالی (قرارداد خطا)
- **فایل:** `services/finance/wallet_service.py`
- **مشکل:** سرویس `ValueError` می‌انداخت؛ قرارداد پروژه `EcoNojinException` با `code` است (handler سراسری gateway به آن وابسته است). تست‌ها درست بودند.
- **اصلاح:** تبدیل ۹ نقطهٔ خطا به `EcoNojinException` با کدهای ماشین‌خوان و وضعیت HTTP درست:
  `UNKNOWN_CATEGORY`/`INVALID_QUANTITY` (422)، `DAILY_CAP_EXCEEDED` (409)، `INSUFFICIENT_BALANCE` (409)، `INVALID_AMOUNT`/`BELOW_MINIMUM_TRANSFER` (422).
- **نتیجه:** `services/finance/tests` → **۲۲/۲۲ پاس**.

### ۲.۵ فرانت‌اند: از «بیلد شکست‌خورده» تا «بیلد سبز» (۶ خطای TS → ۰)
| فایل | مشکل | اصلاح |
|---|---|---|
| `src/components/ui/` (خالی بود) | barrel `./ui` به ماژول ناموجود اشاره می‌کرد | `index.ts` ساخته شد و `@eco/ui` را بازصادر می‌کند |
| `src/components/admin/index.ts` | مسیر اشتباه `./AdminLayout` | `../layout/AdminLayout` |
| `src/components/layout/AdminLayout.tsx` | `handleLogout` تعریف‌نشده + پراپ `className` | پیاده‌سازی خروج + افزودن prop |
| `src/components/providers/QueryProvider.tsx` | `hydrate` import نشده؛ نقض قرارداد `Persister`؛ API منقضی `restoreOptions` (v4) | import درست، Persister با امضاهای `PersistedClient`، حذف API منقضی، افزودن `"use client"` |
| `src/lib/offline/sync.ts` | `registration.sync` از نوع `unknown` | اینترفیس محلی `SyncManager` + cast امن |
| `src/app/globals.css` | `@import './tokens.css'` (فایل در `src/styles/`) | `../styles/tokens.css` و `../styles/layout.css` |
| `next.config.ts` | پلاگین `next-intl` ثبت نشده بود → `Couldn't find next-intl config file` | `createNextIntlPlugin('./src/i18n/request.ts')` |
| `src/components/providers/Providers.tsx` + `app/[locale]/layout.tsx` | `PageAccentProvider` (هوک `usePathname`) **بالاتر از** `NextIntlClientProvider` بود → خطای prerender | به داخل `NextIntlClientProvider` منتقل شد |
| `app/layout.tsx` | `themeColor` در `metadata` (منقضی در Next 15) | به `export const viewport` منتقل شد |
| `[locale]/auth/{login,register,forgot-password}` | `useSearchParams()` بدون مرز Suspense | کامپوننت محتوا + `export default` با `<Suspense>` |
| `[locale]/{page,about,docs,pilot,preview}` | Radix `Slot` با چند فرزندِ هم‌سطح (`asChild`) | ۹ بلوک در یک `<span>` واحد پیچیده شد |
| `src/i18n/messages.json` | **۵۶ کلید مفقود در ۱۲ زبان** (`auth.*`، `dashboard.*`، `village.*`، `roles.*`، `auth.roles.*`) | همه با ترجمهٔ کامل ۱۲زبانه اضافه شد |

### ۲.۶ بهداشت مخزن
- **۱۱۳ فایل پشتیبان** (`*.bak`, `*.bak.*`, `*.offgit`, `*mock_backup`, `*.before_*.bak`) از درخت زنده خارج و به `_quarantine_bak_2026-09-21/` منتقل شد (قابل بازگردانی) + `MANIFEST.md` با نگاشت مسیرها.
- `.gitignore` به‌صورت **merge** (بدون حذف خطوط موجود) تقویت شد: `*.bak.*`, `*mock_backup`, `_quarantine_bak_*/`, `_backup_*/`.

---

## ۳. یافتهٔ معماری مهم (ریشهٔ ۳۱ تست قرمز باقی‌مانده)

`services/carbon` **دو پیاده‌سازی موازی از یک قرارداد** دارد:

| جزء | محل | مصرف‌کننده |
|---|---|---|
| مدل‌های درخواست + استثناها + `CreditState` | `services/carbon/schemas.py` | **تست‌ها** |
| همان مدل‌ها و استثناهای هم‌نام، دوباره تعریف‌شده | داخل `services/carbon/service.py` (خطوط ۴۱–۸۷) | **کد زمان اجرا** |

نتیجه: تست‌ها payloadهای `schemas.py` را می‌فرستند (مثلاً `to_holder_id`/`actor`/`reason`) ولی سرویس انتظار مدل محلی را دارد (`to_holder`/`from_holder`/`holder_id`/`retirement_reason`/`issued_by`/`geometry`) و استثناهایش هم کلاس دیگری‌اند. این دقیقاً همان الگوی «تعریف تکراری قرارداد» است که در `database/models.py` ↔ `database/models/` و `business_modules` هم دیده شد.

**راه‌حل پیشنهادی (تک‌منبع حقیقت):**
1. مدل‌های محلی `service.py` حذف و از `services.carbon.schemas` import شوند.
2. فیلدهای لازم سرویس که در `schemas.py` نیستند به‌صورت **اختیاری** اضافه شوند: `geometry`, `baseline_activity`, `issued_by`, `from_holder`, `amount`, `to_holder`, `holder_id`, `retirement_reason`.
3. استثناهای سرویس با استثناهای `schemas.py` یکسان شوند (تست‌ها همان‌ها را catch می‌کنند).
4. سپس `pytest services/carbon/tests -q` سبز شود (خارج از دامنهٔ Wave 1 نگه داشته شد چون تغییر معنای تجاری «انتقال کامل در برابر انتقال جزئی» است و تصمیم محصولی می‌خواهد).

---

## ۴. کارهای باقی‌مانده (به ترتیب اولویت)

1. **یکسان‌سازی قرارداد carbon** (بند ۳) → آخرین ۳۱ تست قرمز.
2. **۱۷ روتر ثبت‌نشده** در gateway: `audit, compliance, lms, motors, ogc_router, security_router, tourism_router, economy, ecosystem, climate, carbon_engine, content_public, lab, supabase_proxy, hydroma_common, ai_advice_router` (+ نگهبان ضدرگرسیون).
3. **حذف تکراری‌ها:** `services/business_modules`، `database/models/database_models.py` (یتیم)، و مدل‌های هم‌نام declarative (`ContractVersionModel`, `ComputeJob`).
4. **RTL واقعی:** `app/layout.tsx` هنوز `<html lang="fa" dir="rtl">` سخت‌کد دارد → باید per-locale شود.
5. **تست‌های فرانت‌اند:** صفر تست وجود دارد در حالی که `test`/`test:e2e` تبلیغ می‌شود (vitest + playwright).
6. **Alembic:** دو `merge_heads` → یک زنجیرهٔ خطی.
7. **ممیزی حقیقت اسناد:** اصلاح درفت `frontend/` → `apps/web` در README و `docs/11`.

---

## ۵. فرمان‌های بازتولید

```powershell
# بک‌اند
D:\eco_nojin\.venv\Scripts\python.exe -m pytest -q
# → 31 failed, 255 passed, 0 errors   (همهٔ ردها در services/carbon/tests)

# فرانت‌اند
cd D:\eco_nojin\apps\web
& ..\..\node_modules\.bin\tsc.CMD --noEmit -p tsconfig.json   # → exit 0
& .\node_modules\.bin\next.CMD build                          # → exit 0 (Compiled successfully)

# API
D:\eco_nojin\.venv\Scripts\python.exe -c "from services.api_gateway.main import app; print(len(app.openapi()['paths']))"  # → 437
```
