"""Module for calibrating hydrological and agronomic models."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Protocol # Imported 'Any'

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ModelRunner(Protocol):
    """Protocol defining the interface for a model that can be calibrated."""
    def run(self, parameters: Dict[str, Any]) -> Any:
        ...

class CalibrationInput(BaseModel):
    """Input parameters for the calibration process."""
    model_runner: Any = Field(..., description="Instance of the model to calibrate (must follow ModelRunner protocol) - Type erased for Pydantic compatibility") # Changed type hint to Any
    observed_data: List[float] = Field(..., description="List of observed/measured values")
    parameter_bounds: Dict[str, tuple[float, float]] = Field(..., description="Dictionary of parameter names and their (min, max) bounds")
    objective_function: str = Field("rmse", description="Objective function to minimize ('rmse', 'nse', etc.)")


class CalibrationOutput(BaseModel):
    """Output results of the calibration process."""
    calibrated_parameters: Dict[str, float] = Field(..., description="Final calibrated parameter values")
    best_objective_value: float = Field(..., description="Value of the objective function at the optimum")
    history: List[Dict[str, Any]] = Field(..., description="History of parameter sets and objective values during calibration")


class Calibrator:
    """Performs calibration using a simple brute-force or optimization algorithm."""
    
    def __init__(self):
        # Could initialize an optimizer here (e.g., scipy.optimize, platypus)
        pass

    def _rmse(self, simulated: List[float], observed: List[float]) -> float:
        """Calculate Root Mean Square Error."""
        if len(simulated) != len(observed):
            raise ValueError("Simulated and observed data must have the same length for error calculation.")
        diffs = [(s - o)**2 for s, o in zip(simulated, observed)]
        mse = sum(diffs) / len(diffs)
        return mse**0.5

    def _simple_brute_force(self, input_data: CalibrationInput, num_steps: int = 10) -> CalibrationOutput:
        """A simple brute-force calibration for demonstration."""
        logger.info("Starting simple brute-force calibration...")
        
        param_names = list(input_data.parameter_bounds.keys())
        param_ranges = list(input_data.parameter_bounds.values())
        
        # Generate parameter combinations (only works well for 1-2 parameters due to combinatorial explosion)
        # For more parameters, use scipy.optimize or other libraries
        best_params = {}
        best_obj_val = float('inf')
        history = []

        # Example for two parameters
        if len(param_names) == 2:
            p1_name, p2_name = param_names
            p1_min, p1_max = param_ranges[0]
            p2_min, p2_max = param_ranges[1]
            
            step_p1 = (p1_max - p1_min) / num_steps
            step_p2 = (p2_max - p2_min) / num_steps

            for i in range(num_steps + 1):
                for j in range(num_steps + 1):
                    p1_val = p1_min + i * step_p1
                    p2_val = p2_min + j * step_p2
                    params = {p1_name: p1_val, p2_name: p2_val}

                    try:
                        # Run the model with these parameters
                        model_output = input_data.model_runner.run(params) # Runtime check ensures compatibility
                        # Extract simulated values (this depends on the model's output structure)
                        # Assuming model_output has a 'values' attribute or is a list
                        if hasattr(model_output, 'values'):
                            simulated_data = model_output.values
                        else:
                            # Assume it's a list-like object containing simulated values
                            simulated_data = model_output
                        
                        if input_data.objective_function == "rmse":
                            obj_val = self._rmse(simulated_data, input_data.observed_data)
                        else:
                            raise ValueError(f"Unsupported objective function: {input_data.objective_function}")
                        
                        history.append({"params": params.copy(), "objective_value": obj_val})

                        if obj_val < best_obj_val:
                            best_obj_val = obj_val
                            best_params = params.copy()
                    except Exception as e:
                        logger.warning(f"Model run failed for params {params}: {e}. Skipping.")
                        continue
        else:
            raise NotImplementedError("Brute force calibration is only implemented for 1 or 2 parameters. Use an external optimizer for more.")

        logger.info(f"Calibration finished. Best params: {best_params}, Best {input_data.objective_function}: {best_obj_val:.4f}")
        return CalibrationOutput(calibrated_parameters=best_params, best_objective_value=best_obj_val, history=history)

    def execute(self, input_data: CalibrationInput) -> CalibrationOutput:
        """Main execution function."""
        logger.info("Starting calibration process.")
        # For now, use the simple brute-force method
        # In the future, integrate with scipy.optimize.minimize or other libraries
        return self._simple_brute_force(input_data)