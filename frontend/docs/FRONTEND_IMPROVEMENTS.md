# بهبود فرانت‌اند Eco Nojin — مستندسازی تغییرات

**تاریخ:** 2026-08-22
**محدوده:** `frontend/` (Next.js 16 + Tailwind 4 + React 19 + سیستم i18n سفارشی)
**نوع تغییر:** تکمیل ترجمه‌ها، رفع متن‌های هاردکد، هم‌راستایی با بک‌اند

---

## ۱) خلاصه اجرایی

فرانت‌اند از قبل زیرساخت i18n قدرتمندی داشت (۱۴ زبان، `lib/i18n-context.tsx`، فایل‌های `locales/*.json`). در این مرحله سه شکاف اصلی بسته شد:

1. **تکمیل ترجمه:** ۵۳ کلید `platform_*` (مربوط به «تحلیل جامع زمین» / `PlatformAnalysisPanel.tsx`) که فقط در فارسی و انگلیسی وجود داشتند، به ۱۲ زبان دیگر اضافه شد.
2. **افزودن کلیدهای جدید:** ۴ کلید (`home_typing_1..3` و `common_explore`) به هر ۱۴ زبان اضافه شد تا متن‌های هاردکد صفحه اصلی قابل ترجمه شوند.
3. **رفع هاردکد:** متن‌های هاردکد صفحه اصلی (`app/page.tsx`) به تابع `t()` منتقل شد.

نتیجه: **هر ۱۴ زبان حالا دقیقاً ۸۳۶ کلید یکسان دارند.**

---

## ۲) وضعیت قبل از تغییر

| زبان | تعداد کلید |
|---|---|
| fa (فارسی) | 832 |
| en (انگلیسی) | 832 |
| ar, fr, es, pt, ru, hi, zh, ur, bn, de, it, ms | 779 |

- ۵۳ کلید `platform_*` در ۱۲ زبان گمشده بود (fallback به انگلیسی).
- `app/page.tsx` سه سطر تایپ‌شونده hero و برچسب «Explore» را هاردکد داشت (غیرقابل ترجمه).

## ۳) وضعیت بعد از تغییر

| زبان | تعداد کلید |
|---|---|
| **همه ۱۴ زبان** | **836** |

---

## ۴) فهرست دقیق تغییرات

### ۴.۱ ترجمه کلیدهای `platform_*` (۵۳ کلید × ۱۲ زبان = ۶۳۶ مقدار)

کلیدها (هر دو بخش زیر را پوشش می‌دهند):

- عنوان و زیرعنوان پنل: `platform_title`, `platform_subtitle`, `platform_badge`, `platform_nav_title`, `platform_nav_desc`
- فرم ورودی: `platform_land_name`, `platform_land_name_placeholder`, `platform_area_hectares`, `platform_analyze_button`, `platform_analyzing`
- وضعیت‌ها: `platform_success`, `platform_error`, `platform_retry`, `platform_unnamed`, `platform_processing_time`
- خلاصه: `platform_executive_summary`, `platform_annual_carbon_value`
- بخش اقلیم: `platform_climate_title`, `platform_koppen_class`, `platform_avg_temp`, `platform_temp_range`, `platform_annual_precip`
- بخش پوشش گیاهی: `platform_vegetation_title`, `platform_vegetation`, `platform_health`, `platform_density`, `platform_biomass`
- بخش فرسایش: `platform_erosion_title`, `platform_rusle_rate`, `platform_risk_level`, `platform_annual_loss`
- بخش آبیاری: `platform_irrigation_title`, `platform_daily`, `platform_annual_need`, `platform_system`
- بخش کربن: `platform_carbon_title`, `platform_carbon_rate`, `platform_total_carbon`, `platform_carbon_value`
- بخش ریسک: `platform_risk_title`, `platform_suitability`, `platform_overall_risk`, `platform_drought_risk`, `platform_erosion_risk`, `platform_carbon_risk`
- نمودار: `platform_overview_chart`, `platform_soil_stability`, `platform_rainfall`, `platform_drought_resistance`
- توصیه‌ها و خروجی: `platform_recommendations_title`, `platform_no_recommendations`, `platform_export_png`, `platform_export_success`

### ۴.۲ کلیدهای جدید (۴ کلید × ۱۴ زبان = ۵۶ مقدار)

| کلید | fa | en |
|---|---|---|
| `home_typing_1` | برنامه یکپارچه مهندسی منظر | Integrated Landscape Engineering Program |
| `home_typing_2` | احیای سرزمین با هوش مصنوعی | Restoring Land with Artificial Intelligence |
| `home_typing_3` | داده برای آب، خاک و زندگی | Data for Water, Soil, and Life |
| `common_explore` | کاوش | Explore |

### ۴.۳ رفع متن‌های هاردکد در `app/page.tsx`

- `typingLines` هاردکد فارسی → `[t('home_typing_1'), t('home_typing_2'), t('home_typing_3')]`
- `useState('...')` با مقدار فارسی → `useState('')`
- `<span>Explore</span>` → `<span>{t('common_explore')}</span>`
- افزودن `locale` به destructure و وابستگی `useEffect` تایپینگ (`[typedIndex, locale]`) تا با تغییر زبان، متن تایپ‌شونده هم به‌درستی بازتولید شود.

---

## ۵) تأیید صحت

- **تعداد کلیدها:** با اسکریپت Node بررسی شد؛ هر ۱۴ زبان = 836 کلید.
- **TypeScript:** `npx tsc --noEmit` هیچ خطای جدیدی در `app/page.tsx` یا فایل‌های زبان گزارش نکرد. خطاهای گزارش‌شده همگی **از قبل موجود** در فایل‌های دیگر پروژه بودند (به بخش ۷ مراجعه شود).

---

## ۶) سازگاری با بک‌اند

- کلیدهای `platform_*` مستقیماً توسط کامپوننت `PlatformAnalysisPanel.tsx` مصرف می‌شوند و داده‌هایشان از API بک‌اند (تحلیل ERA5 / RUSLE / NDVI) می‌آید. با تکمیل این کلیدها، خروجی بک‌اند در هر ۱۴ زبان به‌درستی برچسب‌گذاری می‌شود.
- فایل `frontend/locales/backend_translations.json` یک فایل قدیمی/موازی است؛ بخش `messages` آن فقط انگلیسی است و با ساختار `en.json`/`fa.json` یکی نیست. در این مرحله دست نخورده باقی ماند (به بخش ۷ بکلاگ مراجعه شود).

---

## ۷) مسائل باقی‌مانده (بکلاگ)

این موارد خارج از محدوده این مرحله بودند و برای کارهای بعدی ثبت می‌شوند:

1. **خطاهای تایپ از قبل موجود** (مرتبط با این تغییر نیستند):
   - `app/dashboard/page.tsx` (نوع ناسازگار نقاط نقشه)
   - `app/modules/ai/page.tsx` و `app/modules/analytics/page.tsx` (شاخص‌گذاری رشته‌ای و نوع `ApiResponse`)
   - `__tests__/data-table.test.tsx` و `__tests__/a11y-scan.test.tsx`
   - `.next/types/validator.ts` → ماژول گم‌شده `app/tools/lime/page.js` (کش build کهنه)
2. **`backend_translations.json`** — بخش `messages` فقط انگلیسی است؛ باید با سیستم اصلی i18n یکی شود یا حذف گردد.
3. **متن‌های هاردکد احتمالی** در صفحات عمیق‌تر (learn/blog/tools) که اسکن اولیه روی ناوبری/فوتر آن‌ها را تمیز نشان داد.

---

## ۸) نحوه بازتولید/تأیید

```bash
cd frontend
# شمارش کلیدها
node -e "const fs=require('fs');for(const f of ['fa','en','ar','fr','es','pt','ru','hi','zh','ur','bn','de','it','ms']){const j=JSON.parse(fs.readFileSync('locales/'+f+'.json','utf8'));console.log(f,Object.keys(j.messages).length)}"
# اجرای برنامه
pnpm dev
```
