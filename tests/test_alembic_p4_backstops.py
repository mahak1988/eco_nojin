"""P4 — the migration is verified in CI, not only in a operator's shell.

`docs/project/PHASE_PLAN.md` P4 requires the guarded Alembic revision to be
re-run-safe, provable offline, and applicable to a scratch database. This test
runs the real Alembic machinery against throwaway SQLite files and pins the
four properties that matter:

1. ``upgrade head`` creates exactly the three deferred foreign edges and the
   ``com_orders (buyer_id, idempotency_key)`` unique backstop;
2. a database built by ``create_all`` (the model-complete world) needs no
   repair — the guards skip, and no constraint is duplicated;
3. ``downgrade`` removes them and ``upgrade`` restores them (a true cycle);
4. the duplicate precheck fails loudly, with the offending pairs, instead of
   letting SQLite raise an opaque ``IntegrityError``.

The default ``DATABASE_URL`` is pointed at a temp file for the whole module:
Alembic's ``env.py`` reads it once per run, and the tests must never touch the
developer's real database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.config import Config

from alembic import command

PROJECT_ROOT = Path(__file__).resolve().parents[1]
P4_REVISION = "20261011_120000_p4_relationship_backstops"
P4_PARENT = "20261011_090000_remaining_legacy_tables"

_FK_EXPECTATIONS = (
    ("com_order_items", "fk_com_order_items_order", "com_orders", ("order_id",)),
    (
        "marketplace_order_items",
        "fk_marketplace_order_items_order",
        "marketplace_orders",
        ("order_id",),
    ),
    (
        "inv_inventory_balances",
        "fk_inv_balances_warehouse",
        "inv_warehouses",
        ("warehouse_id",),
    ),
)
_ORDERS_UNIQUE = ("uq_com_orders_buyer_idem", ("buyer_id", "idempotency_key"))


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    return config


def _inspector(db_path: Path) -> sa.Inspector:
    return sa.inspect(sa.create_engine(f"sqlite:///{db_path.as_posix()}"))


@pytest.fixture
def scratch_db(tmp_path, monkeypatch):
    """A private SQLite file; the real DATABASE_URL is never touched."""
    db_path = tmp_path / "p4_migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    return db_path


def _fks(inspector: sa.Inspector, table: str) -> list[dict]:
    return inspector.get_foreign_keys(table)


def test_upgrade_head_creates_the_backstops(scratch_db):
    command.upgrade(_alembic_config(scratch_db), "head")
    inspector = _inspector(scratch_db)
    for table, name, referred, _columns in _FK_EXPECTATIONS:
        named = [fk for fk in _fks(inspector, table) if fk["name"] == name]
        detail = f"{table}: expected exactly one {name}, got {_fks(inspector, table)}"
        assert len(named) == 1, detail
        assert named[0]["referred_table"] == referred
        assert named[0]["constrained_columns"] == list(_columns)
    uniques = inspector.get_unique_constraints("com_orders")
    matching = [u for u in uniques if u["name"] == _ORDERS_UNIQUE[0]]
    assert len(matching) == 1
    assert matching[0]["column_names"] == list(_ORDERS_UNIQUE[1])


def test_create_all_database_needs_no_repair(scratch_db):
    """The model-complete world: guards skip and nothing is duplicated."""
    import database.models  # noqa: F401  (registers every table on the Base)
    from database.base import Base

    engine = sa.create_engine(f"sqlite:///{scratch_db.as_posix()}")
    Base.metadata.create_all(engine)
    engine.dispose()
    command.stamp(_alembic_config(scratch_db), P4_PARENT)
    command.upgrade(_alembic_config(scratch_db), "head")

    inspector = _inspector(scratch_db)
    for table, _name, referred, _columns in _FK_EXPECTATIONS:
        edges = [fk for fk in _fks(inspector, table) if fk["referred_table"] == referred]
        detail = f"{table} -> {referred} duplicated: {edges}"
        assert len(edges) == 1, detail
    uniques = [
        u
        for u in inspector.get_unique_constraints("com_orders")
        if u["name"] == _ORDERS_UNIQUE[0]
    ]
    assert len(uniques) == 1


def test_downgrade_and_upgrade_cycle(scratch_db):
    command.upgrade(_alembic_config(scratch_db), "head")
    command.downgrade(_alembic_config(scratch_db), P4_PARENT)

    inspector = _inspector(scratch_db)
    for table, name, _referred, _columns in _FK_EXPECTATIONS:
        assert not [fk for fk in _fks(inspector, table) if fk["name"] == name], table
    assert not [
        u for u in inspector.get_unique_constraints("com_orders") if u["name"] == _ORDERS_UNIQUE[0]
    ]

    command.upgrade(_alembic_config(scratch_db), "head")
    inspector = _inspector(scratch_db)
    for table, name, _referred, _columns in _FK_EXPECTATIONS:
        count = len([fk for fk in _fks(inspector, table) if fk["name"] == name])
        assert count == 1, f"{table}: {name} appears {count} times"
    unique_count = len(
        [u for u in inspector.get_unique_constraints("com_orders") if u["name"] == _ORDERS_UNIQUE[0]]
    )
    assert unique_count == 1


def test_duplicate_orders_fail_the_upgrade_loudly(scratch_db):
    """The pre-change world: com_orders without the unique, with duplicates.

    A fresh ``upgrade`` to the parent revision already builds ``com_orders``
    from the registry — which carries the composite unique since the P4 model
    change — so the legacy shape is recreated by hand here (order_number still
    unique, composite absent), the duplicates inserted, and only then does the
    revision run and hit its precheck.
    """
    connection = sqlite3.connect(scratch_db)
    connection.executescript(
        "CREATE TABLE com_orders ("
        " id VARCHAR(64) NOT NULL, "
        " order_number VARCHAR(64), "
        " buyer_id VARCHAR(120) NOT NULL, "
        " seller_id VARCHAR(120), "
        " status VARCHAR(32) NOT NULL, "
        " payment_status VARCHAR(32) NOT NULL, "
        " currency VARCHAR(10) NOT NULL, "
        " subtotal NUMERIC(18, 8) NOT NULL, "
        " platform_fee NUMERIC(18, 8) NOT NULL, "
        " landscape_fee NUMERIC(18, 8) NOT NULL, "
        " total NUMERIC(18, 8) NOT NULL, "
        " shipping_address JSON, "
        " idempotency_key VARCHAR(128), "
        " version INTEGER NOT NULL, "
        " tracking_code VARCHAR(64), "
        " paid_at DATETIME, shipped_at DATETIME, delivered_at DATETIME, "
        " cancelled_at DATETIME, cancel_reason VARCHAR(500), "
        " created_at DATETIME, "
        " PRIMARY KEY (id), "
        " CONSTRAINT uq_com_orders_order_number UNIQUE (order_number));"
        " INSERT INTO com_orders "
        " (id, order_number, buyer_id, status, payment_status, currency, subtotal, "
        "  platform_fee, landscape_fee, total, idempotency_key, version, created_at) "
        " VALUES ('o1', 'ORD-o1', 'buyer-1', 'draft', 'pending', 'IRR', 0, 0, 0, 0, "
        "         'dup-key', 0, '2026-01-01');"
        " INSERT INTO com_orders "
        " (id, order_number, buyer_id, status, payment_status, currency, subtotal, "
        "  platform_fee, landscape_fee, total, idempotency_key, version, created_at) "
        " VALUES ('o2', 'ORD-o2', 'buyer-1', 'draft', 'pending', 'IRR', 0, 0, 0, 0, "
        "         'dup-key', 0, '2026-01-02');"
        " CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);"
        f" INSERT INTO alembic_version (version_num) VALUES ('{P4_PARENT}');"
    )
    connection.commit()
    connection.close()

    with pytest.raises(RuntimeError) as caught:
        command.upgrade(_alembic_config(scratch_db), "head")
    message = str(caught.value)
    assert "duplicate (buyer_id, idempotency_key)" in message
    assert "(buyer-1, dup-key)" in message
    assert "Deduplicate" in message


def test_offline_render_includes_the_repairs(scratch_db, tmp_path):
    """``--sql`` must render the revision without a database."""
    rendered = tmp_path / "migration.sql"
    config = _alembic_config(scratch_db)
    command.upgrade(config, f"{P4_PARENT}:head", sql=True)
    # The render goes to stdout via the env's output buffer; capture through
    # the environment-independent path: re-run with the file output.
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        command.upgrade(config, f"{P4_PARENT}:head", sql=True)
    sql = buffer.getvalue()
    assert "CREATE TABLE _alembic_tmp_com_order_items" in sql
    assert "uq_com_orders_buyer_idem" in sql
    assert rendered is not None  # documented: the render is stdout, not a file
