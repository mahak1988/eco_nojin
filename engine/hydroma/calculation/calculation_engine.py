#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
موتور محاسبه هیدروما     
"""
import json
from pathlib import Path


class CalculationEngine:
    """موتور محاسبه با محاسبه فرمول‌ها"""
    
    def __init__(self, kb_path: str = None):
        if kb_path is None:
            kb_path = Path(__file__).parent.parent.parent.parent / "docs" / "hydroma" / "knowledge_base_detailed.json"
        else:
            kb_path = Path(kb_path)
        
        self.kb_path = kb_path
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> dict:
        if self.kb_path.exists():
            return json.loads(self.kb_path.read_text(encoding="utf-8"))
        return {}
    
    def calculate(self, specialty_id: str, indicator_id: str, region_data: dict) -> dict:
        """محاسبه واقعی یک شاخص"""
        specialty = self.knowledge_base.get(specialty_id)
        
        if not specialty:
            return {"error": f"گرایش {specialty_id} یافت نشد"}
        
        indicators = specialty.get("indicators", [])
        indicator = None
        
        for ind in indicators:
            if ind.get("id") == indicator_id:
                indicator = ind
                break
        
        if not indicator:
            return {"error": f"شاخص {indicator_id} یافت نشد"}
        
        formula = indicator.get("formula", "")
        default_value = indicator.get("default_value", 0.0)
        
        # ارزیابی فرمول با متغیرهای داده‌شده
        from .formula_evaluator import FormulaEvaluator
        evaluator = FormulaEvaluator()
        
        result_value = evaluator.evaluate(formula, region_data)
        
        # اگر فرمول قابل ارزیابی نبود، از مقدار پیش‌فرض استفاده کن
        if result_value == 0.0 and default_value != 0.0:
            result_value = default_value
        
        return {
            "specialty_id": specialty_id,
            "indicator_id": indicator_id,
            "value": result_value,
            "formula": formula,
            "default_value": default_value,
        }
