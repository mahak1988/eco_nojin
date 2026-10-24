"""Formula registry for the HyDroMa engine.

One record per physical quantity, carrying its provenance, its units, its single
canonical implementation, and the test that proves the backends agree.

Provenance and status are separate questions. ``provenance`` says where an
equation comes from -- a published standard, this project's own contribution, or
a composition of published factors that was assembled here. ``status`` says what
has been checked. A novel formula does not need a published standard to be
recorded and verified; it needs a written research definition, which lives in
:mod:`engine.hydroma.formulas.research`.

That axis is typed :data:`EquationAuthorship`, not ``Provenance``. Three other
types in this repository were also called ``Provenance`` and mean where a
*value* came from; the one that survives is
``services._contracts.status.Provenance``. See
:mod:`engine.hydroma.formulas.records` for why the two questions were not
merged.

The rules this package enforces are in :mod:`engine.hydroma.formulas.registry`;
the records are in :mod:`engine.hydroma.formulas.catalog`. A formula registered
without a parity test is refused; one that claims ``verified`` without an anchor
is refused; and a novel formula that does not name its research definition is
refused.
"""

from __future__ import annotations

from .catalog import RECORDS
from .records import Domain, EquationAuthorship, FormulaRecord, Status
from .registry import (
    DivergentOnRequestPathError,
    DuplicateFormulaError,
    all_records,
    composite,
    divergent,
    get,
    novel,
    on_request_path,
    register,
    require_servable,
    research_definition,
    summary,
    unservable_on_request_path,
    verified,
)

__all__ = [
    "RECORDS",
    "DivergentOnRequestPathError",
    "Domain",
    "DuplicateFormulaError",
    "EquationAuthorship",
    "FormulaRecord",
    "Status",
    "all_records",
    "composite",
    "divergent",
    "get",
    "novel",
    "on_request_path",
    "register",
    "require_servable",
    "research_definition",
    "summary",
    "unservable_on_request_path",
    "verified",
]
