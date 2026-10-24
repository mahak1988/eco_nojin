"""Service for legal texts — business logic layer."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from database.models import LegalText
from services.legal.repository import LegalTextRepository

VALID_SLUGS = {
    "terms",
    "privacy",
    "cookies",
    "ecommerce_rules",
    "buy_sell_rules",
    "marketplace_rules",
    "vendor_agreement",
    "data_processing_addendum",
}


class LegalTextService:
    """Business logic for legal texts — delegates DB to the repository."""

    def __init__(self, db: Session):
        self.repo = LegalTextRepository(db)

    @staticmethod
    def validate_slug(slug: str) -> str:
        if slug not in VALID_SLUGS:
            raise ValueError(f"Invalid slug '{slug}'. Valid: {', '.join(sorted(VALID_SLUGS))}")
        return slug

    def list(
        self,
        locale: str | None = None,
        slug: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        if slug:
            self.validate_slug(slug)
        texts = self.repo.list(locale, slug, status, limit, offset)
        return [self._to_response(t) for t in texts]

    def list_locales(self) -> list[str]:
        return self.repo.list_locales()

    def list_slugs(self) -> list[str]:
        return self.repo.list_slugs()

    def get(
        self,
        locale: str,
        slug: str,
        version: int | None = None,
    ) -> dict:
        self.validate_slug(slug)
        text = self.repo.get(locale, slug, version)
        if not text:
            raise LookupError(f"Legal text not found: locale={locale}, slug={slug}")
        return self._to_response(text)

    def list_versions(self, locale: str, slug: str) -> list[dict]:
        self.validate_slug(slug)
        texts = self.repo.list_versions(locale, slug)
        if not texts:
            raise LookupError(f"Legal text not found: locale={locale}, slug={slug}")
        return [
            {
                "version": t.version,
                "status": t.status,
                "effective_at": t.effective_at.isoformat() if t.effective_at else None,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None,
            }
            for t in texts
        ]

    def create(self, payload: dict[str, Any]) -> dict:
        locale = payload.get("locale")
        slug = payload.get("slug")
        # Only the *slug* comes from the fixed content vocabulary. The locale
        # is a separate vocabulary (the locales present in the registry), so
        # validating it with the slug validator rejected every create with
        # "Invalid slug 'fa'".
        if not locale:
            raise ValueError("locale is required")
        self.validate_slug(slug)

        version = payload.get("version")
        if version is None:
            existing = self.repo.get_latest_version(locale, slug)
            version = (existing.version + 1) if existing else 1
        else:
            if self.repo.version_exists(locale, slug, version):
                raise ValueError(
                    f"Legal text version {version} already exists for locale={locale}, slug={slug}"
                )

        data = {
            "locale": locale,
            "slug": slug,
            "title": payload["title"],
            "body": payload["body"],
            "version": version,
            "status": payload.get("status", "draft"),
            "effective_at": payload.get("effective_at"),
        }
        text = self.repo.create(data)
        return self._to_response(text)

    def update(
        self,
        locale: str,
        slug: str,
        version: int,
        payload: dict[str, Any],
    ) -> dict:
        self.validate_slug(slug)
        text = self.repo.get(locale, slug, version)
        if not text:
            raise LookupError(f"Legal text not found: locale={locale}, slug={slug}, version={version}")

        updates: dict[str, Any] = {}
        if payload.get("title") is not None:
            updates["title"] = payload["title"]
        if payload.get("body") is not None:
            updates["body"] = payload["body"]
        if payload.get("status") is not None:
            updates["status"] = payload["status"]
        if payload.get("effective_at") is not None:
            from datetime import datetime
            updates["effective_at"] = datetime.fromisoformat(payload["effective_at"])

        text = self.repo.update(text, updates)
        return self._to_response(text)

    def remove(self, locale: str, slug: str, version: int) -> dict[str, Any]:
        self.validate_slug(slug)
        text = self.repo.get(locale, slug, version)
        if not text:
            raise LookupError(f"Legal text not found: locale={locale}, slug={slug}, version={version}")
        self.repo.delete(text)
        return {"deleted": True, "locale": locale, "slug": slug, "version": version}

    @staticmethod
    def _to_response(text: LegalText) -> dict:
        return {
            "id": text.id,
            "locale": text.locale,
            "slug": text.slug,
            "title": text.title,
            "body": text.body,
            "version": text.version,
            "status": text.status,
            "effective_at": text.effective_at.isoformat() if text.effective_at else None,
            "created_at": text.created_at.isoformat() if text.created_at else None,
            "updated_at": text.updated_at.isoformat() if text.updated_at else None,
        }
