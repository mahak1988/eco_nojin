# فاز ۴-ب — KoboToolbox (رایگان) + Gold Standard + ماژول MRV داشبورد

> وضعیت: **پیاده‌سازی‌شده** — متدولوژی Gold Standard، کلاینت Kobo API v2، ماژول MRV در داشبورد و تب هاب شبیه‌ساز آماده است. تنها چیزی که به اقدام شما نیاز دارد: ثبت‌نام رایگان KoboToolbox و قرار دادن توکن در `.env`.

## ۱) تغییرات بک‌اند

| فایل | تغییر |
|---|---|
| `services/scientific_motors/carbon_mrv.py` | **متدولوژی قابل‌انتخاب**: `vm0032` (پیش‌فرض) یا `gold_standard` — Gold Standard SOC Framework (عمق ۳۰cm، پایش هر ۵ سال)، ضریب ماندگاری پارامتری، برچسب صادقانه |
| `services/mrv/kobo.py` | **API v2** (kf.kobotoolbox.org — سرویس رایگان فعلی) + fallback v1؛ تشخیص فیلدهای SOC (`soc_t_ha`، `soc_g_kg` با تبدیل BD، …) |
| `services/api_gateway/routers/mrv.py` | پارامتر `methodology` در `POST /api/mrv/carbon-budget` |

## ۲) تست (واقعی)

```
methodology=gold_standard + measured_soc_t_ha=66.5 (100 ha, agroforestry)
→ data_mode: field_verified | delta: -1357.16 tCO2e | monitoring: 5 yr
kobo بدون توکن → status: requires_credentials + راهنمای ثبت‌نام
```

## ۳) فرانت‌اند
- **`components/hydroma/MrvCard.tsx`** — ماژول MRV در داشبورد هیدروما: مساحت/مدیریت/استاندارد + دکمه محاسبه → بودجه tCO2e، SOC اولیه/نهایی، حالت داده، وضعیت KoboToolbox
- تب «MRV کربن» در مرکز شبیه‌سازها (از قبل) — حالا با انتخاب استاندارد

## ۴) قدم شما: فعال‌سازی داده میدانی واقعی (۵ دقیقه، رایگان)

1. **ثبت‌نام**: https://kf.kobotoolbox.org → Create account (رایگان)
2. **توکن API**: Settings (آیکن چرخ‌دنده) → API → کپی توکن
3. **فرم**: New → Survey → یک فیلد عددی با نام دقیق `soc_t_ha` بسازید (نمونه SOC خاک، t/ha) + فیلد مکان
4. **اعتبارنامه** در `D:\eco_nojin\.env`:
   ```
   KOBO_TOKEN=توکن_شما
   KOBO_FORM_ID=شناسه_asset_فرم
   ```
5. چند نمونه ثبت کنید → اجرای `POST /api/mrv/carbon-budget` با `use_kobo: true` → `data_mode: field_verified`

## ۵) صداقت
- بدون توکن → `requires_credentials`؛ بدون نمونه → `no_soc_samples`
- برآورد مدل است؛ گواهی Verra/GS نیازمند ثبت در رجیستری رسمی و مستندات کامل متدولوژی است — در UI و پاسخ API صراحتاً ذکر شده

## قدم بعدی (فاز ۴-ج)
گزارش‌های MRV قابل‌خروجی (PDF)، سری‌های زمانی چنددوره‌ای (t0→t5)، نقشه نمونه‌برداری میدانی روی deck.gl.
