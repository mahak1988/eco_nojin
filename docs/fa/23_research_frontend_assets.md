# 23. تحقیق منابع طراحی و داده — انیمیشن، ایموجی متحرک و داشبورد

**تاریخ:** 2026-08-17 | **وضعیت:** تاییدشده | **طبقه‌بندی:** فنی/طراحی

## خلاصه

این سند نتیجه تحقیق چهار منبع برای بهبود ظاهر و تجربه کاربری فرانت‌اند اکو نوژین
(داشبوردها، انیمیشن‌ها و ایموجی‌های متحرک) است: Dribbble (الهام طراحی)،
NASA GISS (داده اقلیم رایگان)، Vercel (استقرار و قالب داشبورد)،
LottieFiles (انیمیشن سبک و ایموجی متحرک).

---

## 1) Dribbble — dribbble.com

**چیست:** بزرگ‌ترین پلتفرم اشتراک نمونه‌کار (shots) طراحان UI/UX جهان.

**آمار یافت‌شده در این تحقیق:**
- ۱۷۷,۰۰۰+ طرح داشبورد در `dribbble.com/tags/dashboard`
- ۲۷,۰۷۴ طرح در `dribbble.com/tags/dashboard-design`
- ۲۲,۰۶۴ طرح در `dribbble.com/tags/dashboard-ui`
- صفحه جستجوی اختصاصی `dribbble.com/search/dashboard`

**کاربرد در اکو نوژین:**
- منبع الهام برای چیدمان داشبورد: کارت‌های KPI، ترکیب نمودارها، رنگ‌بندی، حالت تاریک،
  پشتیبانی RTL و داده‌نمایی (data-viz).
- مرجع سبک بصری برای پنل ادمین، داشبورد علمی (فاز ۹) و داشبورد پایش.
- برچسب‌های پیشنهادی برای جستجو: `dashboard`، `agriculture`، `data-viz`، `map`، `climate`.

**نکته مهم:** فایل‌های قابل دانلود نیستند؛ Dribbble صرفاً منبع الهام است.
برای استفاده مستقیم از طرح، باید با طراح تماس گرفت یا سبک را بازطراحی کرد.

---

## 2) NASA GISS — data.giss.nasa.gov

**چیست:** مؤسسه گدارد ناسا (GISS)؛ میزبان تحلیل دمای سطح زمین GISTEMP v4
(از ۱۸۸۰ تاکنون). نمودارها و جدول‌ها حدود دهم هر ماه به‌روزرسانی می‌شوند.

**داده‌ها:**
- سری‌های زمانی ماهانه دمای سطح (جهانی، نیمکره‌ای، منطقه‌ای) و میانگین سالانه
- نقشه‌های جهانی آنومالی و روند دما: `data.giss.nasa.gov/gistemp/maps/`
- فایل‌های متنی/CSV قابل دانلود (نیازمند parse سمت سرور)

**کاربرد در اکو نوژین:**
- منبع داده رایگان و معتبر برای داشبورد تغییر اقلیم (نمودار آنومالی دما).
- مکمل داده‌های CMIP6/Copernicus که پروژه از قبل استفاده می‌کند.
- داشبورد GISTEMP خود الگوی خوبی برای نمایش روند بلندمدت است.

**منابع معتبر مرتبط:** راهنمای UCAR Climate Data Guide و ویدیو/ویژوال
Scientific Visualization Studio (svs.gsfc.nasa.gov/5603).

---

## 3) Vercel — vercel.com

**چیست:** پلتفرم استقرار (deployment) سرورلس، بهینه برای Next.js (فریم‌ورک فعلی فرانت‌اند).

**امکانات کلیدی:**
- **Preview Deployments:** به‌ازای هر branch/PR یک پیش‌نمایش خودکار
- **Web Analytics:** بینش بازدیدکنندگان (top pages، referrers و…)
- **v0:** تولید رابط کاربری با هوش مصنوعی
- **Edge Functions** و استریم پاسخ‌های AI
- قالب آماده **«Next.js & shadcn/ui Admin Dashboard Template»** با داشبوردهای
  آماده (Default، CRM، Finance، Analytics، Productivity) — هماهنگ با UI kit
  فعلی پروژه (Radix/shadcn که در فاز ۸ اضافه شد)

**کاربرد در اکو نوژین:**
- گزینه استقرار/پیش‌نمایش فرانت‌اند (تکمیل‌کننده برنامه Docker/Nginx پروداکشن)
- قالب shadcn می‌تواند نقطه شروع داشبوردهای جدید باشد

---

## 4) LottieFiles — lottiefiles.com/featured-free-animations

**چیست:** بزرگ‌ترین کتابخانه انیمیشن سبک (Lottie) — بیش از ۱.۳ میلیون انیمیشن،
رایگان و پریمیوم. «طراحی‌شده برای انیمیشن‌های فوق‌سبک، قابل شخصی‌سازی و تعاملی
برای وب، اپ و شبکه‌های اجتماعی» با ابزار AI به نام Motion Copilot.

**فرمت‌ها:** dotLottie، Lottie JSON (سبک/برداری/مقیاس‌پذیر)، MP4 و GIF.
پلیرهای رسمی: `lottie-web` و `@lottiefiles/react-lottie-player`.

**صفحات مرتبط با نیاز ما:**
- `lottiefiles.com/free-animations/dashboard` — انیمیشن‌های داشبورد
- `lottiefiles.com/free-animations/dashboard-stats` — انیمیشن آمار
- `lottiefiles.com/free-animations/animated-emojis` — **ایموجی‌های متحرک**
  (دقیقاً خواسته کاربر)

**جایگزین‌ها (طبق miromiro.app):** Lordicon، IconScout (۱.۳M+ انیمیشن)،
useAnimations، Lottielab.

**کاربرد در اکو نوژین:**
- انیمیشن وضعیت‌ها: loading، empty، success/error
- ایموجی‌های متحرک در دستیار RAG و چت
- انیمیشن اعداد/آمار در داشبورد
- **مزیت اصلی Lottie JSON:** حجم بسیار کم — حیاتی برای کاربران کم‌پهنای‌باند
  و معماری آفلاین-فیرست پروژه

---

## توصیه‌های اجرایی برای اکو نوژین

1. **داشبورد:** الهام از Dribbble + شروع از قالب shadcn/ui شرکت Vercel
   (هماهنگ با Radix فعلی)؛ نمودارها با recharts (از قبل اضافه شده).
2. **انیمیشن:** Lottie JSON + `@lottiefiles/react-lottie-player`؛
   رعایت `prefers-reduced-motion` (پروژه از قبل reduced-motion دارد).
3. **ایموجی متحرک:** بخش `animated-emojis` لاتیفایل‌ها برای چت/دستیار دانش.
4. **داده اقلیم:** NASA GISS به‌عنوان منبع مکمل رایگان (با ذکر منبع) کنار
   CMIP6/Copernicus فعلی.
5. **استقرار:** Vercel برای پیش‌نمایش و تست؛ Docker/Nginx برای پروداکشن
   (تصمیم نهایی با مدیر پروژه).

## منابع (جستجو شده در این تحقیق)

- <https://dribbble.com/tags/dashboard> — ۱۷۷,۰۰۰+ طرح داشبورد
- <https://dribbble.com/tags/dashboard-design> — ۲۷,۰۷۴ طرح
- <https://dribbble.com/tags/dashboard-ui> — ۲۲,۰۶۴ طرح
- <https://dribbble.com/search/dashboard>
- <https://data.giss.nasa.gov/gistemp/> — GISTEMP v4
- <https://data.giss.nasa.gov/gistemp/maps/> — نقشه‌های آنومالی/روند
- <https://climatedataguide.ucar.edu/climate-data/global-surface-temperature-data-gistemp-nasa-goddard-institute-space-studies-giss>
- <https://svs.gsfc.nasa.gov/5603/> — آنومالی دمای جهانی ۱۸۸۰–۲۰۲۵
- <https://vercel.com/docs/frameworks/full-stack/nextjs> — Next.js روی Vercel
- <https://vercel.com/docs/analytics> — Web Analytics
- <https://vercel.com/templates/next.js/next-js-and-shadcn-ui-admin-dashboard> — قالب داشبورد
- <https://lottiefiles.com/free-animations/dashboard>
- <https://lottiefiles.com/free-animations/dashboard-stats>
- <https://lottiefiles.com/free-animations/animated-emojis>
- <https://lottiefiles.com/>
- <https://miromiro.app/blog/free-lottie-animations-best-resources> — جایگزین‌ها
