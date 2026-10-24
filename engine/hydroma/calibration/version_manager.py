"""
Model Version Manager.

Handles the lifecycle of model versions, including creation, promotion, and rollback.
"""

import logging
from typing import Any

import structlog

from engine.ports import (
    Clock,
    SessionFactory,
    SessionPort,
    SystemClock,
    default_session_factory,
    resolve_database_attr,
)

logger = structlog.get_logger()

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """Manages different versions of models."""

    def __init__(
        self,
        session_factory: SessionFactory | None = None,
        clock: Clock | None = None,
    ):
        """
        Args:
            session_factory: Source of the persistence session. Defaults to
                ``database.config.SessionLocal``, resolved on first use rather
                than at import.
            clock: Source of the release date. Defaults to the system clock,
                which is what this always used.
        """
        self._session_factory = session_factory
        self._clock = clock

    def _session(self) -> SessionPort:
        """Open a session, resolving the default factory on first call."""
        factory = self._session_factory or default_session_factory()
        return factory()

    def _model(self):
        """Resolve the ``ModelVersionDB`` row class on first use."""
        return resolve_database_attr("models", "ModelVersionDB")

    def create_new_version(
        self,
        model_name: str,
        version_number: str,
        version_type: str,  # e.g., 'major', 'minor', 'patch', 'calibrated'
        description: str,
        parameters: dict[str, Any],
        performance_metrics: dict[str, float],
        calibration_record_id: str | None = None,
        promote_to_current: bool = False,
    ) -> str | None:
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

        model_version_db = self._model()
        new_version = model_version_db(
            model_name=model_name,
            version_number=version_number,
            version_type=version_type,
            release_date=(self._clock or SystemClock()).today(),
            description=description,
            parameters=parameters,
            performance_metrics=performance_metrics,
            calibration_record_id=calibration_record_id,
            is_current=promote_to_current,
        )

        db = self._session()
        try:
            db.add(new_version)
            db.commit()
            version_id = new_version.id
            logger.info(f"Created new model version {version_number} with ID {version_id}.")

            if promote_to_current:
                self._set_other_versions_not_current(db, model_name, version_id)

            db.commit()  # Commit the is_current updates if any
            return str(version_id)

        except Exception as e:
            logger.error(f"Failed to create model version: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def get_current_version(self, model_name: str):
        """Retrieves the currently active version of a model."""
        model_version_db = self._model()
        db = self._session()
        try:
            current_version = (
                db.query(model_version_db)
                .filter(model_version_db.model_name == model_name, model_version_db.is_current)
                .first()
            )
            return current_version
        finally:
            db.close()

    def get_version_by_number(self, model_name: str, version_number: str):
        """Retrieves a specific version of a model by its number."""
        model_version_db = self._model()
        db = self._session()
        try:
            version = (
                db.query(model_version_db)
                .filter(
                    model_version_db.model_name == model_name,
                    model_version_db.version_number == version_number,
                )
                .first()
            )
            return version
        finally:
            db.close()

    def promote_version(self, version_id: str) -> bool:
        """Promotes a specific version ID to be the current version."""
        logger.info(f"Promoting version ID {version_id} to current.")
        model_version_db = self._model()
        db = self._session()
        try:
            # Find the version to promote
            version_to_promote = (
                db.query(model_version_db).filter(model_version_db.id == version_id).first()
            )
            if not version_to_promote:
                logger.error(f"Version ID {version_id} not found.")
                return False

            model_name = version_to_promote.model_name

            # Set all other versions of this model to is_current = False
            self._set_other_versions_not_current(db, model_name, version_id)

            # Set the target version to is_current = True
            version_to_promote.is_current = True
            db.commit()
            logger.info(
                f"Successfully promoted version {version_to_promote.version_number} (ID: {version_id}) to current."
            )
            return True

        except Exception as e:
            logger.error(f"Failed to promote version: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def _set_other_versions_not_current(
        self, db_session: SessionPort, model_name: str, current_version_id: str
    ):
        """Helper to set is_current=False for all versions of a model except the specified one."""
        model_version_db = self._model()
        db_session.query(model_version_db).filter(
            model_version_db.model_name == model_name,
            model_version_db.id != current_version_id,
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
        parameters={"base_n_level": 115.5, "decay_rate": 0.12},  # From cal record
        performance_metrics={"rmse": 8.2, "nse": 0.85, "r2": 0.87},  # From cal/validation
        calibration_record_id=cal_record_id,
        promote_to_current=True,  # Promote this new calibrated version
    )

    if new_version_id:
        logger.info(f"New model version created and promoted: {new_version_id}")

    # Get the current active version
    current = vm.get_current_version("soil_nutrient_model")
    if current:
        logger.info(f"Current model version is: {current.version_number} (ID: {current.id})")
