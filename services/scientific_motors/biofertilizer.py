"""
Hydroma Nojin - Biofertilizer Recommendation Engine
Recommends optimal biofertilizers based on soil analysis and crop type.
"""
from __future__ import annotations

import numpy as np
import xarray as xr
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .base import (
    AbstractScientificMotor,
    MotorInput,
    MotorOutput,
    MotorParameters,
    MotorResult,
    MotorStatus,
    MotorType,
)


class BiofertilizerType(Enum):
    """Types of biofertilizers."""
    NITROGEN_FIXER = "nitrogen_fixer"
    PHOSPHATE_SOLUBILIZER = "phosphate_solubilizer"
    POTASH_MOBILIZER = "potash_mobilizer"
    MYCORRHIZA = "mycorrhiza"
    PGPR = "pgpr"  # Plant Growth Promoting Rhizobacteria
    BIOCONTROL = "biocontrol"


@dataclass
class BiofertilizerRecommendation:
    """Single biofertilizer recommendation."""
    name: str
    type: BiofertilizerType
    dosage_kg_ha: float
    application_method: str
    timing: str
    expected_benefit: str
    confidence: float


class BiofertilizerMotor(AbstractScientificMotor):
    """
    Biofertilizer Recommendation Motor
    
    Analyzes soil properties and crop requirements to recommend
    optimal biofertilizer combinations for sustainable agriculture.
    """

    @property
    def motor_type(self) -> MotorType:
        return MotorType.BIOFERTILIZER

    @property
    def display_name(self) -> str:
        return "Biofertilizer Recommender"

    def get_input_requirements(self) -> List[MotorInput]:
        return [
            MotorInput("soil_ph", "raster", True, "Soil pH (0-14)"),
            MotorInput("soil_nitrogen", "raster", True, "Soil nitrogen (kg/ha)"),
            MotorInput("soil_phosphorus", "raster", True, "Soil phosphorus (kg/ha)"),
            MotorInput("soil_potassium", "raster", True, "Soil potassium (kg/ha)"),
            MotorInput("soil_organic_matter", "raster", True, "Soil organic matter (%)"),
            MotorInput("soil_texture", "raster", False, "Soil texture class"),
        ]

    def get_outputs(self) -> List[MotorOutput]:
        return [
            MotorOutput("recommendations", "json", "list", "Biofertilizer recommendations"),
            MotorOutput("nitrogen_deficit", "raster", "kg/ha", "Nitrogen deficit map"),
            MotorOutput("phosphorus_deficit", "raster", "kg/ha", "Phosphorus deficit map"),
            MotorOutput("soil_health_score", "raster", "score", "Overall soil health (0-100)"),
        ]

    async def execute(
        self,
        inputs: Dict[str, Any],
        parameters: MotorParameters,
    ) -> MotorResult:
        """Execute biofertilizer recommendation."""
        import time
        start_time = time.time()
        run_id = f"BIOFERT_{parameters.scenario_name}_{int(time.time())}"

        try:
            # Extract inputs
            soil_ph = inputs.get("soil_ph")
            soil_n = inputs.get("soil_nitrogen")
            soil_p = inputs.get("soil_phosphorus")
            soil_k = inputs.get("soil_potassium")
            soil_om = inputs.get("soil_organic_matter")

            if any(v is None for v in [soil_ph, soil_n, soil_p, soil_k, soil_om]):
                return MotorResult(
                    run_id=run_id,
                    motor_type=self.motor_type,
                    status=MotorStatus.FAILED,
                    error_message="Missing required soil inputs",
                )

            # Get crop type from parameters
            crop_type = parameters.custom_params.get("crop_type", "wheat")
            
            # Analyze soil and generate recommendations
            recommendations = self._analyze_soil_and_recommend(
                soil_ph=soil_ph,
                soil_n=soil_n,
                soil_p=soil_p,
                soil_k=soil_k,
                soil_om=soil_om,
                crop_type=crop_type,
            )

            # Calculate nutrient deficits
            n_deficit = self._calculate_nitrogen_deficit(soil_n, soil_om, crop_type)
            p_deficit = self._calculate_phosphorus_deficit(soil_p, soil_ph, crop_type)

            # Calculate soil health score
            health_score = self._calculate_soil_health(
                soil_ph, soil_n, soil_p, soil_k, soil_om
            )

            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.COMPLETED,
                outputs={
                    "recommendations": recommendations,
                    "nitrogen_deficit": n_deficit,
                    "phosphorus_deficit": p_deficit,
                    "soil_health_score": health_score,
                },
                summary={
                    "total_recommendations": len(recommendations),
                    "avg_health_score": float(health_score.mean()),
                    "crop_type": crop_type,
                },
                execution_time_seconds=time.time() - start_time,
            )

        except Exception as e:
            return MotorResult(
                run_id=run_id,
                motor_type=self.motor_type,
                status=MotorStatus.FAILED,
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
            )

    def _analyze_soil_and_recommend(
        self,
        soil_ph: xr.DataArray,
        soil_n: xr.DataArray,
        soil_p: xr.DataArray,
        soil_k: xr.DataArray,
        soil_om: xr.DataArray,
        crop_type: str,
    ) -> List[BiofertilizerRecommendation]:
        """Analyze soil properties and generate recommendations."""
        recommendations = []

        # Calculate mean values for recommendation
        mean_ph = float(soil_ph.mean())
        mean_n = float(soil_n.mean())
        mean_p = float(soil_p.mean())
        mean_k = float(soil_k.mean())
        mean_om = float(soil_om.mean())

        # Crop-specific nutrient requirements (kg/ha)
        crop_requirements = {
            "wheat": {"N": 150, "P": 60, "K": 40},
            "maize": {"N": 180, "P": 70, "K": 50},
            "barley": {"N": 120, "P": 50, "K": 35},
            "cotton": {"N": 200, "P": 80, "K": 60},
            "tomato": {"N": 160, "P": 90, "K": 70},
        }

        requirements = crop_requirements.get(crop_type, crop_requirements["wheat"])

        # 1. Nitrogen fixers (if N is deficient)
        n_deficit = requirements["N"] - mean_n
        if n_deficit > 50:  # Significant deficit
            recommendations.append(BiofertilizerRecommendation(
                name="Rhizobium" if crop_type in ["soybean", "legumes"] else "Azotobacter",
                type=BiofertilizerType.NITROGEN_FIXER,
                dosage_kg_ha=10.0 if n_deficit > 100 else 5.0,
                application_method="Seed treatment or soil application",
                timing="At sowing or early vegetative stage",
                expected_benefit=f"Fix {min(n_deficit, 80)} kg N/ha from atmosphere",
                confidence=min(0.9, n_deficit / 150),
            ))

        # 2. Phosphate solubilizers (if P is low or pH is high)
        p_deficit = requirements["P"] - mean_p
        if p_deficit > 20 or mean_ph > 7.5:
            recommendations.append(BiofertilizerRecommendation(
                name="Pseudomonas fluorescens + Bacillus megaterium",
                type=BiofertilizerType.PHOSPHATE_SOLUBILIZER,
                dosage_kg_ha=8.0,
                application_method="Soil application with FYM",
                timing="Before sowing",
                expected_benefit=f"Solubilize {min(p_deficit, 40)} kg P/ha from soil",
                confidence=0.85 if mean_ph > 7.5 else 0.75,
            ))

        # 3. Potash mobilizers (if K is deficient)
        k_deficit = requirements["K"] - mean_k
        if k_deficit > 15:
            recommendations.append(BiofertilizerRecommendation(
                name="Frateuria aurantia",
                type=BiofertilizerType.POTASH_MOBILIZER,
                dosage_kg_ha=6.0,
                application_method="Soil application",
                timing="At sowing",
                expected_benefit=f"Mobilize {min(k_deficit, 30)} kg K/ha",
                confidence=0.80,
            ))

        # 4. Mycorrhiza (if organic matter is low)
        if mean_om < 1.5:
            recommendations.append(BiofertilizerRecommendation(
                name="Glomus intraradices (AMF)",
                type=BiofertilizerType.MYCORRHIZA,
                dosage_kg_ha=5.0,
                application_method="Root dip or soil application",
                timing="At transplanting or sowing",
                expected_benefit="Improve P uptake by 30-50%, enhance drought tolerance",
                confidence=0.90 if mean_om < 1.0 else 0.75,
            ))

        # 5. PGPR (general plant growth promotion)
        if mean_ph < 6.0 or mean_ph > 8.0:
            recommendations.append(BiofertilizerRecommendation(
                name="Bacillus subtilis + Pseudomonas putida",
                type=BiofertilizerType.PGPR,
                dosage_kg_ha=4.0,
                application_method="Seed treatment",
                timing="Before sowing",
                expected_benefit="Stress tolerance, disease suppression, growth promotion",
                confidence=0.85,
            ))

        # 6. Biocontrol agents (preventive)
        recommendations.append(BiofertilizerRecommendation(
            name="Trichoderma harzianum",
            type=BiofertilizerType.BIOCONTROL,
            dosage_kg_ha=3.0,
            application_method="Soil application or seed treatment",
            timing="Before sowing",
            expected_benefit="Control soil-borne diseases (Fusarium, Pythium)",
            confidence=0.90,
        ))

        return recommendations

    def _calculate_nitrogen_deficit(
        self,
        soil_n: xr.DataArray,
        soil_om: xr.DataArray,
        crop_type: str,
    ) -> xr.DataArray:
        """Calculate nitrogen deficit map."""
        crop_requirements = {
            "wheat": 150, "maize": 180, "barley": 120,
            "cotton": 200, "tomato": 160,
        }
        required_n = crop_requirements.get(crop_type, 150)
        
        # Available N from soil + mineralization from OM
        available_n = soil_n + (soil_om * 20)  # 20 kg N per 1% OM
        
        deficit = np.maximum(required_n - available_n, 0)
        
        return xr.DataArray(
            deficit.values,
            dims=soil_n.dims,
            coords=soil_n.coords,
            attrs={"units": "kg/ha", "description": "Nitrogen deficit"},
        )

    def _calculate_phosphorus_deficit(
        self,
        soil_p: xr.DataArray,
        soil_ph: xr.DataArray,
        crop_type: str,
    ) -> xr.DataArray:
        """Calculate phosphorus deficit map."""
        crop_requirements = {
            "wheat": 60, "maize": 70, "barley": 50,
            "cotton": 80, "tomato": 90,
        }
        required_p = crop_requirements.get(crop_type, 60)
        
        # P availability decreases at high pH
        ph_factor = np.where(soil_ph > 7.5, 0.7, 1.0)
        available_p = soil_p * ph_factor
        
        deficit = np.maximum(required_p - available_p, 0)
        
        return xr.DataArray(
            deficit.values,
            dims=soil_p.dims,
            coords=soil_p.coords,
            attrs={"units": "kg/ha", "description": "Phosphorus deficit"},
        )

    def _calculate_soil_health(
        self,
        soil_ph: xr.DataArray,
        soil_n: xr.DataArray,
        soil_p: xr.DataArray,
        soil_k: xr.DataArray,
        soil_om: xr.DataArray,
    ) -> xr.DataArray:
        """Calculate overall soil health score (0-100)."""
        # pH score (optimal: 6.0-7.5)
        ph_score = np.where(
            (soil_ph >= 6.0) & (soil_ph <= 7.5),
            100,
            100 - np.abs(soil_ph - 6.75) * 15
        )
        ph_score = np.clip(ph_score, 0, 100)

        # Nitrogen score (optimal: >100 kg/ha)
        n_score = np.clip(soil_n / 1.5, 0, 100)

        # Phosphorus score (optimal: >40 kg/ha)
        p_score = np.clip(soil_p / 0.6, 0, 100)

        # Potassium score (optimal: >30 kg/ha)
        k_score = np.clip(soil_k / 0.5, 0, 100)

        # Organic matter score (optimal: >2%)
        om_score = np.clip(soil_om * 40, 0, 100)

        # Weighted average
        health = (
            ph_score * 0.20 +
            n_score * 0.25 +
            p_score * 0.20 +
            k_score * 0.15 +
            om_score * 0.20
        )

        return xr.DataArray(
            health.values,
            dims=soil_ph.dims,
            coords=soil_ph.coords,
            attrs={"units": "score", "description": "Soil health score (0-100)"},
        )