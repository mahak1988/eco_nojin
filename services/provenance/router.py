"""Data Provenance API Router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.hub import hub
from services.api_gateway.errors import safe_detail_for_status
from services.provenance.schemas import (
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
from services.provenance.service import ProvenanceService

router = APIRouter(prefix="/api/v1/provenance", tags=["provenance"])


async def get_db():
    async with hub.get_async_session() as session:
        yield session


async def get_provenance_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ProvenanceService:
    return ProvenanceService(db)


# =============================================================================
# Provenance Records
# =============================================================================


@router.post("", response_model=ProvenanceResponse, status_code=status.HTTP_201_CREATED)
async def create_provenance(
    data: ProvenanceCreate,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
):
    """Create a new provenance record for a scientific output."""
    return await service.create_provenance(data)


@router.get("/{provenance_id}", response_model=ProvenanceResponse)
async def get_provenance(
    provenance_id: str,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
):
    """Get a provenance record by ID."""
    record = await service.get_provenance(provenance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Provenance record not found")
    return record


@router.get("", response_model=ProvenanceListResponse)
async def list_provenance(
    provenance_type: Annotated[str | None, Query(description="Filter by provenance type")] = None,
    output_type: Annotated[str | None, Query(description="Filter by output type")] = None,
    model_name: Annotated[str | None, Query(description="Filter by model name")] = None,
    model_version: Annotated[str | None, Query(description="Filter by model version")] = None,
    is_validated: Annotated[bool | None, Query(description="Filter by validation status")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)] = None,
):
    """List provenance records with filtering and pagination."""
    return await service.list_provenance(
        provenance_type=provenance_type,
        output_type=output_type,
        model_name=model_name,
        model_version=model_version,
        is_validated=is_validated,
        page=page,
        page_size=page_size,
    )


@router.post("/{provenance_id}/validate", response_model=ValidationResponse)
async def validate_provenance(
    provenance_id: str,
    request: ProvenanceValidationRequest,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
):
    """Validate or invalidate a provenance record."""
    try:
        return await service.validate_provenance(request, validator_id="api_user")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


# =============================================================================
# Lineage Traversal
# =============================================================================


@router.post("/lineage", response_model=LineageResponse)
async def get_lineage(
    query: LineageQuery,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
):
    """Traverse data lineage upstream/downstream from a provenance record."""
    return await service.get_lineage(query)


# =============================================================================
# Model Version Management
# =============================================================================


@router.post("/models", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
async def register_model_version(
    data: ModelVersionCreate,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
):
    """Register a new model version for reproducibility tracking."""
    try:
        return await service.register_model_version(data, created_by="api_user")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=safe_detail_for_status(e, 400)) from e


@router.get("/models/{name}/{version}", response_model=ModelVersionResponse)
async def get_model_version(
    name: str,
    version: str,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)],
):
    """Get a specific model version."""
    record = await service.get_model_version(name, version)
    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")
    return record


@router.get("/models", response_model=list[ModelVersionResponse])
async def list_model_versions(
    name: Annotated[str | None, Query(description="Filter by model name")] = None,
    is_active: Annotated[bool | None, Query(description="Filter by active status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)] = None,
):
    """List registered model versions."""
    return await service.list_model_versions(
        name=name, is_active=is_active, page=page, page_size=page_size
    )


@router.post("/models/{name}/{version}/deprecate", response_model=ModelVersionResponse)
async def deprecate_model_version(
    name: str,
    version: str,
    reason: Annotated[str, Query(description="Reason for deprecation")],
    superseded_by_id: Annotated[
    str | None, Query(description="ID of model version that supersedes this one")
] = None,
    service: Annotated[ProvenanceService, Depends(get_provenance_service)] = None,
):
    """Deprecate a model version."""
    try:
        return await service.deprecate_model_version(name, version, reason, superseded_by_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e


# =============================================================================
# Lineage Edges
# =============================================================================


@router.post("/lineage/edges", status_code=status.HTTP_201_CREATED)
async def create_lineage_edge(
    input_provenance_id: str = Query(..., description="Input provenance record ID"),
    output_provenance_id: str = Query(..., description="Output provenance record ID"),
    transformation_type: str = Query(..., description="Type of transformation"),
    transformation_params: dict[str, Any] = Body(
        default_factory=dict, description="Transformation parameters"
    ),
    transformation_code_version: str | None = Query(
        None, description="Code version for transformation"
    ),
    data_quality_score: str | None = Query(None, description="Data quality score"),
    transformation_notes: str | None = Query(None, description="Notes about transformation"),
    service: ProvenanceService = Depends(get_provenance_service),
):
    """Create a lineage edge between two provenance records."""
    try:
        edge = await service.create_lineage_edge(
            input_provenance_id=input_provenance_id,
            output_provenance_id=output_provenance_id,
            transformation_type=transformation_type,
            transformation_params=transformation_params,
            transformation_code_version=transformation_code_version,
            data_quality_score=data_quality_score,
            transformation_notes=transformation_notes,
        )
        return {"status": "success", "edge_id": str(edge.id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=safe_detail_for_status(e, 404)) from e
