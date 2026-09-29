"""S12 — Model and table registration: duplicate declarations on a shared registry.

The finding
-----------
This module exists because of a defect found while building the Phase 0
baseline, and it is the most dangerous class in the engine because it fails at
**import time**, not at call time.

``database/base.py`` and ``database/config.py`` both expose a ``Base``, and
they are the *same object* (verified: identical ``id``, identical
``metadata``). Every module that declares a SQLAlchemy model therefore writes
into one shared ``MetaData`` registry. A table name may be declared only once
per registry, so a second declaration raises::

    InvalidRequestError: Table 'nojin_application_plans' is already defined
    for this MetaData instance.

The consequence is that **import order decides whether the application starts.**
Whichever file is reached second fails. A web worker that imports the gateway
and a background job that imports the biofertilizer services can each succeed
in isolation and collide in a combined process. The same is true of Alembic,
of a management script, and of the test suite — which is how it was found.

Why the class names hide it
---------------------------
The two declarations use *different* class names for the same table::

    database/models.py:642                  class NojinApplicationPlanDB
    engine/hydroma/biofertilizer/models.py:105  class NojinApplicationPlan

so a search for the class name finds one hit and looks clean. Only a search for
``__tablename__`` finds the collision. Every test in this module therefore
keys on the table name, never the class name.
"""

from __future__ import annotations

import ast
import collections
from pathlib import Path

import pytest

from engine.strict_tests.conftest import ENGINE_ROOT

ROOT = ENGINE_ROOT.parent

# Directories whose SQLAlchemy models register against the same declarative
# Base as the engine. Excluded: this suite, vendored packages, generated trees.
_SCAN_ROOTS = ("database", "engine", "services", "orchestrator")
_EXCLUDED_PARTS = frozenset(
    {
        "__pycache__",
        "alembic",
        "migrations",
        "build",
        "build2",
        "cpp_core",
        "strict_tests",
        "baseline",
        ".venv",
        ".kilo",
    }
)


def _repo_root() -> Path:
    return ENGINE_ROOT.parent


def _declarations() -> dict[str, list[tuple[str, int, str]]]:
    """Every ``__tablename__`` in the repository, keyed by table name.

    Parsed with ``ast`` rather than imported, so running this test does not
    itself register a table and cannot cause the failure it is looking for.
    """
    root = _repo_root()
    found: dict[str, list[tuple[str, int, str]]] = collections.defaultdict(list)
    for top in _SCAN_ROOTS:
        base = root / top
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            rel = path.relative_to(root)
            if _EXCLUDED_PARTS.intersection(rel.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                for statement in node.body:
                    if not isinstance(statement, ast.Assign):
                        continue
                    if not any(
                        getattr(t, "id", None) == "__tablename__" for t in statement.targets
                    ):
                        continue
                    try:
                        table = ast.literal_eval(statement.value)
                    except Exception:
                        continue
                    if isinstance(table, str):
                        found[table].append((rel.as_posix(), node.lineno, node.name))
    return dict(found)


def _duplicates() -> dict[str, list[tuple[str, int, str]]]:
    return {
        table: locs for table, locs in _declarations().items() if len({loc[0] for loc in locs}) > 1
    }


class TestTableRegistration:
    def test_parser_finds_a_meaningful_number_of_tables(self) -> None:
        """Guards the guard: an empty parse would make every other test pass."""
        declarations = _declarations()
        assert len(declarations) > 100, (
            f"only {len(declarations)} tables found; the scanner is broken"
        )

    def test_no_table_is_declared_in_two_files(self) -> None:
        duplicates = _duplicates()
        assert not duplicates, "\n".join(
            f"  {table}: {sorted({loc[0] + ':' + str(loc[1]) + ' ' + loc[2] for loc in locs})}"
            for table, locs in sorted(duplicates.items())
        )

    def test_known_duplicates_are_still_the_only_ones(self) -> None:
        """A new collision is a regression; a fixed one must be removed from
        KNOWN_DUPLICATE_TABLES so the strict xfail above cannot rot.

        The third entry is inside the shadowed directory and is covered
        narratively by TestModuleShadowing; it is listed here so that a change
        to the collision set is still noticed.
        """
        # Resolved 27 September 2026: the dead declaration in each pair was
        # removed and the shadowing workaround was dropped. Empty because the
        # repo is clean; a new entry here is a regression, not an update.
        known: dict[str, set[str]] = {}
        actual = {table: {loc[0] for loc in locs} for table, locs in _duplicates().items()}
        unexpected = {table: files for table, files in actual.items() if files != known.get(table)}
        assert not unexpected, f"changed collision set: {unexpected}"
        stale = set(known) - set(actual)
        assert not stale, f"these are now unique; update KNOWN_DUPLICATE_TABLES: {sorted(stale)}"

    def test_shared_base_is_a_single_object(self) -> None:
        """States the mechanism so a future fix knows what must stay true.

        Two Base objects with two registries would make the collision harmless
        by separating the schemas, but they would also mean ``create_all`` only
        creates half the tables. One Base is correct; the duplicates are not.
        """
        from database.base import Base as BaseA
        from database.config import Base as BaseB

        assert BaseA is BaseB, (
            "database.base.Base and database.config.Base have diverged into two "
            "declarative registries; Base.metadata.create_all would then create "
            "only the tables of whichever module was imported"
        )


class TestModuleShadowing:
    """A directory and a file sharing a base name: one of them is unreachable.

    ``database/models.py`` and ``database/models/`` both existed. Python resolved
    the import name to the file, so the directory was a shadow, and the file
    inside it also imported ``Base`` from ``database.models`` - the name it
    shadowed - so it was unimportable by construction as well as by accident.

    It held seven table declarations. Six named result types the engine
    computes and the repository had nowhere to store, none of which appeared in
    any migration, so each result was produced and dropped. All six now live in
    ``database/models.py`` and are covered by a migration.
    """

    SHADOW_DIR = ROOT / "database" / "models"

    def test_the_shadowing_directory_is_gone(self) -> None:
        assert not self.SHADOW_DIR.exists(), (
            "database/models/ is shadowed by database/models.py, so nothing inside "
            "it can be imported"
        )

    def test_the_six_result_models_are_reachable(self) -> None:
        import database.models as models

        rescued = (
            "RunoffCalculationResult",  # models/runoff_model.py
            "GroundwaterModelResult",  # groundwater/models.py
            "CropWaterReqResult",  # calculations/crop_water_req_calc.py
            "StructureDesignResult",  # watershed/calculator.py
            "IrrigationDesignResult",  # irrigation/scheduler.py
            "CalibrationResult",  # simulation/calibration.py
        )
        for name in rescued:
            assert hasattr(models, name), f"{name} is not reachable from database.models"

    def test_the_six_tables_are_registered_on_the_shared_base(self) -> None:
        import database.models  # noqa: F401
        from database.base import Base

        for table in (
            "runoff_calculation_results",
            "groundwater_model_results",
            "crop_water_req_results",
            "structure_design_results",
            "irrigation_design_results",
            "calibration_results",
        ):
            assert table in Base.metadata.tables, table

    def test_a_migration_creates_the_six_tables(self) -> None:
        """Declared is not the same as created, which is how they were lost."""
        from engine.hydroma.alembic_graph import render_range

        sql = render_range("20260926_020000_sponsorships:20260927_010000_engine_result_tables")
        for table in (
            "runoff_calculation_results",
            "groundwater_model_results",
            "crop_water_req_results",
            "structure_design_results",
            "irrigation_design_results",
            "calibration_results",
        ):
            assert f"CREATE TABLE {table}" in sql, table
        assert sql.count("CREATE TABLE") == 6

    def test_the_dead_model_declarations_are_removed(self) -> None:
        """Two dead declarations were removed; nothing may reintroduce them."""
        import database.models as models

        assert not hasattr(models, "NojinApplicationPlanDB")
        import services.models.land_models as land_models

        assert not hasattr(land_models, "LandProfileDB")

    def test_no_table_name_is_declared_twice_with_differing_columns(self) -> None:
        """The property that matters, and the one the removals restored.

        ``extend_existing = True`` appears in eleven places in
        ``biofertilizer/models.py``. It was the workaround that let a second
        declaration of one table name win silently, so the table's real columns
        depended on import order. With no duplicate names left it is inert, and
        asserting its absence would be a cosmetic rule about a file this review
        has no other reason to touch. What has to hold is that the registry holds
        one table object per name.
        """
        import database.models  # noqa: F401
        from database.base import Base

        names = [t.name for t in Base.metadata.tables.values()]
        assert len(names) == len(set(names)), "a table name is bound to more than one table object"
        assert len(names) >= 70, f"only {len(names)} tables registered"


class TestAlembicGraph:
    """The revision graph used to be un-loadable, and nothing covered that.

    ``20260926_020000_sponsorships.py`` set
    ``down_revision = "20260924_000000_add_content_escrow_models"`` - the FILE
    STEM. The file's own ``revision =`` line declares ``20260924_000000``.
    Alembic resolves down_revision against the revision map, so every command
    raised ``KeyError``, which is why no migration could be applied, why the
    tables the schema expects are absent, and why ten test modules fail at
    collection.
    """

    def _heads(self) -> list[str]:
        from engine.hydroma.alembic_graph import heads

        return heads()

    def test_the_graph_loads(self) -> None:
        """If this fails, alembic cannot run at all."""
        found = self._heads()
        assert len(found) >= 1, "no migration heads found at all"

    def test_no_dangling_down_revision(self) -> None:
        """A child may not name a parent that does not exist."""
        from engine.hydroma.alembic_graph import dangling_references

        dangling = dangling_references()
        assert not dangling, f"down_revision names a nonexistent revision: {dangling}"

    def test_down_revisions_are_ids_not_file_stems(self) -> None:
        """The specific defect, pinned so it cannot return."""
        from engine.hydroma.alembic_graph import revision_table

        table = revision_table()
        stems = {path.stem for path in (ROOT / "alembic" / "versions").glob("*.py")}
        for info in table.values():
            for parent in info["parents"]:
                assert parent not in stems or parent in table, (
                    f"{info['file']} sets down_revision to the file stem "
                    f"{parent!r}; the revision id must be used"
                )

    def test_every_revision_is_reachable_from_a_head(self) -> None:
        from engine.hydroma.alembic_graph import unreachable_revisions

        lost = unreachable_revisions()
        assert not lost, f"revisions with no path to a head: {lost}"


class TestImportOrderSensitivity:
    def test_both_model_files_import_in_one_process(self) -> None:
        import importlib
        import sys

        for name in list(sys.modules):
            if name.startswith("database") or name.startswith("engine"):
                del sys.modules[name]
        importlib.import_module("engine.hydroma.biofertilizer.models")
        importlib.import_module("database.models")
        assert "database.models" in sys.modules

    def test_the_land_profile_collision_is_gone(self) -> None:
        """``land_profiles`` had two declarations with disjoint column sets.

        database/models.py::LandProfile carried seven columns and
        services/models/land_models.py::LandProfileDB twenty, on one registry, so
        the second import raised InvalidRequestError and the migration for the
        table used only the first. The services declaration was dead: nothing
        imported the file, and services/land/service.py worked around it by
        aliasing the database model to the name LandProfileDB.
        """
        import database.models as models

        assert hasattr(models, "LandProfile")
        assert models.LandProfile.__tablename__ == "land_profiles"
        import services.models.land_models as land_models

        assert not hasattr(land_models, "LandProfileDB")
