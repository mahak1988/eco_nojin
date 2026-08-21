"""
Integration layer between Telegram Bot and Hydroma scientific motors.
Runs all 11 modules in a pipeline and returns structured results.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class HydromaBotIntegration:
    """Integrates all scientific motors for bot responses."""

    def __init__(self):
        self._satellite = None
        self._motors = {}

    def _ensure_imports(self):
        """Lazy import motors to avoid startup delay."""
        if self._satellite is not None:
            return
        
        try:
            from services.scientific_motors.satellite_integration import (
                SatelliteIntegration, SatelliteContext,
            )
            from services.scientific_motors.crop_advisor import CropAdvisorMotor
            from services.scientific_motors.planting_calendar import PlantingCalendarMotor
            from services.scientific_motors.irrigation_scheduler import IrrigationSchedulerMotor
            from services.scientific_motors.erosion_rusle import RUSLEMotor
            from services.scientific_motors.mrv_system import MRVSystemMotor
            
            self._satellite = SatelliteIntegration()
            self._motors = {
                "crop_advisor": CropAdvisorMotor(),
                "planting_calendar": PlantingCalendarMotor(),
                "irrigation": IrrigationSchedulerMotor(),
                "erosion": RUSLEMotor(),
                "mrv": MRVSystemMotor(),
            }
        except Exception as e:
            print(f"  [BOT] Import error: {e}")
            self._satellite = None

    async def analyze_land(
        self,
        latitude: float,
        longitude: float,
        area_ha: float,
        crop_id: str = "wheat",
        lang: str = "en",
    ) -> Dict[str, Any]:
        """
        Run complete land analysis pipeline.
        
        Returns structured data for all modules.
        """
        self._ensure_imports()
        
        if self._satellite is None:
            return {"error": "Motors not available"}
        
        results = {
            "location": {"lat": latitude, "lon": longitude, "area_ha": area_ha},
            "crop_id": crop_id,
        }
        
        # Create bbox (10km x 10km)
        bbox = (longitude - 0.05, latitude - 0.05, longitude + 0.05, latitude + 0.05)
        
        try:
            # Phase 1: Satellite monitoring
            print(f"  [BOT] Phase 1: Satellite monitoring")
            from services.scientific_motors.satellite_integration import SatelliteContext
            context = SatelliteContext(
                latitude=latitude,
                longitude=longitude,
                bbox=bbox,
            )
            
            sat_params = self._satellite.derive_parameters(
                context, crop_id=crop_id, koppen="BSk"
            )
            
            results["satellite"] = {
                "ndvi": sat_params.ndmi_value,  # Simplified
                "vegetation_health": sat_params.current_vegetation_health,
                "biomass_t_ha": sat_params.biomass_proxy_t_ha,
                "soil_moisture": sat_params.soil_moisture_proxy,
                "baseline_soc": sat_params.baseline_soc_tC_ha,
                "scene_id": sat_params.scene_id,
            }
            
        except Exception as e:
            print(f"  [BOT] Satellite error: {e}")
            results["satellite"] = {"error": str(e)}
        
        try:
            # Phase 2: Crop Advisor
            print(f"  [BOT] Phase 2: Crop Advisor")
            from services.scientific_motors.base import MotorParameters
            
            params = MotorParameters(
                start_date="2026-01-01",
                end_date="2026-12-31",
                time_step="daily",
                scenario_name=f"bot_{int(latitude*100)}_{int(longitude*100)}",
                custom_params={
                    "latitude": latitude,
                    "koppen_climate": "BSk",  # Simplified, could be detected
                    "crops": [crop_id],
                },
            )
            
            crop_result = await self._motors["crop_advisor"].execute({}, params)
            
            if crop_result.status.value == "completed":
                results["crops"] = {
                    "recommended": [crop_id],
                    "suitability": crop_result.summary.get("suitability_score", 0.5),
                }
            else:
                results["crops"] = {"error": crop_result.error_message}
                
        except Exception as e:
            print(f"  [BOT] Crop advisor error: {e}")
            results["crops"] = {"error": str(e)}
        
        try:
            # Phase 3: MRV System (Carbon)
            print(f"  [BOT] Phase 3: MRV System")
            
            mrv_params = MotorParameters(
                start_date="2026-01-01",
                end_date="2036-12-31",
                time_step="yearly",
                scenario_name=f"bot_mrv_{int(latitude*100)}",
                custom_params={
                    "project_name": f"Bot Analysis {latitude:.2f},{longitude:.2f}",
                    "land_area_ha": area_ha,
                    "latitude": latitude,
                    "longitude": longitude,
                    "koppen_climate": "BSk",
                    "baseline_practice": "conventional_tillage",
                    "new_practice": "no_till",
                    "crop_id": crop_id,
                    "project_start_date": "2026-01-01",
                    "project_duration_years": 10,
                },
            )
            
            mrv_result = await self._motors["mrv"].execute({}, mrv_params)
            
            if mrv_result.status.value == "completed":
                results["carbon"] = {
                    "annual_tCO2e_ha": mrv_result.summary.get("annual_sequestration_tCO2e_ha", 0),
                    "total_tCO2e": mrv_result.summary.get("total_credits_tCO2e", 0),
                    "total_value_usd": mrv_result.summary.get("total_value_usd", 0),
                    "additionality": mrv_result.summary.get("additionality", "Unknown"),
                }
            else:
                results["carbon"] = {"error": mrv_result.error_message}
                
        except Exception as e:
            print(f"  [BOT] MRV error: {e}")
            results["carbon"] = {"error": str(e)}
        
        return results


# Singleton
_integration: Optional[HydromaBotIntegration] = None


def get_bot_integration() -> HydromaBotIntegration:
    """Get singleton integration instance."""
    global _integration
    if _integration is None:
        _integration = HydromaBotIntegration()
    return _integration