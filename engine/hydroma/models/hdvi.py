"""
HDVI — Hydroma Drought Vulnerability Index

Multi-scale drought index combining:
- SPI (Standardized Precipitation Index)
- SPEI (Standardized Precipitation-Evapotranspiration Index)
- VHI (Vegetation Health Index)
- SMI (Soil Moisture Index)

Reference: McKee et al. (1993), Vicente-Serrano (2010), Kogan (1995)
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Any
import numpy as np

from .base import ScientificModel, ValidationResult


class HDVI(ScientificModel):
    """Hydroma Drought Vulnerability Index"""
    
    name = "HDVI"
    version = "1.0.0"
    description = "Multi-scale Drought Vulnerability Index"
    
    REFERENCES = {
        "McKee1993": "McKee et al. (1993). The relationship of drought frequency and duration to SPI.",
        "VicenteSerrano2010": "Vicente-Serrano et al. (2010). A Multiscalar Drought Index (SPEI).",
        "Kogan1995": "Kogan, F.N. (1995). Application of vegetation index for drought monitoring.",
    }
    
    def validate_inputs(
        self, spi_value, spei_value, vhi_value, smi_value,
    ) -> Tuple[bool, List[str]]:
        errors = []
        if not (-5 <= spi_value <= 5):
            errors.append("SPI out of typical range [-5, 5]")
        if not (-5 <= spei_value <= 5):
            errors.append("SPEI out of typical range")
        if np.any((vhi_value < 0) | (vhi_value > 100)):
            errors.append("VHI out of range [0, 100]")
        if np.any((smi_value < 0) | (smi_value > 1)):
            errors.append("SMI out of range [0, 1]")
        return len(errors) == 0, errors
    
    @staticmethod
    def spi(precip_series: np.ndarray, window: int = 3) -> np.ndarray:
        """Standardized Precipitation Index"""
        spi_values = np.full_like(precip_series, np.nan, dtype=float)
        
        for i in range(window, len(precip_series)):
            window_data = precip_series[i - window:i]
            if np.any(window_data <= 0):
                continue
            mu = np.mean(window_data)
            sigma = np.std(window_data) + 1e-6
            spi_values[i] = (precip_series[i] - mu) / sigma
        
        return spi_values
    
    @staticmethod
    def vhi(ndvi: np.ndarray, lst: np.ndarray,
            ndvi_min: float = 0.1, ndvi_max: float = 0.9,
            lst_min: float = 270.0, lst_max: float = 330.0) -> np.ndarray:
        """Vegetation Health Index (Kogan 1995)"""
        vci = np.clip((ndvi - ndvi_min) / (ndvi_max - ndvi_min + 1e-9), 0, 1) * 100
        tci = np.clip((lst_max - lst) / (lst_max - lst_min + 1e-9), 0, 1) * 100
        return 0.5 * vci + 0.5 * tci
    
    @staticmethod
    def smi(soil_moisture: np.ndarray, wilting_point: float,
            field_capacity: float) -> np.ndarray:
        """Soil Moisture Index"""
        return np.clip(
            (soil_moisture - wilting_point) / (field_capacity - wilting_point + 1e-9),
            0, 1
        )
    
    def compute(
        self,
        spi_value: float,
        spei_value: float,
        vhi_value: np.ndarray,
        smi_value: np.ndarray,
        weights: Tuple[float, float, float, float] = (0.25, 0.25, 0.25, 0.25),
    ) -> Dict[str, Any]:
        """Compute HDVI"""
        w1, w2, w3, w4 = weights
        
        # Normalize VHI and SMI to SPI-like scale
        vhi_norm = (vhi_value - 50) / 50 * 3
        smi_norm = (smi_value - 0.5) * 6
        
        hdvi = (
            w1 * spi_value +
            w2 * spei_value +
            w3 * vhi_norm +
            w4 * smi_norm
        )
        
        hdvi_clipped = np.clip(hdvi, -3, 3)
        
        return {
            "hdvi": hdvi_clipped,
            "classification": self.classify(hdvi_clipped),
            "spi": spi_value,
            "spei": spei_value,
            "vhi_norm": vhi_norm,
            "smi_norm": smi_norm,
        }
    
    @staticmethod
    def classify(hdvi: np.ndarray) -> np.ndarray:
        """طبقه‌بندی شدت خشکسالی"""
        return np.select(
            [hdvi > 0, hdvi > -1, hdvi > -2],
            ["normal", "mild_drought", "moderate_drought"],
            default="severe_drought"
        )
    
    def validate_against_reference(
        self, inputs: Dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.5,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["hdvi"]))
        
        # HDVI range is [-3, 3], so tolerance is absolute
        absolute_error = abs(computed_value - reference_output)
        
        return ValidationResult(
            passed=absolute_error <= tolerance,
            metric_name="HDVI",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=absolute_error,
            reference_source=reference_source,
        )
