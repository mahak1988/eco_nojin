# برنامه توسعهٔ صفحه /impact

## وضعیت فعلی

صفحهٔ `/impact` در `frontend/src/pages/ImpactPage.tsx` ساختار اولیه را دارد:

| شماره | بخش | وضعیت |
|-------|------|--------|
| 1 | PageHeader (kicker, title, lead) | ✅ سرهم |
| 2 | متریک‌های تعریف‌شده (grid ۵ متریک) | ✅ سرهم، "پس از پایلوت" |
| 3 | جعبه روش‌اندازی (methodology) | ✅ سرهم |
| 4 | گالری میدانی (FieldGallery) | ✅ سرهم، SVG مفهومی |
| 5 | نمودار NDVI نمونه (NdviConceptChart) | ✅ سرهم، دادهٔ تصویری |
| 6 | CtaBand | ✅ سرهم |

مزیت اصلی صفحه در «شفافیت صادقانه» است: هیچ عدد ساختگی نمی‌شود؛ متریک‌ها تعریف شده‌اند ولی انتظار دادهٔ زنده بعد از پایلوت.

---

## اهداف کلی برنامه

1. **حفظ اصل شفافیت صادقانه** — هیچ عددی ساختگی نشود؛ همهٔ خروجی‌ها واضح‌ترین برچسب «کنونی» یا «پس از پایلوت» بگیرند.
2. **استانداردهای بین‌المللی MRV** — بر اساس ISO 14064-2، IPCC 2019 Refinement، GHG Protocol و ICVCM.
3. **آمادگی برای دادهٔ زنده** — معماری کامپوننتی که با وصل شدن به API ماهواره‌ای و بک‌اند، دادهٔ واقعی جایگزین SVG نمونه شود.
4. **قابلیت دسترسی بین‌المللی (i18n)** — دو زبانه fa/en، راست‌به‌چپ و چپ‌به‌چپ، فونت‌های مناسب.
5. **تجربهٔ تعاملی پیشرفته** — شمارنده‌های زنده، کارت‌های ۳بعدی، نقشهٔ ماهواره‌ای لینک‌دار، نمودارهای پویا.

---

## برنامهٔ تفکیک‌شده با جزئیات

### بخش ۱: افزودن متریک‌های علمی دقیق‌تر

**هدف:** گسترش لیست متریک‌ها از ۵ به ۱۰ مورد با جزئیات واحد‌اندازه‌گیری استاندارد و فیلدهای پیشرفته.

**محتوا (impactcarbon.ts) — افزودن به آرایه `metrics`:**

| متریک (fa) | Metric (en) | واحد | استاندارد | Data Source |
|------------|-------------|------|-----------|-------------|
| هکتار زیر پایش | Hectares under monitoring | ha | Sentinel-2 tile | Copernicus CDS |
| کشاورز آموزش‌دیده | Farmers trained | people | — | KoBo field forms |
| اعتبار کربن صادرشده | Carbon credits issued | credits | Verra/Puro | Registry API |
| بهبود شاخص پوشش گیاهی | Vegetation index improvement | ΔNDVI | ESA CCI | Sentinel-2 L2A |
| صرفه‌جویی آب | Water saved | m³ | FAO-56 | Soil + ERA5 |
| انتشار جلوگیری‌شده CO₂ | CO₂ sequestration | tCO₂e | IPCC 2019 | RothC model |
| درصد پوشش گیاهی | Vegetation cover | % | CGLS | Sentinel-2 |
| صرفه‌جویی انرژی | Energy saved | kWh | — | Model-based |
| تنوع زیستی | Biodiversity index | score | — | Field surveys |
| رضایت کشاورز | Farmer satisfaction | NPS | NPS | Survey |

**فیلدهای جدید در `ImpactMetric`:**
```typescript
interface ImpactMetric {
  name: string;
  desc: string;
  unit: string;
  source?: string;     // منبع داده
  method?: string;     // روش محاسبه
  standard?: string;  // استاندارد بین‌المللی
  frequency?: string;  // فرکانس به‌روزرسانی
  apiField?: string;   // نام فیلد در API برای داده زنده
}
```

**فایل هدف:** `frontend/src/content/pages/impactcarbon.ts`

---

### بخش ۲: نمودار MRV (Measurement-Reporting-Verification)

**هدف:** نمایشگر مصوت SVG که چرخهٔ MRV را نشان می‌دهد با انیمیشن گردش.

**کامپوننت جدید:** `frontend/src/components/visuals/MrvCycleChart.tsx`

**طراحی:**
- دایره‌ای با ۳ بخش مداوم: Measurement (📡) → Reporting (📊) → Verification (✅)
- انیمیشن گردش مداوم با Framer Motion (`animate: { rotate: 360 }`)
- هر بخش با آیکن lucid متفاوت و رنگ متفاوت (leaf-500, aqua-500, sand-500)
- برچسب واضح: «MRV cycle based on ISO 14064-2»
- وضعیت زنده: "Live" یا "Conceptual sample" بسته به اتصال به API

**استفاده در ImpactPage:** قبل از نمودارهای زمان‌سری.

---

### بخش ۳: شمارنده‌های زنده (Live Counters)

**هدف:** نمایش شمارنده‌های عددی زنده با انیمیشن شمارش برای متریک‌های کلیدی.

**کامپوننت جدید:** `frontend/src/components/visuals/LiveCounters.tsx`

**طراحی:**
- ۴ شمارنده بزرگ با انیمیشن شمارش (count-up)
- استفاده از Framer Motion برای انیمیشن `useSpring` یا `AnimateNumber`
- منابع داده:
  - `ha` — از API `/api/v1/impact/area`
  - `people` — از API `/api/v1/impact/farmers`
  - `tCO₂e` — از API `/api/v1/impact/carbon`
  - `credits` — از API `/api/v1/impact/credits`
- در حالت conceptual، اعداد ثابت اما با برچسب "Conceptual sample"
- در حالت live، درخواست‌های polling به API هر ۳۰ ثانیه

**طراحی رابط:**
```
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   ۱۲,۵۰۰    │ │   ۷۸۴      │ │  ۲۵.۳      │ │   ۱۴۲     │
│ هکتار زیر   │ │ کشاورز     │ │ تن CO₂eq    │ │ اعتبار     │
│ پایش         │ │ آموزش‌دیده  │ │ ثبت‌شده    │ │ صادرشده   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

---

### بخش ۴: نمودارهای زمان‌سری (Time-Series Charts)

**هدف:** نمایش داده‌های واقعی یا نمونه برای شاخص‌های کلیدی مانند NDVI، NDWI، SOC.

**وضعیت وابستگی:** هیچ کتابخانه‌ای برای نمودار در `package.json` موجود نیست.

**راه‌حل:** استفاده از SVG hand-coded مشابل NdviConceptChart — بدون افزودن dependency جدید.

**کامپوننت جدید:** `frontend/src/components/visuals/ImpactTimeSeries.tsx`

**طراحی:**
- ۴ تب قابل切:
  - NDVI trend (ماهانه، ۱۰ سال) — رنگ leaf
  - NDWI trend (فصلی) — رنگ aqua
  - Carbon stock (خاک، سالانه) — رنگ sand
  - Water savings (ماهانه) — رنگ leaf-400
- انیمیشن path draw با Framer Motion
- دکمه Refresh دستی برای دریافت آخرین داده از API
- برچسب واضح: "Conceptual sample" یا "Live from Sentinel-2"
- داده‌های نمونه در `frontend/src/content/pages/impactcarbon.ts` زیر فیلد `sampleTimeSeries`

---

### بخش ۵: نقشهٔ ماهواره‌ای لینک‌دار (Satellite Map)

**هدف:** نقشه‌ای از پوشش گیاهی ماهواره‌ای با لینک به سرویس‌های خارجی.

**وضعیت وابستگی:** هیچ کتابخانه نقشه در `package.json` نیست.

**راه‌حل فاز ۱:** SVG map با لایهٔ پوشش گیاهی به‌صورت heatmap + مارکرهای پروژه.

**کامپوننت جدید:** `frontend/src/components/visuals/SatelliteMap.tsx`

**طراحی:**
- SVG container با لایهٔ heatmap پوشش گیاهی (NDVI) — رنگ‌های leaf-300 تا leaf-700
- مارکرهای پروژه با رنگ‌بندی بر اساس نوع:
  - 🌱 Forest restoration — رنگ leaf-500
  - 💧 Wetland restoration — رنگ aqua-500
  - 🌾 Sustainable agriculture — رنگ sand-400
- هر مارکر clickable — tooltip با اطلاعات خلاصه
- **لینک به سرویس ماهواره‌ای:**
  - Sentinel Hub EO Browser: `https://apps.sentinel-hub.eu/eo-browser/?zoom=12&lat={lat}&lng={lng}`
  - Copernicus Data Space: `https://dataspace.copernicus.eu/`
  - کلید «View on Sentinel Hub» در هر مارکر
- برچسب واضح: "Satellite view — conceptual overlay, real imagery via Copernicus"

**طراحی ۳بعدی (CSS):**
- استفاده از CSS `transform: perspective` برای حس عمق
- افکت parallax در اسکرول
- glow effect همانند FieldScene

---

### بخش ۶: کارت‌های ۳بعدی تعامتی (3D Interactive Cards)

**هدف:** کارت‌هایی با حس عمق ۳بعدی برای نمایش متریک‌ها و نتایج.

**کامپوننت:** `ImpactMetricCard.tsx` (استفاده در grid متریک‌ها)

**طراحی CSS ۳بعدی:**
- `transform-style: preserve-3d`
- `perspective: 1000px`
- افکت چرخش روی hover (rotateY / rotateX)
- گوشه‌های گرد و shadow پویا
- لایهٔ نور پس‌زمینه با CSS gradient
- رابط برای نمایش مقدار، واحد، روند (↑/↓) و برچسب

**ایدهٔ ۳بعدی:**
```
┌─────────────────────────┐
│  متریک: CO₂ sequestration │
│  مقدار: ۲۵.۳ tCO₂e       │
│  روند: ↑ ۱۲٪ نسبت به ماه  │
└─────────────────────────┘
  (card flips on hover → shows methodology)
```

---

### بخش ۷: جعبهٔ گزارش کارشناسی (MRV Report Box)

**هدف:** نمایش یا دانلود گزارش MRV فنی.

**کامپوننت:** `ImpactReportBox.tsx`

**قابلیت‌ها:**
- Preview کوتاه گزارش MRV با فرمت مناسب
- دکمه دانلود: CSV (native Blob) و PDF (jsPDF — dependency اضافی در فاز ۲)
- فیلتر بر حسب تاریخ و مکان (در فاز ۲)
- برچسب واضح: "Reports generate with live data after pilot begins"
- استفاده از `Blob` API برای CSV (بدون dependency)

---

### بخش ۸: بخش شفافیت داده (Data Transparency)

**هدف:** نمایش منبع داده و روش محاسبه برای هر متریک.

**کامپوننت:** `ImpactDataProvenance.tsx`

**طراحی:**
- جدول یا آکاردئون برای هر متریک
- ستون‌ها: Metric | Data Source | Method | Standards | Frequency
- مثال:
  | NDVI | Sentinel-2 L2A (CDSE) | ESA NASA Nadir BRDF | ESA CCI | Daily |
- قابلیت گسترش برای نمایش جزئیات فنی کامل

---

### بخش ۹: به‌روزرسانی محتوا (impactcarbon.ts)

افزودن فیلدهای جدید به `ImpactContent`:

```typescript
interface ImpactContent {
  // ... existing fields
  liveCounters: {
    title: string;
    note: string;
    items: { label: string; metric: string; apiField: string; unit: string }[];
  };
  mrvCycle: { title: string; desc: string };
  chartsTitle: string;
  chartsNote: string;
  mapTitle: string;
  mapNote: string;
  reportTitle: string;
  reportNote: string;
  transparencyTitle: string;
  transparencyNote: string;
  projects: { name: string; lat: number; lng: number; type: string; status: string }[];
  metrics: ImpactMetric[];
  sampleTimeSeries: {
    ndvi: number[];
    ndwi: number[];
    carbon: number[];
    water: number[];
    months: string[];
  };
}
```

---

### بخش ۱۰: به‌روزرسانی ImpactPage.tsx

ترتیب نهایی بخش‌ها:

| شماره | بخش | کامپوننت |
|-------|------|----------|
| 1 | PageHeader | PageHeader |
| 2 | شمارنده‌های زنده | LiveCounters |
| 3 | متریک‌های تعریف‌شده (3D cards) | grid افقی با ImpactMetricCard |
| 4 | چرخهٔ MRV | MrvCycleChart |
| 5 | نمودارهای زمان‌سری | ImpactTimeSeries |
| 6 | نقشهٔ ماهواره‌ای | SatelliteMap |
| 7 | گزارش کارشناسی | ImpactReportBox |
| 8 | روش‌اندازی | همان glass box |
| 9 | گالری میدانی | FieldGallery + NdviConceptChart |
| 10 | شفافیت داده | ImpactDataProvenance |
| 11 | CtaBand | CtaBand |

---

## برنامه زمان‌بندی

| هفته | بخش | زمان تخمینی |
|------|------|-------------|
| هفته ۱ | بررسی dependencies، به‌روزرسانی محتوا (۱۰ متریک + فیلدهای جدید) | ۳ ساعت |
| هفته ۲ | LiveCounters + MrvCycleChart + ImpactMetricCard (3D cards) | ۵ ساعت |
| هفته ۳ | ImpactTimeSeries (SVG) + SatelliteMap (SVG + links) | ۷ ساعت |
| هفته ۴ | ImpactReportBox + DataProvenance + Integration در ImpactPage | ۴ ساعت |
| هفته ۵ | تست، responsive، بهینه‌سازی | ۲ ساعت |

> **یادداشت وابستگی‌ها:** تمام کامپوننت‌های تصویری با SVG hand-coded + Framer Motion ساخته می‌شوند (مانند NdviConceptChart و FieldScene). هیچ dependency جدیدی در فاز ۱ نصب نمی‌شود. افزودن کتابخانه‌های نقشه (Leaflet), نمودار (Recharts), یا PDF (jsPDF) در فاز ۲ برنامه‌ریزی شده است.

---

## معیارهای تایید (Acceptance Criteria)

```sh
cd frontend
npx tsc --noEmit          # انتظار صفر خطا
npx eslint src/           # انتظار ۰ خطا
npx vitest run            # انتظار ۳۰/۳۰ آزمون قبلی + ۵ آزمون جدید برای صفحه impact
npx vite build            # انتظار سخت‌سازی موفقیت‌آمیز (< 3MB)
npx vite preview          # بررسی دستی: http://localhost:5173/impact
```

---

## نکات فنی

- تمام کامپوننت‌های جدید از `framer-motion` استفاده می‌کنند (Reveal pattern موجود)
- رنگ‌ها باید از CSS variables تعریف‌شده در `index.css` استفاده کنند: `var(--color-leaf-500)`, `var(--color-aqua-500)`, `var(--color-sand-400)`، ...
- کامپوننت‌های جدید باید از الگوی `t = useLang()` استفاده کنند
- تمام گرافیک‌ها باید برچسب واضح داشته باشند: "Conceptual sample" یا "Live data"
- نقشه ماهواره‌ای باید لینک به **Sentinel Hub EO Browser** داشته باشد: `https://apps.sentinel-hub.eu/eo-browser/`
- شمارنده‌های زنده باید با polling به API `/api/v1/impact/*` متصل شوند
- کارت‌های ۳بعدی باید در موبایل (touch) حس بصیرتی نداشته باشند (استفاده از `@media (hover: hover)`)

---

## استانداردهای بین‌المللی ارجاع‌شده

| استاندارد | کاربرد در صفحه |
|----------|---------------|
| ISO 14064-2 | چرخه MRV و اعتبار کربن |
| IPCC 2019 Refinement | محاسبه انتشار CO₂ |
| GHG Protocol | گزارش‌گیری گازهای گلخانه‌ای |
| ICVCM | استانداردهای اعتبار کربن |
| Copernicus | منبع داده ماهواره‌ای Sentinel-2/1 |
| FAIR Data | شفافیت داده و DataProvenance |
| WCAG 2.1 | دسترسی و رنگ‌ها و کیبورد ناوبری |
