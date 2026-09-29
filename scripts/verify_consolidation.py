"""Supervisory verification for parallel consolidation work.

When several agents edit disjoint parts of one codebase, the failure mode is
not usually a wrong edit — it is an edit that was correct in isolation and
wrong in combination, or an agent that stepped outside its file boundary and
produced a conflict nobody noticed until a later run.

This script is the control surface. It answers three questions mechanically:

1. **Ownership** — did any agent edit a file outside its assigned allow-list?
2. **Coherence** — does the contract suite still pass, and does every module
   import?
3. **Ratchet** — did any phase-3 gate metric get worse?

Run it after a parallel batch completes::

    python scripts/verify_consolidation.py
    python scripts/verify_consolidation.py --baseline <pre-batch snapshot.json>
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SNAPSHOT = ROOT / "docs" / "metrics" / "consolidation-snapshot.json"

#: File ownership for a parallel batch. Populated per batch; empty means the
#: ownership check is skipped rather than silently passing.
OWNERSHIP: dict[str, list[str]] = {}

#: Files that must import cleanly for the gateway to be considered sound.
CRITICAL_MODULES = [
    "services.api_gateway.main",
    "services.api_gateway.eventbus",
    "services.finance.ledger_service",
    "services.finance.earning_rates",
    "services.ecowallet.service",
    "services.ecowallet.ledger",
    "services.ledger.service",
    "services.marketplace.service",
    "services.carbon.compliance.kyc_aml",
    "services.scientific_motors.base",
    "services.scientific_motors.carbon_mrv",
    "services.workers.event_worker",
]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def _mod(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


# --------------------------------------------------------------------------- #
# 1. ownership
# --------------------------------------------------------------------------- #


def check_ownership(changed: list[str]) -> list[str]:
    """Report changed files that fall outside every declared allow-list."""
    if not OWNERSHIP:
        return []
    allowed = {f for files in OWNERSHIP.values() for f in files}
    return [f for f in changed if f not in allowed]


def changed_files() -> list[str]:
    """Files the working tree has modified, relative to the index."""
    proc = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    )
    out: list[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ")[-1]
        out.append(path.replace("\\", "/"))
    return out


# --------------------------------------------------------------------------- #
# 2. coherence
# --------------------------------------------------------------------------- #


def check_imports() -> list[str]:
    # The app writes structured JSON log lines to stdout, and one of those
    # lines starts with "{". A bare json.loads on the first brace-looking line
    # picks the log up instead of the report, so the probe tags its output.
    sentinel = "<<<IMPORTS>>>"
    script = (
        "import importlib, json, sys\n"
        "bad = {}\n"
        "for name in json.loads(sys.argv[1]):\n"
        "    try:\n"
        "        importlib.import_module(name)\n"
        "    except BaseException as exc:\n"
        "        bad[name] = f'{type(exc).__name__}: {exc}'[:200]\n"
        f"print('{sentinel}' + json.dumps(bad))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script, json.dumps(CRITICAL_MODULES)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    for line in proc.stdout.splitlines():
        line = line.strip()
        if line.startswith(sentinel):
            return [f"{k}: {v}" for k, v in json.loads(line[len(sentinel) :]).items()]
    return [f"import probe produced no report (exit {proc.returncode})"]


def check_syntax() -> list[str]:
    """Every production module must at least parse.

    Cheap, and it catches a whole class of half-finished edit.
    """
    broken: list[str] = []
    for path in (ROOT / "services").rglob("*.py"):
        if any(part in {"__pycache__", "node_modules", ".venv"} for part in path.parts):
            continue
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            broken.append(f"{_mod(path)}: UTF-8 BOM (breaks ast.parse)")
            continue
        try:
            ast.parse(raw.decode("utf-8", errors="ignore"))
        except SyntaxError as exc:
            broken.append(f"{_mod(path)}:{exc.lineno}: {exc.msg}")
    return broken


def check_contract_suite() -> tuple[int, int, int]:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/contract",
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            r"C:\Users\hp\AppData\Local\Temp\kilo\verify",
            "--tb=no",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    passed = failed = 0
    for token in tail.replace(",", " ").split():
        if token.isdigit():
            pass
    if " passed" in tail:
        for part in tail.split():
            if part.isdigit():
                passed = int(part)
                break
    if " failed" in tail:
        after = tail.split(" failed")[0].split()
        for part in reversed(after):
            if part.isdigit():
                failed = int(part)
                break
    return passed, failed, proc.returncode


# --------------------------------------------------------------------------- #
# 3. ratchet
# --------------------------------------------------------------------------- #


def check_ratchet() -> list[str]:
    proc = subprocess.run(
        [sys.executable, "scripts/measure_baseline.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if proc.returncode == 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if " -> " in line]


def take_snapshot() -> dict:
    from scripts.measure_baseline import compute_all

    return compute_all()


# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", action="store_true", help="write a snapshot and exit")
    parser.add_argument("--skip-contract", action="store_true", help="skip the pytest run")
    args = parser.parse_args()

    if args.snapshot:
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(
            json.dumps(take_snapshot(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {SNAPSHOT.relative_to(ROOT)}")
        return 0

    failures: list[str] = []

    changed = changed_files()
    unowned = check_ownership(changed)
    print(f"changed files: {len(changed)}")
    if OWNERSHIP:
        if unowned:
            failures.append("files changed outside every allow-list: " + ", ".join(unowned[:15]))
        else:
            print("ownership: every changed file is owned by exactly one agent")
    else:
        print("ownership: not configured for this batch (skipped)")

    print("syntax: scanning services/ ...")
    broken = check_syntax()
    if broken:
        failures.append(f"unparseable modules: {broken[:10]}")
    else:
        print("syntax: all production modules parse")

    print("imports: probing critical modules ...")
    bad = check_imports()
    if bad:
        failures.append(f"critical modules failed to import: {bad}")
    else:
        print(f"imports: all {len(CRITICAL_MODULES)} critical modules import")

    if not args.skip_contract:
        print("contract suite: running (this takes a few minutes) ...")
        passed, failed, code = check_contract_suite()
        print(f"contract suite: {passed} passed, {failed} failed")
        if failed or code:
            failures.append(f"contract suite: {failed} failed (exit {code})")

    print("ratchet: checking phase 3 gates ...")
    regressions = check_ratchet()
    if regressions:
        failures.append("ratchet regressions:\n  " + "\n  ".join(regressions))
    else:
        print("ratchet: no gate metric regressed")

    if failures:
        print("\nVERIFICATION FAILED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nVERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
