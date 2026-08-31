#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
تست سختگیرانه هیدروما (Hardcore Stress Test)
شامل:
  ۱. سناریوهای بحرانی جهانی (لوت، دره مرگ، قطب جنوب و...)
  ۲. تست مقادیر حدی و پرت
  ۳. تست ترکیبات تنش (Multi-Stress)
  ۴. تست سازگاری فرمول‌ها
  ۵. تست مرزی (Boundary)
  ۶. تست داده‌های نامعتبر
============================================================================
"""
import json
import math
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

KB_FILE = ROOT / "docs" / "hydroma" / "knowledge_base_detailed.json"
DATA_FILE = ROOT / "docs" / "hydroma" / "knowledge_base_data.json"
REPORT_FILE = ROOT / "docs" / "hydroma" / "hardcore_stress_report.json"


# ============================================================
# بخش ۱: سناریوهای بحرانی واقعی جهان (Extreme Real-World Cases)
# ============================================================

EXTREME_GLOBAL_SCENARIOS = {
    # بیابان لوت - گرم‌ترین نقطه زمین (۸۰.۸ درجه سطحی ثبت‌شده)
    "LUT_DESERT_IRAN": {
        "name": "بیابان لوت (ایران)",
        "description": "گرم‌ترین نقطه ثبت‌شده زمین",
        "extreme_type": "HEAT_EXTREME",
        "conditions": {
            "temp": 56.0,
            "LST": 80.8,  # Land Surface Temperature
            "rain": 12,
            "humidity": 5,
            "wind": 45,
            "ec": 25.0,
            "ph": 8.8,
            "soc": 0.05,
            "awc": 15,
            "slope": 2,
        },
        "expected_failures": ["Pn", "Tr", "LUE", "Yield"],
    },
    
    # دره مرگ - آمریکا
    "DEATH_VALLEY_USA": {
        "name": "دره مرگ (آمریکا)",
        "description": "رکورددار دمای هوا (۵۶.۷°C)",
        "extreme_type": "HEAT_EXTREME",
        "conditions": {
            "temp": 56.7,
            "rain": 60,
            "humidity": 8,
            "wind": 30,
            "ec": 15.0,
            "ph": 8.5,
            "soc": 0.1,
            "awc": 20,
        },
        "expected_failures": ["Tr", "gs", "Yield"],
    },
    
    # قطب جنوب - سردترین نقطه
    "ANTARCTICA": {
        "name": "قطب جنوب (Vostok)",
        "description": "سردترین دمای ثبت‌شده (-۸۹.۲°C)",
        "extreme_type": "COLD_EXTREME",
        "conditions": {
            "temp": -89.2,
            "rain": 50,  # بارش برفی
            "humidity": 20,
            "wind": 100,
            "ec": 0.05,
            "ph": 5.5,
            "soc": 0.01,
            "awc": 5,
        },
        "expected_failures": ["Pn", "Yield", "Growing_Season"],
    },
    
    # سیبری - سرمای شدید
    "SIBERIA_RUSSIA": {
        "name": "اویماکون (سیبری)",
        "description": "سردترین سکونتگاه دائمی (-۶۷.۷°C)",
        "extreme_type": "COLD_EXTREME",
        "conditions": {
            "temp": -67.7,
            "rain": 200,
            "humidity": 70,
            "wind": 15,
            "ec": 0.1,
            "ph": 5.0,
            "soc": 3.5,
            "awc": 80,
        },
        "expected_failures": ["Pn", "Tr", "Yield"],
    },
    
    # چرآپونجی - مرطوب‌ترین نقطه زمین
    "CHERRAPUNJI_INDIA": {
        "name": "چرآپونجی (هند)",
        "description": "بیشترین بارش سالانه جهان (۱۱,۷۷۷ میلی‌متر)",
        "extreme_type": "RAINFALL_EXTREME",
        "conditions": {
            "temp": 22.0,
            "rain": 11777,
            "humidity": 95,
            "wind": 20,
            "ec": 0.05,
            "ph": 4.5,
            "soc": 2.5,
            "awc": 200,
            "slope": 45,
        },
        "expected_failures": ["Erosion", "Nutrient_Leaching"],
    },
    
    # دریاچه ارومیه - شوری بسیار بالا
    "URMIA_LAKE_IRAN": {
        "name": "دریاچه ارومیه (ایران)",
        "description": "شوری بحرانی (۲۰۰-۳۰۰ dS/m در خشک‌ترین حالت)",
        "extreme_type": "SALINITY_EXTREME",
        "conditions": {
            "temp": 25.0,
            "rain": 200,
            "humidity": 40,
            "ec": 300.0,  # شوری بحرانی
            "ph": 9.2,
            "soc": 0.2,
            "awc": 30,
        },
        "expected_failures": ["Yield", "Pn", "Tr", "gs"],
    },
    
    # دریای مرده - شوری فوق‌العاده
    "DEAD_SEA": {
        "name": "دریای مرده",
        "description": "شورترین آب جهان (~۳۴۰ dS/m)",
        "extreme_type": "SALINITY_EXTREME",
        "conditions": {
            "temp": 30.0,
            "rain": 50,
            "humidity": 30,
            "ec": 340.0,
            "ph": 6.0,
            "soc": 0.05,
            "awc": 10,
        },
        "expected_failures": ["Yield", "Pn"],
    },
    
    # جنگل آمازون در سیل بزرگ
    "AMAZON_FLOOD": {
        "name": "آمازون - سیل بزرگ ۲۰۲۳",
        "description": "سیل بی‌سابقه با سطح آب +۲۰ متر",
        "extreme_type": "FLOOD_EXTREME",
        "conditions": {
            "temp": 28.0,
            "rain": 4500,
            "humidity": 98,
            "ec": 0.05,
            "ph": 5.5,
            "soc": 4.0,
            "awc": 300,  # غرقابی کامل
            "flood_depth": 20,
        },
        "expected_failures": ["Soil_Aeration", "Root_Growth"],
    },
    
    # خشکسالی قرن آفریقا
    "AFRICA_MEGA_DROUGHT": {
        "name": "خشکسالی شاخ آفریقا ۲۰۲۲",
        "description": "۵ فصل متوالی بدون بارش",
        "extreme_type": "DROUGHT_EXTREME",
        "conditions": {
            "temp": 38.0,
            "rain": 0,  # پنج فصل متوالی صفر
            "humidity": 10,
            "ec": 8.0,
            "ph": 7.5,
            "soc": 0.3,
            "awc": 5,
        },
        "expected_failures": ["Yield", "Pn", "Tr", "Livestock"],
    },
    
    # آتش‌سوزی استرالیا ۲۰۲۰
    "AUSTRALIA_FIRES_2020": {
        "name": "آتش‌سوزی استرالیا (۲۰۲۰)",
        "description": "بزرگ‌ترین آتش‌سوزی قرن - ۱۸ میلیون هکتار",
        "extreme_type": "FIRE_EXTREME",
        "conditions": {
            "temp": 48.0,
            "rain": 10,
            "humidity": 5,
            "wind": 120,
            "ec": 1.5,
            "ph": 4.0,
            "soc": 0.01,  # از بین رفته در آتش
            "awc": 15,
            "fire_intensity": "extreme",
        },
        "expected_failures": ["Vegetation", "Soil_Organic", "Biodiversity"],
    },
    
    # گردباد کاترینا
    "KATRINA_HURRICANE": {
        "name": "گردباد کاترینا",
        "description": "گردباد دسته ۵ با بادهای ۲۸۰ km/h",
        "extreme_type": "HURRICANE_EXTREME",
        "conditions": {
            "temp": 28.0,
            "rain": 800,
            "wind": 280,
            "humidity": 100,
            "storm_surge": 8,
        },
        "expected_failures": ["All_Structures", "Trees", "Infrastructure"],
    },
    
    # سیل پاکستان ۲۰۲۲
    "PAKISTAN_FLOODS_2022": {
        "name": "سیل پاکستان (۲۰۲۲)",
        "description": "یک سوم کشور زیر آب",
        "extreme_type": "FLOOD_EXTREME",
        "conditions": {
            "temp": 32.0,
            "rain": 3000,
            "humidity": 90,
            "flood_depth": 5,
            "flood_duration_days": 90,
        },
        "expected_failures": ["Crops", "Livestock", "Infrastructure"],
    },
    
    # شرایط آزمایشگاهی: همه استرس‌ها همزمان
    "MULTI_STRESS_HELL": {
        "name": "ترکیب جهنمی استرس‌ها",
        "description": "همه استرس‌ها همزمان - تست حداکثر پایداری",
        "extreme_type": "COMBINED_EXTREME",
        "conditions": {
            "temp": 45.0,
            "rain": 10,
            "humidity": 5,
            "ec": 50.0,
            "ph": 9.5,
            "soc": 0.01,
            "awc": 5,
            "wind": 80,
            "uv_index": 15,
        },
        "expected_failures": ["Everything"],
    },
}


# ============================================================
# بخش ۲: تست مقادیر حدی و پرت (Edge Cases & Outliers)
# ============================================================

EDGE_CASE_TESTS = [
    # مقادیر منفی غیرمنطقی
    {"name": "دمای منفی غیرممکن", "key": "temp", "value": -500, "expected": "ERROR"},
    {"name": "بارش منفی", "key": "rain", "value": -100, "expected": "ERROR"},
    {"name": "شوری منفی", "key": "ec", "value": -5, "expected": "ERROR"},
    {"name": "pH منفی", "key": "ph", "value": -1, "expected": "ERROR"},
    {"name": "SOC منفی", "key": "soc", "value": -0.5, "expected": "ERROR"},
    
    # مقادیر بسیار بزرگ
    {"name": "دمای بسیار بالا", "key": "temp", "value": 1000, "expected": "ERROR"},
    {"name": "بارش بسیار زیاد", "key": "rain", "value": 100000, "expected": "ERROR"},
    {"name": "شوری بسیار بالا", "key": "ec", "value": 5000, "expected": "CRITICAL"},
    {"name": "شیب غیرممکن", "key": "slope", "value": 200, "expected": "ERROR"},
    
    # مقادیر صفر خاص
    {"name": "بارش صفر (خشکسالی کامل)", "key": "rain", "value": 0, "expected": "STRESS"},
    {"name": "SOC صفر", "key": "soc", "value": 0, "expected": "CRITICAL"},
    {"name": "ظرفیت آب صفر", "key": "awc", "value": 0, "expected": "CRITICAL"},
    
    # مقادیر تهی و NaN
    {"name": "مقدار None", "key": "temp", "value": None, "expected": "ERROR"},
    {"name": "مقدار NaN", "key": "temp", "value": float('nan'), "expected": "ERROR"},
    {"name": "مقدار Infinity", "key": "rain", "value": float('inf'), "expected": "ERROR"},
    
    # مقادیر اعشاری بسیار کوچک
    {"name": "بارش نزدیک صفر", "key": "rain", "value": 0.00001, "expected": "STRESS"},
    {"name": "شوری نزدیک صفر", "key": "ec", "value": 0.00001, "expected": "OK"},
    
    # مقادیر pH غیرعادی
    {"name": "pH اسید باتری", "key": "ph", "value": 0.5, "expected": "CRITICAL"},
    {"name": "pH سود سوزآور", "key": "ph", "value": 14, "expected": "CRITICAL"},
    
    # مقادیر ترکیبی پرت
    {"name": "دمای بالا + بارش صفر + شوری بالا", 
     "combo": {"temp": 50, "rain": 0, "ec": 100}, "expected": "CRITICAL"},
    {"name": "دمای زیر صفر + بارش زیاد", 
     "combo": {"temp": -30, "rain": 2000}, "expected": "CRITICAL"},
]


# ============================================================
# بخش ۳: کلاس تست سختگیرانه
# ============================================================

class HardcoreStressTester:
    """تستر سختگیرانه هیدروما"""
    
    def __init__(self, knowledge_base: dict):
        self.kb = knowledge_base
        self.findings = []
        self.stats = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "critical": 0,
            "warning": 0,
            "info": 0,
        }
    
    def add_finding(self, category: str, test_name: str, severity: str,
                    message: str, details: Dict = None):
        """افزودن یک یافته"""
        finding = {
            "category": category,
            "test": test_name,
            "severity": severity,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.findings.append(finding)
        self.stats["total_tests"] += 1
        
        if severity == "CRITICAL":
            self.stats["critical"] += 1
            self.stats["failed"] += 1
        elif severity == "WARNING":
            self.stats["warning"] += 1
        elif severity == "FAILED":
            self.stats["failed"] += 1
        elif severity == "INFO":
            self.stats["info"] += 1
        else:
            self.stats["passed"] += 1
    
    def test_realistic_ranges(self):
        """تست ۱: بررسی محدوده‌های واقع‌بینانه فیزیکی"""
        print("\n🔍 تست ۱: محدوده‌های واقع‌بینانه فیزیکی ...")
        
        physical_limits = {
            "temp": {"min": -93.2, "max": 56.7, "unit": "°C"},  # رکوردهای جهانی
            "rain": {"min": 0, "max": 12000, "unit": "mm/yr"},
            "ec": {"min": 0, "max": 400, "unit": "dS/m"},
            "ph": {"min": 0, "max": 14, "unit": "-"},
            "soc": {"min": 0, "max": 100, "unit": "%"},
            "awc": {"min": 0, "max": 500, "unit": "mm/m"},
            "slope": {"min": 0, "max": 90, "unit": "°"},
        }
        
        for key, specialty in self.kb.items():
            for indicator in specialty.get("indicators", []):
                threshold = indicator.get("threshold", {})
                if not threshold:
                    continue
                
                min_val = threshold.get("min")
                max_val = threshold.get("max")
                
                # بررسی منطقی بودن min < max
                if min_val is not None and max_val is not None:
                    if min_val >= max_val:
                        self.add_finding(
                            "RANGE_LOGIC",
                            f"{key}.{indicator.get('name', 'unknown')}",
                            "CRITICAL",
                            f"min ({min_val}) >= max ({max_val})",
                            {"indicator": indicator.get("name")},
                        )
                    elif min_val == max_val:
                        self.add_finding(
                            "RANGE_LOGIC",
                            f"{key}.{indicator.get('name', 'unknown')}",
                            "WARNING",
                            f"min == max ({min_val})",
                        )
                
                # بررسی مقادیر غیرمنطقی
                if min_val is not None and min_val < -1000:
                    self.add_finding(
                        "RANGE_PHYSICAL",
                        f"{key}.{indicator.get('name', 'unknown')}",
                        "WARNING",
                        f"مقدار حداقل غیرمنطقی: {min_val}",
                    )
                
                if max_val is not None and max_val > 100000:
                    self.add_finding(
                        "RANGE_PHYSICAL",
                        f"{key}.{indicator.get('name', 'unknown')}",
                        "WARNING",
                        f"مقدار حداکثر غیرمنطقی: {max_val}",
                    )
    
    def test_formula_consistency(self):
        """تست ۲: سازگاری فرمول‌ها با محدودیت‌ها"""
        print("\n🔍 تست ۲: سازگاری فرمول‌ها ...")
        
        for key, specialty in self.kb.items():
            for indicator in specialty.get("indicators", []):
                formula = indicator.get("formula", "")
                threshold = indicator.get("threshold", {})
                
                if not formula:
                    self.add_finding(
                        "FORMULA_MISSING",
                        f"{key}.{indicator.get('name', 'unknown')}",
                        "WARNING",
                        "فرمول تعریف نشده",
                    )
                    continue
                
                # بررسی وجود نمادهای متضاد
                if "min" in threshold and "optimal" in threshold:
                    if threshold["min"] == threshold["optimal"]:
                        self.add_finding(
                            "FORMULA_THRESHOLD",
                            f"{key}.{indicator.get('name')}",
                            "WARNING",
                            "min == optimal (محدوده بهینه صفر است)",
                        )
                
                # بررسی فرمول‌های پیچیده بدون ورودی
                if "(" in formula and ")" in formula:
                    # بررسی وجود پارامترها
                    pass
    
    def test_extreme_scenarios(self):
        """تست ۳: سناریوهای بحرانی جهانی"""
        print("\n🔍 تست ۳: سناریوهای بحرانی جهانی ...")
        
        for scenario_id, scenario in EXTREME_GLOBAL_SCENARIOS.items():
            conditions = scenario["conditions"]
            
            # بررسی دماهای غیرعادی
            temp = conditions.get("temp")
            if temp is not None:
                if temp > 60:
                    self.add_finding(
                        "EXTREME_SCENARIO",
                        scenario["name"],
                        "CRITICAL",
                        f"دمای بحرانی: {temp}°C (بالاتر از رکورد جهانی)",
                        {"scenario_id": scenario_id, "conditions": conditions},
                    )
                elif temp < -90:
                    self.add_finding(
                        "EXTREME_SCENARIO",
                        scenario["name"],
                        "CRITICAL",
                        f"دمای بحرانی: {temp}°C (زیر رکورد جهانی)",
                        {"scenario_id": scenario_id},
                    )
            
            # بررسی شوری بحرانی
            ec = conditions.get("ec")
            if ec is not None and ec > 50:
                self.add_finding(
                    "EXTREME_SCENARIO",
                    scenario["name"],
                    "CRITICAL",
                    f"شوری بحرانی: {ec} dS/m",
                    {"scenario_id": scenario_id},
                )
            
            # بررسی pH غیرمنطقی
            ph = conditions.get("ph")
            if ph is not None and (ph < 2 or ph > 12):
                self.add_finding(
                    "EXTREME_SCENARIO",
                    scenario["name"],
                    "CRITICAL",
                    f"pH غیرعادی: {ph}",
                    {"scenario_id": scenario_id},
                )
    
    def test_edge_cases(self):
        """تست ۴: مقادیر حدی و پرت"""
        print("\n🔍 تست ۴: مقادیر حدی و پرت ...")
        
        for test in EDGE_CASE_TESTS:
            test_name = test["name"]
            
            # تست مقادیر غیرمنطقی که باید خطا بدهند
            if test.get("expected") == "ERROR":
                value = test.get("value")
                
                # بررسی None و NaN
                if value is None:
                    self.add_finding(
                        "EDGE_CASE",
                        test_name,
                        "CRITICAL",
                        f"سیستم باید با None مقابله کند",
                        {"key": test.get("key"), "value": "None"},
                    )
                elif isinstance(value, float) and math.isnan(value):
                    self.add_finding(
                        "EDGE_CASE",
                        test_name,
                        "CRITICAL",
                        f"سیستم باید با NaN مقابله کند",
                        {"key": test.get("key"), "value": "NaN"},
                    )
                elif isinstance(value, float) and math.isinf(value):
                    self.add_finding(
                        "EDGE_CASE",
                        test_name,
                        "CRITICAL",
                        f"سیستم باید با Infinity مقابله کند",
                        {"key": test.get("key"), "value": "Infinity"},
                    )
                elif test.get("value") is not None:
                    # مقادیر منفی
                    if isinstance(value, (int, float)) and value < 0 and test.get("key") in ["rain", "ec", "soc", "awc"]:
                        self.add_finding(
                            "EDGE_CASE",
                            test_name,
                            "WARNING",
                            f"مقدار منفی برای فیلد غیرمنفی: {value}",
                            {"key": test.get("key"), "value": value},
                        )
    
    def test_multi_stress(self):
        """تست ۵: استرس‌های چندگانه"""
        print("\n🔍 تست ۵: استرس‌های چندگانه ...")
        
        # ترکیب چند استرس همزمان
        multi_stress_cases = [
            {
                "name": "خشکسالی + گرما + شوری",
                "conditions": {"temp": 45, "rain": 5, "ec": 30},
                "expected": "CRITICAL",
            },
            {
                "name": "سیل + شیب تند",
                "conditions": {"rain": 5000, "slope": 60},
                "expected": "CRITICAL",
            },
            {
                "name": "یخبندان + باد شدید",
                "conditions": {"temp": -40, "wind": 100},
                "expected": "CRITICAL",
            },
            {
                "name": "شوری بالا + pH بالا",
                "conditions": {"ec": 50, "ph": 11},
                "expected": "CRITICAL",
            },
        ]
        
        for case in multi_stress_cases:
            self.add_finding(
                "MULTI_STRESS",
                case["name"],
                "CRITICAL",
                f"ترکیب استرس‌های بحرانی: {case['conditions']}",
                {"conditions": case["conditions"]},
            )
    
    def test_data_quality(self):
        """تست ۶: کیفیت داده‌های تزریق‌شده"""
        print("\n🔍 تست ۶: کیفیت داده‌های تزریق‌شده ...")
        
        # بررسی داده‌های اقلیمی ایران
        if DATA_FILE.exists():
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            regions = data.get("climate_iran", {}).get("regions", {})
            
            for region_name, region_data in regions.items():
                temp = region_data.get("temp", 0)
                rain = region_data.get("rain", 0)
                
                # بررسی همخوانی دما و بارش با اقلیم کوپن
                koppen = region_data.get("koppen", "")
                
                if koppen.startswith("B"):  # خشک
                    if rain > 500:
                        self.add_finding(
                            "DATA_QUALITY",
                            f"منطقه {region_name}",
                            "WARNING",
                            f"بارش بالا برای اقلیم خشک: {rain}mm",
                        )
                    if temp < 5 and koppen == "BWh":
                        self.add_finding(
                            "DATA_QUALITY",
                            f"منطقه {region_name}",
                            "WARNING",
                            f"دمای پایین برای بیابان گرم: {temp}°C",
                        )
    
    def test_formula_evaluability(self):
        """تست ۷: قابلیت ارزیابی فرمول‌ها"""
        print("\n🔍 تست ۷: قابلیت ارزیابی فرمول‌ها ...")
        
        non_evaluable_patterns = [
            ("f(", "تابع نامشخص f()"),
            ("Σ(", "سیگما - نیاز به داده آرایه‌ای"),
            ("∫", "انتگرال - نیاز به پیاده‌سازی عددی"),
            ("ln(", "لگاریتم طبیعی"),
            ("exp(", "تابع نمایی"),
            ("σ_", "انحراف معیار"),
            ("μ_", "میانگین"),
            ("arctan(", "تابع مثلثاتی"),
        ]
        
        for key, specialty in self.kb.items():
            for indicator in specialty.get("indicators", []):
                formula = indicator.get("formula", "")
                
                for pattern, description in non_evaluable_patterns:
                    if pattern in formula:
                        self.add_finding(
                            "FORMULA_EVALUABILITY",
                            f"{key}.{indicator.get('name', 'unknown')}",
                            "WARNING",
                            f"فرمول حاوی {description}: {formula[:60]}",
                            {"pattern": pattern},
                        )
                        break
    
    def test_specialty_completeness(self):
        """تست ۸: کامل بودن گرایش‌ها"""
        print("\n🔍 تست ۸: کامل بودن گرایش‌ها ...")
        
        for key, specialty in self.kb.items():
            # بررسی وجود فیلدهای ضروری
            required_fields = ["name", "indicators", "formulas", "hydroma_role"]
            
            for field in required_fields:
                if field not in specialty:
                    self.add_finding(
                        "COMPLETENESS",
                        key,
                        "CRITICAL",
                        f"فیلد ضروری '{field}' موجود نیست",
                    )
            
            # بررسی وجود شاخص‌ها
            indicators = specialty.get("indicators", [])
            if len(indicators) < 1:
                self.add_finding(
                    "COMPLETENESS",
                    key,
                    "WARNING",
                    f"گرایش بدون شاخص",
                )
            
            # بررسی داشتن default_value برای هر شاخص
            for ind in indicators:
                if "default_value" not in ind:
                    self.add_finding(
                        "COMPLETENESS",
                        f"{key}.{ind.get('name', 'unknown')}",
                        "WARNING",
                        f"مقدار پیش‌فرض ندارد - در شرایط بحرانی محاسبه صفر می‌شود",
                    )
    
    def run_all_tests(self):
        """اجرای همه تست‌ها"""
        print("=" * 70)
        print("تست سختگیرانه هیدروما (Hardcore Stress Test)")
        print("=" * 70)
        
        self.test_realistic_ranges()
        self.test_formula_consistency()
        self.test_extreme_scenarios()
        self.test_edge_cases()
        self.test_multi_stress()
        self.test_data_quality()
        self.test_formula_evaluability()
        self.test_specialty_completeness()
        
        return self.findings, self.stats


# ============================================================
# بخش ۴: اجرای اصلی
# ============================================================

def main():
    print("=" * 70)
    print("🔥 تست سختگیرانه هیدروما")
    print("محیط تست: شرایط بحرانی، کم‌نظیر و غیرنرمال")
    print("=" * 70)
    
    # بارگذاری پایگاه دانش
    if not KB_FILE.exists():
        print(f"❌ پایگاه دانش یافت نشد: {KB_FILE}")
        return
    
    kb = json.loads(KB_FILE.read_text(encoding="utf-8"))
    print(f"\n✅ {len(kb)} گرایش بارگذاری شد")
    
    # ایجاد تستر و اجرای تست‌ها
    tester = HardcoreStressTester(kb)
    findings, stats = tester.run_all_tests()
    
    # ذخیره گزارش
    report = {
        "generated_at": datetime.now().isoformat(),
        "test_type": "Hardcore Stress Test",
        "statistics": stats,
        "findings_count": len(findings),
        "critical_findings": [f for f in findings if f["severity"] == "CRITICAL"],
        "warnings": [f for f in findings if f["severity"] == "WARNING"],
        "all_findings": findings,
        "scenarios_tested": list(EXTREME_GLOBAL_SCENARIOS.keys()),
    }
    
    REPORT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # خلاصه نهایی
    print("\n" + "=" * 70)
    print("📊 نتایج تست سختگیرانه")
    print("=" * 70)
    print(f"   🧪 تعداد تست‌ها: {stats['total_tests']}")
    print(f"   ✅ موفق: {stats['passed']}")
    print(f"   ❌ ناموفق: {stats['failed']}")
    print(f"   🔴 بحرانی: {stats['critical']}")
    print(f"   ⚠️ هشدار: {stats['warning']}")
    print(f"   ℹ️ اطلاعات: {stats['info']}")
    print("=" * 70)
    
    # نمایش یافته‌های بحرانی
    critical_findings = [f for f in findings if f["severity"] == "CRITICAL"]
    if critical_findings:
        print(f"\n🔴 یافته‌های بحرانی (باید رفع شوند):")
        print("-" * 70)
        for i, finding in enumerate(critical_findings[:15], 1):
            print(f"   {i}. [{finding['category']}] {finding['test']}")
            print(f"      → {finding['message']}")
    
    warnings = [f for f in findings if f["severity"] == "WARNING"]
    if warnings:
        print(f"\n⚠️ هشدارها ({len(warnings)} مورد):")
        print("-" * 70)
        for i, finding in enumerate(warnings[:10], 1):
            print(f"   {i}. [{finding['category']}] {finding['test']}")
            print(f"      → {finding['message']}")
    
    print("\n" + "=" * 70)
    print(f"📄 گزارش کامل: {REPORT_FILE}")
    print("=" * 70)
    print("\n🎯 شعار: تن زمین خسته است")
    print("   ما در خدمت بشر و زمین هستیم با پیوند طبیعت و بشر")
    print("=" * 70)


if __name__ == "__main__":
    main()