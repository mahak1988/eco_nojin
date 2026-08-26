# فاز ۳ — اتصال فرانت‌اند به زنجیره علمی + Code-Splitting

> وضعیت: **پیاده‌سازی‌شده** — بیلد سبز (۲.۵۶ ثانیه)؛ باندل ورودی از ۴٬۱۹۶ kB به **۲۱۷ kB** کاهش یافت.

## ۱) داشبورد هیدروما — متحول با داده واقعی

`pages/HydromaDashboard.tsx` بازطراحی شد:

- **کارت «داده واقعی زمین»** (`components/hydroma/RealLandSummaryCard.tsx`): ورودی مختصات، دریافت زنده از Open-Meteo (ERA5) + SoilGrids + CDSE؛ شاخصها: بارش سالانه، دمای میانگین، بافت خاک/SOC، وضعیت ماهواره (صادقانه — `credentials_required` بدون اعتبارنامه).
- **پنل «زنجیره علمی واقعی»** (`components/hydroma/ScientificChainPanel.tsx`): اجرای ۶ موتور (RUSLE، SWAT+ prep، Pywr، RothC، AquaCrop، HEC-RAS/Manning، NSGA-II) با دکمه اجرا؛ متریکها + چیپ وضعیت هر موتور + نشان کش.
- آمار بالای داشبورد دیگر ثابت نیست: بارش/دما/SOC/بافت از داده واقعی میآید.
- چارتهای قدیمی با برچسب «نمونه نمایشی — در فاز ۳ به داده واقعی متصل میشوند» مشخص شدند (قرارداد صداقت W-001).

## ۲) آزمایشگاه مجازی زمین (VLL) — اتصال به زنجیره

`pages/VirtualLandLabPage.tsx`:

- پنل زنجیره علمی + **مقایسه سناریوها** (`components/hydroma/ScenarioCompare.tsx`): دو اجرای واقعی موازی — سناریو الف (شیب ۱۰٪) در برابر سناریو ب (تراسبندی، شیب ۵٪) — جدول مقایسه فرسایش/عملکرد/SOC/قابلیت اطمینان آب با درصد تغییر و علامت خوب/بد.
- **لایه NDVI گرید** (`components/vll/NdviGridCard.tsx`): هیت‌مپ ۷×۷ از `ndvi_grid` واقعی Sentinel-2 وقتی اعتبارنامه CDSE موجود باشد؛ در غیر این صورت بج صادقانه «نیاز به اعتبارنامه رایگان CDSE».
- **رفع نقض صداقت**: fallback ساختگی در `runSimulation` حذف شد — خطا صادقانه نمایش داده میشود (W-001).

## ۳) Code-Splitting (رفع هشدار >500kB)

`App.tsx`: تمام ۳۵ صفحه غیر از HomePage با `React.lazy` + `Suspense` (fallback: `LoadingSpinner` بازنویسی‌شده). نتیجه:

| باندل | قبل | بعد |
|---|---|---|
| ورودی (index) | ۴٬۱۹۶ kB (تک‌فایل) | **۲۱۷ kB** (gzip ۶۸ kB) |
| three.js/چارت‌ها | همیشه لود | فقط هنگام باز شدن صفحه مربوطه |

هشدار باقیمانده فقط برای چانکهای تکی سنگین (OrbitControls 896kB، LivestockEconomicsChart 1.1MB) است که حالا lazy هستند — بار اولیه دیگر تحت تأثیر نیست.

## ۴) فایل‌ها

**جدید**: `components/hydroma/ScenarioCompare.tsx`، `components/vll/NdviGridCard.tsx`
**توسعه**: `components/hydroma/ScientificChainPanel.tsx` (پارامترهای سناریو)، `components/hydroma/RealLandSummaryCard.tsx` (callback مختصات)، `pages/VirtualLandLabPage.tsx`، `pages/HydromaDashboard.tsx`، `App.tsx`، `components/common/LoadingSpinner.tsx` (اسپینر واقعی)

## ۵) قدم بعدی (فاز ۳-ب)
- رندر سیلاب HEC-RAS روی نقشه (deck.gl) پس از نصب باینری HEC-RAS و خروجی واقعی
- اتصال چارتهای نمایشی داشبورد به داده واقعی زنجیره
- نصب باینری رایگان SWAT+ برای اجرای کامل
