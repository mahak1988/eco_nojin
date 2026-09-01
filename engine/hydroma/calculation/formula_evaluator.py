#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
موتور ارزیابی فرمول هیدروما - نسخه نهایی
"""
import math
import re


class FormulaEvaluator:
    """موتور ارزیابی فرمول با جایگزینی صحیح متغیرها"""
    
    SAFE_FUNCS = {
        "abs": abs, "min": min, "max": max, "sum": sum,
        "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
        "exp": math.exp, "sin": math.sin, "cos": math.cos,
        "tan": math.tan, "atan": math.atan, "atan2": math.atan2,
        "pi": math.pi, "e": math.e,
    }
    
    def evaluate(self, formula: str, variables: dict) -> float:
        """ارزیابی فرمول با جایگزینی صحیح متغیرها"""
        if not formula or not isinstance(formula, str):
            return 0.0
        
        try:
            # حذف بخش سمت چپ تساوی
            expr = formula
            if "=" in expr:
                expr = expr.split("=", 1)[1].strip()
            
            # تبدیل عملگرهای یونیکد
            expr = expr.replace("×", "*").replace("÷", "/")
            expr = expr.replace("^", "**")
            expr = expr.replace("Σ(", "sum(")
            
            # جایگزینی متغیرها با مقادیر داده‌شده
            # مرتب‌سازی بر اساس طول نام (بلندتر اول)
            sorted_vars = sorted(variables.keys(), key=len, reverse=True)
            
            for var_name in sorted_vars:
                var_value = variables[var_name]
                if isinstance(var_value, (int, float)):
                    # جایگزینی دقیق با کلمه کامل
                    expr = re.sub(rf'\b{re.escape(var_name)}\b', str(var_value), expr)
            
            # بررسی متغیرهای باقی‌مانده
            remaining = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', expr)
            for var in remaining:
                if var not in self.SAFE_FUNCS:
                    # متغیر ناشناخته - مقدار 0
                    expr = re.sub(rf'\b{re.escape(var)}\b', "0", expr)
            
            # ارزیابی
            result = eval(expr, {"__builtins__": {}}, self.SAFE_FUNCS)
            
            if isinstance(result, (int, float)):
                if math.isnan(result) or math.isinf(result):
                    return 0.0
                return float(result)
            return 0.0
            
        except ZeroDivisionError:
            return 0.0
        except Exception:
            return 0.0
