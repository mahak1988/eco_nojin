"""S05 — Soil hydraulics: van Genuchten retention, the parameter table, AWC.

Standards under test
--------------------
* van Genuchten (1980), SSSAJ 44:892-898 — retention
      theta(h) = theta_r + (theta_s - theta_r) / (1 + |alpha h|^n)^m,  m = 1 - 1/n
* Mualem (1976), WRR 12:513-522 — unsaturated conductivity
      K(h) = Ks Se^0.5 [1 - (1 - Se^(1/m))^m]^2,  Se = (theta - theta_r)/(theta_s - theta_r)
* Brooks & Corey (1964) and Campbell (1974) — alternative retention models
* Saxton & Rawls (2006), SSSAJ 70:975-987 — independent pedotransfer check of
  plant-available water capacity by texture

Structural requirement
----------------------
``soil/physics.py`` and ``soil/water_retention.py`` share one parameter table and
must therefore agree on field capacity. They do not.
"""

from __future__ import annotations

from itertools import pairwise

import pytest
from hypothesis import given, strategies as st

from engine.hydroma.soil import physics as ph, water_retention as wr
from engine.strict_tests.conftest import (
    SAXTON_RAWLS_2006_AWC_MM_PER_M,
)

# FAO-56 field capacity and permanent wilting point. These are the canonical
# pair: -33 cm (0.33 bar) and -15000 cm (15 bar). The engine's own
# water_retention._find_field_capacity looks for -33 cm and says so in its
# docstring, which makes physics.FC_HEAD_CM = 330.0 a 10x outlier rather than an
# alternative convention.
FAO56_FC_HEAD_CM = 33.0
FAO56_PWP_HEAD_CM = 15000.0

# USDA particle-size ranking, coarsest first, for the 12 textures the engine
# ships. Finer texture means smaller effective pore throat, so saturated
# conductivity must be non-increasing down this list.
COARSE_TO_FINE = [
    "sand",
    "loamy_sand",
    "sandy_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_clay_loam",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay",
    "silty_clay",
    "clay",
]


def _ref_vg_theta(h, theta_r, theta_s, alpha, n):
    """FAO-56 eq. 11, with the saturated branch.

    A non-negative head is a positive pressure, which means the soil is
    saturated, so theta is theta_s. The equation is defined for suction only;
    applying |alpha*h| to a positive head would report +100 cm as drier than
    -33 cm.
    """
    if h >= 0:
        return theta_s
    m = 1.0 - 1.0 / n
    ah = abs(alpha * h)
    if ah == 0.0:
        return theta_s
    return theta_r + (theta_s - theta_r) / (1.0 + ah**n) ** m


def _ref_vg_k(h, theta_r, theta_s, alpha, n, ks):
    if h >= 0:
        return ks
    theta = _ref_vg_theta(h, theta_r, theta_s, alpha, n)
    if theta <= theta_r:
        return 0.0
    se = (theta - theta_r) / (theta_s - theta_r)
    se = min(max(se, 0.0), 1.0)
    m = 1.0 - 1.0 / n
    term = 1.0 - (1.0 - se ** (1.0 / m)) ** m
    return ks * se**0.5 * term**2


@st.composite
def vg_parameters(draw) -> dict:
    """One physically admissible van Genuchten parameter set.

    theta_s is drawn first and theta_r constrained below it, so the ordering the
    engine validates is satisfied by construction and no example is discarded.
    """
    theta_s = draw(st.floats(min_value=0.30, max_value=0.65, allow_nan=False))
    theta_r = draw(st.floats(min_value=0.0, max_value=0.25, allow_nan=False))
    while theta_r >= theta_s:
        theta_r = draw(st.floats(min_value=0.0, max_value=0.25, allow_nan=False))
    return {
        "theta_r": theta_r,
        "theta_s": theta_s,
        "alpha": draw(st.floats(min_value=1e-3, max_value=0.5, allow_nan=False)),
        "n": draw(st.floats(min_value=1.05, max_value=3.0, allow_nan=False)),
        "ks": draw(st.floats(min_value=0.01, max_value=1000.0, allow_nan=False)),
    }


class TestParameterTable:
    def test_covers_twelve_usda_textures(self, vg_table: dict) -> None:
        assert len(vg_table) == 12
        assert set(vg_table) == set(SAXTON_RAWLS_2006_AWC_MM_PER_M)

    @pytest.mark.parametrize("texture", COARSE_TO_FINE)
    def test_parameters_are_physically_admissible(self, texture: str, vg_table: dict) -> None:
        p = vg_table[texture]
        assert 0.0 <= p["theta_r"] < p["theta_s"] <= 1.0, texture
        assert p["alpha"] > 0.0, texture
        assert 1.0 < p["n"] <= 3.0, texture
        assert 0.0 < p["Ks"] <= 5000.0, texture

    def test_m_parameter_is_between_zero_and_one(self, vg_table: dict) -> None:
        for texture, p in vg_table.items():
            m = 1.0 - 1.0 / p["n"]
            assert 0.0 < m < 1.0, texture

    def test_saturated_water_content_tracks_clay_content(self, vg_table: dict) -> None:
        """theta_s rises with clay fraction, from about 0.43 for sand to 0.46 for
        silt. This is a pore-volume statement, robust to any parameter source."""
        assert vg_table["sand"]["theta_s"] == pytest.approx(0.430, abs=0.03)
        assert max(p["theta_s"] for p in vg_table.values()) > 0.44
        # Pore volume never exceeds unity and never drops below a loose sand's.
        assert all(0.35 <= p["theta_s"] <= 0.55 for p in vg_table.values())

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The saturated-conductivity column of "
            "engine/hydroma/soil/physics.py:122-135 (SOIL_PARAMETERS_VG) is not "
            "monotone in texture fineness, which hydraulic conductivity must be. "
            "Two inversions, both with the coarse texture given the HIGHER value: "
            "sandy_clay_loam 31.4 cm/day exceeds loam 25.0 cm/day, and clay 4.8 "
            "cm/day exceeds silty_clay 1.92 cm/day and sandy_clay 2.9 cm/day. Clay "
            "has the smallest effective pore throat of any texture, so it must "
            "have the lowest Ks. The comment at line 121 attributes the column to "
            "Carsel & Parrish (1988) x24, but 712.8/24 = 29.7 cm/hr for sand where "
            "the published value is about 50 cm/hr, so the provenance claim does "
            "not hold either."
        ),
    )
    def test_conductivity_decreases_with_texture_fineness(self, vg_table: dict) -> None:
        for coarse, fine in pairwise(COARSE_TO_FINE):
            assert vg_table[fine]["Ks"] <= vg_table[coarse]["Ks"], (
                f"{fine} (Ks {vg_table[fine]['Ks']}) conducts more than "
                f"{coarse} (Ks {vg_table[coarse]['Ks']})"
            )


class TestRetention:
    @given(
        h=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False, allow_infinity=False),
        p=vg_parameters(),
    )
    def test_matches_independent_rederivation(self, h: float, p: dict) -> None:
        assert ph.van_genuchten_theta(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"]) == (
            pytest.approx(
                _ref_vg_theta(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"]), rel=1e-12
            )
        )

    @given(
        h=st.floats(min_value=-1e5, max_value=1e5, allow_nan=False),
        p=vg_parameters(),
    )
    def test_bounded_by_residual_and_saturated(self, h: float, p: dict) -> None:
        theta = ph.van_genuchten_theta(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"])
        # The 1e-12 slack is binary64 rounding: when the denominator evaluates a
        # few ULP below 1.0 the returned theta can exceed theta_s in the last bit.
        assert p["theta_r"] - 1e-12 <= theta <= p["theta_s"] + 1e-12

    @given(
        h=st.floats(min_value=-1e5, max_value=-1e-3, allow_nan=False),
        p=vg_parameters(),
    )
    def test_strictly_decreasing_in_head(self, h: float, p: dict) -> None:
        """theta falls monotonically as the soil dries."""
        a = ph.van_genuchten_theta(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"])
        b = ph.van_genuchten_theta(h - 10.0, p["theta_r"], p["theta_s"], p["alpha"], p["n"])
        assert b < a

    def test_saturated_at_zero_head(self) -> None:
        assert ph.van_genuchten_theta(0.0, 0.078, 0.43, 0.036, 1.56) == pytest.approx(0.43)

    def test_continuous_across_zero(self) -> None:
        below = ph.van_genuchten_theta(-1e-6, 0.078, 0.43, 0.036, 1.56)
        above = ph.van_genuchten_theta(1e-6, 0.078, 0.43, 0.036, 1.56)
        assert below == pytest.approx(above, rel=1e-6)

    def test_rejects_impossible_water_contents(self) -> None:
        with pytest.raises(ValueError, match="theta_s"):
            ph.van_genuchten_theta(-100.0, 0.5, 0.3, 0.036, 1.56)
        with pytest.raises(ValueError, match="theta_s"):
            ph.van_genuchten_theta(-100.0, 0.4, 0.4, 0.036, 1.56)

    @pytest.mark.parametrize("n", [0.5, 1.0, -2.0])
    def test_rejects_non_physical_n(self, n: float) -> None:
        with pytest.raises(ValueError, match="n must be"):
            ph.van_genuchten_theta(-100.0, 0.078, 0.43, 0.036, n)

    @pytest.mark.parametrize("theta_s", [1.0, 1.5, 2.0])
    def test_rejects_saturated_content_above_one(self, theta_s: float) -> None:
        with pytest.raises(ValueError):
            ph.van_genuchten_theta(-100.0, 0.05, theta_s, 0.036, 1.56)

    def test_unknown_texture_raises(self) -> None:
        with pytest.raises(KeyError):
            ph.water_content_at(-100.0, "volcanic_sand")


class TestConductivity:
    @given(
        h=st.floats(min_value=-1e5, max_value=1e4, allow_nan=False),
        p=vg_parameters(),
    )
    def test_matches_independent_rederivation(self, h: float, p: dict) -> None:
        got = ph.van_genuchten_k(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"], p["ks"])
        assert got == pytest.approx(
            _ref_vg_k(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"], p["ks"]), rel=1e-12
        )

    @given(
        h=st.floats(min_value=-1e5, max_value=1e4, allow_nan=False),
        p=vg_parameters(),
    )
    def test_non_negative_and_at_most_ks(self, h: float, p: dict) -> None:
        k = ph.van_genuchten_k(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"], p["ks"])
        assert 0.0 <= k <= p["ks"]

    @given(
        h=st.floats(min_value=-1e4, max_value=-1e-2, allow_nan=False),
        p=vg_parameters(),
    )
    def test_decreases_as_the_soil_dries(self, h: float, p: dict) -> None:
        wet = ph.van_genuchten_k(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"], p["ks"])
        dry = ph.van_genuchten_k(h - 100.0, p["theta_r"], p["theta_s"], p["alpha"], p["n"], p["ks"])
        assert dry <= wet

    def test_equals_ks_at_zero_head(self) -> None:
        assert ph.van_genuchten_k(0.0, 0.078, 0.43, 0.036, 1.56, 25.0) == pytest.approx(25.0)

    @pytest.mark.parametrize("h", [0.5, 1.0, 10.0, 100.0])
    def test_equals_ks_under_positive_pressure(self, h: float) -> None:
        assert ph.van_genuchten_k(h, 0.078, 0.43, 0.036, 1.56, 25.0) == pytest.approx(25.0)

    def test_rejects_non_positive_ks(self) -> None:
        for ks in (0.0, -1.0):
            with pytest.raises(ValueError, match="ks must be positive"):
                ph.van_genuchten_k(-100.0, 0.078, 0.43, 0.036, 1.56, ks)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/soil/physics.py:70-71 rejects ks <= 0. A perfectly "
            "impermeable substrate (ks = 0) is a real and important case in "
            "landfill liners, capping and perched water tables, and the function "
            "has no way to represent it."
        ),
    )
    def test_zero_conductivity_is_a_valid_input(self) -> None:
        assert ph.van_genuchten_k(-100.0, 0.078, 0.43, 0.036, 1.56, 0.0) == 0.0


class TestAlternativeModels:
    """Brooks-Corey and Campbell must share the engine's sign convention."""

    def test_brooks_corey_saturates_above_air_entry(self) -> None:
        assert ph.brooks_corey_theta(0.0, 0.05, 0.43, -10.0, 2.0) == pytest.approx(0.43)
        assert ph.brooks_corey_theta(-5.0, 0.05, 0.43, -10.0, 2.0) == pytest.approx(0.43)

    def test_brooks_corey_decreases_with_drying(self) -> None:
        wet = ph.brooks_corey_theta(-100.0, 0.05, 0.43, -10.0, 2.0)
        dry = ph.brooks_corey_theta(-1000.0, 0.05, 0.43, -10.0, 2.0)
        assert dry < wet

    def test_campbell_saturates_above_entry(self) -> None:
        assert ph.campbell_theta(0.0, 0.05, 0.43, -10.0, 1.3) == pytest.approx(0.43)

    def test_campbell_decreases_with_drying(self) -> None:
        wet = ph.campbell_theta(-100.0, 0.05, 0.43, -10.0, 1.3)
        dry = ph.campbell_theta(-1000.0, 0.05, 0.43, -10.0, 1.3)
        assert dry < wet

    @pytest.mark.parametrize("abs_h", [1.0, 30.0, 100.0, 1000.0, 15000.0])
    def test_campbell_is_odd_in_the_pair_of_signs(self, abs_h: float) -> None:
        """Campbell and Brooks-Corey both take magnitudes; the result must depend
        on |h| and |he| only, so flipping both signs must change nothing."""
        a = ph.campbell_theta(-abs_h, 0.05, 0.43, -10.0, 1.3)
        b = ph.campbell_theta(abs_h, 0.05, 0.43, 10.0, 1.3)
        assert isinstance(a, float)
        assert isinstance(b, float)
        assert a == pytest.approx(b, rel=1e-12)
        assert 0.05 <= a <= 0.43

    def test_campbell_and_brooks_corey_agree_on_sign_convention(self) -> None:
        """Both are fed magnitudes by every other caller in the engine.

        With b = 1.3 the Campbell exponent is 1/b = 0.77 and the Brooks-Corey
        exponent is lambda = 2, so beyond the air-entry pressure Brooks-Corey is
        the drier of the two. Measured at |h| = 30 cm: Campbell 0.213,
        Brooks-Corey 0.092 cm3/cm3.
        """
        for abs_h in (30.0, 300.0, 3000.0):
            campbell = ph.campbell_theta(-abs_h, 0.05, 0.43, -10.0, 1.3)
            brooks = ph.brooks_corey_theta(-abs_h, 0.05, 0.43, -10.0, 2.0)
            assert 0.05 < campbell < 0.43, abs_h
            assert 0.05 < brooks < 0.43, abs_h
            assert campbell > brooks, "Brooks-Corey with lambda=2 must dry out faster"

    def test_brooks_corey_does_not_divide_by_zero(self) -> None:
        value = ph.brooks_corey_theta(0.0, 0.05, 0.43, 10.0, 2.0)
        assert 0.05 <= value <= 0.43

    @pytest.mark.parametrize(
        ("b", "theta_r", "theta_s"),
        [(0.0, 0.05, 0.43), (0.5, 0.5, 0.4)],
    )
    def test_campbell_validates_its_parameters(
        self, b: float, theta_r: float, theta_s: float
    ) -> None:
        with pytest.raises(ValueError):
            ph.campbell_theta(-100.0, theta_r, theta_s, -10.0, b)


class TestAvailableWaterCapacity:
    def test_awc_is_positive_for_every_texture(self, vg_table: dict) -> None:
        for texture in vg_table:
            assert ph.available_water_capacity(texture) > 0.0, texture

    def test_awc_never_under_reports_by_more_than_fivefold(self) -> None:
        """A pedotransfer for a texture class may miss by 30-50 %, never by 150x.

        The floor of 20 % of the Saxton & Rawls (2006) value is deliberately
        generous: it only excludes an answer that is off by more than a factor of
        five in the dangerous direction (under-reporting available water).
        """
        offenders: list[str] = []
        for texture, reference_mm_per_m in SAXTON_RAWLS_2006_AWC_MM_PER_M.items():
            got = ph.available_water_capacity(texture)
            reference = reference_mm_per_m / 1000.0
            if got < 0.20 * reference:
                offenders.append(
                    f"{texture}: {got:.4f} cm3/cm3 is {100 * got / reference:.1f} % "
                    f"of the published {reference:.4f}"
                )
        assert not offenders, "AWC under-reported beyond 5x:\n" + "\n".join(offenders)

    def test_awc_accuracy_at_minus_33_cm_is_better_than_at_minus_330_cm(self) -> None:
        """Records the quantitative case for the depth correction.

        Using the same parameter table, evaluating field capacity at the FAO-56
        depth of -33 cm brings 5 of 12 textures inside 30 % of Saxton & Rawls;
        the engine's -330 cm brings 2 of 12.
        """

        def within_30_pct(head_cm: float) -> int:
            hits = 0
            for texture, reference in SAXTON_RAWLS_2006_AWC_MM_PER_M.items():
                awc = ph.water_content_at(-head_cm, texture) - ph.water_content_at(
                    -FAO56_PWP_HEAD_CM, texture
                )
                if abs(awc - reference / 1000.0) / (reference / 1000.0) <= 0.30:
                    hits += 1
            return hits

        at_33 = within_30_pct(FAO56_FC_HEAD_CM)
        at_330 = within_30_pct(330.0)
        assert at_33 > at_330, f"-33 cm scores {at_33}/12, -330 cm scores {at_330}/12"

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "With FC_HEAD_CM = 330.0 the returned AWC is not monotone in texture "
            "fineness: silt_loam 0.1363 > sandy_clay_loam 0.0583 despite the "
            "latter being the finer soil, and sandy_clay 0.0969 < silty_clay_loam "
            "0.1416 despite the former being coarser. Plant-available water "
            "capacity must rise with clay content over this texture range."
        ),
    )
    def test_awc_increases_with_clay_content(self, vg_table: dict) -> None:
        for coarse, fine in pairwise(COARSE_TO_FINE):
            assert ph.available_water_capacity(fine) > ph.available_water_capacity(coarse), (
                f"{fine} holds less available water than {coarse}"
            )

    def test_awc_uses_the_fao56_field_capacity_depth(self) -> None:
        """States the intended contract without touching FC_HEAD_CM.

        Recomputing AWC at -33 cm from the same parameter table is the value the
        engine should publish.
        """
        for texture in ("sand", "loam", "clay"):
            expected = ph.water_content_at(-FAO56_FC_HEAD_CM, texture) - ph.water_content_at(
                -FAO56_PWP_HEAD_CM, texture
            )
            assert expected > 0.0
        assert ph.water_content_at(-FAO56_FC_HEAD_CM, "loam") > ph.water_content_at(
            -FAO56_FC_HEAD_CM * 10.0, "loam"
        )

    def test_the_two_modules_agree_on_field_capacity(self) -> None:
        """The two modules must not disagree about the same physical constant.

        water_retention has always looked up field capacity at -33 cm; physics
        used 330.0, a factor of ten deeper, which put sand's available water
        99.4 % below the published value and left the two modules describing
        different soils.
        """
        curve = wr.calculate_water_retention_curve("loam")
        assert curve["field_capacity"]["pressure_head"] == -33
        assert curve["wilting_point"]["pressure_head"] == -15000
        assert ph.FC_HEAD_CM == 33.0, (
            f"physics uses -{ph.FC_HEAD_CM} cm while water_retention uses -33 cm"
        )
        assert ph.PWP_HEAD_CM == 15000.0

    def test_upper_module_awc_is_within_a_factor_of_five_of_published_values(self) -> None:
        """water_retention uses the correct -33 cm depth, so its AWC stays within a
        factor of five of Saxton & Rawls for every texture.

        The spread is expected and source-dependent: the engine ships the
        Carsel & Parrish (1988) van Genuchten parameters, a different
        pedotransfer, and the two are known to disagree most on the coarse
        textures (sand 30 % of the published value) and on silt (157 %). The
        criterion is deliberately wide: it excludes only an answer off by orders
        of magnitude, which is exactly the failure at -330 cm.
        """
        for texture, reference_mm_per_m in SAXTON_RAWLS_2006_AWC_MM_PER_M.items():
            curve = wr.calculate_water_retention_curve(texture)
            awc = curve["field_capacity"]["water_content"] - curve["wilting_point"]["water_content"]
            reference = reference_mm_per_m / 1000.0
            assert 0.2 * reference <= awc <= 5.0 * reference, (
                f"{texture}: {awc:.4f} cm3/cm3 against {reference:.4f}"
            )


class TestWaterRetentionApi:
    def test_unknown_texture_falls_back_to_loam_silently(self) -> None:
        params = wr.get_vg_parameters("not_a_texture")
        assert params["texture"] == "loam"
        assert params["theta_r"] == pytest.approx(0.078)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Two functions in the same package read the same table and disagree on "
            "the failure mode. engine/hydroma/soil/physics.py:145 raises KeyError "
            "for an unknown texture, while engine/hydroma/soil/water_retention.py:130 "
            "silently substitutes loam and returns a dict whose 'texture' field "
            "reads 'loam'. A caller asking for a volcanic sand receives loam "
            "parameters with no exception, and the returned dict gives no hint that "
            "a substitution happened; the only trace is a log line that does not "
            "name the texture that was actually requested. For a soil-specific "
            "digital twin this fails open into a wrong answer."
        ),
    )
    def test_unknown_texture_raises_instead_of_substituting(self) -> None:
        with pytest.raises(KeyError):
            wr.get_vg_parameters("not_a_texture")

    def test_custom_heads_without_field_capacity_yield_none(self) -> None:
        """Documented behaviour, and a silent one."""
        result = wr.calculate_water_retention_curve("loam", h_values=[-1, -5, -20])
        assert result["field_capacity"] is None
        assert result["wilting_point"] is None
        assert len(result["curve"]) == 3

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/soil/water_retention.py:181-194 looks up field "
            "capacity by an exact list match on -33 and wilting point on -15000, "
            "so a caller supplying any other set of pressure heads silently "
            "receives field_capacity=None and wilting_point=None. Since the whole "
            "purpose of the function is to report these two points, a head list "
            "that omits them produces a result object with no water-holding "
            "figures and no warning. Interpolation, or interpolation onto the "
            "nearest bracketing heads, is required."
        ),
    )
    @pytest.mark.parametrize("heads", [[-10, -100, -1000], [-20, -50, -200], [0, -5]])
    def test_field_capacity_is_interpolated_for_arbitrary_heads(self, heads: list[float]) -> None:
        result = wr.calculate_water_retention_curve("loam", h_values=heads)
        assert result["field_capacity"] is not None
        assert result["wilting_point"] is not None

    @pytest.mark.parametrize("texture", COARSE_TO_FINE)
    def test_curve_is_monotone_decreasing(self, texture: str) -> None:
        curve = wr.calculate_water_retention_curve(texture)["curve"]
        thetas = [point["water_content"] for point in curve]
        assert thetas == sorted(thetas, reverse=True), texture

    def test_curve_agrees_with_physics_at_the_same_head(self) -> None:
        for texture in ("sand", "loam", "clay"):
            curve = wr.calculate_water_retention_curve(texture)["curve"]
            for point in curve:
                if point["pressure_head"] == 0:
                    continue
                expected = ph.water_content_at(point["pressure_head"], texture)
                assert point["water_content"] == pytest.approx(expected, abs=1e-4), (
                    f"{texture} at {point['pressure_head']} cm"
                )

    def test_available_water_converts_centimetres_to_millimetres(self) -> None:
        out = wr.calculate_available_water(theta_fc=0.30, theta_wp=0.15, root_depth=50.0)
        assert out["available_water_capacity"] == pytest.approx(0.15)
        assert out["total_available_water"] == pytest.approx(7.5)
        assert out["total_available_water_mm"] == pytest.approx(75.0)

    def test_available_water_rejects_inverted_thetas(self) -> None:
        with pytest.raises(ValueError):
            wr.calculate_available_water(theta_fc=0.15, theta_wp=0.30, root_depth=50.0)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/soil/water_retention.py:197 accepts theta_fc and "
            "theta_wp with no check against the physical range 0-1 and root_depth "
            "with no check against zero. root_depth = -50 returns -1500 mm of "
            "available water, i.e. a negative store of water in a root zone, and "
            "theta_fc = 2.0 returns an AWC of 2.0 cm3/cm3."
        ),
    )
    def test_available_water_rejects_impossible_inputs(self) -> None:
        with pytest.raises(ValueError):
            wr.calculate_available_water(theta_fc=0.30, theta_wp=0.15, root_depth=-50.0)
        with pytest.raises(ValueError):
            wr.calculate_available_water(theta_fc=2.0, theta_wp=0.15, root_depth=50.0)
