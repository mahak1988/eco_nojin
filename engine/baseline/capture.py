"""R18 baseline capture and comparison harness.

See ``cases.py`` for what is recorded and why. This module is the machinery:
it runs the cases, serialises them, and compares two captures field by field.

Three commands, no hidden modes:

    python -m engine.baseline.capture --show      # print the live capture
    python -m engine.baseline.capture --diff      # compare against R18.json
    python -m engine.baseline.capture --regenerate # rewrite R18.json (explicit only)

``--regenerate`` is deliberately a separate verb rather than a flag on
``--diff``, so that a stale-baseline failure can never quietly rewrite itself.
Regenerating is a decision that belongs in a commit message, not in a test run.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from engine.baseline import cases as case_module

BASELINE_PATH = Path(__file__).resolve().parent / "R18.json"
SCHEMA_VERSION = 1

# Relative tolerance for the comparison. The capture is pure deterministic
# Python, so a real change moves the value by far more than this; ten
# significant digits is enough to ignore the last-bit noise of a reordered
# expression and tight enough that a 1e-8 relative change is already reported.
REL_TOLERANCE = 1e-9


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(
            f"baseline not found: {path}\n"
            f"regenerate it once with:  python -m engine.baseline.capture --regenerate"
        )
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=1, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten a nested capture into dotted paths so a diff names one number."""
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key in value:
            out.update(_flatten(value[key], f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            out.update(_flatten(item, f"{prefix}[{index}]"))
    else:
        out[prefix] = value
    return out


def compare(
    baseline: dict[str, Any], live: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return (changed entries, structural problems).

    A structural problem is a case or field present in one capture and not the
    other. That is reported separately from a numeric change because it means
    the case list moved, which needs its own decision.
    """
    flat_baseline = _flatten(baseline.get("cases", {}))
    flat_live = _flatten(live)

    missing = sorted(set(flat_baseline) - set(flat_live))
    added = sorted(set(flat_live) - set(flat_baseline))
    changed: list[dict[str, Any]] = []

    for key in sorted(set(flat_baseline) & set(flat_live)):
        old, new = flat_baseline[key], flat_live[key]
        if isinstance(old, bool) or isinstance(new, bool):
            if old != new:
                changed.append(
                    {"path": key, "baseline": old, "live": new, "relative": None, "kind": "bool"}
                )
            continue
        if isinstance(old, (int, float)) and isinstance(new, (int, float)):
            if math.isnan(new):
                changed.append(
                    {"path": key, "baseline": old, "live": "NaN", "relative": None, "kind": "nan"}
                )
                continue
            if old == 0.0 and new == 0.0:
                continue
            denominator = abs(old) if old != 0 else abs(new)
            relative = abs(new - old) / denominator if denominator else 0.0
            if relative > REL_TOLERANCE:
                changed.append(
                    {
                        "path": key,
                        "baseline": old,
                        "live": new,
                        "relative": relative,
                        "kind": "numeric",
                    }
                )
        elif old != new:
            changed.append(
                {"path": key, "baseline": old, "live": new, "relative": None, "kind": "value"}
            )

    return changed, missing + [f"(added) {p}" for p in added]


def build_payload(capture: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_id": "R18",
        "case_names": case_module.case_names(),
        "rel_tolerance": REL_TOLERANCE,
        "cases": capture,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.baseline.capture")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--show", action="store_true", help="print the live capture")
    group.add_argument(
        "--diff", action="store_true", help="compare the live capture against the recorded baseline"
    )
    group.add_argument("--regenerate", action="store_true", help="rewrite the baseline file")
    # Outside the exclusive group: it qualifies --diff rather than competing
    # with it, so "--diff --quiet" is a legal combination.
    parser.add_argument(
        "--quiet", action="store_true", help="with --diff, print only a one-line summary"
    )
    args = parser.parse_args(argv)

    capture = case_module.capture()

    if args.show:
        print(json.dumps(capture, indent=1, sort_keys=True, ensure_ascii=False))
        return 0

    if args.regenerate:
        _write(BASELINE_PATH, build_payload(capture))
        count = len(_flatten(capture))
        print(f"baseline written: {BASELINE_PATH}")
        print(f"  {len(capture)} cases, {count} recorded values")
        print("  include the reason for the change in the commit message")
        return 0

    baseline = _load(BASELINE_PATH)
    changed, structural = compare(baseline, capture)

    if args.quiet:
        print(f"{len(changed)} changed, {len(structural)} structural")
        return 1 if (changed or structural) else 0

    if not changed and not structural:
        print(
            f"baseline {baseline.get('baseline_id', '?')} intact: "
            f"{len(_flatten(capture))} values unchanged"
        )
        return 0

    if structural:
        print(f"STRUCTURAL: {len(structural)} field(s) present in one capture only")
        for path in structural[:40]:
            print(f"  {path}")
        if len(structural) > 40:
            print(f"  ... and {len(structural) - 40} more")
        print()

    if changed:
        print(
            f"CHANGED: {len(changed)} value(s) differ from the baseline "
            f"(tolerance {REL_TOLERANCE:g} relative)"
        )
        print(f"{'relative':>12}  {'baseline':>16}  {'live':>16}  path")
        for entry in sorted(changed, key=lambda e: -(e["relative"] or 0.0))[:60]:
            relative = (
                f"{entry['relative']:.3e}"
                if entry["relative"] is not None
                else f"[{entry['kind']}]"
            )
            print(
                f"{relative:>12}  {entry['baseline']!r:>16}  {entry['live']!r:>16}  {entry['path']}"
            )
        if len(changed) > 60:
            print(f"  ... and {len(changed) - 60} more")
        print()
        print("If a change is intended, regenerate deliberately:")
        print("  python -m engine.baseline.capture --regenerate")
        print("and state the governing standard in the commit message.")

    return 1 if (changed or structural) else 0


if __name__ == "__main__":
    sys.exit(main())
