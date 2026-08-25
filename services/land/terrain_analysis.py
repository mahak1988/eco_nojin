from typing import Dict, Any, List
from pydantic import BaseModel
# Remove direct imports from engine.land as the service will handle this via its dependency injection
# from engine.land.dem_processor import DEMProcessor
# from engine.land.slope_aspect import SlopeAspectAnalyzer
import tempfile
import os
import numpy as np


class TerrainAnalysisRequest(BaseModel):
    """Request model for terrain analysis."""
    land_profile_id: str
    dem_file_path: str
    analysis_types: List[str] = ["slope", "aspect"] # Default to slope and aspect


class TerrainAnalysisResult(BaseModel):
    """Result model for a single analysis type."""
    analysis_type: str
    result_data: Dict[str, Any] # Could be stats, raw data, etc.
    method: str
    parameters: Dict[str, Any]

# The function 'perform_terrain_analysis' has been removed from this file
# as the logic now resides in the LandService which uses ILandEngine.
