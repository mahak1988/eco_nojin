
"""
موتور محاسبه بهبودیافته با اعتبارسنجی علمی
"""
import math
import re
from typing import Dict, Any, Optional


class ScientificCalculator:
    """موتور محاسبه فرمول‌های علمی با اعتبارسنجی"""
    
    def __init__(self):
        self.safe_env = {
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "asin": math.asin,
            "acos": math.acos,
            "atan": math.atan,
            "atan2": math.atan2,
            "pi": math.pi,
            "e": math.e,
        }
    
    def evaluate_formula(self, formula: str, variables: Dict[str, Any]) -> float:
        """ارزیابی ایمن یک فرمول با متغیرهای داده‌شده"""
        try:
            # جایگزینی متغیرها
            expr = formula
            for var_name, var_value in variables.items():
                if isinstance(var_value, (int, float)):
                    expr = expr.replace(var_name, str(var_value))
            
            # حذف عملگرهای نامعتبر
            expr = expr.replace("×", "*").replace("÷", "/")
            expr = expr.replace("^", "**")
            
            # ارزیابی ایمن
            result = eval(expr, {"__builtins__": {}}, self.safe_env)
            
            # بررسی معتبر بودن نتیجه
            if isinstance(result, (int, float)):
                if math.isnan(result) or math.isinf(result):
                    return 0.0
                return float(result)
            else:
                return 0.0
                
        except Exception as e:
            # در صورت خطا، از مقدار پیش‌فرض استفاده کن
            return 0.0
    
    def calculate_with_validation(self, formula: str, variables: Dict[str, Any],
                                   threshold: Dict[str, float]) -> Dict[str, Any]:
        """محاسبه با اعتبارسنجی بر اساس محدوده"""
        value = self.evaluate_formula(formula, variables)
        
        # تعیین وضعیت بر اساس محدوده
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
        
        return {
            "value": round(value, 4),
            "status": status,
            "threshold": threshold,
        }
