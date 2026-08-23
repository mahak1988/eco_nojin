"""Utility functions for topographic calculations using xarray-spatial."""
import xarray as xr
try:
    import xrspatial
except ImportError:
    xrspatial = None
    print("Warning: xrspatial not found. Some topographic functions may not work.")


def calculate_slope_aspect_xarray(dem: xr.DataArray) -> tuple[xr.DataArray, xr.DataArray]:
    """Calculate slope and aspect using xarray-spatial."""
    if xrspatial is None:
        raise ImportError("xarray-spatial is required for this function.")
    slope_radians = xrspatial.slope(dem)
    aspect_radians = xrspatial.aspect(dem)

    # Convert radians to degrees
    slope_degrees = slope_radians * (180.0 / 3.14159)
    aspect_degrees = aspect_radians * (180.0 / 3.14159)
    # Adjust aspect to compass degrees (0-360)
    aspect_compass = ((90.0 - aspect_degrees) + 360.0) % 360.0

    return slope_degrees, aspect_compass

def calculate_curvature_xarray(dem: xr.DataArray) -> xr.DataArray:
    """Calculate curvature using xarray-spatial."""
    if xrspatial is None:
        raise ImportError("xarray-spatial is required for this function.")
    return xrspatial.curvature(dem)

def calculate_flow_direction_xarray(dem: xr.DataArray) -> xr.DataArray:
    """Calculate flow direction using xarray-spatial (D8 algorithm)."""
    if xrspatial is None:
        raise ImportError("xarray-spatial is required for this function.")
    return xrspatial.flow_direction(dem)

def calculate_flow_accumulation_xarray(flow_direction: xr.DataArray) -> xr.DataArray:
    """Calculate flow accumulation using xarray-spatial."""
    if xrspatial is None:
        raise ImportError("xarray-spatial is required for this function.")
    return xrspatial.flow_accumulation(flow_direction)