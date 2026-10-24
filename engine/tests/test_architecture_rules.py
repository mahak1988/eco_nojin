"""Architecture import-guard rule tests (spec §3.3 / ECO-02 DoD / gap G-A6).

Covers every rule published by ``tools/detect_imports.py:get_rules()``:

* one positive test per rule proving the real ``engine/`` and ``services/``
  trees currently satisfy it (the same restricted scan the tool performs),
* at least three negative cases per rule exercising the scanner's AST check
  against temporary files, plus positive controls proving the sanctioned
  allowed paths (``engine.gateway``, ``database.config``, ``database.base``
  and the ``tools/import_guard_policy.json`` exceptions) stay unflagged,
* a data-driven proof that a new rule can be defined without changing the
  tool's code, and honest documentation of what still remains open.

The enforcement tool itself is imported by file path via ``importlib``
(``tools/`` is not a package) so its rule tables are never duplicated here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DETECT_IMPORTS_PATH = PROJECT_ROOT / "tools" / "detect_imports.py"
IMPORT_POLICY_PATH = PROJECT_ROOT / "tools" / "import_guard_policy.json"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
CI_WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
SPEC_PATH = PROJECT_ROOT / "docs/specs/ECO-NOJIN MASTER EXECUTION SPECIFICATION.md"

# Directories excluded by tools/detect_imports.py:scan_project().
EXCLUDED_DIRS = {"__pycache__", ".venv", "venv", "node_modules", "build", "dist", ".eggs"}


def _load_detect_imports():
    """Import the enforcement tool by file path (tools/ is not a package)."""
    spec = importlib.util.spec_from_file_location("detect_imports_under_test", DETECT_IMPORTS_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load enforcement tool from {DETECT_IMPORTS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


di = _load_detect_imports()
RULES = di.get_rules()
RULE_IDS = [rule.id for rule in RULES]

NEGATIVE_CASES: list[dict[str, object]] = [
    # ENGINE_NO_SERVICES (INV-016) --------------------------------------------------
    {
        "id": "engine_no_services__from_services_auth",
        "rule": "ENGINE_NO_SERVICES",
        "path": "engine/mod_neg_services_from.py",
        "imports": ["from services.auth import login"],
        "flagged": True,
    },
    {
        "id": "engine_no_services__import_services_auth",
        "rule": "ENGINE_NO_SERVICES",
        "path": "engine/mod_neg_services_import.py",
        "imports": ["import services.auth"],
        "flagged": True,
    },
    {
        "id": "engine_no_services__deep_router_import",
        "rule": "ENGINE_NO_SERVICES",
        "path": "engine/mod_neg_services_deep.py",
        "imports": ["from services.api_gateway.routers.auth_supabase import verify_token"],
        "flagged": True,
    },
    {
        "id": "engine_no_services__allowed_control_engine_hydroma",
        "rule": "ENGINE_NO_SERVICES",
        "path": "engine/mod_pos_services_control.py",
        "imports": ["import engine.hydroma"],
        "flagged": False,
    },
    # ENGINE_NO_DATABASE (INV-002, sanctioned bridge database.config/database.base) ---
    {
        "id": "engine_no_database__from_models_base",
        "rule": "ENGINE_NO_DATABASE",
        "path": "engine/mod_neg_db_models.py",
        "imports": ["from database.models import Base"],
        "flagged": True,
    },
    {
        "id": "engine_no_database__from_hub",
        "rule": "ENGINE_NO_DATABASE",
        "path": "engine/mod_neg_db_hub.py",
        "imports": ["from database.hub import Hub"],
        "flagged": True,
    },
    {
        "id": "engine_no_database__bare_import_database",
        "rule": "ENGINE_NO_DATABASE",
        "path": "engine/mod_neg_db_bare.py",
        "imports": ["import database"],
        "flagged": True,
    },
    {
        "id": "engine_no_database__allowed_control_config",
        "rule": "ENGINE_NO_DATABASE",
        "path": "engine/mod_pos_db_config.py",
        "imports": ["from database.config import get_settings"],
        "flagged": False,
    },
    {
        "id": "engine_no_database__allowed_control_base",
        "rule": "ENGINE_NO_DATABASE",
        "path": "engine/mod_pos_db_base.py",
        "imports": ["from database.base import Base"],
        "flagged": False,
    },
    # ENGINE_NO_FRONTEND (INV-003) ---------------------------------------------------
    {
        "id": "engine_no_frontend__import_frontend",
        "rule": "ENGINE_NO_FRONTEND",
        "path": "engine/mod_neg_frontend.py",
        "imports": ["import frontend"],
        "flagged": True,
    },
    {
        "id": "engine_no_frontend__from_ui_layout",
        "rule": "ENGINE_NO_FRONTEND",
        "path": "engine/mod_neg_ui.py",
        "imports": ["from ui.layout import render_page"],
        "flagged": True,
    },
    {
        "id": "engine_no_frontend__from_dashboard_app",
        "rule": "ENGINE_NO_FRONTEND",
        "path": "engine/mod_neg_dashboard.py",
        "imports": ["from dashboard.app import create_dashboard"],
        "flagged": True,
    },
    {
        "id": "engine_no_frontend__allowed_control_engine_hydroma",
        "rule": "ENGINE_NO_FRONTEND",
        "path": "engine/mod_pos_frontend_control.py",
        "imports": ["import engine.hydroma"],
        "flagged": False,
    },
    # ENGINE_NO_AUTH ----------------------------------------------------------------
    {
        "id": "engine_no_auth__import_auth",
        "rule": "ENGINE_NO_AUTH",
        "path": "engine/mod_neg_auth.py",
        "imports": ["import auth"],
        "flagged": True,
    },
    {
        "id": "engine_no_auth__from_authentication",
        "rule": "ENGINE_NO_AUTH",
        "path": "engine/mod_neg_authentication.py",
        "imports": ["from authentication.middleware import require_user"],
        "flagged": True,
    },
    {
        "id": "engine_no_auth__from_auth_jwt",
        "rule": "ENGINE_NO_AUTH",
        "path": "engine/mod_neg_auth_jwt.py",
        "imports": ["from auth.jwt import decode_token"],
        "flagged": True,
    },
    {
        "id": "engine_no_auth__allowed_control_engine_hydroma",
        "rule": "ENGINE_NO_AUTH",
        "path": "engine/mod_pos_auth_control.py",
        "imports": ["import engine.hydroma"],
        "flagged": False,
    },
    # ENGINE_NO_PAYMENT -------------------------------------------------------------
    {
        "id": "engine_no_payment__import_payment",
        "rule": "ENGINE_NO_PAYMENT",
        "path": "engine/mod_neg_payment.py",
        "imports": ["import payment"],
        "flagged": True,
    },
    {
        "id": "engine_no_payment__import_stripe",
        "rule": "ENGINE_NO_PAYMENT",
        "path": "engine/mod_neg_stripe.py",
        "imports": ["import stripe"],
        "flagged": True,
    },
    {
        "id": "engine_no_payment__from_paypal_api",
        "rule": "ENGINE_NO_PAYMENT",
        "path": "engine/mod_neg_paypal.py",
        "imports": ["from paypal.api import create_charge"],
        "flagged": True,
    },
    {
        "id": "engine_no_payment__allowed_control_engine_hydroma",
        "rule": "ENGINE_NO_PAYMENT",
        "path": "engine/mod_pos_payment_control.py",
        "imports": ["import engine.hydroma"],
        "flagged": False,
    },
    # ENGINE_NO_BLOCKCHAIN ----------------------------------------------------------
    {
        "id": "engine_no_blockchain__import_blockchain",
        "rule": "ENGINE_NO_BLOCKCHAIN",
        "path": "engine/mod_neg_blockchain.py",
        "imports": ["import blockchain"],
        "flagged": True,
    },
    {
        "id": "engine_no_blockchain__from_web3",
        "rule": "ENGINE_NO_BLOCKCHAIN",
        "path": "engine/mod_neg_web3.py",
        "imports": ["from web3 import Web3"],
        "flagged": True,
    },
    {
        "id": "engine_no_blockchain__from_smart_contract_abi",
        "rule": "ENGINE_NO_BLOCKCHAIN",
        "path": "engine/mod_neg_smart_contract.py",
        "imports": ["from smart_contract.abi import load_abi"],
        "flagged": True,
    },
    {
        "id": "engine_no_blockchain__allowed_control_engine_hydroma",
        "rule": "ENGINE_NO_BLOCKCHAIN",
        "path": "engine/mod_pos_blockchain_control.py",
        "imports": ["import engine.hydroma"],
        "flagged": False,
    },
    # AI_NO_ENGINE_INTERNALS (files below services/ai/) ------------------------------
    {
        "id": "ai_no_engine_internals__soil_physics",
        "rule": "AI_NO_ENGINE_INTERNALS",
        "path": "services/ai/mod_neg_soil_physics.py",
        "imports": ["from engine.hydroma.soil.physics import compute_water_balance"],
        "flagged": True,
    },
    {
        "id": "ai_no_engine_internals__cpp_core",
        "rule": "AI_NO_ENGINE_INTERNALS",
        "path": "services/ai/mod_neg_cpp_core.py",
        "imports": ["import engine.cpp_core"],
        "flagged": True,
    },
    {
        "id": "ai_no_engine_internals__ports",
        "rule": "AI_NO_ENGINE_INTERNALS",
        "path": "services/ai/mod_neg_ports.py",
        "imports": ["from engine.ports import PersistencePort"],
        "flagged": True,
    },
    {
        "id": "ai_no_engine_internals__allowed_control_gateway",
        "rule": "AI_NO_ENGINE_INTERNALS",
        "path": "services/ai/mod_pos_gateway_control.py",
        "imports": ["from engine.gateway import EngineGateway"],
        "flagged": False,
    },
    # SERVICES_NO_ENGINE_INTERNALS (INV-003, policy exceptions) ---------------------
    {
        "id": "services_no_engine_internals__cpp_core",
        "rule": "SERVICES_NO_ENGINE_INTERNALS",
        "path": "services/mod_neg_cpp_core.py",
        "imports": ["from engine.cpp_core import run_batch"],
        "flagged": True,
    },
    {
        "id": "services_no_engine_internals__ports",
        "rule": "SERVICES_NO_ENGINE_INTERNALS",
        "path": "services/mod_neg_ports.py",
        "imports": ["from engine.ports import compute_port"],
        "flagged": True,
    },
    {
        "id": "services_no_engine_internals__soil_chemistry",
        "rule": "SERVICES_NO_ENGINE_INTERNALS",
        "path": "services/mod_neg_soil_chemistry.py",
        "imports": ["from engine.hydroma.soil.chemistry import decompose"],
        "flagged": True,
    },
    {
        "id": "services_no_engine_internals__allowed_control_config_settings",
        "rule": "SERVICES_NO_ENGINE_INTERNALS",
        "path": "services/mod_pos_config_settings.py",
        "imports": ["from engine.hydroma.config.settings import get_settings"],
        "flagged": False,
    },
    {
        "id": "services_no_engine_internals__allowed_control_config_rules",
        "rule": "SERVICES_NO_ENGINE_INTERNALS",
        "path": "services/mod_pos_config_rules.py",
        "imports": ["from engine.hydroma.config.rules import load_rules"],
        "flagged": False,
    },
    {
        "id": "services_no_engine_internals__allowed_control_gateway",
        "rule": "SERVICES_NO_ENGINE_INTERNALS",
        "path": "services/mod_pos_gateway.py",
        "imports": ["from engine.gateway import EngineGateway"],
        "flagged": False,
    },
    {
        "id": "services_no_engine_internals__allowed_control_policy_gap_carbon",
        "rule": "SERVICES_NO_ENGINE_INTERNALS",
        "path": "services/mod_pos_carbon.py",
        "imports": ["from engine.hydroma.carbon.calculator import carbon_sequestration"],
        "flagged": False,
    },
]


def scan_imports(
    tmp_path: Path,
    rel_path: str,
    import_lines: list[str],
    # The tool's Rule/Violation classes only exist at runtime (the module is
    # loaded by path), so their shapes are Any here.
    rules: list[Any] | None = None,
) -> list[Any]:
    """Write a temporary module at ``rel_path`` and run the tool's AST check.

    The file is created below ``tmp_path`` (mirroring the project layout, e.g.
    ``engine/mod.py`` or ``services/ai/mod.py``) and analysed with
    ``detect_imports.analyze_file`` against ``detect_imports.get_rules()``
    (or an explicit rule list), returning the detected violations.
    """
    target = tmp_path / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(import_lines) + "\n", encoding="utf-8")
    found: list[Any] = di.analyze_file(target, RULES if rules is None else rules, tmp_path)
    return found


@pytest.mark.parametrize("case", NEGATIVE_CASES, ids=[str(case["id"]) for case in NEGATIVE_CASES])
def test_architecture_rule_negative_case(case, tmp_path):
    violations = scan_imports(tmp_path, str(case["path"]), list(case["imports"]))  # type: ignore[arg-type]
    flagged_rule_ids = {v.rule_id for v in violations}

    if case["flagged"]:
        assert case["rule"] in flagged_rule_ids, (
            f"{case['id']}: expected {case['rule']} to be flagged, got {sorted(flagged_rule_ids)}"
        )
    else:
        assert not flagged_rule_ids, (
            f"{case['id']}: expected no violations, got "
            f"{[(v.rule_id, v.import_statement) for v in violations]}"
        )


@pytest.fixture(scope="module")
def real_tree_violations() -> tuple[list[Any], int]:
    """Scan the real engine/ and services/ trees like the tool's main path.

    Restricted to those two directories (no .venv walk); test files and the
    policy-sanctioned facade files are skipped exactly as
    ``detect_imports.scan_project`` skips them.
    """
    rules = RULES
    policy_rules = di.load_import_policy()["rules"]
    facade_files = {
        entry["path"] for entry in policy_rules["SERVICES_NO_ENGINE_INTERNALS"]["facade_files"]
    }
    violations: list[Any] = []
    scanned = 0
    for top in ("engine", "services"):
        for py_file in sorted((PROJECT_ROOT / top).rglob("*.py")):
            rel = py_file.relative_to(PROJECT_ROOT)
            if any(part in EXCLUDED_DIRS for part in rel.parts):
                continue
            if di.is_test_file(str(rel)) or rel.as_posix() in facade_files:
                continue
            scanned += 1
            violations.extend(di.analyze_file(py_file, rules, PROJECT_ROOT))
    return violations, scanned


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_real_tree_satisfies_rule(rule_id, real_tree_violations):
    violations, scanned = real_tree_violations
    assert scanned > 100, "real-tree scan covered too few production files to be meaningful"
    offending = [v for v in violations if v.rule_id == rule_id]
    assert offending == [], (
        f"{rule_id} violated by {len(offending)} file(s): "
        f"{[(v.file, v.line) for v in offending[:10]]}"
    )


def test_new_rule_can_be_defined_as_data_without_tool_code_changes(tmp_path):
    """Spec §3.3: new architectural rules must be definable without code changes."""
    ad_hoc_rule = di.Rule(
        id="AD_HOC_NO_SERVICES_FROM_ENGINE",
        name="ad-hoc data-defined probe rule",
        description="Proves get_rules() entries are pure data the scanner applies as-is.",
        source_module="engine",
        forbidden_prefixes=["services"],
        mode="FORBIDDEN_ALL",
        rationale="spec 3.3: data-driven rule definition",
    )
    violations = scan_imports(
        tmp_path,
        "engine/mod_ad_hoc.py",
        ["from services.auth import login"],
        rules=[ad_hoc_rule],
    )
    assert [v.rule_id for v in violations] == [ad_hoc_rule.id]


def test_every_rule_has_at_least_three_negative_cases():
    """ECO-02 DoD: at least three negative cases for every enforced rule."""
    flagged_per_rule = Counter(str(c["rule"]) for c in NEGATIVE_CASES if c["flagged"])
    for rule_id in RULE_IDS:
        assert flagged_per_rule[rule_id] >= 3, (
            f"{rule_id} has {flagged_per_rule[rule_id]} negative case(s), DoD requires 3"
        )


def test_policy_exception_rule_ids_are_covered_by_negative_cases():
    """Guard against policy drift in tools/import_guard_policy.json.

    Every rule id that carries exceptions in the policy must also be
    exercised by the negative-case table above.
    """
    policy = json.loads(IMPORT_POLICY_PATH.read_text(encoding="utf-8"))
    policy_rule_ids = set(policy.get("rules", {}))
    assert policy_rule_ids, "import_guard_policy.json must declare at least one rule"
    covered = {str(c["rule"]) for c in NEGATIVE_CASES}
    assert policy_rule_ids - covered == set(), (
        f"policy rule ids without negative coverage: {sorted(policy_rule_ids - covered)}"
    )


def test_spec_architecture_enforcement_not_connected_to_ci_yet():
    """Document the residual gap G-A6 (reports/eco-nojin/GAP-REGISTER.md).

    Spec §3.3 / ECO-02 DoD required the enforcement tool to be data-driven,
    carry >= 3 negative tests per rule and run in CI. For the project's INV
    rules those requirements are now met here, and this test pins them:

    * data-driven rules — asserted behaviourally by
      ``test_new_rule_can_be_defined_as_data_without_tool_code_changes``;
    * >= 3 negative cases per rule — asserted by
      ``test_every_rule_has_at_least_three_negative_cases``;
    * CI connected — the guard runs as a blocking CI step and this file is
      collected by the default pytest run (pyproject ``testpaths``).

    The one part of G-A6 still open is the naming: the enforcement tool ships
    its rules as ENGINE_*/AI_*/SERVICES_* ids with INV-* rationales, while the
    spec §3.2 table (AR-01..AR-10) is defined in architecture/rules.yaml; the
    AR -> tool-rule mapping is not yet expressed inside
    tools/detect_imports.py itself.
    """
    rules = RULES
    assert len(rules) >= 8
    assert set(RULE_IDS) >= {str(c["rule"]) for c in NEGATIVE_CASES}

    flagged_per_rule = Counter(str(c["rule"]) for c in NEGATIVE_CASES if c["flagged"])
    assert all(flagged_per_rule[rule_id] >= 3 for rule_id in RULE_IDS)

    ci_text = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "detect_imports.py" in ci_text, "architecture import guard must run in CI"
    assert "pytest engine" in ci_text, "engine tests (including this file) must run in CI"
    assert '"engine/tests"' in PYPROJECT_PATH.read_text(encoding="utf-8")

    spec_text = SPEC_PATH.read_text(encoding="utf-8")
    assert "AR-01" in spec_text and "AR-10" in spec_text
    # G-A6 residual: AR-01..AR-10 naming is still absent from the enforcement tool.
    spec_rule_ids = {f"AR-{n:02d}" for n in range(1, 11)}
    assert set(RULE_IDS).isdisjoint(spec_rule_ids)
