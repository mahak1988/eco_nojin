"""
Decision Support System (DSS) Engine.

Synthesizes results from scenarios, optimization, and risk analysis
to provide actionable recommendations.
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import uuid

from database.models import DecisionRecommendationDB
from database.config import SessionLocal
from engine.hydroma.optimization.optimizer import run_land_use_optimization # hypothetical call
from engine.hydroma.risk.assessment import perform_comprehensive_risk_analysis # hypothetical
from engine.hydroma.economics.integration import calculate_agricultural_project_economics # hypothetical

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    CROP_SELECTION = "crop_selection"
    INPUT_OPTIMIZATION = "input_optimization"
    INFRASTRUCTURE_INVESTMENT = "infrastructure_investment"
    RISK_MITIGATION = "risk_mitigation"
    ADAPTATION_STRATEGY = "adaptation_strategy"


@dataclass
class Recommendation:
    """Object representing a single recommendation."""
    project_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    data: Dict[str, Any]
    confidence_level: float
    risk_level: str  # "low", "medium", "high"
    economic_impact: Dict[str, float]  # e.g., {"NPV_irr": 5000000, "IRR_fraction": 0.12}
    environmental_impact: Dict[str, float] # e.g., {"co2_reduction_tonnes": 100, "water_saved_m3": 5000}
    social_impact: Dict[str, float]       # e.g., {"jobs_created": 2.5, "income_increase_fraction": 0.15}
    implementation_timeline: Dict[str, str] # e.g., {"start_date": "2024-06-01", "end_date": "2024-10-30"}
    monitoring_plan: Dict[str, Any]       # e.g., {"checkpoints": [...], "kpis": [...]}


class DecisionSupportSystem:
    """Main DSS class."""

    def __init__(self):
        pass

    def generate_recommendations(self, project_id: str, scenario_comparison: Dict[str, Any], optimization_results: List[Dict[str, Any]]) -> List[Recommendation]:
        """
        Generates recommendations based on scenario comparison and optimization results.

        Args:
            project_id: ID of the project.
            scenario_comparison: Output from ScenarioManager.compare_scenarios.
            optimization_results: List of results from the optimizer.

        Returns:
            List of Recommendation objects.
        """
        logger.info(f"Generating recommendations for project {project_id}")

        recommendations = []

        # Example Logic:
        # 1. Identify the best performing scenario based on a composite score (e.g., high NPV, low risk)
        best_scenario_id = self._find_best_scenario(scenario_comparison)
        if best_scenario_id:
            scenario_data = scenario_comparison[best_scenario_id]
            rec_title = f"Adopt Strategy from Scenario '{best_scenario_id}'"
            rec_desc = f"This scenario yielded an average NPV of {scenario_data.get('npv_irr', 0):,.0f} IRR and a projected risk score of {scenario_data.get('projected_risk_score', 1.0)}."
            recommendation = Recommendation(
                project_id=project_id,
                recommendation_type=RecommendationType.ADAPTATION_STRATEGY,
                title=rec_title,
                description=rec_desc,
                data={"based_on_scenario_id": best_scenario_id},
                confidence_level=0.8,
                risk_level=self._map_risk_score_to_level(scenario_data.get('projected_risk_score', 0.5)),
                economic_impact={"NPV_irr": scenario_data.get('npv_irr', 0)},
                environmental_impact={},
                social_impact={},
                implementation_timeline={"start_date": "TBD", "end_date": "TBD"},
                monitoring_plan={"kpis": ["yield", "profit", "risk"]}
            )
            recommendations.append(recommendation)

        # 2. Incorporate optimization result (e.g., optimal fertilizer rate)
        if optimization_results:
            opt_result = optimization_results[-1] # Take the last one for example
            opt_solution = opt_result.get("optimal_solution", {})
            fert_rate = opt_solution.get("fertilizer_rate_kg_ha_optimal")
            if fert_rate is not None:
                rec_title = f"Apply Optimal Fertilizer Rate: {fert_rate:.2f} kg/ha"
                rec_desc = "Based on optimization analysis to maximize profit while managing risk."
                recommendation = Recommendation(
                    project_id=project_id,
                    recommendation_type=RecommendationType.INPUT_OPTIMIZATION,
                    title=rec_title,
                    description=rec_desc,
                    data=opt_solution,
                    confidence_level=0.9,
                    risk_level="medium", # Based on optimization constraints/risk analysis
                    economic_impact={"potential_profit_increase_irr": "TBD"}, # Would need more calc
                    environmental_impact={"potential_emission_reduction_if_lower_rate": "TBD"},
                    social_impact={},
                    implementation_timeline={"start_date": "Next Season", "end_date": "Ongoing"},
                    monitoring_plan={"kpis": ["yield", "soil_health", "cost_per_hectare"]}
                )
                recommendations.append(recommendation)

        # 3. Generate risk mitigation advice based on highest risks
        # This would require detailed risk analysis output
        # hypothetical_risk_analysis = perform_comprehensive_risk_analysis(...)
        # if hypothetical_risk_analysis.get("market_price_risk", {}).get("value_at_risk_irr", 0) > threshold:
        #     recommendations.append(...)

        return recommendations

    def _find_best_scenario(self, comparison: Dict[str, Any]) -> str:
        """Simple logic to find the 'best' scenario (e.g., highest NPV, acceptable risk)."""
        best_id = None
        best_score = float('-inf')
        for sid, data in comparison.items():
            npv = data.get("npv_irr", 0)
            risk = data.get("projected_risk_score", 1.0)
            # Simple scoring: NPV - (risk_penalty * risk)
            score = npv - (1000000 * risk) # Heuristic penalty
            if score > best_score:
                best_score = score
                best_id = sid
        return best_id

    def _map_risk_score_to_level(self, score: float) -> str:
        """Maps a numerical risk score to a qualitative level."""
        if score < 0.33:
            return "low"
        elif score < 0.66:
            return "medium"
        else:
            return "high"

    def persist_recommendations(self, recommendations: List[Recommendation]) -> List[str]:
        """Saves recommendations to the database."""
        ids = []
        db = SessionLocal()
        try:
            for rec in recommendations:
                db_rec = DecisionRecommendationDB(
                    project_id=rec.project_id,
                    recommendation_type=rec.recommendation_type.value,
                    recommendation_data={
                        "title": rec.title,
                        "description": rec.description,
                        "detailed_data": rec.data
                    },
                    confidence_level=rec.confidence_level,
                    risk_level=rec.risk_level,
                    economic_impact=rec.economic_impact,
                    environmental_impact=rec.environmental_impact,
                    social_impact=rec.social_impact,
                    implementation_timeline=rec.implementation_timeline,
                    monitoring_plan=rec.monitoring_plan,
                    # approved_by, approved_at, implemented_at are set later
                )
                db.add(db_rec)
                db.flush() # To get the ID before commit
                ids.append(str(db_rec.id))

            db.commit()
            logger.info(f"Persisted {len(recommendations)} recommendations to DB.")
        except Exception as e:
            logger.error(f"Failed to persist recommendations: {e}")
            db.rollback()
            raise
        finally:
            db.close()
        return ids


# Example usage
def example_recommendation_generation(project_id: str, scenario_comparison_data: Dict[str, Any]):
    dss = DecisionSupportSystem()

    # Simulate an optimization result
    opt_results = [{"optimal_solution": {"fertilizer_rate_kg_ha_optimal": 125.5}}]

    recommendations = dss.generate_recommendations(project_id, scenario_comparison_data, opt_results)
    persisted_ids = dss.persist_recommendations(recommendations)

    print(f"Generated and persisted {len(persisted_ids)} recommendations: {persisted_ids}")
    for rec in recommendations:
        print(f"- {rec.title}: {rec.description} (Conf: {rec.confidence_level}, Risk: {rec.risk_level})")
