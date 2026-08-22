# توسعه صفحات مدیریتی (Admin) — مستندسازی تغییرات

**تاریخ:** 2026-08-22
**محدوده:** `frontend/components/site/` و `frontend/app/admin/`
**نوع تغییر:** جایگزینی صفحات Placeholder با پیاده‌سازی واقعی متصل به بک‌اند

---

## ۱) خلاصه

۹ صفحه از بخش `/admin` فقط Placeholder بودند (اعلام «در فاز بعدی ساخته می‌شود»). در این مرحله دو صفحه که بک‌اند آماده داشتند، با پیاده‌سازی کامل جایگزین شدند:

| صفحه | وضعیت قبل | وضعیت بعد |
|---|---|---|
| `/admin/farms` | Placeholder (فاز ۶) | مدیریت کامل مزرعه‌ها (CRUD) |
| `/admin/analytics` | Placeholder (فاز ۵) | داشبورد تحلیلی با نمودار |

---

## ۲) فایل‌های ایجاد شده

### ۲.۱ `components/site/AdminFarms.tsx` (جدید)

مدیریت مزرعه‌ها با اتصال کامل به API بک‌اند:

- **فهرست مزرعه‌ها** — جدول با نام، مختصات، مساحت، نوع خاک و اقلیم
- **افزودن مزرعه** — فرم مودال با اعتبارسنجی فیلدهای الزامی (نام، عرض/طول جغرافیایی، مساحت)
- **حذف مزرعه** — با تأیید از طریق mutation و toast
- **وضعیت‌های UI** — بارگذاری، خطا، خالی و «وارد نشده‌اید»

Endpoints استفاده‌شده: `GET/POST /api/v1/farms/` و `DELETE /api/v1/farms/{id}`

### ۲.۲ `components/site/AdminAnalytics.tsx` (جدید)

داشبورد تحلیلی با نمودار recharts:

- **۶ کارت آمار کلی** — مزرعه‌ها، تحلیل خاک، تحلیل ماهواره‌ای، اجرای سناریو، پروژه کربن، میانگین سلامت خاک
- **نمودار روند سلامت خاک** — LineChart از `soil-trends`
- **نمودار روند NDVI** — LineChart از `ndvi-trends`
- **توزیع سلامت خاک** — نوار پیشرفت از `performance-metrics`
- **خلاصه کربن** — کارت‌ها و فهرست پروژه‌ها از `carbon-summary`

Endpoints استفاده‌شده: `/api/v1/analytics/overview`، `/soil-trends`، `/ndvi-trends`، `/performance-metrics`، `/carbon-summary`

### ۲.۳ فایل‌های صفحه (بازنویسی)

- `app/admin/farms/page.tsx` — از `AdminPlaceholder` به `AdminFarms` تغییر کرد
- `app/admin/analytics/page.tsx` — از `AdminPlaceholder` به `AdminAnalytics` تغییر کرد

---

## ۳) هم‌راستایی با بک‌اند

- schema مزرعه دقیقاً مطابق `services/api_gateway/routers/farms.py` (`FarmCreate` / `FarmOut`) است:
  `name`, `latitude`, `longitude`, `elevation_m`, `area_hectares`, `soil_type`, `climate_zone`.
- پاسخ‌های analytics دقیقاً مطابق `services/api_gateway/routers/analytics.py` است.
- الگوی کد (token از localStorage، `apiUrl()`، react-query، کامپوننت‌های shadcn/ui) با کامپوننت‌های موجود مانند `AdminUsers.tsx` و `AdminOverview.tsx` یکسان است.

---

## ۴) تأیید صحت

- **ESLint:** روی ۴ فایل بدون خطا (exit 0).
- **TypeScript (`tsc --noEmit`):** هیچ خطایی در فایل‌های جدید گزارش نشد (خطاهای موجود در پروژه مربوط به فایل‌های دیگر و از قبل موجود بودند).

---

## ۵) یادداشت

- برچسب‌های این صفحات به فارسی نوشته شده‌اند (هماهنگ با سایر کامپوننت‌های بخش admin مانند `AdminUsers.tsx` که پیش‌تر فارسی هاردکد بودند). انتقال آن‌ها به سیستم i18n (`t()`) می‌تواند در مرحله بعدی انجام شود.
- ۷ صفحه Placeholder باقی‌مانده (`translations`, `docs`, `data`, `logs`, `roles`, `backup`, `alerts`) هنوز endpoint آماده در بک‌اند ندارند و در انتظار توسعه بک‌اند هستند.
