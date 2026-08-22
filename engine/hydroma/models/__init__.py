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
from .ewsi import EWSI
from .hyrue import HYRUE
from .ecsi import ECSI
from .hdvi import HDVI
from .epia import EPIA
from .hpheno import HPheno
from .esri import ESRI
from .hlhs import HLHS

__all__ = [
    "ScientificModel",
    "ValidationResult",
    "EWSI",
    "HYRUE",
    "ECSI",
    "HDVI",
    "EPIA",
    "HPheno",
    "ESRI",
    "HLHS",
]

__version__ = "1.0.0"
