"""
Pydantic models for Hydroma Engine analysis results.
"""

from typing import Any

from pydantic import BaseModel, Field

from engine.hydroma.provenance import Provenance


class SoilAnalysisResult(Provenance, BaseModel):
    """نتیجه تحلیل خاک"""

    ec: float = Field(..., description="Electrical conductivity (dS/m)")
    unit: str = "dS/m"
    classification: str = Field(..., description="Salinity classification")
    description: str = Field(..., description="Classification description")
    crop_recommendations: dict[str, Any] = Field(default_factory=dict)
    management: dict[str, Any] = Field(default_factory=dict)


class ClimateAnalysisResult(Provenance, BaseModel):
    """نتیجه تحلیل اقلیم"""

    # Optional because "not computed" is a real outcome: when the engine
    # import fails the result is returned with data_source="unavailable"
    # and no number. A mandatory float would force a placeholder value.
    estimated_et0: float | None = Field(
        default=None, description="Reference evapotranspiration (mm/day), None if not computed"
    )
    input_data: dict[str, Any] = Field(default_factory=dict)
    method: str = "Hargreaves"
    notes: str = ""


class WatershedAnalysisResult(Provenance, BaseModel):
    """نتیجه تحلیل حوضه آبریز"""

    design_proposal: dict[str, Any] = Field(default_factory=dict)
    input_data: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class GroundwaterAnalysisResult(Provenance, BaseModel):
    """نتیجه تحلیل آبخوان"""

    # Optional because "not measured" is a real outcome: no solver is wired
    # into the adapter, so a mandatory float would force a placeholder depth.
    estimated_depth_m: float | None = Field(
        default=None, description="Estimated water table depth (m), None if not measured"
    )
    quality_class: str = Field(
        default="unknown", description="Groundwater quality class"
    )
    input_data: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
