"""Reward reasons, their weights, and the challenge lifecycle.

The design question behind this file: **what does the platform pay for?**

A flat rate pays for being observed, not for doing work, and every programme
that has tried one has ended up paying the easiest participants. So there are
three deliberate shapes here:

* **Evidence beats effort.** ``GROUND_TRUTH_SUBMITTED`` is weighted 4x because it
  is the only input the platform cannot obtain for itself.
* **Maintenance beats one-off installation.** ``REVERIFICATION_COMPLETED`` is
  weighted *above* the first observation. The costly thing in every monitoring
  programme is coming back a second year, and most fail by abandoning it.
* **Bad news pays too.** ``FLAG_CONFIRMED`` and ``CHANGE_DETECTED`` are paid on
  a challenge being upheld or a signal being confirmed. A system that only pays
  for improvement is a system whose participants learn not to report any.

The challenge is the third one, and it is the load-bearing mechanic: it makes
the *finding* the reward, not the conclusion.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from services.wallet.eco_balance import EcoBalanceService, Reason, units_for


class ChallengeStatus(StrEnum):
    OPEN = "open"
    """Awaiting the platform's determination."""

    CONFIRMED = "confirmed"
    """The challenger was right. Paid."""

    DISMISSED = "dismissed"
    """The challenge did not hold. Paid anyway — see the module docstring."""

    WITHDRAWN = "withdrawn"
    """The challenger withdrew. Paid at a reduced rate."""


class ChallengeKind(StrEnum):
    GROUND_TRUTH_DISPUTE = "ground_truth_dispute"
    DATA_QUALITY = "data_quality"
    PRACTICE_VERIFICATION = "practice_verification"
    BOUNDARY = "boundary"


#: Reduced fraction paid on withdrawal. Not zero: a challenger who withdraws
#: honestly still spent effort, and a hard zero teaches people to file challenges
#: they do not believe in, which destroys the signal the challenge exists for.
WITHDRAWAL_PAYOUT = Decimal("0.25")


@dataclass(frozen=True)
class Determination:
    """What the platform concluded, and what it is worth."""

    status: ChallengeStatus
    reason: Reason
    tonnes_co2e: Decimal
    note: str = ""


#: The platform must always pay a determined challenge, including a dismissal.
#: Expressed as a mapping rather than a comment so a future change to it breaks
#: a test.
PAYOUT: dict[ChallengeStatus, bool] = {
    ChallengeStatus.CONFIRMED: True,
    ChallengeStatus.DISMISSED: True,
    ChallengeStatus.WITHDRAWN: True,
    ChallengeStatus.OPEN: False,
}


class ChallengeService:
    """Challenges pay for the finding, not for winning."""

    def __init__(self, db: AsyncSession, balances: EcoBalanceService) -> None:
        self.db = db
        self.balances = balances

    async def determine(
        self,
        *,
        challenger_id: str,
        kind: ChallengeKind,
        observation_id: str,
        evidence: dict,
        outcome: Determination,
    ) -> tuple[Decimal, bool]:
        """Record a determination and pay for it.

        Returns (units, paid).

        ``outcome.tonnes_co2e`` is how much the finding is *worth*, not how much
        carbon was measured — for a quality challenge there is no tonnage at all,
        and forcing one would be the same mistake as keying a reward to a price.
        A determination that is dismissed still pays, because the platform spent
        a reviewer on it and the challenger's signal was still real.
        """
        if outcome.status is ChallengeStatus.OPEN:
            return Decimal("0"), False

        should_pay = PAYOUT[outcome.status]
        if not should_pay:  # pragma: no cover - guarded by the map above
            return Decimal("0"), False

        tonnes = outcome.tonnes_co2e
        if outcome.status is ChallengeStatus.WITHDRAWN:
            tonnes = tonnes * WITHDRAWAL_PAYOUT

        units = units_for(outcome.reason, tonnes)
        await self.balances.credit(
            user_id=challenger_id,
            tonnes_co2e=tonnes,
            source="measured",
            observation_id=observation_id,
            reason=outcome.reason,
            evidence={**evidence, "challenge_kind": kind.value, "status": outcome.status.value},
        )
        return units, True

    @staticmethod
    def note_for(status: ChallengeStatus) -> str:
        """Human-readable reason a determination paid, for the audit trail."""
        if status is ChallengeStatus.DISMISSED:
            return "challenge did not hold; paid because the finding was real"
        if status is ChallengeStatus.WITHDRAWN:
            return f"withdrawn; paid at {WITHDRAWAL_PAYOUT} of the assessed value"
        if status is ChallengeStatus.CONFIRMED:
            return "challenge upheld"
        return "open; nothing paid until determined"
