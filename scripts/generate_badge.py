#!/usr/bin/env python3
"""
HyDroMa Validation Badge Generator
===================================

Generates shields.io compatible SVG badges for model validation status.

Usage:
    python scripts/generate_badge.py --model richards_1d --backend python --result validation_richards_1d_python.json --output badges/richards_1d-python.svg
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any


# Color schemes for different statuses
STATUS_COLORS = {
    "passed": {"bg": "#28a745", "text": "white", "label_bg": "#555"},
    "failed": {"bg": "#dc3545", "text": "white", "label_bg": "#555"},
    "error": {"bg": "#dc3545", "text": "white", "label_bg": "#555"},
    "skipped": {"bg": "#6c757d", "text": "white", "label_bg": "#555"},
    "partial": {"bg": "#ffc107", "text": "#212529", "label_bg": "#555"},
    "drift": {"bg": "#fd7e14", "text": "white", "label_bg": "#555"},
    "unvalidated": {"bg": "#6c757d", "text": "white", "label_bg": "#555"},
    "unknown": {"bg": "#6c757d", "text": "white", "label_bg": "#555"},
}

BACKEND_LABELS = {
    "python": "Python",
    "numba": "Numba",
    "cpp": "C++",
    "wasm": "WASM",
    "auto": "Auto",
}


def generate_shields_badge(
    label: str,
    message: str,
    color: str,
    label_color: str = "#555",
    style: str = "flat",
    logo: str = None,
    logo_color: str = "white",
    cache_seconds: int = 300,
) -> str:
    """Generate a shields.io compatible SVG badge."""
    # Calculate text widths (approximate)
    label_width = len(label) * 6.5 + 10
    message_width = len(message) * 6.5 + 10
    total_width = label_width + message_width + 20

    # Badge colors
    label_bg = "#555"
    message_bg = color
    text_color = "white"

    # For partial/unvalidated, use dark text
    if color in ["#ffc107"]:
        message_text_color = "#212529"
    else:
        message_text_color = "white"

    # SVG template
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{label}: {message}">
  <linearGradient id="a" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="b">
    <rect width="{total_width}" height="20" rx="3" fill="white"/>
  </clipPath>
  <g clip-path="url(#b)">
    <path fill="{label_bg}" d="M0 0h{label_width}v20H0z"/>
    <path fill="{color}" d="M{label_width} 0h{message_width}v20H{label_width}z"/>
    <path fill="url(#a)" d="M0 0h{total_width}v20H0z"/>
  </g>
  <g fill="{message_text_color}" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_width // 2}" y="14" fill="{text_color}">{label}</text>
    <text x="{label_width + message_width // 2}" y="14">{message}</text>
  </g>
</svg>'''

    return svg


def determine_overall_status(result: Dict) -> str:
    """Determine overall badge status from validation result."""
    if result.get("errors", 0) > 0:
        return "error"
    if result.get("failed", 0) > 0:
        return "failed"
    if result.get("passed", 0) > 0 and result.get("failed", 0) == 0 and result.get("errors", 0) == 0:
        return "passed"
    if result.get("skipped", 0) > 0:
        return "skipped"
    return "unknown"


def generate_detailed_badge(result: Dict, model: str, backend: str) -> str:
    """Generate a detailed badge with more information."""
    status = determine_overall_status(result)
    colors = STATUS_COLORS.get(status, STATUS_COLORS["unknown"])

    total = result.get("total", 0)
    passed = result.get("passed", 0)
    failed = result.get("failed", 0)
    errors = result.get("errors", 0)

    # Status message
    if status == "passed":
        message = f"{passed}/{total} passed"
    elif status == "failed":
        message = f"{failed}/{total} failed"
    elif status == "error":
        message = f"{errors}/{total} error"
    else:
        message = status

    label = f"hydroma-{model}-{backend}"
    color = colors["bg"]

    return generate_shields_badge(
        label=label,
        message=message,
        color=color,
        label_color="#555",
    )


def generate_compact_badge(result: Dict, model: str, backend: str) -> str:
    """Generate a compact badge (just status)."""
    status = determine_overall_status(result)
    colors = STATUS_COLORS.get(status, STATUS_COLORS["unknown"])

    label = "validation"
    message = status.capitalize()
    color = colors["bg"]

    return generate_shields_badge(
        label=label,
        message=message,
        color=color,
    )


def generate_matrix_badge(all_results: Dict[str, Dict[str, Any]]) -> str:
    """Generate a matrix badge showing all model statuses."""
    # This would generate a more complex badge showing multiple models
    # For now, return a summary badge
    total_models = len(all_results)
    passed_models = sum(1 for r in all_results.values() if determine_overall_status(r) == "passed")
    failed_models = sum(1 for r in all_results.values() if determine_overall_status(r) in ["failed", "error"])

    if failed_models > 0:
        message = f"{passed_models}/{total_models} passing"
        color = "#dc3545"
    elif passed_models == total_models:
        message = f"{passed_models}/{total_models} passing"
        color = "#28a745"
    else:
        message = f"{passed_models}/{total_models} passing"
        color = "#ffc107"

    return generate_shields_badge(
        label="hydroma-validation",
        message=message,
        color=color,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate validation badge SVG")
    parser.add_argument("--model", required=True, help="Model ID (e.g., richards_1d)")
    parser.add_argument("--backend", required=True, help="Backend (python, numba, cpp, wasm)")
    parser.add_argument("--result", required=True, help="Path to validation result JSON")
    parser.add_argument("--output", required=True, help="Output SVG file path")
    parser.add_argument("--type", choices=["detailed", "compact", "matrix"], default="detailed",
                        help="Badge type")
    parser.add_argument("--all-results-dir", help="Directory with all validation results (for matrix badge)")

    args = parser.parse_args()

    # Load validation result
    with open(args.result, 'r') as f:
        result = json.load(f)

    if args.type == "matrix" and args.all_results_dir:
        # Load all results
        all_results = {}
        for f in Path(args.all_results_dir).glob("validation_*.json"):
            with open(f) as fp:
                data = json.load(f)
                key = f"{data['model']}-{data['backend']}"
                all_results[key] = data
        svg = generate_matrix_badge(all_results)
    elif args.type == "compact":
        svg = generate_compact_badge(result, args.model, args.backend)
    else:
        svg = generate_detailed_badge(result, args.model, args.backend)

    # Write output
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(svg)

    print(f"Badge written to {args.output}")
    print(f"Status: {determine_overall_status(result)}")


if __name__ == "__main__":
    main()