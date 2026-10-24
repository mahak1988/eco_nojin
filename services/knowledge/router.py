"""Knowledge API Router (Daneshyar)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.api_gateway.auth import require_content_admin, require_user
from services.knowledge.schemas import (
    DecisionSupportRequest,
    ExplainabilityLevel,
    KnowledgeCollectionCreate,
    KnowledgeEntryCreate,
    KnowledgeEntryUpdate,
    KnowledgeReviewRequest,
    KnowledgeSearchRequest,
)
from services.knowledge.service import KnowledgeService

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_knowledge_service_dep(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> KnowledgeService:
    return KnowledgeService(db)


def _public_entry(entry, *, include_content: bool = False) -> dict[str, Any]:
    """Project a verified public entry without internal ownership or review data."""
    payload = entry.model_dump(
        exclude={"access_level", "created_by", "validated_by", "validated_at", "download_count"}
    )
    if not include_content:
        payload.pop("content", None)
    return payload


# =============================================================================
# Knowledge Entries
# =============================================================================


@router.post(
    "", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED
)
async def create_knowledge_entry(
    data: KnowledgeEntryCreate,
    user: Annotated[Any, Depends(require_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Submit a private draft; publication and validation remain editorial actions."""
    draft = data.model_copy(update={"validation_status": "draft", "access_level": "restricted"})
    entry = await service.create_entry(draft, user_id=str(user.id))
    return entry.model_dump()


@router.get("", response_model=dict[str, Any])
async def list_knowledge_entries(
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    knowledge_type: Annotated[str | None, Query(description="Filter by knowledge type")] = None,
    validation_status: Annotated[
    str | None, Query(description="Filter by validation status")
] = None,
    access_level: Annotated[str | None, Query(description="Filter by access level")] = None,
    q: Annotated[str | None, Query(description="Search query")] = None,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)] = None,
):
    """List verified public entries; client filters cannot widen visibility."""
    items, total, page, page_size = await service.list_entries(
        page=page,
        page_size=page_size,
        knowledge_type=knowledge_type,
        validation_status="verified",
        access_level="public",
        q=q,
        public_only=True,
    )
    return {
        "items": [_public_entry(item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("/search", response_model=dict[str, Any])
async def search_knowledge_entries(
    search: Annotated[KnowledgeSearchRequest, Depends()],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Search verified public content and publish citation-safe provenance only."""
    public_search = search.model_copy(
        update={"access_level": "public", "validation_status": "verified"}
    )
    result = await service.search_entries(public_search, public_only=True)
    result["items"] = [_public_entry(item) for item in result["items"]]
    provenance = result.get("rag_provenance")
    if isinstance(provenance, dict):
        provenance["references"] = [
            {
                key: reference[key]
                for key in ("reference", "doi", "qudt_units")
                if key in reference
            }
            for reference in provenance.get("references", [])
            if isinstance(reference, dict)
        ]
    return result


@router.get("/mine", response_model=dict[str, Any])
async def list_my_knowledge_entries(
    user: Annotated[Any, Depends(require_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List the caller's own drafts and editorial outcomes."""
    items, total = await service.list_user_entries(
        str(user.id), page=page, page_size=page_size
    )
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.post("/{entry_id}/submit-review", response_model=dict[str, Any])
async def submit_knowledge_entry_for_review(
    entry_id: str,
    user: Annotated[Any, Depends(require_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Submit an owned private draft to the content review queue."""
    try:
        entry = await service.submit_entry_for_review(entry_id, str(user.id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry.model_dump()


@router.get("/review-queue", response_model=dict[str, Any])
async def list_knowledge_review_queue(
    user: Annotated[Any, Depends(require_content_admin)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Return pending entries to content reviewers only."""
    items, total, page, page_size = await service.list_entries(
        page=page, page_size=page_size, validation_status="under_review"
    )
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.post(
    "/review-queue/{entry_id}/decision", response_model=dict[str, Any]
)
async def decide_knowledge_entry_review(
    entry_id: str,
    data: KnowledgeReviewRequest,
    user: Annotated[Any, Depends(require_content_admin)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Approve or reject a pending entry; public visibility follows approval only."""
    try:
        entry = await service.review_entry(entry_id, data.decision, str(user.id))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry.model_dump()


@router.get("/collections", response_model=dict[str, Any])
async def list_collections(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)] = None,
):
    """List public collections only; caller filters cannot expose restricted ones."""
    items, total = await service.list_public_collections(page, page_size)
    return {
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "slug": item.slug,
                "description": item.description,
                "is_public": item.is_public,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


@router.get("/{entry_id}", response_model=dict[str, Any])
async def get_knowledge_entry(
    entry_id: str,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Get a knowledge entry by ID."""
    entry = await service.get_entry(entry_id)
    if not entry or entry.access_level != "public" or entry.validation_status != "verified":
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return _public_entry(entry, include_content=True)


@router.get("/slug/{slug}", response_model=dict[str, Any])
async def get_knowledge_entry_by_slug(
    slug: str,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Get a knowledge entry by slug."""
    entry = await service.get_entry_by_slug(slug)
    if not entry or entry.access_level != "public" or entry.validation_status != "verified":
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return _public_entry(entry, include_content=True)


@router.patch("/{entry_id}", response_model=dict[str, Any])
async def update_knowledge_entry(
    entry_id: str,
    data: KnowledgeEntryUpdate,
    user: Annotated[Any, Depends(require_content_admin)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Update a knowledge entry."""
    entry = await service.update_entry(entry_id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    return entry.model_dump()


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_entry(
    entry_id: str,
    user: Annotated[Any, Depends(require_content_admin)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Delete a knowledge entry."""
    deleted = await service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")


@router.post("/{entry_id}/view", status_code=status.HTTP_204_NO_CONTENT)
async def increment_view_count(
    entry_id: str,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Count views only for content that is actually public and verified."""
    entry = await service.get_entry(entry_id)
    if not entry or entry.access_level != "public" or entry.validation_status != "verified":
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    await service.increment_view_count(entry_id)


# =============================================================================
# Collections
# =============================================================================


@router.post(
    "/collections",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    data: KnowledgeCollectionCreate,
    user: Annotated[Any, Depends(require_content_admin)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Create a new knowledge collection."""
    collection = await service.create_collection(data)
    return collection.model_dump()


@router.get("/collections/{collection_id}", response_model=dict[str, Any])
async def get_collection(
    collection_id: str,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    collection = await service.get_collection(collection_id)
    if not collection or not collection.is_public or collection.access_level != "public":
        raise HTTPException(status_code=404, detail="Collection not found")
    return {
        "id": collection.id,
        "name": collection.name,
        "slug": collection.slug,
        "description": collection.description,
        "is_public": collection.is_public,
    }


@router.get(
    "/collections/{collection_id}/entries", response_model=dict[str, Any]
)
async def get_collection_with_entries(
    collection_id: str,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Return a public collection with only its verified public sources."""
    result = await service.get_public_collection_with_entries(collection_id)
    if not result:
        raise HTTPException(status_code=404, detail="Collection not found")
    collection, entries = result
    return {
        "id": collection.id,
        "name": collection.name,
        "slug": collection.slug,
        "description": collection.description,
        "is_public": collection.is_public,
        "entries": [_public_entry(entry) for entry in entries],
    }


@router.post(
    "/collections/{collection_id}/entries",
    status_code=status.HTTP_201_CREATED,
)
async def add_entry_to_collection(
    collection_id: str,
    entry_id: Annotated[str, Query(description="Entry ID to add")],
    position: Annotated[int, Query(description="Position in collection")] = 0,
    user: Annotated[Any, Depends(require_content_admin)] = None,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)] = None,
):
    """Add a knowledge entry to a collection."""
    success = await service.add_entry_to_collection(
        collection_id, entry_id, position
    )
    if not success:
        raise HTTPException(status_code=404, detail="Collection or entry not found")
    return {"status": "added"}


@router.delete(
    "/collections/{collection_id}/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_entry_from_collection(
    collection_id: str,
    entry_id: str,
    user: Annotated[Any, Depends(require_content_admin)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """Remove a knowledge entry from a collection."""
    success = await service.remove_entry_from_collection(collection_id, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found")


# =============================================================================
# Explainability Contract (Decision Support) - P11
# =============================================================================

@router.post("/decision-support", response_model=dict[str, Any])
async def get_decision_support(
    payload: DecisionSupportRequest,
    user: Annotated[Any, Depends(require_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service_dep)],
):
    """
    Get structured decision support advice with full explainability.

    The response follows the Explainability Contract:
    - goal, inputs, criteria, scenarios, assumptions, constraints
    - reasoning, uncertainty, limitations, provenance
    - version, timestamp, accountable decision-maker
    - advice_applied: false (advice never auto-applies)
    - uncertainty metadata
    """
    # Build the explainability response
    explainability = await service.get_decision_support_explainability(payload, str(user.id))

    # Return based on requested detail level
    if payload.explainability_level == ExplainabilityLevel.SUMMARY:
        return {
            "goal": explainability["goal"],
            "model_id": explainability["model_id"],
            "model_version": explainability["model_version"],
            "domain": explainability["domain"],
            "reasoning_summary": explainability["reasoning_summary"],
            "limitations": explainability["limitations"],
            "version": explainability["version"],
            "timestamp": explainability["timestamp"],
            "advice_applied": False,
        }
    elif payload.explainability_level == ExplainabilityLevel.AUDIT:
        return {
            "goal": explainability["goal"],
            "model_id": explainability["model_id"],
            "model_version": explainability["model_version"],
            "domain": explainability["domain"],
            "purpose": explainability["purpose"],
            "inputs_received": explainability["inputs_received"],
            "criteria_evaluated": explainability["criteria_evaluated"],
            "scenarios_evaluated": explainability["scenarios_evaluated"],
            "reasoning": explainability["reasoning"],
            "assumptions": explainability["assumptions"],
            "constraints": explainability["constraints"],
            "uncertainty": explainability["uncertainty"],
            "uncertainty_tolerance": explainability["uncertainty_tolerance"],
            "limitations": explainability["limitations"],
            "provenance": explainability["provenance"],
            "uncertainty_notes": explainability.get("uncertainty_notes"),
            "accountable_decision_maker": explainability.get("accountable_decision_maker"),
            "version": explainability["version"],
            "timestamp": explainability["timestamp"],
            "advice_applied": False,
            "uncertainty_type": explainability["uncertainty_type"],
            "uncertainty_value": explainability.get("uncertainty_value"),
            "uncertainty_unit": explainability.get("uncertainty_unit"),
            "uncertainty_method": explainability.get("uncertainty_method"),
            "confidence_level": explainability.get("confidence_level"),
            "rag_provenance": explainability.get("rag_provenance"),
        }
    else:  # DETAILED
        return {
            "goal": explainability["goal"],
            "model_version": explainability["model_version"],
            "model_id": explainability["model_id"],
            "domain": explainability["domain"],
            "purpose": explainability["purpose"],
            "inputs_received": explainability["inputs_received"],
            "criteria_evaluated": explainability["criteria_evaluated"],
            "scenarios_evaluated": explainability["scenarios_evaluated"],
            "reasoning": explainability["reasoning"],
            "assumptions": explainability["assumptions"],
            "constraints": explainability["constraints"],
            "uncertainty": explainability["uncertainty"],
            "uncertainty_tolerance": explainability["uncertainty_tolerance"],
            "limitations": explainability["limitations"],
            "provenance": explainability["provenance"],
            "uncertainty_notes": explainability.get("uncertainty_notes"),
            "accountable_decision_maker": explainability.get("accountable_decision_maker"),
            "version": explainability["version"],
            "timestamp": explainability["timestamp"],
            "advice_applied": False,
            "uncertainty_type": explainability["uncertainty_type"],
            "uncertainty_value": explainability.get("uncertainty_value"),
            "uncertainty_unit": explainability.get("uncertainty_unit"),
            "uncertainty_method": explainability.get("uncertainty_method"),
            "confidence_level": explainability.get("confidence_level"),
        }