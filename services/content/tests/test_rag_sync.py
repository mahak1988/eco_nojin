"""Tests for the editorial-content RAG sync and search.

The contract is honesty, not capability: a content item becomes searchable
only when it is *published*, and the sync marks items rather than claiming an
embedding it did not compute.
"""

import pytest


@pytest.fixture
def db(sync_db_session):
    return sync_db_session


def _item(db, **overrides):
    from database import models

    payload = {
        "title": "Water basics",
        "body": "Every drop counts in a dry village.",
        "category": "guide",
        "status": "draft",
        "language": "fa",
        "access_level": "public",
    }
    payload.update(overrides)
    item = models.ContentItem(**payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _published(db, **overrides):
    """A published item (the timestamps are ISO strings in this schema)."""
    from datetime import UTC, datetime

    stamp = datetime.now(UTC).isoformat()
    overrides.setdefault("status", "published")
    overrides.setdefault("published_at", stamp)
    return _item(db, **overrides)


class TestSync:
    """Tests for the RAG sync."""

    def test_nothing_is_synced_when_nothing_is_published(self, db):
        from services.content.rag_sync import sync_content_to_rag

        _item(db, status="draft")
        assert sync_content_to_rag(db) == 0

    def test_a_published_item_is_synced(self, db):
        from services.content.rag_sync import sync_content_to_rag

        _published(db)
        assert sync_content_to_rag(db) == 1

    def test_a_draft_item_is_never_synced(self, db):
        from services.content.rag_sync import sync_content_to_rag

        item = _item(db, status="draft")
        sync_content_to_rag(db)

        from database import models

        stored = db.query(models.ContentItem).filter_by(id=item.id).one()
        assert stored.rag_synced is False

    def test_the_sync_is_idempotent(self, db):
        """A second sync finds nothing left to do."""
        from services.content.rag_sync import sync_content_to_rag

        _published(db)
        assert sync_content_to_rag(db) == 1
        assert sync_content_to_rag(db) == 0


class TestSearch:
    """Tests for the keyword search."""

    def test_a_published_item_is_found(self, db):
        from services.content.rag_sync import search_published_content

        _published(db, title="Rainwater harvesting")
        results = search_published_content(db, "rainwater")
        assert len(results) == 1
        assert results[0].title == "Rainwater harvesting"

    def test_a_draft_item_is_not_found(self, db):
        """Only published content is searchable."""
        from services.content.rag_sync import search_published_content

        _item(db, title="Rainwater harvesting", status="draft")
        assert search_published_content(db, "rainwater") == []

    def test_the_body_is_searched_too(self, db):
        from services.content.rag_sync import search_published_content

        _published(db, title="Basics", body="Mentioning qanats here.")
        assert len(search_published_content(db, "qanats")) == 1

    def test_an_unmatched_term_finds_nothing(self, db):
        from services.content.rag_sync import search_published_content

        _published(db, title="Rainwater")
        assert search_published_content(db, "zzz-not-present") == []

    def test_the_limit_is_respected(self, db):
        from services.content.rag_sync import search_published_content

        for _ in range(5):
            _published(db, title="Rainwater")
        assert len(search_published_content(db, "rainwater", limit=2)) == 2


class TestSnapshot:
    """Tests for the version snapshot."""

    def test_a_snapshot_is_taken(self, db):
        from services.content.rag_sync import snapshot_version

        item = _published(db)
        snapshot_version(db, item)
        db.commit()

        from database import models

        versions = db.query(models.ContentVersion).filter_by(content_id=item.id).all()
        assert len(versions) == 1
        assert versions[0].version == 1

    def test_the_snapshot_records_the_current_title(self, db):
        from services.content.rag_sync import snapshot_version

        item = _published(db, title="Original title")
        snapshot_version(db, item)
        db.commit()

        from database import models

        version = db.query(models.ContentVersion).filter_by(content_id=item.id).one()
        assert version.title == "Original title"

    def test_the_snapshot_increments_the_version(self, db):
        from services.content.rag_sync import snapshot_version

        item = _published(db)
        snapshot_version(db, item)
        db.commit()
        item.title = "Second title"
        snapshot_version(db, item)
        db.commit()

        from database import models

        versions = (
            db.query(models.ContentVersion)
            .filter_by(content_id=item.id)
            .order_by(models.ContentVersion.version)
            .all()
        )
        assert [v.version for v in versions] == [1, 2]
