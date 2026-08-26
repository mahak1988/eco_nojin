# فاز ۱ — داده واقعی ماهواره و اقلیم (Real Land Intelligence)

> وضعیت: **پیاده‌سازی‌شده** — بک‌اند تست‌شده با داده واقعی (HTTP 200 در ۳.۷ ثانیه)، فرانت‌اند با بیلد سبز.

هدف این فاز: حذف داده شبیه‌سازی‌شده از مسیر اصلی و اتصال «زمین انتخابی» به منابع
رایگان داده واقعی (طبق EM-01 گام ۱ و نقشه راه فاز ۱).

---

## ۱) چه چیزی ساخته شد

### بک‌اند (`D:\eco_nojin\services\`)

| فایل | تغییر |
|---|---|
| `satellite/copernicus.py` | پارامتر `collection` برای STAC؛ متد `sample_landsat_lst()` (Landsat 8/9 C2 L2، باند ST_B10 → LST درجه سلسیوس)؛ متد `sample_sentinel1()` (VV/VH خام با برچسب صادقانه `raw_dn_proxy`)؛ `_sample_ndvi_grid()` برای گرید NDVI (درون‌حافظه از COG)؛ پشتیبانی `with_grid=True` در `analyze_location` |
| `satellite/soilgrids.py` **(جدید)** | کلاینت SoilGrids 2.0 از طریق **WCS تایل** (maps.isric.org، رایگان و بدون کلید): بافت (شن/سیلت/رس)، SOC، pH، CEC، چگالی ظاهری + فرمول K-factor راسل (EPIC). واحدها با کراس‌چک روی properties/query API تأیید شد. جست‌وجوی نزدیک‌ترین پیکسل معتبر (پیکسل‌های ماسک‌شده در شهرها) با گزارش صادقانه `sample_offset_km` |
| `satellite/real_land.py` **(جدید)** | سرویس یکپارچه `get_real_land()`: بلوک ماهواره (S2 → NDVI/EVI/SAVI + LAI بوهگ ۲۰۰۲ + C-factor ون‌درنایف ۲۰۰۰ + گرید NDVI، Landsat LST، Sentinel-1)، بلوک اقلیم (Open-Meteo ERA5: بارش، دما، ET₀ FAO-56)، بلوک خاک (SoilGrids). **هیچ fallback شبیه‌سازی‌شده‌ای ندارد** |
| `api_gateway/routers/satellite.py` | اندپوینت جدید `POST /api/v1/satellite/real-land` + مدل `RealLandResponse` |

### تعمیر باگ‌های از پیش موجود (پیش‌نیاز اجرای بک‌اند)

چهار فایل روتر ایمپورت‌های خراب داشتند (`from services.auth.models import ...` در حالی که
مدل‌ها در `database.models` / `services.admin.models` هستند) و سرور اصلاً بالا نمی‌آمد:

- `routers/auth.py` → `AuditLog` از `services.admin.models`؛ `EcoWallet`/`PasswordResetToken` از `database.models`
- `routers/ai_chat.py` → `database.models` (AIConversation, Farm, SatelliteAnalysis, SoilAnalysis, User)
- `routers/carbon.py` → `database.models` (CarbonProject, User)
- `routers/farms.py` → `database.models` (Farm, User)

### فرانت‌اند (`frontend/src/`)

| فایل | تغییر |
|---|---|
| `types/vll.ts` | تایپ‌های `RealLandResult`, `RealSatelliteBlock`, `RealClimateBlock`, `RealSoilBlock`, `RealLandSummary`, `NdviGridPoint` |
| `services/realLandApi.ts` **(جدید)** | `fetchRealLand(lat, lon)` با timeout ۶۰ ثانیه — بدون mock، فقط مسیر واقعی |
| `components/vll/RealLandLoader.tsx` **(جدید)** | دکمه **«🌍 بارگذاری زمین واقعی»** با ورودی lat/lon، نشان‌های وضعیت هر منبع (CDSE / Open-Meteo / SoilGrids)، متریک‌های واقعی (NDVI/LAI/C/دمای سطح، بارش/دما/ET₀، بافت/SOC/pH/K) و راهنمای ثبت‌نام رایگان CDSE هنگام نبود اعتبارنامه |
| `pages/VirtualLandLabPage.tsx` | اتصال `RealLandLoader` به بالای پنل چپ؛ اعمال اقلیم واقعی روی کنترل آب‌وهوا؛ استفاده از خاک واقعی در بدنه شبیه‌سازی؛ نشانگر «۱۰۰٪ داده واقعی / داده واقعی (اقلیم+خاک)» روی صحنه |
| `components/vll/LandLoader.tsx` | **حذف شد** — اورفان بود (تعریف‌شده و هیچ‌جا import نشده)؛ جایگزین: `RealLandLoader` که به صفحه متصل است |

---

## ۲) نتیجه تست واقعی (تهران، ۳۵.۵°N / ۵۱.۵°E)

```
POST /api/v1/satellite/real-land  →  HTTP 200 در ۳.۷ ثانیه

summary:  satellite=credentials_required | climate=ok | soil=ok
climate:  بارش سالانه ۱۹۹.۹ mm | دمای میانگین ۱۹.۲°C | ET₀ سالانه ۱۷۹۱.۵ mm | ۳۶۶ روز
soil:     بافت clay_loam | کربن آلی ۱.۷۷٪ | pH 7.6 | K=0.0516 | offset=0.0 km
satellite: نیاز به اعتبارنامه رایگان CDSE (پیام راهنما در پاسخ)
```

SoilGrids تهران مرکزی (۳۵.۶۸۹۲ / ۵۱.۳۸۹۰): بافت loam، pH 7.6، K=0.0423،
نمونه از پیکسل ۲.۳ کیلومتر دورتر (گزارش صادقانه). نقطه کنترل هلند (۵۲.۱ / ۵.۶):
pH 5.7، SOC 6.6٪ — سازگار با واقعیت.

---

## ۳) وضعیت KPI

| شاخص | وضعیت |
|---|---|
| اقلیم از داده واقعی (Open-Meteo ERA5، بدون کلید) | ✅ ۱۰۰٪ |
| خاک از داده واقعی (SoilGrids ISRIC، بدون کلید) | ✅ ۱۰۰٪ |
| ماهواره از داده واقعی (CDSE Sentinel-2/1 + Landsat LST) | ⏳ پس از افزودن اعتبارنامه رایگان در `.env` |
| حذف simulated از مسیر اصلی | ✅ اندپوینت `real-land` هرگز داده جعلی نمی‌سازد؛ وضعیت `credentials_required` صادقانه گزارش می‌شود |

**منابع رایگان (هیچ‌کدام پولی نیست):** Copernicus Data Space (ثبت‌نام رایگان)،
Open-Meteo ERA5، ISRIC SoilGrids، NASA POWER (پشتیبان اقلیم).

---

## ۴) اقدام لازم کاربر (فقط برای بلوک ماهواره)

۱. ثبت‌نام رایگان در https://dataspace.copernicus.eu
۲. در پنل CDSE یک OAuth client بسازید (client id/secret)
۳. در `D:\eco_nojin\.env` مقدارهای خالی را پر کنید:
   ```
   CDSE_CLIENT_ID=...
   CDSE_CLIENT_SECRET=...
   CDSE_USERNAME=...
   CDSE_PASSWORD=...
   ```
۴. ری‌استارت بک‌اند؛ نشان ماهواره از «نیاز به ثبت‌نام» به «✅ فعال» تغییر می‌کند
   و NDVI/LAI/C-factor واقعی + LST + نسبت VH/VV در پاسخ می‌آید.

(اقلیم و خاک همین حالا واقعی‌اند — بدون هیچ اقدامی.)

---

## ۵) اجرا و تست

```bash
# بک‌اند
cd D:\eco_nojin
.venv\Scripts\activate
uvicorn services.api_gateway.main:app --reload --port 8000

# تست اندپوینت
curl -X POST http://localhost:8000/api/v1/satellite/real-land ^
  -H "Content-Type: application/json" ^
  -d "{\"lat\":35.5,\"lon\":51.5}"

# فرانت‌اند
cd frontend && pnpm install && pnpm run dev   # http://localhost:5173
# مسیر: آزمایشگاه مجازی زمین → «بارگذاری زمین واقعی»
```

---

## ۶) یادداشت‌های فنی

- **SoilGrids چندویژگی در یک درخواست → HTTP 500** (محدودیت سرور)؛ راه‌حل: یک درخواست
  WCS جدا برای هر ویژگی (۷ درخواست موازی با Semaphore(3)، ~۱.۵ ثانیه).
- **پیکسل‌های ماسک‌شده** در شهرها (تهران مرکزی) → جست‌وجوی نزدیک‌ترین پیکسل معتبر
  داخل تایل ±۰.۲۵ درجه با گزارش فاصله واقعی.
- **LAI** از NDVI با رابطه بوهگ (Boegh et al. 2002)؛ **C-factor** با رابطه
  ون‌درنایف (Van der Knijff et al. 2000) — هر دو مستند و علمی.
- **Sentinel-1** فعلاً نسبت VV/VH خام (پروکسی رطوبت خاک) با برچسب صادقانه
  `raw_dn_proxy` — کالیبراسیون radiometric در فاز ۲.
- گرید NDVI (7×7) از طریق API تحویل می‌شود؛ رندر نقشه‌ای آن در فاز ۲/۳.

## ۷) قدم بعدی (فاز ۲)

اتصال زنجیره کامل مدل‌های علمی: SWAT+ (pySWATPlus)، AquaCrop-OSPy، RothC_Py،
Pywr (جایگزین رایگان WEAP)، خودکارسازی HEC-RAS — با اجرای خارج‌ازفرایند و کش نتیجه.
