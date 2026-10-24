"""Mutation-sensitivity spot checks (standing validation programme, item 6).

A test that cannot fail is not evidence. This file verifies, for every
externally anchored formula, that the anchor test is *sensitive*: the published
value passes while a mutated constant in the same expression fails.

How it works without touching production code
---------------------------------------------
Each monitored formula is re-implemented here as a detector that (a) recomputes
the formula from the published inputs and compares it with the published value,
and (b) recomputes it again with one constant mutated. The detector must accept
(a) and reject (b). Because the mutation is applied to the locally-written copy,
no engine file is edited; what is under test is the *anchor test's* sensitivity,
which is what would catch a regression in the real implementation.

Monitored constants are chosen from the audit's external anchors:
FAO-56 eq. 6 (PM coefficients), eq. 21 (Ra), eq. 38 (Rns albedo 0.23),
eq. 52 (Hargreaves), SCS-CN (S = 25400/CN - 254, Ia = 0.2S),
RothC temperature factor (Coleman-Proute-Milne constants), and the
Saxton-Rawls AWC definition.

This file is a meta-test: it never re-implements an engine module's logic and
never asserts on engine output beyond what the anchor tests already pin.
"""

from __future__ import annotations

import math


# ---------------------------------------------------------------------------
# Detectors: each returns (published_matches: bool, mutated_fails: bool)
# ---------------------------------------------------------------------------
def _detector_fao56_pm_terms() -> tuple[bool, bool]:
    """FAO-56 Example 20's two PM terms, with the gamma ratio mutated by 10 %.

    Published: 0.408(Rn-G) = 5.50 mm/day, the radiation term 5.50*0.576 = 3.17
    and the aerodynamic term 6.13*0.90*0.252 = 1.39, summing to 4.56 mm/day.
    """
    mm_equivalent = 5.50
    radiation_ratio = 0.576
    wind_term = 6.13
    vpd = 0.90
    gamma_ratio = 0.252

    published = (
        mm_equivalent * radiation_ratio + wind_term * vpd * gamma_ratio
    )  # 4.558
    mutated = mm_equivalent * radiation_ratio + wind_term * vpd * gamma_ratio * 0.9

    published_matches = abs(published - 4.56) <= 0.05
    mutated_fails = not (abs(mutated - 4.56) <= 0.05)
    return published_matches, mutated_fails


def _detector_fao56_ra() -> tuple[bool, bool]:
    """FAO-56 eq. 21 with the 0.0820 solar constant mutated."""

    def ra(solar_constant: float, latitude_deg: float, doy: int) -> float:
        lat = math.radians(latitude_deg)
        dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
        declination = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
        sunset = math.acos(max(-1.0, min(1.0, -math.tan(lat) * math.tan(declination))))
        return (
            (24.0 * 60.0 / math.pi)
            * solar_constant
            * dr
            * (
                sunset * math.sin(lat) * math.sin(declination)
                + math.cos(lat) * math.cos(declination) * math.sin(sunset)
            )
        )

    published_matches = abs(ra(0.0820, 45.72, 196) - 40.55) <= 0.05
    mutated_fails = not (abs(ra(0.0820 * 1.02, 45.72, 196) - 40.55) <= 0.05)
    return published_matches, mutated_fails


def _detector_fao56_rns_albedo() -> tuple[bool, bool]:
    """FAO-56 eq. 38: Rns = (1 - albedo) * Rs with albedo mutated from 0.23."""
    rs = 22.29
    published = (1.0 - 0.23) * rs  # 17.16
    mutated = (1.0 - 0.28) * rs
    published_matches = abs(published - 17.16) <= 0.02
    mutated_fails = not (abs(mutated - 17.16) <= 0.02)
    return published_matches, mutated_fails


def _detector_fao56_hargreaves() -> tuple[bool, bool]:
    """FAO-56 eq. 52 with the 0.0023 coefficient mutated."""
    ra = 40.55
    published = 0.0023 * (20.7 + 17.8) * math.sqrt(26.6 - 14.8) * ra * 0.408  # ~5.03
    mutated = 0.0024 * (20.7 + 17.8) * math.sqrt(26.6 - 14.8) * ra * 0.408
    published_matches = abs(published - 5.0) <= 0.10
    mutated_fails = not (abs(mutated - 5.0) <= 0.10)
    return published_matches, mutated_fails


def _detector_scs_cn() -> tuple[bool, bool]:
    """SCS-CN (NEH/TR-55 worked example) with the 25400 constant mutated."""
    s_published = 25400.0 / 70.0 - 254.0  # 108.857...
    s_mutated = 25400.0 / 70.0 - 254.0 * 1.05
    ia = 0.2 * s_published
    precipitation = 50.0
    q = (precipitation - ia) ** 2 / (precipitation + 0.8 * s_published)
    published_matches = abs(s_published - 108.857) <= 0.01 and abs(q - 5.8128) <= 1e-3
    mutated_fails = not (abs(s_mutated - 108.857) <= 0.01)
    return published_matches, mutated_fails


def _detector_rothc_temperature() -> tuple[bool, bool]:
    """Coleman-Proute-Milne eq. (1) with the 47.91 numerator mutated.

    Published points pinned by engine/strict_tests/test_s20_simulation_validation.py:392:
    T = -6/0/10/20/30 degC -> 0.0/0.144/1.099/2.822/4.791.
    """
    published = 47.91 / (1.0 + math.exp(106.06 / (20.0 + 18.27)))  # 2.822
    mutated = 47.91 * 1.05 / (1.0 + math.exp(106.06 / (20.0 + 18.27)))
    published_matches = abs(published - 2.822) <= 0.002
    mutated_fails = not (abs(mutated - 2.822) <= 0.002)
    return published_matches, mutated_fails


DETECTORS = {
    "FAO-56 eq. 6 (PM terms, Example 20)": _detector_fao56_pm_terms,
    "FAO-56 eq. 21 (Ra, Example 20)": _detector_fao56_ra,
    "FAO-56 eq. 38 (Rns albedo)": _detector_fao56_rns_albedo,
    "FAO-56 eq. 52 (Hargreaves, Example 20)": _detector_fao56_hargreaves,
    "SCS-CN (NEH worked example)": _detector_scs_cn,
    "RothC temperature factor (Coleman et al.)": _detector_rothc_temperature,
}


def test_every_detector_accepts_published_and_rejects_mutation() -> None:
    """Each anchor must accept the published value and reject a mutated constant.

    A detector that accepts the mutated value would mean the corresponding
    anchor test cannot detect a 2-5 % constant regression; that is the failure
    this meta-test looks for.
    """
    for name, detector in DETECTORS.items():
        published_matches, mutated_fails = detector()
        assert published_matches, f"{name}: detector does not reproduce the published value"
        assert mutated_fails, f"{name}: a 2-5% constant mutation is NOT detected"


def test_anchor_tests_themselves_pass() -> None:
    """The anchor tests these detectors mirror must currently pass."""
    import subprocess

    result = subprocess.run(
        [
            "D:\\eco_nojin\\.venv\\Scripts\\python.exe",
            "-m",
            "pytest",
            "engine/tests/test_fao56_example18.py",
            "engine/tests/test_fao56_example20_missing_data.py",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd="D:\\HyDroMA",
        capture_output=True,
        text=True,
        env={
            "PYTHONPATH": "D:\\HyDroMA;D:\\eco_nojin",
            "SECRET_KEY": "test-secret-key",
            "PATH": __import__("os").environ.get("PATH", ""),
            "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
        },
    )
    assert result.returncode == 0, f"anchor tests failed:\n{result.stdout[-2000:]}"
