"""Sensitivity analysis for HY-RUE model inputs.

Implements a one-at-a-time (OAT) sensitivity analysis: each input
parameter is varied around a baseline value while all others are held
constant, and the effect on the model output (seasonal yield) is measured.

The analysis is **independent** of the HYRUE model's internal structure —
it only requires a callable that takes the same inputs as
:meth:`HYRUE.compute` and returns a dict with ``yield_t_ha``.

Provenance: evaluation_utility (not a scientific model).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SensitivityResult:
    """Result of a sensitivity analysis on one parameter."""

    parameter_name: str
    baseline_value: float
    perturbed_values: list[float]
    baseline_output: float
    perturbed_outputs: list[float]
    sensitivity_coefficients: list[float]
    max_delta: float
    max_relative_sensitivity: float | None
    method: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter_name,
            "baseline_value": self.baseline_value,
            "perturbation_values": self.perturbed_values,
            "baseline_output": self.baseline_output,
            "perturbed_outputs": self.perturbed_outputs,
            "sensitivity_coefficients": self.sensitivity_coefficients,
            "max_delta": self.max_delta,
            "max_relative_sensitivity": self.max_relative_sensitivity,
            "method": self.method,
        }


@dataclass
class SensitivityAnalysisReport:
    """Complete sensitivity analysis report for multiple parameters."""

    results: list[SensitivityResult]
    model_name: str
    baseline_output: float
    notes: str = ""

    def rank_by_sensitivity(self) -> list[SensitivityResult]:
        """Return results ranked by max relative sensitivity (descending)."""
        return sorted(
            self.results,
            key=lambda r: r.max_relative_sensitivity or 0.0,
            reverse=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "baseline_output": self.baseline_output,
            "parameters_analyzed": [r.parameter_name for r in self.results],
            "ranked_by_sensitivity": [
                r.to_dict() for r in self.rank_by_sensitivity()
            ],
            "notes": self.notes,
        }


def _sensitivity_coefficient(
    output: float, baseline_output: float, delta_input: float, baseline_input: float
) -> float:
    """Compute normalised sensitivity coefficient.

    S = (dOutput / Output) / (dInput / Input)
      = (delta_output / baseline_output) / (delta_input / baseline_input)
    """
    if baseline_output == 0 or baseline_input == 0:
        return 0.0
    return (output - baseline_output) / baseline_output / (
        delta_input / baseline_input if delta_input != 0 else 1.0
    )


def oat_sensitivity(
    model_fn: Callable[..., dict[str, Any]],
    baseline_inputs: dict[str, Any],
    param_spec: dict[str, tuple[float, list[float]]],
    output_key: str = "yield_t_ha",
    relative: bool = True,
) -> SensitivityAnalysisReport:
    """Run one-at-a-time sensitivity analysis.

    Args:
        model_fn: Callable that accepts keyword arguments matching
            ``baseline_inputs`` and returns a dict with the ``output_key``.
        baseline_inputs: Dict of input name -> baseline value.
        param_spec: Dict mapping parameter name to
            ``(baseline_value, perturbation_list)``.
        output_key: Key to extract from the model's return dict.
        relative: If True, also compute max_relative_sensitivity.

    Returns:
        A :class:`SensitivityAnalysisReport`.
    """
    model_name = model_fn.__name__ if hasattr(model_fn, "__name__") else "unknown"

    baseline_result = model_fn(**baseline_inputs)
    baseline_output = float(np.mean(baseline_result[output_key]))

    results: list[SensitivityResult] = []

    for param_name, (baseline_val, perturbations) in param_spec.items():
        perturbed_outputs: list[float] = []
        sensitivity_coeffs: list[float] = []

        for pert_val in perturbations:
            mod_inputs = dict(baseline_inputs)
            mod_inputs[param_name] = pert_val
            result = model_fn(**mod_inputs)
            out = float(np.mean(result[output_key]))
            perturbed_outputs.append(out)

            coeffs = _sensitivity_coefficient(
                out, baseline_output, pert_val, baseline_val
            )
            sensitivity_coeffs.append(coeffs)

        deltas = [abs(o - baseline_output) for o in perturbed_outputs]
        max_delta = max(deltas) if deltas else 0.0

        if relative:
            rel_sens = [
                abs(c) for c in sensitivity_coeffs if c != 0.0
            ]
            max_rel_sens = max(rel_sens) if rel_sens else 0.0
        else:
            max_rel_sens = None

        results.append(
            SensitivityResult(
                parameter_name=param_name,
                baseline_value=baseline_val,
                perturbed_values=perturbations,
                baseline_output=baseline_output,
                perturbed_outputs=perturbed_outputs,
                sensitivity_coefficients=sensitivity_coeffs,
                max_delta=max_delta,
                max_relative_sensitivity=max_rel_sens,
                method="one-at-a-time (OAT)",
                notes=f"Baseline {param_name}={baseline_val}",
            )
        )

    return SensitivityAnalysisReport(
        results=results,
        model_name=model_name,
        baseline_output=baseline_output,
        notes="One-at-a-time sensitivity analysis. Each parameter perturbed "
        "independently while others held at baseline.",
    )


def seasonal_sensitivity(
    par: np.ndarray,
    lai: np.ndarray,
    ewsi: np.ndarray,
    t_mean: np.ndarray,
    crop: str = "wheat",
    par_fractions: Sequence[float] = (0.8, 1.0, 1.2),
    lai_fractions: Sequence[float] = (0.8, 1.0, 1.2),
    ewsi_offsets: Sequence[float] = (-0.1, 0.0, 0.1),
    t_offsets: Sequence[float] = (-5.0, 0.0, 5.0),
) -> SensitivityAnalysisReport:
    """Run OAT sensitivity for HYRUE seasonal inputs.

    Each parameter group is perturbed from the full-season baseline arrays:
    - PAR: multiplied by fraction factors
    - LAI: multiplied by fraction factors
    - EWSI: offset added (clipped to [0, 1])
    - T_mean: offset added (°C)

    Args:
        par: Daily PAR array (MJ/m²/day).
        lai: Daily LAI array.
        ewsi: Daily EWSI array [0, 1].
        t_mean: Daily mean temperature array (°C).
        crop: Crop name for HYRUE params.
        par_fractions: Multipliers for PAR sensitivity.
        lai_fractions: Multipliers for LAI sensitivity.
        ewsi_offsets: Additive offsets for EWSI.
        t_offsets: Additive offsets for temperature (°C).

    Returns:
        A :class:`SensitivityAnalysisReport`.
    """
    from engine.hydroma.models.hyrue import HYRUE

    model = HYRUE(crop=crop)

    baseline_inputs: dict[str, Any] = {
        "par": np.asarray(par, dtype=float),
        "lai": np.asarray(lai, dtype=float),
        "ewsi": np.asarray(ewsi, dtype=float),
        "t_mean": np.asarray(t_mean, dtype=float),
    }

    def model_fn(par, lai, ewsi, t_mean):
        return model.compute(par=par, lai=lai, ewsi=ewsi, t_mean=t_mean)

    param_spec: dict[str, tuple[float, list[float]]] = {}

    par_base = float(np.mean(par))
    param_spec["par"] = (
        par_base,
        [par_base * f for f in par_fractions],
    )

    lai_base = float(np.mean(lai))
    param_spec["lai"] = (
        lai_base,
        [lai_base * f for f in lai_fractions],
    )

    ewsi_base = float(np.mean(ewsi))
    ewsi_perturbed = [np.clip(ewsi + off, 0, 1) for off in ewsi_offsets]
    # Use scalar offset for sensitivity coefficient computation
    param_spec["ewsi"] = (
        ewsi_base,
        [float(np.mean(e)) for e in ewsi_perturbed],
    )
    # Store the full array perturbations for the model_fn
    param_spec["_ewsi_arrays"] = (ewsi_base, ewsi_perturbed)

    t_base = float(np.mean(t_mean))
    param_spec["t_mean"] = (
        t_base,
        [t_base + off for off in t_offsets],
    )

    # Run with modified perturbation handling for EWSI arrays
    baseline_result = model_fn(**baseline_inputs)
    baseline_output = float(np.mean(baseline_result["yield_t_ha"]))

    results: list[SensitivityResult] = []
    model_name = "HYRUE"

    for param_name in ["par", "lai", "t_mean", "ewsi"]:
        baseline_val, perturbations = param_spec[param_name]

        perturbed_outputs: list[float] = []
        sensitivity_coeffs: list[float] = []

        for i, pert_val in enumerate(perturbations):
            mod_inputs = dict(baseline_inputs)
            if param_name == "par":
                mod_inputs["par"] = np.asarray(par, dtype=float) * (
                    pert_val / par_base if par_base != 0 else 1.0
                )
            elif param_name == "lai":
                mod_inputs["lai"] = np.asarray(lai, dtype=float) * (
                    pert_val / lai_base if lai_base != 0 else 1.0
                )
            elif param_name == "t_mean":
                mod_inputs["t_mean"] = np.asarray(t_mean, dtype=float) + (
                    pert_val - t_base
                )
            elif param_name == "ewsi":
                mod_inputs["ewsi"] = np.asarray(
                    param_spec["_ewsi_arrays"][1][i], dtype=float
                )

            result = model_fn(**mod_inputs)
            out = float(np.mean(result["yield_t_ha"]))
            perturbed_outputs.append(out)

            coeffs = _sensitivity_coefficient(
                out, baseline_output, pert_val, baseline_val
            )
            sensitivity_coeffs.append(coeffs)

        deltas = [abs(o - baseline_output) for o in perturbed_outputs]
        max_delta = max(deltas) if deltas else 0.0

        rel_sens = [abs(c) for c in sensitivity_coeffs if c != 0.0]
        max_rel_sens = max(rel_sens) if rel_sens else 0.0

        results.append(
            SensitivityResult(
                parameter_name=param_name,
                baseline_value=baseline_val,
                perturbed_values=perturbations,
                baseline_output=baseline_output,
                perturbed_outputs=perturbed_outputs,
                sensitivity_coefficients=sensitivity_coeffs,
                max_delta=max_delta,
                max_relative_sensitivity=max_rel_sens,
                method="one-at-a-time (OAT)",
                notes=f"Baseline mean {param_name}={baseline_val:.4f}",
            )
        )

    return SensitivityAnalysisReport(
        results=results,
        model_name=model_name,
        baseline_output=baseline_output,
        notes="One-at-a-time sensitivity for HYRUE seasonal mode. "
        "PAR and LAI perturbed by multiplicative factors; EWSI by additive "
        "offsets (clipped to [0,1]); T_mean by additive °C offsets.",
    )