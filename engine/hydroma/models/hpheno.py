"""
H-Pheno — Hydroma Phenology Detection

Savitzky-Golay smoothing + derivative analysis for NDVI time series.

Reference: Zhang et al. (2003), White et al. (2009)
"""

from __future__ import annotations

from datetime import date
from typing import Any, ClassVar

import numpy as np

from .base import ScientificModel, ValidationResult, validate_finite


class HPheno(ScientificModel):
    """Hydroma Phenology Detection"""

    name = "H-Pheno"
    version = "1.0.0"
    description = "Phenology detection from NDVI time-series"

    REFERENCES: ClassVar[dict] = {
        "Zhang2003": "Zhang et al. (2003). Monitoring vegetation phenology using MODIS.",
        "White2009": "White et al. (2009). Derivation of phenological metrics from MODIS NDVI.",
    }

    def validate_inputs(
        self,
        ndvi_ts: np.ndarray,
        dates: list[date],
    ) -> tuple[bool, list[str]]:
        errors = validate_finite(
            "HPHENO",
            {"ndvi_ts": ndvi_ts},
        )
        if errors:
            return False, errors
        if len(ndvi_ts) != len(dates):
            errors.append("NDVI and dates arrays must have same length")
        if len(ndvi_ts) < 12:
            errors.append("Need at least 12 observations")
        if np.any((ndvi_ts < -1) | (ndvi_ts > 1)):
            errors.append("NDVI out of range [-1, 1]")
        return len(errors) == 0, errors

    @staticmethod
    def savgol_coefficients(window: int, polyorder: int) -> np.ndarray:
        """Savitzky-Golay convolution kernel of length ``window``.

        A local polynomial least-squares fit evaluated at the window centre is a
        linear operation, so the whole filter is one convolution with the centre
        row of the pseudo-inverse of the window's Vandermonde matrix. That kernel
        depends only on (window, polyorder) and is computed once.

        Implemented here rather than imported from scipy so the method does not
        change with the environment. The previous version called
        ``scipy.signal.savgol_filter`` and, when scipy was absent, fell back to
        ``np.convolve(..., mode="same")`` -- a centred moving average. A moving
        average has no derivative-preserving property, so every downstream
        zero-crossing and ``np.gradient`` silently changed meaning depending on
        whether an optional dependency happened to be installed.
        """
        if window % 2 == 0:
            raise ValueError(f"Savitzky-Golay window must be odd, got {window}")
        if polyorder >= window:
            raise ValueError(f"polyorder {polyorder} must be less than the window {window}")
        half = window // 2
        x = np.arange(-half, half + 1, dtype=float)
        # A = design matrix, rows are the offsets, columns the powers.
        a = np.vander(x, polyorder + 1, increasing=True)
        # Row 0 of the pseudo-inverse evaluates the fitted polynomial at x = 0.
        coeffs = np.linalg.pinv(a)[0]
        return np.flip(coeffs)  # correlate, matching convolve semantics

    @staticmethod
    def smooth(ndvi: np.ndarray, window: int = 11, polyorder: int = 3) -> np.ndarray:
        """Savitzky-Golay smoothing.

        The window is clamped to an odd value that leaves room for the requested
        polynomial order, so the result no longer depends on the series length
        being odd or even. The previous expression
        ``min(window, len(ndvi) - 1 if len(ndvi) % 2 == 0 else len(ndvi))``
        could produce an even window, which scipy rejects, and could reduce the
        window to 3 with the default ``polyorder=3``, which scipy also rejects --
        raising a ValueError that the ``except ImportError`` did not catch.
        """
        data = np.asarray(ndvi, dtype=float)
        n = data.size
        if n == 0:
            return data

        # Shrink an over-long or badly ordered request into something valid.
        window = min(int(window), n if n % 2 else n - 1)
        if window % 2 == 0:
            window -= 1
        window = max(window, 3)
        polyorder = min(int(polyorder), window - 1)

        if window <= 2 or polyorder < 1:
            return data

        coeffs = HPheno.savgol_coefficients(window, polyorder)
        half = window // 2

        # Reflect at the edges so the endpoints are not pulled toward zero, then
        # apply the kernel and crop back to the original length.
        padded = np.pad(data, (half, half), mode="reflect")
        smoothed = np.convolve(padded, coeffs, mode="valid")
        return smoothed[:n]

    @staticmethod
    def derivative(ndvi: np.ndarray, dt_days: float = 5.0) -> np.ndarray:
        """First derivative"""
        return np.gradient(ndvi, dt_days)

    def compute(
        self,
        ndvi_ts: np.ndarray,
        dates: list[date],
        dt_days: float = 5.0,
        ndvi_threshold: float = 0.15,
    ) -> dict[str, Any]:
        """Detect phenological stages"""
        ndvi_smooth = self.smooth(ndvi_ts)
        ndvi_prime = self.derivative(ndvi_smooth, dt_days)

        # SOS: first positive zero-crossing with NDVI above threshold
        sos_idx = None
        for i in range(1, len(ndvi_prime)):
            if ndvi_prime[i - 1] <= 0 < ndvi_prime[i] and ndvi_smooth[i] > ndvi_threshold:
                sos_idx = i
                break

        # POS: maximum of NDVI
        pos_idx = int(np.argmax(ndvi_smooth))

        # EOS: first negative zero-crossing after POS
        eos_idx = None
        for i in range(pos_idx + 1, len(ndvi_prime)):
            if ndvi_prime[i - 1] >= 0 > ndvi_prime[i] and ndvi_smooth[i] > ndvi_threshold:
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
        self,
        inputs: dict[str, Any],
        reference_output: float,
        reference_source: str,
        tolerance: float = 15.0,
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
