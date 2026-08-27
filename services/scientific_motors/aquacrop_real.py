"""
Real AquaCrop Motor — AquaCrop-OSPy wrapper (Phase 2)
=====================================================
Runs the actual FAO AquaCrop crop-water productivity model
(`aquacrop` 3.x package, AquaCrop-OSPy) with REAL inputs:

- daily weather DataFrame (min/max temp, precipitation, reference ET0)
  from Open-Meteo ERA5 (Phase-1 climate path)
- soil texture from ISRIC SoilGrids (Phase-1 soil path)
- crop + planting date from the crop database / user request

Because a full season run is CPU-heavy (tens of seconds), execution is
delegated to a worker thread (`asyncio.to_thread`) so the API event loop
stays responsive; the chain runner adds result caching.

Honesty: any model failure returns MotorStatus.FAILED with the real
error message — no fabricated yield.
"""
from __future__ import annotations

import time
from typing import Any

import pandas as pd

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)


def _first_number(row: Any, column: str) -> float | None:
    """Extract a numeric value from a DataFrame row column (defensive)."""
    if column not in row:
        return None
    try:
        v = row[column]
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None

try:
    from aquacrop import (
        AquaCropModel,
        Crop,
        InitialWaterContent,
        IrrigationManagement,
        Soil,
    )
    AQUACROP_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    AquaCropModel = None  # type: ignore
    Crop = None  # type: ignore
    InitialWaterContent = None  # type: ignore
    IrrigationManagement = None  # type: ignore
    Soil = None  # type: ignore
    AQUACROP_AVAILABLE = False

# SoilGrids texture classes -> AquaCrop built-in soil classes
AQUACROP_SOIL_TYPES = {
    "sand": "Sand",
    "sandy_loam": "SandyLoam",
    "loam": "Loam",
    "silt_loam": "SiltLoam",
    "clay_loam": "ClayLoam",
    "clay": "Clay",
}
AQUACROP_VALID_SOILS = set(AQUACROP_SOIL_TYPES.values()) | {
    "LoamySand", "SandyClay", "SandyClayLoam", "Silt", "SiltClayLoam",
    "SiltClay", "Paddy", "Default",
}

# Common crop names -> AquaCrop built-in crop names
AQUACROP_CROP_ALIASES = {
    "wheat": "Wheat", "maize": "Maize", "corn": "Maize",
    "barley": "Barley", "cotton": "Cotton", "soybean": "Soybean",
    "potato": "Potato", "tomato": "Tomato", "sorghum": "Sorghum",
    "sunflower": "Sunflower", "rice": "PaddyRice", "sugarcane": "SugarCane",
    "quinoa": "Quinoa", "tef": "Tef", "cassava": "Cassava",
    "sugarbeet": "SugarBeet", "drybean": "DryBean",
}
AQUACROP_VALID_CROPS = {
    "Barley", "BarleyGDD", "Cotton", "CottonGDD", "Default", "DryBean",
    "DryBeanGDD", "Maize", "MaizeGDD", "PaddyRice", "PaddyRiceGDD",
    "Potato", "PotatoGDD", "PotatoLocalGDD", "Quinoa", "Sorghum",
    "SorghumGDD", "Soybean", "SoybeanGDD", "SugarBeet", "SugarBeetGDD",
    "SugarBeetGDD_UK", "SugarCane", "Sunflower", "SunflowerGDD", "Tomato",
    "TomatoGDD", "Wheat", "WheatGDD", "WheatGDD_1dec", "HydWheatGDD",
    "WheatLongGDD", "localpaddy", "MaizeChampionGDD", "Tef", "AlfalfaGDD",
    "Cassava",
}


class RealAquaCropMotor(AbstractScientificMotor):
    """FAO AquaCrop executed by AquaCrop-OSPy (real model, not a stub)."""

    @property
    def motor_type(self) -> MotorType:
        return MotorType.AQUACROP

    @property
    def display_name(self) -> str:
        return "AquaCrop 7 (AquaCrop-OSPy)"

    def get_input_requirements(self) -> list[MotorInput]:
        return [
            MotorInput("weather_df", "timeseries", description="Daily tmin/tmax/precip/reference_et"),
            MotorInput("soil_texture", "scalar", description="SoilGrids texture class"),
            MotorInput("crop_name", "scalar", description="FAO crop name, e.g. wheat"),
            MotorInput("planting_date", "scalar", description="YYYY-MM-DD"),
        ]

    def get_outputs(self) -> list[MotorOutput]:
        return [
            MotorOutput("yield_ton_ha", "scalar", "t/ha", "Dry yield"),
            MotorOutput("biomass_ton_ha", "scalar", "t/ha", "Total above-ground biomass"),
            MotorOutput("seasonal_irrigation_mm", "scalar", "mm", "Applied irrigation"),
            MotorOutput("water_productivity", "scalar", "kg/m3", "WP (yield per ET)"),
            MotorOutput("harvest_date", "scalar", "date", "Harvest date"),
        ]

    def _run_sync(
        self,
        weather_df: pd.DataFrame,
        soil_texture: str,
        crop_name: str,
        planting_date: str,
        sim_start: str,
        sim_end: str,
        irrigation_threshold_mm: float | None,
    ) -> dict[str, Any]:
        """Blocking AquaCrop run (called inside a worker thread)."""
        aqua_soil = AQUACROP_SOIL_TYPES.get(soil_texture, soil_texture)
        if aqua_soil not in AQUACROP_VALID_SOILS:
            raise ValueError(
                f"unknown AquaCrop soil type '{soil_texture}' "
                f"(valid: {sorted(AQUACROP_VALID_SOILS)})"
            )
        soil = Soil(soil_type=aqua_soil)

        aqua_crop = AQUACROP_CROP_ALIASES.get(crop_name.lower(), crop_name)
        if aqua_crop not in AQUACROP_VALID_CROPS:
            raise ValueError(
                f"unknown AquaCrop crop '{crop_name}' "
                f"(valid: {sorted(AQUACROP_VALID_CROPS)})"
            )
        # AquaCrop expects planting date as MM/DD (the year comes from the
        # simulation clock, see compute_crop_calendar.py)
        try:
            from datetime import datetime as _dt

            planting_md = _dt.strptime(planting_date, "%Y-%m-%d").strftime("%m/%d")
        except ValueError:
            planting_md = planting_date  # already MM/DD
        kwargs: dict[str, Any] = {"c_name": aqua_crop, "planting_date": planting_md}
        crop = Crop(**kwargs)

        if irrigation_threshold_mm and irrigation_threshold_mm > 0:
            irrigation = IrrigationManagement(
                irrigation_method=1,  # soil moisture threshold
                threshold=irrigation_threshold_mm,
            )
        else:
            irrigation = IrrigationManagement(irrigation_method=3)  # rainfed

        model = AquaCropModel(
            sim_start_time=sim_start.replace("-", "/"),
            sim_end_time=sim_end.replace("-", "/"),
            weather_df=weather_df,
            soil=soil,
            crop=crop,
            initial_water_content=InitialWaterContent(),  # start at field capacity
            irrigation_management=irrigation,
        )
        model.run_model(till_termination=True, process_outputs=True)

        out: dict[str, Any] = {"engine": "AquaCrop-OSPy 3.x"}
        results = model.get_simulation_results()
        if isinstance(results, pd.DataFrame) and len(results):
            row = results.iloc[-1]
            out["yield"] = _first_number(row, "Dry yield (tonne/ha)")
            out["fresh_yield"] = _first_number(row, "Fresh yield (tonne/ha)")
            out["seasonal_irrigation"] = _first_number(row, "Seasonal irrigation (mm)")
            hd = row.get("Harvest Date (YYYY/MM/DD)")
            out["harvest_date"] = str(hd) if hd is not None else None
        elif isinstance(results, dict):
            for key, sub in results.items():
                try:
                    out[str(key).lower()] = float(sub.iloc[-1].iloc[-1])
                except Exception:
                    continue
        # biomass from the crop growth outputs when available
        try:
            growth = model.get_crop_growth()
            if isinstance(growth, pd.DataFrame) and len(growth):
                b = _first_number(growth.iloc[-1], "Biomass")
                if b:
                    out["biomass"] = b
        except Exception:
            pass
        return out

    async def execute(
        self, inputs: dict[str, Any], parameters: MotorParameters
    ) -> MotorResult:
        start_time = time.time()
        run_id = f"AQUACROP_REAL_{int(time.time())}"

        if not AQUACROP_AVAILABLE:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message="aquacrop package not installed (pip install aquacrop)",
            )

        try:
            weather_rows = inputs["weather_rows"]  # list of dicts
            soil_texture = str(inputs.get("soil_texture", "loam"))
            crop_name = str(inputs.get("crop_name", "wheat"))
            planting_date = str(inputs.get("planting_date", "2025-03-01"))
            sim_start = str(parameters.custom_params.get("sim_start", "2025-01-01"))
            sim_end = str(parameters.custom_params.get("sim_end", "2025-12-31"))
            threshold = parameters.custom_params.get("irrigation_threshold_mm")

            if not weather_rows:
                raise ValueError("weather_rows is required (daily climate series)")

            df = pd.DataFrame(weather_rows)
            df["Date"] = pd.to_datetime(df["datetime"])
            df = (
                df.rename(columns={
                    "tmin": "MinTemp",
                    "tmax": "MaxTemp",
                    "precip": "Precipitation",
                    "et0": "ReferenceET",
                })
                [["MinTemp", "MaxTemp", "Precipitation", "ReferenceET", "Date"]]
                .dropna()
            )
            # avoid divide-by-zero in the crop model
            df["ReferenceET"] = df["ReferenceET"].clip(lower=0.1)
            # Restrict weather to the simulation window (+-30 days buffer)
            s0 = pd.Timestamp(sim_start) - pd.Timedelta(days=30)
            s1 = pd.Timestamp(sim_end) + pd.Timedelta(days=30)
            df = df[(df["Date"] >= s0) & (df["Date"] <= s1)]
            if len(df) < 30:
                raise ValueError(
                    "weather series does not cover the simulation window "
                    f"({sim_start}..{sim_end}); got {len(df)} days"
                )
            if df["Date"].min() > pd.Timestamp(sim_start):
                raise ValueError(
                    "climate data must start on or before the simulation start "
                    f"({sim_start}); earliest available is {df['Date'].min().date()}"
                )

            result = await asyncio.to_thread(
                self._run_sync,
                df, soil_texture, crop_name, planting_date,
                sim_start, sim_end, threshold,
            )

            # NOTE: AquaCrop-OSPy v3 reports Dry yield already in tonne/ha
            yield_ton_ha = float(result.get("yield", 0.0) or 0.0)
            biomass = float(result.get("biomass", 0.0) or 0.0)
            irrigation = float(result.get("seasonal_irrigation", 0.0) or 0.0)
            wp = float(result.get("water_productivity", 0.0) or 0.0)
            hd = result.get("harvest_date")
            harvest = str(hd)[:10] if hd else None

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "yield_ton_ha": round(yield_ton_ha, 3),
                    "biomass_ton_ha": round(biomass, 3),
                    "seasonal_irrigation_mm": round(irrigation, 1),
                    "water_productivity_kg_m3": round(wp, 3),
                    "harvest_date": harvest,
                    "crop": crop_name,
                    "engine": "AquaCrop-OSPy 3.x",
                    "raw_keys": list(result.keys()),
                },
                summary={
                    "yield_ton_ha": round(yield_ton_ha, 2),
                    "irrigation_mm": round(irrigation, 0),
                    "wp_kg_m3": round(wp, 2),
                },
                execution_time_seconds=round(time.time() - start_time, 3),
            )
        except Exception as exc:
            detail = str(exc) or type(exc).__name__
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=f"AquaCrop execution failed: {detail}",
                execution_time_seconds=round(time.time() - start_time, 3),
            )


# asyncio is imported lazily here to keep module import order clean
import asyncio  # noqa: E402
