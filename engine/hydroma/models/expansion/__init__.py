"""
Model Expansion Module for Eco Nojin
=====================================

Exports:
- ModelRegistry and metadata classes
- SWATPlusModel
- MODFLOW6Model
"""

from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelStatus,
    ModelMetadata,
    ModelRegistry,
    get_registry,
    register_model,
)

from engine.hydroma.models.expansion.swat_plus import (
    SWATPlusConfig,
    SWATPlusInputs,
    SWATPlusOutputs,
    SWATPlusModel,
)

from engine.hydroma.models.expansion.modflow6 import (
    MODFLOW6Config,
    MODFLOW6Inputs,
    MODFLOW6Outputs,
    MODFLOW6Model,
)

__all__ = [
    "ModelDomain",
    "ModelFidelity",
    "ModelStatus",
    "ModelMetadata",
    "ModelRegistry",
    "get_registry",
    "register_model",
    "SWATPlusConfig",
    "SWATPlusInputs",
    "SWATPlusOutputs",
    "SWATPlusModel",
    "MODFLOW6Config",
    "MODFLOW6Inputs",
    "MODFLOW6Outputs",
    "MODFLOW6Model",
]