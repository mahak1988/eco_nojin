"""Scenario tooling: the ECO-12 phase 1 definition engine.

Public API (all re-exported from :mod:`scenario.engine.baseline_manager`):

``load_scenario``
    Read and validate one YAML scenario definition.
``scenario_diff``
    Structured, per-key diff between two definitions (baseline comparison).
``compare_against_result_snapshot``
    Compare a measured numeric snapshot against the recorded execution
    baseline (``engine/baseline/R18.json``), read-only.
``list_definitions``
    Every validated definition found in a definitions directory.
"""

from __future__ import annotations

from scenario.engine.baseline_manager import (
    REQUIRED_KEYS,
    SEMVER_PATTERN,
    compare_against_result_snapshot,
    list_definitions,
    load_scenario,
    scenario_diff,
)

__all__ = [
    "REQUIRED_KEYS",
    "SEMVER_PATTERN",
    "compare_against_result_snapshot",
    "list_definitions",
    "load_scenario",
    "scenario_diff",
]
