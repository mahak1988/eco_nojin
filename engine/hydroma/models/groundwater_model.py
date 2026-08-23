"""Module for basic groundwater modeling or connection to external models."""
from __future__ import annotations

import logging
from typing import Literal, Any # Added 'Any'

import numpy as np
import xarray as xr
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

ModelType = Literal["analytical", "modflow_link"] # Future: add modflow_link

class GroundwaterInput(BaseModel):
    """Input parameters for groundwater analysis."""
    model_type: ModelType = Field("analytical", description="Type of groundwater model to use")
    transmissivity_m2day: float = Field(..., gt=0, description="Aquifer transmissivity (m2/day)")
    storativity: float = Field(..., gt=0, lt=1, description="Aquifer storativity (dimensionless)")
    pumping_rate_m3day: float = Field(0.0, ge=0, description="Well pumping rate (m3/day)")
    observation_distance_m: float = Field(..., gt=0, description="Distance from well to observation point (m)")
    time_days: float = Field(..., gt=0, description="Time since pumping started (days)")
    # For future modflow integration: path_to_input_files: str


class GroundwaterOutput(BaseModel):
    """Output results of groundwater analysis."""
    drawdown_m: float | Any | None = Field(None, description="Calculated drawdown (m) - Can be a scalar or xr.DataArray") # Changed type hint to Any
    model_description: str = Field(..., description="Description of the model used")


class GroundwaterModel:
    """Provides basic groundwater analysis tools."""
    
    def __init__(self):
        pass

    def _theis_solution(self, input_data: GroundwaterInput) -> float:
        """Calculates drawdown using Theis non-equilibrium solution."""
        logger.info("Calculating drawdown using Theis solution...")
        from scipy.special import expi # Import here to avoid hard dependency
        import numpy as np
        
        T = input_data.transmissivity_m2day
        S = input_data.storativity
        Q = input_data.pumping_rate_m3day
        r = input_data.observation_distance_m
        t = input_data.time_days

        u = (r**2 * S) / (4 * T * t)
        # W(u) is approximated by exponential integral -Ei(-u)
        W_u = -expi(-u)
        s = Q * W_u / (4 * np.pi * T)
        return s

    def execute(self, input_data: GroundwaterInput) -> GroundwaterOutput:
        """Main execution function."""
        logger.info(f"Running groundwater model: {input_data.model_type}")
        if input_data.model_type == "analytical":
            # Currently only implements Theis
            drawdown = self._theis_solution(input_data)
            return GroundwaterOutput(drawdown_m=drawdown, model_description="Theis Solution (Analytical)")
        elif input_data.model_type == "modflow_link":
            # Placeholder for future MODFLOW integration
            raise NotImplementedError("MODFLOW integration is not yet implemented.")
        else:
            raise ValueError(f"Unsupported groundwater model type: {input_data.model_type}")