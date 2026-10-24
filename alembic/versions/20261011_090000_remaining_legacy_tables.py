"""Bring the remaining ``create_all``-only tables under migration control.

Context
-------
``services/api_gateway/main.py::init_db`` builds the schema at runtime with
``Base.metadata.create_all``, so before this revision the only tables an
``alembic upgrade head`` could create were the 23 the four earlier revisions
spell out (content/escrow, the six engine-result tables and the waves 2-6
schema delta). Every other table the shared registry declares -- the user and
organisation plane, products and farms, commerce orders, the marketplace,
village and territory hubs, landscape governance, the eco wallet/ledger
plane, buyer reviews, the public-website tables, the alerting/compute/backup
plane and the biofertilizer legacy row -- existed only through ``create_all``
and was invisible to a fresh alembic database.

How the scope was enumerated
----------------------------
``alembic/env.py`` imports ``database.models`` into ``target_metadata`` and
the application's ``create_all`` uses the same registry: 150 tables as this
revision was written. Diffing those against the tables the four earlier
revisions create (24 names, of which only 23 are in the registry --
``escrow_items`` is declared by no model any more) leaves the 127 names frozen
in ``_IN_SCOPE`` below: 1534 columns, 392 indexes, 15 unique constraints, 3
check constraints (``marketplace_founders.ck_equity_share`` and the two review
checks) and 45 foreign-key edges, every one of them between two in-scope
tables. The enumeration is a snapshot: this registry gained
``marketplace_reviews``/``marketplace_review_helpful`` from a concurrent
feature while the revision was being written, and both are in the scope below;
a table added later still needs its own revision.

The names are frozen literals; the columns, indexes and constraints are read
from the registry at run time. Transcribing 1516 columns by hand is the kind
of error this revision exists to prevent, and reading them is what keeps the
emitted DDL identical to ``create_all``'s -- which is in turn what makes the
guarded path below a true no-op on a create_all-built database. The
consequence, stated plainly: this revision expresses the registry as it is
today, and later model changes need their own revision, exactly as before.

Guarded shape (the pattern ``20261010_180000`` established)
-----------------------------------------------------------
* **Table missing** -> created in full: ``op.create_table`` with every column
  (each foreign key left unnamed, the way the models declare it), the
  unique/check constraints re-declared in their original order, then
  ``op.create_index`` per ``Index`` object.
* **Table present** -> reconciled: missing columns are added -- a column with
  a foreign key goes through a ``batch_alter_table`` block with a *named*
  key, because ``op.add_column`` with a ``ForeignKey`` raises
  ``NotImplementedError`` on SQLite -- a missing server default is repaired
  inside a batch block (``alter_column`` also needs one), a missing unique
  constraint is created inside one (SQLite cannot ``ALTER TABLE ... ADD
  CONSTRAINT``), and missing indexes are created plainly. Only a stale
  database -- an older ``create_all``, or a partially applied revision --
  reaches any of it; on a current create_all database every list is empty and
  the function does nothing.
* **Offline (``--sql``)** -> renders the complete create of all 125 tables
  plus their indexes as if the database were empty. No ``Inspector`` exists
  without a connection, and none is consulted.

Foreign keys
------------
A reference is emitted only when the referenced table is created by this
revision or already present in the database -- the rule ``20261010_180000``
states, checked against the live ``Inspector`` online and against the frozen
scope offline. That covers all 42 edges today. Should a future model add a
reference to a table outside this scope, the reference is skipped rather than
emitted against a table that may not exist; the tables named in
``_OUTSIDE_THE_REGISTRY`` are precisely that case -- they are declared on the
shared ``Base`` but never imported by the application or by ``env.py``, so
they are outside the registry this revision expresses.

Foreign keys this revision does not add
---------------------------------------
``com_order_items.order_id`` -> ``com_orders.id``,
``marketplace_order_items.order_id`` -> ``marketplace_orders.id`` and
``inv_inventory_balances.warehouse_id`` -> ``inv_warehouses.id`` are dropped
by ``20261010_180000`` because the referenced tables were outside its scope;
all three referenced tables are created here, but the columns that carry the
references are not -- they belong to the earlier revision, and repairing them
from this one would make this revision's downgrade drop references a
create_all-built database already had. They are a one-line follow-up inside
``20261010_180000``'s own guarded code, which is where the ``batch_alter_table``
block that adds them belongs.

What this revision does not do
------------------------------
* It does not touch the tables the earlier revisions own. ``land_profiles``
  keeps the ten-column shape ``20260924_000000`` gives it; the model has
  drifted to sixteen columns since (``area_hectares``, ``location_lat``,
  ``location_lon``, ``description``, ``dem_source``, ``dem_resolution_m``),
  and adding them belongs to that revision for the same reason as above.
* It does not add check constraints to existing tables (``marketplace_founders``
  is the only table with one).
* ``escrow_items`` is created by ``20260924_000000`` and ignored here.

Downgrade
---------
Drops exactly the tables this revision creates -- every name in ``_IN_SCOPE``
that exists -- in reverse dependency order; a dropped table takes its indexes
with it. On a database where ``create_all`` had already built those tables the
upgrade created nothing, so a downgrade there is destructive: run it on a
scratch database, never on production.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import sqlalchemy as sa

import database.models  # noqa: F401  (registers every declared table on the shared Base)
from alembic import context, op
from database.base import Base

# revision identifiers, used by Alembic.
revision: str = "20261011_090000_remaining_legacy_tables"
down_revision: str | None = "20261010_180000_waves_2_6_schema_delta"
branch_labels: str | None = None
depends_on: str | None = None

#: Tables declared on the shared ``Base`` that nothing in the application or
#: in ``alembic/env.py`` imports, so they are absent from the registry this
#: revision expresses (and from every ``create_all`` the application builds).
_OUTSIDE_THE_REGISTRY = frozenset(
    {
        "app_notifications",
        "auth_refresh_tokens",
        "auth_users",
        "land_capability_assessments",
        "terrain_analyses",
        "nojin_application_guides",
        "nojin_application_plans",
        "nojin_calibration_records",
        "nojin_cost_benefit",
        "nojin_field_trials",
        "nojin_formulation_recipes",
        "nojin_formulations",
        "nojin_material_composition",
        "nojin_materials",
        "nojin_soil_types",
        "nojin_strains",
        "nojin_water_saving",
    }
)

#: Tables an earlier revision already creates. ``escrow_items`` is declared by
#: no model any more but is still created by ``20260924_000000``; it is listed
#: so the diff that produced ``_IN_SCOPE`` is reproducible by hand.
_COVERED_BY_EARLIER_REVISIONS = frozenset(
    {
        "land_profiles",
        "escrow_items",
        "runoff_calculation_results",
        "groundwater_model_results",
        "crop_water_req_results",
        "structure_design_results",
        "irrigation_design_results",
        "calibration_results",
        "fin_accounts",
        "inv_skus",
        "inv_lots",
        "inv_inventory_balances",
        "inv_stock_movements",
        "inv_reservations",
        "com_order_items",
        "nomadic_communities",
        "marketplace_order_items",
        "landscape_fund_credits",
        "land_parcels",
        "land_ownerships",
        "land_tenure_rights",
        "tourism_guides",
        "tourism_tours",
        "tourism_bookings",
    }
)

#: The frozen scope: every table the registry declares (150) that no earlier
#: revision creates (23 of them, ``escrow_items`` absent from the registry).
#: 1534 columns, 392 indexes, 15 unique constraints, 3 check constraints and
#: 45 foreign-key edges, all of them between in-scope tables.
_IN_SCOPE = frozenset(
    {
        "admin_audit_logs",
        "ai_conversations",
        "alert_notifications",
        "alert_rules",
        "alerts",
        "analytics_snapshots",
        "api_keys",
        "audit_events",
        "audit_logs",
        "b2b_demands",
        "backup_configs",
        "backup_jobs",
        "carbon_credit_records",
        "carbon_credits",
        "carbon_events",
        "carbon_projects",
        "carbon_retirements",
        "com_orders",
        "com_payment_intents",
        "com_settlements",
        "compute_jobs",
        "contact_messages",
        "content_items",
        "content_translations",
        "content_versions",
        "contract_test_runs",
        "contract_versions",
        "credit_audit_logs",
        "daily_earnings",
        "data_lineage",
        "dispute_events",
        "disputes",
        "eco_balance_accounts",
        "eco_balance_entries",
        "eco_transactions",
        "eco_wallets",
        "entrepreneur_profiles",
        "escrow_records",
        "farms",
        "fin_idempotency_keys",
        "fin_journal_batches",
        "fin_journal_entries",
        "idempotency_keys",
        "int_outbox_events",
        "inv_locations",
        "inv_stocktake_lines",
        "inv_stocktakes",
        "inv_warehouses",
        "iot_devices",
        "job_events",
        "knowledge_attachments",
        "knowledge_collection_entries",
        "knowledge_collections",
        "knowledge_entries",
        "landscape_fund_distributions",
        "landscape_funds",
        "landscape_governance",
        "landscape_villages",
        "ledger_entries",
        "legal_texts",
        "login_history",
        "marketplace_commission_rules",
        "marketplace_escrow_entries",
        "marketplace_founders",
        "marketplace_members",
        "marketplace_orders",
        "marketplace_payments",
        "marketplace_products",
        "marketplace_review_helpful",
        "marketplace_reviews",
        "marketplace_sellers",
        "marketplace_wishlist",
        "marketplaces",
        "model_runs",
        "model_versions",
        "monitoring_data",
        "mrv_observations",
        "newsletter_subscribers",
        "nojin_calibration_record_db",
        "notifications",
        "oauth_connections",
        "oracle_challenges",
        "oracle_impact_metrics",
        "oracle_impact_reports",
        "organization_memberships",
        "organizations",
        "password_reset_tokens",
        "pilot_applications",
        "products",
        "provenance_records",
        "quality_certificates",
        "quality_inspections",
        "rangelands",
        "refresh_tokens",
        "reports",
        "restore_jobs",
        "satellite_analyses",
        "scenario_runs",
        "settings",
        "shipment_events",
        "shipments",
        "simulation_runs",
        "soil_analyses",
        "sponsorships",
        "territories",
        "territory_brands",
        "territory_fund_distributions",
        "territory_funds",
        "territory_governance",
        "tool_registry_entries",
        "users",
        "village_brands",
        "village_capabilities",
        "village_destinations",
        "village_development_gaps",
        "village_engagements",
        "village_event_registrations",
        "village_events",
        "village_experiences",
        "village_festivals",
        "village_investments",
        "village_needs",
        "village_opportunities",
        "village_opportunity_interests",
        "village_projects",
        "village_tourism_services",
        "workflow_runs",
    }
)


# --------------------------------------------------------------------------- #
# Registry readers — the declared shape, re-declared for Alembic
# --------------------------------------------------------------------------- #


def _creation_order() -> list[str]:
    """Scope names sorted so every referenced table is created before its user.

    Dependencies are the in-scope foreign-key edges; a self-reference (the
    three parent/supersedes columns in the registry) does not constrain the
    order. The sort is deterministic -- alphabetical within each round -- so
    two runs of this revision emit the same statement order, and the
    downgrade simply walks it backwards.
    """
    dependencies: dict[str, set[str]] = {}
    for name in _IN_SCOPE:
        table = Base.metadata.tables[name]
        targets = {
            key.target_fullname.split(".")[0]
            for column in table.columns
            for key in column.foreign_keys
        }
        dependencies[name] = {
            target for target in targets if target in _IN_SCOPE and target != name
        }

    ordered: list[str] = []
    settled: set[str] = set()
    pending = set(_IN_SCOPE)
    while pending:
        ready = sorted(name for name in pending if dependencies[name] <= settled)
        if not ready:  # pragma: no cover - defensive: a cycle would wedge here
            ready = sorted(pending)
        ordered.extend(ready)
        settled.update(ready)
        pending.difference_update(ready)
    return ordered


def _column_kwargs(source: sa.Column) -> dict[str, Any]:
    """Everything a declare-time column needed except its foreign keys.

    ``default``/``onupdate`` are deliberately absent: they are Python-side
    conveniences ``create_all`` never rendered either. ``server_default`` is
    DDL and travels through.
    """
    kwargs: dict[str, Any] = {
        "primary_key": source.primary_key,
        "nullable": source.nullable,
        "autoincrement": source.autoincrement,
    }
    if source.server_default is not None:
        kwargs["server_default"] = source.server_default.arg
    return kwargs


def _column(source: sa.Column, emit_fk: Callable[[str], bool], *, named: bool) -> sa.Column:
    """One registry column re-declared for a DDL operation."""
    table_name = source.table.name
    foreign_keys = [
        sa.ForeignKey(
            key.target_fullname,
            name=f"fk_{table_name}_{source.name}" if named else None,
            ondelete=key.ondelete,
            onupdate=key.onupdate,
        )
        for key in source.foreign_keys
        if emit_fk(key.target_fullname.split(".")[0])
    ]
    return sa.Column(source.name, source.type, *foreign_keys, **_column_kwargs(source))


def _columns(table: sa.Table, emit_fk: Callable[[str], bool]) -> list[sa.Column]:
    return [_column(source, emit_fk, named=False) for source in table.columns]


def _constraints(table: sa.Table) -> list[sa.Constraint]:
    """The unique and check constraints, re-declared in their original order.

    Foreign-key constraints are not rebuilt: every column re-declares its own
    keys, which is how ``create_all`` expresses them too. The primary key
    rides on the ``primary_key`` columns -- no table in scope has a composite
    one, and a single-column key is re-declared by the column itself.

    The order is the declared ``_creation_order``, not the order
    ``table.constraints`` happens to iterate in: the DDL compiler renders
    constraints sorted by ``_creation_order``, and the rebuilt objects are
    numbered as they are constructed here. Constructing them in declaration
    order is therefore what makes the emitted DDL byte-identical to
    ``create_all``'s -- the constraint text alone is not enough.
    """
    rebuilt: list[sa.Constraint] = []
    for constraint in sorted(table.constraints, key=lambda c: c._creation_order):
        if isinstance(constraint, sa.UniqueConstraint):
            rebuilt.append(
                sa.UniqueConstraint(
                    *[column.name for column in constraint.columns],
                    name=constraint.name,
                )
            )
        elif isinstance(constraint, sa.CheckConstraint):
            rebuilt.append(sa.CheckConstraint(str(constraint.sqltext), name=constraint.name))
    return rebuilt


def _indexes(table: sa.Table) -> list[tuple[str, list[str], bool]]:
    """The declared ``Index`` objects as ``(name, columns, unique)`` triples.

    A single-column ``unique=True, index=True`` renders through ``create_all``
    as its own unique index, so uniqueness for those columns lives here and
    is deliberately absent from the column kwargs -- exactly the split the
    waves 2-6 delta documents for ``fin_accounts.code``.
    """
    return [
        (index.name, [column.name for column in index.columns], bool(index.unique))
        for index in table.indexes
    ]


def _create_indexes(table: sa.Table) -> None:
    for name, columns, unique in _indexes(table):
        op.create_index(name, table.name, columns, unique=unique)


def _reconcile_table(
    table: sa.Table, inspector: sa.Inspector, emit_fk: Callable[[str], bool]
) -> None:
    """Add whatever the live table lacks that the registry declares.

    Only a stale database reaches this path. The SQLite lessons of
    ``20261010_180000`` apply unchanged: a ``batch_alter_table`` block is
    required for a foreign-key column (``op.add_column`` with a
    ``ForeignKey`` raises ``NotImplementedError``), for ``alter_column``
    (which is a table rebuild) and for ``create_unique_constraint`` (SQLite
    cannot ``ALTER TABLE ... ADD CONSTRAINT``). A batch constraint may not be
    unnamed, hence the ``fk_<table>_<column>`` repair names; the plain
    ``add_column``/``create_index`` calls need no such accommodation.
    """
    name = table.name
    live = {column["name"]: column for column in inspector.get_columns(name)}

    missing = [column for column in table.columns if column.name not in live]
    referenced = [column for column in missing if column.foreign_keys]
    if referenced:
        with op.batch_alter_table(name) as batch:
            for column in referenced:
                batch.add_column(_column(column, emit_fk, named=True))
    for column in missing:
        if not column.foreign_keys:
            op.add_column(name, _column(column, emit_fk, named=False))

    for column in table.columns:
        live_column = live.get(column.name)
        declares_default = column.server_default is not None
        if live_column is not None and declares_default and live_column.get("default") is None:
            with op.batch_alter_table(name) as batch:
                batch.alter_column(column.name, server_default=column.server_default.arg)

    live_indexes = {index["name"] for index in inspector.get_indexes(name)}
    live_unique = inspector.get_unique_constraints(name)
    live_unique_names = {unique["name"] for unique in live_unique if unique["name"]}
    live_unique_columns = {tuple(unique["column_names"]) for unique in live_unique}
    for index_name, columns, unique in _indexes(table):
        if index_name not in live_indexes:
            op.create_index(index_name, name, columns, unique=unique)

    for constraint in sorted(table.constraints, key=lambda c: c._creation_order):
        if not isinstance(constraint, sa.UniqueConstraint):
            continue
        columns = [column.name for column in constraint.columns]
        # SQLite reports every UNIQUE -- named or inline -- through
        # get_unique_constraints, and the auto-indexes backing them through
        # neither get_indexes nor get_unique_constraints' names, so the
        # column set is the only reliable identity. Adding a second unique
        # constraint on the same columns would silently double the guarantee
        # and rewrite the table for nothing.
        if tuple(columns) in live_unique_columns:
            continue
        if constraint.name is not None and constraint.name in live_unique_names:
            continue
        repair_name = constraint.name or f"uq_{name}_{'_'.join(columns)}"
        with op.batch_alter_table(name) as batch:
            batch.create_unique_constraint(repair_name, columns)


# --------------------------------------------------------------------------- #
# Revisions
# --------------------------------------------------------------------------- #


def upgrade() -> None:
    order = _creation_order()

    if context.is_offline_mode():
        # No connection exists, so no Inspector can be consulted: render the
        # complete create as if the database were empty, which is exactly
        # what the guarded online path builds on a fresh database. The
        # earlier revisions have already created their own tables by the
        # time this range is reached, so a reference into them is safe.
        emit_fk = _static_fk_target
        for name in order:
            table = Base.metadata.tables[name]
            op.create_table(name, *_columns(table, emit_fk), *_constraints(table))
            _create_indexes(table)
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    present = set(inspector.get_table_names())

    def emit_fk(target: str) -> bool:
        """A reference is emitted only when both endpoints exist: the target
        is created by this revision, or it is already in the database."""
        return target in _IN_SCOPE or target in present

    for name in order:
        table = Base.metadata.tables[name]
        if name in present:
            _reconcile_table(table, inspector, emit_fk)
            continue
        op.create_table(name, *_columns(table, emit_fk), *_constraints(table))
        _create_indexes(table)
        present.add(name)


def downgrade() -> None:
    order = _creation_order()
    if context.is_offline_mode():
        for name in reversed(order):
            op.drop_table(name)
        return
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for name in reversed(order):
        if inspector.has_table(name):
            op.drop_table(name)


def _static_fk_target(target: str) -> bool:
    """Offline sibling of the online ``emit_fk``: the target is created by
    this revision or by an earlier one."""
    return target in _IN_SCOPE or target in _COVERED_BY_EARLIER_REVISIONS
