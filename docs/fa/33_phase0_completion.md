# 33. فاز صفر — تثبیت و هماهنگی فرانت‌اند (Phase 0 Completion)

**تاریخ:** ۲۰۲۶-۰۸-۲۶ | **وضعیت:** انجام‌شده | **نویسنده:** ماهک (AI coworker)

## ۱. هدف

فاز ۰ از «راهکار توسعه و هماهنگی شبیه‌ساز با پروژه» (سند `eco_nojin_development_plan.md`) —
از بین بردن ناهماهنگی‌های ساختاری فرانت‌اند تا **همه صفحات از نقطه ورود قابل دسترسی** باشند
(قانون Zero Orphan Files) و اتصال فرانت به بک‌اند بدون آدرس هاردکد انجام شود.

## ۲. تغییرات انجام‌شده

### ۲.۱ نقشه روت کامل (`frontend/src/App.tsx`)

- افزودن روت `/virtual-lab` برای **VirtualLandLabPage** (صفحه اصلی شبیه‌ساز «آزمایشگاه مجازی زمین») — پیش از این ایمپورت شده بود ولی روت نداشت.
- افزودن روت‌های ۱۵ صفحهٔ اورفان قبلی:
  `/terrain`، `/visualization-3d`، `/models`، `/models/rothc`، `/models/swat`،
  `/models/watershed`، `/land-profiles`، `/capability`، `/monitoring`، `/reports`،
  `/data`، `/api-docs`، `/settings`، `/simulators`، `/profile`، `/hydroma-about`، `/help`، `/support`.
- صفحات کاربردی زیر `ProtectedRoute` (نیازمند ورود) و صفحات عمومی بدون محافظت.
- نقشه کامل روت‌ها به README اضافه شد.

### ۲.۲ حذف صفحات تکراری/منسوخ (اورفان)

حذف فایل‌هایی که هیچ ارجاعی به آن‌ها وجود نداشت (تأیید با grep در کل `frontend/src`):

- `pages/LoginPage.tsx`، `pages/RegisterPage.tsx`، `pages/ForgotPasswordPage.tsx` (نسخهٔ اصلی در `pages/auth/` است)
- `pages/AboutUs.tsx`، `pages/Blog.tsx`، `pages/Contact.tsx`، `pages/Mission.tsx`، `pages/Privacy.tsx`، `pages/Terms.tsx` (نسخهٔ اصلی `*Page.tsx` است)
- `pages/SettingsPage.tsx` (نسخهٔ `Settings.tsx` نگه داشته شد)
- `pages/Dashboard.tsx` (جای آن `HydromaDashboard` و `SimulatorDashboard` است)

### ۲.۳ حذف آدرس هاردکد بک‌اند

- فایل جدید `frontend/src/config.ts` با `API_BASE_URL` (از `VITE_API_BASE_URL` با fallback محلی).
- `frontend/.env.example` ساخته شد.
- `VirtualLandLabPage.tsx`: فراخوانی `fetch` از آدرس ثابت به `API_BASE_URL` منتقل شد.
- `services/simulatorApi.ts`: `API_BASE` از متغیر محیطی خوانده می‌شود.
- `vite.config.ts`: پراکسی توسعه `/api → http://localhost:8000` اضافه شد.

### ۲.۴ ناوبری سایدبار (`components/layout/Sidebar.tsx`)

- هر آیتم منو به یک مسیر واقعی متصل شد (`useNavigate` از react-router):
  داشبورد ← `/hydroma`، برنامه کشت ← `/models`، مدیریت آب ← `/models/watershed`،
  فرسایش ← `/terrain`، دامداری ← `/simulator`، کربن ← `/models/rothc`،
  نقشه‌ها ← `/virtual-lab`، گزارش‌ها ← `/reports`، تنظیمات ← `/settings`.

### ۲.۵ مستندات

- README اصلاح شد: فرانت‌اند **Vite + React 19** (نه Next.js) + جدول مسیرها.
- این سند (`docs/fa/33_phase0_completion.md`) ثبت شد.

## ۳. صحت‌سنجی

- `pnpm -C frontend build` (tsc + vite build) **با موفقیت** انجام شد — ۶۳۵۷ ماژول، بدون خطای کامپایل.
- بررسی شد که هیچ صفحه‌ای بدون روت باقی نمانده است (`AuthShell` یک کامپوننت مشترک است و از صفحات auth ایمپورت می‌شود).
- همه روت‌های جدید با صفحه‌های واقعی (exportهای named/default بررسی‌شده) مطابقت دارند.
- خروجی تولید: `frontend/dist/index.html` ساخته شد.

### ۳.۱ اصلاح خطاهای TypeScript legacy (پیش‌نیاز بیلد)

پروژه از قبل **هرگز با `tsc -b` کامپایل نمی‌شد** — ۴۲ خطای TypeScript در سراسر کدبیس وجود داشت. در فاز ۰ همه اصلاح شد:

- ۳۰+ ایمپورت/پارامتر استفاده‌نشده (TS6133) در صفحات و کامپوننت‌ها حذف شد.
- `WatershedMap` به `react-map-gl` (نصب‌نشده) وابسته بود → با **MapLibre GL مستقیم** بازنویسی شد.
- `NDVIHeatmap` و `CarbonSequestrationChart` فاقد تایپ Props بودند → interface اضافه شد.
- `Button` با framer-motion تداخل handlerهای drag/animation داشت → handlerهای متعارض جدا شدند.
- باگ‌های تایپی (boxGeometry، zIndex، RainDrops و…) اصلاح شدند.

**هشدار باقی‌مانده (غیرمسدودکننده):** باندل ۴.۲MB — برای فازهای بعدی code-splitting با `lazy()` پیشنهاد می‌شود.

## ۴. گام‌های بعدی (فاز ۱)

اتصال داده واقعی ماهواره (CDSE/GEE)، SoilGrids و ERA5؛ سپس زنجیره کامل مدل‌های علمی (فاز ۲).
