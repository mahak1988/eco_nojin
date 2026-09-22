"""Plant Neurobiology analysis module for hydroma engine.

Provides electrical signal processing (action potentials, variation potentials),
VOC profile analysis (stress biomarker detection), and integrated stress
assessment orchestration.

Modules:
    signals: ElectricalSignalProcessor for plant electrical signal features
        and stress classification (AP/VP/SP detection).
    voc: VOCAnalyzer for volatile organic compound profile analysis and
        stress type classification from GC-MS/e-nose data.
    engine: PlantNeuroEngine orchestrating combined signal+VOC analysis.

Example:
    >>> from engine.hydroma.plant_neuro import PlantNeuroEngine, VOCProfile
    >>> engine = PlantNeuroEngine()
    >>> profile = VOCProfile(compounds={"isoprene": 150.0, "myrcene": 60.0})
    >>> assessment = engine.analyze_from_voc(profile)
    >>> print(assessment.integrated_stress_level)
"""

from __future__ import annotations

from .signals import (
    ElectricalSignalProcessor,
    SignalFeatures,
)
from .voc import (
    VOCAnalyzer,
    VOCProfile,
    StressSignature,
)
from .engine import (
    PlantNeuroEngine,
    PlantNeuroConfig,
    StressAssessment,
    StressLevel,
)

__all__ = [
    "ElectricalSignalProcessor",
    "SignalFeatures",
    "VOCAnalyzer",
    "VOCProfile",
    "StressSignature",
    "PlantNeuroEngine",
    "PlantNeuroConfig",
    "StressAssessment",
    "StressLevel",
]
