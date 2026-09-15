# برنامه استراتژیک و گام‌به‌گام توسعه فرانت‌اند اکو نوژین
## ارتقاء عملکرد، رفع نقاط ضعف، و گسترش قابلیت‌ها

| مورد | جزئیات |
|---|---|
| **تاریخ** | ۱۲ سپتامبر ۲۰۲۶ |
| **پروژه** | Eco Nojin / HyDroMa Frontend |
| **مبنای گزارش** | تحلیل کد منبع + برنامه‌های موجود (DASHBOARD/HOME/IMPACT/DEVELOPMENT/ACTION PLANS) |

---

## فهرست مطالب
1. [مقدمه و وضعیت فعلی](#۱-مقدمه)
2. [چارچوب اهداف کوتاه‌مدت و بلندمدت](#۲-اهداف)
3. [فاز ۱ — اصلاحات فوری (۰ تا ۱ ماه)](#۳-فاز-۱)
4. [فاز ۲ — بهبود عملکرد (۱ تا ۳ ماه)](#۴-فاز-۲)
5. [فاز ۳ — ارتقای فناوری (۳ تا ۶ ماه)](#۵-فاز-۳)
6. [فاز ۴ — توسعه ویژگی‌های جدید (۶ تا ۱۲ ماه)](#۶-فاز-۴)
7. [فاز ۵ — گسترش استراتژیک (۱۲ تا ۱۸ ماه)](#۷-فاز-۵)
8. [روش‌های بهبود مستمر](#۸-بهبود-مستمر)
9. [نقشه راه فنی و وابستگی‌ها](#۹-نقشه-راه)
10. [مؤشرات کلیدی عملکرد (KPIs)](#۱۰-kpi)

---

## ۱. مقدمه و وضعیت فعلی

### ۱.۱. خلاصه وضعیت پروژه

فرانت‌اند اکو نوژین بر پایه **React 18 + Vite 5 + TypeScript strict + Tailwind CSS v4** ساخته شده و ۴۰+ صفحه، ۲۳ ماژول محتوایی دوزبانه، داشبورد علمی با ۶۱ مدل و ۵ کانال دسترسی را شامل می‌شود. اما چندین چالش ساختاری و عملکردی وجود دارد:

| حوزه | وضعیت فعلی | اولویت |
|---|---|---|
| SSR/SSG | ❌ ندارد (SPA خالص) | 🔴 بحرانی |
| MapLibre/deck.gl | ❌ نقشه SVG مفهومی | 🔴 بالا |
| داده‌های زنده | ⚠️ Mock/conceptual | 🔴 بالا |
| PWA/آفلاین | ⚠️ ادعایی، پیاده نشده | 🔴 بالا |
| Service Worker | ❌ ندارد | 🟡 متوسط |
| بسته‌بندی واجن‌ها | ⚠️ ۶۱ صفحه lazy + dashboard routes | 🟡 متوسط |
| استانداردهای چاپ | ✅ تعریف شده | ✅ |
| تست‌ها | ⚠️ ۷ تست smoke + ۲ تست lib | 🟡 متوسط |

### ۱.۲. وابستگی‌های کلیدی بر پایه برنامه‌های موجود

بر اساس بررسی `DEVELOPMENT_PLAN.md`، `DASHBOARD_PLAN.md`، `HOME_PAGE_PLAN.md` و `IMPACT_PAGE_PLAN.md`:

- **بخش TrustBand** در صفحه خانه: پیش‌نیاز اضافه کردن `shield` به `Icon.tsx` و `trust` به `site.ts`
- **داشبورد**: حذف سایدبار + درخت دسته‌بندی + کارت‌های یکنواخت
- **صفحه Impact**: ۱۰ متریک + MRV + Live Counters + Time Series + Satellite Map
- **صفحه Home**: TrustBand بین ChannelsGrid و CarbonBand

---

## ۲. چارچوب اهداف کوتاه‌مدت و بلندمدت

### ۲.۱. سطوح اولویت

| سطح | تعریف | زمان‌بندی |
|---|---|---|
| **P0 — بحرانی** | اجتناب‌ناپذیر برای عملکرد یا امنیت | ۰ تا ۴ هفته |
| **P1 — بالا** | تأثیر مستقیم بر UX و کیفیت | ۱ تا ۳ ماه |
| **P2 — متوسط** | ارتقای قابلیت‌ها و رقابت‌پذیری | ۳ تا ۶ ماه |
| **P3 — بلندمدت** | تمایز استراتژیک و گسترش بازار | ۶ تا ۱۸ ماه |

### ۲.۲. هدف کلی

```
                  ┌────────────────────────────────┐
                  │  🎯 هدف نهایی (۱۸ ماه)         │
                  │  پلتفرم شماره ۱ آب و خاک       │
                  │  در خاورمیانه و آسیای جنوبی    │
                  └──────────────┬─────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                     │
   ┌────────▼──────┐   ┌────────▼──────┐   ┌─────────▼──────┐
   │ عملکرد و سرعت│   │ شفافیت و اعتبار│   │ قابلیت و پوشش │
   │ (Performance)│   │ (Trust)       │   │ (Features)    │
   └───────────────┘   └───────────────┘   └────────────────┘
```

---

## ۳. فاز ۱ — اصلاحات فوری (۰ تا ۱ ماه)

### هدف: رفع بلاتکلیفی‌ها و پایه‌سازی برای توسعه آینده

### ۳.۱. Rempte‌های P0 (بحرانی)

#### گام ۱.۱: رفع Shared Dependency Inconsistency (۱ روز)
**بر اساس ACTION_PLAN.md:**
- [ ] اضافه کردن `Shield` به `iconMap` در `frontend/src/components/ui/Icon.tsx`
- [ ] اضافه کردن `trust` به تایپ `SiteContent` در `frontend/src/content/site.ts`
- [ ] بررسی یکپارچگی `IconKey` بین `site.ts` و `sections/types.ts`
- **اثر:** امکان استفاده از TrustBand در HomePage
- **تست:** `npx tsc --noEmit` → صفر خطا

#### گام ۱.۲: نکات امنیتی (۲ روز)
**بر اساس ACTION_PLAN.md:**
- [ ] چرخش کلیدهای Supabase و private key بلاکچین اگر قبلاً اشتراک‌گذاری شده‌اند
- [ ] بررسی `contracts/.env` — مطمئن شدن از اینکه فقط in git-ignored است نه in git
- [ ] حذف فایل‌های حساس (`test_migration.db`, `_proof_v8.db`)
- [ ] بررسی CORS_ORIGINS در `.env` (پرت‌های 5173 و 4173)
- **اثر:** امنیت پایگاه داده و API

#### گام ۱.۳: یکپارچه‌سازی System of Truth (۳ روز)
**بر اساس ACTION_PLAN.md:**
- [ ] یکی‌کردن ۴ سیستم مهاجرت موازی (`alembic/`, `migrations/`, `supabase/migrations/`)
- [ ] تجمیع ۳ لایه بلاکچین (`contracts/`, `blockchain/`, `services/business_modules/blockchain/`)
- [ ] ادغام `frontend/src/context/` و `contexts/` (اگر وجود دارد)
- **اثر:** سادگی نگهداری و کاهش خلأها

### ۳.۲. بهبودهای P1 (فوری)

#### گام ۱.۴: Skip Navigation Link (۱ ساعت)
**بر اساس تحلیل UI/UX:**
- [ ] افزودن در `Navbar.tsx`:
```tsx
<a href="#main-content" className="sr-only focus:not-sr-only">
  پرش به محتوای اصلی
</a>
```
- [ ] افزودن `id="main-content"` به `<main>` در `App.tsx`
- **اثر:** دسترسی‌پذیری WCAG AA — مخصوصاً کاربران صفحه‌خوان

#### گام ۱.۵: Empty State Design (۴ ساعت)
- [ ] طراحی empty state در `DashboardPage.tsx` (وقتی hub runs خالی است)
- [ ] طراحی empty state در صفحات بلاگ و FAQ (وقتی نتیجه جستجو خالی)
- [ ] استفاده از `EmptyBox` component با آیکن، متن و CTA
- **اثر:** UX حرفه‌ای به‌جای صفحه خالی

#### گام ۱.۶: دستیار محتوایی چندزبانه (۲ روز)
- [ ] ایجاد hook `useBilingual()` در `src/lib/i18n.ts`:
```typescript
export function useBilingual(fa: string, en: string) {
  const { lang } = useLang();
  return lang === 'fa' ? fa : en;
}
```
- [ ] تدریجاً جایگزین ۳۰+ مورد `lang === 'fa'` در کامپوننت‌ها
- **اثر:** کاهش ۴۰٪ تکرار کد در کامپوننت‌ها

---

## ۴. فاز ۲ — بهبود عملکرد (۱ تا ۳ ماه)

### هدف: کاهش ۵۰٪ زمان بارگذاری و بهبود Core Web Vitals

### ۴.۱. بهینه‌سازی بارگذاری اولیه

#### گام ۲.۱: SSR/SSG Migration (۳ هفته)
**بزرگ‌ترین تأثیرگذار در کل برنامه:**

**الگوریتم پیشنهادی:** مهاجرت از Vite SPA به **Astro** با Island Architecture

| مرحله | شرح | مدت |
|---|---|---|
| ۲.۱.۱ | نصب Astro و setup پروژه | ۱ روز |
| ۲.۱.۲ | مهاجرت `index.html` و SEO | ۲ روز |
| ۲.۱.۳ | مهاجرت HomePage و PlatformPage (SSR) | ۳ روز |
| ۲.۱.۴ | مهاجرت بقیه صفحات عمومی | ۱ هفته |
| ۲.۱.۵ | حفظ داشبورد به‌عنوان SPA (hydration) | ۲ روز |
| ۲.۱.۶ | تست و بهینه‌سازی | ۳ روز |

**نتیجه مورد انتظار:**
- LCP: از ~۳.۵s به <۱.۵s
- TTI: از ~۴s به <۲s
- بهبود SEO: indexation کامل توسط موتورهای جستجو

#### گام ۲.۲: Service Worker و PWA (۲ هفته)
- [ ] نصب `vite-plugin-pwa`
- [ ] تعریف `vite.config.ts` برای SW:
```typescript
import { VitePWA } from 'vite-plugin-pwa';
// در config:
plugins: [react(), tailwindcss(), VitePWA({ registerType: 'autoUpdate', ... })],
```
- [ ] استراتژی کش: Cache-First برای assets، Network-First برای API
- [ ] Manifest و Icons
- [ ] Background Sync برای فرم‌ها (تماس، پایلوت)
- **اثر:** کاربران می‌توانند بدون اینترنت به محتوای کش‌شده دسترسی داشته باشند

#### گام ۲.۳: Bundle Optimization (۱ هفته)
- [ ] فعال‌سازی `rollup-plugin-visualizer` در `vite.config.ts`:
```typescript
import { visualizer } from 'rollup-plugin-visualizer';
plugins: [react(), tailwindcss(), visualizer({ open: true })]
```
- [ ] اضافه کردن script `pnpm dlx vite-bundle-visualizer` در `ACTION_PLAN.md`
- [ ] Dynamic imports برای کامپوننت‌های سنگین (Charts, Maps)
- [ ] بررسی و حذف dependencies غیرضروری (ACTION_PLAN: `georaster-layer-for-leaflet`, `terraformer`, `@types/mapbox-gl`)
- **اثر:** کاهش ۲۰-۳۰٪ اندازه باندل

### ۴.۲. بهبود Core Web Vitals

#### گام ۲.۴: Image Optimization
- [ ] تبدیل تصاویر SVG به optimized versions با `svgo`
- [ ] اضافه کردن `next/image` equivalent یا `vite-imagetools` برای تصاویر آینده
- [ ] Implementasyon lazy loading برای تصاویر پایین صفحه
- [ ] Preloading فونت Vazirmatn با `<link rel="preload">`

#### گام ۲.۵: Critical CSS
- [ ] استفاده از `vite-plugin-critical` یا `critters`
- [ ] Inline کردن استایل‌های Above-the-Fold در `index.html`
- [ ] Defer کردن CSS غیرحیاتی

#### گام ۲.۶: Preloading و Prefetching
- [ ] `<link rel="preload">` برای فونت‌ها و کانپوننت‌های اصلی
- [ ] Prefetch for پیش‌نمایش صفحات مرتبط در viewport
- [ ] Prerender برای صفحات مهم (Home, Platform, Impact) با Astro

---

## ۵. فاز ۳ — ارتقای فناوری (۳ تا ۶ ماه)

### هدف: رسیدن به سطح فنی رقبای برتر

### ۵.۱. مهاجرت React 19 (۴ هفته)

| مرحله | شرح |
|---|---|
| ۵.۱.۱ | بروزرسانی `package.json` به React 19 + React DOM 19 |
| ۵.۱.۲ | بروزرسانی `@types/react` و `@types/react-dom` |
| ۵.۱.۳ | بروزرسانی Framer Motion، React Router، و وابستگی‌ها |
| ۵.۱.۴ | استفاده از `use()` hook برای lazy data |
| ۵.۱.۵ | مهاجر تدريجی به Server Components (لایه‌های stateless) |
| ۵.۱.۶ | تست و تست regression |

### ۵.۲. MapLibre Integration (۳ هفته)
**جایگزینی SatelliteMap مفهومی با نقشه واقعی:**

- [ ] نصب `maplibre-gl` و `react-maplibre`
- [ ] ایجاد `MapLibreMap.tsx` با:
  - لایه NDVI واقعی از Sentinel-2 (CDSE)
  - مارکرهای پروژه با tooltip تعاملی
  - لایه‌های قابل فعال‌سازی (خاک، آب، کربن)
  - اندازه‌گیری و بوم‌شناسی
- [ ] حفظ fallback SVG برای حالت conceptual
- [ ] بهینه‌سازی حافظه با tile caching

### ۵.۳. Chart Library Integration (۲ هفته)
- [ ] ارزیابی و انتخاب: Recharts یا Chart.js v4
- [ ] جایگزینی `ImpactTimeSeries.tsx` و `NdviConceptChart.tsx`
- [ ] نگه‌داشتن SVG hand-coded برای انیمیشن‌های خاص (Framer Motion)
- [ ] تست عملکرد با ۱۰+ نقطه داده

### ۵.۴. Real-time Data Pipeline (۳ هفته)
- [ ] WebSocket/SSE client برای داده‌های لحظه‌ای
- [ ] TanStack Query (React Query) برای cache + refetch:
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
```
- [ ] Real-time counters با polling هر ۳۰ ثانیه (مثل `LiveCounters.tsx`)
- [ ] Auto-refresh برای داشبورد و پروفایل
- [ ] Status page (`/status`) با health check لحظه‌ای

---

## ۶. فاز ۴ — توسعه ویژگی‌های جدید (۶ تا ۱۲ ماه)

### هدف: ویژگی‌های تمایز و گسترش بازار

### ۶.۱. AI Advisory Engine (۸ هفته)

| مرحله | شرح |
|---|---|
| ۶.۱.۱ | طراحی API endpoint برای advisory |
| ۶.۱.۲ | جمع‌آوری training data از مدل‌های علمی هیدروما |
| ۶.۱.۳ | پیاده‌سازی recommendation engine |
| ۶.۱.۴ | UI: پنل مشاوره در داشبورد و صفحه پلتفرم |
| ۶.۱.۵ | Feedback loop برای بهبود مستمر |

### ۶.۲. Mobile App React Native (۱۲ هفته)
- [ ] ساخت Shell App با React Native
- [ ] Native Modules: دوربین (QR/photo), GPS, push notifications
- [ ] Sync engine برای آفلاین-first
- [ ] USSD/SMS integration با native bridge
- [ ] App Store / Play Store deployment

### ۶.۳. Carbon Marketplace (۱۰ هفته)
- [ ] بازار معاملات اعتبار کربن
- [ ] Standard integration: Verra, Gold Standard, Puro-Earth
- [ ] Dashboard برای صادرکنندگان و خریداران
- [ ] Smart contract interaction با Polygon
- [ ] Real-time pricing feed

### ۶.۴. IoT Dashboard (۶ هفته)
- [ ] View جدید: `/dashboard/iot`
- [ ] Real-time sensor monitoring (MQTT/TTN v3)
- [ ] QA/QC pipeline (per `mrv-qa` model in registry)
- [ ] Alerting system for anomalies
- [ ] Audit trail visualization

### ۶.۵. Digital Twin (۱۶ هفته)
- [ ] ۳D visualization مزرعه با Three.js
- [ ] Integration با Sentinel-2 imagery
- [ ] Simulation overlay برای سناریوها
- [ ] VR/AR support (اختیاری)

---

## ۷. فاز ۵ — گسترش استراتژیک (۱۲ تا ۱۸ ماه)

### هدف: تبدیل شدن به پلتفرم اکوسیستم

### ۷.۱. Open API Marketplace
- [ ] پورتال توسعه‌دهندگان (`/developers`)
- [ ] API documentation با Swagger/OpenAPI
- [ ] API key management و rate limiting dashboard
- [ ] Partner program و revenue sharing

### ۷.۲. Academic Research Portal
- [ ] Dashboard دانشگاهی با ابزار تحقیقاتی
- [ ] Dataset download و citation export
- [ ] Co-authorship و collaboration tools

### ۷.۳. Regenerative Finance (ReFi) Protocol
- [ ] DeFi integration برای تأمین مالی احیای اکوسیستم
- [ ] Tokenomics اکوکیف
- [ ] Carbon-backed lending
- [ ] DAO governance

### ۷.۴. Global Expansion
- [ ] گسترش زبان‌ها از ۱۴ به ۳۰+
- [ ] Regional deployment (Africa, LATAM, South Asia)
- [ ] Local partnerships (NGOs, governments, cooperatives)

---

## ۸. روش‌های بهبود مستمر

### ۸.۱. فرآیندهای توسعه

| روش | تناوب | شرح |
|---|---|---|
| **Code Review** | هر PR | ۲+ نفر بررسی قبل از merge |
| **Weekly Demo** | هفتگی | نمایش پیشرفت برای تیم |
| **Monthly Retrospective** | ماهانه | بررسی عملکرد و بهبود فرآیند |
| **Quarterly Roadmap Review** | فصلی | بازنگری و به‌روزرسانی اولویت‌ها |
| **Security Audit** | ۶ ماهه | بررسی امنیتی توسط متخصص خارجی |
| **Performance Benchmark** | هفتگی | بررسی Lighthouse CI |

### ۸.۲. فرآیندهای کیفیت

#### تست و تأیید (پس از هر فاز):
```bash
# معیارهای تأیید اضطراری
cd frontend
npx tsc --noEmit          # ← انتظار: ۰ خطا
npx eslint src/           # ← انتظار: ۰ خطا
npx vitest run            # ← انتظار: همه تست‌ها سبز
npx vite build            # ← انتظار: ساخت موفق
npx vite preview          # ← بررسی دستی
```

#### KPIs هر فاز:
| KPI | هدف فاز ۱ | هدف فاز ۲ | هدف فاز ۳ |
|---|---|---|---|
| Lighthouse Performance | >60 | >80 | >95 |
| Lighthouse Accessibility | >70 | >85 | >95 |
| Test Coverage | >20% | >40% | >60% |
| Bundle Size | <3MB | <2MB | <1.5MB |
| FCP | <2s | <1.5s | <1s |
| TypeScript Errors | ۰ | ۰ | ۰ |
| ESLint Errors | ۰ | ۰ | ۰ |

### ۸.۳. Learning and Iteration

#### روزانه:
- مطالعه ۱ GitHub issue یا PR از رقبا
- بررسی ۱ مقاله مرتبط (Web Performance, React, Accessibility)

#### هفتگی:
- Core Web Vitals Check (Lighthouse CI)
- Dependency Audit (`npm audit` / `pnpm audit`)
- Review competitor releases

#### ماهانه:
- User feedback analysis
- Analytics review (ترافیک، bounce rate، conversions)
- Roadmap adjustment بر اساس یافته‌ها

### ۸.۴. Continuous Integration Pipeline

```yaml
# پیشنهاد .github/workflows/frontend.yml
name: Frontend CI
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm lint
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm type-check
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm test
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm build
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install && pnpm build
      - uses: treosh/lighthouse-ci-action@v9
        with:
          configPath: .lighthouserc.json
  deploy:
    needs: [lint, typecheck, test, build]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install && pnpm build
      # Deploy to Vercel/Netlify/Render
```

---

## ۹. نقشه راه فنی و وابستگی‌ها

### ۹.۱. وابستگی‌های فاز به فاز

```
فاز ۱ (۰-۱ ماه)
├── TrustBand integration (HOME_PAGE_PLAN.md)
├── Security fixes (ACTION_PLAN.md)
├── Skip Navigation (Accessibility)
├── Empty States (UX)
└── useBilingual helper (Code quality)
         │
         ▼
فاز ۲ (۱-۳ ماه)
├── SSR Migration → Astro (BLOCKER for faze 3+)
├── PWA/Service Worker
├── Bundle Optimization
├── Critical CSS
└── Dashboard Plan execution (DASHBOARD_PLAN.md)
         │
         ▼
فاز ۳ (۳-۶ ماه)
├── React 19 Migration (requires faze 2 stable)
├── MapLibre (requires SSR done)
├── Chart Library (independent)
├── TanStack Query (requires API ready)
└── Real-time Pipeline (requires WebSocket server)
         │
         ▼
فاز ۴ (۶-۱۲ ماه)
├── AI Advisory (requires MapLibre + models ready)
├── Mobile App (requires PWA stable)
├── Carbon Marketplace (requires blockchain ready)
├── IoT Dashboard (requires WebSocket + MQTT)
└── Digital Twin (requires 3D engine + MapLibre)
         │
         ▼
فاز ۵ (۱۲-۱۸ ماه)
├── API Marketplace (requires all APIs stable)
├── Academic Portal (requires models + data)
├── ReFi Protocol (requires carbon credits live)
└── Global Expansion (requires i18n framework)
```

### ۹.۲. مسیر اولویت‌بندی هر فاز

| اولویت | وظیفه | فاز | زمان | وابستگی |
|---|---|---|---|---|
| ۱ | TrustBand Home | ۱ | ۱ روز | Icon + site.ts |
| ۲ | Security rotation | ۱ | ۲ روز | — |
| ۳ | Skip Navigation | ۱ | ۱ ساعت | — |
| ۴ | Empty States | ۱ | ۴ ساعت | — |
| ۵ | useBilingual | ۱ | ۲ روز | — |
| ۶ | Dashboard Plan (5 phases) | ۲ | ۶ هفته | — |
| ۷ | Astro SSR Migration | ۲ | ۳ هفته | — |
| ۸ | PWA/Service Worker | ۲ | ۲ هفته | Node 20+ |
| ۹ | Bundle Optimization | ۲ | ۱ هفته | visualizer |
| ۱۰ | React 19 Migration | ۳ | ۴ هفته | فاز ۲ stable |
| ۱۱ | MapLibre Integration | ۳ | ۳ هفته | فاز ۲ SSR |
| ۱۲ | TanStack Query | ۳ | ۲ هفته | API ready |
| ۱۳ | AI Advisory Engine | ۴ | ۸ هفته | MapLibre + models |
| ۱۴ | Mobile App | ۴ | ۱۲ هفته | PWA stable |
| ۱۵ | Carbon Marketplace | ۴ | ۱۰ هفته | Blockchain |
| ۱۶ | Digital Twin | ۴ | ۱۶ هفته | Three.js + MapLibre |
| ۱۷ | API Marketplace | ۵ | ۱۲ هفته | All APIs |
| ۱۸ | ReFi Protocol | ۵ | ۱۶ هفته | Carbon live |
| ۱۹ | Global Expansion | ۵ | ۱۸ هفته | i18n framework |

---

## ۱۰. مؤشرات کلیدی عملکرد (KPIs)

### ۱۰.۱. KPIs فنی

| متریک | فعلی | هدف ۳ ماهه | هدف ۱۲ ماهه | هدف ۱۸ ماهه |
|---|---|---|---|---|
| **Lighthouse Performance** | ~40-50 | >70 | >90 | >95 |
| **Lighthouse Accessibility** | ~60 | >75 | >90 | >95 |
| **Lighthouse SEO** | ~70 | >85 | >95 | >100 |
| **FCP (First Contentful Paint)** | ~3.5s | <2s | <1.2s | <0.8s |
| **LCP (Largest Contentful Paint)** | ~5s | <2.5s | <1.5s | <1s |
| **CLS (Cumulative Layout Shift)** | ~0.1 | <0.05 | <0.01 | <0.01 |
| **Bundle Size (main)** | TBD | <3MB | <1.5MB | <1MB |
| **Test Coverage** | ~5% | >20% | >40% | >60% |
| **TypeScript Errors** | ۰ | ۰ | ۰ | ۰ |
| **ESLint Errors** | ۰ | ۰ | ۰ | ۰ |

### ۱۰.۲. KPIs کسب‌وکاری

| متریک | هدف |
|---|---|
| **Active Users (MAU)** | ۱۰,۰۰۰ در ۱۲ ماه |
| **Farmers Onboarded** | ۵,۰۰۰ در ۱۸ ماه |
| **Pilot Projects** | ۵۰ در ۱۲ ماه |
| **Carbon Credits Issued** | ۱۰,۰۰۰ tCO₂e در ۱۸ ماه |
| **Languages Supported** | ۳۰+ در ۱۸ ماه |
| **Uptime** | ۹۹.۹% |
| **API Response Time** | <200ms (p95) |

---

## ضمیمه: چک‌لیست عملیاتی هر فاز

### فاز ۱ — روز اول
- [ ] مطالعه و تأیید ACTION_PLAN.md
- [ ] اجرای `git status` و `git diff` برای بررسی وضعیت
- [ ] چرخش کلیدهای امنیتی
- [ ] Security audit اولیه

### فاز ۲ — هر هفته
- [ ] `pnpm build` — ساخت موفق
- [ ] `npx tsc --noEmit` — صفر خطا
- [ ] Lighthouse CI — بررسی regression
- [ ] Bundle visualizer — بررسی اندازه

### فاز ۳+ — هر ماه
- [ ] Sprint retrospective
- [ ] Roadmap review و اولویت‌بندی مجدد
- [ ] Competitor analysis — بررسی ۳ رقیب جدید
- [ ] User feedback synthesis
- [ ] Dependency audit

---

*این برنامه بر اساس تحلیل دقیق کد منبع، برنامه‌های موجود پروژه (DEVELOPMENT/HOME/IMPACT/DASHBOARD/ACTION PLANS) و تحلیل رقبای بازار تهیه شده و باید با تصمیم تیم فنی بازبینی و تأیید شود.*
