"""P5 â€” the money plane's invariants are pinned where the code lives.

Three properties from `docs/project/PHASE_PLAN.md` P5 are proven here:

1. **KN-07 (adjustment blindness)** â€” ``reconcile_inventory`` folds
   ``adjustment`` movements into the signed on-hand sum by recovering the
   signed delta from the documented notes prefixes, so a positive and a
   negative adjustment no longer surface as identical phantom drift, and an
   unrecognised notes format still surfaces as drift instead of being
   silently agreed with;
2. **the money-write boundary** â€” no service package outside the sanctioned
   money owners writes the wallet/ledger/ecosystem balance tables. The scan is
   static (imports + gross write calls), so a new writer fails the test before
   it fails money;
3. **the reconciliation surface** stays read-only: every reconciliation method
   reads and returns; none commits.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from database.models import (
    InvInventoryBalance,
    InvSKU,
    InvStockMovement,
    InvWarehouse,
)
from services.finance.reconciliation import ReconciliationService, _signed_adjustment_delta
from tools.money_boundary import (
    scan_money_writers as _scan_money_writers,
)

pytestmark = pytest.mark.asyncio

# The repo root is three levels up: <root>/services/finance/tests/<this file>.
# ``parents[2]`` resolves to <root>/services, which made the scan target
# "<root>/services/services" -- a directory that does not exist. ``Path.rglob``
# over a missing directory yields nothing, so the boundary assertion below was
# vacuously true on every run: the guard never scanned the repo once.
# See docs/project/SECTOR-TECH-DEBT-REMEDIATION-2026-10-20.md (FR-01).
PROJECT_ROOT = Path(__file__).resolve().parents[3]

#: The tree the money-write boundary is enforced over. Asserted to exist so a
#: future path change cannot silently turn the guard back into a no-op.
SERVICES_ROOT = PROJECT_ROOT / "services"
assert SERVICES_ROOT.is_dir(), f"money-write scan root is missing: {SERVICES_ROOT}"


# --------------------------------------------------------------------------
# 1. the notes contract
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("notes", "expected"),
    [
        ("Adjustment: 5 - found stock", Decimal("5")),
        ("Adjustment: -3 - shrinkage", Decimal("-3")),
        ("Adjustment: -12.5 - stocktake correction", Decimal("-12.5")),
        ("Stocktake variance: 4", Decimal("4")),
        ("Stocktake variance: -4", Decimal("-4")),
        ("Adjustment: ", None),  # writer produced no delta
        ("Adjustment: abc - unknown", None),  # not a number
        ("something else entirely", None),  # unrecognised format
        (None, None),
    ],
)
def test_signed_adjustment_delta_recovers_only_documented_formats(notes, expected):
    assert _signed_adjustment_delta(notes) == expected


# --------------------------------------------------------------------------
# 2. reconciliation folds adjustments
# --------------------------------------------------------------------------


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def _seed_balance_with_adjustments(session, *, adjustments: list[Decimal]):
    """One SKU/warehouse, no other movements, the given adjustment set."""
    session.add(InvSKU(id=1, sku_code="SKU-1", name="Chestnut"))
    session.add(InvWarehouse(id=1, code="WH-1", name="Main"))
    session.add(InvInventoryBalance(sku_id=1, warehouse_id=1, on_hand=Decimal("0")))
    await session.flush()
    for delta in adjustments:
        session.add(
            InvStockMovement(
                movement_type="adjustment",
                sku_id=1,
                warehouse_id=1,
                qty=abs(delta),
                notes=f"Adjustment: {delta} - test", created_by="test",
            )
        )
    await session.flush()

    balance = (
        await session.execute(
            __import__("sqlalchemy").select(InvInventoryBalance).where(
                InvInventoryBalance.sku_id == 1
            )
        )
    ).scalar_one()
    balance.on_hand = sum(adjustments, Decimal("0"))
    await session.commit()
    return balance


async def test_reconciliation_folds_positive_adjustments(session):
    await _seed_balance_with_adjustments(session, adjustments=[Decimal("5"), Decimal("3")])
    result = await ReconciliationService(session).reconcile_inventory()
    assert result["overall_ok"] is True
    assert result["discrepancies_count"] == 0


async def test_reconciliation_folds_mixed_adjustments(session):
    await _seed_balance_with_adjustments(
        session, adjustments=[Decimal("10"), Decimal("-4"), Decimal("-1")]
    )
    result = await ReconciliationService(session).reconcile_inventory()
    assert result["overall_ok"] is True


async def test_unrecognised_adjustment_notes_still_surface_as_drift(session):
    """An adjustment whose direction cannot be recovered is drift, not agreement."""
    session.add(InvSKU(id=1, sku_code="SKU-1", name="Chestnut"))
    session.add(InvWarehouse(id=1, code="WH-1", name="Main"))
    session.add(InvInventoryBalance(sku_id=1, warehouse_id=1, on_hand=Decimal("7")))
    session.add(
        InvStockMovement(
            movement_type="adjustment",
            sku_id=1,
            warehouse_id=1,
            qty=Decimal("7"),
            notes="mystery note with no signed delta",
            created_by="test",
        )
    )
    await session.commit()

    result = await ReconciliationService(session).reconcile_inventory()
    assert result["overall_ok"] is False
    assert result["discrepancies_count"] == 1


# --------------------------------------------------------------------------
# 3. the money-write boundary (static scan)
# --------------------------------------------------------------------------
#
# The scanner, the table map and the write-detection live in
# ``tools/money_boundary.py`` so that this guard and ``tests/test_money_detox.py``
# cannot drift into two different boundaries.


def test_no_unauthorized_money_writer() -> None:
    offenders = _scan_money_writers(PROJECT_ROOT)
    assert offenders == {}, f"unauthorized money-table writers: {offenders}"


def test_money_write_scanner_actually_detects_an_offender(tmp_path) -> None:
    """Negative control: the scanner must FAIL on a tree that has an offender.

    Without this, a path change could turn the boundary guard back into a
    no-op that always passes -- which is exactly what happened before FR-01
    (``parents[2]`` pointed at a directory that does not exist).
    """
    rogue = tmp_path / "services" / "rogue" / "writer.py"
    rogue.parent.mkdir(parents=True)
    rogue.write_text(
        "from database.models import EcoWallet\n"
        "\n"
        "def steal(session):\n"
        "    session.add(EcoWallet(user_id='x', balance=1))\n",
        encoding="utf-8",
    )
    offenders = _scan_money_writers(tmp_path)
    assert "EcoWallet" in offenders
    assert "services.rogue" in offenders["EcoWallet"]


def test_reconciliation_methods_are_read_only() -> None:
    import inspect

    source = inspect.getsource(ReconciliationService)
    assert "commit(" not in source, "the reconciliation surface must not commit"
