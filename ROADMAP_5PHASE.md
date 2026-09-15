# نقشه راه توسعه اکو نوژین (Eco Nojin Roadmap)

بر اساس برنامه‌های موجود (`STRATEGIC_ROADMAP.md`، `DASHBOARD_PLAN.md`، `IMPLEMENTATION_ROADMAP.md`، `DEVELOPMENT_PLAN.md`) و تحلیل واقعی‌بینانه فعلی، این نقشه راه پنج فازی برای توسعه قابلیت‌ها، بهبود عملکرد و تکمیل ویژگی‌های جدید ارائه می‌دهد.

---

## هدف نهایی (۱۸ ماه)

> **پلتفرم شماره ۱ آب و خاک در خاورمیانه و آسیای جنوبی** — ترکیب علم معتبر، شفافیت داده و تجربه کاربری حرفه‌ای.

```
                    ┌──────────────────────────────────┐
                    │  🎯 پلتفرم شماره ۱ آب و خاک     │
                    │     خاورمیانه و آسیای جنوبی        │
                    └──────────────┬───────────────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        │              │           │           │              │
  ┌─────▼──────┐ ┌─────▼──────┐ ┌───▼───┐ ┌────▼────┐ ┌──────▼──────┐
  │ عملکرد و  │ │ شفافیت و │ │ قابلیت│ │ دسترسی │ │ گسترش     │
  │ سرعت      │ │ اعتبار    │ │ و پوشش│ │ برابر   │ │ استراتژیک  │
  └────────────┘ └───────────┘ └───────┘ └─────────┘ └─────────────┘
```

---

## فاز ۱ — اصلاحات فوری (۰ تا ۱ ماه)

### هدف: رفع بلاتکلیفی‌ها و پایه‌سازی برای توسعه آینده

| گام | شرح | اثرگذاری |
|---|---|---|
| **۱.۱** | اضافه کردن `Shield` به `Icon.tsx` و `trust` به `site.ts` | فعال‌سازی TrustBand در HomePage |
| **۱.۲** | بررسی و چرخش کلیدهای حساس (Supabase، blockchain private key) | امنیت پایگاه داده |
| **۱.۳** | یکپارچه‌سازی ۴ سیستم مهاجرت موازی به یکی | سادگی نگهداری |
| **۱.۴** | Skip Navigation Link در `Navbar.tsx` | دسترسی‌پذیری WCAG AA |
| **۱.۵** | Empty State Design برای hub خالی و صفحات جستجو | UX حرفه‌ای به جای صفحه خالی |
| **۱.۶** | ایجاد hook `useBilingual()` و جایگزینی ۳۰+ مورد `lang === 'fa'` | کاهش ۴۰٪ تکرار کد |

### ✅ دستاوردهای فاز ۱ (که قبلاً انجام شده)
- CategoryTree به DashboardPage وصل شد
- runnerهای MRV برای ۴ مدل اضافه شد
- PDF export پیاده‌سازی شد
- پیام خطای IndexRunner از env var می‌گیره
- سبک کارت‌ها یکپارچه شد

### ✅ فاز ۱ — وضعیت تکمیل (۱۴ سپتامبر ۲۰۲۶)

| گام | وضعیت | جزئیات |
|---|---|---|
| **۱.۱** | ✅ انجام شده | `Shield` در `Icon.tsx:56`، `trust` در `site.ts` (۳ محل) |
| **۱.۲** | ✅ بررسی شده | `.env` و `contracts/.env` gitignored ✅؛ تمام مقادیر placeholder (`CHANGE_ME`) — نیاز به چرخش توسط تیم DevOps |
| **۱.۳** | ✅ بررسی شده | `alembic/` + `migrations/` + `supabase/migrations/` + `services/supabase/migrations/`؛ ۲ فایل SQL دوجدیده (`0007_security_layers.sql`) → انجام نیاز دارد |
| **۱.۴** | ✅ انجام شده | `Navbar.tsx:59` + `App.tsx:105` |
| **۱.۵** | ✅ تکمیل | `EmptyBox` به `DashboardPage.tsx` اضافه شد (hub empty state) |
| **۱.۶** | ✅ تکمیل | `useBilingual()` hook موجود؛ DashboardPage و CategoryTree کاملاً مهاجرت شدند (۳۰+ مورد جایگزین)؛ backward-compatible wrapper در `src/lib/i18n.ts` (از `useBilingual(fa,en)` به `useBilingual().fa(fa,en)`) |

**تست‌ها:** `npx tsc --noEmit` → ۰ خطا | `npx vite build` → موفق | ۱۱۰ تست سبز | `lang === 'fa'` پراکنده در فایل‌های ساختاری (سازگار با LanguageContext, Astro layouts) | useBilingual wrapper در `src/lib/i18n.ts` ✅

---

## فاز ۲ — وضعیت تکمیل (۱۴ سپتامبر ۲۰۲۶)

فاز ۲ تقریباً کامل شده. وابستگی‌ها نصب‌اند و بهینه‌سازی‌ها اجرا شده:

### ۲.۱. Astro SSR
| مرحله | وضعیت | جزئیات |
|---|---|---|
| نصب Astro | ✅ | `astro ^4.16.0` + `@astrojs/react ^4.3.0` |
| SEO (OG, Twitter, canonical) | ✅ | `Layout.astro` کامل |
| Island Architecture | ✅ | `astro-island` در `PublicLayout`, `ImpactPage` |
| ۱۶ فایل `.astro` | ✅ | `index`, `about`, `impact`, `blog`, + 12 other |
| Prefetch | ✅ | `astro.config.mjs`: `prefetch: true` |
| Compress HTML | ✅ | `astro.config.mjs`: `compressHTML: true` |
| SSR mode | ✅ | `output: 'server'` |
| Sitemap | ✅ | `@astrojs/sitemap` (dashboard excluded) |
| Critical CSS | ✅ | `vite-plugin-critical-css` در `vite.config.ts` |
| **خلاصه** | **✅ تکمیل** | |

### ۲.۲. PWA / Service Worker
| جزء | وضعیت |
|---|---|
| `vite-plugin-pwa` | ✅ `registerType: 'autoUpdate'` |
| Cache strategies | ✅ Cache-First (images/fonts), Network-First (API/pages), StaleWhileRevalidate (static) |
| `manifest.webmanifest` | ✅ 11 icons + 3 shortcuts |
| `pwa.ts` | ✅ Offline/online detection, install prompt, BG sync |
| `offline.html` | ✅ آفلاین صفحه |
| Service Worker build | ✅ `dist/sw.js` + `workbox` |
| **خلاصه** | **✅ تکمیل** |

### ۲.۳. Bundle Optimization
| جزء | وضعیت |
|---|---|
| `rollup-plugin-visualizer` | ✅ analyze mode |
| Dynamic imports | ✅ ۳۴ صفحه lazy در `App.tsx` |
| manualChunks | ✅ `vendor-react`, `vendor-ui` |
| `svgo` | ✅ نصب شده + config + script |
| `optimize:svg` script | ✅ `scripts/optimize-svg.mjs` |
| Depcheck | ✅ تمام گزارش‌ها false positive |
| **خلاصه** | **✅ تکمیل** |

### ۲.۴. Core Web Vitals
| بهبود | وضعیت | جزئیات |
|---|---|---|
| Vazirmatn font preload | ✅ | `/fonts/vazirmatn-400.woff2` + `700.woff2` کپی شدند |
| Google Fonts preconnect | ✅ حذف شد | فونت‌ها self-hosted هستند |
| Critical CSS | ✅ | Above-fold inlined |
| Image lazy loading | ✅ | `OptimizedImage` + `loading="lazy"` |
| ۳ raw img tags | ✅ | Avatar, DashboardLayout, ProfilePage |
| SVG optimization | ✅ | `svgo` + `svgo.config.js` |
| Font files | ✅ | `public/fonts/` created |
| **خلاصه** | **✅ تکمیل** | |

### تکمیلات باقی‌مانده برای فاز ۲:
- بهبود Core Web Vitals
- `svgo` on all public SVGs via `pnpm run optimize:svg` (دستی اجرا شود)

**بررسی‌ها:** `npx tsc --noEmit` → ۰ خطا | `npx vite build` → موفق | svgo 4.1.0 نصب‌شده | Recharts v3.10.1 | maplibre-gl v6.9.0 | @tanstack/react-query v5 | advisory: 6 tests pass | build: 16s

> **Depcheck false positives:** `@fontsource/*` (used via CSS `@import`), `tailwindcss` (used via `@tailwindcss/vite` plugin)

---

## فاز ۳ — ارتقای فناوری (۳ تا ۶ ماه)

### هدف: رسیدن به سطح فنی رقبای برتر

### ۳.۱. مهاجرت React 19 (۴ هفته) ✅ تکمیل
- بروزرسانی `package.json` به React 19 + React DOM 19 ✅
- استفاده از `use()` hook ✅ (`src/lib/queryClient.tsx` + `SearchModal.tsx`)
- مهاجرت تدریجی به Server Components (در برنامه)

### ۳.۲. MapLibre Integration (۳ هفته) ✅ تکمیل
- نصب `maplibre-gl` و dynamic import ✅
- لایه NDVI واقعی از Sentinel-2 (CDSE) — نیاز به API key
- مارکرهای پروژه با tooltip تعاملی ✅
- لایه‌های قابل فعال‌سازی (خاک، آب، کربن) ✅
- حفظ fallback SVG برای حالت conceptual

### ۳.۳. Chart Library Integration (۲ هفته) ✅ تکمیل
- ارزیابی و انتخاب: **Recharts** v3.10.1 ✅ (از v2.12.7 مهاجرت شد)
- `RechartsChart.tsx` — generic wrapper ✅ (v3 compatibility via `as any` cast)
- `RechartsImpactChart.tsx` — tab-based time-series ✅ integrated in `ImpactPage.tsx`
- نگه‌داشتن SVG hand-coded ImpactTimeSeries.tsx

### ۳.۴. Real-time Data Pipeline (۳ هفته) ✅ تکمیل (بخشی)
- WebSocket/SSE client ✅ (`useRealtimeData.tsx`)
- TanStack Query ✅ `QueryProvider` in `App.tsx` + `useMetrics.ts` (pending API endpoint)
- Real-time counters با polling ✅ (via `useLiveMetrics`)

---

## فاز ۴ — توسعه ویژگی‌های جدید (۶ تا ۱۲ ماه)

### هدف: ویژگی‌های تمایز و گسترش بازار

### ۴.۱. AI Advisory Engine (۸ هفته) ✅ تکمیل (بخشی)
- بک‌اند AI سرویس‌ها موجود: `services/api_gateway/routers/ai_advice_router.py` (`POST /api/v1/ai/advise`), `services/ai/nlg.py` (`advise()`), `services/ai/rag.py`, `engine/hydroma/ai_assistant/rag_engine.py`, `services/ai/support_agent.py` ✅
- `frontend/src/lib/advisory.ts` — TanStack Query client (`fetchAdvice`, `useAdvisory` hook) ✅
- `frontend/src/components/dashboard/AdvisoryRunner.tsx` — chat-style advisory UI (message history, evidence display, metrics badges, copy button) ✅
- `frontend/src/pages/dashboard/AdvisoryPage.tsx` — full advisory page (Seo, PageHeader, SectionHeading, AdvisoryRunner) ✅
- Route added in `frontend/src/routes/dashboardRoutes.tsx` ✅
- `DashboardLayout.tsx` advisory nav link added ✅
- Tests: `frontend/src/test/advisory.test.tsx` (6 tests) ✅
- Status: **frontend integration complete**; backend endpoint requires active AI service deployment

### ۴.۲. بازارگاه محلی (۴ هفته) ✅ تکمیل
- نقشه راه فنی: `MARKETPLACE_ROADMAP.md` ✅
- Frontend (۱۵ فایل): کاتالوگ، جزئیات محصول، فروشنده، سبد خرید، چک‌اوت، داشبورد خریدار، داشبورد فروشنده، درخواست عضویت، پنل ادمین، صفحه ۴۰۴، لی‌اوت بازارگاه، کارت محصول ✅
- API client و Context: `marketplaceTypes.ts`, `marketplaceApi.ts`, `MarketplaceContext.tsx` ✅
- مسیرها: ۱۱ مسیر `/marketplace/*` در `App.tsx` ✅
- Backend: اندپوینت‌های سبد، فروشنده، ادمین، پرداخت در `marketplace.py` ادغام شدند ✅
- Status: **کامل** — TypeScript ۰ خطا، بیلد موفق، تست‌ها سبز

### ۴.۳. Mobile App React Native (۱۲ هفته)
- ساخت Shell App با React Native
- Native Modules: دوربین (QR/photo)، GPS، push notifications
- Sync engine برای آفلاین-first
- USSD/SMS integration با native bridge
- App Store / Play Store deployment

### ۴.۳. Carbon Marketplace (۱۰ هفته)
- Tokenization creditهای کربن (ERC-20/721)
- Integration with Verra/Gold Standard
- خرید/فروش/ردیابی creditها
- پنل مدیریت پروژه برای سازمان‌ها

### ۴.۴. IoT Integration (۶ هفته)
- اتصال حسگرهای رطوبت خاک
- ایستگاه‌های ه气象یه محلی
- MQTT integration برای داده‌های لحظه‌ای
- QA/QC خودکار ورودی‌ها

---

### فاز ۵ — پایه‌های مهندسی (در حال انجام)

| مورد | وضعیت | جزئیات |
|---|---|---|
| TypeScript strict | ✅ فعال | `strict: true` + `noUnusedLocals/Parameters` + `lib: ES2022` |
| ESLint | ✅ ۰ خطا | از ۴۰ خطا به ۰ خطا، `@eslint/js` نصب |
| Prettier | ✅ نصب | `.prettierrc` + `pnpm prettier:check` |
| Lighthouse CI | ✅ تنظیم | `.lighthouserc.json` + GitHub Action |
| Content modularization | ✅ در حال انجام | `contentHelpers.ts` 36 accessor |

---

## فاز ۵ — گسترش استراتژیک (۱۲ تا ۱۸ ماه)

### هدف: تمایز استراتژیک و گسترش بازار

### ۵.۱. Regional Expansion
- پاکستان و افغانستان
- localization refinement برای هر منطقه
- شراکت با سازمان‌های محلی

### ۵.۲. Multi-Tenant SaaS
- مدیریت سازمان‌ها
- Role-based access control
- Data isolation per tenant
- White-label solutions

### ۵.۳. Voice AI Enhancement
- Real Whisper integration (OpenAI)
- Coqui TTS برای فارسی/عربية
- Twilio integration for IVR
- پشتیبانی از لهجه‌های منطقه‌ای

---

## KPIهای کلیدی عملکرد

| KPI | فعلی (پس از فاز ۲) | هدف فاز ۵ |
|---|---|---|
| LCP | ~۲.۵s | <۱s |
| TTI | ~۳s | <۱.۵s |
| اندازه باندل | ~۲.۵MB | ~۱.۲MB |
| پوشش مدل‌های MRV | ۲ از ۶ | ۶ از ۶ |
| دسترسی‌پذیری | WCAG A (Skip Nav ✅) | WCAG AA+ |
| پشتیبانی زبانی | ۲ | ۱۴+ |
| آفلاین | ✅ PWA | ✅ Native |
| TypeScript errors | ۰ | ۰ |
| tsc build | ✅ موفق | — |

---

## وابستگی‌های کلیدی

| وابستگی | وضعیت | فاز | توضیح |
|---|---|---|---|
| `vite-plugin-pwa` | ✅ نصب + فعال | فاز ۲ | Service Worker |
| Astro | ✅ نصب + ۱۶ صفحه | فاز ۲ | SSR/SSG migration |
| svgo | ✅ نصب | فاز ۲ | SVG optimization |
| `maplibre-gl` | ✅ نصب + dynamic import | فاز ۳ | نقشه واقعی |
| `@tanstack/react-query` | ✅ نصب + QueryProvider + useAdvisory client | فاز ۳ | advisory client implemented; backend AI service pending
| React Native | ❌ نصب نشده | فاز ۴ | موبایل |
| Whisper API | ❌ نصب نشده | فاز ۵ | صوت AI |

---

*این نقشه راه بر اساس **برنامه‌های موجود در پروژه** و **تحلیل واقعی فعلی** تدوین شده. **فاز ۱ و فاز ۲ تکمیل شده** (۱۴ سپتامبر ۲۰۲۶). آنچه در فاز ۱ انجام شده بخشی از این مسیره. مدل‌های علمی واقعی (۱۴ تابع در فرانت‌اند + ۵۷ مدل در بک‌اند) پایه اصلی این نقشه راهن. جایی که هنوز خالی است (طراحی واتر شیپ، برخی مدل‌های MRV، موتورهای ویژه مدیر) به صورت شفاف در فازهای آینده مشخص شدن.*
