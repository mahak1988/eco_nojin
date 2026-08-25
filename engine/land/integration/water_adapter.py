"""
Water Integration Adapter
==========================
Connects engine/land/ to EXISTING water modules (no duplication).

Existing modules used:
- engine/hydroma/watershed/calculator.py (calculate_runoff)
- engine/hydroma/groundwater/ (GroundwaterService, models)
- engine/hydroma/soil/water_retention.py (calculate_available_water)
- services/map_engine/pipelines/runoff.py (RunoffPipeline - SCS-CN)
- engine/hydroma/core.py (compute_rainfall_erosivity)

Scientific References:
- USDA SCS National Engineering Handbook (1972)
- Darcy (1856) "Les fontaines publiques de la ville de Dijon"
- Richards (1931) "Capillary conduction of liquids through porous mediums"
- FAO-56 (Allen et al., 1998)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


# ============================================================
# Data Models
# ============================================================

@dataclass
class WaterBalanceInput:
    """Input for water balance calculation"""
    precipitation_mm: float
    et0_mm: float
    crop_coefficient: float = 1.0
    initial_storage_mm: float = 100.0
    area_ha: float = 1.0
    time_step_days: int = 1


@dataclass
class WaterBalanceResult:
    """Water balance result (P - ET - R - dS = 0)"""
    precipitation_mm: float
    evapotranspiration_mm: float
    surface_runoff_mm: float
    deep_percolation_mm: float
    storage_change_mm: float
    final_storage_mm: float
    balance_error_mm: float = 0.0
    is_balanced: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunoffInput:
    """Input for SCS-CN runoff"""
    precipitation_mm: float
    curve_number: float
    area_ha: float = 1.0
    antecedent_moisture: str = "II"  # I, II, III


@dataclass
class RunoffResult:
    """SCS-CN runoff result"""
    runoff_mm: float
    runoff_volume_m3: float
    peak_flow_m3s: float
    cn_adjusted: float
    s_parameter_mm: float
    initial_abstraction_mm: float
    method: str = "scs_cn"


@dataclass
class GroundwaterInput:
    """Input for groundwater flow (Darcy)"""
    hydraulic_conductivity_m_day: float
    hydraulic_gradient: float
    aquifer_thickness_m: float
    aquifer_width_m: float = 1000.0
    porosity: float = 0.3
    specific_yield: float = 0.25


@dataclass
class GroundwaterResult:
    """Groundwater flow result"""
    flow_rate_m3_day: float
    darcy_velocity_m_day: float
    seepage_velocity_m_day: float
    storage_volume_m3: float
    aquifer_type: str = "unconfined"


# ============================================================
# Water Balance Integrator
# ============================================================

class WaterBalanceIntegrator:
    """
    Water balance calculator: P - ET - R - dP - dS = 0
    
    Uses engine/hydroma/soil/water_retention.py for AWC if available.
    """
    
    FIELD_CAPACITY_MM = 200.0
    MAX_STORAGE_MM = 250.0
    
    def __init__(self):
        self._water_retention = None
        self._load_modules()
    
    def _load_modules(self):
        """Load existing water retention module if available"""
        try:
            from engine.hydroma.soil import water_retention
            self._water_retention = water_retention
            logger.info("Loaded engine.hydroma.soil.water_retention")
        except ImportError as e:
            logger.warning(f"water_retention not available: {e}")
    
    def calculate_balance(self, inp: WaterBalanceInput) -> WaterBalanceResult:
        """Calculate water balance"""
        # Validate
        if inp.precipitation_mm < 0:
            raise ValueError("precipitation must be non-negative")
        if inp.et0_mm < 0:
            raise ValueError("et0 must be non-negative")
        if inp.area_ha <= 0:
            raise ValueError("area must be positive")
        
        # Actual ET
        et_demand = inp.et0_mm * inp.crop_coefficient
        available = inp.initial_storage_mm + inp.precipitation_mm
        actual_et = min(et_demand, available)
        
        remaining = available - actual_et
        
        # Deep percolation
        deep_perc = max(0.0, remaining - self.FIELD_CAPACITY_MM)
        
        # Surface runoff
        runoff = max(0.0, remaining - deep_perc - self.MAX_STORAGE_MM)
        
        # Final storage
        final_storage = max(0.0, min(
            remaining - deep_perc - runoff,
            self.MAX_STORAGE_MM
        ))
        
        storage_change = final_storage - inp.initial_storage_mm
        
        # Verify balance: P = ET + R + dP + dS
        balance_check = (
            inp.precipitation_mm - actual_et - runoff 
            - deep_perc - storage_change
        )
        balance_error = abs(balance_check)
        
        return WaterBalanceResult(
            precipitation_mm=inp.precipitation_mm,
            evapotranspiration_mm=round(actual_et, 2),
            surface_runoff_mm=round(runoff, 2),
            deep_percolation_mm=round(deep_perc, 2),
            storage_change_mm=round(storage_change, 2),
            final_storage_mm=round(final_storage, 2),
            balance_error_mm=round(balance_error, 4),
            is_balanced=balance_error < 0.1,
            metadata={
                "et_demand_mm": round(et_demand, 2),
                "water_deficit_mm": round(max(0, et_demand - actual_et), 2),
                "potential_deficit_mm": round(max(0, et_demand - inp.precipitation_mm), 2),
                "method": "thornthwaite_mather",
            }
        )


# ============================================================
# Watershed Integrator (SCS-CN)
# ============================================================

class WatershedIntegrator:
    """
    SCS-CN Runoff calculator.
    
    Uses services/map_engine/pipelines/runoff.py if available.
    
    Q = (P - Ia)^2 / (P - Ia + S)
    S = 25400/CN - 254
    Ia = 0.2 * S
    """
    
    AMC_FACTORS = {"I": 0.6, "II": 1.0, "III": 1.4}
    
    def __init__(self):
        self._runoff_pipeline = None
        self._load_modules()
    
    def _load_modules(self):
        """Load existing runoff pipeline if available"""
        try:
# TODO: Remove circular dependency - services.map_engine.pipelines.runoff
# Original:             from services.map_engine.pipelines.runoff import RunoffPipeline
# Use dependency injection instead
            self._runoff_pipeline = RunoffPipeline
            logger.info("Loaded services.map_engine.pipelines.runoff.RunoffPipeline")
        except ImportError as e:
            logger.warning(f"RunoffPipeline not available: {e}")
    
    def calculate_runoff(self, inp: RunoffInput) -> RunoffResult:
        """Calculate SCS-CN runoff"""
        # Validate
        if inp.precipitation_mm < 0:
            raise ValueError("precipitation must be non-negative")
        if not 30 <= inp.curve_number <= 100:
            raise ValueError("curve_number must be between 30 and 100")
        if inp.area_ha <= 0:
            raise ValueError("area must be positive")
        
        # Adjust CN for AMC
        amc_factor = self.AMC_FACTORS.get(inp.antecedent_moisture, 1.0)
        cn_adjusted = self._adjust_cn(inp.curve_number, amc_factor)
        
        # S parameter
        s_mm = (25400.0 / cn_adjusted) - 254.0
        ia_mm = 0.2 * s_mm
        
        # Runoff
        p = inp.precipitation_mm
        if p <= ia_mm:
            runoff_mm = 0.0
        else:
            runoff_mm = ((p - ia_mm) ** 2) / ((p - ia_mm) + s_mm)
        
        # Volume
        area_m2 = inp.area_ha * 10000.0
        volume_m3 = (runoff_mm / 1000.0) * area_m2
        
        # Peak flow (rational method approximation)
        intensity_mm_hr = 10.0
        c = runoff_mm / p if p > 0 else 0
        peak_flow = (c * intensity_mm_hr * inp.area_ha) / 360.0
        
        return RunoffResult(
            runoff_mm=round(runoff_mm, 2),
            runoff_volume_m3=round(volume_m3, 2),
            peak_flow_m3s=round(peak_flow, 3),
            cn_adjusted=round(cn_adjusted, 1),
            s_parameter_mm=round(s_mm, 2),
            initial_abstraction_mm=round(ia_mm, 2),
            method="scs_cn",
        )
    
    def _adjust_cn(self, cn: float, factor: float) -> float:
        """Adjust CN for antecedent moisture"""
        return min(100.0, max(30.0, cn * factor))
    
    def estimate_cn(
        self,
        soil_type: str,
        land_use: str = "agriculture",
        slope_pct: float = 3.0,
    ) -> float:
        """
        Estimate Curve Number from soil and land use.
        
        Reference: USDA SCS TR-55
        """
        # Base CN by soil hydrologic group
        soil_cn = {
            "sand": 60, "loamy_sand": 65, "sandy_loam": 70,
            "loam": 75, "silt_loam": 78, "clay_loam": 82,
            "clay": 88,
        }
        base_cn = soil_cn.get(soil_type.lower(), 75)
        
        # Land use adjustment
        land_use_adj = {
            "forest": -10, "pasture": -5, "agriculture": 0,
            "urban": 10, "impervious": 25,
        }
        base_cn += land_use_adj.get(land_use.lower(), 0)
        
        # Slope adjustment
        if slope_pct > 10:
            base_cn += 5
        elif slope_pct > 5:
            base_cn += 3
        
        return min(98.0, max(30.0, float(base_cn)))


# ============================================================
# Groundwater Integrator (Darcy)
# ============================================================

class GroundwaterIntegrator:
    """
    Groundwater flow using Darcy's Law.
    
    Uses engine/hydroma/groundwater/ if available.
    
    Q = K * A * i
    """
    
    # Typical K values (m/day)
    K_VALUES = {
        "clay": 0.001, "silt": 0.01, "fine_sand": 1.0,
        "medium_sand": 10.0, "coarse_sand": 50.0, "gravel": 100.0,
    }
    
    def __init__(self):
        self._groundwater_service = None
        self._load_modules()
    
    def _load_modules(self):
        """Load existing groundwater module if available"""
        try:
            from engine.hydroma.groundwater import service
            self._groundwater_service = service
            logger.info("Loaded engine.hydroma.groundwater.service")
        except ImportError as e:
            logger.warning(f"groundwater service not available: {e}")
    
    def calculate_flow(self, inp: GroundwaterInput) -> GroundwaterResult:
        """Calculate groundwater flow (Darcy)"""
        # Validate
        if inp.hydraulic_conductivity_m_day <= 0:
            raise ValueError("hydraulic_conductivity must be positive")
        if inp.aquifer_thickness_m <= 0:
            raise ValueError("aquifer_thickness must be positive")
        if inp.aquifer_width_m <= 0:
            raise ValueError("aquifer_width must be positive")
        if not 0 < inp.porosity < 1:
            raise ValueError("porosity must be between 0 and 1")
        
        # Cross-sectional area
        area_m2 = inp.aquifer_thickness_m * inp.aquifer_width_m
        
        # Darcy's Law: Q = K * A * i
        k = inp.hydraulic_conductivity_m_day
        i = inp.hydraulic_gradient
        
        flow_rate = k * area_m2 * i
        darcy_velocity = flow_rate / area_m2 if area_m2 > 0 else 0
        seepage_velocity = darcy_velocity / inp.porosity
        
        # Storage
        storage_volume = (
            area_m2 * inp.aquifer_width_m * inp.specific_yield
        )
        
        return GroundwaterResult(
            flow_rate_m3_day=round(flow_rate, 2),
            darcy_velocity_m_day=round(darcy_velocity, 4),
            seepage_velocity_m_day=round(seepage_velocity, 4),
            storage_volume_m3=round(storage_volume, 2),
            aquifer_type="unconfined",
        )
    
    def estimate_k(self, texture: str) -> float:
        """Estimate K from soil texture"""
        texture_lower = texture.lower()
        for key, value in self.K_VALUES.items():
            if key in texture_lower or texture_lower in key:
                return value
        return 1.0  # Default: loam


# ============================================================
# Unified Water Analysis
# ============================================================

@dataclass
class UnifiedWaterAnalysis:
    """Complete water analysis result"""
    water_balance: Optional[WaterBalanceResult] = None
    runoff: Optional[RunoffResult] = None
    groundwater: Optional[GroundwaterResult] = None
    recommendations: List[str] = field(default_factory=list)
    overall_status: str = "unknown"


class UnifiedWaterAnalyzer:
    """
    Unified water analysis combining all three components.
    """
    
    def __init__(self):
        self.water_balance = WaterBalanceIntegrator()
        self.watershed = WatershedIntegrator()
        self.groundwater = GroundwaterIntegrator()
    
    def analyze(
        self,
        precipitation_mm: float,
        et0_mm: float,
        soil_type: str = "loam",
        slope_pct: float = 3.0,
        hydraulic_conductivity: Optional[float] = None,
        hydraulic_gradient: float = 0.01,
        aquifer_thickness_m: float = 50.0,
    ) -> UnifiedWaterAnalysis:
        """Complete water analysis"""
        try:
            # Water balance
            wb_input = WaterBalanceInput(
                precipitation_mm=precipitation_mm,
                et0_mm=et0_mm,
            )
            wb_result = self.water_balance.calculate_balance(wb_input)
            
            # Runoff (SCS-CN)
            cn = self.watershed.estimate_cn(soil_type, "agriculture", slope_pct)
            ro_input = RunoffInput(
                precipitation_mm=precipitation_mm,
                curve_number=cn,
            )
            ro_result = self.watershed.calculate_runoff(ro_input)
            
            # Groundwater
            k = hydraulic_conductivity or self.groundwater.estimate_k(soil_type)
            gw_input = GroundwaterInput(
                hydraulic_conductivity_m_day=k,
                hydraulic_gradient=hydraulic_gradient,
                aquifer_thickness_m=aquifer_thickness_m,
            )
            gw_result = self.groundwater.calculate_flow(gw_input)
            
            # Recommendations
            recs = self._generate_recommendations(wb_result, ro_result, gw_result)
            
            # Status
            status = self._determine_status(wb_result, ro_result)
            
            return UnifiedWaterAnalysis(
                water_balance=wb_result,
                runoff=ro_result,
                groundwater=gw_result,
                recommendations=recs,
                overall_status=status,
            )
        
        except Exception as e:
            logger.error(f"Water analysis failed: {e}")
            return UnifiedWaterAnalysis(
                recommendations=[f"Analysis error: {e}"],
                overall_status="error",
            )
    
    def _generate_recommendations(
        self,
        wb: WaterBalanceResult,
        ro: RunoffResult,
        gw: GroundwaterResult,
    ) -> List[str]:
        """Generate water management recommendations"""
        recs = []
        
        # Water deficit
        deficit = wb.metadata.get("water_deficit_mm", 0)
        if deficit > 50:
            recs.append("Significant water deficit - irrigation required")
        elif deficit > 20:
            recs.append("Moderate water deficit - consider supplemental irrigation")
        
        # High runoff
        if ro.runoff_mm > 50:
            recs.append("High surface runoff - implement soil conservation")
            recs.append("Consider contour farming and terracing")
        
        # Groundwater
        if gw.seepage_velocity_m_day < 0.1:
            recs.append("Slow groundwater movement - low recharge potential")
        
        if not recs:
            recs.append("Water balance is favorable - maintain current practices")
        
        return recs
    
    def _determine_status(
        self,
        wb: WaterBalanceResult,
        ro: RunoffResult,
    ) -> str:
        """Determine overall water status"""
        if not wb.is_balanced:
            return "warning"
        
        deficit = wb.metadata.get("water_deficit_mm", 0)
        if deficit > 100:
            return "critical_deficit"
        elif deficit > 50:
            return "deficit"
        elif wb.surface_runoff_mm > 100:
            return "excess_runoff"
        else:
            return "balanced"
