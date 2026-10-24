"""VG-07 baseline: measure uncertainty coverage across the scientific surfaces.

A measurement, not a claim. It counts, offline and reproducibly, how many
surfaces carry a real uncertainty object/field versus the honest
``NOT_ESTIMATED`` placeholder, so the engine owner gets a measured VG-07 target
for S3 (Explainability & Uncertainty) rather than a vague "propagation absent".

Sources scanned (all read-only):
* ``engine/**/*.py``                  — ``UncertaintySpec(`` constructions (real).
* ``engine/validation/*.md``          — each record's machine ``uncertainty`` field.
* ``scenario/definitions/*.yaml`` + ``tools/run_e2e_demo.py`` — ``NOT_ESTIMATED``
  placeholders (the honest sentinel, as used in the tree).

A surface is *real* only if it states a method/interval/CI; the strings
``NOT_ESTIMATED`` / ``not_estimated`` are the placeholder. Read-only, offline.

Usage::

    python tools/uncertainty_audit.py --out reports/validation
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD_SCHEMA = "hydroma.validation.record@1"
_JSON_FENCE = re.compile(r"```json\n(.*?)```", re.DOTALL)
#: The honest uncertainty placeholders in this tree (case-insensitive).
_SENTINEL = re.compile(r"not_estimated|NOT_ESTIMATED|uncertainty_not_estimated|not estimated", re.I)
_REAL_SPEC = re.compile(r"UncertaintySpec\s*\(")


def _iter_py(root: Path):
    yield from sorted(root.rglob("*.py"))


def build_audit() -> dict[str, Any]:
    # 1. Real uncertainty objects constructed in the engine.
    uncertainty_spec_files: dict[str, int] = {}
    spec_total = 0

    # 2. Sentinel placeholders, tracked per area.
    placeholder_files: dict[str, int] = {}
    placeholder_total = 0

    scan_roots = [
        REPO_ROOT / "engine",
        REPO_ROOT / "tools",
        REPO_ROOT / "scenario",
        REPO_ROOT / "runtime",
        REPO_ROOT / "services",
    ]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in _iter_py(root):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            real = len(_REAL_SPEC.findall(text))
            if real:
                rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
                uncertainty_spec_files[rel] = uncertainty_spec_files.get(rel, 0) + real
                spec_total += real
            ph = len(_SENTINEL.findall(text))
            if ph:
                rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
                placeholder_files[rel] = placeholder_files.get(rel, 0) + ph
                placeholder_total += ph

    definitions = REPO_ROOT / "scenario" / "definitions"
    if definitions.exists():
        for path in sorted(definitions.glob("*.yaml")):
            text = path.read_text(encoding="utf-8", errors="replace")
            ph = len(_SENTINEL.findall(text))
            if ph:
                rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
                placeholder_files[rel] = placeholder_files.get(rel, 0) + ph
                placeholder_total += ph

    e2e = REPO_ROOT / "tools" / "run_e2e_demo.py"
    if e2e.exists():
        text = e2e.read_text(encoding="utf-8", errors="replace")
        ph = len(_SENTINEL.findall(text))
        if ph:
            placeholder_files[str(e2e.relative_to(REPO_ROOT)).replace("\\", "/")] = ph

    # 3. Validation-record uncertainty fields (machine block).
    records_real = 0
    records_placeholder = 0
    records_dir = REPO_ROOT / "engine" / "validation"
    for path in sorted(records_dir.glob("*.md")):
        for block in _JSON_FENCE.findall(path.read_text(encoding="utf-8")):
            try:
                payload = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("schema") == RECORD_SCHEMA:
                field = str(payload.get("uncertainty", "")).strip()
                if not field or _SENTINEL.search(field):
                    records_placeholder += 1
                else:
                    records_real += 1
                break

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "tool": "tools/uncertainty_audit.py",
        "baseline": {
            "uncertainty_spec_constructions": spec_total,
            "uncertainty_spec_files": uncertainty_spec_files,
            "sentinel_placeholders": placeholder_total,
            "placeholder_files": placeholder_files,
            "records_real_uncertainty": records_real,
            "records_placeholder_uncertainty": records_placeholder,
        },
    }


def _render(audit: dict[str, Any]) -> str:
    b = audit["baseline"]
    real_surfaces = b["uncertainty_spec_constructions"] + b["records_real_uncertainty"]
    placeholder = b["sentinel_placeholders"] + b["records_placeholder_uncertainty"]
    total = real_surfaces + placeholder
    pct = f"{(100.0 * real_surfaces / total):.1f}%" if total else "n/a"
    lines = [
        "# VG-07 Uncertainty Baseline",
        "",
        f"*Generated {audit['generated_at']} by `{audit['tool']}` — a measurement, not a claim. "
        "Re-run; never hand-edit.*",
        "",
        "| metric | count |",
        "|---|---:|",
        f"| `UncertaintySpec(...)` (engine) | {b['uncertainty_spec_constructions']} |",
        f"| records w/ real uncertainty field | {b['records_real_uncertainty']} |",
        f"| records w/ placeholder/empty uncertainty | {b['records_placeholder_uncertainty']} |",
        f"| `NOT_ESTIMATED` sentinel occurrences | {b['sentinel_placeholders']} |",
        "| **real uncertainty surfaces** | "
        f"{real_surfaces} / {total} (~{pct}) |",
        "",
        "## Where the placeholders are",
        "",
        "| file | NOT_ESTIMATED count |",
        "|---|---:|",
    ]
    for rel, n in sorted(b["placeholder_files"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {rel} | {n} |")
    lines += ["", "## Where `UncertaintySpec` is constructed", "", "| file | count |", "|---|---:|"]
    for rel, n in sorted(b["uncertainty_spec_files"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {rel} | {n} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/validation")
    args = parser.parse_args()

    audit = build_audit()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "UNCERTAINTY-BASELINE.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    (out_dir / "UNCERTAINTY-BASELINE.md").write_text(_render(audit), encoding="utf-8")

    b = audit["baseline"]
    real = b["uncertainty_spec_constructions"] + b["records_real_uncertainty"]
    ph = b["sentinel_placeholders"] + b["records_placeholder_uncertainty"]
    print(f"uncertainty baseline: real={real} placeholder={ph}")
    print("wrote reports/validation/UNCERTAINTY-BASELINE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
