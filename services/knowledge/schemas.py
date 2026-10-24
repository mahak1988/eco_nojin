"""Pydantic schemas for Daneshyar Knowledge API."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeType(StrEnum):
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


class AccessLevel(StrEnum):
    PUBLIC = "public"
    RESTRICTED = "restricted"
    INTERNAL = "internal"


class ValidationStatus(StrEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class KnowledgeEntryCreate(BaseModel):
    """Request to create a knowledge entry."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=1, max_length=500, pattern=r"^[a-z0-9-]+$")
    knowledge_type: Literal[
        "scientific_paper",
        "technical_report",
        "best_practice",
        "case_study",
        "methodology",
        "dataset_description",
        "tool_documentation",
        "policy_brief",
        "indigenous_knowledge",
        "training_material",
    ]
    abstract: str | None = Field(None, max_length=2000)
    content: str = Field(..., min_length=1)
    content_format: Literal["markdown", "html", "plain"] = "markdown"
    authors: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    language: Literal["fa", "en"] = "fa"
    source_url: str | None = Field(None, max_length=500)
    source_organization: str | None = Field(None, max_length=200)
    doi: str | None = Field(None, max_length=100)
    publication_date: datetime | None = None
    is_peer_reviewed: bool = False
    validation_status: Literal["draft", "under_review", "verified", "rejected"] = "draft"
    access_level: Literal["public", "restricted", "internal"] = "public"


class KnowledgeEntryUpdate(BaseModel):
    """Request to update a knowledge entry."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(None, min_length=1, max_length=500)
    abstract: str | None = Field(None, max_length=2000)
    content: str | None = Field(None, min_length=1)
    tags: list[str] | None = None
    categories: list[str] | None = None
    validation_status: Literal["draft", "under_review", "verified", "rejected"] | None = None
    access_level: Literal["public", "restricted", "internal"] | None = None


class KnowledgeReviewRequest(BaseModel):
    """Editorial decision for an entry currently awaiting review."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["verified", "rejected"]


class KnowledgeEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    knowledge_type: str
    abstract: str | None
    content: str
    content_format: str
    authors: list[dict[str, Any]]
    tags: list[str]
    categories: list[str]
    language: str
    source_url: str | None
    source_organization: str | None
    doi: str | None
    publication_date: datetime | None
    is_peer_reviewed: bool
    validation_status: str
    validated_by: str | None
    validated_at: datetime | None
    access_level: str
    view_count: int
    download_count: int
    citation_count: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None


class KnowledgeEntryListResponse(BaseModel):
    items: list["KnowledgeEntryResponse"]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeSearchRequest(BaseModel):
    q: str | None = Field(None, description="Full-text search query")
    knowledge_type: str | None = None
    tags: list[str] | None = None
    categories: list[str] | None = None
    language: Literal["fa", "en"] | None = None
    validation_status: str | None = None
    access_level: Literal["public", "restricted", "internal"] = "public"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Literal["relevance", "date", "views", "title"] = "relevance"
    sort_order: Literal["asc", "desc"] = "desc"


class KnowledgeEntrySearchResponse(BaseModel):
    items: list["KnowledgeEntryResponse"]
    total: int
    page: int
    page_size: int
    total_pages: int
    query: str | None
    took_ms: int


class KnowledgeAttachmentCreate(BaseModel):
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    storage_path: str
    checksum: str
    description: str | None = None
    attachment_type: Literal["pdf", "image", "data", "code", "supplementary"]


class KnowledgeAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entry_id: str
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    storage_path: str
    checksum: str
    description: str | None
    attachment_type: str
    uploaded_by: str | None
    uploaded_at: datetime


class KnowledgeCollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    access_level: Literal["public", "restricted", "internal"] = "public"
    is_public: bool = True


class KnowledgeCollectionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    access_level: Literal["public", "restricted", "internal"] | None = None
    is_public: bool | None = None


class KnowledgeCollectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str | None
    curated_by: str | None
    curator_notes: str | None
    is_public: bool
    access_level: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None


class KnowledgeCollectionResponseWithEntries(KnowledgeCollectionResponse):
    entries: list["KnowledgeEntryResponse"] = []


class KnowledgeCollectionEntryCreate(BaseModel):
    entry_id: str
    position: int = 0


# =============================================================================
# Explainability Contract (Decision Support)
# =============================================================================

class ExplainabilityLevel(StrEnum):
    """Level of detail in explainability response."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    AUDIT = "audit"


class DecisionSupportRequest(BaseModel):
    """Request for decision support advice with explainability."""
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(..., min_length=1, max_length=2000, description="The decision goal or question")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input parameters for the decision")
    criteria: list[str] = Field(default_factory=list, description="Evaluation criteria for the decision")
    scenarios: list[dict[str, Any]] = Field(default_factory=list, description="Alternative scenarios to evaluate")
    assumptions: list[str] = Field(default_factory=list, description="Explicit assumptions")
    constraints: list[str] = Field(default_factory=list, description="Hard constraints")
    uncertainty_tolerance: Literal["low", "medium", "high"] = "medium"
    explainability_level: ExplainabilityLevel = ExplainabilityLevel.SUMMARY


class ExplainabilityResponse(BaseModel):
    """Structured explainability metadata for decision support."""
    model_config = ConfigDict(from_attributes=True)

    # Core identification
    goal: str
    model_version: str
    model_id: str
    domain: str
    purpose: str

    # Inputs and criteria
    inputs_received: dict[str, Any]
    criteria_evaluated: list[str]
    scenarios_evaluated: list[str]

    # Reasoning
    reasoning: str
    assumptions: list[str]
    constraints: list[str]
    uncertainty: dict[str, Any]
    uncertainty_tolerance: str

    # Limitations and provenance
    limitations: list[str]
    provenance: dict[str, Any]
    uncertainty_notes: str | None = None

    # Governance
    accountable_decision_maker: str | None = None
    version: str
    timestamp: datetime
    advice_applied: bool = False  # Always false - advice never auto-applied

    # Uncertainty details
    uncertainty_type: str = "NOT_ESTIMATED"
    uncertainty_value: float | None = None
    uncertainty_unit: str | None = None
    uncertainty_method: str | None = None
    confidence_level: float | None = None


class ExplainabilityResponseSummary(BaseModel):
    """Summary-level explainability (for performance)."""
    goal: str
    model_id: str
    model_version: str
    domain: str
    reasoning_summary: str
    limitations: list[str]
    version: str
    timestamp: datetime
    advice_applied: bool = False


class ExplainabilityResponseAudit(BaseModel):
    """Full audit-level explainability with all provenance."""
    goal: str
    model_id: str
    model_version: str
    domain: str
    purpose: str
    inputs_received: dict[str, Any]
    criteria_evaluated: list[str]
    scenarios_evaluated: list[str]
    reasoning: str
    assumptions: list[str]
    constraints: list[str]
    uncertainty: dict[str, Any]
    uncertainty_tolerance: str
    limitations: list[str]
    provenance: dict[str, Any]
    uncertainty_notes: str | None = None
    accountable_decision_maker: str | None = None
    version: str
    timestamp: datetime
    advice_applied: bool = False
    uncertainty_type: str = "NOT_ESTIMATED"
    uncertainty_value: float | None = None
    uncertainty_unit: str | None = None
    uncertainty_method: str | None = None
    confidence_level: float | None = None
    rag_provenance: dict | None = None


# Forward references
KnowledgeEntryResponse.model_rebuild()