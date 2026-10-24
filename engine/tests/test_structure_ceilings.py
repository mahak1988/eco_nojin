"""Structure ceilings for the engine/services trees (remediation items C-4, B-1).

These are *ratchets*, not aspirations: each one measures the tree as it is
today, pins that measurement in this file, and fails on the first new
offender. Shrinking a measured set requires editing the constant below, which
is the intended friction (a debt count that can only change deliberately),
and every transitional allowlist carries a ``shrink_by`` date in the future.

Ceilings measured on 2026-10-11 (``engine/tests`` + ``services/`` walk):

* over 800 lines: 44 modules (23 under ``engine/``, 21 under ``services/``)
* over 1200 lines under ``engine/gateway/``: 1 module (``__init__.py``, 3117
  lines) — the A-1 gateway split
* engine files importing ``requests``/``httpx``/``urllib.request`` outside the
  sanctioned ingestion area: 8 (16 ingestion files are whitelisted by design)

Nothing here imports engine or services logic except ``engine.honesty`` (a
stdlib-only vocabulary module) and the ``tools/`` scripts, which are run as
subprocesses: the ceilings must hold for code that is merely *present*, not
only for code that imports cleanly.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from engine.honesty import AR_RULES, BRAKES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = PROJECT_ROOT / "tools" / "import_guard_policy.json"
EXPIRY_TOOL_PATH = PROJECT_ROOT / "tools" / "check_policy_expiry.py"

#: Date the measurements below were taken.
MEASURED_ON = date(2026, 10, 11)

#: The date every transitional allowlist in this file must be gone by.
ALLOWLIST_DEADLINE = date(2027, 1, 31)

#: Line ceiling for the gateway package (spec §3.1 / A-2 step 4).
GATEWAY_CEILING = 1200

#: Line ceiling for every other module: no *new* module may exceed it.
MODULE_CEILING = 800

#: Transitional gateway allowlist: module -> shrink-by date. Non-empty on
#: purpose; an empty dict would make the ceiling unconditional and fail today.
GATEWAY_SPLIT_ALLOWLIST: dict[str, str] = {
    "engine/gateway/__init__.py": "2027-01-31",
    "engine/gateway/model_dispatcher.py": "2027-01-31",
}

#: Every module over 800 lines measured on 2026-10-11 (44 modules: 23 in
#: engine/, 21 in services/). A module not on this list that exceeds the
#: ceiling is new debt and fails the test.
LEGACY_LARGE_MODULES: frozenset[str] = frozenset(
    {
        "engine/gateway/model_dispatcher.py",
        "engine/tasmimyar/__init__.py",
        "engine/gateway/__init__.py",
        "engine/hydroma/biofertilizer/advanced_calculator.py",
        "engine/hydroma/biofertilizer/data/materials_data.py",
        "engine/hydroma/biofertilizer/repositories.py",
        "engine/hydroma/config/settings.py",
        "engine/hydroma/cpp_bridge/__init__.py",
        "engine/hydroma/data_pipeline/pipeline.py",
        "engine/hydroma/formulas/catalog.py",
        "engine/hydroma/formulas/research/__init__.py",
        "engine/hydroma/models/validation/runner.py",
        "engine/hydroma/production/deployment.py",
        "engine/hydroma/scenario_composite/engine.py",
        "engine/hydroma/scenario_composite/models_additions.py",
        "engine/hydroma/watershed/calculator.py",
        "engine/land/reference/data.py",
        "engine/models/registry.py",
        "engine/scientific_verification/__init__.py",
        "engine/strict_tests/test_s11_parity_tripwires.py",
        "engine/strict_tests/test_s16_gateway_strict_contracts.py",
        "engine/strict_tests/test_s19_plant_neuro_validation.py",
        "engine/tests/test_decision_economic_criteria.py",
        "engine/tests/test_unwired_model_wiring.py",
        "services/_gateway_facade.py",
        "services/ai/hydroma_rag.py",
        "services/api_gateway/main.py",
        "services/api_gateway/routers/auth.py",
        "services/api_gateway/routers/auth_supabase.py",
        "services/api_gateway/routers/dashboard.py",
        "services/api_gateway/routers/hydroma_dashboard.py",
        "services/api_gateway/routers/marketplace.py",
        "services/api_gateway/routers/village_hub.py",
        "services/api_gateway/tests/test_webhook_hmac_and_asvs.py",
        "services/auth_legacy/service.py",
        "services/commerce/service.py",
        "services/commerce/tests/test_properties_order_money.py",
        "services/finance/routers/finance.py",
        "services/finance/tests/test_properties_money.py",
        "services/inventory/service.py",
        "services/inventory/tests/test_lots_fefo_expiry.py",
        "services/inventory/tests/test_properties_valuation.py",
        "services/marketplace/hub_service.py",
        "services/marketplace/models/village_hub.py",
        "services/marketplace/tests/test_hub_service.py",
        "services/satellite/sentinel2_provider.py",
        "services/security/tests/test_security_remediation.py",
    }
)

#: The count recorded when the list above was measured; kept in sync by the test.
LEGACY_LARGE_MODULES_RECORDED_COUNT = 47

#: Network libraries whose import inside ``engine/`` must be justified.
NETWORK_IMPORTS = frozenset({"requests", "httpx", "urllib.request"})

#: The only place the engine is allowed to talk to the network: the ingestion
#: pipeline, whose downloads pass through ``note_download``.
INGESTION_ROOT = PROJECT_ROOT / "engine" / "hydroma" / "data_pipeline"
DOWNLOAD_GATE_CALL = "note_download("

#: Engine files that import a network library without being sanctioned
#: ingestion code (8 files measured on 2026-10-11). Offline-capable weather /
#: satellite / MRV fetchers and two tests still reach the network directly;
#: they are pinned here so a *new* direct call fails the test.
NETWORK_IMPORT_OFFENDERS: frozenset[str] = frozenset(
    {
        "engine/hydroma/biofertilizer/tests/test_nojin_comprehensive.py",
        "engine/hydroma/models/global_watchdog/climate_fetcher.py",
        "engine/hydroma/mrv/satellite_cdse.py",
        "engine/hydroma/satellite/providers/earth_search.py",
        "engine/hydroma/satellite/providers/nasa_power.py",
        "engine/hydroma/simulation/weather_source.py",
        "engine/land/integration/climate_integrator.py",
        "engine/tests/test_unwired_model_wiring.py",
    }
)

#: Engine files sanctioned to import a network library (16 files measured on
#: 2026-10-11): everything under ``engine/hydroma/data_pipeline/`` that
#: performs or tests ingestion.
NETWORK_IMPORT_WHITELIST: frozenset[str] = frozenset(
    {
        "engine/hydroma/data_pipeline/connectors/cds_connector.py",
        "engine/hydroma/data_pipeline/connectors/era5_connector.py",
        "engine/hydroma/data_pipeline/connectors/grdc_connector.py",
        "engine/hydroma/data_pipeline/connectors/igrac_connector.py",
        "engine/hydroma/data_pipeline/connectors/market_price_connector.py",
        "engine/hydroma/data_pipeline/connectors/usgs_nwis_connector.py",
        "engine/hydroma/data_pipeline/connectors/wapor_connector.py",
        "engine/hydroma/data_pipeline/pipeline.py",
        "engine/hydroma/data_pipeline/tests/test_cds_connector.py",
        "engine/hydroma/data_pipeline/tests/test_cgls_connector.py",
        "engine/hydroma/data_pipeline/tests/test_era5_connector.py",
        "engine/hydroma/data_pipeline/tests/test_grdc_connector.py",
        "engine/hydroma/data_pipeline/tests/test_igrac_connector.py",
        "engine/hydroma/data_pipeline/tests/test_market_price_connector.py",
        "engine/hydroma/data_pipeline/tests/test_usgs_nwis_connector.py",
        "engine/hydroma/data_pipeline/tests/test_wapor_connector.py",
    }
)

#: Sanctioned carve-outs in tools/import_guard_policy.json (6 service + 2
#: engine, matching the policy's ratchet.max_allowed_imports).
POLICY_EXPECTED_ENTRIES = 8


def _python_files(*relative_dirs: str) -> list[Path]:
    """Every ``.py`` below the given top-level directories, deterministically."""
    found: list[Path] = []
    for relative in relative_dirs:
        found.extend((PROJECT_ROOT / relative).rglob("*.py"))
    return sorted(path for path in found if "__pycache__" not in path.parts)


def _relative(path: Path) -> str:
    """Repo-relative POSIX path, the form every constant in this file uses."""
    return path.relative_to(PROJECT_ROOT).as_posix()


def _line_count(path: Path) -> int:
    """Number of lines in a file (universal newlines, never raising on odd bytes)."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def _assert_allowlist_dates_are_open(allowlist: dict[str, str]) -> None:
    """Every transitional allowlist must be explicit, dated and still open."""
    assert allowlist, "transitional allowlist must be explicit (an empty one hides a ceiling)"
    for entry, shrink_by in sorted(allowlist.items()):
        shrink = date.fromisoformat(shrink_by)
        assert MEASURED_ON < shrink <= ALLOWLIST_DEADLINE, (
            f"{entry}: shrink_by {shrink_by} must be after {MEASURED_ON.isoformat()} "
            f"and no later than {ALLOWLIST_DEADLINE.isoformat()}"
        )


def _imported_network_modules(tree: ast.AST) -> set[str]:
    """Root network modules imported anywhere in a parsed module."""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            candidates = [node.module or ""]
        else:
            continue
        for candidate in candidates:
            if candidate in NETWORK_IMPORTS or candidate.split(".")[0] in {"requests", "httpx"}:
                found.add(candidate)
    return found


def _is_sanctioned_ingestion(path: Path) -> bool:
    """True for the ingestion area, or any file that gates a download."""
    if path.is_relative_to(INGESTION_ROOT):
        return True
    source = path.read_text(encoding="utf-8", errors="replace")
    return DOWNLOAD_GATE_CALL in source


def test_no_gateway_module_over_1200_lines():
    """No module under ``engine/gateway/`` exceeds 1200 lines (A-2 step 4).

    ``engine/gateway/__init__.py`` is 3117 lines today, so the ceiling is
    transitional: an oversized module must be on ``GATEWAY_SPLIT_ALLOWLIST``
    with a ``shrink_by`` date that is in the future and no later than
    2027-01-31. The allowlist itself must be non-empty and future-dated, so
    silently deleting it (or letting it rot) fails too.
    """
    _assert_allowlist_dates_are_open(GATEWAY_SPLIT_ALLOWLIST)

    counts: dict[str, int] = {}
    oversized: list[str] = []
    for path in _python_files("engine/gateway"):
        relative = _relative(path)
        lines = _line_count(path)
        counts[relative] = lines
        if lines > GATEWAY_CEILING:
            oversized.append(relative)

    detail = ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
    print(f"engine/gateway line counts: {detail}")

    assert oversized, "the transitional allowlist must correspond to a measured oversized module"
    for relative in sorted(oversized):
        assert relative in GATEWAY_SPLIT_ALLOWLIST, (
            f"{relative} is over {GATEWAY_CEILING} lines and not on GATEWAY_SPLIT_ALLOWLIST "
            "(A-1 gateway split pending)"
        )


def test_no_new_module_over_800_lines():
    """No new module anywhere exceeds 800 lines.

    Measured on 2026-10-11: 44 modules over 800 lines (23 under ``engine/``,
    21 under ``services/``), every one of them pinned in
    ``LEGACY_LARGE_MODULES``. A module that grows past the ceiling without
    being on that list is new debt and fails; shrinking the list is a
    deliberate edit, which is how the count is meant to come down.
    """
    oversized: list[str] = []
    for path in _python_files("engine", "services"):
        if _line_count(path) > MODULE_CEILING:
            oversized.append(_relative(path))

    new_offenders = sorted(set(oversized) - LEGACY_LARGE_MODULES)
    assert new_offenders == [], (
        f"{len(new_offenders)} module(s) exceed {MODULE_CEILING} lines without being on "
        f"LEGACY_LARGE_MODULES: {new_offenders}"
    )

    stale = sorted(LEGACY_LARGE_MODULES - set(oversized))
    if stale:  # not a failure: a shrunk or deleted module just leaves the pin behind
        print(f"stale LEGACY_LARGE_MODULES entries ({len(stale)}): {stale}")

    assert len(LEGACY_LARGE_MODULES) == LEGACY_LARGE_MODULES_RECORDED_COUNT, (
        "LEGACY_LARGE_MODULES changed size: re-measure (was "
        f"{LEGACY_LARGE_MODULES_RECORDED_COUNT} on {MEASURED_ON.isoformat()})"
    )
    print(
        f"modules over {MODULE_CEILING} lines: {len(oversized)} "
        f"(recorded {LEGACY_LARGE_MODULES_RECORDED_COUNT})"
    )


def test_no_network_import_outside_ingestion():
    """``requests``/``httpx``/``urllib.request`` in ``engine/`` only for ingestion.

    The engine is an offline scientific calculator: its only sanctioned
    network code is ``engine/hydroma/data_pipeline/``, whose downloads pass
    through ``note_download`` (``engine/hydroma/data_pipeline/download_gate.py``).
    Measured on 2026-10-11: 16 sanctioned ingestion files import a network
    library, and 8 engine files do so outside that area (weather / satellite /
    MRV fetchers plus two tests) — pinned in ``NETWORK_IMPORT_OFFENDERS`` so a
    *new* direct call fails while the existing debt stays visible.
    """
    importers: dict[str, set[str]] = {}
    for path in _python_files("engine"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except SyntaxError:
            continue
        modules = _imported_network_modules(tree)
        if modules:
            importers[_relative(path)] = modules

    sanctioned = sorted(path for path in importers if _is_sanctioned_ingestion(PROJECT_ROOT / path))
    offenders = sorted(set(importers) - set(sanctioned))

    new_offenders = sorted(set(offenders) - NETWORK_IMPORT_OFFENDERS)
    assert new_offenders == [], (
        f"{len(new_offenders)} engine file(s) import a network library outside the ingestion "
        f"pipeline and are not on NETWORK_IMPORT_OFFENDERS: {new_offenders}"
    )
    resolved = sorted(NETWORK_IMPORT_OFFENDERS - set(offenders))
    if resolved:  # not a failure: drop the entry from NETWORK_IMPORT_OFFENDERS when clean
        print(f"resolved NETWORK_IMPORT_OFFENDERS entries ({len(resolved)}): {resolved}")

    assert sanctioned == sorted(NETWORK_IMPORT_WHITELIST), (
        "the sanctioned ingestion set changed: re-measure NETWORK_IMPORT_WHITELIST "
        f"(was {len(NETWORK_IMPORT_WHITELIST)} files); sanctioned now: {sanctioned}"
    )
    print(
        f"network importers under engine/: {len(importers)} "
        f"({len(sanctioned)} sanctioned ingestion, {len(offenders)} pinned offenders)"
    )


def test_policy_entries_have_expiry():
    """Every carve-out in the policy is dated and justified (B-1).

    Enforcement lives in ``tools/detect_imports.py``; the dates live in
    ``tools/import_guard_policy.json``. Both ``rules.<RULE>.allowed_imports``
    entry lists (the 6 service carve-outs and the 2 engine persistence-bridge
    ones) must carry ``expires`` and ``rationale``, every date must parse and
    stay within the policy's own deadline, and the total must equal the
    ratchet's ``max_allowed_imports``.
    """
    policy: dict[str, Any] = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    rules = policy.get("rules")
    assert isinstance(rules, dict) and rules, "import_guard_policy.json must declare rules"

    ratchet = policy.get("ratchet")
    assert isinstance(ratchet, dict), "policy must carry a top-level ratchet block"
    for key in ("max_allowed_imports", "hard_cap", "next_review"):
        assert key in ratchet, f"ratchet.{key} is missing (B-1)"

    missing: list[str] = []
    total = 0
    for rule_id in sorted(rules):
        entries = rules[rule_id].get("allowed_imports", [])
        for entry in entries:
            total += 1
            module = entry.get("module", "<unnamed>")
            if not entry.get("expires"):
                missing.append(f"{rule_id}:{module}:expires")
            if not entry.get("rationale"):
                missing.append(f"{rule_id}:{module}:rationale")
    assert missing == [], f"policy entries missing expires/rationale: {missing}"

    assert total == POLICY_EXPECTED_ENTRIES, (
        f"expected {POLICY_EXPECTED_ENTRIES} dated carve-outs (6 service + 2 engine), found {total}"
    )
    assert total == ratchet["max_allowed_imports"], (
        "dated entry count must equal ratchet.max_allowed_imports: adding a carve-out means "
        "removing one"
    )
    assert total <= ratchet["hard_cap"], "carve-out count exceeds ratchet.hard_cap"

    for rule_id in sorted(rules):
        for entry in rules[rule_id].get("allowed_imports", []):
            expires = date.fromisoformat(entry["expires"])
            assert MEASURED_ON < expires <= ALLOWLIST_DEADLINE, (
                f"{rule_id}:{entry.get('module')}: expires {entry['expires']} must be current and "
                f"no later than {ALLOWLIST_DEADLINE.isoformat()}"
            )
    print(
        f"policy carve-outs: {total}/{ratchet['max_allowed_imports']} "
        f"(hard cap {ratchet['hard_cap']})"
    )


def test_honesty_vocabulary_cannot_shrink():
    """The claim-status vocabulary is a contract, not a convenience.

    10 brakes and 13 architecture-review rules: the point is that a recorded
    result cannot silently be promoted to a validated one, and that the
    vocabulary itself cannot be trimmed to make a report look greener.
    """
    assert len(BRAKES) == 10, f"expected 10 brakes, found {len(BRAKES)}"
    assert len(AR_RULES) == 13, f"expected 13 AR rules, found {len(AR_RULES)}"


def test_policy_expiry_tool_passes():
    """``tools/check_policy_expiry.py`` (B-1) is wired and currently green.

    Runs the real tool as a subprocess — the same invocation the CI
    ``structure`` job uses — in both its text and ``--json`` forms, so a tool
    that crashes or silently stops failing the build is caught here.
    """
    result = subprocess.run(
        [sys.executable, str(EXPIRY_TOOL_PATH)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, (
        f"check_policy_expiry.py failed:\n{result.stdout}\n{result.stderr}"
    )
    assert "status: PASS" in result.stdout

    machine = subprocess.run(
        [sys.executable, str(EXPIRY_TOOL_PATH), "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert machine.returncode == 0, machine.stderr
    payload = json.loads(machine.stdout)
    assert payload["entries_total"] == POLICY_EXPECTED_ENTRIES
    assert payload["exit_code"] == 0
    print(
        f"check_policy_expiry.py: {payload['entries_total']} entries, "
        f"exit {payload['exit_code']}"
    )
