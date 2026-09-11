# برنامه توسعه صفحه خانه

## وضعیت فعلی

صفحه خانه در `frontend/src/pages/HomePage.tsx` شامل ۸ بخش زیر است:

| شماره | بخش | کامپوننت | وضعیت |
|-------|------|----------|--------|
| 1 | هیرو بنر | `Hero.tsx` | ✅ کامل |
| 2 | بند انتهایا | `StatsBand.tsx` | ✅ کامل |
| 3 | چرا اکو نوژین | `WhyBand.tsx` | ✅ کامل |
| 4 | شبکه قابلیت‌ها | `CapabilityGrid.tsx` | ✅ کامل |
| 5 | زنجیره علمی | `ScienceChain.tsx` (preview) | ✅ کامل |
| 6 | میرو ق مدل‌ها | `ModelsMarquee.tsx` | ✅ کامل |
| 7 | شبکه کانال‌ها | `ChannelsGrid.tsx` | ✅ کامل |
| 8 | بند کربن | `CarbonBand.tsx` | ✅ کامل |
| 9 | بند CTA نهایی | `CtaBand.tsx` | ✅ کامل |

## بخش‌های جدید پیشنهادی

محتوا و کامپوننت‌های زیر آماده وجود دارند اما در صفحه خانه گنجانده نشده‌اند:

### بخش جدید: TrustBand (اعتماد)

- **فایل محتوا**: `src/content/sections/trust.ts` — محتوای دو زبانه (fa/en) با ۴ آیتم اعتماد
- **کامپوننت**: `src/components/sections/TrustBand.tsx` — کامپوننت React آماده
- **مسیر در site.ts**: `t.trust` — در `SiteContent` تعریف شده ولی در `site.ts` پر نشده

شماره در برنامه: بین ChannelsGrid و CarbonBand (بعد از بخش کانال‌ها، قبل از بخش کربن)

### نیازهای پیش‌نیاز

1. **اضافه کردن `trust` به `site.ts`**: فعلاً `SiteContent` در `site.ts` شامل `trust` نیست. باید حالت fa و en را اضافه کنیم.

2. **اصلاح `Icon.tsx`**: کلید آیکن `shield` در `sections/types.ts` تعریف شده اما در `Icon.tsx` map نیست — باعث خطا می‌شود. باید `Shield` از lucide-react اضافه شود.

3. **اضافه کردن TrustBand به HomePage**: یک خط import و یک خط در JSX.

## برنامه گام به گام

### گام ۱: رفع پیش‌نیازهای فنی (۳۰ دقیقه)
- [ ] اضافه کردن `shield` به `iconMap` در `frontend/src/components/ui/Icon.tsx`
- [ ] اضافه کردن `trust` به `SiteContent` type و مقدارهای fa/en در `frontend/src/content/site.ts`
- [ ] بررسی سازگاری `IconKey` بین `site.ts` و `sections/types.ts`

### گام ۲: افزودن TrustBand به صفحه خانه (۱۵ دقیقه)
- [ ] Import TrustBand در `HomePage.tsx`
- [ ] افزودن `<TrustBand />` بین `<ChannelsGrid />` و `<CarbonBand />`

### گام ۳: بررسی و تست نهایی (۱۵ دقیقه)
- [ ] `npx tsc --noEmit` — صفر خطا
- [ ] `npx vite build` — ساخت موفق
- [ ] `npx vitest run` — همه تست‌ها قبول می‌شوند

## شماره بخش‌ها در صفحه خانه (پیشنهادی)

1. هیرو بنر (Hero)
2. بند انتهایا (StatsBand)
3. چرا اکو نوژین (WhyBand)
4. شبکه قابلیت‌ها (CapabilityGrid)
5. زنجیره علمی (ScienceChain - preview)
6. میرو ق مدل‌ها (ModelsMarquee)
7. شبکه کانال‌ها (ChannelsGrid)
8. **باند اعتماد جدید (TrustBand)** ←
9. بند کربن (CarbonBand)
10. بند CTA نهایی (CtaBand)
