"""
Model Registry for Eco Nojin Expansion Models
==============================================

Central registry for all scientific models including:
- Core HyDroMa models (EWSI, HY-RUE, ECSI, etc.)
- Expansion models (SWAT+, MODFLOW 6, DSSAT, APSIM, InVEST)
- Hybrid Physics-ML models (PINN, GP Surrogates)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeVar
from uuid import uuid4

from engine.hydroma.models.base import ScientificModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=ScientificModel)


class ModelDomain(StrEnum):
    """Scientific domain of the model."""

    HYDROLOGY = "hydrology"
    AGRONOMY = "agronomy"
    SOIL = "soil"
    CLIMATE = "climate"
    CARBON = "carbon"
    EROSION = "erosion"
    GROUNDWATER = "groundwater"
    ECOSYSTEM = "ecosystem"
    SOCIOECONOMIC = "socioeconomic"


class ModelFidelity(StrEnum):
    """Model fidelity level."""

    EMPIRICAL = "empirical"  # Statistical/empirical relationships
    PROCESS_BASED = "process_based"  # Physics-based process models
    HYBRID = "hybrid"  # Physics + ML hybrid
    DATA_DRIVEN = "data_driven"  # Pure ML/data-driven


class ModelStatus(StrEnum):
    """Model lifecycle status."""

    EXPERIMENTAL = "experimental"
    VALIDATED = "validated"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""

    model_id: str
    name: str
    version: str
    domain: ModelDomain
    fidelity: ModelFidelity
    status: ModelStatus
    description: str
    references: list[str] = field(default_factory=list)
    doi: str | None = None
    authors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    calibration_sets: list[str] = field(default_factory=list)
    validation_datasets: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "version": self.version,
            "domain": self.domain.value if hasattr(self.domain, "value") else self.domain,
            "fidelity": self.fidelity.value if hasattr(self.fidelity, "value") else self.fidelity,
            "status": self.status.value if hasattr(self.status, "value") else self.status,
            "description": self.description,
            "references": self.references,
            "doi": self.doi,
            "authors": self.authors,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "calibration_sets": self.calibration_sets,
            "validation_datasets": self.validation_datasets,
            "tags": self.tags,
            "provenance": self.provenance,
        }


class ModelRegistry:
    """
    Central registry for all scientific models.

    Features:
    - Model registration with metadata
    - Version management
    - Discovery by domain, fidelity, status
    - Calibration set tracking
    - Validation dataset management
    - Provenance tracking
    """

    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or Path("data/model_registry.json")
        self._models: dict[str, ModelMetadata] = {}
        self._model_classes: dict[str, type[ScientificModel]] = {}
        self._calibration_sets: dict[str, dict[str, Any]] = {}
        self._validation_datasets: dict[str, dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    data = json.load(f)
                for model_data in data.get("models", []):
                    # Convert string enums back to Enum types
                    if "domain" in model_data and isinstance(model_data["domain"], str):
                        model_data["domain"] = ModelDomain(model_data["domain"])
                    if "fidelity" in model_data and isinstance(model_data["fidelity"], str):
                        model_data["fidelity"] = ModelFidelity(model_data["fidelity"])
                    if "status" in model_data and isinstance(model_data["status"], str):
                        model_data["status"] = ModelStatus(model_data["status"])
                    metadata = ModelMetadata(**model_data)
                    self._models[metadata.model_id] = metadata
                logger.info(f"Loaded {len(self._models)} models from registry")
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")

    def _save_registry(self) -> None:
        """Save registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "models": [m.to_dict() for m in self._models.values()],
            "updated_at": datetime.utcnow().isoformat(),
        }
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)

    def register(
        self,
        model_class: type[ScientificModel],
        metadata: ModelMetadata,
        calibration_set: dict[str, Any] | None = None,
        validation_dataset: dict[str, Any] | None = None,
    ) -> str:
        """
        Register a model with metadata.

        Args:
            model_class: The model class (must inherit from ScientificModel)
            metadata: Model metadata
            calibration_set: Optional calibration parameters
            validation_dataset: Optional validation dataset reference

        Returns:
            Model ID
        """
        model_id = metadata.model_id or str(uuid4())
        metadata.model_id = model_id
        metadata.updated_at = datetime.utcnow().isoformat()

        self._models[model_id] = metadata
        self._model_classes[model_id] = model_class

        if calibration_set:
            cal_id = calibration_set.get("id", f"cal_{model_id}_{len(self._calibration_sets)}")
            self._calibration_sets[cal_id] = {
                **calibration_set,
                "model_id": model_id,
                "registered_at": datetime.utcnow().isoformat(),
            }
            metadata.calibration_sets.append(cal_id)

        if validation_dataset:
            val_id = validation_dataset.get(
                "id", f"val_{model_id}_{len(self._validation_datasets)}"
            )
            self._validation_datasets[val_id] = {
                **validation_dataset,
                "model_id": model_id,
                "registered_at": datetime.utcnow().isoformat(),
            }
            metadata.validation_datasets.append(val_id)

        self._save_registry()
        logger.info(f"Registered model: {metadata.name} v{metadata.version} ({model_id})")
        return model_id

    def unregister(self, model_id: str) -> bool:
        """Unregister a model."""
        if model_id in self._models:
            del self._models[model_id]
            self._model_classes.pop(model_id, None)
            self._save_registry()
            logger.info(f"Unregistered model: {model_id}")
            return True
        return False

    def get(self, model_id: str) -> ModelMetadata | None:
        """Get model metadata by ID."""
        return self._models.get(model_id)

    def get_class(self, model_id: str) -> type[ScientificModel] | None:
        """Get model class by ID."""
        return self._model_classes.get(model_id)

    def instantiate(self, model_id: str, **kwargs) -> ScientificModel | None:
        """Instantiate a model by ID."""
        model_class = self._model_classes.get(model_id)
        if model_class:
            return model_class(**kwargs)
        return None

    def list_models(
        self,
        domain: ModelDomain | None = None,
        fidelity: ModelFidelity | None = None,
        status: ModelStatus | None = None,
    ) -> list[ModelMetadata]:
        """List models with optional filters."""
        models = list(self._models.values())
        if domain:
            models = [m for m in models if m.domain == domain]
        if fidelity:
            models = [m for m in models if m.fidelity == fidelity]
        if status:
            models = [m for m in models if m.status == status]
        return models

    def get_best_model(
        self,
        task: str,
        domain: ModelDomain,
        criteria: dict[str, float] | None = None,
    ) -> ModelMetadata | None:
        """
        Get the best model for a task based on criteria.

        Args:
            task: Task description (e.g., "runoff_prediction", "yield_estimation")
            domain: Required domain
            criteria: Weighted criteria (accuracy, speed, uncertainty, etc.)
        """
        candidates = self.list_models(domain=domain, status=ModelStatus.PRODUCTION)
        if not candidates:
            candidates = self.list_models(domain=domain, status=ModelStatus.VALIDATED)

        if not candidates:
            return None

        # Default criteria weights
        default_criteria = {
            "accuracy": 0.4,
            "uncertainty_quantification": 0.2,
            "speed": 0.15,
            "data_requirements": 0.15,
            "maturity": 0.1,
        }
        if criteria:
            default_criteria.update(criteria)

        # Score candidates (simplified scoring)
        scored = []
        for model in candidates:
            score = 0.0
            if model.fidelity == ModelFidelity.PROCESS_BASED:
                score += default_criteria.get("accuracy", 0) * 0.8
            elif model.fidelity == ModelFidelity.HYBRID:
                score += default_criteria.get("accuracy", 0) * 0.9
            elif model.fidelity == ModelFidelity.DATA_DRIVEN:
                score += default_criteria.get("accuracy", 0) * 0.7

            if model.validation_datasets:
                score += default_criteria.get("uncertainty_quantification", 0)

            if model.status == ModelStatus.PRODUCTION:
                score += default_criteria.get("maturity", 0)

            scored.append((score, model))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None

    def register_calibration_set(self, model_id: str, calibration_set: dict[str, Any]) -> str:
        """Register a calibration set for a model."""
        cal_id = calibration_set.get("id", f"cal_{model_id}_{len(self._calibration_sets)}")
        self._calibration_sets[cal_id] = {
            **calibration_set,
            "model_id": model_id,
            "registered_at": datetime.utcnow().isoformat(),
        }
        if model_id in self._models:
            self._models[model_id].calibration_sets.append(cal_id)
            self._save_registry()
        return cal_id

    def get_calibration_set(self, cal_id: str) -> dict[str, Any] | None:
        """Get calibration set by ID."""
        return self._calibration_sets.get(cal_id)

    def register_validation_dataset(self, model_id: str, dataset: dict[str, Any]) -> str:
        """Register a validation dataset for a model."""
        val_id = dataset.get("id", f"val_{model_id}_{len(self._validation_datasets)}")
        self._validation_datasets[val_id] = {
            **dataset,
            "model_id": model_id,
            "registered_at": datetime.utcnow().isoformat(),
        }
        if model_id in self._models:
            self._models[model_id].validation_datasets.append(val_id)
            self._save_registry()
        return val_id

    def get_validation_dataset(self, val_id: str) -> dict[str, Any] | None:
        """Get validation dataset by ID."""
        return self._validation_datasets.get(val_id)

    def export_catalog(self) -> dict[str, Any]:
        """Export full model catalog."""
        return {
            "models": [m.to_dict() for m in self._models.values()],
            "calibration_sets": self._calibration_sets,
            "validation_datasets": self._validation_datasets,
            "exported_at": datetime.utcnow().isoformat(),
        }


# Global registry instance
_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Get global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def register_model(
    model_class: type[ScientificModel],
    name: str,
    version: str,
    domain: ModelDomain,
    fidelity: ModelFidelity,
    status: ModelStatus,
    description: str,
    references: list[str],
    doi: str | None = None,
    authors: list[str] | None = None,
    input_schema: dict | None = None,
    output_schema: dict | None = None,
    tags: list[str] | None = None,
) -> str:
    """Convenience function to register a model."""
    metadata = ModelMetadata(
        model_id="",
        name=name,
        version=version,
        domain=domain,
        fidelity=fidelity,
        status=status,
        description=description,
        references=references,
        doi=doi,
        authors=authors or [],
        input_schema=input_schema or {},
        output_schema=output_schema or {},
        tags=tags or [],
    )
    return get_registry().register(model_class, metadata)
