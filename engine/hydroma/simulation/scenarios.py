"""Scenario matrices for the simulation chain (Phase 3, doc 28).

Baseline / Medium / Intensive interventions. Parameters follow the
kickoff document: CN reduction, C-factor multiplier (crop cover), and
the RUSLE support-practice factor.
"""

from engine.hydroma.simulation.contracts import ScenarioParams

SCENARIOS: dict[str, ScenarioParams] = {
    "Baseline": ScenarioParams(
        name="Baseline",
        cn_change=0.0,
        c_factor_factor=1.0,
        p_factor=1.0,
    ),
    "Medium": ScenarioParams(
        name="Medium",
        cn_change=-8.0,
        c_factor_factor=0.85,
        p_factor=0.50,
    ),
    "Intensive": ScenarioParams(
        name="Intensive",
        cn_change=-15.0,
        c_factor_factor=0.70,
        p_factor=0.35,
    ),
}
