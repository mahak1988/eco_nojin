#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
پچ نهایی: اصلاح الگوریتم محاسبه ریسک
اصلاحات:
  ۱. وزن‌دهی بهتر برای بلایا
  ۲. تکمیل داده‌های بلایا برای همه مناطق
  ۳. لحاظ شرایط بحرانی محلی
============================================================================
"""
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent


# داده‌های بلایا برای همه مناطق
COMPLETE_DISASTER_DATA = {
    "R01_yazd_iran": {
        "annual_rain_mm": 60, "soc_pct": 0.3, "ec_ds_m": 4.5,
        "irrigation_efficiency": 0.45,
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.25, "last_major": 1386},
            {"type": "ریزگرد", "frequency": 0.15, "last_major": 1401},
            {"type": "موج گرما", "frequency": 0.20, "last_major": 1400},
        ],
        "local_risk_factors": ["کمبود شدید آب", "شوری", "ریزگرد مکرر"],
    },
    "R02_khuzestan_iran": {
        "annual_rain_mm": 230, "soc_pct": 0.9, "ec_ds_m": 12.0,
        "irrigation_efficiency": 0.35,
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.20, "last_major": 1388},
            {"type": "سیل", "frequency": 0.10, "last_major": 1398},
            {"type": "ریزگرد", "frequency": 0.25, "last_major": 1401},
        ],
        "local_risk_factors": ["شوری شدید", "ریزگرد بسیار مکرر", "تنش حرارتی"],
    },
    "R03_hamedan_iran": {
        "annual_rain_mm": 320, "soc_pct": 1.8, "ec_ds_m": 0.8,
        "irrigation_efficiency": 0.0,
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.15, "last_major": 1386},
            {"type": "یخبندان", "frequency": 0.30, "last_major": 1399},
            {"type": "فرسایش", "frequency": 0.20, "last_major": 1395},
        ],
        "local_risk_factors": ["یخبندان مکرر", "فرسایش خاک", "نوسانات بارش"],
    },
    "R04_rajasthan_india": {
        "annual_rain_mm": 350, "soc_pct": 0.4, "ec_ds_m": 1.0,
        "irrigation_efficiency": 0.35,
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.35, "last_major": 2019},
            {"type": "موج گرما", "frequency": 0.25, "last_major": 2022},
            {"type": "سیل", "frequency": 0.10, "last_major": 2018},
        ],
        "local_risk_factors": ["خشکسالی بسیار مکرر", "موج گرما شدید", "بارش نامنظم"],
    },
    "R05_amazon_brazil": {
        "annual_rain_mm": 2500, "soc_pct": 2.0, "ec_ds_m": 0.1,
        "irrigation_efficiency": 0.0,
        "historical_disasters": [
            {"type": "سیل", "frequency": 0.20, "last_major": 2021},
            {"type": "خشکسالی", "frequency": 0.05, "last_major": 2010},
            {"type": "آتش‌سوزی", "frequency": 0.15, "last_major": 2019},
        ],
        "local_risk_factors": ["جنگل‌زدایی", "آتش‌سوزی", "تغییر الگوی بارش"],
    },
    "R06_mekong_vietnam": {
        "annual_rain_mm": 1600, "soc_pct": 2.8, "ec_ds_m": 2.0,
        "irrigation_efficiency": 0.45,
        "historical_disasters": [
            {"type": "سیل", "frequency": 0.30, "last_major": 2022},
            {"type": "تایفون", "frequency": 0.15, "last_major": 2020},
            {"type": "خشکسالی", "frequency": 0.10, "last_major": 2016},
        ],
        "local_risk_factors": ["سیل مکرر", "نفوذ شوری", "بالا آمدن سطح دریا"],
    },
    "R07_australia_outback": {
        "annual_rain_mm": 250, "soc_pct": 0.5, "ec_ds_m": 0.8,
        "irrigation_efficiency": 0.0,
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.30, "last_major": 2019},
            {"type": "موج گرما", "frequency": 0.20, "last_major": 2020},
            {"type": "آتش‌سوزی", "frequency": 0.25, "last_major": 2020},
        ],
        "local_risk_factors": ["خشکسالی شدید", "آتش‌سوزی گسترده", "ظرفیت آب پایین"],
    },
    "R08_yemen_highlands": {
        "annual_rain_mm": 250, "soc_pct": 1.5, "ec_ds_m": 0.8,
        "irrigation_efficiency": 0.25,
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.30, "last_major": 2021},
            {"type": "سیل", "frequency": 0.15, "last_major": 2020},
            {"type": "فرسایش", "frequency": 0.35, "last_major": 2019},
        ],
        "local_risk_factors": ["شیب زیاد", "فرسایش شدید", "جنگ", "کمبود آب"],
    },
    "R09_scandinavia": {
        "annual_rain_mm": 530, "soc_pct": 5.0, "ec_ds_m": 0.2,
        "irrigation_efficiency": 0.70,
        "historical_disasters": [
            {"type": "یخبندان", "frequency": 0.25, "last_major": 2021},
            {"type": "خشکسالی", "frequency": 0.05, "last_major": 2018},
            {"type": "بارش شدید", "frequency": 0.10, "last_major": 2019},
        ],
        "local_risk_factors": ["فصل رشد کوتاه", "یخبندان مکرر"],
    },
    "R10_sahel_africa": {
        "annual_rain_mm": 450, "soc_pct": 0.6, "ec_ds_m": 0.3,
        "irrigation_efficiency": 0.0,
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.35, "last_major": 2021},
            {"type": "موج گرما", "frequency": 0.20, "last_major": 2022},
            {"type": "آفت ملخ", "frequency": 0.15, "last_major": 2020},
        ],
        "local_risk_factors": ["خشکسالی بسیار مکرر", "بیابان‌زایی", "آفات"],
    },
}


def calculate_realistic_risk_level(region_id: str, region_data: dict, 
                                    scenario_risk_factors: dict) -> str:
    """محاسبه سطح ریسک واقع‌بینانه"""
    risk_score = 0
    
    # ریسک اقلیمی از سناریو
    temp_change = scenario_risk_factors.get("temp_change", 0)
    rain_change = scenario_risk_factors.get("rain_change", 0)
    management = scenario_risk_factors.get("management", 0.5)
    
    # امتیازات اقلیمی
    if temp_change >= 5:
        risk_score += 3
    elif temp_change >= 3:
        risk_score += 2
    elif temp_change >= 2:
        risk_score += 1
    
    if rain_change <= -20:
        risk_score += 3
    elif rain_change <= -10:
        risk_score += 2
    elif rain_change <= -5:
        risk_score += 1
    
    # امتیازات مدیریتی
    if management <= 0.15:
        risk_score += 3
    elif management <= 0.3:
        risk_score += 2
    elif management <= 0.5:
        risk_score += 1
    
    # امتیازات بلایا (وزن‌دهی بهتر)
    disasters = region_data.get("historical_disasters", [])
    for disaster in disasters:
        freq = disaster.get("frequency", 0)
        if freq >= 0.30:
            risk_score += 2  # بلایای بسیار مکرر: ۲ امتیاز
        elif freq >= 0.20:
            risk_score += 1.5  # بلایای مکرر: ۱.۵ امتیاز
        elif freq >= 0.10:
            risk_score += 1  # بلایای متوسط: ۱ امتیاز
    
    # امتیازات محلی
    local_factors = region_data.get("local_risk_factors", [])
    for factor in local_factors:
        if "شدید" in factor or "بسیار" in factor or "جنگ" in factor:
            risk_score += 2
        elif "مکرر" in factor:
            risk_score += 1.5
        else:
            risk_score += 0.5
    
    # تعیین سطح ریسک
    if risk_score >= 12:
        return "Critical"
    elif risk_score >= 9:
        return "High"
    elif risk_score >= 6:
        return "Medium"
    elif risk_score >= 3:
        return "Low-Medium"
    else:
        return "Low"


def apply_final_risk_fix():
    """اعمال پچ نهایی محاسبه ریسک"""
    
    print("=" * 70)
    print("پچ نهایی: اصلاح الگوریتم محاسبه ریسک")
    print("=" * 70)
    
    # بارگذاری پیش‌بینی‌های بهبودیافته
    improved_file = ROOT / "docs" / "hydroma" / "forecasts" / "global_forecasts_improved.json"
    
    if not improved_file.exists():
        print("❌ فایل پیش‌بینی‌های بهبودیافته یافت نشد")
        return False
    
    forecasts = json.loads(improved_file.read_text(encoding="utf-8"))
    
    # اعمال اصلاحات برای هر منطقه
    print("\n🔄 اصلاح سطح ریسک برای همه مناطق:\n")
    
    for region_id, forecast in forecasts.items():
        if region_id not in COMPLETE_DISASTER_DATA:
            continue
        
        region_data = COMPLETE_DISASTER_DATA[region_id]
        
        # به‌روزرسانی داده‌های منطقه در پیش‌بینی
        for scenario_id, scenario in forecast["scenarios"].items():
            scenario_risk_factors = {
                "temp_change": scenario["climate_changes"]["temp_change_c"],
                "rain_change": scenario["climate_changes"]["rain_change_percent"],
                "management": scenario["management_quality"],
            }
            
            # محاسبه ریسک جدید
            new_risk = calculate_realistic_risk_level(
                region_id, region_data, scenario_risk_factors
            )
            
            old_risk = scenario["risk_level"]
            scenario["risk_level"] = new_risk
            
            # نمایش تغییرات برای سناریوی پایه
            if scenario_id == "baseline":
                icon = "⬆️" if new_risk in ["High", "Critical"] else "➡️"
                print(f"   {icon} {forecast['region']['name_fa']} ({scenario_id}):")
                print(f"      قدیم: {old_risk} → جدید: {new_risk}")
        
        # به‌روزرسانی احتمالات بلایا
        forecast["disaster_probabilities"] = {
            d["type"]: {
                "annual_probability": d["frequency"],
                "last_major_event": d["last_major"],
                "expected_intensity": (
                    "شدید" if d["frequency"] >= 0.30 else
                    "متوسط تا شدید" if d["frequency"] >= 0.20 else
                    "کم تا متوسط" if d["frequency"] >= 0.10 else "کم"
                ),
            }
            for d in region_data["historical_disasters"]
        }
        
        # افزودن فاکتورهای ریسک محلی
        forecast["local_risk_factors"] = region_data.get("local_risk_factors", [])
    
    # ذخیره نتایج نهایی
    final_file = ROOT / "docs" / "hydroma" / "forecasts" / "global_forecasts_final.json"
    final_file.write_text(
        json.dumps(forecasts, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"\n✅ پیش‌بینی‌های نهایی ذخیره شد: {final_file}")
    
    # خلاصه نهایی
    print("\n" + "=" * 70)
    print("خلاصه نهایی سطوح ریسک (سناریوی پایه)")
    print("=" * 70)
    
    risk_counts = {"Low": 0, "Low-Medium": 0, "Medium": 0, "High": 0, "Critical": 0}
    for region_id, forecast in forecasts.items():
        risk = forecast["scenarios"]["baseline"]["risk_level"]
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        icon = {"Low": "🟢", "Low-Medium": "🟢🟡", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}
        print(f"   {icon.get(risk, '⚪')} {forecast['region']['name_fa']}: {risk}")
    
    print(f"\n   📊 توزیع سطوح ریسک:")
    print(f"   🟢 پایین: {risk_counts.get('Low', 0)}")
    print(f"   🟢🟡 پایین-متوسط: {risk_counts.get('Low-Medium', 0)}")
    print(f"   🟡 متوسط: {risk_counts.get('Medium', 0)}")
    print(f"   🟠 بالا: {risk_counts.get('High', 0)}")
    print(f"   🔴 بحرانی: {risk_counts.get('Critical', 0)}")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    apply_final_risk_fix()