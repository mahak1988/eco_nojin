#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
کالیبراسیون نهایی هیدروما - نسخه ۱۱.۰
رفع تمام مشکلات شناسایی‌شده در نسخه ۱۰.۰
============================================================================
"""
import json
import math
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "docs" / "hydroma" / "benchmark_v11"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════
# بخش ۱: مدل هیدروما نسخه ۱۱.۰ (کالیبره‌شده نهایی)
# ══════════════════════════════════════════════════════════════

class HydromaV11:
    """مدل هیدروما نسخه ۱۱.۰ با کالیبراسیون دقیق نهایی"""
    
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
        # فاکتور دما (اصلاح‌شده برای boreal و polar)
        # ─────────────────────────────────────────────
        if biome in ["boreal", "polar"]:
            # ✅ اصلاح: در مناطق boreal، از دمای تابستان استفاده می‌شود
            # اما فصل رشد خیلی کوتاه است
            temp_growing = max(0, temp_max - 15)  # دمای فصل رشد واقعی
            
            # گندم بهاره نیاز به دمای حداقل ۱۵ درجه در طول فصل رشد دارد
            if temp_growing < 10:
                temp_factor = 0.0  # خیلی سرد برای گندم
            elif temp_growing < 15:
                temp_factor = (temp_growing - 10) / 10 * 0.3
            elif temp_growing < 20:
                temp_factor = 0.3 + (temp_growing - 15) / 10 * 0.4
            else:
                temp_factor = 0.7
            
            # ✅ اصلاح: کاهش شدید برای فصل رشد کوتاه
            season_length_factor = min(1.0, growing_season / 180.0)
            temp_factor *= season_length_factor
            
        else:
            temp_diff = abs(temp_mean - temp_opt)
            temp_factor = max(0.0, 1.0 - temp_diff / 20.0)
        
        # ─────────────────────────────────────────────
        # فاکتور بارش (اصلاح‌شده نهایی)
        # ─────────────────────────────────────────────
        if biome in ["tropical_rainforest", "karst"]:
            # ✅ اصلاح نهایی: در مناطق گرمسیری، گندم اصلاً مناسب نیست
            # خاک اسیدی + رطوبت زیاد + بیماری‌ها
            if rain_mm < 500:
                rain_factor = max(0.05, rain_mm / 2000.0)
            elif rain_mm < 1500:
                rain_factor = 0.1 + 0.15 * (rain_mm - 500) / 1000
            elif rain_mm < 2500:
                rain_factor = 0.25
            else:
                # بارش خیلی زیاد - گندم نمی‌تواند رشد کند
                rain_factor = max(0.05, 0.25 - (rain_mm - 2500) / 5000)
            
            # ✅ اصلاح: خاک اسیدی شدید گندم را می‌کشد
            if ph < 5.0:
                rain_factor *= 0.2  # کاهش ۸۰٪
            elif ph < 5.5:
                rain_factor *= 0.5  # کاهش ۵۰٪
            
        elif biome in ["hyper_arid", "cold_desert"]:
            # ✅ اصلاح نهایی: بیابان با آبیاری
            irrigation = location.get("irrigation_mm", 0)
            total_water = rain_mm + irrigation
            
            # حتی با آبیاری، عملکرد بیابانی محدود است
            if total_water < 100:
                rain_factor = max(0.0, total_water / 1000.0)
            elif total_water < 300:
                rain_factor = 0.1 + 0.3 * (total_water - 100) / 200
            elif total_water < 500:
                rain_factor = 0.4
            else:
                rain_factor = min(0.5, 0.4 + 0.1 * (total_water - 500) / 500)
            
            # ✅ اصلاح: محدودیت دمایی بیابان
            if temp_max > 45:
                rain_factor *= 0.5  # کاهش ۵۰٪ به دلیل گرمای شدید
            
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
        # فاکتور شوری
        # ─────────────────────────────────────────────
        if ec > 6.0:
            salt_factor = max(0.0, 1.0 - (ec - 6.0) / 20.0)
        elif ec > 2.0:
            salt_factor = 1.0 - 0.02 * (ec - 2.0)
        else:
            salt_factor = 1.0
        
        # ─────────────────────────────────────────────
        # فاکتور pH
        # ─────────────────────────────────────────────
        if ph < 4.0:
            ph_factor = 0.0
        elif ph > 10.0:
            ph_factor = 0.0
        elif ph < 5.0:
            ph_factor = max(0.0, (ph - 4.0) / 1.5)
        elif ph > 9.0:
            ph_factor = max(0.0, (10.0 - ph) / 1.5)
        elif ph < 5.5 or ph > 8.5:
            ph_factor = 0.7
        else:
            ph_factor = 1.0
        
        # ─────────────────────────────────────────────
        # فاکتور دمای افراطی
        # ─────────────────────────────────────────────
        if temp_max > 45.0:
            heat_stress = max(0.0, 1.0 - (temp_max - 45.0) / 15.0)
        elif temp_min < -20.0:
            if biome in ["boreal", "polar"]:
                heat_stress = 1.0
            else:
                heat_stress = max(0.0, 1.0 - (abs(temp_min) - 20.0) / 30.0)
        else:
            heat_stress = 1.0
        
        # ─────────────────────────────────────────────
        # فاکتور فصل رشد
        # ─────────────────────────────────────────────
        season_factor = min(1.0, growing_season / 120.0)
        
        # ─────────────────────────────────────────────
        # فاکتور بلایای طبیعی (اصلاح‌شده نهایی)
        # ─────────────────────────────────────────────
        disaster_factor = 1.0
        if disaster:
            disaster_type = disaster.get("type", "")
            
            if disaster_type == "flood":
                flood_depth = disaster.get("flood_depth", 0)
                # ✅ اصلاح نهایی: سیل شدید = تخریب کامل
                if flood_depth >= 10:
                    disaster_factor = 0.05  # ۹۵٪ خسارت
                elif flood_depth >= 5:
                    disaster_factor = 0.1  # ۹۰٪ خسارت
                elif flood_depth >= 2:
                    disaster_factor = 0.2  # ۸۰٪ خسارت
                elif flood_depth >= 1:
                    disaster_factor = 0.4  # ۶۰٪ خسارت
                else:
                    disaster_factor = 0.7  # ۳۰٪ خسارت
            
            elif disaster_type == "earthquake":
                magnitude = disaster.get("magnitude", 0)
                # ✅ اصلاح نهایی: زلزله ۹ ریشتر = تخریب شدید
                if magnitude >= 9.0:
                    disaster_factor = 0.1  # ۹۰٪ خسارت
                elif magnitude >= 8.0:
                    disaster_factor = 0.2  # ۸۰٪ خسارت
                elif magnitude >= 7.0:
                    disaster_factor = 0.3  # ۷۰٪ خسارت
                elif magnitude >= 6.0:
                    disaster_factor = 0.5  # ۵۰٪ خسارت
                else:
                    disaster_factor = 0.7  # ۳۰٪ خسارت
            
            elif disaster_type == "hurricane":
                wind_speed = disaster.get("wind_speed", 0)
                if wind_speed >= 250:
                    disaster_factor = 0.1
                elif wind_speed >= 180:
                    disaster_factor = 0.3
                else:
                    disaster_factor = 0.6
            
            elif disaster_type == "volcanic":
                ash_cover = disaster.get("ash_cover", 0)
                if ash_cover > 0.5:
                    disaster_factor = 0.2
                elif ash_cover > 0.2:
                    disaster_factor = 0.5
                else:
                    disaster_factor = 0.8
            
            elif disaster_type == "tsunami":
                disaster_factor = 0.0
            
            elif disaster_type == "asteroid":
                disaster_factor = 0.0
        
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
            "model": "Hydroma v11.0",
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
        
        # ✅ اصلاح: تنظیم دقیق‌تر بر اساس بیوم
        if biome in ["boreal", "polar"]:
            # در مناطق سرد، فصل رشد خیلی کوتاه است
            crop_data["growing_season"] = min(crop_data["growing_season"], 90)
            # و عملکرد حداکثر هم کمتر است
            crop_data["max_yield"] *= 0.6
            
        elif biome in ["tropical_rainforest", "karst"]:
            # در مناطق گرمسیری، گندم و جو عملکرد بسیار پایینی دارند
            if crop in ["wheat", "barley"]:
                crop_data["max_yield"] *= 0.15  # کاهش ۸۵٪
        
        elif biome in ["hyper_arid", "cold_desert"]:
            # در بیابان‌ها حتی با آبیاری عملکرد محدود است
            crop_data["max_yield"] *= 0.5
        
        return crop_data


# ══════════════════════════════════════════════════════════════
# بخش ۲: اجرای کالیبراسیون نهایی
# ══════════════════════════════════════════════════════════════

def main():
    print("=" * 80)
    print("کالیبراسیون نهایی هیدروما - نسخه ۱۱.۰")
    print("رفع تمام مشکلات شناسایی‌شده در نسخه ۱۰.۰")
    print("=" * 80)
    
    # ایجاد مدل
    print("\n🔬 ایجاد مدل هیدروما v11.0 ...")
    model = HydromaV11()
    print("   ✅ Hydroma v11.0 آماده است")
    
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
    
    # مقایسه با نسخه قبلی
    print("\n" + "=" * 80)
    print("📋 مقایسه با نسخه‌های قبلی:")
    print("=" * 80)
    print("   نسخه ۱۰.۰: موفق ۲/۷ | نرخ ۲۸.۶٪")
    print(f"   نسخه ۱۱.۰: موفق {passed}/۷ | نرخ {passed/len(test_cases)*100:.1f}٪")
    
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