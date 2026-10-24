"""Tests for the carbon-credit issuance and retirement rules.

``services/wallet/credits.py`` exists to guarantee two properties:

* a credit never claims a standard it was not verified against — the class is
  decided by whether an attester returned a reference;
* double retirement is impossible — a second retirement of the same unit is
  rejected, and retiring a self-reported credit is still allowed.
"""

from decimal import Decimal

import pytest

from database.models import CarbonCreditState
from services.wallet.credits import (
    SELF_REPORTED_NOTE,
    Attestation,
    AttestationError,
    CreditClass,
    CreditService,
)


class FakeAttester:
    """An attester that always returns a serial number."""

    def __init__(self, serial_number: str = "SER-1", standard_code: str = "VCS"):
        self.serial_number = serial_number
        self.standard_code = standard_code
        self.calls = 0

    async def attest(self, *, project_ref, tonnes_co2e, evidence_digest):
        self.calls += 1
        return Attestation(
            serial_number=self.serial_number,
            standard_code=self.standard_code,
            reference=f"REF-{project_ref}",
        )


class SerialLessAttester:
    """An attester that cannot return a serial number."""

    async def attest(self, *, project_ref, tonnes_co2e, evidence_digest):
        return Attestation(serial_number="", standard_code="VCS", reference="REF-X")


@pytest.fixture
def service(db_session):
    return CreditService(db_session)


class TestCreditClass:
    """Tests for the credit-class vocabulary."""

    def test_the_two_classes_exist(self):
        assert CreditClass.ATTESTED.value == "attested"
        assert CreditClass.SELF_REPORTED.value == "self_reported"

    def test_the_self_reported_note_is_a_sentence(self):
        """The stored value is what a reader sees; it must not be a code."""
        assert " " in SELF_REPORTED_NOTE
        assert SELF_REPORTED_NOTE != CreditClass.SELF_REPORTED.value


class TestIssuing:
    """Tests for issuing a credit."""

    async def test_without_an_attester_the_credit_is_self_reported(self, service):
        record = await service.issue(
            holder_id="holder-1",
            project_ref="proj-1",
            tonnes_co2e=Decimal("10.5"),
            evidence_digest="abc123",
        )
        assert record.credit_class == CreditClass.SELF_REPORTED.value
        assert record.standard_code is None
        assert record.attestation_ref is None
        assert record.serial_number is None

    async def test_with_an_attester_the_credit_is_attested(self, db_session):
        service = CreditService(db_session, attester=FakeAttester())
        record = await service.issue(
            holder_id="holder-1",
            project_ref="proj-1",
            tonnes_co2e=Decimal("10.5"),
            evidence_digest="abc123",
        )
        assert record.credit_class == CreditClass.ATTESTED.value
        assert record.standard_code == "VCS"
        assert record.attestation_ref == "REF-proj-1"
        assert record.serial_number == "SER-1"

    async def test_the_attester_is_called(self, db_session):
        attester = FakeAttester()
        service = CreditService(db_session, attester=attester)
        await service.issue(
            holder_id="h",
            project_ref="p",
            tonnes_co2e=Decimal("1"),
            evidence_digest="d",
        )
        assert attester.calls == 1

    async def test_a_credit_without_evidence_is_refused(self, service):
        """A credit with no evidence is an assertion, not a credit."""
        with pytest.raises(ValueError, match="evidence_digest is required"):
            await service.issue(
                holder_id="h",
                project_ref="p",
                tonnes_co2e=Decimal("1"),
                evidence_digest="",
            )

    async def test_a_non_positive_quantity_is_refused(self, service):
        with pytest.raises(ValueError, match="must be positive"):
            await service.issue(
                holder_id="h",
                project_ref="p",
                tonnes_co2e=Decimal("0"),
                evidence_digest="d",
            )
        with pytest.raises(ValueError, match="must be positive"):
            await service.issue(
                holder_id="h",
                project_ref="p",
                tonnes_co2e=Decimal("-1"),
                evidence_digest="d",
            )

    async def test_an_attester_without_a_serial_is_refused(self, db_session):
        """A registry-issued credit always has a serial number."""
        service = CreditService(db_session, attester=SerialLessAttester())
        with pytest.raises(AttestationError, match="no serial number"):
            await service.issue(
                holder_id="h",
                project_ref="p",
                tonnes_co2e=Decimal("1"),
                evidence_digest="d",
            )


class TestTransferability:
    """Tests for the transferability rule."""

    async def test_a_self_reported_credit_is_not_transferable(self, service):
        record = await service.issue(
            holder_id="h",
            project_ref="p",
            tonnes_co2e=Decimal("1"),
            evidence_digest="d",
        )
        assert await service.is_transferable(record.id) is False

    async def test_an_attested_credit_is_transferable(self, db_session):
        service = CreditService(db_session, attester=FakeAttester())
        record = await service.issue(
            holder_id="h",
            project_ref="p",
            tonnes_co2e=Decimal("1"),
            evidence_digest="d",
        )
        assert await service.is_transferable(record.id) is True

    async def test_a_missing_credit_raises(self, service):
        with pytest.raises(LookupError):
            await service.is_transferable(999999)


class TestRetirement:
    """Tests for retiring a credit."""

    async def test_a_self_reported_credit_can_be_retired(self, service):
        """Retirement applies to both classes."""
        record = await service.issue(
            holder_id="h",
            project_ref="p",
            tonnes_co2e=Decimal("3"),
            evidence_digest="d",
        )
        retirement = await service.retire(
            credit_id=record.id, retired_by="holder-1", chain_tx_hash="0xabc"
        )
        assert retirement.credit_id == record.id
        assert retirement.sequence == 1

    async def test_a_second_retirement_is_refused(self, service):
        """A credit can only ever be retired once."""
        record = await service.issue(
            holder_id="h",
            project_ref="p",
            tonnes_co2e=Decimal("3"),
            evidence_digest="d",
        )
        await service.retire(credit_id=record.id, retired_by="holder-1")
        with pytest.raises(ValueError, match="already retired"):
            await service.retire(credit_id=record.id, retired_by="holder-1")

    async def test_retiring_moves_the_credit_to_retired(self, service):
        """The credit's own state records the retirement."""
        record = await service.issue(
            holder_id="h",
            project_ref="p",
            tonnes_co2e=Decimal("3"),
            evidence_digest="d",
        )
        assert record.state == CarbonCreditState.ACTIVE.value
        await service.retire(credit_id=record.id, retired_by="holder-1")
        await service.db.refresh(record)
        assert record.state == CarbonCreditState.RETIRED.value

    async def test_the_database_refuses_a_second_retirement(self, service):
        """The guarantee is a constraint, not only a code path.

        If the service check were removed, the unique constraint on
        ``carbon_retirements.credit_id`` has to still refuse the duplicate.
        """
        from sqlalchemy.exc import IntegrityError

        from database.models import CarbonRetirement

        record = await service.issue(
            holder_id="h",
            project_ref="p",
            tonnes_co2e=Decimal("3"),
            evidence_digest="d",
        )
        await service.retire(credit_id=record.id, retired_by="holder-1")

        service.db.add(
            CarbonRetirement(
                credit_id=record.id,
                sequence=2,
                retired_by="holder-1",
                payload_digest="0" * 64,
            )
        )
        with pytest.raises(IntegrityError):
            await service.db.commit()
        await service.db.rollback()

    async def test_retiring_a_missing_credit_raises(self, service):
        with pytest.raises(LookupError):
            await service.retire(credit_id=999999, retired_by="h")
