"""Single source of the van Genuchten parameter table.

This module lives in `engine/data` rather than in `engine/hydroma/soil` on
purpose. A loader inside the soil package would make `import
engine.hydroma.soil.soil_table` execute `engine/hydroma/soil/__init__.py`,
which pulls in the whole hydroma package, the database hub and an HTTP client.
The compiled and Numba backends must be able to read the table without that, so
the data module is kept outside the package that consumes it.

Why this module exists
----------------------
Before consolidation the table existed in four places with three different
answers:

* ``soil/physics.py`` — 12 textures, theta_s dataset A, Ks in cm/day
* ``cpp_bridge/soil_physics_fast.py`` — 7 textures, dataset A, Ks in cm/hr
* ``cpp_core/src/soil.cpp`` — 7 textures, dataset A, Ks in cm/hr
* ``land/integration/soil_integrator.py`` — 12 textures, dataset **B**, no Ks

Clay conductivity was 4.80 cm/day in one copy and 2.88 in two others, and the
``theta_s`` column differed in every row between the two Python tables. One
source of truth removes the ambiguity about *where the answer lives*. It does
not settle *what the answer is*; the unresolved conflicts are recorded in
``engine/data/SOIL_TABLE_CONFLICTS.md`` and flagged per row in the CSV.

Provenance
----------
The ``provenance`` column reads *design assumption* and the former Carsel &
Parrish (1988) attribution is withdrawn. The table violates the physical
monotonicity of hydraulic conductivity in texture fineness at two rows, no copy
of the cited publication exists in the repository, and the values appear in no
data file. Under the project rule that anything not traceable is either deleted
or labelled, labelling is the action that does not invent a number.

Units
-----
``ks_cm_per_day`` is the canonical unit. The C++ table has historically been
cm/hr, so :func:`load_table_ks_cm_per_hour` converts. That conversion is the
only difference between the two columns for six of the seven shared rows.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Final

from engine.data.physics_guard import warn_if_disputed

#: Location of the table. Resolved relative to this file rather than the CWD so
#: that a caller may import the engine from any working directory.
TABLE_PATH: Final[Path] = Path(__file__).resolve().parent / "soil_vg_table.csv"

#: Textures ordered coarsest to finest, USDA. The order is used by
#: :mod:`engine.strict_tests.test_s13_soil_table` to check that conductivity
#: falls and pore volume rises with fineness.
FINENESS_ORDER: Final[tuple[str, ...]] = (
    "sand",
    "loamy_sand",
    "sandy_loam",
    "loam",
    "silt_loam",
    "silt",
    "sandy_clay_loam",
    "clay_loam",
    "silty_clay_loam",
    "sandy_clay",
    "silty_clay",
    "clay",
)

#: Rows whose values disagree across the pre-consolidation copies, or which
#: violate a physical monotonicity. Kept as data so that resolving one conflict
#: forces the set to be revisited.
DISPUTED_TEXTURES: Final[frozenset[str]] = frozenset({"sandy_clay_loam", "clay"})

_NUMERIC_COLUMNS: Final[dict[str, str]] = {
    "theta_r": "theta_r",
    "theta_s": "theta_s",
    "alpha": "alpha",
    "n": "n",
    "ks_cm_per_day": "Ks",
}


class SoilTableError(RuntimeError):
    """Raised when the table is missing, malformed, or internally inconsistent."""


def _read_rows() -> list[dict[str, str]]:
    if not TABLE_PATH.exists():
        raise SoilTableError(
            f"van Genuchten table not found at {TABLE_PATH}. The engine cannot "
            f"start without it: every soil module reads it."
        )
    with TABLE_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise SoilTableError(f"{TABLE_PATH} is empty")
    return rows


def load_table() -> dict[str, dict[str, Any]]:
    """The whole table as ``{texture: {parameter: value}}``, with extras.

    The five numeric parameters keep the key names the engine has always used,
    so existing callers are unaffected. Three descriptive keys are added:
    ``provenance``, ``status`` and ``disputed``.
    """
    table: dict[str, dict[str, Any]] = {}
    for row in _read_rows():
        texture = (row.get("texture") or "").strip()
        if not texture:
            raise SoilTableError(f"{TABLE_PATH} has a row with no texture")
        if texture in table:
            raise SoilTableError(
                f"{TABLE_PATH} declares {texture!r} twice. A texture may appear "
                f"once; a second row is how the previous multi-copy divergence "
                f"would come back."
            )
        entry: dict[str, Any] = {}
        for column, key in _NUMERIC_COLUMNS.items():
            raw = (row.get(column) or "").strip()
            if not raw:
                raise SoilTableError(f"{TABLE_PATH}: {texture} has no {column}")
            try:
                entry[key] = float(raw)
            except ValueError as exc:
                raise SoilTableError(
                    f"{TABLE_PATH}: {texture}.{column} = {raw!r} is not a number"
                ) from exc
        status = (row.get("status") or "").strip()
        entry["provenance"] = (row.get("provenance") or "").strip()
        entry["status"] = status
        entry["disputed"] = status.endswith("_disputed") or texture in DISPUTED_TEXTURES
        # Admissible interval from the fineness ordering. Saturated conductivity
        # cannot rise with texture fineness, so a row is bracketed by its coarser
        # and finer neighbours. This is the strongest statement available about a
        # row without the source publication: a value outside its own interval is
        # wrong whatever the source says, and an EMPTY interval means the two
        # neighbours contradict each other, so the defect is not local to one row.
        lower = (row.get("ks_admissible_min") or "").strip()
        upper = (row.get("ks_admissible_max") or "").strip()
        entry["ks_admissible_min"] = float(lower) if lower else 0.0
        entry["ks_admissible_max"] = float(upper) if upper else float("inf")
        entry["ks_interval_empty"] = entry["ks_admissible_min"] > entry["ks_admissible_max"]
        entry["ks_outside_interval"] = not (
            entry["ks_admissible_min"] <= entry["Ks"] <= entry["ks_admissible_max"]
        )
        table[texture] = entry
    return table


#: Loaded once at import. The table is 12 rows; reading it repeatedly would be
#: wasteful and a module-level constant keeps every consumer in agreement.
SOIL_PARAMETERS: Final[dict[str, dict[str, Any]]] = load_table()


def get_params(texture: str) -> dict[str, float]:
    """Numeric parameters for one texture, or ``KeyError`` if unknown.

    Raises rather than substituting a default. A silent substitution is how
    ``water_retention.get_vg_parameters`` answered an unknown texture with loam
    parameters, which is a wrong answer with no signal.
    """
    try:
        entry = SOIL_PARAMETERS[texture]
    except KeyError as exc:
        raise KeyError(
            f"unknown soil texture {texture!r}; available: {sorted(SOIL_PARAMETERS)}"
        ) from exc
    warn_if_disputed(texture, stacklevel=3)
    return {
        "theta_r": entry["theta_r"],
        "theta_s": entry["theta_s"],
        "alpha": entry["alpha"],
        "n": entry["n"],
        "Ks": entry["Ks"],
    }


def get_params_cpp(texture: str) -> dict[str, float]:
    """Parameters for the compiled backend, with ``Ks`` converted to cm/hr.

    The C++ table has always been cm/hr. Exposing the conversion here rather
    than in each consumer is what keeps the two backends from drifting.
    """
    params = get_params(texture)
    params["Ks"] = params["Ks"] / 24.0
    return params


def load_table_ks_cm_per_hour() -> dict[str, dict[str, float]]:
    """The table in the form the C++ kernel expects."""
    return {texture: get_params_cpp(texture) for texture in SOIL_PARAMETERS}


def disputed_textures() -> tuple[str, ...]:
    """Rows still awaiting adjudication, for reporting and for tripwires."""
    return tuple(t for t in FINENESS_ORDER if t in DISPUTED_TEXTURES)
