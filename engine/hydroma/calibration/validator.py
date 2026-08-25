"""
Validation Engine.

Validates model performance against independent datasets after calibration.
"""
import logging
from typing import Dict, Any, List, Callable
import numpy as np
from datetime import date

from database.models import CalibrationRecordDB, ModelVersionDB
from database.config import SessionLocal

logger = logging.getLogger(__name__)


class ModelValidator:
    """Validates a calibrated model against a hold-out dataset."""

    def __init__(self, model_function: Callable):
        """
        Args:
            model_function: The model to validate (should take params dict and return predictions).
        """
        self.model_function = model_function

    def validate(self, calibrated_params: Dict[str, float], validation_data: List[Dict[str, Any]], input_conditions: Dict[str, Any]) -> Dict[str, float]:
        """
        Validates the model.

        Args:
            calibrated_params: Parameters obtained from calibration.
            validation_data: Independent dataset for validation.
            input_conditions: Fixed inputs for the model run.

        Returns:
            Dictionary containing validation metrics.
        """
        logger.info("Starting model validation...")

        observed_vals = np.array([d["observation"] for d in validation_data])
        predicted_vals = []

        for condition_point in validation_data:
            # Combine global inputs with point-specific inputs if needed
            point_input = {**input_conditions, **condition_point.get("input", {})}
            pred = self.model_function(point_input, calibrated_params)
            predicted_vals.append(pred)

        predicted_array = np.array(predicted_vals)

        # Calculate validation metrics
        rmse = np.sqrt(np.mean((observed_vals - predicted_array) ** 2))
        nash_sutcliffe = self._nash_sutcliffe_efficiency(observed_vals, predicted_array)
        r_squared = self._r_squared(observed_vals, predicted_array)

        metrics = {
            "rmse": rmse,
            "nash_sutcliffe_efficiency": nash_sutcliffe,
            "r_squared": r_squared,
            "mean_error": np.mean(observed_vals - predicted_array),
            "mae": np.mean(np.abs(observed_vals - predicted_array))
        }

        logger.info(f"Validation completed. RMSE: {rmse:.4f}, NSE: {nash_sutcliffe:.4f}")
        return metrics

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


def run_validation_for_calibration(calibration_record_id: str, validation_data: List[Dict[str, Any]], input_conditions: Dict[str, Any]):
    """
    Performs validation for a specific calibration record.

    Args:
        calibration_record_id: ID of the calibration record to validate.
        validation_data: Validation dataset.
        input_conditions: Input conditions for the model run.
    """
    logger.info(f"Running validation for calibration record {calibration_record_id}")

    # Retrieve calibrated parameters from DB
    db = SessionLocal()
    try:
        cal_record = db.query(CalibrationRecordDB).filter(CalibrationRecordDB.id == calibration_record_id).first()
        if not cal_record:
            logger.error(f"Calibration record {calibration_record_id} not found.")
            return

        calibrated_params = cal_record.parameters_after
        model_name = cal_record.model_name
        model_version = cal_record.model_version

        # Define the model function based on the model name
        # This is a simplified dispatch. A factory pattern would be better for many models.
        if model_name == "soil_nutrient_model":
            from engine.hydroma.soil.nutrient_dynamic import run_nutrient_model # hypothetical
            model_func = run_nutrient_model
        else:
            logger.error(f"Model {model_name} not recognized for validation.")
            return

        # Run validation
        validator = ModelValidator(model_func)
        validation_metrics = validator.validate(calibrated_params, validation_data, input_conditions)

        # Update the calibration record in DB with validation results
        cal_record.validation_results = validation_metrics
        cal_record.approved_at = date.today() # Consider this validated/approved upon successful validation
        db.commit()
        logger.info(f"Validation results added to calibration record {calibration_record_id}.")

    except Exception as e:
        logger.error(f"Failed during validation process: {e}")
        db.rollback()
    finally:
        db.close()
