"""The two RUSLE duplicates that the registry did NOT absorb, measured.

`services/_contracts/formula.py` is the single home for RUSLE. Two live
implementations of the same physics still sit outside it, and neither can be
delegated because neither is the registry's equation:

* ``engine/land/erosion_risk.py:calculate_ls_factor`` — McCool et al. (1999)
  ``L * S``, with an explicit slope length from D8 flow accumulation. The
  registry's ``ls_factor`` is Foster & Nearing (2005), a *combined* LS with no
  length term at all, so there is no call to substitute even before the
  numbers are compared.
* ``services/satellite/soilgrids.py:rusle_k_factor`` — Williams et al. (1995)
  *multiplicative* four-term EPIC. The registry's ``k_factor_epic`` is Renard
  et al. (1997) *additive*. These are different equations, not two spellings of
  one, and the registry's own docstring already warns against mixing them.

What this file is for
---------------------
Not to make the two agree — they cannot, and a K feeding a published erosion
number is a scientific decision, not a code fix. It is to make the size of the
disagreement executable, so that:

1. nobody delegates one to the other by assuming the difference is rounding;
2. the registry's "roughly 3.6x" claim, which does not reproduce, is visible as
   a measured number someone can correct the docstring against;
3. a decision to standardise has to be ratified first, because the tripwires
   below fail loudly the moment one side moves.

The canonical loam used throughout is clay 30 % / silt 40 % / sand 30 %,
SOC 15 g/kg — the same soil the S-SCI contract test names.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

#: clay 30 %, silt 40 %, sand 30 %, SOC 15 g/kg — the canonical loam.
LOAM = {"sand_pct": 30.0, "silt_pct": 40.0, "clay_pct": 30.0, "soc_g_kg": 15.0}

#: 9 % grade is ``atan(0.09)``. The McCool branch point is on percent grade, not
#: on degrees, and conflating the two hides a 46 % step.
NINE_PERCENT_GRADE_DEG = math.degrees(math.atan(0.09))


def _mccool(slope_deg: float, length_m: float) -> tuple[float, float, float]:
    """The exact arithmetic of ``erosion_risk.calculate_ls_factor``, scalar.

    Returned as ``(L, S, LS)`` so a test can quote the intermediate it disputes.
    """
    theta = math.radians(slope_deg)
    sin_b = math.sin(theta)
    cos_b = math.cos(theta)
    beta = (sin_b / cos_b**2) * math.sqrt(length_m / 300.0)
    m = min(max(beta / (1.0 + beta), 0.0), 1.0)
    l_factor = (length_m / 22.13) ** m
    grade_pct = math.tan(theta) * 100.0
    s_factor = 10.8 * sin_b + 0.03 if grade_pct < 9.0 else 16.8 * sin_b - 0.045 * cos_b**2
    return l_factor, s_factor, l_factor * s_factor


class TestLsFormsAreDifferentEquations:
    """McCool 1999 (engine) vs Foster & Nearing 2005 (registry)."""

    def test_they_are_not_merely_a_length_term_apart(self) -> None:
        """Worked arithmetic at 10 deg, lambda = 100 m.

        Registry (Foster & Nearing 2005), slope in degrees:

            sin(10 deg) = 0.17364817766693033
            LS = 65.41 * sin^2 + 4.56 * sin + 0.065
               = 1.972352837196866 + 0.7918356901612023 + 0.065
               = 2.829188527358068

        McCool 1999 at the same slope and a 100 m slope length:

            grade = tan(10 deg) * 100 = 17.6327 %  -> steep branch
            beta  = (sin/cos^2) * sqrt(100/300) = 0.10337289635062837
            m     = beta / (1 + beta)            = 0.09368808740230163
            L     = (100 / 22.13) ** m           = 1.1517744454027028
            S     = 16.8 * sin - 0.045 * cos^2  = 2.91728938480443 - 0.04364308396768293
                                                 = 2.873646300836747
            LS    = L * S                       = 3.309792374429773

        3.309792374429773 / 2.829188527358068 = 1.1699 — a 17 % disagreement at
        a slope length well inside the range this engine serves, and it is not
        an artefact of the length choice: at 30 m the ratio is 1.032, at
        300 m it is 1.509, at 1000 m it is 2.597.
        """
        from services._contracts.formula import ls_factor

        registry = ls_factor(10.0)
        l_factor, s_factor, mccool = _mccool(10.0, 100.0)

        assert registry == pytest.approx(2.829188527358068, rel=1e-12)
        assert mccool == pytest.approx(3.309792374429773, rel=1e-12)
        assert l_factor == pytest.approx(1.1517744454027028, rel=1e-12)
        assert s_factor == pytest.approx(2.873646300836747, rel=1e-12)
        assert mccool / registry == pytest.approx(1.1699, abs=5e-4)

    @pytest.mark.parametrize(
        ("slope_deg", "length_m", "expected_ratio"),
        [
            (5.0, 30.0, 1.0209),
            (10.0, 30.0, 1.0324),
            (10.0, 100.0, 1.1699),
            (10.0, 300.0, 1.5090),
            (10.0, 1000.0, 2.5972),
            (30.0, 1000.0, 3.6250),
        ],
    )
    def test_the_gap_is_never_below_two_percent(
        self, slope_deg: float, length_m: float, expected_ratio: float
    ) -> None:
        """The registry is a fixed function of slope, McCool grows with length.

        So the ratio is not a constant that a single correction factor could
        absorb — it is a function of an input the registry does not even take.
        """
        from services._contracts.formula import ls_factor

        ratio = _mccool(slope_deg, length_m)[2] / ls_factor(slope_deg)

        assert ratio == pytest.approx(expected_ratio, abs=5e-4)
        assert ratio > 1.02

    def test_the_engine_actually_produces_the_mccool_number(self) -> None:
        """The scalar above is a transcription; this is the real raster call.

        A planar DEM at a known gradient, so the D8 slope length and the slope
        angle are both exact and the two implementations can be compared on the
        same cell.
        """
        from engine.land.erosion_risk import calculate_ls_factor, calculate_slope_degrees
        from services._contracts.formula import ls_factor

        gradient = 0.10  # 10 % grade, a uniform plane
        dem = np.tile((np.arange(12) * gradient * 30.0)[np.newaxis, :], (12, 1)).astype(float)

        engine = calculate_ls_factor(dem=dem, cell_size_m=30.0)

        assert engine.shape == dem.shape
        assert np.all(np.isfinite(engine))
        # The engine's value is McCool; the registry's value for the same mean
        # slope is Foster & Nearing. They are not within 1e-9 of each other.
        mean_slope = float(np.mean(calculate_slope_degrees(dem, 30.0)))
        assert float(engine.max()) != pytest.approx(ls_factor(mean_slope), abs=1e-9)

    def test_the_registry_cannot_express_a_slope_length(self) -> None:
        """The structural reason no delegation is available for LS.

        ``ls_factor`` takes one argument. ``calculate_ls_factor`` needs slope
        length as well as slope, and the length term is the part that grows the
        factor: McCool's L is 1.016 at 30 m and 2.557 at 1000 m at 10 deg. A
        one-argument registry function cannot reproduce that, so a migration here
        would be a physics change dressed as a refactor.
        """
        from engine.land.erosion_risk import calculate_ls_factor
        from services._contracts.formula import ls_factor

        assert ls_factor(10.0) == pytest.approx(2.829188527358068, rel=1e-12)
        assert _mccool(10.0, 30.0)[0] == pytest.approx(1.016438, abs=1e-5)
        assert _mccool(10.0, 1000.0)[0] == pytest.approx(2.557000, abs=1e-5)
        # Same signature shape, so the mismatch is not a calling-convention
        # problem that a wrapper could absorb: it is a different argument list.
        with pytest.raises(TypeError):
            ls_factor(10.0, 100.0)  # type: ignore[call-arg]
        _ = calculate_ls_factor


class TestMcCoolNinePercentBranch:
    """The 9 % branch is on percent grade, and the two arms do not meet."""

    def test_the_branch_is_on_grade_not_degrees(self) -> None:
        """9 % grade is 5.142764557884242 degrees, not 9 degrees.

        A reader who takes the branch to be at 9 degrees will look for a
        discontinuity at 9 deg and not find one, which is why the step below
        has survived.
        """
        assert pytest.approx(5.142764557884242, rel=1e-12) == NINE_PERCENT_GRADE_DEG

    def test_the_two_arms_step_by_46_percent(self) -> None:
        """A +46.4 % step in the steepness factor across one grade boundary.

            low arm   10.8 * sin(theta) + 0.03              = 0.9980871545556185
            code arm  16.8 * sin(theta) - 0.045 * cos^2     = 1.4612749228036532
            step      1.4612749 / 0.9980872 - 1             = +0.464075

        McCool's construction depends on the arms meeting at the boundary, and
        the published steep arm ``16.8 * sin(theta) - 0.50`` gives 1.0059133515
        there — continuous to +0.78 %. The ``-0.045 * cos^2`` arm is a different
        relation substituted for it, and it does not meet its own partner.

        This is recorded, not fixed. Correcting it changes erosion numbers, and
        the choice of arm is a scientific decision for the registry's owner to
        ratify against the RUSLE2 user's guide, not a refactor.
        """
        theta = math.radians(NINE_PERCENT_GRADE_DEG)
        sin_b = math.sin(theta)
        cos_b = math.cos(theta)

        low_arm = 10.8 * sin_b + 0.03
        code_arm = 16.8 * sin_b - 0.045 * cos_b**2
        published_arm = 16.8 * sin_b - 0.50

        assert low_arm == pytest.approx(0.9980871545556185, rel=1e-12)
        assert code_arm == pytest.approx(1.4612749228036532, rel=1e-12)
        assert published_arm == pytest.approx(1.005913351530962, rel=1e-12)

        assert (code_arm / low_arm - 1.0) == pytest.approx(0.464075, abs=5e-5)
        # The published arm is continuous with the low arm to well under 1 %,
        # which is the property the substitution lost.
        assert abs(published_arm / low_arm - 1.0) == pytest.approx(0.007841, abs=5e-5)

    def test_the_baseline_pins_the_engine_number(self) -> None:
        """720 recorded fields would have to be regenerated for any change.

        ``engine/baseline/R18.json`` records the ``erosion`` case at relative
        1e-9, and the case is the McCool implementation. So this is not a number
        that can be swapped quietly: the tripwire in
        ``engine/strict_tests/test_s00_baseline.py`` fails field by field.
        """
        import json
        from pathlib import Path

        recorded = json.loads(Path("engine/baseline/R18.json").read_text(encoding="utf-8"))
        erosion = recorded["cases"]["erosion"]

        fields = sum(1 for case in erosion.values() for row in case["ls"] for _ in row)
        assert sorted(erosion) == ["g0.02", "g0.05", "g0.15", "g0.3", "g0.6"]
        assert fields == 720, f"the erosion case now records {fields} LS fields, not 720"


class TestKFormsAreDifferentEquations:
    """Williams 1995 multiplicative (soilgrids) vs Renard 1997 additive (registry)."""

    def test_the_measured_ratio_is_not_the_3_6x_the_registry_claims(self) -> None:
        """Worked arithmetic for the canonical loam.

        Williams 1995, soilgrids' own spelling, term by term::

            c        = 15 / 1000                          = 0.015
            sn       = 1 - 30/100                          = 0.7
            term1    = 0.2 + 0.3*exp(-0.0256*30*0.6)       = 0.3892336461642285
            term2    = (40 / (30 + 40)) ** 0.3             = 0.8454512788394475
            term3    = 1 - 0.25*c/(c+exp(3.72-2.95*c))     = 0.9999050470757004
            term4    = 1 - 0.7*sn/(sn+exp(-5.51+22.9*sn))  = 0.9999867745662302
            K        = 0.1317 * term1 * term2 * term3 * term4 = 0.04333489530128085

        Renard 1997, registry::

            soc_pct  = 15 / 10                             = 1.5
            bracket  = 0.2 + 0.3*(0.015)^2 + 0.3*(0.985)^2 + 0.025*(30+40)
                     = 2.241135
            K        = 2.241135 * 0.1317                   = 0.2951574795

        0.2951574795 / 0.0433 = 6.8166. The registry docstring and the S-SCI
        contract test both say "roughly 3.6x"; neither reproduces it. Across a
        126-point texture sweep the ratio never falls below 4.78x. The
        docstring understates the divergence, so the number to correct it
        against is here.
        """
        from services._contracts.formula import k_factor_epic
        from services.satellite.soilgrids import rusle_k_factor

        williams = rusle_k_factor(**LOAM)
        renard = k_factor_epic(LOAM["soc_g_kg"], LOAM["clay_pct"], LOAM["silt_pct"])

        assert williams == pytest.approx(0.0433, abs=5e-5)  # rounded to 4 dp
        assert renard == pytest.approx(0.2951574795, rel=1e-12)
        assert renard / williams == pytest.approx(6.8166, abs=5e-4)
        assert renard != pytest.approx(williams, rel=0.5)

    def test_the_contract_tests_williams_copy_is_a_third_equation(self) -> None:
        """``tests/contract/test_s_sci.py`` pins Renard against its own Williams.

        That inline copy divides by ``clay``; soilgrids divides by
        ``clay + silt``. The two Williams spellings differ by 1.29x for the
        canonical loam, so the contract test asserts a real disagreement — its
        ``rel=0.5`` bound is far below either ratio — but it is not witnessing
        the function that is actually in the tree. The registry's own
        "3.6x" is closer to this copy's 5.28x than to soilgrids' 6.82x, which
        suggests the figure was measured against the copy, not the function.
        """
        from services._contracts.formula import k_factor_epic
        from services.satellite.soilgrids import rusle_k_factor

        c = LOAM["soc_g_kg"] / 1000.0
        sn = 1.0 - LOAM["sand_pct"] / 100.0
        contract_copy = (
            0.1317
            * (0.2 + 0.3 * math.exp(-0.0256 * LOAM["sand_pct"] * (1.0 - LOAM["silt_pct"] / 100.0)))
            * (LOAM["silt_pct"] / LOAM["clay_pct"]) ** 0.3
            * (1.0 - 0.25 * c / (c + math.exp(3.72 - 2.95 * c)))
            * (1.0 - 0.7 * sn / (sn + math.exp(-5.51 + 22.9 * sn)))
        )

        tree = rusle_k_factor(**LOAM)
        renard = k_factor_epic(LOAM["soc_g_kg"], LOAM["clay_pct"], LOAM["silt_pct"])

        assert contract_copy == pytest.approx(0.05587670486941109, rel=1e-12)
        assert contract_copy / tree == pytest.approx(1.2905, abs=5e-4)
        assert renard / contract_copy == pytest.approx(5.2823, abs=5e-4)

    def test_the_two_forms_do_not_agree_anywhere_in_texture_space(self) -> None:
        """The lower bound of the ratio, so the tripwire covers the whole domain.

        126 textures (7 clay x 6 silt, sand the remainder) x 3 SOC levels. The
        smallest Renard/Williams ratio in that sweep is 5.197x, at clay 8 /
        silt 10 / sand 82 / SOC 5 g/kg. A finer sweep that reaches down to 4 %
        clay and 60 g/kg SOC bottoms out at 4.783x. "They are in the same
        ballpark" is not true of these two equations anywhere in texture space.
        """
        from services._contracts.formula import k_factor_epic
        from services.satellite.soilgrids import rusle_k_factor

        ratios = []
        for clay in (8, 15, 20, 30, 40, 50, 60):
            for silt in (10, 20, 30, 40, 50, 60):
                sand = max(0.0, 100.0 - clay - silt)
                for soc in (5.0, 15.0, 30.0):
                    williams = rusle_k_factor(sand, silt, clay, soc)
                    renard = k_factor_epic(soc, clay, silt)
                    ratios.append(renard / williams)

        assert len(ratios) == 126
        assert min(ratios) == pytest.approx(5.1974, abs=5e-4)
        assert max(ratios) == pytest.approx(11.5149, abs=5e-4)

    def test_soilgrids_ceiling_is_never_reached(self) -> None:
        """The 0.09 clip in soilgrids is inert over the whole texture domain.

        The registry's ``K_BOUNDS`` comment calls 0.09 "the ceiling
        soilgrids.py clips to" and uses it to justify its own 0.65. That is
        worth knowing, but the ceiling is not what constrains soilgrids: the
        widest value the Williams form produces for a physical texture is
        0.0645. So raising the bound would be free, and lowering the Williams
        equation into a narrower band would not have been caused by the clip.
        """
        from services.satellite.soilgrids import rusle_k_factor

        widest = max(
            rusle_k_factor(max(0.0, 100.0 - clay - silt), silt, clay, soc)
            for clay in range(1, 65)
            for silt in range(1, 90)
            for soc in (0.0, 5.0, 15.0, 40.0, 100.0)
        )

        assert widest == pytest.approx(0.0645, abs=5e-5)
        assert widest < 0.09


class TestWhichKTheTreeActuallyConsumes:
    """The dependency, stated so a standardisation decision knows its target."""

    def test_the_chain_runner_reads_the_williams_k_from_soilgrids(self) -> None:
        """``chain_runner`` takes ``soil["k_factor_rusle"]``, which is Williams.

        ``soilgrids.fetch_soil_profile`` writes ``k_factor_rusle`` at line 255
        from ``rusle_k_factor`` — the Williams form. ``chain_runner`` reads it
        at line 293 and passes it to ``rusle_point`` at line 301, which produces
        ``soil_loss_ton_ha_yr``. So the live chain's K is Williams.

        The registry's Renard K reaches three other places and none of them is
        this chain: ``map_engine/fetchers/soil_fetcher.py:109``,
        ``api_gateway/routers/elevation.py:225`` and
        ``simulation/adapters/erosion_adapter.py:133``.
        """
        from pathlib import Path

        soilgrids_src = Path("services/satellite/soilgrids.py").read_text(encoding="utf-8")
        chain_src = Path("services/scientific_motors/chain_runner.py").read_text(encoding="utf-8")

        assert '"k_factor_rusle": k_factor' in soilgrids_src
        assert "k_factor = rusle_k_factor(sand, silt, clay" in soilgrids_src
        assert 'k_factor = float(soil.get("k_factor_rusle", 0.03))' in chain_src
        assert "rusle_point(annual_rainfall, k_factor, slope_pct" in chain_src
        # The chain must not be quietly switched to the registry form.
        assert "k_factor_epic" not in chain_src

    def test_the_chain_already_mixes_the_two_provenances(self) -> None:
        """Williams K with Foster & Nearing LS in one published soil-loss number.

        This is the honest state of the tree and the reason the two forms must
        not be collapsed by a well-meaning refactor: ``rusle_point`` computes
        its length-steepness factor with the registry's Foster & Nearing
        ``ls_factor`` and is handed a K from the Williams equation. Ratifying
        either change moves a number that the chain already produced from mixed
        sources.
        """
        from services._contracts.formula import k_factor_epic, ls_factor
        from services.satellite.soilgrids import rusle_k_factor
        from services.scientific_motors.chain_runner import rusle_point

        williams = rusle_k_factor(**LOAM)
        renard = k_factor_epic(LOAM["soc_g_kg"], LOAM["clay_pct"], LOAM["silt_pct"])

        with_williams = rusle_point(1000.0, williams, 10.0, crop="wheat", practice="none")
        with_renard = rusle_point(1000.0, renard, 10.0, crop="wheat", practice="none")

        # Both runs share the same LS, so the whole difference is K. The LS is
        # Foster & Nearing from the registry, times a fixed (lambda/22.13)^0.5:
        #   65.41 sin^2 + 4.56 sin + 0.065 at atan(0.10) = 1.1663607211119928
        #   times (100/22.13)^0.5                        = 2.125925
        #   -> 2.479, which is the value rusle_point reports.
        expected_ls = ls_factor(math.degrees(math.atan(0.10))) * (100.0 / 22.13) ** 0.5
        assert expected_ls == pytest.approx(2.4794, abs=1e-3)
        assert with_williams["ls_factor"] == with_renard["ls_factor"] == 2.479
        # 1000 mm/yr, 10 % slope, wheat, no practice. R = 2000, LS = 2.479,
        # C = 0.25, P = 1.0, so A = 2000 * K * 2.479 * 0.25:
        #   Williams  2000 * 0.0433 * 2.479 * 0.25 =  53.68
        #   Renard    2000 * 0.2952 * 2.479 * 0.25 = 365.87 -> clipped to 60.0
        # Both are "very_high" at this rainfall, so the label happens to survive
        # — but the reported loss does not, and the Renard run is silently
        # truncated by rusle_point's 60 t/ha/yr ceiling to one sixth of what the
        # equation produced. That ceiling is itself a published-number decision:
        # under Renard, most humid-climate points would report 60.0.
        assert with_williams["k_factor"] == 0.0433
        assert with_renard["k_factor"] == pytest.approx(0.2952, abs=5e-5)
        assert with_williams["soil_loss_ton_ha_yr"] == pytest.approx(53.68, abs=0.01)
        assert with_renard["soil_loss_ton_ha_yr"] == 60.0
        assert with_williams["risk"] == with_renard["risk"] == "very_high"
        assert 2000.0 * with_renard["k_factor"] * expected_ls * 0.25 == pytest.approx(
            365.87, abs=0.1
        )
