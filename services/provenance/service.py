"""Data Provenance Service - Core business logic for provenance tracking."""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.provenance.models import (
    DataLineage as LineageModel,
    ModelVersion as ModelVersionModel,
    ProvenanceRecord as ProvenanceModel,
    ProvenanceType as ProvenanceTypeEnum,
)
from services.provenance.schemas import (
    LineageEdge,
    LineageNode,
    LineageQuery,
    LineageResponse,
    ModelVersionCreate,
    ModelVersionResponse,
    ProvenanceCreate,
    ProvenanceListResponse,
    ProvenanceResponse,
    ProvenanceValidationRequest,
    ValidationResponse,
)


class ProvenanceService:
    """Service for managing data provenance records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Provenance Record CRUD
    # =========================================================================

    async def create_provenance(
        self, data: ProvenanceCreate, user_id: str | None = None
    ) -> ProvenanceResponse:
        """Create a new provenance record."""
        # Generate content hash for the output
        output_content = {
            "output_id": data.output_id,
            "output_type": data.output_type,
            "model_name": data.model_name,
            "model_version": data.model_version,
            "algorithm_parameters": data.algorithm_parameters,
        }
        hashlib.sha256(json.dumps(output_content, sort_keys=True).encode()).hexdigest()

        # Parse execution_id or generate new
        execution_id = data.execution_id or str(uuid.uuid4())

        ProvenanceModel(
            provenance_type=ProvenanceTypeEnum(data.provenance_type),
            output_id=data.output_id,
            output_type=data.output_type,
            input_hashes=data.input_hashes,
            input_sources=data.input_sources,
            model_version=data.model_version,
            model_name=data.model_name,
            algorithm_parameters=data.algorithm_parameters,
            execution_id=execution_id,
            executed_by=data.executed_by,
            execution_environment=data.execution_environment,
            uncertainty=data.uncertainty,
            confidence_level=data.confidence_level,
            is_validated=data.is_validated,
            validation_notes=data.validation_notes,
            quality_score=data.quality_score,
            is_reproducible=data.is_reproducible,
            reproducibility_notes=data.reproducibility_notes,
            docker_image_digest=data.docker_image_digest,
        )

        self.db.add(data)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(data)

        return ProvenanceResponse.model_validate(data)

    async def get_provenance(self, provenance_id: str) -> ProvenanceResponse | None:
        """Get a provenance record by ID."""
        result = await self.db.execute(
            select(ProvenanceModel).where(ProvenanceModel.id == provenance_id)
        )
        record = result.scalar_one_or_none()
        if record:
            return ProvenanceResponse.model_validate(record)
        return None

    async def list_provenance(
        self,
        provenance_type: str | None = None,
        output_type: str | None = None,
        model_name: str | None = None,
        model_version: str | None = None,
        is_validated: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ProvenanceListResponse:
        """List provenance records with filters and pagination."""
        query = select(ProvenanceModel)

        if provenance_type:
            query = query.where(
                ProvenanceModel.provenance_type == ProvenanceTypeEnum(provenance_type)
            )
        if output_type:
            query = query.where(ProvenanceModel.output_type == output_type)
        if model_name:
            query = query.where(ProvenanceModel.model_name == model_name)
        if model_version:
            query = query.where(ProvenanceModel.model_version == model_version)
        if is_validated is not None:
            query = query.where(ProvenanceModel.is_validated == is_validated)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Pagination
        query = query.order_by(ProvenanceModel.executed_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        records = result.scalars().all()

        items = [ProvenanceResponse.model_validate(r) for r in records]

        return ProvenanceListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )

    async def validate_provenance(
        self, request: ProvenanceValidationRequest, validator_id: str
    ) -> ValidationResponse:
        """Validate or invalidate a provenance record."""
        result = await self.db.execute(
            select(ProvenanceModel).where(ProvenanceModel.id == request.provenance_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"Provenance record {request.provenance_id} not found")

        record.is_validated = request.is_valid
        record.quality_score = request.quality_score
        if request.notes:
            record.validation_notes = (
                record.validation_notes or ""
            ) + f"\n[{datetime.now(UTC).isoformat()}] {validator_id}: {request.notes}"

        await self.db.commit()
        await self.db.refresh(record)

        return ValidationResponse(
            provenance_id=request.provenance_id,
            is_validated=request.is_valid,
            validated_at=datetime.now(UTC),
            validator_id=validator_id,
        )

    # =========================================================================
    # Lineage Traversal
    # =========================================================================

    async def get_lineage(self, query: LineageQuery) -> LineageResponse:
        """Traverse data lineage upstream/downstream."""
        visited: set[str] = set()
        nodes: list[LineageNode] = []
        edges: list[LineageEdge] = []

        async def traverse_upstream(prov_id: str, depth: int):
            if depth > query.max_depth or prov_id in visited:
                return
            visited.add(prov_id)

            # Get the provenance record
            result = await self.db.execute(
                select(ProvenanceModel).where(ProvenanceModel.id == prov_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                return

            nodes.append(
                LineageNode(
                    provenance_id=str(record.id),
                    provenance_type=record.provenance_type.value,
                    output_type=record.output_type,
                    output_id=record.output_id,
                    executed_at=record.executed_at,
                    model_name=record.model_name,
                    model_version=record.model_version,
                    is_validated=record.is_validated,
                )
            )

            # Get upstream lineage edges
            edges_result = await self.db.execute(
                select(LineageModel).where(LineageModel.output_provenance_id == record.id)
            )
            for edge in edges_result.scalars().all():
                edges.append(
                    LineageEdge(
                        from_id=str(edge.input_provenance_id),
                        to_id=str(edge.output_provenance_id),
                        transformation_type=edge.transformation_type,
                        transformation_params=edge.transformation_params,
                    )
                )
                await traverse_upstream(str(edge.input_provenance_id), depth + 1)

        async def traverse_downstream(prov_id: str, depth: int):
            if depth > query.max_depth or prov_id in visited:
                return
            visited.add(prov_id)

            result = await self.db.execute(
                select(ProvenanceModel).where(ProvenanceModel.id == prov_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                return

            nodes.append(
                LineageNode(
                    provenance_id=str(record.id),
                    provenance_type=record.provenance_type.value,
                    output_type=record.output_type,
                    output_id=record.output_id,
                    executed_at=record.executed_at,
                    model_name=record.model_name,
                    model_version=record.model_version,
                    is_validated=record.is_validated,
                )
            )

            # Get downstream lineage edges
            edges_result = await self.db.execute(
                select(LineageModel).where(LineageModel.input_provenance_id == prov_id)
            )
            for edge in edges_result.scalars().all():
                edges.append(
                    LineageEdge(
                        from_id=str(edge.input_provenance_id),
                        to_id=str(edge.output_provenance_id),
                        transformation_type=edge.transformation_type,
                        transformation_params=edge.transformation_params,
                    )
                )
                await traverse_downstream(str(edge.output_provenance_id), depth + 1)

        if query.direction in ("upstream", "both"):
            await traverse_upstream(query.provenance_id, 0)
        if query.direction in ("downstream", "both"):
            await traverse_downstream(query.provenance_id, 0)

        return LineageResponse(
            nodes=nodes,
            edges=edges,
            max_depth_reached=len(visited) >= query.max_depth,
        )

    # =========================================================================
    # Model Version Management
    # =========================================================================

    async def register_model_version(
        self, data: ModelVersionCreate, created_by: str
    ) -> ModelVersionResponse:
        """Register a new model version."""
        # Check if version already exists
        existing = await self.db.execute(
            select(ModelVersionModel).where(
                and_(
                    ModelVersionModel.name == data.name,
                    ModelVersionModel.version == data.version,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Model version {data.name} v{data.version} already exists")

        record = ModelVersionModel(
            name=data.name,
            version=data.version,
            description=data.description,
            algorithm_class=data.algorithm_class,
            framework=data.framework,
            git_commit=data.git_commit,
            docker_image=data.docker_image,
            dependencies=data.dependencies,
            validation_dataset_hash=data.validation_dataset_hash,
            validation_metrics=data.validation_metrics,
            tolerance_config=data.tolerance_config,
            created_by=created_by,
        )

        self.db.add(record)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(record)

        return ModelVersionResponse.model_validate(record)

    async def get_model_version(self, name: str, version: str) -> ModelVersionResponse | None:
        """Get a specific model version."""
        result = await self.db.execute(
            select(ModelVersionModel).where(
                and_(
                    ModelVersionModel.name == name,
                    ModelVersionModel.version == version,
                )
            )
        )
        record = result.scalar_one_or_none()
        if record:
            return ModelVersionResponse.model_validate(record)
        return None

    async def list_model_versions(
        self,
        name: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[ModelVersionResponse]:
        """List model versions with filters."""
        query = select(ModelVersionModel)

        if name:
            query = query.where(ModelVersionModel.name == name)
        if is_active is not None:
            query = query.where(ModelVersionModel.is_active == is_active)

        query = query.order_by(ModelVersionModel.created_at.desc())
        query = query.offset((page - 1) * 20).limit(page_size)

        result = await self.db.execute(query)
        records = result.scalars().all()

        return [ModelVersionResponse.model_validate(r) for r in records]

    async def deprecate_model_version(
        self, name: str, version: str, reason: str, superseded_by_id: str | None = None
    ) -> ModelVersionResponse:
        """Deprecate a model version."""
        result = await self.db.execute(
            select(ModelVersionModel).where(
                and_(
                    ModelVersionModel.name == name,
                    ModelVersionModel.version == version,
                )
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"Model version {name} v{version} not found")

        record.is_deprecated = True
        record.deprecated_at = datetime.now(UTC)
        record.deprecation_reason = reason
        if superseded_by_id:
            record.superseded_by_id = superseded_by_id
        record.is_active = False

        await self.db.commit()
        await self.db.refresh(record)

        return ModelVersionResponse.model_validate(record)

    # =========================================================================
    # Lineage Edge Creation
    # =========================================================================

    async def create_lineage_edge(
        self,
        input_provenance_id: str,
        output_provenance_id: str,
        transformation_type: str,
        transformation_params: dict[str, Any],
        transformation_code_version: str | None = None,
        data_quality_score: str | None = None,
        transformation_notes: str | None = None,
    ) -> LineageModel:
        """Create a lineage edge between two provenance records."""
        # Verify both records exist
        input_record = await self.db.execute(
            select(ProvenanceModel).where(ProvenanceModel.id == input_provenance_id)
        )
        if not input_record.scalar_one_or_none():
            raise ValueError(f"Input provenance {input_provenance_id} not found")

        output_record = await self.db.execute(
            select(ProvenanceModel).where(ProvenanceModel.id == output_provenance_id)
        )
        if not output_record.scalar_one_or_none():
            raise ValueError(f"Output provenance {output_provenance_id} not found")

        edge = LineageModel(
            input_provenance_id=input_provenance_id,
            output_provenance_id=output_provenance_id,
            transformation_type=transformation_type,
            transformation_params=transformation_params,
            transformation_code_version=transformation_code_version,
            data_quality_score=data_quality_score,
            transformation_notes=transformation_notes,
        )

        self.db.add(edge)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(edge)

        return edge

    async def get_lineage_edges(self, provenance_id: str) -> list[LineageModel]:
        """Get all lineage edges for a provenance record."""
        result = await self.db.execute(
            select(LineageModel).where(
                or_(
                    LineageModel.input_provenance_id == provenance_id,
                    LineageModel.output_provenance_id == provenance_id,
                )
            )
        )
        return result.scalars().all()
