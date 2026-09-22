"""
Pydantic models for Hydroma Engine analysis results.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SoilAnalysisResult(BaseModel):
    """نتیجه تحلیل خاک"""

    ec: float = Field(..., description="Electrical conductivity (dS/m)")
    unit: str = "dS/m"
    classification: str = Field(..., description="Salinity classification")
    description: str = Field(..., description="Classification description")
    crop_recommendations: dict[str, Any] = Field(default_factory=dict)
    management: dict[str, Any] = Field(default_factory=dict)


class ClimateAnalysisResult(BaseModel):
    """نتیجه تحلیل اقلیم"""

    estimated_et0: float = Field(..., description="Reference evapotranspiration (mm/day)")
    input_data: dict[str, Any] = Field(default_factory=dict)
    method: str = "Hargreaves"


class WatershedAnalysisResult(BaseModel):
    """نتیجه تحلیل حوضه آبریز"""

    design_proposal: dict[str, Any] = Field(default_factory=dict)
    input_data: dict[str, Any] = Field(default_factory=dict)


class GroundwaterAnalysisResult(BaseModel):
    """نتیجه تحلیل آبخوان"""

    estimated_depth_m: float = Field(..., description="Estimated water table depth (m)")
    quality_class: str = Field(..., description="Groundwater quality class")
    input_data: dict[str, Any] = Field(default_factory=dict)
