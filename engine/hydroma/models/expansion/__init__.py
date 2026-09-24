"""
Model Expansion Module for Eco Nojin
=====================================

Exports:
- ModelRegistry and metadata classes
- SWATPlusModel
- MODFLOW6Model
"""

from engine.hydroma.models.expansion.modflow6 import (
    MODFLOW6Config,
    MODFLOW6Inputs,
    MODFLOW6Model,
    MODFLOW6Outputs,
)
from engine.hydroma.models.expansion.registry import (
    ModelDomain,
    ModelFidelity,
    ModelMetadata,
    ModelRegistry,
    ModelStatus,
    get_registry,
    register_model,
)
from engine.hydroma.models.expansion.swat_plus import (
    SWATPlusConfig,
    SWATPlusInputs,
    SWATPlusModel,
    SWATPlusOutputs,
)

__all__ = [
    "MODFLOW6Config",
    "MODFLOW6Inputs",
    "MODFLOW6Model",
    "MODFLOW6Outputs",
    "ModelDomain",
    "ModelFidelity",
    "ModelMetadata",
    "ModelRegistry",
    "ModelStatus",
    "SWATPlusConfig",
    "SWATPlusInputs",
    "SWATPlusModel",
    "SWATPlusOutputs",
    "get_registry",
    "register_model",
]
