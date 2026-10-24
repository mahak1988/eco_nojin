"""
Calibration Engine for Nojin Biofertilizer Models.

Adjusts model parameters based on field trial outcomes
to improve prediction accuracy.

Persistence arrives through an injected port
(:class:`~engine.hydroma.biofertilizer.persistence_bridge.CalibrationPersistencePort`).
This module used to import ``SessionLocal`` from ``database.config`` at module
scope, so importing it pulled in the whole database layer; remediation item
B-2 replaced that with port injection. The default when no port is given is
the in-process adapter built by
:func:`~engine.hydroma.biofertilizer.persistence_bridge.default_calibration_port`,
and the DB-backed production port is injected by the services/adapters layer.
"""

from datetime import date
from typing import Any

import numpy as np
import structlog
from scipy.optimize import minimize

from engine.ports import SessionFactory

from .persistence_bridge import (
    CalibrationPersistencePort,
    default_calibration_port,
)

logger = structlog.get_logger()


def calibrate_formulation_model(
    formulation_id: str,
    trial_data_ids: list[str],
    model_version: str,
    session_factory: SessionFactory | None = None,
    port: CalibrationPersistencePort | None = None,
):
    """
    Calibrates a biofertilizer effect model using field trial data.

    Args:
        formulation_id: ID of the formulation whose model needs calibration.
        trial_data_ids: List of trial IDs to use for calibration.
        model_version: Version identifier for the model being calibrated.
        session_factory: Source of the persistence session. When given it wins
            over the port's own factory; it pairs coherently with a session
            bound to the same store the port's row classes live on.
        port: Persistence port resolving the ORM row classes and the session
            factory. Defaults to the in-process adapter (see
            :mod:`engine.hydroma.biofertilizer.persistence_bridge`); the
            DB-backed production port is injected by the services layer.

    Returns:
        Calibration report and updated parameters.
    """
    logger.info(f"Calibrating model for formulation {formulation_id} (v{model_version})...")

    # Resolve persistence through the injected port - no database import and
    # no module-level session-factory binding. The row classes come from the
    # port; the session comes from the caller's factory when one is given,
    # otherwise from the port.
    bridge = port if port is not None else default_calibration_port()
    trial_db = bridge.get_model_attr("models", "NojinFieldTrialDB")
    factory = session_factory or bridge.get_session_factory()
    db = factory()
    try:
        trials = db.query(trial_db).filter(trial_db.id.in_(trial_data_ids)).all()

        if not trials:
            raise ValueError(f"No trial data found for IDs: {trial_data_ids}")

        # Prepare data for calibration (X: inputs, y: observed outcomes)
        X_inputs = []
        y_observed = []
        for trial in trials:
            if trial.statistical_analysis and trial.post_application_data:
                # Example features: soil pH, OM, N, P, K, dosage, climate factor
                # Example target: yield_response
                baseline = trial.baseline_data
                X_inputs.append(
                    [
                        baseline.get("soil_ph", 7.0),
                        baseline.get("soil_om_pct", 1.0),
                        baseline.get("soil_n_kg_ha", 100),
                        baseline.get("soil_p_kg_ha", 50),
                        baseline.get("soil_k_kg_ha", 100),
                        trial.dosage_kg_ha,
                        1.0,  # Placeholder for climate factor
                    ]
                )
                y_observed.append(trial.yield_response)

        X = np.array(X_inputs)
        y_true = np.array(y_observed)

        if X.shape[0] == 0 or y_true.shape[0] == 0:
            raise ValueError("Insufficient data for calibration after filtering.")

        # Define objective function (e.g., Mean Squared Error)
        def objective(params):
            # Example simple linear model: y_pred = params[0] + sum(params[1:] * X_features)
            y_pred = params[0] + X.dot(params[1:])
            mse = np.mean((y_true - y_pred) ** 2)
            return mse

        # Initial guess for parameters [intercept, coef1, coef2, ...]
        initial_params = [0.0] * (X.shape[1] + 1)

        # Perform optimization
        result = minimize(objective, initial_params, method="BFGS")

        if not result.success:
            raise RuntimeError(f"Calibration failed: {result.message}")

        updated_params = result.x.tolist()
        quality_score = 1.0 / (1.0 + result.fun)  # Inverse of MSE, higher is better

        # Save calibration record to DB
        calibration_record_db = bridge.get_model_attr(
            "models", "NojinCalibrationRecordDB"
        )
        calibration_record = calibration_record_db(
            formulation_id=formulation_id,
            calibration_date=date.today(),  # Use appropriate date
            calibration_data={
                "trial_ids_used": trial_data_ids,
                "input_features_shape": X.shape,
                "objective_function": "MSE",
                "optimization_method": "BFGS",
                "raw_optimization_result": str(result),  # Store as string for simplicity
            },
            model_version=model_version,
            parameters_updated=updated_params,
            validation_results={},  # Could add train/test split validation here
            calibration_quality_score=quality_score,
            calibrated_by="System_AutoCalibrator_v1",  # Or a user ID
        )
        db.add(calibration_record)
        db.commit()

        logger.info(f"Calibration successful. Quality Score: {quality_score:.4f}")
        return {
            "formulation_id": formulation_id,
            "model_version": model_version,
            "trial_ids_used": trial_data_ids,
            "updated_parameters": updated_params,
            "calibration_quality_score": quality_score,
            "optimization_details": result,
        }

    finally:
        db.close()


def load_calibrated_model(
    formulation_id: str,
    target_date: date | None = None,
    session_factory: SessionFactory | None = None,
    port: CalibrationPersistencePort | None = None,
) -> dict[str, Any]:
    """
    Loads the most recent (or date-specific) calibrated parameters for a model.

    Args:
        formulation_id: ID of the formulation.
        target_date: Optional date to get calibration closest to this date.
        session_factory: Source of the persistence session. When given it wins
            over the port's own factory; it pairs coherently with a session
            bound to the same store the port's row classes live on.
        port: Persistence port resolving the ORM row class and the session
            factory. Defaults to the in-process adapter (see
            :mod:`engine.hydroma.biofertilizer.persistence_bridge`); the
            DB-backed production port is injected by the services layer.

    Returns:
        Dictionary containing model parameters and metadata.
    """
    bridge = port if port is not None else default_calibration_port()
    calibration_record_db = bridge.get_model_attr(
        "models", "NojinCalibrationRecordDB"
    )
    factory = session_factory or bridge.get_session_factory()
    db = factory()
    try:
        query = db.query(calibration_record_db).filter(
            calibration_record_db.formulation_id == formulation_id
        )
        if target_date:
            # Find the record with the closest date
            # This is a simplified approach, might need refinement
            # A more robust solution might involve fetching all and calculating the difference in Python.
            # For simplicity here, we'll sort by descending date to get the latest.
            pass  # Default sort will be applied below
        else:
            query = query.order_by(calibration_record_db.calibration_date.desc())

        latest_calibration = query.first()

        if not latest_calibration:
            # Return default/untrained model parameters
            return {
                "formulation_id": formulation_id,
                "model_version": "default",
                "parameters": None,  # Indicate no calibration available
                "quality_score": 0.0,
                "last_calibration_date": None,
            }

        return {
            "formulation_id": formulation_id,
            "model_version": latest_calibration.model_version,
            "parameters": latest_calibration.parameters_updated,
            "quality_score": latest_calibration.calibration_quality_score,
            "last_calibration_date": latest_calibration.calibration_date,
        }

    finally:
        db.close()
