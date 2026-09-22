# گزارش مطالعه و برنامه توسعه فرانت‌اند اکو نوژین / HyDroMa

**تاریخ:** ۱۷ سپتامبر ۲۰۲۶  
**محدوده:** `frontend/`، صفحات عمومی، احراز هویت، بازارگاه، داشبورد علمی، پنل مدیریت، API clientها و تست‌های UI

## ۱. خلاصه مدیریتی

### وضعیت پس از اجرای P0/P1/P2

اولویت‌های اصلی این گزارش در همین نوبت پیاده‌سازی شدند:

- خطاهای TypeScript برطرف شد و `pnpm type-check` سبز است.
- runnerهای MRV به client مشترک و مسیرهای فعلی backend متصل شدند.
- TrustBand در صفحه خانه فعال شد.
- focus-visible، aria state و live region برای accessibility اضافه شد.
- پاسخ observations برای transparency با قرارداد واقعی MRV تطبیق داده شد.
- PWA از cache کردن پاسخ‌های `/api/` جلوگیری می‌کند.
- build production و تست frontend با worker محدود موفق شدند.

شواهد نهایی:

- `pnpm type-check`: موفق
- `pnpm build`: موفق؛ service worker تولید شد
- Vitest منتخب با یک worker: ۹۸ تست موفق از ۹۸ تست

ریسک‌های باقی‌مانده: هشدار chunkهای بزرگ dashboard/chart، هشدار mock مربوط به `whileHover` در تست UniversalCard، و باقی‌ماندن ۲۳ مورد accessibility ثبت‌شده در audit کامل که نیازمند اجرای axe مجدد هستند.

فرانت‌اند پروژه یک محصول بزرگ چندلایه است، نه یک صفحه وب ساده. ساختار فعلی شامل این بخش‌هاست:

- وب‌سایت عمومی با صفحات خانه، پلتفرم، HyDroMa، اثرگذاری، کربن، شفافیت، بلاگ، FAQ، تماس، راهنماها و صفحات حقوقی
- احراز هویت، ثبت‌نام، بازیابی و تغییر رمز
- داشبورد علمی با حدود ۶۱ مسیر مدل در دسته‌های شاخص‌ها، فرمول‌ها، خاک، آب، شبیه‌سازی، کربن، اقلیم و اقتصاد
- داشبورد زنده برای ماهواره، خاک، کربن، ET0، زنجیره علمی و پایش
- بازارگاه، سبد خرید، پرداخت، سفارش، فروشنده و مدیریت بازارگاه
- پنل ادمین برای کاربران، فروشندگان، تراکنش‌ها، مدل‌ها، امنیت، گزارش‌ها و سلامت پلتفرم
- پشتیبانی فارسی/انگلیسی، RTL/LTR، PWA، خروجی داده و تست‌های accessibility/e2e

وضعیت فعلی از نظر معماری امیدوارکننده است، اما برای توسعه پایدار ابتدا باید سه خطر برطرف شود:

1. خطاهای TypeScript که build را متوقف می‌کنند.
2. ناهماهنگی مسیرهای API فرانت‌اند و backend، مخصوصاً در MRV.
3. ضعف‌های accessibility، تست و برخی صفحات نیمه‌متصل یا دارای داده mock.

## ۲. شواهد فنی فعلی

### TypeScript

در اجرای اولیه `pnpm type-check`، **۱۷ خطا در ۸ فایل** وجود داشت. این خطاها اکنون برطرف شده‌اند؛ فایل‌های مهم این اصلاح عبارت‌اند از:

- [AccessibilityMenu.tsx](../frontend/src/components/sections/AccessibilityMenu.tsx): state استفاده‌نشده
- [useBilingual.ts](../frontend/src/hooks/useBilingual.ts): import استفاده‌نشده و خطای indexing/type safety
- [LanguageContext.tsx](../frontend/src/i18n/LanguageContext.tsx): import استفاده‌نشده
- [CommerceOrdersPage.tsx](../frontend/src/pages/dashboard/commerce/CommerceOrdersPage.tsx): handler/state استفاده‌نشده
- [CommercePaymentsPage.tsx](../frontend/src/pages/dashboard/commerce/CommercePaymentsPage.tsx): handler استفاده‌نشده
- [CommerceSettlementsPage.tsx](../frontend/src/pages/dashboard/commerce/CommerceSettlementsPage.tsx): مقدار `isFa` استفاده‌نشده
- [CommerceShippingPage.tsx](../frontend/src/pages/dashboard/commerce/CommerceShippingPage.tsx): `setActionLoading` تعریف نشده و چند مقدار استفاده‌نشده
- [EcoCoinPage.tsx](../frontend/src/pages/EcoCoinPage.tsx): فیلد `verificationLabel` در type محتوا تعریف نشده

پس از اصلاح، `pnpm type-check` و `pnpm build` هر دو موفق هستند.

### تست‌ها

اجرای اولیه تست‌های Vitest به این نتیجه رسید:

- ۱۴۸ تست موفق از ۱۶۸ تست
- ۱ تست شکست‌خورده: `AdminReportsPage > renders page title`
- خطای timeout در همان تست و سپس JavaScript heap out of memory
- هشدار React درباره عبور propهای Framer Motion مانند `whileHover` به DOM

پس از اجرای تست با worker محدود:

- ۹۸ تست منتخب موفق از ۹۸ تست
- تست `AdminReportsPage` موفق شد
- خطای OOM در اجرای تک‌worker تکرار نشد

فایل‌های مرتبط:

- [admin.test.tsx](../frontend/src/test/admin.test.tsx)
- [AdminReportsPage.tsx](../frontend/src/pages/dashboard/admin/AdminReportsPage.tsx)
- [components.test.tsx](../frontend/src/test/components.test.tsx)
- [queryClient.tsx](../frontend/src/lib/queryClient.tsx)

### Accessibility

گزارش axe قبلی، ۲۳ violation نشان می‌دهد:

- ۷ مورد Critical
- ۱۱ مورد Serious
- ۵ مورد Moderate
- مشکل contrast، label فرم، focus، keyboard navigation، zoom، heading hierarchy و skip link

مرجع:

- [wcag_audit_2026-09-11.md](../frontend/tests/accessibility/wcag_audit_2026-09-11.md)

## ۳. معماری فعلی

### نقطه ورود و shell

- [main.tsx](../frontend/src/main.tsx): mount، StrictMode و ErrorBoundary
- [App.tsx](../frontend/src/App.tsx): providerها، routeها، shell عمومی، auth shell و dashboard shell
- [DashboardGate.tsx](../frontend/src/components/auth/DashboardGate.tsx): حفاظت مسیرهای داشبورد
- [AdminGate.tsx](../frontend/src/components/auth/AdminGate.tsx): حفاظت نقش admin
- [DashboardLayout.tsx](../frontend/src/components/dashboard/DashboardLayout.tsx): پوسته داشبورد
- [PublicLayout.astro](../frontend/src/layouts/PublicLayout.astro) و فایل‌های `.astro`: بخشی از مسیر Astro/SSG

نکته مهم: پروژه هم‌زمان الگوی React/Vite و Astro را دارد. این دو مسیر باید از نظر مالکیت route، SEO، build و deploy مستندسازی و یکپارچه شوند؛ در غیر این صورت یک صفحه ممکن است در دو سیستم تعریف شود.

### API و داده

لایه‌های API متعدد وجود دارند:

- [api.ts](../frontend/src/lib/api.ts)
- [hydromaApi.ts](../frontend/src/lib/hydromaApi.ts)
- [hydromaEngine.ts](../frontend/src/lib/hydromaEngine.ts)
- [hydromaIndices.ts](../frontend/src/lib/hydromaIndices.ts)
- [marketplaceApi.ts](../frontend/src/lib/marketplaceApi.ts)
- [inventoryApi.ts](../frontend/src/lib/inventoryApi.ts)
- [financeApi.ts](../frontend/src/lib/financeApi.ts)
- [commerceApi.ts](../frontend/src/lib/commerceApi.ts)
- [statusApi.ts](../frontend/src/lib/statusApi.ts)
- [transparencyApi.ts](../frontend/src/lib/transparencyApi.ts)

پراکندگی clientها باعث تکرار fetch، مدیریت متفاوت خطا، نبود contract typing یکپارچه و دشواری refresh token می‌شود.

## ۴. صفحات و فایل‌هایی که باید توسعه پیدا کنند

### P0: ضروری قبل از توسعه قابلیت جدید

#### ۴.۱ رفع خطاهای TypeScript و build

فایل‌های مستقیم: همان ۸ فایل بخش شواهد فنی، مخصوصاً:

- `src/hooks/useBilingual.ts`
- `src/pages/dashboard/commerce/CommerceShippingPage.tsx`
- `src/pages/EcoCoinPage.tsx`
- `src/components/sections/AccessibilityMenu.tsx`

خروجی مورد انتظار:

- `pnpm type-check` بدون خطا
- `pnpm build` موفق
- حذف `any` و type assertionهای غیرضروری

#### ۴.۲ یکسان‌سازی APIهای MRV — انجام شد

در حال حاضر runnerهای زیر مسیرهایی دارند که با backend فعلی هم‌نام نیستند:

- [MrvCitizenRunner.tsx](../frontend/src/components/dashboard/MrvCitizenRunner.tsx)
- [MrvIotRunner.tsx](../frontend/src/components/dashboard/MrvIotRunner.tsx)
- [MrvMetricsRunner.tsx](../frontend/src/components/dashboard/MrvMetricsRunner.tsx)
- [MrvQaRunner.tsx](../frontend/src/components/dashboard/MrvQaRunner.tsx)

مسیرهای قدیمی مشاهده‌شده:

- `/api/v1/mrv/citizen/report`
- `/api/v1/mrv/iot/ingest`
- `/api/v1/mrv/metrics`
- `/api/v1/mrv/qa/screen`

قرارداد فعلی backend مسیرهایی مانند این‌ها دارد:

- `/api/v1/mrv/citizen-report`
- `/api/v1/mrv/iot-reading`
- `/api/v1/mrv/dashboard-metrics`
- `/api/v1/mrv/satellite-index`
- `/api/v1/mrv/observations`

این کار با [mrvApi.ts](../frontend/src/lib/mrvApi.ts) انجام شد و runnerها اکنون از adapter مشترک استفاده می‌کنند. این adapter قراردادهای متفاوت UI و backend را به‌صورت متمرکز تبدیل می‌کند.

#### ۴.۳ تکمیل تست AdminReports و کنترل حافظه

فایل‌های هدف:

- [AdminReportsPage.tsx](../frontend/src/pages/dashboard/admin/AdminReportsPage.tsx)
- [admin.test.tsx](../frontend/src/test/admin.test.tsx)
- [AdminLayout.tsx](../frontend/src/components/admin/AdminLayout.tsx)

کار لازم:

- mock کردن fetch و auth در سطح تست
- جلوگیری از polling یا request تکراری بدون cleanup
- افزودن `AbortController` در effectهای async
- اجرای تست با worker محدود و سپس بررسی نشتی حافظه
- اصلاح propهای motion که به DOM منتقل می‌شوند

### P1: تجربه کاربری و دسترسی‌پذیری

#### ۴.۴ پوسته عمومی و ناوبری — بخش اصلی انجام شد

فایل‌های هدف:

- [App.tsx](../frontend/src/App.tsx)
- [PublicLayout.astro](../frontend/src/layouts/PublicLayout.astro)
- [Navbar.tsx](../frontend/src/components/layout/Navbar.tsx)
- [Footer.tsx](../frontend/src/components/layout/Footer.tsx)
- [index.css](../frontend/src/index.css)

کار لازم:

- افزودن skip-to-content واقعی
- focus ring یکنواخت و قابل مشاهده
- بررسی heading hierarchy در صفحات طولانی
- اصلاح responsive layout در عرض ۳۲۰ پیکسل
- حذف محدودیت zoom از meta viewport
- افزودن live region استاندارد برای Toast و اعلان‌ها

Skip link و امکان zoom در کد فعلی از قبل وجود داشتند؛ focus-visible سراسری، aria-expanded/aria-pressed و roleهای Toast نیز اضافه شدند.

#### ۴.۵ کامپوننت‌های فرم و جست‌وجو

فایل‌های هدف:

- `src/components/ui/SearchInput.tsx`
- `src/components/dashboard/FilterPanel.tsx`
- `src/components/ui/SearchModal.tsx`
- `src/components/sections/AutocompleteSearch.tsx`
- `src/components/ui/Toast.tsx`

کار لازم:

- label صریح یا `aria-label` برای همه inputها
- مدیریت focus در modal/dropdown
- keyboard navigation کامل با Escape، Tab، Enter و Arrow keys
- پیام خطای قابل فهم و متصل به input با `aria-describedby`

#### ۴.۶ داشبورد علمی و ناوبری مدل‌ها

فایل‌های هدف:

- [DashboardPage.tsx](../frontend/src/pages/DashboardPage.tsx)
- [dashboardRoutes.tsx](../frontend/src/routes/dashboardRoutes.tsx)
- [CategoryTree.tsx](../frontend/src/components/dashboard/CategoryTree.tsx)
- [DashboardLayout.tsx](../frontend/src/components/dashboard/DashboardLayout.tsx)
- [hydromaregistry.ts](../frontend/src/lib/hydromaregistry.ts)

وضعیت: پوشش مدل‌ها گسترده است، اما صفحه اصلی طولانی و مسیرهای مدل زیاد هستند.

کار لازم:

- drawer یا bottom sheet مناسب موبایل برای navigation
- breadcrumb در صفحات مدل
- فیلتر «فقط مدل‌های قابل اجرا»
- نمایش وضعیت API، latency و provenance در هر runner
- empty/error/loading state یکپارچه
- lazy loading واقعی در سطح routeهای model، نه فقط import مرکزی

### P1: اتصال واقعی قابلیت‌ها

#### ۴.۷ صفحات Live و MRV

فایل‌های هدف:

- `src/pages/dashboard/live/LiveSatellitePage.tsx`
- `src/pages/dashboard/live/LiveCarbonPage.tsx`
- `src/pages/dashboard/live/LiveSciencePage.tsx`
- `src/pages/dashboard/monitoring/LiveMonitoringPage.tsx`
- `src/pages/dashboard/carbon/*`
- `src/lib/hydromaApi.ts`
- `src/lib/transparencyApi.ts`

کار لازم:

- اتصال همه صفحات به endpointهای واقعی با قرارداد واحد
- برچسب روشن real/simulated/no_data
- retry/backoff و نمایش خطای قابل اقدام
- refresh دستی و polling کنترل‌شده
- جلوگیری از نمایش داده mock به‌عنوان داده واقعی

#### ۴.۸ بازارگاه و commerce

فایل‌های هدف:

- `src/pages/marketplace/*`
- `src/pages/dashboard/commerce/*`
- `src/lib/marketplaceApi.ts`
- `src/lib/commerceApi.ts`
- `src/lib/paymentsApi.ts`

کار لازم:

- تکمیل actionهای سفارش، پرداخت، ارسال و settlement
- رفع خطاهای TypeScript فعلی در صفحات commerce
- stateهای loading/disabled برای عملیات حساس مالی
- idempotency و پیام خطای backend در UI
- تست مسیر کامل catalog → cart → checkout → payment → tracking

نکته: در [AdminPanel.tsx](../frontend/src/pages/marketplace/AdminPanel.tsx) متن `Order management coming soon` وجود دارد؛ این بخش هنوز تکمیل نشده و نباید در navigation اصلی به‌عنوان قابلیت کامل نمایش داده شود.

#### ۴.۹ احراز هویت و حساب کاربری

فایل‌های هدف:

- [AuthContext.tsx](../frontend/src/context/AuthContext.tsx)
- [LoginPage.tsx](../frontend/src/pages/LoginPage.tsx)
- [RegisterPage.tsx](../frontend/src/pages/RegisterPage.tsx)
- [ProfilePage.tsx](../frontend/src/pages/dashboard/account/ProfilePage.tsx)
- [useSyncProfile.ts](../frontend/src/hooks/useSyncProfile.ts)

کار لازم:

- یکسان‌سازی login با endpoint نهایی backend
- refresh token و logout در همه clientها
- مدیریت 401 مرکزی به‌جای fetchهای مستقل
- جلوگیری از نمایش صفحه dashboard قبل از تکمیل auth loading
- تست expiry، refresh، logout و account deletion

### P2: صفحات محتوایی و رشد محصول

#### ۴.۱۰ صفحه خانه و اعتماد — انجام شد

فایل‌های هدف:

- [HomePage.tsx](../frontend/src/pages/HomePage.tsx)
- [TrustBand.tsx](../frontend/src/components/sections/TrustBand.tsx)
- [site.ts](../frontend/src/content/site.ts)
- [Icon.tsx](../frontend/src/components/ui/Icon.tsx)

TrustBand در [HomePage.tsx](../frontend/src/pages/HomePage.tsx) فعال شد و از محتوای دو زبانه موجود استفاده می‌کند. ادعاهای testnet/mock همچنان باید در بازبینی محتوایی جداگانه کنترل شوند.

#### ۴.۱۱ صفحه اثرگذاری و شفافیت — اتصال تکمیل شد، بهینه‌سازی باقی است

فایل‌های هدف:

- [ImpactPage.tsx](../frontend/src/pages/ImpactPage.tsx)
- `src/content/pages/impactcarbon.ts`
- `src/components/visuals/SatelliteMap.tsx`
- `src/components/visuals/LiveCounters.tsx`
- `src/lib/transparencyApi.ts`

اولویت توسعه:

- جایگزینی تدریجی SVG مفهومی با داده API
- provenance برای هر metric
- گزارش CSV و PDF فقط از داده واقعی یا با برچسب conceptual
- نمودارهای responsive و قابل دسترسی
- جلوگیری از ادعاهای عددی بدون منبع

Impact از قبل اجزای live counters، MRV cycle، time-series، satellite map و provenance را داشت. client شفافیت اکنون پاسخ `{ observations: [...] }` فعلی MRV را به مدل UI تبدیل می‌کند.

#### ۴.۱۲ PWA و حالت آفلاین — پایه انجام شد، queue باقی است

فایل‌های هدف:

- [pwa.ts](../frontend/src/scripts/pwa.ts)
- `vite.config.ts`
- `src/hooks/useSyncProfile.ts`
- `src/test/e2e/offline.spec.ts`

کار لازم:

- اثبات ثبت service worker در build production
- offline queue برای عملیات citizen/MRV
- نمایش وضعیت online/offline و تعداد عملیات pending
- retry پس از reconnect
- عدم cache کردن داده حساس حساب یا پاسخ‌های admin

Service worker در build تولید می‌شود و routeهای API اکنون `NetworkOnly` هستند تا پاسخ‌های حساس یا mutable cache نشوند. offline queue کامل برای citizen/MRV هنوز نیازمند توسعه مستقل است.

## ۵. فهرست اولویت صفحات

### ابتدا توسعه داده شوند

1. صفحات MRV runner و live carbon، به‌دلیل mismatch API.
2. صفحات commerce، به‌دلیل خطای compile و عملیات مالی ناقص.
3. AdminReports و صفحات admin دارای fetch مستقل، به‌دلیل timeout و ریسک حافظه.
4. صفحات login/profile/auth، برای یکپارچه‌سازی refresh و خطای 401.
5. DashboardLayout و CategoryTree، برای mobile navigation و مقیاس‌پذیری ۶۱ مدل.

### سپس تکمیل شوند

1. Impact و Transparency با داده واقعی و provenance.
2. PWA/offline synchronization.
3. Accessibility shell، فرم‌ها، modalها و toastها.
4. Marketplace checkout، payment، shipment و tracking.
5. Home TrustBand و محتوای اعتماد.

### فعلاً نیازمند بازبینی محتوایی، نه توسعه سنگین

- About، Careers، Investors، Partners، Academia و صفحات حقوقی
- FAQ و Blog، مگر آنکه CMS و خبرنامه واقعی فعال شود
- VoiceGuide و UssdGuide، در صورتی که endpointهای عملیاتی و مثال‌ها با backend همگام بمانند

## ۶. پیشنهاد معماری اجرایی و باقی‌مانده

### مرحله ۱: تثبیت — تکمیل‌شده

- رفع ۱۷ خطای TypeScript
- اصلاح تست AdminReports و اجرای تست با worker محدود
- ایجاد `src/lib/apiClient.ts` با مدیریت base URL، token، 401، timeout و خطای استاندارد
- ایجاد client تایپ‌شده برای MRV

### مرحله ۲: باقی‌مانده‌های P1/P2

- اجرای axe مجدد و رفع contrast/labels/focus باقی‌مانده
- code splitting برای `DashboardLayout`، `CartesianChart` و chunkهای بالای ۳۰۰KB
- تکمیل offline queue واقعی و تست reconnect
- تکمیل workflow marketplace از catalog تا tracking
- اصلاح mock Framer Motion در تست‌ها تا هشدار `whileHover` حذف شود

### مرحله ۲: اتصال قابلیت‌های اصلی

- اتصال runnerهای MRV به endpointهای واقعی
- تکمیل login/profile و refresh token
- تکمیل commerce و marketplace با تست workflow
- اضافه کردن contract test برای هر API client

### مرحله ۳: کیفیت محصول

- اجرای کامل axe در صفحات عمومی و داشبورد
- اصلاح focus، labels، contrast، zoom و responsive 320px
- تکمیل PWA/offline queue
- افزودن telemetry بدون افشای اطلاعات شخصی

### مرحله ۴: تجربه پیشرفته

- نقشه تعاملی واقعی با provenance
- نمودارهای زمان‌سری داده واقعی
- onboarding کاربر
- global search قابل توسعه
- گزارش‌های قابل چاپ و export استاندارد

## ۷. معیار پذیرش پیشنهادی

قبل از اعلام آماده‌بودن فرانت‌اند:

```text
pnpm type-check       => 0 errors
pnpm build            => success
pnpm test             => all tests pass, no OOM
pnpm lint             => 0 blocking errors
pnpm test:accessibility => no critical/serious violations
pnpm test:e2e         => auth, MRV, marketplace and dashboard flows pass
```

## نتیجه نهایی

فرانت‌اند از نظر وسعت، هویت بصری و پوشش دامنه علمی غنی است؛ اما توسعه بعدی باید بر اتصال واقعی و صحت قراردادها متمرکز باشد. بزرگ‌ترین ریسک فعلی، ظاهر صفحات نیست، بلکه فاصله بین routeها، API clientها، backend واقعی و تست‌های integration است. پس از تثبیت TypeScript و API contract، توسعه accessibility، PWA، marketplace و visualization ارزش بیشتری ایجاد خواهد کرد.
