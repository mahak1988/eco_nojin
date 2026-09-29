# S-HONEST — قرارداد وضعیت

> هر مسیری که نمی‌تواند نتیجه‌ای را که وعده می‌دهد تولید کند، **باید بگوید**.

**کد مرجع:** `services/_contracts/status.py`
**دروازه:** G2 (`no-fabricated-success`) — فاز ۳

## چرا این استاندارد

پرخطرترین الگوی نقص در این مخزن، «موفقیت جعلی» است: مسیری که کاری انجام نمی‌دهد ولی پاسخ موفق برمی‌گرداند. نمونه‌های ثبت‌شده در `tolerated-degradations.yaml`:

| آن‌وقت | اکنون |
|---|---|
| `backup` یک خط کامنت SQL می‌نوشت، `passed` برمی‌گرداند | پیاده‌سازی واقعی |
| `verify_integrity()` هش را دور می‌ریخت، `True` برمی‌گرداند | — |
| `verify_chain()` همیشه `False` (ستون‌ها وجود ندارند) | `NotImplementedError` |
| `record_event()` داده را دور می‌ریخت، `True` برمی‌گرداند | — |
| `land_profile` چشم‌انداز می‌ساخت، منبع را `SRTM` اعلام می‌کرد | — |
| `nlg` رکورد شاهد جعلی می‌ساخت | — |
| `trust_score` به همه ۰٫۵ می‌داد | — |
| `oracle` هر چیزی را تأیید می‌کرد | — |

## قاعده

هر پاسخ غیرقطعی **باید** این پوشش را داشته باشد:

```json
{
  "status": "ok | degraded | stale | unavailable | not_implemented",
  "reason": "چه کاری انجام نشد — غیرقابل حذف اگر status != ok",
  "fallback_used": "نام جایگزین، در صورت وجود",
  "provenance": { "source": "computed|derived|measured|external|synthetic",
                  "engine": "path.py:line", "synthetic": false }
}
```

## وضعیت‌ها

| وضعیت | معنا | مثال |
|---|---|---|
| `ok` | داده کامل و واقعی | محاسبه کامل با ورودی معتبر |
| `degraded` | داده واقعی + جایگزین نام‌برداری‌شده | `pg_dump` نبود → جانشین SCAN-CN |
| `stale` | واقعی ولی قدیمی‌تر از حد قابل قبول | کش انقضای ۳۰ روزه |
| `unavailable` | وابستگی خارجی در دسترس نیست | CDSE بدون توکن |
| `not_implemented` | قابلیت وجود ندارد — صریح | بازیابی فیزیکی |

**عمداً غایب:** `failed`. خطا یک استثناست یا پاسخ خطای صریح — نه داده. رمزگذاری خطا به‌عنوان داده همان چیزی است که `{"status": "memory_only"}` را شبیه نتیجه کرد.

## قواعد سخت (نقض = خطا)

1. `status != ok` بدون `reason` غیرقانونی است.
2. `status = ok` همراه `reason` یا `fallback_used` غیرقانونی است — پنهان‌کردن تنزل.
3. داده `synthetic` با `status = ok` غیرقانونی است. **مهم‌ترین قاعده:** تفاوت پروفایل واقعی و جعلی تماماً در همین پرچم است.
4. `provenance.source == "synthetic"` بدون `status = degraded` و `reason` غیرقانونی است.

همه چهار در `Tainted.__post_init__` اعمال می‌شوند.

## درست / نادرست

```python
# ✅ درست
return degraded(
    rows,
    reason="pg_dump not on PATH; substituted SCS-CN surrogate",
    fallback_used="scs.runoff",
    provenance=Provenance(source="derived", engine="swat_plus.py:88"),
)

# ❌ نادرست — همین الگویی که backup اجرا می‌کرد
return {"verification_status": "passed", "size_bytes": 142}

# ❌ نادرست — داده ساختگی بدون اعلام
return {"elevation_mean": 175.0, "dem_source": "SRTM"}
```

## استفاده در مسیر درخواست

```python
result = await motor.run(...)
if not result.ok and result.status is Status.NOT_IMPLEMENTED:
    raise HTTPException(501, result.reason)
return result.data
```

`Tainted.unwrap()` برای فراخوانی‌هایی که تحمل تنزل ندارند، تنزل را به استثنا تبدیل می‌کند (۵۰۳ به‌جای عدد نادرستِ موجه).

## ثبت تنزل

تنزل‌های شناخته‌شده در `docs/standards/tolerated-degradations.yaml` فهرست می‌شوند: مسیر، مالک، تاریخ بازنگری. **فهرست، سند ریسک است نه ابزار سرکوب** — هر سطر یعنی «می‌دانیم این مسیر ناقص است و مالیکش را دارد».
