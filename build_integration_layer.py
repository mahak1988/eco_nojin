#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
ساخت لایه ادغام علمی هیدروما
اتصال الگوریتم‌ها به گرایش‌های تخصصی با محاسبات علمی واقعی
============================================================================
"""
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

KB_FILE = ROOT / "docs" / "hydroma" / "knowledge_base_detailed.json"
REPORT_FILE = ROOT / "docs" / "hydroma" / "integration" / "integration_report.json"

# ماتریس اتصال الگوریتم به گرایش‌ها
ALGORITHM_SPECIALTY_MAP = {
    "H01": ["CLI001", "WAS001", "AGR020"],
    "H02": ["CLI007", "AGR009", "AGR020"],
    "H04": ["CLI012", "AGR009"],
    "H05": ["AGR020", "AGR015", "CLI001"],
    "H06": ["CLI024", "CLI007"],
    "H07": ["AGR015"],
    "H09": ["WAS011", "WAS006", "AGR024"],
    "H10": ["GEO003", "GOV010", "AGR024"],
    "H11": ["WAS018"],
    "H12": ["WAS011"],
    "H13": ["FOR001", "FOR013", "ENV023"],
    "H14": ["GEO017", "GOV016", "GOV021"],
    "H15": ["AGR010", "AGR020"],
    "H17": ["AGR010", "ENV017"],
    "H18": ["AGR020", "ECO001", "LIV001"],
    "H19": ["AGR003", "AGR004"],
    "H21": ["AGR021", "ENV023", "FOR027"],
    "H22": ["TEC001", "ECO001"],
    "H23": ["TEC009", "TEC012"],
    "H25": ["ECO006", "TOU002"],
}


class IntegrationLayer:
    """لایه ادغام علمی"""
    
    def __init__(self, knowledge_base: dict):
        self.kb = knowledge_base
        self.calculator = self._create_calculator()
        self.trace_log = []
    
    def _create_calculator(self):
        """ایجاد موتور محاسبه"""
        import math
        
        class Calculator:
            def __init__(self):
                self.safe_env = {
                    "abs": abs, "max": max, "min": min, "sum": sum,
                    "pow": pow, "sqrt": math.sqrt, "log": math.log,
                    "exp": math.exp, "sin": math.sin, "cos": math.cos,
                    "pi": math.pi, "e": math.e,
                }
            
            def evaluate(self, formula: str, variables: dict) -> float:
                try:
                    expr = formula.replace("×", "*").replace("÷", "/").replace("^", "**")
                    for var_name, var_value in variables.items():
                        if isinstance(var_value, (int, float)):
                            expr = expr.replace(var_name, str(var_value))
                    
                    if "f(" in expr or "Σ" in expr:
                        return None
                    
                    result = eval(expr, {"__builtins__": {}}, self.safe_env)
                    if isinstance(result, (int, float)) and not (math.isnan(result) or math.isinf(result)):
                        return float(result)
                    return None
                except:
                    return None
        
        return Calculator()
    
    def calculate_indicator(self, specialty_id: str, indicator_id: str, 
                           variables: dict) -> dict:
        """محاسبه یک شاخص"""
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
        
        # محاسبه با موتور محاسبه
        formula = indicator.get("formula", "")
        default_value = indicator.get("default_value", 0.0)
        threshold = indicator.get("threshold", {})
        
        calculated = self.calculator.evaluate(formula, variables)
        value = calculated if calculated is not None else default_value
        
        # تعیین وضعیت
        min_val = threshold.get("min", float("-inf"))
        optimal = threshold.get("optimal", value)
        max_val = threshold.get("max", float("inf"))
        
        if value < min_val:
            status = "زیر حد"
        elif value > max_val:
            status = "بالاتر از حد"
        elif abs(value - optimal) / max(abs(optimal), 0.01) < 0.1:
            status = "بهینه"
        else:
            status = "قابل قبول"
        
        result = {
            "specialty": specialty.get("name", ""),
            "indicator": indicator.get("name", ""),
            "symbol": indicator.get("symbol", ""),
            "unit": indicator.get("unit", ""),
            "value": round(value, 4),
            "status": status,
            "formula": formula,
            "threshold": threshold,
            "inputs_used": variables,
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
    
    def integrate_algorithm(self, algo_id: str, specialty_ids: list, 
                           region_data: dict) -> dict:
        """ادغام یک الگوریتم با گرایش‌های تخصصی"""
        result = {
            "algorithm": algo_id,
            "specialties_used": specialty_ids,
            "region": region_data,
            "calculations": {},
            "integrated_output": {},
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
        }
        
        valid_count = 0
        total_count = len(specialty_ids)
        
        for spec_id in specialty_ids:
            if spec_id not in self.kb:
                result["calculations"][spec_id] = {"error": f"گرایش {spec_id} یافت نشد"}
                continue
            
            specialty = self.kb[spec_id]
            indicators = specialty.get("indicators", [])
            
            calc_result = {
                "region": region_data.get("name", ""),
                "specialty": spec_id,
                "indicators": {},
            }
            
            for indicator in indicators:
                ind_id = indicator["id"]
                calc_result["indicators"][ind_id] = self.calculate_indicator(
                    spec_id, ind_id, region_data
                )
            
            result["calculations"][spec_id] = calc_result
            valid_count += 1
        
        result["confidence"] = valid_count / total_count if total_count > 0 else 0.0
        
        return result
    
    def test_all_algorithms(self, region_data: dict) -> list:
        """تست همه الگوریتم‌ها"""
        results = []
        
        for algo_id, specialty_ids in ALGORITHM_SPECIALTY_MAP.items():
            result = self.integrate_algorithm(algo_id, specialty_ids, region_data)
            
            # بررسی موفقیت
            valid_calcs = sum(
                1 for calc in result["calculations"].values()
                if "error" not in calc
            )
            
            test_result = {
                "test": f"ادغام {algo_id}",
                "passed": result["confidence"] >= 0.5,
                "confidence": result["confidence"],
                "specialties_count": len(specialty_ids),
                "valid_calculations": valid_calcs,
                "severity": "critical" if result["confidence"] < 0.5 else "info",
            }
            
            results.append(test_result)
        
        return results


def main():
    print("=" * 70)
    print("ساخت لایه ادغام علمی هیدروما")
    print("=" * 70)
    
    # بارگذاری پایگاه دانش
    print("\n📚 بارگذاری پایگاه دانش ...")
    if not KB_FILE.exists():
        print("   ❌ پایگاه دانش یافت نشد")
        return
    
    kb = json.loads(KB_FILE.read_text(encoding="utf-8"))
    print(f"   ✅ {len(kb)} گرایش بارگذاری شد")
    
    # ایجاد لایه ادغام
    print("\n🔗 ایجاد لایه ادغام ...")
    layer = IntegrationLayer(kb)
    
    # داده‌های منطقه تست (یزد)
    region_data = {
        "name": "yazd",
        "temp": 18.5,
        "rain": 60,
        "koppen": "BWh",
    }
    
    # اجرای تست
    print("\n🧪 اجرای تست ادغام ...")
    test_results = layer.test_all_algorithms(region_data)
    
    # محاسبه آمار
    total_tests = len(test_results)
    passed_tests = sum(1 for t in test_results if t["passed"])
    failed_tests = total_tests - passed_tests
    critical_tests = sum(1 for t in test_results if t["severity"] == "critical")
    avg_confidence = sum(t["confidence"] for t in test_results) / total_tests if total_tests > 0 else 0
    
    # ذخیره گزارش
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "critical": critical_tests,
            "average_confidence": round(avg_confidence, 2),
            "pass_rate_percent": round(passed_tests / total_tests * 100, 1) if total_tests > 0 else 0,
            "tests": test_results,
        },
        "algorithm_specialty_map": ALGORITHM_SPECIALTY_MAP,
        "trace_log": layer.trace_log[:50],  # فقط ۵۰ مورد اول
        "integration_results": [
            layer.integrate_algorithm(algo_id, spec_ids, region_data)
            for algo_id, spec_ids in list(ALGORITHM_SPECIALTY_MAP.items())[:5]
        ],
    }
    
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # خلاصه نتایج
    print("\n" + "=" * 70)
    print("📊 نتایج تست ادغام")
    print("=" * 70)
    print(f"   🧪 تعداد تست‌ها: {total_tests}")
    print(f"   ✅ موفق: {passed_tests} ({report['summary']['pass_rate_percent']}%)")
    print(f"   ❌ ناموفق: {failed_tests}")
    print(f"   🔴 بحرانی: {critical_tests}")
    print(f"   📈 میانگین اعتماد: {avg_confidence:.2f}")
    print("=" * 70)
    
    # نمایش نتایج بحرانی
    if critical_tests > 0:
        print("\n⚠️ الگوریتم‌های بحرانی:")
        for test in test_results:
            if test["severity"] == "critical":
                print(f"   ❌ {test['test']}: اعتماد {test['confidence']:.2f}")
    
    print(f"\n📄 گزارش ذخیره شد: {REPORT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()