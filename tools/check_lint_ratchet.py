#!/usr/bin/env python
"""The lint ratchet.

``tools/lint_baseline.json`` records the lint debt the tree is allowed to
carry and says the ratchet "fails when the count RISES above it, and the
floor is lowered as the debt is paid down". Nothing implemented that: the
Quick-Scan hook ran ``ruff check . --statistics`` and reported the *rules*,
but never compared the *total* against the recorded floor, so the debt could
grow without anyone noticing.

This tool is the missing half:

* it measures the tree's total ruff findings;
* it fails when the total is **above** the recorded floor (the debt grew);
* it never fails when the total is at or below the floor (the debt shrank);
* ``--update`` re-records the floor -- lower only, unless ``--force`` is
  given, so the floor can never be raised by accident.

Usage:
    python tools/check_lint_ratchet.py --root .
    python tools/check_lint_ratchet.py --root . --update
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BASELINE_PATH = Path("tools/lint_baseline.json")
_COUNT = re.compile(r"Found (\d+) errors?")


def _ruff_total(root: Path) -> int:
    """The tree's total ruff findings."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", ".", "--output-format=concise"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    output = result.stdout + result.stderr
    match = _COUNT.search(output)
    if match:
        return int(match.group(1))
    # ``ruff check`` exits non-zero on findings; the count is in the summary.
    for line in output.splitlines():
        if "error" in line and "found" in line.lower():
            digits = re.findall(r"\d+", line)
            if digits:
                return int(digits[-1])
    return 0


def _load(root: Path) -> dict:
    path = root / BASELINE_PATH
    if not path.exists():
        return {"rules": {"max_total": 0}, "measured_at": None, "total": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    parser.add_argument(
        "--update",
        action="store_true",
        help="re-record the floor (lower only, unless --force)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow --update to raise the floor",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    baseline = _load(root)
    floor = int(baseline.get("rules", {}).get("max_total", 0))
    measured = _ruff_total(root)

    print("=" * 70)
    print("LINT RATCHET")
    print("=" * 70)
    print(f"Root:           {root}")
    print(f"Recorded floor: {floor}")
    print(f"Measured now:  {measured}")
    print()

    if args.update:
        if measured > floor and not args.force:
            print(
                f"Refusing to raise the floor from {floor} to {measured}.\n"
                "The ratchet only moves down. Use --force if the rise is "
                "deliberate and recorded."
            )
            print("=" * 70)
            print("Status: FAIL (floor would rise)")
            return 1
        baseline["total"] = measured
        baseline["rules"]["max_total"] = measured
        baseline["measured_at"] = __import__("datetime").date.today().isoformat()
        (root / BASELINE_PATH).write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"Floor re-recorded at {measured}.")
        print("=" * 70)
        print("Status: PASS")
        return 0

    if measured > floor:
        print(
            f"The lint debt grew: {measured} findings against a floor of {floor} "
            f"({measured - floor} more).\n"
            "Pay the debt down, or re-record the floor deliberately with\n"
            "    python tools/check_lint_ratchet.py --update --force"
        )
        print("=" * 70)
        print("Status: FAIL")
        return 1

    if measured < floor:
        print(
            f"The lint debt shrank: {measured} findings against a floor of {floor} "
            f"({floor - measured} fewer).\n"
            "Lower the floor so the ratchet keeps its value:\n"
            "    python tools/check_lint_ratchet.py --update"
        )
    else:
        print("The lint debt is exactly at the floor.")
    print("=" * 70)
    print("Status: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
