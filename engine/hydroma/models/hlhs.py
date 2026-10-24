"""
HLHS — Hydroma Landscape Health Score

Composite index for landscape fund management.
HLHS = 100 × Σ(w_i × (X_i − X_min) / (X_max − X_min))

There is no published index called the Hydroma Landscape Health Score. The
seven-component composition, all seven weights and five of the seven
normalisation bounds are this project's own.

CITATIONS REMOVED 2026-10-01. Shannon (1948) and Nagendra et al. (2002) were
attached to the `shdi` component, and Shannon's citation was attached to no
expression in the file at all: this module never computes an entropy. `shdi`
is an input, normalised by the same min-max call as the other six. What
Shannon (1948) defines -- H = −Σ p_i ln p_i over a probability distribution
of land-cover classes -- is a function of a class distribution this module
does not receive, and what Nagendra et al. (2002) discuss is the discrepancy
between the Shannon and Simpson forms of that same quantity, which also does
not appear here. Naming the two papers without an expression to attach them
to was the defect; they are recorded in the research definition instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from .base import ScientificModel, ValidationResult, validate_finite


@dataclass
class LandscapeMetrics:
    """Input metrics for HLHS calculation"""

    ndvi_mean: float = 0.0
    ewsi_mean: float = 0.0
    soc_t_ha: float = 0.0
    shdi: float = 0.0  # Shannon Diversity Index, SUPPLIED BY THE CALLER
    ecsi_t_co2_ha_yr: float = 0.0
    slope_stability: float = 0.0  # 0 to 1
    connectivity: float = 0.0  # 0 to 1

    # ``shdi`` is NOT computed here. It is a caller-supplied number and this
    # class has no land-cover distribution to compute one from. Shannon's
    # H = -sum(p_i * ln p_i) is bounded by ln(N) for N classes, so an ``shdi``
    # above ln(N) is not a Shannon entropy and belongs to whoever supplied it.
    # The `biodiversity` bound in BOUNDS is 3.0, which is ln(20.1): it silently
    # assumes a landscape of about twenty cover classes, and like the other
    # unsourced bounds it is an engineering choice, not a derivation.

    def to_dict(self) -> dict[str, float]:
        return {
            "ndvi_mean": self.ndvi_mean,
            "ewsi_mean": self.ewsi_mean,
            "soc_t_ha": self.soc_t_ha,
            "shdi": self.shdi,
            "ecsi_t_co2_ha_yr": self.ecsi_t_co2_ha_yr,
            "slope_stability": self.slope_stability,
            "connectivity": self.connectivity,
        }


class HLHS(ScientificModel):
    """Hydroma Landscape Health Score"""

    name = "HLHS"
    version = "1.0.0"
    description = "Composite Landscape Health Score for fund management"

    #: Every weight and five of the seven bounds are unsourced, and two of the
    #: seven inputs (EWSI, ECSI) are themselves project contributions. This is
    #: a composite of composites.
    PROVENANCE: ClassVar[str] = "composite"

    REFERENCES: ClassVar[dict[str, str]] = {}

    WEIGHTS: ClassVar[dict[str, float]] = {
        "vegetation": 0.20,
        "water": 0.20,
        "soil": 0.15,
        "biodiversity": 0.15,
        "carbon": 0.15,
        "topography": 0.10,
        "connectivity": 0.05,
    }

    BOUNDS: ClassVar[dict[str, Any]] = {
        "vegetation": (0.0, 0.8),
        "water": (0.0, 1.0),
        "soil": (0, 100),
        "biodiversity": (0.0, 3.0),
        "carbon": (-2, 5),
        "topography": (0, 1),
        "connectivity": (0, 1),
    }

    # The ScientificModel ABC declares **inputs / dict-based signatures; the
    # concrete model API in this package is a positional typed inputs object.
    # Unifying the two is a cross-hierarchy API decision, so the divergence is
    # marked rather than silently rewritten here.
    def validate_inputs(  # type: ignore[override]
        self, metrics: LandscapeMetrics
    ) -> tuple[bool, list[str]]:
        # A dataclass is checked field by field: a NaN in any metric compares
        # False against every range below and would otherwise reach the
        # weighted sum and turn the whole landscape score into a NaN.
        errors = validate_finite(
            "HLHS",
            {
                field: getattr(metrics, field)
                for field in (
                    "ndvi_mean",
                    "ewsi_mean",
                    "soc_t_ha",
                    "shdi",
                    "ecsi_t_co2_ha_yr",
                    "slope_stability",
                    "connectivity",
                )
            },
        )
        if errors:
            return False, errors
        if not (0 <= metrics.ndvi_mean <= 1):
            errors.append("NDVI mean out of range")
        if not (0 <= metrics.ewsi_mean <= 1):
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

    def compute(  # type: ignore[override]
        self,
        metrics: LandscapeMetrics,
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Compute HLHS"""
        w = weights or self.WEIGHTS
        b = self.BOUNDS

        components = {
            "vegetation": self.normalize(metrics.ndvi_mean, b["vegetation"][0], b["vegetation"][1]),
            "water": self.normalize(1 - metrics.ewsi_mean, 0, 1),
            "soil": self.normalize(metrics.soc_t_ha, b["soil"][0], b["soil"][1]),
            "biodiversity": self.normalize(
                metrics.shdi, b["biodiversity"][0], b["biodiversity"][1]
            ),
            "carbon": self.normalize(metrics.ecsi_t_co2_ha_yr, b["carbon"][0], b["carbon"][1]),
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
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 10.0,
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
