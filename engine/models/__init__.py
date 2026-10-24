"""
Engine Models Package
=====================

Canonical Model Registry for HyDroMA scientific models.
"""

from .registry import ModelRegistry, get_model, get_registry, list_models

__all__ = [
    "ModelRegistry",
    "get_registry", 
    "get_model",
    "list_models",
]