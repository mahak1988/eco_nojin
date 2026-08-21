# 32. اسپرینت ۲ فاز ۳ (بخش دوم) — آبوهوای واقعی و رپر SWAT+

**تاریخ:** 2026-08-17 | **وضعیت:** فعال | **طبقهبندی:** فنی
**مبنا:** سند ۳۱ (بخش اول اسپرینت ۲).

> تحویل این کامیت: منبع آبوهوای واقعی (Open-Meteo + ET0 هارگریوز FAO-56)
> با اتصال اختیاری به زنجیره، و رپر SWAT+ (اجرای باینری + پارسر output.hru).

---

## ۱) آبوهوای واقعی — `simulation/weather_source.py`
- **Open-Meteo Archive API** (رایگان، بدون کلید): Tmin/Tmax/بارش روزانه.
- **ET0 هارگریوز FAO-56** بهصورت محلی: `ET0 = 0.0023·Ra·(Tmean+17.8)·√(Tmax−Tmin)`
  با هندسه خورشیدی استاندارد (Ra از عرض جغرافیایی و روز سال).
- خروجی با همان ترتیب ستونهای aquacrop 3.x: `MinTemp, MaxTemp,
  Precipitation, ReferenceET, Date`.
- شکست شبکه → `WeatherUnavailable` صریح؛ **fallback به آبوهوای مصنوعی فقط
  با برچسب `synthetic (fallback)` + پیام خطا** (هرگز بیصدا).

**اتصال به زنجیره:** `ChainInputs.lat/lon/use_real_weather` — وقتی فعال باشد،
ارکستراتور آبوهوای واقعی را برای پنجره کاشت→برداشت میگیرد و
`weather_source="open-meteo (real)"` در خروجی aquacrop ثبت میشود.

## ۲) رپر SWAT+ — `simulation/runners/swat_runner.py`
- اجرای باینری SWAT+ با subprocess (در دایرکتوری پروژه، قرارداد I/O متنی).
- **پارسر output.hru** بر اساس نام ستون (case-insensitive): AREA، RUNOFF،
  SEDYLD → تجمیع حوضه: `area_ha`، `runoff_mm` (میانگین وزنی-مساحت)،
  `sedyld_t` (جمع sedyld×مساحت).
- **صداقت:** باینری را اپراتور باید از swat.tamu.edu تهیه کند؛ در نبود آن
  `SwatUnavailable` با پیام روشن — هیچ fallback ساختگی تولید نمیشود.
- تستها: پارسر با فیچر واقعی، مسیرهای خطا، و مسیر موفق با subprocess جعلی.

## ۳) تستها
- ۱۸ تست جدید (آبوهوا ۹: هارگریوز، fetch، خطاها، پنجره؛ SWAT ۶؛
  ارکستراتور real-weather ۲ + fallback صادقانه).
- کل سویت: **۴۸۳ پاس**.

## ۴) گام بعدی
- دانلود/تأمین باینری SWAT+ و ساخت پروژه نمونه برای تأیید میدانی پارسر؛
- validation مرجع RothC با داده رسمی؛
- ERA5 از طریق CDS (اختیاری، جایگزین Open-Meteo برای سریهای بلندتر)؛
- اتصال خروجی زنجیره به داشبورد MRV.
