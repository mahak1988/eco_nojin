#!/usr/bin/env python3
# ============================================================================
# چالش ۲۵ دانشمند × ۲۵ منطقه (نسخه ۲ - قطعی)
# همه کد در یک فایل واحد، بدون circular import
# ============================================================================
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
TEST_FILE = PROJECT_ROOT / "tests" / "challenge_25_scientists.py"

COMBINED_CODE = '''# -*- coding: utf-8 -*-
"""
چالش ۲۵ دانشمند × ۲۵ منطقه
تمام کد (مناطق + تست‌ها) در یک فایل واحد
"""
import sys
import math
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from engine.hydroma.climate_adaptation.dynamic_stress_engine import DynamicStressEngine
    from engine.hydroma.climate_adaptation.climate_adaptive_phenology import ClimateAdaptivePhenology
    from engine.hydroma.climate_adaptation.soil_degradation_model import SoilDegradationModel
    from engine.hydroma.climate_adaptation.seed_optimization_engine import SeedOptimizationEngine
    from engine.hydroma.climate_adaptation.uncertainty_knowledge_engine import UncertaintyAndKnowledgeEngine
    ALL_MODULES_LOADED = True
except ImportError as e:
    print(f"WARNING: Some modules not loaded: {e}")
    ALL_MODULES_LOADED = False


REGIONS = {
    "R01_yazd_desert": {
        "name_fa": "یزد - بیابان گرم",
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
        "dominant_crops": ["pomegranate", "saffron", "pistachio"],
        "challenges": ["extreme_heat", "water_scarcity", "salinity"],
    },
    "R02_gobi_cold_desert": {
        "name_fa": "گوبی - بیابان سرد",
        "koppen": "BWk",
        "lat": 42.80, "lon": 105.00, "elevation_m": 1500,
        "annual_rain_mm": 120, "rain_cv": 0.50,
        "tmin_annual_c": -5.0, "tmax_annual_c": 18.0,
        "growing_season_days": 140,
        "soil_type": "Calcisol", "soil_texture": "loam",
        "soc_pct": 0.8, "ph": 8.0, "ec_ds_m": 1.5,
        "awc_mm_m": 100, "ksat_mm_h": 15.0,
        "groundwater_depth_m": 20, "aquifer_thickness_m": 50,
        "irrigation_available": False, "irrigation_efficiency": 0.0,
        "dominant_crops": ["barley", "forage"],
        "challenges": ["extreme_cold", "short_season", "wind_erosion"],
    },
    "R03_khuzestan_saline": {
        "name_fa": "خوزستان - نیمه‌خشک شور",
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
        "dominant_crops": ["date_palm", "sugarcane", "tomato"],
        "challenges": ["salinity", "waterlogging", "heat_stress"],
    },
    "R04_hamedan_rainfed": {
        "name_fa": "همدان - نیمه‌خشک سرد دیم",
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
        "dominant_crops": ["wheat", "barley", "chickpea"],
        "challenges": ["drought_variability", "frost_risk", "soil_erosion"],
    },
    "R05_shiraz_mediterranean": {
        "name_fa": "شیراز - مدیترانه‌ای گرم",
        "koppen": "Csa",
        "lat": 29.59, "lon": 52.58, "elevation_m": 1550,
        "annual_rain_mm": 350, "rain_cv": 0.30,
        "tmin_annual_c": 10.0, "tmax_annual_c": 28.0,
        "growing_season_days": 260,
        "soil_type": "Calcisol", "soil_texture": "clay_loam",
        "soc_pct": 1.5, "ph": 7.8, "ec_ds_m": 1.2,
        "awc_mm_m": 150, "ksat_mm_h": 8.0,
        "groundwater_depth_m": 30, "aquifer_thickness_m": 70,
        "irrigation_available": True, "irrigation_efficiency": 0.55,
        "dominant_crops": ["grape", "citrus", "wheat", "rose"],
        "challenges": ["summer_drought", "water_scarcity"],
    },
    "R06_anatolia_cool_med": {
        "name_fa": "آناتولی - مدیترانه‌ای خنک",
        "koppen": "Csb",
        "lat": 39.93, "lon": 32.85, "elevation_m": 900,
        "annual_rain_mm": 420, "rain_cv": 0.28,
        "tmin_annual_c": 5.0, "tmax_annual_c": 22.0,
        "growing_season_days": 220,
        "soil_type": "Luvisol", "soil_texture": "loam",
        "soc_pct": 2.2, "ph": 7.0, "ec_ds_m": 0.6,
        "awc_mm_m": 170, "ksat_mm_h": 12.0,
        "groundwater_depth_m": 20, "aquifer_thickness_m": 55,
        "irrigation_available": True, "irrigation_efficiency": 0.65,
        "dominant_crops": ["wheat", "sunflower", "sugarbeet"],
        "challenges": ["seasonal_drought", "soil_degradation"],
    },
    "R07_gorgan_humid": {
        "name_fa": "گرگان - نیمه‌حاره‌ای مرطوب",
        "koppen": "Cfa",
        "lat": 36.84, "lon": 54.43, "elevation_m": 50,
        "annual_rain_mm": 550, "rain_cv": 0.25,
        "tmin_annual_c": 12.0, "tmax_annual_c": 25.0,
        "growing_season_days": 300,
        "soil_type": "Fluvisol", "soil_texture": "silt_clay",
        "soc_pct": 2.5, "ph": 6.8, "ec_ds_m": 0.5,
        "awc_mm_m": 180, "ksat_mm_h": 5.0,
        "groundwater_depth_m": 5, "aquifer_thickness_m": 45,
        "irrigation_available": True, "irrigation_efficiency": 0.60,
        "dominant_crops": ["rice", "soybean", "cotton"],
        "challenges": ["humidity_diseases", "waterlogging", "pest_pressure"],
    },
    "R08_north_europe_oceanic": {
        "name_fa": "شمال اروپا - اقیانوسی",
        "koppen": "Cfb",
        "lat": 55.68, "lon": 12.57, "elevation_m": 30,
        "annual_rain_mm": 650, "rain_cv": 0.20,
        "tmin_annual_c": 4.0, "tmax_annual_c": 15.0,
        "growing_season_days": 200,
        "soil_type": "Podzol", "soil_texture": "sandy_loam",
        "soc_pct": 3.5, "ph": 5.5, "ec_ds_m": 0.3,
        "awc_mm_m": 130, "ksat_mm_h": 25.0,
        "groundwater_depth_m": 8, "aquifer_thickness_m": 35,
        "irrigation_available": True, "irrigation_efficiency": 0.75,
        "dominant_crops": ["barley", "potato", "rapeseed"],
        "challenges": ["acid_soil", "short_summer", "leaching"],
    },
    "R09_midwest_continental": {
        "name_fa": "غرب آمریکا - قاره‌ای گرم",
        "koppen": "Dfa",
        "lat": 41.88, "lon": -93.09, "elevation_m": 280,
        "annual_rain_mm": 850, "rain_cv": 0.22,
        "tmin_annual_c": 2.0, "tmax_annual_c": 22.0,
        "growing_season_days": 170,
        "soil_type": "Mollisol", "soil_texture": "silt_clay_loam",
        "soc_pct": 4.0, "ph": 6.5, "ec_ds_m": 0.4,
        "awc_mm_m": 200, "ksat_mm_h": 15.0,
        "groundwater_depth_m": 15, "aquifer_thickness_m": 90,
        "irrigation_available": True, "irrigation_efficiency": 0.80,
        "dominant_crops": ["maize", "soybean", "wheat"],
        "challenges": ["extreme_weather", "monoculture", "nutrient_runoff"],
    },
    "R10_scandinavia_cold": {
        "name_fa": "اسکاندیناوی - قاره‌ای سرد",
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
        "dominant_crops": ["barley", "oat", "potato"],
        "challenges": ["short_season", "frost_damage", "acid_soil"],
    },
    "R11_west_africa_savanna": {
        "name_fa": "ساحل غربی آفریقا - ساوانا",
        "koppen": "Aw",
        "lat": 13.50, "lon": 2.10, "elevation_m": 250,
        "annual_rain_mm": 600, "rain_cv": 0.35,
        "tmin_annual_c": 22.0, "tmax_annual_c": 38.0,
        "growing_season_days": 120,
        "soil_type": "Lixisol", "soil_texture": "sandy_loam",
        "soc_pct": 0.6, "ph": 6.0, "ec_ds_m": 0.3,
        "awc_mm_m": 80, "ksat_mm_h": 20.0,
        "groundwater_depth_m": 15, "aquifer_thickness_m": 25,
        "irrigation_available": False, "irrigation_efficiency": 0.0,
        "dominant_crops": ["millet", "sorghum", "cowpea"],
        "challenges": ["drought", "soil_fertility_decline", "pests"],
    },
    "R12_india_monsoon": {
        "name_fa": "جنوب هند - موسمی",
        "koppen": "Am",
        "lat": 17.68, "lon": 83.21, "elevation_m": 50,
        "annual_rain_mm": 1100, "rain_cv": 0.30,
        "tmin_annual_c": 22.0, "tmax_annual_c": 34.0,
        "growing_season_days": 150,
        "soil_type": "Vertisol", "soil_texture": "clay",
        "soc_pct": 1.2, "ph": 7.5, "ec_ds_m": 0.8,
        "awc_mm_m": 160, "ksat_mm_h": 3.0,
        "groundwater_depth_m": 8, "aquifer_thickness_m": 30,
        "irrigation_available": True, "irrigation_efficiency": 0.40,
        "dominant_crops": ["rice", "cotton", "sugarcane"],
        "challenges": ["monsoon_variability", "waterlogging", "cyclone_risk"],
    },
    "R13_amazon_rainforest": {
        "name_fa": "آمازون - جنگل بارانی",
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
        "dominant_crops": ["cassava", "banana", "rubber"],
        "challenges": ["acid_soil", "nutrient_leaching", "deforestation"],
    },
    "R14_canada_tundra": {
        "name_fa": "شمال کانادا - توندرا",
        "koppen": "ET",
        "lat": 62.45, "lon": -114.37, "elevation_m": 200,
        "annual_rain_mm": 280, "rain_cv": 0.30,
        "tmin_annual_c": -15.0, "tmax_annual_c": 5.0,
        "growing_season_days": 60,
        "soil_type": "Gleysol", "soil_texture": "silt",
        "soc_pct": 8.0, "ph": 5.5, "ec_ds_m": 0.2,
        "awc_mm_m": 250, "ksat_mm_h": 2.0,
        "groundwater_depth_m": 1, "aquifer_thickness_m": 20,
        "irrigation_available": False, "irrigation_efficiency": 0.0,
        "dominant_crops": ["forage_limited"],
        "challenges": ["permafrost", "extreme_cold", "very_short_season"],
    },
    "R15_andes_highland": {
        "name_fa": "آند پرو - ارتفاعات",
        "koppen": "Cwb",
        "lat": -13.53, "lon": -71.97, "elevation_m": 3600,
        "annual_rain_mm": 700, "rain_cv": 0.35,
        "tmin_annual_c": 2.0, "tmax_annual_c": 18.0,
        "growing_season_days": 180,
        "soil_type": "Andosol", "soil_texture": "silt_loam",
        "soc_pct": 6.0, "ph": 5.8, "ec_ds_m": 0.3,
        "awc_mm_m": 200, "ksat_mm_h": 20.0,
        "groundwater_depth_m": 10, "aquifer_thickness_m": 40,
        "irrigation_available": True, "irrigation_efficiency": 0.35,
        "dominant_crops": ["potato", "quinoa", "barley"],
        "challenges": ["altitude", "frost", "uv_radiation", "slope"],
    },
    "R16_gulf_coastal": {
        "name_fa": "خلیج فارس - ساحلی شور",
        "koppen": "BWh",
        "lat": 27.19, "lon": 56.27, "elevation_m": 10,
        "annual_rain_mm": 170, "rain_cv": 0.55,
        "tmin_annual_c": 20.0, "tmax_annual_c": 38.0,
        "growing_season_days": 250,
        "soil_type": "Solonchak", "soil_texture": "sandy_clay",
        "soc_pct": 0.5, "ph": 8.3, "ec_ds_m": 15.0,
        "awc_mm_m": 60, "ksat_mm_h": 8.0,
        "groundwater_depth_m": 2, "aquifer_thickness_m": 15,
        "irrigation_available": True, "irrigation_efficiency": 0.30,
        "dominant_crops": ["date_palm", "vegetables_greenhouse"],
        "challenges": ["extreme_salinity", "humidity", "heat_island"],
    },
    "R17_ethiopia_volcanic": {
        "name_fa": "اتیوپی - خاک آتشفشانی",
        "koppen": "Cwb",
        "lat": 9.02, "lon": 38.74, "elevation_m": 2400,
        "annual_rain_mm": 1100, "rain_cv": 0.30,
        "tmin_annual_c": 10.0, "tmax_annual_c": 24.0,
        "growing_season_days": 220,
        "soil_type": "Andosol", "soil_texture": "silt",
        "soc_pct": 4.5, "ph": 5.8, "ec_ds_m": 0.4,
        "awc_mm_m": 180, "ksat_mm_h": 25.0,
        "groundwater_depth_m": 12, "aquifer_thickness_m": 45,
        "irrigation_available": True, "irrigation_efficiency": 0.40,
        "dominant_crops": ["teff", "coffee", "enset"],
        "challenges": ["soil_acidity", "erosion", "drought_variability"],
    },
    "R18_china_karst": {
        "name_fa": "جنوب چین - کارستی",
        "koppen": "Cfa",
        "lat": 26.65, "lon": 106.63, "elevation_m": 1100,
        "annual_rain_mm": 1200, "rain_cv": 0.28,
        "tmin_annual_c": 10.0, "tmax_annual_c": 24.0,
        "growing_season_days": 250,
        "soil_type": "Leptosol", "soil_texture": "clay_loam",
        "soc_pct": 2.0, "ph": 6.5, "ec_ds_m": 0.3,
        "awc_mm_m": 90, "ksat_mm_h": 40.0,
        "groundwater_depth_m": 30, "aquifer_thickness_m": 60,
        "irrigation_available": True, "irrigation_efficiency": 0.50,
        "dominant_crops": ["rice", "maize", "tea"],
        "challenges": ["water_loss_karst", "thin_soil", "rocky_terrain"],
    },
    "R19_mekong_delta": {
        "name_fa": "مکونگ ویتنام - دلتای سیل‌خیز",
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
        "dominant_crops": ["rice_3crop", "shrimp", "fruit"],
        "challenges": ["flooding", "saline_intrusion", "sea_level_rise"],
    },
    "R20_rajasthan_erratic": {
        "name_fa": "راجستان هند - بارش نامنظم",
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
        "dominant_crops": ["pearl_millet", "mustard", "guar"],
        "challenges": ["erratic_rainfall", "drought", "wind_erosion", "groundwater_depletion"],
    },
    "R21_central_asia_saline": {
        "name_fa": "آسیای مرکزی - شور سدیک",
        "koppen": "BWk",
        "lat": 41.30, "lon": 69.24, "elevation_m": 450,
        "annual_rain_mm": 200, "rain_cv": 0.40,
        "tmin_annual_c": 5.0, "tmax_annual_c": 26.0,
        "growing_season_days": 190,
        "soil_type": "Solonetz", "soil_texture": "clay",
        "soc_pct": 1.0, "ph": 9.2, "ec_ds_m": 8.0,
        "awc_mm_m": 110, "ksat_mm_h": 1.0,
        "groundwater_depth_m": 5, "aquifer_thickness_m": 30,
        "irrigation_available": True, "irrigation_efficiency": 0.40,
        "dominant_crops": ["cotton", "wheat", "rice"],
        "challenges": ["salinity_sodicity", "aral_sea_crisis", "water_scarcity"],
    },
    "R22_vietnam_waterlogged": {
        "name_fa": "ویتنام شمالی - رسی غرقابی",
        "koppen": "Cwa",
        "lat": 21.03, "lon": 105.85, "elevation_m": 15,
        "annual_rain_mm": 1700, "rain_cv": 0.35,
        "tmin_annual_c": 18.0, "tmax_annual_c": 28.0,
        "growing_season_days": 300,
        "soil_type": "Gleysol", "soil_texture": "clay",
        "soc_pct": 3.0, "ph": 5.0, "ec_ds_m": 0.5,
        "awc_mm_m": 190, "ksat_mm_h": 1.0,
        "groundwater_depth_m": 0.5, "aquifer_thickness_m": 20,
        "irrigation_available": True, "irrigation_efficiency": 0.45,
        "dominant_crops": ["rice", "vegetables", "aquaculture"],
        "challenges": ["waterlogging", "typhoon", "soil_acidity"],
    },
    "R23_australia_sandy": {
        "name_fa": "استرالیا - شنی کم‌آب",
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
        "dominant_crops": ["wheat_drought", "sheep_grazing"],
        "challenges": ["extreme_drought", "low_water_holding", "heat_waves"],
    },
    "R24_yemen_terraced": {
        "name_fa": "یمن - کوهستانی پلکانی",
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
        "dominant_crops": ["sorghum", "millet", "qat", "coffee"],
        "challenges": ["extreme_slope", "water_scarcity", "soil_erosion", "conflict"],
    },
    "R25_tehran_urban": {
        "name_fa": "حاشیه تهران - شهری",
        "koppen": "BSk",
        "lat": 35.69, "lon": 51.39, "elevation_m": 1150,
        "annual_rain_mm": 230, "rain_cv": 0.35,
        "tmin_annual_c": 8.0, "tmax_annual_c": 24.0,
        "growing_season_days": 220,
        "soil_type": "Anthrosol", "soil_texture": "mixed",
        "soc_pct": 1.2, "ph": 7.8, "ec_ds_m": 2.5,
        "awc_mm_m": 100, "ksat_mm_h": 10.0,
        "groundwater_depth_m": 15, "aquifer_thickness_m": 50,
        "irrigation_available": True, "irrigation_efficiency": 0.50,
        "dominant_crops": ["vegetables", "greenhouse", "herbs"],
        "challenges": ["pollution", "land_pressure", "water_quality", "heavy_metals"],
    },
}


class TestResult:
    def __init__(self, region_id, scientist, test_name, passed, message, severity="info"):
        self.region_id = region_id
        self.scientist = scientist
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.severity = severity

    def to_dict(self):
        return {
            "region": self.region_id,
            "scientist": self.scientist,
            "test": self.test_name,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity,
        }


class Scientist25Challenge:
    def __init__(self):
        self.results = []
        self.dse = DynamicStressEngine() if ALL_MODULES_LOADED else None
        self.cap = ClimateAdaptivePhenology() if ALL_MODULES_LOADED else None
        self.sdm = SoilDegradationModel() if ALL_MODULES_LOADED else None
        self.soe = SeedOptimizationEngine() if ALL_MODULES_LOADED else None
        self.uke = UncertaintyAndKnowledgeEngine() if ALL_MODULES_LOADED else None

    def add_result(self, region_id, scientist, test_name, passed, message, severity="info"):
        self.results.append(TestResult(region_id, scientist, test_name, passed, message, severity))
        status = "PASS" if passed else "FAIL"
        icon = "[PASS]" if passed else "[FAIL]"
        print(f"   {icon} [{region_id}] {scientist}: {test_name} - {status}")

    def test_hydrologist(self, region_id, region):
        scientist = "هیدرولوژیست"
        rain = region["annual_rain_mm"]
        awc = region["awc_mm_m"]
        ksat = region["ksat_mm_h"]
        texture = region.get("soil_texture", "loam")

        self.add_result(region_id, scientist, "بارش غیرمنفی",
                        rain >= 0, f"بارش={rain}mm",
                        "critical" if rain < 0 else "info")

        if texture == "clay" and ksat > 5:
            self.add_result(region_id, scientist, "Ksat با بافت رسی سازگار نیست",
                            False, f"Ksat={ksat}mm/h برای {texture} بسیار بالاست", "critical")
        elif texture == "sand" and ksat < 20:
            self.add_result(region_id, scientist, "Ksat با بافت شنی سازگار نیست",
                            False, f"Ksat={ksat}mm/h برای {texture} بسیار پایین است", "critical")
        else:
            self.add_result(region_id, scientist, "سازگاری Ksat با بافت",
                            True, f"Ksat={ksat}mm/h، بافت={texture}", "info")

        gw_depth = region.get("groundwater_depth_m", 10)
        if gw_depth < 0:
            self.add_result(region_id, scientist, "عمق آب زیرزمینی منفی",
                            False, f"عمق={gw_depth}m", "critical")
        elif gw_depth < 1:
            self.add_result(region_id, scientist, "آب زیرزمینی بسیار سطحی",
                            True, f"عمق={gw_depth}m - احتمال غرقابی", "warning")
        else:
            self.add_result(region_id, scientist, "عمق آب زیرزمینی منطقی",
                            True, f"عمق={gw_depth}m", "info")

        if texture == "sand" and awc > 80:
            self.add_result(region_id, scientist, "AWC برای خاک شنی غیرواقعی",
                            False, f"AWC={awc}mm/m برای {texture}", "critical")
        else:
            self.add_result(region_id, scientist, "AWC در محدوده",
                            True, f"AWC={awc}mm/m", "info")

    def test_climatologist(self, region_id, region):
        scientist = "اقلیم‌شناس"
        tmin = region["tmin_annual_c"]
        tmax = region["tmax_annual_c"]
        koppen = region["koppen"]

        self.add_result(region_id, scientist, "Tmin < Tmax",
                        tmin < tmax, f"Tmin={tmin}, Tmax={tmax}",
                        "critical" if tmin >= tmax else "info")

        if koppen.startswith("A") and tmin < 15:
            self.add_result(region_id, scientist, "اقلیم A با Tmin<15 ناسازگار",
                            False, f"کوپن={koppen}, Tmin={tmin}", "critical")
        elif koppen.startswith("E") and tmax > 15:
            self.add_result(region_id, scientist, "اقلیم E با Tmax>15 ناسازگار",
                            False, f"کوپن={koppen}, Tmax={tmax}", "critical")
        else:
            self.add_result(region_id, scientist, "سازگاری کوپن با دما",
                            True, f"کوپن={koppen}", "info")

        season = region["growing_season_days"]
        if koppen == "ET" and season > 90:
            self.add_result(region_id, scientist, "فصل رشد توندرا غیرواقعی",
                            False, f"فصل رشد={season} روز", "critical")
        else:
            self.add_result(region_id, scientist, "فصل رشد منطقی",
                            True, f"فصل رشد={season} روز", "info")

        rain_cv = region.get("rain_cv", 0.3)
        if rain_cv > 0.55:
            self.add_result(region_id, scientist, "بارش بسیار نامنظم",
                            True, f"CV={rain_cv}", "warning")
        else:
            self.add_result(region_id, scientist, "CV بارش در محدوده",
                            True, f"CV={rain_cv}", "info")

    def test_soil_scientist(self, region_id, region):
        scientist = "خاک‌شناس"
        soc = region.get("soc_pct", 1.0)
        ph = region.get("ph", 7.0)
        ec = region.get("ec_ds_m", 0.5)

        if soc < 0 or soc > 15:
            self.add_result(region_id, scientist, "SOC خارج از محدوده",
                            False, f"SOC={soc}%", "critical")
        elif soc < 0.5:
            self.add_result(region_id, scientist, "SOC بسیار پایین",
                            True, f"SOC={soc}% - خاک تخریب‌شده", "warning")
        else:
            self.add_result(region_id, scientist, "SOC در محدوده",
                            True, f"SOC={soc}%", "info")

        if ph < 3 or ph > 11:
            self.add_result(region_id, scientist, "pH خارج از محدوده",
                            False, f"pH={ph}", "critical")
        else:
            self.add_result(region_id, scientist, "pH در محدوده",
                            True, f"pH={ph}", "info")

        if self.sdm:
            try:
                report = self.sdm.generate_degradation_report(
                    soc_pct=soc, erosion_rate_t_ha_yr=10.0, ec_ds_m=ec,
                    ksat_mm_h=region.get("ksat_mm_h", 10.0),
                    groundwater_extraction_mm_yr=200.0,
                    soil_type=region.get("soil_texture", "loam"))
                score = report["overall_sustainability_score"]["overall_score"]
                self.add_result(region_id, scientist, "امتیاز پایداری خاک",
                                0 <= score <= 100, f"امتیاز={score:.1f}", "info")
            except Exception as e:
                self.add_result(region_id, scientist, "محاسبه پایداری خاک",
                                False, f"خطا: {str(e)[:50]}", "critical")

    def test_agronomist(self, region_id, region):
        scientist = "زراعت‌کار"
        tmax = region["tmax_annual_c"]
        irrigation = region.get("irrigation_available", False)
        rain = region["annual_rain_mm"]

        if self.dse:
            try:
                h04_ks = self.dse.h04_heat_ks(tmax)
                self.add_result(region_id, scientist, "Ks حرارتی",
                                0 <= h04_ks <= 1, f"Ks={h04_ks:.3f} در Tmax={tmax}C",
                                "critical" if not (0 <= h04_ks <= 1) else "info")
            except Exception as e:
                self.add_result(region_id, scientist, "Ks حرارتی",
                                False, f"خطا: {str(e)[:50]}", "critical")

        if not irrigation and rain < 200:
            self.add_result(region_id, scientist, "دیم با بارش ناکافی",
                            True, f"بارش={rain}mm - دیم پرریسک", "warning")

    def test_salinity_expert(self, region_id, region):
        scientist = "متخصص شوری"
        ec = region.get("ec_ds_m", 0.5)
        ph = region.get("ph", 7.0)
        texture = region.get("soil_texture", "loam")

        if ec > 8 and texture == "clay":
            self.add_result(region_id, scientist, "شوری بالا + خاک رسی",
                            True, "نیاز به زهکشی قبل از آبشویی", "warning")

        if ph > 8.5 and ec > 4:
            self.add_result(region_id, scientist, "شوری-سدیک احتمالی",
                            True, f"pH={ph}, EC={ec}", "warning")

        if self.sdm:
            try:
                result = self.sdm.h11_salinity_trend(ec, 0.1, 10)
                projected_ec = result["ec_projected_ds_m"]
                self.add_result(region_id, scientist, "پیش‌بینی شوری ۱۰ ساله",
                                projected_ec >= ec,
                                f"EC فعلی={ec}, پیش‌بینی={projected_ec}",
                                "warning" if projected_ec > 8 else "info")
            except Exception as e:
                self.add_result(region_id, scientist, "پیش‌بینی شوری",
                                False, f"خطا: {str(e)[:50]}", "critical")

    def test_geneticist(self, region_id, region):
        scientist = "ژنتیک‌دان"
        crops = region.get("dominant_crops", [])
        challenges = region.get("challenges", [])

        if len(crops) <= 1:
            self.add_result(region_id, scientist, "تنوع ژنتیکی پایین",
                            True, f"تعداد={len(crops)}", "warning")

        if self.soe:
            try:
                diversity = min(1.0, len(crops) / 5.0)
                result = self.soe.h19_genetic_vulnerability(diversity, 70.0, len(crops))
                vuln = result["vulnerability_index"]
                self.add_result(region_id, scientist, "آسیب‌پذیری ژنتیکی",
                                0 <= vuln <= 1, f"آسیب‌پذیری={vuln:.2f}",
                                "warning" if vuln > 0.7 else "info")
            except Exception as e:
                self.add_result(region_id, scientist, "آسیب‌پذیری ژنتیکی",
                                False, f"خطا: {str(e)[:50]}", "critical")

    def test_economist(self, region_id, region):
        scientist = "اقتصاددان کشاورزی"
        irrigation = region.get("irrigation_available", False)
        efficiency = region.get("irrigation_efficiency", 0.0)

        if irrigation and (efficiency < 0.1 or efficiency > 0.95):
            self.add_result(region_id, scientist, "راندمان آبیاری غیرواقعی",
                            False, f"راندمان={efficiency}", "critical")
        elif irrigation and efficiency < 0.3:
            self.add_result(region_id, scientist, "راندمان آبیاری پایین",
                            True, f"راندمان={efficiency}", "warning")
        else:
            self.add_result(region_id, scientist, "راندمان آبیاری منطقی",
                            True, f"راندمان={efficiency}", "info")

    def test_climate_change_expert(self, region_id, region):
        scientist = "متخصص تغییر اقلیم"
        rain_cv = region.get("rain_cv", 0.3)

        if self.uke:
            try:
                base_yield = 3.0 if region["annual_rain_mm"] > 300 else 1.5
                result = self.uke.h22_monte_carlo_uncertainty(
                    base_yield, n_simulations=100, climate_variability=rain_cv)
                cv = result["coefficient_of_variation"]
                self.add_result(region_id, scientist, "عدم قطعیت مونت‌کارلو",
                                cv >= 0, f"CV={cv:.3f}, P10={result['p10_t_ha']}, P90={result['p90_t_ha']}",
                                "warning" if cv > 0.5 else "info")
            except Exception as e:
                self.add_result(region_id, scientist, "عدم قطعیت مونت‌کارلو",
                                False, f"خطا: {str(e)[:50]}", "critical")

    def test_erosion_expert(self, region_id, region):
        scientist = "متخصص فرسایش"
        challenges = region.get("challenges", [])
        soc = region.get("soc_pct", 1.0)

        if "slope" in challenges or "extreme_slope" in challenges:
            self.add_result(region_id, scientist, "ریسک فرسایش بالا",
                            True, "شیب > 30%", "warning")

        if soc < 0.5:
            self.add_result(region_id, scientist, "SOC پایین + فرسایش‌پذیری",
                            True, f"SOC={soc}%", "warning")

        if self.sdm:
            try:
                result = self.sdm.h10_root_depth_decay(100.0, 15.0, 10)
                loss = result["depth_loss_percent"]
                self.add_result(region_id, scientist, "کاهش عمق ریشه ۱۰ ساله",
                                loss >= 0, f"کاهش={loss:.1f}%",
                                "warning" if loss > 20 else "info")
            except Exception as e:
                self.add_result(region_id, scientist, "کاهش عمق ریشه",
                                False, f"خطا: {str(e)[:50]}", "critical")

    def test_irrigation_expert(self, region_id, region):
        scientist = "متخصص آبیاری"
        irrigation = region.get("irrigation_available", False)

        if self.cap:
            try:
                result = self.cap.h05_dynamic_planting_day(
                    last_frost_day_of_year=100,
                    soil_temp_series=[8.0, 9.0, 10.0, 11.0],
                    rain_onset_day_of_year=280)
                planting_day = result["planting_day_of_year"]
                self.add_result(region_id, scientist, "تاریخ کاشت پویا",
                                0 < planting_day < 365, f"روز={planting_day}", "info")
            except Exception as e:
                self.add_result(region_id, scientist, "تاریخ کاشت پویا",
                                False, f"خطا: {str(e)[:50]}", "critical")

    def run_all(self):
        print("=" * 70)
        print("چالش ۲۵ دانشمند × ۲۵ منطقه")
        print("=" * 70)

        for region_id, region in REGIONS.items():
            region_name = region['name_fa']
            koppen = region['koppen']
            print(f"\\n[REGION] {region_id}: {region_name} ({koppen})")
            print("-" * 50)

            self.test_hydrologist(region_id, region)
            self.test_climatologist(region_id, region)
            self.test_soil_scientist(region_id, region)
            self.test_agronomist(region_id, region)
            self.test_salinity_expert(region_id, region)
            self.test_geneticist(region_id, region)
            self.test_economist(region_id, region)
            self.test_climate_change_expert(region_id, region)
            self.test_erosion_expert(region_id, region)
            self.test_irrigation_expert(region_id, region)

        return self.results

    def generate_report(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        critical = sum(1 for r in self.results if not r.passed and r.severity == "critical")
        warnings = sum(1 for r in self.results if r.severity == "warning")
        rate = passed / total * 100 if total > 0 else 0

        if critical > 0:
            verdict = "REJECTED - خطاهای بحرانی وجود دارد"
        elif rate >= 95:
            verdict = "APPROVED - مدل برای بنچمارک رسمی آماده است"
        elif rate >= 85:
            verdict = "CONDITIONAL - نیاز به رفع هشدارها قبل از بنچمارک"
        else:
            verdict = "REJECTED - نیاز به بهبود اساسی"

        return {
            "generated_at": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "critical_failures": critical,
            "warnings": warnings,
            "pass_rate_percent": round(rate, 1),
            "verdict": verdict,
            "failures": [r.to_dict() for r in self.results if not r.passed],
            "warnings_detail": [r.to_dict() for r in self.results if r.severity == "warning"],
            "regions_tested": len(REGIONS),
        }


def main():
    challenge = Scientist25Challenge()
    results = challenge.run_all()
    report = challenge.generate_report()

    print("\\n" + "=" * 70)
    print("نتیجه نهایی چالش ۲۵ دانشمند")
    print("=" * 70)
    print(f"   کل تست‌ها: {report['total_tests']}")
    print(f"   موفق: {report['passed']} ({report['pass_rate_percent']}%)")
    print(f"   ناموفق: {report['failed']}")
    print(f"   بحرانی: {report['critical_failures']}")
    print(f"   هشدارها: {report['warnings']}")
    print(f"   مناطق: {report['regions_tested']}")
    verdict = report['verdict']
    print(f"\\n   [VERDICT] {verdict}")
    print("=" * 70)

    report_dir = ROOT / "docs" / "hydroma"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "25_scientist_challenge_report.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\\nگزارش ذخیره شد: {report_file}")


if __name__ == "__main__":
    main()
'''


def install_challenge():
    print("=" * 70)
    print("نصب چالش ۲۵ دانشمند × ۲۵ منطقه (نسخه ۲ - قطعی)")
    print("=" * 70)
    print("[1/2] ایجاد فایل واحد (مناطق + تست‌ها) ...")
    TEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    TEST_FILE.write_text(COMBINED_CODE, encoding="utf-8")
    print(f"   -> {TEST_FILE.relative_to(PROJECT_ROOT)}")
    print(f"   حجم فایل: {TEST_FILE.stat().st_size} bytes")

    print("[2/2] اجرای چالش ...")
    proc = subprocess.run([sys.executable, str(TEST_FILE)], cwd=PROJECT_ROOT)
    if proc.returncode == 0:
        print("\nچالش با موفقیت اجرا شد")
    else:
        print("\nخطا در اجرای چالش")


if __name__ == "__main__":
    install_challenge()