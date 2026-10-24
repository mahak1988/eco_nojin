"""P0-4 -- ``SOIL_AMENDMENT`` depth unit contract at the router boundary.

The public tool spec declares ``soil_depth`` in **metres** (default 0.3),
while the engine kernel ``calculate_sodic_soil_amendment`` is calibrated in
**centimetres** (its depth factor is ``soil_depth / 15``, a 15 cm reference
layer). Before this contract was pinned the router passed the metres value
straight through and every gypsum requirement came out 100x low: ESP 15 at
0.3 m returned 100 kg/ha instead of 10 000 kg/ha.

These tests drive the real runner function
(``services/api_gateway/routers/hydroma_soil._run_soil_salinity``) so the
conversion is exercised where it happens -- once, at the boundary -- rather
than at the kernel, whose unit and published rates are unchanged.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api_gateway.routers.hydroma_soil import _SPEC_BY_ID, _run_soil_salinity

ESP = 15.0
DEPTH_M = 0.3
DEPTH_CM = 30.0
BULK_DENSITY = 1.4


def _params(**overrides: Any) -> dict[str, Any]:
    kw: dict[str, Any] = {
        "ec": 4.0,
        "ec_soil": 4.0,
        "ec_water": 1.0,
        "esp": ESP,
        "soil_depth": DEPTH_M,
        "bulk_density": BULK_DENSITY,
    }
    kw.update(overrides)
    return kw


def test_router_declares_soil_depth_in_metres() -> None:
    """The API contract is unchanged: the spec still advertises metres."""
    spec = _SPEC_BY_ID["soil-salinity"]
    depth = next(p for p in spec["params"] if p["name"] == "soil_depth")
    assert depth["unit"] == "m"
    assert depth["default"] == 0.3


def test_default_half_metre_depth_yields_ten_tonnes_per_hectare() -> None:
    """0.3 m at ESP 15 must give 10 000 kg/ha, not 100 kg/ha.

    The engine's own arithmetic: rate = (ESP - 10) * 0.1 t/100m2 * (30 cm / 15 cm)
    = 1.0 t/100m2 = 10 000 kg/ha. The 100x under-report was the metres-for-
    centimetres substitution.
    """
    result = _run_soil_salinity(_params())["sodic_amendment"]

    assert result["gypsum_required"] is True
    assert result["gypsum_kg_per_ha"] == pytest.approx(10000.0, rel=1e-9)
    assert result["soil_depth_unit"] == "cm"
    assert result["soil_depth"] == pytest.approx(DEPTH_CM, rel=1e-9)
    assert "10000 kg/ha" in result["interpretation"]


def test_conversion_is_exactly_times_one_hundred() -> None:
    """The boundary converts metres -> centimetres, once, and nothing else."""
    shallow = _run_soil_salinity(_params(soil_depth=0.15))["sodic_amendment"]
    deep = _run_soil_salinity(_params(soil_depth=0.30))["sodic_amendment"]

    assert shallow["soil_depth"] == pytest.approx(15.0)
    # Linear in depth, so halving the metres halves the centimetres.
    assert shallow["gypsum_kg_per_ha"] == pytest.approx(
        deep["gypsum_kg_per_ha"] / 2, rel=1e-9
    )


def test_kernel_unit_is_untouched() -> None:
    """The engine kernel keeps centimetres; only the router changed.

    A caller that already speaks centimetres must still get the same answer,
    which is what removes the temptation to "fix" the kernel instead.
    """
    from services._gateway_facade import calculate_sodic_soil_amendment

    direct = calculate_sodic_soil_amendment(ESP, DEPTH_CM, BULK_DENSITY)
    via_router = _run_soil_salinity(_params())["sodic_amendment"]

    assert via_router["gypsum_kg_per_ha"] == pytest.approx(
        direct["gypsum_kg_per_ha"], rel=1e-12
    )


def test_other_salinity_payloads_are_not_narrowed() -> None:
    """The unit fix must not disturb the sibling salinity outputs."""
    result = _run_soil_salinity(_params(ec=6.0, ec_soil=6.0, ec_water=1.5))
    assert result["classification"]["classification"] == "moderately_saline"
    lr = result["leaching_requirement"]["leaching_fraction"]
    assert lr == pytest.approx(1.5 / (5 * 4.0 - 1.5), abs=1e-3)
