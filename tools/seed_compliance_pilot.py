"""P9 — the D-03 pilot seed: one jurisdiction, real-shaped requirement data.

The user's execution instruction closes D-03 with a **pilot** seed: one
jurisdiction, three regulatory sources, and the requirement sets for the two
activity classes the platform actually needs first — food producers and tour
operators. The data is deliberately small and *labelled*: it is a pilot shape,
not a legal database, and the loader is idempotent (re-running it updates the
same rows by their natural keys rather than duplicating them).

Every requirement names its source and its jurisdiction, so the "which rule
applies where" question is answerable — the thing the static ``services/legal``
texts could never answer.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.base import Base
from services.compliance.models import Jurisdiction, RegulatorySource
from services.compliance.service import ComplianceService

#: The pilot jurisdiction (one country, ISO-style code).
PILOT_JURISDICTION = {
    "code": "IR",
    "name": "Iran (pilot)",
    "country": "IR",
}

#: Three regulatory sources, as the pilot's rule base.
PILOT_SOURCES = [
    {
        "key": "ir-fda",
        "name": "Iran Food and Drug Administration (pilot record)",
        "jurisdiction": "IR",
        "url": "https://www.fda.gov.ir/",
    },
    {
        "key": "ir-tourism",
        "name": "Ministry of Cultural Heritage, Tourism and Handicrafts (pilot record)",
        "jurisdiction": "IR",
        "url": "https://www.mcth.ir/",
    },
    {
        "key": "ir-environment",
        "name": "Department of Environment (pilot record)",
        "jurisdiction": "IR",
        "url": "https://www.doe.ir/",
    },
]

#: Requirement sets keyed by (source, activity code).
PILOT_REQUIREMENTS = [
    ("ir-fda", "food.producer", "Food production licence", True),
    ("ir-fda", "food.producer", "HACCP-based hygiene plan", True),
    ("ir-fda", "food.producer", "Batch traceability records", False),
    ("ir-environment", "food.producer", "Waste-water discharge permit", True),
    ("ir-tourism", "tour.operator", "Tourism licence", True),
    ("ir-tourism", "tour.operator", "Guide certification on file", True),
    ("ir-tourism", "tour.operator", "Passenger liability insurance", True),
    ("ir-environment", "tour.operator", "Protected-area entry permit", False),
]


async def seed(db) -> dict:
    """Create the pilot data (idempotent by natural keys); returns the ids."""
    service = ComplianceService(db)

    jurisdiction = (
        await db.execute(
            select(Jurisdiction).where(Jurisdiction.code == PILOT_JURISDICTION["code"])
        )
    ).scalar_one_or_none()
    if jurisdiction is None:
        jurisdiction = await service.add_jurisdiction(**PILOT_JURISDICTION)

    sources: dict[str, str] = {}
    for source in PILOT_SOURCES:
        existing = (
            await db.execute(
                select(RegulatorySource).where(
                    RegulatorySource.jurisdiction == source["jurisdiction"],
                    RegulatorySource.name == source["name"],
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = await service.add_source(
                name=source["name"],
                jurisdiction=source["jurisdiction"],
                url=source["url"],
            )
        sources[source["key"]] = str(existing.id)

    existing_requirements = await service.requirements_for(
        str(jurisdiction.id), "food.producer"
    )
    # The known set must cover BOTH activity codes, not only food — otherwise
    # every tour requirement is re-checked against the food list and skipped
    # (or, worse, duplicated) on the second run.
    tour_known = await service.requirements_for(str(jurisdiction.id), "tour.operator")
    known = {r.title for r in existing_requirements} | {r.title for r in tour_known}
    for source_key, activity_code, title, mandatory in PILOT_REQUIREMENTS:
        if title in known:
            continue
        await service.add_requirement(
            source_id=sources[source_key],
            jurisdiction_id=str(jurisdiction.id),
            activity_code=activity_code,
            title=title,
            mandatory=mandatory,
        )

    return {
        "jurisdiction_id": str(jurisdiction.id),
        "sources": sources,
        "seeded_at": datetime.now(UTC).isoformat(),
    }


async def _main() -> int:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        first = await seed(session)
        second = await seed(session)  # idempotency: no duplicates
        service = ComplianceService(session)
        food = await service.requirements_for(first["jurisdiction_id"], "food.producer")
        tours = await service.requirements_for(first["jurisdiction_id"], "tour.operator")
        print("jurisdiction:", first["jurisdiction_id"][:8], "| sources:", len(first["sources"]))
        print("food requirements:", len(food), "| tour requirements:", len(tours))
        assert len(first["sources"]) == len(second["sources"])
        assert len(food) == 4 and len(tours) == 4, (len(food), len(tours))
    await engine.dispose()
    print("pilot seed OK (idempotent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
