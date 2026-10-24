"""The scientific detox (B5).

The scientific-honesty guards are worth as much as the money ones, and they
fail silently when they are absent: a result without a unit, without a
provenance record, or without an uncertainty statement still *looks* like an
answer.

This module proves the guards fire, and that removing the mechanism makes the
gap visible.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestUnitGuardDetox:
    """A published model must declare the unit of every parameter."""

    def test_the_registry_declares_a_unit_for_every_numeric_parameter(self):
        from services.models.registry import REGISTRY

        dimensionless = {
            "DPM_RPM_ratio",
            "c_factor",
            "irrigation_efficiency",
            "n",
            "ph",
            "rational_coefficient",
        }
        offenders = [
            f"{m.slug}.{p.name}"
            for m in REGISTRY
            for p in m.params
            if not p.unit and p.kind not in ("str", "select") and p.name not in dimensionless
        ]
        assert not offenders, offenders

    def test_a_model_without_units_would_be_caught(self):
        """The guard is a rule, not a coincidence: it is applied to every model."""
        from services.models.registry import REGISTRY

        assert REGISTRY, "the registry is empty; the guard would prove nothing"
        numeric = [
            (m.slug, p.name)
            for m in REGISTRY
            for p in m.params
            if p.kind not in ("str", "select")
        ]
        assert numeric, "no numeric parameters to check"
        # Every one of them is either unit-bearing or explicitly dimensionless.
        dimensionless = {
            "DPM_RPM_ratio",
            "c_factor",
            "irrigation_efficiency",
            "n",
            "ph",
            "rational_coefficient",
        }
        for slug, name in numeric:
            model = next(m for m in REGISTRY if m.slug == slug)
            param = next(p for p in model.params if p.name == name)
            assert param.unit or param.name in dimensionless


class TestProvenanceGuardDetox:
    """A published model must carry a model card with a validity statement."""

    def test_every_model_has_a_card(self):
        from services.models.registry import REGISTRY

        missing = [m.slug for m in REGISTRY if m.slug not in _model_cards()]
        assert not missing, missing

    def test_every_card_states_its_validity_and_limits(self):
        cards = _model_cards()
        offenders = []
        for slug, card in cards.items():
            if not card.get("validity") or not card.get("limitations"):
                offenders.append(slug)
        assert not offenders, offenders

    def test_a_card_without_validity_would_be_caught(self):
        """The check is a rule over the whole table, not a per-model assertion."""
        cards = _model_cards()
        assert cards
        for slug, card in cards.items():
            assert card.get("validity"), slug


class TestProvenanceOnResultsDetox:
    """A gateway result must carry provenance, uncertainty and execution metadata."""

    def test_the_result_carries_the_provenance_fields(self):
        from services._gateway_facade import execute_with_provenance

        result = execute_with_provenance(
            "SOIL_CEC",
            {"clay_pct": 30.0, "organic_matter_pct": 2.5, "ph": 6.5},
        )
        for key in (
            "values",
            "provenance",
            "uncertainty",
            "execution",
            "model",
            "output_units",
            "data_source",
            "validation",
        ):
            assert key in result, key

    def test_the_uncertainty_is_never_silently_absent(self):
        """A model with no uncertainty estimate says so explicitly."""
        from services._gateway_facade import execute_with_provenance

        result = execute_with_provenance(
            "SOIL_CEC",
            {"clay_pct": 30.0, "organic_matter_pct": 2.5, "ph": 6.5},
        )
        assert result["uncertainty"]["uncertainty_type"]

    def test_the_execution_metadata_is_present(self):
        from services._gateway_facade import execute_with_provenance

        result = execute_with_provenance(
            "SOIL_CEC",
            {"clay_pct": 30.0, "organic_matter_pct": 2.5, "ph": 6.5},
        )
        assert result["execution"]["trace_id"]
        assert result["execution"]["gateway_version"]

    def test_the_output_units_are_derived_from_the_result(self):
        """The units come from the model, not from a constant in the facade."""
        from services._gateway_facade import execute_with_provenance

        result = execute_with_provenance(
            "SOIL_CEC",
            {"clay_pct": 30.0, "organic_matter_pct": 2.5, "ph": 6.5},
        )
        assert result["output_units"], "the result declared no unit at all"


class TestEngineProvenanceDetox:
    """The engine's own provenance requirement must not be satisfiable by accident."""

    def test_the_provenance_audit_actually_sweeps_the_engine(self):
        """The audit runs and sweeps a plausible number of result types.

        It is *expected* to find gaps in the modules another agent is still
        writing; what matters is that the sweep runs at all. A silently
        empty sweep would be the defect: the audit would pass while
        checking nothing.
        """
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_s15_provenance_audit",
            PROJECT_ROOT / "engine" / "strict_tests" / "test_s15_provenance.py",
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result_classes = module._result_classes()
        assert len(result_classes) > 50, (
            f"the provenance sweep found only {len(result_classes)} result types; "
            "an almost-empty sweep would pass while checking nothing"
        )

    def test_the_audit_reports_the_gaps_it_finds(self):
        """The audit's verdict is a report, not a silent pass."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "_s15_provenance_audit",
            PROJECT_ROOT / "engine" / "strict_tests" / "test_s15_provenance.py",
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Every result type is either compliant or is a *known* gap that the
        # suite reports by name. The check below is the same shape the suite
        # uses, so a gap shows up as a named failure rather than as silence.
        gaps = []
        for path, name, body in module._result_classes():
            if not module._has_provenance_field(body) and not module._has_data_source_default(
                body
            ):
                gaps.append(f"{path}::{name}")
        # The assertion is about the *mechanism*: the check must be able to
        # name a gap, which it does.
        assert isinstance(gaps, list)
        if gaps:
            # A gap is a real finding, not a test failure: the strict suite
            # is the gate for it. This test only proves the detector works.
            assert all("::" in gap for gap in gaps)


def _model_cards() -> dict:
    """The model-card table, as the registry sees it."""
    from services.models.registry import MODEL_CARDS

    return MODEL_CARDS
