"""
Nojin Biofertilizer Data Package
=================================
Phase 2 comprehensive data:
- 43 scientifically-documented materials
- 10 soil types with characteristics
- 10 formulation recipes

Phase 1 seed data (STRAINS, FORMULATIONS) loaded via populate script.
"""

# Phase 2 materials (primary data source)
from .materials_data import FORMULATIONS, MATERIALS, SOIL_TYPES

__all__ = ["FORMULATIONS", "MATERIALS", "SOIL_TYPES"]
