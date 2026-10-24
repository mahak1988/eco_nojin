"""Scenario-manager regression suite (import repair + risk aggregation).

Pins the behaviour fixed in this change so the defects cannot silently return:

1. ``engine.hydroma.scenarios.scenario_manager`` is importable. It was not:
   line 14 imported ``perform_comprehensive_risk_analysis`` from a
   ``engine.hydroma.risk`` package that did not exist, and lines 15-17 then
   imported ``generate_climate_scenario``, ``define_crop_scenario`` and
   ``run_simulation_chain`` — names neither sibling module defines. The whole
   scenario-writing path was dead code.
2. ``run_scenario`` composes the real simulation chain, the real economics
   integration and the risk aggregator into one finite result set, and
   ``compare_scenarios`` reads the risk score back out of it.
3. The risk aggregator reports zeros plus a note when it is given no market
   data, rather than an estimated figure.
4. ``overall_risk_score`` is bounded in [0, 1] and monotone non-decreasing in
   price volatility.

These are CONTRACT tests, not scientific validation (safety-brake-6
discipline): they pin the shape, the bounds and the aggregation identity of
the reported numbers. They assert nothing about whether a VaR figure is the
right value for the pilot area.
"""

from __future__ import annotations

import importlib
import itertools
import math

import pytest

from engine.hydroma.economics.integration import calculate_agricultural_project_economics
from engine.hydroma.risk.assessment import perform_comprehensive_risk_analysis
from engine.hydroma.scenarios import scenario_manager as scenario_manager_module
from engine.hydroma.scenarios.scenario_manager import (
    ScenarioDefinition,
    ScenarioManager,
    ScenarioType,
)

# A small synthetic land profile. Everything the simulation chain and the
# economics integration need beyond this comes from documented module
# constants, so the profile itself stays deliberately minimal.
LAND_PROFILE: dict = {
    "area_hectares": 12.5,
    "id": "site-synthetic-1",
    "country": "Iran",
    "region": "Isfahan",
    "location_lat": 32.65,
    "location_lon": 51.67,
}

_YIELD_T_HA = 0.7127
_VOLATILITIES = (0.05, 0.10, 0.20, 0.40)


def _economics(price_volatility: float, yield_std_dev: float = 0.3) -> dict:
    """The economics analysis ``run_scenario`` builds, at a given volatility."""
    return calculate_agricultural_project_economics(
        land_profile_data=dict(LAND_PROFILE),
        crop_advisor_output={
            "top_recommendations": [{"name_en": "Wheat", "yield_t_ha": _YIELD_T_HA}]
        },
        biofertilizer_output={"recommendations": []},
        market_data={"commodity_price_per_ton_irr": 2_000_000},
        costing_params={"labor_cost_per_hour_irr": 20_000, "bio_fert_cost_per_kg_irr": 1_000},
        roi_params={"discount_rate": 0.08, "projection_years": 10},
        risk_params={"price_volatility": price_volatility, "yield_std_dev": yield_std_dev},
    )


def _all_numbers_finite(node: object) -> None:
    """Every numeric leaf in a nested result structure is finite, or absent."""
    if isinstance(node, dict):
        for value in node.values():
            _all_numbers_finite(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            _all_numbers_finite(value)
    elif node is None or isinstance(node, (bool, str)):
        return
    elif isinstance(node, (int, float)):
        assert math.isfinite(node), f"non-finite number in result: {node!r}"


# ---------------------------------------------------------------------------
# In-memory persistence doubles
# ---------------------------------------------------------------------------


class _AnyColumn:
    """Class-level stand-in for a mapped column.

    The manager builds criteria such as ``scenario_db.id == scenario_id``
    before handing them to ``filter``, which the fake already narrows to the
    rows it holds. The column therefore only has to not raise.
    """

    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "<column>"


class _FakeScenarioRow:
    """Stand-in ORM row for ``models.ScenarioDB``.

    Deliberately not named ``*Result``/``*Output``/``*Analysis``: the strict
    S15 sweep selects classes by name shape across the whole engine tree and
    would otherwise pick this double up as a result type with no provenance.
    """

    # Class-level stand-ins for mapped columns, so the manager can build
    # ``Model.id == value`` criteria before handing them to filter.
    id = _AnyColumn()
    _ids = itertools.count(1)

    def __init__(self, **kwargs: object) -> None:
        instance_id: str = str(next(_FakeScenarioRow._ids))
        self.__dict__["id"] = instance_id
        self.__dict__.update(kwargs)


class _FakeRunRow:
    """Stand-in ORM row for ``models.ScenarioResultDB`` (see the note above)."""

    scenario_id = _AnyColumn()

    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


_MODELS = {"ScenarioDB": _FakeScenarioRow, "ScenarioResultDB": _FakeRunRow}


class _InMemoryStore:
    """Shared stand-in for the scenario tables, so a write is visible to a read."""

    def __init__(self) -> None:
        self.scenarios: list[_FakeScenarioRow] = []
        self.results: list[_FakeRunRow] = []


class _FakeQuery:
    """Minimal query builder: filters are a no-op over an already-narrow set.

    The remaining QueryPort methods are no-ops too: the manager only ever
    calls ``filter(...).first()``.
    """

    def __init__(self, store: _InMemoryStore, entity: type) -> None:
        self._store = store
        self._entity = entity

    def _rows(self) -> list:
        if self._entity is _FakeScenarioRow:
            return self._store.scenarios
        if self._entity is _FakeRunRow:
            return self._store.results
        return []

    def filter(self, *_criteria: object) -> _FakeQuery:
        return self

    def first(self) -> object | None:
        rows = self._rows()
        return rows[0] if rows else None

    def order_by(self, *_criteria: object) -> _FakeQuery:
        return self

    def limit(self, _count: int) -> _FakeQuery:
        return self

    def join(self, _target: object, *_onclause: object) -> _FakeQuery:
        return self

    def all(self) -> list:
        return list(self._rows())

    def count(self) -> int:
        return len(self._rows())

    def update(self, _values: dict) -> int:
        return 0


class _FakeSession:
    """In-memory session satisfying the whole ``engine.ports.SessionPort``.

    Only the methods the manager uses do anything; the rest exist so the
    double satisfies the port structurally rather than by duck-typing.
    """

    def __init__(self, store: _InMemoryStore) -> None:
        self._store = store

    def query(self, *entities: type) -> _FakeQuery:
        return _FakeQuery(self._store, entities[0] if entities else _FakeScenarioRow)

    def add(self, instance: object) -> None:
        if isinstance(instance, _FakeScenarioRow):
            self._store.scenarios.append(instance)
        elif isinstance(instance, _FakeRunRow):
            self._store.results.append(instance)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None

    def flush(self) -> None:
        return None

    def delete(self, _instance: object) -> None:
        return None

    def refresh(self, _instance: object) -> None:
        return None

    def get(self, _entity: type, _ident: object) -> object | None:
        return None


@pytest.fixture
def store() -> _InMemoryStore:
    return _InMemoryStore()


@pytest.fixture
def manager(monkeypatch, store: _InMemoryStore) -> ScenarioManager:
    """A ScenarioManager wired to the in-memory persistence doubles."""
    monkeypatch.setattr(
        scenario_manager_module,
        "resolve_database_attr",
        lambda _module, name: _MODELS[name],
    )
    return ScenarioManager(session_factory=lambda: _FakeSession(store))


# ---------------------------------------------------------------------------
# Import repair
# ---------------------------------------------------------------------------


def test_scenario_manager_module_imports() -> None:
    """The module that could not be imported at all now imports.

    Identity is deliberately not asserted here: ``test_s12`` wipes every
    ``engine.*`` module from ``sys.modules`` mid-session, so a module re-import
    later in the same run is a distinct object. Callability is the contract
    that matters, and it is checked again by the strict import sweeps.
    """
    module = importlib.import_module("engine.hydroma.scenarios.scenario_manager")

    assert module.ScenarioManager is not None
    assert callable(module.perform_comprehensive_risk_analysis)
    # The simulation entry point that used to be imported from the orchestrator
    # (which never defined it) is a local adapter over the real run_chain.
    assert callable(module.run_simulation_chain)
    assert callable(module.run_chain)


def test_previously_dangling_imports_resolve(manager: ScenarioManager) -> None:
    """Every symbol the four broken import lines pointed at now resolves.

    ``generate_climate_scenario`` and ``define_crop_scenario`` never existed in
    ``climate_scenarios`` / ``crop_scenarios``; ``run_simulation_chain`` never
    existed in ``simulation.orchestrator``; and ``engine.hydroma.risk`` did not
    exist as a package at all.
    """
    module = importlib.import_module("engine.hydroma.scenarios.scenario_manager")

    for name in (
        "calculate_agricultural_project_economics",
        "perform_comprehensive_risk_analysis",
        "get_climate_projection",
        "simulate_crop_yield",
        "ChainInputs",
        "run_chain",
        "ScenarioParams",
    ):
        assert hasattr(module, name), f"{name} must resolve after the import repair"

    # known_types is populated with generators that really exist.
    assert ScenarioType.CLIMATE_CHANGE in manager.known_types
    assert ScenarioType.CROP_MANAGEMENT in manager.known_types
    assert all(callable(generator) for generator in manager.known_types.values())


# ---------------------------------------------------------------------------
# End-to-end scenario run
# ---------------------------------------------------------------------------


def test_run_scenario_returns_finite_economics_and_risk(manager: ScenarioManager) -> None:
    """create -> run produces economic_analysis and risk_analysis, all finite."""
    scenario_id = manager.create_scenario(
        ScenarioDefinition(
            project_id="proj-synthetic-1",
            scenario_name="Crop management - wheat",
            scenario_type=ScenarioType.CROP_MANAGEMENT,
            description="Synthetic contract-test scenario.",
            parameters={"crop_type": "wheat", "practice": "improved"},
        )
    )
    assert scenario_id

    result = manager.run_scenario(scenario_id, dict(LAND_PROFILE))

    for key in ("simulation_outputs", "economic_analysis", "risk_analysis"):
        assert key in result, f"run_scenario must return {key}"

    _all_numbers_finite(result)

    # --- simulation: the real chain ran, with its provenance intact ---
    aquacrop = result["simulation_outputs"]["AquaCropOutput"]
    assert result["simulation_outputs"]["chain_status"] == "ok"
    assert aquacrop["yield_t_ha"] is not None and aquacrop["yield_t_ha"] > 0
    # Hydrology needs an external SWAT+ binary; it must say so, not fake it.
    assert set(result["simulation_outputs"]["NotComputed"]) >= {"swat_plus"}

    # --- economics: the integration call it already made ---
    economic = result["economic_analysis"]
    assert math.isfinite(economic["roi"]["npv_irr"])
    assert economic["revenue"]["total_revenue_irr"] > 0
    assert economic["project_summary"]["area_hectares"] == pytest.approx(12.5)

    # --- risk: the new aggregator, bounded and internally consistent ---
    risk = result["risk_analysis"]
    assert risk["market_data_available"] is True
    assert 0.0 <= risk["overall_risk_score"] <= 1.0
    assert risk["total_var_irr"] >= 0.0
    assert risk["per_stream_var_irr"]["market_price"] >= 0.0
    assert risk["per_stream_var_irr"]["yield"] >= 0.0


def test_compare_scenarios_reports_the_risk_score(manager: ScenarioManager) -> None:
    """compare_scenarios reads yield, NPV and the risk score back out."""
    scenario_ids = [
        manager.create_scenario(
            ScenarioDefinition(
                project_id="proj-synthetic-2",
                scenario_name=f"scenario-{index}",
                scenario_type=ScenarioType.CROP_MANAGEMENT,
                parameters={"crop_type": "wheat"},
            )
        )
        for index in range(2)
    ]
    for scenario_id in scenario_ids:
        manager.run_scenario(scenario_id, dict(LAND_PROFILE))

    comparisons = manager.compare_scenarios(scenario_ids)

    assert set(comparisons) == set(scenario_ids)
    for comparison in comparisons.values():
        assert set(comparison) == {
            "yield_t_ha_avg",
            "npv_irr",
            "projected_risk_score",
        }
        # The stored risk score, not the compare-time default of 1.0.
        assert 0.0 <= comparison["projected_risk_score"] <= 1.0
        assert math.isfinite(comparison["npv_irr"])
        assert comparison["yield_t_ha_avg"] > 0


def test_run_scenario_rejects_an_unknown_scenario(manager: ScenarioManager) -> None:
    """A scenario id with no stored row is an error, not an empty result."""
    with pytest.raises(ValueError, match="not found"):
        manager.run_scenario("does-not-exist", dict(LAND_PROFILE))


# ---------------------------------------------------------------------------
# Honest no-data behaviour
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "economic_analysis",
    [
        {},
        {"risk_assessment": {}},
        {"risk_assessment": {"market_price_risk": {}}},
        {"revenue": {}, "risk_assessment": None},
    ],
)
def test_missing_market_data_yields_the_zero_structure(economic_analysis: dict) -> None:
    """No market data means zeros plus a note, never an estimated figure."""
    risk = perform_comprehensive_risk_analysis({}, economic_analysis)

    assert risk["market_data_available"] is False
    assert risk["overall_risk_score"] == 0.0
    assert risk["total_var_irr"] == 0.0
    assert risk["total_var_to_projected_revenue_ratio"] == 0.0
    assert risk["per_stream_var_irr"] == {}
    assert risk["loss_ratios"] == {"market_price": 0.0, "yield": 0.0}

    price_risk = risk["volatility_adjusted_price_risk"]
    for key in (
        "value_at_risk_per_ton_irr",
        "value_at_risk_percentage",
        "value_at_risk_irr",
        "share_of_price_base_at_risk",
    ):
        assert price_risk[key] == 0.0, key
    assert price_risk["volatility_fraction"] == 0.0

    # The structure explains itself instead of looking like a clean result.
    assert risk["notes"].strip()
    assert "market" in risk["notes"].lower()


# ---------------------------------------------------------------------------
# Score bounds, monotonicity and the aggregation identity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("volatility", _VOLATILITIES)
def test_overall_risk_score_is_bounded(volatility: float) -> None:
    """The documented contract: the score is a fraction in [0, 1]."""
    risk = perform_comprehensive_risk_analysis({}, _economics(volatility))
    assert 0.0 <= risk["overall_risk_score"] <= 1.0


def test_overall_risk_score_is_monotone_in_price_volatility() -> None:
    """Raising price volatility never lowers the score, and does raise it."""
    scores = [
        perform_comprehensive_risk_analysis({}, _economics(v))["overall_risk_score"]
        for v in _VOLATILITIES
    ]
    assert all(b >= a for a, b in zip(scores, scores[1:], strict=False)), scores
    assert scores[-1] > scores[0], scores


def test_price_loss_ratio_is_monotone_in_price_volatility() -> None:
    """The price term itself, which carries the monotone response."""
    ratios = [
        perform_comprehensive_risk_analysis({}, _economics(v))["volatility_adjusted_price_risk"][
            "share_of_price_base_at_risk"
        ]
        for v in _VOLATILITIES
    ]
    assert all(b >= a for a, b in zip(ratios, ratios[1:], strict=False)), ratios
    assert ratios[-1] > ratios[0], ratios


def test_overall_risk_score_matches_the_documented_formula() -> None:
    """The score is the equal-weight mean of the two clamped loss ratios."""
    risk = perform_comprehensive_risk_analysis({}, _economics(0.15))
    ratios = risk["loss_ratios"]

    for ratio in ratios.values():
        assert 0.0 <= ratio <= 1.0

    expected = 0.5 * ratios["market_price"] + 0.5 * ratios["yield"]
    assert risk["weights"] == {"market_price": 0.5, "yield": 0.5}
    assert risk["overall_risk_score"] == pytest.approx(expected)
    assert risk["overall_risk_score"] == pytest.approx(min(1.0, max(0.0, expected)))
    assert risk["risk_formula"]


def test_price_var_is_scaled_from_the_economics_primitive() -> None:
    """The per-tonne VaR is the economics primitive's own, times the quantity."""
    economics = _economics(0.15)
    risk = perform_comprehensive_risk_analysis({}, economics)

    market_risk = economics["risk_assessment"]["market_price_risk"]
    detail = risk["per_stream_var_detail"]["market_price"]
    price_risk = risk["volatility_adjusted_price_risk"]

    # Re-run of assess_market_price_risk with the economics layer's parameters.
    assert price_risk["value_at_risk_per_ton_irr"] == pytest.approx(
        market_risk["value_at_risk_irr"]
    )
    assert price_risk["time_horizon_years"] == market_risk["time_horizon_years"]
    assert price_risk["volatility_fraction"] == pytest.approx(
        market_risk["volatility_fraction"]
    )
    assert price_risk["value_at_risk_percentage"] == pytest.approx(
        market_risk["value_at_risk_percentage"]
    )

    # Scaled to the project level by a quantity taken from the revenue analysis.
    assert detail["projected_quantity_ton"] > 0
    assert risk["per_stream_var_irr"]["market_price"] == pytest.approx(
        price_risk["value_at_risk_per_ton_irr"] * detail["projected_quantity_ton"]
    )


def test_total_var_is_the_sum_of_the_per_stream_vars() -> None:
    """The aggregator sums the streams, as assess_combined_project_risk does."""
    risk = perform_comprehensive_risk_analysis({}, _economics(0.15))
    assert risk["total_var_irr"] == pytest.approx(sum(risk["per_stream_var_irr"].values()))
    # The summed figure is an upper bound, and the note says so.
    assert "upper bound" in risk["notes"].lower()


def test_simulated_yield_is_carried_for_traceability() -> None:
    """The simulation yield is reported, not folded into the VaR arithmetic."""
    risk = perform_comprehensive_risk_analysis(
        {"AquaCropOutput": {"yield_t_ha": _YIELD_T_HA}}, _economics(0.15)
    )
    assert risk["simulated_yield_t_ha"] == pytest.approx(_YIELD_T_HA)
    assert risk["market_data_available"] is True
