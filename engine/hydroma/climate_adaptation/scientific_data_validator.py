
"""
موتور محاسبه بهبودیافته با اعتبارسنجی علمی
"""
import math
import re
from typing import Dict, Any, Optional


import ast as _ast, math as _math, operator as _operator

_ALLOWED_FUNCS = {f: getattr(_math, f) for f in (
    "sqrt", "sin", "cos", "tan", "asin", "acos", "atan", "log", "log2",
    "log10", "exp", "floor", "ceil", "fabs", "pow", "atan2", "hypot")}
_ALLOWED_FUNCS.update({"abs": abs, "min": min, "max": max, "round": round})
_ALLOWED_OPS = {_ast.Add: _operator.add, _ast.Sub: _operator.sub,
                _ast.Mult: _operator.mul, _ast.Div: _operator.truediv,
                _ast.FloorDiv: _operator.floordiv, _ast.Mod: _operator.mod,
                _ast.Pow: _operator.pow, _ast.USub: _operator.neg,
                _ast.UAdd: _operator.pos}


def safe_eval(expr, variables=None):
    """ارزیابی امن عبارت ریاضی — بدون دسترسی به توابع/کلاس‌های پایتون."""
    def _ev(node):
        if isinstance(node, _ast.Expression):
            return _ev(node.body)
        if isinstance(node, _ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, _ast.Name):
            if variables and node.id in variables:
                return variables[node.id]
            if node.id in _ALLOWED_FUNCS:
                return _ALLOWED_FUNCS[node.id]
            raise ValueError(f"نام مجاز نیست: {node.id}")
        if isinstance(node, _ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_ev(node.left), _ev(node.right))
        if isinstance(node, _ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_ev(node.operand))
        if (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name)
                and node.func.id in _ALLOWED_FUNCS and not node.keywords):
            return _ALLOWED_FUNCS[node.func.id](*[_ev(a) for a in node.args])
        if isinstance(node, _ast.Tuple):
            return tuple(_ev(e) for e in node.elts)
        if isinstance(node, _ast.List):
            return [_ev(e) for e in node.elts]
        raise ValueError(f"عبارت مجاز نیست: {type(node).__name__}")
    return _ev(_ast.parse(str(expr), mode="eval"))


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
            result = safe_eval(expr, self.safe_env)
            
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
