# 29. تکمیل فاز ۲ — کانال‌های داده واقعی MRV

**تاریخ:** 2026-08-17 | **وضعیت:** فعال | **طبقه‌بندی:** فنی
**مبنا:** سند ۲۷ فاز ۲ (هفته ۳–۴)؛ الزام EM-01 در بخش ۴۱ PDF.

> این سند افزوده‌های تکمیلی فاز ۲ را توصیف می‌کند: بازیابی واقعی NDVI از
> CDSE، ورود داده IoT و LoRaWAN، همگام‌سازی آفلاین شهروندی، و داشبورد
> عمومی بدون PII. (اسلایس اصلی سه‌سطحی در کامیت d697a21 ثبت شد.)

---

## ۱) اجزای فاز ۲ (کامیت‌های d697a21 → 984a399 → این کامیت)

| مؤلفه | مسیر | نقش |
|---|---|---|
| بازیابی NDVI واقعی سنتینل-۲ | `engine/hydroma/mrv/satellite_cdse.py` | کلاینت STAC سرویس CDSE (کاتالوگ Copernicus) + محاسبهٔ NDVI با rasterio |
| به‌روزرسانی زندهٔ ماهواره | `POST /api/v1/mrv/satellite-refresh` | دریافت NDVI سایت و ثبت با `data_source="real"`؛ گیت `ENABLE_SATELLITE_REAL` |
| ورودی IoT مشترک | `engine/hydroma/mrv/iot_ingest.py` | QA/QC یکسان برای همه مسیرها + پارسر TTN v3 + مصرف‌کننده MQTT |
| وبهوک LoRaWAN | `POST /api/v1/mrv/lorawan-webhook` | دریافت uplink شبکه‌های TTN v3/ChirpStack با کلید `X-Webhook-Key` |
| همگام‌سازی آفلاین | `POST /api/v1/mrv/citizen-reports/batch` | ارسال صف گزارش‌های شهروندی بدون اینترنت (سطح ۳) |
| داشبورد عمومی | `GET /api/v1/mrv/public/dashboard-summary` | آمار تجمیعی **بدون PII** |
| وابستگی‌ها | `paho-mqtt`، `psycopg2-binary` | کلاینت MQTT؛ درایور پستگرس |

## ۲) خط لولهٔ NDVI واقعی (CDSE)

```
POST /satellite-refresh {site_id, lat, lon, start, end, half_side_km}
  → 1) OAuth2 token (client_credentials) در identity.dataspace.copernicus.eu
  → 2) جستجوی STAC: SENTINEL-2 L2A، bbox دور سایت، پنجرهٔ زمانی، ابر < 20٪
  → 3) دانلود باندهای B04 (قرمز) و B08 (مادون‌قرمز نزدیک) — 10 متر
  → 4) NDVI = (NIR−R)/(NIR+R) به‌همراه آماره‌ها + درصد پیکسل معتبر
  → 5) ثبت به‌عنوان سطح ۱ با data_source="real" و provenance کامل
```

- فایل‌های باند موقت در `tempfile.TemporaryDirectory` (پاک‌سازی خودکار توسط
  کتابخانهٔ استاندارد — بدون API حذف فایل دستی).
- هر شکست (اعتبارنامه، جستجو، دانلود، بدون پیکسل معتبر) → `502` صریح؛
  **هرگز دادهٔ simulated به‌صورت بی‌صدا ثبت نمی‌شود** — فرانت‌اند تصمیم
  می‌گیرد با برچسب صریح به شبیه‌سازی برگردد.
- گیت `ENABLE_SATELLITE_REAL != true` → `503` با پیام روشن.

## ۳) قراردادها و امنیت

- **وبهوک:** هدر `X-Webhook-Key` با مقایسهٔ زمان‌ثابت (hmac.compare_digest)؛
  اگر `TELCO_WEBHOOK_KEY` خالی باشد → 401.
- **پارسر TTN v3:** شکل مستقیم یا `uplink_message.decoded_payload` با نگاشت
  واحد داخلی؛ فیلدهای ناشناخته نادیده گرفته می‌شوند.
- **MQTT:** اتصال فقط با `start()`؛ سوژهٔ پیش‌فرض `hydroma/+/reading`؛ پیام
  خراب لاگ و دور ریخته می‌شود (حلقه نمی‌افتد).
- **صداقت داده:** همهٔ ردیف‌ها (حتی rejected) بایگانی می‌شوند؛
  `data_source="real"` فقط برای دادهٔ واقعی؛ داشبورد عمومی هرگز PII
  برنمی‌گرداند (تست تضمین می‌کند).

## ۴) پیکربندی (متغیرهای محیطی)
```
CDSE_BASE_URL / CDSE_IDENTITY_URL / CDSE_CLIENT_ID / CDSE_CLIENT_SECRET
ENABLE_SATELLITE_REAL=true          # گیت فعال‌سازی بازیابی واقعی
TELCO_WEBHOOK_KEY=***               # کلید وبهوک LoRaWAN
MQTT_BROKER_HOST/PORT/USERNAME/PASSWORD   # اختیاری؛ مصرف‌کننده MQTT
POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB   # اتصال محلی پستگرس
```

## ۵) وضعیت تست
- ۲۸ تست جدید در این فاز (۱۴ تکمیل فاز ۲ + ۱۴ CDSE)؛ کل سویت: **۴۳۱+ پاس**.
- مایگریشن alembic روی PostgreSQL محلی: `upgrade head` موفق — ۲۰ جدول
  (PostGIS روی همین نصب موجود است؛ مسیر docker-compose حذف شد).
