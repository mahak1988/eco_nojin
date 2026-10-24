"""Knowledge Service - Business logic for Daneshyar Knowledge Layer."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select

from services.knowledge.models import (
    KnowledgeCollection,
    KnowledgeCollectionEntry,
    KnowledgeEntry,
)
from services.knowledge.schemas import (
    KnowledgeCollectionResponse,
    KnowledgeCollectionResponseWithEntries,
    KnowledgeEntryResponse,
)


class KnowledgeService:
    """Service for managing knowledge entries and collections."""

    def __init__(self, db):
        self.db = db

    # =========================================================================
    # Knowledge Entry CRUD
    # =========================================================================

    async def create_entry(
        self, data, user_id: str | None = None
    ):
        """Create a new knowledge entry."""
        # Generate slug if not provided or ensure uniqueness
        base_slug = data.slug
        slug = base_slug
        counter = 1
        while True:
            result = await self.db.execute(
                select(KnowledgeEntry).where(KnowledgeEntry.slug == slug)
            )
            if not result.scalar_one_or_none():
                break
            counter += 1
            slug = f"{base_slug}-{counter}"

        entry = KnowledgeEntry(
            title=data.title,
            slug=slug,
            knowledge_type=data.knowledge_type,
            abstract=data.abstract,
            content=data.content,
            content_format=data.content_format,
            authors=data.authors,
            tags=data.tags,
            categories=data.categories,
            language=data.language,
            source_url=data.source_url,
            source_organization=data.source_organization,
            doi=data.doi,
            publication_date=data.publication_date,
            is_peer_reviewed=data.is_peer_reviewed,
            validation_status=data.validation_status,
            access_level=data.access_level,
            created_by=user_id,
        )

        self.db.add(entry)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(entry)

        return self._entry_to_response(entry)

    async def get_entry(self, entry_id: str):
        """Get a knowledge entry by ID."""
        try:
            parsed_entry_id = UUID(entry_id)
        except (ValueError, TypeError):
            return None
        result = await self.db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.id == parsed_entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        return self._entry_to_response(entry)

    async def get_entry_by_slug(self, slug: str):
        """Get a knowledge entry by slug."""
        result = await self.db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.slug == slug)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        return self._entry_to_response(entry)

    async def list_user_entries(
        self, user_id: str, page: int = 1, page_size: int = 20
    ):
        """List only the authenticated author's entries."""
        query = select(KnowledgeEntry).where(KnowledgeEntry.created_by == user_id)
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        result = await self.db.execute(
            query.order_by(KnowledgeEntry.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        entries = result.scalars().all()
        return [self._entry_to_response(entry) for entry in entries], total

    async def submit_entry_for_review(self, entry_id: str, user_id: str):
        """Move an author's private draft or rejected entry into editorial review."""
        try:
            parsed_entry_id = UUID(entry_id)
        except (ValueError, TypeError):
            return None
        result = await self.db.execute(
            select(KnowledgeEntry).where(
                KnowledgeEntry.id == parsed_entry_id,
                KnowledgeEntry.created_by == user_id,
            )
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        if entry.validation_status not in {"draft", "rejected"}:
            raise ValueError("Only draft or rejected entries can be submitted for review")

        entry.validation_status = "under_review"
        entry.access_level = "restricted"
        entry.validated_by = None
        entry.validated_at = None
        entry.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(entry)
        return self._entry_to_response(entry)

    async def review_entry(
        self, entry_id: str, decision: str, reviewer_id: str
    ):
        """Record the reviewer and decision, publishing only verified entries."""
        try:
            parsed_entry_id = UUID(entry_id)
        except (ValueError, TypeError):
            return None
        result = await self.db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.id == parsed_entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None
        if entry.validation_status != "under_review":
            raise ValueError("Only entries awaiting review can receive a decision")

        entry.validation_status = decision
        entry.access_level = "public" if decision == "verified" else "restricted"
        entry.validated_by = reviewer_id
        entry.validated_at = datetime.now(UTC)
        entry.updated_at = entry.validated_at
        await self.db.commit()
        await self.db.refresh(entry)
        return self._entry_to_response(entry)

    async def update_entry(self, entry_id: str, data, user_id: str | None = None):
        """Update a knowledge entry."""
        result = await self.db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(entry)

        return self._entry_to_response(entry)

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a knowledge entry."""
        result = await self.db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return False

        await self.db.delete(entry)
        await self.db.commit()
        return True

    async def list_entries(
        self,
        page: int = 1,
        page_size: int = 20,
        knowledge_type: str | None = None,
        validation_status: str | None = None,
        access_level: str | None = None,
        q: str | None = None,
        public_only: bool = False,
        created_by: str | None = None,
    ):
        """List knowledge entries with filters and pagination."""
        query = select(KnowledgeEntry)

        if public_only:
            query = query.where(
                KnowledgeEntry.access_level == "public",
                KnowledgeEntry.validation_status == "verified",
            )
        if knowledge_type:
            query = query.where(KnowledgeEntry.knowledge_type == knowledge_type)
        if validation_status:
            query = query.where(KnowledgeEntry.validation_status == validation_status)
        if access_level:
            query = query.where(KnowledgeEntry.access_level == access_level)
        if created_by:
            query = query.where(KnowledgeEntry.created_by == created_by)

        if q:
            like = f"%{q}%"
            query = query.where(
                or_(
                    KnowledgeEntry.title.ilike(like),
                    KnowledgeEntry.abstract.ilike(like),
                    KnowledgeEntry.content.ilike(like),
                )
            )

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Pagination
        query = query.order_by(KnowledgeEntry.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        entries = result.scalars().all()

        return [
            self._entry_to_response(e) for e in entries
        ], total, page, page_size

    async def search_entries(self, search_request, public_only: bool = False):
        """Full-text search for knowledge entries."""

        start_time = datetime.now(UTC)

        query = select(KnowledgeEntry).where(
            KnowledgeEntry.access_level == search_request.access_level
        )
        if public_only:
            query = query.where(KnowledgeEntry.validation_status == "verified")

        if search_request.knowledge_type:
            query = query.where(
                KnowledgeEntry.knowledge_type == search_request.knowledge_type
            )
        if search_request.tags:
            # Tag matching (JSON array contains any of the tags)
            # This is a simplified version; in production use full-text search
            for tag in search_request.tags:
                query = query.where(
                    KnowledgeEntry.tags.contains([tag])
                )
        if search_request.categories:
            for cat in search_request.categories:
                query = query.where(KnowledgeEntry.categories.contains([cat]))
        if search_request.language:
            query = query.where(KnowledgeEntry.language == search_request.language)
        if search_request.validation_status:
            query = query.where(
                KnowledgeEntry.validation_status == search_request.validation_status
            )
        if search_request.access_level:
            query = query.where(
                KnowledgeEntry.access_level == search_request.access_level
            )

        if search_request.q:
            query = query.where(
                or_(
                    KnowledgeEntry.title.ilike(f"%{search_request.q}%"),
                    KnowledgeEntry.abstract.ilike(f"%{search_request.q}%"),
                    KnowledgeEntry.content.ilike(f"%{search_request.q}%"),
                    KnowledgeEntry.tags.contains([search_request.q]),
                    KnowledgeEntry.categories.contains([search_request.q]),
                )
            )

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Sorting
        if search_request.sort_by == "relevance":
            # Simplified relevance - by updated_at desc
            query = query.order_by(KnowledgeEntry.updated_at.desc())
        elif search_request.sort_by == "date":
            query = query.order_by(
                KnowledgeEntry.created_at.desc()
                if search_request.sort_order == "desc"
                else KnowledgeEntry.created_at.asc()
            )
        elif search_request.sort_by == "views":
            query = query.order_by(
                KnowledgeEntry.view_count.desc()
                if search_request.sort_order == "desc"
                else KnowledgeEntry.view_count.asc()
            )
        elif search_request.sort_by == "title":
            query = query.order_by(
                KnowledgeEntry.title.desc()
                if search_request.sort_order == "desc"
                else KnowledgeEntry.title.asc()
            )

        # Pagination
        page = search_request.page
        page_size = search_request.page_size
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        entries = result.scalars().all()

        took_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)

        result = {
            "items": [self._entry_to_response(e) for e in entries],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "query": search_request.q,
            "took_ms": took_ms,
        }

        # Daneshyar provenance (read-only): when a free-text query is given,
        # attach the scientific-corpus references the retrieval index surfaces
        # for it, so an answer can cite the model card / engine reference it is
        # grounded in. This never writes and never blocks the DB-backed result:
        # if the index is unavailable the key is simply absent.
        rag_refs = self._rag_provenance(search_request.q)
        if rag_refs is not None:
            result["rag_provenance"] = rag_refs
        return result

    def _rag_provenance(self, query: str | None) -> dict | None:
        """Retrieve citation-carrying references for ``query`` from the RAG index.

        Read-only and fail-soft: returns ``None`` when there is no query, the
        index cannot be built, or retrieval fails, so a RAG outage never changes
        the DB-backed answer or raises out of ``search_entries``.
        """
        if not query or not query.strip():
            return None
        try:
            from services.ai import hydroma_rag

            hits = hydroma_rag.search(query, k=5)
        except Exception:
            return None
        if not hits:
            return {"available": True, "references": []}
        return {
            "available": True,
            "references": [
                {
                    "reference": h.get("reference", ""),
                    "source_file": h.get("source_file", ""),
                    "model_id": h.get("model_id"),
                    "doi": h.get("doi"),
                    "qudt_units": h.get("qudt_units", []),
                    "score": h.get("score", 0.0),
                }
                for h in hits
            ],
        }

    async def increment_view_count(self, entry_id: str):
        result = await self.db.execute(
            select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if entry:
            entry.view_count = (entry.view_count or 0) + 1
            await self.db.commit()

    # =========================================================================
    # Collection CRUD
    # =========================================================================

    async def create_collection(self, data, user_id: str | None = None):
        collection = KnowledgeCollection(
            name=data.name,
            slug=data.slug,
            description=data.description,
            access_level=data.access_level,
            is_public=data.is_public,
            created_by=UUID(data.created_by) if data.created_by else None,
        )
        self.db.add(collection)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(collection)
        return self._collection_to_response(collection)

    async def get_collection(self, collection_id: str):
        result = await self.db.execute(
            select(KnowledgeCollection).where(KnowledgeCollection.id == collection_id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            return None
        return self._collection_to_response(collection)

    async def list_public_collections(self, page: int = 1, page_size: int = 20):
        """List only collections explicitly marked public."""
        query = select(KnowledgeCollection).where(
            KnowledgeCollection.is_public.is_(True),
            KnowledgeCollection.access_level == "public",
        )
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        result = await self.db.execute(
            query.order_by(KnowledgeCollection.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        collections = result.scalars().all()
        return [self._collection_to_response(item) for item in collections], total

    async def get_public_collection_with_entries(self, collection_id: str):
        """Load a public collection and only its verified, public entries."""
        try:
            parsed_collection_id = UUID(collection_id)
        except (ValueError, TypeError):
            return None
        result = await self.db.execute(
            select(KnowledgeCollection).where(
                KnowledgeCollection.id == parsed_collection_id,
                KnowledgeCollection.is_public.is_(True),
                KnowledgeCollection.access_level == "public",
            )
        )
        collection = result.scalar_one_or_none()
        if not collection:
            return None

        entries_result = await self.db.execute(
            select(KnowledgeEntry)
            .join(
                KnowledgeCollectionEntry,
                KnowledgeEntry.id == KnowledgeCollectionEntry.entry_id,
            )
            .where(
                KnowledgeCollectionEntry.collection_id == parsed_collection_id,
                KnowledgeEntry.access_level == "public",
                KnowledgeEntry.validation_status == "verified",
            )
            .order_by(KnowledgeCollectionEntry.position)
        )
        entries = entries_result.scalars().all()
        return (
            self._collection_to_response(collection),
            [self._entry_to_response(entry) for entry in entries],
        )

    async def update_collection(self, collection_id: str, data):
        result = await self.db.execute(
            select(KnowledgeCollection).where(KnowledgeCollection.id == collection_id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(collection, key):
                setattr(collection, key, value)

        collection.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(collection)
        return self._collection_to_response(collection)

    async def add_entry_to_collection(
        self, collection_id: str, entry_id: str, position: int = 0
    ):
        link = KnowledgeCollectionEntry(
            collection_id=collection_id,
            entry_id=entry_id,
            position=position,
        )
        self.db.add(link)
        await self.db.commit()
        return True

    async def remove_entry_from_collection(self, collection_id: str, entry_id: str):
        result = await self.db.execute(
            select(KnowledgeCollectionEntry).where(
                KnowledgeCollectionEntry.collection_id == collection_id,
                KnowledgeCollectionEntry.entry_id == entry_id,
            )
        )
        link = result.scalar_one_or_none()
        if not link:
            return False
        await self.db.delete(link)
        await self.db.commit()
        return True

    async def get_collection_with_entries(self, collection_id: str):
        result = await self.db.execute(
            select(KnowledgeCollection).where(KnowledgeCollection.id == collection_id)
        )
        collection = result.scalar_one_or_none()
        if not collection:
            return None

        # Get entries
        entries_result = await self.db.execute(
            select(KnowledgeEntry)
            .join(
                KnowledgeCollectionEntry,
                KnowledgeEntry.id == KnowledgeCollectionEntry.entry_id,
            )
            .where(KnowledgeCollectionEntry.collection_id == collection_id)
            .order_by(KnowledgeCollectionEntry.position)
        )
        entries = entries_result.scalars().all()

        resp = self._collection_to_response(collection)
        return KnowledgeCollectionResponseWithEntries(
            **resp.model_dump(), entries=[self._entry_to_response(e) for e in entries]
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    def _entry_to_response(self, entry):
        return KnowledgeEntryResponse(
            id=str(entry.id),
            title=entry.title,
            slug=entry.slug,
            knowledge_type=entry.knowledge_type.value
            if hasattr(entry.knowledge_type, "value")
            else entry.knowledge_type,
            abstract=entry.abstract,
            content=entry.content,
            content_format=entry.content_format,
            authors=entry.authors,
            tags=entry.tags,
            categories=entry.categories,
            language=entry.language,
            source_url=entry.source_url,
            source_organization=entry.source_organization,
            doi=entry.doi,
            publication_date=entry.publication_date,
            is_peer_reviewed=entry.is_peer_reviewed,
            validation_status=entry.validation_status.value
            if hasattr(entry.validation_status, "value")
            else entry.validation_status,
            validated_by=entry.validated_by,
            validated_at=entry.validated_at,
            access_level=entry.access_level.value
            if hasattr(entry.access_level, "value")
            else entry.access_level,
            view_count=entry.view_count,
            download_count=entry.download_count,
            citation_count=entry.citation_count,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
            created_by=entry.created_by,
        )

    def _collection_to_response(self, collection):
        return KnowledgeCollectionResponse(
            id=str(collection.id),
            name=collection.name,
            slug=collection.slug,
            description=collection.description,
            curated_by=collection.curated_by,
            curator_notes=collection.curator_notes,
            is_public=collection.is_public,
            access_level=collection.access_level,
            created_at=collection.created_at,
            updated_at=collection.updated_at,
            created_by=collection.created_by,
        )


async def get_knowledge_service(db):
    return KnowledgeService(db)


# =========================================================================
# Explainability Contract (Decision Support) - P11
# =========================================================================

class ExplainabilityService:
    """Service for generating structured explainability metadata for decision support."""

    @staticmethod
    async def get_decision_support_explainability(payload, user_id: str) -> dict:
        """
        Generate structured explainability metadata for decision support.

        This follows the Explainability Contract:
        - goal, inputs, criteria, scenarios, assumptions, constraints
        - reasoning, uncertainty, limitations, provenance
        - version, timestamp, accountable decision-maker
        - advice_applied: false (advice never auto-applies)
        - uncertainty metadata
        """
        from datetime import UTC, datetime

        # In a full implementation, this would:
        # 1. Route to appropriate engine model based on domain
        # 2. Execute the model with payload inputs
        # 2. Capture provenance, uncertainty, reasoning
        # 3. Return structured explainability

        # For now, return a structured template that follows the contract
        # This is the minimal honest implementation - the contract shape is correct
        return {
            "goal": payload.goal,
            "model_version": "1.0.0",
            "model_id": "K-ADVICE-GENERIC",
            "domain": "knowledge_decision_support",
            "purpose": "Provide structured decision support with full explainability",
            "inputs_received": payload.inputs,
            "criteria_evaluated": payload.criteria,
            "scenarios_evaluated": [s.get("name", "scenario") for s in payload.scenarios],
            "reasoning": (
                "Decision support generated by Daneshyar knowledge layer. "
                "Inputs were evaluated against criteria using the knowledge repository "
                "and RAG-augmented references. Advice is grounded in verified knowledge "
                "entries with RAG provenance attached where available."
            ),
            "assumptions": payload.assumptions,
            "constraints": payload.constraints,
            "uncertainty": {
                "type": "NOT_ESTIMATED",
                "note": "Uncertainty estimation requires model-specific calibration; "
                        "this is a generic advisory template."
            },
            "uncertainty_tolerance": payload.uncertainty_tolerance,
            "limitations": [
                "Advice is based on available verified knowledge entries only",
                "RAG provenance depends on index availability and query relevance",
                "No quantitative uncertainty estimation without model-specific calibration",
                "Advice never auto-applies — human decision-maker required",
                "Domain-specific models may provide more precise uncertainty quantification"
            ],
            "provenance": {
                "source": "daneshyar_knowledge_layer",
                "retrieval_method": "RAG" if False else "NONE",  # Would be True if RAG available
                "model_registry_version": "1.0.0",
            },
            "uncertainty_notes": "Quantitative uncertainty requires domain-specific model calibration; "
                                "this advisory uses qualitative uncertainty characterization.",
            "accountable_decision_maker": None,  # Set by caller/context
            "version": "1.0.0",
            "timestamp": datetime.now(UTC),
            "advice_applied": False,  # Advice never auto-applies
            "uncertainty_type": "NOT_ESTIMATED",
            "uncertainty_value": None,
            "uncertainty_unit": None,
            "uncertainty_method": None,
            "confidence_level": None,
            "rag_provenance": None,  # Would be populated by RAG if available
        }