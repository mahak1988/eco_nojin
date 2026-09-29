# برنامه اقدامات لازم — داشبورد فرانت‌اند Eco Nojin

**تاریخ سنجش:** 2026-09-26
**مبنا:** `FRONTEND_MASTER_STATUS_FA_2026-09-26.md` (HEAD = `5d8e98b`)
**روش:** هر عدد این سند امروز دوباره اندازه‌گیری شده است. هیچ عددی از داشبورد نقل نشده مگر آنکه با فرمان بازتولید شده باشد.

---

## ۱) خلاصه اجرایی

داشبورد یک تصویر «سبز» از وضعیت می‌دهد، اما اندازه‌گیری مجدد نشان می‌دهد **بخش قابل توجهی از اعداد داشبورد منسوخ یا نادرست است** و دو دروازه کلیدی عملاً قابل استناد نیستند:

| یافته | وضعیت | اثر |
|---|---|---|
| کیفیت کد (`quality`) | ✅ سبز واقعی | ۴۱۲ فایل، ۲۶۷ تست در ۳۷ فایل، ۱۴ locale، site-URL guard |
| `build` | ✅ سبز واقعی | exit 0، ولی فقط ۱ صفحه HTML تولید شد |
| `check-verified-claims` | ✅ سبز واقعی | ۰ ادعای تأییدنشده |
| **E2E (Playwright)** | ⛔ **غیرقابل اجرا** | مرورگر Playwright نصب نیست؛ هر ۳۴ تست با خطای محیطی رد شد |
| **آمار داشبورد** | ⛔ **نادرست** | ۶ عدد کلیدی با اندازه‌گیری واقعی نمی‌خواند |
| **R-1 / R-2 / R-3** | ✅ **قابل بستن با اعداد موجود** | join rule واقعی استخراج شد |

**نتیجه‌گیری:** کد سالم است؛ **گزارش** نیاز به اصلاح دارد. اولویت اول، اصلاح سنجش و مستندسازی است، نه نوشتن صفحه جدید.

---

## ۲) مغایرت‌های داشبورد (ادعا در برابر اندازه‌گیری)

| # | ادعای داشبورد | اندازه‌گیری واقعی | فرمان بازتولید |
|---|---|---|---|
| M-1 | ۲۱۸ فایل `page.tsx` | **۲۱۹** = ۲۱۷ routable (شامل root) + ۱ `_not-found` + ۱ `(catalog)/[...slug]` | `Get-ChildItem -LiteralPath 'apps/web/src/app/[locale]' -Recurse -Filter page.tsx -File` |
| — | «۲۱۶ routable + root + not-found» | ۲۱۷ routable شامل root؛ عدد ۲۱۸ یک `page.tsx` را جا انداخته بود | همان |
| — | ۱۳۲ `live` + ۵۹ `capability` | **۱۸۳ `live` + ۸ `capability`** (جمع ۱۹۱ = همان ۱۹۱ indexable، پس فقط تفکیک جابه‌جا شده) | `CATALOG_STATUS_TOTALS` در `page-catalog.ts:7480` |
| — | ۲۱۹ فایل در build / ۱۳ صفحه static | درست، ولی این **پوشش نیست**: ۲۲۸ مسیر `ƒ (Dynamic)` و فقط **۱** فایل HTML | `apps/web/.next/server/app/**/*.html` |
| — | ۶۷ تست Playwright سبز | **۰ تست قابل اجرا** — مرورگر نصب نیست | `pnpm exec playwright install chromium` |
| — | ۱۴۴ تغییر unstaged | **۱۳۲** (۸۲ `M`، ۹ `D`، ۴۱ `??`) — عمدتاً مالکیت stream دیگر | `git status --porcelain` |
| — | «main جلوتر از origin» | درست: **۱۷ جلو، ۰ عقب** | `git rev-list --left-right --count origin/main...main` |

**تفکیک سطح صفحات (اندازه‌گیری امروز، بدون تغییر):** `market 74` · `public 62` · `workspace 17` · `admin 9` · `developers 9` · `ai 8` · `trust 7` · `system 4` · `research 2` · `hydroma 2`

---

## ۳) یافته‌های جدید که در داشبورد ثبت نشده‌اند

### F-1 — `generateStaticParams` در مسیر کاتالوگ بی‌اثر است ⛔

`apps/web/src/app/[locale]/(catalog)/[...slug]/page.tsx:12` دارای `export const dynamic = 'force-dynamic'` است، در حالی که `generateStaticParams()` در خط ۳۱ مقدار `catalogFallbackParams()` (۲۸۲ مسیر) را برمی‌گرداند. با `force-dynamic` هیچ‌کدام prerender نمی‌شوند.

شاهد: `prerender-manifest.json` شامل `dynamicRoutes: 0` و فقط ۶ ورودی (که همه asset هستند)، و در `.next/server/app` فقط `_not-found.html` وجود دارد.

**معنا:** از ۶۰۰ مسیر منطقی، **صفر مسیر** شواهد زمان‌ساخت دارد. هر ۶۰۰ مسیر فقط در زمان اجرا رندر می‌شوند.

### F-2 — سه orphan واقعی، که یکی از آنها پنهان است ⚠️

ابزار سنجش (`scanRouteFiles` در `page-catalog.test.ts:29` و اسکریپت بازتولید) هر دایرکتوری به نام `api` را کنار می‌گذارد. نتیجه: مسیر واقعی `apps/web/src/app/[locale]/developers/api/page.tsx` هرگز scan نمی‌شود.

سه مسیر فیزیکی بدون جایگاه در کاتالوگ:
1. `/admin/system/health` — تأییدشده
2. `/workspace/operations/health` — تأییدشده
3. `/developers/api` — استنتاج‌شده؛ با اصلاح scanner تأیید می‌شود

این یافته، ادعای «۸۲ مسیر بدون جایگاه» را باطل می‌کند (این ادعا متعلق به پیش از `b03dec5` بوده است).

### F-3 — پوشش واقعی ۶۰۰ مسیر فقط از راه build قابل اثبات نیست

۲۲۸ مسیر `ƒ` یعنی هیچ مسیر فیزیکی‌ای خروجی HTML ندارد. برای استدلال «صفحه زنده است»، شاهد فعلی فقط وجود فایل و وجود endpoint است — نه رندر.

### F-4 — i18n: «۱۴ locale برابر» اما ۱۲ locale به fallback تکیه می‌کنند ⚠️

خروجی `i18n:compile`:
- `en` و `fa`: ۶۸۴ کلید مستقل
- ۱۲ locale دیگر: ۲۸۵ کلید مستقل، ۷۳۵ مؤثر

یعنی حدود ۴۵۰ کلید در ۱۲ زبان ترجمه نشده و از fallback می‌آید. ستون ۱۱ چک‌لیست باید `partial: n/14` را گزارش کند، نه `14/14`.

### F-5 — `444` یک اعلان cardinality است، نه ۴۴۴ صفحه

`marketplace-routes.ts` هیچ فهرست مسیری ندارد؛ فقط `count` per group دارد (جمع = ۴۴۴). مسیرها در زمان اجرا از الگوی `{base}/{prefix}-{n}` ساخته و با `force-dynamic` رندر می‌شوند. این‌ها صفحه محتوایی نیستند.

### F-6 — دروازه E2E در این ماشین شکسته است ⛔

```
Error: browserType.launch: Executable doesn't exist at
...\ms-playwright\chromium_headless_shell-1243\chrome-headless-shell.exe
```

سرور وب بالا آمد (پس build سالم است)؛ فقط binary مرورگر نیست. یا `pnpm exec playwright install chromium` یا استفاده از `PLAYWRIGHT_CHANNEL=msedge` (در `playwright.config.ts:4` پشتیبانی می‌شود).

---

## ۴) بستن reconciliations با اعداد واقعی

### R-1 — join rule واقعی (بسته می‌شود)

فرمول صحیح، جایگزین `218 + 444 = 662`:

```
۶۰۰ مسیر منطقی
├── ۲۶۵ دارای routeFile واقعی        → renderedBy = 'route'
└── ۳۳۵ بدون routeFile
    ├── ۲۸۲ → catalog catch-all
    └── ۵۳  → marketplace catch-all
```

۲۱۶ مسیر فیزیکی اسکن‌شده → **۲۱۴ پوشش‌داده‌شده** توسط کاتالوگ و ۲ orphan. مسیر هفدهم (`/developers/api`) به‌دلیل نقطه کور اسکریپت (F-2) اصلاً اسکن نشده و پس از WP-02 تعیین تکلیف می‌شود.
اختلاف ۲۶۵ در برابر ۲۱۴ یعنی ۵۱ مسیر منطقی با یک route داینامیک (مثل `{id}`) اشتراک دارند — این توضیح‌پذیر است، نه خطا.

**`444` در این معادله جایی ندارد**؛ کلاس cardinality متفاوتی است (فضای آدرس تمپلیت). ترکیب آن با تعداد صفحه فیزیکی از پایه غلط بود.

### R-2 — باکت‌های marketplace (بسته می‌شود)

هر **۷۴** صفحه فیزیکی market در کاتالوگ bind شده‌اند (صفر orphan در market). ارقام `10+14+22+27=73` اعلان‌های منسوخ‌اند. ارقام صحیح از کاتالوگ:

```
۱۲۷ مسیر منطقی marketplace = ۷۴ route-backed + ۵۳ marketplace-catchall
```

### R-3 — orphanها (بسته می‌شود)

۳ orphan به‌جای ۸۲ مسیر. `B11` با اصلاح F-2 بسته می‌شود.

### R-4 — مرز `live` / `capability` (همچنان باز، فقط سندی)

سندهای سطح از `live-partial` استفاده می‌کنند و کاتالوگ `capability`. یک پاراگراف نگاشت در `MARKETPLACE_IMPLEMENTATION.md` و `PUBLIC_PAGES_EXECUTION.md` لازم است.

---

## ۵) بسته‌های کاری (به ترتیب اجرا)

هر بسته دامنه محدود، خروجی مشخص و دروازه مشخص دارد. ترتیب الزامی است.

### WP-01 — بازگرداندن دروازه E2E ⛔ اولویت ۱
- **دامنه:** فقط محیط ماشین. هیچ فایل مخزنی تغییر نمی‌کند.
- **اقدام:** `pnpm exec playwright install chromium` (یا `PLAYWRIGHT_CHANNEL=msedge`).
- **خروجی:** اجرای واقعی `tier0` + `a11y` + `responsive` و ثبت نتیجه.
- **دروازه:** هر ۳۴ تست سبز، یا فهرست خطاهای واقعی محصول.
- **وابستگی:** هیچ. همین حالا قابل اجرا.

### WP-02 — رفع نقطه کور ابزار سنجش ⛔ اولویت ۱
- **دامنه:** `apps/web/src/lib/domains/page-catalog.test.ts:29` فقط.
- **اقدام:** شرط `item.name === 'api'` را حذف یا به `api` زیر `app/api` محدود کن، طوری که `developers/api` scan شود.
- **خروجی:** تست، orphan سوم را گزارش کند.
- **دروازه:** `pnpm --dir apps/web test src/lib/domains/page-catalog.test.ts`.
- **چرا اول:** تا این اصلاح نشود، هر عدد پوشش در WP-03 مشکوک است.

### WP-03 — بستن R-1 و R-3 در کاتالوگ
- **دامنه:** `page-catalog.ts` (فقط در صورت نیاز به سه ورودی جدید) + `page-catalog.test.ts` + `PAGE_CHECKLIST_600.md`.
- **اقدام:**
  1. برای هر ۳ orphan یا ورودی کاتالوگ بساز، یا صریحاً «خارج از کاتالوگ» اعلام کن با دلیل.
  2. بند «join rule» را با فرمول بخش ۴ جایگزین کن.
  3. `B11` را با شواهد جدید ببند.
- **دروازه:** تست کاتالوگ + تست route-manifest سبز؛ `M-1` به ۲۱۹/۲۱۷ اصلاح شود.

### WP-04 — بازاستخراج باکت‌های marketplace (R-2)
- **دامنه:** `MARKETPLACE_IMPLEMENTATION.md` + `PAGE_CHECKLIST_600.md` بخش ۵.۲.
- **اقدام:** ارقام `10/14/22/27` را با `۷۴ route-backed + ۵۳ catchall` جایگزین کن. سطر `0/444/444` را به `0/53/53` اصلاح و ۴۴۴ را به‌عنوان اعلان فضای آدرس علامت‌گذاری کن.
- **دروازه:** `git diff --check -- docs`؛ هیچ عدد بدون فرمان بازتولید.

### WP-05 — نگاشت R-4 در اسناد مالک
- **دامنه:** فقط `docs/frontend/MARKETPLACE_IMPLEMENTATION.md` و `PUBLIC_PAGES_EXECUTION.md`.
- **اقدام:** یک پاراگراف نگاشت `live-partial → capability` با تعریف دقیق.
- **دروازه:** بازبینی docs؛ بدون تغییر کد.

### WP-06 — تصمیم و اصلاح تعارض prerender (F-1 و B10)
- **دامنه:** `(catalog)/[...slug]/page.tsx` و در صورت نیاز سیاست سایر مسیرها.
- **تصمیم لازم از مالک:** یکی از دو گزینه، صریح و مکتوب:
  - **گزینه الف:** `force-dynamic` را بردارید تا ۲۸۲ مسیر prerender شوند (هزینه: زمان build بالا می‌رود).
  - **گزینه ب:** `generateStaticParams` را حذف کنید و صادقانه ثبت کنید که این ۲۸۲ مسیر فقط on-demand رندر می‌شوند.
- **قاعده سخت:** وضعیت فعلی (داشتن هر دو) بدترین حالت است، چون وانمود می‌کند شاهد زمان‌ساخت وجود دارد.
- **دروازه:** `pnpm --dir apps/web build` و بررسی مجدد `prerender-manifest.json` و شمار فایل‌های HTML.

### WP-07 — گزارش صادقانه i18n (F-4)
- **دامنه:** ستون ۱۱ چک‌لیست + در صورت تصمیم مالک، فایل‌های `messages/*.json`.
- **اقدام:** برای گروه‌هایی که fallback دارند `partial: 12/14` بنویسید، نه `14/14`. یا ترجمه را کامل کنید، یا وضعیت را صادقانه گزارش کنید.
- **دروازه:** `pnpm --dir apps/web i18n:compile`.

### WP-08 — اجرای دروازه نهایی و ساخت staging manifest
- **دامنه:** فقط گزارش. بدون تغییر کد.
- **فرمان‌ها** (از ریشه، با `workdir` معادل):
  ```
  pnpm --dir apps/web quality
  pnpm --dir apps/web build
  node scripts/check-verified-claims.mjs
  pnpm check:site-url
  pnpm --dir apps/web exec playwright test tests/tier0.spec.ts tests/a11y.spec.ts tests/responsive.spec.ts tests/marketplace-flow.spec.ts --project=chromium
  ```
- **خروجی:** یک فایل manifest با فهرست دقیق commit، فرمان، نتیجه، تاریخ.
- **توجه:** در این محیط `pnpm -C apps/web <script>` برای script‌های تعریف‌شده کار می‌کند، ولی برای subcommandهایی مثل `vitest`/`playwright` باید `--dir` یا `exec` به‌کار رود.

### WP-09 — به‌روزرسانی داشبورد با اعداد درست
- **دامنه:** فقط `FRONTEND_MASTER_STATUS_FA_2026-09-26.md`.
- **اقدام:** جایگزینی ۲۱۸→۲۱۹، ۱۳۲/۵۹→۱۸۳/۸، ۱۴۴→۱۳۲، و افزودن ستون «شاهد امروز». حذف یا اصلاح ادعای سبز بودن E2E.
- **دروازه:** `git diff --check`؛ هر عدد با فرمان بازتولید همراه باشد.

### WP-10 — تصمیم انتشار ⛔ نیازمند تأیید مالک
- هیچ push خودکاری انجام نمی‌شود.
- `main` اکنون **۱۷ commit** جلوتر از `origin/main` است.
- پیش‌شرط: WP-01 تا WP-09 بسته و دروازه‌ها سبز.

---

## ۶) قوانین ایمنی git (الزامی)

```powershell
# هرگز این را اجرا نکنید:
git add .

# فقط مسیرهای صریح:
git add -- docs/frontend apps/web/src/lib/domains

# قبل از هر commit:
git diff --name-only
git diff --cached --check
```

**قلمرو ممنوع:** `engine/`، `services/`، `alembic/`، `database/`، `tests/unit`، `tests/integration`.
این مسیرها در حال حاضر ۹۰+ تغییر unstaged متعلق به stream دیگر دارند (`engine/cpp_core` ۲۸، `engine/hydroma` ۲۶، `tests/unit` ۲۲، `tests/integration` ۱۱). لمس آن‌ها کل `main` را در معرض ریسک قرار می‌دهد.

---

## ۷) خارج از دامنه این برنامه

این موارد به مالکان دیگر تعلق دارد و **در این برنامه انجام نمی‌شود**:

| ID | موضوع | مالک |
|---|---|---|
| B1 | نبود auth صریح در endpoint سفارش‌های marketplace | `marketplace-api` / security |
| B2 | پذیرش user id دلخواه در wallet | `wallet-api` / security |
| B3 | دو مدل escrow متفاوت | `payments-api` |
| B4 | نبود credential در مخزن | `platform-operations` |
| B5 | `REDIS_URL` کلاستر | `platform-operations` |
| B6 | mount نشدن LMS router | `platform-web` |
| B7 | slug حقوقی بدون محتوای منتشرشده | `content-web` |
| B8 | نبود ذخیره نتایج benchmark | `science-web` |
| — | اجرای runbook حاکمیت GitHub | مالک مخزن (نیازمند مجوز admin) |

**نکته:** WP-01 تا WP-09 هیچ‌کدام به این موارد وابسته نیستند و هیچ‌کدام را مسدود نمی‌کنند.

---

## ۸) تعریف پایان

برنامه زمانی کامل است که هر پنج شرط برقرار باشد:

1. `R-1`، `R-2`، `R-3` بسته و در `PAGE_CHECKLIST_600.md` با فرمول و فرمان بازتولید ثبت شده باشد.
2. `R-4` در اسناد مالک نگاشت شده باشد.
3. تصمیم prerender (WP-06) گرفته و در کد اعمال شده باشد — نه به‌صورت تعارض پنهان.
4. هر عدد گزارش‌شده در داشبورد با شاهد امروز جایگزین شده باشد، بدون باقی ماندن عدد منسوخ.
5. دروازه E2E واقعاً اجرا شده و نتیجه‌اش — سبز یا قرمز — ثبت شده باشد.

**قاعده پایانی:** اگر E2E پس از WP-01 قرمز بماند، آن خطاها گزارش می‌شوند و به مالک داده می‌شوند؛ پنهان‌سازی آن‌ها پذیرفته نیست.
