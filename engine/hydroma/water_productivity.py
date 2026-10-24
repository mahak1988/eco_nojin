"""Water productivity (indicator ENO_WP_001) — FAO WaPOR definition.

Water productivity is the yield per unit of water consumed, expressed in
kg/m3 (FAO Water Productivity Open Portal, WaPOR)::

    WP = Y / ET

with ``Y`` the yield in kg/ha and ``ET`` the water consumed expressed as
a volume. The unit bridge between a depth in mm and a volume over one
hectare is verified and derived here, not assumed::

    1 mm over 1 ha = 0.001 m x 10 000 m2 = 10 m3

so with ``M3_PER_MM_PER_HA = 10.0`` (exactly the product above)::

    WP [kg/m3] = Y [kg/ha] / (ET [mm] x 10.0)

Equivalently, using the exported multiplier::

    WP [kg/m3] = Y [kg/ha] x WP_KG_PER_M3_PER_MM_HA / ET [mm]

Worked example from the FAO WaPOR convention: a yield of 5000 kg/ha
consuming 500 mm of ET equals 500 mm x 10 m3 = 5000 m3, hence
5000 kg / 5000 m3 = 1.0 kg/m3.

Reference: FAO WaPOR (Water Productivity database),
https://www.fao.org/land-water/databases-and-software/wapor/en

Indicator: ``indicators/ENO_WP_001.yaml``.
"""

from __future__ import annotations

from math import isfinite

_MM_TO_M = 0.001
_M2_PER_HA = 10000.0

#: Volume of a 1 mm depth over one hectare, in m3: 0.001 m x 10 000 m2.
M3_PER_MM_PER_HA = _MM_TO_M * _M2_PER_HA

#: Multiplier converting (yield kg/ha, ET mm) to kg/m3: WP = Y / (ET * 10).
WP_KG_PER_M3_PER_MM_HA = 1.0 / M3_PER_MM_PER_HA


def _require_non_negative(value: float, name: str) -> float:
    number = float(value)
    if not isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be a finite value >= 0, got {value!r}")
    return number


def _require_positive(value: float, name: str) -> float:
    number = float(value)
    if not isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be a finite value > 0, got {value!r}")
    return number


def water_productivity_from_m3(yield_kg_per_ha: float, et_m3_per_ha: float) -> float:
    """Water productivity from a yield and a water volume.

    Parameters
    ----------
    yield_kg_per_ha
        Yield in kg/ha; must be finite and ``>= 0``.
    et_m3_per_ha
        Evapotranspired (consumed) water in m3/ha; must be finite and
        strictly positive.

    Returns
    -------
    float
        Water productivity in kg/m3, ``WP = Y / ET``.

    Raises
    ------
    ValueError
        If the yield is negative or non-finite, or the volume is zero,
        negative or non-finite.
    """
    yield_value = _require_non_negative(yield_kg_per_ha, "yield_kg_per_ha")
    volume_value = _require_positive(et_m3_per_ha, "et_m3_per_ha")
    return yield_value / volume_value


def water_productivity(yield_kg_per_ha: float, et_mm: float) -> float:
    """Water productivity per the FAO WaPOR definition, ``WP = Y / ET``.

    Parameters
    ----------
    yield_kg_per_ha
        Yield in kg/ha; must be finite and ``>= 0``.
    et_mm
        Evapotranspired (consumed) water depth in mm; must be finite
        and strictly positive. The depth is converted to a volume with
        the verified constant ``1 mm over 1 ha = 10 m3``, so
        ``WP [kg/m3] = Y / (ET x 10.0)``.

    Returns
    -------
    float
        Water productivity in kg/m3.

    Raises
    ------
    ValueError
        If the yield is negative or non-finite, or ET is zero, negative
        or non-finite.
    """
    yield_value = _require_non_negative(yield_kg_per_ha, "yield_kg_per_ha")
    depth_value = _require_positive(et_mm, "et_mm")
    return water_productivity_from_m3(yield_value, depth_value * M3_PER_MM_PER_HA)
