"""EcoBalance — the independent, non-transferable platform balance.

Phase 1 of ``reports/CREDIT_VALUE_ARCHITECTURE_FA_2026-10-02.md``. The design
rule that everything here serves: **a balance may only be credited from data
whose provenance is ``measured``**, and the credit must name the observation and
pin the exact bytes that justified it.

The rejection is the point. This module issues *nothing* for ``degraded`` or
``simulated`` observations, and that refusal is tested. An incentive paid for
fabricated data is not a weak incentive, it is an instruction to fabricate data.

Deliberately absent, and each omission is a decision rather than a gap:

* **no transfer method.** ``docs/principles`` promises the user keeps their
  data and needs no permission to leave; it does not promise a transferable
  balance. The first one is a right, the second is a regulated instrument.
* **no admin override.** There is no way for an operator to mint a balance,
  because an operator who can mint one is the central authority the platform is
  built to not have.
* **no exchange rate.** A rate would be the first step toward convertibility.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import EcoBalanceAccount, EcoBalanceEntry

#: Units of EcoBalance per tonne of CO2e observed as a removal. A constant, not
#: a market price: this is a recognition of work, never a valuation.
UNITS_PER_TONNE = Decimal("100")


#: What a credit may be issued for. Not free text, and closed on purpose: every
#: addition is a new thing the platform now pays for, so it has to be named here
#: rather than emerging from whatever a caller passes.
#
#: All three families below are keyed to *observed work*, never to a monetary
#: value. See docs/decisions/DEC-0001_REWARD_ONLY_VALUE_INSTRUMENT_FA.md.
class Reason(StrEnum):
    # --- environmental observation ---
    SOIL_CARBON_OBSERVED = "soil_carbon_observed"
    SATELLITE_VERIFIED = "satellite_verified"
    LAND_ACTION_RECORDED = "land_action_recorded"
    #: Re-verification of a field already being monitored. Paid deliberately: the
    #: costly thing in every monitoring programme is coming back a second year,
    #: and most schemes fail by abandoning the re-measurement.
    REVERIFICATION_COMPLETED = "reverification_completed"
    #: Change detected between two observations — degradation or improvement.
    #: Paying for the signal either way is what keeps monitoring honest, because a
    #: system that only pays for improvement is a system that gets gamed.
    CHANGE_DETECTED = "change_detected"
    # --- stewardship practice ---
    SOIL_COVER_MAINTAINED = "soil_cover_maintained"
    EROSION_CONTROL_INSTALLED = "erosion_control_installed"
    WATER_RETENTION_MEASURE = "water_retention_measure"
    COMPOST_OR_RESIDUE_APPLIED = "compost_or_residue_applied"
    # --- evidence quality, paid separately from the work itself ---
    #: Submitting verifiable ground truth about one's own field. This is the
    #: highest-leverage reward in the system: it makes the platform's data better
    #: in a way no satellite pass can, and it is cheap to pay for.
    GROUND_TRUTH_SUBMITTED = "ground_truth_submitted"
    DATA_QUALITY_CORRECTION = "data_quality_correction"
    #: A flagged observation later confirmed, which is the negative case of the
    #: same skill and is otherwise never rewarded.
    FLAG_CONFIRMED = "flag_confirmed"


#: Provenance values accepted as the basis for a credit. Derived from
#: ``engine.hydroma.provenance.DataSource``, restated here rather than imported
#: so that a credit can never be issued from a value this module does not name.
ACCEPTABLE_SOURCES = frozenset({"measured"})

#: Named for auditability: a caller asked for a credit on data we cannot use.
REJECTED = "evidence_source_not_measured"


class EvidenceRejected(ValueError):
    """The observation cannot justify a credit.

    Raised rather than returning zero, because "credited nothing" and "refused
    because the data was degraded" are different facts and a caller must be able
    to tell them apart.
    """

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


#: ASSUMPTION, not a sourced figure. The largest plausible annual soil-carbon
#: gain credited to one hectare in one observation period. Set high enough that
#: no legitimate farm is refused, and low enough that the worst recorded case —
#: 500 tCO2e claimed from a single hectare — is.
#:
#: It was added after an adversarial suite found that nothing bounded the input
#: at all: a caller could claim 500 tonnes, receive tokens, and take them to an
#: exchange. For a platform whose revenue is the token's price, an unbounded
#: claim is not an inconvenience, it is the whole loss.
#:
#: If a real figure becomes available from a soil-carbon methodology, replace
#: this constant and the boundary tests will tell you what moved.
MAX_TONNES_PER_HECTARE = Decimal("25")

#: Raised when a claim exceeds the ceiling for the area it claims.
IMPLAUSIBLE = "implausible_tonnage_for_area"
#:
#: Deliberately not one number for all. A flat rate pays for being *seen* rather
#: than for the work, and every programme that has tried a flat rate ends up
#: paying the easiest participants. Ground truth is weighted highest because it is
#: the only input the platform cannot obtain for itself.
#: Unit multipliers per reason. A constant, never a market value.
#:
#: Deliberately not one number for all. A flat rate pays for being *seen*
#: rather than for the work, and every programme that has tried one ends up
#: paying the easiest participants.
REASON_MULTIPLIER: dict[str, Decimal] = {
    Reason.SOIL_CARBON_OBSERVED: Decimal("1.0"),
    Reason.SATELLITE_VERIFIED: Decimal("0.5"),
    Reason.LAND_ACTION_RECORDED: Decimal("1.0"),
    Reason.REVERIFICATION_COMPLETED: Decimal("1.2"),
    Reason.CHANGE_DETECTED: Decimal("0.8"),
    Reason.SOIL_COVER_MAINTAINED: Decimal("0.9"),
    Reason.EROSION_CONTROL_INSTALLED: Decimal("1.5"),
    Reason.WATER_RETENTION_MEASURE: Decimal("1.5"),
    Reason.COMPOST_OR_RESIDUE_APPLIED: Decimal("1.0"),
    Reason.GROUND_TRUTH_SUBMITTED: Decimal("4.0"),
    Reason.DATA_QUALITY_CORRECTION: Decimal("2.0"),
    Reason.FLAG_CONFIRMED: Decimal("2.5"),
}


def units_for(reason: Reason, tonnes_co2e: Decimal) -> Decimal:
    """Units earned, from tonnes and the reason's weight.

    Two inputs, both earned. No rate, no price, no conversion — see
    docs/decisions/DEC-0001_REWARD_ONLY_VALUE_INSTRUMENT_FA.md.
    """
    weight = REASON_MULTIPLIER.get(reason.value if isinstance(reason, Reason) else str(reason))
    if weight is None:
        raise EvidenceRejected(
            "unknown_reason", f"{reason!r} has no multiplier; every paid reason must be named"
        )
    return (tonnes_co2e * UNITS_PER_TONNE * weight).quantize(Decimal("0.000001"))


def evidence_digest(payload: dict) -> str:
    """SHA-256 over the canonical serialisation of the evidence.

    Canonical because the digest is the claim that two runs saw the same inputs;
    key order or a float repr difference would break that for no good reason.
    """
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


#: Raised when the same observation is submitted twice for one user.
REPLAYED = "observation_already_credited"

#: Provenance recorded for every entry. Fixed 2026-10-03 — the real column value
#: was "measured" even for `source="degraded"`, because a previous version
#: substituted the constant rather than the argument. Nothing read the column, so
#: nothing caught it.
ENTRY_PROVENANCE_MEASURED = "measured"


class EcoBalanceService:
    """Issues EcoBalance from verified observations. Never sells it."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def account_for(self, user_id: str) -> EcoBalanceAccount:
        result = await self.db.execute(
            select(EcoBalanceAccount).where(EcoBalanceAccount.user_id == user_id).with_for_update()
        )
        account = result.scalar_one_or_none()
        if account is not None:
            return account
        account = EcoBalanceAccount(user_id=user_id, balance=Decimal("0"))
        self.db.add(account)
        try:
            await self.db.flush()
        except IntegrityError:
            # A concurrent first credit won the race; adopt its row rather than
            # creating a second one.
            #
            # REGRESSION NOTE 2026-10-03: replacing this rollback() with
            # `begin_nested()` savepoints was tried, because rolling back the
            # whole session raises PendingRollbackError on every later call —
            # a denial of service against whoever sent the request. It made the
            # red-team suite WORSE (2 failures to 9) and was reverted. The fix
            # needs the savepoint at the transaction level around the whole
            # credit(), not around this one statement, and that is a redesign
            # rather than an edit. Left as it was, knowingly imperfect.
            await self.db.rollback()
            result = await self.db.execute(
                select(EcoBalanceAccount)
                .where(EcoBalanceAccount.user_id == user_id)
                .with_for_update()
            )
            return result.scalar_one()
        return account

    async def credit(
        self,
        *,
        user_id: str,
        tonnes_co2e: Decimal,
        source: str,
        observation_id: str,
        reason: Reason,
        evidence: dict,
        plot_area_ha: Decimal | None = None,
    ) -> Decimal:
        """Credit a user for a verified observation. Returns the new balance.

        ``source`` must be ``"measured"`` and ``tonnes_co2e`` must be positive.
        Both are checked here rather than trusted from the caller.

        ``plot_area_ha`` is optional but should be supplied by anything issuing
        against a physical parcel. Without it the plausibility ceiling cannot be
        applied, and the claim is bounded only by being positive — which is the
        hole the adversarial suite found. With it, a claim above
        ``MAX_TONNES_PER_HECTARE`` for that area is refused.
        """
        if source not in ACCEPTABLE_SOURCES:
            raise EvidenceRejected(
                REJECTED,
                f"source={source!r} is not one of {sorted(ACCEPTABLE_SOURCES)}; "
                "a degraded or simulated observation is not a basis for payment",
            )
        if tonnes_co2e <= 0:
            raise ValueError("tonnes_co2e must be positive")
        if plot_area_ha is not None:
            if plot_area_ha <= 0:
                raise ValueError("plot_area_ha must be positive")
            ceiling = plot_area_ha * MAX_TONNES_PER_HECTARE
            if tonnes_co2e > ceiling:
                raise EvidenceRejected(
                    IMPLAUSIBLE,
                    f"{tonnes_co2e} tCO2e claimed from {plot_area_ha} ha exceeds the "
                    f"ceiling of {ceiling} tCO2e ({MAX_TONNES_PER_HECTARE} tCO2e/ha)",
                )

        # A retired observation is still a used observation. Checked before any
        # mutation so the refusal costs nothing.
        prior = await self.db.execute(
            select(EcoBalanceEntry).where(
                EcoBalanceEntry.user_id == user_id,
                EcoBalanceEntry.observation_id == observation_id,
            )
        )
        if prior.scalar_one_or_none() is not None:
            raise EvidenceRejected(
                REPLAYED,
                f"observation {observation_id!r} has already been credited to "
                f"{user_id}, and a credit is never un-credited",
            )

        amount = units_for(reason, tonnes_co2e)
        digest = evidence_digest(
            {**evidence, "tonnes_co2e": str(tonnes_co2e), "reason": reason.value}
        )

        account = await self.account_for(user_id)
        seq_result = await self.db.execute(
            select(func.coalesce(func.max(EcoBalanceEntry.sequence), 0) + 1).where(
                EcoBalanceEntry.user_id == user_id
            )
        )
        sequence = int(seq_result.scalar_one())

        account.balance = account.balance + amount
        account.lifetime_earned = account.lifetime_earned + amount
        account.observation_count = account.observation_count + 1

        self.db.add(
            EcoBalanceEntry(
                user_id=user_id,
                sequence=sequence,
                amount=amount,
                reason=reason.value if isinstance(reason, Reason) else str(reason),
                observation_id=observation_id,
                evidence_digest=digest,
            )
        )
        try:
            await self.db.commit()
        except IntegrityError:
            # The database refuses the replay; translate it so a caller sees a
            # named refusal rather than a driver error, and so no part of the
            # credit survives — the account mutation and the entry are in the
            # same transaction, so the rollback discards both.
            await self.db.rollback()
            raise EvidenceRejected(
                REPLAYED,
                f"observation {observation_id!r} has already been credited to {user_id}",
            ) from None
        return account.balance

    async def ledger(self, user_id: str) -> list[EcoBalanceEntry]:
        result = await self.db.execute(
            select(EcoBalanceEntry)
            .where(EcoBalanceEntry.user_id == user_id)
            .order_by(EcoBalanceEntry.sequence)
        )
        return list(result.scalars().all())

    async def retire(self, *, user_id: str, entry_id: int) -> None:
        """Void an entry — retraction, not a refund.

        Deleting the row would leave the balance and the ledger disagreeing with
        no record that it ever happened, which is the defect class this platform
        exists to avoid. Retired entries stay, marked, and the balance is
        corrected.
        """
        entry = await self.db.get(EcoBalanceEntry, entry_id)
        if entry is None or entry.user_id != user_id:
            raise LookupError(f"no entry {entry_id} for user {user_id}")
        account = await self.account_for(user_id)
        account.balance = account.balance - entry.amount
        if account.balance < 0:
            account.balance = Decimal("0")
        # Marked, never deleted. Deleting cleared the (user_id, observation_id)
        # unique constraint, so a retract-then-reclaim cycle replayed freely —
        # found by a red-team persona doing exactly that. A retraction that
        # erases its own record cannot be audited, which is the opposite of what
        # a retraction is for.
        entry.retired_at = datetime.now(UTC)
        await self.db.commit()
