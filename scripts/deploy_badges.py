#!/usr/bin/env python3
"""Deploy validation badges to GitHub Pages.

Generates SVG badges for each model and pushes them to the badges/ directory.
"""

import json
import sys
from pathlib import Path

BADGES_DIR = Path("badges")
RESULTS_DIR = Path("validation-results")

STATUS_COLORS = {
    "passed": "#28a745",
    "failed": "#dc3545",
    "error": "#dc3545",
    "skipped": "#6c757d",
    "partial": "#ffc107",
    "drift": "#fd7e14",
    "unvalidated": "#6c757d",
    "unknown": "#6c757d",
}


def generate_badge(label: str, message: str, color: str) -> str:
    """Generate a shields.io compatible SVG badge."""
    label_width = len(label) * 6.5 + 10
    message_width = len(message) * 6.5 + 10
    total_width = label_width + message_width + 20

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {message}">
  <linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="b">
    <rect width="{total_width}" height="20" rx="3" fill="white"/>
  </clipPath>
  <g clip-path="url(#b)">
    <path fill="#555" d="M0 0h{label_width}v20H0z"/>
    <path fill="{color}" d="M{label_width} 0h{message_width}v20H{label_width}z"/>
    <path fill="url(#a)" d="M0 0h{total_width}v20H0z"/>
  </g>
  <g fill="white" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_width // 2}" y="14" fill="white">{label}</text>
    <text x="{label_width + message_width // 2}" y="14">{message}</text>
  </g>
</svg>'''


def determine_status(result: dict) -> str:
    """Determine overall status from validation result."""
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


def main():
    BADGES_DIR.mkdir(parents=True, exist_ok=True)

    if not RESULTS_DIR.exists():
        print(f"No results directory: {RESULTS_DIR}")
        sys.exit(1)

    results = {}
    for f in RESULTS_DIR.glob("validation_*.json"):
        with open(f) as fp:
            data = json.load(fp)
            key = f"{data['model']}-{data['backend']}"
            results[key] = data

    if not results:
        print("No validation results found")
        sys.exit(1)

    for key, result in results.items():
        status = determine_status(result)
        color = STATUS_COLORS.get(status, "#6c757d")
        model = result.get("model", "unknown")
        backend = result.get("backend", "unknown")

        if status == "passed":
            message = f"{result['passed']}/{result['total']} passed"
        elif status == "failed":
            message = f"{result['failed']}/{result['total']} failed"
        elif status == "error":
            message = f"{result['errors']}/{result['total']} error"
        else:
            message = status

        svg = generate_badge(f"hydroma-{model}-{backend}", message, color)
        badge_path = BADGES_DIR / f"{model}-{backend}.svg"
        badge_path.write_text(svg)
        print(f"Generated badge: {badge_path} -> {message}")

    # Generate overall badge
    total_models = len({r["model"] for r in results.values()})
    passed_models = sum(1 for r in results.values() if determine_status(r) == "passed")
    failed_models = sum(1 for r in results.values() if determine_status(r) in ["failed", "error"])

    if failed_models > 0:
        overall_msg = f"{passed_models}/{total_models} passing"
        overall_color = "#dc3545"
    elif passed_models == total_models:
        overall_msg = f"{passed_models}/{total_models} passing"
        overall_color = "#28a745"
    else:
        overall_msg = f"{passed_models}/{total_models} passing"
        overall_color = "#ffc107"

    overall_svg = generate_badge("hydroma-validation", overall_msg, overall_color)
    overall_path = BADGES_DIR / "hydroma-validation.svg"
    overall_path.write_text(overall_svg)
    print(f"Generated overall badge: {overall_path} -> {overall_msg}")

    print(f"\nAll badges deployed to {BADGES_DIR}/")


if __name__ == "__main__":
    main()
