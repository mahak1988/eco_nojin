"""D4 — the gateway's error code survives the services boundary.

Remediation item D4 of ``reports/eco-nojin/ERROR-MAP.md`` §4. The facade used
to turn every ``engine.gateway.GatewayError`` into
``RuntimeError(f"Gateway error: {result.message}")``
(``services/_gateway_facade.py:218-219``), discarding ``error_code``,
``validation_errors`` and ``evidence_id`` at the only boundary the 48
services modules that import the facade go through.

``GatewayCallError`` (``services/api_gateway/errors_gateway.py``) is the
replacement. These tests pin both halves of the change:

1. **carry** — the gateway's codes, validation messages, evidence id, trace id
   and model id are all reachable on the raised exception, and are mapped onto
   the specification's 13-code vocabulary through ``spec_error_code``;
2. **preserve** — the exception is still a ``RuntimeError``, still caught by
   ``except RuntimeError``, and ``str(exc)`` is still exactly
   ``"Gateway error: <gateway message>"``, so no existing consumer changes
   behaviour.

The end-to-end cases drive the real ``EngineGateway`` through the facade's
``_execute``, so a regression that puts the erasure back fails here.
"""

from __future__ import annotations

import pytest

from engine.errors import ERROR_CODES
from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    ProvenanceSpec,
)
from services._gateway_facade import _execute, calc_et0_hargreaves
from services._gateway_facade_adapters.carbon import CarbonProjectType
from services._gateway_facade_adapters.climate import (
    ChainInputs,
    CropWaterReqInput,
    ishigami,
)
from services._gateway_facade_adapters.cppbackend import (
    is_cpp_available,
    penman_monteith_et0,
)
from services._gateway_facade_adapters.economics import estimate_direct_employment
from services._gateway_facade_adapters.groundwater import (
    RunoffCalculator,
    assess_water_quality,
)
from services._gateway_facade_adapters.soil import LandscapeMetric, LandscapeMetrics
from services.api_gateway.errors_gateway import (
    GATEWAY_CODE_TO_SPEC_CODE,
    GATEWAY_ERROR_MESSAGE,
    SPEC_ERROR_CODES,
    GatewayCallError,
)

GW = EngineGateway()
PROV = ProvenanceSpec(source="d4_test", source_type="TEST")

#: The three codes ``engine/gateway/__init__.py`` can produce (ERROR-MAP §2.1).
GATEWAY_CODES = ("INVALID_REQUEST", "MODEL_NOT_FOUND", "EXECUTION_ERROR")

#: ``spec_error_code`` for each of the gateway's codes (ERROR-MAP §3).
EXPECTED_SPEC_CODE = {
    "INVALID_REQUEST": "INPUT_INVALID",
    "MODEL_NOT_FOUND": "MODEL_UNKNOWN",
    "EXECUTION_ERROR": "EXECUTION_FAILED",
}

#: A representative slice of the facade's re-exported public surface. A-2 step 1
#: moved the engine-import sites behind the adapters; these names must still be
#: importable from the facade itself.
FACADE_SURFACE = (
    "AnalysisType",
    "CarbonProjectType",
    "ChainInputs",
    "ChainResult",
    "CitizenBatch",
    "ECSI",
    "HPheno",
    "ishigami",
    "LandscapeMetric",
    "LandscapeMetrics",
    "RunoffCalculator",
    "SatelliteIndex",
    "TopographyAnalyzer",
    "assess_water_quality",
    "backend_status",
    "build_bbox",
    "calc_et0_hargreaves",
    "calculate_cec",
    "estimate_direct_employment",
    "estimate_rainfall_erosivity",
    "get_cpp_backend_status",
    "is_cpp_available",
    "run_validation_summary",
)


def _gateway_error(model_id: str, inputs: dict) -> GatewayError:
    """Execute a failing request and return the gateway's error value object."""
    result = GW.execute(
        GatewayRequest(
            model_id=model_id,
            inputs=inputs,
            input_units={},
            provenance=PROV,
        )
    )
    assert isinstance(result, GatewayError), f"expected a GatewayError, got {result!r}"
    return result


class TestMessageIsUnchanged:
    """The D4 behaviour guarantee: ``str(exc)`` is byte-identical."""

    def test_message_format_is_the_facade_template(self) -> None:
        assert GATEWAY_ERROR_MESSAGE == "Gateway error: {message}"

    def test_str_is_exactly_the_pre_d4_text(self) -> None:
        error = _gateway_error("NO_SUCH_MODEL", {"x": 1.0})
        exc = GatewayCallError.from_gateway_error(error)
        assert exc.message == f"Gateway error: {error.message}"
        assert str(exc) == f"Gateway error: {error.message}"

    def test_the_removed_raise_site_produced_the_same_string(self) -> None:
        """Compare against the literal expression the facade used to raise."""
        error = _gateway_error("CANON-001", {"x": 1.0})
        exc = GatewayCallError.from_gateway_error(error)
        legacy = RuntimeError(f"Gateway error: {error.message}")
        assert str(exc) == str(legacy)
        assert exc.args == legacy.args


class TestStillARuntimeError:
    """Behaviour-preserving: existing ``except RuntimeError`` arms keep working."""

    def test_subclasses_runtime_error(self) -> None:
        assert issubclass(GatewayCallError, RuntimeError)

    def test_default_handler_catches_it(self) -> None:
        error = _gateway_error("NO_SUCH_MODEL", {"x": 1.0})
        with pytest.raises(RuntimeError) as caught:
            raise GatewayCallError.from_gateway_error(error)
        assert isinstance(caught.value, GatewayCallError)

    def test_type_name_is_not_required_by_the_message(self) -> None:
        """The message never encodes the Python type, so text matching is safe."""
        error = _gateway_error("NO_SUCH_MODEL", {"x": 1.0})
        exc = GatewayCallError.from_gateway_error(error)
        assert "GatewayCallError" not in str(exc)
        assert "RuntimeError" not in str(exc)


class TestTheGatewayCodeIsCarried:
    """The D4 fix itself: the discarded fields now reach the caller."""

    @pytest.mark.parametrize(
        ("model_id", "inputs"),
        [
            ("NO_SUCH_MODEL", {"x": 1.0}),
            ("CANON-001", {"x": 1.0}),
        ],
    )
    def test_error_code_validation_errors_and_evidence_id_survive(
        self, model_id: str, inputs: dict
    ) -> None:
        error = _gateway_error(model_id, inputs)
        exc = GatewayCallError.from_gateway_error(error)

        assert exc.error_code == error.error_code
        assert exc.error_code in GATEWAY_CODES
        assert exc.validation_errors == list(error.validation_errors)
        assert exc.evidence_id == error.evidence_id
        assert exc.model_id == error.model_id

    def test_trace_id_is_taken_from_execution_metadata(self) -> None:
        error = _gateway_error("NO_SUCH_MODEL", {"x": 1.0})
        exc = GatewayCallError.from_gateway_error(error)
        assert error.execution is not None
        assert exc.trace_id == error.execution.trace_id

    def test_missing_optional_fields_stay_none(self) -> None:
        exc = GatewayCallError("Gateway error: boom")
        assert exc.error_code is None
        assert exc.validation_errors == []
        assert exc.evidence_id is None
        assert exc.trace_id is None
        assert exc.spec_error_code is None

    def test_validation_errors_are_copied_not_aliased(self) -> None:
        exc = GatewayCallError("Gateway error: boom", validation_errors=["a"])
        exc.validation_errors.append("b")
        assert exc.validation_errors == ["a", "b"]

    def test_as_dict_carries_code_first(self) -> None:
        error = _gateway_error("NO_SUCH_MODEL", {"x": 1.0})
        payload = GatewayCallError.from_gateway_error(error).as_dict()
        assert list(payload)[:2] == ["error_code", "spec_error_code"]
        assert payload["error_code"] == error.error_code
        assert payload["spec_error_code"] == "MODEL_UNKNOWN"
        assert payload["model_id"] == "NO_SUCH_MODEL"

    def test_repr_names_the_spec_code(self) -> None:
        exc = GatewayCallError("Gateway error: boom", error_code="MODEL_NOT_FOUND")
        assert repr(exc) == (
            "GatewayCallError(error_code='MODEL_NOT_FOUND', "
            "spec_error_code='MODEL_UNKNOWN', message='Gateway error: boom')"
        )


class TestSpecErrorCodeMapping:
    """The gateway's 3 codes mapped onto the specification's 13 (ERROR-MAP §3)."""

    def test_every_gateway_code_maps_to_a_spec_code(self) -> None:
        for gateway_code, spec_code in EXPECTED_SPEC_CODE.items():
            assert GATEWAY_CODE_TO_SPEC_CODE[gateway_code] == spec_code

    def test_the_map_covers_exactly_the_measured_gateway_vocabulary(self) -> None:
        assert set(GATEWAY_CODE_TO_SPEC_CODE) == set(EXPECTED_SPEC_CODE)

    def test_every_mapped_target_is_in_the_spec_vocabulary(self) -> None:
        for spec_code in GATEWAY_CODE_TO_SPEC_CODE.values():
            assert spec_code in ERROR_CODES, spec_code

    def test_spec_error_codes_is_the_engines_own_13(self) -> None:
        assert SPEC_ERROR_CODES == ERROR_CODES
        assert len(SPEC_ERROR_CODES) == 13

    @pytest.mark.parametrize("gateway_code", GATEWAY_CODES)
    def test_spec_error_code_on_the_exception(self, gateway_code: str) -> None:
        exc = GatewayCallError("Gateway error: boom", error_code=gateway_code)
        assert exc.spec_error_code == EXPECTED_SPEC_CODE[gateway_code]
        assert exc.spec_error_description == ERROR_CODES[exc.spec_error_code]

    def test_an_unknown_gateway_code_invents_nothing(self) -> None:
        exc = GatewayCallError("Gateway error: boom", error_code="SOMETHING_NEW")
        assert exc.spec_error_code is None
        assert exc.spec_error_description is None

    def test_the_end_to_end_model_unknown_case_carries_model_unknown(self) -> None:
        with pytest.raises(GatewayCallError) as caught:
            _execute("NO_SUCH_MODEL", {"x": 1.0})
        assert caught.value.error_code == "MODEL_NOT_FOUND"
        assert caught.value.spec_error_code == "MODEL_UNKNOWN"

    def test_the_end_to_end_missing_input_case_carries_input_invalid(self) -> None:
        with pytest.raises(GatewayCallError) as caught:
            _execute("CANON-001", {"x": 1.0})
        assert caught.value.error_code == "INVALID_REQUEST"
        assert caught.value.spec_error_code == "INPUT_INVALID"
        assert caught.value.validation_errors


class TestTheFacadeBoundaryEndToEnd:
    """The real boundary: ``_execute`` through the real gateway."""

    def test_a_failing_call_raises_gateway_call_error(self) -> None:
        with pytest.raises(GatewayCallError):
            _execute("CANON-001", {"x": 1.0})

    def test_a_failing_call_is_catchable_as_runtime_error(self) -> None:
        with pytest.raises(RuntimeError):
            _execute("CANON-001", {"x": 1.0})

    def test_the_facade_message_is_still_the_gateway_message(self) -> None:
        error = _gateway_error("CANON-001", {"x": 1.0})
        with pytest.raises(GatewayCallError) as caught:
            _execute("CANON-001", {"x": 1.0})
        assert str(caught.value) == f"Gateway error: {error.message}"

    def test_a_successful_call_is_untouched(self) -> None:
        out = _execute(
            "SOIL_CEC",
            {"clay_pct": 22.0, "organic_matter_pct": 3.4, "ph": 7.1},
        )
        assert isinstance(out, dict)
        assert out


class TestFacadePublicSurfaceIsUnchanged:
    """A-2 step 1: the adapters moved the imports, not the public names."""

    @pytest.mark.parametrize("name", FACADE_SURFACE)
    def test_the_facade_still_exports_the_name(self, name: str) -> None:
        import services._gateway_facade as facade

        assert hasattr(facade, name), name

    def test_the_facade_exports_the_error_type(self) -> None:
        import services._gateway_facade as facade

        assert facade.GatewayCallError is GatewayCallError

    def test_a_compute_entry_point_still_works(self) -> None:
        out = calc_et0_hargreaves(
            temp_max=32.0,
            temp_min=18.0,
            elevation=120.0,
            latitude=34.0,
            doy=200,
        )
        assert out["data"]["et0_mm_day"] > 0.0

    @pytest.mark.parametrize(
        "name",
        [
            "ECSI",
            "LandscapeMetrics",
            "TopographyAnalyzer",
            "estimate_rainfall_erosivity",
            "run_validation_summary",
        ],
    )
    def test_the_soil_adapter_and_the_facade_agree(self, name: str) -> None:
        import services._gateway_facade as facade
        from services._gateway_facade_adapters import soil

        assert getattr(facade, name) is getattr(soil, name)

    def test_the_landscape_metric_alias_is_the_same_dataclass(self) -> None:
        assert LandscapeMetric is LandscapeMetrics

    def test_the_economics_wrapper_still_delegates_to_the_engine(self) -> None:
        from services._gateway_facade_adapters import economics

        assert economics.estimate_direct_employment is estimate_direct_employment
        assert estimate_direct_employment.__module__.endswith(
            "_gateway_facade_adapters.economics"
        )

    def test_the_capability_probe_never_raises(self) -> None:
        assert isinstance(is_cpp_available(), bool)

    def test_penman_monteith_is_the_engine_kernel(self) -> None:
        from services._gateway_facade_adapters import cppbackend

        assert cppbackend.penman_monteith_et0 is penman_monteith_et0

    def test_groundwater_and_climate_engine_contracts_are_the_engines(self) -> None:
        from services._gateway_facade_adapters import climate, groundwater

        assert groundwater.RunoffCalculator is RunoffCalculator
        assert groundwater.assess_water_quality is assess_water_quality
        assert climate.CropWaterReqInput is CropWaterReqInput
        assert climate.ishigami is ishigami
        assert climate.ChainInputs is ChainInputs

    def test_carbon_project_type_is_the_engines(self) -> None:
        from services._gateway_facade_adapters import carbon

        assert carbon.CarbonProjectType is CarbonProjectType
