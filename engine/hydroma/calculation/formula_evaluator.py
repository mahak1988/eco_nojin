#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
موتور ارزیابی فرمول هیدروما - نسخه نهایی
"""
import math
import re


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
            result = safe_eval(expr, self.SAFE_FUNCS)
            
            if isinstance(result, (int, float)):
                if math.isnan(result) or math.isinf(result):
                    return 0.0
                return float(result)
            return 0.0
            
        except ZeroDivisionError:
            return 0.0
        except Exception:
            return 0.0
