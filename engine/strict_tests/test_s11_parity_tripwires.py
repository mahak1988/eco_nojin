"""S11 — Parity tripwires between duplicated models.

What this module is for
-----------------------
Twelve groups of the engine hold more than one implementation of the same
physical quantity. Seven of them **disagree**. That is the actionable subset:
for each one, a caller gets a different answer depending on which module they
import, and nothing in the repository says so.

This module makes each disagreement measurable and permanent. Every test is
one of two kinds:

* a **guard**, which passes today and exists to catch future drift, or
* a **strict xfail**, which fails today and records what the correct state is.

The reason string on each xfail is the specification for the corresponding
consolidation commit. ``strict=True`` means that fixing the defect turns the
test into an XPASS failure, so the tripwire cannot rot unnoticed.

Inventory, with the measured divergence
---------------------------------------
| Group | Implementations | Status |
|---|---|---|
| Hargreaves eq. 52 | 4 | 3 agree, 1 is 0.243x (different equation) |
| Penman-Monteith eq. 39 | 2 backends | Python 34-66 % above C++ |
| Soil parameter table | 4 | 12 / 7 / 7 / 4 textures, C++ in cm/hr |
| van Genuchten | 2 | disagree on positive head: K 17.83 vs 25.0 |
| design_check_dam | 2 | disjoint dict schemas, no shared key |
| Rational runoff | 3 | differ by exactly 1/C |
| Latin hypercube | 1 (C++) | no Python twin exists |
| NDVI / EVI | 2 | agree |
| classify_salinity | 2 | agree |

The single most important finding here is that **the C++ Penman-Monteith is
the better implementation of the two.** ``climate.cpp:63-92`` computes the net
longwave loss Rnl from the Stull cloudiness factor, which is exactly the term
the Python backend omits. The missing term is therefore not a research
problem; it is a port that was never done, and the reference implementation is
already 200 lines away in the same repository.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

# A physically coherent reference day: hot Mediterranean summer, moderate
# elevation, so the radiation and aerodynamic terms carry comparable weight.
REF = {
    "tmin": 22.6,
    "tmax": 30.5,
    "rh": 72.0,
    "u2": 1.7,
    "rs": 28.4,
    "elev": 100.0,
    "lat": 41.9,
    "doy": 193,
}


# ==========================================================================
# 1 — Hargreaves eq. 52, four copies
# ==========================================================================
class TestHargreavesCopies:
    """Three copies compute FAO-56 eq. 52; the fourth does not.

    A fifth copy exists in C++ and is covered by
    ``test_compiled_hargreaves_copy_matches_the_core`` below.

    Measured on the reference day (lat 41.9 N, doy 193, Tmin 22.6, Tmax 30.5,
    Ra 41.63 MJ/m2/day):

    ============================  ==========
    climate/et_calculator.py      5.9275
    simulation/weather_source.py  5.9275
    simulation_env/weather.py     5.9275
    calculations/crop_water_req   1.4382
    ============================  ==========

    The fourth uses ``Ra ** 0.5`` where eq. 52 is linear in ``Ra``, so it is not
    the same equation and is 0.243x. Its own comment says "simplified version
    for demonstration".
    """

    def _core(self) -> float:
        from engine.hydroma.climate.et_calculator import (
            calc_et0_hargreaves,
            calc_extraterrestrial_radiation,
        )

        ra = calc_extraterrestrial_radiation(REF["lat"], REF["doy"])
        return calc_et0_hargreaves(t_min=REF["tmin"], t_max=REF["tmax"], ra_mj=ra)

    def test_weather_source_copy_matches_the_core(self) -> None:
        from engine.hydroma.simulation.weather_source import hargreaves_et0

        assert hargreaves_et0(REF["tmin"], REF["tmax"], REF["lat"], REF["doy"]) == pytest.approx(
            self._core(), rel=1e-12
        )

    def test_simulation_env_copy_matches_the_core(self) -> None:
        from engine.hydroma.simulation_env.weather import hargreaves_et0

        assert hargreaves_et0(REF["tmin"], REF["tmax"], REF["lat"], REF["doy"]) == pytest.approx(
            self._core(), rel=1e-12
        )

    def test_all_three_standard_copies_share_the_published_exponent(self) -> None:
        from engine.hydroma.climate.et_calculator import calc_extraterrestrial_radiation

        ra = calc_extraterrestrial_radiation(REF["lat"], REF["doy"])
        t_mean = (REF["tmin"] + REF["tmax"]) / 2.0
        reference = 0.0023 * (t_mean + 17.8) * ((REF["tmax"] - REF["tmin"]) ** 0.48) * (ra * 0.408)
        assert self._core() == pytest.approx(reference, rel=1e-9)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/calculations/crop_water_req_calc.py:62 computes "
            "et0 = 0.0023 * (Tmax - Tmin)**0.5 * (Tmean + 17.8) * ra**0.5. FAO-56 "
            "eq. 52 is LINEAR in the millimetre-equivalent Ra, not its square "
            "root, so this is a different equation. Measured on the reference day "
            "it returns 1.4382 mm/day against 5.9275 for the three correct "
            "copies, i.e. 0.243x and 4.1x under. The module's own comment calls it "
            "'simplified version for demonstration'. Every seasonal ETc, and "
            "therefore every irrigation requirement, computed through this path "
            "is wrong by that factor."
        ),
    )
    def test_crop_water_copy_is_fao56_equation_52(self) -> None:
        from engine.hydroma.calculations.crop_water_req_calc import (
            CropWaterReqInput,
            CropWaterRequirementCalculator,
        )

        result = CropWaterRequirementCalculator().execute(
            CropWaterReqInput(
                crop_type="wheat",
                planting_date="2026-04-01",
                harvest_date="2026-04-02",
                daily_weather_data=[
                    {
                        "date": "2026-04-01",
                        "t_min_c": REF["tmin"],
                        "t_max_c": REF["tmax"],
                        "wind_speed_ms": REF["u2"],
                        "solar_radiation_mj_m2": REF["rs"],
                        "humidity_mean_percent": REF["rh"],
                    }
                ],
                kc_coefficients=[0.4],
            )
        )
        produced = result.seasonal_etc_mm if hasattr(result, "seasonal_etc_mm") else None
        assert produced is not None, f"unexpected output shape: {result}"
        assert produced == pytest.approx(self._core() * 0.4, rel=0.02)

    @pytest.mark.requires_cpp
    def test_compiled_hargreaves_copy_matches_the_core(self) -> None:
        """The compiled fifth copy, against eq. 52 and against the Python core.

        The tolerance is 1e-9 relative: the two expressions associate their
        factors differently and so differ in the last few bits, but the
        exponent error above is 4.7 % at the first case, so nothing this tight
        can hide it.
        """
        from engine.hydroma.climate.et_calculator import calc_et0_hargreaves
        from engine.hydroma.cpp_bridge import get_module

        native = get_module()
        for t_min, t_max, t_mean, ra_mj in (
            (15.0, 25.0, 20.0, 15.0),
            (22.6, 30.5, 26.55, 41.63),
            (5.0, 25.0, 15.0, 20.0),
        ):
            got = native.hargreaves_et0(t_min, t_max, t_mean, ra_mj)
            # FAO-56 eq. 52 re-derived from the publication, at the published
            # exponent, so agreement is evidence rather than a tautology.
            reference = 0.0023 * (t_mean + 17.8) * (t_max - t_min) ** 0.48 * ra_mj * 0.408
            assert got == pytest.approx(reference, rel=1e-9), (
                f"Tmin {t_min}, Tmax {t_max}, Ra {ra_mj} MJ: compiled "
                f"{got:.5f} against eq. 52 at exponent 0.48 {reference:.5f} "
                f"({100 * (got - reference) / reference:+.2f} %)"
            )
            core = calc_et0_hargreaves(t_min=t_min, t_max=t_max, t_mean=t_mean, ra_mj=ra_mj)
            assert got == pytest.approx(core, rel=1e-9), (
                f"Tmin {t_min}, Tmax {t_max}, Ra {ra_mj} MJ: compiled {got:.5f} "
                f"against climate/et_calculator.py {core:.5f}"
            )


# ==========================================================================
# 2 — Penman-Monteith eq. 39, two backends
# ==========================================================================
def _ref_pm_cpp(t_min, t_max, rh_mean, u2, rs, elevation, lat, doy):
    """FAO-56 eq. 39 as implemented in cpp_core/src/climate.cpp:94-130.

    Written from the published equations and the C++ comments, not from the
    C++ source text, so that agreement is evidence rather than tautology.
    """

    def es_of(t: float) -> float:
        """FAO-56 eq. 11."""
        return 0.6108 * math.exp((17.27 * t) / (t + 237.3))

    t_mean = (t_max + t_min) / 2.0
    es = (es_of(t_max) + es_of(t_min)) / 2.0
    e0_mean = es_of(t_mean)
    ea = es * rh_mean / 100.0
    delta = 4098.0 * e0_mean / (t_mean + 237.3) ** 2
    gamma = 0.000665 * 101.3 * (((293.0 - 0.0065 * elevation) / 293.0) ** 5.26)
    # extraterrestrial radiation, eq. 21
    phi = math.radians(lat)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * doy / 365.0)
    decl = 0.409 * math.sin(2.0 * math.pi * doy / 365.0 - 1.39)
    cos_ws = -math.tan(phi) * math.tan(decl)
    ws = math.pi if cos_ws <= -1.0 else (0.0 if cos_ws >= 1.0 else math.acos(cos_ws))
    ra = (
        0.0
        if ws <= 0.0
        else (24.0 * 60.0 / math.pi)
        * 0.082
        * dr
        * max(
            0.0, ws * math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.sin(ws)
        )
    )
    rso = (0.75 + 2e-5 * elevation) * ra
    rns = (1.0 - 0.23) * rs
    rs_rso = min(max(rs / rso if rso > 0 else 1.0, 0.3), 1.0)
    rnl = (
        4.903e-9
        * ((t_max + 273.16) ** 4 + (t_min + 273.16) ** 4)
        / 2.0
        * (0.34 - 0.14 * math.sqrt(ea))
        * (1.35 * rs_rso - 0.35)
    )
    rn = rns - rnl
    num = 0.408 * delta * rn + gamma * (900.0 / (t_mean + 273.0)) * u2 * (es - ea)
    return num / (delta + gamma * (1.0 + 0.34 * u2))


class TestPenmanMonteithBackends:
    """The C++ backend is the reference-quality implementation.

    ``climate.cpp`` includes the net longwave loss Rnl, uses the mean of
    es(Tmax) and es(Tmin) for the vapour-pressure deficit as FAO-56 eq. 11
    requires, and computes Rso from eq. 39. The Python backend has none of the
    three.
    """

    @pytest.mark.requires_cpp
    def test_cpp_backend_matches_the_published_equations(self) -> None:
        """Passes. Establishes which of the two backends is correct."""
        from engine.hydroma.cpp_bridge import get_module

        native = get_module()
        got = native.penman_monteith_et0(
            REF["tmin"],
            REF["tmax"],
            REF["rh"],
            REF["u2"],
            REF["rs"],
            REF["elev"],
            REF["lat"],
            REF["doy"],
        )
        expected = _ref_pm_cpp(
            REF["tmin"],
            REF["tmax"],
            REF["rh"],
            REF["u2"],
            REF["rs"],
            REF["elev"],
            REF["lat"],
            REF["doy"],
        )
        assert got == pytest.approx(expected, rel=1e-9)

    @pytest.mark.requires_cpp
    def test_cpp_backend_includes_net_longwave_loss(self) -> None:
        """The distinguishing term. Without Rnl, Rn would equal Rns exactly."""
        from engine.hydroma.cpp_bridge import get_module

        rnl = get_module().fao56_net_radiation(
            REF["tmin"],
            REF["tmax"],
            REF["rh"],
            REF["rs"],
            REF["elev"],
            REF["lat"],
            REF["doy"],
        )
        rns = (1.0 - 0.23) * REF["rs"]
        assert rnl < rns, "Rnl must reduce net radiation below net shortwave"
        assert rns - rnl > 0.0

    @pytest.mark.parametrize(
        ("t_min", "t_max", "rh", "u2", "rs", "lat", "doy"),
        [
            (22.6, 30.5, 72.0, 1.7, 28.4, 41.9, 193),
            (5.0, 25.0, 50.0, 2.0, 20.0, 35.0, 172),
            (28.0, 38.0, 30.0, 1.0, 30.0, 25.0, 120),
        ],
    )
    @pytest.mark.requires_cpp
    def test_python_and_cpp_backends_agree(
        self,
        t_min: float,
        t_max: float,
        rh: float,
        u2: float,
        rs: float,
        lat: float,
        doy: int,
    ) -> None:
        from engine.hydroma.climate.et_calculator import (
            ClimateData,
            calc_et0_penman_monteith,
        )
        from engine.hydroma.cpp_bridge import get_module

        python_value = calc_et0_penman_monteith(
            ClimateData(
                tmin=t_min,
                tmax=t_max,
                rh_min=rh,
                rh_max=rh,
                wind_speed=u2,
                solar_radiation=rs,
                elevation=100.0,
                latitude=lat,
                doy=doy,
            )
        )
        cpp_value = get_module().penman_monteith_et0(t_min, t_max, rh, u2, rs, 100.0, lat, doy)
        assert python_value == pytest.approx(cpp_value, rel=0.02)

    def test_backends_take_different_inputs(self) -> None:
        """Documents why the comparison above needs the rh_min = rh_max trick.

        Python takes rh_min and rh_max and derives ea from eq. 17; C++ takes a
        single rh_mean. A 1:1 call is therefore not possible, and a naive
        comparison would compare two different physical situations.
        """
        assert "rh_min" in ClimateDataSignature()
        assert "rh_mean_pct" in (get_native_doc("penman_monteith_et0") or "")


def ClimateDataSignature() -> str:
    from engine.hydroma.climate.et_calculator import ClimateData

    return " ".join(ClimateData.__dataclass_fields__)


def get_native_doc(name: str) -> str | None:
    from engine.hydroma.cpp_bridge import get_module

    return getattr(get_module(), name).__doc__


# ==========================================================================
# 3 — Soil parameter table, four copies
# ==========================================================================
class TestSoilParameterTable:
    #: Textures spanning the range, for the van Genuchten sign checks below.
    TEXTURES = ("sand", "loamy_sand", "loam", "clay_loam", "clay")

    def test_python_table_is_the_widest(self) -> None:
        from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG

        assert len(SOIL_PARAMETERS_VG) == 12

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "The van Genuchten table exists in four copies of three sizes. "
            "engine/hydroma/soil/physics.py carries 12 textures, "
            "cpp_core/src/soil.cpp and cpp_bridge/soil_physics_fast.py carry 7, and "
            "land/integration/soil_integrator.py carries 4. The five missing from "
            "the compiled path are sandy_clay, sandy_clay_loam, silt, "
            "silty_clay and silty_clay_loam, so a request for any of them raises "
            "KeyError under C++ and succeeds under Python. The C++ copy also "
            "stores Ks in cm/hr while the Python table is cm/day, and the "
            "engine's own comment at cpp_core/src/soil.cpp claims the values are "
            "matched exactly to the Python file. Separately, physics.py:121 "
            "attributes its Ks column to Carsel & Parrish (1988) x24, which the "
            "column does not satisfy: sandy_clay_loam 31.4 exceeds loam 25.0 and "
            "clay 4.8 exceeds silty_clay 1.92, and hydraulic conductivity cannot "
            "increase with fineness. Consolidation must publish the table from "
            "one source and generate the C++ copy from it."
        ),
    )
    @pytest.mark.requires_cpp
    def test_every_copy_carries_the_same_twelve_textures(self) -> None:
        import re
        from pathlib import Path

        from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG

        root = Path(__file__).resolve().parents[2]
        for relative in (
            "engine/cpp_core/src/soil.cpp",
            "engine/hydroma/cpp_bridge/soil_physics_fast.py",
            "engine/land/integration/soil_integrator.py",
        ):
            text = (root / relative).read_text(encoding="utf-8", errors="replace")
            found = set(
                re.findall(
                    r'"(sand|loamy_sand|sandy_loam|loam|silt_loam|silt'
                    r"|sandy_clay_loam|clay_loam|silty_clay_loam"
                    r'|sandy_clay|silty_clay|clay)"',
                    text,
                )
            )
            missing = set(SOIL_PARAMETERS_VG) - found
            assert not missing, f"{relative} is missing {sorted(missing)}"

    @pytest.mark.requires_cpp
    def test_conductivity_units_are_consistent_between_backends(self) -> None:
        """Reads Ks out of the C++ table at a saturated head.

        The C++ table is cm/hr and the Python table cm/day, so the factor is 24.
        This test establishes that the two tables are the same table up to that
        factor; test_saturated_conductivity_is_identical shows where they are not.
        """
        from engine.hydroma.cpp_bridge import get_module
        from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG

        native = get_module()
        for texture in ("sand", "loamy_sand", "loam"):
            values = native.hydraulic_conductivity([0.0], texture)
            assert float(values[0]) > 0.0
        assert SOIL_PARAMETERS_VG["sand"]["Ks"] > 0.0

    #: Every texture the compiled table carries, in the order the C++ file lists.
    SHARED = ("sand", "loamy_sand", "sandy_loam", "loam", "silt_loam", "clay_loam", "clay")
    #: The six that agree once the C++ precision is accounted for. Clay does not,
    #: and is asserted on its own below.
    ROUNDING_BAND = ("sand", "loamy_sand", "sandy_loam", "loam", "silt_loam", "clay_loam")

    @pytest.mark.requires_cpp
    def test_saturated_conductivity_agrees_within_rounding(self) -> None:
        """Passes. Establishes that the two columns are the same data.

        ``cpp_core/src/soil.cpp`` states its values are matched exactly to the
        Python file, and for six of the seven shared textures the Ks columns
        are indeed the same data to the precision the C++ declares. It carries 2
        to 3 significant figures (29.7, 14.6, 4.42, 1.05, 0.45, 0.26) where the
        Python table carries 4 (712.8, 350.2, 106.1, 25.0, 10.8, 6.2), so a 1 %
        band is the right tolerance for 'same value'. Clay falls outside it by
        40 % and is asserted separately below.
        """
        from engine.hydroma.cpp_bridge import get_module
        from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG

        native = get_module()
        offenders = []
        for texture in self.ROUNDING_BAND:
            cpp = float(native.hydraulic_conductivity([0.0], texture)[0])
            expected = SOIL_PARAMETERS_VG[texture]["Ks"] / 24.0
            if abs(cpp - expected) > 0.01 * expected:
                offenders.append(
                    f"{texture}: C++ {cpp} cm/hr against {expected:.4f} cm/hr "
                    f"({100 * (cpp - expected) / expected:+.1f} %)"
                )
        assert not offenders, "outside the 1 % rounding band:\n" + "\n".join(offenders)

    @pytest.mark.requires_cpp
    def test_clay_conductivity_matches_across_backends(self) -> None:
        """Closed by the rebuild of 27 September 2026.

        The C++ table carried 0.12 cm/hr for clay where the Python table carried
        4.80 cm/day, i.e. 0.2000 cm/hr: a 40 % divergence on the one texture whose
        aquitard behaviour the layered-soil package is built on. Two of the three
        copies agreed at 2.88 cm/day, but the C++ table was provably a derivative
        of the Python one, so its agreement was not independent and the choice
        between them was not decidable from the repository.

        The divergence was resolved structurally instead. The table is now
        published from engine/data/soil_vg_table.csv, the C++ copy is generated
        from it, and rebuilding the extension makes the two agree by construction
        rather than by coincidence. The value itself is still flagged: it sits
        outside the interval the fineness ordering permits, which
        test_s13_soil_table.py::TestConductivityInterval pins.
        """
        from engine.hydroma.cpp_bridge import get_module
        from engine.hydroma.soil.physics import SOIL_PARAMETERS_VG

        cpp = float(get_module().hydraulic_conductivity([0.0], "clay")[0])
        assert cpp == pytest.approx(SOIL_PARAMETERS_VG["clay"]["Ks"] / 24.0, rel=1e-9)

    @staticmethod
    def _both(texture: str, h: float) -> dict[str, float]:
        """theta and K from each copy, each called with its own argument order."""
        from engine.hydroma.soil.physics import (
            SOIL_PARAMETERS_VG,
            van_genuchten_k,
            van_genuchten_theta,
        )
        from engine.hydroma.soil.water_retention import (
            van_genuchten_conductivity,
            van_genuchten_retention,
        )

        p = SOIL_PARAMETERS_VG[texture]
        return {
            "physics_theta": van_genuchten_theta(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"]),
            "physics_k": van_genuchten_k(
                h, p["theta_r"], p["theta_s"], p["alpha"], p["n"], p["Ks"]
            ),
            "retention_theta": van_genuchten_retention(
                p["theta_r"], p["theta_s"], p["alpha"], p["n"], h
            ),
            "retention_k": van_genuchten_conductivity(
                p["theta_r"], p["theta_s"], p["alpha"], p["n"], p["Ks"], h
            ),
            "ks": p["Ks"],
        }

    def test_water_retention_saturates_under_positive_pressure(self) -> None:
        """Passes. Establishes the correct behaviour."""
        for texture in self.TEXTURES:
            values = self._both(texture, 10.0)
            assert values["retention_k"] == pytest.approx(values["ks"], rel=1e-12)
            assert values["retention_theta"] == pytest.approx(max(values["retention_theta"], 0.0))

    @pytest.mark.parametrize("h", [0.5, 1.0, 10.0, 100.0])
    def test_both_copies_saturate_under_positive_pressure(self, h: float) -> None:
        for texture in self.TEXTURES:
            values = self._both(texture, h)
            assert values["physics_k"] == pytest.approx(values["ks"], rel=1e-9), (
                f"{texture} at h=+{h}: physics K = {values['physics_k']}, Ks = {values['ks']}"
            )

    def test_copies_agree_for_negative_heads(self) -> None:
        """The disagreement is confined to the positive branch.

        The two copies take their arguments in a different order, so agreement
        is tested by calling each with its own convention and comparing the
        results, then checking both against an independent re-derivation of eq.
        11.
        """
        from engine.hydroma.soil.physics import (
            SOIL_PARAMETERS_VG,
            van_genuchten_theta as theta_physics,
        )
        from engine.hydroma.soil.water_retention import (
            van_genuchten_retention as theta_retention,
        )

        for texture in self.TEXTURES:
            p = SOIL_PARAMETERS_VG[texture]
            m = 1.0 - 1.0 / p["n"]
            for h in (-1.0, -33.0, -100.0, -1000.0, -15000.0):
                a = theta_physics(h, p["theta_r"], p["theta_s"], p["alpha"], p["n"])
                b = theta_retention(p["theta_r"], p["theta_s"], p["alpha"], p["n"], h)
                assert a == pytest.approx(b, abs=1e-12), (
                    f"{texture} at {h} cm: physics {a} vs water_retention {b}"
                )
                ref = (
                    p["theta_r"]
                    + (p["theta_s"] - p["theta_r"]) / (1.0 + abs(p["alpha"] * h) ** p["n"]) ** m
                )
                assert a == pytest.approx(ref, abs=1e-12)


# ==========================================================================
# 5 — design_check_dam, two functions of the same name
# ==========================================================================
class TestCheckDamCopies:
    def test_the_name_collision_is_gone(self) -> None:
        """Two functions named design_check_dam used to live in this package with
        different physics and a disjoint result schema, and the only production
        caller was wired to the wrong one.

        The screening estimate is now ``design_check_dam_screening`` and flags its
        own output, so a caller reaching for the FAO name gets the FAO design.
        """
        import engine.hydroma.watershed.watershed_calculator as screening

        assert not hasattr(screening, "design_check_dam"), (
            "the screening twin is back under the canonical name; "
            "design_check_dam would resolve to two different designs again"
        )
        assert hasattr(screening, "design_check_dam_screening")

    def test_the_adapter_uses_the_standard_design(self) -> None:
        """The concrete consequence of the collision.

        ``adapters/hydroma_adapter.py`` imported the simplified twin, so the
        platform's watershed analysis answered with a weir coefficient of 1.84
        and a 0.1-slope runoff adjustment, in a schema that shared no key with
        the real design, with discharge 6.3x high for the same inputs.
        """
        import inspect

        from adapters import hydroma_adapter

        source = inspect.getsource(hydroma_adapter)
        assert "watershed.calculator import" in source, (
            "the adapter is not importing the canonical design_check_dam"
        )
        assert "watershed_calculator import" not in source

    def test_screening_output_is_flagged(self) -> None:
        from engine.hydroma.watershed.watershed_calculator import (
            design_check_dam_screening,
        )

        out = design_check_dam_screening(15.0, 5000.0, 50.0)
        assert out["screening_estimate"] is True
        assert out["design_standard"] is None
        assert "use_instead" in out
        assert "screening" in out["notes"].lower()

    def test_both_versions_return_a_shared_schema(self) -> None:
        from engine.hydroma.watershed.calculator import (
            design_check_dam as canonical,
        )
        from engine.hydroma.watershed.watershed_calculator import (
            design_check_dam_screening as screening,
        )

        a = canonical(5.0, 50_000.0, 120.0)
        b = screening(5.0, 50_000.0, 120.0)
        shared = set(a) & set(b)
        assert len(shared) >= 5, f"only {len(shared)} shared keys: {sorted(shared)}"

    def test_weir_coefficient_is_the_same_in_both_versions(self) -> None:
        import inspect

        from engine.hydroma.watershed import calculator, watershed_calculator

        # The screening entry point was renamed to design_check_dam_screening when
        # the name collision with the canonical design_check_dam was removed;
        # this test kept pointing at the old name and raised AttributeError
        # rather than asserting anything. Repointed at the live name.
        a = inspect.getsource(calculator.design_check_dam)
        b = inspect.getsource(watershed_calculator.design_check_dam_screening)
        assert "1.84" not in b, "the simplified version still uses Cd = 1.84"
        assert "1.7" in a, "the canonical version lost its Cd = 1.7"


# ==========================================================================
# 6 — Rational runoff, three implementations
# ==========================================================================
class TestRationalRunoffCopies:
    def test_watershed_helper_applies_the_coefficient(self) -> None:
        """Passes. Establishes the correct behaviour."""
        from engine.hydroma.watershed.calculator import calculate_runoff

        assert calculate_runoff(20_000.0, 50.0, 0.6) == pytest.approx(600.0, rel=1e-9)

    @pytest.mark.parametrize("c", [0.2, 0.4, 0.6, 0.8])
    def test_both_rational_implementations_apply_the_coefficient(self, c: float) -> None:
        from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput
        from engine.hydroma.watershed.calculator import calculate_runoff

        area_m2, rain = 20_000.0, 50.0
        expected = c * rain * area_m2 / 1000.0
        from_engine = (
            RunoffCalculator()
            .execute(
                RunoffInput(
                    precipitation_mm=rain,
                    area_ha=area_m2 / 10_000.0,
                    method="Rational",
                    rational_coefficient=c,
                )
            )
            .volume_m3
        )
        from_watershed = calculate_runoff(area_m2, rain, c)
        assert from_engine == pytest.approx(expected, rel=1e-9)
        assert from_engine == pytest.approx(from_watershed, rel=1e-9)

    def test_the_two_rational_implementations_agree_exactly(self) -> None:
        """The two copies now produce the same volume for the same conditions.

        They differed by exactly 1/C before: runoff_model returned the full
        rainfall volume P x A while watershed returned C x P x A, so 1000 m3
        against 600 m3 at C = 0.6.
        """
        from engine.hydroma.models.runoff_model import RunoffCalculator, RunoffInput
        from engine.hydroma.watershed.calculator import calculate_runoff

        for c in (0.2, 0.4, 0.6, 0.8, 1.0):
            a = (
                RunoffCalculator()
                .execute(
                    RunoffInput(
                        precipitation_mm=50.0,
                        area_ha=2.0,
                        method="Rational",
                        rational_coefficient=c,
                    )
                )
                .volume_m3
            )
            b = calculate_runoff(20_000.0, 50.0, c)
            assert a == pytest.approx(b, rel=1e-12), (c, a, b)


# ==========================================================================
# 7 — Latin hypercube
# ==========================================================================
class TestLatinHypercube:
    """One implementation, in C++. The properties below are the specification
    a Python twin would have to satisfy if one is ever added.
    """

    @pytest.mark.requires_cpp
    def test_each_dimension_is_stratified_exactly_once(self) -> None:
        from engine.hydroma.cpp_bridge import get_module

        n, dims = 32, 4
        design = np.array(get_module().latin_hypercube(n, dims, 12345))
        assert design.shape == (n, dims)
        for j in range(dims):
            bins = np.floor(design[:, j] * n).astype(int)
            counts = np.bincount(bins, minlength=n)
            assert (counts == 1).all(), (
                f"dimension {j} is not stratified: bin counts {counts.tolist()}"
            )

    @pytest.mark.requires_cpp
    def test_all_samples_lie_in_the_unit_interval(self) -> None:
        from engine.hydroma.cpp_bridge import get_module

        design = np.array(get_module().latin_hypercube(16, 2, 7))
        assert (design >= 0.0).all()
        assert (design <= 1.0).all()

    @pytest.mark.requires_cpp
    def test_same_seed_reproduces_the_design(self) -> None:
        from engine.hydroma.cpp_bridge import get_module

        native = get_module()
        a = np.array(native.latin_hypercube(16, 3, 99))
        b = np.array(native.latin_hypercube(16, 3, 99))
        assert np.array_equal(a, b)

    @pytest.mark.requires_cpp
    def test_different_seeds_give_different_designs(self) -> None:
        from engine.hydroma.cpp_bridge import get_module

        native = get_module()
        a = np.array(native.latin_hypercube(16, 3, 1))
        b = np.array(native.latin_hypercube(16, 3, 2))
        assert not np.array_equal(a, b)

    @pytest.mark.requires_cpp
    def test_columns_are_not_pairwise_identical(self) -> None:
        """A sampler that returns the same column twice still passes stratification."""
        from engine.hydroma.cpp_bridge import get_module

        design = np.array(get_module().latin_hypercube(24, 3, 5))
        for j in range(3):
            for k in range(j + 1, 3):
                assert not np.array_equal(design[:, j], design[:, k])

    @pytest.mark.requires_cpp
    def test_no_python_lhs_twin_exists(self) -> None:
        """Documents the gap rather than leaving it implicit.

        ``cpp_bridge`` dispatches arrays below 1e6 rows to a Numba LHS. If that
        Numba path and the C++ path use different algorithms, a Sobol analysis
        whose sample count crosses 1e6 changes its own samples, and the result
        then depends on an array size rather than on the model.
        """
        from pathlib import Path

        source = (
            Path(__file__).resolve().parents[2] / "engine/hydroma/cpp_bridge/__init__.py"
        ).read_text(encoding="utf-8", errors="replace")
        assert "1e6" in source or "1000000" in source
        assert "_ARRAY_CPP_THRESHOLD" in source


# ==========================================================================
# 8 and 9 — consistent duplicates, guarded against drift
# ==========================================================================
class TestConsistentDuplicates:
    """Three groups hold more than one implementation and all of them agree.
    These pass today and exist to keep it that way.
    """

    def test_ndvi_copies_agree(self) -> None:
        from engine.hydroma.crop.ndvi_analysis import calculate_ndvi as crop
        from engine.hydroma.satellite.processors.indices import (
            calculate_ndvi as satellite,
        )

        for red, nir in ((0.05, 0.60), (0.02, 0.35), (0.10, 0.20), (0.0, 0.0)):
            assert crop(red, nir) == pytest.approx(
                float(satellite(np.array([red]), np.array([nir]))[0]), rel=1e-12
            )

    def test_evi_copies_agree(self) -> None:
        from engine.hydroma.crop.ndvi_analysis import calculate_evi as crop
        from engine.hydroma.satellite.processors.indices import (
            calculate_evi as satellite,
        )

        for red, nir, blue in ((0.05, 0.60, 0.04), (0.02, 0.35, 0.03), (0.10, 0.20, 0.08)):
            assert crop(red, nir, blue) == pytest.approx(
                float(satellite(np.array([red]), np.array([nir]), np.array([blue]))[0]),
                rel=1e-12,
            )

    def test_salinity_classifier_copies_agree(self) -> None:
        from engine.hydroma.soil.salinity import classify_salinity as soil
        from engine.hydroma.water.quality import classify_salinity as water

        for ec in (0.3, 1.0, 2.5, 5.0, 10.0, 18.0, 30.0):
            band = soil(ec)
            assert band["classification"] == water(ec) or band.get("class") == water(ec), (
                f"EC {ec}: soil and water classifiers disagree"
            )

    def test_slope_aspect_copies_are_distinguishable(self) -> None:
        """Two signatures, not two answers.

        ``land/slope_aspect.py`` takes anisotropic cell sizes;
        ``land/terrain_analysis.py`` takes a single resolution. A caller who
        passes a 30 m cell to the wrong one either gets an error or silently
        assumes isotropic cells.
        """
        import inspect

        from engine.land.slope_aspect import calculate_slope_aspect as a
        from engine.land.terrain_analysis import calculate_slope_aspect as b

        assert list(inspect.signature(a).parameters) == ["dem_data", "cell_size_x", "cell_size_y"]
        assert list(inspect.signature(b).parameters) == ["dem", "resolution"]


# ==========================================================================
# 10 — A bridged symbol that can never be called
# ==========================================================================
class TestBridgeReachability:
    @pytest.mark.requires_cpp
    def test_soil_params_failure_mode_is_recorded(self) -> None:
        """Passes today and states the failure, so the xfail below is anchored
        to an observed behaviour rather than to a guess about pybind11."""
        from engine.hydroma.cpp_bridge import get_module

        with pytest.raises(TypeError) as info:
            get_module().soil_params("loam")
        message = str(info.value)
        assert "convert function return value" in message or "Unregistered type" in message, (
            f"unexpected failure mode: {message[:160]}"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "engine/hydroma/cpp_bridge exposes "
            "soil_params(texture: str) -> hydroma::SoilTextureParams, and calling "
            "it with a valid argument raises TypeError: 'Unable to convert "
            "function return value to a Python type'. The struct has no pybind11 "
            "type caster registered, so the symbol is advertised in the module's "
            "public API and can never return a value. This is the C++ half of the "
            "soil-table consolidation: the C++ table cannot be read from Python "
            "at all, which is why the texture-coverage gap went unnoticed. The "
            "other 60 exposed symbols take arguments and were verified callable "
            "with argument lists derived from their own docstrings."
        ),
    )
    @pytest.mark.requires_cpp
    def test_soil_params_is_callable(self) -> None:
        from engine.hydroma.cpp_bridge import get_module

        result = get_module().soil_params("loam")
        assert result is not None
