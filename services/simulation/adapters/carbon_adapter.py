"""RothC Adapter - Soil organic carbon turnover"""
from datetime import UTC, datetime

from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext,
    SimulationResult,
    SimulationStatus,
    SimulationType,
)


@SimulatorRegistry.register
class RothCAdapter(BaseSimulator):
    simulator_type = SimulationType.SOIL_CARBON
    name = "RothC-26.3"
    version = "26.3"

    async def validate_context(self, ctx: SimulationContext) -> list[str]:
        errors = []
        if ctx.soil.organic_carbon_pct <= 0:
            errors.append("Initial SOC must be positive")
        return errors

    async def run(self, ctx: SimulationContext) -> SimulationResult:
        """پیش‌بینی ترشح کربن خاک برای ۲۰ سال"""
        try:
            # محاسبه ساده‌شده بر اساس RothC
            initial_soc = ctx.soil.organic_carbon_pct
            years = 20

            # سناریوی بهبود خاک با residue management
            yearly_soc = []
            soc = initial_soc
            for year in range(years):
                # افزایش ۲-۳٪ سالانه با مدیریت خوب
                growth_rate = 0.025 if year < 10 else 0.015
                soc = soc * (1 + growth_rate)
                yearly_soc.append({"year": year + 1, "soc_t_ha": round(soc, 3)})

            total_sequestered = soc - initial_soc
            co2e = total_sequestered * 44 / 12  # C to CO2

            return SimulationResult(
                simulation_id=ctx.simulation_id,
                simulation_type=self.simulator_type,
                status=SimulationStatus.COMPLETED,
                started_at=datetime.now(UTC),
                summary={
                    "initial_soc_t_ha": initial_soc,
                    "final_soc_t_ha": round(soc, 3),
                    "total_sequestered_t_ha": round(total_sequestered, 3),
                    "co2e_sequestered_t_ha": round(co2e, 3),
                    "carbon_credits_eligible": round(co2e * 0.85, 3),
                    "projection_years": years,
                },
                time_series=yearly_soc,
            )
        except Exception as e:
            return SimulationResult(
                simulation_id=ctx.simulation_id,
                simulation_type=self.simulator_type,
                status=SimulationStatus.FAILED,
                started_at=datetime.now(UTC),
                error=str(e),
            )
