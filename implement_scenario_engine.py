#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
موتور سناریونویسی و پیش‌بینی هیدروما
شامل: سناریوهای اقلیمی، بلایای طبیعی، پیش‌بینی با بازه اطمینان
نمونه‌های جهانی: ۱۰ منطقه از ۵ قاره
============================================================================
"""
import json
import sys
import math
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

ROOT = Path(__file__).resolve().parent

# ============================================================
# بخش ۱: تعریف مناطق نمونه جهانی (۱۰ منطقه از ۵ قاره)
# ============================================================

GLOBAL_REGIONS = {
    "R01_yazd_iran": {
        "name_fa": "یزد، ایران",
        "name_en": "Yazd, Iran",
        "continent": "آسیا",
        "country": "ایران",
        "koppen": "BWh",
        "lat": 31.89, "lon": 54.36, "elevation_m": 1237,
        "annual_rain_mm": 60, "rain_cv": 0.45,
        "tmin_annual_c": 12.0, "tmax_annual_c": 32.0,
        "growing_season_days": 280,
        "soil_type": "Arenosol", "soil_texture": "sand",
        "soc_pct": 0.3, "ph": 8.2, "ec_ds_m": 4.5,
        "awc_mm_m": 40, "ksat_mm_h": 50.0,
        "groundwater_depth_m": 35, "aquifer_thickness_m": 80,
        "irrigation_available": True, "irrigation_efficiency": 0.45,
        "dominant_crops": ["پسته", "انار", "زعفران"],
        "challenges": ["گرمای شدید", "کمبود آب", "شوری"],
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.25, "last_major": 1386},
            {"type": "ریزگرد", "frequency": 0.15, "last_major": 1401},
            {"type": "موج گرما", "frequency": 0.20, "last_major": 1400},
        ],
    },
    "R02_khuzestan_iran": {
        "name_fa": "خوزستان، ایران",
        "name_en": "Khuzestan, Iran",
        "continent": "آسیا",
        "country": "ایران",
        "koppen": "BSh",
        "lat": 31.32, "lon": 48.69, "elevation_m": 20,
        "annual_rain_mm": 230, "rain_cv": 0.40,
        "tmin_annual_c": 16.0, "tmax_annual_c": 36.0,
        "growing_season_days": 300,
        "soil_type": "Solonchak", "soil_texture": "clay",
        "soc_pct": 0.9, "ph": 8.5, "ec_ds_m": 12.0,
        "awc_mm_m": 140, "ksat_mm_h": 2.0,
        "groundwater_depth_m": 3, "aquifer_thickness_m": 40,
        "irrigation_available": True, "irrigation_efficiency": 0.35,
        "dominant_crops": ["خرما", "نیشکر", "گوجه‌فرنگی"],
        "challenges": ["شوری شدید", "غرقابی", "تنش حرارتی"],
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.20, "last_major": 1388},
            {"type": "سیل", "frequency": 0.10, "last_major": 1398},
            {"type": "ریزگرد", "frequency": 0.25, "last_major": 1401},
        ],
    },
    "R03_hamedan_iran": {
        "name_fa": "همدان، ایران",
        "name_en": "Hamedan, Iran",
        "continent": "آسیا",
        "country": "ایران",
        "koppen": "BSk",
        "lat": 34.80, "lon": 48.51, "elevation_m": 1740,
        "annual_rain_mm": 320, "rain_cv": 0.35,
        "tmin_annual_c": 2.0, "tmax_annual_c": 22.0,
        "growing_season_days": 180,
        "soil_type": "Cambisol", "soil_texture": "silt_loam",
        "soc_pct": 1.8, "ph": 7.2, "ec_ds_m": 0.8,
        "awc_mm_m": 160, "ksat_mm_h": 10.0,
        "groundwater_depth_m": 25, "aquifer_thickness_m": 60,
        "irrigation_available": False, "irrigation_efficiency": 0.0,
        "dominant_crops": ["گندم", "جو", "نخود"],
        "challenges": ["نوسانات بارش", "ریسک یخبندان", "فرسایش خاک"],
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.15, "last_major": 1386},
            {"type": "یخبندان", "frequency": 0.30, "last_major": 1399},
            {"type": "فرسایش", "frequency": 0.20, "last_major": 1395},
        ],
    },
    "R04_rajasthan_india": {
        "name_fa": "راجستان، هند",
        "name_en": "Rajasthan, India",
        "continent": "آسیا",
        "country": "هند",
        "koppen": "BSh",
        "lat": 26.91, "lon": 75.79, "elevation_m": 430,
        "annual_rain_mm": 350, "rain_cv": 0.60,
        "tmin_annual_c": 16.0, "tmax_annual_c": 34.0,
        "growing_season_days": 120,
        "soil_type": "Regosol", "soil_texture": "sand",
        "soc_pct": 0.4, "ph": 8.0, "ec_ds_m": 1.0,
        "awc_mm_m": 50, "ksat_mm_h": 35.0,
        "groundwater_depth_m": 40, "aquifer_thickness_m": 35,
        "irrigation_available": True, "irrigation_efficiency": 0.35,
        "dominant_crops": ["ارزن مرواریدی", "خردل", "گوار"],
        "challenges": ["بارش نامنظم", "خشکسالی", "فرسایش بادی"],
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.35, "last_major": 2019},
            {"type": "موج گرما", "frequency": 0.25, "last_major": 2022},
            {"type": "سیل", "frequency": 0.10, "last_major": 2018},
        ],
    },
    "R05_amazon_brazil": {
        "name_fa": "آمازون، برزیل",
        "name_en": "Amazon, Brazil",
        "continent": "آمریکای جنوبی",
        "country": "برزیل",
        "koppen": "Af",
        "lat": -3.47, "lon": -62.21, "elevation_m": 80,
        "annual_rain_mm": 2500, "rain_cv": 0.15,
        "tmin_annual_c": 23.0, "tmax_annual_c": 32.0,
        "growing_season_days": 365,
        "soil_type": "Ferralsol", "soil_texture": "clay",
        "soc_pct": 2.0, "ph": 4.5, "ec_ds_m": 0.1,
        "awc_mm_m": 150, "ksat_mm_h": 10.0,
        "groundwater_depth_m": 5, "aquifer_thickness_m": 50,
        "irrigation_available": False, "irrigation_efficiency": 0.0,
        "dominant_crops": ["کاساوا", "موز", "کائوچو"],
        "challenges": ["خاک اسیدی", "آبشویی مواد مغذی", "جنگل‌زدایی"],
        "historical_disasters": [
            {"type": "سیل", "frequency": 0.20, "last_major": 2021},
            {"type": "خشکسالی", "frequency": 0.05, "last_major": 2010},
            {"type": "آتش‌سوزی", "frequency": 0.15, "last_major": 2019},
        ],
    },
    "R06_mekong_vietnam": {
        "name_fa": "مکونگ، ویتنام",
        "name_en": "Mekong, Vietnam",
        "continent": "آسیا",
        "country": "ویتنام",
        "koppen": "Aw",
        "lat": 10.03, "lon": 105.78, "elevation_m": 2,
        "annual_rain_mm": 1600, "rain_cv": 0.30,
        "tmin_annual_c": 23.0, "tmax_annual_c": 33.0,
        "growing_season_days": 365,
        "soil_type": "Fluvisol", "soil_texture": "silt_clay",
        "soc_pct": 2.8, "ph": 5.5, "ec_ds_m": 2.0,
        "awc_mm_m": 170, "ksat_mm_h": 3.0,
        "groundwater_depth_m": 1, "aquifer_thickness_m": 25,
        "irrigation_available": True, "irrigation_efficiency": 0.45,
        "dominant_crops": ["برنج", "میگو", "میوه"],
        "challenges": ["سیل", "نفوذ شوری", "بالا آمدن سطح دریا"],
        "historical_disasters": [
            {"type": "سیل", "frequency": 0.30, "last_major": 2022},
            {"type": "تایفون", "frequency": 0.15, "last_major": 2020},
            {"type": "خشکسالی", "frequency": 0.10, "last_major": 2016},
        ],
    },
    "R07_australia_outback": {
        "name_fa": "استرالیا (آوتبک)",
        "name_en": "Australia Outback",
        "continent": "اقیانوسیه",
        "country": "استرالیا",
        "koppen": "BSh",
        "lat": -31.95, "lon": 141.46, "elevation_m": 150,
        "annual_rain_mm": 250, "rain_cv": 0.45,
        "tmin_annual_c": 10.0, "tmax_annual_c": 30.0,
        "growing_season_days": 180,
        "soil_type": "Arenosol", "soil_texture": "sand",
        "soc_pct": 0.5, "ph": 6.5, "ec_ds_m": 0.8,
        "awc_mm_m": 35, "ksat_mm_h": 60.0,
        "groundwater_depth_m": 25, "aquifer_thickness_m": 40,
        "irrigation_available": False, "irrigation_efficiency": 0.0,
        "dominant_crops": ["گندم دیم", "چرای گوسفند"],
        "challenges": ["خشکسالی شدید", "ظرفیت آب پایین", "موج گرما"],
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.30, "last_major": 2019},
            {"type": "موج گرما", "frequency": 0.20, "last_major": 2020},
            {"type": "آتش‌سوزی", "frequency": 0.25, "last_major": 2020},
        ],
    },
    "R08_yemen_highlands": {
        "name_fa": "یمن (ارتفاعات)",
        "name_en": "Yemen Highlands",
        "continent": "آسیا",
        "country": "یمن",
        "koppen": "BWk",
        "lat": 15.35, "lon": 44.20, "elevation_m": 2300,
        "annual_rain_mm": 250, "rain_cv": 0.50,
        "tmin_annual_c": 10.0, "tmax_annual_c": 25.0,
        "growing_season_days": 200,
        "soil_type": "Leptosol", "soil_texture": "loam",
        "soc_pct": 1.5, "ph": 7.5, "ec_ds_m": 0.8,
        "awc_mm_m": 80, "ksat_mm_h": 12.0,
        "groundwater_depth_m": 50, "aquifer_thickness_m": 30,
        "irrigation_available": True, "irrigation_efficiency": 0.25,
        "dominant_crops": ["سورگوم", "ارزن", "قات", "قهوه"],
        "challenges": ["شیب زیاد", "کمبود آب", "فرسایش خاک", "جنگ"],
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.30, "last_major": 2021},
            {"type": "سیل", "frequency": 0.15, "last_major": 2020},
            {"type": "فرسایش", "frequency": 0.35, "last_major": 2019},
        ],
    },
    "R09_scandinavia": {
        "name_fa": "اسکاندیناوی (سوئد)",
        "name_en": "Scandinavia (Sweden)",
        "continent": "اروپا",
        "country": "سوئد",
        "koppen": "Dfb",
        "lat": 59.33, "lon": 18.07, "elevation_m": 40,
        "annual_rain_mm": 530, "rain_cv": 0.25,
        "tmin_annual_c": -2.0, "tmax_annual_c": 12.0,
        "growing_season_days": 150,
        "soil_type": "Podzol", "soil_texture": "sandy_loam",
        "soc_pct": 5.0, "ph": 5.0, "ec_ds_m": 0.2,
        "awc_mm_m": 120, "ksat_mm_h": 30.0,
        "groundwater_depth_m": 10, "aquifer_thickness_m": 30,
        "irrigation_available": True, "irrigation_efficiency": 0.70,
        "dominant_crops": ["جو", "جو دوسر", "سیب‌زمینی"],
        "challenges": ["فصل رشد کوتاه", "آسیب یخبندان", "خاک اسیدی"],
        "historical_disasters": [
            {"type": "یخبندان", "frequency": 0.25, "last_major": 2021},
            {"type": "خشکسالی", "frequency": 0.05, "last_major": 2018},
            {"type": "بارش شدید", "frequency": 0.10, "last_major": 2019},
        ],
    },
    "R10_sahel_africa": {
        "name_fa": "ساحل آفریقا (نیجر)",
        "name_en": "Sahel Africa (Niger)",
        "continent": "آفریقا",
        "country": "نیجر",
        "koppen": "BSh",
        "lat": 13.50, "lon": 2.10, "elevation_m": 250,
        "annual_rain_mm": 450, "rain_cv": 0.40,
        "tmin_annual_c": 22.0, "tmax_annual_c": 38.0,
        "growing_season_days": 120,
        "soil_type": "Lixisol", "soil_texture": "sandy_loam",
        "soc_pct": 0.6, "ph": 6.0, "ec_ds_m": 0.3,
        "awc_mm_m": 60, "ksat_mm_h": 20.0,
        "groundwater_depth_m": 15, "aquifer_thickness_m": 25,
        "irrigation_available": False, "irrigation_efficiency": 0.0,
        "dominant_crops": ["ارزن", "سورگوم", "لوبیا چشم‌بلبلی"],
        "challenges": ["خشکسالی", "کاهش حاصلخیزی خاک", "آفات"],
        "historical_disasters": [
            {"type": "خشکسالی", "frequency": 0.35, "last_major": 2021},
            {"type": "موج گرما", "frequency": 0.20, "last_major": 2022},
            {"type": "آفت ملخ", "frequency": 0.15, "last_major": 2020},
        ],
    },
}


# ============================================================
# بخش ۲: تعریف سناریوها
# ============================================================

SCENARIOS = {
    "optimistic": {
        "name_fa": "خوشبینانه",
        "name_en": "Optimistic",
        "description": "کاهش انتشار گازهای گلخانه‌ای، اقدامات احیای مؤثر",
        "climate_factors": {
            "temp_change_per_year": 0.0001,  # +0.1°C در 10 سال
            "rain_change_per_year": 0.0005,   # +0.5% در 10 سال
            "et0_change_per_year": 0.0002,
        },
        "management_quality": 0.8,  # مدیریت خوب
        "disaster_mitigation": 0.7,  # کاهش اثر بلایا
    },
    "baseline": {
        "name_fa": "پایه",
        "name_en": "Baseline",
        "description": "ادامه روند فعلی، بدون تغییرات عمده",
        "climate_factors": {
            "temp_change_per_year": 0.0002,  # +0.2°C در 10 سال
            "rain_change_per_year": -0.0005,  # -0.5% در 10 سال
            "et0_change_per_year": 0.0003,
        },
        "management_quality": 0.5,  # مدیریت متوسط
        "disaster_mitigation": 0.5,  # کاهش متوسط اثر بلایا
    },
    "pessimistic": {
        "name_fa": "بدبینانه",
        "name_en": "Pessimistic",
        "description": "انتشار بالا، عدم اقدام مؤثر",
        "climate_factors": {
            "temp_change_per_year": 0.0004,  # +0.4°C در 10 سال
            "rain_change_per_year": -0.0015,  # -1.5% در 10 سال
            "et0_change_per_year": 0.0005,
        },
        "management_quality": 0.3,  # مدیریت ضعیف
        "disaster_mitigation": 0.3,  # کاهش کم اثر بلایا
    },
    "crisis": {
        "name_fa": "بحران",
        "name_en": "Crisis",
        "description": "شرایط بحرانی، بلایای مکرر و شدید",
        "climate_factors": {
            "temp_change_per_year": 0.0005,  # +0.5°C در 10 سال
            "rain_change_per_year": -0.0025,  # -2.5% در 10 سال
            "et0_change_per_year": 0.0008,
        },
        "management_quality": 0.1,  # مدیریت بسیار ضعیف
        "disaster_mitigation": 0.1,  # کاهش بسیار کم اثر بلایا
    },
}


# ============================================================
# بخش ۳: موتور سناریونویسی
# ============================================================

class ScenarioEngine:
    """موتور سناریونویسی و پیش‌بینی هیدروما"""
    
    def __init__(self):
        self.random_seed = 42
        random.seed(self.random_seed)
    
    def generate_forecast(self, region_id: str, horizon_years: int = 10) -> Dict:
        """تولید پیش‌بینی کامل برای یک منطقه"""
        
        if region_id not in GLOBAL_REGIONS:
            return {"error": f"منطقه {region_id} یافت نشد"}
        
        region = GLOBAL_REGIONS[region_id]
        
        forecast = {
            "forecast_id": f"HYD-{region_id}-{datetime.now().strftime('%Y%m%d')}",
            "generated_at": datetime.now().isoformat(),
            "region": {
                "id": region_id,
                "name_fa": region["name_fa"],
                "name_en": region["name_en"],
                "continent": region["continent"],
                "country": region["country"],
                "koppen": region["koppen"],
                "coordinates": {
                    "lat": region["lat"],
                    "lon": region["lon"],
                    "elevation_m": region["elevation_m"],
                },
            },
            "horizon_years": horizon_years,
            "scenarios": {},
            "disaster_probabilities": {},
            "recommendations": {},
            "confidence_level": "Medium",
            "data_quality": "Good",
        }
        
        # تولید پیش‌بینی برای هر سناریو
        for scenario_id, scenario in SCENARIOS.items():
            scenario_forecast = self._generate_scenario_forecast(
                region, scenario, horizon_years
            )
            forecast["scenarios"][scenario_id] = scenario_forecast
        
        # تولید احتمالات بلایا
        forecast["disaster_probabilities"] = self._calculate_disaster_probabilities(region)
        
        # تولید توصیه‌ها
        forecast["recommendations"] = self._generate_recommendations(region, forecast["scenarios"])
        
        return forecast
    
    def _generate_scenario_forecast(self, region: Dict, scenario: Dict, 
                                    horizon_years: int) -> Dict:
        """تولید پیش‌بینی برای یک سناریوی خاص"""
        
        climate_factors = scenario["climate_factors"]
        management_quality = scenario["management_quality"]
        
        # پیش‌بینی تغییرات اقلیمی
        temp_change = climate_factors["temp_change_per_year"] * horizon_years * 10
        rain_change = climate_factors["rain_change_per_year"] * horizon_years * 10
        et0_change = climate_factors["et0_change_per_year"] * horizon_years * 10
        
        # پیش‌بینی عملکرد با بازه اطمینان
        base_yield = self._estimate_base_yield(region)
        climate_factor = 1.0 + (rain_change * 0.5) - (temp_change * 0.1)
        management_factor = 0.7 + management_quality * 0.6
        
        yield_p50 = base_yield * climate_factor * management_factor
        yield_p10 = yield_p50 * 0.7
        yield_p90 = yield_p50 * 1.3
        
        # پیش‌بینی وضعیت خاک
        soc_trend = self._predict_soc_trend(region, management_quality)
        ec_trend = self._predict_ec_trend(region, management_quality)
        
        # تعیین سطح ریسک
        risk_level = self._calculate_risk_level(
            temp_change, rain_change, management_quality
        )
        
        return {
            "name_fa": scenario["name_fa"],
            "name_en": scenario["name_en"],
            "description": scenario["description"],
            "climate_changes": {
                "temp_change_c": round(temp_change, 1),
                "rain_change_percent": round(rain_change * 100, 1),
                "et0_change_percent": round(et0_change * 100, 1),
            },
            "yield_prediction": {
                "P10": round(yield_p10, 2),
                "P50": round(yield_p50, 2),
                "P90": round(yield_p90, 2),
                "unit": "تن/هکتار",
            },
            "soil_health": {
                "soc_trend_percent_per_year": round(soc_trend, 3),
                "ec_trend_ds_m_per_year": round(ec_trend, 3),
                "awc_change_percent": round((management_quality - 0.5) * 20, 1),
            },
            "risk_level": risk_level,
            "management_quality": management_quality,
        }
    
    def _estimate_base_yield(self, region: Dict) -> float:
        """تخمین عملکرد پایه بر اساس شرایط منطقه"""
        rain = region["annual_rain_mm"]
        soc = region.get("soc_pct", 1.0)
        ec = region.get("ec_ds_m", 0.5)
        
        # فرمول ساده تخمین عملکرد
        base = 2.0  # عملکرد پایه
        
        # اثر بارش
        if rain < 100:
            base *= 0.5
        elif rain < 300:
            base *= 0.8
        elif rain > 1000:
            base *= 1.2
        
        # اثر ماده آلی
        base *= (0.7 + soc * 0.1)
        
        # اثر شوری
        if ec > 8:
            base *= 0.6
        elif ec > 4:
            base *= 0.8
        
        return base
    
    def _predict_soc_trend(self, region: Dict, management_quality: float) -> float:
        """پیش‌بینی روند تغییرات کربن آلی خاک"""
        # مدیریت خوب -> افزایش، مدیریت بد -> کاهش
        base_trend = -0.05  # روند پایه: کاهش تدریجی
        management_effect = (management_quality - 0.5) * 0.2
        return base_trend + management_effect
    
    def _predict_ec_trend(self, region: Dict, management_quality: float) -> float:
        """پیش‌بینی روند تغییرات شوری"""
        ec = region.get("ec_ds_m", 0.5)
        irrigation_eff = region.get("irrigation_efficiency", 0.5)
        
        # شوری بالا + راندمان پایین -> افزایش شوری
        if ec > 4 and irrigation_eff < 0.5:
            trend = 0.2  # افزایش شوری
        elif ec > 4:
            trend = 0.05
        else:
            trend = -0.02  # کاهش تدریجی
        
        # اثر مدیریت
        trend -= (management_quality - 0.5) * 0.1
        
        return trend
    
    def _calculate_risk_level(self, temp_change: float, rain_change: float,
                              management_quality: float) -> str:
        """محاسبه سطح ریسک"""
        risk_score = 0
        
        if temp_change > 3:
            risk_score += 2
        elif temp_change > 1:
            risk_score += 1
        
        if rain_change < -10:
            risk_score += 2
        elif rain_change < -5:
            risk_score += 1
        
        if management_quality < 0.3:
            risk_score += 2
        elif management_quality < 0.5:
            risk_score += 1
        
        if risk_score >= 5:
            return "Critical"
        elif risk_score >= 3:
            return "High"
        elif risk_score >= 2:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_disaster_probabilities(self, region: Dict) -> Dict:
        """محاسبه احتمالات بلایا بر اساس داده‌های تاریخی"""
        probabilities = {}
        
        for disaster in region.get("historical_disasters", []):
            probabilities[disaster["type"]] = {
                "annual_probability": disaster["frequency"],
                "last_major_event": disaster.get("last_major", "Unknown"),
                "expected_intensity": self._estimate_disaster_intensity(
                    disaster["type"], disaster["frequency"]
                ),
            }
        
        return probabilities
    
    def _estimate_disaster_intensity(self, disaster_type: str, 
                                     frequency: float) -> str:
        """تخمین شدت بلایا"""
        if frequency > 0.25:
            return "متوسط تا شدید"
        elif frequency > 0.15:
            return "کم تا متوسط"
        else:
            return "کم"
    
    def _generate_recommendations(self, region: Dict, scenarios: Dict) -> Dict:
        """تولید توصیه‌ها بر اساس سناریوها"""
        
        recommendations = {
            "optimistic": [],
            "baseline": [],
            "pessimistic": [],
            "crisis": [],
        }
        
        # توصیه‌های عمومی بر اساس چالش‌های منطقه
        challenges = region.get("challenges", [])
        
        for scenario_id, scenario_data in scenarios.items():
            recs = []
            
            # توصیه بر اساس تغییرات اقلیمی
            temp_change = scenario_data["climate_changes"]["temp_change_c"]
            rain_change = scenario_data["climate_changes"]["rain_change_percent"]
            
            if temp_change > 2:
                recs.append("انتخاب ارقام متحمل به گرما")
                recs.append("تنظیم تاریخ کاشت برای فرار از تنش")
            
            if rain_change < -10:
                recs.append("بهبود سیستم‌های آبیاری و افزایش راندمان")
                recs.append("جمع‌آوری و ذخیره آب باران")
            
            # توصیه بر اساس وضعیت خاک
            soc_trend = scenario_data["soil_health"]["soc_trend_percent_per_year"]
            if soc_trend < 0:
                recs.append("افزایش مواد آلی خاک (کمپوست، کود سبز)")
                recs.append("کشاورزی حفاظتی (کم‌خاک‌ورزی)")
            
            ec_trend = scenario_data["soil_health"]["ec_trend_ds_m_per_year"]
            if ec_trend > 0.1:
                recs.append("اجرای برنامه آبشویی منظم")
                recs.append("بهبود زهکشی و کاهش آب ورودی شور")
            
            # توصیه بر اساس بلایا
            disasters = region.get("historical_disasters", [])
            for disaster in disasters:
                if disaster["frequency"] > 0.2:
                    recs.append(f"آمادگی برای {disaster['type']} (احتمال {disaster['frequency']*100:.0f}٪)")
            
            recommendations[scenario_id] = recs[:5]  # حداکثر ۵ توصیه
        
        return recommendations


# ============================================================
# بخش ۴: تولید گزارش
# ============================================================

def generate_report(forecast: Dict) -> str:
    """تولید گزارش متنی از پیش‌بینی"""
    
    region = forecast["region"]
    
    report = []
    report.append("=" * 70)
    report.append(f"پیش‌بینی هیدروما: {region['name_fa']}")
    report.append(f"({region['name_en']})")
    report.append("=" * 70)
    report.append(f"قاره: {region['continent']} | کشور: {region['country']}")
    report.append(f"اقلیم کوپن: {region['koppen']}")
    report.append(f"مختصات: {region['coordinates']['lat']}°N, {region['coordinates']['lon']}°E")
    report.append(f"ارتفاع: {region['coordinates']['elevation_m']} متر")
    report.append(f"افق پیش‌بینی: {forecast['horizon_years']} سال")
    report.append("")
    
    # سناریوها
    report.append("-" * 70)
    report.append("سناریوهای پیش‌بینی:")
    report.append("-" * 70)
    
    for scenario_id, scenario in forecast["scenarios"].items():
        report.append(f"\n📊 {scenario['name_fa']} ({scenario['name_en']}):")
        report.append(f"   تغییر دما: {scenario['climate_changes']['temp_change_c']:+.1f}°C")
        report.append(f"   تغییر بارش: {scenario['climate_changes']['rain_change_percent']:+.1f}%")
        report.append(f"   عملکرد پیش‌بینی‌شده: {scenario['yield_prediction']['P50']:.2f} تن/هکتار")
        report.append(f"   بازه اطمینان: {scenario['yield_prediction']['P10']:.2f} - {scenario['yield_prediction']['P90']:.2f}")
        report.append(f"   روند کربن آلی: {scenario['soil_health']['soc_trend_percent_per_year']:+.3f}%/سال")
        report.append(f"   روند شوری: {scenario['soil_health']['ec_trend_ds_m_per_year']:+.3f} dS/m/سال")
        report.append(f"   سطح ریسک: {scenario['risk_level']}")
    
    # بلایا
    report.append("\n" + "-" * 70)
    report.append("احتمالات بلایا:")
    report.append("-" * 70)
    
    for disaster, data in forecast["disaster_probabilities"].items():
        report.append(f"   {disaster}: احتمال {data['annual_probability']*100:.0f}% | شدت: {data['expected_intensity']}")
    
    # توصیه‌ها
    report.append("\n" + "-" * 70)
    report.append("توصیه‌های اقدام (سناریوی پایه):")
    report.append("-" * 70)
    
    for i, rec in enumerate(forecast["recommendations"].get("baseline", []), 1):
        report.append(f"   {i}. {rec}")
    
    report.append("\n" + "=" * 70)
    report.append(f"سطح اطمینان: {forecast['confidence_level']}")
    report.append(f"کیفیت داده: {forecast['data_quality']}")
    report.append("=" * 70)
    
    return "\n".join(report)


# ============================================================
# بخش ۵: اجرای اصلی
# ============================================================

def main():
    print("=" * 70)
    print("موتور سناریونویسی و پیش‌بینی هیدروما")
    print("۱۰ منطقه نمونه از ۵ قاره")
    print("=" * 70)
    
    # ایجاد موتور سناریو
    engine = ScenarioEngine()
    
    # تولید پیش‌بینی برای همه مناطق
    all_forecasts = {}
    
    for region_id in GLOBAL_REGIONS.keys():
        print(f"\n🌍 در حال تولید پیش‌بینی برای: {GLOBAL_REGIONS[region_id]['name_fa']}")
        
        forecast = engine.generate_forecast(region_id, horizon_years=10)
        all_forecasts[region_id] = forecast
        
        # نمایش خلاصه
        if "error" not in forecast:
            baseline = forecast["scenarios"]["baseline"]
            print(f"   ✅ پیش‌بینی پایه: {baseline['yield_prediction']['P50']:.2f} تن/هکتار")
            print(f"      ریسک: {baseline['risk_level']}")
    
    # ذخیره پیش‌بینی‌ها
    output_dir = ROOT / "docs" / "hydroma" / "forecasts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ذخیره فایل JSON کامل
    forecasts_file = output_dir / "global_forecasts.json"
    forecasts_file.write_text(
        json.dumps(all_forecasts, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n✅ پیش‌بینی‌ها ذخیره شد: {forecasts_file}")
    
    # تولید گزارش‌های متنی
    print("\n" + "=" * 70)
    print("گزارش‌های تفصیلی:")
    print("=" * 70)
    
    for region_id, forecast in all_forecasts.items():
        if "error" not in forecast:
            report = generate_report(forecast)
            
            # ذخیره گزارش
            report_file = output_dir / f"forecast_{region_id}.txt"
            report_file.write_text(report, encoding="utf-8")
            
            # نمایش گزارش برای چند منطقه نمونه
            if region_id in ["R01_yazd_iran", "R05_amazon_brazil", "R09_scandinavia"]:
                print(f"\n{'='*70}")
                print(f"نمونه گزارش: {GLOBAL_REGIONS[region_id]['name_fa']}")
                print(f"{'='*70}")
                print(report)
    
    # خلاصه نهایی
    print("\n" + "=" * 70)
    print("خلاصه نهایی")
    print("=" * 70)
    
    # شمارش سطوح ریسک
    risk_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for region_id, forecast in all_forecasts.items():
        if "error" not in forecast:
            risk = forecast["scenarios"]["baseline"]["risk_level"]
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
    
    print(f"   📊 تعداد مناطق: {len(all_forecasts)}")
    print(f"   🟢 ریسک پایین: {risk_counts['Low']}")
    print(f"   🟡 ریسک متوسط: {risk_counts['Medium']}")
    print(f"   🟠 ریسک بالا: {risk_counts['High']}")
    print(f"   🔴 ریسک بحرانی: {risk_counts['Critical']}")
    print("=" * 70)
    
    print("\n📋 فایل‌های تولید شده:")
    print(f"   ۱. {forecasts_file}")
    print(f"   ۲. گزارش‌های تفصیلی: {output_dir}/forecast_*.txt")
    print("=" * 70)
    
    print("\n🎯 شعار: تن زمین خسته است")
    print("   ما در خدمت بشر و زمین هستیم با پیوند طبیعت و بشر")
    print("=" * 70)


if __name__ == "__main__":
    main()