"""Shared baseline ratchet for the phase 3 CI gates.

The gates cannot be plain "must be zero" checks: `services/` carries roughly
5,200 lines of unreferenced code and dozens of structural violations, so a zero
barrier would be bypassed on day one and the gate would be worthless.

Instead every gate is a **ratchet**: it records the current count in
``docs/metrics/baseline.json`` and fails when the count gets *worse*. Paying
debt lowers the number and the next run ratchets it down. A gate that blocks
new debt while allowing existing debt is the only kind a team will keep
running.

Usage::

    python scripts/measure_baseline.py            # write / refresh the baseline
    python scripts/measure_baseline.py --check    # exit 1 if anything improved
    python scripts/measure_baseline.py --metric gates.g1_import_failures
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "docs" / "metrics" / "baseline.json"

SKIP_DIR_PARTS = {
    "__pycache__",
    ".git",
    ".kilo",
    "node_modules",
    ".venv",
    "venv",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "backups",
    "data",
    "htmlcov",
}


# --------------------------------------------------------------------------- #
# inventory
# --------------------------------------------------------------------------- #


def iter_python_files(*relative: str) -> list[Path]:
    """Production Python files under the given roots, excluding tests."""
    files: list[Path] = []
    for rel in relative:
        base = ROOT / rel
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if any(part in SKIP_DIR_PARTS for part in path.parts):
                continue
            if "__init__.py" in path.name or ".py" in path.name:
                pass
            if path.name == "__init__.py":
                continue
            if "tests" in path.parts or path.name.startswith("test_"):
                continue
            files.append(path)
    return sorted(set(files))


def count_lines(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        try:
            with path.open(encoding="utf-8", errors="ignore") as handle:
                total += sum(1 for _ in handle)
        except OSError:
            continue
    return total


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #


def metric_inventory() -> dict[str, Any]:
    prod = iter_python_files("services", "engine")
    tests = [
        p
        for p in (ROOT / "services").rglob("*.py")
        if "tests" in p.parts and not any(s in p.parts for s in SKIP_DIR_PARTS)
    ]
    tests += [
        p for p in (ROOT / "tests").rglob("*.py") if not any(s in p.parts for s in SKIP_DIR_PARTS)
    ]
    modules = {
        p.relative_to(ROOT).parts[1]
        for p in (ROOT / "services").iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    }
    return {
        "prod_files": len(prod),
        "prod_lines": count_lines(prod),
        "test_files": len(tests),
        "test_lines": count_lines(tests),
        "service_modules": len(modules),
    }


def metric_dead_code() -> dict[str, Any]:
    """Unreferenced definitions, via vulture (already a dev dependency).

    ``findings`` is the ratchettable number. An approximate LOC figure is not:
    counting the containing file instead of the dead definition overstated the
    debt by 4x on the first run, which is the kind of number that stops anyone
    trusting the ratchet.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "vulture", "services", "--min-confidence", "90"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    findings = [
        line.strip()
        for line in proc.stdout.splitlines()
        if line.strip() and not line.startswith(("No dead code", "dead code"))
    ]
    return {"findings": len(findings), "detail": findings}


def metric_tolerations() -> dict[str, Any]:
    path = ROOT / "docs" / "standards" / "tolerated-degradations.yaml"
    if not path.exists():
        return {"count": 0}
    text = path.read_text(encoding="utf-8")
    return {
        "count": len(re.findall(r"^\s+-\s+id:", text, re.MULTILINE)),
        "high_risk": len(re.findall(r"^\s+risk:\s*high\s*$", text, re.MULTILINE)),
    }


def metric_structure() -> dict[str, Any]:
    from tests.contract.gates import scan_structure  # type: ignore[import-not-found]

    report = scan_structure(ROOT)
    return {"violations": len(report), "by_rule": report.rules()}


def metric_fabrications() -> dict[str, Any]:
    from tests.contract.gates import scan_fabrications  # type: ignore[import-not-found]

    report = scan_fabrications(ROOT)
    rules = report.rules()
    return {"count": len(report), "by_rule": rules}


def metric_scientific() -> dict[str, Any]:
    from tests.contract.gates import scan_motor_conformance  # type: ignore[import-not-found]

    report = scan_motor_conformance(ROOT)
    return {
        "motors": report["total"],
        "with_conformance_test": report["covered"],
    }


def metric_coverage() -> dict[str, Any]:
    """Coverage floors, read from their real sources.

    All three values are *computed*, never hand-added. An earlier version had
    `services_fail_under` written into baseline.json by hand, and the next
    regeneration silently dropped it — which, once the gates were hardened to
    fail on an incomplete baseline, would have failed the build for a reason
    that had nothing to do with the code. Deriving them means they cannot drift
    from what CI actually enforces.
    """
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"fail_under\s*=\s*(\d+(?:\.\d+)?)", text)
    engine_floor = float(match.group(1)) if match else 0.0

    services_floor: float | None = None
    workflow = ROOT / ".github" / "workflows" / "ci-cd.yml"
    if workflow.exists():
        floors = [int(n) for n in re.findall(r"--cov-fail-under=(\d+)", workflow.read_text(encoding="utf-8"))]
        if floors:
            services_floor = float(min(floors))

    # The last measured services figure, kept for context. It is informational:
    # only the floors are ratcheted.
    measured: float | None = None
    recorded = load_baseline().get("metrics", {}).get("coverage", {}).get("services_measured_pct")
    if recorded is not None:
        measured = float(recorded)

    return {
        "fail_under": engine_floor,
        "services_fail_under": services_floor,
        "services_measured_pct": measured,
    }


METRICS = {
    "inventory": metric_inventory,
    "coverage": metric_coverage,
    "dead_code": metric_dead_code,
    "tolerations": metric_tolerations,
    "structure": metric_structure,
    "fabrications": metric_fabrications,
    "scientific": metric_scientific,
}

#: Metrics where a *lower* number is better, so the ratchet can fail on growth.
LOWER_IS_BETTER = {
    "dead_code.findings",
    "tolerations.count",
    "structure.violations",
    "fabrications.count",
}
#: Metrics where a *higher* number is better.
#:
#: `inventory.prod_lines` is deliberately absent. Fewer lines of production
#: code is a *good* outcome during a de-duplication campaign -- putting it in
#: this set meant every correct deletion was scored as a regression and the
#: ratchet had to be re-pinned after each one, which trains the team to expect
#: the gate to be wrong. It is recorded as informational instead.
HIGHER_IS_BETTER = {
    "scientific.with_conformance_test",
    "coverage.fail_under",
    "coverage.services_measured_pct",
}


def _flatten(data: dict[str, Any], prefix: str = "") -> dict[str, int]:
    flat: dict[str, int] = {}
    for key, value in data.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(_flatten(value, f"{path}."))
        elif isinstance(value, int):
            flat[path] = value
    return flat


def compute_all(only: list[str] | None = None) -> dict[str, Any]:
    wanted = only or list(METRICS)
    out: dict[str, Any] = {}
    for name in wanted:
        try:
            out[name] = METRICS[name]()
        except Exception as exc:  # a broken metric must not lose the others
            out[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return out


# --------------------------------------------------------------------------- #
# baseline i/o
# --------------------------------------------------------------------------- #


def load_baseline() -> dict[str, Any]:
    if not BASELINE_PATH.exists():
        return {}
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_baseline(data: dict[str, Any]) -> None:
    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def regressions(current: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    """Return human-readable descriptions of every metric that got worse."""
    base_flat = _flatten(baseline.get("metrics", {}))
    cur_flat = _flatten(current.get("metrics", {})) if "metrics" in current else _flatten(current)
    problems: list[str] = []

    # A baseline missing a section must FAIL, not be treated as "no change".
    # This bit us: running `measure_baseline.py --metric coverage` rewrote the
    # file with that one section, and every ratchet that read a missing key
    # then skipped itself — the honesty gates quietly stopped enforcing. A gate
    # that disables itself when its state is incomplete is worse than no gate,
    # because it still reports green.
    expected_sections = set(METRICS)
    missing = expected_sections - set(baseline.get("metrics", {}))
    if missing:
        problems.append(
            "baseline is missing required section(s): "
            + ", ".join(sorted(missing))
            + " -- ratchets for these would skip instead of enforcing. "
            "Regenerate the whole baseline: python scripts/measure_baseline.py"
        )
    coverage_keys = {"fail_under", "services_fail_under", "services_measured_pct"}
    missing_coverage = coverage_keys - set(baseline.get("metrics", {}).get("coverage", {}))
    if missing_coverage:
        problems.append(
            "baseline coverage section is missing: "
            + ", ".join(sorted(missing_coverage))
            + " -- the coverage ratchets would skip. Regenerate the baseline."
        )

    for key, value in sorted(cur_flat.items()):
        if key in HIGHER_IS_BETTER:
            if key in base_flat and value < base_flat[key]:
                problems.append(
                    f"{key}: {base_flat[key]} -> {value} (higher is better; regression)"
                )
            continue
        if key in LOWER_IS_BETTER and key in base_flat and value > base_flat[key]:
            problems.append(f"{key}: {base_flat[key]} -> {value} (regression)")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if any metric regressed")
    parser.add_argument("--metric", action="append", help="limit to specific metrics")
    args = parser.parse_args()

    sys.path.insert(0, str(ROOT))
    computed = compute_all(args.metric)
    baseline = load_baseline()

    if args.check:
        problems = regressions({"metrics": computed}, baseline)
        if problems:
            print("BASELINE REGRESSION:")
            for problem in problems:
                print(f"  - {problem}")
            print("\nRun: python scripts/measure_baseline.py  (after fixing, or to re-pin)")
            return 1
        print("baseline: no regressions")
        return 0

    payload = dict(baseline)
    payload["metrics"] = computed
    payload["note"] = (
        "Generated by scripts/measure_baseline.py. Ratchet state for the phase 3 CI gates: "
        "a metric that improves should be re-pinned by running this script again."
    )
    save_baseline(payload)
    print(f"wrote {BASELINE_PATH.relative_to(ROOT)}")
    for key, value in sorted(_flatten(computed).items()):
        print(f"  {key} = {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
