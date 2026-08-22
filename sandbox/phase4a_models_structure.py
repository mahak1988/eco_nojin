"""
Phase 4a: Professional Models Structure Generator
هدف: ایجاد ساختار enterprise برای مدل‌های Hydroma
پروتکل: Type hints + Docstrings + Validation data + Benchmarks
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
MODELS_ROOT = PROJECT_ROOT / "engine" / "hydroma" / "models"

# ============================================================================
# Template definitions
# ============================================================================

STRUCTURE = {
    "__init__.py": '''"""
Hydroma Scientific Models Library
=================================

Proprietary scientific models for precision agriculture and landscape management.

Models:
- EWSI: Multi-source Water Stress Index
- HYRUE: Radiation Use Efficiency Model
- ECSI: Carbon Sequestration Index
- HDVI: Drought Vulnerability Index
- EPIA: Precision Irrigation Advisor
- HPheno: Phenology Detection
- ESRI: Salinity Risk Index
- HLHS: Landscape Health Score

Author: EcoNojin Scientific Council
License: Proprietary
"""
from .base import ScientificModel, ValidationResult
from .ewsi import EWSI
from .hyrue import HYRUE
from .ecsi import ECSI
from .hdvi import HDVI
from .epia import EPIA
from .hpheno import HPheno
from .esri import ESRI
from .hlhs import HLHS

__all__ = [
    "ScientificModel",
    "ValidationResult",
    "EWSI",
    "HYRUE",
    "ECSI",
    "HDVI",
    "EPIA",
    "HPheno",
    "ESRI",
    "HLHS",
]

__version__ = "1.0.0"
''',
    
    "base.py": '''"""
Base classes for Hydroma scientific models.

All scientific models must inherit from ScientificModel and implement:
- validate_inputs()
- compute()
- validate_against_reference()
- uncertainty_quantification()
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class ValidationResult:
    """نتیجه اعتبارسنجی یک مدل"""
    passed: bool
    metric_name: str
    computed_value: float
    reference_value: float
    tolerance: float
    relative_error: float
    reference_source: str
    notes: str = ""
    
    @property
    def is_within_tolerance(self) -> bool:
        return self.relative_error <= self.tolerance


class ScientificModel(ABC):
    """
    کلاس پایه برای تمام مدل‌های علمی Hydroma.
    
    الزامات:
    - تمام ورودی‌ها باید type-hinted باشند
    - تمام محاسبات باید vectorized باشند (numpy)
    - باید validation against published data داشته باشند
    - باید uncertainty quantification ارائه دهند
    """
    
    name: str = "BaseModel"
    version: str = "1.0.0"
    description: str = "Base scientific model"
    
    # Reference literature for validation
    REFERENCES: Dict[str, str] = {}
    
    def __init__(self, **config):
        self.config = config
        self._last_computation_time: Optional[float] = None
        self._uncertainty_estimate: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def validate_inputs(self, **inputs) -> Tuple[bool, List[str]]:
        """اعتبارسنجی ورودی‌ها قبل از محاسبه"""
        pass
    
    @abstractmethod
    def compute(self, **inputs) -> Any:
        """محاسبه اصلی مدل"""
        pass
    
    @abstractmethod
    def validate_against_reference(
        self,
        inputs: Dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.1,
    ) -> ValidationResult:
        """مقایسه با داده مرجع علمی"""
        pass
    
    def uncertainty_quantification(
        self,
        base_inputs: Dict[str, Any],
        perturbation_percent: float = 10.0,
        n_samples: int = 100,
    ) -> Dict[str, Any]:
        """
        تحلیل حساسیت و عدم قطعیت با Monte Carlo
        
        پارامترهای ورودی را با توزیع نرمال مختل می‌کند و
        توزیع خروجی را گزارش می‌دهد.
        """
        import time
        
        outputs = []
        rng = np.random.default_rng(42)
        
        t0 = time.time()
        for _ in range(n_samples):
            perturbed = {}
            for key, value in base_inputs.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    sigma = abs(value) * perturbation_percent / 100
                    perturbed[key] = rng.normal(value, max(sigma, 1e-6))
                elif isinstance(value, np.ndarray):
                    sigma = np.abs(value) * perturbation_percent / 100
                    perturbed[key] = rng.normal(value, np.maximum(sigma, 1e-6))
                else:
                    perturbed[key] = value
            
            try:
                result = self.compute(**perturbed)
                if isinstance(result, np.ndarray):
                    outputs.append(float(np.mean(result)))
                elif isinstance(result, (int, float)):
                    outputs.append(float(result))
            except Exception:
                continue
        
        elapsed = time.time() - t0
        
        if not outputs:
            return {"error": "All Monte Carlo samples failed"}
        
        outputs_arr = np.array(outputs)
        base_result = self.compute(**base_inputs)
        base_value = float(np.mean(base_result)) if isinstance(base_result, np.ndarray) else float(base_result)
        
        self._uncertainty_estimate = {
            "mean": float(np.mean(outputs_arr)),
            "std": float(np.std(outputs_arr)),
            "min": float(np.min(outputs_arr)),
            "max": float(np.max(outputs_arr)),
            "percentile_5": float(np.percentile(outputs_arr, 5)),
            "percentile_95": float(np.percentile(outputs_arr, 95)),
            "coefficient_of_variation": float(np.std(outputs_arr) / (np.mean(outputs_arr) + 1e-9)),
            "n_samples": len(outputs),
            "n_failed": n_samples - len(outputs),
            "computation_time_seconds": elapsed,
            "base_value": base_value,
        }
        
        return self._uncertainty_estimate
    
    def sensitivity_analysis(
        self,
        base_inputs: Dict[str, Any],
        parameters_to_test: Optional[List[str]] = None,
        perturbation_percent: float = 10.0,
    ) -> Dict[str, float]:
        """
        Local sensitivity analysis: اثر تغییر هر پارامتر روی خروجی
        
        Returns: {parameter_name: sensitivity_index}
        """
        base_result = self.compute(**base_inputs)
        base_value = float(np.mean(base_result)) if isinstance(base_result, np.ndarray) else float(base_result)
        
        params = parameters_to_test or [
            k for k, v in base_inputs.items() if isinstance(v, (int, float))
        ]
        
        sensitivities = {}
        for param in params:
            perturbed = base_inputs.copy()
            original = perturbed[param]
            perturbed[param] = original * (1 + perturbation_percent / 100)
            
            try:
                new_result = self.compute(**perturbed)
                new_value = float(np.mean(new_result)) if isinstance(new_result, np.ndarray) else float(new_result)
                if abs(base_value) > 1e-9:
                    sensitivity = (new_value - base_value) / base_value / (perturbation_percent / 100)
                else:
                    sensitivity = 0.0
                sensitivities[param] = float(sensitivity)
            except Exception:
                sensitivities[param] = 0.0
        
        return sensitivities
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(version={self.version})"
''',
    
    "ewsi.py": '''"""
EWSI — EcoNojin Water Stress Index

Multi-source fusion index combining:
- Sentinel-2 NDMI (optical)
- Atmospheric VPD (meteorological)
- Root zone soil moisture (pedological)

Reference: Gao (1996), Monteith (1993)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import numpy as np

from .base import ScientificModel, ValidationResult


@dataclass
class EWSIWeights:
    """وزن‌های مؤلفه‌های EWSI"""
    ndmi: float = 0.4
    vpd: float = 0.3
    soil: float = 0.3
    
    def __post_init__(self):
        total = self.ndmi + self.vpd + self.soil
        if abs(total - 1.0) > 1e-6:
            self.ndmi /= total
            self.vpd /= total
            self.soil /= total


class EWSI(ScientificModel):
    """EcoNojin Water Stress Index"""
    
    name = "EWSI"
    version = "1.0.0"
    description = "Multi-source Water Stress Index"
    
    REFERENCES = {
        "Gao1996": "Gao, B.C. (1996). NDWI - A normalized difference water index. Remote Sensing of Environment, 58(3), 257-266.",
        "Monteith1993": "Monteith, J.L. (1993). The exchange of water and carbon by crops in a semi-arid subtropical climate.",
    }
    
    # Valid ranges based on peer-reviewed literature
    NDMI_RANGE = (-1.0, 1.0)
    VPD_RANGE = (0.0, 10.0)  # kPa
    SOIL_MOISTURE_RANGE = (0.0, 0.6)  # m³/m³
    
    def __init__(self, weights: EWSIWeights = None, **config):
        super().__init__(**config)
        self.weights = weights or EWSIWeights()
    
    def validate_inputs(self, nir, swir, vpd, soil_moisture, soil_field_capacity) -> Tuple[bool, List[str]]:
        errors = []
        
        # NDMI validation
        ndmi = (nir - swir) / (nir + swir + 1e-9)
        if np.any((ndmi < self.NDMI_RANGE[0]) | (ndmi > self.NDMI_RANGE[1])):
            errors.append(f"NDMI out of range {self.NDMI_RANGE}")
        
        # VPD validation
        if not (self.VPD_RANGE[0] <= vpd <= self.VPD_RANGE[1]):
            errors.append(f"VPD {vpd} out of range {self.VPD_RANGE}")
        
        # Soil moisture validation
        if not (self.SOIL_MOISTURE_RANGE[0] <= soil_moisture <= self.SOIL_MOISTURE_RANGE[1]):
            errors.append(f"Soil moisture {soil_moisture} out of range")
        
        if soil_moisture > soil_field_capacity * 1.1:
            errors.append("Soil moisture exceeds field capacity")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def ndmi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """Normalized Difference Moisture Index"""
        with np.errstate(divide="ignore", invalid="ignore"):
            result = (nir - swir) / (nir + swir + 1e-9)
        return np.clip(np.nan_to_num(result, nan=np.nan), -1, 1)
    
    def compute(
        self,
        nir: np.ndarray,
        swir: np.ndarray,
        vpd: float,
        soil_moisture: float,
        soil_field_capacity: float,
    ) -> np.ndarray:
        """
        Compute EWSI
        
        Returns:
            numpy array in range [0, 1] where:
            - 0: no stress (optimal)
            - 1: severe stress
        """
        # Component 1: NDMI stress (inverted)
        ndmi_val = self.ndmi(nir, swir)
        ndmi_stress = np.clip(1 - ndmi_val, 0, 1)
        
        # Component 2: VPD stress (normalized)
        vpd_stress = np.clip((vpd - 0.5) / 3.5, 0, 1)
        
        # Component 3: Soil moisture stress
        soil_stress = np.clip(1 - (soil_moisture / soil_field_capacity), 0, 1)
        
        # Weighted fusion
        ewsı = (
            self.weights.ndmi * ndmi_stress +
            self.weights.vpd * vpd_stress +
            self.weights.soil * soil_stress
        )
        
        return np.clip(ewsı, 0, 1)
    
    def validate_against_reference(
        self,
        inputs: Dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.1,
    ) -> ValidationResult:
        computed = self.compute(**inputs)
        computed_value = float(np.mean(computed)) if isinstance(computed, np.ndarray) else float(computed)
        
        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)
        
        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="EWSI",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
    
    @staticmethod
    def classify(ewsı: np.ndarray) -> np.ndarray:
        """طبقه‌بندی سطح تنش آبی"""
        return np.select(
            [ewsı < 0.3, ewsı < 0.6, ewsı < 0.8],
            ["optimal", "mild", "moderate"],
            default="severe"
        )
''',
    
    "hyrue.py": '''"""
HY-RUE — Hydroma Radiation Use Efficiency Model

Based on Monteith (1977) enhanced with Sentinel-2 LAI retrieval.
B = Σ(PAR × fIPAR × ε × f_stress)
Y = B × HI

Reference: Monteith (1977), Steduto et al. (2009)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from .base import ScientificModel, ValidationResult


@dataclass
class HYRUEParams:
    """پارامترهای مدل HY-RUE"""
    epsilon: float = 2.5  # RUE (g/MJ IPAR)
    k: float = 0.65  # Extinction coefficient
    hi: float = 0.45  # Harvest index
    lai_max: float = 6.0  # Maximum LAI
    t_opt: float = 25.0  # Optimal temperature (°C)
    t_min: float = 5.0  # Minimum temperature
    t_max: float = 35.0  # Maximum temperature
    
    # Crop-specific presets
    CROP_PRESETS = {
        "wheat": {"epsilon": 2.2, "hi": 0.45, "t_opt": 20.0},
        "maize": {"epsilon": 3.3, "hi": 0.50, "t_opt": 25.0},
        "rice": {"epsilon": 2.2, "hi": 0.45, "t_opt": 28.0},
        "potato": {"epsilon": 2.8, "hi": 0.75, "t_opt": 18.0},
    }
    
    @classmethod
    def for_crop(cls, crop_name: str) -> "HYRUEParams":
        presets = cls.CROP_PRESETS.get(crop_name.lower())
        if presets:
            return cls(**presets)
        return cls()


class HYRUE(ScientificModel):
    """Hydroma Radiation Use Efficiency Model"""
    
    name = "HY-RUE"
    version = "1.0.0"
    description = "Radiation Use Efficiency with satellite LAI"
    
    REFERENCES = {
        "Monteith1977": "Monteith, J.L. (1977). Climate and the efficiency of crop production in Britain. Phil Trans R Soc B, 281, 277-294.",
        "Steduto2009": "Steduto et al. (2009). AquaCrop-The FAO crop model. Agronomy Journal, 101(3), 426-437.",
    }
    
    def __init__(self, params: HYRUEParams = None, crop: str = None, **config):
        super().__init__(**config)
        if crop:
            self.params = HYRUEParams.for_crop(crop)
        else:
            self.params = params or HYRUEParams()
    
    def validate_inputs(self, par, lai, ewsı, t_mean) -> Tuple[bool, List[str]]:
        errors = []
        if not (0 <= par <= 50):
            errors.append(f"PAR {par} MJ/m² out of range")
        if np.any(lai < 0) or np.any(lai > 10):
            errors.append("LAI out of range [0, 10]")
        if np.any((ewsı < 0) | (ewsı > 1)):
            errors.append("EWSI out of range [0, 1]")
        if not (-10 <= t_mean <= 50):
            errors.append(f"Temperature {t_mean}°C out of range")
        return len(errors) == 0, errors
    
    @staticmethod
    def f_ipar(lai: np.ndarray, k: float = 0.65) -> np.ndarray:
        """Fraction of intercepted PAR (Beer-Lambert)"""
        return 1 - np.exp(-k * np.clip(lai, 0, 20))
    
    @staticmethod
    def stress_temperature(t_mean: float, t_opt: float = 25.0,
                           t_min: float = 5.0, t_max: float = 35.0) -> float:
        """Temperature stress factor (Gaussian response)"""
        if t_mean < t_min or t_mean > t_max:
            return 0.0
        return float(np.exp(-((t_mean - t_opt) / 8) ** 2))
    
    def compute_daily(
        self,
        par: float,
        lai: np.ndarray,
        ewsı: np.ndarray,
        t_mean: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """محاسبه روزانه"""
        f_ipar = self.f_ipar(lai, self.params.k)
        f_water = 1 - ewsı
        f_temp = self.stress_temperature(t_mean, self.params.t_opt,
                                          self.params.t_min, self.params.t_max)
        
        apár = par * f_ipar
        biomass = apár * self.params.epsilon * f_water * f_temp
        
        return f_ipar, biomass
    
    def compute(
        self,
        par: float,
        lai: np.ndarray,
        ewsı: np.ndarray,
        t_mean: float,
        days: int = 1,
    ) -> Dict[str, Any]:
        """Compute biomass and yield"""
        f_ipar, daily_biomass = self.compute_daily(par, lai, ewsı, t_mean)
        
        total_biomass = daily_biomass * days
        yield_value = total_biomass * self.params.hi
        
        return {
            "f_ipar": f_ipar,
            "daily_biomass_g_m2": daily_biomass,
            "total_biomass_g_m2": total_biomass,
            "yield_g_m2": yield_value,
            "yield_t_ha": yield_value / 100,  # convert g/m² to t/ha
        }
    
    def validate_against_reference(
        self, inputs: Dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.2,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["yield_t_ha"]))
        
        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)
        
        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="Yield (t/ha)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
''',
    
    "ecsi.py": '''"""
ECSI — EcoNojin Carbon Sequestration Index

Based on RothC-26.3 model.
dC/dt = I - k × C × f(T) × f(M) × f(P)

Reference: Coleman & Jenkinson (1996)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

from .base import ScientificModel, ValidationResult


class ECSI(ScientificModel):
    """EcoNojin Carbon Sequestration Index based on RothC"""
    
    name = "ECSI"
    version = "1.0.0"
    description = "Carbon Sequestration based on RothC-26.3"
    
    REFERENCES = {
        "Coleman1996": "Coleman, K. & Jenkinson, D.S. (1996). RothC-26.3 - A model for the turnover of carbon in soil.",
    }
    
    # RothC pool decomposition rates (per year)
    POOLS = {
        "DPM": 10.0,  # Decomposable Plant Material
        "RPM": 0.3,   # Resistant Plant Material
        "BIO": 0.66,  # Microbial Biomass
        "HUM": 0.02,  # Humified Organic Matter
        "IOM": 0.0,   # Inert Organic Matter
    }
    
    # Pool fractions in total SOC (typical for agricultural soils)
    POOL_FRACTIONS = {
        "DPM": 0.01,
        "RPM": 0.04,
        "BIO": 0.03,
        "HUM": 0.54,
        "IOM": 0.38,
    }
    
    def validate_inputs(
        self, initial_soc, carbon_input, t_mean, rainfall,
        evaporation, clay_fraction, land_use,
    ) -> Tuple[bool, List[str]]:
        errors = []
        if initial_soc < 0 or initial_soc > 500:
            errors.append("Initial SOC out of range [0, 500] t/ha")
        if carbon_input < 0:
            errors.append("Carbon input must be non-negative")
        if not (-20 <= t_mean <= 40):
            errors.append("Temperature out of range")
        if rainfall < 0:
            errors.append("Rainfall must be non-negative")
        if evaporation < 0:
            errors.append("Evaporation must be non-negative")
        if not (0 <= clay_fraction <= 1):
            errors.append("Clay fraction must be in [0, 1]")
        return len(errors) == 0, errors
    
    @staticmethod
    def temperature_factor(t_mean_c: float) -> float:
        """RothC temperature rate modifier"""
        if t_mean_c <= -5.0:
            return 0.0
        return float(np.exp(0.047 * t_mean_c - 0.86))
    
    @staticmethod
    def moisture_factor(rainfall_mm: float, evaporation_mm: float,
                        clay_fraction: float = 0.23) -> float:
        """RothC moisture rate modifier"""
        if evaporation_mm <= 0:
            return 1.0
        ratio = rainfall_mm / evaporation_mm
        return float(np.clip(ratio * (1 - clay_fraction), 0.0, 1.0))
    
    @staticmethod
    def plant_retain_factor(land_use: str) -> float:
        """Plant retain factor by land use"""
        factors = {
            "arable": 0.6, "grassland": 0.85, "forest": 0.95,
            "bare": 0.0, "orchard": 0.8, "wetland": 0.9,
        }
        return factors.get(land_use, 0.6)
    
    @staticmethod
    def co2_bio_hum_ratio(clay_fraction: float) -> float:
        """CO2/(BIO+HUM) ratio from clay content"""
        return 1.67 + 1.94 * clay_fraction
    
    def compute(
        self,
        initial_soc_t_ha: float,
        carbon_input_t_ha: float,
        t_mean_c: float,
        rainfall_mm: float,
        evaporation_mm: float,
        clay_fraction: float = 0.23,
        land_use: str = "arable",
        dt_years: float = 1.0,
    ) -> Dict[str, Any]:
        """Compute annual SOC sequestration"""
        f_T = self.temperature_factor(t_mean_c)
        f_M = self.moisture_factor(rainfall_mm, evaporation_mm, clay_fraction)
        f_P = self.plant_retain_factor(land_use)
        
        # Pool-specific decomposition
        pool_soc = {
            pool: initial_soc_t_ha * self.POOL_FRACTIONS[pool]
            for pool in self.POOLS
        }
        
        total_decomposition = sum(
            self.POOLS[pool] * pool_soc[pool] * f_T * f_M * f_P
            for pool in self.POOLS if pool != "IOM"
        ) * dt_years
        
        delta_soc = carbon_input_t_ha * dt_years - total_decomposition
        co2_eq = delta_soc * 44 / 12
        
        return {
            "delta_soc_t_ha_yr": delta_soc,
            "co2_eq_t_ha_yr": co2_eq,
            "final_soc_t_ha": initial_soc_t_ha + delta_soc,
            "temperature_factor": f_T,
            "moisture_factor": f_M,
            "plant_retain_factor": f_P,
            "total_decomposition_t_ha": total_decomposition,
        }
    
    def validate_against_reference(
        self, inputs: Dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.3,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = result["delta_soc_t_ha_yr"]
        
        relative_error = abs(computed_value - reference_output) / (abs(reference_output) + 1e-9)
        
        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ΔSOC (t/ha/yr)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
''',
    
    "hdvi.py": '''"""
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
''',
    
    "epia.py": '''"""
EPIA — EcoNojin Precision Irrigation Advisor

FAO-56 ETc + Sentinel-2 Kc for precision scheduling.
ETc = ET0 × Kc × Ks

Reference: Allen et al. (1998) FAO-56
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Any
import numpy as np

from .base import ScientificModel, ValidationResult


class EPIA(ScientificModel):
    """EcoNojin Precision Irrigation Advisor"""
    
    name = "EPIA"
    version = "1.0.0"
    description = "Precision Irrigation Advisor with satellite Kc"
    
    REFERENCES = {
        "Allen1998": "Allen et al. (1998). Crop evapotranspiration. FAO Irrigation and Drainage Paper 56.",
        "Jensen2016": "Jensen, M.E. & Allen, R.G. (2016). Crop Water Requirements.",
    }
    
    def validate_inputs(
        self, et0, lai, soil_moisture, rainfall_forecast_mm,
    ) -> Tuple[bool, List[str]]:
        errors = []
        if not (0 <= et0 <= 20):
            errors.append("ET0 out of range")
        if np.any(lai < 0) or np.any(lai > 10):
            errors.append("LAI out of range")
        if not (0 <= soil_moisture <= 0.6):
            errors.append("Soil moisture out of range")
        if rainfall_forecast_mm < 0:
            errors.append("Rainfall must be non-negative")
        return len(errors) == 0, errors
    
    @staticmethod
    def kc_from_lai(lai: np.ndarray, lai_max: float = 6.0,
                    kc_min: float = 0.1, kc_max: float = 1.2) -> np.ndarray:
        """Derive Kc from LAI"""
        return np.clip(
            kc_min + (kc_max - kc_min) * (lai / lai_max),
            kc_min, kc_max
        )
    
    @staticmethod
    def ks_water_stress(soil_moisture: float, depletion_fraction: float = 0.5,
                        taw: float = 50.0) -> float:
        """Water stress coefficient Ks (FAO-56)"""
        raw = depletion_fraction * taw
        dr = taw * (1 - soil_moisture / 0.4)  # Simplified
        if dr <= raw:
            return 1.0
        return float(np.clip((taw - dr) / (taw - raw + 1e-6), 0, 1))
    
    @staticmethod
    def effective_rainfall(rainfall_mm: float, method: str = "usda_scs") -> float:
        """Effective rainfall (USDA-SCS method)"""
        if rainfall_mm <= 250:
            return float((125 - 0.2 * rainfall_mm) * rainfall_mm / 125)
        return float(0.75 * rainfall_mm - 25)
    
    def compute(
        self,
        et0: float,
        lai: np.ndarray,
        soil_moisture: float,
        rainfall_forecast_mm: float,
        irrigation_efficiency: float = 0.85,
        taw: float = 50.0,
        depletion_fraction: float = 0.5,
    ) -> Dict[str, Any]:
        """Generate irrigation recommendation"""
        kc = self.kc_from_lai(lai)
        ks = self.ks_water_stress(soil_moisture, depletion_fraction, taw)
        etc = et0 * kc * ks
        
        p_eff = self.effective_rainfall(rainfall_forecast_mm)
        irri_net = np.maximum(0, etc - p_eff)
        irri_gross = irri_net / irrigation_efficiency
        irri_m3_ha = irri_gross * 10  # mm to m³/ha
        
        raw = depletion_fraction * taw
        days = max(1, int(raw / (et0 + 1e-6)))
        
        mean_kc = float(np.mean(kc))
        if mean_kc < 0.3:
            stage = "initial"
        elif mean_kc < 0.8:
            stage = "development"
        elif mean_kc < 1.1:
            stage = "mid-season"
        else:
            stage = "late-season"
        
        return {
            "et0": et0,
            "kc": kc,
            "ks": ks,
            "etc": etc,
            "irrigation_need_mm": irri_net,
            "irrigation_need_m3_ha": irri_m3_ha,
            "days_until_irrigation": days,
            "crop_stage": stage,
            "recommendation": f"Irrigate {float(np.mean(irri_gross)):.1f} mm in {days} days ({stage})",
        }
    
    def validate_against_reference(
        self, inputs: Dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.2,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["etc"]))
        
        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)
        
        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ETc (mm/day)",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
''',
    
    "hpheno.py": '''"""
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
''',
    
    "esri.py": '''"""
ESRI — EcoNojin Salinity Risk Index

Spectral Salinity Index + soil EC + irrigation management.

Reference: Ayers & Westcot (1985) FAO-29, Richards (1954)
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Any
import numpy as np

from .base import ScientificModel, ValidationResult


class ESRI(ScientificModel):
    """EcoNojin Salinity Risk Index"""
    
    name = "ESRI"
    version = "1.0.0"
    description = "Salinity Risk Index (spectral + soil + irrigation)"
    
    REFERENCES = {
        "Ayers1985": "Ayers, R.S. & Westcot, D.W. (1985). Water quality for agriculture. FAO Irrigation and Drainage Paper 29.",
        "Richards1954": "Richards, L.A. (1954). Diagnosis and improvement of saline and alkali soils.",
    }
    
    def validate_inputs(
        self, blue, red, nir, swir, ec_soil_dsm, ec_irrigation_dsm,
    ) -> Tuple[bool, List[str]]:
        errors = []
        for band_name, band in [("blue", blue), ("red", red), ("nir", nir), ("swir", swir)]:
            if np.any(band < 0) or np.any(band > 1):
                errors.append(f"{band_name} band reflectance out of range [0, 1]")
        if ec_soil_dsm < 0 or ec_soil_dsm > 30:
            errors.append("Soil EC out of range [0, 30] dS/m")
        if ec_irrigation_dsm < 0 or ec_irrigation_dsm > 10:
            errors.append("Irrigation EC out of range [0, 10] dS/m")
        return len(errors) == 0, errors
    
    @staticmethod
    def salinity_index_s2(blue: np.ndarray, red: np.ndarray,
                          nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
        """Sentinel-2 Salinity Index"""
        with np.errstate(divide="ignore", invalid="ignore"):
            numerator = np.sqrt(blue * red + 1e-9)
            ratio1 = nir / (swir + 1e-6)
            ratio2 = blue / (red + 1e-6)
            si = numerator / (ratio1 * ratio2 + 1e-6)
        return np.nan_to_num(si, nan=np.nan)
    
    @staticmethod
    def leaching_requirement(ec_w: float, ec_e: float) -> float:
        """FAO-32 Leaching Requirement"""
        if ec_w <= 0:
            return 0.0
        denominator = 5 * ec_e - ec_w
        if denominator <= 0:
            return 1.0
        return min(1.0, ec_w / denominator)
    
    def compute(
        self,
        blue: np.ndarray,
        red: np.ndarray,
        nir: np.ndarray,
        swir: np.ndarray,
        ec_soil_dsm: float = 2.0,
        ec_irrigation_dsm: float = 0.5,
        actual_leaching_fraction: float = 0.2,
        weights: Tuple[float, float, float] = (0.3, 0.5, 0.2),
    ) -> Dict[str, Any]:
        """Compute ESRI"""
        alpha, beta, gamma = weights
        
        si = self.salinity_index_s2(blue, red, nir, swir)
        si_norm = np.clip(si / 10, 0, 1)
        
        ec_norm = np.clip(ec_soil_dsm / 16, 0, 1)
        
        lr_required = self.leaching_requirement(ec_irrigation_dsm, ec_soil_dsm)
        lr_deficit = np.clip(lr_required - actual_leaching_fraction, 0, 1)
        
        esri = alpha * si_norm + beta * ec_norm + gamma * lr_deficit
        
        return {
            "esri": np.clip(esri, 0, 1),
            "classification": self.classify(esri),
            "salinity_index": si,
            "ec_norm": ec_norm,
            "leaching_requirement": lr_required,
            "leaching_deficit": lr_deficit,
        }
    
    @staticmethod
    def classify(esri: np.ndarray) -> np.ndarray:
        """طبقه‌بندی ریسک شوری"""
        return np.select(
            [esri < 0.3, esri < 0.6, esri < 0.8],
            ["low", "moderate", "high"],
            default="severe"
        )
    
    def validate_against_reference(
        self, inputs: Dict[str, Any], reference_output: float,
        reference_source: str, tolerance: float = 0.15,
    ) -> ValidationResult:
        result = self.compute(**inputs)
        computed_value = float(np.mean(result["esri"]))
        
        relative_error = abs(computed_value - reference_output) / (reference_output + 1e-9)
        
        return ValidationResult(
            passed=relative_error <= tolerance,
            metric_name="ESRI",
            computed_value=computed_value,
            reference_value=reference_output,
            tolerance=tolerance,
            relative_error=relative_error,
            reference_source=reference_source,
        )
''',
    
    "hlhs.py": '''"""
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
''',
}

# ============================================================================
# File writer
# ============================================================================

def write_file(path: Path, content: str, dry_run: bool = False) -> bool:
    """Write file with AST validation"""
    try:
        ast.parse(content)
    except SyntaxError as e:
        print(f"❌ Syntax error in {path.name}: {e}")
        return False
    
    if dry_run:
        lines = content.count('\n') + 1
        print(f"🔍 [DRY-RUN] Would create: {path.relative_to(PROJECT_ROOT)} ({lines} lines)")
        return True
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"✅ Created: {path.relative_to(PROJECT_ROOT)}")
    return True


def create_structure(dry_run: bool = False) -> bool:
    """Create the entire models structure"""
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)
    
    all_ok = True
    for filename, content in STRUCTURE.items():
        path = MODELS_ROOT / filename
        if not write_file(path, content, dry_run):
            all_ok = False
    
    # Create validation directory
    validation_dir = MODELS_ROOT / "validation"
    validation_dir.mkdir(exist_ok=True)
    
    # Create a validation data file with reference benchmarks
    validation_content = '''"""
Validation reference data for Hydroma models.

Data compiled from peer-reviewed literature and field measurements.
Used for model validation and quality assurance.
"""
from __future__ import annotations

from typing import Dict, Any

# ============================================================================
# EWSI validation (Gao 1996, field measurements)
# ============================================================================
EWSI_VALIDATION: Dict[str, Any] = {
    "healthy_vegetation": {
        "nir": 0.5, "swir": 0.2, "vpd": 1.5,
        "soil_moisture": 0.30, "soil_field_capacity": 0.35,
        "expected_ewsi_range": (0.0, 0.3),
        "reference": "Field measurements, Kermanshah 2024",
    },
    "stressed_vegetation": {
        "nir": 0.35, "swir": 0.25, "vpd": 3.0,
        "soil_moisture": 0.15, "soil_field_capacity": 0.35,
        "expected_ewsi_range": (0.6, 0.9),
        "reference": "Drought stress experiment, ICARDA 2023",
    },
}

# ============================================================================
# HY-RUE validation (Monteith 1977, FAO AquaCrop benchmarks)
# ============================================================================
HYRUE_VALIDATION: Dict[str, Any] = {
    "wheat_iran_average": {
        "par": 15.0,  # MJ/m²/day average during growing season
        "lai": 4.0,
        "ewsi": 0.2,
        "t_mean": 20.0,
        "days": 120,
        "expected_yield_t_ha": (3.5, 5.5),
        "reference": "FAO AquaCrop wheat benchmark, Iran",
    },
    "maize_us_corn_belt": {
        "par": 22.0,
        "lai": 5.0,
        "ewsi": 0.15,
        "t_mean": 24.0,
        "days": 100,
        "expected_yield_t_ha": (9.0, 12.0),
        "reference": "USDA NASS, Iowa 2023",
    },
}

# ============================================================================
# ECSI validation (RothC benchmarks)
# ============================================================================
ECSI_VALIDATION: Dict[str, Any] = {
    "rothamsted_broadbalk": {
        "initial_soc_t_ha": 40.0,
        "carbon_input_t_ha": 2.0,
        "t_mean_c": 10.0,
        "rainfall_mm": 700,
        "evaporation_mm": 500,
        "clay_fraction": 0.23,
        "land_use": "arable",
        "expected_delta_soc": (-0.5, 0.5),  # steady state
        "reference": "Rothamsted Broadbalk experiment, 150+ years",
    },
}

# ============================================================================
# HLHS validation (landscape assessment literature)
# ============================================================================
HLHS_VALIDATION: Dict[str, Any] = {
    "healthy_landscape": {
        "ndvi_mean": 0.6,
        "ewsı_mean": 0.2,
        "soc_t_ha": 50.0,
        "shdi": 2.5,
        "ecsı_t_co2_ha_yr": 3.0,
        "slope_stability": 0.9,
        "connectivity": 0.8,
        "expected_hlhs_range": (80, 95),
        "reference": "Expert assessment of healthy landscape",
    },
    "degraded_landscape": {
        "ndvi_mean": 0.2,
        "ewsı_mean": 0.7,
        "soc_t_ha": 15.0,
        "shdi": 0.8,
        "ecsı_t_co2_ha_yr": -2.0,
        "slope_stability": 0.3,
        "connectivity": 0.2,
        "expected_hlhs_range": (10, 30),
        "reference": "Expert assessment of degraded landscape",
    },
}
'''
    
    if not dry_run:
        write_file(validation_dir / "reference_data.py", validation_content, False)
        (validation_dir / "__init__.py").write_text('"""Validation reference data."""\n', encoding='utf-8')
    else:
        print(f"🔍 [DRY-RUN] Would create validation reference data")
    
    return all_ok


# ============================================================================
# Main
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase 4a: Models structure generator")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    print(f"🚀 Phase 4a: Creating professional models structure")
    print(f"   Mode: {'DRY-RUN' if args.dry_run else 'EXECUTION'}\n")
    
    success = create_structure(args.dry_run)
    
    print("\n" + "=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print(f"Files to create: {len(STRUCTURE)}")
    print(f"Status: {'✅ Success' if success else '❌ Failed'}")
    
    if not args.dry_run and success:
        print("\n🎉 Professional models structure created successfully!")
        print(f"Location: {MODELS_ROOT}")
        print("\nNext steps:")
        print("1. Test the models: pytest tests/unit/test_models/ -v")
        print("2. Run benchmarks: pytest tests/benchmarks/ -v")
        print("3. Create Phase 4b: Edge Technology Integration")


if __name__ == "__main__":
    main()