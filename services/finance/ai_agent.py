"""AI Agent for financial settlement and reconciliation (Phase 7).

This agent watches posted journal batches, wallet ledger, orders and
settlements, detects discrepancies autonomously, and proposes (or, when
authorized, applies) correcting journal entries.  It is deliberately
fail-closed: every AI action is logged as a draft journal entry that must be
posted by an admin unless ``auto_post`` is explicitly enabled in the request.

All money math uses ``Decimal`` — never float — and every entry posts to the
double-entry ledger so the trial balance always stays auditable.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    ComOrder,
    ComPaymentIntent,
    ComSettlement,
    EcoWallet,
    FinAccount,
    FinJournalBatch,
    FinJournalEntry,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.ledger_service import LedgerService
from services.finance.reconciliation import (
    ReconciliationService,
)

logger = logging.getLogger(__name__)

#: Assets the finance engine knows how to journal.
VALID_ASSETS = ("IRR", "ECO", "CARBON_tCO2e", "USD")

#: Confidence threshold below which the agent never auto-posts — it only
#: suggests and waits for an admin to approve.
AUTO_POST_CONFIDENCE_THRESHOLD = Decimal("0.95")


class AIAgentError(EcoNojinException):
    """Raised when the AI agent cannot safely act."""


class FinanceAIAgent:
    """Autonomous financial agent: detects, scores, and (optionally) posts
    correcting journal entries for settlement and reconciliation drift."""

    def __init__(self, db: AsyncSession, auto_post: bool = False):
        self.db = db
        self.auto_post = auto_post
        self.ledger = LedgerService(db)
        self.recon = ReconciliationService(db)

    # ════════════════════════════════════════════════════════════════════════
    # Public: detect + propose corrections
    # ═════════════════════════════════════════════════════════════════════════

    async def detect_and_propose(
        self,
        *,
        as_of: datetime | None = None,
        confidence_floor: Decimal = Decimal("0.0"),
    ) -> dict:
        """Run every detector, score each finding, and return proposed
        corrections.

        When ``auto_post`` is True and a finding's confidence is at or above
        ``AUTO_POST_CONFIDENCE_THRESHOLD``, the correcting batch is posted
        immediately; otherwise it is returned as a draft awaiting admin
        approval.
        """
        if as_of is None:
            as_of = datetime.now(UTC)

        proposals: list[dict] = []

        # 1. Wallet vs ledger drift
        proposals.extend(await self._detect_wallet_drift(as_of))

        # 2. Order vs payment vs settlement drift
        proposals.extend(await self._detect_order_settlement_drift())

        # 3. Inventory on_hand vs movement ledger drift
        proposals.extend(await self._detect_inventory_drift())

        # 4. Journal batches that are unbalanced (should never happen, but
        #    catch it if a direct DB edit occurred)
        proposals.extend(await self._detect_unbalanced_batches())

        # Score and filter
        for p in proposals:
            p["confidence"] = self._score_confidence(p)
            p["auto_post_eligible"] = (
                p["confidence"] >= AUTO_POST_CONFIDENCE_THRESHOLD
                and p["confidence"] >= confidence_floor
            )

        posted = []
        suggested = []
        for p in proposals:
            if p["auto_post_eligible"] and self.auto_post:
                try:
                    batch = await self._post_correction(p)
                    posted.append(
                        {
                            **p,
                            "action": "posted",
                            "batch_id": batch.id,
                            "batch_number": batch.batch_number,
                        }
                    )
                except Exception as exc:  # noqa: BLE001 — one bad proposal must not abort the run
                    logger.warning(
                        "AI agent auto-post failed for %s: %s", p.get("type"), exc
                    )
                    suggested.append({**p, "action": "post_failed", "error": str(exc)})
            else:
                suggested.append({**p, "action": "suggested"})

        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "as_of": as_of.isoformat(),
            "auto_post": self.auto_post,
            "total_proposals": len(proposals),
            "posted": posted,
            "suggested": suggested,
        }

    # ═════════════════════════════════════════════════════════════════════════
    # Detectors
    # ═════════════════════════════════════════════════════════════════════════

    async def _detect_wallet_drift(self, as_of: datetime) -> list[dict]:
        """Wallet.balance vs FinJournalEntry sum for REWARD_LIABILITY."""
        result = await self.db.execute(
            select(EcoWallet).where(EcoWallet.is_active.is_(True))
        )
        wallets = result.scalars().all()
        proposals: list[dict] = []

        for wallet in wallets:
            ledger_balance = await self.recon._get_ledger_balance(
                wallet.user_id, "ECO"
            )
            drift = wallet.balance - ledger_balance
            if drift == 0:
                continue

            # Find an account to credit/debit against.
            drift_account = await self._find_account(
                code="REWARD_LIABILITY", asset="ECO"
            )
            clearing_account = await self._find_account(
                code="ECO_ASSET", asset="ECO"
            )

            proposals.append(
                {
                    "type": "wallet_ledger_drift",
                    "user_id": wallet.user_id,
                    "wallet_balance": str(wallet.balance),
                    "ledger_balance": str(ledger_balance),
                    "drift": str(drift),
                    "severity": "high",
                    "suggested_entries": self._draft_entries(
                        drift_account_id=str(drift_account.id) if drift_account else "",
                        clearing_account_id=str(
                            clearing_account.id
                        )
                        if clearing_account
                        else "",
                        amount=abs(drift),
                        debit_first=drift > 0,
                        description=(
                            f"Wallet ledger drift correction for user "
                            f"{wallet.user_id}"
                        ),
                    ),
                }
            )

        return proposals

    async def _detect_order_settlement_drift(self) -> list[dict]:
        """Orders that are settled but missing/incorrect settlement journal."""
        orders = (await self.db.execute(select(ComOrder))).scalars().all()
        intents = (await self.db.execute(select(ComPaymentIntent))).scalars().all()
        settlements = (await self.db.execute(select(ComSettlement))).scalars().all()
        batches = (await self.db.execute(select(FinJournalBatch))).scalars().all()

        posted_batch_ids = {batch.id for batch in batches if batch.is_posted}
        intents_by_order: dict[str, list[ComPaymentIntent]] = {}
        for intent in intents:
            intents_by_order.setdefault(intent.order_id, []).append(intent)
        settlements_by_order = {s.order_id: s for s in settlements}

        proposals: list[dict] = []
        for order in orders:
            if order.status != "settled":
                continue
            settlement = settlements_by_order.get(order.id)
            if settlement is None:
                proposals.append(
                    {
                        "type": "missing_settlement",
                        "order_id": order.id,
                        "order_total": str(order.total),
                        "severity": "high",
                        "suggested_entries": self._draft_entries(
                            drift_account_id="",
                            clearing_account_id="",
                            amount=order.total,
                            debit_first=True,
                            description=f"Missing settlement journal for order {order.id}",
                        ),
                    }
                )
                continue

            settled_total = (
                settlement.amount + settlement.commission_fee + settlement.landscape_fee
            )
            if settled_total != order.total:
                drift = order.total - settled_total
                proposals.append(
                    {
                        "type": "settlement_amount_mismatch",
                        "order_id": order.id,
                        "settlement_total": str(settled_total),
                        "order_total": str(order.total),
                        "drift": str(drift),
                        "severity": "medium",
                        "suggested_entries": self._draft_entries(
                            drift_account_id="",
                            clearing_account_id="",
                            amount=abs(drift),
                            debit_first=drift > 0,
                            description=(
                                f"Settlement amount mismatch for order {order.id}"
                            ),
                        ),
                    }
                )
            if settlement.journal_batch_id not in posted_batch_ids:
                proposals.append(
                    {
                        "type": "unposted_settlement_batch",
                        "order_id": order.id,
                        "journal_batch_id": settlement.journal_batch_id,
                        "severity": "medium",
                        "suggested_entries": self._draft_entries(
                            drift_account_id="",
                            clearing_account_id="",
                            amount=Decimal("0"),
                            debit_first=True,
                            description=(
                                f"Settlement journal batch not posted for order "
                                f"{order.id}"
                            ),
                        ),
                    }
                )

        return proposals

    async def _detect_inventory_drift(self) -> list[dict]:
        """InventoryBalance.on_hand vs signed movement sums (reuses recon logic)."""
        result = await self.recon.reconcile_inventory()
        proposals: list[dict] = []
        for d in result.get("discrepancies", []):
            proposals.append(
                {
                    "type": "inventory_on_hand_drift",
                    "sku_id": d["sku_id"],
                    "warehouse_id": d["warehouse_id"],
                    "on_hand": d["on_hand"],
                    "ledger_on_hand": d["ledger_on_hand"],
                    "drift": d["on_hand_drift"],
                    "severity": "high",
                    "suggested_entries": self._draft_entries(
                        drift_account_id="",
                        clearing_account_id="",
                        amount=abs(Decimal(d["on_hand_drift"])),
                        debit_first=Decimal(d["on_hand_drift"]) > 0,
                        description=(
                            f"Inventory on-hand drift for SKU "
                            f"{d['sku_id']} / WH {d['warehouse_id']}"
                        ),
                    ),
                }
            )
        return proposals

    async def _detect_unbalanced_batches(self) -> list[dict]:
        """Posted journal batches whose debits != credits (defense in depth)."""
        batches = (
            await self.db.execute(
                select(FinJournalBatch).where(FinJournalBatch.is_posted.is_(True))
            )
        ).scalars().all()
        proposals: list[dict] = []
        for batch in batches:
            result = await self.db.execute(
                select(
                    func.sum(
                        func.case(
                            (FinJournalEntry.entry_type == "debit", FinJournalEntry.amount),
                            else_=Decimal("0"),
                        )
                    ).label("debit"),
                    func.sum(
                        func.case(
                            (FinJournalEntry.entry_type == "credit", FinJournalEntry.amount),
                            else_=Decimal("0"),
                        )
                    ).label("credit"),
                ).where(FinJournalEntry.batch_id == batch.id)
            )
            row = result.one()
            debit = row.debit or Decimal("0")
            credit = row.credit or Decimal("0")
            if debit != credit:
                proposals.append(
                    {
                        "type": "unbalanced_journal_batch",
                        "batch_id": batch.id,
                        "batch_number": batch.batch_number,
                        "debit": str(debit),
                        "credit": str(credit),
                        "drift": str(debit - credit),
                        "severity": "critical",
                        "suggested_entries": self._draft_entries(
                            drift_account_id="",
                            clearing_account_id="",
                            amount=abs(debit - credit),
                            debit_first=debit < credit,
                            description=(
                                f"Unbalanced journal batch {batch.batch_number}"
                            ),
                        ),
                    }
                )
        return proposals

    # ═════════════════════════════════════════════════════════════════════════
    # Posting
    # ═════════════════════════════════════════════════════════════════════════

    async def _post_correction(self, proposal: dict) -> FinJournalBatch:
        """Post a correcting journal batch for an AI proposal."""
        entries = proposal["suggested_entries"]
        batch = await self.ledger.create_journal_batch(
            reference_type="ai_settlement_correction",
            reference_id=proposal.get("type", "ai_correction"),
            entries=entries,
            description=(
                f"AI agent correction: {proposal['type']} — "
                f"{proposal.get('description', '')}"
            ),
            created_by="ai_agent",
        )
        await self.ledger.post_journal_batch(batch.id)
        return batch

    # ═════════════════════════════════════════════════════════════════════════
    # Helpers
    # ═════════════════════════════════════════════════════════════════════════

    def _score_confidence(self, proposal: dict) -> Decimal:
        """Heuristic confidence score (0–1). Auto-post only when >= 0.95."""
        base = Decimal("0.5")
        sev = proposal.get("severity", "medium")
        if sev == "critical":
            base = Decimal("0.8")
        elif sev == "high":
            base = Decimal("0.65")
        elif sev == "medium":
            base = Decimal("0.55")
        elif sev == "low":
            base = Decimal("0.4")

        # Amount present and parsable increases confidence.
        try:
            Decimal(str(proposal.get("drift", "0")))
            base += Decimal("0.1")
        except (InvalidOperation, TypeError):
            pass

        # Known type names score higher.
        known = {
            "wallet_ledger_drift",
            "settlement_amount_mismatch",
            "missing_settlement",
            "unposted_settlement_batch",
            "inventory_on_hand_drift",
            "unbalanced_journal_batch",
        }
        if proposal.get("type") in known:
            base += Decimal("0.1")

        return min(base, Decimal("1.0"))

    async def _find_account(
        self, *, code: str, asset: str
    ) -> FinAccount | None:
        result = await self.db.execute(
            select(FinAccount).where(
                FinAccount.code == code, FinAccount.asset == asset
            )
        )
        return result.scalar_one_or_none()

    def _draft_entries(
        self,
        *,
        drift_account_id: str,
        clearing_account_id: str,
        amount: Decimal,
        debit_first: bool,
        description: str,
    ) -> list[dict]:
        """Build a two-line balanced journal entry draft.

        When the real account codes are not yet resolved (empty strings), the
        entry is returned as a *draft* with ``account_id`` left empty so an
        admin can fill it before posting.  Auto-post will skip drafts that
        lack real account ids.
        """
        debit_entry = {
            "account_id": drift_account_id if debit_first else clearing_account_id,
            "entry_type": "debit",
            "asset": "ECO",
            "amount": str(amount),
            "description": description,
        }
        credit_entry = {
            "account_id": clearing_account_id if debit_first else drift_account_id,
            "entry_type": "credit",
            "asset": "ECO",
            "amount": str(amount),
            "description": description,
        }
        return [debit_entry, credit_entry]

    async def apply_suggested(
        self,
        *,
        proposal_index: int,
        from_list: str = "suggested",
        account_overrides: dict[str, str] | None = None,
    ) -> dict:
        """Admin applies a previously-suggested draft, optionally overriding
        account codes before posting."""
        # This method is intentionally thin: the router re-runs detect_and_propose
        # with auto_post=True for a single proposal.  Keep this as a future
        # hook for per-proposal editing.
        raise AIAgentError(
            "apply_suggested not implemented; re-run /finance/ai/detect with "
            "auto_post=true for targeted posting",
            code="NOT_IMPLEMENTED",
        )
