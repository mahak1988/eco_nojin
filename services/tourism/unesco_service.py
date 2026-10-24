"""UNESCO Intangible Cultural Heritage indicator service."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.tourism.models import (
    IntangibleHeritageElement,
    UnescoAssessment,
    UnescoIndicator,
)
from services.village.models import CommunitySpace, SpaceStatus


class UnescoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ═════════════════════════════════════════════════════════════
    # intangible heritage elements
    # ═════════════════════════════════════════════════════════════

    async def create_heritage_element(
        self,
        *,
        village_id: str,
        element_name: str,
        domain: str,
        created_by: str,
        element_name_en: str | None = None,
        description: str | None = None,
        threatened_level: str = "viable",
        inscription_year: int | None = None,
        safeguarding_plan: dict | None = None,
    ) -> IntangibleHeritageElement:
        """Register an intangible heritage element for a village."""
        await self._require_active_space(village_id)

        element = IntangibleHeritageElement(
            village_id=village_id,
            element_name=element_name,
            element_name_en=element_name_en,
            domain=domain,
            description=description,
            threatened_level=threatened_level,
            inscription_year=inscription_year,
            safeguarding_plan=safeguarding_plan,
        )
        self.db.add(element)
        await self.db.commit()
        await self.db.refresh(element)
        return element

    async def list_heritage_elements(
        self,
        *,
        village_id: str | None = None,
        domain: str | None = None,
        threatened_level: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IntangibleHeritageElement]:
        stmt = select(IntangibleHeritageElement)
        if village_id:
            stmt = stmt.where(IntangibleHeritageElement.village_id == village_id)
        if domain:
            stmt = stmt.where(IntangibleHeritageElement.domain == domain)
        if threatened_level:
            stmt = stmt.where(
                IntangibleHeritageElement.threatened_level == threatened_level
            )
        stmt = (
            stmt.order_by(IntangibleHeritageElement.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ═════════════════════════════════════════════════════════════
    # indicators
    # ═════════════════════════════════════════════════════════════

    async def set_indicator(
        self,
        *,
        village_id: str,
        indicator_code: str,
        indicator_name: str,
        domain: str,
        status: str,
        assessed_by: str,
        justification: str | None = None,
        safeguarding_plan: dict | None = None,
    ) -> UnescoIndicator:
        """Create or update a UNESCO indicator for a village."""
        await self._require_active_space(village_id)

        existing = await self.db.execute(
            select(UnescoIndicator).where(
                UnescoIndicator.village_id == village_id,
                UnescoIndicator.indicator_code == indicator_code,
            )
        )
        indicator = existing.scalar_one_or_none()
        now = datetime.now(UTC)

        if indicator is None:
            indicator = UnescoIndicator(
                village_id=village_id,
                indicator_code=indicator_code,
                indicator_name=indicator_name,
                domain=domain,
                status=status,
                last_assessment_at=now,
                justification=justification,
                safeguarding_plan=safeguarding_plan,
            )
            self.db.add(indicator)
        else:
            indicator.indicator_name = indicator_name
            indicator.domain = domain
            indicator.status = status
            indicator.last_assessment_at = now
            indicator.justification = justification
            indicator.safeguarding_plan = safeguarding_plan

        await self.db.commit()
        await self.db.refresh(indicator)
        return indicator

    async def list_indicators(
        self,
        *,
        village_id: str | None = None,
        domain: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UnescoIndicator]:
        stmt = select(UnescoIndicator)
        if village_id:
            stmt = stmt.where(UnescoIndicator.village_id == village_id)
        if domain:
            stmt = stmt.where(UnescoIndicator.domain == domain)
        if status:
            stmt = stmt.where(UnescoIndicator.status == status)
        stmt = (
            stmt.order_by(UnescoIndicator.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ═════════════════════════════════════════════════════════════
    # assessments
    # ═════════════════════════════════════════════════════════════

    async def create_assessment(
        self,
        *,
        village_id: str,
        indicator_code: str,
        calificatif: str,
        assessed_by: str,
        justification: str | None = None,
    ) -> UnescoAssessment:
        """Record a periodic UNESCO assessment for an indicator."""
        await self._require_active_space(village_id)

        # Ensure the indicator exists.
        indicator = await self.db.execute(
            select(UnescoIndicator).where(
                UnescoIndicator.village_id == village_id,
                UnescoIndicator.indicator_code == indicator_code,
            )
        )
        if indicator.scalar_one_or_none() is None:
            raise ValueError(
                f"indicator {indicator_code} not found for village {village_id}; "
                "create it first with set_indicator"
            )

        assessment = UnescoAssessment(
            village_id=village_id,
            indicator_code=indicator_code,
            calificatif=calificatif,
            justification=justification,
            assessed_by=assessed_by,
        )
        self.db.add(assessment)

        # Update the indicator status to match the latest assessment.
        await self.set_indicator(
            village_id=village_id,
            indicator_code=indicator_code,
            indicator_name="",  # placeholder; preserved if exists
            domain="",
            status=calificatif,
            assessed_by=assessed_by,
            justification=justification,
        )

        await self.db.commit()
        await self.db.refresh(assessment)
        return assessment

    async def list_assessments(
        self,
        *,
        village_id: str | None = None,
        indicator_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UnescoAssessment]:
        stmt = select(UnescoAssessment)
        if village_id:
            stmt = stmt.where(UnescoAssessment.village_id == village_id)
        if indicator_code:
            stmt = stmt.where(UnescoAssessment.indicator_code == indicator_code)
        stmt = (
            stmt.order_by(UnescoAssessment.assessed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ═════════════════════════════════════════════════════════════
    # dashboard
    # ═════════════════════════════════════════════════════════════

    async def unesco_dashboard(
        self,
        *,
        village_id: str | None = None,
    ) -> dict:
        """Aggregate UNESCO indicators and heritage elements."""
        stmt = select(UnescoIndicator)
        if village_id:
            stmt = stmt.where(UnescoIndicator.village_id == village_id)
        indicators = (await self.db.execute(stmt)).scalars().all()

        by_status: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        for ind in indicators:
            by_status[ind.status] = by_status.get(ind.status, 0) + 1
            by_domain[ind.domain] = by_domain.get(ind.domain, 0) + 1

        stmt2 = select(IntangibleHeritageElement)
        if village_id:
            stmt2 = stmt2.where(IntangibleHeritageElement.village_id == village_id)
        elements = (await self.db.execute(stmt2)).scalars().all()

        elements_by_level: dict[str, int] = {}
        for el in elements:
            elements_by_level[el.threatened_level] = (
                elements_by_level.get(el.threatened_level, 0) + 1
            )

        return {
            "village_id": village_id,
            "total_indicators": len(indicators),
            "indicators_by_status": by_status,
            "indicators_by_domain": by_domain,
            "total_heritage_elements": len(elements),
            "heritage_elements_by_threatened_level": elements_by_level,
        }

    # ═════════════════════════════════════════════════════════════
    # internals
    # ═════════════════════════════════════════════════════════════

    async def _require_active_space(self, village_id: str) -> CommunitySpace:
        result = await self.db.execute(
            select(CommunitySpace).where(CommunitySpace.village_id == village_id)
        )
        space = result.scalar_one_or_none()
        if space is None:
            raise ValueError(f"no governance space for village {village_id}")
        if space.status != SpaceStatus.ACTIVE.value:
            raise ValueError(
                f"village {village_id} is not governance-active "
                f"(status={space.status})"
            )
        return space
