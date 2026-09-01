#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سرویس ادغام هیدروما - نسخه نهایی با محاسبه واقعی
"""
import json
from pathlib import Path


class CoreIntegration:
    """سرویس ادغام با محاسبه واقعی"""
    
    def __init__(self, kb_path: str = None):
        if kb_path is None:
            kb_path = Path(__file__).parent.parent.parent / "docs" / "hydroma" / "knowledge_base_detailed.json"
        else:
            kb_path = Path(kb_path)
        
        self.kb_path = kb_path
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> dict:
        if self.kb_path.exists():
            return json.loads(self.kb_path.read_text(encoding="utf-8"))
        return {}
    
    def integrate(self, algorithm_id: str, region_data: dict) -> dict:
        """ادغام یک الگوریتم با محاسبه واقعی"""
        # الگوریتم‌های ادغام
        algorithms = {
            "H01": ["CLI001", "WAS001", "AGR020"],
            "H02": ["CLI007", "AGR009", "AGR020"],
            "H04": ["CLI012", "AGR009"],
        }
        
        if algorithm_id not in algorithms:
            return {"error": f"الگوریتم {algorithm_id} یافت نشد"}
        
        specialties = algorithms[algorithm_id]
        results = {}
        
        from engine.hydroma.calculation.calculation_engine import CalculationEngine
        engine = CalculationEngine()
        
        for spec_id in specialties:
            spec = self.knowledge_base.get(spec_id, {})
            indicators = spec.get("indicators", [])
            
            spec_results = {}
            for ind in indicators:
                ind_id = ind.get("id", "")
                result = engine.calculate(spec_id, ind_id, region_data)
                spec_results[ind_id] = result
            
            results[spec_id] = spec_results
        
        return {
            "status": "success",
            "algorithm": algorithm_id,
            "results": results,
        }
