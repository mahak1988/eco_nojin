"""Tests for the satellite index path.

Two defects, both of which turned a missing observation into a confident number.

* ``calculate_ndvi`` cast the numerator to float and left the denominator in the
  input dtype, so a ``uint16`` raw-DN input wrapped at 65535 in the sum. The other
  index functions had the mirror problem: no cast at all.
* Every function ended with ``np.nan_to_num(values, nan=0.0)``. The index
  functions do not write NaN for an undefined ratio -- they use the native
  ``denominator == 0`` guard -- but a **cloud mask does** write NaN, and
  ``nan_to_num`` converted those cloud pixels to 0.0. ``analyzer`` then took
  ``nanmedian``, which therefore included the clouds as a reading of exactly
  zero, and ``interpret_ndvi(0.0)`` classifies as bare soil: a fully clouded scene
  produced a recommendation to plant drought-resistant species.
"""

from __future__ import annotations

import numpy as np
import pytest

from engine.hydroma.satellite.processors.indices import (
    calculate_all_indices,
    calculate_evi,
    calculate_nbr,
    calculate_ndvi,
    calculate_ndwi,
    calculate_savi,
)


def _bands(n: int = 1000, seed: int = 0):
    rng = np.random.default_rng(seed)
    return {
        "red": rng.uniform(0.01, 0.3, n),
        "nir": rng.uniform(0.2, 0.9, n),
        "blue": rng.uniform(0.01, 0.2, n),
        "green": rng.uniform(0.05, 0.35, n),
        "swir": rng.uniform(0.05, 0.5, n),
    }


# ------------------------------------------------------------- integer input


def test_uint16_raw_dn_does_not_overflow():
    """Regression: the denominator stayed uint16 and wrapped at 65535."""
    red = np.array([100, 200, 300, 400], dtype=np.uint16)
    nir = np.array([3000, 4000, 5000, 6000], dtype=np.uint16)

    out = calculate_ndvi(red, nir)
    expected = (nir.astype(np.float64) - red) / (nir.astype(np.float64) + red)

    assert out.dtype == np.float64
    np.testing.assert_allclose(out, expected, rtol=1e-12)


def test_integer_input_across_all_indices():
    bands = {k: (v * 10_000).astype(np.int32) for k, v in _bands(200, seed=3).items()}
    for fn, args in [
        (calculate_ndvi, (bands["red"], bands["nir"])),
        (calculate_evi, (bands["red"], bands["nir"], bands["blue"])),
        (calculate_savi, (bands["red"], bands["nir"])),
        (calculate_ndwi, (bands["green"], bands["nir"])),
        (calculate_nbr, (bands["nir"], bands["swir"])),
    ]:
        out = fn(*args)
        assert out.dtype == np.float64, f"{fn.__name__} did not promote to float64"
        assert np.all(np.isfinite(out)), f"{fn.__name__} produced non-finite output"


# ------------------------------------------------------------- cloud masking


def test_nan_pixels_stay_nan():
    """Regression: cloud pixels were rewritten to 0.0 and counted as bare soil."""
    red = np.array([0.1, np.nan, 0.2, 0.3])
    nir = np.array([0.5, np.nan, 0.6, 0.7])

    out = calculate_ndvi(red, nir)

    assert np.isnan(out[1]), "a cloud-masked pixel must not become a number"
    assert np.all(np.isfinite(out[[0, 2, 3]]))


def test_median_ignores_cloudy_pixels():
    """The aggregation must not see the clouds at all."""
    red = np.full(10, 0.1)
    nir = np.full(10, 0.5)
    clear = calculate_ndvi(red, nir)

    # Every pixel but three is cloud.
    red_cloudy = red.copy()
    nir_cloudy = nir.copy()
    red_cloudy[:7] = np.nan
    nir_cloudy[:7] = np.nan

    assert np.nanmedian(calculate_ndvi(red_cloudy, nir_cloudy)) == pytest.approx(
        float(np.nanmedian(clear))
    )


def test_nan_median_of_an_entirely_cloudy_scene_is_detectable():
    """The analyzer must be able to notice there is nothing to aggregate."""
    cloudy = calculate_ndvi(np.full(10, np.nan), np.full(10, np.nan))

    assert np.all(np.isnan(cloudy))
    assert not np.isfinite(np.nanmedian(cloudy))


# ---------------------------------------------------------- numeric contract


@pytest.mark.parametrize(
    ("fn", "args"),
    [
        (calculate_ndvi, (np.zeros(4), np.zeros(4))),
        (calculate_savi, (np.zeros(4), np.zeros(4))),
        (calculate_ndwi, (np.zeros(4), np.zeros(4))),
        (calculate_nbr, (np.zeros(4), np.zeros(4))),
    ],
)
def test_zero_denominator_gives_zero_not_nan_or_inf(fn, args):
    out = fn(*args)
    assert np.all(out == 0.0)
    assert not np.any(np.isnan(out))


def test_every_index_is_clipped_to_unit_range():
    bands = _bands(2000, seed=7)
    out = calculate_all_indices(
        bands["red"],
        bands["nir"],
        bands["blue"],
        bands["swir"],
        bands["green"],
    )
    for name, values in out.items():
        assert np.all(values >= -1.0), f"{name} below -1"
        assert np.all(values <= 1.0), f"{name} above 1"


def test_calculate_all_indices_does_not_fabricate_a_missing_band():
    """A band that was not supplied must be absent, not invented."""
    bands = _bands(50)
    out = calculate_all_indices(bands["red"], bands["nir"])

    assert set(out) == {"ndvi", "savi"}
    assert "evi" not in out, "EVI cannot be computed without a blue band"
    assert "nbr" not in out, "NBR cannot be computed without a SWIR band"


def test_no_nan_to_num_hides_a_result():
    """The module must not blanket-rewrite NaN to 0.0 anywhere."""
    import ast
    from pathlib import Path

    src = Path("engine/hydroma/satellite/processors/indices.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    calls = [
        ast.unparse(n)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "nan_to_num"
    ]
    assert not calls, f"satellite index path still uses nan_to_num: {calls}"


# ------------------------------------------------- agreement with the bridge


def test_matches_the_cpp_bridge_indices():
    """Same expression, same result: the satellite path and the native kernels."""
    import engine.hydroma.cpp_bridge as bridge

    core = bridge.get_module()
    if core is None:
        pytest.skip("C++ extension is not built")

    bands = _bands(5000, seed=11)

    np.testing.assert_allclose(
        calculate_ndvi(bands["red"], bands["nir"]),
        core.ndvi_array(bands["red"], bands["nir"]),
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        calculate_evi(bands["red"], bands["nir"], bands["blue"]),
        core.evi_array(bands["red"], bands["nir"], bands["blue"]),
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        calculate_ndwi(bands["green"], bands["nir"]),
        core.ndwi_array(bands["green"], bands["nir"]),
        rtol=1e-12,
        atol=1e-12,
    )
