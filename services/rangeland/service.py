from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.rangeland.models import Rangeland

logger = logging.getLogger(__name__)


class RangelandService:
    """Business logic for rangeland entities (BG-014).

    This service wraps the ORM model so routers never touch the session directly.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_rangelands(
        self,
        village_id: str | None = None,
        usage_type: str | None = None,
        condition: str | None = None,
        limit: int = 200,
    ) -> list[Rangeland]:
        stmt = select(Rangeland).limit(limit)
        if village_id:
            stmt = stmt.where(Rangeland.village_id == village_id)
        if usage_type:
            stmt = stmt.where(Rangeland.usage_type == usage_type)
        if condition:
            stmt = stmt.where(Rangeland.condition == condition)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_rangeland(self, rangeland_id: str) -> Rangeland | None:
        result = await self.db.execute(
            select(Rangeland).where(Rangeland.rangeland_id == rangeland_id)
        )
        return result.scalar_one_or_none()

    async def create_rangeland(self, **data: Any) -> Rangeland:
        # Check for duplicate rangeland_id to avoid IntegrityError
        existing = await self.get_rangeland(data.get("rangeland_id", ""))
        if existing:
            raise ValueError(f"Rangeland with id {data['rangeland_id']} already exists")
        rangeland = Rangeland(**data)
        self.db.add(rangeland)
        await self.db.commit()
        await self.db.refresh(rangeland)
        return rangeland

    async def update_rangeland(self, rangeland_id: str, data: dict) -> Rangeland | None:
        await self.db.execute(
            update(Rangeland)
            .where(Rangeland.rangeland_id == rangeland_id)
            .values(**data)
            .execution_options(synchronize_session="fetch")
        )
        await self.db.commit()
        return await self.get_rangeland(rangeland_id)

    async def delete_rangeland(self, rangeland_id: str) -> bool:
        result = await self.db.execute(
            select(Rangeland).where(Rangeland.rangeland_id == rangeland_id)
        )
        rangeland = result.scalar_one_or_none()
        if rangeland is None:
            return False
        await self.db.delete(rangeland)
        await self.db.commit()
        return True

    async def stats_for_territory(self, village_id: str) -> dict[str, Any]:
        result = await self.db.execute(
            select(func.count())
            .select_from(Rangeland)
            .where(Rangeland.village_id == village_id)
        )
        count = result.scalar_one()

        area_result = await self.db.execute(
            select(func.coalesce(func.sum(Rangeland.area_ha), Decimal("0")))
            .where(Rangeland.village_id == village_id)
        )
        total_area = area_result.scalar_one()

        prod_result = await self.db.execute(
            select(func.avg(Rangeland.productivity_index))
            .where(Rangeland.village_id == village_id, Rangeland.productivity_index.is_not(None))
        )
        avg_prod = float(prod_result.scalar_one() or 0)

        return {
            "village_id": village_id,
            "count": count,
            "total_area_ha": total_area,
            "avg_productivity_index": round(avg_prod, 2) if avg_prod else None,
            "condition_distribution": {},
            "usage_type_distribution": {},
        }
