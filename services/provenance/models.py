"""Database models for Data Provenance tracking."""

import enum
import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    JSON,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from database.base import Base


class ProvenanceType(str, enum.Enum):
    """Type of provenance record."""

    SCIENTIFIC_OUTPUT = "scientific_output"  # Model computation result
    DATA_TRANSFORMATION = "data_transformation"  # ETL/processing step
    DATA_SOURCE = "data_source"  # Raw data ingestion
    MODEL_INFERENCE = "model_inference"  # ML/DL model prediction
    SIMULATION_RUN = "simulation_run"  # Scientific simulation
    AGGREGATION = "aggregation"  # Data aggregation


class ProvenanceRecord(Base):
    """Immutable record of data provenance for scientific outputs."""

    __tablename__ = "provenance_records"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core identification
    provenance_type = Column(SQLEnum(ProvenanceType), nullable=False, index=True)
    output_id = Column(String(255), nullable=False, index=True)  # Reference to output entity
    output_type = Column(
        String(100), nullable=False
    )  # e.g., "carbon_sequestration", "erosion_risk"

    # Input lineage
    input_hashes = Column(JSON, nullable=False, default=list)  # List of input content hashes
    input_sources = Column(JSON, nullable=False, default=list)  # List of source identifiers

    # Model/algorithm versioning
    model_version = Column(String(100), nullable=False, index=True)  # Semantic version
    model_name = Column(String(100), nullable=False, index=True)  # e.g., "carbon_sequestration_v1"
    algorithm_parameters = Column(JSON, nullable=False, default=dict)  # Frozen parameters

    # Execution context
    execution_id = Column(PG_UUID(as_uuid=True), default=uuid.uuid4, index=True)
    executed_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    executed_by = Column(String(255), nullable=True)  # User/system identifier
    execution_environment = Column(JSON, nullable=False, default=dict)  # Runtime info

    # Uncertainty quantification
    uncertainty = Column(JSON, nullable=False, default=dict)  # Uncertainty quantification results
    confidence_level = Column(String(50), nullable=True)  # e.g., "95%", "high", "medium"

    # Quality flags
    is_validated = Column(Boolean, default=False, nullable=False, index=True)
    validation_notes = Column(Text, nullable=True)
    quality_score = Column(String(20), nullable=True)  # e.g., "high", "medium", "low"

    # Reproducibility
    is_reproducible = Column(Boolean, default=True, nullable=False)
    reproducibility_notes = Column(Text, nullable=True)
    docker_image_digest = Column(String(255), nullable=True)  # For containerized execution

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    lineage_edges = relationship(
        "DataLineage",
        foreign_keys="DataLineage.output_provenance_id",
        back_populates="output_provenance",
    )
    reverse_lineage_edges = relationship(
        "DataLineage",
        foreign_keys="DataLineage.input_provenance_id",
        back_populates="input_provenance",
    )

    __table_args__ = (
        Index("ix_provenance_type_executed", "provenance_type", "executed_at"),
        Index("ix_provenance_output_lookup", "output_type", "output_id"),
        Index("ix_provenance_model_version", "model_name", "model_version"),
        Index("ix_provenance_validation", "is_validated", "executed_at"),
    )


class ModelVersion(Base):
    """Tracks registered model versions for reproducibility."""

    __tablename__ = "model_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)  # Semantic version

    # Model metadata
    description = Column(Text, nullable=True)
    algorithm_class = Column(
        String(200), nullable=True
    )  # e.g., "HydromaCore.estimate_carbon_sequestration_potential"
    framework = Column(String(50), nullable=True)  # e.g., "pytorch", "sklearn", "cpp", "custom"

    # Versioning
    git_commit = Column(String(40), nullable=True)  # Git SHA
    docker_image = Column(String(255), nullable=True)  # Docker image with digest
    dependencies = Column(JSON, nullable=False, default=dict)  # Pinned dependencies

    # Validation
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_deprecated = Column(Boolean, default=False, nullable=False)
    deprecation_reason = Column(Text, nullable=True)
    superseded_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=True)

    # Validation results
    validation_dataset_hash = Column(String(64), nullable=True)  # SHA256 of validation dataset
    validation_metrics = Column(JSON, nullable=False, default=dict)
    tolerance_config = Column(JSON, nullable=False, default=dict)  # Acceptance criteria

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(String(255), nullable=True)
    deprecated_at = Column(DateTime(timezone=True), nullable=True)

    # Self-referential relationship for deprecation chain
    superseded_by = relationship("ModelVersion", remote_side=[id], backref="supersedes")

    __table_args__ = (
        Index("ix_model_version_name_ver", "name", "version", unique=True),
        Index("ix_model_active", "is_active", "is_deprecated"),
    )


class DataLineage(Base):
    """Tracks data lineage between provenance records."""

    __tablename__ = "data_lineage"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links between provenance records
    input_provenance_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("provenance_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    output_provenance_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("provenance_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Transformation metadata
    transformation_type = Column(
        String(100), nullable=False
    )  # e.g., "interpolation", "aggregation", "model_inference"
    transformation_params = Column(JSON, nullable=False, default=dict)
    transformation_code_version = Column(String(100), nullable=True)

    # Quality
    data_quality_score = Column(String(20), nullable=True)
    transformation_notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    input_provenance = relationship(
        "ProvenanceRecord",
        foreign_keys=[input_provenance_id],
        back_populates="lineage_edges",
    )
    output_provenance = relationship(
        "ProvenanceRecord",
        foreign_keys=[output_provenance_id],
        back_populates="reverse_lineage_edges",
    )

    __table_args__ = (
        Index(
            "ix_lineage_input_output", "input_provenance_id", "output_provenance_id", unique=True
        ),
        Index("ix_lineage_transformation", "transformation_type"),
    )
