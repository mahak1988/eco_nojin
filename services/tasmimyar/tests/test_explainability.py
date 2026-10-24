"""P11 — advice without evidence, limits or an owner is refused."""

from __future__ import annotations

import pytest

from services.tasmimyar.explainability import AdviceError, explainable_advice

pytestmark = pytest.mark.asyncio


def _valid_kwargs(**overrides):
    kwargs = {
        "goal": "maximise household income within the water budget",
        "inputs_used": {"rainfall_mm": 320, "area_ha": 2.0},
        "inputs_ignored": {"market_prices": "stale by 11 days"},
        "criteria": [{"name": "income", "weight": 0.7}, {"name": "water", "weight": 0.3}],
        "scenarios": [{"name": "wheat", "score": 0.62}, {"name": "saffron", "score": 0.58}],
        "assumptions": ["rainfall follows the 10-year median"],
        "uncertainty": "±15% on yield under a dry-year scenario",
        "limits": "soil chemistry not sampled; no extension-service capacity priced",
        "model_id": "CROP_YIELD",
        "accountable_user_id": "user-1",
        "recommendation": "saffron on the north parcel",
    }
    kwargs.update(overrides)
    return kwargs


def test_a_complete_advice_carries_every_contract_field():
    advice = explainable_advice(**_valid_kwargs())
    for field in (
        "goal", "inputs_used", "inputs_ignored", "criteria", "scenarios",
        "assumptions", "uncertainty", "limits", "model_status",
        "accountable_user_id", "auto_applied",
    ):
        assert field in advice, field
    assert advice["auto_applied"] is False
    assert advice["criteria_weight_total"] == 1.0


def test_advice_without_limits_is_refused():
    with pytest.raises(AdviceError):
        explainable_advice(**_valid_kwargs(limits=""))


def test_advice_without_an_accountable_owner_is_refused():
    with pytest.raises(AdviceError):
        explainable_advice(**_valid_kwargs(accountable_user_id=""))


def test_advice_without_scenarios_is_refused():
    with pytest.raises(AdviceError):
        explainable_advice(**_valid_kwargs(scenarios=[]))


def test_the_model_status_stamp_rides_along():
    advice = explainable_advice(**_valid_kwargs())
    stamp = advice["model_status"]
    assert stamp["model_id"] == "CROP_YIELD"
    assert "publishable_without_caveat" in stamp
    # an unvalidated model must not be silently presented as validated
    assert stamp["caveat"]
