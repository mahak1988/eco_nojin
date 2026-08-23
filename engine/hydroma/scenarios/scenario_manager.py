"""
Scenario Management Engine.

Orchestrates the definition, execution, and storage of various scenarios
(e.g., climate, crop management, infrastructure).
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from database.models import ScenarioDB, ScenarioResultDB, SessionLocal
from engine.hydroma.scenarios.climate_scenarios import generate_climate_scenario
from engine.hydroma.scenarios.crop_scenarios import define_crop_scenario
from engine.hydroma.simulation.orchestrator import run_simulation_chain
from engine.hydroma.economics.integration import calculate_agricultural_project_economics
from engine.hydroma.risk.assessment import perform_comprehensive_risk_analysis # hypothetical

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    CLIMATE_CHANGE = "climate_change"
    CROP_MANAGEMENT = "crop_management"
    INFRASTRUCTURE_DEVELOPMENT = "infrastructure_development"
    BIOFERTILIZER_APPLICATION = "biofertilizer_application"
    COMBINED = "combined"


@dataclass
class ScenarioDefinition:
    """Defines a single scenario."""
    project_id: str
    scenario_name: str
    scenario_type: ScenarioType
    baseline_scenario_id: Optional[str] = None
    description: str = ""
    assumptions: Dict[str, Any] = None
    parameters: Dict[str, Any] = None # e.g., {"temp_change_degC": 2.0, "rainfall_change_percent": -10}


class ScenarioManager:
    """Main class for managing scenarios."""

    def __init__(self):
        self.known_types = {
            ScenarioType.CLIMATE_CHANGE: generate_climate_scenario,
            ScenarioType.CROP_MANAGEMENT: define_crop_scenario,
            # Add more as needed
        }

    def create_scenario(self, definition: ScenarioDefinition) -> str:
        """Creates a new scenario record in the database."""
        logger.info(f"Creating scenario '{definition.scenario_name}' for project {definition.project_id}")
        db_scenario = ScenarioDB(
            project_id=definition.project_id,
            scenario_name=definition.scenario_name,
            scenario_type=definition.scenario_type.value,
            baseline_scenario_id=definition.baseline_scenario_id,
            description=definition.description,
            assumptions=definition.assumptions or {},
            parameters=definition.parameters or {},
            status="created",
            created_by="System",
        )
        db = SessionLocal()
        try:
            db.add(db_scenario)
            db.commit()
            logger.info(f"Scenario '{definition.scenario_name}' created with ID {db_scenario.id}.")
            return str(db_scenario.id)
        except Exception as e:
            logger.error(f"Failed to create scenario: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def run_scenario(self, scenario_id: str, land_profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a scenario by retrieving its definition and running the simulation chain."""
        logger.info(f"Running scenario with ID {scenario_id}")
        db = SessionLocal()
        try:
            scenario = db.query(ScenarioDB).filter(ScenarioDB.id == scenario_id).first()
            if not scenario:
                raise ValueError(f"Scenario with ID {scenario_id} not found.")

            scenario_type = ScenarioType(scenario.scenario_type)
            scenario_params = scenario.parameters

            # --- Apply Scenario Modifications ---
            # This is a critical part where the scenario parameters modify the land profile or inputs
            modified_inputs = self._apply_modifications(land_profile_data, scenario_type, scenario_params)

            # --- Execute Simulation Chain ---
            logger.info("Starting simulation chain for scenario...")
            simulation_outputs = run_simulation_chain(modified_inputs)

            # --- Calculate Economics ---
            logger.info("Calculating economics for scenario...")
            # This requires outputs from sim chain (e.g., yield) and inputs (e.g., costs).
            # For simplicity, we use a placeholder.
            economic_analysis = calculate_agricultural_project_economics(
                land_profile_data=modified_inputs,
                crop_advisor_output={"top_recommendations": [{"name_en": "Wheat", "yield_t_ha": simulation_outputs.get("AquaCropOutput", {}).get("yield_t_ha", 3.0)}]},
                biofertilizer_output={"recommendations": []},
                market_data={"commodity_price_per_ton_irr": 2000000},
                costing_params={"labor_cost_per_hour_irr": 20000, "bio_fert_cost_per_kg_irr": 1000},
                roi_params={"discount_rate": 0.08, "projection_years": 10},
                risk_params={"price_volatility": 0.15, "yield_std_dev": 0.3}
            )

            # --- Perform Risk Analysis ---
            logger.info("Performing risk analysis for scenario...")
            risk_analysis = perform_comprehensive_risk_analysis(simulation_outputs, economic_analysis)

            # --- Store Results ---
            result_data = {
                "simulation_outputs": simulation_outputs,
                "economic_analysis": economic_analysis,
                "risk_analysis": risk_analysis
            }

            db_result = ScenarioResultDB(
                scenario_id=scenario_id,
                result_type="full_analysis", # More granular types possible
                result_data=result_data,
                # Uncertainty could be derived from Monte Carlo or sensitivity analysis
                uncertainty_data={},
                confidence_level=0.9 # Placeholder
            )
            db.add(db_result)
            db.commit()

            logger.info(f"Scenario {scenario_id} run completed and results stored.")
            return result_data

        except Exception as e:
            logger.error(f"Failed during scenario run: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    def _apply_modifications(self, land_profile: Dict[str, Any], scenario_type: ScenarioType, params: Dict[str, Any]) -> Dict[str, Any]:
        """Applies scenario-specific modifications to the base land profile or input data."""
        modified = land_profile.copy()

        if scenario_type == ScenarioType.CLIMATE_CHANGE:
            # Modify climate data within the land profile based on params
            temp_shift = params.get("temp_change_degC", 0.0)
            precip_change = params.get("rainfall_change_percent", 0.0)
            # This is a simplified example. In reality, this might modify a separate climate data object.
            # For now, we'll add them to the modified profile for downstream use.
            modified["scenario_climate_shifts"] = {
                "temp_change_degC": temp_shift,
                "precip_change_percent": precip_change
            }
        elif scenario_type == ScenarioType.CROP_MANAGEMENT:
            # Modify crop choice, irrigation, etc.
            modified["scenario_crop_choice"] = params.get("crop_type", "default")
            modified["scenario_management_practice"] = params.get("practice", "traditional")

        # Add logic for other scenario types (INFRASTRUCTURE_DEVELOPMENT, etc.)

        return modified

    def compare_scenarios(self, scenario_ids: List[str]) -> Dict[str, Any]:
        """Compares results from multiple scenarios."""
        logger.info(f"Comparing scenarios: {scenario_ids}")
        comparisons = {}
        for sid in scenario_ids:
            db = SessionLocal()
            try:
                result = db.query(ScenarioResultDB).filter(ScenarioResultDB.scenario_id == sid).first()
                if result:
                    # Extract key metrics for comparison (e.g., yield, NPV, risk score)
                    sim_out = result.result_data.get("simulation_outputs", {})
                    econ_out = result.result_data.get("economic_analysis", {})
                    risk_out = result.result_data.get("risk_analysis", {})

                    comparisons[sid] = {
                        "yield_t_ha_avg": sim_out.get("AquaCropOutput", {}).get("yield_t_ha", 0),
                        "npv_irr": econ_out.get("roi", {}).get("npv_irr", 0),
                        "projected_risk_score": risk_out.get("overall_risk_score", 1.0),
                        # Add more metrics as needed
                    }
            finally:
                db.close()
        return comparisons