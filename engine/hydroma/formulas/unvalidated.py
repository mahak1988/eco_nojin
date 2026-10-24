"""Unvalidated-coefficient registry: the machine-readable form of the debt.

Owner decision, 2026-10-02: **an explicit "unvalidated" label, now**. The three
options on the table were label them, split them, or fund the research first, and
the label was chosen as the cheapest honest reversible one -- research can fill
in the sources later. This module is that label, made machine-readable, so no
unsourced number can reach a farmer as fact while still looking like a fact.

What this is not
----------------
It is not a list somebody typed. Every entry is **extracted from the source by
AST at import time**: the qualified name, the literal value and the ``file:line``
come from walking the real module, never from a hand-maintained array. A
hand-written list of 178 constants would contain transcription errors, and a
wrong constant list is worse than no list, because it looks authoritative.

The one thing that *cannot* be extracted cheaply is whether a constant is
load-bearing -- that needs a 4374-case perturbation sweep costing 110 seconds --
so the verdicts are a stored measurement in
:mod:`engine.hydroma.formulas.unvalidated_verdicts`, verified by a test that
re-runs the sweep. Everything else is derived at call time.

The three bodies of debt, as ``docs/knowledge-engine/COEFFICIENT-DEBT.md``
counts them
----------------------------------------------------------------------
1. ``engine/hydroma/formulas/research/__init__.py`` -- 14 written definitions,
   13 of which carry an ``UNSOURCED`` declaration. The 14th declares the same
   thing in different punctuation; that adjudication is recorded explicitly as
   an assertion with a section reference, not smuggled in as a measurement.
2. ``engine/hydroma/biofertilizer/calculator.py`` ``NojinCalculator`` -- 178
   constants, 105 load-bearing, 73 cosmetic.
3. ``services/scientific_motors/biofertilizer.py`` -- 87 constants. Its
   load-bearing-ness was **not** measured, so it reports ``unmeasured`` rather
   than borrowing the calculator's verdict.

Validation states
-----------------
``validated``
    Every coefficient in the scope has a named source. Not reachable today.
``unvalidated``
    Fully classified, and at least one coefficient has no source. The everyday
    state, and the one the owner asked for.
``unmeasured``
    The scope's load-bearing-ness was never swept. Honest, and distinct from a
    clean bill of health.
``unclassified``
    **A coefficient in this scope has no recorded verdict** -- it was added
    after the sweep, or a recorded literal no longer matches the source. This
    is the mechanical gate: a new unsourced constant cannot be added silently,
    because the state degrades and every result built from the scope says so.
    Precedence is ``unclassified`` > ``unvalidated`` / ``validated`` > ``unmeasured``.

What this does not do
---------------------
It does not make a number correct. A coefficient can be unsourced and right.
This registry measures *provenance* and *load-bearing-ness*, and says so; it
does not evaluate agronomy, and it refuses to guess.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .unvalidated_verdicts import (
    CLASS_TABLE_VERDICTS,
    MEASURED_ON,
    METHOD_BODY_VERDICTS,
    SWEEP_CASES,
    UNVALIDATED_RESULT_FIELDS,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

#: Repository-relative paths. Kept as POSIX strings so a digest computed on one
#: machine means the same thing on another.
CALCULATOR_SOURCE = "engine/hydroma/biofertilizer/calculator.py"
LIVE_MOTOR_SOURCE = "services/scientific_motors/biofertilizer.py"
RESEARCH_SOURCE = "engine/hydroma/formulas/research/__init__.py"

DEBT_DOCUMENT = "docs/knowledge-engine/COEFFICIENT-DEBT.md"

#: The six class-level numeric tables the 4374-case sweep measured, and the only
#: ones with recorded verdicts. Extraction does **not** filter on this set: every
#: class-level numeric assignment in ``NojinCalculator`` is registered, and a
#: seventh table arrives as ``unclassified`` rather than being missed. The set
#: exists to say which bodies have a measurement, and it is what the sweep test
#: iterates.
CALCULATOR_CLASS_TABLES = frozenset(
    {
        "CROP_FACTORS",
        "OPTIMAL_PH",
        "OPTIMAL_TEMP_C",
        "OPTIMAL_MOISTURE_PCT",
        "SEASONAL_FACTORS",
        "STRAIN_SYNERGY",
    }
)

VALIDATED = "validated"
UNVALIDATED = "unvalidated"
UNMEASURED = "unmeasured"
UNCLASSIFIED = "unclassified"

DOC_SECTION_RESEARCH = f"{DEBT_DOCUMENT} section 2"
DOC_SECTION_CALCULATOR = f"{DEBT_DOCUMENT} section 3"
DOC_SECTION_MOTOR = f"{DEBT_DOCUMENT} section 5"

#: The one research definition whose unsourced coefficients it does not mark
#: with the ``UNSOURCED`` token. Recorded here as an adjudication with a
#: citation rather than inferred by string-matching, because inferring it would
#: mean pretending a heuristic is a measurement.
ADJUDICATED_UNMARKED = ("nojin_biofertilizer_suitability",)


class UnvalidatedRegistryError(RuntimeError):
    """Raised when the registry cannot be built from the source it claims to read."""


@dataclass(frozen=True, slots=True)
class CoefficientEntry:
    """One numeric literal that decides something, and where it was read from.

    ``load_bearing`` is ``None`` when no verdict has been measured for it.
    ``source`` is the citation, and it is ``None`` for every entry in this
    repository today -- that ``None`` is the debt, made explicit.
    """

    scope: str
    body: str
    qualified_name: str
    value: float
    line: int
    column: int
    index: int
    load_bearing: bool | None
    source: str | None
    doc_section: str
    source_file: str = ""

    @property
    def location(self) -> str:
        return f"{self.source_file}:{self.line}"


@dataclass(frozen=True, slots=True)
class ResearchDefinitionStatus:
    """A written formula definition and whether it admits its coefficients are unsourced."""

    quantity: str
    line: int
    declares_unsourced: bool
    doc_section: str
    note: str = ""


@dataclass(frozen=True, slots=True)
class CoefficientValidation:
    """The label. Derived from the registry; never written by hand.

    This is what a caller reads to tell an unvalidated number from a validated
    one. ``unvalidated_fields`` names the result fields that a load-bearing
    unsourced constant can move, measured over the sweep.
    """

    state: str
    source_file: str
    scope: str
    total_coefficients: int
    load_bearing: int
    cosmetic: int
    unclassified: int
    sourced: int
    unvalidated_fields: tuple[str, ...]
    registry_digest: str
    measured_on: str | None
    detail: str

    @property
    def is_fact(self) -> bool:
        """True only when a caller may present the numbers as established fact."""
        return self.state == VALIDATED

    def as_payload(self) -> dict[str, Any]:
        """A JSON-ready dict, for a service or a response body."""
        return {
            "state": self.state,
            "source_file": self.source_file,
            "scope": self.scope,
            "total_coefficients": self.total_coefficients,
            "load_bearing": self.load_bearing,
            "cosmetic": self.cosmetic,
            "unclassified": self.unclassified,
            "sourced": self.sourced,
            "unvalidated_fields": list(self.unvalidated_fields),
            "registry_digest": self.registry_digest,
            "measured_on": self.measured_on,
            "detail": self.detail,
        }


# --------------------------------------------------------------------- helpers


def _is_number(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    )


def _numeric_literals(node: ast.AST) -> list[ast.Constant]:
    """Every numeric literal under ``node``, in ``ast.walk`` order.

    This is deliberately identical to ``num_leaves`` in
    ``tests/unit/test_knowledge_engine_plan.py`` and to the counting method
    ``COEFFICIENT-DEBT.md`` section 3.1 documents. Same traversal, same order,
    so the registry and the prose cannot disagree about what counts.
    """
    # The explicit isinstance spells out the narrowing mypy cannot infer from
    # the _is_number predicate; it is implied by it, so the filter is unchanged.
    return [
        n for n in ast.walk(node) if isinstance(n, ast.Constant) and _is_number(n)
    ]


def _container_paths(node: ast.AST) -> dict[int, str]:
    """Map ``id(literal)`` to its subscript path inside a dict/tuple/list.

    Used only to make a qualified name readable -- ``CROP_FACTORS['rice']
    ['factor']`` instead of ``CROP_FACTORS#1``. A literal the walk reaches but
    this descent does not (one inside an expression rather than a container) is
    simply absent, and the caller falls back to the index.
    """
    found: dict[int, str] = {}

    def walk(current: ast.AST, prefix: str) -> None:
        if isinstance(current, ast.Dict):
            for key, value in zip(current.keys, current.values, strict=True):
                if key is None:
                    walk(value, prefix)
                elif isinstance(key, ast.Constant):
                    walk(value, f"{prefix}[{key.value!r}]")
                else:
                    walk(value, f"{prefix}[{ast.unparse(key)}]")
        elif isinstance(current, (ast.List, ast.Tuple, ast.Set)):
            for position, value in enumerate(current.elts):
                walk(value, f"{prefix}[{position}]")
        elif _is_number(current):
            found[id(current)] = prefix

    walk(node, "")
    return found


def _table_name(stmt: ast.stmt) -> str | None:
    if isinstance(stmt, ast.Assign):
        target = stmt.targets[0]
    elif isinstance(stmt, ast.AnnAssign):
        target = stmt.target
    else:
        return None
    return target.id if isinstance(target, ast.Name) else None


def _verdict_rows(body_name: str, literals: list[ast.Constant]) -> tuple[list[bool | None], int]:
    """Pair recorded verdicts to the literals now in the source.

    Returns ``(rows, stale)``. A row is ``None`` where no verdict applies.

    The pairing is deliberately **whole-body or nothing**. A recorded verdict is
    only valid for the exact literal sequence it was measured on, and there is
    no reliable way to re-attribute one after an edit: ``ast.walk`` is
    breadth-first, so appending one literal to an expression can reorder the
    literals around it, and two of them in this file share a column and a value
    while carrying opposite verdicts. Re-pairing them by position would quietly
    put a load-bearing verdict on a cosmetic constant. Invalidating the body is
    stricter and cannot do that, and a caller is told exactly which body to
    re-sweep.

    ``stale`` counts recorded verdicts with no literal left to attach to --
    a deletion, which is drift in the other direction and must not pass silently.
    A body whose literals moved is *not* counted here: its unpaired literals are
    already counted by the ``None`` rows, and counting the table again would
    double-report the same constants.
    """
    table = METHOD_BODY_VERDICTS.get(body_name)
    if table is None:
        table = CLASS_TABLE_VERDICTS.get(body_name)
    if table is None:
        return [None] * len(literals), 0
    stale = max(0, len(table) - len(literals))
    if len(table) != len(literals) or any(
        column != literal.col_offset or value != literal.value
        for (column, value, _load_bearing), literal in zip(table, literals, strict=False)
    ):
        return [None] * len(literals), stale
    return [row[2] for row in table], 0


# ------------------------------------------------------------------ extraction


def _class_scope(
    source: str, *, module: str, class_name: str
) -> tuple[list[CoefficientEntry], int, tuple[str, ...]]:
    """Entries for one class, stale recorded verdicts, and the bodies to re-sweep."""
    tree = ast.parse(source)
    cls = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
        None,
    )
    if cls is None:
        raise UnvalidatedRegistryError(
            f"{module} has no class {class_name!r}; the registry cannot be built"
        )

    entries: list[CoefficientEntry] = []
    stale = 0
    dirty: list[str] = []

    def build(
        body: str, body_name: str, literal_node: ast.AST, paths: dict[int, str] | None
    ) -> None:
        literals = _numeric_literals(literal_node)
        rows, extra = _verdict_rows(body_name, literals)
        nonlocal stale
        stale += extra
        if any(row is None for row in rows):
            dirty.append(body_name)
        for index, literal in enumerate(literals):
            suffix = paths.get(id(literal)) if paths else None
            if suffix:
                qualified = f"{class_name}.{body_name}{suffix}"
            else:
                qualified = f"{class_name}.{body_name}#{index}"
            entries.append(
                CoefficientEntry(
                    scope=class_name,
                    body=body,
                    qualified_name=qualified,
                    value=literal.value,
                    line=literal.lineno,
                    column=literal.col_offset,
                    index=index,
                    load_bearing=rows[index],
                    source=None,
                    doc_section=DOC_SECTION_CALCULATOR,
                    source_file=module,
                )
            )

    methods = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for method in methods:
        build("method_body", method.name, method, None)
    for stmt in cls.body:
        if not isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            continue
        name = _table_name(stmt)
        value = stmt.value
        if name is None or value is None or not _numeric_literals(value):
            continue
        # Every class-level numeric assignment, not just the six the sweep
        # measured. A seventh table has no recorded verdicts, so it lands in
        # `unclassified` -- which is the point. Filtering on the known six would
        # make a new table invisible, and an invisible table is the exact
        # failure this registry exists to prevent.
        build("class_table", name, value, _container_paths(value))
    return entries, stale, tuple(dirty)


def class_entries(source: str, *, module: str, class_name: str) -> tuple[CoefficientEntry, ...]:
    """Every numeric literal in ``class_name``: method bodies, then class tables.

    Two groups, matching how the debt document counts: a literal in a method
    body, and a literal in a class-level table. ``__init__`` and ``calculate``
    contribute none today; they are walked anyway, so a literal added to either
    is registered rather than missed.
    """
    entries, _stale, _dirty = _class_scope(source, module=module, class_name=class_name)
    return tuple(entries)


def module_entries(source: str, *, module: str, class_name: str) -> tuple[CoefficientEntry, ...]:
    """Every numeric literal in the methods of one class in a module.

    The live motor keeps its 87 constants in method bodies, so the class scope
    is the unit. Module-level numeric assignments are included too, because a
    new one must be registered rather than missed.
    """
    tree = ast.parse(source)
    entries: list[CoefficientEntry] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            name = _table_name(stmt) or "<module>"
            value = stmt.value
            if value is None:
                continue
            for index, literal in enumerate(_numeric_literals(value)):
                entries.append(
                    CoefficientEntry(
                        scope=module,
                        body="module_table",
                        qualified_name=f"{module}.{name}#{index}",
                        value=literal.value,
                        line=literal.lineno,
                        column=literal.col_offset,
                        index=index,
                        load_bearing=None,
                        source=None,
                        doc_section=DOC_SECTION_MOTOR,
                        source_file=module,
                    )
                )
    cls = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name),
        None,
    )
    if cls is None:
        raise UnvalidatedRegistryError(
            f"{module} has no class {class_name!r}; the registry cannot be built"
        )
    for method in cls.body:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        literals = _numeric_literals(method)
        for index, literal in enumerate(literals):
            entries.append(
                CoefficientEntry(
                    scope=module,
                    body="method_body",
                    qualified_name=f"{module}.{method.name}#{index}",
                    value=literal.value,
                    line=literal.lineno,
                    column=literal.col_offset,
                    index=index,
                    load_bearing=None,
                    source=None,
                    doc_section=DOC_SECTION_MOTOR,
                    source_file=module,
                )
            )
    return tuple(entries)


def research_entries(source: str) -> tuple[ResearchDefinitionStatus, ...]:
    """One record per written formula definition, and whether it admits its numbers.

    ``declares_unsourced`` is the measured part: the literal token ``UNSOURCED``
    inside that definition's text. The 14th definition records the same problem
    without the token, so it is carried as ``note`` -- an assertion with a
    section reference, not a measurement pretending to be one.
    """
    tree = ast.parse(source)
    node = next(
        (
            stmt.value
            for stmt in tree.body
            if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and _table_name(stmt) == "DEFINITIONS"
        ),
        None,
    )
    if node is None or not isinstance(node, ast.Dict):
        raise UnvalidatedRegistryError("research/__init__.py has no DEFINITIONS dict")
    out: list[ResearchDefinitionStatus] = []
    for key, value in zip(node.keys, node.values, strict=True):
        if not isinstance(key, ast.Constant) or not isinstance(value, ast.Constant):
            continue
        quantity = key.value
        declares = "UNSOURCED" in value.value
        note = ""
        if not declares and quantity in ADJUDICATED_UNMARKED:
            note = (
                "records unsourced coefficients without the UNSOURCED token; "
                f"adjudicated in {DOC_SECTION_RESEARCH}"
            )
        out.append(
            ResearchDefinitionStatus(
                quantity=quantity,
                line=key.lineno,
                declares_unsourced=declares,
                doc_section=DOC_SECTION_RESEARCH,
                note=note,
            )
        )
    return tuple(out)


# -------------------------------------------------------------------- registry


def _digest(entries: tuple[CoefficientEntry, ...]) -> str:
    hasher = hashlib.sha256()
    for entry in entries:
        hasher.update(
            f"{entry.qualified_name}|{entry.value!r}|{entry.load_bearing}|{entry.line}\n".encode()
        )
    return hasher.hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class UnvalidatedCoefficientRegistry:
    """The whole debt, as extracted from the tree on this machine, just now."""

    source_file: str
    scope: str
    entries: tuple[CoefficientEntry, ...]
    measured: bool
    measured_on: str | None
    stale_verdicts: int = 0
    unclassified_bodies: tuple[str, ...] = ()

    @property
    def digest(self) -> str:
        return _digest(self.entries)

    def by_qualified_name(self, name: str) -> CoefficientEntry | None:
        return next((e for e in self.entries if e.qualified_name == name), None)

    def validation(self) -> CoefficientValidation:
        total = len(self.entries)
        classified = [e for e in self.entries if e.load_bearing is not None]
        load_bearing = sum(1 for e in classified if e.load_bearing)
        cosmetic = len(classified) - load_bearing
        unclassified = (total - len(classified)) + self.stale_verdicts
        sourced = sum(1 for e in self.entries if e.source is not None)

        if not self.measured:
            state = UNMEASURED
            detail = (
                f"load-bearing-ness of the {total} coefficients in {self.scope} was "
                f"never measured; provenance is unvalidated on all of them"
            )
            fields: tuple[str, ...] = ()
        elif unclassified:
            state = UNCLASSIFIED
            detail = (
                f"{unclassified} of {total} coefficients in {self.scope} have no recorded "
                "load-bearing verdict, in "
                f"{len(self.unclassified_bodies)} body/bodies "
                f"({', '.join(self.unclassified_bodies)}): the source has moved since the "
                "sweep, or a constant was added or removed without re-running it"
            )
            fields = UNVALIDATED_RESULT_FIELDS
        elif sourced == total:
            state = VALIDATED
            detail = "every coefficient in this scope has a named source"
            fields = ()
        else:
            state = UNVALIDATED
            detail = (
                f"{total - sourced} of {total} coefficients in {self.scope} have no "
                f"source; {load_bearing} of them move a result field"
            )
            fields = UNVALIDATED_RESULT_FIELDS

        return CoefficientValidation(
            state=state,
            source_file=self.source_file,
            scope=self.scope,
            total_coefficients=total,
            load_bearing=load_bearing,
            cosmetic=cosmetic,
            unclassified=unclassified,
            sourced=sourced,
            unvalidated_fields=fields,
            registry_digest=self.digest,
            measured_on=self.measured_on,
            detail=detail,
        )


def registry_from_source(
    source: str,
    *,
    module: str,
    class_name: str,
    measured: bool = True,
    measured_on: str | None = MEASURED_ON,
) -> UnvalidatedCoefficientRegistry:
    """Build a registry from source text rather than from a file on disk.

    Used by the drift tests, and by anything that needs to know what the label
    *would* say about a modified calculator without touching the file. The file
    is never written.
    """
    entries, stale, dirty = _class_scope(source, module=module, class_name=class_name)
    return UnvalidatedCoefficientRegistry(
        source_file=module,
        scope=class_name,
        entries=tuple(entries),
        measured=measured,
        measured_on=measured_on if measured else None,
        stale_verdicts=stale,
        unclassified_bodies=dirty,
    )


@lru_cache(maxsize=8)
def registry_for(source_file: str, scope: str) -> UnvalidatedCoefficientRegistry:
    """Extract one scope's registry from disk. Cached; the tree does not move mid-run."""
    if source_file == RESEARCH_SOURCE:
        raise UnvalidatedRegistryError(
            "the research definitions are prose, not numeric literals; use research_status()"
        )
    path = REPO_ROOT / source_file
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise UnvalidatedRegistryError(
            f"{source_file} cannot be read, so no validation label can be derived: {exc}"
        ) from exc

    if source_file == CALCULATOR_SOURCE:
        return registry_from_source(source, module=source_file, class_name=scope)
    measured = False
    return UnvalidatedCoefficientRegistry(
        source_file=source_file,
        scope=scope,
        entries=module_entries(source, module=source_file, class_name=scope),
        measured=measured,
        measured_on=None,
    )


@lru_cache(maxsize=8)
def research_status() -> tuple[ResearchDefinitionStatus, ...]:
    """The 14 written definitions, extracted from the research module."""
    return research_entries((REPO_ROOT / RESEARCH_SOURCE).read_text(encoding="utf-8"))


@lru_cache(maxsize=8)
def validation_for(source_file: str, scope: str) -> CoefficientValidation:
    """The label for one scope, derived from the registry rather than typed."""
    return registry_for(source_file, scope).validation()


def calculator_validation() -> CoefficientValidation:
    """The label for ``NojinCalculator``. What ``NojinResult`` carries."""
    return validation_for(CALCULATOR_SOURCE, "NojinCalculator")


def live_motor_validation() -> CoefficientValidation:
    """The label for ``services/scientific_motors/biofertilizer.py``."""
    return validation_for(LIVE_MOTOR_SOURCE, "BiofertilizerMotor")


def summary() -> dict[str, Any]:
    """Counts for every body, as ``COEFFICIENT-DEBT.md`` section 1 reports them."""
    research = research_status()
    calculator = validation_for(CALCULATOR_SOURCE, "NojinCalculator")
    motor = validation_for(LIVE_MOTOR_SOURCE, "BiofertilizerMotor")
    return {
        "sweep_cases": SWEEP_CASES,
        "measured_on": MEASURED_ON,
        "research_definitions": len(research),
        "research_declares_unsourced": sum(1 for r in research if r.declares_unsourced),
        "research_adjudicated_unmarked": sum(1 for r in research if r.note),
        "calculator_total": calculator.total_coefficients,
        "calculator_load_bearing": calculator.load_bearing,
        "calculator_cosmetic": calculator.cosmetic,
        "motor_total": motor.total_coefficients,
        "states": {
            "NojinCalculator": calculator.state,
            "BiofertilizerMotor": motor.state,
        },
    }


__all__ = [
    "ADJUDICATED_UNMARKED",
    "CALCULATOR_CLASS_TABLES",
    "CALCULATOR_SOURCE",
    "LIVE_MOTOR_SOURCE",
    "RESEARCH_SOURCE",
    "UNCLASSIFIED",
    "UNMEASURED",
    "UNVALIDATED",
    "VALIDATED",
    "CoefficientEntry",
    "CoefficientValidation",
    "ResearchDefinitionStatus",
    "UnvalidatedCoefficientRegistry",
    "UnvalidatedRegistryError",
    "calculator_validation",
    "class_entries",
    "live_motor_validation",
    "module_entries",
    "registry_for",
    "registry_from_source",
    "research_entries",
    "research_status",
    "summary",
    "validation_for",
]
