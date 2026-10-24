"""Repository for admin overview metrics — moves DB access out of the router."""

from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ComOrder, ContentItem, Farm, LandProfile, Product, User


class OverviewRepository:
    """Read-only access to platform overview statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def count_platform_stats(self) -> dict[str, int]:
        """Return aggregated counts for the overview dashboard."""
        results: dict[str, int] = {}

        count_stmts: list[tuple[str, object]] = [
            ("total_users", select(func.count()).select_from(User)),
            ("active_users", select(func.count()).select_from(User).where(User.is_active)),
            ("total_farms", select(func.count()).select_from(Farm)),
            ("total_land_profiles", select(func.count()).select_from(LandProfile)),
            ("total_content", select(func.count()).select_from(ContentItem)),
            ("published_content", select(func.count()).select_from(ContentItem).where(ContentItem.status == "published")),
            ("total_marketplace_products", select(func.count()).select_from(Product)),
            ("total_orders", select(func.count()).select_from(ComOrder)),
        ]

        for label, stmt in count_stmts:
            result = await self.db.execute(stmt)
            results[label] = result.scalar_one()

        return results

    async def count_requests_24h(self, hours: int) -> int | None:
        """Return total request count in the last N hours, or None if no log table."""
        try:
            result = await self.db.execute(
                text(
                    "SELECT COUNT(*) AS total "
                    "FROM api_request_log "
                    "WHERE created_at >= NOW() - make_interval(hours => :h)"
                ),
                {"h": hours},
            )
            return result.scalar_one()
        except Exception:
            return None

    async def count_successful_requests_24h(self, hours: int) -> int | None:
        """Return successful request count in the last N hours, or None if no log table."""
        try:
            result = await self.db.execute(
                text(
                    "SELECT COUNT(*) FILTER (WHERE status_code < 400) AS success "
                    "FROM api_request_log "
                    "WHERE created_at >= NOW() - make_interval(hours => :h)"
                ),
                {"h": hours},
            )
            return result.scalar_one()
        except Exception:
            return None
