"""
Nojin Calculator - Advanced Biofertilizer Application Optimization
===================================================================
Scientific implementation with advanced features:

1. Multi-strain synergy calculation
2. Seasonal dynamics modeling
3. Soil microbiome interaction
4. Long-term persistence modeling
5. Calibration from field trials
6. Cross-phase integration (Water, MRV)

Based on:
- Bhattacharyya & Jha (2012) - PGPR research
- Glick (2014) - ACC deaminase bacteria
- Soil microbiology principles
- Multi-strain interaction studies
"""

from __future__ import annotations

import logging
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StrainType(str, Enum):
    """Classification of biofertilizer strains."""
    NITROGEN_FIXING = "nitrogen_fixing"
    PHOSPHORUS_SOLUBILIZING = "phosphorus_solubilizing"
    POTASSIUM_SOLUBILIZING = "potassium_solubilizing"
    ACC_DEAMINASE = "acc_deaminase"
    SIDEPHORE_PRODUCING = "siderophore_producing"
    MULTI_TRAIT = "multi_trait"


class FormulationType(str, Enum):
    """Types of biofertilizer formulations."""
    LIQUID = "liquid"
    POWDER = "powder"
    GRANULE = "granule"
    SEED_COATING = "seed_coating"


class ApplicationMethod(str, Enum):
    """Application methods for biofertilizers."""
    SOIL_APPLICATION = "soil_application"
    SEED_TREATMENT = "seed_treatment"
    FOLIAR_SPRAY = "foliar_spray"
    ROOT_DIP = "root_dip"
    DRIP_IRRIGATION = "drip_irrigation"


@dataclass
class SoilCondition:
    """Soil conditions for application planning."""
    ph: float
    organic_carbon_pct: float
    nitrogen_kg_ha: float
    phosphorus_kg_ha: float
    potassium_kg_ha: float
    temperature_c: float
    moisture_pct: float
    texture: str = "loam"
    microbiome_diversity_index: Optional[float] = None  # Shannon diversity


@dataclass
class StrainProfile:
    """Profile of a single bacterial strain."""
    strain_type: StrainType
    efficacy_score: float  # 0-100
    persistence_days: int
    compatibility_score: float = 100.0  # Compatibility with other strains


@dataclass
class NojinInput:
    """Input for Nojin application calculation."""
    land_profile_id: str
    crop_type: str
    soil: SoilCondition
    target_yield_t_ha: float
    application_method: ApplicationMethod = ApplicationMethod.SOIL_APPLICATION
    formulation_type: FormulationType = FormulationType.LIQUID
    strains: Optional[List[StrainProfile]] = None
    season: Optional[str] = None  # "spring", "summer", "fall", "winter"
    irrigation_available: bool = False
    water_stress_index: Optional[float] = None  # From Phase 3 integration


@dataclass
class NojinResult:
    """Result of Nojin application calculation."""
    land_profile_id: str
    
    # Recommended dosage
    recommended_dosage_kg_ha: float
    optimal_application_date_offset_days: int
    reapplication_interval_days: int
    
    # Expected benefits
    expected_yield_increase_pct: float
    expected_nitrogen_fixation_kg_ha: float
    expected_phosphorus_solubilization_pct: float
    expected_potassium_mobility_pct: float
    
    # Multi-strain analysis
    strain_synergy_score: float  # 0-100
    strain_compatibility: str  # "excellent", "good", "moderate", "poor"
    
    # Environmental factors
    soil_compatibility_score: float  # 0-100
    temperature_suitability: str
    moisture_suitability: str
    seasonal_suitability: str
    
    # Long-term effects
    persistence_days: int
    soil_health_improvement_score: float  # 0-100
    
    # Risk assessment
    risk_level: str  # "low", "moderate", "high"
    
    # Status (MUST be before defaults)
    suitability_score: float  # 0-100
    
    # Integration data (defaults)
    water_efficiency_impact: Optional[float] = None  # From Phase 3
    carbon_sequestration_potential: Optional[float] = None  # For Phase 8
    
    # Recommendations (defaults)
    recommendations: List[str] = field(default_factory=list)


class NojinCalculator:
    """
    Advanced Nojin biofertilizer application calculator.
    
    Features:
    - Multi-strain synergy calculation
    - Seasonal dynamics modeling
    - Soil microbiome interaction
    - Long-term persistence modeling
    - Calibration from field trials
    - Cross-phase integration
    
    Example:
        >>> calculator = NojinCalculator()
        >>> soil = SoilCondition(ph=6.8, organic_carbon_pct=1.2, ...)
        >>> strains = [StrainProfile(StrainType.NITROGEN_FIXING, 85, 120)]
        >>> input_data = NojinInput(land_profile_id="test", crop_type="wheat", 
        ...                         soil=soil, strains=strains, ...)
        >>> result = calculator.calculate(input_data)
    """
    
    # Crop-specific factors
    CROP_FACTORS = {
        "wheat": {"n_demand": 120, "p_demand": 60, "k_demand": 40, "factor": 1.0},
        "rice": {"n_demand": 150, "p_demand": 70, "k_demand": 50, "factor": 1.1},
        "corn": {"n_demand": 180, "p_demand": 80, "k_demand": 60, "factor": 1.2},
        "tomato": {"n_demand": 100, "p_demand": 50, "k_demand": 70, "factor": 0.9},
        "potato": {"n_demand": 130, "p_demand": 90, "k_demand": 100, "factor": 1.05},
        "cotton": {"n_demand": 140, "p_demand": 75, "k_demand": 55, "factor": 1.15},
        "soybean": {"n_demand": 60, "p_demand": 50, "k_demand": 45, "factor": 0.85},
    }
    
    # Optimal ranges
    OPTIMAL_PH = (6.0, 7.5)
    OPTIMAL_TEMP_C = (15, 35)
    OPTIMAL_MOISTURE_PCT = (40, 70)
    
    # Seasonal factors
    SEASONAL_FACTORS = {
        "spring": 1.0,
        "summer": 0.9,
        "fall": 1.1,
        "winter": 0.7,
    }
    
    # Strain synergy matrix (simplified)
    STRAIN_SYNERGY = {
        (StrainType.NITROGEN_FIXING, StrainType.PHOSPHORUS_SOLUBILIZING): 1.15,
        (StrainType.NITROGEN_FIXING, StrainType.POTASSIUM_SOLUBILIZING): 1.10,
        (StrainType.PHOSPHORUS_SOLUBILIZING, StrainType.POTASSIUM_SOLUBILIZING): 1.12,
        (StrainType.NITROGEN_FIXING, StrainType.ACC_DEAMINASE): 1.20,
        (StrainType.PHOSPHORUS_SOLUBILIZING, StrainType.SIDEPHORE_PRODUCING): 1.18,
    }
    
    def __init__(self, calibration_data: Optional[Dict] = None):
        """Initialize NojinCalculator with optional calibration data."""
        self.calibration_data = calibration_data or {}
        logger.info("NojinCalculator initialized")
    
    def calculate(self, input_data: NojinInput) -> NojinResult:
        """
        Calculate optimal Nojin application parameters.
        
        Args:
            input_data: NojinInput with soil, crop, and strain information
            
        Returns:
            NojinResult with comprehensive recommendations
        """
        logger.info(f"Calculating Nojin application for {input_data.crop_type}")
        
        # Validate input
        self._validate_input(input_data)
        
        # Multi-strain analysis
        synergy_score, strain_compatibility = self._analyze_multi_strain(input_data.strains)
        
        # Calculate dosage
        dosage = self._calculate_dosage(input_data, synergy_score)
        
        # Calculate timing
        timing_offset = self._calculate_timing(input_data)
        reapplication_interval = self._calculate_reapplication_interval(input_data)
        
        # Calculate expected benefits
        yield_increase = self._predict_yield_increase(input_data, synergy_score)
        n_fixation = self._predict_nitrogen_fixation(input_data, synergy_score)
        p_solubilization = self._predict_phosphorus_solubilization(input_data, synergy_score)
        k_mobility = self._predict_potassium_mobility(input_data, synergy_score)
        
        # Assess environmental factors
        compatibility = self._assess_soil_compatibility(input_data.soil)
        temp_suitability = self._assess_temperature(input_data.soil.temperature_c)
        moisture_suitability = self._assess_moisture(input_data.soil.moisture_pct)
        seasonal_suitability = self._assess_season(input_data.season)
        
        # Long-term effects
        persistence = self._calculate_persistence(input_data)
        soil_health = self._calculate_soil_health_improvement(input_data, synergy_score)
        
        # Risk assessment
        risk = self._assess_risk(compatibility, synergy_score)
        
        # Cross-phase integration
        water_efficiency = self._calculate_water_efficiency_impact(input_data)
        carbon_potential = self._estimate_carbon_sequestration(input_data, soil_health)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            input_data, compatibility, risk, synergy_score, seasonal_suitability
        )
        
        # Overall suitability
        suitability = self._calculate_suitability(compatibility, risk, synergy_score)
        
        return NojinResult(
            land_profile_id=input_data.land_profile_id,
            recommended_dosage_kg_ha=dosage,
            optimal_application_date_offset_days=timing_offset,
            reapplication_interval_days=reapplication_interval,
            expected_yield_increase_pct=yield_increase,
            expected_nitrogen_fixation_kg_ha=n_fixation,
            expected_phosphorus_solubilization_pct=p_solubilization,
            expected_potassium_mobility_pct=k_mobility,
            strain_synergy_score=synergy_score,
            strain_compatibility=strain_compatibility,
            soil_compatibility_score=compatibility,
            temperature_suitability=temp_suitability,
            moisture_suitability=moisture_suitability,
            seasonal_suitability=seasonal_suitability,
            persistence_days=persistence,
            soil_health_improvement_score=soil_health,
            risk_level=risk,
            water_efficiency_impact=water_efficiency,
            carbon_sequestration_potential=carbon_potential,
            recommendations=recommendations,
            suitability_score=suitability,
        )
    
    def _validate_input(self, input_data: NojinInput) -> None:
        """Validate input parameters."""
        if input_data.soil.ph <= 0 or input_data.soil.ph > 14:
            raise ValueError("Soil pH must be between 0 and 14")
        if input_data.soil.moisture_pct < 0 or input_data.soil.moisture_pct > 100:
            raise ValueError("Soil moisture must be 0-100%")
        if input_data.target_yield_t_ha <= 0:
            raise ValueError("Target yield must be positive")
    
    def _analyze_multi_strain(self, strains: Optional[List[StrainProfile]]) -> Tuple[float, str]:
        """
        Analyze multi-strain synergy.
        
        Returns:
            Tuple of (synergy_score, compatibility_rating)
        """
        if not strains or len(strains) == 0:
            return 50.0, "moderate"
        
        if len(strains) == 1:
            return strains[0].efficacy_score, "good"
        
        # Calculate synergy
        synergy_multiplier = 1.0
        for i, strain1 in enumerate(strains):
            for strain2 in strains[i+1:]:
                pair = tuple(sorted([strain1.strain_type, strain2.strain_type]))
                if pair in self.STRAIN_SYNERGY:
                    synergy_multiplier *= self.STRAIN_SYNERGY[pair]
        
        # Calculate average efficacy
        avg_efficacy = np.mean([s.efficacy_score for s in strains])
        synergy_score = avg_efficacy * synergy_multiplier
        
        # Assess compatibility
        avg_compatibility = np.mean([s.compatibility_score for s in strains])
        if avg_compatibility >= 90:
            compatibility = "excellent"
        elif avg_compatibility >= 75:
            compatibility = "good"
        elif avg_compatibility >= 60:
            compatibility = "moderate"
        else:
            compatibility = "poor"
        
        return round(synergy_score, 1), compatibility
    
    def _calculate_dosage(self, input_data: NojinInput, synergy_score: float) -> float:
        """Calculate recommended dosage."""
        crop_info = self.CROP_FACTORS.get(input_data.crop_type.lower(), 
                                          self.CROP_FACTORS["wheat"])
        
        base_rate = 2.0 if input_data.formulation_type == FormulationType.LIQUID else 5.0
        crop_factor = crop_info["factor"]
        
        # Soil modifier
        soil_modifier = 1.0
        if input_data.soil.organic_carbon_pct < 0.5:
            soil_modifier = 1.2
        elif input_data.soil.organic_carbon_pct > 2.0:
            soil_modifier = 0.9
        
        # Synergy modifier (better synergy = less dosage needed)
        synergy_modifier = 1.0 - (synergy_score - 50) / 200
        
        dosage = base_rate * crop_factor * soil_modifier * synergy_modifier
        return round(dosage, 2)
    
    def _calculate_timing(self, input_data: NojinInput) -> int:
        """Calculate optimal application timing."""
        if input_data.application_method == ApplicationMethod.SOIL_APPLICATION:
            return -10
        elif input_data.application_method == ApplicationMethod.SEED_TREATMENT:
            return 0
        elif input_data.application_method == ApplicationMethod.FOLIAR_SPRAY:
            return 21
        else:
            return -7
    
    def _calculate_reapplication_interval(self, input_data: NojinInput) -> int:
        """Calculate reapplication interval based on persistence."""
        if input_data.strains:
            avg_persistence = np.mean([s.persistence_days for s in input_data.strains])
            return int(avg_persistence * 0.8)  # Reapply before full decay
        return 60  # Default 60 days
    
    def _predict_yield_increase(self, input_data: NojinInput, synergy_score: float) -> float:
        """Predict yield increase percentage."""
        base_increase = 15.0
        
        soil_quality = input_data.soil.organic_carbon_pct / 2.0
        soil_quality = min(max(soil_quality, 0.5), 1.5)
        
        ph_factor = 1.0
        if self.OPTIMAL_PH[0] <= input_data.soil.ph <= self.OPTIMAL_PH[1]:
            ph_factor = 1.2
        elif input_data.soil.ph < 5.0 or input_data.soil.ph > 8.5:
            ph_factor = 0.7
        
        # Synergy bonus
        synergy_bonus = (synergy_score - 50) / 50 * 5
        
        increase = base_increase * soil_quality * ph_factor + synergy_bonus
        return round(min(increase, 35.0), 1)
    
    def _predict_nitrogen_fixation(self, input_data: NojinInput, synergy_score: float) -> float:
        """Predict nitrogen fixation contribution."""
        base_fixation = 30.0
        
        n_modifier = 1.0
        if input_data.soil.nitrogen_kg_ha < 50:
            n_modifier = 1.3
        elif input_data.soil.nitrogen_kg_ha > 150:
            n_modifier = 0.8
        
        synergy_bonus = (synergy_score - 50) / 100
        
        fixation = base_fixation * n_modifier * (1 + synergy_bonus)
        return round(fixation, 1)
    
    def _predict_phosphorus_solubilization(self, input_data: NojinInput, synergy_score: float) -> float:
        """Predict phosphorus solubilization percentage."""
        base_solubilization = 25.0
        
        p_modifier = 1.0
        if input_data.soil.phosphorus_kg_ha < 20:
            p_modifier = 1.4
        elif input_data.soil.phosphorus_kg_ha > 60:
            p_modifier = 0.8
        
        synergy_bonus = (synergy_score - 50) / 100
        
        solubilization = base_solubilization * p_modifier * (1 + synergy_bonus)
        return round(min(solubilization, 50.0), 1)
    
    def _predict_potassium_mobility(self, input_data: NojinInput, synergy_score: float) -> float:
        """Predict potassium mobility improvement."""
        base_mobility = 20.0
        
        k_modifier = 1.0
        if input_data.soil.potassium_kg_ha < 30:
            k_modifier = 1.3
        elif input_data.soil.potassium_kg_ha > 80:
            k_modifier = 0.9
        
        synergy_bonus = (synergy_score - 50) / 100
        
        mobility = base_mobility * k_modifier * (1 + synergy_bonus)
        return round(min(mobility, 40.0), 1)
    
    def _assess_soil_compatibility(self, soil: SoilCondition) -> float:
        """Assess soil compatibility with PGPR."""
        score = 100.0
        
        if not (self.OPTIMAL_PH[0] <= soil.ph <= self.OPTIMAL_PH[1]):
            ph_deviation = min(abs(soil.ph - self.OPTIMAL_PH[0]),
                               abs(soil.ph - self.OPTIMAL_PH[1]))
            score -= ph_deviation * 10
        
        if not (self.OPTIMAL_TEMP_C[0] <= soil.temperature_c <= self.OPTIMAL_TEMP_C[1]):
            temp_deviation = min(abs(soil.temperature_c - self.OPTIMAL_TEMP_C[0]),
                                 abs(soil.temperature_c - self.OPTIMAL_TEMP_C[1]))
            score -= temp_deviation * 2
        
        if not (self.OPTIMAL_MOISTURE_PCT[0] <= soil.moisture_pct <= self.OPTIMAL_MOISTURE_PCT[1]):
            moisture_deviation = min(abs(soil.moisture_pct - self.OPTIMAL_MOISTURE_PCT[0]),
                                     abs(soil.moisture_pct - self.OPTIMAL_MOISTURE_PCT[1]))
            score -= moisture_deviation * 0.5
        
        if soil.organic_carbon_pct > 1.5:
            score += 5
        
        # Microbiome diversity bonus
        if soil.microbiome_diversity_index and soil.microbiome_diversity_index > 2.5:
            score += 5
        
        return round(max(0.0, min(100.0, score)), 1)
    
    def _assess_temperature(self, temp_c: float) -> str:
        """Assess temperature suitability."""
        if self.OPTIMAL_TEMP_C[0] <= temp_c <= self.OPTIMAL_TEMP_C[1]:
            return "optimal"
        elif temp_c < self.OPTIMAL_TEMP_C[0] - 5 or temp_c > self.OPTIMAL_TEMP_C[1] + 5:
            return "unsuitable"
        else:
            return "marginal"
    
    def _assess_moisture(self, moisture_pct: float) -> str:
        """Assess moisture suitability."""
        if self.OPTIMAL_MOISTURE_PCT[0] <= moisture_pct <= self.OPTIMAL_MOISTURE_PCT[1]:
            return "optimal"
        elif moisture_pct < 20 or moisture_pct > 85:
            return "unsuitable"
        else:
            return "marginal"
    
    def _assess_season(self, season: Optional[str]) -> str:
        """Assess seasonal suitability."""
        if not season:
            return "unknown"
        
        season_lower = season.lower()
        if season_lower in ["spring", "fall"]:
            return "optimal"
        elif season_lower == "summer":
            return "good"
        elif season_lower == "winter":
            return "marginal"
        else:
            return "unknown"
    
    def _calculate_persistence(self, input_data: NojinInput) -> int:
        """Calculate expected persistence in days."""
        if input_data.strains:
            avg_persistence = np.mean([s.persistence_days for s in input_data.strains])
            
            # Adjust for soil conditions
            if input_data.soil.organic_carbon_pct > 1.5:
                avg_persistence *= 1.2
            
            if input_data.soil.moisture_pct < 30:
                avg_persistence *= 0.8
            
            return int(avg_persistence)
        
        return 90  # Default
    
    def _calculate_soil_health_improvement(self, input_data: NojinInput, synergy_score: float) -> float:
        """Calculate soil health improvement score."""
        base_improvement = 10.0
        
        # Higher synergy = better soil health
        synergy_bonus = (synergy_score - 50) / 10
        
        # Organic carbon potential
        oc_bonus = 0
        if input_data.soil.organic_carbon_pct < 1.0:
            oc_bonus = 5
        
        improvement = base_improvement + synergy_bonus + oc_bonus
        return round(min(improvement, 25.0), 1)
    
    def _assess_risk(self, compatibility: float, synergy_score: float) -> str:
        """Assess application risk level."""
        if compatibility >= 80 and synergy_score >= 70:
            return "low"
        elif compatibility >= 60 and synergy_score >= 50:
            return "moderate"
        else:
            return "high"
    
    def _calculate_water_efficiency_impact(self, input_data: NojinInput) -> Optional[float]:
        """
        Calculate water efficiency impact (Phase 3 integration).
        
        PGPR can improve water use efficiency by 10-20%.
        """
        if input_data.irrigation_available:
            base_improvement = 15.0
            
            # Better soil health = better water retention
            if input_data.soil.organic_carbon_pct > 1.5:
                base_improvement += 5
            
            return round(base_improvement, 1)
        
        return None
    
    def _estimate_carbon_sequestration(self, input_data: NojinInput, soil_health: float) -> Optional[float]:
        """
        Estimate carbon sequestration potential (Phase 8 MRV integration).
        
        PGPR can contribute to soil carbon sequestration.
        """
        base_sequestration = 0.2  # t CO2/ha/year
        
        # Higher soil health = more sequestration
        health_multiplier = soil_health / 10
        
        # Organic carbon potential
        if input_data.soil.organic_carbon_pct < 1.0:
            base_sequestration *= 1.5
        
        sequestration = base_sequestration * health_multiplier
        return round(sequestration, 2)
    
    def _generate_recommendations(
        self,
        input_data: NojinInput,
        compatibility: float,
        risk: str,
        synergy_score: float,
        seasonal_suitability: str,
    ) -> List[str]:
        """Generate comprehensive recommendations."""
        recommendations = []
        
        # Soil condition recommendations
        if compatibility >= 80:
            recommendations.append("Soil conditions are excellent for Nojin application")
        elif compatibility >= 60:
            recommendations.append("Soil conditions are acceptable but could be improved")
        else:
            recommendations.append("Consider soil amendment before application")
        
        # pH recommendations
        if input_data.soil.ph < self.OPTIMAL_PH[0]:
            recommendations.append(f"Apply lime to raise pH from {input_data.soil.ph:.1f} to {self.OPTIMAL_PH[0]}")
        elif input_data.soil.ph > self.OPTIMAL_PH[1]:
            recommendations.append(f"Apply sulfur to lower pH from {input_data.soil.ph:.1f} to {self.OPTIMAL_PH[1]}")
        
        # Organic matter
        if input_data.soil.organic_carbon_pct < 1.0:
            recommendations.append("Add organic matter (compost) to improve microbial habitat")
        
        # Multi-strain recommendations
        if synergy_score >= 80:
            recommendations.append("Excellent strain synergy detected - proceed with confidence")
        elif synergy_score < 50:
            recommendations.append("Consider adjusting strain combination for better synergy")
        
        # Seasonal recommendations
        if seasonal_suitability == "marginal":
            recommendations.append("Consider applying in spring or fall for better results")
        
        # Risk-based recommendations
        if risk == "high":
            recommendations.append("Consider trial application on small area first")
        
        # Irrigation recommendation
        if input_data.irrigation_available:
            recommendations.append("Irrigation available - expect 15% better water use efficiency")
        
        if not recommendations:
            recommendations.append("Proceed with standard application protocol")
        
        return recommendations
    
    def _calculate_suitability(self, compatibility: float, risk: str, synergy_score: float) -> float:
        """Calculate overall suitability score."""
        base = compatibility
        
        if risk == "high":
            base -= 10
        elif risk == "moderate":
            base -= 5
        
        # Synergy bonus
        synergy_bonus = (synergy_score - 50) / 10
        base += synergy_bonus
        
        return round(max(0.0, min(100.0, base)), 1)
    
    def calibrate_from_trials(self, trial_results: List[Dict]) -> Dict:
        """
        Calibrate model parameters from field trial results.
        
        Args:
            trial_results: List of trial result dictionaries
            
        Returns:
            Updated calibration parameters
        """
        if not trial_results:
            return self.calibration_data
        
        # Calculate average yield response
        yield_responses = [t.get("yield_response", 0) for t in trial_results]
        avg_yield_response = np.mean(yield_responses)
        
        # Update calibration
        self.calibration_data["avg_yield_response"] = avg_yield_response
        self.calibration_data["trial_count"] = len(trial_results)
        self.calibration_data["last_calibration"] = datetime.now().isoformat()
        
        logger.info(f"Calibrated with {len(trial_results)} trials, avg yield response: {avg_yield_response:.1f}%")
        
        return self.calibration_data


# Public API
__all__ = [
    "NojinCalculator",
    "NojinInput",
    "NojinResult",
    "SoilCondition",
    "StrainProfile",
    "StrainType",
    "FormulationType",
    "ApplicationMethod",
]