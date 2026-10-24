"""Radiation unit contract for the HYRUE pipeline.

Defines the canonical radiation units and conversion factors used across
the weather ingestion, PAR conversion, and HYRUE biomass computation
pipelines.  All radiation values flowing into HYRUE must be expressed in
one of these canonical units before use.

Canonical energy units (per square metre per day):
    SW_MJ_M2_DAY    Shortwave radiation, MJ/m²/day
    SW_KWH_M2_DAY   Shortwave radiation, kWh/m²/day
    PAR_MJ_M2_DAY   Photosynthetically Active Radiation, MJ/m²/day
    PAR_MOL_M2_DAY  PAR, mol photons/m²/day

Canonical instantaneous power units:
    PAR_MJ_M2_S     PAR, MJ/m²/second

Derived:
    IPAR_MJ_M2_DAY  Intercepted PAR, MJ/m²/day
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RadiationUnit(StrEnum):
    """Canonical radiation units used in the HYRUE pipeline."""

    # Shortwave (total downward shortwave, 300–3000 nm approx.)
    SW_MJ_M2_DAY = "MJ/m^2/day"
    SW_KWH_M2_DAY = "kWh/m^2/day"

    # PAR (400–700 nm band)
    PAR_MJ_M2_DAY = "MJ/m^2/day"
    PAR_MOL_M2_DAY = "mol/m^2/day"
    PAR_MJ_M2_S = "MJ/m^2/s"

    # Intercepted PAR (PAR × f_IPAR)
    IPAR_MJ_M2_DAY = "MJ/m^2/day"


#: Conversion factor: 1 kWh = 3.6 MJ
KWH_TO_MJ = 3.6

#: Default PAR fraction of shortwave (0.5 = ~50% of shortwave is PAR)
#: Source: Monteith & Unsworth (2013), FAO-56 default in absence of spectral data.
#: Status: estimated — a calibration-grade assumption, NOT a measured parameter.
DEFAULT_PAR_FRACTION = 0.5

#: Approximate energy per mole of PAR photons (400–700 nm).
#: ~0.217 MJ/mol for mid-red wavelengths; varies with spectral distribution.
#: Status: estimated — used only when converting between energy and photon units.
MJ_PER_MOL_PAR = 0.217


@dataclass
class ParConversionSpec:
    """Specification of how a shortwave-to-PAR conversion was performed.

    Captures the coefficient, method, provenance, and scientific status so
    that every derived PAR value is traceable.

    The conversion is a simple multiplication:

        PAR = frac_par × SW_down

    where ``frac_par`` is the fraction of total shortwave downward radiation
    that falls within the 400–700 nm PAR band.
    """

    frac_par: float
    method: str
    status: str = "documented"
    coeff_source: str = ""


def kwh_to_mj(kwh_value: float) -> float:
    """Convert kWh/m²/day to MJ/m²/day."""
    return kwh_value * KWH_TO_MJ


def mj_to_kwh(mj_value: float) -> float:
    """Convert MJ/m²/day to kWh/m²/day."""
    return mj_value / KWH_TO_MJ


def par_energy_to_mol(
    par_mj_m2_day: float, mj_per_mol: float = MJ_PER_MOL_PAR
) -> float:
    """Convert PAR energy (MJ/m²/day) to PAR photon flux (mol/m²/day).

    Uses the Approximate energy per mole of PAR photons.  The exact value
    depends on spectral distribution within the 400–700 nm band.
    """
    if mj_per_mol <= 0:
        raise ValueError("mj_per_mol must be positive")
    return par_mj_m2_day / mj_per_mol


def par_mol_to_energy(
    par_mol_m2_day: float, mj_per_mol: float = MJ_PER_MOL_PAR
) -> float:
    """Convert PAR photon flux (mol/m²/day) to PAR energy (MJ/m²/day)."""
    if mj_per_mol <= 0:
        raise ValueError("mj_per_mol must be positive")
    return par_mol_m2_day * mj_per_mol


def shortwave_to_par(
    sw_value: float,
    sw_unit: str,
    par_fraction: float = DEFAULT_PAR_FRACTION,
    already_par: bool = False,
) -> tuple[float, ParConversionSpec | None]:
    """Convert shortwave radiation to PAR energy (MJ/m²/day).

    Applies the PAR fraction (default 0.5) after normalising the input
    shortwave value to MJ/m²/day.

    Raises ValueError for unrecognised units — callers must not silently
    assume a unit.

    Args:
        sw_value: Daily shortwave downward radiation in ``sw_unit``, or daily
            PAR if ``already_par=True``.
        sw_unit: Unit of ``sw_value``.
        par_fraction: Fraction of shortwave that is PAR (default 0.5).
        already_par: If True, ``sw_value`` is already PAR — no conversion
            is applied. Returns the value unchanged with a documented spec.

    Returns:
        Tuple of (par_value_mj_m2_day, spec_or_none).
        If ``already_par`` is True, returns the value and a documented spec
        with frac_par=1.0.
    """
    sw_norm = (
        sw_unit.strip().lower().replace(" ", "").replace("·", "").replace("^", "")
    )
    sw_norm = sw_norm.replace("²", "2")

    if sw_norm in ("mj/m2/day", "mj/m^2/day", "mj·m^-2·day^-1"):
        sw_mj = sw_value
    elif sw_norm in (
        "kw-hr/m2/day", "kwhr/m2/day", "kwh/m2/day",
        "kw·h/m²/day", "kwhr/m2day",
    ):
        sw_mj = kwh_to_mj(sw_value)
    else:
        raise ValueError(
            f"Unrecognised shortwave unit '{sw_unit}'. "
            f"Supported: '{RadiationUnit.SW_MJ_M2_DAY}', "
            f"'{RadiationUnit.SW_KWH_M2_DAY}'."
        )

    if par_fraction <= 0 or par_fraction > 1:
        raise ValueError("par_fraction must be in (0, 1]")

    if already_par:
        return sw_mj, ParConversionSpec(
            frac_par=1.0,
            method="no conversion: input already identified as PAR",
            status="documented",
            coeff_source="none",
        )

    return sw_mj * par_fraction, ParConversionSpec(
        frac_par=par_fraction,
        method=f"PAR = {par_fraction} × shortwave",
        status="estimated",
        coeff_source="standard_agricultural_meteorology_assumption",
    )


__all__ = [
    "RadiationUnit",
    "ParConversionSpec",
    "KWH_TO_MJ",
    "DEFAULT_PAR_FRACTION",
    "MJ_PER_MOL_PAR",
    "kwh_to_mj",
    "mj_to_kwh",
    "par_energy_to_mol",
    "par_mol_to_energy",
    "shortwave_to_par",
]
