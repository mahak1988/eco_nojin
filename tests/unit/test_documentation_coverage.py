"""Documentation coverage, measured rather than asserted.

Two failure modes this guards against:

1. A formula-bearing model ships without a registry record, so it has no stated
   provenance, no units, and no proof. The first survey found the opposite problem
   -- a registry holding only textbook formulas while the project's own
   composites were absent -- and the fix has to be enforced, not remembered.
2. A document is added without being reachable from the index, which is the same
   way the eight documents became scattered across four directories.

MACHINERY is deliberately not registered. A registry, a cache, a controller, a
base class or a dataclass is not a formula, and filing it as one is the category
error the survey made.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine.hydroma.formulas import all_records

REPO = Path(__file__).resolve().parents[2]

#: Modules this work introduced. Each must carry a module docstring.
#: Python modules this work introduced. Each must carry a module docstring.
CREATED_MODULES = [
    "engine/hydroma/formulas/__init__.py",
    "engine/hydroma/formulas/records.py",
    "engine/hydroma/formulas/registry.py",
    "engine/hydroma/formulas/catalog.py",
    "engine/hydroma/formulas/research/__init__.py",
    "engine/hydroma/models/validation/__init__.py",
    "engine/hydroma/models/validation/loader.py",
    "engine/hydroma/models/validation/runner.py",
    "scripts/run_cpp_tests.py",
    "scripts/run_tests.py",
    "scripts/doc_coverage.py",
    "tests/db_support.py",
]

#: Build scripts, which document themselves in REM comments rather than a
#: docstring, so they are checked for a header instead of parsed.
CREATED_SCRIPTS = [
    "engine/cpp_core/build_pybind.bat",
    "engine/cpp_core/build_tests.bat",
]

#: Narrative documents, each reachable from the index.
DOCUMENTS = [
    "docs/ENGINEERING_INDEX_FA.md",
    "engine/cpp_core/README_BUILD_STATUS_FA.md",
    "engine/hydroma/cpp_bridge/README_STATUS_FA.md",
    "engine/hydroma/formulas/README_STATUS_FA.md",
    "reports/TECHNICAL_AUDIT_FA_2026-09-25.md",
    "reports/REMEDIATION_PLAN_FA_2026-09-25.md",
    "reports/WAVE_3_INTEGRATION_PLAN_FA_2026-09-26.md",
    "reports/WBI_Q1_Q2_PLAN_FA_2026-09-26.md",
    "reports/OPEN_ITEMS_FA_2026-09-26.md",
]

#: Classes that compute but are not formulas, with the reason each is excluded.
MACHINERY = {
    "ModelRegistry": "registry of models, not an equation",
    "SQLiteCache": "storage, not an equation",
    "SimulationController": "dispatch, not an equation",
    "ScientificModel": "abstract base class",
    "ValidationResult": "result dataclass",
    "HYRUEParams": "parameter dataclass",
    "DroughtScenario": "scenario dataclass",
    "GlobalWatchdog": "orchestrator",
    "ClimateFetcher": "network fetch",
    "ScientificCalculator": "validator facade",
    "ModelInput": "input container, not an equation",
    "ModelOutput": "output container, not an equation",
}

#: Model directories that must be scanned for coverage.
MODEL_DIRS = [
    "engine/hydroma/models",
    "engine/hydroma/soil",
    "engine/hydroma/climate_adaptation",
    "engine/hydroma/simulation_env",
]

#: Registry key that covers a class whose own name differs. A record may cover a
#: family or a method rather than a class name, so this is the alias table, and it
#: is deliberately explicit: an alias that hides an unexamined gap is the failure
#: mode this test exists to catch.
ALIASES = {
    "WBIv3": "wbi_water_bankruptcy",
    "HLHS": "hlhs_landscape_health",
    "ESRI": "esri_salinity_risk",
    "HDVI": "hdvi_drought_vulnerability",
    "EWSI": "ewsi_water_stress",
    "HYRUE": "hyrue_stress_coupling",
    "ECSI": "rothc_moisture_modifier",
    "EPIA": "epia_precision_irrigation",
    "HPheno": "hpheno_phenology",
    "GroundwaterModel": "theis_groundwater",
    "RunoffCalculator": "scs_curve_number_runoff",
    "SpatialRunoffCalculator": "spatial_runoff",
    "MODFLOW6Model": "modflow6_groundwater_flow",
    "SWATPlusModel": "swatplus_watershed",
    "KGCv5": "koppen_geiger_class",
    # The climate_adaptation family: one record covers the five classes.
    "DynamicStressEngine": "climate_adaptation_stress_engine",
    "SoilDegradationModel": "climate_adaptation_stress_engine",
    "UncertaintyAndKnowledgeEngine": "climate_adaptation_stress_engine",
    "SeedOptimizationEngine": "climate_adaptation_stress_engine",
    "ClimateAdaptivePhenology": "climate_adaptation_stress_engine",
}

ACCESSORS = {
    "to_dict",
    "from_dict",
    "model_dump",
    "dict",
    "json",
    "validate",
    "get",
    "set",
    "copy",
    "items",
    "keys",
    "values",
    "register",
    "run",
    "execute",
    "close",
    "clear",
    "store",
    "load",
    "warm",
    "cfg",
    "draw",
}


def _is_formula_bearing(node: ast.ClassDef) -> bool:
    """A class that exposes a method doing work, not a dunder or a field getter."""
    if node.name.startswith("Test"):
        return False
    for item in node.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if item.name.startswith("_") or item.name in ACCESSORS:
            continue
        if len(item.body) == 1 and isinstance(item.body[0], ast.Return):
            ret = item.body[0].value
            if isinstance(ret, ast.Name) and ret.id in ("self", "_value", "value"):
                continue
        return True
    return False


def _compute_classes() -> dict[str, str]:
    found: dict[str, str] = {}
    for base in MODEL_DIRS:
        directory = REPO / base
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.py")):
            if "validation" in path.parts or "tests" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in tree.body:
                if (
                    isinstance(node, ast.ClassDef)
                    and node.name[0].isupper()
                    and _is_formula_bearing(node)
                ):
                    found.setdefault(node.name, f"{base}/{path.name}:{node.lineno}")
    return found


# --------------------------------------------------------------- the documents


@pytest.mark.parametrize("rel", DOCUMENTS)
def test_document_exists(rel: str):
    path = REPO / rel
    assert path.is_file(), f"missing document: {rel}"
    assert path.stat().st_size > 500, f"{rel} is too short to be a document"


@pytest.mark.parametrize(
    "rel",
    [
        "engine/cpp_core/build_pybind.bat",
        "engine/cpp_core/build_tests.bat",
        "scripts/run_cpp_tests.py",
        "scripts/run_tests.py",
        "scripts/doc_coverage.py",
        "tests/db_support.py",
    ],
)
def test_created_script_is_reachable_from_the_index(rel: str):
    """A build script nobody can find is a build script nobody runs."""
    index = (REPO / "docs/ENGINEERING_INDEX_FA.md").read_text(encoding="utf-8")
    assert Path(rel).name in index, f"{rel} is not linked from the documentation index"


def test_every_document_is_reachable_from_the_index():
    index = (REPO / "docs/ENGINEERING_INDEX_FA.md").read_text(encoding="utf-8")
    for rel in DOCUMENTS:
        if rel == "docs/ENGINEERING_INDEX_FA.md":
            continue
        name = rel.rsplit("/", 1)[-1]
        assert name in index, f"{rel} is not linked from the documentation index"


def test_the_index_states_the_three_distinctions():
    """The index is only useful if it carries the rules the documents rely on."""
    index = (REPO / "docs/ENGINEERING_INDEX_FA.md").read_text(encoding="utf-8")
    for token in ("standard", "composite", "novel", "verified", "divergent", "stub"):
        assert token in index, f"the index does not explain {token!r}"


# ----------------------------------------------------------------- the modules


@pytest.mark.parametrize("rel", CREATED_MODULES)
def test_created_module_has_a_docstring(rel: str):
    path = REPO / rel
    assert path.is_file(), f"missing module: {rel}"
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
    assert len(doc.strip()) >= 80, f"{rel} has no substantive module docstring"


@pytest.mark.parametrize("rel", CREATED_SCRIPTS)
def test_created_script_documents_itself(rel: str):
    """A batch file cannot carry a docstring, so it must carry a header."""
    path = REPO / rel
    assert path.is_file(), f"missing script: {rel}"
    head = path.read_text(encoding="utf-8", errors="replace")
    assert "REM " in head or "::" in head, f"{rel} has no explanatory header"
    assert len(head) > 400, f"{rel} is too short to explain what it builds"


# ------------------------------------------------------------------ coverage


def test_every_formula_bearing_model_is_registered():
    """A model that computes but has no record has no stated provenance."""
    registered = set(all_records())
    unregistered = []
    for name, where in _compute_classes().items():
        if name in MACHINERY or name in registered:
            continue
        if ALIASES.get(name) in registered:
            continue
        unregistered.append(f"{name} ({where})")

    assert not unregistered, "formula-bearing models missing a registry record:\n" + "\n".join(
        sorted(unregistered)
    )


def test_the_machinery_exclusions_are_justified():
    """An exclusion without a stated reason is an unexamined gap."""
    for name, reason in MACHINERY.items():
        assert reason, f"{name} has no reason recorded"
        assert not reason.startswith("see"), f"{name} points elsewhere: {reason!r}"


def test_no_registered_formula_is_unreachable():
    """A record whose module has gone is a stale claim."""
    registered = all_records()
    for quantity, record in registered.items():
        assert (REPO / record.canonical).is_file(), (
            f"{quantity} names a canonical module that does not exist: {record.canonical}"
        )


def test_no_as_built_document_contains_a_future_tense_claim():
    """The documents describe the present. A plan lives in reports/ instead.

    'will be' is allowed when it quotes a cited standard or a decision already
    recorded, so only the promise-like forms are rejected.
    """
    banned = ("to be implemented", "will be implemented", "coming soon", "in future work")
    for rel in DOCUMENTS:
        text = (REPO / rel).read_text(encoding="utf-8", errors="replace").lower()
        for phrase in banned:
            assert phrase not in text, f"{rel} promises {phrase!r} in an as-built document"
