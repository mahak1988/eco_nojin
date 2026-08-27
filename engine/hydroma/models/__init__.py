"""
Hydroma Scientific Models Library
=================================

Proprietary scientific models for precision agriculture and landscape management.

Models:
- EWSI: Multi-source Water Stress Index
- HYRUE: Radiation Use Efficiency Model
- ECSI: Carbon Sequestration Index
- HDVI: Drought Vulnerability Index
- EPIA: Precision Irrigation Advisor
- HPheno: Phenology Detection
- ESRI: Salinity Risk Index
- HLHS: Landscape Health Score

Author: EcoNojin Scientific Council
License: Proprietary
"""
from .base import ScientificModel, ValidationResult
from .ecsi import ECSI
from .epia import EPIA
from .esri import ESRI
from .ewsi import EWSI
from .hdvi import HDVI
from .hlhs import HLHS
from .hpheno import HPheno
from .hyrue import HYRUE

__all__ = [
    "ECSI",
    "EPIA",
    "ESRI",
    "EWSI",
    "HDVI",
    "HLHS",
    "HYRUE",
    "HPheno",
    "ScientificModel",
    "ValidationResult",
]

__version__ = "1.0.0"
