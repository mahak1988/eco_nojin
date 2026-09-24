#!/usr/bin/env python3
"""
HyDroMa Slaughterhouse Gate
===========================

Aggregates validation results and enforces gates for PR merge.

Usage:
    python scripts/slaughterhouse_gate.py --results-dir validation-results/ --matrix "[...]" --pr-number 123
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_results(results_dir: Path) -> dict[str, dict]:
    """Load all validation result JSON files."""
    results = {}
    for f in results_dir.glob("validation_*.json"):
        with open(f) as fp:
            data = json.load(fp)
            key = f"{data['model']}-{data['backend']}"
            results[key] = data
    return results


def determine_status(result: dict) -> str:
    """Determine overall status for a model-backend pair."""
    if result.get("errors", 0) > 0:
        return "error"
    if result.get("failed", 0) > 0:
        return "failed"
    if (
        result.get("passed", 0) > 0
        and result.get("failed", 0) == 0
        and result.get("errors", 0) == 0
    ):
        return "passed"
    if result.get("skipped", 0) > 0:
        return "skipped"
    return "unknown"


def gate_check(results: dict[str, dict], matrix: list[dict]) -> dict[str, Any]:
    """Perform gate checks and return summary."""
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_skipped = 0

    model_status = {}
    backend_status = {}

    for _key, result in results.items():
        status = determine_status(result)
        model = result.get("model", "unknown")
        backend = result.get("backend", "unknown")

        # Aggregate
        total_tests += result.get("total", 0)
        total_passed += result.get("passed", 0)
        total_failed += result.get("failed", 0)
        total_errors += result.get("errors", 0)
        total_skipped += result.get("skipped", 0)

        # Model-level
        if model not in model_status:
            model_status[model] = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
        model_status[model][status] = model_status[model].get(status, 0) + 1

        # Backend-level
        if backend not in backend_status:
            backend_status[backend] = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
        backend_status[backend][status] = backend_status[backend].get(status, 0) + 1

    # Determine overall gate status
    gate_passed = total_errors == 0 and total_failed == 0

    return {
        "gate_passed": gate_passed,
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "errors": total_errors,
            "skipped": total_skipped,
        },
        "model_status": model_status,
        "backend_status": backend_status,
        "individual_results": {
            key: {
                "model": r["model"],
                "backend": r["backend"],
                "status": determine_status(r),
                "passed": r.get("passed", 0),
                "failed": r.get("failed", 0),
                "errors": r.get("errors", 0),
                "skipped": r.get("skipped", 0),
            }
            for key, r in results.items()
        },
    }


def generate_markdown_summary(gate_result: dict, pr_number: int) -> str:
    """Generate markdown summary for PR comment."""
    summary = gate_result["summary"]
    gate_passed = gate_result["gate_passed"]

    status_emoji = "✅" if gate_passed else "❌"
    gate_text = "PASSED" if gate_passed else "FAILED"

    md = f"""## {status_emoji} HyDroMa Slaughterhouse Gate: {gate_text}

**PR #{pr_number}** — Validation Summary

| Metric | Count |
|--------|-------|
| Total Tests | {summary["total_tests"]} |
| ✅ Passed | {summary["passed"]} |
| ❌ Failed | {summary["failed"]} |
| 💥 Errors | {summary["errors"]} |
| ⏭️ Skipped | {summary["skipped"]} |

### Model Status

| Model | ✅ Passed | ❌ Failed | 💥 Errors | ⏭️ Skipped | Status |
|-------|-----------|-----------|-----------|------------|--------|
"""

    for model, counts in sorted(gate_result["model_status"].items()):
        p = counts.get("passed", 0)
        f = counts.get("failed", 0)
        e = counts.get("error", 0)
        s = counts.get("skipped", 0)
        status = "✅" if e == 0 and f == 0 else "❌" if e > 0 or f > 0 else "⏭️"
        md += f"| {model} | {p} | {f} | {e} | {s} | {status} |\n"

    md += "\n### Backend Status\n\n"
    md += "| Backend | ✅ Passed | ❌ Failed | 💥 Errors | ⏭️ Skipped |\n"
    md += "|---------|-----------|-----------|-----------|------------|\n"

    for backend, counts in sorted(gate_result["backend_status"].items()):
        p = counts.get("passed", 0)
        f = counts.get("failed", 0)
        e = counts.get("error", 0)
        s = counts.get("skipped", 0)
        md += f"| {backend} | {p} | {f} | {e} | {s} |\n"

    md += "\n### Individual Results\n\n"
    md += "| Model | Backend | Status | Passed | Failed | Errors | Skipped |\n"
    md += "|-------|---------|--------|--------|--------|--------|----------|\n"

    for _key, result in sorted(gate_result["individual_results"].items()):
        status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "error": "💥",
            "skipped": "⏭️",
            "unknown": "❓",
        }
        md += f"| {result['model']} | {result['backend']} | {status_emoji.get(result['status'], '❓')} {result['status']} | {result['passed']} | {result['failed']} | {result['errors']} | {result['skipped']} |\n"

    if not gate_passed:
        md += "\n> 🚫 **Gate Failed** — This PR cannot be merged until all validations pass.\n"
    else:
        md += "\n> ✅ **Gate Passed** — All validations passed.\n"

    return md


def main():
    parser = argparse.ArgumentParser(description="HyDroMa Slaughterhouse Gate")
    parser.add_argument(
        "--results-dir", required=True, help="Directory with validation result JSON files"
    )
    parser.add_argument("--matrix", required=True, help="JSON matrix of models × backends")
    parser.add_argument("--pr-number", type=int, required=True, help="Pull request number")
    parser.add_argument(
        "--output", default="slaughterhouse_summary.md", help="Output markdown file"
    )
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        sys.exit(1)

    print(f"Loading results from {results_dir}...")
    results = load_results(results_dir)
    print(f"Loaded {len(results)} validation results")

    # Parse matrix (not used for gating but for reference)
    matrix = json.loads(args.matrix)
    print(f"Matrix contains {len(matrix)} model-backend combinations")

    # Perform gate check
    gate_result = gate_check(results, matrix)

    # Generate markdown summary
    md = generate_markdown_summary(gate_result, args.pr_number)

    # Write output
    with open(args.output, "w") as f:
        f.write(md)

    print(f"Gate result: {'PASSED' if gate_result['gate_passed'] else 'FAILED'}")
    print(f"Summary written to {args.output}")

    # Exit with error code if gate failed
    if not gate_result["gate_passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
