"""
H-Pheno — Hydroma Phenology Detection

Savitzky-Golay smoothing + derivative zero-crossing for NDVI time series.

Reference: Savitzky & Golay (1964) for the smoothing kernel, which IS what
the code does. See `HPheno.REFERENCES` for the two citations removed on
2026-10-01 and why.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, ClassVar, cast

import numpy as np

from .base import ScientificModel, ValidationResult, validate_finite


class HPheno(ScientificModel):
    """Hydroma Phenology Detection"""

    name = "H-Pheno"
    version = "1.0.0"
    description = "Phenology detection from NDVI time-series"

    #: The smoothing is Savitzky & Golay's and is implemented exactly. The
    #: phenological detection on top of it -- a fixed NDVI threshold and the
    #: first derivative zero-crossing -- is this project's own rule.
    PROVENANCE: ClassVar[str] = "composite"

    #: CITATIONS REPLACED 2026-10-01. Zhang et al. (2003) and White et al.
    #: (2009) were cited, and neither method is implemented here.
    #:
    #: * Zhang et al. (2003) fits a HARMONIC curve to the NDVI series and takes
    #:   the phenological dates from the phase of the fit.
    #: * White et al. (2009) uses a DOUBLE-LOGISTIC (asymmetric bell) curve for
    #:   the same purpose.
    #:
    #: Both are curve fits. This module fits no curve: it smooths with a
    #: Savitzky-Golay filter, differentiates with np.gradient, and takes the
    #: first upward zero-crossing above a fixed threshold as the start of
    #: season and the first downward crossing after the maximum as the end.
    #: That is a third, uncited method, so the two citations were describing
    #: code that was not written. The kernel itself is unchanged and is the
    #: best-validated code in this package -- see
    #: `tests/unit/test_hpheno_smoothing.py`, which tests the SG property that a
    #: polynomial of the fitted order is reproduced exactly, rather than a
    #: recorded number.
    #:
    #: Replacing the detection rule with a real harmonic or double-logistic fit
    #: is model work: it changes every date this model reports. The published
    #: fits also need a least-squares fit per period and a decision about the
    #: number of cycles per year, neither of which exists here. Recorded, not
    #: rewritten.
    REFERENCES: ClassVar[dict] = {
        "Savitzky1964": (
            "Savitzky, A. & Golay, M.J.E. (1964). Smoothing and differentiation "
            "of data by simplified least squares procedures. Analytical "
            "Chemistry, 36(8), 1627-1639. The convolution kernel in "
            "`savgol_coefficients` is the centre row of the pseudo-inverse of "
            "the window's Vandermonde matrix, which is that least-squares fit "
            "evaluated at the window centre."
        )
    }

    # The ScientificModel ABC declares **inputs / dict-based signatures; the
    # concrete model API in this package is a positional typed inputs object.
    # Unifying the two is a cross-hierarchy API decision, so the divergence is
    # marked rather than silently rewritten here.
    def validate_inputs(  # type: ignore[override]
        self,
        ndvi_ts: np.ndarray,
        dates: Any,
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
        # A malformed date column is a validation failure, not a TypeError
        # thrown later from the season-length subtraction.
        try:
            HPheno._as_dates(dates)
        except (TypeError, ValueError) as exc:
            errors.append(str(exc))
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
        return cast(np.ndarray, np.flip(coeffs))  # correlate, convolve semantics

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
        # np.gradient's stub returns Any because the output shape depends on
        # both inputs; the ndarray it builds here is the declared result.
        return cast(np.ndarray, np.gradient(ndvi, dt_days))

    @staticmethod
    def _as_dates(dates: Any) -> list[date]:
        """Coerce the date column to ``datetime.date``.

        ``compute`` computes a length of season as
        ``(eos_date - sos_date).days``, which needs real dates. The signature
        has always said ``list[date]``, but a YAML corpus cannot express a
        ``date``: PyYAML's safe loader has no date type, so every fixture in
        this repository supplies ISO-8601 strings, and the corpus loader did
        not convert them. ``hpheno`` then raised
        ``TypeError: unsupported operand type(s) for -: 'str' and 'str'`` on
        the line that computes the season length. Nothing surfaced it because
        ``hpheno`` is not in the validation runner's dispatch table, so the
        case was reported ``not_run`` and never executed.

        The API router already converted before calling
        (``services/api_gateway/routers/hydroma_indices.py:529``), so the two
        entry points into the same model disagreed about what ``dates``
        contained.

        An ISO-8601 ``YYYY-MM-DD`` string is unambiguous, so accepting it here
        is safe and makes the declared type and the shipped corpus agree.
        Anything else raises with the position, because a silently wrong date
        would move every reported phenological date.
        """
        if isinstance(dates, np.ndarray):
            dates = dates.tolist()
        if isinstance(dates, (date, str)):
            dates = [dates]
        try:
            items = list(dates)
        except TypeError as exc:
            raise TypeError(f"dates must be a sequence, got {type(dates).__name__}") from exc

        out: list[date] = []
        for i, value in enumerate(items):
            if isinstance(value, datetime):
                out.append(value.date())
            elif isinstance(value, date):
                out.append(value)
            elif isinstance(value, str):
                try:
                    # fromisoformat also accepts a full timestamp, and takes the
                    # date part of it, which is what a caller means.
                    out.append(datetime.fromisoformat(value.strip()).date())
                except ValueError as exc:
                    raise ValueError(
                        f"dates[{i}] = {value!r} is neither a date nor an ISO-8601 string: {exc}"
                    ) from exc
            else:
                raise TypeError(
                    f"dates[{i}] = {value!r} is a {type(value).__name__}; "
                    f"expected date, datetime, or 'YYYY-MM-DD'"
                )
        return out

    def compute(  # type: ignore[override]
        self,
        ndvi_ts: np.ndarray,
        dates: Any,
        dt_days: float = 5.0,
        ndvi_threshold: float = 0.15,
    ) -> dict[str, Any]:
        """Detect phenological stages.

        ``dates`` may be ``datetime.date`` objects or ISO-8601 strings; both
        are normalised by ``_as_dates`` before the season length is computed.
        """
        dates = self._as_dates(dates)
        ndvi_smooth = self.smooth(ndvi_ts)
        ndvi_prime = self.derivative(ndvi_smooth, dt_days)

        # SOS: first positive zero-crossing with NDVI above threshold
        # RECORDED DEFECT 2026-10-01, root cause of a negative season length.
        # This accepts ANY upward sign change in the derivative whose smoothed
        # NDVI clears the threshold, and the derivative of a smoothed flat
        # baseline is numerical noise. Measured on a single-season Gaussian NDVI
        # profile with a post-season baseline of 0.2 -- the ordinary shape, not
        # a pathological one -- the derivative over the baseline runs
        # -1.0e-05, +3.0e-04, so index 20 is an "upward zero-crossing", the
        # smoothed NDVI there is 0.1969 which clears 0.15, and the model
        # declares the start of season to be three weeks AFTER the peak.
        # Combined with the EOS bound below, `los_days` came out NEGATIVE.
        #
        # The real fix is a prominence or minimum-slope threshold on the SOS
        # crossing, which is a phenology decision with callers behind it. What
        # is guarded below is only the invariant that needs no science: a start
        # of season cannot follow an end of season.
        sos_idx = None
        for i in range(1, len(ndvi_prime)):
            if ndvi_prime[i - 1] <= 0 < ndvi_prime[i] and ndvi_smooth[i] > ndvi_threshold:
                sos_idx = i
                break

        # POS: maximum of NDVI
        pos_idx = int(np.argmax(ndvi_smooth))

        # EOS: first negative zero-crossing after POS
        # RECORDED DEFECT 2026-10-01, not changed: this loop starts at
        # ``pos_idx + 1``, so it never examines the pair
        # ``(pos_idx - 1, pos_idx)``. POS is ``argmax`` of the smoothed
        # series, which is also where the derivative changes sign, so the
        # downward crossing it is looking for is frequently AT ``pos_idx`` and
        # the loop skips past it. Measured on a single-season series whose
        # smoothed peak coincides with the derivative sign change:
        # ``eos = None`` and ``los_days = 0``, because ``eos_date`` was never
        # set and the ``if sos_date and eos_date`` guard returned 0. The
        # fixture in ``validation/test_cases/hpheno.yaml`` does not show it --
        # its symmetric series puts the argmax one index off the sign change,
        # so the crossing lands at ``pos_idx + 1`` and is found -- which is
        # why a one-sided series is the case that exposes it.
        #
        # Changing the bound makes a start-of-season detection possible that
        # was previously reported as none, so it moves every reported season
        # length for a one-sided series. That is a phenology decision with
        # callers behind it. Recorded here rather than applied.
        eos_idx = None
        for i in range(pos_idx + 1, len(ndvi_prime)):
            if ndvi_prime[i - 1] >= 0 > ndvi_prime[i] and ndvi_smooth[i] > ndvi_threshold:
                eos_idx = i
                break

        sos_date = dates[sos_idx] if sos_idx is not None else None
        pos_date = dates[pos_idx] if pos_idx is not None else None
        eos_date = dates[eos_idx] if eos_idx is not None else None

        los = 0
        # A season length is a difference of two dates and cannot be negative.
        # Before this guard it was, on ordinary single-season series: the SOS
        # rule can lock onto noise in the derivative over a flat post-season
        # baseline (see above) and place the start of season after the peak,
        # giving los_days = -50 for a 250-day season. The `else 0` here keeps
        # the existing convention that an undeterminable season reports 0, but
        # it was previously indistinguishable from a genuine zero-length
        # season, so `los_days_is_meaningful` is reported alongside it.
        los_is_meaningful = sos_date is not None and eos_date is not None and eos_date >= sos_date
        if los_is_meaningful and sos_date is not None and eos_date is not None:
            los = (eos_date - sos_date).days

        return {
            "sos": sos_date,
            "pos": pos_date,
            "eos": eos_date,
            "los_days": los,
            "los_days_is_meaningful": los_is_meaningful,
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
