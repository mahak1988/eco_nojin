"""Property-based tests for the inventory valuation and reservation invariants.

Every test is a Hypothesis property test on a deterministic profile:
``deadline=None``, a small ``max_examples`` budget, ``database=None`` (no
example database is written) and ``derandomize=True`` (the same examples on
every run). Each example starts from a database the test wipes itself, so no
example can observe another's rows, and no key is shared between examples.

What is pinned, by invariant:

1. **Valuation conservation** — replaying the stored movement ledger under the
   documented moving-average rule, ``Σ received value == Σ issued value +
   remaining pool value``. The residual is the Decimal arithmetic's own
   28-digit division dust, orders of magnitude below the ``Numeric(18, 8)``
   money scale, and the test says so rather than hiding it.
2. **Storage fidelity** — every movement stores ``qty × unit_cost`` at the
   money scale, and an outbound leg's stored ``unit_cost`` is that moment's
   moving average.
3. **Read-API parity** — ``sku_valuation().total_value`` equals the pool value
   and equals the same SKU's row in ``valuation_report()``; the report folds
   from its SKUs and its warehouses.
4. **Ledger parity** — the ``ECO_INVENTORY`` journal balance is the stock's
   value and ``ECO_COGS`` is what was issued, both to the money scale.
5. **Valuation rules** — an outflow leaves the average unchanged, a transfer
   preserves value and posts no batch, an empty pool re-bases on the next
   inbound cost, the average blends receipts, and unimplemented methods are
   refused.
6. **Reservation lifecycle** — across random reserve/consume/release
   sequences, ``available + reserved`` is conserved, ``reserved`` equals the
   open reservation sum, nothing goes negative, and an expired reservation is
   released by the P2-18 sweeper.
7. **Reconciliation** — a random stock history reconciles clean.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select, text

from database.models import (
    FinJournalEntry,
    InvReservation,
    InvStockMovement,
)
from services.api_gateway.exceptions import EcoNojinException
from services.finance.chart_of_accounts import ECO_COGS, ECO_INVENTORY
from services.finance.ledger_service import LedgerService
from services.inventory.service import (
    VALUATION_METHOD,
    StockService,
    sweep_expired_reservations,
)

# ---------------------------------------------------------------------------
# Deterministic Hypothesis profile.
# ---------------------------------------------------------------------------

_HEALTH = [HealthCheck.function_scoped_fixture, HealthCheck.too_slow]

PROPERTY = settings(
    max_examples=15,
    deadline=None,
    database=None,
    derandomize=True,
    suppress_health_check=_HEALTH,
)

#: Only the tables this file writes, children before parents, so one DELETE
#: pass fully isolates one example from the next.
_OWNED_TABLES = (
    "inv_stocktake_lines",
    "inv_stocktakes",
    "inv_reservations",
    "inv_stock_movements",
    "inv_inventory_balances",
    "inv_lots",
    "inv_locations",
    "inv_warehouses",
    "inv_skus",
    "fin_journal_entries",
    "fin_journal_batches",
    "fin_accounts",
    "audit_events",
)

#: The money scale of the ``Numeric(18, 8)`` columns the movements are stored
#: in, and therefore the coarsest rounding anything in this file can carry.
MONEY_SCALE = Decimal("0.00000001")

#: Movement types that add value to a warehouse pool at the movement's own
#: cost, and those that take value out at the pool's current average. The rule
#: is the one ``_average_costs_from_movements`` documents and applies.
INBOUND_MOVEMENT_TYPES = frozenset({"receipt", "return", "unblock"})
OUTBOUND_MOVEMENT_TYPES = frozenset({"issue", "scrap"})


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _cents(low: int, high: int) -> st.SearchStrategy[Decimal]:
    return st.integers(min_value=low, max_value=high).map(lambda c: Decimal(c) / 100)


def _money(value: Decimal) -> Decimal:
    """The quantisation the storage layer applies to a cost.

    ``_build_movement`` writes ``_money(unit_cost)`` and the module's ``_money``
    rounds half up at the money scale, so half-even here would disagree with
    what is actually stored on an exact half.
    """
    return Decimal(value).quantize(MONEY_SCALE, rounding=ROUND_HALF_UP)


async def _wipe(db_session) -> None:
    """Empty every table this file touches, so an example starts clean."""
    await db_session.rollback()
    for table in _OWNED_TABLES:
        await db_session.execute(text(f"DELETE FROM {table}"))
    await db_session.commit()
    db_session.expunge_all()


# ---------------------------------------------------------------------------
# The invariant, stated in the test's own terms
# ---------------------------------------------------------------------------


def _replay(movements: list[InvStockMovement]) -> dict:
    """Replay the stored movement ledger under the moving-average rule.

    This is an independent restatement of the documented policy, not a call
    into the implementation: a warehouse holds a ``(quantity, value)`` pair, an
    inbound leg adds ``qty x cost``, an outbound leg removes ``qty x average``
    and leaves the average untouched, a transfer removes from the source at
    the average and adds to the destination at the cost the row records, and an
    empty pool re-bases on the next inbound leg.

    Returns ``{"pools", "received", "issued", "remaining", "legs"}`` where each
    leg carries the value the rule attributes to it.
    """
    pools: dict[int, list[Decimal]] = {}
    received = Decimal("0")
    issued = Decimal("0")
    legs: list[dict] = []

    def _draw(warehouse_id: int) -> Decimal | None:
        """The pool's average before a draw, or ``None`` of an empty pool."""
        pool = pools.get(warehouse_id)
        if pool is None or pool[0] <= 0:
            return None
        return pool[1] / pool[0]

    def _take(warehouse_id: int, qty: Decimal) -> Decimal | None:
        """Remove ``qty`` from ``warehouse_id`` at the pool's average.

        Returns the average the removal was priced at, or ``None`` when the
        pool had nothing to give. An empty *value* still has a quantity, so
        the quantity leg is taken at a zero average rather than skipped —
        that is what ``_average_costs_from_movements`` does too.
        """
        pool = pools.setdefault(warehouse_id, [Decimal("0"), Decimal("0")])
        average = _draw(warehouse_id)
        if average is None:
            return None
        pool[0] -= qty
        if pool[0] <= 0:
            # A drawn-down pool re-bases to zero rather than keeping a
            # fraction, exactly as the module documents.
            pool[0] = Decimal("0")
            pool[1] = Decimal("0")
        else:
            pool[1] = average * pool[0]
        return average

    def _add(warehouse_id: int, qty: Decimal, cost: Decimal) -> None:
        pool = pools.setdefault(warehouse_id, [Decimal("0"), Decimal("0")])
        pool[0] += qty
        pool[1] += qty * cost

    for movement in movements:
        qty = Decimal(str(movement.qty))
        stored_cost = (
            Decimal(str(movement.unit_cost))
            if movement.unit_cost is not None
            else Decimal("0")
        )
        warehouse_id = int(movement.warehouse_id)

        if movement.movement_type in INBOUND_MOVEMENT_TYPES:
            # Valued at the movement's own cost: the receipt price, the
            # caller's return price, or the average an unblock restores at.
            value = qty * stored_cost
            _add(warehouse_id, qty, stored_cost)
            received += value
            legs.append(
                {
                    "movement": movement,
                    "kind": "inbound",
                    "warehouse_id": warehouse_id,
                    "qty": qty,
                    "cost": stored_cost,
                    "value": value,
                }
            )
            continue

        if movement.movement_type in OUTBOUND_MOVEMENT_TYPES:
            average = _take(warehouse_id, qty)
            if average is not None:
                value = qty * average
                issued += value
                legs.append(
                    {
                        "movement": movement,
                        "kind": "outbound",
                        "warehouse_id": warehouse_id,
                        "qty": qty,
                        "cost": average,
                        "value": value,
                    }
                )
            continue

        if movement.movement_type == "transfer":
            # One row carries both legs: out of the warehouse it is stored on,
            # into ``to_warehouse_id``.
            average = _take(warehouse_id, qty)
            if average is not None:
                value = qty * average
                issued += value
                legs.append(
                    {
                        "movement": movement,
                        "kind": "outbound",
                        "warehouse_id": warehouse_id,
                        "qty": qty,
                        "cost": average,
                        "value": value,
                    }
                )
            if movement.to_warehouse_id is not None:
                destination = int(movement.to_warehouse_id)
                # The destination leg is valued at the cost the row records,
                # which is the source average quantised to the money scale.
                inbound_value = qty * stored_cost
                _add(destination, qty, stored_cost)
                received += inbound_value
                legs.append(
                    {
                        "movement": movement,
                        "kind": "inbound",
                        "warehouse_id": destination,
                        "qty": qty,
                        "cost": stored_cost,
                        "value": inbound_value,
                    }
                )

    remaining = sum((pool[1] for pool in pools.values()), Decimal("0"))
    return {
        "pools": pools,
        "received": received,
        "issued": issued,
        "remaining": remaining,
        "legs": legs,
    }


async def _movements(db_session, sku_id: int) -> list[InvStockMovement]:
    """One SKU's movements in ledger order."""
    return (
        (
            await db_session.execute(
                select(InvStockMovement)
                .where(InvStockMovement.sku_id == sku_id)
                .order_by(InvStockMovement.created_at, InvStockMovement.id)
            )
        )
        .scalars()
        .all()
    )


async def _account_balance(db_session, account_code: str, asset: str = "IRR"):
    """Signed balance of one account: credits positive, debits negative."""
    return await LedgerService(db_session).get_account_balance(account_code, asset)


# ---------------------------------------------------------------------------
# strategies
# ---------------------------------------------------------------------------


@st.composite
def stock_plan(draw):
    """A random but executable stock history.

    Quantities are drawn as a share of whatever is on hand when the body
    reaches the operation, so the plan is always satisfiable without rejection
    sampling and without guessing the state.
    """
    return {
        "receipts": draw(
            st.lists(
                st.tuples(st.integers(1, 40), _cents(1, 5000)),
                min_size=1,
                max_size=4,
            )
        ),
        "ops": draw(
            st.lists(
                st.tuples(
                    st.sampled_from(
                        [
                            "issue",
                            "return",
                            "scrap",
                            "unblock",
                            "transfer",
                        ]
                    ),
                    st.integers(1, 4),
                ),
                min_size=0,
                max_size=5,
            )
        ),
        "reservations": draw(
            st.lists(
                st.tuples(
                    st.integers(1, 4), st.sampled_from(["consume", "release"])
                ),
                min_size=0,
                max_size=4,
            )
        ),
    }


def _share(qty: Decimal, share: int) -> Decimal:
    """A whole-unit ``qty``/``share``, never smaller than one."""
    if qty < 1:
        return qty
    return max(Decimal("1"), (qty / share).quantize(Decimal("1")))


@st.composite
def reconcilable_plan(draw):
    """A stock history the balance-vs-ledger reconciliation can read exactly.

    Every operation here — a receipt, an issue, a return, a scrap, an unblock,
    a transfer, a reserve, a consume, a release — has a movement row that
    reconciles, so the plan is a clean state and the assertion is the strong
    one: ``overall_ok``. ``unblock`` used to be filtered out as the one
    documented gap (it moved ``on_hand`` while the reconciliation's signed
    movement sum ignored it); it is now summed as an inbound leg, so it stays.
    """
    return draw(stock_plan())


async def _run_plan(db_session, plan) -> tuple[int, StockService]:
    """Execute a plan against a fresh SKU and two warehouses."""
    stock = StockService(db_session)
    warehouses = [
        await stock.create_warehouse(_unique("WH"), _unique("warehouse")),
        await stock.create_warehouse(_unique("WH"), _unique("warehouse")),
    ]
    sku = await stock.create_sku(_unique("SKU"), _unique("item"))

    for index, (qty, cost) in enumerate(plan["receipts"]):
        warehouse = warehouses[index % len(warehouses)]
        await stock.receipt(
            sku.id, warehouse.id, Decimal(qty), unit_cost=cost, created_by="prop"
        )

    source, target = warehouses
    for kind, share in plan["ops"]:
        balance = await stock.get_balance(sku.id, source.id)
        if kind in ("issue", "scrap"):
            if balance.on_hand < 1:
                continue
            qty = _share(balance.on_hand, share)
            if kind == "issue":
                await stock.issue(sku.id, source.id, qty, created_by="prop")
            else:
                await stock.scrap(sku.id, source.id, qty, reason="damaged")
        elif kind == "return":
            await stock.return_goods(sku.id, source.id, Decimal(share), created_by="prop")
        elif kind == "unblock":
            if balance.blocked < 1:
                continue
            await stock.unblock_stock(
                sku.id, source.id, _share(balance.blocked, share), reason="restored"
            )
        else:  # transfer
            if balance.on_hand < 1:
                continue
            qty = _share(balance.on_hand, share)
            await stock.transfer(sku.id, source.id, target.id, qty, created_by="prop")

    for share, action in plan["reservations"]:
        balance = await stock.get_balance(sku.id, source.id)
        if balance.available < 1:
            continue
        qty = _share(balance.available, share)
        reservation = await stock.reserve_stock(
            sku.id,
            source.id,
            qty,
            "order",
            _unique("order"),
            expires_at=datetime.now(UTC) + timedelta(days=365),
            created_by="prop",
        )
        if action == "consume":
            await stock.consume_reservation(reservation.id, qty)
        else:
            await stock.release_reservation(reservation.id)

    return sku.id, stock


# ---------------------------------------------------------------------------
# 1-3. valuation conservation and storage fidelity
# ---------------------------------------------------------------------------


class TestValuationConservation:
    """Received value is either issued or still on the shelf."""

    @given(plan=stock_plan())
    @PROPERTY
    async def test_received_value_equals_issued_plus_remaining(
        self, db_session, plan
    ):
        await _wipe(db_session)
        sku_id, _ = await _run_plan(db_session, plan)

        movements = await _movements(db_session, sku_id)
        replay = _replay(movements)

        # The money that came in is the money that went out plus what is left.
        residual = replay["received"] - replay["issued"] - replay["remaining"]
        assert residual == 0 or abs(residual) < Decimal("1e-15"), (
            f"residual {residual} on {len(movements)} movements"
        )
        # And it is never anywhere near the money scale, which is the smallest
        # quantity a real accounting error could be a multiple of.
        assert abs(residual) <= MONEY_SCALE * len(movements)

    @given(plan=stock_plan())
    @PROPERTY
    async def test_every_leg_is_valued_the_way_it_was_written(
        self, db_session, plan
    ):
        """``total_cost`` is the movement's own quantised valuation, and an
        outbound ``unit_cost`` is the average of the moment."""
        await _wipe(db_session)
        sku_id, _ = await _run_plan(db_session, plan)

        movements = await _movements(db_session, sku_id)
        replay = _replay(movements)

        for leg in replay["legs"]:
            movement = leg["movement"]
            stored_total = (
                Decimal(str(movement.total_cost))
                if movement.total_cost is not None
                else Decimal("0")
            )
            # ``total_cost`` is ``_money(unit_cost x qty)``, so it matches the
            # value the rule attributes to within the money scale times the
            # quantity that scale is applied to.
            assert abs(stored_total - leg["value"]) <= MONEY_SCALE * max(
                leg["qty"], Decimal("1")
            ) + MONEY_SCALE, leg["kind"]

            if leg["kind"] == "outbound" and leg["cost"] > 0:
                # The average is written rounded half even to the money scale.
                assert Decimal(str(movement.unit_cost)) == _money(leg["cost"]), movement

    @given(plan=stock_plan())
    @PROPERTY
    async def test_valuation_total_is_the_pool_value(self, db_session, plan):
        await _wipe(db_session)
        sku_id, stock = await _run_plan(db_session, plan)

        movements = await _movements(db_session, sku_id)
        replay = _replay(movements)
        valuation = await stock.sku_valuation(sku_id)

        by_warehouse = {
            int(row["warehouse_id"]): row for row in valuation["warehouses"]
        }
        for warehouse_id, (qty, value) in replay["pools"].items():
            row = by_warehouse[warehouse_id]
            # ``total_value`` is on hand x average, quantised to the scale.
            assert Decimal(str(row["on_hand"])) == qty
            assert abs(Decimal(str(row["total_value"])) - value) <= MONEY_SCALE
            # ``moving_average_cost`` is the pool's average; which of the two
            # sources it is read from decides whether the money-scale rounding
            # has already been applied, so the comparison allows for it.
            average = value / qty if qty > 0 else Decimal("0")
            assert abs(Decimal(str(row["moving_average_cost"])) - average) <= MONEY_SCALE

        assert abs(valuation["total_value"] - _money(replay["remaining"])) <= MONEY_SCALE

    @given(plan=stock_plan())
    @PROPERTY
    async def test_sku_valuation_matches_the_valuation_report(
        self, db_session, plan
    ):
        """One SKU, two read paths, one number."""
        await _wipe(db_session)
        sku_id, stock = await _run_plan(db_session, plan)

        valuation = await stock.sku_valuation(sku_id)
        report = await stock.valuation_report()
        row = next(item for item in report["skus"] if item["sku_id"] == sku_id)

        assert row["sku_code"] == (await stock.get_sku_by_id(sku_id)).sku_code
        assert row["on_hand"] == valuation["on_hand"]
        assert row["moving_average_cost"] == valuation["moving_average_cost"]
        assert row["total_value"] == valuation["total_value"]
        assert report["method"] == VALUATION_METHOD == "weighted_avg"

    @given(plan=stock_plan())
    @PROPERTY
    async def test_the_valuation_report_folds_from_its_parts(
        self, db_session, plan
    ):
        await _wipe(db_session)
        sku_id, stock = await _run_plan(db_session, plan)

        report = await stock.valuation_report()
        per_sku = sum((row["total_value"] for row in report["skus"]), Decimal("0"))
        per_warehouse = sum(
            (row["total_value"] for row in report["warehouses"]), Decimal("0")
        )

        assert abs(report["total_value"] - per_sku) <= MONEY_SCALE * len(report["skus"])
        assert abs(report["total_value"] - per_warehouse) <= MONEY_SCALE * len(
            report["warehouses"]
        )
        assert report["total_value"] == _money(per_sku)

    @given(plan=stock_plan())
    @PROPERTY
    async def test_the_inventory_account_holds_the_stock_value(
        self, db_session, plan
    ):
        """``ECO_INVENTORY`` debits minus credits is the stock's value."""
        await _wipe(db_session)
        sku_id, stock = await _run_plan(db_session, plan)

        movements = await _movements(db_session, sku_id)
        replay = _replay(movements)

        valuation = await stock.sku_valuation(sku_id)
        # ``get_account_balance`` credits positive, so the inventory account
        # (an asset) shows up negative by the value it holds.
        inventory = await _account_balance(db_session, ECO_INVENTORY)
        count = len(movements)

        assert abs(-inventory - replay["remaining"]) <= MONEY_SCALE * count, (
            f"ledger {-inventory} against pool {replay['remaining']}"
        )
        assert abs(-inventory - valuation["total_value"]) <= MONEY_SCALE * count

    @given(plan=stock_plan())
    @PROPERTY
    async def test_the_cogs_account_holds_what_was_issued(
        self, db_session, plan
    ):
        """``ECO_COGS`` debits is the value that left the warehouse."""
        await _wipe(db_session)
        sku_id, stock = await _run_plan(db_session, plan)

        movements = await _movements(db_session, sku_id)

        cogs = await _account_balance(db_session, ECO_COGS)
        issued_to_cogs = sum(
            (
                Decimal(str(movement.qty)) * Decimal(str(movement.unit_cost))
                for movement in movements
                if movement.movement_type == "issue"
            ),
            Decimal("0"),
        )
        issued_qty = sum(
            (
                Decimal(str(movement.qty))
                for movement in movements
                if movement.movement_type in ("issue", "return")
            ),
            Decimal("0"),
        )
        returned = sum(
            (
                Decimal(str(movement.qty))
                * Decimal(str(movement.unit_cost))
                for movement in movements
                if movement.movement_type == "return"
            ),
            Decimal("0"),
        )

        # ``get_account_balance`` credits positive, so the expense account is
        # negative by the net cost of goods issued. The tolerance is the money
        # scale applied per unit of quantity as well as per leg: the movement
        # stores ``_money(average)`` while the journal booked
        # ``_money(average x qty)``, so a large quantity can differ from
        # ``qty x stored unit_cost`` by that scale times the quantity.
        tolerance = MONEY_SCALE * (issued_qty + len(movements))
        assert abs(-cogs - (issued_to_cogs - returned)) <= tolerance, (
            f"ledger {-cogs} against stored {issued_to_cogs - returned}"
        )

    @given(plan=stock_plan())
    @PROPERTY
    async def test_the_replay_agrees_with_the_service_implementation(
        self, db_session, plan
    ):
        """The invariant is restated here, but it must match the service."""
        await _wipe(db_session)
        sku_id, stock = await _run_plan(db_session, plan)

        movements = await _movements(db_session, sku_id)
        replay = _replay(movements)

        from services.inventory.service import _average_costs_from_movements

        implemented = _average_costs_from_movements(movements)
        for warehouse_id, (qty, value) in replay["pools"].items():
            expected = value / qty if qty > 0 else Decimal("0")
            assert implemented.get(warehouse_id, Decimal("0")) == expected


# ---------------------------------------------------------------------------
# 4. the valuation rules themselves
# ---------------------------------------------------------------------------


class TestValuationRules:
    """The moving-average rules, pinned one at a time."""

    @given(cost=_cents(1, 5000), qty=st.integers(1, 40), out=st.integers(1, 40))
    @PROPERTY
    async def test_an_outflow_leaves_the_average_unchanged(
        self, db_session, cost, qty, out
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))

        await stock.receipt(sku.id, warehouse.id, Decimal(qty), unit_cost=cost)

        costs = await stock._moving_average_costs(sku.id)
        before = costs[warehouse.id]
        assert before == cost

        if out >= qty:
            # Draining the pool re-bases it to zero; that is the next test.
            return
        await stock.issue(sku.id, warehouse.id, Decimal(out))

        costs = await stock._moving_average_costs(sku.id)
        # An outflow draws from the pool at the current average, so the
        # average itself does not move.
        assert costs[warehouse.id] == before

    async def test_an_empty_pool_rebases_on_the_next_inbound_cost(self, db_session):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))

        await stock.receipt(sku.id, warehouse.id, Decimal("10"), unit_cost=Decimal("5"))
        await stock.issue(sku.id, warehouse.id, Decimal("10"))

        costs = await stock._moving_average_costs(sku.id)
        assert costs.get(warehouse.id, Decimal("0")) == Decimal("0")

        await stock.receipt(sku.id, warehouse.id, Decimal("4"), unit_cost=Decimal("12"))
        costs = await stock._moving_average_costs(sku.id)
        assert costs[warehouse.id] == Decimal("12")

    @given(first=_cents(1, 5000), second=_cents(1, 5000), qty=st.integers(1, 40))
    @PROPERTY
    async def test_the_average_blends_receipts_not_prices(
        self, db_session, first, second, qty
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))

        await stock.receipt(sku.id, warehouse.id, Decimal(qty), unit_cost=first)
        await stock.receipt(sku.id, warehouse.id, Decimal(qty), unit_cost=second)

        costs = await stock._moving_average_costs(sku.id)
        assert costs[warehouse.id] == (first + second) / 2

    @given(cost=_cents(1, 5000), qty=st.integers(1, 40))
    @PROPERTY
    async def test_a_transfer_preserves_value_and_posts_no_batch(
        self, db_session, cost, qty
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        source = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        target = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))

        await stock.receipt(sku.id, source.id, Decimal(qty), unit_cost=cost)
        await stock.transfer(sku.id, source.id, target.id, Decimal(qty))

        movements = await _movements(db_session, sku_id=sku.id)
        entries = (
            (
                await db_session.execute(
                    select(FinJournalEntry).where(FinJournalEntry.asset == "IRR")
                )
            )
            .scalars()
            .all()
        )
        # Only the receipt booked anything: a transfer moves value within one
        # account, so a batch would debit and credit ``ECO_INVENTORY``.
        receipt_entries = [
            entry
            for entry in entries
            if entry.description and "receipt" in entry.description.lower()
        ]
        assert len(receipt_entries) == 2  # one debit, one credit
        assert len({entry.batch_id for entry in receipt_entries}) == 1
        assert len(entries) == 2

        replay = _replay(movements)
        # The value is intact: the same quantity, the same value, one
        # warehouse to the right, and the whole of it accounted for.
        assert replay["pools"][source.id] == [Decimal("0"), Decimal("0")]
        assert replay["pools"][target.id] == [Decimal(qty), qty * cost]
        assert replay["received"] == replay["issued"] + replay["remaining"]

        valuation = await stock.sku_valuation(sku.id)
        assert valuation["total_value"] == _money(qty * cost)

    @pytest.mark.parametrize("method", ["fifo", "standard", "lifo", ""])
    async def test_unimplemented_valuation_methods_are_refused(self, db_session, method):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        await stock.receipt(sku.id, warehouse.id, Decimal("5"), unit_cost=Decimal("1"))

        with pytest.raises(EcoNojinException) as raised:
            await stock.sku_valuation(sku.id, method=method)

        assert raised.value.code in {
            "INVALID_VALUATION_METHOD",
            "UNSUPPORTED_VALUATION_METHOD",
        }

    async def test_weighted_average_is_the_implemented_method(self, db_session):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        await stock.receipt(sku.id, warehouse.id, Decimal("5"), unit_cost=Decimal("1"))

        valuation = await stock.sku_valuation(sku.id)
        assert valuation["method"] == "weighted_avg"
        assert valuation["total_value"] == Decimal("5.00000000")


# ---------------------------------------------------------------------------
# 5. reservation lifecycle
# ---------------------------------------------------------------------------


@st.composite
def reservation_plan(draw):
    """A random reserve / consume / release sequence."""
    return draw(
        st.lists(
            st.tuples(
                st.integers(1, 6),
                st.sampled_from(["consume", "release", "partial"]),
            ),
            min_size=1,
            max_size=6,
        )
    )


class TestReservationLifecycle:
    """``available + reserved`` is conserved, and nothing goes negative."""

    @given(received=st.integers(1, 200), plan=reservation_plan())
    @PROPERTY
    async def test_reserve_consume_release_conserves_stock(
        self, db_session, received, plan
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))

        await stock.receipt(
            sku.id, warehouse.id, Decimal(received), unit_cost=Decimal("2")
        )
        initial = Decimal(received)
        consumed_total = Decimal("0")

        for share, action in plan:
            balance = await stock.get_balance(sku.id, warehouse.id)
            if balance.available < 1:
                continue
            qty = _share(balance.available, share)
            # Snapshot: the identity map hands the same row back after the
            # mutation, so the pre-move values have to be read as numbers
            # here or they would be the post-move ones.
            on_hand_before = Decimal(str(balance.on_hand))
            reserved_before = Decimal(str(balance.reserved))
            available_before = Decimal(str(balance.available))

            reservation = await stock.reserve_stock(
                sku.id,
                warehouse.id,
                qty,
                "order",
                _unique("order"),
                expires_at=datetime.now(UTC) + timedelta(days=365),
                created_by="prop",
            )

            after_reserve = await stock.get_balance(sku.id, warehouse.id)
            # Reserving is a hold, not a movement: the stock is still there.
            assert Decimal(str(after_reserve.on_hand)) == on_hand_before
            assert Decimal(str(after_reserve.reserved)) == reserved_before + qty
            assert Decimal(str(after_reserve.available)) == available_before - qty
            assert Decimal(str(after_reserve.available)) >= 0
            # Availability is the part of on hand that is not on hold, so the
            # two pools add back up to the physical stock that is left.
            assert Decimal(str(after_reserve.available)) + Decimal(
                str(after_reserve.reserved)
            ) == initial - consumed_total

            if action == "consume":
                await stock.consume_reservation(reservation.id, qty)
                consumed_total += qty
            elif action == "partial":
                half = (qty / 2).quantize(Decimal("1"))
                if half >= 1:
                    await stock.consume_reservation(reservation.id, half)
                    consumed_total += half
                    await stock.release_reservation(reservation.id)
            else:
                await stock.release_reservation(reservation.id)

            after = await stock.get_balance(sku.id, warehouse.id)
            on_hand_after = Decimal(str(after.on_hand))
            reserved_after = Decimal(str(after.reserved))
            available_after = Decimal(str(after.available))
            assert on_hand_after >= 0
            assert reserved_after >= 0
            assert available_after >= 0
            # A consumed quantity leaves for good; a released one comes back.
            assert on_hand_after == initial - consumed_total
            assert available_after + reserved_after == initial - consumed_total

        final = await stock.get_balance(sku.id, warehouse.id)
        final_on_hand = Decimal(str(final.on_hand))
        final_reserved = Decimal(str(final.reserved))
        assert final_on_hand == initial - consumed_total
        assert Decimal(str(final.available)) == final_on_hand - final_reserved

    @given(received=st.integers(1, 200), plan=reservation_plan())
    @PROPERTY
    async def test_reserved_equals_the_open_reservation_sum(
        self, db_session, received, plan
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        await stock.receipt(
            sku.id, warehouse.id, Decimal(received), unit_cost=Decimal("2")
        )

        for share, action in plan:
            balance = await stock.get_balance(sku.id, warehouse.id)
            if balance.available < 1:
                continue
            qty = _share(balance.available, share)
            reservation = await stock.reserve_stock(
                sku.id,
                warehouse.id,
                qty,
                "order",
                _unique("order"),
                expires_at=datetime.now(UTC) + timedelta(days=365),
                created_by="prop",
            )
            if action == "consume":
                await stock.consume_reservation(reservation.id, qty)
            elif action == "partial":
                half = (qty / 2).quantize(Decimal("1"))
                if half >= 1:
                    await stock.consume_reservation(reservation.id, half)
                    await stock.release_reservation(reservation.id)
            else:
                await stock.release_reservation(reservation.id)

            rows = (
                (
                    await db_session.execute(
                        select(InvReservation).where(
                            InvReservation.sku_id == sku.id,
                            InvReservation.status == "active",
                        )
                    )
                )
                .scalars()
                .all()
            )
            open_qty = sum(
                (Decimal(str(row.qty)) - Decimal(str(row.consumed_qty)) for row in rows),
                Decimal("0"),
            )
            balance = await stock.get_balance(sku.id, warehouse.id)
            # The balance's ``reserved`` counter is exactly the quantity the
            # open reservations still hold.
            assert balance.reserved == open_qty

    @given(received=st.integers(1, 200), extra=st.integers(1, 3))
    @PROPERTY
    async def test_a_reservation_cannot_exceed_availability(
        self, db_session, received, extra
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        await stock.receipt(
            sku.id, warehouse.id, Decimal(received), unit_cost=Decimal("2")
        )

        balance = await stock.get_balance(sku.id, warehouse.id)
        with pytest.raises(EcoNojinException) as raised:
            await stock.reserve_stock(
                sku.id,
                warehouse.id,
                balance.available + Decimal(extra),
                "order",
                _unique("order"),
                created_by="prop",
            )
        assert raised.value.code == "INSUFFICIENT_AVAILABLE_STOCK"

        # The refused reservation left the balance untouched.
        after = await stock.get_balance(sku.id, warehouse.id)
        assert after.on_hand == balance.on_hand
        assert after.reserved == balance.reserved

    @given(received=st.integers(1, 200))
    @PROPERTY
    async def test_an_expired_reservation_is_released_by_the_sweeper(
        self, db_session, received
    ):
        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        await stock.receipt(
            sku.id, warehouse.id, Decimal(received), unit_cost=Decimal("2")
        )

        balance = await stock.get_balance(sku.id, warehouse.id)
        available_before = Decimal(str(balance.available))

        # The live hold is made while the reservation is still live, then its
        # deadline elapses. Creating it already expired would let
        # ``reserve_stock``'s lazy sweep release it before the test could
        # assert anything about the sweeper itself.
        fresh = await stock.reserve_stock(
            sku.id,
            warehouse.id,
            Decimal("1"),
            "order",
            _unique("fresh-order"),
            expires_at=datetime.now(UTC) + timedelta(days=365),
            created_by="prop",
        )
        if available_before < Decimal("2"):
            # Not enough stock to hold twice; the sweeper is covered by the
            # larger ``received`` examples.
            return

        hold = _share(available_before - Decimal("1"), 2)
        expired = await stock.reserve_stock(
            sku.id,
            warehouse.id,
            hold,
            "order",
            _unique("expired-order"),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            created_by="prop",
        )
        expired.expires_at = datetime.now(UTC) - timedelta(hours=2)
        await db_session.commit()

        before = await stock.get_balance(sku.id, warehouse.id)
        # ``InvInventoryBalance.available`` is a *property* over the mutable
        # row, so "the availability before the sweep" has to be captured as a
        # number now: reading ``before.available`` after the sweep would give
        # the post-sweep value, because the sweeper mutates ``reserved`` on
        # the very same identity-mapped row.
        before_on_hand = Decimal(str(before.on_hand))
        before_reserved = Decimal(str(before.reserved))
        before_available = Decimal(str(before.available))
        assert before_reserved == hold + Decimal("1")

        released = await sweep_expired_reservations(db_session)

        assert released == 1
        assert expired.status == "expired"
        assert expired.released_at is not None
        assert fresh.status == "active"

        after = await stock.get_balance(sku.id, warehouse.id)
        after_on_hand = Decimal(str(after.on_hand))
        after_reserved = Decimal(str(after.reserved))
        after_available = Decimal(str(after.available))
        # The expired hold is back in availability; the fresh one is not.
        assert after_reserved == Decimal("1")
        assert after_available == before_available + hold
        assert after_available == after_on_hand - after_reserved
        assert after_on_hand == before_on_hand


# ---------------------------------------------------------------------------
# 6. reconciliation over a random stock history
# ---------------------------------------------------------------------------


class TestStockReconciliation:
    """What the service wrote is what the reconciliation expects to read."""

    @given(plan=reconcilable_plan())
    @PROPERTY
    async def test_a_random_stock_history_reconciles_clean(
        self, db_session, plan
    ):
        from services.finance.reconciliation import ReconciliationService

        await _wipe(db_session)
        sku_id, _ = await _run_plan(db_session, plan)

        result = await ReconciliationService(db_session).reconcile_inventory()
        assert result["overall_ok"] is True, result["discrepancies"]
        assert result["discrepancies_count"] == 0
        assert result["total_balances_checked"] >= 1

    async def test_an_unblock_is_not_phantom_drift_for_the_reconciliation(
        self, db_session
    ):
        """``unblock_stock`` restores ``on_hand`` and the reconciliation reads it.

        ``unblock_stock`` adds the quantity back to ``on_hand`` and
        ``_average_costs_from_movements`` prices the leg as inbound, so the
        signed movement sum must count it as inbound too — the mirror of the
        ``scrap`` that produced it. It used to count neither leg, so a scrap
        followed by an unblock reconciled clean at the scrap and then reported
        the whole restored quantity as ``on_hand_drift``; both the finance
        reconciliation (``ReconciliationService.reconcile_inventory``) and the
        SQL one (``StockService.reconcile_inventory``) now sum it, and a
        scrap-then-unblock round trip leaves the balance and the ledger in
        agreement with zero drift.

        This is the mirror of the finance-side regression test,
        ``services/finance/tests/test_reconcile_unblock_fix.py``: the same
        sequence against the stock service's own SQL reconciliation.
        """
        from services.finance.reconciliation import ReconciliationService

        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        service = ReconciliationService(db_session)

        await stock.receipt(
            sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1")
        )
        await stock.scrap(sku.id, warehouse.id, Decimal("10"), reason="damaged")

        assert (await service.reconcile_inventory())["overall_ok"] is True
        assert (await stock.reconcile_inventory())["overall_ok"] is True

        await stock.unblock_stock(sku.id, warehouse.id, Decimal("10"))

        # The finance reconciliation: the restored quantity is summed, so the
        # two sides agree with no drift left over.
        finance = await service.reconcile_inventory()
        assert finance["overall_ok"] is True
        assert finance["discrepancies_count"] == 0
        assert finance["discrepancies"] == []
        assert finance["total_balances_checked"] == 1

        # The stock service's own SQL reconciliation: the same, on its own
        # response shape.
        ledger = await stock.reconcile_inventory()
        assert ledger["overall_ok"] is True
        assert ledger["discrepancies_count"] == 0
        assert ledger["discrepancies"] == []
        assert ledger["total_checked"] == 1

    async def test_an_adjustment_is_phantom_drift_for_the_reconciliation(
        self, db_session
    ):
        """INTENTIONAL: ``adjust`` moves ``on_hand`` but writes an unsigned
        ``adjustment`` movement.

        Unlike the unblock case this one is documented, in
        ``reconcile_inventory``'s own docstring: ``adjustment`` movements store
        ``abs(qty)`` with the signed delta only in a free-text note, so they
        cannot be folded into the signed sum deterministically and are
        excluded. The consequence is the one pinned here — a positive
        adjustment surfaces as drift until a stocktake approves it.
        """
        from services.finance.reconciliation import ReconciliationService

        await _wipe(db_session)
        stock = StockService(db_session)
        warehouse = await stock.create_warehouse(_unique("WH"), _unique("wh"))
        sku = await stock.create_sku(_unique("SKU"), _unique("item"))
        service = ReconciliationService(db_session)

        await stock.receipt(
            sku.id, warehouse.id, Decimal("100"), unit_cost=Decimal("1")
        )
        assert (await service.reconcile_inventory())["overall_ok"] is True

        await stock.adjust(sku.id, warehouse.id, Decimal("4"), reason="found stock")

        result = await service.reconcile_inventory()
        assert result["overall_ok"] is False
        assert result["discrepancies_count"] == 1
        assert Decimal(result["discrepancies"][0]["on_hand_drift"]) == Decimal("4")
