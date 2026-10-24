"""
Standardized Precipitation Index (SPI) — McKee et al. (1993).

This module implements the two-stage construction McKee et al. define:

1. accumulate precipitation over the timescale of interest, so a single
   SPI value describes a *scale* (1, 3, 6, 12 months) rather than a month;
2. fit a two-parameter gamma distribution to the accumulated totals that
   are strictly positive, including the probability of a zero total as a
   separate term;
3. transform the resulting cumulative probability to the standard normal,
   ``SPI = Phi^-1(F(x))``.

Primary references
------------------
* McKee, T.B., Doesken, N.J. and Kleist, J. (1993). *The relationship of
  drought frequency and duration to time scales.* Eighth Conference on
  Applied Climatology, American Meteorological Society, Anaheim, CA,
  17–22 January 1993, pp. 179–184.
* WMO No. 1090, *Standardized Precipitation Index User Guide* (Svoboda,
  Hayes and Smith), World Meteorological Organization, Geneva, 2012.
  This is the operational guide that fixes the three timescales above as
  the recommended set and describes the zero-precipitation term used here.

Method detail worth stating explicitly, because it is the part that is
most often quietly omitted:

* **The zero-precipitation term.** Monthly precipitation contains exact
  zeros, and a continuous gamma fitted to the positive values alone has
  no mass at zero, so the raw gamma CDF understates the probability of dry
  accumulations. McKee therefore uses the mixed distribution
  ``P(x = 0) = m / n`` (the observed fraction of zero accumulations) and,
  for ``x > 0``, ``P = P0 + (1 - P0) * GammaCDF(x)``. That term is applied
  here; without it a drought-prone record returns SPI values that are
  systematically too mild.
* **Probability clipping.** ``Phi^-1`` diverges at 0 and 1, and the
  maximum-likelihood gamma fit on a finite record can return a cumulative
  probability of exactly 0 or exactly 1 for an extreme accumulation.
  Probabilities are therefore clipped into ``[1e-10, 1 - 1e-10]`` before
  the inverse-normal transform. The clip bounds the result to roughly
  ``|SPI| <= 6.36``; a clipped value means "the fitted distribution puts
  this accumulation beyond its resolvable tail", not a measured value.

Implementation constraints
--------------------------
``zed_compliant`` — this module imports only the Python standard library
typing annotations, ``numpy`` and ``scipy.stats``. It imports nothing from
``engine`` and has no knowledge of the platform's model registry, gateway
or persistence layer, so it can be used standalone and tested against
scipy as an independent reference implementation.

One gamma distribution is fitted per call, over the whole record, which
is the procedure McKee describes. A rolling or split-sample fit would
produce a different (and non-comparable) index and is deliberately not
offered here.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.stats import gamma, norm

__all__ = ["SUPPORTED_SCALES", "calculate_spi"]

#: Timescales recommended by WMO No. 1090 (McKee's Table 2 set).
SUPPORTED_SCALES: tuple[int, ...] = (1, 3, 6, 12)

#: Probabilities are clipped into this closed interval before the inverse
#: normal transform, so that ``Phi^-1`` is always finite. See the module
#: docstring. The value bounds ``|SPI|`` to about 6.36.
_PROBABILITY_CLIP: float = 1e-10

#: A gamma distribution is not identifiable from fewer than two distinct
#: positive observations, so the fit is refused below this count. This is a
#: numerical floor, not a recommendation: WMO No. 1090 asks for records of
#: at least 30 years, which is the caller's responsibility, not this
#: function's.
_MIN_NONZERO_FOR_FIT: int = 2


def _validate_scale(scale: Any) -> int:
    """Return *scale* as an int, or raise ``ValueError``.

    Only 1, 3, 6 and 12 are accepted, per WMO No. 1090. Anything else —
    including a non-integral value and a scale outside the supported set —
    is a caller error rather than something to approximate.
    """
    if isinstance(scale, bool):
        raise ValueError(f"SPI time scale must be an integer number of months, got {scale!r}")
    if isinstance(scale, (int, np.integer)):
        value = int(scale)
    elif isinstance(scale, float) and float(scale).is_integer():
        value = int(scale)
    else:
        raise ValueError(
            f"SPI time scale must be an integer number of months, got {scale!r}"
        )
    if value not in SUPPORTED_SCALES:
        raise ValueError(
            f"SPI time scale must be one of {SUPPORTED_SCALES} months, got {scale!r}"
        )
    return value


def _as_series(precipitation: Any) -> np.ndarray:
    """Coerce scalar / list / ndarray input to a 1-D float array.

    A scalar is treated as a one-month record. Multi-dimensional input is
    flattened in C order, because a timescale accumulation over an
    ambiguous axis would be a silent guess.
    """
    values = np.asarray(precipitation, dtype=float)
    if values.ndim == 0:
        values = values.reshape(1)
    elif values.ndim > 1:
        values = values.reshape(-1)
    if values.size == 0:
        raise ValueError("precipitation series is empty; SPI needs at least one month")
    if not np.all(np.isfinite(values)):
        raise ValueError("precipitation series contains NaN or infinite values")
    if np.any(values < 0.0):
        raise ValueError("precipitation series contains negative values")
    return values


def _accumulate(values: np.ndarray, scale: int) -> np.ndarray:
    """Moving *scale*-month sum, NaN for the first ``scale - 1`` months.

    Index ``i`` holds ``sum(values[i - scale + 1 : i + 1])`` for
    ``i >= scale - 1`` and NaN below that, because the first full window
    closes at ``scale - 1``.
    """
    accumulated = np.full(values.shape, np.nan, dtype=float)
    if values.size >= scale:
        cumulative = np.concatenate(([0.0], np.cumsum(values)))
        last = values.size + 1 - scale
        accumulated[scale - 1 :] = cumulative[scale:] - cumulative[:last]
    return accumulated


def calculate_spi(precipitation: Any, scale: int) -> np.ndarray:
    """Standardized Precipitation Index over *scale* months.

    Implements McKee et al. (1993) as operationalised in WMO No. 1090:
    moving-sum accumulation, maximum-likelihood gamma fit to the positive
    accumulations with the zero-precipitation probability term, and the
    inverse-normal transform of the resulting cumulative probability.

    Parameters
    ----------
    precipitation:
        Monthly precipitation totals (mm month-1) as a scalar, list or
        ``numpy`` array. Non-finite or negative values raise
        ``ValueError``.
    scale:
        Accumulation timescale in months. Must be one of ``SUPPORTED_SCALES``
        (1, 3, 6, 12); any other value raises ``ValueError``.

    Returns
    -------
    ``numpy.ndarray`` of float, the same length as the input.

    * The first ``scale - 1`` entries are NaN — no full window exists there.
    * Remaining entries are finite unless the probability clip is hit, in
      which case they are the clipped bound (roughly +/-6.36), never inf.

    Raises
    ------
    ValueError
        If *scale* is unsupported, the series is empty or non-finite or
        negative, or fewer than two accumulations are strictly positive
        (the gamma distribution is then not identifiable).

    Notes
    -----
    This is a distributional standardization, not a z-score. It is
    unbounded and asymptotic at zero, and it is not comparable with a
    rolling-window z-score of the same record.

    Correctness and conformance of the published procedure are verified in
    ``engine/tests/test_spi_calculator.py`` three ways: against a scipy
    recomputation (fit, mixed CDF, inverse normal), against a from-scratch
    implementation that shares no code with this module (Newton MLE from the
    published score equation, series/continued-fraction incomplete gamma,
    stdlib AS241 inverse normal), and against the published classification
    bands pinned in ``tests/reference_data/mckee_spi_classification.csv``.
    No published numeric SPI value table (e.g. Guttman 1999) is available
    offline, so this establishes conformance to the published method, not
    agreement with external index values; that remaining gap is recorded in
    the indicator record ``indicators/ENO_SPI_001.yaml``.
    """
    months = _validate_scale(scale)
    values = _as_series(precipitation)

    accumulated = _accumulate(values, months)

    spi_values = np.full(values.shape, np.nan, dtype=float)

    finite_window = ~np.isnan(accumulated)
    if not np.any(finite_window):
        return spi_values

    window = accumulated[finite_window]
    n_window = float(window.size)

    positive = window[window > 0.0]
    if positive.size < _MIN_NONZERO_FOR_FIT:
        raise ValueError(
            "SPI needs at least two strictly positive accumulated totals to fit "
            f"a gamma distribution, got {positive.size}"
        )

    # McKee's zero-precipitation probability term: P(x = 0) = m / n.
    zero_probability = float(window.size - positive.size) / n_window

    # Two-parameter gamma (loc fixed at 0) by maximum likelihood on the
    # positive accumulations only.
    shape, _location, gamma_scale = gamma.fit(positive, floc=0.0)

    # Cumulative probability of the mixed (zero-inflated) distribution.
    positive_mask = window > 0.0
    probability = np.empty(window.shape, dtype=float)
    probability[~positive_mask] = zero_probability
    probability[positive_mask] = zero_probability + (1.0 - zero_probability) * gamma.cdf(
        window[positive_mask], shape, scale=gamma_scale
    )

    # Phi^-1 diverges at 0 and 1; clip so the result is always finite.
    probability = np.clip(probability, _PROBABILITY_CLIP, 1.0 - _PROBABILITY_CLIP)

    spi_values[finite_window] = norm.ppf(probability)
    return spi_values
