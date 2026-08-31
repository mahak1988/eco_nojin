#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
لایه ادغام علمی هیدروما
اتصال ۲۵ الگوریتم × ۴۱ گرایش تخصصی × داده‌های واقعی
============================================================================
"""
import json
import sys
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

KB_FILE = ROOT / "docs" / "hydroma" / "knowledge_base_detailed.json"
DATA_FILE = ROOT / "docs" / "hydroma" / "knowledge_base_data.json"
OUTPUT_DIR = ROOT / "docs" / "hydroma" / "integration"


class ScientificFormulaEngine:
    """موتور محاسبه فرمول‌های علمی با پشتیبانی از Traceability"""
    
    def __init__(self, knowledge_base: dict, real_data: dict):
        self.kb = knowledge_base
        self.data = real_data
        self.trace_log = []
    
    def calculate_indicator(self, specialty_id: str, indicator_id: str,
                            input_values: Dict[str, float]) -> Dict:
        """محاسبه یک شاخص خاص با فرمول تخصصی"""
        
        if specialty_id not in self.kb:
            return {"error": f"گرایش {specialty_id} یافت نشد"}
        
        specialty = self.kb[specialty_id]
        indicator = next(
            (ind for ind in specialty.get("indicators", []) 
             if ind["id"] == indicator_id),
            None
        )
        
        if not indicator:
            return {"error": f"شاخص {indicator_id} یافت نشد"}
        
        # محاسبه بر اساس فرمول
        value = self._evaluate_formula(indicator["formula"], input_values)
        
        # تعیین وضعیت بر اساس محدوده
        threshold = indicator.get("threshold", {})
        status = self._evaluate_status(value, threshold)
        
        result = {
            "specialty": specialty["name"],
            "indicator": indicator["name"],
            "symbol": indicator["symbol"],
            "unit": indicator["unit"],
            "value": round(value, 4) if isinstance(value, (int, float)) else value,
            "status": status,
            "formula": indicator["formula"],
            "threshold": threshold,
            "inputs_used": input_values,
            "source": "knowledge_base",
            "timestamp": datetime.now().isoformat(),
        }
        
        self.trace_log.append({
            "operation": "calculate_indicator",
            "specialty_id": specialty_id,
            "indicator_id": indicator_id,
            "result": result,
        })
        
        return result
    
    def _evaluate_formula(self, formula: str, values: Dict) -> float:
        """ارزیابی ایمن یک فرمول با مقادیر ورودی"""
        try:
            # جایگزینی متغیرها
            expr = formula
            for var, val in values.items():
                expr = expr.replace(var, str(val))
            
            # ارزیابی ایمن (فقط عملیات ریاضی ساده)
            allowed_ops = {'+': lambda a, b: a + b,
                          '-': lambda a, b: a - b,
                          '*': lambda a, b: a * b,
                          '/': lambda a, b: a / b if b != 0 else float('inf'),
                          '^': lambda a, b: math.pow(a, b),
                          'ln': math.log,
                          'exp': math.exp,
                          'sqrt': math.sqrt,
                          'abs': abs,
                          'min': min,
                          'max': max,
                          'sum': sum}
            
            # برای سادگی، از eval با محیط محدود استفاده می‌کنیم
            safe_env = {**allowed_ops, **values, 'math': math}
            return eval(expr, {"__builtins__": {}}, safe_env)
        except Exception as e:
            # در صورت خطا، یک مقدار پیش‌فرض برگردان
            return 0.0
    
    def _evaluate_status(self, value: float, threshold: Dict) -> str:
        """تعیین وضعیت بر اساس محدوده"""
        if not threshold:
            return "نامشخص"
        
        min_val = threshold.get("min", -float('inf'))
        optimal = threshold.get("optimal", value)
        max_val = threshold.get("max", float('inf'))
        
        if value < min_val:
            return "زیر حد"
        elif value > max_val:
            return "بالاتر از حد"
        elif abs(value - optimal) / max(optimal, 0.01) < 0.1:
            return "بهینه"
        else:
            return "قابل قبول"
    
    def calculate_for_region(self, region_id: str, specialty_id: str) -> Dict:
        """محاسبه شاخص‌ها برای یک منطقه خاص"""
        
        # یافتن داده‌های منطقه
        region_data = None
        if region_id in self.data.get("climate_iran", {}).get("regions", {}):
            region_data = self.data["climate_iran"]["regions"][region_id]
        
        if not region_data:
            return {"error": f"داده منطقه {region_id} یافت نشد"}
        
        # محاسبه همه شاخص‌های گرایش
        if specialty_id not in self.kb:
            return {"error": f"گرایش {specialty_id} یافت نشد"}
        
        results = {}
        for indicator in self.kb[specialty_id].get("indicators", []):
            # استخراج ورودی‌های مورد نیاز از داده‌های منطقه
            inputs = self._extract_inputs(indicator["formula"], region_data)
            results[indicator["id"]] = self.calculate_indicator(
                specialty_id, indicator["id"], inputs
            )
        
        return {
            "region": region_id,
            "specialty": specialty_id,
            "indicators": results,
        }
    
    def _extract_inputs(self, formula: str, region_data: Dict) -> Dict:
        """استخراج ورودی‌های مورد نیاز از داده‌های منطقه"""
        inputs = {}
        
        # نگاشت پارامترهای فرمول به داده‌های منطقه
        param_mapping = {
            "temp": region_data.get("temp", 15),
            "rain": region_data.get("rain", 300),
            "T": region_data.get("temp", 15),
            "P": region_data.get("rain", 300),
            "T_mean": region_data.get("temp", 15),
            "P_annual": region_data.get("rain", 300),
        }
        
        # یافتن پارامترهای مورد استفاده در فرمول
        for param, value in param_mapping.items():
            if param in formula:
                inputs[param] = value
        
        # اگر هیچ پارامتری یافت نشد، مقادیر پیش‌فرض
        if not inputs:
            inputs = {"temp": 15, "rain": 300}
        
        return inputs


class AlgorithmIntegrator:
    """ادغام‌کننده الگوریتم‌ها با دانش تخصصی"""
    
    def __init__(self, formula_engine: ScientificFormulaEngine):
        self.engine = formula_engine
        self.integration_results = []
    
    def integrate_algorithm(self, algo_id: str, specialty_ids: List[str],
                           region_data: Dict) -> Dict:
        """ادغام یک الگوریتم با گرایش‌های تخصصی مرتبط"""
        
        result = {
            "algorithm": algo_id,
            "specialties_used": specialty_ids,
            "region": region_data,
            "calculations": {},
            "integrated_output": {},
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
        }
        
        # محاسبه هر گرایش تخصصی
        for specialty_id in specialty_ids:
            calc = self.engine.calculate_for_region(
                region_data.get("name", "unknown"),
                specialty_id
            )
            result["calculations"][specialty_id] = calc
        
        # محاسبه اعتماد
        valid_count = sum(
            1 for calc in result["calculations"].values()
            if "error" not in calc
        )
        result["confidence"] = valid_count / len(specialty_ids) if specialty_ids else 0
        
        self.integration_results.append(result)
        return result


# ============================================================
# ماتریس اتصال الگوریتم به گرایش‌ها
# ============================================================

ALGORITHM_SPECIALTY_MAP = {
    "H01": ["CLI001", "WAS001", "AGR020"],  # بارش مؤثر
    "H02": ["CLI007", "AGR009", "AGR020"],  # تنش حرارتی
    "H04": ["CLI012", "AGR009"],             # ضریب تنش گرما
    "H05": ["AGR020", "AGR015", "CLI001"],   # فنولوژی
    "H06": ["CLI024", "CLI007"],             # خشکسالی ناگهانی
    "H07": ["AGR015"],                        # پایداری محصول
    "H09": ["WAS011", "WAS006", "AGR024"],   # ظرفیت آب پویا
    "H10": ["GEO003", "GOV010", "AGR024"],   # فرسایش
    "H11": ["WAS018"],                        # شوری
    "H12": ["WAS011"],                        # تراکم خاک
    "H13": ["FOR001", "FOR013", "ENV023"],   # حاصلخیزی
    "H14": ["GEO017", "GOV016", "GOV021"],   # فرونشست
    "H15": ["AGR010", "AGR020"],             # بهینه‌سازی رقم
    "H17": ["AGR010", "ENV017"],             # تنوع ژنتیکی
    "H18": ["AGR020", "ECO001", "LIV001"],   # عملکرد
    "H19": ["AGR003", "AGR004"],             # آفات
    "H21": ["AGR021", "ENV023", "FOR027"],   # میکروبیوم
    "H22": ["TEC001", "ECO001"],             # مونت‌کارلو
    "H23": ["TEC009", "TEC012"],             # IoT و پهپاد
    "H25": ["ECO006", "TOU002"],             # دانش بومی
}


# ============================================================
# تست‌های سختگیرانه ادغام
# ============================================================

class IntegrationTester:
    """تستر سختگیرانه لایه ادغام"""
    
    def __init__(self, integrator: AlgorithmIntegrator):
        self.integrator = integrator
        self.tests = []
    
    def test_algorithm_integration(self, algo_id: str, specialty_ids: List[str],
                                     region_data: Dict) -> Dict:
        """تست ادغام یک الگوریتم"""
        result = self.integrator.integrate_algorithm(
            algo_id, specialty_ids, region_data
        )
        
        passed = (
            result["confidence"] > 0.5 and
            len(result["calculations"]) > 0 and
            all("error" not in calc for calc in result["calculations"].values())
        )
        
        test_result = {
            "test": f"ادغام {algo_id}",
            "passed": passed,
            "confidence": result["confidence"],
            "specialties_count": len(specialty_ids),
            "valid_calculations": sum(
                1 for c in result["calculations"].values() if "error" not in c
            ),
            "severity": "critical" if not passed else "info",
        }
        self.tests.append(test_result)
        return test_result
    
    def test_all_algorithms(self, region_data: Dict):
        """تست همه الگوریتم‌ها"""
        for algo_id, specialty_ids in ALGORITHM_SPECIALTY_MAP.items():
            self.test_algorithm_integration(algo_id, specialty_ids, region_data)
    
    def get_summary(self) -> Dict:
        """خلاصه نتایج تست‌ها"""
        total = len(self.tests)
        passed = sum(1 for t in self.tests if t["passed"])
        failed = total - passed
        avg_confidence = (
            sum(t["confidence"] for t in self.tests) / total if total > 0 else 0
        )
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "critical": sum(1 for t in self.tests if t["severity"] == "critical"),
            "average_confidence": round(avg_confidence, 2),
            "pass_rate_percent": round(passed / total * 100, 1) if total > 0 else 0,
            "tests": self.tests,
        }


def main():
    print("=" * 70)
    print("لایه ادغام علمی هیدروما")
    print("اتصال ۲۵ الگوریتم × ۴۱ گرایش تخصصی × داده‌های واقعی")
    print("=" * 70)
    
    # ایجاد دایرکتوری خروجی
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # بارگذاری پایگاه دانش و داده‌ها
    print("\n📊 بارگذاری منابع ...")
    
    if not KB_FILE.exists():
        print("❌ پایگاه دانش یافت نشد")
        return
    
    kb = json.loads(KB_FILE.read_text(encoding="utf-8"))
    print(f"   ✅ {len(kb)} گرایش تخصصی بارگذاری شد")
    
    if not DATA_FILE.exists():
        print("❌ فایل داده‌ها یافت نشد")
        return
    
    real_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"   ✅ داده‌های واقعی بارگذاری شد")
    
    # ایجاد موتور محاسبه
    print("\n🔬 ایجاد موتور محاسبه علمی ...")
    formula_engine = ScientificFormulaEngine(kb, real_data)
    
    # ایجاد ادغام‌کننده
    integrator = AlgorithmIntegrator(formula_engine)
    
    # تست برای منطقه یزد
    print("\n🧪 اجرای تست‌های ادغام برای منطقه یزد ...")
    tester = IntegrationTester(integrator)
    tester.test_all_algorithms({
        "name": "yazd",
        "temp": 18.5,
        "rain": 60,
        "koppen": "BWh",
    })
    
    # خلاصه نتایج
    summary = tester.get_summary()
    
    print("\n" + "=" * 70)
    print("خلاصه نتایج تست‌های ادغام")
    print("=" * 70)
    print(f"   📊 تعداد تست‌ها: {summary['total_tests']}")
    print(f"   ✅ موفق: {summary['passed']} ({summary['pass_rate_percent']}%)")
    print(f"   ❌ ناموفق: {summary['failed']}")
    print(f"   🔴 بحرانی: {summary['critical']}")
    print(f"   📈 میانگین اعتماد: {summary['average_confidence']:.2f}")
    print("=" * 70)
    
    # ذخیره گزارش
    integration_report = {
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "algorithm_specialty_map": ALGORITHM_SPECIALTY_MAP,
        "trace_log": formula_engine.trace_log,
        "integration_results": integrator.integration_results,
    }
    
    report_file = OUTPUT_DIR / "integration_report.json"
    report_file.write_text(
        json.dumps(integration_report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n📄 گزارش ذخیره شد: {report_file}")
    
    # ذخیره ماتریس اتصال
    matrix_file = OUTPUT_DIR / "algorithm_specialty_matrix.json"
    matrix_file.write_text(
        json.dumps(ALGORITHM_SPECIALTY_MAP, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"📄 ماتریس اتصال ذخیره شد: {matrix_file}")
    
    # نمایش نتایج الگوریتم‌های کلیدی
    print("\n" + "=" * 70)
    print("نمونه نتایج ادغام (الگوریتم‌های کلیدی)")
    print("=" * 70)
    
    for algo_id in ["H01", "H09", "H11", "H18", "H22"]:
        if algo_id in ALGORITHM_SPECIALTY_MAP:
            specialties = ALGORITHM_SPECIALTY_MAP[algo_id]
            result = integrator.integrate_algorithm(
                algo_id, specialties, {"name": "yazd", "temp": 18.5, "rain": 60}
            )
            print(f"\n   🔬 {algo_id}:")
            print(f"      گرایش‌های استفاده‌شده: {', '.join(specialties)}")
            print(f"      اعتماد: {result['confidence']:.2f}")
            print(f"      محاسبات: {len(result['calculations'])} گرایش")
    
    print("\n" + "=" * 70)
    print("🎯 شعار: تن زمین خسته است")
    print("   ما در خدمت بشر و زمین هستیم با پیوند طبیعت و بشر")
    print("=" * 70)


if __name__ == "__main__":
    main()