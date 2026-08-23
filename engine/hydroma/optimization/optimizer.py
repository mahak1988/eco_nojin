"""
Optimization Engine.

Finds optimal solutions for multi-objective problems like maximizing yield,
profit, and sustainability while minimizing cost and risk.
"""
import logging
from typing import Dict, Any, List, Tuple, Callable
import numpy as np
from scipy.optimize import differential_evolution, minimize
from datetime import datetime

from database.models import OptimizationResultDB, SessionLocal
from engine.hydroma.scenarios.scenario_manager import ScenarioManager

logger = logging.getLogger(__name__)


class MultiObjectiveOptimizer:
    """Generic optimizer for multi-objective problems."""

    def __init__(self, objectives: List[Tuple[Callable, bool]], constraints: List[Callable], bounds: List[Tuple[float, float]]):
        """
        Args:
            objectives: List of tuples (objective_function, maximize_flag).
            constraints: List of constraint functions (must return >= 0).
            bounds: List of (min, max) bounds for each decision variable.
        """
        self.objectives = objectives
        self.constraints = constraints
        self.bounds = bounds
        self.num_vars = len(bounds)

    def _scalarize_objectives(self, params: np.ndarray, weights: List[float]) -> float:
        """Combines multiple objectives into a single scalar value using weights."""
        if len(weights) != len(self.objectives):
            raise ValueError("Number of weights must match number of objectives.")
        total = 0.0
        for i, (obj_func, maximize) in enumerate(self.objectives):
            val = obj_func(params)
            # If maximize, negate for minimization algorithm
            multiplier = -1 if maximize else 1
            total += weights[i] * (multiplier * val)
        return total

    def optimize_weighted_sum(self, weights: List[float], method: str = 'differential_evolution') -> Dict[str, Any]:
        """
        Solves the optimization problem using a weighted sum approach.

        Args:
            weights: Weights for each objective (should sum to 1).
            method: Optimization method ('differential_evolution', 'minimize').

        Returns:
            Dictionary containing the optimal solution and metrics.
        """
        logger.info(f"Starting optimization using {method} with weights {weights}")

        def objective_to_minimize(params):
            return self._scalarize_objectives(params, weights)

        # Define constraints for scipy (must be >= 0)
        scipy_constraints = [{'type': 'ineq', 'fun': con} for con in self.constraints]

        if method == 'differential_evolution':
            result = differential_evolution(objective_to_minimize, self.bounds, seed=42, maxiter=1000)
        elif method == 'minimize':
            # Need an initial guess for 'minimize'
            x0 = [(b[0] + b[1]) / 2.0 for b in self.bounds]
            result = minimize(objective_to_minimize, x0, method='SLSQP', bounds=self.bounds, constraints=scipy_constraints)
        else:
            raise ValueError(f"Unknown method: {method}")

        if not result.success:
            logger.error(f"Optimization failed: {result.message}")
            return {"success": False, "error": result.message, "solution": None}

        solution = result.x
        objective_values = [obj_func(solution) for obj_func, _ in self.objectives]

        logger.info(f"Optimization completed. Solution: {solution}, Objectives: {objective_values}")
        return {
            "success": True,
            "solution": dict(zip([f"var_{i}" for i in range(self.num_vars)], solution)),
            "objective_values": dict(zip(["obj_" + str(i) for i in range(len(objective_values))], objective_values)),
            "optimization_details": result
        }

    def find_pareto_front(self, num_points: int = 20) -> List[Dict[str, Any]]:
        """
        Attempts to find an approximation of the Pareto front by solving
        the problem with different weight vectors.

        Args:
            num_points: Number of points to sample on the front.

        Returns:
            List of solutions on the Pareto front.
        """
        logger.info(f"Attempting to find Pareto front with {num_points} points.")
        front = []
        # Simple heuristic: vary weights systematically
        # For 2 objectives: w1 from 0 to 1, w2 = 1 - w1
        # For more, use a grid or random sampling.
        if len(self.objectives) == 2:
            for i in range(num_points):
                w1 = i / (num_points - 1)
                w2 = 1.0 - w1
                weights = [w1, w2]
                res = self.optimize_weighted_sum(weights, method='differential_evolution')
                if res["success"]:
                    front.append({
                        "weights": weights,
                        "solution": res["solution"],
                        "objectives": res["objective_values"]
                    })
        else:
            logger.warning("Pareto front approximation is basic for >2 objectives.")
            # Implement a more robust sampler for general N objectives
            for _ in range(num_points):
                weights = np.random.dirichlet([1]*len(self.objectives)) # Uniformly sample weight space
                res = self.optimize_weighted_sum(weights.tolist(), method='differential_evolution')
                if res["success"]:
                    front.append({
                        "weights": weights.tolist(),
                        "solution": res["solution"],
                        "objectives": res["objective_values"]
                    })

        logger.info(f"Found {len(front)} points on the Pareto front.")
        return front


def run_land_use_optimization(scenario_id: str, objective_weights: Dict[str, float]) -> str:
    """
    Runs a specific optimization for land use, e.g., optimal crop mix or fertilizer application rate.

    Args:
        scenario_id: The base scenario to optimize within.
        objective_weights: Weights for objectives like {'yield': 0.4, 'profit': 0.4, 'risk': 0.2}.

    Returns:
        ID of the created optimization result record.
    """
    # Define decision variables (e.g., area for crop A, B, C; fertilizer rate)
    # Example: Optimize fertilizer rate for wheat
    bounds = [(10, 200)] # Fertilizer rate kg/ha

    # Define objectives (functions of decision variables)
    def obj_yield(fert_rate):
        # This would call the simulation chain with different fert rates
        # and extract yield. For now, a dummy function.
        rate = fert_rate[0]
        return 3.0 + 0.02 * rate - 0.0001 * rate**2 # Quadratic response

    def obj_profit(fert_rate):
        # Profit = Revenue(Yield) - Cost(FertRate)
        yield_val = obj_yield(fert_rate)
        revenue = yield_val * 2000000 # Price per ton
        cost = fert_rate[0] * 5 # Cost per kg
        return revenue - cost

    def obj_risk(fert_rate):
        # A proxy for risk, perhaps based on variance or a penalty for high rates
        return fert_rate[0] * 0.01 # Higher rate = higher risk

    objectives = [
        (obj_yield, True),  # Maximize yield
        (obj_profit, True), # Maximize profit
        (obj_risk, False)   # Minimize risk (so we minimize this term)
    ]

    # Define constraints (e.g., total area <= available area, fert_rate <= max_rate)
    def con_area(fert_rate):
        return 100 - 1 # Assuming 1 ha, area constraint. Dummy.
    constraints = [con_area]

    # Map weights from dict to list order
    ordered_weights = [objective_weights.get('yield', 0), objective_weights.get('profit', 0), objective_weights.get('risk', 0)]
    # Normalize weights
    total_w = sum(ordered_weights)
    if total_w > 0:
        ordered_weights = [w / total_w for w in ordered_weights]

    optimizer = MultiObjectiveOptimizer(objectives, constraints, bounds)
    result = optimizer.optimize_weighted_sum(ordered_weights)

    if result["success"]:
        # Save the optimization record to DB
        opt_result = OptimizationResultDB(
            scenario_id=scenario_id,
            optimization_type="fertilizer_rate_optimization",
            objective_function=str(objective_weights), # Store as string for simplicity
            constraints={"max_rate_kg_ha": 200}, # Stored constraints
            optimal_solution={"fertilizer_rate_kg_ha_optimal": result["solution"]["var_0"]},
            sensitivity_analysis={}, # Could run sensitivity here
            pareto_front=[], # Could compute here
            convergence_metrics={"nfev": result["optimization_details"].nfev, "nit": getattr(result["optimization_details"], 'nit', 0)},
            computation_time_seconds=result["optimization_details"].execution_time if hasattr(result["optimization_details"], 'execution_time') else 0.0
        )
        db = SessionLocal()
        try:
            db.add(opt_result)
            db.commit()
            logger.info(f"Saved optimization result {opt_result.id} for scenario {scenario_id}.")
            return str(opt_result.id)
        except Exception as e:
            logger.error(f"Failed to save optimization result: {e}")
            db.rollback()
        finally:
            db.close()

    return None