"""Repository hygiene guards.

These are cheap, fast checks against defects that are embarrassing in front of
a funder and expensive to fix late: an unfilled licence placeholder, a missing
contributor agreement, or a capability flag that drifted back to claiming more
than the code delivers.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LICENSE = REPO / "LICENSE"
CONTRIBUTING = REPO / "CONTRIBUTING.md"
AUTHORS = REPO / "AUTHORS"
BLOCKCHAIN_ROUTER = REPO / "services" / "api_gateway" / "routers" / "blockchain.py"
REDEMPTION = REPO / "services" / "ecowallet" / "redemption.py"
CREDIT_BRIDGE = REPO / "services" / "carbon" / "integration" / "credit_bridge.py"


class TestLicenseOwnership:
    """A funder's first IP-provenance check reads this file.

    An unfilled `[YEAR] [COPYRIGHT HOLDER]` cannot be signed off, so the
    placeholder must never come back.
    """

    def test_no_unfilled_placeholder(self):
        text = LICENSE.read_text(encoding="utf-8")
        assert "[YEAR]" not in text, "LICENSE still has an unfilled year"
        assert "[COPYRIGHT HOLDER]" not in text, (
            "LICENSE still has an unfilled copyright holder"
        )

    def test_named_holder_and_year(self):
        text = LICENSE.read_text(encoding="utf-8")
        assert re.search(r"Copyright \(c\) 20\d{2}", text), (
            "LICENSE has no year in its copyright line"
        )
        assert "دشت امید نارون" in text, "LICENSE does not name the holder"

    def test_remaining_gaps_are_declared_not_forgotten(self):
        """Items only the company can supply must be flagged, not silently blank."""
        text = LICENSE.read_text(encoding="utf-8")
        assert "TO BE SUPPLIED" in text, (
            "the registration number is still an undeclared gap"
        )

    def test_contributor_agreement_exists(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "Contributor Licence Agreement" in text
        # Whitespace-insensitive: the sentence wraps across lines.
        assert re.search(r"unsigned contribution cannot be\s+merged", text), (
            "the CLA must state that unsigned contributions are not merged"
        )

    def test_authors_file_names_the_holder(self):
        text = AUTHORS.read_text(encoding="utf-8")
        assert "دشت امید نارون" in text
        assert "dependency" in text.lower(), (
            "AUTHORS must disclose vendored third-party code"
        )


class TestNoOverstatedCapability:
    """The admin panel renders /health. It must not claim more than exists."""

    def test_every_capability_flag_is_false(self):
        src = BLOCKCHAIN_ROUTER.read_text(encoding="utf-8")
        advertised = re.findall(r'"features":\s*\{[^}]*\}', src, re.S)
        assert advertised, "no features block found in the blockchain router"
        for block in advertised:
            assert "True" not in block, f"a capability is advertised: {block}"

    def test_each_capability_carries_a_reason(self):
        src = BLOCKCHAIN_ROUTER.read_text(encoding="utf-8")
        body = src.split("_ECOCOIN_NOT_IMPLEMENTED", 1)[-1]
        for capability in (
            "ecocoin",
            "impact_certificate",
            "phase_gate",
            "oracle",
            "treasury",
            "ecosystem_fund",
            "mint_controller",
        ):
            assert f'"{capability}"' in body, f"{capability} has no stated status"

    def test_referral_program_is_not_claimed(self):
        src = BLOCKCHAIN_ROUTER.read_text(encoding="utf-8")
        assert '"referral_program": True' not in src, (
            "referral_program was True with no referral implementation"
        )

    def test_no_route_registered_twice(self):
        """A duplicated route shadows its handler and is unreachable."""
        src = BLOCKCHAIN_ROUTER.read_text(encoding="utf-8")
        paths = re.findall(r'^@router\.(?:get|post)\("([^"]+)"', src, re.M)
        duplicates = {p for p in paths if paths.count(p) > 1}
        assert not duplicates, f"duplicate routes: {sorted(duplicates)}"

    def test_no_phase_is_claimed_complete(self):
        src = BLOCKCHAIN_ROUTER.read_text(encoding="utf-8")
        assert '"all_passed": True' not in src, (
            "a phase gate is reported as passed with nothing implemented"
        )


class TestNoPromiseWeCannotKeep:
    """Redemption options are user-facing promises. Each must be one we can keep."""

    def test_insurance_discount_is_absent(self):
        src = REDEMPTION.read_text(encoding="utf-8")
        assert "INSURANCE_DISCOUNT = " not in src, (
            "insurance discount promised; the platform has no insurer and wants none"
        )

    def test_its_removal_is_recorded(self):
        src = REDEMPTION.read_text(encoding="utf-8")
        assert '"insurance_discount"' in src, (
            "the removal must stay auditable, not silent"
        )

    def test_market_access_claim_was_replaced_not_deleted(self):
        src = REDEMPTION.read_text(encoding="utf-8")
        assert "MARKET_ACCESS = " not in src
        assert "MARKET_FEE_DISCOUNT = " in src, (
            "the replacement should target a benefit we actually control"
        )

    def test_no_nominal_cash_value_is_asserted(self):
        """A stated IRR figure is a promise about someone else's pricing."""
        src = REDEMPTION.read_text(encoding="utf-8")
        assert "value_irr" not in src, (
            "nominal IRR value implies a third-party benefit we cannot deliver"
        )

    def test_every_option_states_what_is_not_included(self):
        """A boundary nobody reads is not a boundary.

        Every `RedemptionOption(...)` instantiation must carry
        `not_included=`. The dataclass itself is a class, not a call, so the
        two counts must be equal.
        """
        src = REDEMPTION.read_text(encoding="utf-8")
        options = src.count("RedemptionOption(")
        boundaries = src.count("not_included=")
        assert options > 0, "no redemption options found"
        assert boundaries == options, (
            f"{options - boundaries} option(s) declare no boundary"
        )


class TestDataQualityGate:
    """A modelled estimate has no measurement behind it and cannot back a token."""

    def test_only_field_verified_is_token_eligible(self):
        src = CREDIT_BRIDGE.read_text(encoding="utf-8")
        assert '{"field_verified"}' in src
        assert "modelled_estimate" not in src.split("TOKEN_ELIGIBLE_DATA_MODES", 1)[-1][:200], (
            "a modelled estimate must not be in the token-eligible set"
        )

    def test_issuance_gate_fails_closed(self):
        src = CREDIT_BRIDGE.read_text(encoding="utf-8")
        assert "TokenIssuanceNotPermitted" in src
        assert "raise TokenIssuanceNotPermitted" in src, (
            "the gate must raise, not merely log"
        )

    def test_state_vocabulary_cannot_silently_diverge(self):
        src = CREDIT_BRIDGE.read_text(encoding="utf-8")
        assert "TRANSFERRED" in src, (
            "TokenStatus.TRANSFERRED was missing, so every transfer reported a "
            "false DISCREPANCY"
        )
        assert "Unknown off-chain credit state" in src, (
            "an unknown state must raise rather than look like a mismatch"
        )


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
