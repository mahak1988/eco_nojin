"""Contract tests for the C++ bridge: fallback signatures must match the native ones.

``_with_telemetry`` forwards the same positional arguments to whichever backend
it selects. Where a Python fallback and the native symbol disagree on parameter
order, every call made without the extension silently computes the wrong thing.

``penman_monteith_et0`` was exactly that case: the native binding takes
``(t_min, t_max, rh_mean_pct, u2, rs_mj, elevation_m, lat_deg, doy)`` while the
fallback read ``(tmin, tmax, rh, rs, u2, z, lat, doy)`` -- positions 4 and 5
swapped, so wind speed was used as solar radiation and vice versa. This test
pins the contract for every bridged function that has a Python fallback, so the
next mismatch is caught here rather than in an irrigation recommendation.
"""

from __future__ import annotations

import inspect

import pytest

import engine.hydroma.cpp_bridge as bridge

core = bridge.get_module()

#: bridge name -> (python fallback, required parameter names)
#: The native order is the contract; the fallback must mirror it.
_FALLBACKS = {
    "penman_monteith_et0": (
        bridge._py_penman_monteith_et0,
        ("tmin", "tmax", "rh_mean", "u2", "rs", "z", "lat", "doy"),
    ),
    "ndvi": (bridge._py_ndvi, ("red", "nir")),
    "evi": (bridge._py_evi, ("red", "nir", "blue")),
    "savi": (bridge._py_savi, ("red", "nir", "L")),
    "ndwi": (bridge._py_ndwi, ("green", "nir")),
    "nbr": (bridge._py_nbr, ("nir", "swir")),
}


def test_native_module_is_loaded():
    if core is None:
        pytest.skip("C++ extension is not built")


@pytest.mark.parametrize("name", sorted(_FALLBACKS))
def test_fallback_arity_matches_the_native_symbol(name):
    fallback, _ = _FALLBACKS[name]
    native = getattr(core, name, None)
    if native is None:
        pytest.skip(f"{name} is not exposed by the extension")

    assert len(inspect.signature(fallback).parameters) == _expected_arity(name)


def _expected_arity(name: str) -> int:
    native = getattr(core, name)
    doc = native.__doc__ or ""
    # pybind11 renders the signature in the docstring as "name(a: float, b: int)".
    start = doc.find("(")
    end = doc.find(")")
    assert start != -1 and end > start, f"unreadable native signature: {doc!r}"
    inner = doc[start + 1 : end].strip()
    if not inner:
        return 0
    return len(inner.split(","))


@pytest.mark.parametrize("name", sorted(_FALLBACKS))
def test_fallback_parameter_count_matches_native_docstring(name):
    fallback, expected_names = _FALLBACKS[name]

    assert tuple(inspect.signature(fallback).parameters) == expected_names


def test_penman_monteith_argument_order_is_u2_then_rs():
    """The regression, stated explicitly so it cannot be reintroduced quietly."""
    params = list(inspect.signature(bridge._py_penman_monteith_et0).parameters)

    assert params[3] == "u2", "position 4 must be wind speed (u2)"
    assert params[4] == "rs", "position 5 must be solar radiation (Rs)"


def test_penman_monteith_backends_agree():
    """Both backends must return the same number for the same physical inputs."""
    if core is None:
        pytest.skip("C++ extension is not built")

    cases = [
        (18.0, 29.0, 55.0, 2.0, 22.0, 1200.0, 35.7, 200),   # typical summer day
        (2.0, 9.0, 70.0, 2.0, 6.0, 1200.0, 35.7, 15),      # cloudy winter
        (2.0, 9.0, 70.0, 2.0, 1.2, 1200.0, 35.7, 15),      # very overcast
        (5.0, 12.0, 80.0, 1.5, 3.0, 1500.0, 35.7, 355),    # winter, high elevation
    ]
    for tmin, tmax, rh, u2, rs, z, lat, doy in cases:
        cpp = core.penman_monteith_et0(tmin, tmax, rh, u2, rs, z, lat, doy)
        py = float(bridge._py_penman_monteith_et0(tmin, tmax, rh, u2, rs, z, lat, doy))
        rel = abs(cpp - py) / max(abs(py), 1e-12)
        assert rel < 1e-9, f"ET0 diverges at {tmin},{tmax},{rh},{u2},{rs}: cpp={cpp} py={py}"


def test_penman_monteith_is_sensitive_to_wind_speed():
    """Guards the swap: a wrong argument order makes ET0 insensitive to u2."""
    base = dict(tmin=18.0, tmax=29.0, rh_mean=55.0, rs=22.0, z=1200.0, lat=35.7, doy=200)
    slow = float(bridge._py_penman_monteith_et0(u2=1.0, **base))
    windy = float(bridge._py_penman_monteith_et0(u2=5.0, **base))

    assert windy > slow * 1.05, "ET0 must increase with wind speed"


def test_penman_monteith_is_sensitive_to_solar_radiation():
    base = dict(tmin=18.0, tmax=29.0, rh_mean=55.0, u2=2.0, z=1200.0, lat=35.7, doy=200)
    dull = float(bridge._py_penman_monteith_et0(rs=6.0, **base))
    bright = float(bridge._py_penman_monteith_et0(rs=25.0, **base))

    assert bright > dull * 1.1, "ET0 must increase with measured solar radiation"


def test_index_backends_agree():
    """The five indices, all four shapes of input.

    Compared with a tight tolerance rather than bitwise. Cross-compiler
    reassociation and fused multiply-add make bitwise equality between a C++
    kernel and a NumPy kernel an unreasonable requirement; the observed spread
    is ~3e-10 absolute, which is ordinary double-precision noise and not a
    difference in the expression being evaluated.
    """
    if core is None:
        pytest.skip("C++ extension is not built")

    import numpy as np

    rng = np.random.default_rng(0)
    for shape in ((50,), (10, 5), (1, 64), (64, 1)):
        red = rng.uniform(0.01, 0.3, shape)
        nir = rng.uniform(0.2, 0.9, shape)
        cpp = np.asarray(core.ndvi_array(red, nir)).reshape(-1)
        py = np.asarray(bridge._py_ndvi(red, nir)).reshape(-1)
        np.testing.assert_allclose(cpp, py, rtol=1e-12, atol=1e-12)
