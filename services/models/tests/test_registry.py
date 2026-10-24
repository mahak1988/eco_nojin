"""Tests for the services-level scientific model registry.

``services/models/registry.py`` wraps real engine functions and labels each
model with a fidelity badge. Two properties matter:

* every entry wraps a *real* function — there are no stubs;
* ``run_model`` refuses an unknown slug or a missing required parameter
  instead of silently falling back.
"""

import pytest

from services.models.registry import (
    MODEL_CARDS,
    REGISTRY,
    get_model,
    list_models,
    model_card,
    run_model,
)

VALID_FIDELITIES = {"official", "simplified", "experimental"}

#: Valid values for the string/select parameters, so the "every model runs"
#: test exercises the model rather than tripping over a placeholder.
STRING_VALUES: dict[str, str] = {
    "crop_type": "wheat",
    "scenario": "SSP2-4.5",
    "rcp": "SSP2-4.5",
    "project_type": "afforestation",
    "region": "temperate",
    "texture": "loam",
    "texture_class": "loam",
}


def _sample_value(slug: str, param) -> object:
    """A plausible value for a parameter that has no default."""
    if param.kind in ("str", "select"):
        return STRING_VALUES.get(param.name, "wheat")
    if param.name in ("theta_r",):
        return 0.05
    if param.name in ("theta_s",):
        return 0.45
    if param.name in ("n",):
        return 1.5
    if param.name in ("alpha",):
        return 0.02
    if param.name in ("matric_potential",):
        return -100.0
    if param.name in ("slope_length",):
        return 20.0
    if param.name in ("slope_percent",):
        return 5.0
    if param.name in ("annual_rainfall",):
        return 800.0
    if param.name in ("doy",):
        return 180
    if param.name in ("latitude",):
        return 30.0
    if param.name in ("longitude",):
        return 50.0
    if param.name in ("year", "time_horizon"):
        return 2050
    if param.name in ("precipitation", "rainfall_mm"):
        return 500.0
    if param.name in ("area_ha", "drainage_area_ha"):
        return 1.0
    if param.name in ("peak_flow",):
        return 2.0
    if param.name in ("slope",):
        return 5.0
    if param.name in ("ph",):
        return 6.5
    if param.name in ("organic_matter",):
        return 2.5
    if param.name in ("nitrogen",):
        return 100.0
    if param.name in ("phosphorus",):
        return 20.0
    if param.name in ("potassium",):
        return 150.0
    if param.name in ("cec",):
        return 12.0
    if param.name in ("available_water",):
        return 300.0
    if param.name in ("mean_temp",):
        return 22.0
    return 1.0


class TestRegistryContents:
    """Tests for the registry inventory."""

    def test_the_registry_is_not_empty(self):
        assert len(REGISTRY) > 0

    def test_the_slugs_are_unique(self):
        slugs = [m.slug for m in REGISTRY]
        assert len(slugs) == len(set(slugs))

    def test_every_model_declares_a_known_fidelity(self):
        for model in REGISTRY:
            assert model.fidelity in VALID_FIDELITIES, model.slug

    def test_every_model_has_both_names(self):
        for model in REGISTRY:
            assert model.name_fa, model.slug
            assert model.name_en, model.slug

    def test_every_model_has_a_reference(self):
        """A model without a reference cannot be cited."""
        for model in REGISTRY:
            assert model.reference, model.slug

    def test_every_model_has_a_domain(self):
        for model in REGISTRY:
            assert model.domain, model.slug

    def test_every_model_has_at_least_one_parameter(self):
        for model in REGISTRY:
            assert model.params, model.slug

    def test_every_parameter_has_a_label(self):
        for model in REGISTRY:
            for param in model.params:
                assert param.label, f"{model.slug}.{param.name}"

    def test_only_string_parameters_may_be_unitless(self):
        """A numeric parameter without a unit is a unit bug.

        The unitless *numeric* parameters are the known dimensionless ones
        (ratios, pH, exponents). A string or select parameter carries no unit
        by nature.
        """
        dimensionless = {
            "DPM_RPM_ratio",
            "c_factor",
            "irrigation_efficiency",
            "n",
            "ph",
            "rational_coefficient",
        }
        for model in REGISTRY:
            for param in model.params:
                if param.unit:
                    continue
                if param.kind in ("str", "select"):
                    continue
                assert param.name in dimensionless, f"{model.slug}.{param.name}"

    def test_a_string_default_is_declared_as_a_string(self):
        """A string default under a numeric kind breaks the caller path.

        ``run_model`` coerces a caller-supplied value with ``float()`` when the
        kind is numeric, so a string default such as ``region='temperate'``
        has to be declared ``kind='str'`` or passing it raises
        ``ValueError: could not convert string to float``.
        """
        for model in REGISTRY:
            for param in model.params:
                if isinstance(param.default, str):
                    assert param.kind == "str", f"{model.slug}.{param.name}"

    def test_every_model_card_exists(self):
        for model in REGISTRY:
            card = model_card(model.slug)
            assert card["validity"], model.slug
            assert card["limitations"], model.slug


class TestListModels:
    """Tests for the API-facing metadata view."""

    def test_it_lists_every_model(self):
        assert len(list_models()) == len(REGISTRY)

    def test_every_entry_carries_the_honesty_fields(self):
        for entry in list_models():
            assert entry["slug"]
            assert entry["fidelity"] in VALID_FIDELITIES
            assert entry["validity"]
            assert entry["limitations"]
            assert entry["reference"]

    def test_every_entry_lists_its_parameters(self):
        for entry in list_models():
            assert isinstance(entry["params"], list)
            for param in entry["params"]:
                assert param["name"]
                assert param["label"]
                assert "unit" in param
                assert param["kind"] in ("float", "int", "str", "select")


class TestGetModel:
    """Tests for the single-model lookup."""

    def test_a_known_slug_resolves(self):
        model = get_model(REGISTRY[0].slug)
        assert model is not None
        assert model.slug == REGISTRY[0].slug

    def test_an_unknown_slug_resolves_to_none(self):
        assert get_model("definitely-not-a-model") is None


class TestRunModel:
    """Tests for model execution."""

    def test_an_unknown_slug_is_refused(self):
        with pytest.raises(ValueError, match="unknown model slug"):
            run_model("definitely-not-a-model", {})

    def test_a_missing_required_parameter_is_refused(self):
        """A missing parameter must never fall back to a silent default."""
        model = next(m for m in REGISTRY if any(p.default is None for p in m.params))
        missing = next(p.name for p in model.params if p.default is None)
        params = {
            p.name: (p.default if p.default is not None else 1.0)
            for p in model.params
            if p.name != missing
        }
        with pytest.raises(ValueError, match="missing required parameter"):
            run_model(model.slug, params)

    def test_a_successful_run_reports_its_fidelity(self):
        """At least one model must run end-to-end with its declared defaults."""
        ran = False
        for model in REGISTRY:
            params = {p.name: p.default for p in model.params if p.default is not None}
            if len(params) != len(model.params):
                continue  # a required parameter has no default
            try:
                outcome = run_model(model.slug, params)
            except (ValueError, TypeError, KeyError):
                continue
            assert outcome["slug"] == model.slug
            assert outcome["fidelity"] == model.fidelity
            assert "result" in outcome
            assert outcome["executed_ms"] >= 0
            ran = True
            break
        assert ran, "no model could be executed with its declared defaults"

    def test_the_declared_params_match_the_function_signature(self):
        """A declared parameter the function does not accept is a dead model.

        ``erosion_usle`` declared ``slope_length_m`` / ``annual_rainfall_mm``
        while the underlying function took ``slope_length`` /
        ``annual_rainfall``, so every call raised ``TypeError`` and the model
        could never run.
        """
        import inspect

        for model in REGISTRY:
            accepted = set(inspect.signature(model.run).parameters)
            for param in model.params:
                assert param.name in accepted, f"{model.slug}.{param.name}"

    def test_a_model_with_a_complete_parameter_set_runs(self):
        """A model whose parameters are all satisfiable must actually run.

        This catches the other half of the defect: routing to a gateway id
        that is not registered in the engine.
        """
        failures: list[str] = []
        for model in REGISTRY:
            required = [p for p in model.params if p.default is None]
            if not required:
                continue
            params = {
                p.name: (
                    p.default
                    if p.default is not None
                    else _sample_value(model.slug, p)
                )
                for p in model.params
            }
            try:
                run_model(model.slug, params)
            except Exception as exc:  # noqa: BLE001 - the point is to report it
                failures.append(f"{model.slug}: {type(exc).__name__}: {exc}")
        assert not failures, "models that cannot run:\n  " + "\n  ".join(failures)


class TestModelCards:
    """Tests for the honesty card table."""

    def test_the_card_table_covers_every_model(self):
        for model in REGISTRY:
            assert model.slug in MODEL_CARDS, model.slug

    def test_an_unknown_slug_returns_an_empty_card(self):
        card = model_card("definitely-not-a-model")
        assert card["validity"] == ""
        assert card["limitations"] == ""
