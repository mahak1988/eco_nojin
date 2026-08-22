"""
HLHS — Hydroma Landscape Health Score

Composite index for landscape fund management.
HLHS = Σ(w_i × (X_i - X_min) / (X_max - X_min))

Reference: Shannon (1948), Nagendra (2002)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from .base import ScientificModel, ValidationResult


@dataclass
class LandscapeMetrics:
    """Input metrics for HLHS calculation"""
    ndvi_mean: float = 0.0
    ewsı_mean: float = 0.0
    soc_t_ha: float = 0.0
    shdi: float = 0.0  # Shannon Diversity Index
    ecsı_t_co2_ha_yr: float = 0.0
    slope_stability: float = 0.0  # 0 to 1
    connectivity: float = 0.0  # 0 to 1
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "ndvi_mean": self.ndvi_mean,
            "ewsı_mean": self.ewsı_mean,
            "soc_t_ha": self.soc_t_ha,
            "shdi": self.shdi,
            "ecsı_t_co2_ha_yr": self.ecsı_t_co2_ha_yr,
            "slope_stability": self.slope_stability,
            "connectivity": self.connectivity,
        }


class HLHS(ScientificModel):
    """Hydroma Landscape Health Score"""
    
    name = "HLHS"
    version = "1.0.0"
    description = "Composite Landscape Health Score for fund management"
    
    REFERENCES = {
        "Shannon1948": "Shannon, C.E. (1948). A Mathematical Theory of Communication.",
        "Nagendra2002": "Nagendra, H. (2002). Opposite trends in response for the Shannon and Simpson indices.",
    }
    
    WEIGHTS = {
        "vegetation": 0.20,
        "water": 0.20,
        "soil": 0.15,
        "biodiversity": 0.15,
        "carbon": 0.15,
        "topography": 0.10,
        "connectivity": 0.05,
    }
    
    BOUNDS = {
        "vegetation": (0.0, 0.8),
        "water": (0.0, 1.0),
        "soil": (0, 100),
        "biodiversity": (0.0, 3.0),
        "carbon": (-2, 5),
        "topography": (0, 1),
        "connectivity": (0, 1),
    }
    
    def validate_inputs(self, metrics: LandscapeMetrics) -> Tuple[bool, List[str]]:
        errors = []
        if not (0 <= metrics.ndvi_mean <= 1):
            errors.append("NDVI mean out of range")
        if not (0 <= metrics.ewsı_mean <= 1):
            errors.append("EWSI mean out of range")
        if metrics.soc_t_ha < 0:
            errors.append("SOC must be non-negative")
        if metrics.shdi < 0:
            errors.append("SHDI must be non-negative")
        return len(errors) == 0, errors
    
    @staticmethod
    def normalize(value: float, vmin: float, vmax: float) -> float:
        """Min-max normalization to [0, 1]"""
        if vmax <= vmin:
            return 0.5
        return max(0.0, min(1.0, (value - vmin) / (vmax - vmin)))
    
    def compute(
        self,
        metrics: LandscapeMetrics,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Compute HLHS"""
        w = weights or self.WEIGHTS
        b = self.BOUNDS
        
        components = {
            "vegetation": self.normalize(metrics.ndvi_mean, b["vegetation"][0], b["vegetation"][1]),
            "water": self.normalize(1 - metrics.ewsı_mean, 0, 1),
            "soil": self.normalize(metrics.soc_t_ha, b["soil"][0], b["soil"][1]),
            "biodiversity": self.normalize(metrics.shdi, b["biodiversity"][0], b["biodiversity"][1]),
            "carbon": self.normalize(metrics.ecsı_t_co2_ha_yr, b["carbon"][0], b["carbon"][1]),
            "topography": self.normalize(metrics.slope_stability, 0, 1),
            "connectivity": self.normalize(metrics.connectivity, 0, 1),
        }
        
        hlhs = sum(w[k] * v for k, v in components.items()) * 100
        
        if hlhs >= 80:
            classification = "excellent"
        elif hlhs >= 60:
            classification = "good"
        elif hlhs >= 40:
            classification = "fair"
        elif hlhs >= 20:
            classification = "poor"
        else:
            classification = "critical"
        
        return {
            "hlhs": hlhs,
            "components": components,
            "classification": classification,
            "weights_used": w,
        }
    
    def validate_against_reference(
        self, inputs: Dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 10.0,
    ) -> ValidationResult:
        """tolerance in HLHS points (0-100)"""
        result = self.compute(**inputs)
        computed_value = result["hlhs"]
        
        absolute_error = abs(computed_value - reference_output)
        
        return ValidationResult(
            passed=absolute_error <= tolerance,
            metric_name="HLHS",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=absolute_error / 100,
            reference_source=reference_source,
        )
