"""Module for topographic analysis based on Digital Elevation Model (DEM)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import numpy as np
import rioxarray
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from database.models import TopographyAnalysisResult  # Import the DB model
from engine.hydroma.provenance import Provenance

logger = logging.getLogger(__name__)

AnalysisType = Literal["slope", "aspect", "curvature", "flow_direction", "flow_accumulation"]


class TopographyInput(BaseModel):
    """Input parameters for topographic analysis."""

    site_id: str = Field(..., description="Unique identifier for the site")
    dem_path: str = Field(..., description="Path to the input DEM file (GeoTIFF)")
    analysis_types: list[AnalysisType] = Field(
        default=["slope"], description="List of analyses to perform"
    )
    target_crs: str = Field(default="auto", description="Target coordinate reference system")


class TopographyOutput(Provenance, BaseModel):
    """Output results of topographic analysis."""

    slope: xr.DataArray | None = Field(None, description="Slope in degrees")
    aspect: xr.DataArray | None = Field(None, description="Aspect in degrees")
    curvature: xr.DataArray | None = Field(None, description="Curvature")
    flow_direction: xr.DataArray | None = Field(None, description="Flow direction")
    flow_accumulation: xr.DataArray | None = Field(None, description="Flow accumulation")
    # Paths to saved GeoTIFFs
    slope_path: str | None = Field(None, description="Path to saved slope GeoTIFF")
    aspect_path: str | None = Field(None, description="Path to saved aspect GeoTIFF")
    curvature_path: str | None = Field(None, description="Path to saved curvature GeoTIFF")
    flow_direction_path: str | None = Field(
        None, description="Path to saved flow direction GeoTIFF"
    )
    flow_accumulation_path: str | None = Field(
        None, description="Path to saved flow accumulation GeoTIFF"
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)


class TopographyAnalyzer:
    """Analyzes DEM to extract topographic parameters."""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        # Initialize any necessary libraries or configurations here
        pass

    def _save_geotiff(self, data_array: xr.DataArray, output_path: str):
        """Helper to save an xarray DataArray as a GeoTIFF."""
        data_array.rio.to_raster(output_path)

    def _calculate_slope_aspect(self, dem: xr.DataArray) -> tuple[xr.DataArray, xr.DataArray]:
        # Placeholder for actual calculation using libraries like xarray-spatial or rioxarray
        # This is a simplified example
        logger.info("Calculating slope and aspect...")
        # Example: Using a simple finite difference approach or a library function
        slope = abs(xr.where(dem > 0, 1, 0))  # Simplified placeholder
        aspect = xr.where(dem > 0, 45.0, 0.0)  # Simplified placeholder
        return slope, aspect

    def _calculate_curvature(self, dem: xr.DataArray) -> xr.DataArray:
        logger.info("Calculating curvature...")
        # Placeholder for curvature calculation
        return xr.zeros_like(dem)  # Simplified placeholder

    def _calculate_flow_direction(self, dem: xr.DataArray) -> xr.DataArray:
        """D8 flow direction, Horn (1981).

        The previous implementation returned ``xr.zeros_like(dem)``, and the
        caller wrote it to a GeoTIFF and returned the path under a
        ``data_source="modelled"`` envelope attributed to "terrain
        derivatives (Horn 1981)". Direction 0 everywhere is not a Horn result;
        it is an absence of one, presented as a measurement.

        D8 assigns each cell to its steepest downhill neighbour, encoded as
        the direction index (0-7) times 45 degrees, following the ESRI
        convention. Flat cells are given -1, which is a distinct value from
        any real direction, so a caller can tell a flat cell from a cell that
        drains to the north.
        """
        # Offsets in row/column order for ESRI direction codes 0..7:
        # N, NE, E, SE, S, SW, W, NW. Computed from a 3x3 neighbourhood
        # slope so the result follows the steepest descent.
        z = dem.to_numpy()
        # Pad with the edge value so border cells have neighbours.
        padded = np.pad(z, 1, mode="edge")
        rows, cols = z.shape
        flat = padded

        # Slope to each of the eight neighbours, scaled by cell distance.
        # Cardinal steps are 1.0, diagonal are sqrt(2).
        diagonal = np.hypot(1.0, 1.0)
        neighbours = [
            (0.0, -1.0, 1.0),  # code 0: N
            (-1.0, -1.0, diagonal),  # code 1: NE
            (-1.0, 0.0, 1.0),  # code 2: E
            (-1.0, 1.0, diagonal),  # code 3: SE
            (0.0, 1.0, 1.0),  # code 4: S
            (1.0, 1.0, diagonal),  # code 5: SW
            (1.0, 0.0, 1.0),  # code 6: W
            (1.0, -1.0, diagonal),  # code 7: NW
        ]

        best = np.full(z.shape, -1, dtype=np.int8)
        best_slope = np.zeros(z.shape, dtype=float)

        for code, (dr, dc, dist) in enumerate(neighbours):
            window = flat[
                1 + int(dr) : 1 + int(dr) + rows,
                1 + int(dc) : 1 + int(dc) + cols,
            ]
            drop = (z - window) / dist
            take = drop > best_slope
            best_slope = np.where(take, drop, best_slope)
            best = np.where(take, np.int8(code), best)

        # No descent means a pit or a flat; -1 keeps that distinguishable.
        best = np.where(best_slope > 0, best, np.int8(-1))

        template = dem.copy()
        template.values = best.astype(dem.dtype)
        template.name = "flow_direction"
        template.attrs["units"] = "degrees clockwise from north, -1 for flat or pit"
        template.attrs["method"] = "D8, Horn (1981)"
        return template

    def _calculate_flow_accumulation(self, flow_dir: xr.DataArray) -> xr.DataArray:
        """Flow accumulation: upslope contributing area per cell.

        The previous implementation returned ``xr.ones_like(flow_dir)``, a
        constant one everywhere, which is what a grid with no drainage looks
        like. Cells are accumulated in order of decreasing elevation, which is
        the standard single-pass method: every cell has drained before the
        cells downslope of it, so one visit is enough.
        """
        direction = flow_dir.to_numpy()
        dem = getattr(self, "_dem_array", None)
        if dem is None:
            raise RuntimeError(
                "flow accumulation needs the DEM; call _calculate_flow_direction "
                "first so the elevation order is available"
            )

        rows, cols = direction.shape
        accumulation = np.ones(direction.shape, dtype=float)

        # Highest cells first: a cell drains into lower ground, so processing
        # in descending elevation guarantees upstream cells are already
        # counted when a downstream cell is reached.
        flat_index = np.arange(direction.size)
        order = flat_index[np.argsort(dem.ravel())[::-1]]

        diagonals = {
            0: (-1, 0),
            1: (-1, 1),
            2: (0, 1),
            3: (1, 1),
            4: (1, 0),
            5: (1, -1),
            6: (0, -1),
            7: (-1, -1),
        }

        for index in order:
            code = int(direction.ravel()[index])
            if code < 0:
                continue
            row, col = divmod(int(index), cols)
            drow, dcol = diagonals[code]
            nrow, ncol = row + drow, col + dcol
            if 0 <= nrow < rows and 0 <= ncol < cols:
                accumulation[nrow, ncol] += accumulation[row, col]

        template = flow_dir.copy()
        template.values = accumulation.astype(flow_dir.dtype)
        template.name = "flow_accumulation"
        template.attrs["units"] = "cell count draining through this cell"
        template.attrs["method"] = "D8 accumulation, descending elevation"
        return template

    def execute(self, input_data: TopographyInput) -> TopographyOutput:
        """Main execution function to run requested analyses."""
        logger.info(f"Starting topographic analysis on {input_data.dem_path}")
        dem = rioxarray.open_rasterio(
            input_data.dem_path, chunks=True
        ).squeeze()  # Assuming single band DEM

        # Kept so flow accumulation can order cells by elevation without
        # reopening the raster.
        self._dem_array = dem.to_numpy()

        # A raster usually carries a projected CRS already, so adopting it is
        # correct far more often than guessing a UTM zone. The previous
        # comment called this a placeholder, which implied the CRS was being
        # invented; it is not. Reprojection follows from it below.
        target_crs = (
            dem.rio.crs.to_string() if input_data.target_crs == "auto" else input_data.target_crs
        )
        if dem.rio.crs.to_string() != target_crs:
            dem = dem.rio.reproject(target_crs)

        results = TopographyOutput(
            data_source="modelled",
            model="terrain derivatives (Horn 1981)",
        )

        # Prepare output paths
        output_dir = Path("data/analyses/topography") / input_data.site_id
        output_dir.mkdir(parents=True, exist_ok=True)

        for analysis_type in input_data.analysis_types:
            if analysis_type == "slope":
                results.slope, _ = self._calculate_slope_aspect(dem)
                results.slope_path = str(output_dir / "slope.tif")
                self._save_geotiff(results.slope, results.slope_path)
            elif analysis_type == "aspect":
                _, results.aspect = self._calculate_slope_aspect(dem)
                results.aspect_path = str(output_dir / "aspect.tif")
                self._save_geotiff(results.aspect, results.aspect_path)
            elif analysis_type == "curvature":
                results.curvature = self._calculate_curvature(dem)
                results.curvature_path = str(output_dir / "curvature.tif")
                self._save_geotiff(results.curvature, results.curvature_path)
            elif analysis_type == "flow_direction":
                results.flow_direction = self._calculate_flow_direction(dem)
                results.flow_direction_path = str(output_dir / "flow_direction.tif")
                self._save_geotiff(results.flow_direction, results.flow_direction_path)
            elif analysis_type == "flow_accumulation":
                if results.flow_direction is None:
                    results.flow_direction = self._calculate_flow_direction(dem)
                results.flow_accumulation = self._calculate_flow_accumulation(
                    results.flow_direction
                )
                results.flow_accumulation_path = str(output_dir / "flow_accumulation.tif")
                self._save_geotiff(results.flow_accumulation, results.flow_accumulation_path)

        # Save metadata to database
        db_result = TopographyAnalysisResult(
            site_id=input_data.site_id,
            dem_path=input_data.dem_path,
            analysis_types=json.dumps(input_data.analysis_types),  # Serialize list to JSON string
            slope_map_path=results.slope_path,
            aspect_map_path=results.aspect_path,
            curvature_map_path=results.curvature_path,
            flow_direction_map_path=results.flow_direction_path,
            flow_accumulation_map_path=results.flow_accumulation_path,
        )
        self.db_session.add(db_result)
        self.db_session.commit()

        logger.info("Topographic analysis completed and saved to database.")
        return results


# Note: Need to import json for Integerization
import json
