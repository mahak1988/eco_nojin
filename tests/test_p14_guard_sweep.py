"""P14 — the independent acceptance sweep: the guards that must exist.

P14's rule is that the implementer of a capability is not its auditor. These
tests do not re-test behaviour; they verify that the **guards delivered by the
earlier phases are still in the code**, so a later change cannot quietly delete
a protection while its behaviour tests still pass. Each test fails if the
corresponding guard is removed.

Covered: the access-control guards (P3), the freeze on EcoCoin writes (P1),
the money-write boundary scan (P5), the publication stamp's honesty (P10),
the tourism capacity refusal (P8), and the governance activation gate (P7).
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _source(*relative_parts: str) -> str:
    return (PROJECT_ROOT.joinpath(*relative_parts)).read_text(encoding="utf-8")


def test_orders_route_still_requires_the_user() -> None:
    source = _source("services", "api_gateway", "routers", "marketplace.py")
    assert 'Depends(require_user)]' in source, "the orders scope check disappeared"


def test_buyer_identity_still_comes_from_the_token() -> None:
    source = _source("services", "api_gateway", "routers", "marketplace.py")
    assert "buyer_name=str(user.id)" in source
    assert "P3: the buyer identity comes from the token" in source


def test_product_image_mutation_still_checks_ownership() -> None:
    source = _source("services", "api_gateway", "routers", "marketplace.py")
    assert "producer_id" in source and "403" in source


def test_ecocoin_writes_are_still_frozen() -> None:
    source = _source("services", "blockchain", "service.py")
    assert "_assert_ecocoin_writes_enabled" in source
    assert source.count("_assert_ecocoin_writes_enabled()") >= 10


def test_fabricated_ecocoin_routes_are_still_disabled() -> None:
    source = _source("services", "api_gateway", "routers", "blockchain.py")
    assert "_eco_disabled" in source
    assert source.count("Depends(_eco_disabled)") >= 15


def test_reconciliation_still_folds_adjustments() -> None:
    source = _source("services", "finance", "reconciliation.py")
    assert "_signed_adjustment_delta" in source


def test_publication_stamp_still_understates_never_overstates() -> None:
    source = _source("engine", "models", "publication.py")
    assert 'PUBLISHABLE_LEVELS = frozenset({"S3"})' in source


def test_advice_still_carries_limits_and_an_owner() -> None:
    source = _source("services", "tasminyar" , "explainability.py") if (
        PROJECT_ROOT / "services" / "tasminyar" / "explainability.py"
    ).is_file() else _source("services", "tasmimyar", "explainability.py")
    assert "advice must state its limits" in source
    assert "auto_applied" in source


def test_departure_capacity_is_still_enforced() -> None:
    """The seat rule lives on the model — one source for both services."""
    source = _source("services", "tourism", "departures.py")
    assert "departure has" in source and "seats left" in source
    assert "def take_seats" in source and "def release_seats" in source
    # the booking path routes through it, not around it
    service_source = _source("services", "tourism", "service.py")
    assert "departure.take_seats(participants_count)" in service_source
    assert "departure.release_seats(" in service_source


def test_governance_activation_gate_still_requires_charter_and_coordinator() -> None:
    source = _source("services", "village", "service.py")
    assert "a working group with a live coordinator" in source
    assert "activation requires an adopted charter" in source


def test_governance_router_still_scopes_cross_village_reads() -> None:
    source = _source("services", "village", "api.py")
    assert "_require_admin_of" in source
    assert "403" in source


def test_compliance_router_still_scopes_cross_subject_reads() -> None:
    source = _source("services", "compliance", "api.py")
    assert "another subject" in source
    assert source.count("403") >= 3
