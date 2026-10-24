"""Scenario tracking and uncertainty quantification for HY-RUE predictions.

Defines:
    - :class:`Scenario` — a description of an alternative input scenario.
    - :class:`ScenarioResult` — the prediction output for that scenario.
    - :class:`UncertaintyReport` — aggregated uncertainty across scenarios.
    - :func:`run_scenarios` — execute HYRUE under multiple input configurations.

This module is import-safe: depends on numpy, pydantic-adjacent dataclasses,
and the eval layer — no service or network imports.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np

from engine.hydroma.eval.prediction import PredictionResult


class UncertaintyMethod(StrEnum):
    """Method used to derive a prediction interval."""

    ENSEMBLE_RANGE = "ensemble_range"
    BOOTSTRAP = "bootstrap"
    MONTE_CARLO = "monte_carlo"
    PARAMETRIC = "parametric"
    SCENARIO_SPREAD = "scenario_spread"
    NONE = "none"


@dataclass
class Scenario:
    """A description of an alternative model-input scenario.

    Attributes:
        scenario_id: Unique identifier for the scenario.
        name: Human-readable name.
        description: What changes in this scenario.
        input_source_config: Dict describing the input data source configuration
            (e.g. ``{"par": "satellite_retrieved", "lai": "model_generated"}``).
        par_source: Which PAR source to use (overrides default).
        lai_source: Which LAI source to use.
        ewsi_source: Which EWSI source to use.
        shortwave_source: Which shortwave source to use.
        climate_priors: Optional override climate priors for the scenario.
        metadata: Additional scenario metadata.
    """

    scenario_id: str
    name: str
    description: str = ""
    input_source_config: dict[str, str] = field(default_factory=dict)
    par_source: str | None = None
    lai_source: str | None = None
    ewsi_source: str | None = None
    shortwave_source: str | None = None
    climate_priors: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ScenarioResult:
    """The prediction output for a single scenario.

    Attributes:
        scenario: The :class:`Scenario` that was run.
        prediction: The :class:`PredictionResult` produced.
        input_source_used: The input source configuration actually used.
        uncertainty_method: Which uncertainty method applies (if any).
        prediction_interval: (lower, upper) tuple, or None.
        metadata: Additional metadata about how the scenario was computed.
    """

    scenario: Scenario
    prediction: PredictionResult
    input_source_used: dict[str, str]
    uncertainty_method: str = UncertaintyMethod.NONE.value
    prediction_interval: tuple[float, float] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class UncertaintyReport:
    """Aggregated uncertainty across multiple scenario results.

    Attributes:
        scenario_results: All scenario results.
        central_value: The median (or mean) prediction across scenarios.
        uncertainty_method: The method used to derive intervals.
        prediction_interval_lower: Lower bound.
        prediction_interval_upper: Upper bound.
        std_dev: Standard deviation across scenario predictions.
        coefficient_of_variation: |std| / |mean|.
        n_scenarios: Number of scenarios contributing.
        spread_range: Max - min across scenarios.
    """

    scenario_results: list[ScenarioResult]
    central_value: float | None = None
    uncertainty_method: str = UncertaintyMethod.SCENARIO_SPREAD.value
    prediction_interval_lower: float | None = None
    prediction_interval_upper: float | None = None
    std_dev: float | None = None
    coefficient_of_variation: float | None = None
    n_scenarios: int = 0
    spread_range: float | None = None
    metadata: dict[str, Any] | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "n_scenarios": self.n_scenarios,
            "central_value": self.central_value,
            "uncertainty_method": self.uncertainty_method,
            "prediction_interval": (
                self.prediction_interval_lower,
                self.prediction_interval_upper,
            ),
            "std_dev": self.std_dev,
            "coefficient_of_variation": self.coefficient_of_variation,
            "spread_range": self.spread_range,
        }


def run_scenarios(
    scenarios: Sequence[Scenario],
    prediction_fn: Any,
    *,
    uncertainty_method: str = UncertaintyMethod.SCENARIO_SPREAD.value,
) -> list[ScenarioResult]:
    """Execute HYRUE under each scenario and collect results.

    Parameters
    ----------
    scenarios:
        Ordered list of :class:`Scenario` objects.
    prediction_fn:
        A callable that accepts keyword arguments from the scenario's
        ``input_source_config`` and returns a :class:`PredictionResult`.
        Signature: ``prediction_fn(**scenario.input_source_config) -> PredictionResult``.
    uncertainty_method:
        Label recorded in each :class:`ScenarioResult`.

    Returns:
        List of :class:`ScenarioResult`, one per scenario.
    """
    results: list[ScenarioResult] = []

    for scenario in scenarios:
        config = dict(scenario.input_source_config or {})

        if scenario.par_source is not None:
            config["par_source"] = scenario.par_source
        if scenario.lai_source is not None:
            config["lai_source"] = scenario.lai_source
        if scenario.ewsi_source is not None:
            config["ewsi_source"] = scenario.ewsi_source
        if scenario.shortwave_source is not None:
            config["shortwave_source"] = scenario.shortwave_source
        if scenario.climate_priors is not None:
            config["climate_priors"] = scenario.climate_priors

        prediction = prediction_fn(**config)

        results.append(
            ScenarioResult(
                scenario=scenario,
                prediction=prediction,
                input_source_used=config,
                uncertainty_method=uncertainty_method,
                prediction_interval=None,
            )
        )

    return results


def aggregate_uncertainty(
    scenario_results: Sequence[ScenarioResult],
    *,
    method: str = UncertaintyMethod.SCENARIO_SPREAD.value,
    ci_percentile: float = 95.0,
) -> UncertaintyReport:
    """Aggregate scenario results into an :class:`UncertaintyReport`.

    Parameters
    ----------
    scenario_results:
        Output of :func:`run_scenarios`.
    method:
        Label for the uncertainty methodology used.
    ci_percentile:
        For ``method="percentile"``, use this percentile to derive the
        symmetric prediction interval. Default 95 %.
    """
    values: list[float] = []
    for sr in scenario_results:
        if sr.prediction.value is not None:
            values.append(sr.prediction.value)

    if not values:
        return UncertaintyReport(
            scenario_results=list(scenario_results),
            uncertainty_method=method,
            n_scenarios=len(scenario_results),
        )

    arr = np.array(values, dtype=float)
    n = len(arr)
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    cv = abs(std_val / mean_val) if mean_val != 0 else float("inf")
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    spread = max_val - min_val

    if method == "percentile":
        alpha = (100 - ci_percentile) / 2.0
        lower = float(np.percentile(arr, alpha))
        upper = float(np.percentile(arr, 100 - alpha))
    else:
        half = 1.96 * std_val if std_val > 0 else 0.0
        lower = mean_val - half
        upper = mean_val + half

    return UncertaintyReport(
        scenario_results=list(scenario_results),
        central_value=mean_val,
        uncertainty_method=method,
        prediction_interval_lower=lower,
        prediction_interval_upper=upper,
        std_dev=std_val,
        coefficient_of_variation=cv,
        n_scenarios=n,
        spread_range=spread,
        metadata={"ci_percentile": ci_percentile, "values": list(values)},
    )


def _lai_source(base_prediction: PredictionResult) -> str:
    """Extract LAI source label from a prediction's provenance dict."""
    provenance = base_prediction.lai_provenance
    if not provenance:
        return "model_generated"
    return provenance.get("source_model", "model_generated")


def build_default_scenarios(
    base_prediction: PredictionResult,
    *,
    par_sources: Sequence[str] = ("satellite_retrieved", "analysis_product", "estimated"),
    lai_sources: Sequence[str] = ("field_measured", "satellite_retrieved", "model_generated"),
    ewsi_sources: Sequence[str] = ("field_measured", "model_generated"),
) -> list[Scenario]:
    """Build a grid of input-source scenarios around a base prediction.

    Each scenario varies one input source at a time (OAT) plus the all-satellite
    combination, so the spread isolates which input contributes most to
    prediction uncertainty.
    """
    scenarios: list[Scenario] = []
    idx = 0

    for par_src in par_sources:
        idx += 1
        scenarios.append(
            Scenario(
                scenario_id=f"S{idx:03d}",
                name=f"PAR_source_{par_src}",
                description=f"PAR sourced from {par_src}, other inputs at baseline",
                input_source_config={
                    "par_source": par_src,
                    "lai_source": _lai_source(base_prediction),
                    "ewsi_source": "model_generated",
                },
                par_source=par_src,
            )
        )

    for lai_src in lai_sources:
        idx += 1
        scenarios.append(
            Scenario(
                scenario_id=f"S{idx:03d}",
                name=f"LAI_source_{lai_src}",
                description=f"LAI sourced from {lai_src}, other inputs at baseline",
                input_source_config={
                    "par_source": base_prediction.par_provenance or "satellite_retrieved",
                    "lai_source": lai_src,
                    "ewsi_source": "model_generated",
                },
                lai_source=lai_src,
            )
        )

    for ewsi_src in ewsi_sources:
        idx += 1
        scenarios.append(
            Scenario(
                scenario_id=f"S{idx:03d}",
                name=f"EWSI_source_{ewsi_src}",
                description=f"EWSI sourced from {ewsi_src}, other inputs at baseline",
                input_source_config={
                    "par_source": base_prediction.par_provenance or "satellite_retrieved",
                    "lai_source": "model_generated",
                    "ewsi_source": ewsi_src,
                },
                ewsi_source=ewsi_src,
            )
        )

    idx += 1
    scenarios.append(
        Scenario(
            scenario_id=f"S{idx:03d}",
            name="all_satellite",
            description="All inputs from satellite/gridded products",
            input_source_config={
                "par_source": "satellite_retrieved",
                "lai_source": "satellite_retrieved",
                "ewsi_source": "model_generated",
            },
        )
    )

    return scenarios
