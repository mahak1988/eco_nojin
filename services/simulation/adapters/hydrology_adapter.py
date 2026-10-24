"""SWAT+ Adapter - Watershed hydrology & aquifer recharge"""

from datetime import UTC, datetime

from services._gateway_facade import calculate_runoff
from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext,
    SimulationResult,
    SimulationStatus,
    SimulationType,
)


def _scs_runoff_depth_mm(precipitation: float, curve_number: int) -> float:
    """SCS-CN runoff depth in mm, from the engine through the facade.

    The USDA-SCS triplet -- retention ``S = 25400/CN - 254``, initial
    abstraction ``Ia = 0.2 S`` and runoff depth ``Q = (P - Ia)^2 / (P + 0.8 S)``
    for ``P > Ia`` (else 0) -- is computed by the engine's
    ``RunoffCalculator._scs_cn_method`` (gateway CANON-004). Nothing here
    re-derives it, so this adapter cannot drift from the engine's value.
    """
    if precipitation <= 0.0:
        # CANON-004's input contract is precipitation > 0. A dry or negative
        # event is below every initial abstraction, which is the branch the
        # inline form took.
        return 0.0
    result = calculate_runoff(
        precipitation=float(precipitation), curve_number=float(curve_number)
    )
    # mypy: Any from the gateway result dict.
    depth: float = result["runoff_depth_mm"]
    return depth


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

        # SCS-CN equation: Q = (P - 0.2S)^2 / (P + 0.8S). Routed to the engine
        # (facade -> gateway CANON-004), which owns the retention S and the
        # initial abstraction Ia = 0.2 S internally.
        runoff = _scs_runoff_depth_mm(precipitation, cn)

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
            "sand": 60,
            "loamy_sand": 65,
            "sandy_loam": 70,
            "loam": 75,
            "silt_loam": 78,
            "silt": 80,
            "clay_loam": 82,
            "clay": 88,
        }
        return texture_cn.get(soil.texture.lower(), 75)
