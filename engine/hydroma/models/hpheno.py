"""
H-Pheno — Hydroma Phenology Detection

Savitzky-Golay smoothing + derivative analysis for NDVI time series.

Reference: Zhang et al. (2003), White et al. (2009)
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List, Tuple, Any
import numpy as np

from .base import ScientificModel, ValidationResult


class HPheno(ScientificModel):
    """Hydroma Phenology Detection"""
    
    name = "H-Pheno"
    version = "1.0.0"
    description = "Phenology detection from NDVI time-series"
    
    REFERENCES = {
        "Zhang2003": "Zhang et al. (2003). Monitoring vegetation phenology using MODIS.",
        "White2009": "White et al. (2009). Derivation of phenological metrics from MODIS NDVI.",
    }
    
    def validate_inputs(
        self, ndvi_ts: np.ndarray, dates: List[date],
    ) -> Tuple[bool, List[str]]:
        errors = []
        if len(ndvi_ts) != len(dates):
            errors.append("NDVI and dates arrays must have same length")
        if len(ndvi_ts) < 12:
            errors.append("Need at least 12 observations")
        if np.any((ndvi_ts < -1) | (ndvi_ts > 1)):
            errors.append("NDVI out of range [-1, 1]")
        return len(errors) == 0, errors
    
    @staticmethod
    def smooth(ndvi: np.ndarray, window: int = 11, polyorder: int = 3) -> np.ndarray:
        """Savitzky-Golay smoothing"""
        try:
            from scipy.signal import savgol_filter
            return savgol_filter(ndvi, min(window, len(ndvi) - 1 if len(ndvi) % 2 == 0 else len(ndvi)), polyorder)
        except ImportError:
            return np.convolve(ndvi, np.ones(min(window, len(ndvi)))/min(window, len(ndvi)), mode='same')
    
    @staticmethod
    def derivative(ndvi: np.ndarray, dt_days: float = 5.0) -> np.ndarray:
        """First derivative"""
        return np.gradient(ndvi, dt_days)
    
    def compute(
        self,
        ndvi_ts: np.ndarray,
        dates: List[date],
        dt_days: float = 5.0,
        ndvi_threshold: float = 0.15,
    ) -> Dict[str, Any]:
        """Detect phenological stages"""
        ndvi_smooth = self.smooth(ndvi_ts)
        ndvi_prime = self.derivative(ndvi_smooth, dt_days)
        
        # SOS: first positive zero-crossing with NDVI above threshold
        sos_idx = None
        for i in range(1, len(ndvi_prime)):
            if ndvi_prime[i-1] <= 0 < ndvi_prime[i] and ndvi_smooth[i] > ndvi_threshold:
                sos_idx = i
                break
        
        # POS: maximum of NDVI
        pos_idx = int(np.argmax(ndvi_smooth))
        
        # EOS: first negative zero-crossing after POS
        eos_idx = None
        for i in range(pos_idx + 1, len(ndvi_prime)):
            if ndvi_prime[i-1] >= 0 > ndvi_prime[i] and ndvi_smooth[i] > ndvi_threshold:
                eos_idx = i
                break
        
        sos_date = dates[sos_idx] if sos_idx is not None else None
        pos_date = dates[pos_idx] if pos_idx is not None else None
        eos_date = dates[eos_idx] if eos_idx is not None else None
        
        los = (eos_date - sos_date).days if sos_date and eos_date else 0
        
        return {
            "sos": sos_date,
            "pos": pos_date,
            "eos": eos_date,
            "los_days": los,
            "ndvi_smooth": ndvi_smooth,
            "ndvi_derivative": ndvi_prime,
            "max_ndvi": float(np.max(ndvi_smooth)),
        }
    
    def validate_against_reference(
        self, inputs: Dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 15.0,
    ) -> ValidationResult:
        """tolerance in days for LOS"""
        result = self.compute(**inputs)
        computed_value = float(result["los_days"])
        
        absolute_error = abs(computed_value - reference_output)
        
        return ValidationResult(
            passed=absolute_error <= tolerance,
            metric_name="Length of Season (days)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=absolute_error / (reference_output + 1e-9),
            reference_source=reference_source,
        )
