"""P0-5 -- the pedotransfer response no longer serves an unconfirmed Ks.

``engine/hydroma/soil/pedotransfer.py`` computes a saturated conductivity whose
coefficient set and 2.778 prefactor appear nowhere else in this repository and
cannot be traced to Saxton & Rawls (2006): with sand 40 / clay 20 it returns
~1.16e9 cm/day (11 500 km/day), and it returns *more* water for more clay
(4.1e38 cm/day for pure clay). Before this gate the value was emitted under the
key ``ks_cm_per_day`` and served live by ``SOIL_PEDOTRANSFER`` and
``POST /api/v1/hydroma/soil/pedotransfer/run``.

The arithmetic is unchanged; the value is now emitted under
``ks_cm_per_day_unconfirmed`` with ``ks_confirmed = False`` and the
``UNCONFIRMED_UNITHED_CONSTANTS`` marker. No caller and no test in the tree
read the old key, so nothing was deleted -- the rename is the containment.
"""

from __future__ import annotations

import pytest

from engine.gateway import (
    EngineGateway,
    GatewayError,
    GatewayRequest,
    GatewayResult,
    ProvenanceSpec,
)
from engine.hydroma.soil.pedotransfer import (
    UNCONFIRMED_UNITHED_CONSTANTS,
    estimate_soil_parameters,
)

GW = EngineGateway()
PROV = ProvenanceSpec(source="p0_5", source_type="TEST")

SANDY_LOAM = {"sand_pct": 65.0, "clay_pct": 10.0, "om_pct": 1.5}
CLAY = {"sand_pct": 0.0, "clay_pct": 100.0, "om_pct": 1.5}


def _gateway_values(**inputs: float) -> dict:
    r = GW.execute(
        GatewayRequest(
            model_id="SOIL_PEDOTRANSFER", inputs=inputs, input_units={}, provenance=PROV
        )
    )
    assert isinstance(r, GatewayResult), f"gateway failure: {r.error_code}: {r.message}"
    return r.values


class TestPedotransferKsGate:
    @pytest.mark.parametrize("inputs", [SANDY_LOAM, CLAY])
    def test_unconfirmed_key_is_present_and_flag_is_false(self, inputs: dict) -> None:
        out = estimate_soil_parameters(**inputs)
        assert "ks_cm_per_day_unconfirmed" in out
        assert out["ks_confirmed"] is False
        assert out["ks_unconfirmed_marker"] == UNCONFIRMED_UNITHED_CONSTANTS
        assert out["ks_note"]

    def test_confirmed_key_is_absent_from_the_kernel(self) -> None:
        assert "ks_cm_per_day" not in estimate_soil_parameters(**SANDY_LOAM)

    def test_awc_is_still_published_unflagged(self) -> None:
        """The containment must not disable the three attributed regressions."""
        out = estimate_soil_parameters(**SANDY_LOAM)
        for key in ("theta_1500", "theta_33", "awc"):
            assert key in out
        assert 0.0 < out["awc"] < 1.0

    def test_gateway_response_has_no_ks_cm_per_day(self) -> None:
        values = _gateway_values(**SANDY_LOAM)
        assert "ks_cm_per_day" not in values
        assert "ks_cm_per_day_unconfirmed" in values
        assert values["ks_confirmed"] is False

    def test_router_payload_has_no_ks_cm_per_day(self) -> None:
        """The live public endpoint is what the defect reached."""
        from services.api_gateway.routers.hydroma_soil import _run_pedotransfer

        out = _run_pedotransfer(dict(SANDY_LOAM))
        assert "ks_cm_per_day" not in out
        assert out["ks_unconfirmed_marker"] == UNCONFIRMED_UNITHED_CONSTANTS

    def test_facade_payload_has_no_ks_cm_per_day(self) -> None:
        from services._gateway_facade import estimate_soil_parameters as facade_ptf

        out = facade_ptf(SANDY_LOAM["sand_pct"], SANDY_LOAM["clay_pct"], SANDY_LOAM["om_pct"])
        assert "ks_cm_per_day" not in out
        assert out["ks_confirmed"] is False

    def test_a_failing_gateway_request_is_still_a_gateway_error(self) -> None:
        r = GW.execute(
            GatewayRequest(
                model_id="SOIL_PEDOTRANSFER-UNKNOWN",
                inputs={},
                input_units={},
                provenance=PROV,
            )
        )
        assert isinstance(r, GatewayError)
