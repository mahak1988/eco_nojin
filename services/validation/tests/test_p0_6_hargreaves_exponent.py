"""P0-6 -- the public FAO-56 eq. 52 check uses the published exponent.

``services/validation/formula_checks.py:211`` computed the Hargreaves ET0
identity with exponent **0.48** and its ``source`` string claimed "FAO publishes
0.48". FAO-56 eq. 52 prints ``(Tmax - Tmin)^0.5`` with Ra in mm/day; the engine
and the services strict suite (``test_s17_service_strict.py:159``) both pin
5.279098340839128 for Tmin 10 / Tmax 25 / lat 40 / DOY 150.

Before the fix the endpoint answered ``expected 5.00078205064849`` vs
``actual 5.279098340839128`` and ``passed: false`` at
``GET /api/v1/hydroma/validation``.
"""

from __future__ import annotations

import math

import pytest

from services.validation.formula_checks import run_all

#: The value the services strict suite pins for Tmin 10 / Tmax 25 / lat 40 / doy 150.
HARGREAVES_EXPECTED = 5.279098340839128


def _check(check_id: str) -> dict:
    summary = run_all()
    match = [c for c in summary["checks"] if c["id"] == check_id]
    assert match, f"check {check_id} not found in {[c['id'] for c in summary['checks']]}"
    return match[0]


def test_fao56_hargreaves_check_passes() -> None:
    check = _check("fao56_hargreaves")
    assert check["passed"] is True
    assert check["actual"] == pytest.approx(HARGREAVES_EXPECTED, rel=1e-9)
    assert check["expected"] == pytest.approx(HARGREAVES_EXPECTED, rel=1e-9)


def test_checker_source_does_not_claim_fao_publishes_0_48() -> None:
    check = _check("fao56_hargreaves")
    assert "0.48" not in check["source"]


def test_expression_uses_the_published_half_exponent() -> None:
    """The pinned value is the eq. 52 value with the 0.5 power and the 0.408
    MJ -> mm conversion, re-derived independently of the engine's own
    ``_hargreaves_core``.

    The module-level helpers this test used to call were removed from
    ``formula_checks`` when it was reduced to the ``run_all`` summary, so the
    extraterrestrial radiation is derived here from FAO-56 eq. 21 — which is
    the point of the test: a derivation the engine does not share.
    """
    t_min, t_max, t_mean = 10.0, 25.0, 17.5
    latitude, doy = 40.0, 150

    lat = math.radians(latitude)
    solar_constant = 0.0820  # MJ m^-2 min^-1
    inverse_relative_distance = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    solar_declination = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    sunset_hour_angle = math.acos(-math.tan(lat) * math.tan(solar_declination))
    ra_mj = (
        (24 * 60 / math.pi)
        * solar_constant
        * inverse_relative_distance
        * (
            sunset_hour_angle * math.sin(lat) * math.sin(solar_declination)
            + math.cos(lat) * math.cos(solar_declination) * math.sin(sunset_hour_angle)
        )
    )
    reference = 0.0023 * (t_mean + 17.8) * math.sqrt(t_max - t_min) * ra_mj * 0.408
    assert reference == pytest.approx(HARGREAVES_EXPECTED, rel=1e-9)

    # And the published check agrees with that re-derivation, not with the
    # 0.48 form: the endpoint reports the same value as its ``actual``.
    assert _check("fao56_hargreaves")["actual"] == pytest.approx(reference, rel=1e-9)


def test_every_check_passes_end_to_end() -> None:
    """The endpoint's aggregate result must not be red on this item any more."""
    summary = run_all()
    assert summary["failed"] == 0, [c["id"] for c in summary["checks"] if not c["passed"]]
    assert summary["passed"] == summary["total"]
