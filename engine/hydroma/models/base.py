"""
Base classes for Hydroma scientific models.

All scientific models must inherit from ScientificModel and implement:
- validate_inputs()
- compute()
- validate_against_reference()
- uncertainty_quantification()
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar

import numpy as np

from engine.hydroma.provenance import DataSource


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


@dataclass
class ModelInput:
    """Inputs handed to a model, keyed by name.

    The expansion models -- MODFLOW6, SWAT+, the Gaussian-process surrogate and
    the PINN -- all construct a ``ModelInput`` and return a ``ModelOutput``, but
    neither type was ever defined. Because the modules use
    ``from __future__ import annotations``, the missing annotation on the return
    type was invisible at import and the failure only appeared at run time as
    ``NameError`` on the first line of real work.

    A mapping wrapper rather than a field per input, because the set of inputs
    differs per model and a shared schema would either be a lowest-common-
    denominator or a large union that validates nothing.
    """

    values: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.values[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self.values

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def items(self):
        return self.values.items()

    def keys(self):
        return self.values.keys()


#: Below this magnitude a reference carries no relative information, so the
#: tolerance test falls back to an absolute comparison. See
#: ``ModelOutput.is_within_tolerance``.
_ABSOLUTE_FLOOR = 1e-9


def non_finite_fields(values: dict[str, Any]) -> list[str]:
    """Names of the inputs that carry a NaN or an infinity.

    Every range check in this repository is written as ``if x < lo or x > hi``.
    In Python each comparison against NaN is False, so ``nan < 0`` is False and
    ``nan > hi`` is False: a NaN passes every bound and reaches the arithmetic,
    where it silently poisons the whole result. The same is true of an
    infinity, which passes an upper bound it exceeds only if the bound is
    itself infinite.

    This is the one guard a model cannot forget, because every model calls it.
    """

    def _bad(value: Any) -> bool:
        if isinstance(value, (str, bytes, bool)):
            return False
        if isinstance(value, np.ndarray):
            return bool(value.dtype.kind in "fc" and not np.all(np.isfinite(value)))
        if isinstance(value, (int, float, np.integer, np.floating)):
            return not bool(np.isfinite(value))
        return False

    return [name for name, value in values.items() if _bad(value)]


def validate_finite(model_name: str, values: dict[str, Any]) -> list[str]:
    """The errors every model's validate_inputs must start with.

    Returns one message per offending input. Callers append their own
    range checks after this, so a NaN produces a clear complaint rather than
    a silent wrong answer.
    """
    return [
        f"{model_name}: {name} must be finite, got {value!r}"
        for name, value in values.items()
        if name in non_finite_fields(values)
    ]


def relative_error_of(computed: float, reference: float) -> float:
    """Relative error, guarded against a zero or near-zero reference.

    The unguarded form divides by the reference, so a model that correctly
    returns no growth, or no decomposition, reports an enormous error for a
    right answer. When the reference carries no scale, the absolute
    difference is the only meaningful number and is returned directly.
    """
    scale = abs(reference)
    if scale <= _ABSOLUTE_FLOOR:
        return abs(computed - reference)
    return abs(computed - reference) / scale


@dataclass
class ModelOutput:
    """A model's result, with the provenance needed to tell a real answer from a
    fabricated one.

    ``data_source`` and ``model`` are not decoration. Several models in this
    codebase can return a plausible number without running: a solver falls back to
    a mock, a surrogate returns noise, and nothing about the returned value
    distinguishes that from a real result. Requiring both fields here makes the
    distinction impossible to omit, and a caller can check it without knowing
    which model it is talking to.
    """

    # Required, and with no default. The docstring above asks for exactly this
    # and the two lines that used to sit here defeated it: `data_source: str =
    # "simulated"` let any of the twenty call sites omit the label while
    # returning a measured number, and `str` accepted any value at all, so a
    # typo was a query that matched nothing rather than a validation error.
    #
    # `computed` is separate from `data_source` because the two answer different
    # questions. A number can be computed from live sensor data and still be
    # fabricated, and a number can be entirely internal and still be honest.
    #
    # Order matters: every non-default field must precede every defaulted one.
    data_source: DataSource
    model: str
    success: bool | None = None
    outputs: dict[str, Any] = field(default_factory=dict)
    uncertainty: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.outputs[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.outputs.get(key, default)

    def items(self):
        return self.outputs.items()

    def __contains__(self, key: object) -> bool:
        return key in self.outputs

    notes: str = ""

    @property
    def is_within_tolerance(self) -> bool:
        # A relative test divides by the reference. When the reference is
        # zero or near zero that division explodes, so a model that correctly
        # returns no growth (HYRUE outside its temperature band) or no
        # decomposition was reported as a failure. An absolute floor makes the
        # comparison meaningful for a quantity that is legitimately zero, and
        # the relative test still applies everywhere it can.
        absolute_error = abs(self.computed_value - self.reference_value)
        scale = abs(self.reference_value)
        if scale <= _ABSOLUTE_FLOOR:
            return absolute_error <= max(self.tolerance, _ABSOLUTE_FLOOR)
        return (absolute_error / scale) <= self.tolerance


def unavailable_output(
    model: str,
    reason: str,
    *,
    missing: str = "",
    remedy: str = "",
) -> ModelOutput:
    """A ``ModelOutput`` that says a model did not run, and why.

    Several models in this repository can produce a number without the
    component that gives the number meaning: MODFLOW 6 without flopy, the GP
    surrogate without gpytorch, an adapter whose optional import failed. Before
    this helper each of them invented a plausible result and labelled it
    ``modelled``, which is the failure ``S-HONEST`` exists to prevent.

    The three properties that matter:

    - ``data_source`` is ``"unavailable"``, never ``"modelled"``. A caller
      filtering on provenance now sees the difference.
    - ``success`` stays ``True``. The call did not raise, and turning a
      capability gap into an exception would break callers that already handle
      an empty result. ``success`` was never the honest signal; the label is.
    - ``outputs`` is empty and ``notes`` names what is missing and what to
      install, so a reader can act on it.
    """

    notes = reason
    if missing:
        notes += f" Missing: {missing}."
    if remedy:
        notes += f" To enable: {remedy}."
    return ModelOutput(
        success=True,
        outputs={},
        uncertainty={},
        data_source="unavailable",
        model=model,
        notes=notes.strip(),
    )


def compute_checked(model: ScientificModel, **inputs: Any) -> Any:
    """Run a model's ``compute`` after checking its inputs.

    Seven of the eight models in this package have a ``compute`` that never
    calls its own ``validate_inputs``, so the checks that were written for
    them are optional. That makes a silent wrong answer reachable from the
    public API: pass an out-of-range value, or a NaN, and the model returns a
    number anyway.

    The checks exist; nothing forced anyone to run them. This function is the
    way to run them without changing any model's signature, and it is what a
    caller should use unless they have a reason to skip validation.

    ECSI already validates inside ``compute`` and is unaffected.
    """

    accepted = {
        name for name in inspect.signature(type(model).validate_inputs).parameters if name != "self"
    }
    ok, problems = model.validate_inputs(**{k: v for k, v in inputs.items() if k in accepted})
    if not ok:
        raise ValueError(f"{type(model).__name__}: " + "; ".join(problems))
    return model.compute(**inputs)


class ScientificModel(ABC):
    """
    کلاس پایه برای تمام مدل‌های علمی Hydroma.

    الزامات:
    - تمام ورودی‌ها باید type-hinted باشند
    - تمام محاسبات باید vectorized باشند (numpy)
    - باید validation against published data داشته باشند
    - باید uncertainty quantification ارائه دهند

    دربارهٔ اعتبارسنجی: ``validate_inputs`` عمداً فراخوانی جداگانه است تا
    یک فراخوان بتواند یک مجموعه ورودی را بدون پرداخت هزینهٔ محاسبه
    بررسی کند. همین جداسازی یعنی ``compute`` ناچار به فراخوانی آن نیست، و
    هفت مدل از هشت مدل این کار را نمی‌کنند: فراخوانی که بررسی را رد کند،
    نتیجهٔ بررسی‌نشده می‌گیرد. ``probe_robustness.py`` گزارش می‌دهد کدام
    مدل‌ها در این وضعیت‌اند.
    """

    name: str = "BaseModel"
    version: str = "1.0.0"
    description: str = "Base scientific model"

    # Reference literature for validation
    REFERENCES: ClassVar[dict[str, str]] = {}

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
        base_value = (
            float(np.mean(base_result))
            if isinstance(base_result, np.ndarray)
            else float(base_result)
        )

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
        base_value = (
            float(np.mean(base_result))
            if isinstance(base_result, np.ndarray)
            else float(base_result)
        )

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
                new_value = (
                    float(np.mean(new_result))
                    if isinstance(new_result, np.ndarray)
                    else float(new_result)
                )
                if abs(base_value) > 1e-9:
                    sensitivity = (
                        (new_value - base_value) / base_value / (perturbation_percent / 100)
                    )
                else:
                    sensitivity = 0.0
                sensitivities[param] = float(sensitivity)
            except Exception:
                sensitivities[param] = 0.0

        return sensitivities

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(version={self.version})"
