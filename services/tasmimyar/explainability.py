"""P11 — the decision-support explainability contract.

``docs/project/PHASE_PLAN.md`` P11: advice is never auto-applied, and every
recommendation carries its evidence and limits. This module is the one builder
a decision-support response must use, so a response cannot omit the fields that
make the advice auditable:

* the goal the advice optimises for;
* the inputs actually used (and the inputs deliberately ignored);
* the criteria and their weights;
* the scenarios compared;
* the assumptions and the uncertainty;
* the model version and the status stamp (``engine.models.publication``);
* the **accountable decision-maker** — the human who owns the decision.

The builder refuses to produce advice without evidence or without limits: a
recommendation that cannot say what it does not know is not a recommendation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


class AdviceError(ValueError):
    """A recommendation that cannot be made honest is refused."""


def explainable_advice(
    *,
    goal: str,
    inputs_used: dict[str, Any],
    inputs_ignored: dict[str, Any],
    criteria: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    assumptions: list[str],
    uncertainty: str,
    limits: str,
    model_id: str,
    accountable_user_id: str,
    recommendation: str,
) -> dict[str, Any]:
    """Build one explainable recommendation (never auto-applied)."""
    if not goal or not goal.strip():
        raise AdviceError("advice without a goal is not advice")
    if not scenarios:
        raise AdviceError("advice must compare at least one scenario")
    if not criteria:
        raise AdviceError("advice must state its criteria")
    if not assumptions:
        raise AdviceError("advice must state its assumptions")
    if not uncertainty or not uncertainty.strip():
        raise AdviceError("advice must state its uncertainty")
    if not limits or not limits.strip():
        raise AdviceError("advice must state its limits — an unbounded claim is refused")
    if not accountable_user_id:
        raise AdviceError("advice must name the accountable decision-maker")
    total_weight = sum(float(c.get("weight", 0)) for c in criteria)
    if abs(total_weight) < 1e-9:
        raise AdviceError("criteria weights must not sum to zero")

    from engine.models.publication import publication_stamp

    try:
        stamp = publication_stamp(model_id)
    except KeyError as exc:
        raise AdviceError(f"unknown model: {model_id}") from exc

    return {
        "advice_id": str(uuid4()),
        "created_at": datetime.now(UTC).isoformat(),
        "goal": goal,
        "recommendation": recommendation,
        "inputs_used": inputs_used,
        "inputs_ignored": inputs_ignored,
        "criteria": criteria,
        "criteria_weight_total": total_weight,
        "scenarios": scenarios,
        "assumptions": assumptions,
        "uncertainty": uncertainty,
        "limits": limits,
        "model_status": stamp,
        "accountable_user_id": accountable_user_id,
        "auto_applied": False,  # the contract: advice is never auto-applied
    }
