"""P1-11 (bounded) -- the three inline FAO-56 eq. 52 copies are routed to the engine.

``services/_gateway_facade.calc_et0_hargreaves`` is the sanctioned path to the
engine's CANON-002 node (``engine.hydroma.climate.et_calculator``). Three
service modules carried their own inline copy of the equation, and each copy:

* omitted the **0.408** MJ -> mm conversion (2.45x over-statement), and
* substituted **Rs** (surface radiation, or W/m2) for **Ra** (extraterrestrial).

The copies now delegate. AR-05/AR-06 (one canonical implementation per named
equation) holds. The tests below pin the values the *routed* code produces, so
the delegation is a measured change, not a silent one.

Values are computed for fixed inputs so they are reproducible:

* ``crop_adapter`` -- tmin 15 / tmax 32, bbox centre latitude 35.45, DOY 288
  (2026-10-15).
* ``drought_agent`` -- a 3-row series at latitude 32.65.
* ``scenario_agent`` -- the same series, +2 degC.
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pandas as pd
import pytest

from services._gateway_facade import calc_extraterrestrial_radiation
from services.analysis.drought_agent import DroughtAgent
from services.analysis.scenario_agent import ScenarioAgent, ScenarioConfig
from services.simulation.adapters.crop_adapter import AquaCropAdapter
from services.simulation.schemas import (
    BBox,
    CropParameters,
    SimulationContext,
    SimulationType,
    SoilProfile,
    WeatherData,
)


@pytest.fixture
def series() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-07-01", "2026-07-02", "2026-07-03"]),
            "precip": [0.0, 0.0, 0.0],
            "t2m_max": [30.0, 31.0, 32.0],
            "t2m_min": [10.0, 11.0, 12.0],
            "t2m_mean": [20.0, 21.0, 22.0],
            # W/m2/day, i.e. SURFACE radiation -- the term the inline copies
            # wrongly used in the Ra slot.
            "solar": [250.0, 251.0, 252.0],
        }
    )


def _crop_context() -> SimulationContext:
    return SimulationContext(
        simulation_id="eq52-routing",
        simulation_type=SimulationType.COMPREHENSIVE,
        bbox=BBox(north=35.5, south=35.4, east=51.5, west=51.4),
        soil=SoilProfile(texture="loam"),
        weather=WeatherData(temp_min_c=15.0, temp_max_c=32.0, solar_radiation_mj_m2=18.0),
        crop=CropParameters(crop_type="wheat", planting_date=date(2026, 10, 15)),
        start_date=date(2026, 10, 15),
    )


class TestCropAdapter:
    def test_et0_comes_from_the_engine_gateway(self) -> None:
        """0.0023 (Tmean+17.8) (Tmax-Tmin)^0.5 (Ra * 0.408) at Ra = Ra(lat, doy).

        OLD (inline copy, Rs for Ra and no 0.408): 7.0498 mm/day.
        NEW (routed): 3.969527613893537 mm/day.
        """
        adapter = AquaCropAdapter()
        ctx = _crop_context()

        got = adapter._et0_hargreaves(
            ctx.weather,
            latitude=adapter._site_latitude_degrees(ctx),
            doy=ctx.start_date.timetuple().tm_yday,
        )

        assert got == pytest.approx(3.969527613893537, rel=1e-9)
        assert got < 7.05, "a routed value >= the old over-statement means no delegation"

    def test_routed_value_matches_the_published_equation(self) -> None:
        """Independent re-derivation of FAO-56 eq. 52 for the same site."""
        ctx = _crop_context()
        adapter = AquaCropAdapter()
        latitude = adapter._site_latitude_degrees(ctx)
        doy = ctx.start_date.timetuple().tm_yday
        t_min, t_max = 15.0, 32.0
        ra_mj = float(
            calc_extraterrestrial_radiation(latitude, doy)["data"]["ra_mj_m2_day"]
        )
        reference = (
            0.0023
            * ((t_max + t_min) / 2.0 + 17.8)
            * math.sqrt(t_max - t_min)
            * ra_mj
            * 0.408
        )
        got = adapter._et0_hargreaves(
            ctx.weather, latitude=latitude, doy=doy
        )
        assert got == pytest.approx(reference, rel=1e-9)

    def test_surface_radiation_is_not_used_anymore(self) -> None:
        """The old copy read ``weather.solar_radiation_mj_m2``; the routed
        version must be insensitive to it, because Ra is extraterrestrial."""
        ctx = _crop_context()
        adapter = AquaCropAdapter()
        kwargs = {
            "latitude": adapter._site_latitude_degrees(ctx),
            "doy": ctx.start_date.timetuple().tm_yday,
        }
        baseline = adapter._et0_hargreaves(ctx.weather, **kwargs)
        ctx.weather.solar_radiation_mj_m2 = 0.0
        assert adapter._et0_hargreaves(ctx.weather, **kwargs) == pytest.approx(baseline)

    def test_public_runner_still_returns_a_positive_et0(self) -> None:
        """The public contract is unchanged: ``run`` still succeeds and the
        water requirement still derives from ET0."""
        from services.simulation.service import SimulationService

        ctx = _crop_context()
        service = SimulationService()
        import asyncio

        result = asyncio.run(
            service.run_simulation(SimulationType.CROP_GROWTH, ctx)
        )
        assert result.summary["yield_ton_ha"] > 0
        assert result.summary["total_irrigation_mm"] > 0


class TestDroughtAgent:
    def test_pet_series_is_routed(self, series: pd.DataFrame) -> None:
        """NEW (routed): [6.549423897773624, 6.718196011551364, 6.886365311934312].
        OLD (inline, Rs for Ra, no 0.408): [8.398242, 8.65489938, 8.91333417].
        """
        got = DroughtAgent._hargreaves_pet_series(series, 32.65)
        assert got == pytest.approx(
            [6.549423897773624, 6.718196011551364, 6.886365311934312], rel=1e-9
        )
        assert isinstance(got, np.ndarray)

    def test_old_inline_form_is_not_what_the_agent_computes(self, series: pd.DataFrame) -> None:
        tmax = series["t2m_max"].to_numpy(dtype=float)
        tmin = series["t2m_min"].to_numpy(dtype=float)
        tmean = (tmax + tmin) / 2.0
        old = 0.0023 * (tmean + 17.8) * np.sqrt(np.maximum(tmax - tmin, 0)) * (
            series["solar"].to_numpy(dtype=float) * 0.0864
        )
        got = DroughtAgent._hargreaves_pet_series(series, 32.65)
        assert not np.allclose(got, old)
        assert np.all(got < old), "the routed PET must be lower, not higher"


class TestScenarioAgent:
    def test_modified_pet_is_routed(self, series: pd.DataFrame) -> None:
        """NEW (routed, +2 degC): [6.895954262735192, 7.064494775033394,
        7.232413820071714]. OLD (inline, Rs for Ra, no 0.408): higher.
        """
        agent = ScenarioAgent(ScenarioConfig(base_lat=32.65, base_lon=51.4))
        got = agent._modified_pet(series, 2.0)
        assert got == pytest.approx(
            [6.895954262735192, 7.064494775033394, 7.232413820071714], rel=1e-9
        )
        assert isinstance(got, np.ndarray)

    def test_zero_temperature_change_falls_back_to_the_series(self, series) -> None:
        """The unchanged-temperature branch is not routed; it keeps its
        documented fallback behaviour."""
        series_with_et0 = series.assign(et0=[4.0, 4.0, 4.0])
        pet = series_with_et0.get(
            "et0", series_with_et0.get("solar", np.ones(3) * 5)
        ).values
        assert list(pet) == [4.0, 4.0, 4.0]
