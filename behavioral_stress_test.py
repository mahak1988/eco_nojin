#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
تست رفتاری سختگیرانه هیدروما (Behavioral Stress Test)
پارادایم جدید: به جای گزارش شرایط بحرانی، رفتار مدیریت را تست می‌کند
============================================================================
"""
import json
import math
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

REPORT_FILE = ROOT / "docs" / "hydroma" / "behavioral_stress_report.json"


class BehavioralStressTester:
    """تستر رفتاری - بررسی مدیریت شرایط بحرانی"""
    
    def __init__(self):
        self.results = []
        self.stats = {
            "total": 0, "passed": 0, "failed": 0,
            "critical": 0, "warning": 0,
        }
    
    def assert_test(self, category, name, condition, message_pass, message_fail,
                    severity="critical"):
        """ثبت نتیجه یک تست"""
        self.stats["total"] += 1
        passed = bool(condition)
        
        if passed:
            self.stats["passed"] += 1
            msg = message_pass
            icon = "✅"
        else:
            self.stats["failed"] += 1
            if severity == "critical":
                self.stats["critical"] += 1
            else:
                self.stats["warning"] += 1
            msg = message_fail
            icon = "❌"
        
        self.results.append({
            "category": category,
            "test": name,
            "passed": passed,
            "message": msg,
            "severity": severity,
        })
        
        print(f"   {icon} [{category}] {name}")
        print(f"      → {msg}")
        
        return passed
    
    # ============================================================
    # تست ۱: اعتبارسنجی ورودی‌ها
    # ============================================================
    def test_input_validation(self):
        print("\n🔍 تست ۱: اعتبارسنجی ورودی‌ها (رفع ۳ یافته بحرانی) ...")
        
        try:
            from engine.hydroma.climate_adaptation.input_validator import (
                sanitize, sanitize_dict, validate_physical_consistency
            )
            validator_loaded = True
        except ImportError as e:
            validator_loaded = False
            self.assert_test(
                "INPUT_VALIDATION", "بارگذاری ماژول",
                False, "", f"ماژول بارگذاری نشد: {e}"
            )
            return
        
        # تست ۱.۱: مدیریت None
        result = sanitize(None, "temp", default=15.0)
        self.assert_test(
            "INPUT_VALIDATION", "مدیریت None",
            result == 15.0,
            f"None به مقدار پیش‌فرض تبدیل شد: {result}",
            f"انتظار ۱۵، دریافت {result}"
        )
        
        # تست ۱.۲: مدیریت NaN
        result = sanitize(float('nan'), "temp", default=20.0)
        self.assert_test(
            "INPUT_VALIDATION", "مدیریت NaN",
            result == 20.0,
            f"NaN به مقدار پیش‌فرض تبدیل شد: {result}",
            f"انتظار ۲۰، دریافت {result}"
        )
        
        # تست ۱.۳: مدیریت Infinity
        result = sanitize(float('inf'), "temp", default=25.0)
        self.assert_test(
            "INPUT_VALIDATION", "مدیریت Infinity",
            result == 56.7,  # کران بالا برای دما
            f"Infinity به کران فیزیکی تبدیل شد: {result}",
            f"انتظار ۵۶.۷ (کران دما)، دریافت {result}"
        )
        
        # تست ۱.۴: مدیریت مقادیر منفی
        result = sanitize(-100, "rain", default=0.0)
        self.assert_test(
            "INPUT_VALIDATION", "مدیریت بارش منفی",
            result == 0.0,
            f"بارش منفی به صفر محدود شد: {result}",
            f"انتظار ۰، دریافت {result}"
        )
        
        # تست ۱.۵: مدیریت مقادیر خیلی بزرگ
        result = sanitize(999999, "rain", default=300.0)
        self.assert_test(
            "INPUT_VALIDATION", "مدیریت بارش بسیار بزرگ",
            result == 12000.0,  # کران بالا برای بارش
            f"بارش بزرگ به کران محدود شد: {result}",
            f"انتظار ۱۲۰۰۰، دریافت {result}"
        )
        
        # تست ۱.۶: پاک‌سازی دیکشنری
        dirty = {"temp": None, "rain": float('nan'), "ec": -5, "ph": 15}
        clean = sanitize_dict(dirty, defaults={"temp": 15, "rain": 300, "ec": 1, "ph": 7})
        self.assert_test(
            "INPUT_VALIDATION", "پاک‌سازی دیکشنری",
            clean["temp"] == 15 and clean["ec"] == 0 and clean["ph"] == 14,
            f"دیکشنری کثیف پاک‌سازی شد: {clean}",
            f"پاک‌سازی نادرست: {clean}"
        )
    
    # ============================================================
    # تست ۲: استرس ترکیبی خشکسالی+گرما+شوری
    # ============================================================
    def test_drought_heat_salinity(self):
        print("\n🔍 تست ۲: مدیریت خشکسالی+گرما+شوری ...")
        
        try:
            from engine.hydroma.climate_adaptation.multi_stress_engine import (
                drought_heat_salinity_stress
            )
        except ImportError as e:
            self.assert_test(
                "MULTI_STRESS", "بارگذاری موتور تنش",
                False, "", f"ماژول بارگذاری نشد: {e}"
            )
            return
        
        # تست ۲.۱: شرایط عادی → خروجی ملایم
        result = drought_heat_salinity_stress(temp=25, rain=300, ec=1)
        self.assert_test(
            "MULTI_STRESS", "شرایط عادی → استرس ملایم",
            result["combined_stress"] < 0.25,
            f"شرایط عادی به درستی استرس ملایم داد: {result['combined_stress']}",
            f"انتظار <۰.۲۵، دریافت {result['combined_stress']}"
        )
        
        # تست ۲.۲: شرایط بحرانی → خروجی بحرانی
        result = drought_heat_salinity_stress(temp=45, rain=5, ec=30)
        self.assert_test(
            "MULTI_STRESS", "شرایط بحرانی → استرس بحرانی",
            result["combined_stress"] >= 0.75,
            f"شرایط بحرانی به درستی شناسایی شد: {result['severity']} ({result['combined_stress']})",
            f"انتظار >=۰.۷۵، دریافت {result['combined_stress']}"
        )
        
        # تست ۲.۳: ساختار خروجی معتبر
        required_keys = ["heat_stress", "drought_stress", "salinity_stress",
                         "combined_stress", "amplified_stress", "severity"]
        has_all = all(k in result for k in required_keys)
        self.assert_test(
            "MULTI_STRESS", "ساختار خروجی کامل",
            has_all,
            "تمام فیلدهای لازم موجود است",
            "فیلدهای ناقص"
        )
    
    # ============================================================
    # تست ۳: سیل+شیب
    # ============================================================
    def test_flood_slope(self):
        print("\n🔍 تست ۳: مدیریت سیل+شیب ...")
        
        try:
            from engine.hydroma.climate_adaptation.multi_stress_engine import (
                flood_slope_stress
            )
        except ImportError as e:
            self.assert_test("FLOOD_SLOPE", "بارگذاری", False, "", f"{e}")
            return
        
        # تست ۳.۱: شرایط بحرانی → شناسایی صحیح
        result = flood_slope_stress(rain=5000, slope=60)
        self.assert_test(
            "FLOOD_SLOPE", "سیل+شیب بحرانی → شناسایی صحیح",
            result["combined_stress"] >= 0.5,
            f"سیل+شیب به درستی شناسایی شد: {result['severity']} (ریسک فرسایش: {result['erosion_risk']})",
            f"انتظار >=۰.۵، دریافت {result['combined_stress']}"
        )
        
        # تست ۳.۲: شرایط عادی → ریسک پایین
        result = flood_slope_stress(rain=100, slope=5)
        self.assert_test(
            "FLOOD_SLOPE", "شرایط عادی → ریسک پایین",
            result["combined_stress"] < 0.25,
            f"شرایط عادی به درستی ریسک پایین داد: {result['combined_stress']}",
            f"انتظار <۰.۲۵، دریافت {result['combined_stress']}"
        )
    
    # ============================================================
    # تست ۴: یخبندان+باد
    # ============================================================
    def test_frost_wind(self):
        print("\n🔍 تست ۴: مدیریت یخبندان+باد ...")
        
        try:
            from engine.hydroma.climate_adaptation.multi_stress_engine import (
                frost_wind_stress
            )
        except ImportError as e:
            self.assert_test("FROST_WIND", "بارگذاری", False, "", f"{e}")
            return
        
        # تست ۴.۱: شرایط بحرانی → شناسایی صحیح
        result = frost_wind_stress(temp=-40, wind=100)
        self.assert_test(
            "FROST_WIND", "یخبندان+باد بحرانی → شناسایی صحیح",
            result["effective_frost_stress"] >= 0.75,
            f"یخبندان+باد به درستی شناسایی شد: {result['severity']} (سرمای موثر ×{result['wind_chill_factor']})",
            f"انتظار >=۰.۷۵، دریافت {result['effective_frost_stress']}"
        )
    
    # ============================================================
    # تست ۵: شوری+قلیائیت
    # ============================================================
    def test_salinity_alkalinity(self):
        print("\n🔍 تست ۵: مدیریت شوری+قلیائیت ...")
        
        try:
            from engine.hydroma.climate_adaptation.multi_stress_engine import (
                salinity_ph_stress
            )
        except ImportError as e:
            self.assert_test("SALINITY_PH", "بارگذاری", False, "", f"{e}")
            return
        
        # تست ۵.۱: شرایط بحرانی → شناسایی سدیمی شدن
        result = salinity_ph_stress(ec=50, ph=11)
        self.assert_test(
            "SALINITY_PH", "شوری+قلیائیت → ریسک سدیمی شدن",
            result["sodification_risk"] > 0.5,
            f"ریسک سدیمی شدن شناسایی شد: {result['sodification_risk']} ({result['recommendation']})",
            f"انتظار >۰.۵، دریافت {result['sodification_risk']}"
        )
        
        # تست ۵.۲: شوری فوق بحرانی (ارومیه) → مدیریت بدون کرش
        result = salinity_ph_stress(ec=300, ph=9.2)
        self.assert_test(
            "SALINITY_PH", "شوری ارومیه (۳۰۰) → مدیریت بدون کرش",
            result["salinity_stress"] == 1.0 and result["severity"] == "بحرانی",
            f"شوری ارومیه به درستی مدیریت شد: {result['severity']}",
            f"مدیریت ناموفق: {result}"
        )
    
    # ============================================================
    # تست ۶: مقادیر پیش‌فرض در پایگاه دانش
    # ============================================================
    def test_knowledge_base_defaults(self):
        print("\n🔍 تست ۶: مقادیر پیش‌فرض در پایگاه دانش ...")
        
        kb_file = ROOT / "docs" / "hydroma" / "knowledge_base_detailed.json"
        if not kb_file.exists():
            self.assert_test("KB_DEFAULTS", "پایگاه دانش", False, "", "یافت نشد")
            return
        
        kb = json.loads(kb_file.read_text(encoding="utf-8"))
        
        # شمارش شاخص‌ها با مقدار پیش‌فرض
        total = 0
        with_default = 0
        for spec_id, spec in kb.items():
            for ind in spec.get("indicators", []):
                total += 1
                if "default_value" in ind:
                    with_default += 1
        
        coverage = with_default / total if total > 0 else 0
        self.assert_test(
            "KB_DEFAULTS", "پوشش مقادیر پیش‌فرض",
            coverage >= 0.9,
            f"{with_default}/{total} شاخص مقدار پیش‌فرض دارند ({coverage*100:.0f}%)",
            f"پوشش ناکافی: {coverage*100:.0f}%"
        )
        
        # بررسی فرمول‌های تبدیل‌شده
        abstract_count = 0
        for spec_id, spec in kb.items():
            for ind in spec.get("indicators", []):
                formula = ind.get("formula", "")
                if formula.startswith("f(") or "= f(" in formula:
                    abstract_count += 1
        
        self.assert_test(
            "KB_DEFAULTS", "حذف فرمول‌های انتزاعی",
            abstract_count <= 5,
            f"فقط {abstract_count} فرمول انتزاعی باقی مانده",
            f"{abstract_count} فرمول انتزاعی باقی مانده (باید <=۵ باشد)"
        )
    
    # ============================================================
    # اجرای همه تست‌ها
    # ============================================================
    def run_all(self):
        print("=" * 70)
        print("🧪 تست رفتاری سختگیرانه هیدروما")
        print("پارادایم جدید: تست رفتار مدیریت شرایط بحرانی")
        print("=" * 70)
        
        self.test_input_validation()
        self.test_drought_heat_salinity()
        self.test_flood_slope()
        self.test_frost_wind()
        self.test_salinity_alkalinity()
        self.test_knowledge_base_defaults()
        
        return self.results, self.stats


def main():
    tester = BehavioralStressTester()
    results, stats = tester.run_all()
    
    # ذخیره گزارش
    report = {
        "generated_at": datetime.now().isoformat(),
        "test_type": "Behavioral Stress Test (New Paradigm)",
        "paradigm": "تست رفتار مدیریت شرایط بحرانی به جای گزارش شرایط",
        "statistics": stats,
        "pass_rate_percent": round(stats["passed"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0,
        "results": results,
    }
    
    REPORT_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    # خلاصه نهایی
    print("\n" + "=" * 70)
    print("📊 نتایج تست رفتاری")
    print("=" * 70)
    print(f"   🧪 تعداد تست‌ها: {stats['total']}")
    print(f"   ✅ موفق: {stats['passed']} ({report['pass_rate_percent']}%)")
    print(f"   ❌ ناموفق: {stats['failed']}")
    print(f"   🔴 بحرانی: {stats['critical']}")
    print("=" * 70)
    print(f"📄 گزارش: {REPORT_FILE}")
    print("=" * 70)
    
    if report["pass_rate_percent"] >= 90:
        print("🎉 سیستم آماده بنچمارک رسمی است")
    else:
        print("⚠️ نیاز به بهبود بیشتر")
    print("=" * 70)


if __name__ == "__main__":
    main()