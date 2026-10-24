"""Daneshyar knows how to attach RAG provenance to a knowledge search.

``KnowledgeService.search_entries`` still reads the ``knowledge_entries`` table
(read-only) and, when a free-text query is given, additionally attaches the
scientific-corpus references surfaced by the RAG index — each pointing at a real
file. This never writes and never breaks the DB-backed answer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import services.ai.hydroma_rag as rag
from services.knowledge import models as km
from services.knowledge.schemas import KnowledgeSearchRequest
from services.knowledge.service import KnowledgeService

pytestmark = pytest.mark.heavy

_REPO_ROOT = Path(rag.__file__).resolve().parents[2]


async def test_search_reads_real_knowledge_rows(db_session):
    entry = km.KnowledgeEntry(
        title="Penman Monteith reference evapotranspiration FAO",
        slug="pm-et0-fao",
        knowledge_type=km.KnowledgeType.SCIENTIFIC_PAPER,
        content="body",
        access_level="public",
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)

    service = KnowledgeService(db_session)
    result = await service.search_entries(KnowledgeSearchRequest(q="evapotranspiration"))
    assert result["total"] >= 1
    assert any("evapotranspiration" in item.title.lower() for item in result["items"])


async def test_search_appends_rag_provenance_to_real_files(db_session):
    service = KnowledgeService(db_session)
    result = await service.search_entries(
        KnowledgeSearchRequest(q="evapotranspiration FAO-56")
    )
    assert "rag_provenance" in result
    provenance = result["rag_provenance"]
    assert provenance["available"] is True
    references = provenance["references"]
    assert references, "a scientific query should surface references"
    for ref in references:
        src = ref["source_file"]
        assert src and (_REPO_ROOT / src).exists(), f"real source expected: {src}"
        assert ref["reference"]


async def test_search_without_query_has_no_rag_provenance(db_session):
    service = KnowledgeService(db_session)
    result = await service.search_entries(KnowledgeSearchRequest(q=None))
    assert "rag_provenance" not in result
