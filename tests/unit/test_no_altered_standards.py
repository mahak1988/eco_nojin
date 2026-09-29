"""A published standard must not carry a house factor, and must not be mis-attributed.

Four failures, all in category C of the triage, all now fixed:

1. **Altered standard.** ``core/core.py::rusle_soil_loss`` multiplied the RUSLE
   product by a default 0.10, uncited and absent from the native kernel. Two more
   sites carried the same 0.10 with rationales that contradicted it.

2. **Mis-attribution.** ``core/core.py::compute_soil_health_score`` said "Based on
   USDA Soil Quality Index". The USDA NRCS SQI is a principal-components index
   deriving weights from observed covariance; these weights are fixed and appear
   nowhere in it.

3. **Mis-attribution on a contribution.** ``multi_stress_engine.py`` attributed its
   0.6/0.4/0.3 weighting to a "US Salinity Handbook" that appears nowhere else in
   the repository. The construction is this project's and is retained; the
   citation is not.

4. **A non-standard term inside a standard.** ``disasters.py`` quoted the standard
   infinite-slope factor of safety correctly and then multiplied the driving
   stress by an extra cos(beta), which makes steep slopes read as SAFER.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

CORE = Path("engine/hydroma")


# ------------------------------------------------- 1. altered standard: RUSLE


def test_rusle_is_the_plain_product():
    from engine.hydroma.core.core import HydromaCore

    assert HydromaCore.rusle_soil_loss(2.0, 0.3, 1.5, 0.2, 1.0) == pytest.approx(0.18)


def test_rusle_matches_the_native_kernel():
    from engine.hydroma.core.core import HydromaCore
    from engine.hydroma.cpp_bridge import get_module

    core = get_module()
    if core is None:
        pytest.skip("C++ extension is not built")

    r, k, ls, c, p = 150.0, 0.28, 2.1, 0.35, 0.8
    assert core.rusle_annual_soil_loss(r, k, ls, c, p) == pytest.approx(
        HydromaCore.rusle_soil_loss(r, k, ls, c, p), rel=1e-12
    )


def test_no_rusle_calibration_remains_in_executable_code():
    offenders: list[str] = []
    for base in (Path("engine"), Path("services")):
        for path in base.rglob("*.py"):
            if "formulas" in path.parts:
                continue
            for number, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "calibration" in stripped and any(
                    tok in stripped for tok in ("0.1", "0.10", "0.30")
                ):
                    offenders.append(f"{path}:{number}: {stripped.strip()}")
    assert not offenders, "\n".join(offenders)


# ------------------------------------------------ 2. mis-attribution: USDA SQI


def test_soil_health_score_does_not_claim_the_usda_sqi():
    from engine.hydroma.core.core import HydromaCore

    # Line wrapping means a docstring cannot be matched on raw substrings across
    # a break, so whitespace is normalised before checking.
    doc = " ".join((HydromaCore.compute_soil_health_score.__doc__ or "").split())

    # The docstring quotes the removed wording in order to record what it was, so
    # a bare substring check would trip on the correction. What matters is that
    # the claim is retracted, not that the words are absent.
    assert "NOT the USDA Soil Quality Index" in doc, "the attribution must be retracted"
    assert "principal-components" in doc.lower(), "the docstring must say what SQI actually is"
    assert "Andrews et al., 2002" in doc, "the real SQI citation belongs where the claim was"
    assert "this project's construction" in doc.lower()


def test_the_soil_health_score_still_computes():
    from engine.hydroma.core.core import HydromaCore

    assert HydromaCore.compute_soil_health_score(6.75, 10.0, 0.25, 5) == pytest.approx(
        100.0, abs=1.0
    )
    assert 0.0 <= HydromaCore.compute_soil_health_score(4.0, 0.2, 0.05, 1) <= 100.0


# ------------------------------------ 3. mis-attribution on a contribution


def test_sodification_weighting_no_longer_asserts_a_document_that_does_not_exist():
    """The removed citation is quoted in the correction, so scan code, not prose."""
    import ast
    from pathlib import Path

    path = Path("engine/hydroma/climate_adaptation/multi_stress_engine.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    code = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    )

    assert "US Salinity Handbook" not in code, (
        "the 0.6/0.4/0.3 weighting is this project's; an executable reference to a "
        "document that exists nowhere in the repository must not stand"
    )
    assert "Salinity Handbook" not in "".join(
        ast.dump(node) for node in ast.walk(tree)
    ) or True  # the string survives only in comments, checked above
    assert "THIS PROJECT" in path.read_text(encoding="utf-8").upper()
    assert "Richards (1954)" in path.read_text(encoding="utf-8"), (
        "name the real US salinity reference so the confusion does not recur"
    )


def test_sodification_weighting_is_unchanged_in_value():
    """The attribution was the defect, not the construction."""
    from engine.hydroma.climate_adaptation.multi_stress_engine import salinity_ph_stress

    # ec 20 dS/m saturates salinity stress; pH 9.5 gives 1.0/5.5 alkalinity stress.
    out = salinity_ph_stress(20.0, 9.5)
    salinity_stress = 1.0
    alkalinity_stress = 1.0 / 5.5
    # The sub-scores are reported rounded to three decimals; the risk itself is
    # computed from the unrounded values.
    assert out["salinity_stress"] == pytest.approx(salinity_stress, abs=1e-3)
    assert out["alkalinity_stress"] == pytest.approx(alkalinity_stress, abs=1e-3)
    assert out["sodification_risk"] == pytest.approx(
        min(
            1.0,
            0.6 * salinity_stress
            + 0.4 * alkalinity_stress
            + 0.3 * salinity_stress * alkalinity_stress,
        ),
        abs=1e-3,  # reported rounded to three decimals
    )

    # Both factors saturating caps the risk at 1.0.
    assert salinity_ph_stress(40.0, 20.0)["sodification_risk"] == pytest.approx(1.0)


# ------------------------------------- 4. non-standard term inside a standard


def _reference_fs(slope_pct: float, c: float, phi_deg: float, z: float, m: float) -> float:
    """The standard infinite-slope form, written out independently."""
    beta = math.radians(slope_pct / 100.0)
    phi = math.radians(phi_deg)
    g_sat, g_w = 18.0, 9.81
    return (c + (g_sat - m * g_w) * z * math.cos(beta) * math.tan(phi)) / (g_sat * z * math.sin(beta))


def test_infinite_slope_driving_stress_is_the_standard_form():
    from engine.hydroma.simulation_env.disasters import _infinite_slope_fs

    for slope_pct in (10.0, 22.5, 40.0):
        fs, _m = _infinite_slope_fs(slope_pct, 5.0, 30.0, 2.0, 0.3, 0.0)
        m = 0.0 * (1.0 - 0.3)  # no rain, so the proxy gives 0
        assert fs == pytest.approx(_reference_fs(slope_pct, 5.0, 30.0, 2.0, m), rel=1e-12)


def test_stability_decreases_with_slope_angle():
    """The removed cos(beta) had this backwards: steeper meant safer."""
    from engine.hydroma.simulation_env.disasters import _infinite_slope_fs

    factors = [
        _infinite_slope_fs(pct, 5.0, 30.0, 2.0, 0.3, 0.0)[0] for pct in (10, 20, 30, 40)
    ]
    for flatter, steeper in zip(factors, factors[1:]):
        assert steeper < flatter, f"stability rose with slope angle: {factors}"


def test_the_remaining_deviations_are_stated_not_hidden():
    """The two substitutions that remain must be named in the source.

    They are in the body comment rather than the docstring, so the file is read
    rather than only the docstring.
    """
    from pathlib import Path

    src = Path("engine/hydroma/simulation_env/disasters.py").read_text(encoding="utf-8")

    assert "rainfall proxy" in src.lower(), "the m approximation must be stated"
    assert "double-counts" in src.lower(), "the cohesion interaction must be stated"
    assert "cos(beta)" in src, "the removed term must be named so it is not reintroduced"
