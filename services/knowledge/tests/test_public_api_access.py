from __future__ import annotations

from types import SimpleNamespace

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from services.api_gateway.auth import require_content_admin, require_user
from services.knowledge import models
from services.knowledge.router import get_db, router


@pytest_asyncio.fixture
def knowledge_app(db_session):
    app = FastAPI()
    app.include_router(router)

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    return app


@pytest.mark.asyncio
async def test_public_knowledge_routes_exclude_unverified_and_private_rows(
    knowledge_app, db_session
):
    public_entry = models.KnowledgeEntry(
        title="Verified public source",
        slug="verified-public-source",
        knowledge_type=models.KnowledgeType.SCIENTIFIC_PAPER,
        content="Public body",
        abstract="Public abstract",
        access_level="public",
        validation_status="verified",
        created_by="internal-user-id",
        validated_by="reviewer-id",
    )
    private_entry = models.KnowledgeEntry(
        title="Internal draft",
        slug="internal-draft",
        knowledge_type=models.KnowledgeType.TECHNICAL_REPORT,
        content="Private body",
        access_level="internal",
        validation_status="draft",
    )
    unreviewed_public = models.KnowledgeEntry(
        title="Unreviewed public draft",
        slug="unreviewed-public-draft",
        knowledge_type=models.KnowledgeType.BEST_PRACTICE,
        content="Unreviewed body",
        access_level="public",
        validation_status="draft",
    )
    db_session.add_all([public_entry, private_entry, unreviewed_public])
    await db_session.commit()
    await db_session.refresh(public_entry)
    await db_session.refresh(private_entry)

    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as client:
        listed = await client.get(
            "/api/v1/knowledge",
            params={"access_level": "internal", "validation_status": "draft"},
        )
        searched = await client.get(
            "/api/v1/knowledge/search",
            params={"q": "draft", "access_level": "internal"},
        )
        private_detail = await client.get(f"/api/v1/knowledge/{private_entry.id}")
        public_detail = await client.get(f"/api/v1/knowledge/{public_entry.id}")

    assert listed.status_code == 200
    assert [item["slug"] for item in listed.json()["items"]] == ["verified-public-source"]
    assert "content" not in listed.json()["items"][0]
    assert "created_by" not in listed.json()["items"][0]
    assert "validated_by" not in listed.json()["items"][0]
    assert searched.status_code == 200
    assert searched.json()["total"] == 0
    assert private_detail.status_code == 404
    assert public_detail.status_code == 200
    assert public_detail.json()["content"] == "Public body"
    assert "created_by" not in public_detail.json()


@pytest.mark.asyncio
async def test_public_search_removes_internal_rag_provenance(
    knowledge_app, db_session, monkeypatch
):
    from services.knowledge.service import KnowledgeService

    public_entry = models.KnowledgeEntry(
        title="Verified searchable source",
        slug="verified-searchable-source",
        knowledge_type=models.KnowledgeType.SCIENTIFIC_PAPER,
        content="Searchable public content",
        access_level="public",
        validation_status="verified",
    )
    db_session.add(public_entry)
    await db_session.commit()

    monkeypatch.setattr(
        KnowledgeService,
        "_rag_provenance",
        lambda _service, _query: {
            "available": True,
            "references": [{
                "reference": "A public citation",
                "doi": "10.0000/example",
                "qudt_units": ["mm"],
                "source_file": "internal/private/source.pdf",
                "model_id": "internal-model",
                "score": 0.97,
            }],
        },
    )

    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/knowledge/search",
            params={
                "q": "searchable",
                "access_level": "internal",
                "validation_status": "draft",
            },
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert [item["slug"] for item in response.json()["items"]] == ["verified-searchable-source"]
    assert response.json()["rag_provenance"]["references"] == [{
        "reference": "A public citation",
        "doi": "10.0000/example",
        "qudt_units": ["mm"],
    }]


@pytest.mark.asyncio
async def test_public_collections_hide_private_metadata_and_unverified_entries(
    knowledge_app, db_session
):
    public_collection = models.KnowledgeCollection(
        name="Public collection",
        slug="public-collection",
        description="Public description",
        curated_by="private curator",
        curator_notes="internal curation note",
        is_public=True,
        access_level="public",
    )
    private_collection = models.KnowledgeCollection(
        name="Private collection",
        slug="private-collection",
        is_public=False,
        access_level="restricted",
    )
    verified_entry = models.KnowledgeEntry(
        title="Verified collection source",
        slug="verified-collection-source",
        knowledge_type=models.KnowledgeType.SCIENTIFIC_PAPER,
        content="Verified content",
        access_level="public",
        validation_status="verified",
    )
    draft_entry = models.KnowledgeEntry(
        title="Draft collection source",
        slug="draft-collection-source",
        knowledge_type=models.KnowledgeType.TECHNICAL_REPORT,
        content="Draft content",
        access_level="public",
        validation_status="draft",
    )
    db_session.add_all([public_collection, private_collection, verified_entry, draft_entry])
    await db_session.flush()
    db_session.add_all(
        [
            models.KnowledgeCollectionEntry(
                collection_id=public_collection.id, entry_id=verified_entry.id
            ),
            models.KnowledgeCollectionEntry(
                collection_id=public_collection.id, entry_id=draft_entry.id
            ),
            models.KnowledgeCollectionEntry(
                collection_id=private_collection.id, entry_id=verified_entry.id
            ),
        ]
    )
    await db_session.commit()
    await db_session.refresh(public_collection)
    await db_session.refresh(private_collection)

    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as client:
        listed = await client.get(
            "/api/v1/knowledge/collections", params={"is_public": "false"}
        )
        public_entries = await client.get(
            f"/api/v1/knowledge/collections/{public_collection.id}/entries"
        )
        private_entries = await client.get(
            f"/api/v1/knowledge/collections/{private_collection.id}/entries"
        )

    assert listed.status_code == 200
    assert [item["slug"] for item in listed.json()["items"]] == ["public-collection"]
    assert "curated_by" not in listed.json()["items"][0]
    assert "curator_notes" not in listed.json()["items"][0]
    assert public_entries.status_code == 200
    assert [item["slug"] for item in public_entries.json()["entries"]] == [
        "verified-collection-source"
    ]
    assert "content" not in public_entries.json()["entries"][0]
    assert private_entries.status_code == 404


@pytest.mark.asyncio
async def test_knowledge_submission_requires_login_and_is_forced_to_private_draft(
    knowledge_app,
):
    payload = {
        "title": "Community observation",
        "slug": "community-observation",
        "knowledge_type": "case_study",
        "content": "Submitted material",
        "access_level": "public",
        "validation_status": "verified",
    }
    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as anonymous:
        denied = await anonymous.post("/api/v1/knowledge", json=payload)

    assert denied.status_code == 401

    knowledge_app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="author-1", role="farmer"
    )
    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as authenticated:
        created = await authenticated.post("/api/v1/knowledge", json=payload)

    assert created.status_code == 201
    assert created.json()["validation_status"] == "draft"
    assert created.json()["access_level"] == "restricted"
    assert created.json()["created_by"] == "author-1"


@pytest.mark.asyncio
async def test_knowledge_review_workflow_is_owner_scoped_and_publishes_only_approval(
    knowledge_app, db_session
):
    author_draft = models.KnowledgeEntry(
        title="Author draft",
        slug="author-draft",
        knowledge_type=models.KnowledgeType.CASE_STUDY,
        content="Private content",
        access_level="restricted",
        validation_status="draft",
        created_by="author-1",
    )
    other_author_entry = models.KnowledgeEntry(
        title="Other author draft",
        slug="other-author-draft",
        knowledge_type=models.KnowledgeType.CASE_STUDY,
        content="Another private content",
        access_level="restricted",
        validation_status="draft",
        created_by="author-2",
    )
    db_session.add_all([author_draft, other_author_entry])
    await db_session.commit()
    await db_session.refresh(author_draft)
    await db_session.refresh(other_author_entry)

    knowledge_app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="author-1", role="farmer"
    )
    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as author_client:
        mine = await author_client.get("/api/v1/knowledge/mine")
        denied_other = await author_client.post(
            f"/api/v1/knowledge/{other_author_entry.id}/submit-review"
        )
        submitted = await author_client.post(
            f"/api/v1/knowledge/{author_draft.id}/submit-review"
        )
        non_reviewer_queue = await author_client.get("/api/v1/knowledge/review-queue")

    assert mine.status_code == 200
    assert [item["id"] for item in mine.json()["items"]] == [str(author_draft.id)]
    assert denied_other.status_code == 404
    assert submitted.status_code == 200
    assert submitted.json()["validation_status"] == "under_review"
    assert submitted.json()["access_level"] == "restricted"
    assert non_reviewer_queue.status_code == 403

    knowledge_app.dependency_overrides[require_content_admin] = lambda: SimpleNamespace(
        id="reviewer-1"
    )
    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as reviewer_client:
        queue = await reviewer_client.get("/api/v1/knowledge/review-queue")
        approved = await reviewer_client.post(
            f"/api/v1/knowledge/review-queue/{author_draft.id}/decision",
            json={"decision": "verified"},
        )
        public_detail = await reviewer_client.get(
            f"/api/v1/knowledge/{author_draft.id}"
        )
        duplicate_decision = await reviewer_client.post(
            f"/api/v1/knowledge/review-queue/{author_draft.id}/decision",
            json={"decision": "rejected"},
        )

    assert queue.status_code == 200
    assert [item["id"] for item in queue.json()["items"]] == [str(author_draft.id)]
    assert approved.status_code == 200
    assert approved.json()["validation_status"] == "verified"
    assert approved.json()["access_level"] == "public"
    assert approved.json()["validated_by"] == "reviewer-1"
    assert approved.json()["validated_at"]
    assert public_detail.status_code == 200
    assert public_detail.json()["content"] == "Private content"
    assert duplicate_decision.status_code == 409


@pytest.mark.asyncio
async def test_knowledge_review_rejection_remains_private_and_requires_review_role(
    knowledge_app, db_session
):
    pending = models.KnowledgeEntry(
        title="Pending source",
        slug="pending-source",
        knowledge_type=models.KnowledgeType.TECHNICAL_REPORT,
        content="Pending content",
        access_level="restricted",
        validation_status="under_review",
        created_by="author-1",
    )
    db_session.add(pending)
    await db_session.commit()
    await db_session.refresh(pending)

    knowledge_app.dependency_overrides[require_user] = lambda: SimpleNamespace(
        id="reviewer", role="farmer"
    )
    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as regular_client:
        denied = await regular_client.post(
            f"/api/v1/knowledge/review-queue/{pending.id}/decision",
            json={"decision": "rejected"},
        )
    assert denied.status_code == 403

    knowledge_app.dependency_overrides[require_content_admin] = lambda: SimpleNamespace(
        id="reviewer-2"
    )
    async with AsyncClient(
        transport=ASGITransport(app=knowledge_app),
        base_url="http://test",
    ) as reviewer_client:
        rejected = await reviewer_client.post(
            f"/api/v1/knowledge/review-queue/{pending.id}/decision",
            json={"decision": "rejected"},
        )
        private_detail = await reviewer_client.get(f"/api/v1/knowledge/{pending.id}")

    assert rejected.status_code == 200
    assert rejected.json()["validation_status"] == "rejected"
    assert rejected.json()["access_level"] == "restricted"
    assert rejected.json()["validated_by"] == "reviewer-2"
    assert private_detail.status_code == 404
