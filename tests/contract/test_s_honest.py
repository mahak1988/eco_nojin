"""Tests for the S-HONEST contract module.

The status envelope is only worth anything if its invariants actually hold, so
these tests pin the four rules that make "silent success" impossible:

1. a non-OK status cannot omit ``reason``;
2. an OK status cannot carry a reason or a fallback;
3. synthetic data cannot be reported as OK;
4. ``assert_honest`` catches a response dict that contradicts its own
   provenance.

The last one is the mechanical half of the CI gate that phase 3 wires up, and
it is written here against the concrete shapes that were previously shipping
fabricated success from ``backup``, ``traceability`` and ``land_profile``.
"""

from __future__ import annotations

import pytest

from services._contracts.status import (
    IncompleteResultError,
    Provenance,
    Status,
    Tainted,
    assert_honest,
    degraded,
    not_implemented,
    ok,
    unavailable,
)


class TestInvariants:
    def test_non_ok_requires_a_reason(self):
        with pytest.raises(ValueError, match="requires a non-empty reason"):
            Tainted(data=[1], status=Status.DEGRADED)

    def test_ok_cannot_carry_a_reason(self):
        with pytest.raises(ValueError, match="cannot carry a reason"):
            Tainted(data=[1], status=Status.OK, reason="used a surrogate")

    def test_ok_cannot_carry_a_fallback(self):
        with pytest.raises(ValueError, match="cannot carry a reason"):
            Tainted(data=[1], status=Status.OK, fallback_used="scs.runoff")

    def test_synthetic_cannot_be_reported_as_ok(self):
        with pytest.raises(ValueError, match="synthetic data cannot be reported"):
            Tainted(data=[1], status=Status.OK, provenance=Provenance(source="x", synthetic=True))

    def test_synthetic_is_allowed_when_the_status_says_so(self):
        result = degraded(
            [1],
            reason="terrain synthesised, not measured",
            provenance=Provenance(source="synthetic", synthetic=True),
        )
        assert result.status is Status.DEGRADED
        assert not result.ok


class TestConstruction:
    def test_ok_helper(self):
        result = ok([1, 2, 3])
        assert result.ok
        assert result.unwrap() == [1, 2, 3]

    def test_degraded_records_the_fallback(self):
        result = degraded([], reason="pg_dump absent", fallback_used="scs.runoff")
        assert result.status is Status.DEGRADED
        assert result.fallback_used == "scs.runoff"

    def test_unavailable(self):
        result = unavailable(None, reason="CDSE token not configured")
        assert result.status is Status.UNAVAILABLE

    def test_not_implemented(self):
        result = not_implemented("physical restore (pg_basebackup)")
        assert result.status is Status.NOT_IMPLEMENTED
        assert result.data is None

    def test_unwrap_raises_for_incomplete(self):
        with pytest.raises(IncompleteResultError) as exc:
            not_implemented("nope").unwrap()
        assert "not_implemented" in str(exc.value)

    def test_as_dict_is_json_ready(self):
        payload = degraded(
            5,
            reason="surrogate",
            fallback_used="x",
            provenance=Provenance(source="derived", engine="a.py:1"),
        ).as_dict()
        assert payload["status"] == "degraded"
        assert payload["provenance"]["engine"] == "a.py:1"
        assert payload["provenance"]["synthetic"] is False


class TestAssertHonest:
    def test_passes_for_an_ordinary_response(self):
        assert_honest({"status": "ok", "data": [1, 2]})
        assert_honest({"rows": [{"account_id": "cash"}]})

    def test_catches_passed_over_synthetic_provenance(self):
        """The backup shape: 'passed' alongside fabricated content."""
        with pytest.raises(ValueError, match="contradicts synthetic provenance"):
            assert_honest(
                {
                    "status": "passed",
                    "provenance": {"source": "synthetic", "synthetic": True},
                }
            )

    def test_catches_a_nested_contradiction(self):
        with pytest.raises(ValueError, match="contradicts synthetic provenance"):
            assert_honest(
                {
                    "result": {
                        "verification_status": "passed",
                        "data_provenance": {"synthetic": True},
                    }
                }
            )

    def test_a_tainted_ok_with_synthetic_provenance_cannot_be_constructed(self):
        """The invariant is enforced at construction, so assert_honest never
        has to catch this case at all."""
        with pytest.raises(ValueError, match="synthetic data cannot be reported"):
            Tainted(
                data=1, status=Status.OK, provenance=Provenance(source="synthetic", synthetic=True)
            )

    def test_allows_degraded_with_synthetic_provenance(self):
        assert_honest(
            {
                "status": "degraded",
                "reason": "terrain invented",
                "provenance": {"source": "synthetic", "synthetic": True},
            }
        )


class TestStatusCoversEveryNotImplementedPath:
    def test_no_status_encodes_failure_as_data(self):
        """`failed` must never be a member: a failure is an exception."""
        assert "failed" not in {s.value for s in Status}

    def test_registry_entries_reference_a_contract_status(self):
        import re
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        registry = root / "docs" / "standards" / "tolerated-degradations.yaml"
        text = registry.read_text(encoding="utf-8")
        declared = set(re.findall(r"^\s+status:\s*(\w+)\s*$", text, re.MULTILINE))
        assert declared, "registry should declare statuses"
        assert declared <= {"ok", "degraded", "stale", "unavailable", "not_implemented"}

    def test_every_toleration_names_an_owner(self):
        import re
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        text = (root / "docs" / "standards" / "tolerated-degradations.yaml").read_text(
            encoding="utf-8"
        )
        owners = re.findall(r"^\s+owner:\s*(D-\d+)\s*$", text, re.MULTILINE)
        assert len(owners) >= 15, "every toleration needs a named owner"
        assert all(re.fullmatch(r"D-\d+", o) for o in owners)

    def test_phase1_items_are_no_longer_tolerated(self):
        """Phase 1 replaced these; they must not linger in the registry."""
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        text = (root / "docs" / "standards" / "tolerated-degradations.yaml").read_text(
            encoding="utf-8"
        )
        for gone in ("backup-mock-file", "ledger-verify-chain", "ledger-memory-only"):
            assert gone not in text, f"{gone} was fixed in phase 1 and should be removed"
