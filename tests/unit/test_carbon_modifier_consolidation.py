"""Tests for the consolidation of the carbon modifier and the dead core module.

Two duplicates were found and both are now closed.

``engine/hydroma/core.py`` was a module shadowed by the ``engine/hydroma/core/``
package of the same name, so it was unreachable: Python always resolves a package
over a same-named module. The package's own ``__init__`` documented the shadowing
but the old file was left behind, where anyone editing it would see no effect.

``HydromaCore.rothc_decomposition_rate_modifier`` was a second, divergent carbon
model carrying the RothC name. It computed a Q10 exponential of 2.0 about a 20 C
base with an ad-hoc clamp, and a four-step moisture ladder keyed on *annual
rainfall* rather than on soil-moisture deficit. The canonical RothC temperature
response is ``47.9 / (1 + exp(106.06 / (T + 18.27)))`` and its moisture response
is a continuous function of the monthly deficit. Two implementations of one named
quantity meant a caller got a different answer depending on which it reached.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from engine.hydroma.core import HydromaCore
from engine.hydroma.simulation.runners.rothc_runner import temp_factor, water_factor

# ------------------------------------------------------ the dead module is gone


def test_shadowed_core_module_no_longer_exists():
    """A module shadowed by a package of the same name is unreachable code."""
    from pathlib import Path

    assert not Path("engine/hydroma/core.py").exists(), (
        "engine/hydroma/core.py is shadowed by the core/ package, so it is dead code"
    )


def test_the_package_still_serves_the_public_api():
    import engine.hydroma.core as core

    assert core.__file__.endswith("core\\__init__.py") or core.__file__.endswith("core/__init__.py")
    assert hasattr(HydromaCore, "compute_rainfall_erosivity")
    assert hasattr(HydromaCore, "compute_crop_water_requirement")


# -------------------------------------------- the modifier matches canonical RothC


def test_delegates_to_the_canonical_temperature_response():
    """Regression: this used a Q10 of 2.0 about a 20 C base."""
    for mean_temp in (0.0, 5.0, 10.0, 20.0, 28.0):
        annual_rain, cover = 500.0, 1.0
        wetness = min(max(annual_rain / 1200.0, 0.0), 1.0)
        deficit = 60.0 * (1.0 - wetness)
        expected = temp_factor(mean_temp) * water_factor(deficit, 60.0) * cover

        got = HydromaCore.rothc_decomposition_rate_modifier(annual_rain, mean_temp, cover)

        assert got == pytest.approx(expected, rel=1e-12), (
            f"at {mean_temp} C the modifier is not the canonical RothC product"
        )


def test_is_not_a_q10_exponential():
    """A direct statement of the old behaviour, so it cannot return silently."""
    annual_rain, mean_temp, cover = 500.0, 20.0, 1.0
    old_q10 = 2.0 ** ((mean_temp - 20) / 10) * 0.7 * cover  # 20 C -> factor 1.0, ladder 0.7

    got = HydromaCore.rothc_decomposition_rate_modifier(annual_rain, mean_temp, cover)

    assert got != pytest.approx(old_q10, rel=1e-6)


def test_temperature_response_follows_the_implemented_curve():
    """Pins the response that is actually implemented.

    The shape is known to be wrong: it is monotonically increasing with
    temperature, where a RothC temperature response must peak and fall off. That
    is a science question needing the primary source (see the docstring on
    ``temp_factor`` and the registry record), so this test pins the measured
    behaviour rather than an unverified shape.
    """
    vals = {
        t: HydromaCore.rothc_decomposition_rate_modifier(500.0, t, 1.0)
        for t in (0.0, 5.0, 10.0, 20.0, 25.0, 30.0)
    }
    for t, v in vals.items():
        assert np.isfinite(v), f"modifier {v} at {t} C is not finite"
        assert v > 0.0, f"modifier {v} at {t} C is not positive"
    for warmer, cooler in zip(list(vals.values())[1:], list(vals.values())[:-1], strict=False):
        assert warmer > cooler, "the implemented response stops being increasing"


def test_low_temperature_follows_the_official_zero_cutoff():
    """RothC_Code hard-zeros RM_Tmp below -5 C. The pole at -18.27 C is never reached.

    A previous version of this file asserted the opposite: that -18.27 C raised a
    ZeroDivisionError and that -20 C returned 47.9. The first was a crash the model
    does not have (the official code zeroes), and the second was read off a
    temperature the model never evaluates.
    """
    from engine.hydroma.simulation.runners.rothc_runner import (
        TEMP_FACTOR_ZERO_BELOW_C,
        temp_factor,
    )

    assert temp_factor(-6.0) == 0.0
    assert temp_factor(-20.0) == 0.0
    assert temp_factor(TEMP_FACTOR_ZERO_BELOW_C) > 0.0, "the cut-off is below -5 C, not at it"
    assert np.isfinite(temp_factor(-4.9))


def test_the_expression_is_the_canonical_rothc_form():
    """Guards against 'correcting' the reciprocal form, which is not an error.

    The Rothamsted model description section 1.6.1 gives
    RM_Tmp = 47.91 / (1 + e^(106.06/(T+18.27))), hard-coded identically in the
    official Fortran, Python and R. An earlier revision of this file asserted the
    shape was wrong; that assertion was withdrawn twice and is replaced by this
    one.
    """
    import inspect

    from engine.hydroma.simulation.runners.rothc_runner import temp_factor

    doc = inspect.getdoc(temp_factor) or ""
    assert "withdrawn" in doc.lower(), "the retraction must stay in the docstring"
    assert "47.91" in doc, "the published numerator must be stated"
    assert "no optimum" in doc.lower()

    # The reciprocal structure, stated so a future edit cannot quietly change it.
    assert temp_factor(20.0) == pytest.approx(47.91 / (1.0 + np.exp(106.06 / 38.27)))


def test_open_scaling_question_is_settled():
    """The numerator was the open question; it is now a cited constant."""
    from engine.hydroma.formulas import get

    assert "NUMERATOR UNVERIFIED" not in (get("rothc_temperature_modifier").literature_ref)

    record = get("rothc_temperature_modifier")
    assert record.is_verified, "the temperature modifier is now sourced and verified"
    assert "47.91" in record.notes
    assert "withdrawn" in record.notes.lower()


def test_response_increases_with_temperature_which_is_the_measured_behaviour():
    vals = [
        HydromaCore.rothc_decomposition_rate_modifier(600.0, t, 1.0)
        for t in (0.0, 10.0, 20.0, 30.0)
    ]
    for prev, nxt in itertools.pairwise(vals):
        assert nxt > prev, "the implemented response stops increasing with temperature"


def test_cover_scales_the_result_linearly():
    bare = HydromaCore.rothc_decomposition_rate_modifier(600.0, 18.0, 0.2)
    dense = HydromaCore.rothc_decomposition_rate_modifier(600.0, 18.0, 0.8)

    assert dense == pytest.approx(4 * bare, rel=1e-9)


def test_moisture_responds_to_rainfall_through_the_deficit():
    dry = HydromaCore.rothc_decomposition_rate_modifier(0.0, 15.0, 1.0)
    wet = HydromaCore.rothc_decomposition_rate_modifier(2400.0, 15.0, 1.0)

    assert wet > dry, "more water must not slow decomposition"


def test_result_is_positive_and_finite():
    for annual_rain in (0.0, 300.0, 3000.0):
        for mean_temp in (0.0, 15.0, 30.0):
            v = HydromaCore.rothc_decomposition_rate_modifier(annual_rain, mean_temp)
            assert np.isfinite(v)
            assert v > 0.0


def test_source_does_not_reimplement_the_rothc_equations():
    """No second copy of the science may live in the facade."""
    import inspect

    src = inspect.getsource(HydromaCore.rothc_decomposition_rate_modifier)
    assert "2.0 ** ((mean_temp_c - 20) / 10)" not in src, "the Q10 exponential is back"
    assert "annual_rainfall_mm < 400" not in src, "the rainfall-keyed moisture ladder is back"
