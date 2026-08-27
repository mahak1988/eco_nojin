"""
Calibration Engine.

Automatically adjusts model parameters to fit observed data.
"""
import logging
from collections.abc import Callable
from datetime import date
from typing import Any

import numpy as np
from scipy.optimize import minimize

from database.config import SessionLocal
from database.models import CalibrationRecordDB

logger = logging.getLogger(__name__)


class ModelCalibrator:
    """Generic calibrator for numerical models."""

    def __init__(self, model_function: Callable, param_bounds: dict[str, tuple[float, float]]):
        """
        Args:
            model_function: The model to calibrate (should take params dict and return predictions).
            param_bounds: Dictionary mapping parameter names to (min, max) bounds.
        """
        self.model_function = model_function
        self.param_bounds = param_bounds
        self.bounds_list = list(param_bounds.values())
        self.param_names = list(param_bounds.keys())

    def _objective_function(self, params: list[float], observed_data: np.ndarray, input_conditions: dict[str, Any]) -> float:
        """Objective function to minimize (e.g., RMSE)."""
        param_dict = dict(zip(self.param_names, params))
        predicted_data = self.model_function(input_conditions, param_dict)
        rmse = np.sqrt(np.mean((observed_data - predicted_data) ** 2))
        logger.debug(f"Params: {param_dict}, RMSE: {rmse}")
        return rmse

    def calibrate(self, initial_params: dict[str, float], observed_data: np.ndarray, input_conditions: dict[str, Any], method: str = 'L-BFGS-B') -> dict[str, Any]:
        """
        Performs the calibration.

        Args:
            initial_params: Initial guess for parameters.
            observed_data: Observed values to fit against.
            input_conditions: Fixed inputs for the model run.
            method: Optimization method for scipy.minimize.

        Returns:
            Dictionary containing results and new parameters.
        """
        logger.info(f"Starting calibration using method {method}")
        observed_array = np.asarray(observed_data)

        initial_values = [initial_params[name] for name in self.param_names]

        result = minimize(
            fun=self._objective_function,
            x0=initial_values,
            args=(observed_array, input_conditions),
            bounds=self.bounds_list,
            method=method
        )

        if not result.success:
            logger.error(f"Calibration failed: {result.message}")
            return {"success": False, "error": result.message, "metrics": {}}

        optimized_params = dict(zip(self.param_names, result.x))
        final_rmse = result.fun

        # Calculate other metrics
        predicted_final = self.model_function(input_conditions, optimized_params)
        nash_sutcliffe = self._nash_sutcliffe_efficiency(observed_array, predicted_final)
        r_squared = self._r_squared(observed_array, predicted_final)

        metrics = {
            "rmse": final_rmse,
            "nash_sutcliffe_efficiency": nash_sutcliffe,
            "r_squared": r_squared,
            "iterations": result.nit
        }

        logger.info(f"Calibration completed successfully. Final RMSE: {final_rmse:.4f}")
        return {
            "success": True,
            "optimized_params": optimized_params,
            "initial_params": initial_params,
            "metrics": metrics,
            "optimization_details": result
        }

    def _nash_sutcliffe_efficiency(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculates Nash-Sutcliffe Efficiency (NSE)."""
        nse_top = np.sum((observed - predicted) ** 2)
        nse_bot = np.sum((observed - np.mean(observed)) ** 2)
        if nse_bot == 0:
            return 1.0 if nse_top == 0 else 0.0
        return 1 - (nse_top / nse_bot)

    def _r_squared(self, observed: np.ndarray, predicted: np.ndarray) -> float:
        """Calculates R-squared."""
        ss_res = np.sum((observed - predicted) ** 2)
        ss_tot = np.sum((observed - np.mean(observed)) ** 2)
        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0
        return 1 - (ss_res / ss_tot)


def run_soil_nutrient_calibration(observed_soil_data: list[dict[str, float]], input_conditions: dict[str, Any], model_version: str) -> str:
    """
    Runs a specific calibration for the soil nutrient model.

    Args:
        observed_soil_data: List of observed nutrient levels over time.
        input_conditions: Inputs like weather, fertilization, etc.
        model_version: Version identifier for the model being calibrated.

    Returns:
        ID of the created calibration record.
    """
    # Prepare data for the objective function
    # Example: Calibrate for Nitrogen over time
    observed_timeseries = [d["nitrogen_ppm"] for d in observed_soil_data]
    input_conditions_for_model = input_conditions # Pass as-is or transform

    # Define the model function and its parameters to calibrate
    def model_wrapper(conditions, params):
        # This function calls the actual model with params and returns a timeseries
        # Example call (adjust based on real model signature):
        # return run_nutrient_model(conditions, **params)
        # For demo, return a dummy prediction based on params
        baseline = np.full(len(observed_timeseries), params.get("base_n_level", 100))
        decay = params.get("decay_rate", 0.1)
        time_factor = np.arange(len(observed_timeseries))
        prediction = baseline * np.exp(-decay * time_factor)
        return prediction

    param_bounds = {
        "base_n_level": (50.0, 200.0),
        "decay_rate": (0.01, 0.5)
    }

    initial_guess = {
        "base_n_level": 120.0,
        "decay_rate": 0.1
    }

    calibrator = ModelCalibrator(model_wrapper, param_bounds)
    result = calibrator.calibrate(initial_guess, observed_timeseries, input_conditions_for_model)

    if result["success"]:
        # Save the calibration record to DB
        cal_record = CalibrationRecordDB(
            model_name="soil_nutrient_model",
            model_version=model_version,
            calibration_date=date.today(),
            calibration_data={
                "observed_data_length": len(observed_timeseries),
                "input_conditions_summary": str(input_conditions)[:200], # Truncate for DB
            },
            parameters_before=result["initial_params"],
            parameters_after=result["optimized_params"],
            calibration_metrics=result["metrics"],
            calibration_quality_score=result["metrics"]["nash_sutcliffe_efficiency"], # Use NSE as quality score
            validation_results={}, # Will be filled later by validator
            calibrated_by="AutoCalibrator_v1"
        )
        db = SessionLocal()
        try:
            db.add(cal_record)
            db.commit()
            logger.info(f"Saved calibration record {cal_record.id} for soil model.")
            return cal_record.id
        except Exception as e:
            logger.error(f"Failed to save calibration record: {e}")
            db.rollback()
        finally:
            db.close()

    return None
