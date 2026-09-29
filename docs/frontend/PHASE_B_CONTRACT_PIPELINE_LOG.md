# گزارش اجرای فاز B — خط لولهٔ قرارداد

**تاریخ اجرا:** ۲۰۲۶/۰۹/۲۸ · **پیش‌نیاز:** `PHASE_A_EXECUTION_LOG.md`
**دامنه:** B1 بازتولید قرارداد · B2 کلاینت تایپ‌شده · B3 گیت قرارداد · B4 پیگیری شکاف

---

## ۱) نتیجهٔ یک‌نگاهه

| گام | وضعیت | شاهد |
|---|---|---|
| ادغام headهای مهاجرت | ✅ | تک‌head `b3e09e91d6f3` |
| B1 بازتولید `openapi.json` از دروازهٔ زنده | ✅ | ۴۸۲ → **۴۸۹ مسیر** (۷ افزوده، ۰ حذف) |
| B2 تولید کلاینت Orval | ✅ | `packages/api-client/src/generated.ts` — **۶۷٬۱۶۱ خط** |
| B2-b سبز کردن `type-check` | ✅ | سه خطای تایپ در یک تست تازه رفع شد → exit 0 |
| B3 گیت قرارداد (تازه ساخته شد) | ✅ اجرا شد | **۴۶۴ تطبیق / ۳۹ شکاف** |
| B4 پیگیری شکاف | 🔎 فهرست‌شده | ۳۸ endpoint وجود ندارد (404)، ۱ نیازمند احراز (401) |

---

## ۲) کارهای انجام‌شده و شواهد

### ۲.۱ ادغام گراف مهاجرت
پیش از این دو head وجود داشت و `alembic upgrade head` کار نمی‌کرد.
```
$ alembic merge heads -m "merge webauthn and engine result heads"
Generating alembic/versions/b3e09e91d6f3_merge_webauthn_and_engine_result_heads.py ... done
$ alembic upgrade head   →  b3e09e91d6f3 (head) (mergepoint)
```
فایل تازه: `alembic/versions/b3e09e91d6f3_merge_webauthn_and_engine_result_heads.py`

### ۲.۲ بازتولید `openapi.json` (B1)
مقایسهٔ فایل مخزن با دروازهٔ زنده:
| سنجه | مقدار |
|---|---|
| مسیر زنده | **۴۸۹** |
| مسیر مخزن | ۴۸۲ |
| افزوده | ۷ |
| حذف‌شده | ۰ |
| عملیات (با متد) | ۵۴۶ = GET 277 · POST 232 · PUT 15 · DELETE 17 · PATCH 5 |

هفت مسیر افزوده، همه از قابلیت تازهٔ اسپانسر:
```
/api/v1/sponsors
/api/v1/sponsors/slot
/api/v1/admin/sponsors
/api/v1/admin/sponsors/{sponsor_id}/activate
/api/v1/admin/sponsors/{sponsor_id}/green-review
/api/v1/admin/sponsors/{sponsor_id}/suspend
/api/v1/admin/sponsors/{sponsor_id}/terminate
```
پشتیبان: `openapi.json.bak-20260928`

### ۲.۳ تولید کلاینت تایپ‌شده (B2)
`packages/api-client/src/generated.ts` از ۴۸۹ مسیر بازتولید شد (۶۷٬۱۶۱ خط، ۲٫۸۹MB) و انواع تازهٔ اسپانسر (`SponsorTier`, `SponsorshipCreate`, `SponsorshipOut`, …) در آن هست.

### ۲.۴ رفع خطای تایپ
`apps/web/src/lib/domains/list-unclaimed.test.ts` سه خطای ضمنی `any` داشت:
```ts
// قبل
function walk(dir, acc = []) {
// بعد
function walk(dir: string, acc: string[] = []): string[] {
```
پس از اصلاح: `tsc --noEmit` → **exit 0**. پشتیبان: همان فایل با پسوند `.bak-20260928`.

---

## ۳) گیت قرارداد (B3) — تازه ساخته شد

**فایل:** `scripts/check-api-contract.mjs`
**کار:** هر مسیر `/api/...` که کد فرانت‌اند مصرف می‌کند باید در `openapi.json` منتشر شده باشد (با نرمال‌سازی `{param}` و `${...}`). مسیرهای داخلی خود BFF (`/api/auth/*`, `/api/observability/*`, `/api/csp-report`) و مسیر دموی design-system استثنا شده‌اند.

**نتیجهٔ اجرا:**
```
published paths : 489
used paths      : 503
matched         : 464
missing         : 39        ← exit 1
```

### ۳.۱ سی و نه شکاف: آزمون زنده روی دروازه
هر شکاف روی دروازهٔ زنده آزمایش شد:

| خوشه | تعداد | وضعیت زنده | خوانش |
|---|---|---|---|
| `/api/v1/public/components/*` | ۹ | **404** | endpoint وجود ندارد |
| `/api/v1/public/education/*` | ۶ | **404** | endpoint وجود ندارد |
| `/api/v1/public/policy/*` | ۴ | **404** | endpoint وجود ندارد |
| `/api/v1/public/api/schema`, `/endpoints` | ۲ | **404** | endpoint وجود ندارد |
| `/api/v1/ecowallet`, `/marketplace`, `/manual`, `/lms/courses` | ۴ | **404** | endpoint وجود ندارد |
| `/api/v1/farms` | ۱ | **401** | وجود دارد ولی نیازمند نشست |
| بقیه (تک‌موردی) | ۱۳ | 404 | endpoint وجود ندارد |

**نتیجهٔ مهم (بر پایهٔ ۹ آزمون شاخص):** این‌ها «قرارداد منتشرنشده» نیستند؛ endpointهایشان روی دروازهٔ زنده نیست (۸ مورد ۴۰۴ و ۱ مورد ۴۰۱). یعنی صفحه‌هایی مانند `/public/education/courses` و `/market/wallet` داده‌ای برای گرفتن ندارند و باید یا در بک‌اند ساخته شوند یا از کاتالوگ خارج/`noindex` شوند.

> این فهرست مکمل `docs/frontend/CONTRACT_REQUEST_154.md` است: آن سند مسیرهای کاتالوگ را می‌پوشاند، این گیت مسیرهای **مصرف‌شده در کد** را.

### ۳.۲ توصیهٔ استقرار گیت
الان گیت `exit 1` می‌دهد؛ اگر همین حالا به `pnpm quality` و CI اضافه شود، CI را قرمز می‌کند. مسیر پیشنهادی:
1. **اکنون:** اجرای دستی/گزارشی (`node scripts/check-api-contract.mjs`).
2. **پس از بستن ۳۹ شکاف:** افزودن به `quality` و CI به‌صورت بلاک‌کننده.

---

## ۴) گام بعدی

| # | کار | معیار |
|---|---|---|
| B4-ب | تحویل ۳۹ شکاف به‌عنوان خوشه به بک‌اند (یا حذف/noindex) | عدد `missing` به صفر برسد |
| B4-پ | افزودن گیت قرارداد به CI پس از بسته‌شدن شکاف | `pnpm quality` شامل گیت |
| A4-ب | اجرای کامل ۱۹ اسپک Playwright روی پنج project | ثبت نتیجهٔ هر اسپک |
| C | اتصال سطح‌به‌سطح با جدول «جدول دیتابیس → endpoint → صفحه» | هر سطح با داده یا حالت خالی صادقانه |
