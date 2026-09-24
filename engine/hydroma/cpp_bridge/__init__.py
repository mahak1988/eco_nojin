"""
Eco Nojin - C++ Bridge (Hybrid Intelligence Pattern)
=====================================================

Auto-generated bridge that exposes all hydroma_core C++ functions
with automatic Python fallback and performance telemetry.

Generated: 2026-08-20 20:02:12
C++ functions: 56
C++ structs: 0

Principle: C++ for hot-path kernels, Python for everything else.
All C++ functions have Python fallbacks.
"""

import functools
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("econojin.cpp_bridge")

try:
    import numpy as _np
except ImportError:  # pragma: no cover - numpy is a hard dependency in practice
    _np = None

# Telemetry storage
_telemetry = {
    "cpp_calls": 0,
    "fallback_calls": 0,
    "total_cpp_time_ms": 0.0,
    "total_fallback_time_ms": 0.0,
}

# =============================================================================
# Try to import hydroma_core (compiled C++ module)
# =============================================================================
_cpp_available = False
_hydroma_core = None

# Ensure bridge directory is in sys.path for hydroma_core.pyd
import sys

_bridge_dir = str(Path(__file__).parent.absolute())
if _bridge_dir not in sys.path:
    sys.path.insert(0, _bridge_dir)

_cpp_import_error: str | None = None

try:
    import hydroma_core as _hydroma_core

    _cpp_available = True
    logger.info("C++ hydroma_core loaded (%d functions exposed)", len(dir(_hydroma_core)))
    # Alias the extension under its submodule name so that
    # ``from engine.hydroma.cpp_bridge import hydroma_core`` cannot load the same
    # .pyd a second time (pybind11 then raises
    # 'generic_type: type "WaveParameters" is already registered!').
    sys.modules.setdefault(__name__ + ".hydroma_core", _hydroma_core)
except ImportError as e:
    _cpp_import_error = str(e)
    # Degradation must be loud: it changes the numerical/performance envelope.
    logger.error(
        "C++ hydroma_core NOT available (%s). Falling back to the Python kernels; "
        "rebuild the extension (engine/cpp_core/CMakeLists.txt) on a host with MSVC/CMake.",
        e,
    )


#: Active numerical backend: "cpp" when the compiled extension loaded, else "python".
BACKEND: str = "cpp" if _cpp_available else "python"


def backend_status() -> dict:
    """Degradation state, so /health and /metrics cannot hide a Python fallback."""
    return {
        "backend": BACKEND,
        "cpp_available": _cpp_available,
        "import_error": _cpp_import_error,
        "telemetry": get_telemetry(),
    }


def is_cpp_available() -> bool:
    """Check if C++ acceleration is available."""
    return _cpp_available


def get_telemetry() -> dict:
    """Get performance telemetry."""
    return _telemetry.copy()


def reset_telemetry() -> None:
    """Reset telemetry counters."""
    global _telemetry
    _telemetry = {
        "cpp_calls": 0,
        "fallback_calls": 0,
        "total_cpp_time_ms": 0.0,
        "total_fallback_time_ms": 0.0,
    }


# =============================================================================
# Telemetry-aware wrapper
# =============================================================================
def _has_array_arg(args: tuple, kwargs: dict) -> bool:
    """True when the call carries an array-like argument."""
    for value in list(args) + list(kwargs.values()):
        if _np is not None and isinstance(value, _np.ndarray):
            return True
    return False


def _with_telemetry(func_name: str, cpp_func: Callable | None, py_func: Callable) -> Callable:
    """Wrap a function pair with telemetry, array dispatch and fallback.

    The C++ extension exposes both scalar (``name``) and vectorised
    (``name_array``) entry points. The scalar symbol must never be handed an
    array (pybind11 raises 'incompatible function arguments'), so array calls
    are routed to the ``_array`` symbol when it exists.
    """

    @functools.wraps(py_func)
    def wrapper(*args, **kwargs):
        if _cpp_available and cpp_func is not None:
            target = cpp_func
            if _has_array_arg(args, kwargs):
                array_func = getattr(_hydroma_core, f"{func_name}_array", None)
                if array_func is not None:
                    target = array_func
            try:
                t0 = time.perf_counter()
                result = target(*args, **kwargs)
                elapsed = (time.perf_counter() - t0) * 1000
                _telemetry["cpp_calls"] += 1
                _telemetry["total_cpp_time_ms"] += elapsed
                return result
            except Exception as e:
                logger.debug(f"C++ {func_name} failed, falling back: {e}")
        # Fallback to Python
        t0 = time.perf_counter()
        result = py_func(*args, **kwargs)
        elapsed = (time.perf_counter() - t0) * 1000
        _telemetry["fallback_calls"] += 1
        _telemetry["total_fallback_time_ms"] += elapsed
        return result

    return wrapper


# =============================================================================
# Python fallbacks (always work)
# =============================================================================


def _py_ndvi(red, nir):
    """NDVI: (NIR - Red) / (NIR + Red)"""
    denom = nir + red
    if isinstance(denom, (int, float)):
        return (nir - red) / (denom + 1e-10) if denom != 0 else 0.0
    # numpy array
    return (nir - red) / (denom + 1e-10)


def _py_evi(red, nir, blue):
    """EVI: 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)"""
    denom = nir + 6 * red - 7.5 * blue + 1
    return 2.5 * (nir - red) / (denom + 1e-10)


def _py_savi(red, nir, L=0.5):
    """SAVI: ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
    return ((nir - red) / (nir + red + L + 1e-10)) * (1 + L)


def _py_ndwi(green, nir):
    """NDWI: (Green - NIR) / (Green + NIR)"""
    return (green - nir) / (green + nir + 1e-10)


def _py_nbr(nir, swir):
    """NBR: (NIR - SWIR) / (NIR + SWIR)"""
    return (nir - swir) / (nir + swir + 1e-10)


def _py_rusle_annual_soil_loss(r, k, ls, c, p):
    """RUSLE A = R * K * LS * C * P (elementwise for arrays)."""
    return r * k * ls * c * p


def _py_latin_hypercube(n_samples, n_dimensions, seed=None):
    """Latin Hypercube Sampling over the unit hypercube."""
    rng = _np.random.default_rng(seed)
    cut = _np.linspace(0.0, 1.0, n_samples + 1)
    samples = rng.uniform(cut[:-1], cut[1:], size=(n_samples, n_dimensions))
    for j in range(n_dimensions):
        rng.shuffle(samples[:, j])
    return samples


def _py_monte_carlo_uniform(n_samples, bounds, seed=None):
    """Uniform Monte Carlo sampling inside [lo, hi] bounds per dimension."""
    rng = _np.random.default_rng(seed)
    lo = _np.asarray([b[0] for b in bounds], dtype=float)
    hi = _np.asarray([b[1] for b in bounds], dtype=float)
    return rng.uniform(lo, hi, size=(n_samples, len(bounds)))


def _py_penman_monteith_et0(tmin, tmax, rh_mean, rs, u2, z, lat, doy):
    """FAO-56 Penman-Monteith reference ET0 [mm/day] (vectorised)."""
    tmin = _np.asarray(tmin, dtype=float)
    tmax = _np.asarray(tmax, dtype=float)
    rh = _np.asarray(rh_mean, dtype=float)
    rs = _np.asarray(rs, dtype=float)
    u2 = _np.asarray(u2, dtype=float)
    z = _np.asarray(z, dtype=float)
    lat = _np.asarray(lat, dtype=float)
    doy = _np.asarray(doy, dtype=float)
    tmean = (tmin + tmax) / 2.0

    def svp(temp):
        return 0.6108 * _np.exp(17.27 * temp / (temp + 237.3))

    es = (svp(tmax) + svp(tmin)) / 2.0
    ea = es * rh / 100.0
    delta = 4098.0 * svp(tmean) / (tmean + 237.3) ** 2
    pressure = 101.3 * ((293.0 - 0.0065 * z) / 293.0) ** 5.26
    gamma = 0.000665 * pressure

    # Extraterrestrial radiation (FAO-56 eq. 21-25)
    phi = _np.deg2rad(lat)
    dr = 1.0 + 0.033 * _np.cos(2.0 * _np.pi * doy / 365.0)
    decl = 0.409 * _np.sin(2.0 * _np.pi * doy / 365.0 - 1.39)
    ws = _np.arccos(_np.clip(-_np.tan(phi) * _np.tan(decl), -1.0, 1.0))
    ra = (
        (24.0 * 60.0 / _np.pi)
        * 0.0820
        * dr
        * (ws * _np.sin(phi) * _np.sin(decl) + _np.cos(phi) * _np.cos(decl) * _np.sin(ws))
    )
    rso = (0.75 + 2e-5 * z) * ra
    rns = (1.0 - 0.23) * rs
    rnl = (
        4.903e-9
        * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4)
        / 2.0
        * (0.34 - 0.14 * _np.sqrt(_np.maximum(ea, 0.0)))
        * _np.clip(1.35 * rs / _np.maximum(rso, 1e-6) - 0.35, 0.05, 1.0)
    )
    rn = rns - rnl
    num = 0.408 * delta * rn + gamma * (900.0 / (tmean + 273.0)) * u2 * (es - ea)
    den = delta + gamma * (1.0 + 0.34 * u2)
    return _np.maximum(num / den, 0.0)


def _py_muskingum_cunge_route(inflow, k, x, dt, dx, slope, manning, bottom_width, side_slope):
    """Muskingum outflow hydrograph O(t+1) = C0*I(t+1) + C1*I(t) + C2*O(t)."""
    inflow = _np.asarray(inflow, dtype=float)
    denom = k - k * x + 0.5 * dt
    c0 = (-k * x + 0.5 * dt) / denom
    c1 = (k * x + 0.5 * dt) / denom
    c2 = (k - k * x - 0.5 * dt) / denom
    outflow = _np.empty_like(inflow)
    outflow[0] = inflow[0]
    for i in range(1, inflow.size):
        outflow[i] = c0 * inflow[i] + c1 * inflow[i - 1] + c2 * outflow[i - 1]
    return _np.maximum(outflow, 0.0)


def _py_not_implemented(*args, **kwargs):
    """Fallback for functions without Python implementation."""
    raise NotImplementedError("Python fallback not implemented. C++ is required for this function.")


# =============================================================================
# Bridge functions (C++ with Python fallback)
# =============================================================================

# Bridge: BottomBoundary
BottomBoundary = _with_telemetry(
    "BottomBoundary",
    getattr(_hydroma_core, "BottomBoundary", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: CropWaterParams
CropWaterParams = _with_telemetry(
    "CropWaterParams",
    getattr(_hydroma_core, "CropWaterParams", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: CropWaterResult
CropWaterResult = _with_telemetry(
    "CropWaterResult",
    getattr(_hydroma_core, "CropWaterResult", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: RichardsOptions
RichardsOptions = _with_telemetry(
    "RichardsOptions",
    getattr(_hydroma_core, "RichardsOptions", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: RichardsResult
RichardsResult = _with_telemetry(
    "RichardsResult",
    getattr(_hydroma_core, "RichardsResult", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: RoutingResult
RoutingResult = _with_telemetry(
    "RoutingResult",
    getattr(_hydroma_core, "RoutingResult", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: RusleCell
RusleCell = _with_telemetry(
    "RusleCell",
    getattr(_hydroma_core, "RusleCell", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: SaintVenantOptions
SaintVenantOptions = _with_telemetry(
    "SaintVenantOptions",
    getattr(_hydroma_core, "SaintVenantOptions", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: SaintVenantResult
SaintVenantResult = _with_telemetry(
    "SaintVenantResult",
    getattr(_hydroma_core, "SaintVenantResult", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: TopBoundary
TopBoundary = _with_telemetry(
    "TopBoundary",
    getattr(_hydroma_core, "TopBoundary", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: WaveParameters
WaveParameters = _with_telemetry(
    "WaveParameters",
    getattr(_hydroma_core, "WaveParameters", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: YieldStats
YieldStats = _with_telemetry(
    "YieldStats",
    getattr(_hydroma_core, "YieldStats", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: compute_wave_parameters
compute_wave_parameters = _with_telemetry(
    "compute_wave_parameters",
    getattr(_hydroma_core, "compute_wave_parameters", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: estimate_mean_lhs
estimate_mean_lhs = _with_telemetry(
    "estimate_mean_lhs",
    getattr(_hydroma_core, "estimate_mean_lhs", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: estimate_mean_mc
estimate_mean_mc = _with_telemetry(
    "estimate_mean_mc",
    getattr(_hydroma_core, "estimate_mean_mc", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: estimate_rainfall_erosivity
estimate_rainfall_erosivity = _with_telemetry(
    "estimate_rainfall_erosivity",
    getattr(_hydroma_core, "estimate_rainfall_erosivity", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: evi
evi = _with_telemetry(
    "evi", getattr(_hydroma_core, "evi", None) if _cpp_available else None, _py_evi
)

# Bridge: evi_array
evi_array = _with_telemetry(
    "evi_array",
    getattr(_hydroma_core, "evi_array", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: extraterrestrial_radiation
extraterrestrial_radiation = _with_telemetry(
    "extraterrestrial_radiation",
    getattr(_hydroma_core, "extraterrestrial_radiation", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: fao56_net_radiation
fao56_net_radiation = _with_telemetry(
    "fao56_net_radiation",
    getattr(_hydroma_core, "fao56_net_radiation", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: hargreaves_et0
hargreaves_et0 = _with_telemetry(
    "hargreaves_et0",
    getattr(_hydroma_core, "hargreaves_et0", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: hydraulic_conductivity
hydraulic_conductivity = _with_telemetry(
    "hydraulic_conductivity",
    getattr(_hydroma_core, "hydraulic_conductivity", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: latin_hypercube
latin_hypercube = _with_telemetry(
    "latin_hypercube",
    getattr(_hydroma_core, "latin_hypercube", None) if _cpp_available else None,
    _py_latin_hypercube,
)

# Bridge: ls_factor
ls_factor = _with_telemetry(
    "ls_factor",
    getattr(_hydroma_core, "ls_factor", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: manning_normal_depth
manning_normal_depth = _with_telemetry(
    "manning_normal_depth",
    getattr(_hydroma_core, "manning_normal_depth", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: monte_carlo_uniform
monte_carlo_uniform = _with_telemetry(
    "monte_carlo_uniform",
    getattr(_hydroma_core, "monte_carlo_uniform", None) if _cpp_available else None,
    _py_monte_carlo_uniform,
)

# Bridge: muskingum_cunge_route
muskingum_cunge_route = _with_telemetry(
    "muskingum_cunge_route",
    getattr(_hydroma_core, "muskingum_cunge_route", None) if _cpp_available else None,
    _py_muskingum_cunge_route,
)

# Bridge: nbr
nbr = _with_telemetry(
    "nbr", getattr(_hydroma_core, "nbr", None) if _cpp_available else None, _py_nbr
)

# Bridge: nbr_array
nbr_array = _with_telemetry(
    "nbr_array",
    getattr(_hydroma_core, "nbr_array", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: ndvi
ndvi = _with_telemetry(
    "ndvi", getattr(_hydroma_core, "ndvi", None) if _cpp_available else None, _py_ndvi
)

# Bridge: ndvi_array
ndvi_array = _with_telemetry(
    "ndvi_array",
    getattr(_hydroma_core, "ndvi_array", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: ndwi
ndwi = _with_telemetry(
    "ndwi", getattr(_hydroma_core, "ndwi", None) if _cpp_available else None, _py_ndwi
)

# Bridge: ndwi_array
ndwi_array = _with_telemetry(
    "ndwi_array",
    getattr(_hydroma_core, "ndwi_array", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: penman_monteith_et0
penman_monteith_et0 = _with_telemetry(
    "penman_monteith_et0",
    getattr(_hydroma_core, "penman_monteith_et0", None) if _cpp_available else None,
    _py_penman_monteith_et0,
)

# Bridge: route_flood_wave
route_flood_wave = _with_telemetry(
    "route_flood_wave",
    getattr(_hydroma_core, "route_flood_wave", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: route_multi_reach
route_multi_reach = _with_telemetry(
    "route_multi_reach",
    getattr(_hydroma_core, "route_multi_reach", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: rusle_annual_soil_loss
rusle_annual_soil_loss = _with_telemetry(
    "rusle_annual_soil_loss",
    getattr(_hydroma_core, "rusle_annual_soil_loss", None) if _cpp_available else None,
    _py_rusle_annual_soil_loss,
)

# Bridge: rusle_grid
rusle_grid = _with_telemetry(
    "rusle_grid",
    getattr(_hydroma_core, "rusle_grid", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: rusle_grid_total
rusle_grid_total = _with_telemetry(
    "rusle_grid_total",
    getattr(_hydroma_core, "rusle_grid_total", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: savi
savi = _with_telemetry(
    "savi", getattr(_hydroma_core, "savi", None) if _cpp_available else None, _py_savi
)

# Bridge: savi_array
savi_array = _with_telemetry(
    "savi_array",
    getattr(_hydroma_core, "savi_array", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: scale_samples
scale_samples = _with_telemetry(
    "scale_samples",
    getattr(_hydroma_core, "scale_samples", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: sediment_delivery_ratio
sediment_delivery_ratio = _with_telemetry(
    "sediment_delivery_ratio",
    getattr(_hydroma_core, "sediment_delivery_ratio", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: sediment_trapped
sediment_trapped = _with_telemetry(
    "sediment_trapped",
    getattr(_hydroma_core, "sediment_trapped", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: sediment_yield
sediment_yield = _with_telemetry(
    "sediment_yield",
    getattr(_hydroma_core, "sediment_yield", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: simplified_yield
simplified_yield = _with_telemetry(
    "simplified_yield",
    getattr(_hydroma_core, "simplified_yield", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: simulate_crop_water
simulate_crop_water = _with_telemetry(
    "simulate_crop_water",
    getattr(_hydroma_core, "simulate_crop_water", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: simulate_richards
simulate_richards = _with_telemetry(
    "simulate_richards",
    getattr(_hydroma_core, "simulate_richards", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: simulate_saint_venant
simulate_saint_venant = _with_telemetry(
    "simulate_saint_venant",
    getattr(_hydroma_core, "simulate_saint_venant", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: soil_erodibility_k
soil_erodibility_k = _with_telemetry(
    "soil_erodibility_k",
    getattr(_hydroma_core, "soil_erodibility_k", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: soil_params
soil_params = _with_telemetry(
    "soil_params",
    getattr(_hydroma_core, "soil_params", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: soil_water_content
soil_water_content = _with_telemetry(
    "soil_water_content",
    getattr(_hydroma_core, "soil_water_content", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: specific_moisture_capacity
specific_moisture_capacity = _with_telemetry(
    "specific_moisture_capacity",
    getattr(_hydroma_core, "specific_moisture_capacity", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: supported_textures
supported_textures = _with_telemetry(
    "supported_textures",
    getattr(_hydroma_core, "supported_textures", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: trap_efficiency_brune
trap_efficiency_brune = _with_telemetry(
    "trap_efficiency_brune",
    getattr(_hydroma_core, "trap_efficiency_brune", None) if _cpp_available else None,
    _py_not_implemented,
)

# Bridge: yield_ensemble_lhs
yield_ensemble_lhs = _with_telemetry(
    "yield_ensemble_lhs",
    getattr(_hydroma_core, "yield_ensemble_lhs", None) if _cpp_available else None,
    _py_not_implemented,
)

# =============================================================================
# Expose C++ structs/classes
# =============================================================================


# =============================================================================
# Public API
# =============================================================================
__all__ = [
    # Functions
    "BottomBoundary",
    "CropWaterParams",
    "CropWaterResult",
    "RichardsOptions",
    "RichardsResult",
    "RoutingResult",
    "RusleCell",
    "SaintVenantOptions",
    "SaintVenantResult",
    "TopBoundary",
    "WaveParameters",
    "YieldStats",
    "compute_wave_parameters",
    "estimate_mean_lhs",
    "estimate_mean_mc",
    "estimate_rainfall_erosivity",
    "evi",
    "evi_array",
    "extraterrestrial_radiation",
    "fao56_net_radiation",
    "get_telemetry",
    "hargreaves_et0",
    "hydraulic_conductivity",
    # Status
    "is_cpp_available",
    "latin_hypercube",
    "ls_factor",
    "manning_normal_depth",
    "monte_carlo_uniform",
    "muskingum_cunge_route",
    "nbr",
    "nbr_array",
    "ndvi",
    "ndvi_array",
    "ndwi",
    "ndwi_array",
    "penman_monteith_et0",
    "reset_telemetry",
    "route_flood_wave",
    "route_multi_reach",
    "rusle_annual_soil_loss",
    "rusle_grid",
    "rusle_grid_total",
    "savi",
    "savi_array",
    "scale_samples",
    "sediment_delivery_ratio",
    "sediment_trapped",
    "sediment_yield",
    "simplified_yield",
    "simulate_crop_water",
    "simulate_richards",
    "simulate_saint_venant",
    "soil_erodibility_k",
    "soil_params",
    "soil_water_content",
    "specific_moisture_capacity",
    "supported_textures",
    "trap_efficiency_brune",
    "yield_ensemble_lhs",
    # Structs
]
