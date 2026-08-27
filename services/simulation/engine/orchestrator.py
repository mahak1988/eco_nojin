"""Simulation Orchestrator - هماهنگ‌کننده چند شبیه‌ساز"""
import uuid
from datetime import UTC, datetime

from services.simulation.base import SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext,
    SimulationResult,
    SimulationStatus,
    SimulationType,
)


class SimulationOrchestrator:
    """اجرای ترکیبی چند شبیه‌ساز برای تحلیل جامع"""

    def __init__(self):
        self.registry = SimulatorRegistry()
        # بارگذاری adapterها
        import services.simulation.adapters  # noqa: F401

    async def run_comprehensive(self, ctx: SimulationContext) -> dict[str, SimulationResult]:
        """اجرای تمام شبیه‌سازی‌های مرتبط برای یک context"""
        results = {}

        sim_types = [
            SimulationType.CROP_GROWTH,
            SimulationType.SOIL_CARBON,
            SimulationType.WATER_EROSION,
            SimulationType.WIND_EROSION,
            SimulationType.INFILTRATION,
        ]

        # اگر windbreak وجود دارد
        if ctx.windbreak:
            sim_types.append(SimulationType.WINDBREAK)

        # اگر multi-layer وجود دارد
        if ctx.multi_layer:
            sim_types.append(SimulationType.MULTI_LAYER)

        # اگر bbox وجود دارد، watershed را هم اجرا کن
        if ctx.bbox:
            sim_types.append(SimulationType.WATERSHED)

        for sim_type in sim_types:
            simulator = self.registry.get(sim_type)
            if simulator:
                # یک simulation_id منحصر به فرد برای هر شبیه‌سازی
                child_ctx = ctx.model_copy()
                child_ctx.simulation_id = f"{ctx.simulation_id or uuid.uuid4()}_{sim_type.value}"
                result = await simulator.execute(child_ctx)
                results[sim_type.value] = result

        return results

    async def run_single(
        self, sim_type: SimulationType, ctx: SimulationContext,
    ) -> SimulationResult:
        """اجرای یک شبیه‌ساز خاص"""
        simulator = self.registry.get(sim_type)
        if not simulator:
            return SimulationResult(
                simulation_id=ctx.simulation_id,
                simulation_type=sim_type,
                status=SimulationStatus.FAILED,
                started_at=datetime.now(UTC),
                error=f"No simulator registered for {sim_type.value}",
            )
        return await simulator.execute(ctx)

    def list_simulators(self) -> list[dict]:
        return self.registry.list_all()
