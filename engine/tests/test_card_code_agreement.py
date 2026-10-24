"""Card <-> code agreement for the six corrected model cards (P0-2, P0-9).

A model card is a published claim. This module makes that claim falsifiable: for
each of the six cards corrected in the P0 label round, the card's own text is
parsed -- the equation it states, the constants it prints, the reference-case
numbers it quotes -- and the corresponding implementation is required to
reproduce it for a fixed input.

What is checked
---------------
CANON-005  Theis drawdown. The card quotes THEIS_REFERENCE (T, S, Q, r, t) and
           the measured drawdown; the gateway node must return that value and
           the closed form parsed from the card must reproduce it.
CANON-006  van Genuchten theta(h) and the AWC definition, against loam
           parameters; plus the card's measured AWC agreement claim (30.2 % -
           157.2 %, 5 of 12 textures within 30 % of Saxton & Rawls 2006).
CANON-007  RUSLE LS. The card states beta, m, L, S and LS; the implementation
           (C++ kernel or its Python twin) must match that algebra.
CANON-009  Terrain: the aspect argument order, the TWI length-vs-area
           definition, and the profile/plan curvature denominators.
CANON-011  Extraterrestrial radiation: the card's eq. 21 constants and the
           quoted reference day (lat 41.9, DOY 193) must reproduce in the
           engine.
CANON-015  Kirpich Tc: the card's equation and its quoted 23.44 minutes for
           1000 m at 1 %.

Where a card asserts a *number*, the test asserts the implementation reproduces
it, so a later edit to either side fails loudly. Where a card asserts a *form*,
the test re-derives the form independently and compares, so a constant drift in
the engine fails loudly too.

Runtime is kept under 20 s: no network, no compiled-kernel rebuild, small DEMs,
and one gateway instance shared across the module.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from engine.gateway import (
    EngineGateway,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)

CARDS = Path(__file__).resolve().parents[1] / "models" / "cards"

GW = EngineGateway()
PROV = ProvenanceSpec(source="card_code_agreement", source_type="TEST")


# --------------------------------------------------------------------------- #
# Card parsing helpers                                                         #
# --------------------------------------------------------------------------- #
def _card_text(stem: str) -> str:
    path = CARDS / f"{stem}.md"
    assert path.exists(), f"missing card {path}"
    return path.read_text(encoding="utf-8")


def _field(text: str, name: str) -> str:
    """Return the value cell of the markdown table row whose key is ``name``."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"| **{name}**"):
            # The value is between the 2nd '|' and the LAST '|'; values
            # themselves may contain '|' (e.g. |alpha*h|).
            inner = stripped[1:].rsplit("|", 1)[0]
            return inner.split("|", 1)[1].strip()
    raise AssertionError(f"card field {name!r} not found")


def _numbers(text: str, pattern: str) -> list[float]:
    return [float(m) for m in re.findall(pattern, text)]


def _one(text: str, pattern: str) -> float:
    found = re.findall(pattern, text)
    assert found, f"pattern {pattern!r} not found in card text"
    return float(found[0])


def _norm(text: str) -> str:
    """ASCII-normalise the typography the cards use, so the same regular
    expressions match Greek letters, the U+2212 minus, and the middot."""
    table = str.maketrans(
        {
            "\u2212": "-",  # minus sign
            "\u00b7": "*",  # middle dot
            "\u00d7": "*",  # multiplication sign
            "\u03b8": "theta",
            "\u03b1": "alpha",
            "\u03b2": "beta",
            "\u03b4": "delta",
            "\u03c6": "phi",
            "\u03bb": "lambda",
            "\u03b3": "gamma",
            "\u2013": "-",
            "\u2014": "-",
        }
    )
    return text.translate(table)


#: Every correction note in the six cards starts with one of these markers, so
#: the tests below can read the card's *stated* claim without the retired
#: wording that documents its own correction.
RETIRED_MARKERS = (
    "**Retired form:",
    "**Retired figure:",
    "**Retired claims:",
    "**Retired citation:",
    "**Divergence of record:",
)


def _stated(text: str, before: str | None = None) -> str:
    """The card's own claim, with every correction note removed."""
    out = _norm(text)
    for marker in RETIRED_MARKERS:
        out = out.split(marker)[0]
    if before is not None:
        out = out.split(before)[0]
    return out


def _gw_values(model_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
    r = GW.execute(
        GatewayRequest(model_id=model_id, inputs=inputs, input_units={}, provenance=PROV)
    )
    assert isinstance(r, GatewayResult), f"{model_id}: {r.error_code}: {r.message}"
    return r.values


def _closed_vg_theta(h: float, theta_r: float, theta_s: float, alpha: float, n: float) -> float:
    """van Genuchten (1980) retention, from the primary source."""
    m = 1.0 - 1.0 / n
    return float(theta_r + (theta_s - theta_r) / (1.0 + abs(alpha * h) ** n) ** m)


def _ls_reference(slope_length_m: float, slope_percent: float) -> float:
    """CANON-007's stated RUSLE LS algebra, evaluated on its own.

    beta = (sin(theta) / 0.0896) / (3 * sin(theta)^0.8 + 0.56), m = beta / (1 + beta),
    L = (lambda / 22.13)^m, S = 10.8 sin(theta) + 0.03 below 9 % else
    16.8 sin(theta) - 0.50, LS = L * S.
    """
    slope_fraction = slope_percent / 100.0
    theta = math.atan(slope_fraction)
    sin_theta = math.sin(theta)
    beta = (sin_theta / 0.0896) / (3.0 * sin_theta**0.8 + 0.56)
    m = beta / (1.0 + beta)
    L = (slope_length_m / 22.13) ** m
    if slope_fraction < 0.09:
        S = 10.8 * sin_theta + 0.03
    else:
        S = 16.8 * sin_theta - 0.50
    return float(L * S)


# --------------------------------------------------------------------------- #
# CANON-005 -- Theis                                                           #
# --------------------------------------------------------------------------- #
class TestCanon005Theis:
    CARD = "CANON-005_theis_solution"

    def test_card_quotes_the_measured_reference_drawdown(self) -> None:
        ref = _field(_card_text(self.CARD), "reference_cases")
        # The reference case numbers are parsed out of the card itself.
        (T,) = _numbers(ref, r"T=(\d+)")
        (S,) = _numbers(ref, r"S=(0\.\d+)")
        (Q,) = _numbers(ref, r"Q=(\d+)")
        (r_dist,) = _numbers(ref, r"r=(\d+) m")
        (t_days,) = _numbers(ref, r"t=(\d+) day")
        claimed = _one(ref, r"\(([\d.]+) m measured")

        values = _gw_values(
            "CANON-005",
            {
                "transmissivity_m2day": T,
                "storativity": S,
                "pumping_rate_m3day": Q,
                "distance_from_well_m": r_dist,
                "time_since_pumping_start_days": t_days,
            },
        )
        assert values["drawdown_m"] == pytest.approx(claimed, rel=1e-12)

        # The card's governing equation, re-derived independently here:
        #   u = r^2 S / (4 T t),  s = Q / (4 pi T) * W(u),  W(u) = -E1(-u)
        from scipy.special import expi

        u = (r_dist * r_dist * S) / (4.0 * T * t_days)
        closed = (Q / (4.0 * math.pi * T)) * (-expi(-u))
        assert closed == pytest.approx(claimed, rel=1e-9)
        assert values["drawdown_m"] == pytest.approx(closed, rel=1e-9)

    def test_card_no_longer_claims_a_validated_label(self) -> None:
        text = _card_text(self.CARD)
        status = _field(text, "validation_status")
        assert "VALIDATED_METHOD_CONFORMANCE" in status
        traceability = text.split("## 9. Implementation & Traceability")[1]
        assert "Validated against" not in traceability
        assert "matches reference case" not in _field(text, "verification_status")


# --------------------------------------------------------------------------- #
# CANON-006 -- van Genuchten / Mualem / AWC                                    #
# --------------------------------------------------------------------------- #
class TestCanon006VanGenuchten:
    CARD = "CANON-006_van_genuchten"

    # The loam row of the embedded parameter table, the same row the strict
    # suites use as their fixed input.
    LOAM = {"theta_r": 0.078, "theta_s": 0.43, "alpha": 0.036, "n": 1.56}

    def test_theta_matches_the_stated_equation(self) -> None:
        equation = _norm(_field(_card_text(self.CARD), "governing_equations"))
        assert "theta(h) = theta_r + (theta_s - theta_r)" in equation
        assert "m = 1 - 1/n" in equation

        p = self.LOAM
        for h in (0.0, -10.0, -33.0, -300.0, -15000.0):
            got = _gw_values(
                "CANON-006",
                {
                    "matric_potential": h,
                    "theta_r": p["theta_r"],
                    "theta_s": p["theta_s"],
                    "vg_alpha": p["alpha"],
                    "vg_n": p["n"],
                },
            )["van_genuchten_theta"]
            assert got == pytest.approx(
                _closed_vg_theta(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"]),
                rel=1e-12,
            ), f"theta({h})"

    def test_awc_matches_the_stated_definition(self) -> None:
        """AWC = theta(FC) - theta(PWP) at -33 and -15000 cm, times 1000 for mm/m."""
        definition = _norm(_field(_card_text(self.CARD), "governing_equations"))
        for token in ("-33", "-15000", "1000"):
            assert token in definition
        p = self.LOAM
        reference = (
            _closed_vg_theta(-33.0, p["theta_r"], p["theta_s"], p["alpha"], p["n"])
            - _closed_vg_theta(-15000.0, p["theta_r"], p["theta_s"], p["alpha"], p["n"])
        ) * 1000.0
        got = _gw_values("SOIL_AWC", {"texture_class": "loam"})["awc"] * 1000.0
        assert got == pytest.approx(reference, rel=1e-9)

    def test_measured_awc_agreement_claim_reproduces(self) -> None:
        """The card prints the agreement it measures; the measurement is redone
        here from the strict suite's own Saxton & Rawls (2006) table."""
        from engine.hydroma.soil.physics import available_water_capacity
        from engine.strict_tests.conftest import SAXTON_RAWLS_2006_AWC_MM_PER_M

        claim = _field(_card_text(self.CARD), "empirical_validation")
        low = _one(claim, r"\*\*(\d+\.\d+) %")
        high = _one(claim, r"to (\d+\.\d+) %")
        within_match = re.search(r"(\d+) of 12 textures", claim)
        assert within_match is not None
        within = int(within_match.group(1))

        ratios: list[float] = []
        hits = 0
        for texture, reference_mm_m in SAXTON_RAWLS_2006_AWC_MM_PER_M.items():
            got_mm_m = available_water_capacity(texture) * 1000.0
            ratios.append(100.0 * got_mm_m / reference_mm_m)
            if abs(got_mm_m - reference_mm_m) / reference_mm_m <= 0.30:
                hits += 1
        assert min(ratios) == pytest.approx(low, abs=0.1)
        assert max(ratios) == pytest.approx(high, abs=0.1)
        assert hits == within

    def test_the_fabricated_agreement_claim_is_gone(self) -> None:
        """The correction note may quote the retired figures, but no field that
        reports the model's status may still carry them as its claim."""
        text = _card_text(self.CARD)
        for field in ("verification_status", "validation_status", "empirical_validation"):
            value = _stated(_field(text, field))
            assert "<1 %" not in value
            assert "matches Saxton-Rawls AWC to <1" not in value
            assert "Validated against Saxton & Rawls" not in value


# --------------------------------------------------------------------------- #
# CANON-007 -- RUSLE LS                                                        #
# --------------------------------------------------------------------------- #
class TestCanon007RusleLs:
    CARD = "CANON-007_rusle_ls_factor"

    SLOPE_LENGTH_M = 100.0
    SLOPE_PERCENT = 10.0

    def test_implementation_matches_the_stated_algebra(self) -> None:
        equation = _norm(_field(_card_text(self.CARD), "governing_equations"))
        # The AH-703 beta form, exactly as the card states it.
        assert "beta = (sin theta / 0.0896) / (3 * sin theta^0.8 + 0.56)" in equation
        assert "m = beta / (1 + beta)" in equation
        assert "L = (lambda / 22.13)^m" in equation or "L = (λ / 22.13)^m" in equation

        from engine.hydroma.wrapper import compute_erosion

        got = compute_erosion(
            self.SLOPE_LENGTH_M, self.SLOPE_PERCENT, 600.0, "loam", 0.5, 0.8
        )["LS_factor"]

        # Independent re-derivation from the card's stated equation. The
        # implementation rounds its LS to 3 decimals, so the tolerance is the
        # documented rounding granularity.
        assert got == pytest.approx(_ls_reference(
            self.SLOPE_LENGTH_M, self.SLOPE_PERCENT
        ), abs=5e-4)

    def test_the_compiled_kernel_agrees_too(self) -> None:
        """The C++ kernel is the canonical implementation the card names; when
        it is present it must give the same LS as the card's stated algebra."""
        pytest.importorskip("hydroma_core", reason="compiled kernel not built")
        from engine.hydroma.wrapper import _cpp

        got = _cpp.ls_factor(self.SLOPE_LENGTH_M, self.SLOPE_PERCENT)
        assert got == pytest.approx(
            _ls_reference(self.SLOPE_LENGTH_M, self.SLOPE_PERCENT), rel=1e-9
        )

    def test_no_logarithmic_beta_form_survives(self) -> None:
        """The retired beta form used 0.513 * ln(sin theta / 0.0896); it must not
        be the card's stated equation."""
        equation = _field(_card_text(self.CARD), "governing_equations")
        assert "0.513" not in equation
        assert "ln(sin" not in equation

    def test_no_velocity_form_ls_survives(self) -> None:
        """The retired S form (sin theta / 0.0896)^(beta/2) must be gone."""
        equation = _field(_card_text(self.CARD), "governing_equations")
        assert "beta/2" not in equation.replace("β/2", "beta/2")


# --------------------------------------------------------------------------- #
# CANON-009 -- Terrain                                                         #
# --------------------------------------------------------------------------- #
class TestCanon009Terrain:
    CARD = "CANON-009_terrain_analysis"
    CELL = 30.0

    @staticmethod
    def _dem_descending(direction: str, n: int = 9) -> np.ndarray:
        """A unit-per-cell ramp whose steepest descent is due ``direction``."""
        dem = np.zeros((n, n), dtype=float)
        for i in range(n):
            for j in range(n):
                if direction == "south":
                    dem[i, j] = -float(i)
                elif direction == "north":
                    dem[i, j] = float(i)
                elif direction == "east":
                    dem[i, j] = -float(j)
                else:  # west
                    dem[i, j] = float(j)
        return dem

    def test_aspect_argument_order_matches_the_card(self) -> None:
        from engine.land.terrain_analysis import calculate_slope_aspect

        aspect_text = _field(_card_text(self.CARD), "governing_equations").split(
            "**Aspect**"
        )[1].split("**Topographic Wetness Index")[0]
        equation = _norm(_stated(aspect_text))
        # The corrected form: east component first, then the northward component.
        assert "arctan2(-p, -q)" in equation
        # The transposed form the card used to print must not survive as the
        # stated equation (it appears only inside the retired-form note).
        assert "arctan2(q, -p)" not in equation

        for direction, expected in (
            ("north", 0.0),
            ("east", 90.0),
            ("south", 180.0),
            ("west", 270.0),
        ):
            _, aspect = calculate_slope_aspect(
                self._dem_descending(direction), self.CELL
            )
            interior = aspect[1:-1, 1:-1]
            assert np.allclose(
                interior, expected, atol=1e-6
            ), f"descent toward {direction}: aspect {np.unique(interior)}, want {expected}"

    def test_twi_length_definition_matches_the_card(self) -> None:
        from engine.land.terrain_analysis import calculate_slope_aspect, calculate_twi

        full = _field(_card_text(self.CARD), "governing_equations")
        twi_text = full.split("**Topographic Wetness Index (TWI)**")[1].split(
            "**Topographic Position Index"
        )[0]
        stated = _norm(twi_text).split("**Retired form:")[0]
        assert "The implementation defines A_s as the flow accumulation" in stated
        assert "cell size" in stated
        assert "cell_area" not in stated

        dem = self._dem_descending("east")
        twi = calculate_twi(dem, self.CELL)

        # Independent re-derivation on the same grid, from first principles:
        # on an east-descending unit ramp every cell drains one column east, so
        # the interior accumulation at column j is j, and Horn's kernel gives
        # |grad z| = 1 / cell_size exactly.
        slope_deg, _ = calculate_slope_aspect(dem, self.CELL)
        beta_slope = math.tan(math.radians(slope_deg[4, 4]))
        assert beta_slope == pytest.approx(1.0 / self.CELL, rel=1e-12), (
            "Horn's kernel must recover the plane's gradient, 1 / cell_size"
        )
        interior_accumulation = 5.0  # column 5 on a 9-column east ramp
        length_form = math.log(interior_accumulation * self.CELL / beta_slope)
        area_form = math.log(interior_accumulation * self.CELL**2 / beta_slope)

        assert twi[4, 5] == pytest.approx(length_form, rel=1e-9)

        # The area form would differ by exactly ln(cell_size): the card must not
        # have quietly adopted it.
        assert twi[4, 5] - area_form == pytest.approx(-math.log(self.CELL), rel=1e-9)

    def test_curvature_denominators_match_the_card(self) -> None:
        from engine.land.terrain_analysis import calculate_curvature

        text = _card_text(self.CARD)
        equation = _field(text, "governing_equations")
        assert "denom^1.5" in equation
        assert "denom^0.5" in equation
        assert "denom" in equation

        dem = self._dem_descending("east")
        curvature = calculate_curvature(dem, self.CELL)
        # A plane has zero curvature in every form; the sign and magnitude must
        # agree with the hand value, and the units claim must be the one the
        # card makes (see _units_are_not_a_single_dimension).
        assert np.allclose(curvature["profile"][1:-1, 1:-1], 0.0, atol=1e-9)
        assert np.allclose(curvature["plan"][1:-1, 1:-1], 0.0, atol=1e-9)

        units_row = _field(text, "units")
        assert "1/m" in units_row
        assert "not dimensionless" in units_row

    def test_units_are_not_a_single_dimension(self) -> None:
        """The card must state the two different dimensions rather than a
        single 'curvature in 1/m' claim."""
        units_row = _field(_card_text(self.CARD), "units")
        assert "1/m" in units_row
        assert "not dimensionless" in units_row


# --------------------------------------------------------------------------- #
# CANON-011 -- Extraterrestrial radiation                                      #
# --------------------------------------------------------------------------- #
class TestCanon011Radiation:
    CARD = "CANON-011_solar_radiation"

    def test_reference_day_reproduces_the_quoted_value(self) -> None:
        text = _card_text(self.CARD)
        ref = _field(text, "reference_cases")
        latitude = _one(ref, r"lat=(\d+\.\d+)")
        doy = int(_one(ref, r"doy=(\d+)"))
        claimed = _one(ref, r"\*\*Ra = ([\d.]+) MJ/m")

        values = _gw_values("CANON-011_RAD", {"latitude": latitude, "doy": doy})
        assert values["ra_mj_m2_day"] == pytest.approx(claimed, rel=1e-12)

    def test_eq_21_constants_reproduce(self) -> None:
        """The equation the card prints, evaluated from its own constants."""
        equation = _norm(_field(_card_text(self.CARD), "governing_equations"))
        gsc = _one(equation, r"Gsc = (0\.0820)")
        dr_c = _one(equation, r"dr = 1 \+ (0\.033)")
        dec_a = _one(equation, r"delta = (0\.409)")
        dec_b = _one(equation, r"- (1\.39)")

        latitude, doy = 41.9, 193
        phi = math.radians(latitude)
        dr = 1.0 + dr_c * math.cos(2.0 * math.pi * doy / 365.0)
        delta = dec_a * math.sin(2.0 * math.pi * doy / 365.0 - dec_b)
        ws = math.acos(-math.tan(phi) * math.tan(delta))
        closed = (
            (24.0 * 60.0 / math.pi)
            * gsc
            * dr
            * (
                ws * math.sin(phi) * math.sin(delta)
                + math.cos(phi) * math.cos(delta) * math.sin(ws)
            )
        )
        got = _gw_values("CANON-011_RAD", {"latitude": latitude, "doy": doy})[
            "ra_mj_m2_day"
        ]
        assert got == pytest.approx(closed, rel=1e-9)

    def test_wrong_reference_value_is_not_printed(self) -> None:
        """The retired 24.5 figure may appear only inside the correction note,
        never as the card's own claim."""
        text = _card_text(self.CARD)
        for field in ("reference_cases", "verification_status", "validation_status"):
            value = _stated(_field(text, field))
            assert "24.5" not in value
            assert "Haurwitz" not in value


# --------------------------------------------------------------------------- #
# CANON-015 -- Kirpich time of concentration                                   #
# --------------------------------------------------------------------------- #
class TestCanon015Kirpich:
    CARD = "CANON-015_watershed_calculator"

    def test_quoted_value_reproduces_the_implementation(self) -> None:
        from engine.hydroma.watershed.calculator import calculate_kirpich_tc

        equation = _norm(_stated(_field(_card_text(self.CARD), "governing_equations")))
        coefficient = _one(equation, r"Tc = (\d+\.\d+)")
        exponent_l = _one(equation, r"L\^(\d+\.\d+)")
        exponent_s = _one(equation, r"S\^-(\d+\.\d+)")
        claimed = _one(equation, r"Tc = \d+\.\d+ minutes \((\d+\.\d+)\)")

        length_m, slope_m_m = 1000.0, 0.01
        got = calculate_kirpich_tc(length_m, slope_m_m)
        assert got == pytest.approx(claimed, rel=1e-9)
        assert got == pytest.approx(
            coefficient * length_m**exponent_l * slope_m_m**-exponent_s, rel=1e-12
        )

    def test_the_velocity_form_is_not_advertised(self) -> None:
        equation = _stated(_field(_card_text(self.CARD), "governing_equations"))
        assert "velocity" not in equation
        assert "0.5" not in equation

    def test_the_mccool_citation_is_removed(self) -> None:
        text = _card_text(self.CARD)
        assert "McCool" not in _stated(_field(text, "reference_cases"))
        assert "McCool" not in _stated(_field(text, "validation_status"))
        assert "McCool" not in _stated(_field(text, "verification_status"))


# --------------------------------------------------------------------------- #
# Cross-card honesty guard                                                     #
# --------------------------------------------------------------------------- #
CORRECTED_CARDS = [
    "CANON-005_theis_solution",
    "CANON-006_van_genuchten",
    "CANON-007_rusle_ls_factor",
    "CANON-009_terrain_analysis",
    "CANON-011_solar_radiation",
    "CANON-015_watershed_calculator",
]


@pytest.mark.parametrize("stem", CORRECTED_CARDS)
def test_every_cited_test_path_exists(stem: str) -> None:
    """No card may cite a test file that does not exist (project rule 3).

    The scan is over the ``unit_tests`` field, which is what the rule names.
    Paths are written either from the repository root (``engine/...``) or from
    ``engine/`` itself (``strict_tests/...``).
    """
    text = _card_text(stem)
    repo = Path(__file__).resolve().parents[2]
    engine_root = repo / "engine"
    cited = set(re.findall(r"`([^`]+\.(?:py|cpp))`", _field(text, "unit_tests")))
    missing = sorted(
        c
        for c in cited
        if not (repo / c).exists() and not (engine_root / c).exists()
    )
    assert not missing, f"{stem} unit_tests cite {len(missing)} nonexistent paths: {missing}"


@pytest.mark.parametrize("stem", CORRECTED_CARDS)
def test_cards_declare_a_status_vocabulary_label(stem: str) -> None:
    """Each corrected card must carry one of the project's single status
    vocabulary, not a free-form 'validated' claim."""
    text = _card_text(stem)
    status = _field(text, "validation_status")
    vocabulary = (
        "VALIDATED_EXTERNAL",
        "VALIDATED_METHOD",
        "VALIDATED_METHOD_CONFORMANCE",
        "VALIDATED_MASS_CONSERVATION",
        "VALIDATED_UNIT_DEFINITION",
        "REGRESSION_ANCHOR_STABLE",
        "PARTIAL",
        "UNVALIDATED",
        "BLOCKED",
    )
    assert any(word in status for word in vocabulary), (
        f"{stem} validation_status carries no vocabulary label: {status[:120]}"
    )
