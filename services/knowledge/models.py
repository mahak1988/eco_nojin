"""Data models for Daneshyar Knowledge Layer."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from database.base import Base


class KnowledgeType(StrEnum):
    """Type of knowledge entry."""

    SCIENTIFIC_PAPER = "scientific_paper"
    TECHNICAL_REPORT = "technical_report"
    BEST_PRACTICE = "best_practice"
    CASE_STUDY = "case_study"
    METHODOLOGY = "methodology"
    DATASET_DESCRIPTION = "dataset_description"
    TOOL_DOCUMENTATION = "tool_documentation"
    POLICY_BRIEF = "policy_brief"
    INDIGENOUS_KNOWLEDGE = "indigenous_knowledge"
    TRAINING_MATERIAL = "training_material"


class KnowledgeEntry(Base):
    """Knowledge entry in the Daneshyar repository."""

    __tablename__ = "knowledge_entries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Core identification
    title = Column(String(500), nullable=False, index=True)
    slug = Column(String(500), nullable=False, unique=True, index=True)
    knowledge_type = Column(SQLEnum(KnowledgeType), nullable=False, index=True)

    # Content
    abstract = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Full text content (markdown)
    content_format = Column(String(20), nullable=False, default="markdown")

    # Metadata
    authors = Column(JSON, nullable=False, default=list)  # List of author objects
    tags = Column(JSON, nullable=False, default=list)  # Searchable tags
    categories = Column(JSON, nullable=False, default=list)  # Hierarchical categories
    language = Column(String(10), nullable=False, default="fa")  # fa, en, etc.

    # Provenance
    source_url = Column(String(500), nullable=True)
    source_organization = Column(String(200), nullable=True)
    doi = Column(String(100), nullable=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)

    # Quality & validation
    is_peer_reviewed = Column(Boolean, default=False, nullable=False, index=True)
    validation_status = Column(
        String(20), default="draft", nullable=False, index=True
    )  # draft, under_review, verified, rejected
    validated_by = Column(String(255), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)

    # Access control
    access_level = Column(
        String(20), default="public", nullable=False, index=True
    )  # public, restricted, internal

    # Metrics
    view_count = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    citation_count = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_by = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_knowledge_type_status", "knowledge_type", "validation_status"),
        Index("ix_knowledge_search", "title", "abstract", "tags"),
        Index("ix_knowledge_access_level", "access_level"),
        Index("ix_knowledge_created", "created_at"),
    )


class KnowledgeAttachment(Base):
    """File attachments for knowledge entries."""

    __tablename__ = "knowledge_attachments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    entry_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    storage_path = Column(String(500), nullable=False)  # Path in storage backend
    checksum = Column(String(64), nullable=False)  # SHA256

    description = Column(Text, nullable=True)
    attachment_type = Column(
        String(50), nullable=False
    )  # pdf, image, data, code, supplementary

    uploaded_by = Column(String(255), nullable=True)
    uploaded_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (
        Index("ix_attachment_entry", "entry_id"),
    )


class KnowledgeCollection(Base):
    """Curated collections of knowledge entries."""

    __tablename__ = "knowledge_collections"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String(200), nullable=False, unique=True, index=True)
    slug = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Curation
    curated_by = Column(String(255), nullable=True)
    curator_notes = Column(Text, nullable=True)

    # Visibility
    is_public = Column(Boolean, default=True, nullable=False, index=True)
    access_level = Column(String(20), default="public", nullable=False)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    created_by = Column(String(255), nullable=True)


class KnowledgeCollectionEntry(Base):
    """Many-to-many link between collections and entries."""

    __tablename__ = "knowledge_collection_entries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    collection_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entry_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Order within collection
    position = Column(Integer, default=0, nullable=False)

    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    added_by = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_collection_entry_unique", "collection_id", "entry_id", unique=True),
    )