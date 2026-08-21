# 31. اسپرینت ۲ فاز ۳ — کالیبراسیون، UQ و API زنجیره

**تاریخ:** 2026-08-17 | **وضعیت:** فعال | **طبقهبندی:** فنی
**مبنا:** سند ۳۰ (اسپرینت ۱)؛ سند ۲۸.

> تحویل اسپرینت ۲ (بخش اول): آنالیز حساسیت Sobol + عدمقطعیت،
> validation ساختاری RothC (تعادل تحلیلی)، و اندپوینت
> `POST /api/v1/simulation/run` با ذخیرهسازی.

---

## ۱) اجزا (کامیت این سند)

| مؤلفه | مسیر | نقش |
|---|---|---|
| کالیبراسیون/UQ | `simulation/calibration.py` | نمونهگیری Saltelli + اندیسهای Sobol (مرتبه اول/کل) — خالص numpy |
| تست Ishigami | `tests/unit/test_simulation_calibration.py` | اعتبارسنجی پیادهسازی با تابع تحلیلی (S1، ST دقیق) |
| validation ساختاری RothC | تستهای جدید RothC | تعادل تحلیلی هر ۴ مخزن + همگرایی + تعادل جرم CO2 |
| جدول ذخیرهسازی | `simulation_runs` (مایگریشن b1c2d3e4f5a6) | persistence نتایج زنجیره |
| روتر API | `services/api_gateway/routers/simulation.py` | POST /run + GET /runs |
| مدل | `SimulationRun` در database/models.py | سایت/سناریو/خروجیها/وضعیت |

## ۲) Sobol' (Saltelli 2010)
- برآوردگرها: `S1_i = mean(f(B)·(f(AB_i) − f(A)))/Var`،
  `ST_i = mean((f(A) − f(AB_i))²)/(2·Var)` — با تصحیح ایندکسگذاری
  ماتریسهای درهم (interleaved).
- **تست Ishigami** (N=8192): S1=(0.307, 0.431, −0.016) و
  ST=(0.553, 0.447, 0.236) در برابر مقادیر تحلیلی (0.3139, 0.4424, 0) و
  (0.5576, 0.4424, 0.2437) — پیادهسازی تأییدشده است.
- پشتیبانی توزیع: uniform (باندها) و normal (mu/sigma)؛ seed برای بازتولید.

## ۳) validation ساختاری RothC (بدون داده مرجع)
- برای طرح ماهانه-گسسته: `pool_eq = in_pool/(1 − exp(−k_m))` با
  `k_m = RATE/12·T·W·P` و `total_dec = input/(1 − X_STAB)` (چون کسر تثبیتشده
  در BIO/HUM بازیافت میشود تا همه C در نهایت تنفس شود).
- مدل در ۳۰۰۰ سال با پیشبینی تحلیلی برای هر ۴ مخزن **< ۲٪ انحراف** دارد:
  DPM 0.86، RPM 17.05، BIO 7.45، HUM 285.6 — منطبق.
- همگرایی: SOC در افقهای ۳۰۰۰ و ۱۰۰۰۰ سال یکسان؛ CO2 سالانه در حالت پایا
  ≈ ورودی سالانه (تعادل جرم).
- **validation مرجع (خروجی رسمی RothC-26.3) همچنان در اسپرینت ۲ باقی است**
  — برچسب مدل تا آن زمان `pending reference validation` میماند.

## ۴) API
```
POST /api/v1/simulation/run   ChainInputs JSON → اجرای زنجیره + ذخیره
GET  /api/v1/simulation/runs?site_id=...  لیست اجراها
```
- هر اجرا با `status=ok|partial` (شکست یک مرحله = partial با پیام) ذخیره میشود.
- مایگریشن روی SQLite dev و PostgreSQL اعمالشدنی است.

## ۵) تستها
- ۱۱ تست جدید (کالیبراسیون ۶، API ۳، RothC ساختاری ۲)؛ کل سویت: **۴۶۵ پاس**.

## ۶) گام بعدی (ادامه اسپرینت ۲)
SWAT+ باینری + اتصال خروجی به WEAP/HEC-RAS؛ validation مرجع RothC با
دادههای رسمی؛ آبوهوای واقعی (ERA5 از طریق CDS)؛ اتصال خروجی زنجیره به
داشبورد MRV.
