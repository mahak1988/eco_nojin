"""
Nojin Biofertilizer - Service Layer
====================================
Business logic with cross-phase integration.

Integrates with:
- Phase 3 (Water): Water efficiency impact
- Phase 8 (MRV): Carbon sequestration tracking
- CropAdvisor: Crop-specific recommendations
"""

from __future__ import annotations

import logging
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from database import SessionLocal

from .calculator import (
    NojinCalculator,
    NojinInput,
    NojinResult,
    SoilCondition,
    StrainProfile,
    StrainType,
    FormulationType,
    ApplicationMethod,
)
from .repositories import (
    NojinStrainRepository,
    NojinFormulationRepository,
    NojinApplicationPlanRepository,
    NojinFieldTrialRepository,
    NojinCalibrationRecordRepository,
)
from .models import (
    NojinStrain,
    NojinFormulation,
    NojinApplicationPlan,
    NojinFieldTrial,
    NojinCalibrationRecord,
)

logger = logging.getLogger(__name__)


class NojinService:
    """
    Main service for Nojin biofertilizer operations.
    
    Coordinates:
    - Calculator (scientific computations)
    - Repositories (data access)
    - External services (Phase 3, Phase 8, CropAdvisor)
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None
        
        # Initialize calculator with latest calibration
        self.calculator = NojinCalculator()
        
        # Initialize repositories
        self.strains = NojinStrainRepository(self.session)
        self.formulations = NojinFormulationRepository(self.session)
        self.application_plans = NojinApplicationPlanRepository(self.session)
        self.field_trials = NojinFieldTrialRepository(self.session)
        self.calibration_records = NojinCalibrationRecordRepository(self.session)
        
        logger.info("NojinService initialized")
    
    def close(self):
        if self._owns_session:
            self.session.close()
            self.strains.close()
            self.formulations.close()
            self.application_plans.close()
            self.field_trials.close()
            self.calibration_records.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ═══════════════════════════════════════════════════════════════
    # CORE OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def get_recommendation(
        self,
        land_profile_id: str,
        crop_type: str,
        soil: SoilCondition,
        target_yield_t_ha: float,
        formulation_code: Optional[str] = None,
        application_method: ApplicationMethod = ApplicationMethod.SOIL_APPLICATION,
        season: Optional[str] = None,
        irrigation_available: bool = False,
    ) -> NojinResult:
        """
        Get comprehensive Nojin application recommendation.
        
        Args:
            land_profile_id: Land profile identifier
            crop_type: Crop type (wheat, rice, corn, etc.)
            soil: Soil conditions
            target_yield_t_ha: Target yield in tons/hectare
            formulation_code: Optional formulation code (uses best match if None)
            application_method: Application method
            season: Season (spring, summer, fall, winter)
            irrigation_available: Whether irrigation is available
        
        Returns:
            NojinResult with comprehensive recommendation
        """
        logger.info(f"Getting recommendation for {crop_type} on {land_profile_id}")
        
        # Find appropriate formulation
        formulation = None
        if formulation_code:
            formulation = self.formulations.get_by_code(formulation_code)
            if not formulation:
                logger.warning(f"Formulation {formulation_code} not found")
        else:
            # Auto-select best formulation for crop
            suitable = self.formulations.get_for_crop(crop_type)
            if suitable:
                formulation = suitable[0]
        
        # Build strain profiles from formulation
        strain_profiles = None
        if formulation:
            strain_profiles = self._build_strain_profiles_from_formulation(formulation)
        
        # Build input
        input_data = NojinInput(
            land_profile_id=land_profile_id,
            crop_type=crop_type,
            soil=soil,
            target_yield_t_ha=target_yield_t_ha,
            application_method=application_method,
            formulation_type=FormulationType(formulation.formulation_type) if formulation else FormulationType.LIQUID,
            strains=strain_profiles,
            season=season,
            irrigation_available=irrigation_available,
        )
        
        # Calculate
        result = self.calculator.calculate(input_data)
        
        logger.info(f"Recommendation generated: dosage={result.recommended_dosage_kg_ha} kg/ha, "
                   f"suitability={result.suitability_score}")
        
        return result
    
    def create_application_plan(
        self,
        formulation_id: int,
        land_profile_id: Optional[int],
        crop_type: str,
        application_date: date,
        application_method: str,
        dosage_kg_ha: float,
        expected_yield_response: Optional[float] = None,
        expected_soil_improvement: Optional[str] = None,
        risk_assessment: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> NojinApplicationPlan:
        """Create a new application plan."""
        plan = self.application_plans.create(
            formulation_id=formulation_id,
            land_profile_id=land_profile_id,
            crop_type=crop_type,
            application_date=application_date,
            application_method=application_method,
            dosage_kg_ha=dosage_kg_ha,
            expected_yield_response=expected_yield_response,
            expected_soil_improvement=expected_soil_improvement,
            risk_assessment=risk_assessment,
            created_by=created_by,
        )
        logger.info(f"Created application plan {plan.id} for {crop_type}")
        return plan
    
    def record_field_trial(
        self,
        application_plan_id: Optional[int],
        trial_location: str,
        trial_date: date,
        crop_type: str,
        plot_area_ha: Optional[float] = None,
        treatment_design: Optional[str] = None,
        baseline_data: Optional[str] = None,
        post_application_data: Optional[str] = None,
        yield_response: Optional[float] = None,
        soil_improvement: Optional[str] = None,
        observations: Optional[str] = None,
        statistical_analysis: Optional[str] = None,
    ) -> NojinFieldTrial:
        """Record a field trial result."""
        trial = self.field_trials.create(
            application_plan_id=application_plan_id,
            trial_location=trial_location,
            trial_date=trial_date,
            crop_type=crop_type,
            plot_area_ha=plot_area_ha,
            treatment_design=treatment_design,
            baseline_data=baseline_data,
            post_application_data=post_application_data,
            yield_response=yield_response,
            soil_improvement=soil_improvement,
            observations=observations,
            statistical_analysis=statistical_analysis,
        )
        logger.info(f"Recorded field trial {trial.id} at {trial_location}")
        return trial
    
    # ═══════════════════════════════════════════════════════════════
    # CALIBRATION
    # ═══════════════════════════════════════════════════════════════
    
    def calibrate_from_trials(
        self,
        formulation_id: int,
        model_version: str = "1.0",
        calibrated_by: Optional[str] = None,
    ) -> NojinCalibrationRecord:
        """
        Calibrate model for a formulation based on field trials.
        
        Args:
            formulation_id: Formulation ID
            model_version: Model version string
            calibrated_by: Calibrator name
        
        Returns:
            Created calibration record
        """
        logger.info(f"Calibrating formulation {formulation_id}")
        
        # Get all trials for this formulation
        trials = self.field_trials.get_for_formulation(formulation_id)
        
        if not trials:
            raise ValueError(f"No field trials found for formulation {formulation_id}")
        
        # Prepare trial data for calculator
        trial_results = []
        for trial in trials:
            if trial.yield_response is not None:
                trial_results.append({
                    "trial_id": trial.id,
                    "yield_response": trial.yield_response,
                    "crop_type": trial.crop_type,
                    "plot_area_ha": trial.plot_area_ha,
                    "trial_date": trial.trial_date.isoformat() if trial.trial_date else None,
                })
        
        if not trial_results:
            raise ValueError(f"No trials with yield_response for formulation {formulation_id}")
        
        # Calibrate calculator
        calibration_data = self.calculator.calibrate_from_trials(trial_results)
        
        # Calculate quality score based on trial count and variance
        yield_responses = [t["yield_response"] for t in trial_results]
        import numpy as np
        variance = np.var(yield_responses)
        quality_score = max(0, 100 - variance)  # Lower variance = higher quality
        quality_score = min(100, quality_score + len(trial_results) * 5)  # Bonus for more trials
        
        # Create record
        record = self.calibration_records.create(
            formulation_id=formulation_id,
            calibration_date=date.today(),
            calibration_data=json.dumps(calibration_data),
            model_version=model_version,
            parameters_updated=json.dumps({"trial_count": len(trial_results)}),
            validation_results=json.dumps({
                "avg_yield_response": float(np.mean(yield_responses)),
                "std_yield_response": float(np.std(yield_responses)),
                "trial_count": len(trial_results),
            }),
            calibration_quality_score=quality_score,
            calibrated_by=calibrated_by,
        )
        
        logger.info(f"Calibrated formulation {formulation_id} with {len(trial_results)} trials, "
                   f"quality={quality_score:.1f}")
        
        return record
    
    # ═══════════════════════════════════════════════════════════════
    # CROSS-PHASE INTEGRATION
    # ═══════════════════════════════════════════════════════════════
    
    def get_water_efficiency_impact(
        self,
        land_profile_id: str,
        formulation_id: int,
        soil: SoilCondition,
    ) -> Optional[Dict[str, Any]]:
        """
        Integration with Phase 3 (Water Intelligence).
        
        Calculates water efficiency improvement from Nojin application.
        """
        logger.info(f"Calculating water efficiency impact for {land_profile_id}")
        
        try:
            # Get formulation
            formulation = self.formulations.get_by_id(formulation_id)
            if not formulation:
                return None
            
            # Use calculator to estimate
            input_data = NojinInput(
                land_profile_id=land_profile_id,
                crop_type="generic",
                soil=soil,
                target_yield_t_ha=5.0,
                irrigation_available=True,  # Assume irrigation for water impact
            )
            
            result = self.calculator.calculate(input_data)
            
            return {
                "land_profile_id": land_profile_id,
                "formulation_id": formulation_id,
                "water_efficiency_improvement_pct": result.water_efficiency_impact,
                "soil_moisture_retention_improvement": "10-20%",
                "irrigation_reduction_potential": "15%",
                "notes": "PGPR improves root development and soil structure, "
                        "leading to better water retention and use efficiency.",
                "calculated_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Water efficiency calculation failed: {e}")
            return None
    
    def get_carbon_sequestration_potential(
        self,
        land_profile_id: str,
        formulation_id: int,
        soil: SoilCondition,
        area_ha: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
        """
        Integration with Phase 8 (MRV - Monitoring, Reporting, Verification).
        
        Estimates carbon sequestration potential from Nojin application.
        """
        logger.info(f"Estimating carbon sequestration for {land_profile_id}")
        
        try:
            # Use calculator to estimate
            input_data = NojinInput(
                land_profile_id=land_profile_id,
                crop_type="generic",
                soil=soil,
                target_yield_t_ha=5.0,
            )
            
            result = self.calculator.calculate(input_data)
            
            annual_sequestration = (result.carbon_sequestration_potential or 0) * area_ha
            ten_year_sequestration = annual_sequestration * 10
            
            return {
                "land_profile_id": land_profile_id,
                "formulation_id": formulation_id,
                "area_ha": area_ha,
                "annual_sequestration_t_co2": annual_sequestration,
                "ten_year_sequestration_t_co2": ten_year_sequestration,
                "soil_health_improvement": result.soil_health_improvement_score,
                "verification_method": "Soil sampling + remote sensing (Sentinel-2)",
                "mrv_standard": "Verra VCS / Gold Standard",
                "calculated_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Carbon sequestration calculation failed: {e}")
            return None
    
    def integrate_with_crop_advisor(
        self,
        land_profile_id: str,
        crop_type: str,
        soil: SoilCondition,
    ) -> Dict[str, Any]:
        """
        Integration with CropAdvisor for combined recommendations.
        
        Returns combined fertilizer + biofertilizer recommendation.
        """
        logger.info(f"Integrating with CropAdvisor for {crop_type}")
        
        # Get Nojin recommendation
        nojin_rec = self.get_recommendation(
            land_profile_id=land_profile_id,
            crop_type=crop_type,
            soil=soil,
            target_yield_t_ha=5.0,
        )
        
        # Calculate fertilizer reduction due to Nojin
        # N fixation reduces N fertilizer need
        n_reduction_kg_ha = nojin_rec.expected_nitrogen_fixation_kg_ha
        
        # P solubilization reduces P fertilizer need
        p_reduction_kg_ha = 20.0  # Typical reduction
        
        return {
            "land_profile_id": land_profile_id,
            "crop_type": crop_type,
            "nojin_recommendation": {
                "dosage_kg_ha": nojin_rec.recommended_dosage_kg_ha,
                "application_method": nojin_rec.recommendations[0] if nojin_rec.recommendations else "standard",
                "suitability_score": nojin_rec.suitability_score,
            },
            "fertilizer_adjustments": {
                "nitrogen_reduction_kg_ha": n_reduction_kg_ha,
                "phosphorus_reduction_kg_ha": p_reduction_kg_ha,
                "estimated_cost_saving_usd_ha": round((n_reduction_kg_ha + p_reduction_kg_ha) * 1.5, 2),
            },
            "integrated_benefits": {
                "yield_increase_pct": nojin_rec.expected_yield_increase_pct,
                "soil_health_improvement": nojin_rec.soil_health_improvement_score,
                "water_efficiency_improvement_pct": nojin_rec.water_efficiency_impact,
            },
            "calculated_at": datetime.now().isoformat(),
        }
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _build_strain_profiles_from_formulation(
        self,
        formulation: NojinFormulation,
    ) -> Optional[List[StrainProfile]]:
        """Build StrainProfile list from formulation."""
        if not formulation:
            return None
        
        # For now, use default profiles based on formulation type
        # In production, this would query actual strains linked to formulation
        default_profiles = [
            StrainProfile(
                strain_type=StrainType.NITROGEN_FIXING,
                efficacy_score=85.0,
                persistence_days=120,
                compatibility_score=90.0,
            ),
            StrainProfile(
                strain_type=StrainType.PHOSPHORUS_SOLUBILIZING,
                efficacy_score=80.0,
                persistence_days=100,
                compatibility_score=85.0,
            ),
        ]
        
        return default_profiles
    
    # ═══════════════════════════════════════════════════════════════
    # STATISTICS & REPORTING
    # ═══════════════════════════════════════════════════════════════
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall Nojin system statistics."""
        return {
            "strains_count": self.strains.count(),
            "formulations_count": self.formulations.count(),
            "application_plans_count": len(self.application_plans.get_all(limit=10000)),
            "field_trials_count": len(self.field_trials.get_all(limit=10000)),
            "calibration_records_count": len(self.calibration_records.get_all(limit=10000)),
            "generated_at": datetime.now().isoformat(),
        }


__all__ = ["NojinService"]
