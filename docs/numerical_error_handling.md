# راهنمای مدیریت خطا در محاسبات عددی

## مشکل شناسایی‌شده

تست‌های آشوب نشان دادند که محاسبات با مقادیر نامعتبر (منفی، صفر، بی‌نهایت)
خطا می‌دهند و سیستم را می‌شکنند.

## راه‌حل‌های پیشنهادی

### 1. استفاده از تابع‌های امن (TRY)

به جای:
```sql
SELECT LOG(value) FROM table
```

استفاده کن:
```sql
SELECT TRY(LOG(value)) FROM table
```

### 2. فیلتر کردن مقادیر نامعتبر

```sql
SELECT
    site_id,
    AVG(temperature) as avg_temp
FROM weather_daily
WHERE temperature IS NOT NULL
  AND temperature BETWEEN -100 AND 100  -- محدوده منطقی
GROUP BY site_id
```

### 3. استفاده از CASE برای مقادیر لبه‌ای

```sql
SELECT
    CASE
        WHEN value > 0 THEN LOG(value)
        WHEN value = 0 THEN 0
        ELSE NULL
    END as safe_log
FROM table
```

### 4. محافظت در سطح اپلیکیشن

```python
import math

def safe_sqrt(x):
    """محاسبه امن ریشه دوم"""
    if x is None or math.isnan(x) or math.isinf(x):
        return None
    if x < 0:
        return None
    return math.sqrt(x)

def safe_log(x, base=10):
    """محاسبه امن لگاریتم"""
    if x is None or x <= 0:
        return None
    try:
        return math.log(x, base)
    except (ValueError, OverflowError):
        return None
```

## پیاده‌سازی در لایه‌های مختلف

| لایه | راه‌حل |
|---|---|
| **دیتابیس** | `TRY()`, `COALESCE()`, `CASE WHEN` |
| **SQLAlchemy** | Validator در مدل‌ها |
| **API Gateway** | Pydantic validation |
| **موتور محاسباتی** | توابع امن (بالا) |
