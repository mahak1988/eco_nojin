"""
Wind & Water Erosion Adapters
- WEPS-style برای فرسایش بادی
- RUSLE برای فرسایش آبی
"""
from datetime import datetime, timezone
from typing import List

from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext, SimulationResult, SimulationStatus, SimulationType,
)

@SimulatorRegistry.register
class WindErosionAdapter(BaseSimulator):
    simulator_type = SimulationType.WIND_EROSION
    name = "WEPS-style"
    version = "1.0.0"
    
    async def validate_context(self, ctx: SimulationContext) -> List[str]:
        return []
    
    async def run(self, ctx: SimulationContext) -> SimulationResult:
        wind_speed = ctx.weather.wind_speed_ms
        K = self._soil_erodibility(ctx.soil.texture)
        threshold = 4.0  # m/s - آستانه فرسایش بادی
        
        # اثر بادشکن
        wb_factor = 1.0
        if ctx.windbreak:
            porosity = ctx.windbreak.porosity_pct / 100
            optimal = 0.4
            efficiency = 1 - abs(porosity - optimal)
            wb_factor = max(0.3, 1 - efficiency * 0.6)
        
        # فرمول WEPS ساده‌شده
        if wind_speed > threshold:
            excess = wind_speed - threshold
            erosion = K * (excess ** 3) * 0.5 * wb_factor
        else:
            erosion = 0.0
        
        risk = "low"
        if erosion >= 5: risk = "moderate"
        if erosion >= 15: risk = "high"
        if erosion >= 30: risk = "severe"
        
        return SimulationResult(
            simulation_id=ctx.simulation_id,
            simulation_type=self.simulator_type,
            status=SimulationStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            summary={
                "wind_speed_ms": wind_speed,
                "soil_erodibility": K,
                "threshold_speed_ms": threshold,
                "erosion_ton_ha_year": round(erosion, 2),
                "windbreak_reduction_factor": round(wb_factor, 3),
                "risk_level": risk,
            },
        )
    
    def _soil_erodibility(self, texture: str) -> float:
        return {
            "sand": 0.45, "loamy_sand": 0.35, "sandy_loam": 0.25,
            "loam": 0.20, "silt_loam": 0.18, "silt": 0.15,
            "clay_loam": 0.12, "clay": 0.08,
        }.get(texture.lower(), 0.20)

@SimulatorRegistry.register
class WaterErosionAdapter(BaseSimulator):
    simulator_type = SimulationType.WATER_EROSION
    name = "RUSLE"
    version = "1.0.0"
    
    async def validate_context(self, ctx: SimulationContext) -> List[str]:
        return []
    
    async def run(self, ctx: SimulationContext) -> SimulationResult:
        R = max(50, ctx.weather.precipitation_mm * 2.5)
        K = self._k_factor(ctx.soil)
        LS = ctx.parameters.get("slope_factor", 1.5)
        C = ctx.parameters.get("cover_factor", 0.3)
        P = ctx.parameters.get("practice_factor", 1.0)
        
        soil_loss = R * K * LS * C * P
        
        return SimulationResult(
            simulation_id=ctx.simulation_id,
            simulation_type=self.simulator_type,
            status=SimulationStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            summary={
                "R_factor": round(R, 2),
                "K_factor": round(K, 3),
                "LS_factor": round(LS, 2),
                "C_factor": C,
                "P_factor": P,
                "soil_loss_ton_ha_year": round(soil_loss, 2),
                "tolerable_loss": 5.0,
                "risk_level": "low" if soil_loss < 5 else "high",
            },
        )
    
    def _k_factor(self, soil) -> float:
        k = {
            "sand": 0.15, "loamy_sand": 0.20, "sandy_loam": 0.25,
            "loam": 0.30, "silt_loam": 0.35, "silt": 0.45,
            "clay_loam": 0.30, "clay": 0.25,
        }.get(soil.texture.lower(), 0.30)
        return max(0.05, k * (1 - soil.organic_carbon_pct * 0.05))
    