"""Service for designing irrigation systems."""
from __future__ import annotations

import json
import logging
from datetime import date
from typing import Literal, List
from uuid import uuid4

import geopandas as gpd
import pandas as pd
from pydantic import BaseModel, Field
from shapely.geometry import Point, LineString

logger = logging.getLogger(__name__)

IrrigationType = Literal["drip", "sprinkler", "furrow"]

class IrrigationScheduleItem(BaseModel):
    """Represents a single irrigation event."""
    date: date
    duration_minutes: int
    volume_liters_per_plant: float | None = None # For drip
    depth_mm: float | None = None # For sprinkler/furrow


class IrrigationDesignInput(BaseModel):
    """Input parameters for irrigation system design."""
    site_location_lat: float = Field(..., ge=-90, le=90, description="Latitude of the field")
    site_location_lon: float = Field(..., ge=-180, le=180, description="Longitude of the field")
    crop_type: str = Field(..., description="Type of crop to be irrigated")
    area_ha: float = Field(..., gt=0, description="Area of the field (hectares)")
    irrigation_type: IrrigationType = Field(..., description="Type of irrigation system")
    water_source_flow_m3hr: float = Field(..., gt=0, description="Flow rate of the water source (m3/hour)")
    plant_spacing_m: float = Field(1.0, gt=0, description="Spacing between plants (meters)")
    row_spacing_m: float = Field(2.0, gt=0, description="Spacing between rows (meters)")


class IrrigationDesignOutput(BaseModel):
    """Output results of the irrigation design."""
    design_id: str = Field(..., description="Unique identifier for this design")
    layout_geojson: dict = Field(..., description="GeoJSON representation of pipes and emitters/sprinklers")
    equipment_list: dict[str, int | float] = Field(..., description="List of required equipment (e.g., {'drippers': 500, 'valves': 10})")
    irrigation_schedule: List[IrrigationScheduleItem] = Field(..., description="Recommended irrigation schedule")
    design_summary: dict = Field(..., description="Key design parameters (e.g., pipe lengths, emitter specs)")


class IrrigationDesigner:
    """Designs irrigation systems."""
    
    def __init__(self):
        # Load equipment specs, hydraulic properties, crop Kc tables, etc.
        self.emitter_specs = {"drip": {"flow_lhr": 2.0}} # Example
        self.nozzle_specs = {"sprinkler": {"radius_m": 10, "flow_lpm": 5.0}} # Example


    def _design_drip_system(self, input_data: IrrigationDesignInput) -> IrrigationDesignOutput:
        logger.info("Designing a drip irrigation system...")
        
        # Calculate number of plants and emitters
        area_m2 = input_data.area_ha * 10000
        plant_count = int(area_m2 / (input_data.plant_spacing_m * input_data.row_spacing_m))
        emitter_count = plant_count # Assuming 1 emitter per plant

        # Estimate lateral and mainline lengths
        row_length_m = input_data.area_ha * 100 / input_data.row_spacing_m # Approximation
        row_count = int(input_data.area_ha * 10000 / (row_length_m * input_data.row_spacing_m))
        lateral_length_total_m = row_length_m * row_count
        mainline_length_m = input_data.row_spacing_m * row_count * 0.8 # Approximation

        # Estimate equipment
        dripper_count = emitter_count
        valve_count = max(1, int(row_count / 10)) # One valve per 10 laterals
        pressure_regulator_count = valve_count

        # Create a simple layout (lines for laterals, point for main inlet)
        center_point = Point(input_data.site_location_lon, input_data.site_location_lat)
        # Simplified representation of laterals as parallel lines
        lat_delta = 0.0001
        long_delta = 0.0005
        laterals = []
        for i in range(min(5, row_count)): # Show first 5 for simplicity
            start_lat = center_point.y - (lat_delta * 2) + (i * lat_delta)
            end_lat = center_point.y - (lat_delta * 2) + (i * lat_delta)
            start_lon = center_point.x - long_delta / 2
            end_lon = center_point.x + long_delta / 2
            laterals.append(LineString([(start_lon, start_lat), (end_lon, end_lat)]))

        gdf_lateral = gpd.GeoDataFrame([1]*len(laterals), geometry=laterals, crs="EPSG:4326")
        # Combine geometries into a single feature collection
        combined_geometry = {
            "type": "GeometryCollection",
            "geometries": [json.loads(gdf_lateral.to_json())['features'][i]['geometry'] for i in range(len(laterals))]
        }

        # Create a simple schedule (example: every 3 days, 30 minutes)
        schedule = []
        for day_offset in range(0, 90, 3): # Next 90 days, every 3 days
            schedule.append(IrrigationScheduleItem(
                date=date.today().replace(day=date.today().day + day_offset),
                duration_minutes=30,
                volume_liters_per_plant=10.0 # Example
            ))

        return IrrigationDesignOutput(
            design_id=f"DIP-{uuid4().hex[:8]}",
            layout_geojson=combined_geometry,
            equipment_list={
                "drippers": dripper_count,
                "valves": valve_count,
                "pressure_regulators": pressure_regulator_count,
                "lateral_pipe_m": round(lateral_length_total_m, 2),
                "main_pipe_m": round(mainline_length_m, 2)
            },
            irrigation_schedule=schedule,
            design_summary={
                "total_plants": plant_count,
                "emitter_flow_lhr": self.emitter_specs["drip"]["flow_lhr"],
                "estimated_system_pressure_bar": 1.0 # Placeholder
            }
        )

    def execute(self, input_data: IrrigationDesignInput) -> IrrigationDesignOutput:
        """Main execution function."""
        logger.info(f"Starting design for irrigation type: {input_data.irrigation_type}")
        if input_data.irrigation_type == "drip":
            return self._design_drip_system(input_data)
        # Add elif clauses for "sprinkler", "furrow"
        else:
            raise ValueError(f"Design for irrigation type '{input_data.irrigation_type}' is not yet fully implemented.")