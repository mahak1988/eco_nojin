"""Infiltration Adapter - Water infiltration & soil moisture"""
from typing import List
from services.simulation.base import BaseSimulator, SimulatorRegistry
from services.simulation.schemas import (
    SimulationContext, SimulationResult, SimulationStatus, SimulationType,
)
from datetime import datetime, timezone
import math

@SimulatorRegistry.register
class InfiltrationAdapter(BaseSimulator):
    """نفوذپذیری آب و رطوبت خاک - Green-Ampt Model"""
    simulator_type = SimulationType.INFILTRATION
    name = "Green-Ampt"
    version = "1.0.0"
    
    async def validate_context(self, ctx: SimulationContext) -> List[str]:
        return []
    
    async def run(self, ctx: SimulationContext) -> SimulationResult:
        """Green-Ampt infiltration model"""
        Ks = ctx.soil.infiltration_rate_mm_hr  # hydraulic conductivity
        suction = self._suction_head(ctx.soil.texture)
        porosity = self._porosity(ctx.soil.texture)
        initial_moisture = ctx.parameters.get("initial_moisture_pct", 30.0) / 100
        delta_theta = porosity - initial_moisture
        
        # شبیه‌سازی ۲۴ ساعته
        time_series = []
        cumulative = 0.0
        for hour in range(1, 25):
            rainfall = ctx.weather.precipitation_mm / 24
            # Green-Ampt equation
            if cumulative > 0:
                f = Ks * (1 + (suction * delta_theta) / cumulative)
            else:
                f = Ks
            infiltrated = min(f, rainfall)
            cumulative += infiltrated
            runoff = max(0, rainfall - infiltrated)
            
            time_series.append({
                "hour": hour,
                "infiltration_rate_mm_hr": round(f, 2),
                "cumulative_mm": round(cumulative, 2),
                "runoff_mm": round(runoff, 2),
            })
        
        return SimulationResult(
            simulation_id=ctx.simulation_id,
            simulation_type=self.simulator_type,
            status=SimulationStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            summary={
                "hydraulic_conductivity_mm_hr": Ks,
                "suction_head_mm": suction,
                "porosity": porosity,
                "total_infiltration_mm": round(cumulative, 2),
                "total_runoff_mm": round(ctx.weather.precipitation_mm - cumulative, 2),
                "infiltration_efficiency_pct": round(
                    (cumulative / ctx.weather.precipitation_mm * 100) if ctx.weather.precipitation_mm > 0 else 100,
                    1
                ),
            },
            time_series=time_series,
        )
    
    def _suction_head(self, texture: str) -> float:
        """Suction head (mm) by soil texture"""
        return {
            "sand": 50, "loamy_sand": 80, "sandy_loam": 120,
            "loam": 200, "silt_loam": 280, "silt": 350,
            "clay_loam": 300, "clay": 450,
        }.get(texture.lower(), 200)
    
    def _porosity(self, texture: str) -> float:
        """Porosity by soil texture"""
        return {
            "sand": 0.40, "loamy_sand": 0.42, "sandy_loam": 0.44,
            "loam": 0.46, "silt_loam": 0.48, "silt": 0.50,
            "clay_loam": 0.48, "clay": 0.52,
        }.get(texture.lower(), 0.46)
    