"""Tests for the multi-source verification oracle.

The oracle aggregates attestations from independent nodes, opens a challenge
window on a reported impact, and refuses to score a report nobody vouched
for. The properties that matter:

* an unknown node cannot attest;
* the challenge window is honoured, and a challenge records *who* raised it;
* finalisation reads the aggregate as a dict (the metric is a plain mapping).
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.oracle.service import DataSource, OracleService


@pytest.fixture
def service():
    """An oracle with a stub vault and ecosystem service."""
    vault = MagicMock()
    vault.store = AsyncMock(return_value="VAULT-1")
    vault.retrieve = AsyncMock(return_value={"payload": "x"})

    ecosystem = MagicMock()
    ecosystem.get_activity = AsyncMock(return_value={"id": "act-1"})
    ecosystem.get_trust_multiplier = AsyncMock(return_value=10000)

    return OracleService(vault, ecosystem)


async def _submit(service, activity_id="act-1", confidence=90):
    await service.register_oracle_node("node-1", "pk-1")
    await service.submit_attestation(
        activity_id=activity_id,
        node_id="node-1",
        data_type="soil_carbon",
        confidence=confidence,
        commitment="commit-1",
        signature="sig-1",
    )
    return await service.submit_impact_report(
        activity_id=activity_id,
        reporter="reporter-1",
        data_type="soil_carbon",
        confidence=confidence,
        impact_hash="hash-1",
        evidence_commitment="commit-1",
    )


class TestNodeRegistration:
    """Tests for the oracle-node registry."""

    async def test_a_node_is_registered(self, service):
        assert await service.register_oracle_node("node-1", "pk-1") is True
        assert "node-1" in service.registered_nodes

    async def test_a_node_is_not_registered_twice(self, service):
        await service.register_oracle_node("node-1", "pk-1")
        assert await service.register_oracle_node("node-1", "pk-1") is False

    async def test_the_weight_and_reputation_are_recorded(self, service):
        await service.register_oracle_node("node-1", "pk-1", weight=3, reputation=80)
        node = service.registered_nodes["node-1"]
        assert node["weight"] == 3
        assert node["reputation"] == 80


class TestAttestation:
    """Tests for the attestation path."""

    async def test_an_unknown_node_cannot_attest(self, service):
        with pytest.raises(ValueError, match="Unknown oracle node"):
            await service.submit_attestation(
                activity_id="act-1",
                node_id="stranger",
                data_type="soil_carbon",
                confidence=90,
                commitment="c",
                signature="s",
            )

    async def test_a_registered_node_can_attest(self, service):
        await service.register_oracle_node("node-1", "pk-1")
        attestation_id = await service.submit_attestation(
            activity_id="act-1",
            node_id="node-1",
            data_type="soil_carbon",
            confidence=90,
            commitment="c",
            signature="s",
        )
        assert attestation_id.startswith("ATT-")

    async def test_a_confidence_above_the_maximum_is_refused(self, service):
        await service.register_oracle_node("node-1", "pk-1")
        with pytest.raises(ValueError, match="Confidence exceeds maximum"):
            await service.submit_attestation(
                activity_id="act-1",
                node_id="node-1",
                data_type="soil_carbon",
                confidence=101,
                commitment="c",
                signature="s",
            )

    async def test_the_attestation_is_kept(self, service):
        """The attestation must be stored, or the aggregation has nothing to read."""
        await service.register_oracle_node("node-1", "pk-1")
        await service.submit_attestation(
            activity_id="act-1",
            node_id="node-1",
            data_type="soil_carbon",
            confidence=90,
            commitment="c",
            signature="s",
        )
        assert len(service._attestations["act-1"]) == 1
        assert service._attestations["act-1"][0]["node_id"] == "node-1"


class TestImpactReport:
    """Tests for the impact report and its challenge window."""

    async def test_a_report_is_stored(self, service):
        report_id = await _submit(service)
        assert report_id.startswith("RPT-")
        assert "act-1" in service._pending_reports

    async def test_a_report_opens_a_challenge_window(self, service):
        await _submit(service)
        pending = service._pending_reports["act-1"]
        assert pending["challenge_deadline"] is not None
        assert pending["challenge_deadline"] > datetime.now(UTC)

    async def test_a_report_for_an_unknown_activity_is_refused(self, service):
        service.ecosystem_service.get_activity = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="Activity not found"):
            await _submit(service, activity_id="act-nope")


class TestChallenge:
    """Tests for the challenge workflow."""

    async def test_a_report_can_be_challenged(self, service):
        await _submit(service)
        assert await service.challenge_report("act-1", "challenger-1") is True

    async def test_an_unknown_activity_cannot_be_challenged(self, service):
        assert await service.challenge_report("act-nope", "challenger-1") is False

    async def test_the_challenger_is_recorded(self, service):
        """The challenge must be attributable to the node that raised it."""
        await _submit(service)
        await service.challenge_report("act-1", "challenger-7")
        assert service._challenges["act-1"]["challenger"] == "challenger-7"

    async def test_a_report_cannot_be_challenged_twice(self, service):
        await _submit(service)
        assert await service.challenge_report("act-1", "challenger-1") is True
        assert await service.challenge_report("act-1", "challenger-2") is False

    async def test_a_challenge_is_resolved(self, service):
        await _submit(service)
        await service.challenge_report("act-1", "challenger-1")
        assert await service.resolve_challenge("act-1", upheld=True) is True
        assert "act-1" not in service._challenges

    async def test_resolving_an_unknown_challenge_fails(self, service):
        assert await service.resolve_challenge("act-nope", upheld=True) is False


class TestFinalization:
    """Tests for the metric finalisation."""

    async def test_the_metrics_cannot_be_finalised_inside_the_window(self, service):
        """The challenge window must be honoured."""
        await _submit(service)
        assert await service.finalize_impact_metrics("act-1") is None

    async def test_the_metrics_are_finalised_after_the_window(self, service):
        """After the window the aggregate is read and returned.

        The aggregate is a plain dict, so reading it as an attribute raised
        ``AttributeError`` and the finalisation never completed.
        """
        await _submit(service)
        # Move the deadline into the past.
        service._pending_reports["act-1"]["challenge_deadline"] = datetime.now(
            UTC
        ) - timedelta(seconds=1)

        finalized = await service.finalize_impact_metrics("act-1")
        assert finalized is not None
        assert finalized["activity_id"] == "act-1"
        assert finalized["metrics"]["confidence"] == 85

    async def test_a_challenged_report_is_not_finalised(self, service):
        await _submit(service)
        await service.challenge_report("act-1", "challenger-1")
        service._pending_reports["act-1"]["challenge_deadline"] = datetime.now(
            UTC
        ) - timedelta(seconds=1)
        assert await service.finalize_impact_metrics("act-1") is None

    async def test_an_unknown_activity_has_no_metrics(self, service):
        assert await service.finalize_impact_metrics("act-nope") is None

    def test_the_data_source_vocabulary_is_closed(self):
        assert {source.value for source in DataSource} == {
            "satellite",
            "gps_photo",
            "field",
            "lab",
            "community",
        }
