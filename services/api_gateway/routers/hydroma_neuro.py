"""HyDroMa Plant Neurobiology API Router.

Endpoints for plant stress analysis using electrical signals and VOC profiles.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from engine.hydroma.plant_neuro import (
    PlantNeuroEngine,
    StressLevel,
    VOCProfile,
)

logger = logging.getLogger("econojin.api.plant_neuro")

router = APIRouter(prefix="/api/v1/plant-neuro", tags=["plant-neuro"])

_engine: PlantNeuroEngine | None = None


def get_engine() -> PlantNeuroEngine:
    """Get or lazily create the PlantNeuroEngine instance."""
    global _engine
    if _engine is None:
        _engine = PlantNeuroEngine()
    return _engine


class ElectricalSignalRequest(BaseModel):
    """Request for electrical signal-based stress analysis."""

    signal_mv: list[float] = Field(..., description="Raw electrical signal in millivolts")
    sampling_rate_hz: float = Field(default=100.0, description="Sampling rate in Hz")


class VOCAnalysisRequest(BaseModel):
    """Request for VOC-based stress analysis."""

    compounds: dict[str, float] = Field(..., description="Compound names to concentrations (ppb)")
    plant_id: str | None = Field(default=None, description="Optional plant identifier")


class CombinedAnalysisRequest(BaseModel):
    """Request for combined electrical + VOC stress analysis."""

    signal_mv: list[float] | None = Field(
        default=None, description="Raw electrical signal in millivolts"
    )
    voc_compounds: dict[str, float] | None = Field(
        default=None, description="Compound names to concentrations (ppb)"
    )
    sampling_rate_hz: float = Field(default=100.0, description="Sampling rate in Hz")
    plant_id: str | None = Field(default=None, description="Optional plant identifier")


class StressAssessmentResponse(BaseModel):
    """Response with plant stress assessment results."""

    electrical_stress_type: str | None = None
    electrical_confidence: float = 0.0
    electrical_severity: float = 0.0
    voc_stress_type: str | None = None
    voc_confidence: float = 0.0
    voc_severity: float = 0.0
    integrated_stress_level: str = "healthy"
    integrated_severity_score: float = 0.0
    recommendations: list[str] = Field(default_factory=list)


@router.post("/analyze/signals", response_model=StressAssessmentResponse)
async def analyze_from_signals(request: ElectricalSignalRequest) -> StressAssessmentResponse:
    """Analyze plant stress from electrical signal data.

    Accepts raw electrical signal (action potentials, variation potentials)
    and returns stress classification, confidence, and severity.
    """
    import numpy as np

    engine = get_engine()
    engine.config.sampling_rate_hz = request.sampling_rate_hz

    try:
        signal = np.array(request.signal_mv, dtype=np.float64)
        assessment = engine.analyze_from_signals(signal)
        return StressAssessmentResponse(
            electrical_stress_type=assessment.electrical_stress_type,
            electrical_confidence=assessment.electrical_confidence,
            electrical_severity=assessment.electrical_severity,
            integrated_stress_level=assessment.integrated_stress_level.value,
            integrated_severity_score=assessment.integrated_severity_score,
            recommendations=assessment.recommendations,
        )
    except Exception as e:
        logger.error("Signal analysis failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/voc", response_model=StressAssessmentResponse)
async def analyze_from_voc(request: VOCAnalysisRequest) -> StressAssessmentResponse:
    """Analyze plant stress from VOC profile data.

    Accepts volatile organic compound concentrations and returns
    stress classification, confidence, and severity.
    """
    engine = get_engine()
    profile = VOCProfile(
        compounds=request.compounds,
        plant_id=request.plant_id,
    )
    try:
        assessment = engine.analyze_from_voc(profile)
        return StressAssessmentResponse(
            voc_stress_type=assessment.voc_stress_type,
            voc_confidence=assessment.voc_confidence,
            voc_severity=assessment.voc_severity,
            integrated_stress_level=assessment.integrated_stress_level.value,
            integrated_severity_score=assessment.integrated_severity_score,
            recommendations=assessment.recommendations,
        )
    except Exception as e:
        logger.error("VOC analysis failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/combined", response_model=StressAssessmentResponse)
async def analyze_combined(request: CombinedAnalysisRequest) -> StressAssessmentResponse:
    """Analyze plant stress from both electrical signals and VOC profiles.

    Fuses results from both modalities using weighted integration.
    Either or both inputs can be provided; at least one is required.
    """
    import numpy as np

    engine = get_engine()
    engine.config.sampling_rate_hz = request.sampling_rate_hz

    signal = np.array(request.signal_mv, dtype=np.float64) if request.signal_mv else None
    voc_profile = (
        VOCProfile(
            compounds=request.voc_compounds,
            plant_id=request.plant_id,
        )
        if request.voc_compounds
        else None
    )

    try:
        assessment = engine.analyze_combined(
            signal_mv=signal,
            voc_profile=voc_profile,
        )
        return StressAssessmentResponse(
            electrical_stress_type=assessment.electrical_stress_type,
            electrical_confidence=assessment.electrical_confidence,
            electrical_severity=assessment.electrical_severity,
            voc_stress_type=assessment.voc_stress_type,
            voc_confidence=assessment.voc_confidence,
            voc_severity=assessment.voc_severity,
            integrated_stress_level=assessment.integrated_stress_level.value,
            integrated_severity_score=assessment.integrated_severity_score,
            recommendations=assessment.recommendations,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Combined analysis failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stress-levels", response_model=list[str])
async def get_stress_levels() -> list[str]:
    """List available stress level classifications."""
    return [level.value for level in StressLevel]
