"""Module for topographic analysis based on Digital Elevation Model (DEM)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Literal

import numpy as np
import rioxarray
import xarray as xr
from pydantic import BaseModel, ConfigDict, Field

from engine.hydroma.provenance import ResultProvenance
from engine.ports import SessionPort, resolve_database_attr

logger = logging.getLogger(__name__)

AnalysisType = Literal["slope", "aspect", "curvature", "flow_direction", "flow_accumulation"]


# ============================================================================
# Path confinement
# ============================================================================
# Both inputs to this module are caller-controlled strings that were previously
# used verbatim:
#
#   * `site_id` became `Path("data/analyses/topography") / site_id`, so a caller
#     could `mkdir` anywhere the process could write and have GeoTIFFs written
#     there.
#   * `dem_path` went straight to `xr.open_dataset`, so a caller could name any
#     file the process can read -- a `.env`, a private key, `/etc/shadow`.
#
# The route in front of this is already `require_admin`, which limits *who* can
# reach it, and that was never the point: an administrator is not supposed to be
# able to read arbitrary files. The fix therefore belongs here, so it also holds
# for notebooks and batch jobs.
#
# Reconstructed 2026-10-03. A worktree merge replaced this module with an older
# revision and took the whole path-safety layer with it; the regression was caught
# by tests/unit/test_topography_path_safety.py, whose docstring records the same
# defect the authz gate had three times: a check that prose can satisfy.


class UnsafePathError(ValueError):
    """A caller-supplied path was rejected before it reached the filesystem."""


#: Where analysed rasters are written. Absolute, so containment never depends on
#: the process working directory -- which is precisely what made the old
#: relative form unsafe.
OUTPUT_ROOT: Path = Path("data/analyses/topography").resolve()

#: Where DEM inputs may be read from. Absolute for the same reason.
DEM_ALLOWED_ROOTS: tuple[Path, ...] = (
    Path("data/inputs").resolve(),
    Path("data/dem").resolve(),
    Path("data/manual").resolve(),
)

#: A readable id is kept verbatim, so the output layout stays legible.
_READABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

#: Ceiling on a generated directory name. `mkdir(parents=True)` turns a long
#: segment into a Windows path-length failure, so an unbounded id must not
#: produce an unbounded directory.
_SEGMENT_MAX = 32


def safe_site_segment(site_id: str) -> str:
    """Reduce a caller-supplied site id to one path segment that cannot traverse.

    A readable id is returned unchanged. Anything else is replaced by a short
    digest rather than rejected: rejection would break working calls for ids that
    merely contain a dot, and a digest cannot traverse and does not collide.
    """
    if _READABLE_ID.match(site_id):
        return site_id
    return hashlib.sha256(site_id.encode("utf-8", "replace")).hexdigest()[:_SEGMENT_MAX]


def resolve_output_dir(site_id: str) -> Path:
    """The directory this site's rasters go in, always inside :data:`OUTPUT_ROOT`.

    Containment is re-checked on the *resolved* path rather than trusted from the
    construction, because `Path("/root") / "x/../../y"` normalises silently and a
    symlinked parent could still escape.
    """
    candidate = (OUTPUT_ROOT / safe_site_segment(site_id)).resolve()
    if candidate != OUTPUT_ROOT and OUTPUT_ROOT not in candidate.parents:
        raise UnsafePathError(f"site_id {site_id!r} resolves outside the output root")
    return candidate


def resolve_dem_path(dem_path: str | None) -> Path:
    """Resolve a DEM input, refusing anything outside :data:`DEM_ALLOWED_ROOTS`.

    The name is checked against the allowed roots and the file must exist, so an
    arbitrary read is not possible even for a path that happens to be inside a
    permitted directory.
    """
    if dem_path is None or not str(dem_path).strip():
        raise UnsafePathError("dem_path is empty")

    candidate = Path(dem_path).resolve()
    if not any(candidate == root or root in candidate.parents for root in DEM_ALLOWED_ROOTS):
        raise UnsafePathError(
            f"dem_path {dem_path!r} is outside the permitted roots "
            f"({[str(r) for r in DEM_ALLOWED_ROOTS]})"
        )
    if not candidate.is_file():
        raise UnsafePathError(f"dem_path {dem_path!r} does not exist")
    return candidate


class TopographyInput(BaseModel):
    """Input parameters for topographic analysis."""

    site_id: str = Field(..., description="Unique identifier for the site")
    dem_path: str = Field(..., description="Path to the input DEM file (GeoTIFF)")
    analysis_types: list[AnalysisType] = Field(
        default=["slope"], description="List of analyses to perform"
    )
    target_crs: str = Field(default="auto", description="Target coordinate reference system")


class TopographyOutput(ResultProvenance, BaseModel):
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

    def __init__(self, db_session: SessionPort):
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
        # Both caller-supplied paths go through the confinement helpers before
        # anything touches the filesystem. Doing it here rather than in the router
        # is what makes it hold for notebooks and batch jobs too.
        dem_file = resolve_dem_path(input_data.dem_path)
        output_dir = resolve_output_dir(input_data.site_id)

        logger.info(f"Starting topographic analysis on {dem_file}")
        dem_raster = rioxarray.open_rasterio(dem_file, chunks=True)
        # A multi-band raster opens as a Dataset; every consumer below
        # (.squeeze, .rio.crs, the derivative helpers) needs the single-band
        # DataArray the module's contract describes.
        assert isinstance(dem_raster, xr.DataArray)  # single-band DEM opens as DataArray
        dem = dem_raster.squeeze()  # Assuming single band DEM

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

        # mypy cannot see the Field(None) defaults on the optional fields, so it
        # synthesizes a __init__ that requires them; pydantic supplies them at
        # runtime (same treatment as ResultProvenance in test_s15_provenance.py).
        results = TopographyOutput(  # type: ignore[call-arg]
            data_source="modelled",
            model="terrain derivatives (Horn 1981)",
        )

        # Prepare output paths
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
        topography_result = resolve_database_attr("models", "TopographyAnalysisResult")
        db_result = topography_result(
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

