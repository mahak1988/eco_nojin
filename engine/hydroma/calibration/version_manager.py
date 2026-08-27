"""
Model Version Manager.

Handles the lifecycle of model versions, including creation, promotion, and rollback.
"""
import logging
from datetime import date
from typing import Any

from database.config import SessionLocal
from database.models import ModelVersionDB

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """Manages different versions of models."""

    def __init__(self):
        pass

    def create_new_version(
        self,
        model_name: str,
        version_number: str,
        version_type: str, # e.g., 'major', 'minor', 'patch', 'calibrated'
        description: str,
        parameters: dict[str, Any],
        performance_metrics: dict[str, float],
        calibration_record_id: str = None,
        promote_to_current: bool = False
    ) -> str:
        """
        Creates a new model version entry in the database.

        Args:
            model_name: Name of the model.
            version_number: Version string (e.g., '1.0.0', '1.0.0-cal-20241027').
            version_type: Type of version bump.
            description: Description of changes.
            parameters: Model parameters for this version.
            performance_metrics: Performance metrics on benchmark dataset.
            calibration_record_id: Optional ID of the calibration that produced this version.
            promote_to_current: If True, sets is_current=True for this version and False for others.

        Returns:
            ID of the newly created version.
        """
        logger.info(f"Creating new version {version_number} for model {model_name}")

        new_version = ModelVersionDB(
            model_name=model_name,
            version_number=version_number,
            version_type=version_type,
            release_date=date.today(),
            description=description,
            parameters=parameters,
            performance_metrics=performance_metrics,
            calibration_record_id=calibration_record_id,
            is_current=promote_to_current
        )

        db = SessionLocal()
        try:
            db.add(new_version)
            db.commit()
            version_id = new_version.id
            logger.info(f"Created new model version {version_number} with ID {version_id}.")

            if promote_to_current:
                self._set_other_versions_not_current(db, model_name, version_id)

            db.commit() # Commit the is_current updates if any
            return str(version_id)

        except Exception as e:
            logger.error(f"Failed to create model version: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_current_version(self, model_name: str) -> ModelVersionDB:
        """Retrieves the currently active version of a model."""
        db = SessionLocal()
        try:
            current_version = db.query(ModelVersionDB).filter(
                ModelVersionDB.model_name == model_name,
                ModelVersionDB.is_current == True
            ).first()
            return current_version
        finally:
            db.close()

    def get_version_by_number(self, model_name: str, version_number: str) -> ModelVersionDB:
        """Retrieves a specific version of a model by its number."""
        db = SessionLocal()
        try:
            version = db.query(ModelVersionDB).filter(
                ModelVersionDB.model_name == model_name,
                ModelVersionDB.version_number == version_number
            ).first()
            return version
        finally:
            db.close()

    def promote_version(self, version_id: str) -> bool:
        """Promotes a specific version ID to be the current version."""
        logger.info(f"Promoting version ID {version_id} to current.")
        db = SessionLocal()
        try:
            # Find the version to promote
            version_to_promote = db.query(ModelVersionDB).filter(ModelVersionDB.id == version_id).first()
            if not version_to_promote:
                logger.error(f"Version ID {version_id} not found.")
                return False

            model_name = version_to_promote.model_name

            # Set all other versions of this model to is_current = False
            self._set_other_versions_not_current(db, model_name, version_id)

            # Set the target version to is_current = True
            version_to_promote.is_current = True
            db.commit()
            logger.info(f"Successfully promoted version {version_to_promote.version_number} (ID: {version_id}) to current.")
            return True

        except Exception as e:
            logger.error(f"Failed to promote version: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def _set_other_versions_not_current(self, db_session: SessionLocal, model_name: str, current_version_id: str):
        """Helper to set is_current=False for all versions of a model except the specified one."""
        db_session.query(ModelVersionDB).filter(
            ModelVersionDB.model_name == model_name,
            ModelVersionDB.id != current_version_id
        ).update({"is_current": False})


# Example usage
def example_version_creation_and_promotion(cal_record_id: str):
    vm = ModelVersionManager()

    # Create a new version based on a calibration result
    new_version_id = vm.create_new_version(
        model_name="soil_nutrient_model",
        version_number="1.1.0-calibrated-20241027",
        version_type="calibrated",
        description="Version 1.1.0 after calibration using field data from Q3 2024.",
        parameters={"base_n_level": 115.5, "decay_rate": 0.12}, # From cal record
        performance_metrics={"rmse": 8.2, "nse": 0.85, "r2": 0.87}, # From cal/validation
        calibration_record_id=cal_record_id,
        promote_to_current=True # Promote this new calibrated version
    )

    if new_version_id:
        print(f"New model version created and promoted: {new_version_id}")

    # Get the current active version
    current = vm.get_current_version("soil_nutrient_model")
    if current:
        print(f"Current model version is: {current.version_number} (ID: {current.id})")
