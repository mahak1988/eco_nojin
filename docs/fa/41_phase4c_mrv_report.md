# فاز ۴-ج — گزارش PDF، روند t0→t5، نقشه نمونهبرداری میدانی

> وضعیت: **پیادهسازی و تستشده** — گزارش HTTP 200 (۴۹KB، ۰.۷۹ ثانیه) · بیلد سبز ۵.۴۴s · Commit `eb2f595`.

## ۱) گزارش MRV بهصورت PDF (فارسی RTL، رایگان)

- `services/mrv/mrv_pdf.py` — پشته رایگان: **fpdf2** (MIT، جاسازی کامل فونت Tahoma — بدون مشکل subset) + `arabic-reshaper` + `python-bidi` برای RTL
- اندپوینت: `POST /api/mrv/carbon-budget/report` → PDF با: هدر، جدول نتایج اصلی (Δ tCO2e، SOC اولیه/نهایی، مساحت، حالت داده، ضریب ماندگاری، گواهیپذیر)، روند چنددورهای، جدول نمونههای میدانی Kobo، سلب مسئولیت صادقانه
- تأیید رندر: استخراج متن PyMuPDF → ۲۸۶ کاراکتر فارسی با شکلهای اتصال صحیح («اکو نوژین»)

## ۲) روند چنددورهای t0→t5

- `carbon_mrv.py`: پارامتر `measurements: [{year, soc_t_ha}]` → خروجی `periods` (Δ tCO2e/ha بین هر دوره)
- تست: ۲۰۲۰: 60.0 → ۲۰۲۲: 62.5 (+9.17) → ۲۰۲۵: 66.5 (+14.67 tCO2e/ha)

## ۳) نقشه نمونهبرداری میدانی روی deck.gl

- `MrvCard.tsx`: `FieldSampleMap` — ScatterplotLayer با نقاط واقعی Kobo (lat/lon/soc، رنگ = SOC)؛ بدون نمونه → راهنمای import + دکمه دریافت CSV
- `kobo.py`: نمونهها حالا lat/lon را هم برمیگردانند

## ۴) فرم KoboToolbox واقعی — ساخته و deploy شد

- **فرم «Eco Nojin SOC samples»** در حساب شما (hassansadeghi) با API ساخته و deploy شد: uid `a56wC6d79NM3VCgbCxGssQ`، فیلدهای `soc_t_ha/lat/lon/note`
- `.env` اصلاح شد: `KOBO_FORM_ID=a56wC6d79NM3VCgbCxGssQ` (placeholder قبلی خراب بود)
- ⚠️ **نکته صادقانه**: تزریق نمونهها از طریق API روی kf.kobotoolbox.org ممکن نشد (اندپوینت bulk JSON غیرفعال است و OpenRosa خطای 500 میدهد). راه قطعی ۱ دقیقهای:
  1. در kf.kobotoolbox.org فرم «Eco Nojin SOC samples» را باز کنید
  2. Data ← Import ← فایل `data/mrv/kobo_samples_import.csv` (یا دکمه «دریافت CSV» در داشبورد)
  3. اجرای مجدد MRV → `field_verified` + نقشه نمونهها فعال میشود
- نمونهها برچسب `demo` دارند (ساختهشده با اتوماسیون — داده آزمایشگاهی واقعی نیستند)

## ۵) فایلهای این فاز

**جدید**: `services/mrv/mrv_pdf.py`، `data/mrv/kobo_samples_import.csv`
**توسعه**: `carbon_mrv.py` (periods)، `kobo.py` (lat/lon)، `mrv_router.py` (اندپوینت report)، `MrvCard.tsx` (نقشه deck.gl + CSV)

## ۶) تکمیل رابط کاربری (commits e415a3f + ca8b733)

- ویرایشگر سری چنددوره‌ای t0→t5 در کارت MRV (افزودن/حذف تا ۶ نقطه) + جدول روند Δ tCO2e/ha
- دکمه «دانلود گزارش PDF» — POST /api/mrv/carbon-budget/report با همان پارامترها
- سازگاری معنایی: آخرین نقطه سری = baseline میدانی → ield_verified (همانند measured_soc_t_ha)
- تست HTTP: measurements [60.0, 62.5, 66.5] → data_mode=field_verified، Δ صادقانه −1357.16 tCO2e

## قدم بعدی (فاز ۴-د / ۵)
اتصال داده میدانی واقعی آزمایشگاهی، ماژولهای اقتصاد معیشت (فاز ۵)، یا نصب باینریهای SWAT+/HEC-RAS برای اجرای کامل.
