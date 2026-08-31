#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
کالیبراسیون نهایی هیدروما - نسخه ۱۰.۰
رفع تمام مشکلات شناسایی‌شده در بنچمارک جهانی
============================================================================
"""
import json
import math
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "docs" / "hydroma" / "benchmark_v10"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════
# بخش ۱: مدل هیدروما نسخه ۱۰.۰ (کالیبره‌شده)
# ══════════════════════════════════════════════════════════════

class HydromaV10:
    """مدل هیدروما نسخه ۱۰.۰ با کالیبراسیون نهایی"""
    
    def __init__(self):
        self.RUE = 2.5
        self.fPAR = 0.92
        self.HI_potential = 0.48
    
    def simulate(self, location: dict, crop: str, disaster: dict = None) -> dict:
        """شبیه‌سازی عملکرد با کالیبراسیون نهایی"""
        climate = location["climate"]
        soil = location["soil"]
        biome = location.get("biome", "temperate")
        
        temp_mean = climate["temp_mean"]
        rain_mm = climate["rain_mm"]
        temp_max = climate.get("temp_max", temp_mean + 15)
        temp_min = climate.get("temp_min", temp_mean - 15)
        ec = soil.get("ec", 2.0)
        ph = soil.get("ph", 7.0)
        
        crop_data = self._get_crop_data(crop, biome)
        max_yield = crop_data["max_yield"]
        temp_opt = crop_data["temp_opt"]
        growing_season = crop_data["growing_season"]
        
        # ─────────────────────────────────────────────
        # فاکتور دما (اصلاح‌شده برای مناطق سرد)
        # ─────────────────────────────────────────────
        if biome in ["boreal", "polar"]:
            # در مناطق سرد، از دمای تابستان استفاده می‌شود
            temp_growing = temp_max - 10  # دمای فصل رشد
            temp_diff = abs(temp_growing - temp_opt)
            temp_factor = max(0.0, 1.0 - temp_diff / 15.0)
        else:
            temp_diff = abs(temp_mean - temp_opt)
            temp_factor = max(0.0, 1.0 - temp_diff / 20.0)
        
        # ─────────────────────────────────────────────
        # فاکتور بارش (اصلاح‌شده برای مناطق گرمسیری و بیابانی)
        # ─────────────────────────────────────────────
        if biome in ["tropical_rainforest", "karst"]:
            # در مناطق گرمسیری، بارش زیاد عملکرد را کاهش می‌دهد
            if rain_mm < 500:
                rain_factor = max(0.1, rain_mm / 1000.0)
            elif rain_mm < 1500:
                rain_factor = 0.5 + 0.3 * (rain_mm - 500) / 1000
            elif rain_mm < 2500:
                rain_factor = 0.8
            else:
                # بارش خیلی زیاد عملکرد را کاهش می‌دهد
                rain_factor = max(0.2, 0.8 - (rain_mm - 2500) / 10000)
            
            # خاک اسیدی عملکرد گندم را کاهش می‌دهد
            if ph < 5.5:
                rain_factor *= 0.5
            
        elif biome in ["hyper_arid", "cold_desert"]:
            # در مناطق بیابانی، آبیاری اهمیت دارد
            irrigation = location.get("irrigation_mm", 0)
            total_water = rain_mm + irrigation
            
            if total_water < 100:
                rain_factor = max(0.0, total_water / 500.0)
            elif total_water < 300:
                rain_factor = 0.2 + 0.4 * (total_water - 100) / 200
            else:
                rain_factor = min(0.8, 0.6 + 0.2 * (total_water - 300) / 200)
            
            # اگر آبیاری وجود دارد، عملکرد بهبود می‌یابد
            if irrigation > 200:
                rain_factor = max(rain_factor, 0.7)
            
        else:
            # مناطق معتدل
            if rain_mm < 100:
                rain_factor = max(0.0, rain_mm / 500.0)
            elif rain_mm < 500:
                rain_factor = 0.2 + 0.5 * (rain_mm - 100) / 400
            elif rain_mm < 1000:
                rain_factor = 0.7 + 0.2 * (rain_mm - 500) / 500
            else:
                rain_factor = max(0.4, 0.9 - (rain_mm - 1000) / 5000)
        
        # ─────────────────────────────────────────────
        # فاکتور شوری (بدون تغییر)
        # ─────────────────────────────────────────────
        if ec > 6.0:
            salt_factor = max(0.0, 1.0 - (ec - 6.0) / 20.0)
        elif ec > 2.0:
            salt_factor = 1.0 - 0.02 * (ec - 2.0)
        else:
            salt_factor = 1.0
        
        # ─────────────────────────────────────────────
        # فاکتور pH (اصلاح‌شده)
        # ─────────────────────────────────────────────
        if ph < 4.0:
            ph_factor = 0.0  # خاک خیلی اسیدی - هیچ گیاهی رشد نمی‌کند
        elif ph > 10.0:
            ph_factor = 0.0  # خاک خیلی قلیایی - هیچ گیاهی رشد نمی‌کند
        elif ph < 5.0:
            ph_factor = max(0.0, (ph - 4.0) / 1.5)
        elif ph > 9.0:
            ph_factor = max(0.0, (10.0 - ph) / 1.5)
        elif ph < 5.5 or ph > 8.5:
            ph_factor = 0.7
        else:
            ph_factor = 1.0
        
        # ─────────────────────────────────────────────
        # فاکتور دمای افراطی (بدون تغییر)
        # ─────────────────────────────────────────────
        if temp_max > 45.0:
            heat_stress = max(0.0, 1.0 - (temp_max - 45.0) / 15.0)
        elif temp_min < -20.0:
            if biome in ["boreal", "polar"]:
                # در مناطق سرد، دمای زمستان مهم نیست
                heat_stress = 1.0
            else:
                heat_stress = max(0.0, 1.0 - (abs(temp_min) - 20.0) / 30.0)
        else:
            heat_stress = 1.0
        
        # ─────────────────────────────────────────────
        # فاکتور فصل رشد (جدید)
        # ─────────────────────────────────────────────
        season_factor = min(1.0, growing_season / 120.0)
        
        # ─────────────────────────────────────────────
        # فاکتور بلایای طبیعی (جدید)
        # ─────────────────────────────────────────────
        disaster_factor = 1.0
        if disaster:
            disaster_type = disaster.get("type", "")
            
            if disaster_type == "flood":
                flood_depth = disaster.get("flood_depth", 0)
                if flood_depth > 5:
                    disaster_factor = 0.1  # سیل شدید - ۹۰٪ خسارت
                elif flood_depth > 1:
                    disaster_factor = 0.3  # سیل متوسط
                else:
                    disaster_factor = 0.7  # سیل خفیف
            
            elif disaster_type == "earthquake":
                magnitude = disaster.get("magnitude", 0)
                if magnitude >= 9.0:
                    disaster_factor = 0.2  # زلزله خیلی شدید
                elif magnitude >= 7.0:
                    disaster_factor = 0.4  # زلزله شدید
                else:
                    disaster_factor = 0.7  # زلزله خفیف
            
            elif disaster_type == "hurricane":
                wind_speed = disaster.get("wind_speed", 0)
                if wind_speed >= 250:
                    disaster_factor = 0.1  # طوفان دسته ۵
                elif wind_speed >= 180:
                    disaster_factor = 0.3  # طوفان دسته ۳-۴
                else:
                    disaster_factor = 0.6  # طوفان خفیف
            
            elif disaster_type == "volcanic":
                ash_cover = disaster.get("ash_cover", 0)
                if ash_cover > 0.5:
                    disaster_factor = 0.2  # خاکستر زیاد
                elif ash_cover > 0.2:
                    disaster_factor = 0.5  # خاکستر متوسط
                else:
                    disaster_factor = 0.8  # خاکستر کم
            
            elif disaster_type == "tsunami":
                disaster_factor = 0.0  # سونامی - تخریب کامل
            
            elif disaster_type == "asteroid":
                disaster_factor = 0.0  # برخورد شهاب‌سنگ - تخریب کامل
        
        # ─────────────────────────────────────────────
        # محاسبه عملکرد نهایی
        # ─────────────────────────────────────────────
        biomass_potential = max_yield * 2.0
        
        yield_t_ha = (
            biomass_potential *
            temp_factor *
            rain_factor *
            salt_factor *
            ph_factor *
            heat_stress *
            season_factor *
            disaster_factor *
            self.HI_potential
        )
        
        yield_t_ha = max(0.0, min(yield_t_ha, max_yield))
        
        return {
            "model": "Hydroma v10.0",
            "yield_t_ha": round(yield_t_ha, 3),
            "biomass_t_ha": round(yield_t_ha * 2.0, 3),
            "factors": {
                "temp_factor": round(temp_factor, 3),
                "rain_factor": round(rain_factor, 3),
                "salt_factor": round(salt_factor, 3),
                "ph_factor": round(ph_factor, 3),
                "heat_stress": round(heat_stress, 3),
                "season_factor": round(season_factor, 3),
                "disaster_factor": round(disaster_factor, 3),
            },
        }
    
    def _get_crop_data(self, crop: str, biome: str) -> dict:
        """دریافت داده‌های محصول بر اساس بیوم"""
        
        # داده‌های پایه
        crops = {
            "wheat": {"max_yield": 12.0, "temp_opt": 18.0, "growing_season": 210},
            "barley": {"max_yield": 10.0, "temp_opt": 16.0, "growing_season": 200},
            "maize": {"max_yield": 15.0, "temp_opt": 25.0, "growing_season": 120},
            "rice": {"max_yield": 10.0, "temp_opt": 28.0, "growing_season": 120},
            "soybean": {"max_yield": 6.0, "temp_opt": 25.0, "growing_season": 130},
            "cotton": {"max_yield": 4.0, "temp_opt": 25.0, "growing_season": 180},
            "sugar_beet": {"max_yield": 60.0, "temp_opt": 18.0, "growing_season": 180},
            "potato": {"max_yield": 50.0, "temp_opt": 18.0, "growing_season": 100},
            "tomato": {"max_yield": 80.0, "temp_opt": 24.0, "growing_season": 120},
            "cucumber": {"max_yield": 60.0, "temp_opt": 24.0, "growing_season": 100},
            "pistachio": {"max_yield": 3.0, "temp_opt": 25.0, "growing_season": 210},
            "date_palm": {"max_yield": 8.0, "temp_opt": 30.0, "growing_season": 240},
            "saffron": {"max_yield": 0.02, "temp_opt": 15.0, "growing_season": 210},
            "alfalfa": {"max_yield": 20.0, "temp_opt": 20.0, "growing_season": 180},
            "clover": {"max_yield": 15.0, "temp_opt": 18.0, "growing_season": 180},
            "grass": {"max_yield": 15.0, "temp_opt": 18.0, "growing_season": 180},
            "coffee": {"max_yield": 3.0, "temp_opt": 22.0, "growing_season": 240},
            "tea": {"max_yield": 3.0, "temp_opt": 20.0, "growing_season": 240},
            "banana": {"max_yield": 50.0, "temp_opt": 27.0, "growing_season": 365},
            "grape": {"max_yield": 15.0, "temp_opt": 20.0, "growing_season": 210},
        }
        
        crop_data = crops.get(crop, {"max_yield": 5.0, "temp_opt": 20.0, "growing_season": 120})
        
        # تنظیم بر اساس بیوم
        if biome in ["boreal", "polar"]:
            # در مناطق سرد، فصل رشد کوتاه‌تر است
            crop_data["growing_season"] = min(crop_data["growing_season"], 120)
        elif biome in ["tropical_rainforest", "karst"]:
            # در مناطق گرمسیری، گندم و جو عملکرد پایینی دارند
            if crop in ["wheat", "barley"]:
                crop_data["max_yield"] *= 0.3  # کاهش ۷۰٪
        
        return crop_data


# ══════════════════════════════════════════════════════════════
# بخش ۲: اجرای کالیبراسیون نهایی
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("کالیبراسیون نهایی هیدروما - نسخه ۱۰.۰")
    print("رفع تمام مشکلات شناسایی‌شده در بنچمارک جهانی")
    print("=" * 80)
    
    # ایجاد مدل
    print("\n🔬 ایجاد مدل هیدروما v10.0 ...")
    model = HydromaV10()
    print("   ✅ Hydroma v10.0 آماده است")
    
    # تست‌های کلیدی
    print("\n🧪 اجرای تست‌های کلیدی ...")
    
    test_cases = [
        {
            "name": "جنگل کنگو (گندم)",
            "location": {
                "climate": {"temp_mean": 25.0, "rain_mm": 2000.0, "temp_max": 32.0, "temp_min": 20.0},
                "soil": {"ec": 0.2, "ph": 5.5},
                "biome": "tropical_rainforest",
            },
            "crop": "wheat",
            "expected": 0.8,
        },
        {
            "name": "سیبری (گندم بهاره)",
            "location": {
                "climate": {"temp_mean": -8.0, "rain_mm": 250.0, "temp_max": 30.0, "temp_min": -67.0},
                "soil": {"ec": 0.3, "ph": 5.5},
                "biome": "boreal",
                "irrigation_mm": 100,
            },
            "crop": "wheat",
            "expected": 0.3,
        },
        {
            "name": "صحرا (گندم با آبیاری)",
            "location": {
                "climate": {"temp_mean": 30.0, "rain_mm": 5.0, "temp_max": 55.0, "temp_min": 5.0},
                "soil": {"ec": 6.0, "ph": 8.2},
                "biome": "hyper_arid",
                "irrigation_mm": 300,
            },
            "crop": "wheat",
            "expected": 0.5,
        },
        {
            "name": "سیل افراطی",
            "location": {
                "climate": {"temp_mean": 25.0, "rain_mm": 10000.0, "temp_max": 35.0, "temp_min": 15.0},
                "soil": {"ec": 2.0, "ph": 7.0},
                "biome": "tropical_rainforest",
            },
            "crop": "wheat",
            "expected": 0.5,
            "disaster": {"type": "flood", "flood_depth": 10},
        },
        {
            "name": "زلزله ۹ ریشتر",
            "location": {
                "climate": {"temp_mean": 25.0, "rain_mm": 100.0, "temp_max": 35.0, "temp_min": 15.0},
                "soil": {"ec": 2.0, "ph": 7.0},
                "biome": "temperate",
            },
            "crop": "wheat",
            "expected": 1.0,
            "disaster": {"type": "earthquake", "magnitude": 9.0},
        },
        {
            "name": "طوفان دسته ۵",
            "location": {
                "climate": {"temp_mean": 25.0, "rain_mm": 500.0, "temp_max": 35.0, "temp_min": 15.0},
                "soil": {"ec": 2.0, "ph": 7.0},
                "biome": "temperate",
            },
            "crop": "wheat",
            "expected": 0.5,
            "disaster": {"type": "hurricane", "wind_speed": 400},
        },
        {
            "name": "آتشفشان فعال",
            "location": {
                "climate": {"temp_mean": 25.0, "rain_mm": 100.0, "temp_max": 35.0, "temp_min": 15.0},
                "soil": {"ec": 2.0, "ph": 7.0},
                "biome": "volcanic",
            },
            "crop": "wheat",
            "expected": 0.5,
            "disaster": {"type": "volcanic", "ash_cover": 0.8},
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        result = model.simulate(test["location"], test["crop"], test.get("disaster"))
        expected = test["expected"]
        simulated = result["yield_t_ha"]
        
        # محاسبه خطا
        if expected > 0:
            error = abs(simulated - expected) / expected * 100
        else:
            error = 0 if simulated < 0.1 else 100
        
        icon = "✅" if error < 50 else "❌"
        if error < 50:
            passed += 1
        else:
            failed += 1
        
        print(f"\n   {icon} {test['name']}")
        print(f"      شبیه‌سازی: {simulated:.2f} t/ha | انتظار: {expected:.2f} t/ha | خطا: {error:.1f}%")
        
        # نمایش فاکتورها
        factors = result["factors"]
        print(f"      فاکتورها: temp={factors['temp_factor']}, rain={factors['rain_factor']}, "
              f"disaster={factors['disaster_factor']}")
    
    # خلاصه
    print("\n" + "=" * 80)
    print("📊 خلاصه کالیبراسیون نهایی")
    print("=" * 80)
    print(f"   🧪 تعداد تست‌ها: {len(test_cases)}")
    print(f"   ✅ موفق: {passed}")
    print(f"   ❌ ناموفق: {failed}")
    print(f"   📈 نرخ موفقیت: {passed/len(test_cases)*100:.1f}%")
    
    # نتیجه‌گیری
    if failed == 0:
        conclusion = "🏆 هیدروما آماده برای بنچمارک رسمی جهانی است"
    elif failed <= 2:
        conclusion = "🟡 هیدروما نیاز به بهبود جزئی دارد"
    else:
        conclusion = "🔴 هیدروما نیاز به کالیبراسیون بیشتر دارد"
    
    print(f"\n📝 نتیجه: {conclusion}")
    print("\n🎯 شعار: تن زمین خسته است - ما در خدمت بشر و زمین هستیم")
    print("=" * 80)


if __name__ == "__main__":
    main()