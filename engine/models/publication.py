"""Publication stamps: what a user-facing payload must say about its model (P10/D-13).

``docs/project/OPEN_DECISIONS.md`` D-13 fixes the bar: only ``validated`` models
may be published to users without a caveat. The registry
(``engine/models/registry.py``) and its S-level view
(``engine/models/maturity.py``) already carry the truth — this module is the one
call a service makes to get the status block that must travel *next to* the
model output, so no route has to re-derive (or forget) the caveat.

Honesty rules, inherited from the maturity module:

* the stamp is derived, never asserted — it reads the registry and can
  understate a model but never overstate one;
* an unvalidated model is not "wrong", it is "not yet evidenced" — the caveat
  says exactly that, in the payload's own language of record;
* an unknown model id raises rather than defaulting to "fine".

Usage from a service route::

    from engine.models.publication import publication_stamp

    result = gateway.execute(GatewayRequest(model_id=..., ...))
    if isinstance(result, GatewayResult):
        return {"values": result.values, "model_status": publication_stamp(model_id)}
"""

from __future__ import annotations

from typing import Any

from engine.models.maturity import maturity_of
from engine.models.registry import RegisteredModelSpec, get_model

__all__ = ["publication_stamp", "PUBLISHABLE_LEVELS"]

#: Maturity levels whose output may be published without a caveat. The ECO-06
#: bar (spec §6.6) is ``S3+``; nothing in this repository maps above ``S3``
#: today, so the set is exactly ``{"S3"}`` until evidence changes.
PUBLISHABLE_LEVELS = frozenset({"S3"})

_CAVEATS = {
    "S0": (
        "این مدل هنوز پیاده‌سازی نشده است؛ خروجی آن مقدار علمی نیست. "
        "(This model has no implementation; its output is not a scientific value.)"
    ),
    "S1": (
        "این مدل ثبت شده اما بررسی نشده است؛ خروجی صرفاً محاسبهٔ اولیه است. "
        "(Registered but unverified: an initial computation, not a result.)"
    ),
    "S2": (
        "این مدل پیاده‌سازی شده اما هنوز اعتبارسنجی نشده است؛ خروجی باید با "
        "منابع مستقل کنترل شود. "
        "(Implemented but not validated independently — verify against references.)"
    ),
    "S3": (
        "این مدل برابر با مرجع مستقل اعتبارسنجی شده است. "
        "(Validated against an independent reference.)"
    ),
}

_DEFAULT_CAVEAT = (
    "وضعیت اعتبارسنجی این مدل نامشخص است. "
    "(This model's validation status is unknown.)"
)


def publication_stamp(model_id: str) -> dict[str, Any]:
    """Return the status block that must accompany a scientific payload.

    Raises ``KeyError`` for an unregistered model — a route must not publish
    output for a model it cannot name.
    """
    model = get_model(model_id)  # None for an unknown id
    level = maturity_of(model_id)  # raises KeyError for an unknown id
    publishable = level in PUBLISHABLE_LEVELS
    # ``register`` upgrades every stored spec to RegisteredModelSpec, so the
    # structured status fields are present; this assertion says that instead of
    # letting a plain ModelSpec fall through to an AttributeError. It runs after
    # maturity_of so the unknown-id path stays a KeyError, which is what the
    # caller-facing contract promises.
    assert isinstance(model, RegisteredModelSpec), model_id

    return {
        "model_id": model.model_id,
        "model_version": getattr(model, "model_version", None),
        "maturity_level": level,
        "validation_status": model.validation_status.value,
        "implementation_status": model.implementation_status.value,
        "verification_status": model.verification_status.value,
        "publishable_without_caveat": publishable,
        "caveat": _CAVEATS.get(level, _DEFAULT_CAVEAT),
    }
