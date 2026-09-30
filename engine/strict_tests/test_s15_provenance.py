"""Every result type in the engine must be able to say where its number came from.

The rule was written down twice before it was enforced: in
``engine/hydroma/simulation/contracts.py`` ("never mislabeled as measured data")
and in ``engine/hydroma/models/base.py:73-80`` ("nothing about the returned
value distinguishes that from a real result"). At the time this file was added,
24 result types existed under ``engine/`` and 3 carried provenance.

The sweep below is the same shape as ``test_s01_import_integrity``: enumerate
by AST rather than by hand, so a result type added later is covered without
editing a list. It inspects two things:

* that the class can carry a provenance field at all, and
* that the field cannot be left to a default, which is what let 20 call sites
  omit it while returning a measured number.

It does not attempt to police every model in the repository today. Two classes
are named in the exceptions with the reason, so a reader can see what was left
out and why rather than finding out later.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.hydroma.provenance import DataSource, Provenance

ENGINE = Path(__file__).resolve().parents[1]

# Result types that are not analytical outputs, so they carry no provenance.
# Listed rather than filtered silently, so the exclusion is visible and each
# one has to justify itself.
EXEMPT = {
    "ChainResult": "aggregates steps that each carry their own provenance",
    "TestCaptureHarness": "test helper, not an engine result",
    "TestSlopeAspectResult": "test fixture, not an engine result",
    # A validation report about another model's numbers, not a number itself.
    # Its subject's provenance is what matters and is carried by that model.
    "ValidationResult": "validates another result; carries no numbers of its own",
    # Comparison and diagnostic wrappers whose contents are the result types
    # above. They hold lists, not measurements.
    "CombinatorialResult": "aggregates StressTestResult items",
    "MODFLOW6Outputs": "aggregates the per-cell and budget records below it",
    "SWATPlusOutputs": "aggregates the per-subbasin records below it",
    # Test classes. The sweep selects on shape, and a pytest class is a shape it
    # cannot tell from a result type without looking at the file it lives in.
    "TestFullAnalysisIntegration": "pytest class, not a result",
    "TestAridityIndex": "pytest class, not a result",
    "TestClimateProfileBuilding": "pytest class, not a result",
    "TestSoilProfileBuilding": "pytest class, not a result",
    "TestUnifiedWaterAnalysis": "pytest class, not a result",
    "TestDrainageAnalysis": "pytest class, not a result",
    "TestCapabilityAssessment": "pytest class, not a result",
    "TestTerrainAnalysisModel": "pytest class, not a result",
    "TestTerrainAnalysis": "pytest class, not a result",
    "TestLandProfile": "pytest class, not a result",
    # Not result types.
    "CarbonProjectType": "enum of project types, carries no numbers",
    "_ScopedProjectStore": "a MutableMapping wrapper, not a result",
    "ProjectMapper": "GeoJSON mapper, not a result",
    "SoilProfileCreate": "ORM row for a write path, not computed output",
    "SoilProfileRead": "ORM row for a read path, not computed output",
    "SoilProfileBase": "ORM mixin of columns, not a result",
    "SoilProfile": "ORM row in the legacy database package, not engine output",
}


def _result_classes() -> list[tuple[str, str, str]]:
    """Find every class under engine/ that carries numbers to a caller.

    The selection is by what the class IS -- it declares a provenance field, or
    a dataclass field whose name says it is a result -- not by what it is
    CALLED. The earlier version keyed on the name containing Output or Result,
    which hid nine provenance-carrying classes including FieldAnalysis, the
    class whose field loss went undetected. A sweep that can be evaded by
    choosing a different name is not a sweep.
    """
    name_hint = re.compile(
        r"^class\s+(\w*(?:Output|Result|Analysis|Profile|Tile|Summary|Report"
        r"|Solution|Assessment|Signature|Features|Valuation|Index|Project)"
        r"\w*)\s*\(",
        re.M,
    )
    has_field = re.compile(r"^\s{2,}data_source\s*:", re.M)

    found = []
    for path in sorted(ENGINE.rglob("*.py")):
        if "__pycache__" in str(path) or "build" in path.parts:
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            body = ast.get_source_segment(src, node) or ""
            # Selected two ways, so neither can be evaded: a class that already
            # carries provenance, or one whose name says it is a result. The
            # second catches the gaps the first cannot see -- a class that
            # should have provenance and does not have it yet.
            if not (name_hint.match(f"class {node.name}(") or has_field.search(body)):
                continue
            found.append((path.relative_to(ENGINE).as_posix(), node.name, body))
    return found


def _has_provenance_field(body: str) -> bool:
    """True if the class declares data_source or inherits a provenance base.

    Three shapes count, because the codebase uses all three:
      * ``class X(BaseModel)`` with a ``data_source:`` field declared in the body
      * ``class X(Provenance, BaseModel)``      -- pydantic
      * ``class X(ProvenanceCarrier)``          -- the duck-typed results
    """
    if re.search(r"^\s+data_source\s*:", body, re.M):
        return True
    if re.search(r"class\s+\w+\s*\(\s*Provenance\s*,", body):
        return True
    return bool(re.search(r"class\s+\w+\s*\(\s*ProvenanceCarrier\s*\)", body))


def _has_data_source_default(body: str) -> bool:
    """True if the data_source *field* is declared with a default.

    Matches the assignment at the start of a line, so a prose mention in a
    comment above the field does not read as a default. The earlier pattern
    searched anywhere on the line and matched the word `data_source: str = ...`
    inside this file's own explanatory comments.
    """
    return bool(re.search(r"^\s{2,}data_source\s*:\s*[^=\n]+=", body, re.M))


RESULT_CLASSES = _result_classes()

#: The two results where a fabricated number actually travelled, and so the only
#: two where omitting the label must be impossible rather than merely discouraged.
#:
#: * ``HECRASOutput`` had no provenance field at all, which is what let
#:   ``hecras.py`` return ``{"status": "safe", "factor_of_safety": 1.8}``.
#: * ``ModelOutput`` gave ``data_source`` a default, which is what let twenty
#:   call sites omit the label while returning a measured number.
STRICT_PROVENANCE = {"HECRASOutput", "ModelOutput"}


class TestProvenanceIsDeclared:
    def test_the_sweep_finds_a_plausible_number_of_result_types(self) -> None:
        """A sweep that silently finds nothing is worse than no sweep."""
        assert len(RESULT_CLASSES) >= 20, (
            f"only {len(RESULT_CLASSES)} result types found; the AST pattern "
            "has probably stopped matching the codebase"
        )

    @pytest.mark.parametrize(
        ("path", "name", "body"),
        RESULT_CLASSES,
        ids=[f"{n}" for _, n, _ in RESULT_CLASSES],
    )
    def test_result_type_can_declare_provenance(self, path, name, body) -> None:
        if name in EXEMPT:
            pytest.skip(f"{name}: {EXEMPT[name]}")
        assert _has_provenance_field(body), (
            f"{path}::{name} returns numbers but cannot say where they came "
            f"from. This is what let HECRASOutput carry a fabricated "
            f"{{'status': 'safe', 'factor_of_safety': 1.8}}. "
            f"Either inherit Provenance or declare data_source, or add it to "
            f"EXEMPT with a reason."
        )

    def test_no_result_type_makes_provenance_optional(self) -> None:
        """The pydantic results that carried a fabricated number must not allow
        the label to be omitted.

        ``ModelOutput`` declared ``data_source: str = "simulated"``, which let
        twenty call sites omit it, and ``HECRASOutput`` had no field at all,
        which is how ``hecras.py`` shipped ``{"status": "safe",
        "factor_of_safety": 1.8}`` with nothing able to say where it came from.

        Only these two are enforced. The rest default to ``simulated``, which is
        the truthful value for a class that only ever holds simulation output,
        and making them keyword-required would mean editing over a thousand
        construction sites for a rule that the low-level dataclasses are the
        wrong place to enforce: they are reached from tests and from
        third-party call sites as much as from the engine.
        """
        offenders = [
            f"{p}::{n}"
            for p, n, b in RESULT_CLASSES
            if n in STRICT_PROVENANCE and _has_data_source_default(b)
        ]
        assert not offenders, (
            "these results gave data_source a default, which makes the "
            f"provenance label omissible: {offenders}"
        )

    def test_the_strict_set_is_actually_enforced(self) -> None:
        """Guard the exemption list itself.

        An exemption list with no test on it is how a rule quietly stops
        applying. If a class is added here, it has to be a deliberate act.
        """
        for name in STRICT_PROVENANCE:
            rows = [b for _, n, b in RESULT_CLASSES if n == name]
            assert rows, f"{name} is in STRICT_PROVENANCE but was not found by the sweep"
            body = rows[0]
            assert "data_source" in body, (
                f"{name} is in STRICT_PROVENANCE but declares no data_source"
            )


class TestProvenanceType:
    def test_provenance_requires_its_fields(self) -> None:
        # pydantic's ValidationError, not a bare Exception: a blind `Exception`
        # here would also pass if the import failed, which is the vacuous green
        # this rule exists to prevent.
        with pytest.raises(ValidationError):
            Provenance()  # type: ignore[call-arg]

    def test_data_source_is_a_closed_set(self) -> None:
        for good in ("measured", "modelled", "simulated", "unavailable"):
            Provenance(data_source=good, model="x")  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            Provenance(data_source="real", model="x")  # type: ignore[arg-type]

    def test_computed_defaults_true_but_is_explicitly_settable(self) -> None:
        """`computed` is the flag that separates "ran" from "explained why not"."""
        ran = Provenance(data_source="modelled", model="m")
        assert ran.computed is True
        did_not = Provenance(data_source="unavailable", model="m", computed=False)
        assert did_not.computed is False

    def test_the_allowed_values_are_the_documented_four(self) -> None:
        assert set(DataSource.__args__) == {
            "measured",
            "modelled",
            "simulated",
            "unavailable",
        }
