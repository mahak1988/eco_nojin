"""
Groundwater Service - Phase 3 Water Intelligence
==================================================
Implements Darcy's Law, sustainability metrics, and aquifer analysis.

Scientific Basis:
- Darcy's Law: Q = -K * A * (dh/dl)
- Sustainability Index: Recharge / Abstraction
- Water Balance: ΔS = Recharge - Discharge - Abstraction

References:
- Freeze & Cherry (1979) - Groundwater
- Todd & Mays (2005) - Groundwater Hydrology
"""

from __future__ import annotations

import logging
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class AquiferType(str, Enum):
    """Classification of aquifer types."""
    UNCONFINED = "unconfined"
    CONFINED = "confined"
    SEMI_CONFINED = "semi_confined"
    FRACTURED = "fractured"


class WaterQualityClass(str, Enum):
    """Water quality classification based on TDS."""
    EXCELLENT = "excellent"      # < 300 mg/L
    GOOD = "good"                # 300-600 mg/L
    FAIR = "fair"                # 600-900 mg/L
    POOR = "poor"                # 900-1200 mg/L
    UNACCEPTABLE = "unacceptable"  # > 1200 mg/L


@dataclass
class GroundwaterInput:
    """Input data for groundwater analysis."""
    land_profile_id: str
    well_depth_m: float
    water_table_depth_m: float
    hydraulic_conductivity_m_s: float  # K
    aquifer_thickness_m: float
    aquifer_type: AquiferType = AquiferType.UNCONFINED
    recharge_rate_mm_yr: float = 0.0
    abstraction_rate_m3_yr: float = 0.0
    tds_mg_l: float = 0.0  # Total dissolved solids
    porosity: float = 0.3
    specific_yield: float = 0.15


@dataclass
class GroundwaterResult:
    """Result of groundwater analysis."""
    land_profile_id: str
    
    # Flow calculations
    darcy_flux_m_s: float
    transmissivity_m2_s: float
    specific_capacity_m2_s: float
    
    # Sustainability metrics
    sustainability_index: float  # 0-1, >1 = sustainable
    safe_yield_m3_yr: float
    reserve_m3: float
    
    # Quality
    water_quality_class: WaterQualityClass
    
    # Risk assessment
    overexploitation_risk: str  # "low", "moderate", "high", "critical"
    contamination_risk: str
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    status: str  # "healthy", "stressed", "depleted"


class GroundwaterService:
    """
    Groundwater analysis service implementing Darcy's Law and sustainability metrics.
    
    Example:
        >>> service = GroundwaterService()
        >>> input_data = GroundwaterInput(
        ...     land_profile_id="test-001",
        ...     well_depth_m=50.0,
        ...     water_table_depth_m=10.0,
        ...     hydraulic_conductivity_m_s=1e-4,
        ...     aquifer_thickness_m=40.0,
        ... )
        >>> result = service.analyze(input_data)
    """
    
    def __init__(self):
        """Initialize GroundwaterService."""
        logger.info("GroundwaterService initialized")
    
    def analyze(self, input_data: GroundwaterInput) -> GroundwaterResult:
        """
        Perform complete groundwater analysis.
        
        Args:
            input_data: GroundwaterInput with all required parameters
            
        Returns:
            GroundwaterResult with flow, sustainability, and quality metrics
        """
        logger.info(f"Analyzing groundwater for profile {input_data.land_profile_id}")
        
        # Validate input
        self._validate_input(input_data)
        
        # Calculate Darcy flux: Q/A = -K * dh/dl
        darcy_flux = self._calculate_darcy_flux(input_data)
        
        # Calculate transmissivity: T = K * b
        transmissivity = input_data.hydraulic_conductivity_m_s * input_data.aquifer_thickness_m
        
        # Calculate specific capacity
        specific_capacity = transmissivity / input_data.well_depth_m
        
        # Calculate safe yield
        safe_yield = self._calculate_safe_yield(input_data)
        
        # Calculate sustainability index
        sustainability_index = self._calculate_sustainability(input_data, safe_yield)
        
        # Calculate reserve
        reserve = self._calculate_reserve(input_data)
        
        # Classify water quality
        water_quality = self._classify_water_quality(input_data.tds_mg_l)
        
        # Assess risks
        overexploitation_risk = self._assess_overexploitation(sustainability_index)
        contamination_risk = self._assess_contamination(input_data)
        
        # Determine status
        status = self._determine_status(sustainability_index, water_quality)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            sustainability_index, overexploitation_risk, water_quality
        )
        
        return GroundwaterResult(
            land_profile_id=input_data.land_profile_id,
            darcy_flux_m_s=darcy_flux,
            transmissivity_m2_s=transmissivity,
            specific_capacity_m2_s=specific_capacity,
            sustainability_index=sustainability_index,
            safe_yield_m3_yr=safe_yield,
            reserve_m3=reserve,
            water_quality_class=water_quality,
            overexploitation_risk=overexploitation_risk,
            contamination_risk=contamination_risk,
            recommendations=recommendations,
            status=status,
        )
    
    def _validate_input(self, input_data: GroundwaterInput) -> None:
        """Validate input parameters."""
        if input_data.hydraulic_conductivity_m_s <= 0:
            raise ValueError("Hydraulic conductivity must be positive")
        if input_data.aquifer_thickness_m <= 0:
            raise ValueError("Aquifer thickness must be positive")
        if input_data.well_depth_m <= 0:
            raise ValueError("Well depth must be positive")
        if input_data.water_table_depth_m < 0:
            raise ValueError("Water table depth cannot be negative")
    
    def _calculate_darcy_flux(self, input_data: GroundwaterInput) -> float:
        """
        Calculate Darcy flux using Darcy's Law.
        
        Q/A = -K * dh/dl
        
        For simplicity, assume hydraulic gradient = water_table_depth / well_depth
        """
        hydraulic_gradient = input_data.water_table_depth_m / input_data.well_depth_m
        darcy_flux = input_data.hydraulic_conductivity_m_s * hydraulic_gradient
        return float(darcy_flux)
    
    def _calculate_safe_yield(self, input_data: GroundwaterInput) -> float:
        """
        Calculate safe yield (80% of recharge to maintain sustainability).
        
        Safe Yield = 0.8 * Recharge * Area
        
        Assume 1 hectare = 10,000 m² for calculation
        """
        recharge_m_yr = input_data.recharge_rate_mm_yr / 1000.0
        area_m2 = 10000.0  # 1 hectare
        safe_yield = 0.8 * recharge_m_yr * area_m2
        return float(safe_yield)
    
    def _calculate_sustainability(self, input_data: GroundwaterInput, safe_yield: float) -> float:
        """
        Calculate sustainability index.
        
        Sustainability Index = Safe Yield / Abstraction
        - > 1.0: Sustainable
        - 0.7-1.0: Marginal
        - < 0.7: Unsustainable
        """
        if input_data.abstraction_rate_m3_yr <= 0:
            return 1.0  # No abstraction = fully sustainable
        
        return safe_yield / input_data.abstraction_rate_m3_yr
    
    def _calculate_reserve(self, input_data: GroundwaterInput) -> float:
        """
        Calculate groundwater reserve volume.
        
        Reserve = Aquifer Volume * Porosity * Specific Yield
        """
        aquifer_volume = input_data.aquifer_thickness_m * 10000.0  # 1 hectare
        reserve = aquifer_volume * input_data.porosity * input_data.specific_yield
        return float(reserve)
    
    def _classify_water_quality(self, tds_mg_l: float) -> WaterQualityClass:
        """Classify water quality based on TDS."""
        if tds_mg_l < 300:
            return WaterQualityClass.EXCELLENT
        elif tds_mg_l < 600:
            return WaterQualityClass.GOOD
        elif tds_mg_l < 900:
            return WaterQualityClass.FAIR
        elif tds_mg_l < 1200:
            return WaterQualityClass.POOR
        else:
            return WaterQualityClass.UNACCEPTABLE
    
    def _assess_overexploitation(self, sustainability_index: float) -> str:
        """Assess overexploitation risk based on sustainability index."""
        if sustainability_index > 1.0:
            return "low"
        elif sustainability_index > 0.7:
            return "moderate"
        elif sustainability_index > 0.4:
            return "high"
        else:
            return "critical"
    
    def _assess_contamination(self, input_data: GroundwaterInput) -> str:
        """Assess contamination risk based on water quality."""
        if input_data.tds_mg_l < 600:
            return "low"
        elif input_data.tds_mg_l < 1200:
            return "moderate"
        else:
            return "high"
    
    def _determine_status(self, sustainability_index: float, water_quality: WaterQualityClass) -> str:
        """Determine overall aquifer status."""
        if sustainability_index > 1.0 and water_quality in [WaterQualityClass.EXCELLENT, WaterQualityClass.GOOD]:
            return "healthy"
        elif sustainability_index > 0.7 or water_quality in [WaterQualityClass.EXCELLENT, WaterQualityClass.GOOD, WaterQualityClass.FAIR]:
            return "stressed"
        else:
            return "depleted"
    
    def _generate_recommendations(
        self,
        sustainability_index: float,
        overexploitation_risk: str,
        water_quality: WaterQualityClass,
    ) -> List[str]:
        """Generate management recommendations."""
        recommendations = []
        
        if overexploitation_risk == "critical":
            recommendations.append("URGENT: Reduce abstraction by at least 50%")
            recommendations.append("Implement artificial recharge programs")
        elif overexploitation_risk == "high":
            recommendations.append("Reduce abstraction by 30%")
            recommendations.append("Monitor water levels monthly")
        elif overexploitation_risk == "moderate":
            recommendations.append("Maintain current abstraction levels")
            recommendations.append("Monitor water levels quarterly")
        
        if water_quality in [WaterQualityClass.POOR, WaterQualityClass.UNACCEPTABLE]:
            recommendations.append("Install water treatment system")
            recommendations.append("Investigate contamination sources")
        
        if sustainability_index > 1.2:
            recommendations.append("Aquifer has capacity for increased abstraction")
            recommendations.append("Consider managed aquifer recharge (MAR)")
        
        if not recommendations:
            recommendations.append("Continue current management practices")
            recommendations.append("Monitor annually")
        
        return recommendations


# Public API
__all__ = [
    "GroundwaterService",
    "GroundwaterInput",
    "GroundwaterResult",
    "AquiferType",
    "WaterQualityClass",
]
