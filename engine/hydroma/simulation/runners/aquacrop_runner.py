"""AquaCrop-OSPy runner (Phase 3, sprint 1).

Wraps the FAO AquaCrop model (aquacrop package 3.1.0) behind the standard
ModelRunner interface. Weather can be supplied by the caller; otherwise a
synthetic growing-season series is generated so the runner stays usable
offline. All outputs are labeled data_source="simulated" (model output is
never presented as measured field data).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from engine.hydroma.simulation.runners.base import ModelRunner

# Weather column names required by aquacrop 3.x.
WEATHER_COLUMNS = ["Date", "MinTemp", "MaxTemp", "ReferenceET", "Precipitation"]


def _mmdd(date_str: str) -> str:
    """Convert 'YYYY/MM/DD' to 'MM/DD' (aquacrop 3.x Crop format)."""
    parts = date_str.split("/")
    if len(parts) == 3:
        return f"{parts[1]}/{parts[2]}"
    return date_str


def synthetic_weather(
    start: str,
    end: str,
    tmin_base: float = 10.0,
    tmax_base: float = 24.0,
    eto: float = 5.0,
    precip: float = 6.0,
) -> pd.DataFrame:
    """Build a synthetic daily weather frame covering [start, end].

    Dates are parsed from 'YYYY/MM/DD'. Temperatures ramp linearly across
    the window; ET0 and precipitation are constant (placeholder climate).
    """
    dates = pd.date_range(start.replace("/", "-"), end.replace("/", "-"), freq="D")
    n = len(dates)
    ramp = np.linspace(0.0, 1.0, n)
    # Column ORDER matters: aquacrop 3.x reads weather_df.values positionally
    # as [temp_min, temp_max, precipitation, et0] and keeps Date last
    # (matches the package's own example CSVs).
    return pd.DataFrame(
        {
            "MinTemp": tmin_base + 8.0 * ramp,
            "MaxTemp": tmax_base + 12.0 * ramp,
            "Precipitation": np.full(n, precip),
            "ReferenceET": np.full(n, eto),
            "Date": dates,
        }
    )


class AquaCropRunner(ModelRunner):
    """Run one AquaCrop season and return provenance-labeled results."""

    name = "AquaCrop-OSPy"
    version = "3.1.0"

    def __init__(self, end_buffer_days: int = 15) -> None:
        self._end_buffer_days = end_buffer_days

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """Run a single season.

        Accepted kwargs: crop (default Wheat), soil_type (default SiltLoam),
        planting_date, harvest_date ('YYYY/MM/DD'), weather (DataFrame or None).
        """
        crop = kwargs.get("crop", "Wheat")
        soil_type = kwargs.get("soil_type", "SiltLoam")
        planting_date = kwargs.get("planting_date", "2020/03/01")
        harvest_date = kwargs.get("harvest_date", "2020/07/20")
        weather = kwargs.get("weather")

        sim_end = pd.Timestamp(harvest_date.replace("/", "-")) + pd.Timedelta(
            days=self._end_buffer_days
        )
        weather_df = weather if weather is not None else synthetic_weather(
            planting_date, sim_end.strftime("%Y/%m/%d")
        )
        missing = [c for c in WEATHER_COLUMNS if c not in weather_df.columns]
        if missing:
            raise ValueError(f"weather missing columns: {missing}")
        if weather_df["Date"].max() < sim_end:
            raise ValueError(
                f"weather data ends before simulation end {sim_end:%Y/%m/%d}; "
                "extend the weather series"
            )

        from aquacrop import AquaCropModel, Crop, InitialWaterContent, Soil

        model = AquaCropModel(
            sim_start_time=planting_date,
            sim_end_time=sim_end.strftime("%Y/%m/%d"),
            weather_df=weather_df,
            soil=Soil(soil_type=soil_type),
            crop=Crop(
                c_name=crop,
                planting_date=_mmdd(planting_date),
                harvest_date=_mmdd(harvest_date),
            ),
            initial_water_content=InitialWaterContent(value=["FC"]),
        )
        finished = model.run_model(till_termination=True, initialize_model=True)
        if not finished:
            raise RuntimeError("AquaCrop simulation did not finish")
        results = model.get_simulation_results()
        growth = model.get_crop_growth()

        yield_kg_ha = self._parse(results, ("Dry yield (tonne/ha)", "Yield"), tonnes_to_kg=True)
        # biomass peaks during the season and may read 0 at the tail; take the max.
        biomass_kg_ha = self._parse_max(growth, ("biomass", "Biomass"))
        residue = None
        if yield_kg_ha is not None and biomass_kg_ha is not None:
            residue = max(biomass_kg_ha - yield_kg_ha, 0.0)

        return {
            "crop": crop,
            "yield_kg_ha": yield_kg_ha,
            "biomass_kg_ha": biomass_kg_ha,
            "residue_kg_ha": residue,
            "et_mm": None,
            "wue_kg_m3": None,
            "data_source": "simulated",
            "model": f"AquaCrop-OSPy {self.version}",
            "raw_keys": sorted(str(k) for k in results.keys()),
        }

    @staticmethod
    def _parse(
        container: dict[str, Any],
        candidates: tuple[str, ...],
        tonnes_to_kg: bool = False,
    ) -> float | None:
        """Return the last scalar found among candidate result keys."""
        for key in candidates:
            if key not in container:
                continue
            value = container[key]
            if hasattr(value, "values"):
                value = value.values
            try:
                arr = np.asarray(value, dtype=float).ravel()
            except (TypeError, ValueError):
                continue
            if arr.size == 0 or not np.isfinite(arr[-1]):
                continue
            number = float(arr[-1])
            if tonnes_to_kg and 0.0 < number < 50.0:
                number *= 1000.0
            return number
        return None

    @staticmethod
    def _parse_max(
        container: dict[str, Any],
        candidates: tuple[str, ...],
    ) -> float | None:
        """Return the maximum finite value found among candidate keys."""
        for key in candidates:
            if key not in container:
                continue
            value = container[key]
            if hasattr(value, "values"):
                value = value.values
            try:
                arr = np.asarray(value, dtype=float).ravel()
            except (TypeError, ValueError):
                continue
            finite = arr[np.isfinite(arr)]
            if finite.size == 0:
                continue
            return float(finite.max())
        return None
