"""Property-based tests for the money/accounting invariants of the ledger.

Every test here is a Hypothesis property test, and every one of them is
deterministic: the profile pins ``deadline=None``, a small ``max_examples``
budget, ``database=None`` (no example database is written) and
``derandomize=True`` (the same examples on every run), and each example
starts from a database the test wipes itself. There is no wall-clock
dependency in any assertion and no key is shared between examples, so
running a file twice produces the same result.

What is pinned, by invariant:

1. **Double-entry balance** — a batch whose debits equal its credits *per
   asset* is accepted, and ``trial_balance`` reports the same balance per
   asset; one that does not is refused with ``UNBALANCED_JOURNAL`` and
   nothing is persisted. ``LedgerService.get_account_balance``'s documented
   sign convention (credit positive, debit negative) makes the signed
   balances of every account sum to zero.
2. **Fee conservation and the take-rate band** —
   ``revenue_indicators``' pure arithmetic: the realised take rate stays
   inside the band its own schedule measures, ``rounding_drift`` is exactly
   ``nominal - realised``, and a discount never conjures or destroys money.
3. **Idempotency** — replaying the same payment intent against
   ``FinIdempotencyKey`` credits once, a key reused with a different payload
   is refused, and two users never share a key. Re-posting a batch is
   refused rather than applied twice.
4. **Reconciliation** — a randomly seeded but internally consistent state
   reconciles clean; a single injected discrepancy is always caught.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select, text

from database.models import (
    ComOrder,
    ComPaymentIntent,
    ComSettlement,
    EcoWallet,
    FinIdempotencyKey,
    FinJournalBatch,
    FinJournalEntry,
    InvInventoryBalance,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.chart_of_accounts import REWARD_LIABILITY, ensure_account
from services.finance.ledger_service import LedgerService
from services.finance.reconciliation import ReconciliationService
from services.finance.revenue_indicators import (
    DISCOUNTED_FEE_LINE,
    MAX_DISCOUNT_BPS,
    commerce_schedule,
    discounted_fees,
    projected_revenue,
    realised_bps,
)

# ---------------------------------------------------------------------------
# Deterministic Hypothesis profile.
#
# ``budget`` is kept small on purpose: this file is a fast suite, not a deep
# exploration. ``database=None`` keeps the example DB out of the repository so
# a run cannot be influenced by a leftover database, and ``derandomize``
# fixes the seed so the same examples are drawn on every run.
# ---------------------------------------------------------------------------

_HEALTH = [HealthCheck.function_scoped_fixture, HealthCheck.too_slow]

PROPERTY = settings(
    max_examples=20,
    deadline=None,
    database=None,
    derandomize=True,
    suppress_health_check=_HEALTH,
)

#: Only the tables this file writes, children before parents, so one DELETE
#: pass fully isolates one example from the next.
_OWNED_TABLES = (
    "com_order_items",
    "com_payment_intents",
    "com_settlements",
    "com_orders",
    "fin_journal_entries",
    "fin_journal_batches",
    "fin_idempotency_keys",
    "daily_earnings",
    "eco_wallets",
    "fin_accounts",
    "inv_reservations",
    "inv_stock_movements",
    "inv_inventory_balances",
    "inv_lots",
    "inv_warehouses",
    "inv_skus",
    "audit_events",
)

ASSETS = ("IRR", "ECO", "CARBON_tCO2e", "USD")

#: The discrepancies the orders/payments reconciliation is required to catch.
#: One is injected at a time, into an otherwise clean state.
INJECTIONS = (
    "wallet_drift",
    "payment_amount_mismatch",
    "orphaned_intent",
    "unconfirmed_intent",
    "missing_settlement",
    "settlement_amount_mismatch",
    "unposted_batch",
)

#: The take-rate ceiling ``revenue_indicators``' module docstring publishes.
#: It used to publish a single figure -- 588 bps -- that no schedule
#: respects: the commerce schedule (400 bps nominal) measures 0-600 bps and
#: the tourism schedule (1200 bps nominal, three lines) measures 0-1600 bps.
#: The documentation was corrected to the measured, per-schedule bands
#: (commerce 0-600, peaking on a 0.50 subtotal), and
#: ``tests/test_take_rate_band_correction.py`` re-derives both bands from
#: ``realised_bps`` on every run so the prose cannot drift from the
#: arithmetic again. This is the commerce figure the corrected docstring
#: states, and it is held to the sweep in
#: ``test_the_measured_ceiling_matches_the_documented_one``.
DOCUMENTED_BPS_CEILING = 600

#: The ceiling the code actually respects, measured over every cent from 0.01
#: to 100.00 (and confirmed to 2000.00). It is the nominal 400 bps of the
#: commerce schedule plus at most one cent of rounding per schedule line on a
#: one-cent order, so it is tight rather than arbitrary.
MEASURED_BPS_CEILING = 600


def _unique(prefix: str) -> str:
    """A per-example identifier, so no two examples can collide on a key."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _without_checked_at(check: dict) -> dict:
    """A reconciliation payload without its ``checked_at`` wall-clock stamp."""
    return {key: value for key, value in check.items() if key != "checked_at"}


def _cents(low: int, high: int) -> st.SearchStrategy[Decimal]:
    """A cent-granular positive Decimal, the granularity real money has."""
    return st.integers(min_value=low, max_value=high).map(lambda c: Decimal(c) / 100)


async def _wipe(db_session) -> None:
    """Empty every table this file touches, so an example starts clean.

    The ``db_session`` fixture is function-scoped, so Hypothesis hands the
    same session to every example of one test; without this the second
    example would observe the first one's rows and the properties would be
    about an ever-growing ledger instead of about one batch.
    """
    await db_session.rollback()
    for table in _OWNED_TABLES:
        await db_session.execute(text(f"DELETE FROM {table}"))
    await db_session.commit()
    db_session.expunge_all()


# ---------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------


def _split(total_cents: int, parts: int, draw) -> list[int]:
    """``parts`` positive cent amounts summing exactly to ``total_cents``."""
    if parts <= 1:
        return [total_cents]
    cuts = sorted(
        draw(
            st.lists(
                st.integers(min_value=1, max_value=total_cents - 1),
                min_size=parts - 1,
                max_size=parts - 1,
                unique=True,
            )
        )
        if total_cents > parts
        else []
    )
    bounds = [0, *cuts, total_cents]
    pieces = [bounds[i + 1] - bounds[i] for i in range(len(bounds) - 1)]
    return [piece for piece in pieces if piece > 0]


@st.composite
def balanced_batch(draw):
    """A balanced batch: per asset the debits equal the credits.

    Returns ``(entries, expected)`` where ``expected`` maps each asset to the
    debit and credit cent total that asset's legs add up to.
    """
    assets = draw(
        st.lists(st.sampled_from(ASSETS), min_size=1, max_size=3, unique=True)
    )
    entries: list[dict] = []
    expected: dict[str, dict[str, Decimal]] = {}
    for index, asset in enumerate(assets):
        amount = draw(st.integers(min_value=20, max_value=100_000))
        debit_parts = _split(amount, draw(st.integers(2, 4)), draw)
        credit_parts = _split(amount, draw(st.integers(2, 4)), draw)
        for side, parts in (("debit", debit_parts), ("credit", credit_parts)):
            for position, part in enumerate(parts):
                entries.append(
                    {
                        "account_id": f"P-{index}-{side}-{position}",
                        "entry_type": side,
                        "asset": asset,
                        "amount": str(Decimal(part) / 100),
                        "description": f"{side} leg {position} of {asset}",
                    }
                )
        expected[asset] = {
            "debit": Decimal(amount) / 100,
            "credit": Decimal(amount) / 100,
        }
    return entries, expected


# ---------------------------------------------------------------------------
# 1. double-entry balance
# ---------------------------------------------------------------------------


class TestDoubleEntryBalance:
    """A balanced batch is accepted and balances; an unbalanced one is not."""

    @given(plan=balanced_batch())
    @PROPERTY
    async def test_balanced_batch_is_accepted_and_balances_per_asset(
        self, db_session, plan
    ):
        entries, expected = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        batch = await ledger.create_journal_batch(
            reference_type="property",
            reference_id=_unique("ref"),
            entries=entries,
            description="property batch",
            created_by="property-test",
        )

        # A draft is invisible to the reports: only posted batches aggregate.
        empty = await ledger.trial_balance()
        assert empty["rows"] == []

        await ledger.post_journal_batch(batch.id)

        report = await ledger.trial_balance()
        by_asset = {row["asset"]: row for row in report["totals"]}
        assert set(by_asset) == set(expected)

        for asset, totals in expected.items():
            row = by_asset[asset]
            assert row["balanced"] is True, f"{asset}: {row}"
            assert Decimal(row["debit"]) == totals["debit"]
            assert Decimal(row["credit"]) == totals["credit"]
            assert Decimal(row["debit"]) == Decimal(row["credit"])

        persisted = len(
            (
                await db_session.execute(
                    select(FinJournalEntry).where(FinJournalEntry.batch_id == batch.id)
                )
            )
            .scalars()
            .all()
        )
        assert persisted == len(entries)

    @given(plan=balanced_batch(), cent=st.integers(min_value=1, max_value=500))
    @PROPERTY
    async def test_unbalanced_batch_is_rejected_and_persists_nothing(
        self, db_session, plan, cent
    ):
        entries, _ = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        first = entries[0]
        entries[0] = {
            **first,
            "amount": str(Decimal(first["amount"]) + Decimal(cent) / 100),
        }

        with pytest.raises(EcoNojinException) as raised:
            await ledger.create_journal_batch(
                reference_type="property",
                reference_id=_unique("ref"),
                entries=entries,
                description="unbalanced property batch",
                created_by="property-test",
            )

        assert raised.value.code == "UNBALANCED_JOURNAL"

        # Nothing was persisted — neither the batch nor one of its legs.
        batches = (await db_session.execute(select(FinJournalBatch))).scalars().all()
        rows = (await db_session.execute(select(FinJournalEntry))).scalars().all()
        assert batches == []
        assert rows == []

    @given(plan=balanced_batch(), credit=st.integers(min_value=1, max_value=9))
    @PROPERTY
    async def test_shortening_one_credit_leg_is_detected(
        self, db_session, plan, credit
    ):
        entries, _ = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        index = next(
            i for i, entry in enumerate(entries) if entry["entry_type"] == "credit"
        )
        leg = entries[index]
        entries[index] = {
            **leg,
            "amount": str(Decimal(leg["amount"]) - Decimal(credit) / 100),
        }

        with pytest.raises(EcoNojinException) as raised:
            await ledger.create_journal_batch(
                reference_type="property",
                reference_id=_unique("ref"),
                entries=entries,
            )

        assert raised.value.code in {"UNBALANCED_JOURNAL", "INVALID_AMOUNT"}

    @given(plan=balanced_batch())
    @PROPERTY
    async def test_signed_account_balances_sum_to_zero(self, db_session, plan):
        """The documented sign convention: credit positive, debit negative."""
        entries, _ = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        batch = await ledger.create_journal_batch(
            reference_type="property", reference_id=_unique("ref"), entries=entries
        )
        await ledger.post_journal_batch(batch.id)

        accounts = {
            row[0]
            for row in (
                await db_session.execute(select(FinJournalEntry.account_id).distinct())
            ).all()
        }
        total = Decimal("0")
        for account_id in accounts:
            entry = next(e for e in entries if e["account_id"] == account_id)
            total += await ledger.get_account_balance(account_id, entry["asset"])
        assert total == 0

    @given(plan=balanced_batch())
    @PROPERTY
    async def test_trial_balance_columns_are_mutually_exclusive(self, db_session, plan):
        entries, _ = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        batch = await ledger.create_journal_batch(
            reference_type="property", reference_id=_unique("ref"), entries=entries
        )
        await ledger.post_journal_batch(batch.id)

        report = await ledger.trial_balance()
        # One row per (account, asset) pair, and a row can never be both a
        # debit balance and a credit balance at once.
        keys = [(row["account_id"], row["asset"]) for row in report["rows"]]
        assert len(keys) == len(set(keys))
        for row in report["rows"]:
            debit_balance = Decimal(row["debit_balance"])
            credit_balance = Decimal(row["credit_balance"])
            assert debit_balance >= 0 and credit_balance >= 0
            assert debit_balance == 0 or credit_balance == 0
            assert Decimal(row["total_debits"]) >= 0
            assert Decimal(row["total_credits"]) >= 0

    @given(
        bad_amount=st.sampled_from(
            ["0", "-1", "-0.01", "0.00", "-100", "-0.00000001"]
        )
    )
    @PROPERTY
    async def test_non_positive_amount_is_refused(self, db_session, bad_amount):
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        with pytest.raises(EcoNojinException) as raised:
            await ledger.create_journal_batch(
                reference_type="property",
                reference_id=_unique("ref"),
                entries=[
                    {
                        "account_id": "P-DEBIT",
                        "entry_type": "debit",
                        "asset": "IRR",
                        "amount": bad_amount,
                    },
                    {
                        "account_id": "P-CREDIT",
                        "entry_type": "credit",
                        "asset": "IRR",
                        "amount": bad_amount,
                    },
                ],
            )

        assert raised.value.code == "INVALID_AMOUNT"
        assert (await db_session.execute(select(FinJournalBatch))).scalars().all() == []

    @given(bad_asset=st.text(min_size=1, max_size=12).filter(lambda s: s not in ASSETS))
    @PROPERTY
    async def test_asset_outside_the_allowlist_is_refused(self, db_session, bad_asset):
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        with pytest.raises(EcoNojinException) as raised:
            await ledger.create_journal_batch(
                reference_type="property",
                reference_id=_unique("ref"),
                entries=[
                    {
                        "account_id": "P-DEBIT",
                        "entry_type": "debit",
                        "asset": bad_asset,
                        "amount": "5",
                    },
                    {
                        "account_id": "P-CREDIT",
                        "entry_type": "credit",
                        "asset": bad_asset,
                        "amount": "5",
                    },
                ],
            )

        assert raised.value.code == "INVALID_ASSET"

    @given(bad_type=st.text(min_size=1, max_size=12).filter(lambda s: s not in ("debit", "credit")))
    @PROPERTY
    async def test_unknown_entry_type_is_refused(self, db_session, bad_type):
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        with pytest.raises(EcoNojinException) as raised:
            await ledger.create_journal_batch(
                reference_type="property",
                reference_id=_unique("ref"),
                entries=[
                    {
                        "account_id": "P-DEBIT",
                        "entry_type": bad_type,
                        "asset": "IRR",
                        "amount": "5",
                    },
                    {
                        "account_id": "P-CREDIT",
                        "entry_type": "credit",
                        "asset": "IRR",
                        "amount": "5",
                    },
                ],
            )

        assert raised.value.code == "INVALID_ENTRY_TYPE"

    async def test_empty_batch_is_refused(self, db_session):
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        with pytest.raises(EcoNojinException) as raised:
            await ledger.create_journal_batch(
                reference_type="property", reference_id=_unique("ref"), entries=[]
            )

        assert raised.value.code == "EMPTY_JOURNAL"

    @given(plan=balanced_batch())
    @PROPERTY
    async def test_batch_is_balanced_whichever_way_the_legs_are_ordered(
        self, db_session, plan
    ):
        """Ordering is presentation, not accounting: the totals cannot move."""
        entries, expected = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        batch = await ledger.create_journal_batch(
            reference_type="property",
            reference_id=_unique("ref"),
            entries=list(reversed(entries)),
        )
        await ledger.post_journal_batch(batch.id)

        report = await ledger.trial_balance()
        by_asset = {row["asset"]: row for row in report["totals"]}
        for asset, totals in expected.items():
            assert Decimal(by_asset[asset]["debit"]) == totals["debit"]
            assert Decimal(by_asset[asset]["credit"]) == totals["credit"]

    @given(plan=balanced_batch())
    @PROPERTY
    async def test_posting_twice_is_refused_and_changes_nothing(self, db_session, plan):
        entries, _ = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        batch = await ledger.create_journal_batch(
            reference_type="property", reference_id=_unique("ref"), entries=entries
        )
        await ledger.post_journal_batch(batch.id)

        with pytest.raises(EcoNojinException) as raised:
            await ledger.post_journal_batch(batch.id)

        assert raised.value.code == "ALREADY_POSTED"

        refreshed = (
            await db_session.execute(
                select(FinJournalBatch).where(FinJournalBatch.id == batch.id)
            )
        ).scalar_one()
        assert refreshed.is_posted is True
        # A replay wrote no second copy of anything.
        rows = (
            (
                await db_session.execute(
                    select(FinJournalEntry).where(FinJournalEntry.batch_id == batch.id)
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == len(entries)


# ---------------------------------------------------------------------------
# 2. fee conservation and the take-rate band (revenue_indicators, pure)
# ---------------------------------------------------------------------------


class TestTakeRateAndFeeConservation:
    """The revenue arithmetic: what is collected, and what it costs the buyer.

    These are pure functions of ``revenue_indicators`` -- no database, no
    clock -- so the properties run synchronously and need no fixture.
    """

    @staticmethod
    def _line_names(schedule: dict[str, Decimal]) -> tuple[str, ...]:
        """The schedule's fee lines, in the order the module reports them."""
        return tuple(name for name in schedule if name != "commission_bps")

    @given(subtotal=_cents(1, 200_000))
    @PROPERTY
    def test_fee_lines_conserve_the_schedule(self, subtotal):
        schedule = commerce_schedule()

        projection = projected_revenue(subtotal, schedule)

        # Every figure a caller can quote is a Decimal, and the realised
        # commission is built from the schedule's own cent-quantised lines.
        assert isinstance(projection["gross"], Decimal)
        assert isinstance(projection["realised_commission"], Decimal)
        assert isinstance(projection["rounding_drift"], Decimal)
        assert projection["nominal_bps"] == schedule["commission_bps"]
        # The seller is paid the subtotal: fees are added on top, not deducted.
        assert projection["gross"] == subtotal

    @given(subtotal=_cents(1, 200_000))
    @PROPERTY
    def test_rounding_drift_is_exactly_nominal_minus_realised(self, subtotal):
        schedule = commerce_schedule()
        projection = projected_revenue(subtotal, schedule)

        assert projection["rounding_drift"] == (
            projection["nominal_commission"] - projection["realised_commission"]
        )
        # The drift is rounding, not a fee change: it is bounded by one cent
        # per schedule line.
        lines = len(self._line_names(schedule))
        assert abs(projection["rounding_drift"]) <= lines * Decimal("0.01")
        # And the realised commission is itself within one cent per line of
        # the nominal one, so the two can never be quoted interchangeably.
        assert abs(projection["realised_commission"] - projection["nominal_commission"]) <= (
            lines * Decimal("0.01")
        )

    @given(subtotal=_cents(1, 200_000))
    @PROPERTY
    def test_realised_take_rate_stays_inside_the_documented_band(self, subtotal):
        """The band ``revenue_indicators``' module docstring publishes.

        The docstring used to state a single "ranges from 0 to 588 bps"
        figure that no schedule respects. The corrected documentation states
        the measured, per-schedule bands instead -- commerce 0-600 bps and
        tourism 0-1600 bps -- and the commerce band's 600 is the nominal 400
        bps plus at most one cent of rounding per schedule line on a
        one-cent order (at a 0.50 subtotal, 0.015 platform + 0.005
        landscape, both rounded half up, collects 0.03 on 0.50 = 600 bps).
        ``tests/test_take_rate_band_correction.py`` re-derives both bands
        from ``realised_bps`` itself; this test pins the commerce ceiling
        against the ceiling the docstring publishes, so a regression in
        either direction is visible. The measured ceiling is tight rather
        than arbitrary: a documentation figure that disagrees with it is a
        documentation defect, and the arithmetic is what the services
        charge.
        """
        schedule = commerce_schedule()
        nominal = int(schedule["commission_bps"])

        realised = realised_bps(subtotal, schedule)

        assert realised >= 0
        assert realised <= MEASURED_BPS_CEILING, f"{subtotal} realised {realised} bps"

        # The band is the nominal rate plus the most the cent-quantisation of
        # every line can add: one cent per line, on this subtotal. That is
        # the structural reason the ceiling is finite and small, and it holds
        # for any subtotal, not just the ones drawn here.
        lines = len(self._line_names(schedule))
        drift_ceiling = lines * Decimal("0.01") / subtotal * Decimal("10000")
        assert realised <= nominal + int(drift_ceiling) + 1, (
            f"{subtotal} realised {realised} bps against structural ceiling "
            f"{nominal + int(drift_ceiling) + 1}"
        )

    def test_the_measured_ceiling_and_the_published_one_agree(self):
        """``DOCUMENTED_BPS_CEILING`` is a claim about the code; it is true.

        This is the exhaustive version of the band property: every cent from
        0.01 to 100.00 is evaluated, the true extremes are found, and they are
        pinned. It is here rather than in a comment because a docstring that
        overstates a bound is the kind of thing a later reader would trust.

        The module docstring used to publish a single 588 bps figure that the
        sweep contradicts at its peak; the corrected documentation states the
        measured, per-schedule bands (commerce 0-600, tourism 0-1600), so the
        figure this file constrains is the one the sweep derives rather than a
        prose number nobody re-measures.
        ``tests/test_take_rate_band_correction.py`` holds the docstring's own
        wording to the same sweep.
        """
        schedule = commerce_schedule()
        extremes = []
        for cent in range(1, 10_001):
            subtotal = Decimal(cent) / 100
            extremes.append(int(realised_bps(subtotal, schedule)))

        assert min(extremes) == 0
        # The measured ceiling is re-derived here, not read from the constant,
        # so a schedule or rounding change moves it and fails the assertion
        # below rather than silently agreeing with the documentation.
        measured = max(extremes)
        assert measured == MEASURED_BPS_CEILING
        # The published figure is what the code actually produces.
        assert DOCUMENTED_BPS_CEILING == measured
        assert DOCUMENTED_BPS_CEILING == 600

    @given(subtotal=_cents(1, 200_000), discount_bps=st.integers(-5000, 60000))
    @PROPERTY
    def test_a_discount_never_conjures_or_destroys_money(
        self, subtotal, discount_bps
    ):
        schedule = commerce_schedule()
        applied = max(Decimal("0"), min(Decimal(discount_bps), MAX_DISCOUNT_BPS))
        lines = self._line_names(schedule)

        fees = discounted_fees(subtotal, schedule, Decimal(discount_bps))

        before = [fees[f"{name}_before"] for name in lines]
        after = [fees[f"{name}_after"] for name in lines]

        # sum(after) + waived == sum(before), exactly, for every discount.
        assert sum(after, Decimal("0")) + fees["waived"] == sum(before, Decimal("0"))
        # No fee line is ever negative, whatever the caller asked for.
        assert all(value >= Decimal("0") for value in after)
        assert fees["waived"] >= Decimal("0")
        # The discount is clamped, so a 60 000 bps request books 10 000.
        assert fees["discount_bps_applied"] == applied
        # The waiver can never exceed the line it waives.
        assert fees["waived"] <= sum(before, Decimal("0"))
        # ``total`` is the subtotal plus the fee lines that survive, and
        # ``total_before`` the fee lines that were charged, before any waiver.
        assert fees["total"] == subtotal + sum(after, Decimal("0"))
        assert fees["total_before"] == sum(before, Decimal("0"))

    @given(subtotal=_cents(1, 200_000), discount_bps=st.integers(0, 20000))
    @PROPERTY
    def test_a_full_discount_waives_only_the_line_it_names(
        self, subtotal, discount_bps
    ):
        schedule = commerce_schedule()
        lines = self._line_names(schedule)
        target = DISCOUNTED_FEE_LINE

        full = discounted_fees(subtotal, schedule, Decimal(MAX_DISCOUNT_BPS))
        partial = discounted_fees(subtotal, schedule, Decimal(discount_bps))

        # At 100 % the discounted line collects nothing and waives all of it:
        # the pre-discount fee of that line is exactly the waiver, so the sum
        # of the two is the pre-discount fee and never revenue.
        assert full[f"{target}_after"] == Decimal("0")
        assert full[f"{target}_before"] == full["waived"]
        # Every other line passes straight through a discount that names a
        # different line -- the landscape fund is not the platform's to waive.
        for name in lines:
            if name != target:
                assert full[f"{name}_after"] == full[f"{name}_before"]
        assert full["total"] == subtotal + sum(
            (full[f"{name}_after"] for name in lines if name != target),
            Decimal("0"),
        )
        # A larger discount can only ever collect less.
        assert partial["total"] >= full["total"]


# ---------------------------------------------------------------------------
# 3. idempotency of a payment/batch intent
# ---------------------------------------------------------------------------


class TestIdempotency:
    """Replaying the same intent credits once; the table makes it so."""

    @staticmethod
    async def _guarded_payment(
        db_session,
        *,
        user_id: str,
        key: str,
        route: str,
        payload_hash: str,
        effect,
    ):
        """The idempotency-table semantics the gateway middleware implements.

        Check-then-write on ``(user_id, key)``: a completed key replays its
        cached response, a pending one is a 409, a key reused with a
        different payload is a 422, and anything else runs ``effect`` once
        and records it. Returns the status of the attempt.
        """
        existing = (
            (
                await db_session.execute(
                    select(FinIdempotencyKey).where(
                        FinIdempotencyKey.key == key,
                        FinIdempotencyKey.user_id == user_id,
                    )
                )
            )
            .scalar_one_or_none()
        )
        if existing is not None:
            if existing.request_hash != payload_hash:
                return "reused"
            if existing.status == "completed":
                return "replayed"
            return "in_progress"

        record = FinIdempotencyKey(
            user_id=user_id,
            key=key,
            route=route,
            request_hash=payload_hash,
            status="pending",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        db_session.add(record)
        await db_session.commit()

        await effect()

        existing = (
            (
                await db_session.execute(
                    select(FinIdempotencyKey).where(
                        FinIdempotencyKey.key == key,
                        FinIdempotencyKey.user_id == user_id,
                    )
                )
            )
            .scalar_one()
        )
        existing.status = "completed"
        existing.response_code = 200
        existing.response_body = {"credited": True}
        await db_session.commit()
        return "applied"

    @staticmethod
    async def _credit_wallet(db_session, user_id: str, amount: Decimal, reference: str):
        """Credit one wallet and book the matching REWARD_LIABILITY entry."""
        from services.finance.ledger_service import LedgerService as _Ledger

        wallet = (
            (
                await db_session.execute(
                    select(EcoWallet).where(EcoWallet.user_id == user_id)
                )
            )
            .scalar_one_or_none()
        )
        if wallet is None:
            wallet = EcoWallet(user_id=user_id, balance=Decimal("0"), version=1)
            db_session.add(wallet)
            await db_session.commit()

        wallet.balance = Decimal(str(wallet.balance)) + amount
        await db_session.commit()

        ledger = _Ledger(db_session)
        batch = await ledger.create_journal_batch(
            reference_type="eco_earning",
            reference_id=reference,
            entries=[
                {
                    "account_id": "ECO_ASSET",
                    "entry_type": "debit",
                    "asset": "ECO",
                    "amount": str(amount),
                },
                {
                    "account_id": REWARD_LIABILITY,
                    "entry_type": "credit",
                    "asset": "ECO",
                    "amount": str(amount),
                },
            ],
            created_by=user_id,
        )
        await ledger.post_journal_batch(batch.id)

    @given(amount=_cents(1, 10_000), replays=st.integers(1, 4))
    @PROPERTY
    async def test_replaying_one_payment_intent_credits_once(
        self, db_session, amount, replays
    ):
        await _wipe(db_session)
        user_id = _unique("user")
        key = _unique("idem")
        payload_hash = uuid.uuid4().hex
        reference = _unique("earn")

        async def effect():
            await self._credit_wallet(db_session, user_id, amount, reference)

        for _ in range(replays):
            status = await self._guarded_payment(
                db_session,
                user_id=user_id,
                key=key,
                route="/api/v1/finance/wallet/earn",
                payload_hash=payload_hash,
                effect=effect,
            )
            assert status in {"applied", "replayed"}

        wallet = (
            await db_session.execute(select(EcoWallet).where(EcoWallet.user_id == user_id))
        ).scalar_one()
        assert Decimal(str(wallet.balance)) == amount

        credits = (
            (
                await db_session.execute(
                    select(FinJournalEntry).where(
                        FinJournalEntry.account_id == REWARD_LIABILITY,
                        FinJournalEntry.asset == "ECO",
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(credits) == 1
        assert Decimal(str(credits[0].amount)) == amount

    @given(amount=_cents(1, 10_000))
    @PROPERTY
    async def test_key_reused_with_a_different_payload_is_refused(
        self, db_session, amount
    ):
        await _wipe(db_session)
        user_id = _unique("user")
        key = _unique("idem")

        status = await self._guarded_payment(
            db_session,
            user_id=user_id,
            key=key,
            route="/api/v1/finance/wallet/earn",
            payload_hash=uuid.uuid4().hex,
            effect=lambda: self._credit_wallet(db_session, user_id, amount, _unique("earn")),
        )
        assert status == "applied"

        status = await self._guarded_payment(
            db_session,
            user_id=user_id,
            key=key,
            route="/api/v1/finance/wallet/earn",
            payload_hash=uuid.uuid4().hex,
            effect=lambda: self._credit_wallet(db_session, user_id, amount, _unique("earn")),
        )
        assert status == "reused"

        wallet = (
            await db_session.execute(select(EcoWallet).where(EcoWallet.user_id == user_id))
        ).scalar_one()
        assert Decimal(str(wallet.balance)) == amount

    @given(amount=_cents(1, 10_000))
    @PROPERTY
    async def test_two_users_never_share_an_idempotency_key(
        self, db_session, amount
    ):
        """The unique index is on ``(user_id, key)`` — a shared key is two keys."""
        await _wipe(db_session)
        key = _unique("shared-key")

        for user_id in (_unique("alice"), _unique("bob")):
            status = await self._guarded_payment(
                db_session,
                user_id=user_id,
                key=key,
                route="/api/v1/finance/wallet/earn",
                payload_hash=uuid.uuid4().hex,
                effect=lambda u=user_id: self._credit_wallet(
                    db_session, u, amount, _unique("earn")
                ),
            )
            assert status == "applied"

        rows = (
            (await db_session.execute(select(FinIdempotencyKey)))
            .scalars()
            .all()
        )
        assert len(rows) == 2
        assert {row.key for row in rows} == {key}

        for user_id in (row.user_id for row in rows):
            wallet = (
                await db_session.execute(
                    select(EcoWallet).where(EcoWallet.user_id == user_id)
                )
            ).scalar_one()
            assert Decimal(str(wallet.balance)) == amount

    async def test_the_unique_index_actually_rejects_a_duplicate(self, db_session):
        await _wipe(db_session)
        key = _unique("idem")
        for _ in range(2):
            db_session.add(
                FinIdempotencyKey(
                    user_id="dup-user",
                    key=key,
                    route="/api/v1/finance/wallet/earn",
                    request_hash=uuid.uuid4().hex,
                    status="pending",
                )
            )
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            await db_session.commit()
        await db_session.rollback()

        rows = (await db_session.execute(select(FinIdempotencyKey))).scalars().all()
        assert rows == []


# ---------------------------------------------------------------------------
# 4. reconciliation
# ---------------------------------------------------------------------------


async def _seed_wallet_and_ledger(db_session, user_id: str, amount: Decimal) -> None:
    """A wallet whose balance is exactly its REWARD_LIABILITY ledger balance."""
    await ensure_account(
        db_session,
        code=REWARD_LIABILITY,
        name="Reward liability",
        type="liability",
        asset="ECO",
        currency="ECO",
    )
    await ensure_account(
        db_session,
        code="ECO_ASSET",
        name="ECO asset",
        type="asset",
        asset="ECO",
        currency="ECO",
    )

    db_session.add(EcoWallet(user_id=user_id, balance=amount, version=1))
    await db_session.commit()

    ledger = LedgerService(db_session)
    batch = await ledger.create_journal_batch(
        reference_type="eco_earning",
        reference_id=_unique("earn"),
        entries=[
            {
                "account_id": "ECO_ASSET",
                "entry_type": "debit",
                "asset": "ECO",
                "amount": str(amount),
            },
            {
                "account_id": REWARD_LIABILITY,
                "entry_type": "credit",
                "asset": "ECO",
                "amount": str(amount),
            },
        ],
        created_by=user_id,
    )
    await ledger.post_journal_batch(batch.id)


async def _seed_posted_batch(db_session, amount: Decimal) -> int:
    ledger = LedgerService(db_session)
    batch = await ledger.create_journal_batch(
        reference_type="settlement",
        reference_id=_unique("ref"),
        entries=[
            {
                "account_id": "ECO_CASH",
                "entry_type": "debit",
                "asset": "IRR",
                "amount": str(amount),
            },
            {
                "account_id": "ECO_SELLER_PAYABLE",
                "entry_type": "credit",
                "asset": "IRR",
                "amount": str(amount),
            },
        ],
        created_by="property-test",
    )
    await ledger.post_journal_batch(batch.id)
    return batch.id


async def _seed_order(db_session, total: Decimal, status: str, payment_status: str):
    order = ComOrder(
        id=_unique("order"),
        order_number=_unique("ORD"),
        buyer_id="buyer-property",
        seller_id="seller-property",
        status=status,
        payment_status=payment_status,
        currency="IRR",
        subtotal=total,
        platform_fee=Decimal("0"),
        landscape_fee=Decimal("0"),
        total=total,
    )
    db_session.add(order)
    await db_session.commit()
    return order


async def _seed_intent(db_session, order_id: str, amount: Decimal, status: str):
    intent = ComPaymentIntent(
        id=_unique("pi"),
        order_id=order_id,
        buyer_id="buyer-property",
        provider="bank_transfer",
        amount=amount,
        currency="IRR",
        status=status,
    )
    db_session.add(intent)
    await db_session.commit()
    return intent


async def _seed_settlement(db_session, order_id: str, amount: Decimal, batch_id):
    settlement = ComSettlement(
        id=_unique("stl"),
        order_id=order_id,
        seller_id="seller-property",
        amount=amount,
        currency="IRR",
        commission_fee=Decimal("0"),
        landscape_fee=Decimal("0"),
        status="paid",
        journal_batch_id=batch_id,
    )
    db_session.add(settlement)
    await db_session.commit()
    return settlement


@st.composite
def clean_state(draw):
    """A random financial state that is consistent by construction."""
    return {
        "wallet_amount": draw(_cents(1, 100_000)),
        "orders": draw(
            st.lists(
                st.tuples(_cents(1, 100_000), st.sampled_from(["paid", "settled"])),
                min_size=0,
                max_size=3,
            )
        ),
        "draft": draw(st.booleans()),
    }


class TestReconciliation:
    """Clean states reconcile clean; one injected discrepancy is always caught."""

    @given(state=clean_state())
    @PROPERTY
    async def test_clean_state_reconciles_overall(self, db_session, state):
        await _wipe(db_session)
        user_id = _unique("user")

        await _seed_wallet_and_ledger(db_session, user_id, state["wallet_amount"])

        posted_batch_id = None
        for total, status in state["orders"]:
            order = await _seed_order(db_session, total, status, "paid")
            await _seed_intent(db_session, order.id, total, "succeeded")
            if status == "settled":
                if posted_batch_id is None:
                    posted_batch_id = await _seed_posted_batch(db_session, total)
                await _seed_settlement(db_session, order.id, total, posted_batch_id)

        if state["draft"]:
            # A draft order legitimately carries no payment intent yet.
            await _seed_order(db_session, Decimal("5"), "draft", "pending")

        service = ReconciliationService(db_session)
        for check in (
            await service.reconcile_wallet_ledger(),
            await service.reconcile_orders_payments(),
            await service.reconcile_inventory(),
        ):
            assert check["discrepancies"] == [], check
            assert check["discrepancies_count"] == 0
            assert check["overall_ok"] is True

        full = await service.run_full_reconciliation()
        assert full["overall_ok"] is True
        assert set(full["checks"]) == {"wallet_ledger", "orders_payments", "inventory"}

    async def test_empty_database_reconciles_clean(self, db_session):
        await _wipe(db_session)
        full = await ReconciliationService(db_session).run_full_reconciliation()
        assert full["overall_ok"] is True

    @given(state=clean_state(), injection=st.sampled_from(INJECTIONS))
    @PROPERTY
    async def test_a_single_injected_discrepancy_is_detected(
        self, db_session, state, injection
    ):
        await _wipe(db_session)
        user_id = _unique("user")
        await _seed_wallet_and_ledger(db_session, user_id, state["wallet_amount"])

        posted_batch_id = await _seed_posted_batch(db_session, Decimal("500"))

        # Every state always carries one fully consistent settled order, so
        # each injection has a settlement to act on whichever orders the
        # random state also contributed.
        settled_order = await _seed_order(db_session, Decimal("500"), "settled", "paid")
        await _seed_intent(db_session, settled_order.id, Decimal("500"), "succeeded")
        await _seed_settlement(db_session, settled_order.id, Decimal("500"), posted_batch_id)

        for total, status in state["orders"]:
            order = await _seed_order(db_session, total, status, "paid")
            await _seed_intent(db_session, order.id, total, "succeeded")
            if status == "settled":
                await _seed_settlement(db_session, order.id, total, posted_batch_id)

        order = settled_order
        settlement = (
            (
                await db_session.execute(
                    select(ComSettlement).where(ComSettlement.order_id == order.id)
                )
            )
            .scalars()
            .one_or_none()
        )

        if injection == "wallet_drift":
            wallet = (
                await db_session.execute(
                    select(EcoWallet).where(EcoWallet.user_id == user_id)
                )
            ).scalar_one()
            wallet.balance = Decimal(str(wallet.balance)) + Decimal("0.01")
            await db_session.commit()
        elif injection == "payment_amount_mismatch":
            intent = (
                (
                    await db_session.execute(
                        select(ComPaymentIntent).where(
                            ComPaymentIntent.order_id == order.id
                        )
                    )
                )
                .scalars()
                .first()
            )
            intent.amount = Decimal(str(intent.amount)) + Decimal("0.01")
            await db_session.commit()
        elif injection == "orphaned_intent":
            await _seed_intent(
                db_session, _unique("missing-order"), Decimal("500"), "succeeded"
            )
        elif injection == "unconfirmed_intent":
            intent = (
                (
                    await db_session.execute(
                        select(ComPaymentIntent).where(
                            ComPaymentIntent.order_id == order.id
                        )
                    )
                )
                .scalars()
                .first()
            )
            intent.status = "awaiting_transfer"
            await db_session.commit()
        elif injection == "missing_settlement":
            if settlement is not None:
                await db_session.delete(settlement)
                await db_session.commit()
        elif injection == "settlement_amount_mismatch":
            if settlement is not None:
                settlement.amount = Decimal(str(settlement.amount)) - Decimal("0.01")
                await db_session.commit()
        else:  # unposted_batch
            if settlement is not None:
                batch = (
                    await db_session.execute(
                        select(FinJournalBatch).where(
                            FinJournalBatch.id == settlement.journal_batch_id
                        )
                    )
                ).scalar_one()
                batch.is_posted = False
                await db_session.commit()

        service = ReconciliationService(db_session)
        wallets = await service.reconcile_wallet_ledger()
        orders_check = await service.reconcile_orders_payments()
        inventory = await service.reconcile_inventory()

        # A wallet discrepancy is the wallet check's to catch; every other
        # injection here is the orders check's. Neither is ever the
        # inventory check's: an inventory drift is the inventory test's job.
        if injection == "wallet_drift":
            assert wallets["overall_ok"] is False
            assert wallets["discrepancies_count"] == 1
            # The service serialises the difference through a float, so the
            # comparison has to tolerate float presentation noise on the way.
            assert wallets["discrepancies"][0]["difference"] == pytest.approx(
                0.01, abs=1e-9
            )
            assert orders_check["overall_ok"] is True
            assert inventory["overall_ok"] is True
        else:
            assert orders_check["overall_ok"] is False, orders_check["discrepancies"]
            assert orders_check["discrepancies_count"] >= 1
            assert wallets["overall_ok"] is True
            assert inventory["overall_ok"] is True

        full = await service.run_full_reconciliation()
        assert full["overall_ok"] is False
        # ``checked_at`` is a timestamp, so the fold is compared without it.
        assert _without_checked_at(full["checks"]["wallet_ledger"]) == _without_checked_at(
            wallets
        )
        assert _without_checked_at(full["checks"]["orders_payments"]) == (
            _without_checked_at(orders_check)
        )
        assert _without_checked_at(full["checks"]["inventory"]) == _without_checked_at(
            inventory
        )

    @given(
        injection=st.sampled_from(
            ["on_hand_drift", "reserved_drift", "orphan_only", "settlement_only"]
        )
    )
    @PROPERTY
    async def test_inventory_discrepancy_is_always_detected(self, db_session, injection):
        from services.inventory.service import StockService

        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse("PROP-WH", "Property Warehouse")
        sku = await stock.create_sku(sku_code=_unique("SKU"), name="Property compost")
        await stock.receipt(sku.id, warehouse.id, Decimal("100"), created_by="property")

        service = ReconciliationService(db_session)
        clean = await service.reconcile_inventory()
        assert clean["overall_ok"] is True
        assert clean["total_balances_checked"] == 1

        if injection == "on_hand_drift":
            balance = (
                await db_session.execute(
                    select(InvInventoryBalance).where(
                        InvInventoryBalance.sku_id == sku.id,
                        InvInventoryBalance.warehouse_id == warehouse.id,
                    )
                )
            ).scalar_one()
            balance.on_hand += Decimal("0.5")
            await db_session.commit()
        elif injection == "reserved_drift":
            reservation = await stock.reserve_stock(
                sku.id, warehouse.id, Decimal("10"), "order", _unique("order")
            )
            await stock.consume_reservation(reservation.id)
            balance = (
                await db_session.execute(
                    select(InvInventoryBalance).where(
                        InvInventoryBalance.sku_id == sku.id,
                        InvInventoryBalance.warehouse_id == warehouse.id,
                    )
                )
            ).scalar_one()
            balance.reserved += Decimal("3")
            await db_session.commit()
        elif injection == "orphan_only":
            # An orphaned payment intent alone must fail the orders check.
            await _seed_intent(
                db_session, _unique("missing-order"), Decimal("500"), "succeeded"
            )
        else:
            order = await _seed_order(db_session, Decimal("500"), "settled", "paid")
            await _seed_intent(db_session, order.id, Decimal("500"), "succeeded")
            batch_id = await _seed_posted_batch(db_session, Decimal("500"))
            await _seed_settlement(db_session, order.id, Decimal("500"), batch_id)
            settlement = (
                await db_session.execute(
                    select(ComSettlement).where(ComSettlement.order_id == order.id)
                )
            ).scalar_one()
            settlement.journal_batch_id = None
            await db_session.commit()

        result = await service.reconcile_inventory()
        orders_check = await service.reconcile_orders_payments()

        if injection in {"on_hand_drift", "reserved_drift"}:
            assert result["overall_ok"] is False
            assert result["discrepancies_count"] == 1
            drift = result["discrepancies"][0]
            if injection == "on_hand_drift":
                assert Decimal(drift["on_hand_drift"]) == Decimal("0.5")
            else:
                assert Decimal(drift["reserved_drift"]) == Decimal("3")
        else:
            assert orders_check["overall_ok"] is False
            assert orders_check["discrepancies_count"] >= 1


# ---------------------------------------------------------------------------
# 5. journal rows are balanced however they were written
# ---------------------------------------------------------------------------


class TestJournalIntegrity:
    """What the ledger stores is what the reports say."""

    @given(plan=balanced_batch())
    @PROPERTY
    async def test_stored_amounts_round_trip_as_decimals(self, db_session, plan):
        entries, _ = plan
        await _wipe(db_session)
        ledger = LedgerService(db_session)

        batch = await ledger.create_journal_batch(
            reference_type="property", reference_id=_unique("ref"), entries=entries
        )
        await ledger.post_journal_batch(batch.id)

        rows = (
            (
                await db_session.execute(
                    select(FinJournalEntry)
                    .where(FinJournalEntry.batch_id == batch.id)
                    .order_by(FinJournalEntry.id)
                )
            )
            .scalars()
            .all()
        )
        stored = {
            row.id: (
                row.account_id,
                row.entry_type,
                row.asset,
                Decimal(str(row.amount)),
            )
            for row in rows
        }
        written = {
            (
                entry["account_id"],
                entry["entry_type"],
                entry["asset"],
                Decimal(entry["amount"]),
            )
            for entry in entries
        }
        assert sorted(stored.values()) == sorted(written)

        debits = sum(
            (amount for _, kind, _, amount in stored.values() if kind == "debit"),
            Decimal("0"),
        )
        credits = sum(
            (amount for _, kind, _, amount in stored.values() if kind == "credit"),
            Decimal("0"),
        )
        assert debits == credits

    async def test_trial_balance_ignores_draft_batches(self, db_session):
        await _wipe(db_session)
        ledger = LedgerService(db_session)
        await ledger.create_journal_batch(
            reference_type="property",
            reference_id=_unique("ref"),
            entries=[
                {
                    "account_id": "P-DEBIT",
                    "entry_type": "debit",
                    "asset": "IRR",
                    "amount": "10",
                },
                {
                    "account_id": "P-CREDIT",
                    "entry_type": "credit",
                    "asset": "IRR",
                    "amount": "10",
                },
            ],
        )

        report = await ledger.trial_balance()
        assert report["rows"] == []
        assert report["totals"] == []
