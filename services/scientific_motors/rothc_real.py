"""
Real RothC-26.3 Motor — pyRothC wrapper (Phase 2)
=================================================
Runs the actual Rothamsted Carbon Model 26.3 via the `pyRothC` package
(installed in the project venv) using REAL inputs:

- monthly temperature / precipitation / reference ET0 (Open-Meteo ERA5)
- clay % and initial SOC (ISRIC SoilGrids, from the Phase-1 real-land path)
- land-use dependent DPM/RPM ratio and residue carbon inputs

References
----------
- Coleman & Jenkinson (1996) RothC-26.3.
- Grol (pyRothC 0.0.4) — scipy odeint integration, euler fallback.

Honesty: failures raise a clear error into MotorResult.FAILED — no
fabricated carbon trajectories.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

import numpy as np

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)

try:  # pyRothC is a declared project dependency (package name: pyRothC)
    from pyRothC.RothC import RothC as PyRothC
    PYROTHC_AVAILABLE = True
except Exception:  # pragma: no cover - import guard
    PyRothC = None  # type: ignore
    PYROTHC_AVAILABLE = False


# DPM/RPM ratio by land use (RothC-26.3 defaults)
DPM_RPM_RATIOS = {
    "cropland": 1.44,
    "grassland": 0.67,
    "forest": 0.25,
    "shrubland": 0.50,
    "bare": 0.0,
}


class RealRothCMotor(AbstractScientificMotor):
    """RothC-26.3 executed by the pyRothC package (real model, not a stub)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def motor_type(self) -> MotorType:
        return MotorType.ROTH_C

    @property
    def display_name(self) -> str:
        return "RothC-26.3 (pyRothC)"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("monthly_temperature_c", "timeseries", description="12 monthly mean temps (°C)"),
            MotorInput("monthly_precipitation_mm", "timeseries", description="12 monthly precipitation sums (mm)"),
            MotorInput("monthly_et0_mm", "timeseries", description="12 monthly potential ET sums (mm)"),
            MotorInput("clay_pct", "scalar", description="Soil clay content (%)"),
            MotorInput("soc_initial_t_ha", "scalar", description="Initial topsoil SOC (t C/ha)"),
            MotorInput("land_use", "scalar", required=False, description="cropland/grassland/forest/..."),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("final_soc_t_ha", "scalar", "t C/ha", "Total SOC at the end of the run"),
            MotorOutput("soc_change_t_ha_yr", "scalar", "t C/ha/yr", "Mean annual SOC change"),
            MotorOutput("pools", "scalar", "t C/ha", "Final RothC pools (DPM/RPM/BIO/HUM/IOM)"),
            MotorOutput("annual_series", "timeseries", "t C/ha", "Annual total SOC trajectory"),
        ]

    async def execute(
        self, inputs: Dict[str, Any], parameters: MotorParameters
    ) -> MotorResult:
        start_time = time.time()
        run_id = f"ROTHC_REAL_{int(time.time())}"

        if not PYROTHC_AVAILABLE:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message="pyRothC package not installed (pip install pyRothC)",
            )

        try:
            t_month = np.asarray(inputs["monthly_temperature_c"], dtype=float)
            p_month = np.asarray(inputs["monthly_precipitation_mm"], dtype=float)
            e_month = np.asarray(inputs["monthly_et0_mm"], dtype=float)
            clay_pct = float(inputs.get("clay_pct", 23.4))
            soc_t_ha = float(inputs.get("soc_initial_t_ha", 30.0))
            land_use = str(inputs.get("land_use", "cropland"))
            years = int(parameters.custom_params.get("years", 20))
            input_carbon = float(parameters.custom_params.get("input_carbon_t_ha_yr", 1.7))
            farmyard_manure = float(parameters.custom_params.get("farmyard_manure_t_ha_yr", 0.0))
            bare = bool(parameters.custom_params.get("bare", land_use == "bare"))

            if len(t_month) != 12 or len(p_month) != 12 or len(e_month) != 12:
                raise ValueError("monthly climate inputs must contain exactly 12 values")

            # RothC initial pools: IOM = 0.049 * SOC^1.139 (RothC-26.3);
            # remaining SOC starts in HUM (documented approximation).
            iom = 0.049 * soc_t_ha ** 1.139
            hum = max(0.0, soc_t_ha - iom)
            c0 = np.array([0.0, 0.0, 0.0, hum, iom])

            dr = DPM_RPM_RATIOS.get(land_use, 1.44)

            model = PyRothC(
                temperature=t_month.tolist(),
                precip=p_month.tolist(),
                evaporation=e_month.tolist(),
                years=years,
                C0=c0,
                input_carbon=input_carbon,
                farmyard_manure=farmyard_manure,
                clay=clay_pct,
                soil_thickness=25.0,
                DR=dr,
                pE=1.0,          # potential ET0 (FAO-56) → pE=1.0
                bare=bare,
            )
            df = model.compute()  # monthly pool matrix (years*12 rows)

            annual = [
                float(df.iloc[i * 12:(i + 1) * 12].sum(axis=1).mean())
                for i in range(years)
            ]
            final_pools = {k: round(float(v), 3) for k, v in df.iloc[-1].items()}
            final_soc = float(df.iloc[-1].sum())
            change = (final_soc - soc_t_ha) / max(1, years)

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "final_soc_t_ha": round(final_soc, 3),
                    "soc_change_t_ha_yr": round(change, 4),
                    "pools": final_pools,
                    "annual_series": [round(v, 3) for v in annual],
                    "initial_soc_t_ha": round(soc_t_ha, 3),
                    "years": years,
                    "engine": "pyRothC 0.0.4 (RothC-26.3)",
                },
                summary={
                    "soc_final_t_ha": round(final_soc, 2),
                    "soc_change_t_ha_yr": round(change, 3),
                },
                execution_time_seconds=round(time.time() - start_time, 3),
            )
        except Exception as exc:
            return MotorResult(
                run_id=run_id, motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=f"RothC-26.3 execution failed: {exc}",
                execution_time_seconds=round(time.time() - start_time, 3),
            )
