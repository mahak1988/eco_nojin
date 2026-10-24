"""pint-based unit audit -- the audit half of external-alignment item X-1.

This module is intentionally dependency-light (standard library + pint only) so it
stays importable anywhere, including outside the engine process. It builds a
``pint.UnitRegistry`` extended with the six domain units that do not parse in a
stock registry, an alias table for the engine's raw unit strings, and three
behaviour-preserving helpers: ``parse_unit``, ``check_compatible`` and ``audit``.

Wiring this audit into the gateway is a SEPARATE, LATER step. Calling ``audit``
from ``_normalize_inputs`` (see engine/gateway/__init__.py:2008-2022) must record
problems WITHOUT changing the multiplicative unit path or any computed result,
respecting the plan's brake-2 constraint (no equation, public-API, unit or schema
change without explicit mandate). Conversion adoption is itself a further,
mandated step; this module only audits, it never rescales.
"""

import pint


class UnknownUnitError(Exception):
    """Raised by ``parse_unit`` for a string that is neither a known unit nor a
    declared alias/placeholder token."""


UNIT_REGISTRY = pint.UnitRegistry()
UNIT_REGISTRY.define("person = count")
UNIT_REGISTRY.define("year = 365.25 * day")
UNIT_REGISTRY.define("FTE = count")
UNIT_REGISTRY.define("curve_number_points = count")
UNIT_REGISTRY.define("fraction_of_TAW = count")
UNIT_REGISTRY.define("fraction_of_consumption = count")

ALIASES = {
    "kg per person per year": "kg/(person*year)",
    "kg/m3": "kg/m**3",
    "FTE": "FTE",
    "curve number points": "curve_number_points",
    "fraction of TAW": "fraction_of_TAW",
    "fraction of consumption": "fraction_of_consumption",
    "unknown": "dimensionless",
    "si": "dimensionless",
    "none": "dimensionless",
    "": "dimensionless",
}

_INTERVAL_UNITS = {
    "degC": "delta_degC",
    "degree_Celsius": "delta_degC",
    "delta_degC": "delta_degC",
    "delta_degree_Celsius": "delta_degree_Celsius",
    "degF": "delta_degF",
    "degree_Fahrenheit": "delta_degF",
    "delta_degF": "delta_degF",
}


def parse_unit(s: str) -> pint.Unit:
    """Return the ``pint.Unit`` for ``s`` (after alias substitution).

    Raises ``UnknownUnitError`` for genuinely unknown strings; never returns a
    partial or silently-wrong unit for a bogus token.
    """
    expr = ALIASES.get(s, s)
    try:
        return UNIT_REGISTRY.Unit(expr)
    except (pint.PintError, ValueError, TypeError, ZeroDivisionError) as exc:
        raise UnknownUnitError(f"unknown unit {s!r}") from exc


def check_compatible(unit_a: str, unit_b: str) -> bool:
    """True iff both strings parse and their units are dimensionally compatible.

    Returns ``False`` (never raises) if either side is unparseable.
    """
    try:
        parsed_a = parse_unit(unit_a)
        parsed_b = parse_unit(unit_b)
    except UnknownUnitError:
        return False
    return bool(parsed_a.is_compatible_with(parsed_b))


def audit(specs: dict[str, str]) -> list[str]:
    """Return one problem string per unparseable named unit (naming its key)."""
    problems: list[str] = []
    for key, unit in specs.items():
        try:
            parse_unit(unit)
        except UnknownUnitError:
            problems.append(f"{key}: unparseable unit {unit!r}")
    return problems


def convert(value: float, from_unit: str, to_unit: str) -> float:
    """Convert ``value`` from one unit to another using ``UNIT_REGISTRY``.

    Offset temperatures convert absolutely (``degC`` -> ``K``); a temperature
    difference between an offset unit and its delta twin (``degC`` ->
    ``delta_degC``) falls back to pint's interval interpretation, which is the
    only legal way to express that difference.
    """
    src = ALIASES.get(from_unit, from_unit)
    dst = ALIASES.get(to_unit, to_unit)
    try:
        quantity = UNIT_REGISTRY.Quantity(value, src).to(dst)
    except (pint.DimensionalityError, pint.OffsetUnitCalculusError):
        from_expr = _INTERVAL_UNITS.get(src, src)
        to_expr = _INTERVAL_UNITS.get(dst, dst)
        quantity = UNIT_REGISTRY.Quantity(value, from_expr).to(to_expr)
    return float(quantity.magnitude)
