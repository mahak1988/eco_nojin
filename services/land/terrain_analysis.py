
# Remove direct imports from engine.land as the service will handle this via its dependency injection
# from engine.land.dem_processor import DEMProcessor
# from engine.land.slope_aspect import SlopeAspectAnalyzer
from typing import Any

from pydantic import BaseModel


class TerrainAnalysisRequest(BaseModel):
    """Request model for terrain analysis."""
    land_profile_id: str
    dem_file_path: str
    analysis_types: list[str] = ["slope", "aspect"] # Default to slope and aspect


class TerrainAnalysisResult(BaseModel):
    """Result model for a single analysis type."""
    analysis_type: str
    result_data: dict[str, Any] # Could be stats, raw data, etc.
    method: str
    parameters: dict[str, Any]

# The function 'perform_terrain_analysis' has been removed from this file
# as the logic now resides in the LandService which uses ILandEngine.
