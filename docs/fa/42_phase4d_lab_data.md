# فاز ۴-د — اتصال داده آزمایشگاهی و مقایسه با مدل

> وضعیت: **پیادهسازی و تستشده** — HTTP 200 · بیلد سبز · Commit در این چرخه.

## هدف
پل بین داده واقعی آزمایشگاهی (SOC خاک) و برآورد مدل (SoilGrids) با آمار صادقانه.

## اجزا
- `services/mrv/lab_data.py` — مخزن محلی `data/lab/lab_samples.json`؛ اعتبارسنجی ردیفها (lat/lon/soc_t_ha)؛
  تبدیل مدل همسان با زنجیره: `soc_t_ha = soc_g_kg × bulk_density × 2.5`
- `services/api_gateway/routers/lab.py` — اندپوینتها:
  - `POST /api/mrv/lab/samples` — ثبت نمونهها (واقعی کاربر)
  - `GET /api/mrv/lab/samples` — فهرست
  - `POST /api/mrv/lab/compare` — آمار مقایسه: n، میانگینها، bias، RMSE، MAPE، R²
- `LabCompareCard.tsx` — در داشبورد: ویرایشگر JSON نمونهها (پیشفرض demo برچسبخورده)، جدول جفت «آزمایشگاه vs مدل»، آمار، یادآوری W-001

## صادقیت (W-001)
- KGE صادقانه `null` است — نیازمند سری زمانی مشاهدهای؛ هیچ عدد ساختگی پر نمیشود.
- وضعیتها: `no_lab_data` → `low_sample_warning` (<2) → `comparison_ready` (≥2)
- نمونههای demo صریحاً برچسب دارند و فقط برای تست جریاناند.

## تست
5 نمونه (SOC 58.2–67.1) → stored=5 → comparison_ready: میانگین اندازهگیری 63.16 vs مدل 54.74،
bias +8.42 t C/ha، RMSE 10.95، MAPE 13.14%، R² منفی (برازش ضعیف با داده demo — صادقانه گزارش شد).
