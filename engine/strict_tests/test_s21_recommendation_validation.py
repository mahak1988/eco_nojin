"""Independent validation of the plant-neuro subagent's S21 successor focus:
the recommendation / advisory layer.

Routes: RECOMMEND (DecisionSupportSystem), SOIL_RECOMMENDATIONS
(generate_recommendations / estimate_amendment_costs), SOIL_HEALTH.
Method: entailment, determinism, coverage, bounds, order-independence, and
honest rejection -- each against a criterion derived from the module's own
documented rules, never from its output.
"""
import copy

from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)
from engine.hydroma.decision_support.dss import DecisionSupportSystem
from engine.hydroma.soil.health import calculate_soil_health_index
from engine.hydroma.soil.recommendations import (
    estimate_amendment_costs,
    generate_recommendations,
)

GW = EngineGateway()
PROV = ProvenanceSpec(source="s21", source_type="TEST")


def _values(model_id, inputs):
    r = GW.execute(
        GatewayRequest(model_id=model_id, inputs=inputs, input_units={}, provenance=PROV)
    )
    assert isinstance(r, GatewayResult), f"{model_id}: {r.error_code}: {r.message}"
    return r.values


BASE_SOIL = {
    "health_score": 80,
    "ph": 6.8,
    "organic_matter": 3.0,
    "texture": "loam",
    "salinity": {"classification": "non_saline"},
}


class TestEntailment:
    """Each recommendation must be entailed by its trigger state."""

    def test_acidic_soil_entails_lime(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL, ph=5.2))
        fertility = recs["fertility_management"]
        assert [r["action"] for r in fertility] == ["apply_lime"]
        assert "5.2" in fertility[0]["details"]

    def test_alkaline_soil_entails_sulfur_and_never_lime(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL, ph=8.1))
        actions = [r["action"] for r in recs["fertility_management"]]
        assert "apply_sulfur" in actions
        assert "apply_lime" not in actions, "acid and alkali advice must not co-fire"

    def test_low_organic_matter_entails_compost(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL, organic_matter=1.2))
        assert [r["action"] for r in recs["biological_management"]] == ["add_compost"]

    def test_healthy_soil_entails_no_amendment(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL))
        assert recs["fertility_management"] == []
        assert recs["biological_management"] == []

    def test_critical_health_entails_immediate_remediation(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL, health_score=25))
        assert recs["priority_actions"][0]["action"] == "immediate_remediation"
        assert recs["priority_actions"][0]["urgency"] == "high"

    def test_good_health_entails_maintenance(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL, health_score=75))
        assert recs["priority_actions"][0]["action"] == "maintenance"

    def test_saline_soil_entails_a_salinity_action(self) -> None:
        recs = generate_recommendations(
            dict(BASE_SOIL, salinity={"classification": "strongly_saline",
                                      "management": {"action": "leaching_required"},
                                      "description": "restricted"})
        )
        actions = [r["action"] for r in recs["physical_management"]]
        assert "leaching_required" in actions


class TestNoSelfContradiction:
    """No advice may contradict its own trigger state (master directive §10)."""

    def test_healthy_soil_never_advises_leaching_or_liming(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL))
        all_actions = [
            r.get("action")
            for group in ("fertility_management", "physical_management", "biological_management")
            for r in recs[group]
        ]
        assert not all_actions, f"healthy soil drew advice: {all_actions}"

    def test_texture_advice_matches_the_texture(self) -> None:
        loam = generate_recommendations(dict(BASE_SOIL, texture="loam"))
        assert loam["physical_management"] == []
        sandy = generate_recommendations(dict(BASE_SOIL, texture="sand"))
        assert [r["issue"] for r in sandy["physical_management"]] == ["low_water_holding"]
        clay = generate_recommendations(dict(BASE_SOIL, texture="clay"))
        assert [r["issue"] for r in clay["physical_management"]] == ["poor_drainage"]

    def test_monitoring_expands_with_declining_health(self) -> None:
        good = generate_recommendations(dict(BASE_SOIL, health_score=80))
        poor = generate_recommendations(dict(BASE_SOIL, health_score=45))
        assert len(poor["monitoring_plan"]) > len(good["monitoring_plan"])
        # EC monitoring appears exactly when the health score crosses 60.
        assert not any(m["parameter"] == "EC (salinity)" for m in good["monitoring_plan"])
        assert any(m["parameter"] == "EC (salinity)" for m in poor["monitoring_plan"])


class TestCostRollUp:
    """The roll-up must equal the sum of the per-action bands it documents."""

    def test_costs_match_the_emitted_actions(self) -> None:
        recs = generate_recommendations(
            dict(BASE_SOIL, ph=5.2, organic_matter=1.2)
        )
        costs = recs["estimated_costs"]
        assert costs["estimated_min"] == 50 + 100  # lime + compost bands
        assert costs["estimated_max"] == 100 + 200
        assert costs["unit"] == "$/ha"

    def test_zero_actions_costs_zero(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL))
        assert recs["estimated_costs"]["estimated_min"] == 0
        assert recs["estimated_costs"]["interpretation"] == "Total estimated cost: $0-$0/ha"

    def test_unknown_actions_do_not_inflate_the_total(self) -> None:
        recs = generate_recommendations(dict(BASE_SOIL))
        recs["fertility_management"].append({"action": "invite_aliens"})
        costs = estimate_amendment_costs(recs)
        assert costs["estimated_min"] == 0


class TestDeterminismAndContract:
    """Determinism, bounded values, and honest rejection of bad input."""

    def test_recommendations_are_deterministic_modulo_timestamp(self) -> None:
        a = generate_recommendations(dict(BASE_SOIL, ph=5.0))
        b = generate_recommendations(dict(BASE_SOIL, ph=5.0))
        a.pop("generated_at"), b.pop("generated_at")
        assert a == b

    def test_health_score_bounds_are_respected(self) -> None:
        for score in (0, 50, 100):
            recs = generate_recommendations(dict(BASE_SOIL, health_score=score))
            assert recs["priority_actions"], "every state must carry a priority action"

    def test_soil_health_index_stays_in_the_unit_scale(self) -> None:
        """The Soil Health Index is a weighted average of 0-100 indicator
        scores normalised by ``max_score``, so ``overall_score`` must stay in
        [0, max_score] for any admissible input."""
        for ph, om, n, p, k in ((4.2, 0.3, 5.0, 3.0, 20.0), (7.4, 4.5, 90.0, 45.0, 300.0),
                                (9.0, 0.1, 1.0, 1.0, 5.0)):
            result = calculate_soil_health_index(
                ph=ph, organic_matter=om, nitrogen=n, phosphorus=p, potassium=k
            )
            assert 0.0 <= result["overall_score"] <= result["max_score"], result
            assert result["max_score"] == 100.0

    def test_soil_health_index_monotone_in_organic_matter(self) -> None:
        """Holding the other indicators fixed, more organic matter cannot
        lower the index -- the OM indicator is scored on a unimodal curve."""
        low = calculate_soil_health_index(
            ph=6.8, organic_matter=0.5, nitrogen=30.0, phosphorus=20.0, potassium=150.0
        )
        high = calculate_soil_health_index(
            ph=6.8, organic_matter=3.5, nitrogen=30.0, phosphorus=20.0, potassium=150.0
        )
        assert high["overall_score"] >= low["overall_score"], (
            low["overall_score"], high["overall_score"]
        )

    def test_gateway_route_matches_the_module(self) -> None:
        via_route = _values(
            "SOIL_RECOMMENDATIONS",
            {"health_score": 80, "ph": 6.8, "organic_matter": 3.0,
             "texture": "loam", "salinity": {"classification": "non_saline"}},
        )
        direct = generate_recommendations(dict(BASE_SOIL))
        direct.pop("generated_at")
        # The route spreads the module's dict into the gateway envelope.
        assert via_route["priority_actions"] == direct["priority_actions"]
        assert via_route["estimated_costs"] == direct["estimated_costs"]
        assert via_route["monitoring_plan"] == direct["monitoring_plan"]

    def test_gateway_rejects_incomplete_soil_state(self) -> None:
        r = GW.execute(
            GatewayRequest(
                model_id="SOIL_HEALTH",
                inputs={"ph": 7.0},
                input_units={},
                provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
        assert r.error_code == "INVALID_REQUEST"
        assert any("organic_matter" in e for e in (r.validation_errors or []))


class TestRecommendRoute:
    """The RECOMMEND route through the decision-support system.

    Acceptance criterion: the module's documented scoring rule,
    ``score = npv_irr - 1_000_000 * projected_risk_score``
    (``_find_best_scenario``), re-derived here from first principles.
    """

    def test_empty_context_is_rejected_not_silently_empty(self) -> None:
        """A context carrying neither optimization results nor a scenario
        comparison must be rejected with the missing groups named -- the
        decision-support system cannot compute a recommendation from nothing,
        and an empty list would look like a valid answer (S21 contract, S17
        required-input pattern)."""
        r = GW.execute(
            GatewayRequest(
                model_id="RECOMMEND",
                inputs={"context": {"project_id": "s21-probe"}},
                input_units={},
                provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
        assert r.error_code in ("INVALID_REQUEST", "EXECUTION_ERROR")
        assert "optimization_results" in r.message or "scenario_comparison" in r.message

    def test_recommend_is_deterministic(self) -> None:
        payload = {"context": {"project_id": "s21-probe",
                               "scenario_comparison": {"only": {"npv_irr": 3.0}}}}
        a = _values("RECOMMEND", payload)["recommendations"]
        b = _values("RECOMMEND", copy.deepcopy(payload))["recommendations"]
        assert a == b

    def test_best_scenario_follows_the_documented_score(self) -> None:
        """beta: 5.0M IRR at 0.2 risk beats alpha: 1.0M at 0.9 risk under the
        documented penalty, and the recommendation must say so with the
        scenario's own numbers."""
        got = _values(
            "RECOMMEND",
            {"context": {"project_id": "s21", "scenario_comparison": {
                "alpha": {"npv_irr": 1_000_000.0, "projected_risk_score": 0.9},
                "beta": {"npv_irr": 5_000_000.0, "projected_risk_score": 0.2}}}},
        )["recommendations"]
        assert len(got) == 1
        rec = got[0]
        assert "beta" in rec["title"]
        assert rec["data"]["based_on_scenario_id"] == "beta"
        assert rec["economic_impact"]["NPV_irr"] == 5_000_000.0
        assert rec["risk_level"] == "low"  # 0.2 < 0.33

    def test_high_npv_high_risk_wins_under_the_penalty(self) -> None:
        """alpha: 10M at 0.95 risk scores 10M - 950k = 9.05M; beta: 1M at 0.1
        scores 900k. The documented rule selects alpha, and the risk level
        must be reported honestly as high rather than smoothed away."""
        got = _values(
            "RECOMMEND",
            {"context": {"project_id": "s21", "scenario_comparison": {
                "alpha": {"npv_irr": 10_000_000.0, "projected_risk_score": 0.95},
                "beta": {"npv_irr": 1_000_000.0, "projected_risk_score": 0.1}}}},
        )["recommendations"]
        assert got[0]["data"]["based_on_scenario_id"] == "alpha"
        assert got[0]["risk_level"] == "high"

    def test_scenario_insertion_order_does_not_change_the_winner(self) -> None:
        scenarios_forward = {
            "alpha": {"npv_irr": 2_000_000.0, "projected_risk_score": 0.4},
            "beta": {"npv_irr": 8_000_000.0, "projected_risk_score": 0.3},
        }
        scenarios_backward = dict(reversed(list(scenarios_forward.items())))
        a = _values(
            "RECOMMEND",
            {"context": {"project_id": "p", "scenario_comparison": scenarios_forward}},
        )["recommendations"]
        b = _values(
            "RECOMMEND",
            {"context": {"project_id": "p", "scenario_comparison": scenarios_backward}},
        )["recommendations"]
        assert [r["data"]["based_on_scenario_id"] for r in a] == [
            r["data"]["based_on_scenario_id"] for r in b
        ] == ["beta"]

    def test_confidence_and_risk_bounds(self) -> None:
        got = _values(
            "RECOMMEND",
            {"context": {"project_id": "p", "scenario_comparison": {
                "only": {"npv_irr": 1.0, "projected_risk_score": 0.5}}}},
        )["recommendations"]
        for rec in got:
            assert 0.0 <= rec["confidence_level"] <= 1.0
            assert rec["risk_level"] in {"low", "medium", "high"}

    def test_direct_dss_call_matches_the_route(self) -> None:
        dss = DecisionSupportSystem()
        direct = dss.generate_recommendations(
            "s21", {"only": {"npv_irr": 3.0, "projected_risk_score": 0.1}}, []
        )
        via_route = _values(
            "RECOMMEND",
            {"context": {"project_id": "s21", "scenario_comparison": {
                "only": {"npv_irr": 3.0, "projected_risk_score": 0.1}}}},
        )["recommendations"]
        assert len(direct) == len(via_route) == 1
        assert direct[0].title == via_route[0]["title"]
