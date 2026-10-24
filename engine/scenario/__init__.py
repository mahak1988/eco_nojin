"""Scenario — a navigable mirror of the spec §3.1 chain (re-export layer).

What this package is
--------------------
``engine/scenario`` is the spec §3.1 *scenario* node. Today it is a re-export
layer: every name below is imported from the module that owns it today, so the
scenario tier — the scenario manager, the versioned scenario-definition layer
and the ``engine/hydroma/scenario`` package placeholder — is navigable from
one place without moving anything.

Module migration happens later, behind a mandate: A-4 step 2 migrates families
into this package one at a time, each behind a parity test. Nothing here has
started that migration — this file holds no scenario logic of its own.

The TODAY-correct modules mirrored here
---------------------------------------
* ``engine.hydroma.scenarios.scenario_manager`` — the scenario manager
  (``ScenarioManager``, ``ScenarioDefinition``, ``ScenarioType``,
  ``run_simulation_chain``).
* ``engine.hydroma.scenario`` — the one-line placeholder package. It carries
  no public names, so nothing is re-exported from it; the module object is
  exposed as ``hydroma_scenario`` only so the placeholder stays reachable.
* ``scenario.engine.baseline_manager`` — the ECO-12 definition layer
  (``load_scenario``, ``scenario_diff``, ``list_definitions``,
  ``compare_against_result_snapshot`` plus the ``REQUIRED_KEYS`` and
  ``SEMVER_PATTERN`` governance constants).
"""

from __future__ import annotations

from engine.hydroma import scenario as hydroma_scenario
from engine.hydroma.scenarios.scenario_manager import (
    ScenarioDefinition,
    ScenarioManager,
    ScenarioType,
    run_simulation_chain,
)
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
    "ScenarioDefinition",
    "ScenarioManager",
    "ScenarioType",
    "compare_against_result_snapshot",
    "hydroma_scenario",
    "list_definitions",
    "load_scenario",
    "run_simulation_chain",
    "scenario_diff",
]
