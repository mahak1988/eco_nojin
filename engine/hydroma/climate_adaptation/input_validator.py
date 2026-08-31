"""
موتور اعتبارسنجی و پاک‌سازی ورودی‌ها
رفع یافته‌های بحرانی: None, NaN, Infinity
"""
import math
from typing import Any, Optional

# محدوده‌های فیزیکی معتبر
PHYSICAL_BOUNDS = {
    "temp": {"min": -93.2, "max": 56.7},
    "rain": {"min": 0.0, "max": 12000.0},
    "ec": {"min": 0.0, "max": 400.0},
    "ph": {"min": 0.0, "max": 14.0},
    "soc": {"min": 0.0, "max": 100.0},
    "awc": {"min": 0.0, "max": 500.0},
    "slope": {"min": 0.0, "max": 90.0},
    "humidity": {"min": 0.0, "max": 100.0},
    "wind": {"min": 0.0, "max": 400.0},
}


def sanitize(value: Any, key: str = None, default: float = 0.0) -> float:
    """
    پاک‌سازی یک مقدار ورودی:
    - None -> default
    - NaN -> default
    - Infinity -> کران فیزیکی
    - خارج از محدوده فیزیکی -> کران
    """
    # مدیریت None
    if value is None:
        return default
    
    # تبدیل به عدد
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    
    # مدیریت NaN و Infinity
    if math.isnan(value):
        return default
    if math.isinf(value):
        if key and key in PHYSICAL_BOUNDS:
            return PHYSICAL_BOUNDS[key]["max"] if value > 0 else PHYSICAL_BOUNDS[key]["min"]
        return default
    
    # اعمال کران‌های فیزیکی
    if key and key in PHYSICAL_BOUNDS:
        bounds = PHYSICAL_BOUNDS[key]
        value = max(bounds["min"], min(bounds["max"], value))
    
    return value


def sanitize_dict(data: dict, defaults: dict = None) -> dict:
    """پاک‌سازی یک دیکشنری از مقادیر"""
    defaults = defaults or {}
    result = {}
    for key, value in data.items():
        default = defaults.get(key, 0.0)
        result[key] = sanitize(value, key, default)
    return result


def validate_physical_consistency(data: dict) -> list:
    """بررسی سازگاری فیزیکی بین مقادیر"""
    issues = []
    
    # بررسی دما و بارش
    temp = data.get("temp")
    rain = data.get("rain")
    
    # اگر دما خیلی پایین است، بارش باید برف باشد
    if temp is not None and temp < -40 and rain is not None and rain > 5000:
        issues.append("بارش بسیار بالا در دمای بسیار پایین غیرمعمول است")
    
    # بررسی شوری و ظرفیت آب
    ec = data.get("ec")
    awc = data.get("awc")
    if ec is not None and ec > 100 and awc is not None and awc > 200:
        issues.append("ظرفیت آب بالا با شوری بحرانی ناسازگار است")
    
    return issues
