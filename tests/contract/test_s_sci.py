"""Tests for the S-SCI formula registry.

Every formula is pinned against a hand calculation or a published value, so a
refactor cannot silently change a published scientific number. The registry
mechanics are pinned too: a formula without a reference is refused, and a
duplicate registration is refused.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from services._contracts import formula as f


#: The reference Williams implementation as it appears in
#: ``services/satellite/soilgrids.py``. Kept here so the registry can be
#: checked against the code the point chain actually runs.
def _williams_ref(sand_pct: float, silt_pct: float, clay_pct: float, soc_g_kg: float) -> float:
    c = soc_g_kg / 1000.0
    sn = 1.0 - sand_pct / 100.0
    return (
        0.1317
        * (0.2 + 0.3 * math.exp(-0.0256 * sand_pct * (1.0 - silt_pct / 100.0)))
        * (silt_pct / (silt_pct + clay_pct)) ** 0.3
        * (1.0 - 0.25 * c / (c + math.exp(3.72 - 2.95 * c)))
        * (1.0 - 0.7 * sn / (sn + math.exp(-5.51 + 22.9 * sn)))
    )


class TestRegistryMechanics:
    def test_every_formula_carries_a_reference_and_units(self):
        assert f.FORMULAS, "registry should not be empty"
        for name, formula in f.FORMULAS.items():
            assert formula.reference.strip(), f"{name} has no reference"
            assert formula.units.strip(), f"{name} has no units"

    def test_a_blank_reference_is_refused(self):
        with pytest.raises(ValueError, match="requires a non-empty reference"):
            f.register("test.no_ref", lambda: 1.0, reference="  ", units="x")

    def test_duplicate_registration_is_refused(self):
        with pytest.raises(ValueError, match="already registered"):
            f.register("rusle.ls", lambda x: x, reference="r", units="u")

    def test_lookup_reports_what_is_registered(self):
        with pytest.raises(KeyError, match="registered:"):
            f.lookup("rusle.does_not_exist")

    def test_the_expected_quantities_are_present(self):
        assert {
            "rusle.ls",
            "rusle.r",
            "scs.runoff",
            "rusle.erosion_class",
            # Both EPIC-labelled K forms are registered separately: they are
            # different equations, not variants of one.
            "rusle.k.renard1997",
            "rusle.k.williams1995",
        } <= set(f.FORMULAS)

    def test_displaced_implementations_are_named(self):
        """Each formula records what it replaces, so the debt is traceable."""
        assert any("soil_fetcher" in r for r in f.lookup("rusle.k.renard1997").replaces)
        assert any("chain_runner" in r for r in f.lookup("rusle.ls").replaces)
        assert any("soilgrids" in r for r in f.lookup("rusle.k.williams1995").replaces)
        assert any("chain_runner" in r for r in f.lookup("rusle.erosion_class").replaces)


class TestLsFactor:
    @pytest.mark.parametrize(
        ("slope_deg", "expected"),
        [
            (0.0, 0.065),
            (1.0, 0.1645),
            (2.0, 0.3038),
            (3.0, 0.4828),
            (5.0, 0.9593),
            (10.0, 2.8292),
            (20.0, 9.2761),
            (30.0, 18.6975),
            (45.0, 35.9944),
            (80.0, 67.9934),
        ],
    )
    def test_matches_foster_nearing(self, slope_deg: float, expected: float):
        sin_b = math.sin(math.radians(slope_deg))
        exact = 65.41 * sin_b**2 + 4.56 * sin_b + 0.065
        assert f.ls_factor(slope_deg) == pytest.approx(exact, abs=1e-9)
        assert f.ls_factor(slope_deg) == pytest.approx(expected, abs=1e-3)

    def test_is_monotonic_over_the_whole_range(self):
        """The property that disqualifies the Wischmeier & Smith form.

        That relation is non-monotonic below ~3 degrees: it peaks near 2
        degrees and then decreases, so a steeper slope would reduce erosion.
        """
        slopes = [0, 0.5, 1, 2, 2.9, 3.0, 3.1, 5, 10, 20, 30, 45, 60, 80, 89]
        values = [f.ls_factor(s) for s in slopes]
        for previous, current, slope in zip(values, values[1:], slopes[1:], strict=False):
            assert current > previous, f"LS did not increase at slope {slope}"

    def test_the_displaced_wischmeier_smith_form_really_would_have_decreased(self):
        """Confirms the choice was necessary, not preference."""

        def raw(s: float) -> float:
            sin_b = math.sin(math.radians(s))
            return (9.8 * sin_b + 0.03) / (16.8 * sin_b - 0.50)

        assert raw(2.0) > raw(5.0), "W-S is non-monotonic below 3 degrees"

    def test_the_two_relations_cannot_be_spliced(self):
        """They disagree ~3.7x at 3 degrees, so a piecewise switch would
        introduce a discontinuity larger than the disagreement."""
        at_three = f.ls_factor(3.0)
        ws_at_three = f.ls_factor_wischmeier_smith(3.0)
        assert ws_at_three / at_three > 2.5

    def test_wischmeier_smith_refuses_its_undefined_range(self):
        """The denominator 16.8*sin(b) - 0.5 crosses zero at ~1.71 degrees."""
        with pytest.raises(ValueError, match="undefined at"):
            f.ls_factor_wischmeier_smith(1.0)
        with pytest.raises(ValueError, match="undefined at"):
            f.ls_factor_wischmeier_smith(1.7)

    def test_wischmeier_smith_still_works_where_it_is_valid(self):
        sin_b = math.sin(math.radians(10))
        assert f.ls_factor_wischmeier_smith(10) == pytest.approx(
            (9.8 * sin_b + 0.03) / (16.8 * sin_b - 0.50), abs=1e-9
        )

    def test_takes_degrees_not_percent(self):
        """chain_runner used a polynomial in slope PERCENT with no trig."""
        assert f.ls_factor(10) != pytest.approx(0.065 + 0.045 * 10 + 0.0065 * 10**2)

    def test_rejects_a_negative_slope(self):
        with pytest.raises(ValueError, match="slope_deg"):
            f.ls_factor(-1)


class TestKFactorEpic:
    def test_matches_renard_hand_calculation(self):
        # soc 15 g/kg == 1.5 %, clay 30 %, silt 40 %
        soc_pct = 1.5
        raw = (
            0.2 + 0.3 * (soc_pct / 100) ** 2 + 0.3 * (1 - soc_pct / 100) ** 2 + 0.025 * (30 + 40)
        ) * 0.1317
        assert f.k_factor_epic(15, 30, 40) == pytest.approx(min(raw, f.K_BOUNDS[1]), abs=1e-9)

    def test_does_not_saturate_for_real_soils(self):
        """Regression guard.

        The bound was 0.09, which is the ceiling
        ``services/satellite/soilgrids.py`` clips to — but that file uses the
        *multiplicative* Williams form, a different equation with a narrower
        output band. Applying its ceiling to the Renard polynomial clipped
        **every** real texture to 0.09, so three migrated call sites returned
        a constant and a soil-erosion raster came out flat.
        """
        values = {
            f.k_factor_epic(oc, clay, silt)
            for clay in (10, 20, 30, 40)
            for silt in (20, 30, 40)
            for oc in (5, 15, 30)
        }
        assert len(values) > 5, f"K is saturating: only {len(values)} distinct values"
        for value in values:
            assert value < f.K_BOUNDS[1], f"{value} is pinned to the ceiling"
            assert value > f.K_BOUNDS[0]

    def test_increases_with_fine_fraction(self):
        coarse = f.k_factor_epic(5, 10, 10)
        loam = f.k_factor_epic(10, 30, 30)
        clay = f.k_factor_epic(15, 50, 35)
        assert coarse < loam < clay

    def test_soc_is_read_on_a_g_per_kg_scale(self):
        """1 % organic carbon == 10 g/kg, so the function's own scale is
        verifiable: 10 g/kg must reproduce the 1 % hand calculation above, and
        1 g/kg (i.e. 0.1 %) must give a different, lower value.

        The earlier version of this test asserted ``(10, ...) == (1.0, ...)``,
        which is false — 1.0 g/kg is 0.1 %, not 1 %.
        """
        one_percent = f.k_factor_epic(10, 20, 30)
        tenth_percent = f.k_factor_epic(1.0, 20, 30)
        assert one_percent != pytest.approx(tenth_percent, abs=1e-6)
        # More organic carbon means less erodible, so the 1 % value is lower.
        assert one_percent < tenth_percent
        # And the hand calculation for 1.5 % / clay 30 / silt 40 agrees.
        assert f.k_factor_epic(15, 30, 40) == pytest.approx(0.2952, abs=5e-4)

    def test_stays_within_the_literature_range(self):
        for soc in (0, 5, 15, 50, 200):
            value = f.k_factor_epic(soc, 20, 30)
            assert f.K_BOUNDS[0] <= value <= f.K_BOUNDS[1]

    def test_rejects_impossible_textures(self):
        with pytest.raises(ValueError, match="clay_pct"):
            f.k_factor_epic(10, 120, 30)
        with pytest.raises(ValueError, match="silt_pct"):
            f.k_factor_epic(10, 20, -5)

    def test_rejects_negative_soc(self):
        with pytest.raises(ValueError, match="soc_g_per_kg"):
            f.k_factor_epic(-1, 20, 30)

    def test_the_two_epic_forms_are_separately_registered(self):
        """Williams 1995 multiplicative and Renard 1997 additive are different
        equations, not variants of one. They disagree by a factor of about 6.8
        for a loam — measured, not estimated.
        """
        assert f.lookup("rusle.k.renard1997") is not f.lookup("rusle.k.williams1995")
        for name in ("rusle.k.renard1997", "rusle.k.williams1995"):
            assert f.lookup(name).reference.strip(), f"{name} has no citation"

    def test_the_measured_ratio_between_the_two_k_forms(self):
        """Pins the number the registry's warning quotes.

        Loam, SOC 15 g/kg: Williams 0.043335, Renard 0.295157 -> 6.811x.
        An earlier version of this test asserted "roughly 3.6x" from a
        hand-typed copy of the Williams form that divided by `clay` instead of
        `clay + silt` -- a third equation that exists nowhere in the tree.
        """
        williams = f.k_factor_williams(sand_pct=30, silt_pct=40, clay_pct=30, soc_g_per_kg=15)
        renard = f.k_factor_epic(15, 30, 40)
        assert williams == pytest.approx(0.043335, abs=1e-6)
        assert renard == pytest.approx(0.295157, abs=1e-6)
        assert renard / williams == pytest.approx(6.811, rel=0.01)

    def test_the_williams_form_divides_by_silt_plus_clay(self):
        """Guards the mistake the old inline copy made."""
        # Halving the fine fraction must change the answer; if the divisor were
        # `clay` alone, silt would drop out of t2 entirely.
        a = f.k_factor_williams(30, 40, 30, 15)
        b = f.k_factor_williams(30, 20, 30, 15)
        assert a != pytest.approx(b, rel=1e-6), "silt_pct must reach the formula"

    def test_the_point_chain_reads_the_williams_form(self):
        """Which K the live chain uses, so a future standardisation is a
        deliberate decision rather than an accident."""
        source = (
            Path(__file__).resolve().parents[2] / "services" / "satellite" / "soilgrids.py"
        ).read_text(encoding="utf-8")
        assert "def rusle_k_factor" in source, "the chain's K entry point moved"
        assert f.k_factor_williams(30, 40, 30, 15) == pytest.approx(
            min(max(_williams_ref(30, 40, 30, 15), f.K_BOUNDS_WILLIAMS[0]), f.K_BOUNDS_WILLIAMS[1]),
            abs=1e-9,
        ), "the registry's Williams must match what soilgrids computes"


class TestRFactor:
    def test_matches_fournier(self):
        assert f.r_factor(1000) == pytest.approx(0.0534 * 1000**2, abs=1e-6)

    def test_is_not_clamped(self):
        """A bound tight enough to look plausible would reject the relation's
        own output; silently clipping a computed physical quantity is the
        failure mode S-HONEST exists to prevent."""
        assert f.r_factor(1000) > 500.0

    def test_rejects_negative_precipitation(self):
        with pytest.raises(ValueError, match="annual_precip_mm"):
            f.r_factor(-1)


class TestErosionClass:
    @pytest.mark.parametrize(
        ("loss", "label"),
        [
            (0.0, "negligible"),
            (4.9, "negligible"),
            (5.0, "low"),
            (11.9, "low"),
            (12.0, "moderate"),
            (24.9, "moderate"),
            (25.0, "high"),
            (49.9, "high"),
            (50.0, "very_high"),
        ],
    )
    def test_thresholds(self, loss: float, label: str):
        assert f.erosion_class(loss) == label

    def test_the_discarded_thresholds_differed(self):
        """chain_runner used 5/10/20, so 15 t/ha/yr was 'high' there and 'moderate' here."""
        assert f.erosion_class(15) == "moderate"


class TestRunoffScs:
    def test_matches_the_tr55_hand_calculation(self):
        retention = 25400.0 / 75 - 254.0
        ia = 0.2 * retention
        expected = (80.0 - ia) ** 2 / (80.0 + 0.8 * retention)
        assert f.runoff_scs(80, 75) == pytest.approx(expected, abs=1e-9)

    def test_no_runoff_below_the_initial_abstraction(self):
        retention = 25400.0 / 75 - 254.0
        assert f.runoff_scs(0.2 * retention, 75) == 0.0

    def test_perfect_drainage_curve_gives_full_runoff(self):
        retention = 25400.0 / 100 - 254.0
        assert f.runoff_scs(1000, 100) == pytest.approx(1000 - 0.2 * retention, abs=1e-6)

    def test_increases_with_precipitation(self):
        values = [f.runoff_scs(p, 70) for p in (20, 50, 100, 200)]
        assert values == sorted(values)

    def test_rejects_an_invalid_curve_number(self):
        with pytest.raises(ValueError, match="curve_number"):
            f.runoff_scs(50, 10)

    def test_rejects_negative_precipitation(self):
        with pytest.raises(ValueError, match="precip_mm"):
            f.runoff_scs(-5, 75)
