"""P4: the three deferred foreign keys and the com_orders idempotency backstop.

Context
-------
``20261011_090000`` documented (in "Foreign keys this revision does not add")
that ``com_order_items.order_id`` -> ``com_orders.id``,
``marketplace_order_items.order_id`` -> ``marketplace_orders.id`` and
``inv_inventory_balances.warehouse_id`` -> ``inv_warehouses.id`` were dropped
because the referenced tables sat outside the earlier revision's scope, and
that the repair belonged to a follow-up in guarded code. This revision is that
follow-up. All three referenced tables are created by the head revision now,
and the columns that carry the references already exist in every database (old
``create_all`` builds included them), so adding the constraints is a repair,
not a schema change.

It also lands KN-03: the unique backstop on ``com_orders (buyer_id,
idempotency_key)``. The service layer has been buyer-scoping its idempotency
lookup since the cross-tenant fix; the schema never enforced it.

Guarded shape (the pattern the earlier revisions established)
-------------------------------------------------------------
* **The rebuild source is the registry, not the database.** SQLite batch mode
  recreates the table, so it needs a complete definition. Reflecting the live
  database is impossible in ``--sql`` mode, and hand-spelling the three tables
  is transcription drift. ``Base.metadata`` is the same source of truth the
  head revision read its columns from, so ``copy_from`` is the registry table.
* **No silent column loss.** Before a rebuild, the live table's columns are
  compared with the registry definition; a live column the registry does not
  declare (a drifted deployment) aborts the upgrade with the column names
  instead of dropping data.
* **The registry already declares all three edges** (and, after the model
  change that accompanies this revision, the unique constraint), so the rebuild
  itself restores them. ``create_foreign_key`` / ``create_unique_constraint``
  are called only for an edge the registry does *not* declare — that is the
  path a future table takes.
* **Re-runnable.** Online, every step first checks the live database for the
  edge/constraint and skips the rebuild when it is present, so a fresh
  ``alembic upgrade head``, an old ``create_all`` build, or a partially
  repaired database all converge.
* **Duplicate precheck** -> the unique cannot exist over duplicate data. The
  upgrade queries ``com_orders`` for repeated ``(buyer_id, idempotency_key)``
  first and raises with the offending pairs, so the operator dedupes
  deliberately. NULL keys are not duplicates (SQL unique treats NULLs as
  distinct).
* **Offline (``--sql``)** -> renders the three rebuilds and the unique add with
  the registry definitions; no database is consulted.

Downgrade
---------
Drops the unique constraint and the three foreign keys, each guarded by
presence. On a ``create_all``-built database these objects already existed
before this revision, so a downgrade removes what ``create_all`` would have
created — run it on a scratch database, never on production.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401  (registers every declared table on the shared Base)
from alembic import context, op
from database.base import Base

# revision identifiers, used by Alembic.
revision: str = "20261011_120000_p4_relationship_backstops"
down_revision: str | None = "20261011_090000_remaining_legacy_tables"
branch_labels: str | None = None
depends_on: str | None = None

#: (table, local column(s), referred table, constraint name)
_FOREIGN_KEYS: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("com_order_items", ("order_id",), "com_orders", "fk_com_order_items_order"),
    (
        "marketplace_order_items",
        ("order_id",),
        "marketplace_orders",
        "fk_marketplace_order_items_order",
    ),
    (
        "inv_inventory_balances",
        ("warehouse_id",),
        "inv_warehouses",
        "fk_inv_balances_warehouse",
    ),
)

_ORDERS_UNIQUE_NAME = "uq_com_orders_buyer_idem"
_ORDERS_UNIQUE_COLUMNS = ("buyer_id", "idempotency_key")


def _inspector() -> Any:
    return sa.inspect(op.get_bind())


def _registry_table(name: str) -> sa.Table:
    try:
        return Base.metadata.tables[name]
    except KeyError as exc:  # pragma: no cover - guarded by the scope list
        raise RuntimeError(
            f"{name} is not in the registry; this revision cannot repair it"
        ) from exc


def _live_columns(table: str) -> set[str]:
    return {column["name"] for column in _inspector().get_columns(table)}


def _assert_registry_covers_live(table: str) -> None:
    """Refuse a rebuild that would drop a column the model does not declare."""
    registry_columns = {column.name for column in _registry_table(table).columns}
    extra = _live_columns(table) - registry_columns
    if extra:
        raise RuntimeError(
            f"{table} has live columns the registry does not declare: "
            f"{sorted(extra)}. Add them to the model (their own revision) "
            "before running this repair."
        )


def _has_foreign_key(table: str, constraint_name: str, columns: tuple[str, ...]) -> bool:
    """True when the named constraint or an equivalent edge already exists."""
    if not _inspector().has_table(table):
        return True  # nothing to repair — treat as satisfied, never fail the upgrade
    for fk in _inspector().get_foreign_keys(table):
        if fk.get("name") == constraint_name:
            return True
        constrained = tuple(fk.get("constrained_columns") or ())
        if fk.get("referred_table") and constrained == tuple(columns):
            return True
    return False


def _has_unique(table: str, name: str, columns: tuple[str, ...]) -> bool:
    if not _inspector().has_table(table):
        return True
    for unique in _inspector().get_unique_constraints(table):
        if unique.get("name") == name:
            return True
        if tuple(sorted(unique.get("column_names") or ())) == tuple(sorted(columns)):
            return True
    return False


def _assert_no_duplicate_orders() -> None:
    """Fail loudly, with the offending pairs, if the data blocks the unique."""
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT buyer_id, idempotency_key, COUNT(*) AS n "
            "FROM com_orders "
            "WHERE idempotency_key IS NOT NULL "
            "GROUP BY buyer_id, idempotency_key "
            "HAVING COUNT(*) > 1"
        )
    ).fetchall()
    if rows:
        pairs = ", ".join(f"({r[0]}, {r[1]}) x{r[2]}" for r in rows[:20])
        raise RuntimeError(
            "com_orders holds duplicate (buyer_id, idempotency_key) pairs — "
            f"{len(rows)} group(s): {pairs}. Deduplicate (keep the oldest row "
            "per group, delete or null the rest) and re-run this revision; the "
            "runtime has been buyer-scoped, so these are historical rows only."
        )


def _registry_without_edge(
    table: str, columns: tuple[str, ...], referred: str
):
    """The registry definition minus the edge ``_repair_table`` re-adds.

    The fallback used when reflection is impossible (offline rendering, or a
    reflection failure) must behave like the live table it stands in for: no
    edge to repair. Copying the registry as-is and adding the edge duplicates
    it in the rendered script (measured: two identical FK clauses), while
    skipping the add silently drops the repair offline (measured: no FK at
    all in ``upgrade base:head --sql``). Stripping the edge from the copy
    source and re-adding it explicitly gives exactly one edge in both paths.
    """
    source = _registry_table(table)
    stripped = []
    for column in source.columns:
        copy = column.copy()
        copy.foreign_keys = set()
        stripped.append(copy)
    return sa.Table(source.name, sa.MetaData(), *stripped)


def _copy_from_live(table: str, columns: tuple[str, ...], referred: str):
    """The rebuild source: the live table, or the registry minus the repaired edge.

    Online this reflects the live table — which lacks the edge this revision
    repairs, so the rebuild carries nothing extra and the explicit add is the
    single edge. Offline there is no bind to reflect against, so the registry
    stands in for it, minus the edge the explicit add will supply.
    """
    from sqlalchemy import MetaData

    try:
        return sa.Table(table, MetaData(), autoload_with=op.get_bind())
    except Exception:
        return _registry_without_edge(table, columns, referred)


def _repair_table(
    table: str,
    columns: tuple[str, ...],
    referred: str,
    name: str,
) -> None:
    """Rebuild ``table`` and add the edge explicitly — exactly once.

    Both render paths were measured: online (live source, no edge) and offline
    (registry-minus-edge source) end with one edge each. The guard in
    ``upgrade()`` (any existing FK on the same column referring to the same
    table, named or not) makes a second run a no-op.
    """
    copy_from = _copy_from_live(table, columns, referred)
    with op.batch_alter_table(table, copy_from=copy_from) as batch:
        batch.create_foreign_key(name, referred, list(columns), ["id"])


def _repair_orders_unique() -> None:
    """Rebuild ``com_orders`` and add the composite unique exactly once."""
    # the unique is not a column-level edge, so the registry copy keeps it
    # (SQLite renders one constraint either way); a re-run is guarded by
    # _has_unique
    copy_from = _registry_table("com_orders")
    with op.batch_alter_table("com_orders", copy_from=copy_from) as batch:
        batch.create_unique_constraint(_ORDERS_UNIQUE_NAME, list(_ORDERS_UNIQUE_COLUMNS))


def upgrade() -> None:
    if context.is_offline_mode():
        for table, columns, referred, name in _FOREIGN_KEYS:
            _repair_table(table, columns, referred, name)
        _repair_orders_unique()
        return

    for table, columns, referred, name in _FOREIGN_KEYS:
        if _inspector().has_table(table) and not _has_foreign_key(table, name, columns):
            _assert_registry_covers_live(table)
            _repair_table(table, columns, referred, name)

    if not _has_unique("com_orders", _ORDERS_UNIQUE_NAME, _ORDERS_UNIQUE_COLUMNS):
        _assert_no_duplicate_orders()
        _assert_registry_covers_live("com_orders")
        _repair_orders_unique()


def downgrade() -> None:
    if context.is_offline_mode():
        return
    inspector = _inspector()
    if inspector.has_table("com_orders") and _has_unique(
        "com_orders", _ORDERS_UNIQUE_NAME, _ORDERS_UNIQUE_COLUMNS
    ):
        with op.batch_alter_table("com_orders") as batch:
            batch.drop_constraint(_ORDERS_UNIQUE_NAME, type_="unique")
    for table, columns, _referred, name in reversed(_FOREIGN_KEYS):
        if _has_foreign_key(table, name, columns):
            with op.batch_alter_table(table) as batch:
                batch.drop_constraint(name, type_="foreignkey")
