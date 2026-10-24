"""P10 / D-13 — the publication stamp is derived and never overstates a model.

These tests pin the three properties that make the stamp safe to attach to
user-facing payloads:

1. a validated model is publishable without a caveat, an unvalidated one is
   not — and the caveat names the gap instead of hiding it;
2. the stamp reads the registry (it can understate, never overstate) — a model
   whose status is raised in the registry gets the better stamp only after the
   evidence lands;
3. an unregistered model id raises instead of silently publishing.
"""

from __future__ import annotations

import pytest

from engine.models.maturity import maturity_of
from engine.models.publication import PUBLISHABLE_LEVELS, publication_stamp
from engine.models.registry import RegisteredModelSpec, get_model, list_models


def _spec(model_id: str) -> RegisteredModelSpec:
    """The registered spec, narrowed to the status-carrying subclass.

    ``get_model`` returns ``ModelSpec | None`` because that is what the services
    layer looks up; every id below comes from ``list_models()``, so the ``None``
    arm cannot be reached -- and asserting the narrower type is stronger than
    reading status attributes off an optional.
    """
    spec = get_model(model_id)
    assert isinstance(spec, RegisteredModelSpec), model_id
    return spec


def _a_validated_model_id() -> str:
    for model_id in list_models():
        if _spec(model_id).validation_status.value == "validated":
            return model_id
    pytest.skip("no validated model registered")


def _an_unvalidated_model_id() -> str:
    for model_id in list_models():
        if _spec(model_id).validation_status.value == "unvalidated":
            return model_id
    pytest.skip("no unvalidated model registered")


def test_validated_model_is_publishable_without_caveat() -> None:
    model_id = _a_validated_model_id()
    stamp = publication_stamp(model_id)
    assert stamp["publishable_without_caveat"] is True
    assert stamp["validation_status"] == "validated"
    assert stamp["caveat"]  # the stamp still carries the evidence line


def test_unvalidated_model_is_not_publishable_without_caveat() -> None:
    model_id = _an_unvalidated_model_id()
    stamp = publication_stamp(model_id)
    assert stamp["publishable_without_caveat"] is False
    assert stamp["validation_status"] == "unvalidated"
    assert "اعتبارسنجی" in stamp["caveat"]  # the caveat names the gap, in Persian
    assert "validated" in stamp["caveat"]


def test_stamp_matches_the_registry_and_maturity_view() -> None:
    for model_id in list_models():
        stamp = publication_stamp(model_id)
        model = _spec(model_id)
        assert stamp["maturity_level"] == maturity_of(model_id)
        assert stamp["validation_status"] == model.validation_status.value
        assert stamp["implementation_status"] == model.implementation_status.value
        assert stamp["verification_status"] == model.verification_status.value
        assert stamp["publishable_without_caveat"] == (
            stamp["maturity_level"] in PUBLISHABLE_LEVELS
        )


def test_unknown_model_id_raises() -> None:
    with pytest.raises(KeyError):
        publication_stamp("NO_SUCH_MODEL")


def test_publishable_set_is_exactly_the_eco06_bar() -> None:
    """Nothing is publishable without a caveat below the validated bar."""
    assert PUBLISHABLE_LEVELS == {"S3"}
