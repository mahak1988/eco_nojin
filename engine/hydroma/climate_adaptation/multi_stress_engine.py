"""
موتور ترکیب تنش‌های چندگانه
رفع یافته‌های بحرانی: ترکیب استرس‌ها
"""
from typing import Dict


def drought_heat_salinity_stress(temp: float, rain: float, ec: float) -> Dict:
    """ترکیب خشکسالی + گرما + شوری"""
    heat_stress = min(1.0, max(0.0, (temp - 35) / 15)) if temp > 35 else 0.0
    drought_stress = min(1.0, max(0.0, (50 - rain) / 50)) if rain < 50 else 0.0
    salinity_stress = min(1.0, max(0.0, (ec - 4) / 16)) if ec > 4 else 0.0
    
    # ترکیب با اثر تشدید (تشدید ۱.۵ برابری)
    combined = 1.0 - (1 - heat_stress) * (1 - drought_stress) * (1 - salinity_stress)
    amplified = min(1.0, combined * 1.5)
    
    return {
        "heat_stress": round(heat_stress, 3),
        "drought_stress": round(drought_stress, 3),
        "salinity_stress": round(salinity_stress, 3),
        "combined_stress": round(combined, 3),
        "amplified_stress": round(amplified, 3),
        "severity": _severity(amplified),
    }


def flood_slope_stress(rain: float, slope: float) -> Dict:
    """ترکیب سیل + شیب تند"""
    flood_risk = min(1.0, max(0.0, (rain - 500) / 2000)) if rain > 500 else 0.0
    slope_risk = max(0.0, slope / 90)
    
    combined = flood_risk * (1 + slope_risk)  # شیب، سیل را تشدید می‌کند
    combined = min(1.0, combined)
    
    return {
        "flood_risk": round(flood_risk, 3),
        "slope_risk": round(slope_risk, 3),
        "combined_stress": round(combined, 3),
        "severity": _severity(combined),
        "erosion_risk": round(min(1.0, flood_risk * slope_risk * 2), 3),
    }


def frost_wind_stress(temp: float, wind: float) -> Dict:
    """ترکیب یخبندان + باد شدید"""
    frost_stress = min(1.0, max(0.0, (-temp) / 40)) if temp < 0 else 0.0
    wind_chill_factor = 1 + wind / 100  # باد، سرمای موثر را افزایش می‌دهد
    
    effective_frost = min(1.0, frost_stress * wind_chill_factor)
    
    return {
        "frost_stress": round(frost_stress, 3),
        "wind_chill_factor": round(wind_chill_factor, 3),
        "effective_frost_stress": round(effective_frost, 3),
        "severity": _severity(effective_frost),
    }


def salinity_ph_stress(ec: float, ph: float) -> Dict:
    """ترکیب شوری بالا + قلیائیت"""
    salinity_stress = min(1.0, max(0.0, (ec - 4) / 16)) if ec > 4 else 0.0
    alkalinity_stress = min(1.0, max(0.0, (ph - 8.5) / 5.5)) if ph > 8.5 else 0.0
    
    # شوری + قلیائیت = سدیمی شدن (بسیار خطرناک)
    # مدل وزن‌دهی تشدیدی (US Salinity Handbook)
    # شوری عامل اصلی (60%)، قلیائیت عامل تشدید (40%)، و اثر تعاملی (30%)
    sodification_risk = min(1.0, 
                            (salinity_stress * 0.6) + 
                            (alkalinity_stress * 0.4) + 
                            (salinity_stress * alkalinity_stress * 0.3))
    
    return {
        "salinity_stress": round(salinity_stress, 3),
        "alkalinity_stress": round(alkalinity_stress, 3),
        "sodification_risk": round(sodification_risk, 3),
        "severity": _severity(max(salinity_stress, sodification_risk)),
        "recommendation": "نیاز فوری به گچ و زهکشی" if sodification_risk > 0.5 else "پایش",
    }


def _severity(stress: float) -> str:
    if stress >= 0.75:
        return "بحرانی"
    elif stress >= 0.5:
        return "شدید"
    elif stress >= 0.25:
        return "متوسط"
    else:
        return "ملایم"
