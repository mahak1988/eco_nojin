"""Schema delta for the waves that added lots, marketplace order items,
landscape fund credits, the land registry, the rural/tribal tourism tables and
the columns this program hung on the legacy ``fin_*`` / ``inv_*`` / ``com_*`` /
nomadic tables.

Revision ID: 20261010_180000_waves_2_6_schema_delta
Revises: 20260927_010000_engine_result_tables
Create Date: 2026-10-10 18:00:00

Why this revision is guarded
----------------------------
Three revisions existed before this one and they create only the
content/escrow, sponsorships and engine-result tables. Everything else the
application declares is created at runtime by ``Base.metadata.create_all``
(``services/api_gateway/main.py::init_db``), so a database built that way
already holds this whole schema, while a database built by ``alembic upgrade``
alone holds none of it. A blind ``op.create_table`` / ``op.add_column`` is
therefore wrong in one of the two directions, and this revision reconciles
instead: inside ``upgrade()`` it reads a live ``sqlalchemy.inspect`` of the
current connection and applies only the objects that are actually missing.

* fresh, alembic-only database -- every table, column, index and constraint
  below is created;
* ``create_all``-built database -- the revision is a no-op wherever the object
  already exists, so it is safe to run over a production-shaped database and
  leaves its schema byte-identical.

That second property is the reason the new columns land at all: every one of
them belongs to a table that no revision creates, so a create-only revision
could never be applied over the databases this program actually targets.

Offline rendering
-----------------
``alembic upgrade --sql`` has no connection to inspect, so the revision takes
the one branch it can justify and renders the complete schema as if the
database were empty. The SQLite-specific ``batch_alter_table`` work is skipped
there: batch mode without a live connection has to reflect the table, and
Alembic refuses to guess rather than mis-render (its error names the
``copy_from`` escape hatch, which would have to restate ``inv_inventory_balances``
and would silently drop the foreign keys reflection preserves). Rendering still
exercises the graph, every operation call and every type mapping; the
constraint DDL itself is exercised online.

Foreign keys deliberately left unexpressed
------------------------------------------
* ``inv_lots.sku_id`` is a ``String(36)`` column holding an ``inv_skus.id``
  Integer primary key as text. PostgreSQL rejects a foreign key between
  incompatible key types, and a surrogate integer key would split the lot's
  identity, so it stays a business key exactly as
  ``database/models.py::InvLot`` documents.
* ``marketplace_order_items.order_id`` -> ``marketplace_orders.id`` and
  ``com_order_items.order_id`` -> ``com_orders.id`` reference tables this
  program did not add and no revision creates, so a fresh alembic database
  would refuse the reference.
* ``inv_inventory_balances.warehouse_id`` -> ``inv_warehouses.id`` is the one
  real foreign key dropped for that reason: ``inv_warehouses`` is a legacy
  table outside this revision.
* ``landscape_fund_credits.fund_id``/``village_id``,
  ``nomadic_communities.village_id``, ``land_parcels.village_id``,
  ``land_tenure_rights.community_id`` and the tourism ``village_id`` columns
  are cross-module business keys that carry no foreign key in the model at
  all.

The references this revision *can* express -- ``land_ownerships.parcel_id``,
``land_tenure_rights.parcel_id`` -> ``land_parcels``, ``tourism_tours.guide_id``
-> ``tourism_guides``, ``tourism_bookings.tour_id`` -> ``tourism_tours`` and
the ``*lot_uuid`` columns -> ``inv_lots`` -- are emitted, with the tables
ordered so every parent exists first. They are named ``fk_<table>_<column>``
because batch mode refuses an unnamed constraint, which keeps the reference a
created table declares and the one a rebuilt table re-declares the same object.

``fin_accounts.parent_id`` (2.5)
--------------------------------
The column was ``String(64)`` with a ``ForeignKey("fin_accounts.id")`` against
the Integer ``fin_accounts.id``. PostgreSQL rejects that constraint on its own
terms -- the key types are incompatible whatever the value looks like -- so the
defect was the foreign key, not the text.

The Integer-typed variant was tried first and rejected on evidence: rewriting
``chart_of_accounts.ensure_account`` to pass ``int(...)`` and flipping the
column to ``Integer`` fails five assertions, because the value is read back as
text.

* ``test_chart_of_accounts.py`` pins ``parent_id == str(parent.id)`` in four
  places;
* ``test_inventory_valuation_accounts.py`` pins it once more, and that file is
  outside this task's edit scope, so the assertion cannot be updated at all.

The revision therefore keeps the ``String(64)`` business key and drops only the
reference, which is the whole fix: no type migration, no data rewrite, nothing
to weaken a test to accommodate, and no ``alter column`` in either direction.
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa

from alembic import context, op

# revision identifiers
revision = "20261010_180000_waves_2_6_schema_delta"
down_revision = "20260927_010000_engine_result_tables"
branch_labels = None
depends_on = None


# --------------------------------------------------------------------------- #
# The schema, described as data
#
# A table is (name, columns, indexes, constraints, dropped_by_downgrade):
#
#   columns      (name, type, ``sa.Column`` kwargs, ForeignKey target | None)
#   indexes      (name, columns, unique, added_by_this_program)
#   constraints  (name, columns, added_by_this_program)
#
# Copied column-for-column from the declarations in ``database/models.py``
# (:class:`FinAccount`, :class:`InvSKU`, :class:`ComOrderItem`, :class:`InvLot`,
# :class:`InvInventoryBalance`, :class:`InvStockMovement`,
# :class:`InvReservation`, :class:`LandParcel`, :class:`LandOwnership`,
# :class:`LandTenureRight`), ``services/marketplace/models/__init__.py``,
# ``services/marketplace/models/village_hub.py``,
# ``services/landscape/models/__init__.py`` and
# ``services/tourism/models/__init__.py``. ``server_default`` is carried
# wherever the model declares one, because ``create_all`` emits it and an
# added column without it would be NOT NULL against a populated table.
#
# A single-column ``unique=True, index=True`` such as ``fin_accounts.code``
# renders through ``create_all`` as its own unique index, so uniqueness lives
# in the index list below and is deliberately absent from the column kwargs;
# putting it in both would create the constraint twice.
#
# ``tourism_tours.tour_type``/``difficulty`` are ``sa.Enum`` holding the
# *member names* (:data:`services.tourism.models.TourismTourType`), which is
# what SQLAlchemy's ``Enum`` persists; spelled as literals so the revision
# stays independent of the module it describes.
# --------------------------------------------------------------------------- #


_TOUR_TYPE = sa.Enum(
    "ECOTOURISM",
    "NOMADIC",
    "CULTURAL",
    "AGRO",
    "SCIENTIFIC",
    "WELLNESS",
    "ADVENTURE",
    "CULINARY",
    name="tourismtourtype",
)
_DIFFICULTY = sa.Enum(
    "EASY",
    "MODERATE",
    "CHALLENGING",
    "EXPERT",
    name="tourismdifficultylevel",
)


_TABLES: tuple[tuple[str, tuple[Any, ...], tuple[Any, ...], tuple[Any, ...], bool], ...] = (
    # ------------------------------------------------------------------ #
    # Legacy bases. The columns this program added to them are what the
    # delta path applies; the table itself only appears on a database
    # where ``create_all`` never ran.
    # ------------------------------------------------------------------ #
    (
        "fin_accounts",
        (
            ("id", sa.Integer(), {"primary_key": True}, None),
            ("code", sa.String(64), {"nullable": False}, None),
            ("name", sa.String(200), {"nullable": False}, None),
            ("type", sa.String(30), {"nullable": False}, None),
            ("asset", sa.String(10), {"nullable": False}, None),
            ("currency", sa.String(10), {"nullable": True}, None),
            ("parent_id", sa.String(64), {"nullable": True}, None),
            ("is_active", sa.Boolean(), {"nullable": False, "server_default": sa.true()}, None),
        ),
        (
            ("ix_fin_accounts_code", ("code",), True, False),
            ("ix_fin_accounts_parent_id", ("parent_id",), False, True),
        ),
        (),
        False,
    ),
    (
        "inv_skus",
        (
            ("id", sa.Integer(), {"primary_key": True}, None),
            ("sku_code", sa.String(64), {"nullable": False}, None),
            ("name", sa.String(200), {"nullable": False}, None),
            ("uom", sa.String(32), {"nullable": False}, None),
            ("category_id", sa.Integer(), {"nullable": True}, None),
            ("standard_cost", sa.Numeric(18, 8), {"nullable": True}, None),
            ("default_warehouse_id", sa.Integer(), {"nullable": True}, None),
            ("is_active", sa.Boolean(), {"nullable": False, "server_default": sa.true()}, None),
            ("is_trackable", sa.Boolean(), {"nullable": False, "server_default": sa.true()}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (("ix_inv_skus_sku_code", ("sku_code",), True, False),),
        (),
        False,
    ),
    (
        "inv_lots",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("sku_id", sa.String(36), {"nullable": False}, None),
            ("lot_number", sa.String(100), {"nullable": False}, None),
            ("expiry_date", sa.Date(), {"nullable": True}, None),
            ("received_at", sa.DateTime(timezone=True), {"nullable": False}, None),
            ("unit_cost", sa.Numeric(18, 8), {"nullable": False}, None),
            ("qty_received", sa.Numeric(18, 4), {"nullable": False}, None),
            ("qty_remaining", sa.Numeric(18, 4), {"nullable": False}, None),
            ("supplier_ref", sa.String(255), {"nullable": True}, None),
            ("status", sa.String(20), {"nullable": False}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (
            ("ix_inv_lots_sku_id", ("sku_id",), False, True),
            ("ix_inv_lots_lot_number", ("lot_number",), False, True),
            ("ix_inv_lots_sku_expiry", ("sku_id", "expiry_date"), False, True),
        ),
        (),
        True,
    ),
    (
        "inv_inventory_balances",
        (
            ("id", sa.Integer(), {"primary_key": True}, None),
            ("sku_id", sa.Integer(), {"nullable": False}, "inv_skus.id"),
            ("warehouse_id", sa.Integer(), {"nullable": False}, None),
            (
                "location_id",
                sa.Integer(),
                {"nullable": False, "server_default": sa.text("0")},
                None,
            ),
            ("lot_id", sa.Integer(), {"nullable": False, "server_default": sa.text("0")}, None),
            ("lot_uuid", sa.String(36), {"nullable": True}, "inv_lots.id"),
            ("on_hand", sa.Numeric(18, 8), {"nullable": False}, None),
            ("reserved", sa.Numeric(18, 8), {"nullable": False}, None),
            ("blocked", sa.Numeric(18, 8), {"nullable": False}, None),
            ("in_transit", sa.Numeric(18, 8), {"nullable": False}, None),
            ("last_movement_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (
            ("ix_inv_inventory_balances_sku_id", ("sku_id",), False, False),
            ("ix_inv_inventory_balances_warehouse_id", ("warehouse_id",), False, False),
        ),
        (
            (
                "uq_inv_balance_sku_wh_loc_lot",
                ("sku_id", "warehouse_id", "location_id", "lot_id"),
                True,
            ),
        ),
        False,
    ),
    (
        "inv_stock_movements",
        (
            ("id", sa.Integer(), {"primary_key": True}, None),
            ("movement_type", sa.String(32), {"nullable": False}, None),
            ("sku_id", sa.Integer(), {"nullable": False}, None),
            ("warehouse_id", sa.Integer(), {"nullable": False}, None),
            ("from_location_id", sa.Integer(), {"nullable": True}, None),
            ("to_location_id", sa.Integer(), {"nullable": True}, None),
            ("lot_id", sa.Integer(), {"nullable": True}, None),
            ("lot_uuid", sa.String(36), {"nullable": True}, "inv_lots.id"),
            ("qty", sa.Numeric(18, 8), {"nullable": False}, None),
            ("unit_cost", sa.Numeric(18, 8), {"nullable": True}, None),
            ("total_cost", sa.Numeric(18, 8), {"nullable": True}, None),
            ("reference_type", sa.String(64), {"nullable": True}, None),
            ("reference_id", sa.String(128), {"nullable": True}, None),
            ("from_warehouse_id", sa.Integer(), {"nullable": True}, None),
            ("to_warehouse_id", sa.Integer(), {"nullable": True}, None),
            ("notes", sa.String(1000), {"nullable": True}, None),
            ("created_by", sa.String(120), {"nullable": False}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (("ix_inv_stock_movements_sku_id", ("sku_id",), False, False),),
        (),
        False,
    ),
    (
        "inv_reservations",
        (
            ("id", sa.Integer(), {"primary_key": True}, None),
            ("sku_id", sa.Integer(), {"nullable": False}, None),
            ("warehouse_id", sa.Integer(), {"nullable": False}, None),
            ("location_id", sa.Integer(), {"nullable": True}, None),
            ("lot_id", sa.Integer(), {"nullable": True}, None),
            ("lot_uuid", sa.String(36), {"nullable": True}, "inv_lots.id"),
            ("qty", sa.Numeric(18, 8), {"nullable": False}, None),
            ("consumed_qty", sa.Numeric(18, 8), {"nullable": False}, None),
            ("status", sa.String(32), {"nullable": False}, None),
            ("reference_type", sa.String(64), {"nullable": False}, None),
            ("reference_id", sa.String(128), {"nullable": False}, None),
            ("reference_line_id", sa.String(128), {"nullable": True}, None),
            ("expires_at", sa.DateTime(timezone=True), {"nullable": True}, None),
            ("consumed_at", sa.DateTime(timezone=True), {"nullable": True}, None),
            ("released_at", sa.DateTime(timezone=True), {"nullable": True}, None),
            ("created_by", sa.String(120), {"nullable": False}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (("ix_inv_reservations_sku_id", ("sku_id",), False, False),),
        (),
        False,
    ),
    (
        "com_order_items",
        (
            ("id", sa.String(64), {"primary_key": True}, None),
            ("order_id", sa.String(64), {"nullable": False}, None),
            ("sku_id", sa.Integer(), {"nullable": False}, None),
            ("sku_code", sa.String(64), {"nullable": False}, None),
            ("name", sa.String(200), {"nullable": False}, None),
            ("quantity", sa.Numeric(18, 8), {"nullable": False}, None),
            ("unit_price", sa.Numeric(18, 8), {"nullable": False}, None),
            ("line_total", sa.Numeric(18, 8), {"nullable": False}, None),
            ("warehouse_id", sa.Integer(), {"nullable": False}, None),
            ("reservation_id", sa.Integer(), {"nullable": True}, None),
            (
                "fulfilled_qty",
                sa.Numeric(18, 8),
                {"nullable": False, "server_default": "0"},
                None,
            ),
        ),
        (("ix_com_order_items_order_id", ("order_id",), False, False),),
        (),
        False,
    ),
    (
        "nomadic_communities",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("village_id", sa.String(100), {"nullable": True}, None),
            ("owner_user_id", sa.String(36), {"nullable": True}, None),
            ("created_by", sa.String(36), {"nullable": True}, None),
            ("name", sa.String(200), {"nullable": False}, None),
            ("name_en", sa.String(200), {"nullable": True}, None),
            ("region", sa.String(200), {"nullable": True}, None),
            ("country", sa.String(10), {"nullable": True}, None),
            ("capacities", sa.JSON(), {"nullable": True}, None),
            ("pasture_area_ha", sa.Numeric(12, 2), {"nullable": True}, None),
            ("migration_route", sa.JSON(), {"nullable": True}, None),
            ("herd_size_estimate", sa.Integer(), {"nullable": True}, None),
            ("tourism_experience", sa.Text(), {"nullable": True}, None),
            ("has_tented_accommodation", sa.Boolean(), {"nullable": True}, None),
            ("contact_person", sa.String(200), {"nullable": True}, None),
            ("contact_phone", sa.String(50), {"nullable": True}, None),
            ("is_approved", sa.Boolean(), {"nullable": True}, None),
            ("is_active", sa.Boolean(), {"nullable": True}, None),
            ("approved_by", sa.String(36), {"nullable": True}, None),
            ("approved_at", sa.DateTime(timezone=True), {"nullable": True}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": True}, None),
            ("updated_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (
            ("idx_nomadic_region", ("region",), False, False),
            ("idx_nomadic_village", ("village_id",), False, True),
            ("idx_nomadic_owner", ("owner_user_id",), False, True),
            ("ix_nomadic_communities_village_id", ("village_id",), False, True),
            ("ix_nomadic_communities_owner_user_id", ("owner_user_id",), False, True),
        ),
        (),
        False,
    ),
    # ------------------------------------------------------------------ #
    # Tables this program added.
    # ------------------------------------------------------------------ #
    (
        "marketplace_order_items",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("order_id", sa.String(36), {"nullable": False}, None),
            ("product_id", sa.String(36), {"nullable": False}, None),
            ("seller_id", sa.String(36), {"nullable": True}, None),
            ("product_name", sa.String(300), {"nullable": False}, None),
            ("quantity", sa.Numeric(12, 2), {"nullable": False}, None),
            ("unit", sa.String(50), {"nullable": True}, None),
            ("unit_price", sa.Numeric(15, 2), {"nullable": False}, None),
            ("line_total", sa.Numeric(15, 2), {"nullable": False}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (
            ("ix_marketplace_order_items_order_id", ("order_id",), False, True),
            ("ix_marketplace_order_items_product_id", ("product_id",), False, True),
            ("ix_marketplace_order_items_seller_id", ("seller_id",), False, True),
            ("ix_marketplace_order_items_created_at", ("created_at",), False, True),
            ("idx_order_item_order", ("order_id",), False, True),
            ("idx_order_item_product", ("product_id",), False, True),
            ("idx_order_item_seller", ("seller_id",), False, True),
        ),
        (),
        True,
    ),
    (
        "landscape_fund_credits",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("fund_id", sa.String(36), {"nullable": False}, None),
            ("village_id", sa.String(100), {"nullable": False}, None),
            ("order_id", sa.String(64), {"nullable": False}, None),
            ("settlement_id", sa.String(64), {"nullable": True}, None),
            ("journal_batch_id", sa.Integer(), {"nullable": True}, None),
            ("amount", sa.Numeric(18, 2), {"nullable": False}, None),
            ("currency", sa.String(10), {"nullable": False}, None),
            ("created_at", sa.DateTime(), {"nullable": True}, None),
        ),
        (
            ("ix_landscape_fund_credits_fund_id", ("fund_id",), False, True),
            ("ix_landscape_fund_credits_village_id", ("village_id",), False, True),
            ("ix_landscape_fund_credits_order_id", ("order_id",), False, True),
            ("idx_lfc_fund", ("fund_id",), False, True),
            ("idx_lfc_village", ("village_id",), False, True),
            ("idx_lfc_order", ("order_id",), False, True),
        ),
        (),
        True,
    ),
    (
        "land_parcels",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("deed_no", sa.String(64), {"nullable": False}, None),
            ("village_id", sa.String(100), {"nullable": False}, None),
            ("name", sa.String(200), {"nullable": False}, None),
            ("area_ha", sa.Numeric(12, 2), {"nullable": False}, None),
            ("boundary", sa.JSON(), {"nullable": True}, None),
            (
                "land_use",
                sa.String(32),
                {"nullable": False, "server_default": sa.text("agricultural")},
                None,
            ),
            ("capability_class", sa.String(10), {"nullable": True}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": False}, None),
            ("updated_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (
            ("ix_land_parcels_deed_no", ("deed_no",), True, True),
            ("ix_land_parcels_village_id", ("village_id",), False, True),
            ("ix_land_parcel_village", ("village_id",), False, True),
        ),
        (),
        True,
    ),
    (
        "land_ownerships",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("parcel_id", sa.String(36), {"nullable": False}, "land_parcels.id"),
            ("owner_user_id", sa.String(120), {"nullable": False}, None),
            (
                "ownership_type",
                sa.String(32),
                {"nullable": False, "server_default": sa.text("individual")},
                None,
            ),
            ("share_pct", sa.Numeric(5, 2), {"nullable": False}, None),
            ("effective_from", sa.Date(), {"nullable": False}, None),
            ("effective_to", sa.Date(), {"nullable": True}, None),
            ("evidence_ref", sa.String(255), {"nullable": True}, None),
            (
                "is_verified",
                sa.Boolean(),
                {"nullable": False, "server_default": sa.false()},
                None,
            ),
            ("verified_by", sa.String(120), {"nullable": True}, None),
            ("verified_at", sa.DateTime(timezone=True), {"nullable": True}, None),
            ("created_at", sa.DateTime(timezone=True), {"nullable": False}, None),
        ),
        (
            ("ix_land_ownerships_parcel_id", ("parcel_id",), False, True),
            ("ix_land_ownerships_owner_user_id", ("owner_user_id",), False, True),
            ("ix_land_ownership_parcel", ("parcel_id",), False, True),
            ("ix_land_ownership_owner", ("owner_user_id",), False, True),
        ),
        (
            (
                "uq_land_ownership_parcel_owner_from",
                ("parcel_id", "owner_user_id", "effective_from"),
                True,
            ),
        ),
        True,
    ),
    (
        "land_tenure_rights",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            (
                "right_type",
                sa.String(32),
                {"nullable": False, "server_default": sa.text("grazing")},
                None,
            ),
            ("parcel_id", sa.String(36), {"nullable": False}, "land_parcels.id"),
            (
                "holder_type",
                sa.String(16),
                {"nullable": False, "server_default": sa.text("user")},
                None,
            ),
            ("holder_user_id", sa.String(120), {"nullable": True}, None),
            ("community_id", sa.String(36), {"nullable": True}, None),
            ("season_start", sa.Integer(), {"nullable": False}, None),
            ("season_end", sa.Integer(), {"nullable": False}, None),
            ("granted_by", sa.String(120), {"nullable": False}, None),
            (
                "status",
                sa.String(20),
                {"nullable": False, "server_default": sa.text("pending")},
                None,
            ),
            ("created_at", sa.DateTime(timezone=True), {"nullable": False}, None),
            ("activated_at", sa.DateTime(timezone=True), {"nullable": True}, None),
            ("closed_at", sa.DateTime(timezone=True), {"nullable": True}, None),
        ),
        (
            ("ix_land_tenure_rights_parcel_id", ("parcel_id",), False, True),
            ("ix_land_tenure_rights_holder_user_id", ("holder_user_id",), False, True),
            ("ix_land_tenure_rights_community_id", ("community_id",), False, True),
            ("ix_land_tenure_parcel", ("parcel_id",), False, True),
            ("ix_land_tenure_holder", ("holder_user_id",), False, True),
            ("ix_land_tenure_community", ("community_id",), False, True),
        ),
        (),
        True,
    ),
    (
        "tourism_guides",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("user_id", sa.String(36), {"nullable": False}, None),
            ("village_id", sa.String(100), {"nullable": False}, None),
            ("full_name", sa.String(200), {"nullable": False}, None),
            ("bio", sa.Text(), {"nullable": True}, None),
            ("languages", sa.JSON(), {"nullable": True}, None),
            ("specialties", sa.JSON(), {"nullable": True}, None),
            ("license_number", sa.String(100), {"nullable": True}, None),
            ("is_verified", sa.Boolean(), {"nullable": True}, None),
            ("insurance_provider", sa.String(200), {"nullable": True}, None),
            ("insurance_policy_number", sa.String(100), {"nullable": True}, None),
            ("insurance_expiry", sa.Date(), {"nullable": True}, None),
            ("total_tours", sa.Integer(), {"nullable": True}, None),
            ("rating", sa.Numeric(3, 2), {"nullable": True}, None),
            ("created_at", sa.DateTime(), {"nullable": True}, None),
            ("updated_at", sa.DateTime(), {"nullable": True}, None),
        ),
        (
            ("ix_tourism_guides_user_id", ("user_id",), False, True),
            ("ix_tourism_guides_village_id", ("village_id",), False, True),
        ),
        (),
        True,
    ),
    (
        "tourism_tours",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("guide_id", sa.String(36), {"nullable": False}, "tourism_guides.id"),
            ("village_id", sa.String(100), {"nullable": False}, None),
            ("title", sa.String(300), {"nullable": False}, None),
            ("slug", sa.String(300), {"nullable": False}, None),
            ("description", sa.Text(), {"nullable": True}, None),
            ("tour_type", _TOUR_TYPE, {"nullable": False}, None),
            ("duration_hours", sa.Integer(), {"nullable": False}, None),
            ("max_participants", sa.Integer(), {"nullable": True}, None),
            ("min_participants", sa.Integer(), {"nullable": True}, None),
            ("difficulty", _DIFFICULTY, {"nullable": True}, None),
            ("price_per_person", sa.Numeric(12, 2), {"nullable": False}, None),
            ("currency", sa.String(3), {"nullable": True}, None),
            ("includes", sa.JSON(), {"nullable": True}, None),
            ("excludes", sa.JSON(), {"nullable": True}, None),
            ("itinerary", sa.JSON(), {"nullable": True}, None),
            ("meeting_point", sa.JSON(), {"nullable": True}, None),
            ("images", sa.JSON(), {"nullable": True}, None),
            ("safety_equipment", sa.JSON(), {"nullable": True}, None),
            ("ecological_capacity", sa.Integer(), {"nullable": True}, None),
            ("current_bookings", sa.Integer(), {"nullable": True}, None),
            ("status", sa.String(20), {"nullable": True}, None),
            ("is_regenerative", sa.Boolean(), {"nullable": True}, None),
            ("regenerative_activity", sa.Text(), {"nullable": True}, None),
            ("approved_by", sa.String(36), {"nullable": True}, None),
            ("approved_at", sa.DateTime(), {"nullable": True}, None),
            ("total_bookings", sa.Integer(), {"nullable": True}, None),
            ("rating", sa.Numeric(3, 2), {"nullable": True}, None),
            ("created_at", sa.DateTime(), {"nullable": True}, None),
            ("updated_at", sa.DateTime(), {"nullable": True}, None),
        ),
        (
            ("ix_tourism_tours_tour_type", ("tour_type",), False, True),
            ("ix_tourism_tours_slug", ("slug",), True, True),
            ("ix_tourism_tours_status", ("status",), False, True),
            ("ix_tourism_tours_village_id", ("village_id",), False, True),
            ("ix_tourism_tours_created_at", ("created_at",), False, True),
            ("idx_tour_village", ("village_id",), False, True),
            ("idx_tour_type", ("tour_type",), False, True),
            ("idx_tour_status", ("status",), False, True),
        ),
        (),
        True,
    ),
    (
        "tourism_bookings",
        (
            ("id", sa.String(36), {"primary_key": True}, None),
            ("booking_number", sa.String(50), {"nullable": False}, None),
            ("tour_id", sa.String(36), {"nullable": False}, "tourism_tours.id"),
            ("guest_id", sa.String(36), {"nullable": False}, None),
            ("village_id", sa.String(100), {"nullable": False}, None),
            ("participants_count", sa.Integer(), {"nullable": False}, None),
            ("tour_date", sa.DateTime(), {"nullable": False}, None),
            ("special_requests", sa.Text(), {"nullable": True}, None),
            ("subtotal", sa.Numeric(15, 2), {"nullable": False}, None),
            ("platform_fee", sa.Numeric(15, 2), {"nullable": True}, None),
            ("landscape_fee", sa.Numeric(15, 2), {"nullable": True}, None),
            ("insurance_fee", sa.Numeric(15, 2), {"nullable": True}, None),
            ("total", sa.Numeric(15, 2), {"nullable": False}, None),
            ("currency", sa.String(3), {"nullable": True}, None),
            ("status", sa.String(20), {"nullable": True}, None),
            ("payment_status", sa.String(20), {"nullable": True}, None),
            ("insurance_provider", sa.String(200), {"nullable": True}, None),
            ("insurance_policy_number", sa.String(100), {"nullable": True}, None),
            ("blockchain_tx_hash", sa.String(100), {"nullable": True}, None),
            ("settlement_status", sa.String(20), {"nullable": True}, None),
            ("regenerative_commitment", sa.Text(), {"nullable": True}, None),
            ("regenerative_completed", sa.Boolean(), {"nullable": True}, None),
            ("created_at", sa.DateTime(), {"nullable": True}, None),
            ("updated_at", sa.DateTime(), {"nullable": True}, None),
        ),
        (
            ("ix_tourism_bookings_booking_number", ("booking_number",), True, True),
            ("ix_tourism_bookings_guest_id", ("guest_id",), False, True),
            ("ix_tourism_bookings_village_id", ("village_id",), False, True),
            ("ix_tourism_bookings_status", ("status",), False, True),
            ("ix_tourism_bookings_created_at", ("created_at",), False, True),
            ("idx_booking_tour", ("tour_id",), False, True),
            ("idx_booking_guest", ("guest_id",), False, True),
            ("idx_booking_status", ("status",), False, True),
        ),
        (),
        True,
    ),
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

#: Every table spec keyed by table name, so the repair helpers do not have to
#: search the tuple.
_SPECS: dict[str, tuple[Any, ...]] = {spec[0]: spec for spec in _TABLES}


def _column(spec: tuple[Any, ...], table: str) -> sa.Column:
    """One ``sa.Column`` built from a ``(name, type, kwargs, foreign key)`` spec.

    The foreign key is named because batch mode demands it: ``add_column``
    renders a bare reference that SQLite's ``ALTER TABLE`` cannot execute, and
    even batch mode refuses an unnamed constraint. Naming it also keeps the
    inline definition in a created table and the reference in a rebuilt one
    byte-identical, so a downgrade followed by an upgrade lands on the same
    schema.
    """
    name, type_, kwargs, foreign_key = spec
    if foreign_key is None:
        return sa.Column(name, type_, **kwargs)
    return sa.Column(name, type_, sa.ForeignKey(foreign_key, name=f"fk_{table}_{name}"), **kwargs)


def _create_table(name: str, spec: tuple[Any, ...]) -> None:
    """Create ``name`` whole, including its inline unique constraints."""
    _, columns, _indexes, constraints, _dropped = spec
    unique = [
        sa.UniqueConstraint(*constraint_columns, name=constraint_name)
        for constraint_name, constraint_columns, _added in constraints
    ]
    op.create_table(name, *[_column(column, name) for column in columns], *unique)


def _create_indexes(
    name: str,
    indexes: tuple[Any, ...],
    *,
    only_added: bool,
    present: frozenset[str] = frozenset(),
) -> None:
    """Create ``name``'s indexes.

    ``only_added`` restricts the call to the indexes this program introduced
    and skips any the database already has; the create path passes ``False`` so
    a freshly created table still gets the indexes that predate it.
    """
    for index_name, index_columns, unique, added in indexes:
        if only_added and (not added or index_name in present):
            continue
        op.create_index(index_name, name, list(index_columns), unique=unique)


def _inspector() -> Any:
    """The live inspector for the current connection."""
    return sa.inspect(op.get_bind())


def _index_names(inspector: Any, name: str) -> frozenset[str]:
    """The index names the database already has on ``name``."""
    return frozenset(index["name"] for index in inspector.get_indexes(name))


# --------------------------------------------------------------------------- #
# The columns this program added to tables that already existed.

# ``upgrade`` adds whatever the models declare and the database lacks;
# ``downgrade`` may remove only these, because the rest of each column list
# belongs to the legacy ``create_all`` schema that predates this program.
# --------------------------------------------------------------------------- #

_ADDED_COLUMNS: dict[str, frozenset[str]] = {
    "fin_accounts": frozenset({"parent_id", "is_active"}),
    "inv_skus": frozenset({"is_active", "is_trackable"}),
    "com_order_items": frozenset({"fulfilled_qty"}),
    "nomadic_communities": frozenset(
        {
            "village_id",
            "owner_user_id",
            "created_by",
            "pasture_area_ha",
            "migration_route",
            "herd_size_estimate",
            "approved_by",
            "approved_at",
        }
    ),
    "inv_inventory_balances": frozenset({"lot_uuid"}),
    "inv_stock_movements": frozenset({"lot_uuid"}),
    "inv_reservations": frozenset({"lot_uuid"}),
}


def _repair_table(name: str, inspector: Any, referenced: tuple[Any, ...]) -> None:
    """Add what the delta path cannot express outside batch mode.

    SQLite has no ``ALTER TABLE ... ADD CONSTRAINT``, so a reference on an
    added column, the ``uq_inv_balance_sku_wh_loc_lot`` constraint and the
    ``server_default=text("0")`` on ``location_id``/``lot_id`` all need the
    copy-and-move batch strategy. They share one block so a table is rebuilt
    once, and the whole block is skipped when there is nothing to add — which
    is what makes the revision a no-op over a current ``create_all`` database.

    The ``server_default`` repair matters for a database built by an older
    ``create_all`` that emitted ``location_id`` and ``lot_id`` without one: the
    columns are NOT NULL, so they cannot be added to a populated table without
    something to fall back on.
    """
    spec = _SPECS[name]
    columns = {column["name"]: column for column in inspector.get_columns(name)}
    defaults = [
        (column_name, kwargs["server_default"])
        for column_name, _type, kwargs, _foreign_key in spec[1]
        if "server_default" in kwargs and columns.get(column_name, {}).get("default") is None
    ]
    constraints = {c["name"] for c in inspector.get_unique_constraints(name)}
    missing = [
        (constraint_name, list(constraint_columns))
        for constraint_name, constraint_columns, added in spec[3]
        if added and constraint_name not in constraints
    ]
    if not referenced and not defaults and not missing:
        return
    with op.batch_alter_table(name) as batch:
        for column in referenced:
            batch.add_column(_column(column, name))
        for column_name, server_default in defaults:
            batch.alter_column(column_name, server_default=server_default)
        for constraint_name, constraint_columns in missing:
            batch.create_unique_constraint(constraint_name, constraint_columns)


def _unrepair_table(name: str, inspector: Any) -> None:
    """Put the legacy tables back the way they were before this revision.

    The added columns, the indexes that reference them, the
    ``uq_inv_balance_sku_wh_loc_lot`` constraint and the ``server_default`` on
    ``location_id``/``lot_id`` all have to come off in one table rebuild, and
    the rebuild has to be handed the table's definition explicitly: batch mode
    reflects by default, and the reflected foreign key on a column being
    dropped survives the rebuild, so the data copy inserts a column the new
    table no longer has and SQLite rejects the whole statement. Spelling the
    table out lets the doomed column keep its placeholder while dropping its
    foreign key, and it is where the ``server_default`` this revision lifted
    off ``location_id`` and ``lot_id`` is put back.

    Every column that carries a ``server_default`` is either dropped here or is
    one of those two, so none of the surviving ones keep a default.
    """
    present_columns = {column["name"] for column in inspector.get_columns(name)}
    dropped = _ADDED_COLUMNS.get(name, frozenset()) & present_columns
    if not dropped:
        return

    spec = _SPECS[name]
    foreign_keys: dict[str, list[str]] = {}
    for foreign_key in inspector.get_foreign_keys(name):
        if set(foreign_key["constrained_columns"]) & dropped:
            continue
        for position, column in enumerate(foreign_key["constrained_columns"]):
            foreign_keys.setdefault(column, []).append(
                f"{foreign_key['referred_table']}.{foreign_key['referred_columns'][position]}"
            )
    columns = [
        sa.Column(
            column[0],
            column[1],
            *(
                sa.ForeignKey(target, name=f"fk_{name}_{column[0]}")
                for target in foreign_keys.get(column[0], ())
            ),
            **{key: value for key, value in column[2].items() if key != "server_default"},
        )
        for column in spec[1]
        if column[0] in present_columns
    ]
    primary = [c[0] for c in spec[1] if c[2].get("primary_key")]
    indexes = [
        sa.Index(index_name, *index_columns, unique=unique)
        for index_name, index_columns, unique, _added in spec[2]
        if not set(index_columns) & dropped
    ]
    constraints = [
        sa.UniqueConstraint(*constraint_columns, name=constraint_name)
        for constraint_name, constraint_columns, added in spec[3]
        if not added
    ]
    table = sa.Table(name, sa.MetaData(), *columns, *indexes, *constraints)
    table.append_constraint(sa.PrimaryKeyConstraint(*primary))
    with op.batch_alter_table(name, copy_from=table) as batch:
        for column_name in sorted(dropped):
            batch.drop_column(column_name)


# --------------------------------------------------------------------------- #
# Migration
# --------------------------------------------------------------------------- #


def upgrade() -> None:
    """Guarded schema delta — see the module docstring."""
    if context.is_offline_mode():
        for spec in _TABLES:
            name = spec[0]
            _create_table(name, spec)
            _create_indexes(name, spec[2], only_added=False)
        return

    inspector = _inspector()
    for spec in _TABLES:
        name, columns, indexes, _constraints, _dropped = spec
        if not inspector.has_table(name):
            _create_table(name, spec)
            _create_indexes(name, indexes, only_added=False)
            continue

        present_columns = {column["name"] for column in inspector.get_columns(name)}
        missing = [column for column in columns if column[0] not in present_columns]
        for column in missing:
            if column[3] is None:
                op.add_column(name, _column(column, name))
        _create_indexes(name, indexes, only_added=True, present=_index_names(inspector, name))
        _repair_table(name, inspector, referenced=tuple(c for c in missing if c[3] is not None))


def downgrade() -> None:
    """Reverse exactly what this revision created.

    The tables this program added are dropped. The legacy bases are left in
    place — ``create_all`` built them long before this revision, and dropping
    them would delete data the upgrade never owned — so only the added columns,
    the indexes that reference them and the constraint come back off them.
    """
    if context.is_offline_mode():
        # Batch mode cannot render without a live connection; see upgrade().
        return

    inspector = _inspector()
    for spec in reversed(_TABLES):
        name = spec[0]
        if not inspector.has_table(name):
            continue
        if spec[4]:
            # Its indexes and constraints die with the table.
            op.drop_table(name)
            continue
        _unrepair_table(name, inspector)

