"""Composite scenario engine: route a scenario through every reachable model.

Public API::

    from engine.hydroma.scenario_composite import CompositeScenarioEngine

    engine = CompositeScenarioEngine()
    spec = engine.define_scenario("drought_2050", template="climate_2050_ssp245")
    run = engine.run(spec)
    context = run["decision_context"]
"""

from __future__ import annotations

from .catalog import SCENARIO_TEMPLATES, TEMPLATE_NAMES, get_template
from .engine import CompositeScenarioEngine, ScenarioSpec, StepFailure
from .indicators import Indicator
from .models_additions import LOCAL_MODELS, LocalModel

__all__ = [
    "CompositeScenarioEngine",
    "ScenarioSpec",
    "StepFailure",
    "Indicator",
    "LocalModel",
    "LOCAL_MODELS",
    "SCENARIO_TEMPLATES",
    "TEMPLATE_NAMES",
    "get_template",
]
