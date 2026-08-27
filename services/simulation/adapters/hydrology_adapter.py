"""SWAT+ Adapter - Watershed hydrology & aquifer recharge"""
from datetime import UTC, datetime

from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext,
    SimulationResult,
    SimulationStatus,
    SimulationType,
)


@SimulatorRegistry.register
class SWATPlusAdapter(BaseSimulator):
    simulator_type = SimulationType.WATERSHED
    name = "SWAT+"
    version = "1.3.0"

    async def validate_context(self, ctx: SimulationContext) -> list[str]:
        errors = []
        if not ctx.bbox:
            errors.append("BBox required for watershed simulation")
        return errors

    async def run(self, ctx: SimulationContext) -> SimulationResult:
        """شبیه‌سازی هیدرولوژی حوضه + تغذیه آبخوان"""
        # SCS Curve Number method برای runoff
        cn = self._calculate_curve_number(ctx.soil)
        precipitation = ctx.weather.precipitation_mm

        # SCS-CN equation: Q = (P - 0.2S)^2 / (P + 0.8S)
        S = (25400 / cn) - 254
        if precipitation > 0.2 * S:
            runoff = ((precipitation - 0.2 * S) ** 2) / (precipitation + 0.8 * S)
        else:
            runoff = 0.0

        infiltration = precipitation - runoff
        # ۳۰٪ از نفوذ به آبخوان می‌رسد
        aquifer_recharge = infiltration * 0.3

        return SimulationResult(
            simulation_id=ctx.simulation_id,
            simulation_type=self.simulator_type,
            status=SimulationStatus.COMPLETED,
            started_at=datetime.now(UTC),
            summary={
                "curve_number": cn,
                "precipitation_mm": precipitation,
                "runoff_mm": round(runoff, 2),
                "infiltration_mm": round(infiltration, 2),
                "aquifer_recharge_mm": round(aquifer_recharge, 2),
                "baseflow_mm": round(infiltration * 0.2, 2),
                "et_mm": round(precipitation * 0.4, 2),
            },
        )

    def _calculate_curve_number(self, soil) -> int:
        """SCS Curve Number based on soil texture"""
        texture_cn = {
            "sand": 60, "loamy_sand": 65, "sandy_loam": 70,
            "loam": 75, "silt_loam": 78, "silt": 80,
            "clay_loam": 82, "clay": 88,
        }
        return texture_cn.get(soil.texture.lower(), 75)
