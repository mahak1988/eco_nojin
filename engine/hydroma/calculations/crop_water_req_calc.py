"""Module for calculating crop water requirements."""

from __future__ import annotations

import logging
from datetime import date

from pydantic import BaseModel, Field

from engine.hydroma.climate.et_calculator import calc_et0_hargreaves

logger = logging.getLogger(__name__)


class DailyWeather(BaseModel):
    """Represents daily weather data."""

    date: date
    t_max_c: float = Field(..., description="Maximum daily temperature (Celsius)")
    t_min_c: float = Field(..., description="Minimum daily temperature (Celsius)")
    wind_speed_ms: float = Field(..., description="Average daily wind speed (m/s)")
    solar_radiation_mj_m2: float = Field(..., description="Daily solar radiation (MJ/m2)")
    humidity_mean_percent: float = Field(..., description="Mean daily humidity (%)")


class CropWaterReqInput(BaseModel):
    """Input parameters for crop water requirement calculation."""

    crop_type: str = Field(..., description="Type of crop (e.g., wheat, corn)")
    planting_date: date = Field(..., description="Planting date")
    harvest_date: date = Field(..., description="Harvest date")
    daily_weather_data: list[DailyWeather] = Field(..., description="List of daily weather data")
    kc_coefficients: list[float] = Field(
        ..., description="List of daily Kc coefficients matching weather data"
    )
    # Could also accept a path to a weather file or integrate with existing weather fetching


class CropWaterReqOutput(BaseModel):
    """Output results of crop water requirement calculation."""

    daily_et_crop: list[float] = Field(..., description="Daily crop evapotranspiration (mm/day)")
    seasonal_water_requirement: float = Field(
        ..., description="Total seasonal water requirement (mm)"
    )
    # Could include irrigation schedule


class CropWaterRequirementCalculator:
    """Calculates crop water requirements based on FAO 56 methodology."""

    def __init__(self):
        # In a full implementation, we might load Kc tables here
        pass

    def _calculate_et0_hargreaves(self, weather: DailyWeather) -> float:
        """Reference evapotranspiration by the Hargreaves-Samani method.

        Delegates to ``climate.et_calculator.calc_et0_hargreaves``, the single
        implementation. This copy evaluated its own expression, and it was not
        eq. 52: it used ``Ra ** 0.5`` where eq. 52 is linear in the
        millimetre-equivalent Ra, so every seasonal ETc and every irrigation
        requirement computed through this path was 4.1x too small. Its own
        comment called it "simplified version for demonstration".

        **Known limitation, unchanged by this fix.** The input field is
        ``solar_radiation_mj_m2``, measured global radiation Rs, and this method
        uses it as a stand-in for extraterrestrial radiation Ra. Rs is at most
        about 0.78 Rso, so this remains an approximation and the result is not
        eq. 52 evaluated on the right input. What the delegation fixes is the
        equation and the exponent; the input substitution needs a schema change
        and is recorded rather than silently altered.
        """
        t_mean = (weather.t_max_c + weather.t_min_c) / 2
        return calc_et0_hargreaves(
            t_min=weather.t_min_c,
            t_max=weather.t_max_c,
            t_mean=t_mean,
            ra_mj=weather.solar_radiation_mj_m2,
        )

    def execute(self, input_data: CropWaterReqInput) -> CropWaterReqOutput:
        """Main execution function."""
        logger.info(f"Calculating water requirement for crop: {input_data.crop_type}")

        if len(input_data.daily_weather_data) != len(input_data.kc_coefficients):
            raise ValueError("Length of weather data and Kc coefficients must match.")

        daily_et_crop_list = []
        for weather, kc in zip(
            input_data.daily_weather_data, input_data.kc_coefficients, strict=False
        ):
            # Get ET0 (could come from another module or be passed in)
            et0 = self._calculate_et0_hargreaves(weather)
            # ETc = Kc * ET0
            et_crop = kc * et0
            daily_et_crop_list.append(round(et_crop, 2))

        total_seasonal_req = sum(daily_et_crop_list)

        return CropWaterReqOutput(
            daily_et_crop=daily_et_crop_list,
            seasonal_water_requirement=round(total_seasonal_req, 2),
        )
