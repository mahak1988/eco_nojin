# درخواست قرارداد — ۳۷ مسیر مصرف‌شده در کد که endpoint ندارند

**تاریخ:** ۲۰۲۶/۰۹/۲۸ · **منبع:** `scripts/check-api-contract.mjs --json` → `docs/frontend/contract-gaps.json`
**وضعیت سنجش:** ۵۰۳ مسیر مصرف‌شده · ۴۶۴ تطبیق · ۲ مسیر پویا (قابل راستی‌آزمایی استاتیک نیست) · **۳۷ شکاف**
**رابطه با اسناد دیگر:** این سند مکمل `CONTRACT_REQUEST_154.md` است (آن سند مسیرهای کاتالوگ را می‌پوشاند؛ این سند مسیرهایی را که **کد امروز صدا می‌زند**).

---

## ۱) نکتهٔ کلیدی: ۳۰ از ۳۷ از یک ماژول می‌آید

| ماژول مصرف‌کننده | تعداد شکاف |
|---|---|
| `apps/web/src/lib/api/public.ts` | **۳۰** |
| `lib/api/cart.ts` + `lib/api/escrow.ts` | ۱ (`/api/v1/marketplace`) |
| `lib/api/manual.ts` | ۱ |
| `lib/workspaces/registry.ts` | ۱ (`/api/v1/security/status`) |
| صفحه‌ها (`market/wallet`، `hydroma/farms`، `public/education/*`) | ۴ |
| `packages/api-client/src/generated.ts` | ۱ (`/api/v1/soil`) |

یعنی یک تصمیم واحد روی `lib/api/public.ts` می‌تواند ۳۰ شکاف را ببندد.

---

## ۲) دسته‌بندی و پیشنهاد تعیین‌تکلیف

### الف) محتوای ثابت — endpoint لازم نیست (۲۴ مسیر)
این‌ها نباید endpoint داده بگیرند؛ باید صفحهٔ محتوایی `static` و **indexable** شوند (نیازمند افزودن وضعیت `static` به قاعدهٔ کاتالوگ).

| خوشه | مسیرها | مصرف‌کننده | تعیین‌تکلیف |
|---|---|---|---|
| معرفی اجزا | `/api/v1/public/components` و ۸ زیرمسیر (api-playground، dispute-resolution، ecowallet، hydroma-engine، land-profiler، marketplace، mrv-dashboard، satellite-view) | `lib/api/public.ts` | `static` — متن معرفی از کد/محتوا |
| سیاست‌ها | `/policy/{accessibility,cookies,governance,licensing,privacy,terms}` | `lib/api/public.ts` | `static` — متن حقوقی از `content_items` |
| علم و شواهد | `/science/{data-sources,evidence-base,methodology,reproducibility,uncertainty,validation}` | `lib/api/public.ts` | `static` |
| قرارداد API | `/public/api/schema`، `/public/api/endpoints` | `lib/api/public.ts` | از `openapi.json` **تولید** شود، نه endpoint |

### ب) نیازمند قرارداد واقعی (۱۱ مسیر)

| مسیر | مصرف‌کننده | جدول مرتبط در دیتابیس | پیشنهاد |
|---|---|---|---|
| `/api/v1/ecowallet` | `market/wallet/page.tsx` | `ecowallet` (موجود) | قرارداد کیف پول (موجودی/تراکنش) |
| `/api/v1/farms` | `hydroma/farms/page.tsx` | `farms` (موجود، ۰ رکورد) | قرارداد مزارع |
| `/api/v1/manual` | `lib/api/manual.ts` | `data/manual/eco_manual_v1.sqlite` | قرارداد دادهٔ دستی |
| `/api/v1/marketplace` | `lib/api/cart.ts`, `lib/api/escrow.ts` | `com_order`, `escrow_records` | یا به `/marketplace/stats` نگاشت شود یا قرارداد ریشه |
| `/api/v1/security/status` | `lib/workspaces/registry.ts` | `audit_event`, `admin_audit_logs` | **وضعیت: بدون قرارداد** — در `openapi.json` منتشر نشده و معادل منتشرشده‌ای ندارد؛ mount امنیتی در درخت کاری در جریان است (هنوز کامیت/منتشر نشده) و دروازهٔ در حال اجرا آن را ۴۰۴ می‌دهد؛ اقدام پیشنهادی: پس از استقرار mount و بازتولید `openapi.json` (خارج از دامنهٔ فایلی عامل ۱) یا اقدام عامل مالک `lib/workspaces/registry.ts`. (اجرای عامل ۱ — ۲۰۲۶/۰۹/۲۹) |
| `/api/v1/lms/courses` | `public/education/courses` | `content_items` | **وضعیت: صفحه static شد** — ۲۰۲۶/۰۹/۲۸ در فهرست «محتوای اعلام‌شده» (`contract-allowlist.json`) ثبت شد؛ endpoint لازم ندارد (صفحه بدون fetch واقعی است). (اجرای عامل ۱ — ۲۰۲۶/۰۹/۲۸) |
| `/api/v1/public/education/*` (certifications, courses, video, videos, workshops, video/{id}) | `lib/api/public.ts` + ۳ صفحه | `content_items` | محتوا از جدول موجود یا `static` |
| `/api/v1/public/policy/{param}/versions` | `lib/api/public.ts` | `content_versions` (موجود) | **وضعیت: از کد حذف شد** — تابع `policy.versions` مصرف‌کننده‌ای در کل مخزن نداشت و معادل کامل منتشرشده هم ندارد (`/api/v1/legal-texts/{locale}/{slug}/versions` فقط فرادادهٔ نسخه برمی‌گرداند و برای accessibility/licensing/governance خارج از VALID_SLUGS خطا می‌دهد)؛ فراخوانی بلامصرف از `public.ts` حذف شد. اگر آینده به تاریخچهٔ نسخه نیاز بود: ابتدا قرارداد نسخه‌های متن حقوقی بر پایهٔ `content_versions` منتشر شود، سپس binding بازگردانده شود. (اجرای عامل ۱ — ۲۰۲۶/۰۹/۲۸) |
| `/api/v1/soil` | `generated.ts` | — | نگاشت اشتباه؛ در دروازه `/api/v1/soil/` و `/soil/analyze` هست → بازبینی لازم |

---

## ۳) معیار پذیرش (تا `missing` صفر شود)

| # | معیار |
|---|---|
| ۱ | برای هر مسیر یکی از سه وضعیت ثبت شود: «قرارداد منتشر شد» / «از کد حذف شد» / «صفحه `static` شد» |
| ۲ | `node scripts/check-api-contract.mjs --json` → `missingPaths = 0` |
| ۳ | پس از آن، گیت به `pnpm quality` و CI به‌صورت **بلاک‌کننده** اضافه شود |
| ۴ | هیچ مسیری بدون یکی از این سه وضعیت باقی نماند |

---

## ۴) مسیرهای پویا (اطلاعی، نه شکاف)

| مسیر | فایل | توضیح |
|---|---|---|
| `/api/v1/{param}/health` | `app/[locale]/system/page.tsx` | از قالب رشته ساخته می‌شود |
| `/api/{param}{param}` | `app/api/[...path]/route.ts` | خود BFF |

---

## به‌روزرسانی ۲۰۲۶/۰۹/۲۸ — از ۳۷ به ۲

### کاهش با اصلاح دقت گیت (۳۷ → ۹)
| مورد | علت | تعداد |
|---|---|---|
| ثابت‌های پیشوندی (`MARKETPLACE_BASE`, `MANUAL_BASE`) | این‌ها endpoint نیستند؛ مسیر واقعی در فراخوانی‌های درون‌یابی‌شده است | ۳ |
| تفاوت اسلش پایانی (`/api/v1/soil/` در برابر `/api/v1/soil`) | نرمال‌سازی دوطرفه در گیت | ۱ |
| موارد اعلام‌شدهٔ قبلی (components/policy/science/api) | محتوای ثابت | ۲۳ |

### کاهش با تصمیم محصولی (۹ → ۲)
هفت مسیر آموزش (`public/education/*` و `lms/courses`) به فهرست «محتوای اعلام‌شده» اضافه شدند: محتوای آموزشی از لایهٔ محتوای خود اپ می‌آید، نه از یک منبع API.
`docs/frontend/contract-allowlist.json` اکنون ۳۰ مسیر اعلام‌شده دارد.

### شکاف واقعی باقی‌مانده (نیازمند قرارداد)
| مسیر | مصرف‌کننده | جدول مرتبط در دیتابیس | اقدام پیشنهادی |
|---|---|---|---|
| `/api/v1/public/policy/{param}/versions` | `lib/api/public.ts` | `content_versions` (موجود) | **از کد حذف شد** — binding بلامصرف حذف شد (اجرای عامل ۱ — ۲۰۲۶/۰۹/۲۸)؛ دیگر شکاف نیست |
| `/api/v1/security/status` | `lib/workspaces/registry.ts` | `audit_event`, `admin_audit_logs` | انتشار قرارداد — mount امنیتی در درخت کاری در جریان است (کامیت‌نشده)؛ پس از استقرار و بازتولید `openapi.json` این مسیر از `missing` خارج می‌شود — خارج از دامنهٔ فایلی عامل ۱. (اجرای عامل ۱ — ۲۰۲۶/۰۹/۲۹) |

### وضعیت گیت پس از اصلاحات
```
published paths : 489
used paths      : 500
matched         : 466
dynamic         : 2
declared content: 30
missing         : 2      ← از ۳۷
```

### بهروزرسانی ۲۰۲۶/۰۹/۲۸ (اجرای عامل ۱) — از ۲ به ۱

`/api/v1/public/policy/{param}/versions` از «بدون قرارداد» به «از کد حذف شد» تغییر وضعیت داد: تابع `policy.versions` در `lib/api/public.ts` هیچ مصرف‌کننده‌ای در کل مخزن نداشت و معادل کامل منتشرشده نیز ندارد؛ فراخوانی بلامصرف حذف شد (روش ۲ از سه روش مجاز هدف). در صورت نیاز آینده به تاریخچهٔ نسخه‌های متن حقوقی، ابتدا قرارداد بر پایهٔ `content_versions` منتشر شود و سپس binding بازگردانده شود.

```
published paths : 489
used paths      : 499
matched         : 466
dynamic         : 2
declared content: 30
missing         : 1      ← از ۳۷
```

شکاف واقعی باقی‌مانده: `/api/v1/security/status` (مصرف‌کننده: `lib/workspaces/registry.ts` — خارج از دامنهٔ فایلی عامل ۱؛ نیازمند انتشار قرارداد وضعیت امنیتی یا اقدام عامل مالک آن فایل).

### به‌روزرسانی ۲۰۲۶/۰۹/۲۹ (اجرای عامل ۱) — پردازش تنها مسیر باقی‌ماندهٔ `missing` (بدون تغییر عدد)

`/api/v1/security/status` (مصرف‌کننده: `lib/workspaces/registry.ts`) طبق «الگوریتم هر اجرا» پردازش شد:

- **معادل منتشرشده: ندارد.** فهرست کامل ۴۸۹ مسیر `openapi.json` برای معادل بازبینی شد؛ نه در خوشهٔ `security` و نه در `health`/`status` مسیر هم‌ارزی وجود ندارد.
- **یافتهٔ تازه:** mount امنیتی در کد درخت کاری در جریان است (`services/api_gateway/routers/security_router.py` و `main.py` — کامیت‌نشده، آخرین ویرایش ۲۰۲۶/۰۹/۲۸)؛ اما در وضعیت فعلی (۱) در `openapi.json` منتشر نشده و (۲) نمونهٔ در حال اجرای دروازه (پورت ۸۰۰۰) آن را سرو نمی‌کند (`GET /api/v1/security/status` → ۴۰۴). آزمون e2e در `testing_lab/integration_tests/test_e2e.py` انتظار پاسخ ۲۰۰ از این مسیر را ثبت کرده است.
- **اقدام این اجرا:** ثبت «وضعیت: بدون قرارداد» + اقدام پیشنهادی در همین سند؛ بازنویسی/حذف فراخوانی ممکن نبود — مصرف‌کننده خارج از دامنهٔ فایلی عامل ۱ است و مورد از جنس «محتوای ثابت» (allowlist) نیست.
- **پیشنهاد:** پس از استقرار کد mount امنیتی و بازتولید `openapi.json` از دروازه، گیت بدون هیچ تغییر فرانت‌اند به `missing = 0` می‌رسد؛ تا آن زمان نیازمند اقدام بک‌اند/ناشر قرارداد است (خارج از دامنهٔ فایلی عامل ۱).

وضعیت گیت این اجرا: `missing` ۱ → ۱؛ `pnpm -C apps/web type-check` → exit 0.
