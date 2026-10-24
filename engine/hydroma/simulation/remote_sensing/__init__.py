"""Satellite reflectance package.

Modules:
    satellite_source      - SatelliteSource abstractions (Sentinel-2, Landsat)
    reflectance_quality   - Cloud masking, valid-pixel fraction, quality control
    spectral_indices      - NDMI and related spectral indices
    temporal_composite    - Temporal compositing and interpolation
    satellite_cache       - Disk cache for satellite acquisitions

Note: submodules are resolved lazily via ``__getattr__`` to avoid
re-entrant import cycles (``satellite_source`` <-> ``satellite_cache``).
"""

from __future__ import annotations

import importlib
from typing import Any

#: Public name -> submodule that defines it.
_EXPORTS: dict[str, str] = {
    "BandReflectance": "satellite_source",
    "LandsatC2L2Source": "satellite_source",
    "ReflectanceAcquisition": "satellite_source",
    "ReflectanceTimeSeries": "satellite_source",
    "SatelliteSource": "satellite_source",
    "Sentinel2Source": "satellite_source",
    "default_source_for": "satellite_source",
    "ndmi_from_reflectance": "satellite_source",
    "validate_reflectance_range": "satellite_source",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Resolve a public name by importing its defining submodule on demand."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_EXPORTS))
