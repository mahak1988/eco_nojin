"""Pydantic schemas for Data Provenance API."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ProvenanceType(str, Enum):
    SCIENTIFIC_OUTPUT = "scientific_output"
    DATA_TRANSFORMATION = "data_transformation"
    DATA_SOURCE = "data_source"
    MODEL_INFERENCE = "model_inference"
    SIMULATION_RUN = "simulation_run"
    AGGREGATION = "aggregation"


class ProvenanceCreate(BaseModel):
    """Request to create a provenance record."""

    model_config = ConfigDict(extra="forbid")

    provenance_type: Literal[
        "scientific_output",
        "data_transformation",
        "data_source",
        "model_inference",
        "simulation_run",
        "aggregation",
    ] = Field(..., description="Type of provenance record")
    output_id: str = Field(
        ..., min_length=1, max_length=255, description="Reference to output entity"
    )
    output_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of output (e.g., carbon_sequestration)"
    )

    # Input lineage
    input_hashes: List[str] = Field(
        default_factory=list, description="List of input content hashes (SHA256)"
    )
    input_sources: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of source identifiers"
    )

    # Model/algorithm versioning
    model_version: str = Field(
        ..., min_length=1, max_length=100, description="Semantic version of model/algorithm"
    )
    model_name: str = Field(
        ..., min_length=1, max_length=100, description="Name of model/algorithm"
    )
    algorithm_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Frozen algorithm parameters"
    )

    # Execution context
    execution_id: Optional[str] = Field(None, description="Execution correlation ID")
    executed_by: Optional[str] = Field(None, max_length=255, description="User/system identifier")
    execution_environment: Dict[str, Any] = Field(
        default_factory=dict, description="Runtime environment info"
    )

    # Uncertainty quantification
    uncertainty: Dict[str, Any] = Field(
        default_factory=dict, description="Uncertainty quantification results"
    )
    confidence_level: Optional[str] = Field(
        None, max_length=50, description="Confidence level (e.g., '95%', 'high')"
    )

    # Quality
    is_validated: bool = Field(False, description="Whether output has been validated")
    validation_notes: Optional[str] = Field(None, description="Validation notes")
    quality_score: Optional[Literal["high", "medium", "low"]] = Field(
        None, description="Quality assessment"
    )

    # Reproducibility
    is_reproducible: bool = Field(True, description="Whether result is reproducible")
    reproducibility_notes: Optional[str] = Field(None, description="Reproducibility notes")
    docker_image_digest: Optional[str] = Field(
        None, max_length=255, description="Docker image digest for reproducibility"
    )


class ProvenanceResponse(ProvenanceCreate):
    """Response with full provenance record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    execution_id: str
    executed_at: datetime
    is_validated: bool
    quality_score: Optional[str]
    is_reproducible: bool
    created_at: datetime
    updated_at: datetime


class ProvenanceListResponse(BaseModel):
    """Paginated provenance records."""

    items: List[ProvenanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LineageQuery(BaseModel):
    """Query for lineage traversal."""

    model_config = ConfigDict(extra="forbid")

    provenance_id: str = Field(..., description="Starting provenance record ID")
    direction: Literal["upstream", "downstream", "both"] = Field(
        "upstream", description="Traversal direction"
    )
    max_depth: int = Field(5, ge=1, le=20, description="Maximum traversal depth")
    include_metadata: bool = Field(True, description="Include full metadata in response")


class LineageNode(BaseModel):
    """Node in lineage graph."""

    provenance_id: str
    provenance_type: str
    output_type: str
    output_id: str
    executed_at: datetime
    model_name: str
    model_version: str
    is_validated: bool


class LineageEdge(BaseModel):
    """Edge in lineage graph."""

    from_id: str
    to_id: str
    transformation_type: str
    transformation_params: Dict[str, Any]


class LineageResponse(BaseModel):
    """Lineage graph response."""

    nodes: List[LineageNode]
    edges: List[LineageEdge]
    max_depth_reached: bool


class ModelVersionCreate(BaseModel):
    """Request to register a model version."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(
        ..., min_length=1, max_length=50, pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?$"
    )
    description: Optional[str] = None
    algorithm_class: Optional[str] = Field(None, max_length=200)
    framework: Optional[str] = Field(None, max_length=50)
    git_commit: Optional[str] = Field(None, max_length=40, pattern=r"^[a-f0-9]{40}$")
    docker_image: Optional[str] = Field(None, max_length=255)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    validation_dataset_hash: Optional[str] = Field(None, max_length=64)
    validation_metrics: Dict[str, Any] = Field(default_factory=dict)
    tolerance_config: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class ModelVersionResponse(ModelVersionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    is_deprecated: bool
    deprecated_at: Optional[datetime]
    superseded_by_id: Optional[str]
    created_at: datetime
    deprecated_at: Optional[datetime]


class ProvenanceValidationRequest(BaseModel):
    """Request to validate a provenance record."""

    model_config = ConfigDict(extra="forbid")

    provenance_id: str
    is_valid: bool
    validator_id: str
    notes: Optional[str] = None
    quality_score: Optional[Literal["high", "medium", "low"]] = None


class ValidationResponse(BaseModel):
    """Validation response."""

    provenance_id: str
    is_validated: bool
    validated_at: datetime
    validator_id: str
