"""SimulationService - لایه کسب‌وکار"""

from services.simulation.engine.orchestrator import SimulationOrchestrator
from services.simulation.schemas import (
    SimulationContext,
    SimulationResult,
    SimulationType,
)


class SimulationService:
    def __init__(self, db=None):
        self.db = db
        self.orchestrator = SimulationOrchestrator()

    async def run_simulation(
        self, sim_type: SimulationType, ctx: SimulationContext,
    ) -> SimulationResult:
        return await self.orchestrator.run_single(sim_type, ctx)

    async def run_comprehensive(self, ctx: SimulationContext) -> dict[str, SimulationResult]:
        return await self.orchestrator.run_comprehensive(ctx)

    def list_simulators(self) -> list[dict]:
        return self.orchestrator.list_simulators()
