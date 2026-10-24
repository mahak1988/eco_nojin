"""P10: ecotourism festivals, editions, bookings, UNESCO indicators and assessments.

Creates the tables needed to run village festivals and track UNESCO
Intangible Cultural Heritage indicators. Guarded and idempotent: each table
is created only when absent so the revision coexists with create_all and can
be re-run on migrated databases.
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "20261017_110000_p10_tourism_festivals_unesco"
down_revision: str | None = "20261017_100000_p7_published_fields_json"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(name: str) -> bool:
    if context.is_offline_mode():
        return False
    inspector = sa.inspect(op.get_bind())
    return inspector.has_table(name)


def upgrade() -> None:
    if context.is_offline_mode():
        return

    if not _table_exists("tourism_festivals"):
        op.create_table(
            "tourism_festivals",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "village_id",
                sa.String(100),
                sa.ForeignKey("gov_community_spaces.village_id"),
                nullable=False,
                index=True,
            ),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("name_en", sa.String(200), nullable=True),
            sa.Column("festival_type", sa.String(50), nullable=False),
            sa.Column("season", sa.String(20), nullable=False),
            sa.Column("start_date", sa.Date, nullable=False),
            sa.Column("end_date", sa.Date, nullable=False),
            sa.Column("recurrence", sa.String(20), default="annual", nullable=False),
            sa.Column("capacity", sa.Integer, nullable=False),
            sa.Column("base_ticket_price", sa.Numeric(12, 2), nullable=False),
            sa.Column("landscape_fee_bps", sa.Integer, default=200, nullable=False),
            sa.Column("is_regenerative", sa.Boolean, default=False, nullable=False),
            sa.Column("status", sa.String(20), default="planned", nullable=False),
            sa.Column("created_by", sa.String(36), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime,
                default=lambda: sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("idx_festival_village", "tourism_festivals", ["village_id"])
        op.create_index("idx_festival_season", "tourism_festivals", ["season"])
        op.create_index("idx_festival_status", "tourism_festivals", ["status"])

    if not _table_exists("festival_editions"):
        op.create_table(
            "festival_editions",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "festival_id",
                sa.String(36),
                sa.ForeignKey("tourism_festivals.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("year", sa.Integer, nullable=False),
            sa.Column("total_seats", sa.Integer, nullable=False),
            sa.Column("seats_available", sa.Integer, nullable=False),
            sa.Column("total_revenue", sa.Numeric(14, 2), default="0"),
            sa.Column("landscape_fees", sa.Numeric(14, 2), default="0"),
            sa.Column("started_at", sa.DateTime, nullable=True),
            sa.Column("completed_at", sa.DateTime, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime,
                default=lambda: sa.func.now(),
                nullable=False,
            ),
        )
        # SQLite: UNIQUE constraint requires batch_alter_table
        bind = op.get_bind()
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("festival_editions") as batch_op:
                batch_op.create_unique_constraint(
                    "uq_festival_edition_year", ["festival_id", "year"]
                )
        else:
            op.create_unique_constraint(
                "uq_festival_edition_year", "festival_editions", ["festival_id", "year"]
            )
        op.create_index("idx_edition_year", "festival_editions", ["year"])

    if not _table_exists("festival_bookings"):
        op.create_table(
            "festival_bookings",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "festival_id",
                sa.String(36),
                sa.ForeignKey("tourism_festivals.id"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "edition_id",
                sa.String(36),
                sa.ForeignKey("festival_editions.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("guest_id", sa.String(36), nullable=False, index=True),
            sa.Column("participants_count", sa.Integer, nullable=False),
            sa.Column("ticket_price", sa.Numeric(12, 2), nullable=False),
            sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
            sa.Column("platform_fee", sa.Numeric(14, 2), default="0"),
            sa.Column("landscape_fee", sa.Numeric(14, 2), default="0"),
            sa.Column("total", sa.Numeric(14, 2), nullable=False),
            sa.Column("status", sa.String(20), default="pending", nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime,
                default=lambda: sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("idx_festival_booking_guest", "festival_bookings", ["guest_id"])
        op.create_index(
            "idx_festival_booking_status", "festival_bookings", ["status"]
        )

    if not _table_exists("intangible_heritage_elements"):
        op.create_table(
            "intangible_heritage_elements",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("village_id", sa.String(100), nullable=False, index=True),
            sa.Column("element_name", sa.String(200), nullable=False),
            sa.Column("element_name_en", sa.String(200), nullable=True),
            sa.Column("domain", sa.String(50), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("threatened_level", sa.String(30), default="viable", nullable=False),
            sa.Column("inscription_year", sa.Integer, nullable=True),
            sa.Column("safeguarding_plan", sa.JSON, nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime,
                default=lambda: sa.func.now(),
                onupdate=lambda: sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index("idx_ihe_village", "intangible_heritage_elements", ["village_id"])
        op.create_index(
            "idx_ihe_domain", "intangible_heritage_elements", ["domain"]
        )
        op.create_index(
            "idx_ihe_status", "intangible_heritage_elements", ["threatened_level"]
        )

    if not _table_exists("unesco_indicators"):
        op.create_table(
            "unesco_indicators",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("village_id", sa.String(100), nullable=False, index=True),
            sa.Column("indicator_code", sa.String(20), nullable=False),
            sa.Column("indicator_name", sa.String(200), nullable=False),
            sa.Column("domain", sa.String(50), nullable=False),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("last_assessment_at", sa.DateTime, nullable=True),
            sa.Column("justification", sa.Text, nullable=True),
            sa.Column("safeguarding_plan", sa.JSON, nullable=True),
            sa.Column(
                "updated_at",
                sa.DateTime,
                default=lambda: sa.func.now(),
                onupdate=lambda: sa.func.now(),
                nullable=False,
            ),
        )
        # SQLite: UNIQUE constraint requires batch_alter_table
        bind = op.get_bind()
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("unesco_indicators") as batch_op:
                batch_op.create_unique_constraint(
                    "uq_unesco_village_indicator", ["village_id", "indicator_code"]
                )
        else:
            op.create_unique_constraint(
                "uq_unesco_village_indicator",
                "unesco_indicators",
                ["village_id", "indicator_code"],
            )
        op.create_index("idx_unesco_village", "unesco_indicators", ["village_id"])
        op.create_index("idx_unesco_status", "unesco_indicators", ["status"])

    if not _table_exists("unesco_assessments"):
        op.create_table(
            "unesco_assessments",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("village_id", sa.String(100), nullable=False, index=True),
            sa.Column("indicator_code", sa.String(20), nullable=False),
            sa.Column("calificatif", sa.String(30), nullable=False),
            sa.Column("justification", sa.Text, nullable=True),
            sa.Column("assessed_by", sa.String(36), nullable=False),
            sa.Column(
                "assessed_at",
                sa.DateTime,
                default=lambda: sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index(
            "idx_assessment_village", "unesco_assessments", ["village_id"]
        )
        op.create_index(
            "idx_assessment_indicator", "unesco_assessments", ["indicator_code"]
        )


def downgrade() -> None:
    # Tables are not dropped on purpose: festival data and UNESCO assessments
    # are operational records. Dropping would lose audit history.
    pass
