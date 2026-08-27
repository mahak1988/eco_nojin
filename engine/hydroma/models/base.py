"""
Base classes for Hydroma scientific models.

All scientific models must inherit from ScientificModel and implement:
- validate_inputs()
- compute()
- validate_against_reference()
- uncertainty_quantification()
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

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
    REFERENCES: dict[str, str] = {}

    def __init__(self, **config):
        self.config = config
        self._last_computation_time: float | None = None
        self._uncertainty_estimate: dict[str, Any] | None = None

    @abstractmethod
    def validate_inputs(self, **inputs) -> tuple[bool, list[str]]:
        """اعتبارسنجی ورودی‌ها قبل از محاسبه"""
        pass

    @abstractmethod
    def compute(self, **inputs) -> Any:
        """محاسبه اصلی مدل"""
        pass

    @abstractmethod
    def validate_against_reference(
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 0.1,
    ) -> ValidationResult:
        """مقایسه با داده مرجع علمی"""
        pass

    def uncertainty_quantification(
        self,
        base_inputs: dict[str, Any],
        perturbation_percent: float = 10.0,
        n_samples: int = 100,
    ) -> dict[str, Any]:
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
        base_inputs: dict[str, Any],
        parameters_to_test: list[str] | None = None,
        perturbation_percent: float = 10.0,
    ) -> dict[str, float]:
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
