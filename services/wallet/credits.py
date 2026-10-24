"""Carbon credit issuance and retirement — Phases 2 and 3.

From ``reports/CREDIT_VALUE_ARCHITECTURE_FA_2026-10-02.md``.

Two properties this module exists to guarantee:

**A credit never claims a standard it was not verified against.** The class is
decided by whether a configured attester returned a reference, and the database
rejects the other three combinations. There is no default standard constant
anywhere. This is the structural replacement for the defect that stamped
``standard_code="VCS"`` on every credit regardless of evidence.

**Double retirement is impossible, and always-retirement is possible for both
classes.** A second retirement of the same unit is rejected by a unique
constraint rather than by a code path, so forgetting a check cannot reopen it.
Retiring a self-reported credit is allowed — the double-counting risk does not
depend on who verified the credit.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import CarbonCreditRecord, CarbonCreditState, CarbonRetirement


class CreditClass(StrEnum):
    ATTESTED = "attested"
    SELF_REPORTED = "self_reported"


#: The value stored for a self-reported credit. Deliberately a sentence rather
#: than a code, because it is what a reader of the record sees. Never a standard.
SELF_REPORTED_NOTE = "no registry consulted; measured by the platform"


class AttestationError(ValueError):
    """An attestation was requested but no attester can support it."""


@dataclass(frozen=True)
class Attestation:
    """What an attester returns. A serial number is mandatory.

    If a registry issues credits it always has one. An attester that cannot
    return one is not an attester for the purpose of this table.
    """

    serial_number: str
    standard_code: str
    reference: str


class Attester(Protocol):
    """Pluggable verifier. Absent is a valid configuration, not an error."""

    async def attest(
        self, *, project_ref: str, tonnes_co2e: Decimal, evidence_digest: str
    ) -> Attestation | None: ...


def _digest(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class CreditService:
    def __init__(self, db: AsyncSession, attester: Attester | None = None) -> None:
        self.db = db
        #: None is the normal state today. It yields SELF_REPORTED, not an error.
        self.attester = attester

    async def issue(
        self,
        *,
        holder_id: str,
        project_ref: str,
        tonnes_co2e: Decimal,
        evidence_digest: str,
    ) -> CarbonCreditRecord:
        """Issue one credit. The class follows the evidence, never a preference."""
        if tonnes_co2e <= 0:
            raise ValueError("tonnes_co2e must be positive")
        if not evidence_digest:
            raise ValueError(
                "evidence_digest is required; a credit with no evidence is an assertion"
            )

        attestation = None
        if self.attester is not None:
            attestation = await self.attester.attest(
                project_ref=project_ref,
                tonnes_co2e=tonnes_co2e,
                evidence_digest=evidence_digest,
            )

        if attestation is None:
            record = CarbonCreditRecord(
                serial_number=None,
                project_ref=project_ref,
                holder_id=holder_id,
                tonnes_co2e=tonnes_co2e,
                credit_class=CreditClass.SELF_REPORTED.value,
                standard_code=None,
                attestation_ref=None,
            )
        else:
            if not attestation.serial_number:
                raise AttestationError(
                    "attester returned no serial number; a registry-issued credit "
                    "always has one, so this attester cannot support 'attested'"
                )
            record = CarbonCreditRecord(
                serial_number=attestation.serial_number,
                project_ref=project_ref,
                holder_id=holder_id,
                tonnes_co2e=tonnes_co2e,
                credit_class=CreditClass.ATTESTED.value,
                standard_code=attestation.standard_code,
                attestation_ref=attestation.reference,
            )

        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def is_transferable(self, credit_id: int) -> bool:
        """Self-reported credits are not transferable. Anyone.

        This is a rule, not an authorisation decision, so it is not behind a
        dependency that could be wired wrongly.
        """
        record = await self.db.get(CarbonCreditRecord, credit_id)
        if record is None:
            raise LookupError(f"no credit {credit_id}")
        return record.credit_class == CreditClass.ATTESTED.value

    async def retire(
        self,
        *,
        credit_id: int,
        retired_by: str,
        chain_tx_hash: str | None = None,
    ) -> CarbonRetirement:
        """Retire a credit. Applies to both classes.

        The credit's own state moves to ``RETIRED`` and the retirement table
        carries a unique constraint on ``credit_id``. Either one alone would
        be enough to stop a double retirement; both are in place so that
        removing the service check cannot reopen the hole.
        """
        record = await self.db.get(CarbonCreditRecord, credit_id)
        if record is None:
            raise LookupError(f"no credit {credit_id}")

        if record.state == CarbonCreditState.RETIRED.value:
            raise ValueError(
                f"credit {credit_id} is already retired; double retirement is refused"
            )

        seq = await self.db.execute(
            select(func.coalesce(func.max(CarbonRetirement.sequence), 0) + 1).where(
                CarbonRetirement.credit_id == credit_id
            )
        )
        sequence = int(seq.scalar_one())

        digest = _digest(
            {
                "credit_id": credit_id,
                "sequence": sequence,
                "class": record.credit_class,
                "tonnes": str(record.tonnes_co2e),
                "serial": record.serial_number,
                "retired_by": retired_by,
            }
        )
        retirement = CarbonRetirement(
            credit_id=credit_id,
            sequence=sequence,
            retired_by=retired_by,
            payload_digest=digest,
            chain_tx_hash=chain_tx_hash,
        )
        self.db.add(retirement)

        record.state = CarbonCreditState.RETIRED.value

        await self.db.commit()
        await self.db.refresh(retirement)
        return retirement

    async def retirement_history(self, credit_id: int) -> list[CarbonRetirement]:
        result = await self.db.execute(
            select(CarbonRetirement)
            .where(CarbonRetirement.credit_id == credit_id)
            .order_by(CarbonRetirement.sequence)
        )
        return list(result.scalars().all())
