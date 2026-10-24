"""Verification tests for the McKee SPI calculator.

Module under test: ``engine/hydroma/spi_calculator.py``,
``calculate_spi`` (spec ECO-10, priority-1 indicator ENO_SPI_001).

What these tests are
--------------------
Three layers of verification, none of which can agree with the module by
construction:

1. **Published-procedure conformance.** The implemented procedure is McKee
   et al. (1993) as operationalised in WMO No. 1090: moving-sum accumulation,
   maximum-likelihood gamma fit to the positive accumulations with the
   zero-precipitation probability term, and the inverse-normal transform.
   Each layer is re-implemented here from scratch, sharing no code with the
   module: the MLE is solved from the published score equation
   ``ln(a) - psi(a) = ln(mean) - mean(ln x)`` with a Newton iteration whose
   digamma is itself built from the standard series/asymptotic expansions
   (Numerical Recipes); the gamma CDF is the regularized incomplete gamma
   computed by the series/continued-fraction algorithm, which is additionally
   checked against the exact Erlang closed form for integer shapes; the
   inverse normal transform uses the standard library's AS241 implementation
   (``statistics.NormalDist.inv_cdf``) rather than scipy.
2. **Published classification table.** ``tests/reference_data/
   mckee_spi_classification.csv`` carries the published SPI category bands
   (McKee et al. 1993 / WMO No. 1090); one test pins them so the reference
   itself cannot drift.
3. **Behavioural properties.** Standardized output (mean ~ 0, std ~ 1),
   boundedness through dry spells, leading-NaN contract, supported timescales.

What these tests are NOT (safety-brake-6 discipline)
----------------------------------------------------
No published SPI *value* table (e.g. Guttman 1999, JAWRA 35(2):311-322) has
been compared against this output: such a table is not available offline and
ZED forbids live download. The verification above is of the published
procedure and its numerical implementation, not against external index values.
The indicator record therefore says ``VALIDATED_METHOD_CONFORMANCE`` and
carries the reference-table gap explicitly, and every series used here is
synthetic.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pytest
from scipy.special import digamma as _scipy_digamma
from scipy.stats import gamma, norm

from engine.hydroma.spi_calculator import SUPPORTED_SCALES, calculate_spi

_CLASSIFICATION_CSV = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "reference_data"
    / "mckee_spi_classification.csv"
)

#: Seed fixed so the fixture series are deterministic across runs.
_RNG_SEED = 42

#: Generous band for the moment test. The standardization is exact in
#: expectation; the slack absorbs sampling error in the finite record, not
#: a wrong implementation.
_MOMENT_TOLERANCE = 0.15

#: Agreement band for the from-scratch numerical reference. The series and
#: continued-fraction algorithms carry their own ~1e-13 accuracy; 1e-8 leaves
#: room for the Newton MLE and the AS241 transform without hiding anything.
_INDEPENDENT_TOLERANCE = 1e-8


# --------------------------------------------------------------------------
# From-scratch implementations of the published procedure's layers
# --------------------------------------------------------------------------
def _digamma(x: float) -> float:
    """Digamma psi(x) from the standard series and asymptotic expansions.

    The recurrence is applied up to x >= 10 so the asymptotic series, extended
    through the B12 term, is accurate to ~1e-12 in the region that matters
    for the gamma MLE.
    """
    result = 0.0
    while x < 10.0:
        result -= 1.0 / x
        x += 1.0
    f = 1.0 / (x * x)
    asymptotic = (
        math.log(x)
        - 0.5 / x
        + f
        * (
            -1.0 / 12.0
            + f
            * (
                1.0 / 120.0
                + f
                * (
                    -1.0 / 252.0
                    + f
                    * (
                        1.0 / 240.0
                        + f * (-1.0 / 132.0 + f * (691.0 / 32760.0))
                    )
                )
            )
        )
    )
    return result + asymptotic


def _fit_gamma_mle(values: np.ndarray) -> tuple[float, float]:
    """Maximum-likelihood gamma fit (loc = 0) solved from the score equation.

    Solves ``ln(a) - psi(a) = ln(mean) - mean(ln x)`` for the shape ``a``
    with Newton's method, then sets the scale to ``mean / a``. Scott's
    approximation provides the starting point. Shares no code with scipy.
    """
    log_values = np.log(values)
    mean_log = float(np.mean(log_values))
    mean = float(np.mean(values))
    s = math.log(mean) - mean_log
    if s <= 0.0:
        raise ValueError("score equation has no solution for this sample")
    shape = (3.0 - s + math.sqrt((3.0 - s) ** 2 + 24.0 * s)) / (12.0 * s)
    for _ in range(100):
        score = math.log(shape) - _digamma(shape) - s
        derivative = 1.0 / shape - (_digamma(shape + 1e-6) - _digamma(shape)) / 1e-6
        step = score / derivative
        shape -= step
        if abs(step) < 1e-14 * max(1.0, shape):
            break
    return float(shape), mean / shape


def _regularized_gamma_p(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x) by series/continued fraction.

    Numerical Recipes' gser/gcf pair: the power series for ``x < a + 1`` and
    the Lentz continued fraction for ``x >= a + 1``. For integer ``a`` this
    is also checked against the exact Erlang closed form in
    ``test_reference_implementations_are_self_verified``.
    """
    if x < 0.0 or a <= 0.0:
        raise ValueError("P(a, x) requires a > 0 and x >= 0")
    if x == 0.0:
        return 0.0
    ln_gamma_a = math.lgamma(a)
    if x < a + 1.0:
        # Power series (gser).
        term = 1.0 / a
        total = term
        for n in range(1, 1000):
            term *= x / (a + n)
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        return total * math.exp(-x + a * math.log(x) - ln_gamma_a)

    # Lentz continued fraction for x >= a + 1 (gcf).
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    q = math.exp(-x + a * math.log(x) - ln_gamma_a)
    return 1.0 - q * h


def _normal_inv_cdf(p: float) -> float:
    """Inverse standard-normal CDF via the standard library's AS241 code."""
    return NormalDist().inv_cdf(p)


def _independent_spi(precipitation: np.ndarray, scale: int) -> np.ndarray:
    """The McKee/WMO-1090 procedure rebuilt from scratch (no scipy, no module)."""
    values = np.asarray(precipitation, dtype=float)
    result = np.full(values.shape, np.nan, dtype=float)
    if values.size < scale:
        return result

    accumulated = np.convolve(values, np.ones(scale, dtype=float), mode="valid")
    positive = accumulated[accumulated > 0.0]
    zero_probability = (accumulated.size - positive.size) / accumulated.size

    shape, gamma_scale = _fit_gamma_mle(positive)

    probability = np.empty(accumulated.shape, dtype=float)
    probability[accumulated <= 0.0] = zero_probability
    for index, value in enumerate(accumulated):
        if value > 0.0:
            probability[index] = zero_probability + (1.0 - zero_probability) * (
                _regularized_gamma_p(shape, value / gamma_scale)
            )
    probability = np.clip(probability, 1e-10, 1.0 - 1e-10)

    result[scale - 1 :] = [_normal_inv_cdf(p) for p in probability]
    return result


def _reference_spi(precipitation: np.ndarray, scale: int) -> np.ndarray:
    """Independent McKee SPI using scipy for the fit, CDF and inverse normal.

    Deliberately uses a different accumulation path (``np.convolve``) from
    the module under test (cumulative-sum differencing), so the two share
    no code.
    """
    values = np.asarray(precipitation, dtype=float)
    result = np.full(values.shape, np.nan, dtype=float)
    if values.size < scale:
        return result

    accumulated = np.convolve(values, np.ones(scale, dtype=float), mode="valid")
    positive = accumulated[accumulated > 0.0]
    zero_probability = (accumulated.size - positive.size) / accumulated.size

    shape, _location, gamma_scale = gamma.fit(positive, floc=0.0)

    probability = np.empty(accumulated.shape, dtype=float)
    probability[accumulated <= 0.0] = zero_probability
    probability[accumulated > 0.0] = zero_probability + (1.0 - zero_probability) * gamma.cdf(
        accumulated[accumulated > 0.0], shape, scale=gamma_scale
    )
    probability = np.clip(probability, 1e-10, 1.0 - 1e-10)

    result[scale - 1 :] = norm.ppf(probability)
    return result



def test_matches_scipy_gamma_on_deterministic_series() -> None:
    """SPI equals the inline scipy recomputation on a fixed gamma series.

    Correctness test only: scipy is used as an independent implementation
    of the published procedure, which is the strongest offline reference
    available. It is not a published SPI table, so agreement here does not
    amount to validation of the index.
    """
    rng = np.random.default_rng(_RNG_SEED)
    precipitation = rng.gamma(shape=1.5, scale=20.0, size=240)

    for scale in SUPPORTED_SCALES:
        computed = calculate_spi(precipitation, scale)
        reference = _reference_spi(precipitation, scale)

        assert computed.shape == precipitation.shape
        max_deviation = float(np.nanmax(np.abs(computed - reference)))
        assert np.allclose(computed, reference, rtol=1e-9, equal_nan=True), (
            f"scale={scale} months: max |computed - reference| = {max_deviation:.3e}"
        )


def test_standardization_moments() -> None:
    """A long gamma record maps to SPI with mean ~0 and std ~1.

    Property test of the probability-integral transform, not a validation
    claim: it says the output is standardized, not that it matches any
    published index values.
    """
    rng = np.random.default_rng(1234)
    precipitation = rng.gamma(shape=2.0, scale=18.0, size=720)
    assert precipitation.size >= 600

    for scale in SUPPORTED_SCALES:
        spi = calculate_spi(precipitation, scale)
        valid = spi[~np.isnan(spi)]

        assert np.isfinite(valid).all()
        assert abs(float(np.mean(valid))) <= _MOMENT_TOLERANCE
        assert abs(float(np.std(valid)) - 1.0) <= _MOMENT_TOLERANCE


def test_scales_supported_and_invalid_scale_raises() -> None:
    """Every WMO-recommended timescale returns a full-length array."""
    rng = np.random.default_rng(_RNG_SEED)
    precipitation = rng.gamma(shape=1.2, scale=25.0, size=120)

    for scale in SUPPORTED_SCALES:
        spi = calculate_spi(precipitation, scale)
        assert isinstance(spi, np.ndarray)
        assert spi.shape == precipitation.shape
        assert np.isfinite(spi[scale - 1 :]).all()

    with pytest.raises(ValueError):
        calculate_spi(precipitation, 5)


def test_zero_precipitation_handling() -> None:
    """A long dry spell stays finite and bounded, and does not crash.

    Consistency test of the zero-precipitation term (McKee's ``P(x = 0)``)
    on synthetic data: the zeros must produce a SPI, not a NaN and not a
    divergent value. It asserts boundedness, not a published SPI value.
    """
    rng = np.random.default_rng(7)
    wet = rng.gamma(shape=1.2, scale=25.0, size=600)
    precipitation = np.concatenate([wet[:300], np.zeros(24, dtype=float), wet[300:]])

    for scale in SUPPORTED_SCALES:
        spi = calculate_spi(precipitation, scale)

        assert np.isnan(spi[: scale - 1]).all()
        assert np.isfinite(spi[scale - 1 :]).all()
        assert float(np.nanmin(spi)) >= -4.0
        assert float(np.nanmax(spi)) <= 4.0


def test_leading_window_is_nan() -> None:
    """The first ``scale - 1`` months have no full window and are NaN.

    Correctness test of the documented leading-window contract; it says
    nothing about the scientific quality of the values that follow.
    """
    rng = np.random.default_rng(_RNG_SEED)
    precipitation = rng.gamma(shape=1.5, scale=20.0, size=120)

    for scale in SUPPORTED_SCALES:
        spi = calculate_spi(precipitation, scale)

        assert np.isnan(spi[: scale - 1]).all()
        assert not np.isnan(spi[scale - 1 :]).any()


# --------------------------------------------------------------------------
# Verification of the test's own reference implementations, then of the
# module against that from-scratch reference
# --------------------------------------------------------------------------
def test_reference_implementations_are_self_verified() -> None:
    """The from-scratch layers are verified before they verify the module.

    * the incomplete-gamma routine equals the exact Erlang closed form for
      integer shapes (so its series/continued-fraction switch is correct);
    * the Newton MLE solver satisfies the published score equation
      ``ln(a) - psi(a) = ln(mean) - mean(ln x)`` (so scipy's standard fit and
      the test's own fit agree through the published condition);
    * the AS241 inverse normal agrees with scipy's ppf.
    """
    # Exact Erlang closed form for integer shape a = n:
    #   F(x) = 1 - exp(-x) * sum_{k=0}^{n-1} x^k / k!
    def erlang_cdf(x: float, n: int) -> float:
        term = 1.0
        total = 1.0
        for k in range(1, n):
            term *= x / k
            total += term
        return 1.0 - math.exp(-x) * total

    for shape_n in (1, 2, 3, 5, 8):
        for x in (0.5, 2.0, 7.5, 30.0, 200.0):
            assert _regularized_gamma_p(float(shape_n), x) == pytest.approx(
                erlang_cdf(x, shape_n), abs=1e-12
            ), (shape_n, x)

    rng = np.random.default_rng(11)
    sample = rng.gamma(shape=1.7, scale=12.0, size=300)
    shape, scale = _fit_gamma_mle(sample)
    s = math.log(float(np.mean(sample))) - float(np.mean(np.log(sample)))
    assert math.log(shape) - _digamma(shape) == pytest.approx(s, abs=1e-9)
    scipy_shape, _loc, scipy_scale = gamma.fit(sample, floc=0.0)
    assert shape == pytest.approx(scipy_shape, rel=1e-6), (
        f"from-scratch MLE shape {shape} vs scipy {scipy_shape}"
    )
    assert scale == pytest.approx(scipy_scale, rel=1e-6)

    # The test's own digamma agrees with scipy's digamma (psi).
    for x in (0.3, 1.0, 2.5, 9.0, 40.0):
        assert _digamma(x) == pytest.approx(float(_scipy_digamma(x)), abs=1e-10)

    # AS241 inverse normal agrees with scipy's ppf.
    for p in (1e-6, 0.001, 0.02, 0.5, 0.98, 0.999, 1 - 1e-6):
        assert _normal_inv_cdf(p) == pytest.approx(float(norm.ppf(p)), abs=1e-12)


def test_module_matches_from_scratch_published_procedure() -> None:
    """SPI equals a from-scratch McKee/WMO-1090 implementation, sharing no code.

    The reference path uses its own Newton MLE fit, its own incomplete-gamma
    routine and the standard library's AS241 inverse normal — no scipy call
    and no module function. A dry spell with zeros is included so the
    zero-precipitation term is exercised on every scale.
    """
    rng = np.random.default_rng(_RNG_SEED)
    wet = rng.gamma(shape=1.4, scale=22.0, size=180)
    precipitation = np.concatenate([wet[:150], np.zeros(18, dtype=float), wet[150:]])

    for scale in SUPPORTED_SCALES:
        computed = calculate_spi(precipitation, scale)
        reference = _independent_spi(precipitation, scale)

        assert np.allclose(computed, reference, rtol=_INDEPENDENT_TOLERANCE, equal_nan=True), (
            f"scale={scale} months: max |computed - from-scratch| = "
            f"{float(np.nanmax(np.abs(computed - reference))):.3e}"
        )


def test_published_classification_table_is_intact() -> None:
    """The McKee/WMO-1090 category bands in the reference CSV are the published ones.

    The table is the reference data the indicator record cites; this test
    pins it so it cannot silently drift (and records that no published SPI
    *value* table is available offline — only the classification bands).
    """
    with _CLASSIFICATION_CSV.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 7
    expected = [
        ("2.00", "+inf", "extremely wet"),
        ("1.50", "1.99", "very wet"),
        ("1.00", "1.49", "moderately wet"),
        ("-0.99", "0.99", "near normal"),
        ("-1.49", "-1.00", "moderately dry"),
        ("-1.99", "-1.50", "severely dry"),
        ("-inf", "-2.00", "extremely dry"),
    ]
    for row, (low, high, label) in zip(rows, expected, strict=True):
        assert row["spi_min"] == low
        assert row["spi_max"] == high
        assert row["category_label"] == label
        assert "McKee" in row["source"] and "1090" in row["source"]


def test_spi_values_fall_in_validated_bands_when_extreme() -> None:
    """A record-long dry spell must produce a 'severely dry' or worse SPI.

    The published bands give this test an external meaning: the SPI of a
    12-month total far below the fitted median is expected in the severe or
    extreme drought band, per the classification table.
    """
    rng = np.random.default_rng(_RNG_SEED)
    wet = rng.gamma(shape=1.4, scale=22.0, size=240)
    drought = np.concatenate([wet, np.zeros(12, dtype=float)])

    spi = calculate_spi(drought, scale=12)
    last = float(spi[-1])
    assert last <= -1.5, f"record-breaking 12-month total gives SPI {last}"

