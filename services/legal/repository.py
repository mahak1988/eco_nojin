"""Repository for legal texts — moves all DB access out of the router."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import LegalText


class LegalTextRepository:
    """Read and write legal texts. All DB access lives here."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        locale: str | None = None,
        slug: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LegalText]:
        stmt = select(LegalText)
        if locale:
            stmt = stmt.where(LegalText.locale == locale)
        if slug:
            stmt = stmt.where(LegalText.slug == slug)
        if status:
            stmt = stmt.where(LegalText.status == status)
        stmt = stmt.order_by(LegalText.locale, LegalText.slug, LegalText.version.desc())
        stmt = stmt.limit(limit).offset(offset)
        return self.db.execute(stmt).scalars().all()

    def list_locales(self) -> list[str]:
        stmt = select(LegalText.locale).distinct()
        return [row[0] for row in self.db.execute(stmt).all()]

    def list_slugs(self) -> list[str]:
        stmt = select(LegalText.slug).distinct()
        return [row[0] for row in self.db.execute(stmt).all()]

    def get(
        self,
        locale: str,
        slug: str,
        version: int | None = None,
    ) -> LegalText | None:
        stmt = select(LegalText).where(LegalText.locale == locale, LegalText.slug == slug)
        if version:
            stmt = stmt.where(LegalText.version == version)
        else:
            stmt = stmt.order_by(LegalText.version.desc())
        return self.db.execute(stmt).scalars().first()

    def list_versions(self, locale: str, slug: str) -> list[LegalText]:
        stmt = (
            select(LegalText)
            .where(LegalText.locale == locale, LegalText.slug == slug)
            .order_by(LegalText.version.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_latest_version(self, locale: str, slug: str) -> LegalText | None:
        stmt = (
            select(LegalText)
            .where(LegalText.locale == locale, LegalText.slug == slug)
            .order_by(LegalText.version.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def version_exists(self, locale: str, slug: str, version: int) -> bool:
        stmt = select(LegalText).where(
            LegalText.locale == locale,
            LegalText.slug == slug,
            LegalText.version == version,
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def create(self, data: dict[str, Any]) -> LegalText:
        text = LegalText(**data)
        self.db.add(text)
        self.db.commit()
        self.db.refresh(text)
        return text

    def update(self, text: LegalText, updates: dict[str, Any]) -> LegalText:
        for key, value in updates.items():
            setattr(text, key, value)
        self.db.commit()
        self.db.refresh(text)
        return text

    def delete(self, text: LegalText) -> None:
        self.db.delete(text)
        self.db.commit()
