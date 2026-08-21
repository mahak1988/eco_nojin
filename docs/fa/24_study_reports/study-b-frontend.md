# گزارش مطالعه فرانتاند پروژه اکو نوژین

**مسیر پروژه:** `D:\eco_nojin\frontend`
**تاریخ مطالعه:** ۲۰۲۶-۰۸-۱۷
**ابزار:** PowerShell (`Get-ChildItem`، `Get-Content -Encoding UTF8`)، Node.js (اسکریپتهای تحلیل)، اجرای واقعی تستها با Vitest
**روش:** بررسی کامل ساختار پوشهها، خواندن فایلهای کلیدی (layout، pages، components، lib، locales، public)، شمارش آماری (کد اسکریپت تحلیل)، اجرای تستها، اسکن encoding و orphan.

---

## ۱) `package.json` — وابستگیها، اسکریپتها، نسخهها

فایل: `D:\eco_nojin\frontend\package.json` — نام `eco-nojin-frontend`، نسخه `0.1.0`، private.

**نکته مهم:** نسخه Next.js **۱۶.۳.۱** است، نه ۱۵. (backup ها نشان میدهند: `package.json.backup` → Next 15.1.6 + i18next + react-i18next؛ `package.json.backup-nextjs16` → next "latest"). بنابراین ارتقای ۱۵ → ۱۶ انجام شده و فایلهای پشتیبان برای rollback نگه داشته شدهاند. React **۱۹.۲.۸** (react و react-dom).

**اسکریپتها** (`scripts`):
- `dev`: `next dev`
- `build`: `next build`
- `start`: `next start`
- `lint`: `eslint . --max-warnings=1000` (یعنی تا ۱۰۰۰ warning بدون fail شدن)

**وابستگیهای production (dependency):**
- Radix UI (۱۸ پکیج): `@radix-ui/react-avatar|checkbox|collapsible|dialog|dropdown-menu|hover-card|label|popover|progress|radio-group|scroll-area|select|separator|slider|switch|tabs|tooltip` — پایه UI kit.
- `next@16.3.1`، `react@^19.2.8`، `react-dom@^19.2.8`
- `@tanstack/react-query@^5.101.4` — مدیریت state سمت سرور
- `@hookform/resolvers@^5.8.0` + `react-hook-form@^7.85.0` + `zod@^4.4.3` — فرم و اعتبارسنجی
- `recharts@^3.10.1` — نمودارها
- `leaflet@^1.9.4` + `react-leaflet@^5.0.0` + `@types/leaflet` — نقشهها
- `framer-motion@^13.1.0` — انیمیشن
- `cmdk@^1.1.1` — Command Palette
- `class-variance-authority@^0.7.1`، `clsx@^2.1.1`، `tailwind-merge@^3.6.0` — استایل
- `lucide-react@^1.31.0` + `react-icons@^5.7.0` — آیکونها (هر دو!)
- `date-fns@^4.4.0`، `html2canvas@^1.4.1` (خروجی تصویر از نمودار)، `sonner@^2.0.8` (toast)
- `@tailwindcss/postcss@^4.3.3` — Tailwind v4

**devDependencies:** `@capacitor/cli@^8.5.0`، `@testing-library/react@^16.3.2` + `jest-dom@^7.0.1`، `eslint@^9.39.5` + `eslint-config-next@^16.3.1`، `jsdom@^30.0.1`، `tailwindcss@^4.3.3`، `typescript@^5`، `vitest@^4.1.10`، `@types/node@^20`.

**مدیریت پکیج:** `packageManager: pnpm@11.4.0`؛ `engines.node >= 18.18.0`.
`.npmrc`: `ignore-scripts=true` + `enable-pre-post-scripts=false` (برای جلوگیری از کامپایل sharp)، `shamefully-hoist=true`، `strict-peer-dependencies=false`. `pnpm-workspace.yaml` هم `allowBuilds.sharp: false`.

**`next.config.js`:** `reactStrictMode: true`، `turbopack: {}` (باندلر پیشفرض Next 16)، `images.unoptimized: true` (عدم استفاده از sharp)، و **`typescript.ignoreBuildErrors: true`** — بدهی تایپی موجود (مستند به W-022 در docs/11_weaknesses_and_fixes.md) را میپوشاند.

**`capacitor.config.ts`:** appId `com.econojin.app`، `webDir: 'out'` (خروجی static export) — ولی در next.config.js `output: 'export'` تنظیم نشده (ناسازگاری).

---

## ۲) ساختار App Router — فهرست کامل مسیرها

کل: **۲۰۶ فایل `page.tsx`**، رجیستری ۱۷۰ مسیر (`lib/site-registry.ts`، auto-generated)، همه ۱۷۰ رجیستری دارای page هستند؛ ۳۶ صفحه خارج از رجیستری. فقط ۲ فایل layout: `app/layout.tsx` (ریشه) و `app/dashboard/layout.tsx` (سایدبار). **هیچ `loading.tsx`، `error.tsx`، `not-found.tsx` وجود ندارد.**

### ریشه و صفحات عمومی
- `app/page.tsx` (۳۰KB — صفحه اصلی، Hero + feature grid ۹ ماژول + آمار، با framer-motion و inline style؛ «client» است)
- `app/pages/page.tsx` — فهرست نقشه سایت همه ۱۷۰ صفحه (گروهبندیشده)
- `app/about/page.tsx`، `app/mission/page.tsx`، `app/contact/page.tsx`، `app/pricing/page.tsx`، `app/donate/page.tsx`، `app/careers/page.tsx`، `app/roadmap/page.tsx`، `app/press/page.tsx`، `app/partners/page.tsx`، `app/events/page.tsx`، `app/webinars/page.tsx`، `app/newsletter/page.tsx`، `app/faq/page.tsx`، `app/help/page.tsx`، `app/support/page.tsx`، `app/search/page.tsx` (جستجوی محلی registry + جستجوی دانش از API)
- احراز هویت: `app/login/page.tsx`، `app/register/page.tsx`، `app/forgot-password/page.tsx`، `app/reset-password/page.tsx`، `app/profile/page.tsx`، `app/settings/page.tsx`
- `app/models/page.tsx` → `ModelCatalog`؛ `app/learn/page.tsx` (هاب آموزش)؛ `app/blog/page.tsx` + ۴ مقاله؛ `app/news/page.tsx` + ۲ خبر

### admin (پنل مدیریت — ۱۹ مسیر)
- `app/admin/page.tsx` و `app/admin/overview/page.tsx` → `AdminNav` + `AdminOverview` (متریکهای واقعی با React Query)
- `app/admin/health/page.tsx` → `AdminHealth`؛ `admin/bots` → `AdminBots`؛ `admin/errors` → `AdminErrors`؛ `admin/users` → `AdminUsers`؛ `admin/content` → `AdminContent`؛ `admin/models` → `AdminModels`؛ `admin/security` → `AdminSecurity`؛ `admin/settings` → `AdminSettings`
- بقیه (`admin/alerts|analytics|backup|data|docs|farms|logs|roles|translations`) → الگوی `AdminPlaceholder` (۹ استفاده)

### modules (ماژولهای تعاملی — هر ماژول ۵ صفحه)
۹ ماژول: `ai` (چتبات SSE/WebSocket + صوت)، `analytics`، `carbon`، `ecowallet`، `erosion`، `marketplace`، `satellite` (تحلیل باندهای ماهوارهای + نقشه)، `scenarios` (SSP)، `soil` (مثلث بافت USDA + سلامت خاک)، `voice`، `watershed` (طراحی سازه آبخیز).
- صفحه تعاملی: `app/modules/<module>/page.tsx` (client، فرم + فراخوانی API + Navbar قدیمی)
- صفحات محتوایی: `app/modules/<module>/overview|guide|science|faq/page.tsx` → الگوی `SitePage` + `pageContent`
- **ریسک:** `app/modules/page.tsx` وجود ندارد → مسیر `/modules` 404 میدهد (رجیستری هم شامل `modules` نیست؛ SiteNav به `modules/*` لینک دارد ولی هاب ندارد)

### dashboard (داشبورد — ۱۴ مسیر)
- `app/dashboard/page.tsx` (داشبورد قدیمی client: CRUD مزرعه، گرید ماژولها، ScenarioComparison، ErosionRiskMap)
- `app/dashboard/overview/page.tsx` → **`DashboardOverview`** (نسخه جدید React Query: farms + satellite health + سطح یادگیری)
- `app/dashboard/farms/page.tsx` → `FarmDashboard`؛ `dashboard/farm-detail/page.tsx` → `FarmDetail`
- بقیه (`activities|alerts|analytics|education|marketplace|messages|reports|schedule|settings|support|wallet`) → SitePage محتوایی؛ `dashboard/farms/new` → فرم ثبت مزرعه
- `app/dashboard/layout.tsx` → `Sidebar` + `TopBar` (در دسکتاپ و موبایل)

### science (لایه آکادمیک — ۱۰ مسیر)
- `app/science/page.tsx` → `ScienceDashboard` (دیتاستها، استنادها، نمودارهای ERA5 نمونه)
- `science/research|datasets|models|publications|citations|open-data|repositories|labs|field-pilot` → SitePage

### خدمات، آموزش، ابزار، جامعه، قانونی، حساب
- `services/*` (۹ صفحه)، `learn/*` (هاب + ۹ دسته + ۲۱ مقاله عمقی)، `tools/*` (هاب + ۱۲ ماشینحساب: irrigation, compost-cn, fertilizer, carbon-stock, erosion (RUSLE), water-footprint, seeding, lime, soil-water, drip-design, biomass, co2-offset)، `community/*` + `forum/*` (۵)، `legal/*` (۴: terms, privacy, security, cookies)، `account/*` (۷: billing, devices, notifications, questions, saved, security, subscriptions)
- SEO: `app/robots.ts` و `app/sitemap.ts` از siteRegistry (BASE: `NEXT_PUBLIC_SITE_URL` || `https://eco-nojin.ir`)

---

## ۳) کامپوننتها

### UI Kit (الگوی shadcn/ui روی Radix)
در `components/ui/` (۲۵ فایل + `index.ts` barrel): `avatar, badge, button, card, checkbox, collapsible, command, data-table, dialog, dropdown-menu, form, input, label, motion-icon, popover, progress, radio-group, scroll-area, select, separator, sheet, skeleton, slider, sonner, switch, tabs, tooltip`.
- `components/ui/data-table.tsx` — DataTable عمومی: جستجو، مرتبسازی (با `localeCompare("fa")`)، صفحهبندی، خروجی CSV (با BOM)، نمای کارت در موبایل
- `components/ui/sheet.tsx` — بر پایه Radix Dialog با variant های چپ/راست (پیشفرض right برای RTL)
- `components/ui/command.tsx` — بر پایه cmdk + Dialog (CommandPalette)
- نکته: `sheet` و `command` از `index.ts` export نشدهاند.

### کامپوننتهای site (نظام جدید)
`SiteNav.tsx` (منوی کشویی ۸ گروه)، `SiteFooter.tsx`، `SitePage.tsx` (Breadcrumbs + hero + سکشنها + صفحات مرتبط + فهرست کامل سایت — ۱۵۴ صفحه از آن استفاده میکنند)، `CommandPalette.tsx` (Ctrl+K)، `AdminNav/AdminOverview/AdminHealth/AdminBots/AdminErrors/AdminUsers/AdminContent/AdminModels/AdminSecurity/AdminSettings/AdminPlaceholder`، `DashboardOverview.tsx`، `FarmDashboard.tsx`، `FarmDetail.tsx`، `ModelCatalog.tsx`، `Quiz.tsx`، `FaqList.tsx`، `MarkdownView.tsx`، `NewsletterForm.tsx`، `CalcTool.tsx` (۱۲ استفاده)، `SitePage`.

### کامپوننتهای layout (نظام قدیمی)
`components/layout/Navbar.tsx`، `Footer.tsx`، `MobileMenu.tsx`، `Sidebar.tsx`، `TopBar.tsx` — ۲۳ صفحه از Navbar استفاده میکنند. **دو نظام ناوبری موازی وجود دارد.**

### shared / auth / maps / visualizations
- `components/shared/ApiState.tsx` → `LoadingState`، `ErrorState`، `SuccessState`، `InfoState` + تابع `normalizeError`؛ `components/shared/ThemeToggle.tsx`
- `components/auth/AuthModal.tsx` — **orphan**
- `components/maps/` → `CoordinatePicker`، `ErosionRiskMap`، `MultiLayerMap` (Leaflet)، `MapClickHandler` (**orphan**)
- `components/visualizations/` → `HealthGauge` (SVG gauge)، `IndicesRadar` (رادار NDVI/EVI/SAVI/NDWI/NBR)، `NutrientMeter`، `SoilTriangle` (مثلث بافت USDA)

### ⚠️ کامپوننتهای orphan (بدون هیچ import) — ۱۶ فایل
`WatershedPanel, SoilDashboard, SatellitePanel, ScenarioPanel, EcoWalletPanel, MarketplacePanel, CropPlannerPanel, ChatAssistant, CarbonCreditPanel, BenchmarkPanel, MobileFeaturesPanel` (در `components/` ریشه) + `AuthModal, FarmSelector, ProjectTimeline, MapClickHandler` + هوکهای `useCamera, useGeolocation, useOfflineStorage` + `styles/globals.css` (۲۴۲۴ بایت، هیچجا import نشده — فایل اصلی `app/globals.css` است). اینها نقض صریح قانون «Zero Orphan Files» هستند (چندین component نوشته شدهاند ولی هیچ صفحهای از آنها استفاده نمیکند؛ مثلاً صفحههای ماژولها نسخه inline خودشان را دارند).

---

## ۴) نمودارها — charts kit با recharts

Kit در `components/charts/` با barrel در `index.ts`:
| فایل | نمودار | کاربرد |
|---|---|---|
| `hydrograph.tsx` | LineChart (دبی m³/s + بارش اختیاری) | science-dashboard |
| `rainfall-chart.tsx` | BarChart (بارش mm) | science-dashboard |
| `water-balance.tsx` | ComposedChart (Bar ورودی/خروجی + Line ذخیره) | science-dashboard |
| `soil-moisture.tsx` | LineChart + ReferenceLine (FC/PWP) | — (فقط تست) |
| `et0-chart.tsx` | AreaChart با linearGradient | — (فقط تست) |
| `flow-duration.tsx` | LineChart با YAxis مقیاس log (FDC) | — (فقط تست) |
| `chart-card.tsx` | Card wrapper | science-dashboard |
| `ScenarioComparison.tsx` (۱۶.۹KB) | خطوط ۴ سناریو SSP (126/245/370/585) ۲۰۳۰–۲۱۰۰ + ComposedChart + خروجی html2canvas | `app/dashboard/page.tsx` و `app/modules/scenarios/page.tsx` |

نکات:
- **PieChart استفاده نشده**؛ همه نمودارها `dir="ltr"` دارند (درست برای اعداد/محورها در RTL).
- science-dashboard از داده DEMO با برچسب «نمایش شماتیک» استفاده میکند (وضعیت صادقانه قبل از اتصال ERA5).
- `ScenarioComparison` مدل anomali محلی + فراخوانی `POST /api/v1/scenarios/apply` دارد.
- ویژیوالیزیشنهای SVG دستی (IndicesRadar, SoilTriangle, HealthGauge) در صفحات satellite و soil استفاده میشوند.
- تمام ۵ نمودار kit در `__tests__/charts.test.tsx` با mock کردن `ResponsiveContainer` تست شدهاند.

---

## ۵) i18n — ۱۴ زبان، پیشفرض fa، RTL

**از next-intl استفاده نشده** — یک سیستم i18n سفارشی با React Context:
- `lib/i18n.ts`: آرایه `locales` (۱۴ زبان: ar, bn, de, en, es, fa, fr, hi, it, ms, pt, ru, ur, zh)، نقشه `directions` (فقط fa/ar/ur → rtl)، `defaultLocale = "fa"`.
- `lib/i18n-context.tsx`: `I18nProvider` (در `app/layout.tsx` دور همهچیز) با hook `useI18n()` → `t(key)`، `locale`، `setLocale`، `direction`، `font`. زبان در `localStorage('locale')` ذخیره میشود؛ `t()` fallback به `en` و سپس خود کلید.
- `lib/locales-data.ts` و `locales-data` خودکار import همه JSON ها.
- **ترجمهها:** فایلهای JSON در `locales/*.json` با ساختار `{locale, direction, app_name, engine_name, messages}`.
  - آمار کلیدها: **fa = 389، en = 389**؛ ۱۲ زبان دیگر هر کدام **۳۵۳** کلید (۳۶ کلید `nav_*` و `scenario_*` فقط fa/en دارند → در زبانهای دیگر fallback به انگلیسی).
  - `locales/registry.en.json` — ۱۷۰ عنوان انگلیسی رجیستری برای `entryTitle()` در `lib/site-i18n.ts` (GROUP_TITLES ۱۱ گروه).
  - `locales/backend_translations.json` — ترجمههای پیامهای back-end (مثل `satellite.recommendation.*`).
- اعمال dir/lang: سه مکانیزم موازی/تکراری — `I18nProvider` (useEffect)، `FontLanguageProvider.tsx` (با `setInterval(applyFont, 500)` پایش localStorage!)، `useFontLanguage`؛ `LocaleAttributeSync.tsx` هم orphan است.
- ریشه: `<html lang="fa" dir="rtl">` در `app/layout.tsx`.
- **مشکل encoding واقعی در ۳ فایل:** `app/modules/ai/page.tsx` (پیشنهادهای فارسی چتبات)، `app/profile/page.tsx` (برچسبهای زبان: 'ظپط§ط±ط³غŒ' و 'Tأ¼rkأ§e')، `app/register/page.tsx` — متن فارسی double-encoded (موجیبیک) شدهاند.
- همچنین `app/dashboard/page.tsx` شامل `âœ“ Active` (بهجای ✓) است.

---

## ۶) اتصال به API

- **کلاینت:** `lib/api-client.ts` — wrapper بومی **fetch** (axios نیست) با متدهای `api.get/post/put/delete`، بازگشت `ApiResponse<T> = {success, data?, error?, status?}`.
- **Base URL:** `API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'` (نسخه دوم در `lib/config.ts` با `apiUrl()` که trailing slash را حذف میکند — دو تعریف موازی از یک ثابت).
- **Auth:** توکن JWT از `localStorage('auth_token')`، هدر `Authorization: Bearer`؛ در 401 توکن و یوزر پاک میشوند.
- **خطا:** پیام از `data.detail || data.message || HTTP <status>`؛ بادی غیر JSON بهصورت متن نگهداری میشود؛ خطاهای شبکه در catch.
- **UI خطا:** `components/shared/ApiState.tsx` — `normalizeError()` آرایههای FastAPI 422 (هر عنصر `{loc, msg}`) را به «loc.msg؛ loc.msg» تبدیل میکند؛ `ErrorState` برای نمایش.
- **کش/State:** React Query در `app/providers.tsx` (`retry: 1`, `staleTime: 30_000`, `refetchOnWindowFocus: false`) — اما فقط **۲ کامپوننت** از آن استفاده میکنند (`AdminOverview`, `DashboardOverview`)؛ بقیه صفحات از useState/useEffect + api-client استفاده میکنند (بدون کش/دیدیپلیکیشن).
- `lib/farm-context.tsx` و `lib/auth-context.tsx` از `api-client` استفاده میکنند (auth: `/api/v1/auth/login|register`، farms: `/api/v1/farms/`).
- Endpoint های مورد استفاده: `/api/v1/watershed/design`، `/api/v1/satellite/analyze|health`، `/api/v1/scenarios/apply`، `/api/v1/science/datasets|citations/index`، `/api/v1/admin/overview`، `/api/v1/knowledge/search` (در search page).

---

## ۷) تستها — Vitest

- `vitest.config.mts`: environment **jsdom**، globals، `setupFiles: vitest.setup.ts` (stub برای ResizeObserver و scrollIntoView)، alias `@` → ریشه.
- `vitest.setup.ts`: `@testing-library/jest-dom/vitest` + polyfill ها.
- **۵ فایل تست / ۱۸ تست — همگی PASS** (اجرای واقعی تأیید شد، ۵.۷ ثانیه):
  - `__tests__/charts.test.tsx` (۵ تست) — render ۵ نمودار recharts با mock ResponsiveContainer
  - `__tests__/data-table.test.tsx` (۶) — جستجو/مرتبسازی/صفحهبندی/empty/loading
  - `__tests__/form.test.tsx` (۳) — FormField/FormSection
  - `__tests__/sheet.test.tsx` (۲) — باز/بسته شدن Sheet
  - `__tests__/command-palette.test.tsx` (۲) — باز شدن با Ctrl+K و ناوبری
- **شکافها:** تستی برای api-client، i18n-context، auth/farm/theme context، کامپوننتهای admin، ScienceDashboard، ScenarioComparison وجود ندارد. هیچ اسکریپت `test` در package.json نیست (باید `pnpm vitest run` زده شود). eslint `__tests__` را ignore میکند.
- هشدار Vite: `__dirname` در vitest.config.mts → پیشنهاد `import.meta.dirname`.

---

## ۸) PWA — manifest و Service Worker

- `public/manifest.json`: name «Eco Nojin — اکو نوژین»، `dir: rtl`، `lang: fa`، `display: standalone`، آیکونهای SVG (`/icon-192.svg`, `/icon.svg`). **آیکونهای PNG در `public/icons/` فایلهای ۷۰ بایتی placeholder هستند** و در manifest نیستند؛ theme/background `#0a0f1c`.
- `public/sw.js`: کش `eco-nojin-v1.2`، استراتژی **network-first با fallback کش**، precache فهرست (`/`, `/index.html`, `/pages`, `/learn`, `/tools`, فونتهای Vazirmatn)، fallback آفلاین `/`، پشتیبانی Background Sync (`sync-offline-data`)، `skipWaiting`/`clients.claim`، و fetch برای cross-origin فقط اگر `/api/v1/` در URL باشد.
- `lib/swRegistration.ts`: `registerServiceWorker()` + `requestSync()` — **هیچجا import نشده است!** تنها ثبت واقعی SW در `components/MobileFeaturesPanel.tsx` است که خودش orphan است → **در عمل SW هرگز ثبت نمیشود و آفلاین-فرست واقعی فعال نیست.**
- `lib/useOfflineStorage.ts`: هوک IndexedDB (DB `eco-nojin-offline`, store `offline-queue`) با `addToQueue/processQueue/clearQueue` و `isOnline` — این هوک هم orphan است (هیچ صفحهای از آن استفاده نمیکند).
- Capacitor برای app موبایل: `webDir: 'out'` ولی خروجی static export پیکربندی نشده؛ `androidScheme: https`، پلاگینهای Geolocation/Camera/LocalNotifications/SplashScreen.

---

## ۹) نکات RTL و فارسی

- ریشه `<html lang="fa" dir="rtl">` + `suppressHydrationWarning`.
- **فونت Vazirmatn self-hosted** در `public/fonts/vazirmatn/` (۴ وزن: Regular/Medium/Bold/ExtraBold — woff2، مجموعاً ~۲۰۰KB) با `@font-face` در `app/globals.css` و `font-display: swap` — بدون وابستگی CDN (offline-safe).
- `font-synthesis: none` روی `html` (بدون bold/italic مصنوعی؛ استفاده از وجههای واقعی — اصلاح رایج فارسی).
- متغیرهای CSS: `--font-fa-classic`, `--font-fa-modern`, `--font-en`, `--font-ar`؛ قواعد `[dir="rtl"]` و `[dir="ltr"]`؛ در RTL ورودیها `text-align: right`.
- نقشه فونت هر زبان در `i18n-context.tsx` (Inter، Vazirmatn، Cairo، Noto Nastaliq Urdu، Noto Sans Devanagari/SC/Bengali) و `setInterval` ۵۰۰ms در FontLanguageProvider.
- الگوی دوگانه dir: صفحات قدیمی `<div dir={direction}>` دارند؛ صفحات SitePage `<div dir="rtl">` ثابت؛ ریشه html هم dir را عوض میکند (چند لایه مدیریت dir).
- نمودارها با `dir="ltr"` (اعداد/محورها)؛ DataTable مرتبسازی `localeCompare("fa")`؛ `calculators.ts` با `toLocaleString("fa-IR")`؛ اعداد فارسی در quiz-data.
- ترکیب ناهمگون زبان: بسیاری از صفحات قدیمی رشتههای انگلیسی hardcode دارند («Welcome», «Your Farms», «No farms yet», «Design Structure» در watershed) کنار متن فارسی — نیمهبینالمللیسازی.
- در `admin/overview` از `dir="ltr"` برای ایمیلها استفاده شده (داخل RTL).

---

## نقاط قوت

1. **پوشش صفحات بسیار گسترده و منظم:** ۲۰۶ صفحه با رجیستری ۱۷۰ مسیر auto-generated که همه با صفحه واقعی جفت هستند؛ `app/pages/page.tsx` و فوتر SitePage کل سایت را بههم لینک میکنند (هیچ صفحه مردهای در رجیستری).
2. **الگوی SitePage یکپارچه (Phase 3):** ۱۵۴ صفحه با breadcrumb، سکشن، صفحات مرتبط و فهرست کامل — نگهداری محتوا از `lib/site-content.ts` (۱۵۶ کلید) ساده است.
3. **UI kit کامل shadcn/Radix** با data-table قدرتمند (جستجو/مرتبسازی فارسی/CSV/موبایل) و تستهای واقعی که همگی pass میشوند (۱۸ تست).
4. **چارت kit تخصصی هیدرولوژی** (Hydrograph، FDC با مقیاس log، WaterBalance، SoilMoisture با FC/PWP، ET0 Area) — علمی و با تست.
5. **PWA/Capacitor زیرساخت خوب:** sw.js با network-first + Background Sync و فونتهای self-hosted؛ manifest RTL/fa.
6. **صادقبودن علمی:** در science-dashboard دادههای DEMO با برچسب «نمایش شماتیک»، و در AdminOverview «متریکهای واقعی — بدون عدد ساختگی»؛ محاسبهگرها با فرمول مستند (FAO-56, RUSLE, IPCC).
7. **توجه به RTL:** font-synthesis:none، Vazirmatn آفلاین، `dir="ltr"` در نمودارها، جهت درست Sheet (راست).
8. مدیریت خطای متمرکز FastAPI (normalizeError برای 422) و 401-پاککردن خودکار توکن.

## نقاط ضعف / ریسک

1. **باک بحرانی:** `components/science/science-dashboard.tsx` خط ۱۱۰ — `const liveCount = useMemo(...)` **خارج از کامپوننت** (module scope) → خطای «Invalid hook call» هنگام رندر `/science`. (با `ignoreBuildErrors` build میگذرد ولی runtime کرش میکند.)
2. **موجیبیک واقعی در ۳ فایل:** `app/modules/ai/page.tsx`، `app/profile/page.tsx`، `app/register/page.tsx` (متن فارسی double-encoded) + `âœ“` در `app/dashboard/page.tsx` + کلید خراب `LEARNING_KEY = "eco-no…ress"` در `lib/learning-store.ts`.
3. **۱۶ فایل orphan** (۱۱ پنل بزرگ + AuthModal + FarmSelector + ProjectTimeline + MapClickHandler + هوکهای offline/geo/camera + styles/globals.css) — نقض Zero Orphan Files.
4. **PWA غیرفعال در عمل:** `registerServiceWorker` هرگز صدا زده نمیشود؛ آیکونهای PNG ۷۰ بایتی placeholder؛ `webDir: 'out'` بدون `output: 'export'`.
5. **دو نظام موازی:** Navbar/Footer قدیمی (۲۳ صفحه، انگلیسی hardcode) کنار SiteNav/SiteFooter؛ دو تعریف `API_BASE` (api-client.ts و config.ts)؛ سه مکانیزم dir/font (I18nProvider + FontLanguageProvider با polling 500ms + useFontLanguage).
6. **بدهی تایپی پنهانشده:** `typescript.ignoreBuildErrors: true` و `lint --max-warnings=1000` — خطاهای تایپ/ESLint در CI دیده نمیشوند.
7. **i18n ناقص:** ۳۶ کلید جدید فقط fa/en؛ فقط ۲ کامپوننت React Query دارند (بقیه fetch-on-mount بدون dedup/کش)؛ مسیر `/modules` وجود ندارد (404).
8. بدون `error.tsx`/`not-found.tsx`/`loading.tsx`؛ سایتمپ همیشه priority 0.7 (شرط `e.path === "/"` هیچوقت درست نمیشود).
9. React Query در AdminOverview از localStorage مستقیم (نه از AuthContext) میخواند؛ تست برای اجزای حیاتی (auth, api, admin) وجود ندارد.

## پیشنهادها

1. **فوری:** رفع باگ `useMemo` در science-dashboard.tsx (انتقال به داخل کامپوننت)؛ اصلاح موجیبیک ۳ فایل + `âœ“` + `LEARNING_KEY`؛ حذف یا اتصال فایلهای orphan (یا ثبت آن در backlog بهعنوان «منسوخ»).
2. **PWA:** فراخوانی `registerServiceWorker()` در root layout (مثلاً در providers)؛ ساخت آیکونهای PNG واقعی؛ هماهنگسازی `output: 'export'` با Capacitor یا حذف Capacitor اگر استفاده نمیشود.
3. **یکسانسازی:** ادغام Navbar→SiteNav و Footer→SiteFooter؛ حذف تعریف تکراری API_BASE (استفاده از `lib/config.ts`)؛ حذف polling 500ms فونت (رویداد storage کافی است) و تکمیل LocaleAttributeSync یا حذف آن.
4. **انضباط تایپ:** فعال کردن تدریجی type-check (حذف `ignoreBuildErrors` بعد از رفع W-022)؛ افزودن `typecheck` به scripts؛ افزودن اسکریپت `test` (vitest run) در package.json و اجرای آن در CI.
5. **i18n:** ترجمه ۳۶ کلید به ۱۲ زبان دیگر؛ جایگزینی رشتههای hardcode انگلیسی صفحات قدیمی با `t()`؛ افزودن تست برای `t()`/fallback و direction.
6. **مسیر `/modules`:** ساخت `app/modules/page.tsx` بهعنوان هاب ۹ ماژول و افزودن به registry.
7. **افزودن** `app/error.tsx` (RTL, فارسی) و `not-found.tsx`؛ اصلاح sitemap priority.
8. **گسترش React Query** به صفحات دادهگرفته (watershed, satellite, scenarios) با staleTime مناسب و حالتهای loading/error یکپارچه از ApiState.

---

*گزارش با مطالعه مستقیم فایلها، اجرای تستها (۱۸/۱۸ موفق) و اسکنهای آماری تهیه شد. مسیرهای دقیق همه فایلهای ذکرشده در متن آمده است.*
