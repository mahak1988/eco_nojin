# برنامهٔ توسعهٔ داشبورد — نسخهٔ ۲.۰

## وضعیت فعلی

داشبورد در `frontend/src/pages/DashboardPage.tsx` ساختار زیر را دارد:

### معماری فعلی
- **DashboardLayout** (`components/dashboard/DashboardLayout.tsx`): Sidebar بازجا با دسته‌بندی مدل‌ها (۸ دسته) + لینک‌های حساب کاربری
- **DashboardPage** (`pages/DashboardPage.tsx`): محتوا شامل محاسبه‌گرهای زنده، مرکز داده، رجیستری مدل‌ها، و پورتفولیو ۱۲ بسته
- **routes** (`routes/dashboardRoutes.tsx`): ۶۱ مسیر مدل به تفکیق — هر مدل صفحهٔ جزئیات خودش را دارد
- **registry** (`lib/hydromaregistry.ts`): ۶۱ مدل در ۸ دسته (indices, formulas, soil, hydro, simulation, carbon, climate, economics)

### مشکلات فعلی
1. **سایدبار ثابت** — در موبایل فضا می‌گیرد، UX پیچیده
2. **رابط یک‌صفحه‌ای** — همه چیز در یک صفحه، پیمایش طولانی
3. **کارت‌ها بدون الگوی یکنواخت** — هر بخش استایل خودش را دارد
4. **دسته‌بندی نمایان نیست** — مدل‌ها در یک لیست طولانی در سایدبار

---

## اهداف برنامه

1. **حذف سایدبار** — داشبورد یک‌صفحه‌ای یا breadcrumb-based بدون سایدبار
2. **درخت دسته‌بندی مرحله‌ای** — هر دسته کشویی با زیردسته‌های مدل‌ها
3. **کارت‌های ۳بعدی یکنواخت** — استفاده از `UniversalCard` در تمام بخش‌ها
4. **رابط واکنش‌گرا** — موبایل، تبلت، دسکتاپ
5. **ناوبری هوشمند** — جستجو، فیلتر، دسترسی مستقیم به مدل

---

## برنامهٔ تفکیک‌شده

### فاز ۱: حذف سایدبار و ساخت ساختار جدید

**تغییرات کلیدی:**
- **حفظ DashboardLayout** برای مسیرهای فرعی (model pages) — ولی sidebar فقط در موبایل نمایش داده نشود
- **DashboardPage** می‌شود یک "dashboard home" با:
  - بخش محاسبه‌گرها (همانند فعلی)
  - بخش مرکز داده (همانند فعلی)
  - بخش **درخت دسته‌بندی مدل‌ها** (جایگزین جدول رجیستری)
  - بخش پورتفولیو ۱۲ بسته (به‌روزرسانی شده)

**فایل هدف:** `pages/DashboardPage.tsx`

### فاز ۲: درخت دسته‌بندی مدل‌ها

**کامپوننت جدید:** `components/dashboard/CategoryTree.tsx`

**ویژگی‌ها:**
- هر دسته یک کارت ۳بعدی بزرگ با عنوان فارسی/انگلیسی و شمار تعداد مدل‌ها
- کلیک روی هر دسته → باز شدن (expand) زیردسته‌های مدل‌ها
- مدل‌ها با `UniversalCard` (flip-on-hover) نمایش داده می‌شوند:
  - جلو: نام مدل + توضیح کوتاه
  - بازگشت: منبع، مرجع، نوع پیاده‌سازی (calculator/engine)

**داده‌های ورودی:** از `registry` و `categories` در `hydromaregistry.ts`

### فاز ۳: رابط واکنش‌گرا و جستجو

**اضافه کردن به CategoryTree:**
- بارکش دسته‌بندی‌ها (search box) — فیلتر لحظه‌ای
- toggle نمایش همه/فقط موارد قابل محاسبه (calculator-only)
- responsive grid: `lg:grid-cols-1` برای درخت، `lg:grid-cols-2` برای مدل‌ها

### فاز ۴: بهینه‌سازی سایدبار

**تغییر DashboardLayout:**
- سایدبار به صورت ** collapsible** در دسکتاپ (collapse به آیکن‌ها)
- در موبایل: **bottom sheet** یا drawer — فعال نشود
- لینک به `/dashboard` همیشه واضح باشد

### فاز ۵: ترکیب و تست نهایی

- بروزرسانی `DashboardPage.tsx` با درخت دسته‌بندی
- حفظ محاسبه‌گرها و مرکز داده
- ریفکتور پورتفولیو با UniversalCard
- تست کامل

---

## ساختار نهایی صفحهٔ داشبورتر (DashboardPage)

| شماره | بخش | کامپوننت |
|-------|------|----------|
| 1 | PageHeader | همان (title: "داشبورد هیدروما") |
| 2 | محاسبه‌گرهای زنده | همان ۵ ماشین‌حساب افقی |
| 3 | مرکز داده | همان hub (runs + refresh) |
| 4 | درخت دسته‌بندی مدل‌ها | `CategoryTree` جدید |
| 5 | پورتفولیو ۱۲ بسته | با UniversalCard (flip-on-hover) |
| 6 | CtaBand | همان |

---

## دسته‌بندی مدل‌ها و رنگ‌ها

| دسته | کلید | تعداد | تم رنگی | آیکن |
|------|------|-------|---------|------|
| شاخص‌های ترکیبی | indices | ۷ | aqua | Satellite |
| فرمول‌های پایه | formulas | ۹ | leaf | Calculator |
| خاک‌شناسی | soil | ۸ | sand | Layers |
| هیدرولوژی | hydro | ۳ | aqua | Droplets |
| شبیه‌سازی | simulation | ۶ | leaf | Settings |
| کربن و MRV | carbon | ۶ | sand | Leaf |
| اقلیم و آبیاری | climate | ۲ | aqua | CloudSun |
| اقتصاد و تصمیم | economics | ۱۰ | leaf | Coins |

---

## معیارهای تأیید

```sh
cd frontend
npx tsc --noEmit          # ۰ خطا در فایل‌های جدید
npx eslint src/components/dashboard/ src/pages/DashboardPage.tsx  # ۰ خطا
npx vitest run            # ۳۰/۳۰ تست قبلی + جدید
npx vite build            # ساخت موفق
```

---

## نکات فنی

- **بدون dependency جدید** — از UniversalCard موجود استفاده می‌شود
- **SSR-safe** — `window.matchMedia` برای `prefers-reduced-motion`
- **Keyboard accessible** — کارت‌های flip با `Enter`/`Space` قابل باز و بسته شدن
- **Performance** — استفاده از `motion.div` با `initial/animate` فقط یک بار
- **RTL/LTR** — تمام متن‌ها از `useLang` می‌آیند
