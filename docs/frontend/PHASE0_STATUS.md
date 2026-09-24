# گزارش وضعیت فاز ۰ — پایهٔ فرانتاند واقعی (به‌روزرسانی ۲۰۲۶/۰۹/۲۲)

> وضعیت اجراشدهٔ فاز ۰ برنامهٔ جامع (نسخهٔ ۲٫۰). همهٔ صفحات فقط از بک‌اند و دیتابیس واقعی می‌خوانند؛ هیچ دادهٔ آزمایشی/ساختگی وجود ندارد.

## ۱) بک‌اند — رفع باگ و اتصال به دیتابیس واقعی

**ریشهٔ باگ:** روتر `platform` از Supabase استفاده می‌کرد ولی `SUPABASE_URL` یک مقدار جایگزین (`https://your…`) بود و resolve نمی‌شد؛ در نتیجه `getaddrinfo failed`. دیتابیس واقعی این محیط **SQLite** است (`data/econojin.db`).

**اصلاحات اعمال‌شده در `services/api_gateway/routers/platform.py`:**

| مورد | قبل | بعد |
|---|---|---|
| `GET /platform/landscapes` | ۵۰۰ (Supabase ناسازگار) | ۲۰۰ — خواندن از `land_profiles` واقعی |
| `POST /platform/landscapes` | نوشتن در Supabase | نوشتن در دیتابیس واقعی |
| `GET /platform/stats` | خطا را می‌خورد و صفر برمی‌گرداند (گمراه‌کننده) | شمارش واقعی + فیلد `db_reachable`؛ در خطا مقادیر `null` (بدون جایگزین ساختگی) |
| `GET /platform/health` | «supabase_available» گمراه‌کننده | وضعیت واقعی اتصال دیتابیس (`db_reachable`, `db_backend`) |
| `POST /platform/analyze` | **دادهٔ ساختگی** (NDVI با `np.random`، ضرایب ثابت) | با نگهبان صداقت غیرفعال شد و `503` صادقانه برمی‌گرداند تا به منبع واقعی (Sentinel-2/ERA5) وصل شود |

**نسخهٔ پشتیبان:** `services/api_gateway/routers/platform.py.bak-20260922`

**شواهد زنده (اجرا شده):**
- `/api/v1/platform/health` → `{"status":"operational","db_reachable":true,"db_backend":"sqlite","cpp_available":true}`
- `/api/v1/platform/stats` → `total_landscapes: 3، total_projects: 0، active_projects: 0`
- `/api/v1/platform/landscapes` → ۲۰۰ با ۳ رکورد واقعی

> ⚠️ توجه: سه رکورد موجود در جدول `land_profiles` نام «test» دارند (بازماندهٔ کارهای قبلی). این‌ها رکوردهای **واقعیِ** دیتابیس‌اند و ساختهٔ این Agent نیستند؛ در صورت نیاز باید پاک شوند.

## ۲) کلاینت تایپ‌شدهٔ API (Orval)

- کلاینت کامل از `openapi_schema.json` (۴۴۵ مسیر) تولید شد → `packages/api-client/src/generated.ts` (۲٫۶MB، ۶۰٬۴۹۲ خط).
- پیکربندی اصلاح شد: `client: 'react-query'`، `override.query.version: 5` و `clean: false`.
- فایل‌های mutator/index بازسازی شدند (`packages/api-client/src/mutator.ts`, `index.ts`).
- خطاهای تایپ برطرف شد: `packages/api-client/tsconfig.json` (حذف extends شکسته)، `global.d.ts` برای `Headers`، و mutator ساده‌شده.
- `pnpm -C packages/api-client exec tsc --noEmit` **سبز**.
- پیامد: هر صفحه می‌تواند به‌صورت تایپ‌امن به endpointهای واقعی متصل شود.

## ۳) کاتالوگ ۱۴ زبان

| وضعیت | زبان‌ها |
|---|---|
| کامل (منبع) | `fa`, `en` |
| موج ۰ (ترجمهٔ ماشینی، با برچسب صادقانه) | `ar`, `ur`, `de`, `es`, `fr` |
| اسکلت + fallback به fa | `hi`, `it`, `ms`, `pt`, `ru`, `zh`, `bn` |

قواعد فعال: مسیر پیشوندی `/{locale}/…`، `dir` پویا (fa/ar/ur = RTL)، fallback زنجیره‌ای **locale → en → fa**، عدد محلی‌شده، برچسب صادقانهٔ ترجمهٔ ماشینی.

> 🔧 نکته شناخته‌شده: پرچم `machineTranslated` برایLocaleهای `fa` و `en` در بیلد فعلی همچنان `true` برمی‌گردد (مشکل کش/ماژول سمت سرور Next.js). در حال حاضر Notice در UI برای fa/en نمایش داده می‌شود اگرچه کاتالوگ منبع هستند. این مورد قبل از آغاز فاز ۱ با ری‌استارت سرور تولیدی و/یا بررسی مسیر `loadMessages` حل خواهد شد.

## ۴) برش عمودی ساخته‌شده (همه با دادهٔ واقعی)

| مسیر | محتوا | منبع واقعی |
|---|---|---|
| `/{locale}` | کاور (T01) + شمارنده‌های واقعی | `/platform/stats` |
| `/{locale}/home` | خانهٔ عمومی: آمار، پروفایل‌های زمین، محصولات | `/platform/stats`، `/platform/landscapes`، `/marketplace/products` |
| `/{locale}/hydroma` | موتور علمی: فهرست مدل‌ها + وضعیت هستهٔ C++ | `/hydroma/models`، `/models/cpp-status` |
| `/{locale}/market` | بازارگاه: آمار + ۵ محصول واقعی | `/marketplace/products`، `/marketplace/stats` |
| `/{locale}/status` | وضعیت سامانه + فهرست پروفایل‌های زمین | `/platform/*` |

**دادهٔ واقعی نمایش‌داده‌شده (نمونه):** محصولات «Organic Wheat (Golestan)»، «Nomadic Dairy (Qashqai)»، «Premium Saffron (Khorasan)»؛ مدل‌های «Richards 1D»، «Saint-Venant 1D»، «RUSLE Erosion»، «FAO-56 Penman-Monteith ET0»؛ و پیام صادقهٔ «هستهٔ عددی C++ در دسترس نیست» (DLL ساخته نشده).

## ۵) کیفیت

- `pnpm build` **سبز**؛ ۵ مسیر، همگی **Dynamic** (هر درخواست از بک‌اند زنده).
- `pnpm -C apps/web type-check` **سبز**.
- `pnpm -C packages/api-client exec tsc --noEmit` **سبز**.
- First Load JS ≈ **107KB** (زیر بودجهٔ 200KB).
- آزمایش چندزبانه: `/fa`, `/en`, `/ar`, `/de`, `/zh` روی مسیرهای مختلف همه ۲۰۰.
- `.next` از گیت برداشته شد (`git rm -r --cached apps/web/.next`); بیلدهای تولیدی دیگر در گیت ردیابی نمی‌شوند.

## ۶) گام‌های بعدی (آماده‌سازی برای فاز ۱)

1. اتصال `packages/api-client` (Orval) به خود اپ و مصرف هوک‌های تایپ‌شده در صفحات.
2. انتقال دارایی‌های نسل ۲ (محتوای غنی fa/en، فونت‌های محلی، sitemap/OG، تست‌های Playwright).
3. ساخت کیت پایه (۱۵ کامپوننت) و قالب‌های T02–T12.
4. تکمیل زبان‌های موج ۰ باقیمانده و سپس موج ۱.
5. بازبینی داده: پاک‌سازی رکوردهای «test» و تعریف دادهٔ پایلوت واقعی.
6. حل مشکل پرچم `machineTranslated` برای fa/en (نیاز به ری‌استارت سرور تولیدی یا بازبینی `loadMessages`).

## ۷) اجرا

```bash
# بک‌اند
.venv\Scripts\python -m uvicorn services.api_gateway.main:app --host 127.0.0.1 --port 8000
# فرانت‌اند
cd apps\web && pnpm install && pnpm dev    # http://localhost:3000/fa
```

متغیرها: `API_BASE_URL` (سرور) و `API_PROXY_TARGET` (پروکسی) — پیش‌فرض `http://127.0.0.1:8000`.