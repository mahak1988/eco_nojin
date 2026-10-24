"""S3-C1 honesty guard: every scientific gateway surface carries uncertainty.

VG-07 guard for the ECO-VALIDATION-PROGRAM (S3, Explainability & Uncertainty).
A gateway result must NEVER silently drop uncertainty: it must attach an
``UncertaintySpec`` that is EITHER a real quantified uncertainty (method/value/
confidence populated) OR the explicit honest sentinel ``NOT_ESTIMATED``. As the
engine owner wires real uncertainty onto Tier-C outputs (S3-C1), this keeps
holding; any surface that returns None or an unclassified uncertainty fails here.

The representative inputs are the engine's own worked values (USGS Theis, VG loam,
RUSLE 800ft/2%, USDA loam AWC) already exercised elsewhere in this suite.
"""

from __future__ import annotations

import pytest

from engine.gateway import EngineGateway, GatewayRequest, ProvenanceSpec

GW = EngineGateway()
PROV = ProvenanceSpec(source="uncertainty_guard", source_type="TEST")

#: (model_id, inputs) using each model's canonical, executed inputs.
CASES = {
    "CANON-005": {
        "transmissivity_m2day": 1000.0,
        "storativity": 3e-4,
        "pumping_rate_m3day": 4088.0,
        "distance_from_well_m": 1000.0,
        "time_since_pumping_start_days": 10.0,
    },
    "CANON-006": {
        "matric_potential": -100.0,
        "theta_r": 0.078,
        "theta_s": 0.43,
        "vg_alpha": 0.036,
        "vg_n": 1.56,
    },
    "CANON-007": {"slope_percent": 2.0, "slope_length_m": 243.84},
    "SOIL_AWC": {"texture_class": "loam"},
}


def _is_real_uncertainty(spec) -> bool:
    return any(getattr(spec, f, None) is not None for f in ("value", "method", "confidence_level"))


@pytest.mark.parametrize("model_id", sorted(CASES))
def test_scientific_surface_carries_uncertainty(model_id: str) -> None:
    result = GW.execute(
        GatewayRequest(
            model_id=model_id,
            inputs=CASES[model_id],
            input_units={},
            provenance=PROV,
        )
    )
    # A returned error is not a silently-missing uncertainty; it is a separate
    # (rejected-input) contract this suite does not assert on.
    assert result.uncertainty is not None, (
        f"{model_id}: result has no uncertainty spec (silent absence)"
    )
    spec = result.uncertainty
    utype = getattr(spec, "uncertainty_type", None)
    sentinel = utype == "NOT_ESTIMATED" or "NOT_ESTIMATED" in str(utype)
    assert _is_real_uncertainty(spec) or sentinel, (
        f"{model_id}: uncertainty is neither quantified nor the honest NOT_ESTIMATED "
        f"sentinel (type={utype})"
    )
    assert result.provenance is not None, f"{model_id}: result has no provenance (silent absence)"
